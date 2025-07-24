#!/bin/bash
# Start training on RunPod - Self-contained script

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}   BetterPrompts DistilBERT Training${NC}"
echo -e "${BLUE}=================================================${NC}"

# Check if we're on RunPod
if [ ! -d "/workspace" ]; then
    echo -e "${RED}❌ Error: This script must be run on RunPod!${NC}"
    echo -e "${YELLOW}Current directory: $(pwd)${NC}"
    exit 1
fi

# Step 1: Install dependencies
echo -e "\n${BLUE}📦 Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Step 2: Check GPU
echo -e "\n${BLUE}🎮 Checking GPU...${NC}"
nvidia-smi
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"

# Step 3: Check for training data
echo -e "\n${BLUE}📊 Checking training data...${NC}"
if [ ! -f "data/openai_training_data.json" ]; then
    echo -e "${YELLOW}⚠️  Training data not found at data/openai_training_data.json${NC}"
    echo -e "${YELLOW}Checking if data needs to be uploaded...${NC}"
    
    # Check if user uploaded it elsewhere
    if [ -f "/workspace/openai_training_data.json" ]; then
        echo -e "${GREEN}✅ Found data in /workspace, moving it...${NC}"
        mv /workspace/openai_training_data.json data/
    elif [ -f "../openai_training_data.json" ]; then
        echo -e "${GREEN}✅ Found data in parent directory, moving it...${NC}"
        mv ../openai_training_data.json data/
    else
        echo -e "${RED}❌ No training data found!${NC}"
        echo -e "${YELLOW}Please upload openai_training_data.json to:${NC}"
        echo -e "${YELLOW}  /workspace/runpod-training-package/data/${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Training data found: $(du -h data/openai_training_data.json | cut -f1)${NC}"

# Step 4: Create directories
echo -e "\n${BLUE}📁 Creating output directories...${NC}"
mkdir -p models results logs

# Step 5: Start training
echo -e "\n${GREEN}🚀 Starting training...${NC}"
echo -e "${YELLOW}This will take approximately 20-25 minutes${NC}"
echo -e "${YELLOW}Training will run in tmux session 'training'${NC}"

# Start training in tmux
tmux new-session -d -s training "python train_model.py 2>&1 | tee logs/training.log"

# Start GPU monitor in another tmux session
tmux new-session -d -s gpu_monitor "watch -n 1 nvidia-smi"

echo -e "\n${GREEN}✅ Training started!${NC}"
echo -e "\n${BLUE}📺 Monitor training:${NC}"
echo -e "  - Attach to training: ${YELLOW}tmux attach -t training${NC}"
echo -e "  - Watch GPU: ${YELLOW}tmux attach -t gpu_monitor${NC}"
echo -e "  - View logs: ${YELLOW}tail -f logs/training.log${NC}"
echo -e "  - Quick monitor: ${YELLOW}./monitor.sh${NC}"
echo -e "\n${BLUE}💡 Detach from tmux: Ctrl+B, then D${NC}"

# Show initial log output
sleep 3
echo -e "\n${BLUE}📄 Initial training output:${NC}"
tail -n 20 logs/training.log