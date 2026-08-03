from qdrant_client import QdrantClient, models

QDRANT_HOST = 'localhost'
QDRANT_PORT = 6333
COLLECTION_NAME = 'playbook_chunks'
EMBEDDING_DIM = 384

def get_client() -> QdrantClient:
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

def ensure_collection(client: QdrantClient) -> None:
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                'dense': models.VectorParams(size=EMBEDDING_DIM, distance=models.Distance.COSINE)
            },
            sparse_vectors_config={
                'bm25': models.SparseVectorParams(modifier=models.Modifier.IDF)
            }
        )

# if __name__ == '__main__':
#     ensure_collection(get_client())