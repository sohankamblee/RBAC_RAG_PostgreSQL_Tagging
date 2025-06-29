const API_URL = "http://localhost:9000";
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
    // --- Hide upload section on logout ---
    document.getElementById('upload').style.display = "none";
}


async function login() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value.trim();
    document.getElementById('login-error').innerText = "";
    if (!username || !password) {
        document.getElementById('login-error').innerText = "Please enter username and password.";
        return;
    }
    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);

    try {
        const res = await fetch(`${API_URL}/login`, {
            method: "POST",
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
            // --- Show upload section if user is admin ---
            if (payload.access_tags && payload.access_tags.includes("admin")) {
                document.getElementById('upload').style.display = "block";
            } else {
                document.getElementById('upload').style.display = "none";
            }
        } else {
            const err = await res.json();
            document.getElementById('login-error').innerText = err.detail || "Login failed.";
        }
    } catch (e) {
        document.getElementById('login-error').innerText = "Network error or server not reachable.";
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
    const tagsInput = document.getElementById('access-tags');
    const jwt = getJWT();
    if (!fileInput.files.length || !jwt) {
        alert("Please select at least one file and login first.");
        return;
    }
    const tags = tagsInput.value.split(',').map(t => t.trim()).filter(Boolean);
    if (!tags.length) {
        alert("Please enter at least one access tag.");
        return;
    }
    const formData = new FormData();
    for (let i = 0; i < fileInput.files.length; i++) {
        formData.append("files", fileInput.files[i]);
    }
    tags.forEach(tag => formData.append("access_tags", tag));

    // Send the upload request
    const res = await fetch(`${API_URL}/upload`, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${jwt}`
        },
        body: formData
    });
    const data = await res.json();

    // Display results in a user-friendly way
    let html = "";
    if (data.results && Array.isArray(data.results)) {
        html = "<ul>";
        data.results.forEach(r => {
            if (r.status === "success") {
                html += `<li><b>${r.filename}</b>: ✅ Uploaded (${r.chunks_uploaded} chunks)</li>`;
            } else {
                html += `<li><b>${r.filename}</b>: ❌ Failed (${r.reason})</li>`;
            }
        });
        html += "</ul>";
    } else {
        html = "Unexpected response: " + JSON.stringify(data);
    }
    document.getElementById('upload-result').innerHTML = html;
}