#!/bin/sh
set -e

echo "🚀 Starting frontend initialization..."

# Clean up previous build artifacts (but not node_modules)
echo "🧹 Cleaning previous build artifacts..."
rm -rf .next

# Check if node_modules exists and has content
if [ ! -d "node_modules" ] || [ -z "$(ls -A node_modules 2>/dev/null)" ]; then
    echo "📦 Installing dependencies..."
    npm install --legacy-peer-deps
else
    echo "✅ Dependencies already installed"
fi

# Check if we need to update dependencies (optional)
if [ -f "package.json" ]; then
    echo "🔍 Checking for dependency updates..."
    # Only install if package.json has changed
    npm install --legacy-peer-deps --prefer-offline
fi

echo "🎯 Starting Next.js development server..."
exec npm run dev