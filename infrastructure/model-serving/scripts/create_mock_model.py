#!/usr/bin/env python3
"""Create a mock model archive for development testing."""

import os
import json
import torch
import torch.nn as nn
from pathlib import Path

# Simple mock model for intent classification
class MockIntentClassifier(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.fc = nn.Linear(768, num_classes)  # BERT-like hidden size
        
    def forward(self, input_ids):
        # Mock processing - just return random logits
        batch_size = input_ids.shape[0] if hasattr(input_ids, 'shape') else 1
        return torch.randn(batch_size, 10)

def create_mock_model():
    """Create a mock model and save it."""
    model_dir = Path("mock_model")
    model_dir.mkdir(exist_ok=True)
    
    # Create and save the model
    model = MockIntentClassifier()
    torch.save(model.state_dict(), model_dir / "model.pth")
    
    # Create model config
    config = {
        "model_type": "intent_classifier",
        "num_classes": 10,
        "hidden_size": 768,
        "labels": [
            "question_answering",
            "creative_writing", 
            "code_generation",
            "data_analysis",
            "reasoning",
            "summarization",
            "translation",
            "conversation",
            "task_planning",
            "problem_solving"
        ]
    }
    
    with open(model_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    # Create a simple handler file
    handler_code = '''
import torch
import json
from ts.torch_handler.base_handler import BaseHandler

class IntentClassifierHandler(BaseHandler):
    """Mock handler for intent classification."""
    
    def preprocess(self, data):
        """Preprocess the input data."""
        # For mock, just return the data as-is
        return data
    
    def inference(self, data):
        """Run inference on the model."""
        # Mock inference - return random predictions
        outputs = []
        for item in data:
            # Generate random logits for 10 classes
            logits = torch.randn(1, 10)
            probs = torch.softmax(logits, dim=-1)
            outputs.append({
                "logits": logits.tolist()[0],
                "probabilities": probs.tolist()[0],
                "predicted_class": int(torch.argmax(probs)),
                "confidence": float(torch.max(probs))
            })
        return outputs
    
    def postprocess(self, data):
        """Postprocess the model output."""
        return data
'''
    
    with open(model_dir / "handler.py", "w") as f:
        f.write(handler_code)
    
    print(f"Mock model created in {model_dir}")
    print("\nTo create the model archive, run:")
    print(f"torch-model-archiver --model-name intent_classifier --version 1.0.0 \\")
    print(f"  --model-file {model_dir}/model.pth \\")
    print(f"  --handler {model_dir}/handler.py \\")
    print(f"  --extra-files {model_dir}/config.json \\")
    print(f"  --export-path ./model-store")

if __name__ == "__main__":
    create_mock_model()