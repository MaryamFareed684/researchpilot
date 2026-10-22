from pathlib import Path

UPLOAD_DIR = Path("data/uploads")   # where uploaded PDFs are saved
MAX_UPLOAD_MB = 20
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024