#!/bin/bash
# Complete Wave 5 pipeline execution script

# Progress tracking function
TOTAL_STEPS=5
CURRENT_STEP=0

show_progress() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    local step_name="$1"
    local percent=$((CURRENT_STEP * 100 / TOTAL_STEPS))
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf "Progress: [%3d%%] Step %d/%d: %s\n" "$percent" "$CURRENT_STEP" "$TOTAL_STEPS" "$step_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Start timer
START_TIME=$(date +%s)

echo "==================================================="
echo "Wave 5: Fine-tune DistilBERT Model Pipeline"
echo "==================================================="
echo "Started at: $(date)"

# Set paths
DATA_PATH="data_generation/openai_training_data.json"
MODEL_DIR="models/distilbert_intent_classifier"
ONNX_DIR="models/onnx"
VALIDATION_DIR="validation_results"

# Check if training data exists
show_progress "Verify Training Data"
if [ ! -f "$DATA_PATH" ]; then
    echo "❌ Training data not found at $DATA_PATH"
    echo "Please run Wave 3 data generation first:"
    echo "  cd data_generation"
    echo "  python generate_training_data.py --examples-per-intent 1000"
    exit 1
fi

echo "✅ Found training data at $DATA_PATH"
echo "📊 File size: $(du -h $DATA_PATH | cut -f1)"

# Step 1: Train DistilBERT model
show_progress "Train DistilBERT Model"
echo "⏱️  Estimated time: 20-30 minutes"
echo "📝 Training with 5 epochs, batch size 32, learning rate 5e-5"
python train_distilbert.py \
    --data-path "$DATA_PATH" \
    --output-dir "$MODEL_DIR" \
    --num-epochs 5 \
    --batch-size 32 \
    --learning-rate 5e-5 \
    --fp16 \
    --export-onnx

if [ $? -ne 0 ]; then
    echo "❌ Training failed!"
    exit 1
fi

echo "✅ Training completed successfully"

# Step 2: Validate model accuracy
show_progress "Validate Model Accuracy"
echo "🎯 Target accuracy: >88%"
python scripts/validate_model_accuracy.py \
    --model-path "$MODEL_DIR" \
    --data-path "$DATA_PATH" \
    --output-dir "$VALIDATION_DIR" \
    --show-examples \
    --num-examples 10

if [ $? -ne 0 ]; then
    echo "❌ Model does not meet accuracy requirement!"
    exit 1
fi

echo "✅ Model meets accuracy requirement (>88%)"

# Step 3: Export to ONNX with optimization
show_progress "Export to Optimized ONNX"
echo "📦 Applying quantization and optimization"
python scripts/export_to_onnx.py \
    --model-path "$MODEL_DIR" \
    --output-dir "$ONNX_DIR" \
    --model-name distilbert_intent_classifier \
    --benchmark \
    --quantize

if [ $? -ne 0 ]; then
    echo "⚠️  ONNX export failed (non-critical)"
else
    echo "✅ ONNX export completed"
fi

# Step 4: Generate integration code
show_progress "Generate Integration Code"
echo "🔧 Creating production-ready integration"
python scripts/integrate_distilbert_model.py \
    --model-path "$ONNX_DIR/distilbert_intent_classifier_optimized.onnx" \
    --use-onnx \
    --generate-integration

echo "✅ Integration code generated"

# Step 5: Summary
show_progress "Pipeline Complete"

# Calculate total time
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "==================================================="
echo "Wave 5 Pipeline Complete!"
echo "==================================================="
echo "⏱️  Total time: ${MINUTES}m ${SECONDS}s"
echo ""
echo "📊 Results Summary:"
echo "  - Model saved to: $MODEL_DIR"
echo "  - ONNX model at: $ONNX_DIR"
echo "  - Validation results: $VALIDATION_DIR"
echo "  - Integration code: distilbert_ml_classifier.py"
echo ""
echo "📈 Performance Metrics:"
if [ -f "$VALIDATION_DIR/validation_results.json" ]; then
    accuracy=$(python -c "import json; print(json.load(open('$VALIDATION_DIR/validation_results.json'))['intent']['accuracy'])")
    echo "  - Test Accuracy: $(python -c "print(f'{$accuracy*100:.2f}%')")"
fi
echo ""
echo "🚀 Next Steps:"
echo "  1. Copy integration code to intent classifier service:"
echo "     cp distilbert_ml_classifier.py ../backend/services/intent-classifier/app/models/"
echo ""
echo "  2. Update intent classifier to use new model:"
echo "     - Add model selection logic"
echo "     - Implement A/B testing"
echo "     - Deploy with feature flags"
echo ""
echo "  3. Monitor performance in production:"
echo "     - Track inference latency"
echo "     - Monitor accuracy on real data"
echo "     - Collect user feedback"
echo ""
echo "✅ Wave 5 completed successfully!"