# app/rag_engine_mcp.py
from typing import List, Dict
import httpx

from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM as Ollama

llm = Ollama(
    model="mistral",
    temperature=0.3  # Lower temperature for more focused responses)

)

FASTMCP_ENDPOINT = "http://localhost:8000/mcp"

async def generate_answer(query: str, filtered_docs: List[Dict]) -> str:
    """
    Generates an answer for the user's query based on the provided context documents.
    Args:
        query (str): The user's question or query.
        filtered_docs (List[Dict]): List of documents that the user is authorized to access.
    Returns:
        str: The generated answer based on the context documents.
    If filtered_docs is empty, returns a message indicating no access.
    """
    
    if not filtered_docs:
        return "Sorry, you are not authorized to access this information."

    # Join all document contents
    context = "\n\n".join([doc["content"] for doc in filtered_docs if "content" in doc])

    prompt_template = PromptTemplate.from_template(
        template = """
You are an intelligent assistant helping users with context-based queries.
Only use the context provided below strictly to answer the query. 
Do not use general knowledge or external information.
If context is empty, respond only with "Sorry you are not authorized to access this info." 
Context:
{context}

Query:
{query}
"""
    )

    final_prompt = prompt_template.invoke({
        "context": context,
        "query" : query
    })

    response = f"Final Answer: {llm.invoke(final_prompt)}"

    return response
    

    # # Call FastMCP (async)
    # async with httpx.AsyncClient() as client:
    #     resp = await client.post(FASTMCP_ENDPOINT, json={"prompt": prompt})
    #     return resp.json()["response"]
