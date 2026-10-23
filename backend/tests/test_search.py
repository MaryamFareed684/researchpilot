import pymupdf
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def pdf_with_pages(texts):
    doc = pymupdf.open()
    for text in texts:
        page = doc.new_page()
        page.insert_textbox(pymupdf.Rect(72, 72, 540, 760), text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


def test_search_returns_the_right_page():
    pdf = pdf_with_pages([
        "Photosynthesis is the process by which green plants convert sunlight into chemical energy using chlorophyll.",
        "The Roman Empire built roads, aqueducts and large stone bridges across Europe during antiquity.",
        "Neural networks learn weights by gradient descent and backpropagation of errors through layers.",
    ])
    up = client.post("/upload", files={"file": ("mix.pdf", pdf, "application/pdf")})
    assert up.status_code == 200
    doc_id = up.json()["doc_id"]

    r = client.post("/search", json={"question": "How do plants use sunlight and chlorophyll?", "top_k": 3, "doc_id": doc_id})
    results = r.json()["results"]
    assert results[0]["page"] == 1
    assert results[0]["doc_name"] == "mix.pdf"

    r = client.post("/search", json={"question": "roman roads and bridges", "doc_id": doc_id})
    assert r.json()["results"][0]["page"] == 2


def test_search_validates_input():
    assert client.post("/search", json={"question": "a"}).status_code == 422
    assert client.post("/search", json={"question": "valid question", "top_k": 99}).status_code == 422