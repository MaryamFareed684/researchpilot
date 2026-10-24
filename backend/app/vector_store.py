import uuid
from functools import lru_cache

from qdrant_client import QdrantClient, models

from app.config import QDRANT_PATH
from app.embeddings import VECTOR_SIZE

COLLECTION = "chunks"


@lru_cache(maxsize=1)
def get_client() -> QdrantClient:
    if QDRANT_PATH == ":memory:":
        client = QdrantClient(":memory:")
    else:
        client = QdrantClient(path=QDRANT_PATH)  # local mode: saved in a folder
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
        )
    return client


def add_chunks(doc_id: str, chunks: list[dict], vectors: list[list[float]]) -> None:
    points = [
        models.PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "doc_id": doc_id,
                "doc_name": chunk["doc_name"],
                "page": chunk["page"],
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
            },
        )
        for chunk, vector in zip(chunks, vectors)
    ]
    get_client().upsert(collection_name=COLLECTION, points=points)


def search(query_vector: list[float], top_k: int = 5, doc_id: str | None = None) -> list[dict]:
    query_filter = None
    if doc_id:
        query_filter = models.Filter(
            must=[models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))]
        )
    hits = get_client().query_points(
        collection_name=COLLECTION,
        query=query_vector,
        limit=top_k,
        query_filter=query_filter,
        with_payload=True,
    ).points
    return [{"score": round(h.score, 4), **h.payload} for h in hits]

def count_document_chunks(doc_id: str) -> int:
    """How many chunks are stored for this document (0 = not indexed yet)."""
    result = get_client().count(
        collection_name=COLLECTION,
        count_filter=models.Filter(
            must=[models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))]
        ),
        exact=True,
    )
    return result.count