# DistilBERT Training Guide for BetterPrompts

This guide explains how to train a DistilBERT model for intent classification as a lightweight alternative to DeBERTa-v3.

## Overview

DistilBERT offers several advantages over DeBERTa for production deployments:
- **2x faster inference** than BERT/DeBERTa
- **40% smaller model size** (66M vs 110M+ parameters)
- **Maintains 97% of BERT's performance** on most tasks
- **Lower memory requirements** for edge deployment
- **Faster training time** due to fewer layers

## Quick Start

### 1. Basic Training

Train DistilBERT with default settings:

```bash
cd ml-pipeline
python scripts/train_distilbert_classifier.py --prepare-data
```

### 2. Training with Custom Configuration

Use the optimized DistilBERT configuration:

```bash
python scripts/train_distilbert_classifier.py \
    --config configs/distilbert_config.yaml \
    --prepare-data \
    --num-epochs 15
```

### 3. Hyperparameter Search

Find optimal hyperparameters for your dataset:

```bash
python scripts/train_distilbert_classifier.py \
    --config configs/distilbert_config.yaml \
    --hyperparameter-search \
    --experiment-name distilbert_hyperparam_search
```

### 4. Transfer Learning with Layer Freezing

For faster training with limited data, freeze bottom transformer layers:

```bash
python scripts/train_distilbert_classifier.py \
    --config configs/distilbert_config.yaml \
    --freeze-layers 3 \
    --num-epochs 10
```

## Advanced Usage

### Benchmark Performance

Compare inference speed after training:

```bash
python scripts/train_distilbert_classifier.py \
    --config configs/distilbert_config.yaml \
    --benchmark \
    --compare-baseline
```

### Compare with DeBERTa

Run a comprehensive comparison between models:

```bash
python scripts/compare_models.py \
    --deberta-checkpoint models/checkpoints/deberta_best/model.pt \
    --distilbert-checkpoint models/distilbert/checkpoints/best_model/model.pt \
    --benchmark-speed \
    --output-dir comparison_results
```

## Configuration Options

### Key Parameters in `distilbert_config.yaml`

```yaml
model:
  distilbert_classifier:
    pretrained_model: "distilbert-base-uncased"  # Base model
    pooling_strategy: "cls"  # How to pool token embeddings
    use_complexity_features: true  # Include complexity features
    freeze_layers: 0  # Number of transformer layers to freeze
    use_layer_norm: true  # Use layer normalization in classifier

training:
  batch_size: 64  # Larger batches possible with DistilBERT
  learning_rate: 5e-5  # Slightly higher LR works well
  num_epochs: 15  # More epochs since training is faster
  fp16: true  # Mixed precision training for speed

optimization:
  quantization:
    enabled: true  # Enable for further size reduction
  onnx_export:
    enabled: true  # Export to ONNX for deployment
```

### Optimization Strategies

1. **Layer Freezing**: Freeze 2-3 bottom layers for transfer learning
2. **Mixed Precision**: Use FP16 training for 2x speed improvement
3. **Gradient Accumulation**: Reduce if GPU memory allows
4. **Larger Batch Sizes**: DistilBERT can handle 2-4x larger batches

## Training Data

### Using Existing Data

The training script will use the same data as DeBERTa:

```bash
python scripts/train_distilbert_classifier.py --prepare-data
```

### Generating New Data

Generate synthetic training data optimized for DistilBERT:

```bash
cd data_generation
python generate_training_data.py \
    --examples-per-intent 500 \
    --edge-cases 1000 \
    --output distilbert_training_data.json
```

## Model Deployment

### Export to ONNX

For production deployment, export to ONNX:

```python
from src.models.distilbert_classifier_model import create_distilbert_model
import torch

model = create_distilbert_model(num_labels=10)
model.load_state_dict(torch.load('path/to/checkpoint.pt'))
model.eval()

# Export to ONNX
dummy_input = torch.randint(0, 30000, (1, 128))
torch.onnx.export(
    model,
    (dummy_input,),
    "distilbert_intent_classifier.onnx",
    export_params=True,
    opset_version=14,
    input_names=['input_ids'],
    output_names=['logits'],
    dynamic_axes={'input_ids': {0: 'batch_size', 1: 'sequence_length'}}
)
```

### TorchServe Integration

Deploy with TorchServe (already configured in infrastructure):

```bash
# Create model archive
torch-model-archiver \
    --model-name distilbert_intent_classifier \
    --version 1.0 \
    --model-file ml-pipeline/src/models/distilbert_classifier_model.py \
    --serialized-file models/distilbert/checkpoints/best_model/model.pt \
    --handler ml-pipeline/src/serving/distilbert_handler.py \
    --extra-files "ml-pipeline/configs/distilbert_config.yaml"

# Deploy to TorchServe
curl -X POST "http://localhost:8081/models?url=distilbert_intent_classifier.mar"
```

## Performance Expectations

Based on typical results, you can expect:

| Metric | DeBERTa-v3 | DistilBERT | Difference |
|--------|------------|------------|------------|
| Accuracy | ~92% | ~88-90% | -2-4% |
| F1 Score | ~91% | ~87-89% | -2-4% |
| Inference Speed | 50 samples/sec | 100-120 samples/sec | 2-2.4x faster |
| Model Size | 440 MB | 250 MB | 43% smaller |
| Training Time | 2-3 hours | 1-1.5 hours | 50% faster |

## Troubleshooting

### Out of Memory Errors

Reduce batch size or enable gradient checkpointing:

```python
model.distilbert.gradient_checkpointing_enable()
```

### Low Accuracy

1. Try unfreezing all layers
2. Increase training epochs
3. Use a lower learning rate (2e-5)
4. Enable data augmentation

### Slow Training

1. Enable mixed precision training (fp16)
2. Increase batch size if GPU allows
3. Freeze bottom 2-3 transformer layers

## Best Practices

1. **Start with Default Config**: Use the provided `distilbert_config.yaml`
2. **Monitor Validation Loss**: Stop training if validation loss increases
3. **Use Early Stopping**: Prevent overfitting with patience=5
4. **Benchmark Before Deployment**: Always test inference speed
5. **Compare with Baseline**: Ensure accuracy trade-off is acceptable

## Next Steps

1. Train the model: `python scripts/train_distilbert_classifier.py`
2. Evaluate performance: Check MLflow UI for metrics
3. Compare with DeBERTa: Run the comparison script
4. Deploy to production: Use ONNX or TorchServe
5. Monitor in production: Track accuracy and latency metrics

For questions or issues, refer to the main ML Pipeline documentation or create an issue in the repository.