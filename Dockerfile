# Hugging Face Spaces — Docker deployment
# Builds React frontend, then runs Flask backend which serves everything.
# HF Spaces expects the app on port 7860.

FROM python:3.11-slim

# ── System deps ──────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        nodejs \
        npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Build React frontend ──────────────────────────────────────────────────────
COPY frontend/package.json frontend/package-lock.json* ./frontend/
RUN cd frontend && npm install

COPY frontend/ ./frontend/
RUN cd frontend && npm run build

# ── Backend source + trained model ───────────────────────────────────────────
COPY app.py classifier.py feature_extraction.py language_config.py ./
COPY model/ ./model/

# ── Runtime config ────────────────────────────────────────────────────────────
ENV PORT=7860
EXPOSE 7860

# Single worker because the sklearn model is not thread-safe during load;
# increase --workers if you switch to a thread-safe serving strategy.
CMD ["gunicorn", \
     "--bind", "0.0.0.0:7860", \
     "--timeout", "300", \
     "--workers", "1", \
     "--threads", "4", \
     "app:app"]
