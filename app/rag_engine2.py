import logging
from app.retriever import retrieve_documents_by_filter, retrieve_context_by_search
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM as Ollama
from app.embedder import embed_query_to_vector
from app.vector_store import chroma_collection

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the LLM with Ollama
llm = Ollama(
    model="mistral",
    temperature=0.3  # Lower temperature for more focused responses
)

# Generate answer using RBAC-filtered ChromaDB docs
async def generate_answer2(query: str, user):
    THRESHOLD = 1.0  
    logger.info(f"Received query: {query}")
    query_embedding = embed_query_to_vector(query)
    logger.info("Query embedding generated.")
    # Broad fetch (no RBAC filter in Chroma)
    results = chroma_collection.query(
        query_embeddings=[query_embedding],
        n_results=5  # get more, then filter
    )
    logger.info(f"ChromaDB query results (first element): {results.get('documents', [[]])[0][:1]}")
    print("\n\n\n\n\n\nChromaDB results (first element):", results.get('documents', [[]])[0][:1])

    ########################
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    scores = results.get("distances", [[]])[0] 
    logger.info(f"ChromaDB query returned {len(docs)} docs.")

    # Build context with access_tags attached
    context_parts = []
    for i, (doc, meta, score) in enumerate(zip(docs, metas, scores)):
        doc_tags = set(tag.strip() for tag in meta.get("access_tags", "").split(","))
        logger.debug(f"Doc tags: {doc_tags} | User tags: {set(user['access_tags'])}")
        print(f"Doc {i} : {doc[:100]}\n\n\n\n Doc tags: {doc_tags} | User tags: {set(user['access_tags'])}")
        if set(user["access_tags"]) & doc_tags:
            if score <= THRESHOLD:
                context_parts.append(doc)
            else:
                logger.info(f"Doc {i} score {score:.4f} exceeds threshold, skipping.")
        else:
            logger.info(f"Doc {i} access_tags {doc_tags} do not match user tags {set(user['access_tags'])}, skipping.")     

    if not context_parts:
        response = "Sorry, you are not authorized to access this info."
        print("\n\nLLM response:", response)    
        logger.info(f"LLM response: {response}")
        return response        

    ########################

    # # Manual RBAC filter
    # filtered_docs = []
    # for doc, meta in zip(results.get("documents", [[]])[0], results.get("metadatas", [[]])[0]):
    #     doc_tags = set(tag.strip() for tag in meta.get("access_tags", "").split(","))
    #     logger.debug(f"Doc tags: {doc_tags} | User tags: {set(user['access_tags'])}")
    #     if set(user["access_tags"]) & doc_tags:
    #         filtered_docs.append(doc)
    #     # if len(filtered_docs) >= MAX_CHUNKS:
    #     #     break

    # if not filtered_docs:
    #     response = "Sorry, you are not authorized to access this info."
    #     print("\n\nLLM response:", response)
    #     logger.info(f"LLM response: {response}")
    #     return response
    

    for i, context_part in enumerate(context_parts[:5]):  # Limit to first 5 for logging
        print(f"context part {i}: {context_part[:100]}")

    context = "\n".join(context_parts) 
    logger.info(f"Context for LLM:\n{context}")
    print("\n\n\nContext for LLM:\n", context)

    prompt_template = PromptTemplate.from_template(
        template="""You are a company assistant with strict RBAC (Role-Based Access Control) policies.

If the provided context is empty,
reply with exactly: "Sorry, you are not authorized to access this info."

If context is not empty, answer the user's query STRICTLY USING ONLY the information in the context.

✅ Do not use any external or general knowledge.
🛑 Do not assume, infer, or guess missing details. Simply reply with "This information is not available"

User Query: {query}

Context:
{context}
"""
    )

    final_prompt = prompt_template.invoke({
        'query': query,
        'context': context
    })
    logger.info(f"Final prompt sent to LLM:\n{final_prompt}")
    print("\n\n\n\n\nFinal prompt sent to LLM:\n", final_prompt)

    response = llm.invoke(final_prompt)
    logger.info(f"LLM response: {response.strip()}")
    print("\n\n\n\n\nLLM response:", response.strip())
    return response.strip()