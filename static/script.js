async function sendMessage() {
    const input = document.getElementById("messageInput");
    const message = input.value;
    input.value="";
    try{
    
    const response = await fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message: message
        })
    });
    if (!response.ok){
        throw new Error("Server error: "+reponse.status);
    }
    const data = await response.json();
    

    const chatHistory = document.getElementById("chatHistory");
    const messageDiv=document.createElement("div");
    messageDiv.className="chat-message";
   messageDiv.innerHTML = `
   <div class="user-question">
    <p>${message}</p>
   </div>
   <div class = "answer-section">
        <p>${data.answer}</p>
    </div>
    ${data.sources && data.sources.length>0 ? `
        <div class = "sources-section">
            <h3>Sources</h3>
            <div id = "source-list"></div>
        </div>
    `:""}
    `;
    chatHistory.appendChild(messageDiv);

    const sourceList = messageDiv.querySelector("#source-list");

    const seenSources = new Set();
    let sourceNumber = 1;

    (data.sources || []).forEach((source, index) =>{
        const sourceKey = `${source.filename}-${source.page}`;

        if(seenSources.has(sourceKey)){
            return;
        }
        seenSources.add(sourceKey);
        
    sourceList.innerHTML+=`
        <div class ="source-card">
            <strong>${sourceNumber}.${source.filename}</strong>
            <span>Page ${source.page}</span>
        </div>
    `;
    sourceNumber++;
    });
}   catch (error){
        const chatHistory= document.getElementById("chatHistory");
        const errorDiv = document.createElement("div");

        errorDiv.className="answer-section";
        errorDiv.textContent="Something went wrong. Please check that Flask and Ollama are running.";

        chatHistory.appendChild(errorDiv);
        console.error(error);
    }
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

document.getElementById("messageInput").addEventListener("keydown",function(event){
    if (event.key === "Enter"){
        sendMessage();
    }
});