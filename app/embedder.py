from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
splitter = RecursiveCharacterTextSplitter()

def embed_doc(chunk_texts: list[str]) -> list[list[float]]:
    """
    Embed a list of chunk texts and return a list of embedding vectors.
    
    Args:
        chunk_texts (list of str): The document chunks.

    Returns:
        list[list[float]]: Embedding vectors (1 per chunk).
    """
    if not chunk_texts or not isinstance(chunk_texts, list):
        raise ValueError("Input must be a list of strings (chunked texts).")
    doc_embedding_vector = embedding_model.embed_documents(chunk_texts)
    return doc_embedding_vector

def embed_query_to_vector(query:str):
    return embedding_model.embed_query(query)