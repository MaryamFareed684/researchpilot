import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app import embeddings, vector_store
from app.config import MAX_UPLOAD_BYTES, MAX_UPLOAD_MB, UPLOAD_DIR
from app.pdf_utils import PDFError, extract_pages
from app.pipeline import index_pages

app = FastAPI(title="ResearchPilot")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}


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

    # 5. Clean -> chunk -> embed -> store in Qdrant (heavy work, so off the main thread)
    doc_id = uuid.uuid4().hex
    chunks_indexed = await run_in_threadpool(index_pages, doc_id, pages)
    if chunks_indexed == 0:
        raise HTTPException(status_code=422, detail="No usable text chunks found in this PDF.")

    # 6. Save the original file under the random id
    (UPLOAD_DIR / f"{doc_id}.pdf").write_bytes(data)

    return {
        "doc_id": doc_id,
        "doc_name": file.filename,
        "total_pages": total_pages,
        "pages_with_text": len(pages),
        "chunks_indexed": chunks_indexed,
        "preview": pages[0]["text"][:300],
    }


class SearchRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    top_k: int = Field(default=5, ge=1, le=10)
    doc_id: str | None = None  # search only one document if given


@app.post("/search")
def search(req: SearchRequest):
    query_vector = embeddings.embed_query(req.question)
    results = vector_store.search(query_vector, top_k=req.top_k, doc_id=req.doc_id)
    return {"question": req.question, "results": results}