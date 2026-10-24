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


def search(query_vector: list[float], top_k: int = 5, doc_id: str | None = None,
           doc_ids: list[str] | None = None) -> list[dict]:
    """Find the closest chunks. Optionally search only inside one or several documents."""
    ids = doc_ids or ([doc_id] if doc_id else None)
    query_filter = None
    if ids:
        query_filter = models.Filter(
            must=[models.FieldCondition(key="doc_id", match=models.MatchAny(any=ids))]
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

def delete_document_chunks(doc_id: str) -> None:
    """Remove every chunk of one document from Qdrant."""
    get_client().delete(
        collection_name=COLLECTION,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))]
            )
        ),
    )

def first_chunks(doc_id: str, n: int = 2) -> list[dict]:
    """The first `n` chunks of page 1 (title and abstract), without any search."""
    points, _ = get_client().scroll(
        collection_name=COLLECTION,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id)),
                models.FieldCondition(key="page", match=models.MatchValue(value=1)),
            ]
        ),
        limit=50,
        with_payload=True,
    )
    chunks = sorted((p.payload for p in points), key=lambda c: c["chunk_index"])
    return [{"score": 1.0, **c} for c in chunks[:n]]