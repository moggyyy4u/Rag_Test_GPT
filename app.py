from flask import Flask, render_template, request 
app = Flask(__name__)
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data["message"]

    return{"answer": f"You asked: {message}"}
@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)