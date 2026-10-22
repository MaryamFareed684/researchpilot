import pymupdf  # this is PyMuPDF


class PDFError(Exception):
    """Raised when a file cannot be read as a PDF."""


def extract_pages(pdf_bytes: bytes, doc_name: str) -> tuple[list[dict], int]:
    """Read a PDF. Returns (pages, total_pages).

    pages = one dictionary per page that has text.
    Each item: {"doc_name": "paper.pdf", "page": 4, "text": "We trained ..."}
    Page numbers start at 1, like the numbers a human sees.
    """
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise PDFError("Could not open this file as a PDF.") from exc

    pages = []
    with doc:
        for index, page in enumerate(doc):
            text = page.get_text("text").strip()
            if not text:
                continue  # empty or scanned page: nothing to read
            pages.append({"doc_name": doc_name, "page": index + 1, "text": text})
        total_pages = len(doc)
    return pages, total_pages