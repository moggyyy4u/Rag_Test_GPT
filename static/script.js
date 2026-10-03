async function sendMessage() {
    const input = document.getElementById("messageInput");
    const message = input.value;

    const response = await fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message: message
        })
    });

    const data = await response.json();

document.getElementById("response").textContent = data.answer;
}