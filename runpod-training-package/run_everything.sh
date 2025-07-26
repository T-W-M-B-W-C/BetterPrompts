#!/bin/bash
# Comprehensive RunPod training automation script
# This script handles EVERYTHING - just run it and relax!

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Banner
clear
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║        BetterPrompts DistilBERT Training Automation        ║${NC}"
echo -e "${CYAN}║              Sit back and relax - I got this!              ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to display progress
show_progress() {
    local step=$1
    local total=$2
    local desc=$3
    local percent=$((step * 100 / total))
    
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}[${percent}%] Step ${step}/${total}: ${desc}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Total steps
TOTAL_STEPS=8

# Step 1: System check
show_progress 1 $TOTAL_STEPS "Checking system environment"
echo -e "${YELLOW}🔍 Verifying RunPod environment...${NC}"

# Check if we're on RunPod
if [ ! -d "/workspace" ]; then
    echo -e "${RED}❌ Error: Not running on RunPod!${NC}"
    exit 1
fi

# Check GPU
echo -e "\n${BLUE}🎮 GPU Information:${NC}"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader | \
    awk -F', ' '{printf "  GPU: %s\n  Memory: %s\n  Driver: %s\n", $1, $2, $3}'

# Check Python
echo -e "\n${BLUE}🐍 Python Information:${NC}"
python --version
pip --version

echo -e "${GREEN}✅ System check passed!${NC}"
sleep 2

# Step 2: Install dependencies
show_progress 2 $TOTAL_STEPS "Installing Python dependencies"
echo -e "${YELLOW}📦 Installing required packages...${NC}"

# Upgrade pip first
pip install --upgrade pip setuptools wheel --quiet

# Install PyTorch with CUDA support
echo "  Installing PyTorch with CUDA..."
pip install torch==2.0.1+cu118 -f https://download.pytorch.org/whl/torch_stable.html --quiet

# Install other dependencies
echo "  Installing ML dependencies..."
pip install -r requirements.txt --quiet

# Verify installations
echo -e "\n${BLUE}📋 Verifying installations:${NC}"
python -c "import torch; print(f'  PyTorch: {torch.__version__}')"
python -c "import torch; print(f'  CUDA Available: {torch.cuda.is_available()}')"
python -c "import transformers; print(f'  Transformers: {transformers.__version__}')"

echo -e "${GREEN}✅ Dependencies installed!${NC}"
sleep 2

# Step 3: Check for training data
show_progress 3 $TOTAL_STEPS "Verifying training data"
echo -e "${YELLOW}📊 Checking for training data...${NC}"

if [ ! -f "data/openai_training_data.json" ]; then
    echo -e "${RED}❌ Training data not found!${NC}"
    
    # Check common locations
    if [ -f "/workspace/openai_training_data.json" ]; then
        echo -e "${GREEN}✅ Found data in /workspace, moving it...${NC}"
        mv /workspace/openai_training_data.json data/
    elif [ -f "../openai_training_data.json" ]; then
        echo -e "${GREEN}✅ Found data in parent directory, moving it...${NC}"
        mv ../openai_training_data.json data/
    else
        echo -e "${RED}❌ No training data found anywhere!${NC}"
        echo -e "${YELLOW}Please upload openai_training_data.json${NC}"
        exit 1
    fi
fi

# Display data info
DATA_SIZE=$(du -h data/openai_training_data.json | cut -f1)
DATA_LINES=$(wc -l < data/openai_training_data.json)
echo -e "${GREEN}✅ Training data found:${NC}"
echo -e "  Size: ${DATA_SIZE}"
echo -e "  Lines: ${DATA_LINES}"
sleep 2

# Step 4: Prepare directories
show_progress 4 $TOTAL_STEPS "Preparing directories"
echo -e "${YELLOW}📁 Creating output directories...${NC}"

mkdir -p models/final models/checkpoints models/onnx
mkdir -p results
mkdir -p logs

echo -e "${GREEN}✅ Directories ready!${NC}"
sleep 1

# Step 5: Start training
show_progress 5 $TOTAL_STEPS "Starting training process"
echo -e "${YELLOW}🚀 Launching training...${NC}"
echo -e "${CYAN}This will take approximately 20-25 minutes${NC}"
echo -e "${CYAN}Training will run in background - you can monitor progress${NC}"

# Kill any existing training sessions
tmux kill-session -t training 2>/dev/null || true
tmux kill-session -t gpu_monitor 2>/dev/null || true

# Start training in tmux
echo -e "\n${BLUE}Starting training session...${NC}"
tmux new-session -d -s training "python train_model.py 2>&1 | tee logs/training.log"

# Start GPU monitor
echo -e "${BLUE}Starting GPU monitor...${NC}"
tmux new-session -d -s gpu_monitor "watch -n 1 nvidia-smi"

# Wait for training to actually start
echo -e "\n${YELLOW}⏳ Waiting for training to initialize...${NC}"
sleep 10

# Step 6: Monitor initial progress
show_progress 6 $TOTAL_STEPS "Monitoring training progress"
echo -e "${YELLOW}📊 Initial training status:${NC}"

# Show last few lines of log
if [ -f "logs/training.log" ]; then
    echo -e "\n${BLUE}Recent log entries:${NC}"
    tail -10 logs/training.log | sed 's/^/  /'
fi

# Step 7: Provide monitoring instructions
show_progress 7 $TOTAL_STEPS "Setting up monitoring"
echo -e "${GREEN}✅ Training is running!${NC}"
echo -e "\n${BLUE}📺 Monitor your training:${NC}"
echo -e "  ${YELLOW}Option 1:${NC} Run monitoring script"
echo -e "    ${CYAN}./monitor.sh${NC}"
echo -e ""
echo -e "  ${YELLOW}Option 2:${NC} Attach to training session"
echo -e "    ${CYAN}tmux attach -t training${NC}"
echo -e "    (Detach with Ctrl+B, then D)"
echo -e ""
echo -e "  ${YELLOW}Option 3:${NC} Watch GPU usage"
echo -e "    ${CYAN}tmux attach -t gpu_monitor${NC}"
echo -e ""
echo -e "  ${YELLOW}Option 4:${NC} Follow training log"
echo -e "    ${CYAN}tail -f logs/training.log${NC}"

# Step 8: Auto-monitor setup
show_progress 8 $TOTAL_STEPS "Complete! Setting up auto-monitor"
echo -e "${GREEN}✅ Everything is set up and running!${NC}"
echo -e "\n${YELLOW}Would you like to start the monitoring dashboard? (y/n)${NC}"
read -r -n 1 response
echo

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo -e "\n${BLUE}Starting monitoring dashboard...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to exit monitor (training will continue)${NC}"
    sleep 3
    exec ./monitor.sh
else
    echo -e "\n${GREEN}✅ Setup complete!${NC}"
    echo -e "${BLUE}Training is running in the background.${NC}"
    echo -e "${YELLOW}Run ${CYAN}./monitor.sh${YELLOW} anytime to check progress.${NC}"
    echo -e "\n${CYAN}Results will be available in ~25 minutes at:${NC}"
    echo -e "  ${YELLOW}results/training_results_*.tar.gz${NC}"
fi

# Final message
echo -e "\n${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    Happy Training! 🚀                      ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"