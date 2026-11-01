FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    FASTEMBED_CACHE_PATH=/models

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download both models now, while building, so the server does not download them on its first request
RUN python -c "from fastembed import TextEmbedding; from fastembed.rerank.cross_encoder import TextCrossEncoder; TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2'); TextCrossEncoder(model_name='Xenova/ms-marco-MiniLM-L-6-v2')"

COPY app ./app
RUN mkdir -p /app/data

# Render tells the app which port to use through $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]