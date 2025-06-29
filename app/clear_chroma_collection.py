from app.vector_store import chroma_collection

def batch_iterable(iterable, batch_size):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i:i + batch_size]

if __name__ == "__main__":
    print("Clearing all documents from ChromaDB collection...")
    all_ids = chroma_collection.get()["ids"]
    if all_ids:
        BATCH_SIZE = 1000
        for batch in batch_iterable(all_ids, BATCH_SIZE):
            chroma_collection.delete(ids=batch)
            print(f"Deleted batch of {len(batch)} documents.")
        print(f"Deleted {len(all_ids)} documents from ChromaDB collection.")
    else:
        print("ChromaDB collection is already empty.")