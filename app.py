from flask import Flask, render_template, request 
from pypdf import PdfReader
import os
app = Flask(__name__)
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data["message"]

    if "normalization" in message.lower():
        answer="Normalization is the process of organizing data in a database to reduce redundancy and improve data integrity."
    else:
        answer="I don't know that yet."

    return{"answer": answer}

@app.route("/upload", methods=["POST"])
def upload():
    file= request.files["file"]
   

    file_path = "uploads/" + file.filename
    file.save(file_path)
  

    

    
    reader = PdfReader(file_path)
    text=""

    for page in reader.pages:
        text+= page.extract_text() or ""

    chunks=[]

    position =0
    chunk_size = 500
    overlap = 100

    while position < len(text):
        chunk= text[position:position+chunk_size]
        chunks.append(chunk)
        position+= chunk_size-overlap

    


   

    return{"filename": file.filename}

@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)