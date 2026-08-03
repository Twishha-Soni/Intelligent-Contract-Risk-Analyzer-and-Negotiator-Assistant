from sentence_transformers import SentenceTransformer

_dense_model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_dense(text: str) -> list[float]:
    return _dense_model.encode(text, normalize_embeddings=True).tolist()