#!/usr/bin/env python3
"""Wave 5 Pipeline with TQDM Progress Tracking"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime

from tqdm import tqdm
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.syntax import Syntax
from rich import box

# Initialize Rich console for pretty output
console = Console()

# Configuration
DATA_PATH = "data_generation/openai_training_data.json"
MODEL_DIR = "models/distilbert_intent_classifier"
ONNX_DIR = "models/onnx"
VALIDATION_DIR = "validation_results"

# Pipeline steps with estimated durations (in seconds)
PIPELINE_STEPS = [
    {
        "name": "Verify Training Data",
        "command": None,  # Custom check
        "estimated_duration": 2,
        "critical": True
    },
    {
        "name": "Train DistilBERT Model",
        "command": [
            "python", "train_distilbert.py",
            "--data-path", DATA_PATH,
            "--output-dir", MODEL_DIR,
            "--num-epochs", "5",
            "--batch-size", "32",
            "--learning-rate", "5e-5",
            "--fp16",
            "--export-onnx"
        ],
        "estimated_duration": 1800,  # 30 minutes
        "critical": True
    },
    {
        "name": "Validate Model Accuracy",
        "command": [
            "python", "scripts/validate_model_accuracy.py",
            "--model-path", MODEL_DIR,
            "--data-path", DATA_PATH,
            "--output-dir", VALIDATION_DIR,
            "--show-examples",
            "--num-examples", "10"
        ],
        "estimated_duration": 60,
        "critical": True
    },
    {
        "name": "Export to Optimized ONNX",
        "command": [
            "python", "scripts/export_to_onnx.py",
            "--model-path", MODEL_DIR,
            "--output-dir", ONNX_DIR,
            "--model-name", "distilbert_intent_classifier",
            "--benchmark",
            "--quantize"
        ],
        "estimated_duration": 120,
        "critical": False
    },
    {
        "name": "Generate Integration Code",
        "command": [
            "python", "scripts/integrate_distilbert_model.py",
            "--model-path", f"{ONNX_DIR}/distilbert_intent_classifier_optimized.onnx",
            "--use-onnx",
            "--generate-integration"
        ],
        "estimated_duration": 10,
        "critical": False
    }
]


def verify_training_data() -> bool:
    """Verify training data exists and is valid."""
    if not Path(DATA_PATH).exists():
        console.print(f"[red]❌ Training data not found at {DATA_PATH}[/red]")
        console.print("\n[yellow]Please run Wave 3 data generation first:[/yellow]")
        console.print("  cd data_generation")
        console.print("  python generate_training_data.py --examples-per-intent 1000")
        return False
    
    # Check data validity
    try:
        with open(DATA_PATH, 'r') as f:
            data = json.load(f)
        example_count = len(data.get('examples', []))
        console.print(f"[green]✅ Found {example_count:,} training examples[/green]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Error reading training data: {e}[/red]")
        return False


def run_command_with_progress(command: List[str], step_name: str, pbar: tqdm) -> Tuple[bool, str]:
    """Run a command with progress updates."""
    try:
        # Start the process
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        output_lines = []
        
        # Read output line by line
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            
            if line:
                output_lines.append(line.strip())
                
                # Update progress bar description with key info
                if "Epoch" in line:
                    pbar.set_description(f"{step_name}: {line.strip()[:50]}...")
                elif "accuracy" in line.lower() or "f1" in line.lower():
                    pbar.set_description(f"{step_name}: {line.strip()}")
                elif "step" in line.lower() and "/" in line:
                    # Extract step progress
                    try:
                        parts = line.split()
                        for part in parts:
                            if "/" in part and part.replace("/", "").replace(",", "").isdigit():
                                current, total = part.replace(",", "").split("/")
                                progress = int(current) / int(total)
                                pbar.update(progress - pbar.n)
                    except:
                        pass
        
        # Get return code
        return_code = process.wait()
        
        # Capture any stderr
        stderr = process.stderr.read()
        if stderr:
            output_lines.extend(stderr.strip().split('\n'))
        
        output = '\n'.join(output_lines)
        return return_code == 0, output
        
    except Exception as e:
        return False, str(e)


def run_pipeline():
    """Run the complete Wave 5 pipeline with progress tracking."""
    start_time = datetime.now()
    
    # Display header
    console.print("\n[bold cyan]=" * 50)
    console.print("[bold cyan]Wave 5: Fine-tune DistilBERT Model Pipeline")
    console.print("[bold cyan]=" * 50 + "\n")
    
    # Calculate total estimated time
    total_duration = sum(step['estimated_duration'] for step in PIPELINE_STEPS)
    
    # Results tracking
    results = {
        "steps_completed": 0,
        "steps_failed": 0,
        "warnings": [],
        "errors": [],
        "metrics": {}
    }
    
    # Main progress bar for overall pipeline
    with tqdm(total=len(PIPELINE_STEPS), desc="Pipeline Progress", unit="step") as main_pbar:
        
        for i, step in enumerate(PIPELINE_STEPS):
            step_name = step['name']
            console.print(f"\n[bold blue]Step {i+1}/{len(PIPELINE_STEPS)}: {step_name}[/bold blue]")
            console.print("-" * 50)
            
            # Step progress bar
            with tqdm(total=1.0, desc=step_name, unit="progress", leave=False) as step_pbar:
                
                # Special handling for verification step
                if step['command'] is None:
                    success = verify_training_data()
                    step_pbar.update(1.0)
                else:
                    # Run command with progress monitoring
                    success, output = run_command_with_progress(
                        step['command'], 
                        step_name, 
                        step_pbar
                    )
                    
                    # Extract metrics from output if available
                    if "accuracy" in output.lower():
                        for line in output.split('\n'):
                            if "test accuracy" in line.lower() and ":" in line:
                                try:
                                    accuracy = float(line.split(":")[-1].strip().rstrip('%')) / 100
                                    results['metrics']['test_accuracy'] = accuracy
                                except:
                                    pass
                
                # Update results
                if success:
                    console.print(f"[green]✅ {step_name} completed successfully[/green]")
                    results['steps_completed'] += 1
                else:
                    if step['critical']:
                        console.print(f"[red]❌ {step_name} failed![/red]")
                        results['steps_failed'] += 1
                        results['errors'].append(f"{step_name} failed")
                        
                        # Show error details
                        if step['command'] and 'output' in locals():
                            error_lines = output.split('\n')[-10:]  # Last 10 lines
                            console.print("\n[red]Error details:[/red]")
                            for line in error_lines:
                                if line.strip():
                                    console.print(f"  {line}")
                        
                        main_pbar.close()
                        return results
                    else:
                        console.print(f"[yellow]⚠️  {step_name} failed (non-critical)[/yellow]")
                        results['warnings'].append(f"{step_name} failed (non-critical)")
            
            # Update main progress
            main_pbar.update(1)
            
            # Show progress stats
            elapsed = (datetime.now() - start_time).total_seconds()
            estimated_remaining = (total_duration - elapsed) if elapsed < total_duration else 0
            console.print(f"[dim]Elapsed: {elapsed:.0f}s | Est. remaining: {estimated_remaining:.0f}s[/dim]")
    
    # Display summary
    display_summary(results, start_time)
    
    return results


def display_summary(results: Dict[str, Any], start_time: datetime):
    """Display a comprehensive summary of the pipeline execution."""
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Create summary panel
    summary_content = f"""
[bold green]Pipeline Complete![/bold green]

⏱️  Total Duration: {duration/60:.1f} minutes
✅ Steps Completed: {results['steps_completed']}/{len(PIPELINE_STEPS)}
❌ Steps Failed: {results['steps_failed']}
⚠️  Warnings: {len(results['warnings'])}
"""
    
    if results['metrics'].get('test_accuracy'):
        accuracy = results['metrics']['test_accuracy']
        accuracy_color = "green" if accuracy >= 0.88 else "red"
        summary_content += f"\n📊 Test Accuracy: [{accuracy_color}]{accuracy*100:.2f}%[/{accuracy_color}]"
        if accuracy >= 0.88:
            summary_content += " [green]✅ Meets requirement[/green]"
        else:
            summary_content += " [red]❌ Below requirement[/red]"
    
    console.print("\n" + "=" * 50)
    console.print(Panel(summary_content, title="Pipeline Summary", box=box.ROUNDED))
    
    # Show file locations
    files_table = Table(title="Generated Files", box=box.SIMPLE)
    files_table.add_column("Type", style="cyan")
    files_table.add_column("Location", style="green")
    
    files_table.add_row("Model", MODEL_DIR)
    files_table.add_row("ONNX", f"{ONNX_DIR}/distilbert_intent_classifier_optimized.onnx")
    files_table.add_row("Validation", VALIDATION_DIR)
    files_table.add_row("Integration", "distilbert_ml_classifier.py")
    
    console.print("\n", files_table)
    
    # Show next steps
    next_steps = """
[bold]🚀 Next Steps:[/bold]

1. Copy integration code to intent classifier service:
   [cyan]cp distilbert_ml_classifier.py ../backend/services/intent-classifier/app/models/[/cyan]

2. Update intent classifier to use new model:
   - Add model selection logic
   - Implement A/B testing
   - Deploy with feature flags

3. Monitor performance in production:
   - Track inference latency
   - Monitor accuracy on real data
   - Collect user feedback
"""
    
    console.print(Panel(next_steps, title="What's Next", box=box.ROUNDED))
    
    # Show warnings if any
    if results['warnings']:
        console.print("\n[yellow]⚠️  Warnings:[/yellow]")
        for warning in results['warnings']:
            console.print(f"  - {warning}")


def main():
    """Main entry point."""
    try:
        results = run_pipeline()
        
        # Exit with appropriate code
        if results['steps_failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        console.print("\n[red]Pipeline interrupted by user[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Pipeline error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()