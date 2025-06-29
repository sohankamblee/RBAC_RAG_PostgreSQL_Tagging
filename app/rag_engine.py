from app.retriever import retrieve_documents_by_filter, retrieve_context_by_search
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM as Ollama
from app.embedder import embed_query_to_vector
from app.vector_store import chroma_collection

# Initialize the LLM with Ollama
llm =  Ollama(
            model="mistral",
            temperature=0.3  # Lower temperature for more focused responses
        )

# Function to generate an answer based on the user's query and RBAC filtered documents
# function to orchestrate the RAG process
# returns a response which FastAPI will return as JSON response
# Generate answer using RBAC-filtered ChromaDB docs
async def generate_answer(query: str, user):
    # Embed the query
    query_embedding = embed_query_to_vector(query)
    # RBAC filter: only docs with matching access_tags and roles
    filter_dict = {
        "$or": [
            {"access_tags": {"$in": user["access_tags"]}},
            {"roles": {"$in": user["roles"]}}
        ]
    }
    results = chroma_collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        where=filter_dict
    )
    docs = results.get("documents", [[]])[0]
    context = "\n".join(docs) if docs else ""

    prompt_template = PromptTemplate.from_template(
        template="""
    You are a company assistant.

    If the provided context is empty or says the user is 'not authorized',
    reply with exactly: "Sorry, you are not authorized to access this info."

    Otherwise, answer the user's query **strictly using only** the information in the context below.

    ✅ Do not use any external or general knowledge.
    🛑 Do not assume, infer, or guess missing details.
    📌 Quote specific facts such as names, job titles, email addresses, dates, and policy instructions exactly as stated in the context.
    🧠 If the answer is not explicitly stated in the context, reply with: "Sorry, this information is not available."

    User Query: {query}

    Context:
    {context}
    """
    )

    final_prompt = prompt_template.invoke({
        'user_role': ", ".join(user["roles"]),
        'query': query,
        'context': context
    })
    response = llm.invoke(final_prompt)
    return response.strip()
