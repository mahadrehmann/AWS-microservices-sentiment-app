"""
download_model.py
-----------------
Run during Docker BUILD (not at runtime) to bake the HuggingFace model
weights into an image layer.  This ensures the container never needs
internet access after deployment — critical for air-gapped K8s nodes.

Usage (called by Dockerfile):
    python download_model.py
"""

import logging

from transformers import pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"


def main():
    logger.info("Downloading model weights for: %s", MODEL_NAME)
    # Instantiating the pipeline triggers a full download of model weights
    # and tokenizer files into the HuggingFace cache (~/.cache/huggingface).
    _ = pipeline("sentiment-analysis", model=MODEL_NAME)
    logger.info("Model weights cached successfully. Build layer will persist them.")


if __name__ == "__main__":
    main()
