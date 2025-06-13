from app.retriever import retrieve_documents_by_filter, retrieve_context_by_search
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM as Ollama

# Initialize the LLM with Ollama
llm =  Ollama(
            model="mistral",
            temperature=0.3  # Lower temperature for more focused responses
        )

# Function to generate an answer based on the user's query and RBAC filtered documents
# function to orchestrate the RAG process
# returns a response which FastAPI will return as JSON response
async def generate_answer(query:str,user):
    # filter documents based on user roles, departments, and access tags
    filtered_docs = await retrieve_documents_by_filter(user) 

    # If no documents are found, return an "unauthorized" message
    if not filtered_docs:
        return {"answer": "You are not authorized to access this info."}
    
    # Retrieve context based on the user's query and the filtered documents
    # retrieve on basis of semantic search
    # returns a context string
    context = await retrieve_context_by_search(query,filtered_docs)

    # prompt template for the LLM involving the user role, query, and context
    prompt_template = PromptTemplate.from_template(
        template =  """
        You are a company assistant. 
        If the provided context is empty or says the user is 'not authorized', 
        reply with only: "Sorry, you are not authorized to access this info."
        Otherwise, answer the user's query concisely based only on the context.

        User query: {query}
        Context:
        {context}
        """
    )
    # final prompt instance by passing user roles, query, and context
    final_prompt = prompt_template.invoke(
        {'user_role': ", ".join(user["roles"]), #user["roles"] is a list, hence joining with comma
         'query':query, 
         'context':context}
    )
    
    # Invoke the LLM with the final prompt and return the response
    response = llm.invoke(final_prompt)
    return response
