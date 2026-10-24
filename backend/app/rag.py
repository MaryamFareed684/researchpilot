import re

from app import embeddings, llm, vector_store
from app.config import CONTEXT_CHUNKS
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


def answer_question(question: str, doc_id: str | None = None, top_k: int = CONTEXT_CHUNKS) -> dict:
    # 1. Retrieve the best chunks
    hits = vector_store.search(embeddings.embed_query(question), top_k=top_k, doc_id=doc_id)
    if not hits:
        return {"answer": NO_EVIDENCE, "status": "no_evidence", "citations": [],
                "invalid_citations": [], "sources": []}

    # 2. Ask the LLM, using only those chunks
    answer = normalize_brackets(llm.generate(build_messages(question, hits)))

    # 3. Turn [n] into real citations (doc name, page, passage) using OUR data
    cited = extract_citation_numbers(answer)
    valid = [n for n in cited if 1 <= n <= len(hits)]
    invalid = [n for n in cited if n not in valid]
    citations = [
        {"n": n, "doc_name": hits[n - 1]["doc_name"], "page": hits[n - 1]["page"], "text": hits[n - 1]["text"]}
        for n in valid
    ]

    # 4. Decide the status
    if "do not contain enough evidence" in answer.lower():
        status = "no_evidence"
        citations = []
    elif valid and not invalid:
        status = "answered"
    else:
        status = "unverified"  # no citation, or it cited a source that does not exist

    sources = [{"n": i, "doc_name": h["doc_name"], "page": h["page"], "score": h["score"]}
               for i, h in enumerate(hits, start=1)]
    return {"answer": answer, "status": status, "citations": citations,
            "invalid_citations": invalid, "sources": sources}