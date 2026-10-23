from functools import lru_cache

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_SIZE = 384  # this model turns every text into 384 numbers


@lru_cache(maxsize=1)
def get_model():
    """Load the model once (the first call downloads ~90 MB, later calls are instant)."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    vectors = get_model().encode(texts, normalize_embeddings=True, batch_size=32)
    return vectors.tolist()


def embed_query(question: str) -> list[float]:
    return embed_texts([question])[0]