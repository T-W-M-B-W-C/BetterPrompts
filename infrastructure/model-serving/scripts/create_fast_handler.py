#!/usr/bin/env python3
"""Create a fast, lightweight handler for development testing."""

import json

FAST_HANDLER = '''
import json
import time
import random
from typing import List, Dict, Any

class IntentClassifierHandler:
    """Minimal fast handler for development."""
    
    def __init__(self):
        self.labels = [
            "question_answering", "creative_writing", "code_generation",
            "data_analysis", "reasoning", "summarization", "translation",
            "conversation", "task_planning", "problem_solving"
        ]
        self.initialized = True
        print("Fast handler initialized")
    
    def handle(self, data: List[Dict], context) -> List[Dict]:
        """Direct handling without complex preprocessing."""
        start = time.time()
        results = []
        
        for item in data:
            # Extract text directly
            if isinstance(item, dict):
                text = item.get("text") or item.get("data") or ""
            else:
                text = str(item)
            
            # Mock inference - fast random selection
            intent_idx = hash(text) % len(self.labels)
            confidence = 0.7 + (random.random() * 0.25)
            
            # Minimal response
            result = {
                "intent": self.labels[intent_idx],
                "confidence": round(confidence, 3),
                "complexity": {
                    "level": "moderate",
                    "score": 0.5
                },
                "techniques": [
                    {
                        "name": "chain_of_thought",
                        "confidence": 0.8,
                        "description": "Step-by-step reasoning"
                    }
                ],
                "metadata": {
                    "inference_time_ms": round((time.time() - start) * 1000, 2),
                    "handler": "fast_dev"
                }
            }
            results.append(result)
        
        return results

# Global handler instance
_service = IntentClassifierHandler()

def handle(data, context):
    """TorchServe entry point."""
    try:
        if not data:
            data = [{"text": "default"}]
        return _service.handle(data, context)
    except Exception as e:
        return [{"error": str(e), "handler": "fast_dev"}]
'''

# Save the handler
with open("fast_handler.py", "w") as f:
    f.write(FAST_HANDLER)

print("Fast handler created: fast_handler.py")
print("\nTo use this handler:")
print("1. Copy it to the container:")
print("   docker cp fast_handler.py betterprompts-torchserve:/tmp/")
print("2. Create a new model archive with it:")
print("   docker compose exec torchserve torch-model-archiver \\")
print("     --model-name intent_classifier_fast \\")
print("     --version 1.0 \\")
print("     --handler /tmp/fast_handler.py \\")
print("     --export-path /home/model-server/model-store \\")
print("     --force")
print("3. Register the fast model")