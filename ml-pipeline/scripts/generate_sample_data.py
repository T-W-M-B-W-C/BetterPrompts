#!/usr/bin/env python3
"""
Generate sample training data for intent classification
"""

import json
import random
from pathlib import Path
from typing import List, Dict
import click

# Sample prompts for each intent category
INTENT_SAMPLES = {
    "question_answering": [
        "What is the capital of France?",
        "How does photosynthesis work?",
        "Can you explain quantum computing in simple terms?",
        "What are the benefits of meditation?",
        "How do I change a tire?",
        "What's the difference between machine learning and AI?",
        "When was the internet invented?",
        "What causes earthquakes?",
        "How do vaccines work?",
        "What is blockchain technology?"
    ],
    "creative_writing": [
        "Write a short story about a time traveler",
        "Create a poem about the ocean",
        "Generate a creative product description for a smart water bottle",
        "Write a dialogue between two AI assistants",
        "Compose a haiku about programming",
        "Create a fictional news headline from the year 2050",
        "Write a character description for a cyberpunk novel",
        "Generate creative names for a coffee shop",
        "Write a limerick about debugging code",
        "Create a plot twist for a mystery novel"
    ],
    "code_generation": [
        "Write a Python function to calculate fibonacci numbers",
        "Create a React component for a todo list",
        "Generate SQL query to find top 10 customers by revenue",
        "Write a bash script to backup files",
        "Create a JavaScript function to validate email addresses",
        "Generate a Python class for a binary search tree",
        "Write CSS for a responsive navigation menu",
        "Create a REST API endpoint in Node.js",
        "Generate unit tests for a calculator function",
        "Write a Python decorator for logging function calls"
    ],
    "data_analysis": [
        "Analyze this sales data and identify trends",
        "What insights can you draw from this customer feedback?",
        "Calculate the correlation between these variables",
        "Perform sentiment analysis on these reviews",
        "Create a summary statistics report for this dataset",
        "Identify outliers in this financial data",
        "What patterns do you see in this time series?",
        "Compare the performance metrics across regions",
        "Analyze the user engagement metrics",
        "What are the key drivers of customer churn?"
    ],
    "reasoning": [
        "If all roses are flowers and some flowers fade quickly, can we conclude that some roses fade quickly?",
        "Solve this logic puzzle: Three boxes contain apples, oranges, and both...",
        "What are the ethical implications of AI in healthcare?",
        "Evaluate the pros and cons of remote work",
        "If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?",
        "What factors should be considered when choosing a programming language?",
        "Analyze the cause and effect relationship between these events",
        "What are the logical fallacies in this argument?",
        "Compare and contrast two different approaches to solving this problem",
        "What assumptions are being made in this scenario?"
    ],
    "summarization": [
        "Summarize this article about climate change",
        "Give me the key points from this meeting transcript",
        "Create a brief summary of this research paper",
        "What are the main takeaways from this book chapter?",
        "Summarize this technical documentation in simple terms",
        "Extract the important information from this email thread",
        "Provide a concise summary of this news article",
        "What are the key findings from this study?",
        "Summarize this product review",
        "Create an executive summary of this report"
    ],
    "translation": [
        "Translate 'Hello, how are you?' to Spanish",
        "How do you say 'Thank you very much' in Japanese?",
        "Translate this paragraph from English to French",
        "What's the German word for 'butterfly'?",
        "Convert this technical text to plain English",
        "Translate this menu from Italian to English",
        "How would you express this idiom in Chinese?",
        "Translate this error message to user-friendly language",
        "Convert this legal text to simple terms",
        "Translate this poem while preserving its meaning"
    ],
    "conversation": [
        "Hi! How are you today?",
        "Tell me about yourself",
        "What do you think about the weather?",
        "Can we discuss philosophy?",
        "I'm feeling stressed, any advice?",
        "What's your opinion on this topic?",
        "Let's have a friendly chat",
        "Can you help me practice for an interview?",
        "I'd like to discuss my career options",
        "What are your thoughts on recent tech trends?"
    ],
    "task_planning": [
        "Help me plan a birthday party for 20 people",
        "Create a study schedule for my exams",
        "I need to organize a team building event",
        "Plan a 7-day trip to Japan",
        "Help me create a workout routine",
        "Design a project timeline for app development",
        "Create a meal prep plan for the week",
        "Help me organize my home office",
        "Plan a marketing campaign for a new product",
        "Create a budget for a small business"
    ],
    "problem_solving": [
        "My computer is running slowly, how can I fix it?",
        "How can I improve team communication?",
        "What's the best way to learn a new language?",
        "How do I resolve conflicts with coworkers?",
        "My plants are dying, what should I do?",
        "How can I reduce my carbon footprint?",
        "What's the best approach to debug this code?",
        "How do I improve my public speaking skills?",
        "What strategies can help with procrastination?",
        "How can I optimize my website's performance?"
    ]
}

# Complexity modifiers to add to prompts
COMPLEXITY_MODIFIERS = {
    "low": ["", "please", "can you", "I need"],
    "medium": [
        "and explain your reasoning",
        "with examples",
        "in detail",
        "step by step",
        "and compare alternatives"
    ],
    "high": [
        "First analyze the problem, then provide multiple solutions with pros and cons",
        "Consider edge cases and potential issues",
        "Provide a comprehensive analysis including",
        "Break this down into steps and explain each part",
        "Analyze from multiple perspectives and synthesize"
    ]
}


def generate_sample(intent: str, base_prompt: str) -> Dict:
    """Generate a single training sample"""
    # Determine complexity
    complexity_level = random.choices(['low', 'medium', 'high'], weights=[0.4, 0.4, 0.2])[0]
    complexity_score = {'low': 0.3, 'medium': 0.6, 'high': 0.9}[complexity_level]
    
    # Add complexity modifier
    modifier = random.choice(COMPLEXITY_MODIFIERS[complexity_level])
    if modifier:
        if complexity_level == 'low':
            text = f"{modifier} {base_prompt.lower()}"
        else:
            text = f"{base_prompt} {modifier}"
    else:
        text = base_prompt
    
    # Add some variation
    if random.random() < 0.3:
        text = text.capitalize()
    
    # Create sample
    sample = {
        "text": text,
        "intent": intent,
        "complexity": complexity_score + random.uniform(-0.1, 0.1),  # Add noise
        "metadata": {
            "complexity_level": complexity_level,
            "base_prompt": base_prompt,
            "has_modifier": bool(modifier)
        }
    }
    
    return sample


def generate_dataset(num_samples: int = 1000) -> List[Dict]:
    """Generate a complete dataset"""
    samples = []
    samples_per_intent = num_samples // len(INTENT_SAMPLES)
    
    for intent, prompts in INTENT_SAMPLES.items():
        for _ in range(samples_per_intent):
            base_prompt = random.choice(prompts)
            sample = generate_sample(intent, base_prompt)
            samples.append(sample)
    
    # Shuffle samples
    random.shuffle(samples)
    
    return samples


def add_cross_intent_samples(samples: List[Dict], num_samples: int = 100) -> List[Dict]:
    """Add samples that could belong to multiple intents"""
    cross_intent_prompts = [
        ("Explain how to write a function that analyzes data", ["reasoning", "code_generation", "data_analysis"]),
        ("Translate this code comment to Spanish", ["translation", "code_generation"]),
        ("Write a creative story about solving a mystery", ["creative_writing", "problem_solving"]),
        ("Summarize this conversation about planning", ["summarization", "conversation", "task_planning"]),
        ("Help me understand and implement this algorithm", ["question_answering", "code_generation", "reasoning"])
    ]
    
    for _ in range(num_samples):
        prompt, possible_intents = random.choice(cross_intent_prompts)
        primary_intent = random.choice(possible_intents)
        
        sample = generate_sample(primary_intent, prompt)
        sample['metadata']['multi_intent'] = True
        sample['metadata']['possible_intents'] = possible_intents
        
        samples.append(sample)
    
    return samples


@click.command()
@click.option('--num-samples', default=1000, help='Number of samples to generate')
@click.option('--output-path', default='data/raw/training_data.json', help='Output file path')
@click.option('--add-cross-intent', is_flag=True, help='Add cross-intent samples')
def main(num_samples: int, output_path: str, add_cross_intent: bool):
    """Generate sample training data for intent classification"""
    # Generate base dataset
    samples = generate_dataset(num_samples)
    
    # Add cross-intent samples if requested
    if add_cross_intent:
        samples = add_cross_intent_samples(samples, num_samples // 10)
    
    # Create output directory
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save dataset
    with open(output_file, 'w') as f:
        json.dump(samples, f, indent=2)
    
    # Print statistics
    print(f"Generated {len(samples)} samples")
    print("\nIntent distribution:")
    intent_counts = {}
    for sample in samples:
        intent = sample['intent']
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    for intent, count in sorted(intent_counts.items()):
        print(f"  {intent}: {count} samples")
    
    print(f"\nDataset saved to: {output_file}")
    
    # Also save as JSONL for streaming
    jsonl_path = output_file.with_suffix('.jsonl')
    with open(jsonl_path, 'w') as f:
        for sample in samples:
            f.write(json.dumps(sample) + '\n')
    
    print(f"JSONL version saved to: {jsonl_path}")


if __name__ == "__main__":
    main()