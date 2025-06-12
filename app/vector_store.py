import chromadb

chroma_client = chromadb.PersistentClient(path="./chroma_store")

# Create or load a collection
chroma_collection = chroma_client.get_or_create_collection(name="documents")

