import time
import time
import numpy as np

start = time.perf_counter()
from flask import Flask, render_template, request, Response, stream_with_context
print("Flask:", round(time.perf_counter()-start, 2))

start = time.perf_counter()
import json
import os
print("JSON and OS:", round(time.perf_counter()-start, 2))

start = time.perf_counter()
from pypdf import PdfReader
print("PyPDF:", round(time.perf_counter()-start, 2))


start = time.perf_counter()
import faiss
print("FAISS:", round(time.perf_counter()-start, 2))

start = time.perf_counter()
import ollama
print("Ollama:", round(time.perf_counter()-start, 2))


app= Flask(__name__)

start_time= time.perf_counter()
embedding_model =None
def get_embedding_model():
    global embedding_model

    if embedding_model is None:
        from sentence_transformers import SentenceTransformer
        embedding_model=SentenceTransformer("all-MiniLM-L6-v2")
    return embedding_model

faiss_index = None
chunks = []
uploaded_files = set()
upload_progress={
     "percent":0,
     "status":"idle"
}


@app.route("/chat", methods=["POST"])
def chat():
    global faiss_index, chunks
    data = request.get_json()
    message = data["message"]

    retrieved_chunks=[]
    context=""
    print("FAISS index:", faiss_index)
    print("Number of chunks:",len(chunks))
    if faiss_index is not None and len(chunks)>0:
       

        question_vector = get_embedding_model().encode(
        [message],
        normalize_embeddings=True
        )

        similarities, indices = faiss_index.search(question_vector,3)

        threshold= 0.40

        for score, i in zip(similarities[0],indices[0]):

            if score>= threshold:

                chunk=chunks[i]

                retrieved_chunks.append({
                    "text": chunk["text"],
                    "page": chunk["page"],
                    "filename": chunk["filename"]
        })

 

    context = "\n\n".join(
        chunk["text"] for chunk in retrieved_chunks
    )
    
    if retrieved_chunks:
    

            prompt = f"""
            You are a helpful school assistant.

            Answer the user's question using the uploaded document as your primary source.

            DOCUMENT ANSWER:
            Include facts supported by the uploaded context.

            GENERAL KNOWLEDGE:
            Include additional relevant information not covered by the document.
            If no additional information is needed, write NONE.

            Rules:
            1. Never invent facts from the document.
            2. Give accurate examples when requested.
            3. If uncertain, say so.
            4. Keep the answer clear and easy for a student to understand.

            Uploaded context:
            {context}

            User question:
            {message}
            """

    else:

        prompt = f"""
        You are a helpful school assistant.

        Answer the user's question using general knowledge.

        GENERAL KNOWLEDGE:
        Give a clear, accurate and helpful answer.
        Do not include a DOCUMENT ANSWER section.
        Do not mention uploaded documents.

        Rules:
        1. Do not invent facts.
        2. Give accurate examples when requested.
        3. If uncertain, say so.
        4. Keep the answer clear and easy for a student to understand.

        User question:
        {message}
        """
         
    
    response = ollama.chat(
        model ="qwen2.5:3b",
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ],
        stream=True
    )
    @stream_with_context
    def generate():
        generation_start=time.perf_counter()
        first_token_time=None
        answer = ""
        yield f"data: {json.dumps({'type':'start','has_document_context':len(retrieved_chunks)>0})}\n\n"

        for chunk in response:
            text=chunk["message"]["content"]

            if first_token_time is None:
                 first_token_time=time.perf_counter()
                 print("Time to first token:", round(first_token_time-generation_start,2),"seconds")
                 
            answer+=text

            print("Sending token:", repr(text), flush=True)

            yield f"data: {json.dumps({'type':'token','content': text})}\n\n"

        print("Total generation time:",round(time.perf_counter()-generation_start,2),"seconds")
        
        document_answer=""
        general_answer=""

        lower_answer = answer.lower()

        doc_marker = "document answer:"
        general_marker = "general knowledge:"

        doc_start = lower_answer.find(doc_marker)
        general_start = lower_answer.find(general_marker)

        if doc_start != -1 and general_start != -1:

            document_answer = answer[
                doc_start + len(doc_marker):general_start
            ].strip()

            general_answer = answer[
                general_start + len(general_marker):
            ].strip()

        elif general_start != -1:

            general_answer = answer[
                general_start + len(general_marker):
            ].strip()

        elif doc_start != -1:

            document_answer = answer[
                doc_start + len(doc_marker):
            ].strip()

        else:
            general_answer = answer.strip()

        if len(retrieved_chunks)==0:
             document_answer=""
             sources=[]
        else:
             sources = retrieved_chunks

        if document_answer.upper()in [
                "NONE",
                "NONE.",
                ""
            ]:
                document_answer=""
                sources=[]

        if general_answer.upper() in ["NONE","NONE.",""]:
                general_answer=""

        final_data={
                "type":"complete",
                "document_answer": document_answer,
                "general_answer":general_answer,
                "sources": sources
            }

        yield f"data: {json.dumps(final_data)}\n\n"

    return Response(
                generate(),
                mimetype="text/event-stream",
                headers = {
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering":"no",
                    "Connection":"keep-alive"
                },
                
                
        )

@app.route("/upload-progress")
def get_upload_progress():
     return upload_progress

@app.route("/upload", methods=["POST"])
def upload():
    global faiss_index, chunks, upload_progress
    file= request.files["file"]
    if file.filename in uploaded_files:
        return{
            "message": "This file has already been uploaded",
            "filename": file.filename
        }, 409
    file_path = "uploads/" + file.filename
    file.save(file_path)

    upload_progress={
         "percent":20,
         "status":"Extracting PDF text..."
    }
    
    reader = PdfReader(file_path)
   



    new_chunks =[]
    total_pages =len(reader.pages)

    chunk_size = 500
    overlap = 100

    for page_number, page in enumerate(reader.pages,start=1):
        upload_progress={
            "percent": 20 + int((page_number/total_pages)*20),
            "status": f"Extracting page {page_number}of {total_pages}..."
        }
        page_text =page.extract_text() or ""

        position =0

        while position < len(page_text):
            chunk= page_text[position:position+chunk_size]
            new_chunks.append({
                "text": chunk,
                "page": page_number,
                "filename": file.filename
            })
            position+= chunk_size-overlap

    texts= [chunk["text"] for chunk in new_chunks]


    model= get_embedding_model()
    all_vectors=[]
    batch_size=32
    total_batches=(len(texts)+batch_size-1)//batch_size
    for i in range(0,len(texts),batch_size):
        batch=texts[i:i+batch_size]

        batch_vectors=model.encode(
            batch,
            normalize_embeddings = True
        )

        all_vectors.extend(batch_vectors)
        completed_batches=(i//batch_size)+1

        upload_progress={
            "percent":40+int((completed_batches/total_batches)*50),
            "status": f"Generating embeddings...{completed_batches}/{total_batches} batches"
        }
    vectors= np.asarray(all_vectors,dtype="float32")

    dimension = vectors.shape[1]

    upload_progress={
         "percent":90,
         "status":"Updating FAISS index..."
    }

    if faiss_index is None:
        faiss_index = faiss.IndexFlatIP(dimension)

    faiss_index.add(vectors)

    chunks.extend(new_chunks)
    uploaded_files.add(file.filename)

    upload_progress={
             "percent":100,
             "status":"Upload complete!"
        }

    chunks.extend(new_chunks)
    uploaded_files.add(file.filename)
    return{
        "filename": file.filename,
        "chunks": len(chunks),
        "vectors": vectors.shape[0]
        }

@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True,use_reloader= False)