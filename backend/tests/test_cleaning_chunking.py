from app.chunking import make_chunks
from app.cleaning import is_mostly_numbers, remove_repeated_headers


def page(n, text):
    return {"doc_name": "d.pdf", "page": n, "text": text}


def test_repeated_header_is_removed():
    pages = [page(i, f"Published at ICLR 2024\nReal content of page {i} is here.") for i in range(1, 6)]
    cleaned = remove_repeated_headers(pages)
    assert all("ICLR" not in p["text"] for p in cleaned)
    assert "Real content of page 3" in cleaned[2]["text"]


def test_unique_first_line_is_kept():
    pages = [page(i, f"Unique title {i}\nBody {i}") for i in range(1, 6)]
    assert "Unique title 2" in remove_repeated_headers(pages)[1]["text"]


def test_numbers_only_detected():
    assert is_mostly_numbers("6\n4\n17\n3\n6\n-\n23\n4\n15")
    assert not is_mostly_numbers("Models can infer personal attributes from text.")


def test_chunks_keep_page_and_never_cross_pages():
    long_text = "Language models infer personal attributes. " * 60
    chunks = make_chunks([page(2, long_text), page(5, long_text)])
    assert {c["page"] for c in chunks} == {2, 5}
    assert len(chunks) > 2
    assert all(len(c["text"]) <= 900 for c in chunks)


def test_table_of_numbers_is_dropped():
    junk = "\n".join(str(n) for n in range(100))
    assert make_chunks([page(1, junk)]) == []