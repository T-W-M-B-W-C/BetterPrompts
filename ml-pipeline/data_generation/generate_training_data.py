#!/usr/bin/env python3
"""CLI script for generating synthetic training data for intent classification."""

import asyncio
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
import json

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from loguru import logger
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from data_generator import TrainingDataGenerator
from data_validator import DataValidator
from prompt_templates import IntentType


# Load environment variables
load_dotenv()

console = Console()


def setup_logging(log_level: str = "INFO"):
    """Set up logging configuration."""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Also log to file
    log_file = Path("data_generation.log")
    logger.add(
        log_file,
        level="DEBUG",
        rotation="10 MB",
        retention="7 days"
    )


def print_banner():
    """Print welcome banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║          Synthetic Training Data Generator                 ║
║              Intent Classification v1.0                    ║
╚═══════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold blue"))


def print_configuration(args):
    """Print generation configuration."""
    table = Table(title="Generation Configuration", show_header=True)
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Examples per intent", str(args.examples_per_intent))
    table.add_row("Edge cases", str(args.edge_cases))
    table.add_row("Total examples", str(args.examples_per_intent * len(IntentType) + args.edge_cases))
    table.add_row("Use OpenAI", "Yes" if args.use_openai else "No (Templates only)")
    table.add_row("Output file", str(args.output))
    table.add_row("Batch size", str(args.batch_size))
    table.add_row("Temperature", str(args.temperature))
    
    console.print(table)


async def generate_small_test_batch(generator: TrainingDataGenerator, output_path: Path):
    """Generate a small test batch for validation."""
    console.print("\n[bold yellow]Generating small test batch...[/bold yellow]")
    
    # Generate 2 examples per intent + 10 edge cases
    test_dataset = await generator.generate_full_dataset(
        examples_per_intent=2,
        edge_case_count=10,
        use_openai=False,  # Use templates for quick test
        output_path=output_path
    )
    
    return test_dataset


async def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic training data for intent classification",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Generation parameters
    parser.add_argument(
        "--examples-per-intent",
        type=int,
        default=1000,
        help="Number of examples to generate per intent type (default: 1000)"
    )
    
    parser.add_argument(
        "--edge-cases",
        type=int,
        default=2000,
        help="Number of edge cases to generate (default: 2000)"
    )
    
    parser.add_argument(
        "--use-openai",
        action="store_true",
        help="Use OpenAI API for generation (requires OPENAI_API_KEY)"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("training_data.json"),
        help="Output file path (default: training_data.json)"
    )
    
    # OpenAI parameters
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (can also use OPENAI_API_KEY env var)"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.8,
        help="Temperature for OpenAI generation (default: 0.8)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for OpenAI requests (default: 10)"
    )
    
    # Other options
    parser.add_argument(
        "--test",
        action="store_true",
        help="Generate a small test batch (30 examples)"
    )
    
    parser.add_argument(
        "--validate-only",
        type=Path,
        help="Validate an existing dataset file"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level)
    
    # Print banner
    print_banner()
    
    # Validate only mode
    if args.validate_only:
        console.print(f"\n[bold cyan]Validating dataset: {args.validate_only}[/bold cyan]")
        validator = DataValidator()
        result = validator.validate_file(args.validate_only)
        
        # Generate report
        report_path = args.validate_only.with_suffix('.validation_report.txt')
        report = validator.generate_validation_report(result, report_path)
        
        console.print(report)
        
        if result.is_valid:
            console.print("[bold green]✓ Dataset validation passed![/bold green]")
            return 0
        else:
            console.print("[bold red]✗ Dataset validation failed![/bold red]")
            return 1
    
    # Check API key if using OpenAI
    if args.use_openai:
        api_key = args.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            console.print("[bold red]Error: OpenAI API key required![/bold red]")
            console.print("Set OPENAI_API_KEY environment variable or use --api-key")
            return 1
    else:
        api_key = None
        console.print("[yellow]Note: Using template generation only (no OpenAI)[/yellow]")
    
    # Set random seed if provided
    if args.seed:
        import random
        import numpy as np
        random.seed(args.seed)
        np.random.seed(args.seed)
        console.print(f"[cyan]Random seed set to: {args.seed}[/cyan]")
    
    # Initialize generator
    try:
        generator = TrainingDataGenerator(api_key=api_key)
        
        # Update configuration
        generator.config["temperature"] = args.temperature
        generator.config["batch_size"] = args.batch_size
        
    except Exception as e:
        console.print(f"[bold red]Error initializing generator: {e}[/bold red]")
        return 1
    
    # Test mode
    if args.test:
        output_path = Path("test_training_data.json")
        await generate_small_test_batch(generator, output_path)
        console.print(f"\n[bold green]Test batch saved to: {output_path}[/bold green]")
        return 0
    
    # Print configuration
    print_configuration(args)
    
    # Confirm generation
    if args.use_openai:
        total_examples = args.examples_per_intent * len(IntentType) + args.edge_cases
        estimated_cost = total_examples * 0.0015  # Rough estimate
        
        console.print(f"\n[yellow]Estimated OpenAI cost: ${estimated_cost:.2f}[/yellow]")
        
        confirm = console.input("\n[bold]Proceed with generation? [y/N]: [/bold]")
        if confirm.lower() != 'y':
            console.print("[red]Generation cancelled.[/red]")
            return 0
    
    # Generate dataset
    try:
        console.print("\n[bold blue]Starting generation...[/bold blue]")
        start_time = datetime.now()
        
        dataset = await generator.generate_full_dataset(
            examples_per_intent=args.examples_per_intent,
            edge_case_count=args.edge_cases,
            use_openai=args.use_openai,
            output_path=args.output
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        console.print(f"\n[bold green]Generation completed in {duration:.1f} seconds![/bold green]")
        console.print(f"[green]Dataset saved to: {args.output}[/green]")
        
        # Save metadata
        metadata_path = args.output.with_suffix('.metadata.json')
        metadata = {
            "generation_date": datetime.now().isoformat(),
            "duration_seconds": duration,
            "arguments": vars(args),
            "statistics": dataset["metadata"]["statistics"],
            "diversity_metrics": dataset["metadata"]["diversity_metrics"]
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        console.print(f"[green]Metadata saved to: {metadata_path}[/green]")
        
        return 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Generation interrupted by user.[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n[bold red]Error during generation: {e}[/bold red]")
        logger.exception("Generation failed")
        return 1


if __name__ == "__main__":
    # Run the async main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)