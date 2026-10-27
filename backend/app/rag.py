import math
import re

from app import embeddings, hybrid, llm, vector_store
from app.config import CONTEXT_CHUNKS, SEARCH_MODE


from app.prompts import NO_EVIDENCE, build_messages

# matches [1], [12], and also [1, 2]
_CITATION = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")

# Some models write citations with other bracket styles, like 【4】. Convert them to [4].
_BRACKETS = str.maketrans({"【": "[", "】": "]", "［": "[", "］": "]"})


def normalize_brackets(answer: str) -> str:
    return answer.translate(_BRACKETS)


def extract_citation_numbers(answer: str) -> list[int]:
    """Return the source numbers the answer cites, in order, without repeats."""
    numbers = []
    for match in _CITATION.finditer(normalize_brackets(answer)):
        for part in match.group(1).split(","):
            n = int(part)
            if n not in numbers:
                numbers.append(n)
    return numbers


_ONLY_CITATIONS = re.compile(r"(\[\d+(?:\s*,\s*\d+)*\]\s*)+")


def find_uncited_sentences(answer: str) -> list[str]:
    """Sentences that state something but carry no [n] citation.

    Headings, very short fragments and the standard "Not stated..." line are ignored.
    """
    answer = normalize_brackets(answer)
    pieces = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", answer) if s.strip()]
    sentences = []  # [text, has_citation]
    for piece in pieces:
        if _ONLY_CITATIONS.fullmatch(piece):          # a lone "[3]" belongs to the sentence before it
            if sentences:
                sentences[-1][1] = True
            continue
        text = piece.lstrip("-*• ").strip()
        if text.startswith("#") or len(text) < 25 or "not stated in the retrieved" in text.lower():
            continue
        sentences.append([text, bool(_CITATION.search(piece))])
    return [text for text, cited in sentences if not cited]


def retrieve(question: str, query_vector: list[float], top_k: int, doc_ids: list[str] | None = None) -> list[dict]:
    """One place that decides how we search: SEARCH_MODE=vector or hybrid."""
    if SEARCH_MODE == "hybrid":
        return hybrid.search(question, query_vector, top_k=top_k, doc_ids=doc_ids)
    return vector_store.search(query_vector, top_k=top_k, doc_ids=doc_ids)


def retrieve_per_document(query_vector: list[float], doc_ids: list[str], per_doc_k: int,
                          question: str = "") -> list[dict]:
    """The quota: take the best `per_doc_k` chunks from EACH document,
    so that no single paper can crowd out the others."""
    hits = []
    for doc_id in doc_ids:
        hits.extend(retrieve(question, query_vector, per_doc_k, [doc_id]))
    return hits


def no_evidence_result() -> dict:
    return {"answer": NO_EVIDENCE, "status": "no_evidence", "citations": [],
            "invalid_citations": [], "uncited_sentences": [], "sources": []}


def build_result(answer: str, hits: list[dict]) -> dict:
    """Check the citations in an LLM answer against the sources we gave it."""
    answer = normalize_brackets(answer)

    # Turn [n] into real citations (doc name, page, passage) using OUR data
    cited = extract_citation_numbers(answer)
    valid = [n for n in cited if 1 <= n <= len(hits)]
    invalid = [n for n in cited if n not in valid]
    citations = [
        {"n": n, "doc_name": hits[n - 1]["doc_name"], "page": hits[n - 1]["page"], "text": hits[n - 1]["text"]}
        for n in valid
    ]

    # Decide the status
    uncited = find_uncited_sentences(answer)
    if "do not contain enough evidence" in answer.lower():
        status = "no_evidence"
        citations = []
        uncited = []
    elif not valid or invalid:
        status = "unverified"         # no citation at all, or it cited a source that does not exist
    elif uncited:
        status = "partially_cited"    # some sentences make claims without any citation
    else:
        status = "answered"

    sources = [{"n": i, "doc_name": h["doc_name"], "page": h["page"], "score": h["score"]}
               for i, h in enumerate(hits, start=1)]
    return {"answer": answer, "status": status, "citations": citations,
            "invalid_citations": invalid, "uncited_sentences": uncited[:5], "sources": sources}


def answer_question(question: str, doc_id: str | None = None, doc_ids: list[str] | None = None,
                    top_k: int = CONTEXT_CHUNKS) -> dict:
    ids = doc_ids or ([doc_id] if doc_id else None)
    query_vector = embeddings.embed_query(question)

    # 1. Retrieve. With several documents, every document gets its own share.
    if ids and len(ids) > 1:
        hits = retrieve_per_document(query_vector, ids, max(1, math.ceil(top_k / len(ids))), question)
    else:
        hits = retrieve(question, query_vector, top_k, ids)
    if not hits:
        return no_evidence_result()

    # 2. Ask the LLM, using only those chunks, then check its citations
    return build_result(llm.generate(build_messages(question, hits)), hits)