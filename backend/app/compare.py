from app import embeddings, llm, rag
from app.config import COMPARE_CHUNKS_PER_DOC
from app.prompts import build_compare_messages


def compare_documents(focus: str, docs: list[dict]) -> dict:
    """docs = records from the registry (doc_id, doc_name, ...)."""
    query_vector = embeddings.embed_query(focus)
    hits = rag.retrieve_per_document(query_vector, [d["doc_id"] for d in docs], COMPARE_CHUNKS_PER_DOC)
    if not hits:
        return rag.no_evidence_result()
    messages = build_compare_messages(focus, [d["doc_name"] for d in docs], hits)
    return rag.build_result(llm.generate(messages), hits)