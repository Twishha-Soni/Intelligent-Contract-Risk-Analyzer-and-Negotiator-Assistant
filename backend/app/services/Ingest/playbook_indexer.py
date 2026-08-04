# services/playbook_indexer.py
from qdrant_client.models import PointStruct

from app.database.vector_store import get_client, ensure_collection, COLLECTION_NAME
from app.services.Ingest.playbook_chunker import chunk_playbook
from app.services.metadata import classify_category
from app.models.playbook_chunk import PlaybookChunk
from app.services.bm25_index import embed_sparse
from app.services.embeddings import embed_dense

def index_playbook(path: str) -> int:
    client = get_client()
    ensure_collection(client)

    chunks = chunk_playbook(path)
    points = []

    for i, chunk in enumerate(chunks):
        category = classify_category(chunk.section_title, chunk.chunk_text)

        points.append(PointStruct(
            id=i,
            vector={
                'dense': embed_dense(chunk.chunk_text),
                'bm25': embed_sparse(chunk.chunk_text)
            },
            payload={
                'chunk_id': chunk.chunk_id,
                'category': category,
                'section_title': chunk.section_title,
                'chunk_text': chunk.chunk_text,
                'page_number': chunk.page_number
            }
        ))

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


if __name__ == '__main__':
    import sys
    count = index_playbook(sys.argv[1])
    print(f"Indexed {count} playbook chunks into '{COLLECTION_NAME}'")