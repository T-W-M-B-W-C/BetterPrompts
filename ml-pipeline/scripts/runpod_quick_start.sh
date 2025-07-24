#!/bin/bash
# Quick start script for RunPod - Downloads code and starts training

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration (update these)
REPO_URL="${REPO_URL:-https://github.com/your-org/betterprompts.git}"
DATA_URL="${DATA_URL:-}"  # Optional: URL to download training data
SHUTDOWN_DELAY="${SHUTDOWN_DELAY:-10}"  # Minutes before auto-shutdown

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}   BetterPrompts Wave 5 Quick Start${NC}"
echo -e "${BLUE}=================================================${NC}"

# Check if on RunPod
if [ ! -d "/workspace" ]; then
    echo -e "${RED}❌ This script must be run on a RunPod instance!${NC}"
    exit 1
fi

cd /workspace

# Step 1: Clone repository if needed
if [ ! -d "betterprompts" ]; then
    echo -e "\n${BLUE}📥 Cloning BetterPrompts repository...${NC}"
    git clone "$REPO_URL" betterprompts
    echo -e "${GREEN}✅ Repository cloned${NC}"
else
    echo -e "${GREEN}✅ Repository already exists${NC}"
fi

cd betterprompts/ml-pipeline

# Step 2: Install dependencies
echo -e "\n${BLUE}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt --quiet
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Step 3: Check for training data
if [ ! -f "data_generation/openai_training_data.json" ]; then
    echo -e "\n${YELLOW}⚠️  Training data not found!${NC}"
    
    if [ -n "$DATA_URL" ]; then
        echo -e "${BLUE}📊 Downloading training data...${NC}"
        wget -q "$DATA_URL" -O data_generation/openai_training_data.json
        echo -e "${GREEN}✅ Training data downloaded${NC}"
    else
        echo -e "${RED}Please upload training data to:${NC}"
        echo -e "${RED}  /workspace/betterprompts/ml-pipeline/data_generation/openai_training_data.json${NC}"
        echo -e "\n${YELLOW}From your local machine:${NC}"
        echo -e "  scp data_generation/openai_training_data.json root@$(hostname -I | awk '{print $1}'):/workspace/betterprompts/ml-pipeline/data_generation/"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Training data found${NC}"
fi

# Step 4: Show system info
echo -e "\n${BLUE}🖥️  System Information:${NC}"
echo -e "Pod IP: $(hostname -I | awk '{print $1}')"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo -e "PyTorch: $(python -c 'import torch; print(torch.__version__)')"
echo -e "CUDA: $(python -c 'import torch; print(torch.cuda.is_available())')"

# Step 5: Start training
echo -e "\n${GREEN}=================================================${NC}"
echo -e "${GREEN}🚀 Starting training in 5 seconds...${NC}"
echo -e "${GREEN}=================================================${NC}"
echo -e "\n${YELLOW}Press Ctrl+C to cancel${NC}"
sleep 5

# Run training with auto-shutdown
echo -e "\n${BLUE}🏃 Running training pipeline...${NC}"
python scripts/runpod_train.py --shutdown-delay "$SHUTDOWN_DELAY"

# If we get here, training completed
echo -e "\n${GREEN}=================================================${NC}"
echo -e "${GREEN}✅ Training pipeline completed!${NC}"
echo -e "${GREEN}=================================================${NC}"