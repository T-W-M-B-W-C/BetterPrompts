#!/bin/bash

# Script to install Git LFS on RunPod Ubuntu system

set -e

echo "🔧 Installing Git LFS on RunPod..."
echo "================================="

# Update package list
echo "📦 Updating package list..."
apt-get update

# Install Git LFS
echo "📥 Installing Git LFS..."
apt-get install -y git-lfs

# Initialize Git LFS for the user
echo "🚀 Initializing Git LFS..."
git lfs install

# Verify installation
echo ""
echo "✅ Verifying installation..."
git lfs version

echo ""
echo "✅ Git LFS successfully installed!"
echo ""
echo "Now you can run:"
echo "  ./scripts/add_model_to_git_lfs.sh"
echo "to add your trained model to Git with LFS tracking."