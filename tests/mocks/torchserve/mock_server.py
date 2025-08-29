"""
Mock TorchServe server for testing intent classification
Simulates ML model inference with configurable latency and error rates
"""
import asyncio
import json
import os
import random
import time
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Load mock responses
with open("responses.json", "r") as f:
    MOCK_RESPONSES = json.load(f)

# Configuration from environment
MOCK_LATENCY_MS = int(os.getenv("MOCK_LATENCY_MS", "100"))
MOCK_ERROR_RATE = float(os.getenv("MOCK_ERROR_RATE", "0"))

app = FastAPI(title="Mock TorchServe", version="1.0.0")


class PredictionRequest(BaseModel):
    """TorchServe prediction request format"""
    text: str
    model_name: Optional[str] = "intent_classifier"


class PredictionResponse(BaseModel):
    """TorchServe prediction response format"""
    predictions: List[Dict]


@app.get("/ping")
async def ping():
    """Health check endpoint"""
    return {"status": "Healthy"}


@app.get("/models")
async def list_models():
    """List available models"""
    return {
        "models": [
            {
                "modelName": "intent_classifier",
                "modelVersion": "1.0",
                "status": "READY",
                "workers": 2,
                "batchSize": 1
            }
        ]
    }


@app.get("/models/{model_name}")
async def model_info(model_name: str):
    """Get model information"""
    if model_name != "intent_classifier":
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {
        "modelName": model_name,
        "modelVersion": "1.0",
        "modelUrl": "mock://intent_classifier.mar",
        "runtime": "python",
        "minWorkers": 1,
        "maxWorkers": 4,
        "batchSize": 1,
        "maxBatchDelay": 100,
        "loadedAtStartup": True,
        "status": "READY"
    }


@app.post("/predictions/{model_name}")
async def predict(model_name: str, request: PredictionRequest):
    """Mock prediction endpoint"""
    
    # Simulate random errors based on error rate
    if random.random() < MOCK_ERROR_RATE:
        raise HTTPException(
            status_code=503,
            detail="Model inference failed (simulated error)"
        )
    
    # Simulate inference latency
    await asyncio.sleep(MOCK_LATENCY_MS / 1000.0)
    
    # Get appropriate response based on input
    text_lower = request.text.lower()
    
    # Determine intent based on keywords
    if any(keyword in text_lower for keyword in ["write", "create", "implement", "code", "function", "class"]):
        intent = "code_generation"
        confidence = 0.92 + random.uniform(-0.05, 0.05)
    elif any(keyword in text_lower for keyword in ["explain", "what", "how", "why", "describe"]):
        intent = "explanation"
        confidence = 0.88 + random.uniform(-0.05, 0.05)
    elif any(keyword in text_lower for keyword in ["debug", "fix", "error", "issue", "problem"]):
        intent = "debugging"
        confidence = 0.90 + random.uniform(-0.05, 0.05)
    elif any(keyword in text_lower for keyword in ["analyze", "review", "evaluate", "assess"]):
        intent = "analysis"
        confidence = 0.85 + random.uniform(-0.05, 0.05)
    elif any(keyword in text_lower for keyword in ["document", "readme", "docs", "guide"]):
        intent = "documentation"
        confidence = 0.87 + random.uniform(-0.05, 0.05)
    else:
        intent = "general"
        confidence = 0.65 + random.uniform(-0.10, 0.10)
    
    # Ensure confidence is in valid range
    confidence = max(0.0, min(1.0, confidence))
    
    # Create probability distribution
    intents = ["code_generation", "explanation", "debugging", "analysis", "documentation", "general"]
    probabilities = {}
    
    # Assign high probability to detected intent
    probabilities[intent] = confidence
    
    # Distribute remaining probability
    remaining = 1.0 - confidence
    for other_intent in intents:
        if other_intent != intent:
            probabilities[other_intent] = remaining / (len(intents) - 1) + random.uniform(-0.02, 0.02)
    
    # Normalize probabilities
    total = sum(probabilities.values())
    probabilities = {k: v/total for k, v in probabilities.items()}
    
    response = {
        "predictions": [{
            "intent": intent,
            "confidence": confidence,
            "probabilities": probabilities,
            "model_version": "1.0",
            "inference_time_ms": MOCK_LATENCY_MS
        }]
    }
    
    return response


@app.post("/predictions/{model_name}/batch")
async def batch_predict(model_name: str, requests: List[PredictionRequest]):
    """Mock batch prediction endpoint"""
    
    # Process each request
    responses = []
    for req in requests:
        resp = await predict(model_name, req)
        responses.extend(resp["predictions"])
    
    return {"predictions": responses}


@app.delete("/models/{model_name}/{version}")
async def unregister_model(model_name: str, version: str):
    """Mock model unregistration"""
    return {"status": "Model unregistered successfully"}


@app.put("/models/{model_name}/{version}/set-default")
async def set_default_version(model_name: str, version: str):
    """Mock setting default model version"""
    return {"status": f"Version {version} is now default for {model_name}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)