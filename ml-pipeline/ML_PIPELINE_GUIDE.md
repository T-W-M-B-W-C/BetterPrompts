# BetterPrompts ML Pipeline - Complete Guide

## Overview

The BetterPrompts ML Pipeline is a production-ready machine learning infrastructure for training, evaluating, and serving intent classification models based on DeBERTa-v3. This pipeline is designed to support the core functionality of the BetterPrompts system - automatically detecting user intent and applying appropriate prompt engineering techniques.

## Architecture

### Core Components

1. **Data Processing Pipeline**
   - Automated data ingestion and preprocessing
   - Text cleaning and normalization
   - Feature extraction (complexity, length, code indicators)
   - Data augmentation (paraphrasing, synonym replacement)
   - Train/validation/test splitting with stratification

2. **Model Architecture**
   - Base Model: DeBERTa-v3 (microsoft/deberta-v3-base)
   - 10 intent classes + complexity prediction
   - Multiple pooling strategies (CLS, mean, max, attention)
   - Optional complexity features integration
   - Configurable layer freezing for transfer learning

3. **Training Infrastructure**
   - Distributed training support
   - Hyperparameter tuning with Optuna
   - Mixed precision training (FP16)
   - Gradient accumulation for large batches
   - Early stopping and model checkpointing

4. **Experiment Tracking**
   - MLflow for experiment management
   - Automatic metric logging
   - Model versioning and registry
   - Artifact storage

5. **Data Versioning**
   - DVC for data version control
   - S3-compatible remote storage
   - Reproducible pipelines

6. **Evaluation Framework**
   - Comprehensive metrics (accuracy, F1, AUC, calibration)
   - Confusion matrices and ROC curves
   - Error analysis and confidence distributions
   - Live example predictions

## Quick Start

### 1. Environment Setup

```bash
cd ml-pipeline
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 2. Generate Sample Data

```bash
python scripts/generate_sample_data.py \
    --num-samples 1000 \
    --add-cross-intent
```

### 3. Train Model

```bash
# Simple training
python scripts/train_intent_classifier.py \
    --prepare-data \
    --config configs/ml_pipeline_config.yaml

# With hyperparameter search
python scripts/train_intent_classifier.py \
    --prepare-data \
    --hyperparameter-search \
    --config configs/ml_pipeline_config.yaml
```

### 4. View Results

```bash
# Start MLflow UI
mlflow ui --backend-store-uri sqlite:///mlflow.db

# Navigate to http://localhost:5000
```

### 5. Evaluate Model

```bash
python scripts/evaluate_model.py \
    --model-path models/checkpoints/best_model/model.pt \
    --output-dir evaluation_results \
    --live-examples
```

## Model Performance

### Target Metrics
- **Accuracy**: >90% on test set
- **F1-score (weighted)**: >0.88
- **Inference latency**: <100ms (p95)
- **Model size**: <500MB

### Intent Categories
1. **question_answering**: General knowledge queries
2. **creative_writing**: Story, poem, content generation
3. **code_generation**: Programming tasks
4. **data_analysis**: Data insights and analytics
5. **reasoning**: Logic and problem-solving
6. **summarization**: Text condensation
7. **translation**: Language conversion
8. **conversation**: Dialogue and chat
9. **task_planning**: Project and task organization
10. **problem_solving**: Issue resolution

## Training Pipeline

### Data Flow
```
Raw Data → Preprocessing → Feature Extraction → Augmentation → Tokenization → Training
    ↓            ↓              ↓                    ↓              ↓           ↓
   JSON      Clean Text    Complexity Score    2x Samples    Token IDs    Model
```

### Training Process
1. **Data Preparation**
   - Load raw data (JSON/JSONL/CSV)
   - Clean and normalize text
   - Extract features
   - Split into train/val/test
   - Apply augmentation
   - Tokenize with DeBERTa tokenizer

2. **Model Training**
   - Initialize DeBERTa-v3 base model
   - Add classification head
   - Train with AdamW optimizer
   - Cosine learning rate schedule
   - Early stopping on validation F1

3. **Hyperparameter Tuning**
   - Optuna-based optimization
   - Search space:
     - Learning rate: 1e-5 to 5e-5
     - Batch size: 16, 32, 64
     - Dropout: 0.1 to 0.5
     - Pooling strategy: cls, mean, max, attention
   - Median pruning for efficiency

4. **Model Selection**
   - Track all experiments in MLflow
   - Select based on validation performance
   - Save best model checkpoint

## Evaluation Pipeline

### Metrics Calculated
- **Classification Metrics**: Accuracy, Precision, Recall, F1-score
- **Ranking Metrics**: Top-k accuracy, ROC-AUC
- **Calibration Metrics**: ECE (Expected Calibration Error)
- **Confidence Analysis**: Distribution plots, calibration curves

### Error Analysis
- Confusion matrix visualization
- Misclassification examples
- Low-confidence correct predictions
- Per-class performance breakdown

## Production Deployment

### Model Serving (Coming Soon)
```python
# TorchServe deployment
torch-model-archiver \
    --model-name intent_classifier \
    --version 1.0 \
    --model-file src/models/intent_classifier_model.py \
    --serialized-file models/production/model.pt \
    --handler handlers/intent_handler.py

torchserve --start \
    --model-store model_store \
    --models intent_classifier=intent_classifier.mar
```

### Integration with Backend
The trained model integrates with the Intent Classification Service:
- Model loaded on service startup
- Batch inference support
- Result caching with Redis
- Prometheus metrics export

## Monitoring & Maintenance

### Model Monitoring (Planned)
- **Performance Tracking**: Real-time accuracy monitoring
- **Data Drift Detection**: Input distribution changes
- **Concept Drift**: Output distribution shifts
- **A/B Testing**: Gradual rollout framework

### Retraining Pipeline
1. Collect new labeled data
2. Validate data quality
3. Merge with existing dataset
4. Retrain with transfer learning
5. Compare performance
6. Deploy if improved

## Advanced Features

### Custom Intent Addition
To add new intent categories:
1. Update `INTENT_SAMPLES` in `generate_sample_data.py`
2. Modify `intent_labels` in `data_processor.py`
3. Update model config for new label count
4. Retrain with transfer learning

### Multi-Language Support
Future enhancement for multilingual classification:
- Use multilingual DeBERTa (mdeberta-v3-base)
- Language-specific preprocessing
- Cross-lingual training data

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**
   - Reduce batch size in config
   - Enable gradient accumulation
   - Use mixed precision training

2. **Poor Performance**
   - Check data distribution
   - Increase training data
   - Try different pooling strategies
   - Adjust learning rate

3. **Slow Training**
   - Enable multi-GPU training
   - Use larger batch sizes
   - Reduce validation frequency

## Next Steps

1. **Model Serving Infrastructure**: Set up TorchServe for production deployment
2. **CI/CD Pipeline**: Automated testing and deployment
3. **Monitoring System**: Real-time performance tracking
4. **A/B Testing**: Framework for model comparison
5. **Active Learning**: Identify and label uncertain examples

## Resources

- [DeBERTa Paper](https://arxiv.org/abs/2006.03654)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [DVC Documentation](https://dvc.org/doc)
- [Optuna Documentation](https://optuna.readthedocs.io/)

## Contributing

When contributing to the ML pipeline:
1. Follow the existing code structure
2. Add comprehensive docstrings
3. Include unit tests for new features
4. Update this documentation
5. Run evaluation before submitting