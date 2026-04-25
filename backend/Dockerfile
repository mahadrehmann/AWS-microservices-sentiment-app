# =============================================================================
# Microservice A — AI Backend Dockerfile
# =============================================================================
# Strategy:
#   1. Install CPU-only PyTorch first (separate pip index) — avoids pulling
#      the massive CUDA wheel (~2 GB) and keeps the final image ~1.5 GB.
#   2. Install remaining Python deps.
#   3. Run download_model.py to bake HuggingFace weights into the image layer.
#      The container therefore starts instantly with no internet dependency.
#   4. Launch uvicorn on port 8000.
# =============================================================================

FROM python:3.11-slim AS base

# ── System-level dependencies ──────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ──────────────────────────────────────────────────────
WORKDIR /app

# ── Step 1: CPU-only PyTorch (must come before requirements.txt) ──────────
# Using the official PyTorch CPU index keeps the image lean (~1.5 GB vs ~4 GB).
RUN pip install --no-cache-dir \
    torch==2.3.0 \
    --index-url https://download.pytorch.org/whl/cpu

# ── Step 2: Application dependencies ──────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Step 3: Copy application source ───────────────────────────────────────
COPY . .

# ── Step 4: Bake model weights into this image layer ─────────────────────
# This runs at BUILD time; weights are cached in /root/.cache/huggingface/
# The resulting layer is committed, so runtime startup needs no downloads.
ENV TRANSFORMERS_OFFLINE=0
RUN python download_model.py
# After download, lock the container to offline mode for security.
ENV TRANSFORMERS_OFFLINE=1

# ── Runtime ───────────────────────────────────────────────────────────────
EXPOSE 8000

# Healthcheck for Docker / K8s liveness probe
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
