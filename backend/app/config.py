import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # reads backend/.env (run the server from the backend folder)

# Folder where uploaded PDFs are saved (created automatically)
UPLOAD_DIR = Path("data/uploads")

# Reject files bigger than this
MAX_UPLOAD_MB = 20
# The small SQLite file that lists our documents (tests use a temporary file)
DB_PATH = os.getenv("DB_PATH", "data/researchpilot.db")
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

# Where Qdrant keeps its data (use ":memory:" in tests)
QDRANT_PATH = os.getenv("QDRANT_PATH", "data/qdrant")

# Chunking settings (in characters)
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
MIN_CHUNK_CHARS = 40

# LLM settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
CONTEXT_CHUNKS = 5        # how many chunks we give the LLM
MAX_ANSWER_TOKENS = 1500  # limit the answer length
LLM_TEMPERATURE = 0.1     # low = factual, not creative

# --- Day 4 ---
SUMMARY_CHUNKS_PER_ASPECT = 3   # chunks retrieved for each summary question
COMPARE_CHUNKS_PER_DOC = 4     # chunks retrieved per paper when comparing

# --- Day 5: which websites may call this API from a browser (comma separated) ---
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]