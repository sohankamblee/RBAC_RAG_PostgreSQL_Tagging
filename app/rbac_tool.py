from typing import List, Dict
from app.vector_store import chroma_collection
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

THRESHOLD = 1.0

async def rbac_filter(query: str, user) -> List[Dict[str, str]]:
    """
    Filters Chroma search results using access_tags from user metadata.
    
    Args:
        query (str): User's question/query.
        user (dict): Current authenticated user, should contain access_tags.
        
    Returns:
        List[Dict[str, str]]: List of dicts, each with a 'content' key holding authorized document text.
    """
    logger.info(f"[RBACFilter] Running for query: '{query}' and user tags: {user.get('access_tags')}")

    # Search similar docs from ChromaDB
    search_results = chroma_collection.query(
        query_texts=[query],
        n_results=5,
        include=["metadatas", "documents", "distances"]
    )

    docs = search_results["documents"][0]      # List[str]
    metas = search_results["metadatas"][0]     # List[dict]
    scores = search_results["distances"][0]    # List[float]

    context_parts = []
    user_tags = set(user.get("access_tags", []))

    for i, (doc, meta, score) in enumerate(zip(docs, metas, scores)):
        doc_tags = set(tag.strip() for tag in meta.get("access_tags", "").split(","))
        
        logger.info(f"\nDoc {i} preview: {doc[:100]}...\nTags - Doc: {doc_tags} | User: {user_tags} | Score: {score}")

        if score <= THRESHOLD:
            if doc_tags & user_tags:
                context_parts.append({"content": doc})  # ✅ wrap in dict
            else:
                logger.info(f"[RBACFilter] Doc {i} access_tags {doc_tags} do not match user tags {user_tags}, skipping.")
        else:
            logger.info(f"[RBACFilter] Doc {i} distance score {score:.2f} exceeds threshold ({THRESHOLD}), skipping.")

    logger.info(f"[RBACFilter] Authorized context parts: {len(context_parts)} / {len(docs)}")
    return context_parts
