"""Cross-encoder reranker: reads the question and one chunk TOGETHER and scores how well the chunk answers it."""
from functools import lru_cache

from app.config import RERANK_MODEL


@lru_cache(maxsize=1)
def get_model():
    from fastembed.rerank.cross_encoder import TextCrossEncoder  # imported here so tests and RERANK=0 never load it

    return TextCrossEncoder(model_name=RERANK_MODEL)


def rerank(question: str, hits: list[dict], top_k: int) -> list[dict]:
    """Re-order candidate chunks by relevance to the question and keep the best `top_k`."""
    if len(hits) <= 1:
        return hits[:top_k]
    scores = list(get_model().rerank(question, [hit["text"] for hit in hits]))
    ranked = sorted(zip(scores, hits), key=lambda pair: pair[0], reverse=True)
    return [{**hit, "score": round(float(score), 4)} for score, hit in ranked[:top_k]]