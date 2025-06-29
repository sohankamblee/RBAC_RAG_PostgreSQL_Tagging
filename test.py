from langchain_ollama import OllamaLLM as Ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.embedder import embed_query_to_vector,embedding_model
from langchain_community.vectorstores import Chroma

query = "What is the procedure for referring an employee at ACME Corp?"

llm = Ollama( 
    model="mistral",
    temperature=0.3  # Lower temperature for more focused responses
    )

loader = PyPDFLoader("Employee_Referral_Policy_ACME.pdf")

pages = loader.load()
content = "\n".join([page.page_content for page in pages])

print("Extracted content:", content[:500])  # Print first 500 chars

# ...existing code...

splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
chunks = splitter.create_documents([content])

print(f"Number of chunks: {len(chunks)}")
for i, chunk in enumerate(chunks):
    print(f"Chunk {i} (first 100 chars): {chunk.page_content[:100]}")

import uuid
collection_name = f"audit_logs_collection_{uuid.uuid4()}"
chroma_collection2 = Chroma.from_documents(
    documents=chunks,
    embedding=embedding_model,
    collection_name=collection_name,
    persist_directory="chroma_db_test"
)

query_embedding = embed_query_to_vector(query)

docs = chroma_collection2.similarity_search_by_vector(
    embedding=query_embedding,
    k=10
)
print(f"Retrieved {len(docs)} docs from Chroma.")
for i, doc in enumerate(docs):
    print(f"Doc {i} (first 100 chars): {doc.page_content[:100]}")

context = "\n".join(doc.page_content for doc in docs) if docs else ""
print("Context:", context)
# ...rest of your code...
template = PromptTemplate.from_template(
    template=""" You are an AI assistant.
    Based on the provided context, answer the user's query.
    If the context is empty or does not contain relevant information, reply with: "Sorry, this information is not available."
    User Query: {query}
    Context:    {context}   
    """
    )



final_prompt = template.invoke({
        'query': query,
        'context': context
    })
response = llm.invoke(final_prompt)
print("\n\n\n\n Response:", response.strip())