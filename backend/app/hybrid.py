"""Hybrid search: vector (meaning) + BM25 (exact words), merged with Reciprocal Rank Fusion."""
import re

from qdrant_client import models
from rank_bm25 import BM25Okapi

from app import vector_store

RRF_K = 60  # the standard constant in 1 / (RRF_K + rank)

_TOKEN = re.compile(r"[a-z0-9]+(?:[.,][0-9]+)*")
_STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "to", "and", "or", "is", "are", "was", "were", "did", "do",
    "does", "what", "which", "who", "how", "many", "much", "for", "by", "with", "as", "at", "from",
    "that", "this", "it", "its", "be", "used", "use",
}


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOPWORDS]


# The BM25 index is rebuilt only when the number of stored chunks changes
# (an upload or a delete changes it), so it is never stale.
_cache: dict = {"count": -1, "chunks": [], "bm25": None}


def _all_chunks() -> list[dict]:
    chunks, offset = [], None
    while True:
        points, offset = vector_store.get_client().scroll(
            collection_name=vector_store.COLLECTION, limit=500, offset=offset, with_payload=True
        )
        chunks.extend(p.payload for p in points)
        if offset is None:
            return chunks


def _index():
    count = vector_store.get_client().count(collection_name=vector_store.COLLECTION, exact=True).count
    if _cache["count"] != count:
        chunks = _all_chunks()
        corpus = [tokenize(c["text"]) or ["_"] for c in chunks]
        _cache.update(count=count, chunks=chunks, bm25=BM25Okapi(corpus) if chunks else None)
    return _cache["chunks"], _cache["bm25"]


def keyword_search(question: str, top_k: int, doc_ids: list[str] | None = None) -> list[dict]:
    chunks, bm25 = _index()
    tokens = tokenize(question)
    if not chunks or not tokens:
        return []
    scores = bm25.get_scores(tokens)
    ranked = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)
    hits = []
    for i in ranked:
        if scores[i] <= 0:
            break
        if doc_ids and chunks[i]["doc_id"] not in doc_ids:
            continue
        hits.append({"score": round(float(scores[i]), 4), **chunks[i]})
        if len(hits) == top_k:
            break
    return hits


def _key(hit: dict) -> tuple:
    return (hit["doc_id"], hit["page"], hit["chunk_index"])


def fuse(rankings: list[list[dict]], top_k: int) -> list[dict]:
    """Reciprocal Rank Fusion: each list gives a chunk 1 / (60 + rank); the scores add up."""
    scores: dict[tuple, float] = {}
    chunks: dict[tuple, dict] = {}
    for ranking in rankings:
        for rank, hit in enumerate(ranking, start=1):
            k = _key(hit)
            scores[k] = scores.get(k, 0.0) + 1.0 / (RRF_K + rank)
            chunks[k] = hit
    best = sorted(scores, key=scores.get, reverse=True)[:top_k]
    return [{**chunks[k], "score": round(scores[k], 4)} for k in best]


def search(question: str, query_vector: list[float], top_k: int = 5,
           doc_ids: list[str] | None = None) -> list[dict]:
    pool = max(top_k * 4, 20)  # let each method nominate more than we finally keep
    by_meaning = vector_store.search(query_vector, top_k=pool, doc_ids=doc_ids)
    by_words = keyword_search(question, pool, doc_ids)
    return fuse([by_meaning, by_words], top_k)