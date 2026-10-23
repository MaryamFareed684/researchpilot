import pymupdf
from fastapi.testclient import TestClient

from app.main import app
from app.pdf_utils import extract_pages

client = TestClient(app)


def make_pdf(page_texts):
    """Build a small PDF in memory for testing."""
    doc = pymupdf.open()
    for text in page_texts:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_page_numbers_are_kept():
    pdf = make_pdf(["First page text", "", "Third page text"])
    pages, total = extract_pages(pdf, "demo.pdf")
    assert total == 3
    assert [p["page"] for p in pages] == [1, 3]  # empty page 2 skipped, numbers kept
    assert pages[1]["doc_name"] == "demo.pdf"


def test_upload_ok():
    pdf = make_pdf(["Hello RAG, this page is long enough to become a chunk.", "Second page, also long enough to become a chunk."])
    r = client.post("/upload", files={"file": ("a.pdf", pdf, "application/pdf")})
    assert r.status_code == 200
    body = r.json()
    assert body["total_pages"] == 2 and "Hello RAG" in body["preview"]


def test_rejects_non_pdf_name():
    r = client.post("/upload", files={"file": ("a.txt", b"hi", "text/plain")})
    assert r.status_code == 400


def test_rejects_fake_pdf():
    r = client.post("/upload", files={"file": ("a.pdf", b"not a pdf", "application/pdf")})
    assert r.status_code == 400


def test_rejects_scanned_pdf():
    pdf = make_pdf([""])
    r = client.post("/upload", files={"file": ("a.pdf", pdf, "application/pdf")})
    assert r.status_code == 422