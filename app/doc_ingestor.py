# app/doc_ingestor_mcp.py

from app.database import store_metadata
from app.embedder import embed_doc
from fastapi import HTTPException, UploadFile
from app.models import UploadRequest
from app.vector_store import chroma_collection
from app.embedder import splitter
from app.auto_tagging import auto_tag_pdf
from langchain_community.document_loaders import PyPDFLoader
import tempfile
import os
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def batch_iterable(iterable, batch_size):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i:i + batch_size]

async def ingest_pdfs(files: list[str], access_tags: list[str] = None, user: dict = {} ):
    # results stores the status of each file processed
    results = []
    
    # batch size for ChromaDB
    # ChromaDB requires batching for efficient ingestion
    BATCH_SIZE = 5000  # ChromaDB safe batch size


    for file in files:

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(await file.read())
                tmp_path = tmp.name

        logger.info(f"Processing file: {file.filename}")
        try:            
            if not access_tags: 
                access_tag = await auto_tag_pdf(tmp_path)

            elif access_tag:
                access_tag = ",".join(access_tags)    

            # Extract text from PDF using LangChain PyPDFLoader
            loader = PyPDFLoader(tmp_path)
            pages = loader.load()
            content = "\n".join([page.page_content for page in pages])
            logger.info(f"Extracted text from {file.filename}, length: {len(content)}")

            if not content.strip():
                logger.warning(f"{file.filename} is empty after extraction.")
                results.append({"filename": file.filename, "status": "failed", "reason": "Empty PDF"})
                continue    

            # text splitting
            chunks = splitter.create_documents([content])
            chunk_texts = [chunk.page_content for chunk in chunks]
            logger.info(f"Split {file.filename} into {len(chunk_texts)} chunks.")

            if not chunk_texts:
                logger.warning(f"No chunks created for {file.filename}.")
                results.append({"filename": file.filename, "status": "failed", "reason": "No chunks"})
                continue

            for i, chunk in enumerate(chunk_texts[:5]):
                logger.info(f"Sample chunk {i}: {chunk[:100]}")

            chunk_embeddings = embed_doc(chunk_texts)
            logger.info(f"Generated embeddings for {file.filename}.")

            if len(chunk_texts) != len(chunk_embeddings):
                logger.error(f"Embedding mismatch for {file.filename}.")
                results.append({"filename": file.filename, "status": "failed", "reason": "Embedding mismatch"})
                continue

            document_id = str(uuid.uuid4())
            metadatas = [{
                "title": file.filename,
                "chunk_index": i,
                "access_tags": access_tag,
                "created_by": user["username"],
                "document_id": document_id
            } for i in range(len(chunk_texts))]
            ids = [f"{document_id}_{i}" for i in range(len(chunk_texts))]

            # Store in ChromaDB in batches
            for chunk_batch, embed_batch, meta_batch, id_batch in zip(
                batch_iterable(chunk_texts, BATCH_SIZE),
                batch_iterable(chunk_embeddings, BATCH_SIZE),
                batch_iterable(metadatas, BATCH_SIZE),
                batch_iterable(ids, BATCH_SIZE)
            ):
                logger.debug(f"Sample metadata: {meta_batch[0]}")
                logger.debug(f"access_tags type: {type(meta_batch[0]['access_tags'])}")

                logger.info(f"Adding batch of {len(chunk_batch)} chunks to ChromaDB for {file.filename}")
                chroma_collection.add(
                    documents=chunk_batch,
                    embeddings=embed_batch,
                    metadatas=meta_batch,
                    ids=id_batch
                )

            results.append({
                "filename": file.filename,
                "status": "success",
                "document_id": document_id,
                "chunks_uploaded": len(chunk_texts)
            })
            logger.info(f"Successfully processed {file.filename}")

        except Exception as e:
            logger.exception(f"Failed to process {file.filename}: {e}")
            results.append({
                "filename": file.filename,
                "status": "failed",
                "reason": str(e)
            })

    return {
        "message": "Upload complete.",
        "results": results
    }