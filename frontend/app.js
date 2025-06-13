const API_URL = "http://localhost:8000"; // Change if backend runs elsewhere

function getJWT() {
    return document.getElementById('jwt').value.trim();
}

async function askQuestion() {
    const question = document.getElementById('question').value.trim();
    const jwt = getJWT();
    if (!question || !jwt) {
        alert("Please enter a question and JWT token.");
        return;
    }
    const res = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${jwt}`
        },
        body: JSON.stringify({ query: question })
    });
    const data = await res.json();
    document.getElementById('answer').innerText = data.answer || JSON.stringify(data);
}

async function uploadDoc() {
    const fileInput = document.getElementById('docfile');
    const jwt = getJWT();
    if (!fileInput.files.length || !jwt) {
        alert("Please select a file and enter JWT token.");
        return;
    }
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    // If your /upload expects JSON, adjust accordingly
    const res = await fetch(`${API_URL}/upload`, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${jwt}`
        },
        body: formData
    });
    const data = await res.json();
    document.getElementById('upload-result').innerText = JSON.stringify(data);
}