from functools import lru_cache

import numpy as np

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_SIZE = 384  # this model turns every text into 384 numbers


@lru_cache(maxsize=1)
def get_model():
    """Load the model once (the first call downloads ~90 MB, later calls are instant).

    fastembed runs the same model with ONNX instead of PyTorch: much smaller and uses less memory.
    """
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    vectors = np.array(list(get_model().embed(texts, batch_size=32)), dtype="float32")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vectors / norms).tolist()  # length 1, so cosine similarity works as before


def embed_query(question: str) -> list[float]:
    return embed_texts([question])[0]