const API_URL = "http://localhost:8000";
let jwtToken = null;

function getJWT() {
    return jwtToken;
}

function parseJwt (token) {
    try {
        return JSON.parse(atob(token.split('.')[1]));
    } catch (e) {
        return {};
    }
}

function logout() {
    jwtToken = null;
    document.getElementById('main-ui').style.display = "none";
    document.getElementById('login-section').style.display = "block";
    document.getElementById('login-username').value = "";
    document.getElementById('login-password').value = "";
    document.getElementById('login-error').innerText = "";
    document.getElementById('answer').innerText = "";
    document.getElementById('upload-result').innerText = "";
    document.getElementById('user-name').innerText = "";
    document.getElementById('user-role').innerText = "";
    // Optionally clear file input and question
    if (document.getElementById('docfile')) document.getElementById('docfile').value = "";
    if (document.getElementById('question')) document.getElementById('question').value = "";
}


async function login() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value.trim();
    document.getElementById('login-error').innerText = "";
    if (!username || !password) {
        document.getElementById('login-error').innerText = "Please enter username and password.";
        return;
    }
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    const res = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: formData
    });

    if (res.ok) {
        const data = await res.json();
        jwtToken = data.access_token;
        // Decode JWT to get user info
        const payload = parseJwt(jwtToken);
        document.getElementById('user-name').innerText = payload.sub || "";
        document.getElementById('user-role').innerText = payload.roles ? `(${Array.isArray(payload.roles) ? payload.roles.join(', ') : payload.roles})` : "";
        document.getElementById('login-section').style.display = "none";
        document.getElementById('main-ui').style.display = "block";
    } else {
        const err = await res.json();
        document.getElementById('login-error').innerText = err.detail || "Login failed.";
    }
}

async function askQuestion() {
    const question = document.getElementById('question').value.trim();
    const jwt = getJWT();
    if (!question || !jwt) {
        alert("Please enter a question and login first.");
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
        alert("Please select a file and login first.");
        return;
    }
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

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