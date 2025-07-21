#!/bin/bash
# TorchServe startup script with mock model creation

echo "🚀 Starting TorchServe initialization..."

# Check if model store directory exists
mkdir -p /home/model-server/model-store

# Check if we have any models
if [ -z "$(ls -A /home/model-server/model-store 2>/dev/null)" ]; then
    echo "📦 No models found. Creating mock model for development..."
    
    # Install torch-model-archiver if not present
    pip install torch-model-archiver torch torchvision --no-cache-dir
    
    # Create mock model
    cd /tmp
    python - << 'EOF'
import torch
import torch.nn as nn
import json
from pathlib import Path

# Simple mock model
class MockIntentClassifier(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.fc = nn.Linear(768, num_classes)
        
    def forward(self, x):
        return self.fc(x)

# Create model
model = MockIntentClassifier()
torch.save(model.state_dict(), "model.pth")

# Create config
config = {
    "num_classes": 10,
    "labels": ["question_answering", "creative_writing", "code_generation", 
               "data_analysis", "reasoning", "summarization", "translation",
               "conversation", "task_planning", "problem_solving"]
}
with open("config.json", "w") as f:
    json.dump(config, f)

# Create handler
handler_code = '''
import torch
import json
from ts.torch_handler.base_handler import BaseHandler

class IntentClassifierHandler(BaseHandler):
    def preprocess(self, data):
        return torch.randn(len(data), 768)  # Mock embeddings
    
    def inference(self, data):
        with torch.no_grad():
            outputs = self.model(data)
            probs = torch.softmax(outputs, dim=-1)
            return probs
    
    def postprocess(self, data):
        results = []
        with open("config.json") as f:
            config = json.load(f)
        labels = config.get("labels", [])
        
        for probs in data:
            pred_idx = torch.argmax(probs).item()
            results.append({
                "predicted_class": pred_idx,
                "predicted_label": labels[pred_idx] if pred_idx < len(labels) else "unknown",
                "confidence": float(torch.max(probs)),
                "probabilities": probs.tolist()
            })
        return results
'''
with open("handler.py", "w") as f:
    f.write(handler_code)

print("Mock model files created successfully!")
EOF
    
    # Create model archive
    echo "📦 Creating model archive..."
    torch-model-archiver \
        --model-name intent_classifier \
        --version 1.0.0 \
        --model-file model.pth \
        --handler handler.py \
        --extra-files config.json \
        --export-path /home/model-server/model-store \
        --force
    
    echo "✅ Mock model archive created!"
fi

# Start TorchServe
echo "🚀 Starting TorchServe..."
exec torchserve \
    --start \
    --model-store /home/model-server/model-store \
    --models intent_classifier=intent_classifier.mar \
    --ts-config /home/model-server/config/config.properties \
    --foreground