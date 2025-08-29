#!/usr/bin/env python3
"""Simplified data generation script with minimal dependencies."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from loguru import logger
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

console = Console()

# Configure OpenAI
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    console.print("[bold red]Error: OPENAI_API_KEY not found in environment![/bold red]")
    console.print("Please set it with: export OPENAI_API_KEY=your-key-here")
    sys.exit(1)

client = openai.OpenAI(api_key=api_key)

# Intent types
INTENTS = [
    "question_answering",
    "creative_writing",
    "code_generation",
    "data_analysis",
    "reasoning",
    "summarization",
    "translation",
    "conversation",
    "task_planning",
    "problem_solving"
]

def generate_prompt(intent: str) -> str:
    """Generate a prompt for a specific intent."""
    prompts = {
        "question_answering": "Generate a question that someone might ask to learn about a topic. Make it natural and realistic.",
        "creative_writing": "Generate a request for creative writing like a story, poem, or narrative.",
        "code_generation": "Generate a request for writing code or implementing a programming solution.",
        "data_analysis": "Generate a request for analyzing data or extracting insights from information.",
        "reasoning": "Generate a request that requires logical reasoning or problem-solving.",
        "summarization": "Generate a request to summarize or condense information.",
        "translation": "Generate a request to translate text between languages.",
        "conversation": "Generate a conversational prompt or discussion starter.",
        "task_planning": "Generate a request for planning or organizing tasks and activities.",
        "problem_solving": "Generate a request for solving a specific problem or issue."
    }
    
    base_prompt = prompts.get(intent, "Generate a user request.")
    return f"{base_prompt} Return only the user's request text, nothing else."

def generate_examples(intent: str, count: int = 10) -> list:
    """Generate examples for a specific intent."""
    examples = []
    
    console.print(f"[cyan]Generating {count} examples for {intent}...[/cyan]")
    
    for i in range(count):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates diverse user prompts."},
                    {"role": "user", "content": generate_prompt(intent)}
                ],
                temperature=0.8,
                max_tokens=150
            )
            
            text = response.choices[0].message.content.strip()
            
            example = {
                "text": text,
                "intent": intent,
                "audience": "general",
                "complexity": "moderate",
                "confidence": 0.85,
                "metadata": {
                    "generation_method": "openai",
                    "model": "gpt-3.5-turbo"
                },
                "generated_at": datetime.now().isoformat()
            }
            
            examples.append(example)
            console.print(f"  [{i+1}/{count}] ✓", end="\r")
            
        except Exception as e:
            logger.error(f"Error generating example: {e}")
            console.print(f"  [{i+1}/{count}] ✗ Error: {e}")
    
    console.print(f"[green]Generated {len(examples)} examples for {intent}[/green]")
    return examples

def main():
    """Main function."""
    console.print("[bold blue]Simple Training Data Generator[/bold blue]\n")
    
    # Generate a small dataset
    all_examples = []
    examples_per_intent = 5  # Small number for testing
    
    for intent in INTENTS:
        examples = generate_examples(intent, examples_per_intent)
        all_examples.extend(examples)
    
    # Create dataset
    dataset = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_examples": len(all_examples),
            "config": {
                "examples_per_intent": examples_per_intent,
                "model": "gpt-3.5-turbo",
                "temperature": 0.8
            }
        },
        "examples": all_examples
    }
    
    # Save to file
    output_path = Path("simple_training_data.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    console.print(f"\n[bold green]Dataset saved to: {output_path}[/bold green]")
    console.print(f"Total examples: {len(all_examples)}")
    
    # Show sample
    console.print("\n[bold]Sample examples:[/bold]")
    for i, example in enumerate(all_examples[:3]):
        console.print(f"\n{i+1}. Intent: [cyan]{example['intent']}[/cyan]")
        console.print(f"   Text: {example['text'][:80]}...")

if __name__ == "__main__":
    main()