import os
import tempfile
import zlib

# Must be set BEFORE the app is imported: use an in-memory Qdrant for tests
os.environ["QDRANT_PATH"] = ":memory:"
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")

import pytest

from app import embeddings


def fake_embed_texts(texts):
    """A tiny stand-in for the real model, so tests are fast and need no download.

    It counts words into 384 buckets, so texts sharing words get similar vectors.
    """
    vectors = []
    for text in texts:
        v = [0.0] * embeddings.VECTOR_SIZE
        for word in text.lower().split():
            v[zlib.crc32(word.encode()) % embeddings.VECTOR_SIZE] += 1.0
        norm = sum(x * x for x in v) ** 0.5 or 1.0
        vectors.append([x / norm for x in v])
    return vectors


@pytest.fixture(autouse=True)
def use_fake_embeddings(monkeypatch):
    monkeypatch.setattr(embeddings, "embed_texts", fake_embed_texts)