import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app import config


@contextmanager
def _connect():
    """Open the SQLite file, save changes at the end, and always close it."""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dictionaries
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS documents (
                   doc_id       TEXT PRIMARY KEY,
                   doc_name     TEXT NOT NULL,
                   total_pages  INTEGER NOT NULL,
                   chunks       INTEGER NOT NULL,
                   uploaded_at  TEXT NOT NULL
               )"""
        )


def add_document(doc_id: str, doc_name: str, total_pages: int, chunks: int) -> None:
    """Add a document. If the same file is already registered, keep the first record."""
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO documents VALUES (?, ?, ?, ?, ?)",
            (doc_id, doc_name, total_pages, chunks, datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )


def list_documents() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM documents ORDER BY uploaded_at DESC, doc_name").fetchall()
    return [dict(r) for r in rows]


def get_document(doc_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,)).fetchone()
    return dict(row) if row else None


def delete_document(doc_id: str) -> bool:
    """Returns True if a row was removed."""
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
    return cursor.rowcount > 0