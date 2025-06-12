from app.retriever import retrieve_documents_by_filter, retrieve_context_by_search
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaLLM as Ollama

#llm1 = ChatOpenAI(model='gpt-4o-mini')
llm2 =  Ollama(
            model="mistral",
            temperature=0.3  # Lower temperature for more focused responses
        )


async def generate_answer(query:str,user):
    filtered_docs = await retrieve_documents_by_filter(user) #documents retrieved after RBAC filtering
    
    if not filtered_docs:
        return {"answer": "You are not authorized to access this info."}
    
    context = await retrieve_context_by_search(query,filtered_docs)

    prompt_template = PromptTemplate.from_template(
        template =  """
        You are a company assistant. 
        If the provided context is empty or says the user is 'not authorized', 
        reply with only: "Sorry, you are not authorized to access this info."
        Otherwise, answer the user's query concisely based only on the context.

        User role: {user_role}
        User query: {query}
        Context:
        {context}
        """
    )
    final_prompt = prompt_template.invoke(
        {'user_role': ", ".join(user["roles"]),
         'query':query, 
         'context':context}
    )
    
    response = llm2.invoke(final_prompt)
    return response
