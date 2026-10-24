import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # reads backend/.env (run the server from the backend folder)

# Folder where uploaded PDFs are saved (created automatically)
UPLOAD_DIR = Path("data/uploads")

# Reject files bigger than this
MAX_UPLOAD_MB = 20
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