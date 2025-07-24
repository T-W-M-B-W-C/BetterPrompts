# Synthetic Training Data Generation

This module generates high-quality synthetic training data for the intent classification system.

## Overview

The data generation system creates diverse, realistic training examples for 10 different intent types:
- question_answering
- creative_writing  
- code_generation
- data_analysis
- reasoning
- summarization
- translation
- conversation
- task_planning
- problem_solving

## Features

- **10,000+ Examples**: 1000 examples per intent type
- **2000 Edge Cases**: Ambiguous, typos, extreme lengths, multi-language
- **Audience Diversity**: Child, beginner, intermediate, expert, general
- **Complexity Levels**: Simple, moderate, complex
- **Quality Validation**: Automatic validation and metrics
- **OpenAI Integration**: Optional GPT-3.5 generation for more variety
- **Rate Limiting**: Smart rate limiting for API calls

## Installation

```bash
# Install dependencies
cd ml-pipeline/data_generation
pip install -r requirements.txt

# Set OpenAI API key (optional)
export OPENAI_API_KEY=your-api-key-here
```

## Usage

### Quick Start (Templates Only)

Generate dataset using only templates (no API costs):

```bash
python generate_training_data.py --test
```

### Full Dataset Generation

#### Using Templates Only (Free)
```bash
python generate_training_data.py \
  --examples-per-intent 1000 \
  --edge-cases 2000 \
  --output training_data.json
```

#### Using OpenAI API (Better Diversity)
```bash
python generate_training_data.py \
  --use-openai \
  --examples-per-intent 1000 \
  --edge-cases 2000 \
  --temperature 0.8 \
  --output training_data_openai.json
```

### Validate Existing Dataset

```bash
python generate_training_data.py --validate-only training_data.json
```

## CLI Options

```
Options:
  --examples-per-intent N   Examples per intent type (default: 1000)
  --edge-cases N           Number of edge cases (default: 2000)
  --use-openai            Use OpenAI API for generation
  --output PATH           Output file path (default: training_data.json)
  --api-key KEY          OpenAI API key (or use env var)
  --temperature FLOAT     OpenAI temperature (default: 0.8)
  --batch-size N         Batch size for API calls (default: 10)
  --test                 Generate small test batch
  --validate-only PATH   Validate existing dataset
  --seed N              Random seed for reproducibility
  --log-level LEVEL     Logging level (DEBUG/INFO/WARNING/ERROR)
```

## Output Format

The generated dataset follows this schema:

```json
{
  "metadata": {
    "generated_at": "2024-01-24T12:00:00",
    "total_examples": 12000,
    "config": {
      "examples_per_intent": 1000,
      "edge_cases": 2000,
      "use_openai": false,
      "temperature": 0.8
    },
    "statistics": {
      "total_generated": 12000,
      "intent_question_answering": 1000,
      ...
    },
    "diversity_metrics": {
      "audience_distribution": {...},
      "complexity_distribution": {...},
      "uniqueness_score": 0.85,
      "topic_coverage": 0.92,
      "style_variety": 0.78
    }
  },
  "examples": [
    {
      "text": "How does machine learning work?",
      "intent": "question_answering",
      "audience": "beginner",
      "complexity": "simple",
      "confidence": 0.92,
      "metadata": {
        "generation_method": "template",
        "style": "formal",
        "technical_level": 3
      },
      "generated_at": "2024-01-24T12:00:01"
    },
    ...
  ]
}
```

## Quality Metrics

The system automatically calculates:

- **Uniqueness Score**: Measures diversity based on n-gram analysis
- **Topic Coverage**: Percentage of intent types covered
- **Style Variety**: Different writing styles represented
- **Audience Distribution**: Balance across audience levels
- **Complexity Distribution**: Balance across complexity levels

## Validation

Each example is validated for:

- ✅ Proper JSON structure
- ✅ Valid intent labels
- ✅ Reasonable text length (3-1000 chars)
- ✅ Confidence scores (0.3-0.99)
- ✅ Text quality (word diversity, no excessive repetition)
- ✅ Intent-text matching (keywords align with declared intent)

## Cost Estimation

When using OpenAI:
- ~$0.0015 per example (GPT-3.5-turbo)
- Full dataset (12K examples): ~$18
- Includes rate limiting to stay within tier limits

## Architecture

```
data_generation/
├── openai_client.py       # Rate-limited OpenAI client
├── prompt_templates.py    # Templates for all intent types
├── diversity_strategies.py # Diversity and edge case generation
├── data_generator.py      # Main orchestration logic
├── data_validator.py      # Quality validation
├── generate_training_data.py # CLI interface
└── test_generation.py     # Test suite
```

## Testing

Run the test suite:

```bash
python test_generation.py
```

This will:
1. Test all components individually
2. Generate a small test dataset
3. Validate the output
4. Test the CLI interface

## Best Practices

1. **Start Small**: Test with `--test` flag first
2. **Monitor Costs**: Check estimated costs before using OpenAI
3. **Validate Output**: Always validate generated datasets
4. **Use Seeds**: For reproducible generation, use `--seed`
5. **Check Logs**: Review `data_generation.log` for issues

## Troubleshooting

### Import Errors
```bash
# Make sure you're in the right directory
cd ml-pipeline/data_generation
# Install dependencies
pip install -r requirements.txt
```

### OpenAI Rate Limits
- The system automatically handles rate limits
- Reduce `--batch-size` if hitting limits
- Check usage at https://platform.openai.com/usage

### Memory Issues
- Reduce `--examples-per-intent` 
- Generate in batches and combine JSON files

## Next Steps

After generation:
1. Move `training_data.json` to ml-pipeline data directory
2. Use for training intent classifier models
3. Evaluate model performance
4. Iterate on generation parameters if needed