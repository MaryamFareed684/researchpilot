import hashlib
import re

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app import compare, db, embeddings, rag, summarize, vector_store
from app.config import MAX_UPLOAD_BYTES, MAX_UPLOAD_MB, UPLOAD_DIR
from app.llm import LLMError
from app.pdf_utils import PDFError, extract_pages
from app.pipeline import index_pages

app = FastAPI(title="ResearchPilot")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
db.init_db()


@app.exception_handler(LLMError)
async def llm_error_handler(request: Request, exc: LLMError):
    """Any LLM problem becomes a clean JSON error with the right status code."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------- upload

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    # 1. Check the file name
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are allowed.")

    # 2. Read the file, but never more than the limit (+1 byte to detect "too big")
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File is larger than {MAX_UPLOAD_MB} MB.")

    # 3. A real PDF always starts with these 5 bytes
    if not data.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="This is not a real PDF file.")

    # 4. Extract text page by page
    try:
        pages, total_pages = extract_pages(data, file.filename)
    except PDFError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not pages:
        raise HTTPException(status_code=422, detail="No text found. This may be a scanned PDF (images only).")

    # 5. The document id is a fingerprint of the file's content, so the same
    #    file always gets the same id and is never indexed twice
    doc_id = hashlib.sha256(data).hexdigest()[:32]
    already_indexed = vector_store.count_document_chunks(doc_id)
    if already_indexed:
        chunks_indexed = already_indexed
    else:
        # Clean -> chunk -> embed -> store in Qdrant (heavy work, so off the main thread)
        chunks_indexed = await run_in_threadpool(index_pages, doc_id, pages)
        if chunks_indexed == 0:
            raise HTTPException(status_code=422, detail="No usable text chunks found in this PDF.")

    # 6. Save the original file and add it to the library
    (UPLOAD_DIR / f"{doc_id}.pdf").write_bytes(data)
    db.add_document(doc_id, file.filename, total_pages, chunks_indexed)

    return {
        "doc_id": doc_id,
        "doc_name": file.filename,
        "total_pages": total_pages,
        "pages_with_text": len(pages),
        "chunks_indexed": chunks_indexed,
        "already_indexed": bool(already_indexed),
        "preview": pages[0]["text"][:300],
    }


# ---------------------------------------------------------------- library

@app.get("/documents")
def list_documents():
    return {"documents": db.list_documents()}


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    # doc ids are 32 hex characters; anything else cannot be ours
    if not re.fullmatch(r"[0-9a-f]{32}", doc_id):
        raise HTTPException(status_code=404, detail="Document not found.")

    existed_in_db = db.delete_document(doc_id)
    had_chunks = vector_store.count_document_chunks(doc_id) > 0
    vector_store.delete_document_chunks(doc_id)
    pdf_path = UPLOAD_DIR / f"{doc_id}.pdf"
    had_file = pdf_path.exists()
    pdf_path.unlink(missing_ok=True)

    if not (existed_in_db or had_chunks or had_file):
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"deleted": doc_id}


# ---------------------------------------------------------------- search and ask

class SearchRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    top_k: int = Field(default=5, ge=1, le=10)
    doc_id: str | None = None  # search only one document if given


@app.post("/search")
def search(req: SearchRequest):
    query_vector = embeddings.embed_query(req.question)
    results = vector_store.search(query_vector, top_k=req.top_k, doc_id=req.doc_id)
    return {"question": req.question, "results": results}


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    top_k: int = Field(default=5, ge=1, le=10)
    doc_id: str | None = None            # ask one document
    doc_ids: list[str] | None = None     # or several (each gets its own share)


@app.post("/ask")
def ask(req: AskRequest):
    return rag.answer_question(req.question, doc_id=req.doc_id, doc_ids=req.doc_ids, top_k=req.top_k)


# ---------------------------------------------------------------- summary and comparison

class SummarizeRequest(BaseModel):
    doc_id: str


@app.post("/summarize")
def summarize_paper(req: SummarizeRequest):
    doc = db.get_document(req.doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    result = summarize.summarize_document(doc["doc_id"], doc["doc_name"])
    return {"doc_id": doc["doc_id"], "doc_name": doc["doc_name"], **result}


class CompareRequest(BaseModel):
    doc_ids: list[str] = Field(min_length=2, max_length=3)
    focus: str = Field(min_length=3, max_length=300)


@app.post("/compare")
def compare_papers(req: CompareRequest):
    if len(set(req.doc_ids)) != len(req.doc_ids):
        raise HTTPException(status_code=400, detail="Choose different documents to compare.")
    docs = []
    for doc_id in req.doc_ids:
        doc = db.get_document(doc_id)
        if doc is None:
            raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")
        docs.append(doc)
    return compare.compare_documents(req.focus, docs)