from flask import Flask, render_template, request 
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

    file.save("uploads/" + file.filename)

    return{"filename": file.filename}

@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)