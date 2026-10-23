import os
from pathlib import Path

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