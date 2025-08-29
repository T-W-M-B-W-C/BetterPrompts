#!/usr/bin/env python3
"""Test script to validate data generation with a small batch."""

import asyncio
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from data_generator import TrainingDataGenerator
from data_validator import DataValidator
from prompt_templates import IntentType, AudienceLevel, ComplexityLevel
from diversity_strategies import DiversityStrategy, EdgeCaseGenerator

from rich.console import Console
from rich import print as rprint

console = Console()


async def test_components():
    """Test individual components."""
    console.print("[bold blue]Testing Individual Components[/bold blue]\n")
    
    # Test 1: Prompt Templates
    console.print("1. Testing Prompt Templates...")
    try:
        from prompt_templates import prompt_manager, get_random_prompt
        
        # Test each intent
        for intent in list(IntentType)[:3]:  # Test first 3
            prompt = get_random_prompt(intent)
            console.print(f"  {intent.value}: [green]{prompt[:50]}...[/green]")
        
        console.print("  ✅ Prompt templates working\n")
    except Exception as e:
        console.print(f"  ❌ Error: {e}\n")
        return False
    
    # Test 2: Diversity Strategies
    console.print("2. Testing Diversity Strategies...")
    try:
        strategy = DiversityStrategy()
        
        # Generate diverse prompts
        prompt, metadata = strategy.generate_diverse_prompt(
            IntentType.QUESTION_ANSWERING,
            AudienceLevel.BEGINNER,
            ComplexityLevel.SIMPLE
        )
        
        console.print(f"  Generated: [green]{prompt[:50]}...[/green]")
        console.print(f"  Style: {metadata.get('style', 'unknown')}")
        console.print("  ✅ Diversity strategies working\n")
    except Exception as e:
        console.print(f"  ❌ Error: {e}\n")
        return False
    
    # Test 3: Edge Case Generator
    console.print("3. Testing Edge Case Generator...")
    try:
        edge_gen = EdgeCaseGenerator()
        
        # Test edge case
        prompt, intent, metadata = edge_gen.generate_edge_case("typos_and_errors")
        console.print(f"  Generated: [yellow]{prompt}[/yellow]")
        console.print(f"  Type: {metadata.get('edge_case_type', 'unknown')}")
        
        # Test ambiguous case
        prompt, intents, metadata = edge_gen.generate_ambiguous_example()
        console.print(f"  Ambiguous: [yellow]{prompt[:50]}...[/yellow]")
        console.print(f"  Possible intents: {len(intents)}")
        console.print("  ✅ Edge case generator working\n")
    except Exception as e:
        console.print(f"  ❌ Error: {e}\n")
        return False
    
    return True


async def test_small_generation():
    """Test generation with a small batch."""
    console.print("[bold blue]Testing Small Batch Generation[/bold blue]\n")
    
    try:
        # Create generator (without OpenAI)
        generator = TrainingDataGenerator()
        
        # Generate tiny dataset
        console.print("Generating test dataset (5 examples per intent + 10 edge cases)...")
        
        dataset = await generator.generate_full_dataset(
            examples_per_intent=5,
            edge_case_count=10,
            use_openai=False,  # Templates only
            output_path=Path("test_output.json")
        )
        
        console.print(f"\n✅ Generated {len(dataset['examples'])} examples")
        
        # Validate the dataset
        console.print("\n[bold blue]Validating Generated Dataset[/bold blue]\n")
        
        validator = DataValidator()
        result = validator.validate_dataset(dataset)
        
        # Print validation summary
        console.print(f"Valid examples: {result.valid_examples}/{result.total_examples}")
        console.print(f"Errors: {len(result.errors)}")
        console.print(f"Warnings: {len(result.warnings)}")
        
        if result.errors:
            console.print("\nFirst 5 errors:")
            for error in result.errors[:5]:
                console.print(f"  - {error.get('message', str(error))}")
        
        # Check diversity metrics
        metrics = dataset['metadata']['diversity_metrics']
        console.print("\n[bold blue]Diversity Metrics[/bold blue]")
        console.print(f"Uniqueness score: {metrics['uniqueness_score']:.2f}")
        console.print(f"Topic coverage: {metrics['topic_coverage']:.2f}")
        console.print(f"Style variety: {metrics['style_variety']:.2f}")
        
        # Sample some examples
        console.print("\n[bold blue]Sample Examples[/bold blue]")
        for i, example in enumerate(dataset['examples'][:5]):
            console.print(f"\n{i+1}. Intent: [cyan]{example['intent']}[/cyan]")
            console.print(f"   Text: {example['text'][:80]}...")
            console.print(f"   Audience: {example['audience']}, Complexity: {example['complexity']}")
            console.print(f"   Confidence: {example['confidence']:.2f}")
        
        return True
        
    except Exception as e:
        console.print(f"\n❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_cli():
    """Test CLI script."""
    console.print("\n[bold blue]Testing CLI Script[/bold blue]\n")
    
    import subprocess
    
    # Test help
    result = subprocess.run(
        [sys.executable, "generate_training_data.py", "--help"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        console.print("✅ CLI help works")
    else:
        console.print("❌ CLI help failed")
        return False
    
    # Test validation mode
    if Path("test_output.json").exists():
        result = subprocess.run(
            [sys.executable, "generate_training_data.py", "--validate-only", "test_output.json"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            console.print("✅ CLI validation mode works")
        else:
            console.print("❌ CLI validation mode failed")
    
    return True


async def main():
    """Run all tests."""
    console.print("\n" + "="*60)
    console.print("[bold cyan]Synthetic Data Generation Test Suite[/bold cyan]")
    console.print("="*60 + "\n")
    
    # Test components
    if not await test_components():
        console.print("[bold red]Component tests failed![/bold red]")
        return 1
    
    # Test generation
    if not await test_small_generation():
        console.print("[bold red]Generation test failed![/bold red]")
        return 1
    
    # Test CLI
    if not await test_cli():
        console.print("[bold red]CLI test failed![/bold red]")
        return 1
    
    console.print("\n[bold green]✅ All tests passed![/bold green]")
    console.print("\n[bold cyan]Next Steps:[/bold cyan]")
    console.print("1. To generate full dataset with templates only:")
    console.print("   [yellow]python generate_training_data.py --examples-per-intent 1000 --edge-cases 2000[/yellow]")
    console.print("\n2. To generate with OpenAI (requires API key):")
    console.print("   [yellow]python generate_training_data.py --use-openai --examples-per-intent 1000[/yellow]")
    console.print("\n3. To validate existing dataset:")
    console.print("   [yellow]python generate_training_data.py --validate-only training_data.json[/yellow]")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)