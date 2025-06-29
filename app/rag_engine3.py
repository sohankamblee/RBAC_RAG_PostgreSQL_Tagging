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
    temperature=0.3  
)

# Generate answer using RBAC-filtered ChromaDB docs
async def generate_answer3(query: str, user):
    THRESHOLD = 0.6
    logger.info(f"Received query: {query}")
    query_embedding = embed_query_to_vector(query)
    logger.info("Query embedding generated.")

    # Vector search in ChromaDB
    results = chroma_collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    scores = results.get("distances", [[]])[0] 
    logger.info(f"ChromaDB query returned {len(docs)} docs.")

    # Build context with access_tags attached
    context_parts = []
    for i, (doc, meta, score) in enumerate(zip(docs, metas, scores)):
        doc_access_tags = meta.get("access_tags", "")
        if score <= THRESHOLD:
            context_parts.append(
            f"\n\n\n\n\n\n\n\n[Access Tags: {doc_access_tags}]\n{doc}"
            )
            logger.info(f"Doc {i} access_tags: {doc_access_tags} | Content: {doc[:80]}")
        else:
            logger.info(f"Doc {i} score {score:.4f} exceeds threshold, skipping.")
        
        

    context = "\n\n".join(context_parts)
    logger.info(f"Context for LLM:\n{context}")
    print("\n\nContext for LLM:\n", context)

    # Prepare prompt for LLM to do RBAC
    prompt_template = PromptTemplate.from_template(
        template="""
You are a company assistant with strict RBAC (Role-Based Access Control) rules.

Below is a list of context chunks retrieved from company documents. Each chunk is preceded by its [Access Tags: ...] line.

The user has the following access tags: {user_access_tags}

For each chunk (separated by \n\n\n\n\n\n), if the user_access_tags do NOT overlap (match) with any of the chunk's access tags, you MUST NOT use that chunk to answer the query. 
If none of the chunks are accessible, reply with exactly: "Sorry, you are not authorized to access this info."

If one or more chunk is accessible (access tags overlap), answer the user's query **strictly using only** the accessible context chunks. Do not use any external or general knowledge. If the answer is not explicitly stated in the accessible context, reply with: "Sorry, this information is not available."

User Query: {query}

Context Chunks:
{context}
"""
    )

    final_prompt = prompt_template.invoke({
        'query': query,
        'context': context,
        'user_access_tags': ", ".join(user["access_tags"])
    })
    logger.info(f"Final prompt sent to LLM:\n{final_prompt}")
    print("\n\nFinal prompt sent to LLM:\n", final_prompt)

    response = llm.invoke(final_prompt)
    logger.info(f"LLM response: {response.strip()}")
    print("\n\nLLM response:", response.strip())
    return response.strip()