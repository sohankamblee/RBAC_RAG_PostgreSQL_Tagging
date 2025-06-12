import chromadb

# create a persistent ChromaDB client
# PersistentClient allows for storing data on disk
# This client will store the vector embeddings and metadata in a local directory
chroma_client = chromadb.PersistentClient(path="./chroma_store")

# Create or load a collection
# chroma_collection is the collection where documents and their embeddings will be stored
chroma_collection = chroma_client.get_or_create_collection(name="documents")

