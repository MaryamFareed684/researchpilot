from app import embeddings, llm, rag, vector_store
from app.config import SUMMARY_CHUNKS_PER_ASPECT
from app.prompts import build_summary_messages

# One search question for each part of the summary, phrased the way papers are written
ASPECT_QUERIES = [
    "In this paper we propose and evaluate our approach. Our method and experimental setup.",
    "We use the following datasets and data for our experiments.",
    "Our results show that we find the main findings and conclusion of this work.",
    "Limitations of our work, ethics statement, and future work. We acknowledge that.",
]


def summarize_document(doc_id: str, doc_name: str) -> dict:
    # The abstract is the authors' own summary, so it always comes first
    hits = vector_store.first_chunks(doc_id, n=2)
    seen = {(h["page"], h["chunk_index"]) for h in hits}

    for vector in embeddings.embed_texts(ASPECT_QUERIES):
        for hit in vector_store.search(vector, top_k=SUMMARY_CHUNKS_PER_ASPECT, doc_ids=[doc_id]):
            key = (hit["page"], hit["chunk_index"])
            if key not in seen:  # the same chunk may answer two aspects
                seen.add(key)
                hits.append(hit)
    if not hits:
        return rag.no_evidence_result()
    return rag.build_result(llm.generate(build_summary_messages(doc_name, hits)), hits)