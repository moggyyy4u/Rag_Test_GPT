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


async function uploadFile() {
    const input = document.getElementById("fileInput");
    const file = input.files[0];

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("/upload", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    document.getElementById("uploadResponse").textContent =
        `Uploaded: ${data.filename}`;
}