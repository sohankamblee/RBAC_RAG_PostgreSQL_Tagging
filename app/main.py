# main.py
from fastapi import FastAPI, Depends, HTTPException
from app.auth import get_current_user
from app.models import QueryRequest, UploadRequest
from app.rag_engine import generate_answer
from app.doc_ingestor import ingest_document
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
    allow_origins=["*"],  # Or specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the frontend static files directory
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

# Initialize password context for hashing passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- LOGIN ENDPOINT ---
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


# Endpoint to upload documents
# gets current user from JWT token, checks if user is authenticated,
# if not authenticated, raises HTTP 401 error, 
# and then processes the document upload
# upload access is restricted to users with 'admin' access tag
@app.post("/upload")
async def upload_doc(request: UploadRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401)
    if "admin" not in user["access_tags"]:
        raise HTTPException(status_code=403, detail="You are not authorized to upload documents.")
    return await ingest_document(request, user)

# Endpoint to ask questions
# gets current user from JWT token, checks if user is authenticated,
# if not authenticated, raises HTTP 401 error,
# and then processes the question to the RAG engine
@app.post("/ask")
async def ask_question(request: QueryRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401)
    return await generate_answer(request.query, user)