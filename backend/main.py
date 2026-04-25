"""
Microservice A: AI Backend
Sentiment analysis using HuggingFace DistilBERT
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global model reference (loaded once at startup)
# ---------------------------------------------------------------------------
MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"
sentiment_pipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the model once when the container starts."""
    global sentiment_pipeline
    logger.info("Loading sentiment analysis model: %s", MODEL_NAME)
    sentiment_pipeline = pipeline("sentiment-analysis", model=MODEL_NAME)
    logger.info("Model loaded successfully. Ready to serve requests.")
    yield
    # Cleanup (optional — process exits anyway)
    sentiment_pipeline = None
    logger.info("Application shutdown. Model unloaded.")


# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Sentiment Analysis API",
    description="A lightweight AI microservice for text sentiment analysis.",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow all origins so the Nginx frontend (or any K8s ingress) can call this.
# Tighten to specific domains in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    text: str

    class Config:
        json_schema_extra = {
            "example": {"text": "I absolutely love this project!"}
        }


class AnalyzeResponse(BaseModel):
    label: str       # "POSITIVE" or "NEGATIVE"
    score: float     # Confidence 0.0 – 1.0
    text: str        # Echo the input for UI convenience


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    """Kubernetes liveness / readiness probe endpoint."""
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/analyze", response_model=AnalyzeResponse, tags=["Inference"])
async def analyze_sentiment(request: AnalyzeRequest):
    """
    Accepts a JSON body with a 'text' field and returns the predicted
    sentiment label and confidence score.
    """
    if not request.text.strip():
        raise HTTPException(status_code=422, detail="Text field must not be empty.")

    if sentiment_pipeline is None:
        raise HTTPException(status_code=503, detail="Model is not loaded yet.")

    logger.info("Analyzing text (len=%d)", len(request.text))
    result = sentiment_pipeline(request.text)[0]

    return AnalyzeResponse(
        label=result["label"],
        score=round(result["score"], 4),
        text=request.text,
    )
