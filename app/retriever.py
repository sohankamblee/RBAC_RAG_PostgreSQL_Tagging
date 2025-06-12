# app/retriever.py

from app.auth import get_current_user
from app.database import get_documents_by_filter
from fastapi import Depends, HTTPException
from app.embedder import embed_query_to_vector, embed_doc 
from langchain_community.vectorstores import Chroma
from app.vector_store import chroma_client
import uuid

# Function to retrieve documents based on the current user’s roles, departments, and access tags
async def retrieve_documents_by_filter(user=Depends(get_current_user)):
    # User details: roles, departments, tags
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized user")

    # Apply RBAC and data-level access filtering using the user's metadata
    user_filters = {
        "roles": user["roles"],
        "departments": user["departments"],
        "access_tags": user["access_tags"],
    }

    # Fetch documents from database with RBAC filters
    documents = await get_documents_by_filter(user_filters)

    return documents


async def retrieve_context_by_search(query:str, filtered_docs):
    #filtered_vectors = embed_doc(" ".join(doc["content"] for doc in filtered_docs))
    
    if not filtered_docs:
        return ""

    # Embed the query
    query_vector = embed_query_to_vector(query)

    #  Prepare content + embeddings of filtered docs
    doc_texts = [doc["content"] for doc in filtered_docs]
    doc_ids = [f"temp_{i}" for i in range(len(filtered_docs))]
    doc_embeddings = embed_doc(doc_texts)

    # creating a temporary collection in ChromaDB
    temp_collection_name = f"temp_filtered_context_{uuid.uuid4()}"
    temp_collection = chroma_client.get_or_create_collection(temp_collection_name)

    # Add documents to the temporary collection
    temp_collection.add(
        documents=doc_texts,
        embeddings=doc_embeddings,
        ids=doc_ids
    )

    # Perform semantic similarity search
    result = temp_collection.query(
        query_embeddings=[query_vector],
        n_results=5,  # Top K documents
        include=["documents"]
    )

    # Clean up: delete the temp collection
    chroma_client.delete_collection(temp_collection_name)

    top_docs = result.get("documents", [[]])[0]
    context_string = "\n".join(top_docs)
    return context_string
