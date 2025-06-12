# main.py
from fastapi import FastAPI, Depends, HTTPException
from app.auth import get_current_user
from app.models import QueryRequest, UploadRequest
from app.rag_engine import generate_answer
from app.doc_ingestor import ingest_document

app = FastAPI()

@app.post("/upload")
async def upload_doc(request: UploadRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401)
    return await ingest_document(request, user)

@app.post("/ask")
async def ask_question(request: QueryRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401)
    return await generate_answer(request.query, user)