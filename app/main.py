# main.py
from fastapi import FastAPI, Depends, HTTPException
from app.auth import get_current_user
from app.models import QueryRequest, UploadRequest
from app.rag_engine import generate_answer
from app.doc_ingestor import ingest_document
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

# Define API endpoints:-

# Endpoint to upload documents
# gets current user from JWT token, checks if user is authenticated,
# if not authenticated, raises HTTP 401 error, 
# and then processes the document upload
@app.post("/upload")
async def upload_doc(request: UploadRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401)
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