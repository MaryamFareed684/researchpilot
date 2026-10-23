from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.cleaning import is_mostly_numbers
from app.config import CHUNK_OVERLAP, CHUNK_SIZE, MIN_CHUNK_CHARS

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def make_chunks(pages: list[dict]) -> list[dict]:
    """Cut each page into chunks. A chunk never crosses a page boundary,
    so every chunk has exactly one page number."""
    chunks = []
    for page in pages:
        for i, piece in enumerate(_splitter.split_text(page["text"])):
            piece = piece.strip()
            if len(piece) < MIN_CHUNK_CHARS or is_mostly_numbers(piece):
                continue  # too short, or a table of numbers
            chunks.append(
                {
                    "doc_name": page["doc_name"],
                    "page": page["page"],
                    "chunk_index": i,
                    "text": piece,
                }
            )
    return chunks