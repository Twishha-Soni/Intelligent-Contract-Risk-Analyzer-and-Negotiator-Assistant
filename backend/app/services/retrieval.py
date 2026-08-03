from qdrant_client import models

from app.database.vector_store import get_client, COLLECTION_NAME
from app.services.bm25_index import embed_sparse
from app.services.embeddings import embed_dense
from app.services.metadata import classify_category
from app.models.clause import Clause

TOP_K = 5
PREFETCH_LIMIT = 20

def retrieve_playbook_context(clause: Clause, top_k: int = TOP_K) -> list[dict]:
    candidate_category = classify_category(clause.section, clause.clause_text)

    category_filter = models.Filter(
        must=[
            models.FieldCondition(
                key='category',
                match=models.MatchValue(value=candidate_category)
            )
        ]
    )

    results = _hybrid_query(clause.clause_text, category_filter, top_k)
    seen_ids = {r.id for r in results}

    if len(results) < top_k:
        backfill = _hybrid_query(clause.clause_text, None, top_k - len(results))
        for r in backfill:
            if r.id not in seen_ids:
                results.append(r)
                seen_ids.add(r.id)

    return [
        {
            'chunk_id': r.payload['chunk_id'],
            'category': r.payload['category'],
            'section_title': r.payload['section_title'],
            'chunk_text': r.payload['chunk_text'],
            'page_number': r.payload['page_number'],
            'score': r.score
        }
        for r in results
    ]    


def _hybrid_query(clause_text: str, category_filter: models.Filter | None, limit: int):
    client = get_client()
    dense_vec = embed_dense(clause_text)
    sparse_vec = embed_sparse(clause_text)

    return client.query_points(
        collecion_name=COLLECTION_NAME,
        prefetch=[
            models.Prefetch(query=dense_vec, using='dense', limit=PREFETCH_LIMIT, filter=category_filter),
            models.Prefetch(query=sparse_vec, using='bm25', limit=PREFETCH_LIMIT, filter=category_filter)
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=limit
    ).points
