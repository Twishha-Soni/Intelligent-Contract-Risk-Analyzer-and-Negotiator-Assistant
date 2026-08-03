from fastembed import SparseTextEmbedding
from qdrant_client import models

_bm25_model = SparseTextEmbedding(model_name='Qdrant/bm25')

def embed_sparse(text: str) -> models.SparseVector:
    result = next(_bm25_model.embed([text]))
    return models.SparseVector(indices=result.indices.tolist(), values=result.values.tolist())