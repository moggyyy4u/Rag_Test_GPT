import ollama

response = ollama.chat(
    model="qwen2.5:3b",
    messages=[
        {
            "role": "user",
            "content": "What is normalization in a database?"
        }
    ]
)

print(response["message"]["content"])