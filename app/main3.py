# main3.py
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from typing import List
from app.auth import get_current_user
from app.models import QueryRequest, UploadRequest
from app.mcp_app import orchestrator
from app.doc_ingestor import ingest_pdfs
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from app.config import JWT_SECRET, ALGORITHM 
from datetime import datetime, timedelta, timezone
from app.database import get_user_by_token
import jwt

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware to allow cross-origin requests
# allows integration with frontend application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9000"],  # Or specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the frontend static files directory
# mount() is used to serve static files from the "frontend_ui" directory
# static files means files like HTML, CSS, JS, images, etc.
app.mount("/frontend", StaticFiles(directory="frontend_ui", html=True), name="frontend")

# Initialize password context for hashing passwords
# CryptContext is used to handle password hashing and verification
# bcrypt is a secure hashing algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- LOGIN ENDPOINT ---
# handles user login using OAuth2PasswordRequestForm
# OAuth2PasswordRequestForm is a standard form for username and password
# it checks the provided credentials against the database
# Depends() is used to inject dependencies into the endpoint
# dependency injction means that FastAPI will automatically provide the required dependencies
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await get_user_by_token(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    payload = {
        "sub": user["username"],
        "roles": user["roles"],
        "departments": user["departments"],
        "access_tags": user["access_tags"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}



# --- BULK PDF UPLOAD ENDPOINT ---
# File is used to handle file uploads
# Form is used to handle form data (like access tags)
@app.post("/upload")
async def upload_pdfs(
    files: List[UploadFile] = File(...),
    mode : str = Form(...),
    access_tags: List[str] = Form(None),
    user=Depends(get_current_user)
):
    if not user:
        raise HTTPException(status_code=401)
    # Only allow users with 'admin' access to upload
    if "admin" not in user["access_tags"]:
        raise HTTPException(status_code=403, detail="You are not authorized to upload documents.")

    if mode == "auto":
        access_tags = None

    elif mode == "manual":
        pass

    # Save uploaded files to disk
    filepaths = []
    for file in files:
        filepath = f"./uploads/{file.filename}"
        with open(filepath, "wb") as f:
            f.write(await file.read())
        filepaths.append(filepath)

    task = f"Please ingest pdfs whose pdf paths and access_tags have been passed.. "
    result = await orchestrator.plan(task = task, user = user, access_tags = access_tags, file_paths=filepaths)
    return {"result: ", result}

# Endpoint to ask questions
# gets current user from JWT token, checks if user is authenticated,
# if not authenticated, raises HTTP 401 error,
# and then processes the question to the RAG engine
@app.post("/ask")
async def ask_question(request: QueryRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401)
    
    task = (
        f"You are a query agent.\n"
        f"The user object is: {user}\n"
        f"Please answer the following question: '{request.query}'\n"
        f"Use your tools as needed to follow RBAC filtering before answering."
    )
    result = await orchestrator.plan(task=task, user=user)
    return {"result: ", result}
    
    
    #return await generate_answer(request.query, user)
    #return await generate_answer2(request.query, user)
    #return await generate_answer3(request.query, user)
    #return await generate_answer4(request.query, user)


#################################################################################
# 
# # main.py
# import uvicorn
# from fastapi import FastAPI, UploadFile, Form
# from mcp_app import orchestrator

# app = FastAPI()

#@app.post("/upload")
# async def upload_pdfs(
#     files: List[UploadFile] = File(...),
#     access_tags: List[str] = Form(...),
#     user=Depends(get_current_user)
# ):
#     if not user:
#         raise HTTPException(status_code=401)
#     # Only allow users with 'admin' access to upload
#     if "admin" not in user["access_tags"]:
#         raise HTTPException(status_code=403, detail="You are not authorized to upload documents.")
#     return await ingest_pdfs(files, access_tags, user)

# @app.post("/ask")
# async def ask_question(user: str = Form(...), query: str = Form(...)):
#     task = f"Please answer: '{query}'"
#     result = await orchestrator.plan(task=task, user=user)
#     return {"result": result}

# if __name__ == "__main__":
#     uvicorn.run(app, host="localhost", port=9000)
    
