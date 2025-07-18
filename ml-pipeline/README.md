# BetterPrompts ML Pipeline

This directory contains the machine learning pipeline for training, evaluating, and serving the intent classification and prompt enhancement models.

## Architecture Overview

```
ml-pipeline/
├── data/                    # Data versioning with DVC
│   ├── raw/                # Original, immutable data
│   ├── processed/          # Cleaned, transformed data
│   ├── external/           # External datasets
│   └── interim/            # Intermediate data
├── models/                 # Model artifacts
│   ├── checkpoints/        # Training checkpoints
│   ├── production/         # Production-ready models
│   └── experiments/        # Experimental models
├── notebooks/              # Jupyter notebooks for exploration
├── src/                    # Source code
│   ├── data/              # Data processing scripts
│   ├── features/          # Feature engineering
│   ├── models/            # Model definitions and training
│   ├── evaluation/        # Model evaluation metrics
│   ├── serving/           # Model serving infrastructure
│   ├── monitoring/        # Model monitoring and drift detection
│   └── utils/             # Utility functions
├── tests/                  # Unit and integration tests
├── configs/                # Configuration files
└── scripts/                # Automation scripts
```

## Key Components

### 1. Data Pipeline
- **DVC**: Data version control for reproducibility
- **Preprocessing**: Text normalization, tokenization, augmentation
- **Feature Engineering**: Embeddings, semantic features, complexity metrics

### 2. Model Training
- **DeBERTa-v3**: Fine-tuned for intent classification
- **Hyperparameter Tuning**: Optuna-based optimization
- **Distributed Training**: Multi-GPU support with Horovod

### 3. Experiment Tracking
- **MLflow**: Experiment tracking and model registry
- **Metrics**: Accuracy, F1, precision, recall, latency
- **Artifacts**: Models, configs, visualizations

### 4. Model Serving
- **TorchServe**: Production model serving
- **Model Registry**: Version control for models
- **A/B Testing**: Gradual rollout framework

### 5. Monitoring
- **Drift Detection**: Data and concept drift monitoring
- **Performance Metrics**: Real-time model performance
- **Alerting**: Automated alerts for degradation

## Quick Start

### Setup Environment
```bash
cd ml-pipeline
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Initialize DVC
```bash
dvc init
dvc remote add -d storage s3://betterprompts-ml-data
```

### Train Model
```bash
python scripts/train_intent_classifier.py --config configs/intent_classifier.yaml
```

### Start MLflow UI
```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns
```

### Serve Model
```bash
torchserve --start --model-store models/production --models intent_classifier=intent_classifier.mar
```

## Model Architecture

### Intent Classifier (DeBERTa-v3)
- **Base Model**: microsoft/deberta-v3-base
- **Task**: Multi-class classification (10 intent categories)
- **Input**: User prompts (max 512 tokens)
- **Output**: Intent probabilities + complexity score

### Training Data Format
```json
{
  "text": "Help me write a function to calculate fibonacci numbers",
  "intent": "code_generation",
  "complexity": 0.6,
  "metadata": {
    "language": "python",
    "domain": "algorithms"
  }
}
```

## Performance Targets
- **Accuracy**: >90% on test set
- **Latency**: <100ms p95
- **Throughput**: >1000 RPS
- **Model Size**: <500MB

## CI/CD Pipeline
1. **Data Validation**: Schema validation, quality checks
2. **Model Training**: Automated training on new data
3. **Evaluation**: Performance regression tests
4. **Deployment**: Automated rollout with canary testing