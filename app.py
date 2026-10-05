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


@app.route("/chat", methods=["POST"])
def chat():
    global faiss_index, chunks
    data = request.get_json()
    message = data["message"]

    if faiss_index is None or len(chunks)==0:
        return{"answer": "Please upload a document first."}

    question_vector = embedding_model.encode([message])

    distances, indices = faiss_index.search(question_vector,3)

    retrieved_chunks=[]

    for i in indices[0]:
        retrieved_chunks.append(chunks[i])

    context = "\n\n".join(retrieved_chunks)

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
        "answer": answer
        
    }
 

@app.route("/upload", methods=["POST"])
def upload():
    global faiss_index, chunks
    file= request.files["file"]
    file_path = "uploads/" + file.filename
    file.save(file_path)
    
    reader = PdfReader(file_path)
    print("Number of pages:", len(reader.pages))
    text=""

    for page in reader.pages:
        text+= page.extract_text() or ""

    print("Extracted text length:", len(text))
    print("First 200 characters:", text[:200])

    chunks=[]

    position =0
    chunk_size = 500
    overlap = 100

    while position < len(text):
        chunk= text[position:position+chunk_size]
        chunks.append(chunk)
        position+= chunk_size-overlap

    vectors= embedding_model.encode(chunks)
    print("Number of chunks:", len(chunks))
    print("Vector shape:", vectors.shape)
    dimension = vectors.shape[1]
    faiss_index= faiss.IndexFlatL2(dimension)
    faiss_index.add(vectors)

    return{
        "filename": file.filename,
        "chunks": len(chunks),
        "vectors": vectors.shape[0]}

@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)