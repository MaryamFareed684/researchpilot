import pymupdf
import pytest
from fastapi.testclient import TestClient

from app import llm
from app.config import UPLOAD_DIR
from app.main import app

client = TestClient(app)

PLANTS = "Photosynthesis is the process by which green plants convert sunlight into chemical energy using chlorophyll."
ROMANS = "The Roman Empire built roads, aqueducts and large stone bridges across Europe during antiquity."


def make_pdf(text):
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_textbox(pymupdf.Rect(72, 72, 540, 760), text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


def upload(name, text):
    r = client.post("/upload", files={"file": (name, make_pdf(text), "application/pdf")})
    assert r.status_code == 200
    return r.json()["doc_id"]


@pytest.fixture()
def two_docs():
    return upload("plants.pdf", PLANTS), upload("romans.pdf", ROMANS)


@pytest.fixture()
def captured(monkeypatch):
    """Replace the LLM with a fake that remembers the prompt it was given."""
    box = {}

    def fake(messages):
        box["messages"] = messages
        return "Some supported statement [1]."

    monkeypatch.setattr(llm, "generate", fake)
    return box


def test_library_lists_uploaded_documents(two_docs):
    docs = client.get("/documents").json()["documents"]
    names = {d["doc_name"] for d in docs}
    assert {"plants.pdf", "romans.pdf"} <= names
    plants = next(d for d in docs if d["doc_name"] == "plants.pdf")
    assert plants["total_pages"] == 1 and plants["chunks"] >= 1


def test_delete_removes_everything(two_docs):
    plants_id, _ = two_docs
    assert (UPLOAD_DIR / f"{plants_id}.pdf").exists()
    assert client.delete(f"/documents/{plants_id}").status_code == 200

    ids = {d["doc_id"] for d in client.get("/documents").json()["documents"]}
    assert plants_id not in ids                                   # registry row gone
    found = client.post("/search", json={"question": "plants sunlight chlorophyll", "doc_id": plants_id}).json()
    assert found["results"] == []                                 # chunks gone
    assert not (UPLOAD_DIR / f"{plants_id}.pdf").exists()         # file gone
    assert client.delete(f"/documents/{plants_id}").status_code == 404


def test_delete_rejects_strange_ids():
    assert client.delete("/documents/not-a-real-id").status_code == 404
    assert client.delete("/documents/..%2F..%2Fsecret").status_code in (404, 405)


def test_ask_several_documents_gives_each_a_share(two_docs, captured):
    r = client.post("/ask", json={"question": "plants sunlight and roman roads", "doc_ids": list(two_docs), "top_k": 2})
    names = {s["doc_name"] for s in r.json()["sources"]}
    assert names == {"plants.pdf", "romans.pdf"}


def test_summary_uses_only_that_paper(two_docs, captured):
    plants_id, _ = two_docs
    r = client.post("/summarize", json={"doc_id": plants_id})
    body = r.json()
    assert r.status_code == 200 and body["status"] == "answered"
    assert body["doc_name"] == "plants.pdf"
    system, user = captured["messages"][0]["content"], captured["messages"][1]["content"]
    for heading in ("## Methodology", "## Datasets", "## Main findings", "## Limitations"):
        assert heading in system
    assert "chlorophyll" in user and "Roman" not in user         # no mixing of papers


def test_summary_of_unknown_document_is_404():
    assert client.post("/summarize", json={"doc_id": "0" * 32}).status_code == 404


def test_compare_shows_both_papers_to_the_model(two_docs, captured):
    r = client.post("/compare", json={"doc_ids": list(two_docs), "focus": "what is described"})
    assert r.status_code == 200 and r.json()["status"] == "answered"
    user = captured["messages"][1]["content"]
    assert "plants.pdf" in user and "romans.pdf" in user
    assert "chlorophyll" in user and "aqueducts" in user


def test_compare_input_rules(two_docs):
    a, b = two_docs
    assert client.post("/compare", json={"doc_ids": [a], "focus": "anything"}).status_code == 422
    assert client.post("/compare", json={"doc_ids": [a, a], "focus": "anything"}).status_code == 400
    assert client.post("/compare", json={"doc_ids": [a, "0" * 32], "focus": "anything"}).status_code == 404


def test_reupload_repairs_the_library():
    """A paper that is already indexed is still (re)registered in the library."""
    from app import db

    data = make_pdf("Octopuses have three hearts and blue blood, and they can change colour quickly.")
    first = client.post("/upload", files={"file": ("octopus.pdf", data, "application/pdf")}).json()
    db.delete_document(first["doc_id"])  # pretend the library lost it
    again = client.post("/upload", files={"file": ("octopus.pdf", data, "application/pdf")}).json()
    assert again["already_indexed"] is True
    assert first["doc_id"] in {d["doc_id"] for d in client.get("/documents").json()["documents"]}


def test_uncited_sentences_are_found():
    from app.rag import find_uncited_sentences

    answer = (
        "## Paper A\n"
        "Paper A measures accuracy on a held-out set of instances [1]. "
        "It also reports a second metric that nobody cited anywhere.\n"
        "- Another claim with a citation placed after the full stop. [2]\n"
        "## Methodology\nNot stated in the retrieved passages.\n"
    )
    assert find_uncited_sentences(answer) == ["It also reports a second metric that nobody cited anywhere."]


def test_partially_cited_status(two_docs, monkeypatch):
    monkeypatch.setattr(llm, "generate", lambda m: "Plants make energy from light [1]. This sentence has no citation at all.")
    body = client.post("/ask", json={"question": "How do plants use sunlight?", "doc_ids": [two_docs[0]]}).json()
    assert body["status"] == "partially_cited"
    assert body["uncited_sentences"] == ["This sentence has no citation at all."]


def test_summary_starts_with_the_first_page(two_docs, captured):
    client.post("/summarize", json={"doc_id": two_docs[0]})
    user = captured["messages"][1]["content"]
    assert "[1] (plants.pdf, page 1)" in user  # source number 1 is the paper's opening chunk