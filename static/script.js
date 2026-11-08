async function sendMessage() {
    const input = document.getElementById("messageInput");
    const message = input.value.trim();

    if (!message) return;

    input.value = "";

    const chatHistory = document.getElementById("chatHistory");

    const messageDiv = document.createElement("div");
    messageDiv.className = "chat-message";

    messageDiv.innerHTML = `
        <div class="user-question">
            <p></p>
        </div>

        <div class="answer-section">
            <p id="streamedAnswer"></p>
        </div>
    `;
   
    messageDiv.querySelector(".user-question p").textContent = message;

    chatHistory.appendChild(messageDiv);

    const streamedAnswer = messageDiv.querySelector("#streamedAnswer");

    try {

        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });

        if (!response.ok) {
            throw new Error("Server error: " + response.status);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        let buffer = "";
        let receivedText="";
        let finalData = null;

        let currentSection=null;
        let documentText="";
        let generalText="";
        let pendingText="";
        let hasDocumentContext=false;
        while (true) {

            const { value, done } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            

            const events = buffer.split("\n\n");

            buffer = events.pop();

            for (const event of events) {

                if (!event.startsWith("data: ")) continue;

                const data = JSON.parse(event.slice(6));

                if(data.type==="start"){
                    hasDocumentContext=data.has_document_context;
                }

                if (data.type === "token") {
                    streamedAnswer.textContent+=data.content
                }
                if (data.type === "complete") {
                    finalData = data;
                }
            }
        }
        console.log("FULL MODEL RESPONSE:",receivedText);
        
        messageDiv.querySelector(".answer-section").remove();

        if (finalData.document_answer) {
            const documentSection = document.createElement("div");
            documentSection.className = "answer-section";

            const heading = document.createElement("h3");
            heading.textContent = "From your uploaded notes";

            const paragraph = document.createElement("p");
            paragraph.textContent = finalData.document_answer;

            documentSection.append(heading, paragraph);
            messageDiv.appendChild(documentSection);
        }

        if (finalData.general_answer) {
            const generalSection = document.createElement("div");
            generalSection.className = "answer-section";

            const heading = document.createElement("h3");
            heading.textContent = "General knowledge";

            const paragraph = document.createElement("p");
            paragraph.textContent = finalData.general_answer;

            generalSection.append(heading, paragraph);
            messageDiv.appendChild(generalSection);
        }

        if (finalData.sources && finalData.sources.length > 0) {

            const sourcesSection = document.createElement("div");
            sourcesSection.className = "sources-section";

            sourcesSection.innerHTML = `
                <h3>Sources</h3>
                <div class="source-list"></div>
            `;

            const sourceList = sourcesSection.querySelector(".source-list");
            const seenSources = new Set();

            let sourceNumber = 1;

            finalData.sources.forEach(source => {

                const sourceKey = `${source.filename}-${source.page}`;

                if (seenSources.has(sourceKey)) return;

                seenSources.add(sourceKey);

                const sourceCard = document.createElement("div");
                sourceCard.className = "source-card";

                sourceCard.textContent =
                    `${sourceNumber}. ${source.filename} — Page ${source.page}`;

                sourceList.appendChild(sourceCard);

                sourceNumber++;
            });

            messageDiv.appendChild(sourcesSection);
        }

    }  catch (error) {

        const errorDiv = document.createElement("div");

        errorDiv.className = "answer-section";
        errorDiv.textContent =
            "Something went wrong. Please check that Flask and Ollama are running.";

        messageDiv.appendChild(errorDiv);

        console.error(error);
    }
}


async function uploadFile() {
    const input = document.getElementById("fileInput");
    const file = input.files[0];

    if (!file) {
        document.getElementById("uploadResponse").textContent = "Please select a PDF first.";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const progressContainer = document.getElementById("uploadProgress");
    const progressBar = document.getElementById("progressBar");
    const progressText = document.getElementById("progressText");
    const uploadStatus = document.getElementById("uploadStatus");
    const uploadResponse = document.getElementById("uploadResponse");

    progressContainer.style.display = "block";
    progressBar.value = 0;
    progressText.textContent = "0%";
    uploadStatus.textContent = "Uploading PDF...";
    uploadResponse.textContent = "";

    const xhr = new XMLHttpRequest();
    let progressInterval = null;

    xhr.open("POST", "/upload");

    xhr.upload.addEventListener("progress", function(event) {
        if (event.lengthComputable) {
            const percent = Math.round((event.loaded / event.total) * 20);

            progressBar.value = percent;
            progressText.textContent = percent + "%";

            if (percent === 20 && !progressInterval) {
                uploadStatus.textContent = "Processing PDF...";

                progressInterval = setInterval(async function() {
                    try {
                        const response = await fetch("/upload-progress");
                        const progress = await response.json();

                        progressBar.value = progress.percent;
                        progressText.textContent = progress.percent + "%";
                        uploadStatus.textContent = progress.status;
                    } catch (error) {
                        console.log("Progress update failed:", error);
                    }
                }, 500);
            }
        }
    });

    xhr.onload = function() {
        if (progressInterval) {
            clearInterval(progressInterval);
        }

        let data;

        try {
            data = JSON.parse(xhr.responseText);
        } catch (error) {
            uploadStatus.textContent = "Upload failed.";
            uploadResponse.textContent = "Invalid server response.";
            return;
        }

        if (xhr.status >= 200 && xhr.status < 300) {
            progressBar.value = 100;
            progressText.textContent = "100%";
            uploadStatus.textContent = "Upload and processing complete!";
            uploadResponse.textContent = `Uploaded: ${data.filename}`;
        } else {
            uploadStatus.textContent = "Upload failed.";
            uploadResponse.textContent = data.message || "Something went wrong.";
        }
    };

    xhr.onerror = function() {
        if (progressInterval) {
            clearInterval(progressInterval);
        }

        uploadStatus.textContent = "Upload failed.";
        uploadResponse.textContent = "Network error. Please try again.";
    };

    xhr.send(formData);
}

document.getElementById("messageInput").addEventListener("keydown",function(event){
    if (event.key === "Enter"){
        sendMessage();
    }
});