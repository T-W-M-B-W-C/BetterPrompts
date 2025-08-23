#!/bin/bash
# RunPod Web Terminal Training Script
# Copy and paste these commands into your RunPod web terminal

echo "🚀 Starting BetterPrompts Training Setup on RunPod"

# 1. Create workspace directory
cd /workspace
mkdir -p betterprompts/ml-pipeline
cd betterprompts/ml-pipeline

# 2. Install Python dependencies
echo "📦 Installing dependencies..."
pip install torch==2.0.1+cu118 -f https://download.pytorch.org/whl/torch_stable.html
pip install transformers==4.35.0 datasets==2.14.0 accelerate==0.24.0
pip install scikit-learn pandas numpy loguru tqdm tensorboard
pip install nvidia-ml-py3 gpustat

# 3. Create directory structure
echo "📁 Creating directory structure..."
mkdir -p data/raw data/processed models scripts configs src

# 4. Create a simple upload receiver script
cat > receive_data.py << 'EOF'
import sys
import base64

print("Ready to receive base64 encoded data. Send 'END_OF_DATA' when complete.")
data_lines = []
while True:
    line = input()
    if line == "END_OF_DATA":
        break
    data_lines.append(line)

# Decode and save
encoded_data = ''.join(data_lines)
decoded_data = base64.b64decode(encoded_data)

with open('data/raw/training_data_large.json', 'wb') as f:
    f.write(decoded_data)

print(f"✅ Saved training data: {len(decoded_data)} bytes")
EOF

echo "📝 Data receiver script created. You can now upload your training data."
echo ""
echo "To upload your training data, run this on your LOCAL machine:"
echo "base64 < /Users/lechristopherblackwell/Desktop/Codeblackwell/BetterPrompts/ml-pipeline/data/raw/training_data_large.json | pbcopy"
echo ""
echo "Then in the RunPod terminal:"
echo "python receive_data.py"
echo "Paste the base64 data and press Enter"
echo "Type END_OF_DATA and press Enter"