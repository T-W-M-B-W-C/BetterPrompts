#!/bin/bash
# Deploy to RunPod script

# Configuration
RUNPOD_HOST="root@103.196.86.219"
RUNPOD_PORT="18733"
SSH_KEY="~/.ssh/id_ed25519"
LOCAL_DIR="$(pwd)"

echo "🚀 Deploying to RunPod..."

# Step 1: Create archive of ml-pipeline
echo "📦 Creating deployment archive..."
tar -czf ml-pipeline-deploy.tar.gz \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='models/*' \
    --exclude='*.tar.gz' \
    .

# Step 2: Transfer to RunPod
echo "📤 Transferring to RunPod..."
scp -P $RUNPOD_PORT -i $SSH_KEY \
    ml-pipeline-deploy.tar.gz \
    $RUNPOD_HOST:/workspace/

# Step 3: Setup script
echo "📝 Creating setup script..."
cat > runpod_setup_commands.sh << 'EOF'
#!/bin/bash
cd /workspace

# Extract files
echo "📦 Extracting files..."
mkdir -p betterprompts/ml-pipeline
tar -xzf ml-pipeline-deploy.tar.gz -C betterprompts/ml-pipeline/
rm ml-pipeline-deploy.tar.gz

# Install dependencies
echo "🐍 Installing Python packages..."
cd betterprompts/ml-pipeline
pip install --upgrade pip
pip install -r requirements.txt
pip install nvidia-ml-py3 gpustat

# Verify setup
echo "✅ Verifying setup..."
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"

echo "🎉 Setup complete!"
EOF

# Transfer and execute setup
scp -P $RUNPOD_PORT -i $SSH_KEY \
    runpod_setup_commands.sh \
    $RUNPOD_HOST:/workspace/

ssh -p $RUNPOD_PORT -i $SSH_KEY $RUNPOD_HOST \
    "chmod +x /workspace/runpod_setup_commands.sh && /workspace/runpod_setup_commands.sh"

# Cleanup
rm ml-pipeline-deploy.tar.gz runpod_setup_commands.sh

echo "✅ Deployment complete!"