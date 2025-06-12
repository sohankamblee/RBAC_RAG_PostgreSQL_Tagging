from langchain_ollama import OllamaLLM as Ollama

llm = Ollama( 
    model="mistral",
    temperature=0.3  # Lower temperature for more focused responses
    )

response = llm.invoke("What is engineering?")
print(response)