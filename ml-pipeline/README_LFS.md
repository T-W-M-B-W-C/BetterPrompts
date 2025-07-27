# Git LFS Setup for ML Models

This project uses Git Large File Storage (LFS) to manage large ML model files and training data.

## Prerequisites

1. Install Git LFS:
   ```bash
   # macOS
   brew install git-lfs
   
   # Ubuntu/Debian
   sudo apt-get install git-lfs
   
   # Windows
   # Download from https://git-lfs.github.com/
   ```

2. Initialize Git LFS in your local repository:
   ```bash
   git lfs install
   ```

## Tracked File Types

The following file types are automatically tracked by Git LFS:

- **ML Model Files**: `*.safetensors`, `*.pt`, `*.bin`, `*.onnx`, `*.h5`, `*.pkl`, `*.pth`
- **Training Data**: Large JSON files in `ml-pipeline/data_generation/`
- **Compiled Binaries**: `backend/services/*/main`, `*.exe`

## Working with LFS Files

### Pulling LFS Files
When you clone or pull the repository, LFS files are downloaded automatically:
```bash
git clone https://github.com/CodeBlackwell/BetterPrompts.git
# LFS files are downloaded automatically
```

To manually download LFS files:
```bash
git lfs pull
```

### Adding New Model Files
Simply add files as normal - Git LFS will handle them automatically:
```bash
# Train your model
python train_model.py

# Add the model file (LFS handles it automatically)
git add ml-pipeline/trained_models/my_model.safetensors
git commit -m "Add trained model"
git push
```

### Checking LFS Status
```bash
# See which files are tracked by LFS
git lfs ls-files

# See LFS tracking patterns
git lfs track

# Check LFS file sizes
git lfs status
```

## Storage Limits

GitHub provides 1 GB of free LFS storage and 1 GB/month bandwidth. For this project:
- Each model checkpoint is ~267MB
- Training data files can be 5-50MB
- Monitor usage at: https://github.com/settings/billing

## Troubleshooting

### LFS files showing as text pointers
If you see pointer files instead of actual content:
```bash
git lfs pull
```

### "This repository is over its data quota" error
- Check your LFS usage on GitHub
- Consider upgrading your plan or removing old model versions

### Slow clone/pull operations
LFS files are downloaded separately from regular Git objects. For faster operations:
```bash
# Clone without LFS files
GIT_LFS_SKIP_SMUDGE=1 git clone <url>

# Then pull only the LFS files you need
git lfs pull --include="ml-pipeline/trained_models/final/*"
```

## Best Practices

1. **Don't commit temporary model files** - Only commit final or milestone models
2. **Use descriptive names** - Include version, date, or performance metrics in filenames
3. **Document model metadata** - Keep a JSON/YAML file with model training parameters
4. **Clean up old versions** - Remove outdated model files to save LFS storage

## Example Workflow

```bash
# 1. Train a model
python ml-pipeline/scripts/train_model.py

# 2. Evaluate and save only the best model
python ml-pipeline/scripts/evaluate_and_save.py

# 3. Add model and metadata
git add ml-pipeline/trained_models/intent_classifier_v2.0.safetensors
git add ml-pipeline/trained_models/intent_classifier_v2.0_metadata.json

# 4. Commit and push
git commit -m "feat: add intent classifier v2.0 with 94% accuracy"
git push
```