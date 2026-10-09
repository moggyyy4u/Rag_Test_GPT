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

    const responseDiv = document.getElementById("response");

   responseDiv.innerHTML = `
   <p><strong>Answer:</strong></p>
   <p>${data.answer}</p>

   <p><strong>Sources:</strong></p>
    `;

    data.sources.forEach((source, index) =>{
        responseDiv.innerHTML += `
        <p>
            ${index +1}.${source.filename} — Page ${source.page}
        
        </p>
    `;
    });
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
        response.ok
            ?`Uploaded: ${data.filename}`
            : data.message;
}