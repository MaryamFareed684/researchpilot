from app import embeddings, vector_store
from app.chunking import make_chunks
from app.cleaning import remove_repeated_headers


def index_pages(doc_id: str, pages: list[dict]) -> int:
    """clean -> chunk -> embed -> store. Returns how many chunks were stored."""
    pages = remove_repeated_headers(pages)
    chunks = make_chunks(pages)
    if not chunks:
        return 0
    vectors = embeddings.embed_texts([c["text"] for c in chunks])
    vector_store.add_chunks(doc_id, chunks, vectors)
    return len(chunks)