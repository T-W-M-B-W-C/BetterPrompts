#!/bin/bash
# RunPod environment setup script for BetterPrompts Wave 5 training

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}   BetterPrompts RunPod Environment Setup${NC}"
echo -e "${BLUE}=================================================${NC}"

# Check if running on RunPod
if [ ! -d "/workspace" ]; then
    echo -e "${YELLOW}⚠️  Warning: /workspace not found. Are you on RunPod?${NC}"
fi

# Update system packages
echo -e "\n${BLUE}📦 Updating system packages...${NC}"
apt-get update -qq
apt-get install -y -qq \
    git \
    wget \
    curl \
    unzip \
    htop \
    nvtop \
    tmux \
    vim \
    jq \
    python3-pip

echo -e "${GREEN}✅ System packages installed${NC}"

# Install Python ML dependencies
echo -e "\n${BLUE}🐍 Installing Python dependencies...${NC}"
pip install --upgrade pip setuptools wheel

# Core ML packages
pip install \
    torch==2.0.1+cu118 \
    -f https://download.pytorch.org/whl/torch_stable.html

pip install \
    transformers==4.35.0 \
    datasets==2.14.0 \
    accelerate==0.24.0 \
    scikit-learn==1.3.0 \
    numpy==1.24.3 \
    pandas==2.0.3

# Additional packages
pip install \
    loguru==0.7.0 \
    tqdm==4.66.0 \
    rich==13.5.0 \
    tensorboard==2.13.0 \
    onnx==1.14.0 \
    onnxruntime-gpu==1.15.1 \
    nvidia-ml-py3==7.352.0

echo -e "${GREEN}✅ Python dependencies installed${NC}"

# Create directory structure
echo -e "\n${BLUE}📁 Setting up directory structure...${NC}"
mkdir -p /workspace/betterprompts/{models,data,logs,results}

# Install monitoring tools
echo -e "\n${BLUE}📊 Installing GPU monitoring tools...${NC}"
pip install gpustat py3nvml

# Create helpful aliases
echo -e "\n${BLUE}🔧 Setting up helpful aliases...${NC}"
cat >> ~/.bashrc << 'EOF'

# BetterPrompts aliases
alias gpu='watch -n 1 nvidia-smi'
alias gpus='gpustat -i'
alias tb='tensorboard --logdir /workspace/betterprompts/models --host 0.0.0.0'
alias bp='cd /workspace/betterprompts'

# Colored prompt for RunPod
export PS1="\[\033[01;32m\]runpod\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]$ "
EOF

# Create a welcome message
cat > /workspace/welcome.txt << 'EOF'
🚀 RunPod Environment Ready for BetterPrompts Training!

Quick Commands:
- gpu      : Monitor GPU usage
- gpus     : Detailed GPU stats  
- bp       : Go to BetterPrompts directory
- tb       : Start TensorBoard

Training:
1. Upload your data:
   scp -r ml-pipeline root@[THIS_POD_IP]:/workspace/betterprompts/

2. Start training:
   cd /workspace/betterprompts/ml-pipeline
   python scripts/runpod_train.py

3. Download results:
   scp root@[THIS_POD_IP]:/workspace/betterprompts/ml-pipeline/*.tar.gz ./

EOF

# Display summary
echo -e "\n${GREEN}=================================================${NC}"
echo -e "${GREEN}✅ RunPod environment setup complete!${NC}"
echo -e "${GREEN}=================================================${NC}"

# Show GPU info
echo -e "\n${BLUE}🎮 GPU Information:${NC}"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader

# Show Python/PyTorch info
echo -e "\n${BLUE}🐍 Python Environment:${NC}"
python3 -c "import torch; print(f'PyTorch: {torch.__version__}')"
python3 -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
python3 -c "import transformers; print(f'Transformers: {transformers.__version__}')"

echo -e "\n${YELLOW}📝 See /workspace/welcome.txt for usage instructions${NC}"
cat /workspace/welcome.txt