#!/usr/bin/env python3
"""
Script to download and cache the DeBERTa model before starting the service.
This ensures the model is available even if there are network issues during runtime.
"""

import os
import sys
import logging
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_model():
    """Download and cache the DeBERTa model."""
    model_name = os.environ.get("MODEL_NAME", "microsoft/deberta-v3-base")
    cache_dir = os.environ.get("TRANSFORMERS_CACHE", "/app/.cache/huggingface")
    
    # Create cache directory if it doesn't exist
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading model: {model_name}")
    logger.info(f"Cache directory: {cache_dir}")
    
    try:
        # Download tokenizer
        logger.info("Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            force_download=False,  # Use cache if available
            resume_download=True,  # Resume partial downloads
        )
        logger.info("Tokenizer downloaded successfully")
        
        # Download model - this is where it fails currently
        logger.info("Downloading model weights...")
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            force_download=False,
            resume_download=True,
            num_labels=10,  # Match the intent labels count
            ignore_mismatched_sizes=True
        )
        logger.info("Model downloaded successfully")
        
        # Test the model
        logger.info("Testing model...")
        test_text = "This is a test"
        inputs = tokenizer(test_text, return_tensors="pt", max_length=512, truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)
        logger.info(f"Model test successful. Output shape: {outputs.logits.shape}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        
        # Clear potentially corrupted cache
        logger.info("Clearing cache and retrying...")
        import shutil
        cache_path = Path(cache_dir) / "models--microsoft--deberta-v3-base"
        if cache_path.exists():
            shutil.rmtree(cache_path)
            logger.info(f"Cleared cache: {cache_path}")
        
        # Try one more time with force download
        try:
            logger.info("Retrying with force download...")
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=cache_dir,
                force_download=True,
            )
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                cache_dir=cache_dir,
                force_download=True,
                num_labels=10,
                ignore_mismatched_sizes=True
            )
            logger.info("Model downloaded successfully on retry")
            return True
        except Exception as retry_error:
            logger.error(f"Retry failed: {retry_error}")
            return False

if __name__ == "__main__":
    success = download_model()
    if not success:
        logger.error("Model download failed. The service will use fallback classifiers.")
        # Don't exit with error - let the service start with fallback
        sys.exit(0)
    else:
        logger.info("Model ready for use")
        sys.exit(0)