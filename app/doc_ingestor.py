# doc_ingestor.py

from app.database import store_metadata
from app.embedder import embed_doc
from fastapi import HTTPException
from app.models import UploadRequest
from app.vector_store import chroma_collection
from app.embedder import splitter

# function to ingest a document, chunk it, embed the chunks, and store metadata
async def ingest_document(request: UploadRequest, user):
    # Extract document details from the request
    title = request.title
    content = request.content

    # text splitting
    chunks = splitter.create_documents(content)  

    if not chunks:
        raise HTTPException(status_code=400, detail="Document content is empty or too short to chunk")
    
    # Embed chunks
    chunk_texts = [chunk.page_content for chunk in chunks]
    chunk_embeddings = embed_doc(chunk_texts)  # List[List[float]], one embedding per chunk

    # check if number of embeddings match the number of chunks
    if len(chunk_texts) != len(chunk_embeddings):
        raise HTTPException(status_code=500, detail="Mismatch between chunks and embeddings")
    
    # Prepare metadata (tags, roles, departments) to be stored
    # Assuming user is a dictionary with necessary fields
    # tags stores RBAC tags, roles, departments, and access level
    tags = {
        "departments": user.get("departments", []),
        "roles": user.get("roles", []),
        "access_tags": user.get("access_tags", []),
        "access_level": user.get("access_level", "general_access")  # Default to 'general_access'
    }

    # Prepare user info for metadata storage
    user_info = {
        "id": user["id"]  # Or use user["user_id"] depending on your user model
    }

    # Store metadata (title, content, embedding, user info, tags) in PostgreSQL table document_metadata
    # returns document_id 
    # store embeddings in ChromaDB (vector store) - Persistent storage
    # returns confirmation of successful upload
    try:
          #     Store in PostgreSQL database
        document_id = await store_metadata(title, content, user_info, tags)

          # 🔹 Store in ChromaDB (vector store)
        chroma_collection.add(
            documents=chunk_texts,
            embeddings=chunk_embeddings,
            metadatas=[{
                "title": title,
                "chunk_index": i,
                "departments": ", ".join(tags["departments"]) if tags["departments"] else "",
                "roles": ", ".join(tags["roles"]) if tags["roles"] else "",
                "access_tags": ", ".join(tags["access_tags"]) if tags["access_tags"] else "",
                "access_level": tags["access_level"],
                "created_by": user["username"],
                "document_id": str(document_id)
            } for i in range(len(chunk_texts))],
            ids=[f"{document_id}_{i}" for i in range(len(chunk_texts))]
        )

        return {
            "status": "success",
            "message": "Document uploaded and chunked successfully",
            "document_id": document_id,
            "chunks_uploaded": len(chunk_texts)
        }
    # Handle any exceptions that occur during the process of storing metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing document metadata: {str(e)}")

