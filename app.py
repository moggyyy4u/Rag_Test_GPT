from flask import Flask, render_template, request 
from pypdf import PdfReader
import os
from sentence_transformers import SentenceTransformer
import faiss
import ollama

app= Flask(__name__)

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

faiss_index = None
chunks = []
uploaded_files = set()


@app.route("/chat", methods=["POST"])
def chat():
    global faiss_index, chunks
    data = request.get_json()
    message = data["message"]

    if faiss_index is None or len(chunks)==0:
        return{"answer": "Please upload a document first."}

    question_vector = embedding_model.encode(
        [message],
        normalize_embeddings=True
        )

    similarities, indices = faiss_index.search(question_vector,3)

    print("Distances:", similarities[0])

    threshold= 0.40

    retrieved_chunks=[]

    for score, i in zip(similarities[0],indices[0]):

        if score>= threshold:

            chunk=chunks[i]

            retrieved_chunks.append({
                "text": chunk["text"],
                "page": chunk["page"],
                "filename": chunk["filename"]
        })
    print("Similarities:", similarities[0])

    if len(retrieved_chunks)==0:
        return{
            "answer": "I couldn't find the answer in the uploaded document.",
            "sources": []
        }
        

    context = "\n\n".join(
        chunk["text"] for chunk in retrieved_chunks
    )

    prompt = f"""
You are a helpful school assistant.

Answer the user's question using ONLY the information provided in the context.

If the answer cannot be found in the context, say:
"I couldn't find the answer in the uploaded document."

Context:
{context}

Question:
{message}

Answer:
"""
    response = ollama.chat(
        model ="qwen2.5:3b",
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )
    answer = response["message"]["content"]
    return{
        "answer": answer,
        "sources": retrieved_chunks
        
    }
 

@app.route("/upload", methods=["POST"])
def upload():
    global faiss_index, chunks
    file= request.files["file"]
    if file.filename in uploaded_files:
        return{
            "message": "This file has already been uploaded",
            "filename": file.filename
        }, 409
    file_path = "uploads/" + file.filename
    file.save(file_path)
    
    reader = PdfReader(file_path)
   



    new_chunks =[]

    chunk_size = 500
    overlap = 100

    for page_number, page in enumerate(reader.pages,start=1):
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


    vectors= embedding_model.encode(
        texts,
        normalize_embeddings = True
    )
    print("Number of chunks:", len(chunks))
    print("Vector shape:", vectors.shape)
    dimension = vectors.shape[1]
    if faiss_index is None:
        faiss_index = faiss.IndexFlatIP(dimension)

    faiss_index.add(vectors)

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
    app.run(debug=True)