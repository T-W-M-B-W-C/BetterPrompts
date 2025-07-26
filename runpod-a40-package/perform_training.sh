#!/bin/bash
# Optimized one-click training script for RunPod A40
# Just run: ./perform_training.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        BetterPrompts DistilBERT Training - A40 GPU         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

# Step 1: Install dependencies if needed
if ! python -c "import transformers" 2>/dev/null; then
    echo -e "\n${YELLOW}📦 Installing dependencies...${NC}"
    pip install -q torch transformers datasets accelerate scikit-learn numpy tqdm
fi

# Step 2: Verify environment
echo -e "\n${BLUE}🔍 Verifying environment...${NC}"
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || echo "GPU info not available"

# Step 3: Check for data
if [ ! -f "data/openai_training_data.json" ]; then
    echo -e "${YELLOW}📊 Setting up sample data...${NC}"
    mkdir -p data
    # Create sample data if real data missing
    python -c "
import json
examples = [
    {'text': 'How do I implement a binary search tree?', 'intent': 'code_generation'},
    {'text': 'Explain quantum computing', 'intent': 'explanation'},
    {'text': 'Write a poem about AI', 'intent': 'creative_writing'},
] * 1000  # Repeat for demo
with open('data/openai_training_data.json', 'w') as f:
    json.dump({'examples': examples}, f)
print('Created sample data')
"
fi

# Step 4: Run training
echo -e "\n${GREEN}🚀 Starting training...${NC}"
python train_model.py

# Step 5: Package results
echo -e "\n${BLUE}📦 Packaging results...${NC}"
timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p results
tar -czf "results/model_${timestamp}.tar.gz" models/final/

echo -e "\n${GREEN}✅ Training complete!${NC}"
echo -e "${YELLOW}Model saved to: results/model_${timestamp}.tar.gz${NC}"
echo -e "\n${BLUE}Download with:${NC}"
echo -e "scp -P [PORT] root@[IP]:/workspace/runpod-a40-package/results/model_${timestamp}.tar.gz ./"