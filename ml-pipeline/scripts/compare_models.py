#!/usr/bin/env python3
"""
Compare DeBERTa and DistilBERT models for intent classification
Evaluates performance, speed, and resource usage
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import torch
from tqdm import tqdm

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.data.data_loader import DataModule
from src.models.intent_classifier_model import create_model as create_deberta_model
from src.models.distilbert_classifier_model import create_distilbert_model
from src.evaluation.metrics import calculate_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelComparator:
    """Compare different models on various metrics"""
    
    def __init__(self, config_path: str = "configs/ml_pipeline_config.yaml"):
        self.config_path = config_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Load data
        self.data_module = DataModule(config_path)
        self.data_module.setup()
        
        # Get label information
        self.label_names = self.data_module.train_dataset.get_label_names()
        self.num_labels = len(self.label_names)
    
    def load_models(
        self,
        deberta_checkpoint: str = None,
        distilbert_checkpoint: str = None
    ) -> Tuple[torch.nn.Module, torch.nn.Module]:
        """Load both models"""
        logger.info("Loading models...")
        
        # Load DeBERTa
        deberta_model = create_deberta_model(
            config_path=self.config_path,
            num_labels=self.num_labels
        ).to(self.device)
        
        if deberta_checkpoint:
            deberta_model.load_state_dict(torch.load(deberta_checkpoint, map_location=self.device))
            logger.info(f"Loaded DeBERTa checkpoint from {deberta_checkpoint}")
        
        # Load DistilBERT
        distilbert_model = create_distilbert_model(
            num_labels=self.num_labels
        ).to(self.device)
        
        if distilbert_checkpoint:
            distilbert_model.load_state_dict(torch.load(distilbert_checkpoint, map_location=self.device))
            logger.info(f"Loaded DistilBERT checkpoint from {distilbert_checkpoint}")
        
        return deberta_model, distilbert_model
    
    def evaluate_model(
        self,
        model: torch.nn.Module,
        dataloader: torch.utils.data.DataLoader,
        model_name: str
    ) -> Dict:
        """Evaluate a single model"""
        logger.info(f"Evaluating {model_name}...")
        
        model.eval()
        all_preds = []
        all_labels = []
        all_probs = []
        
        total_time = 0
        num_samples = 0
        
        with torch.no_grad():
            for batch in tqdm(dataloader, desc=f"Evaluating {model_name}"):
                # Move batch to device
                batch = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v 
                        for k, v in batch.items()}
                
                # Time inference
                start_time = time.time()
                outputs = model(**batch)
                end_time = time.time()
                
                total_time += end_time - start_time
                num_samples += batch['input_ids'].size(0)
                
                # Get predictions
                probs = torch.softmax(outputs.logits, dim=-1)
                preds = torch.argmax(probs, dim=-1)
                
                all_probs.extend(probs.cpu().numpy())
                all_preds.extend(preds.cpu().numpy())
                if 'labels' in batch:
                    all_labels.extend(batch['labels'].cpu().numpy())
        
        # Calculate metrics
        metrics = calculate_metrics(
            np.array(all_labels),
            np.array(all_preds),
            np.array(all_probs),
            self.label_names
        )
        
        # Add timing metrics
        metrics['total_inference_time'] = total_time
        metrics['samples_per_second'] = num_samples / total_time
        metrics['ms_per_sample'] = (total_time / num_samples) * 1000
        
        # Calculate model size
        model_size_mb = sum(p.numel() * p.element_size() for p in model.parameters()) / 1024 / 1024
        metrics['model_size_mb'] = model_size_mb
        
        # Count parameters
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        metrics['total_parameters'] = total_params
        metrics['trainable_parameters'] = trainable_params
        
        return metrics
    
    def benchmark_speed(
        self,
        model: torch.nn.Module,
        model_name: str,
        batch_sizes: List[int] = [1, 8, 32, 64],
        sequence_lengths: List[int] = [64, 128, 256],
        num_runs: int = 100
    ) -> pd.DataFrame:
        """Benchmark inference speed with different configurations"""
        logger.info(f"Benchmarking {model_name} speed...")
        
        results = []
        model.eval()
        
        for batch_size in batch_sizes:
            for seq_len in sequence_lengths:
                # Create dummy inputs
                input_ids = torch.randint(0, 30000, (batch_size, seq_len)).to(self.device)
                attention_mask = torch.ones(batch_size, seq_len).to(self.device)
                
                # Warmup
                for _ in range(10):
                    with torch.no_grad():
                        _ = model(input_ids, attention_mask=attention_mask)
                
                # Benchmark
                torch.cuda.synchronize() if torch.cuda.is_available() else None
                start_time = time.time()
                
                for _ in range(num_runs):
                    with torch.no_grad():
                        _ = model(input_ids, attention_mask=attention_mask)
                
                torch.cuda.synchronize() if torch.cuda.is_available() else None
                end_time = time.time()
                
                total_time = end_time - start_time
                avg_time_ms = (total_time / num_runs) * 1000
                throughput = (batch_size * num_runs) / total_time
                
                results.append({
                    'model': model_name,
                    'batch_size': batch_size,
                    'sequence_length': seq_len,
                    'avg_time_ms': avg_time_ms,
                    'throughput_samples_per_sec': throughput,
                    'latency_ms_per_sample': avg_time_ms / batch_size
                })
        
        return pd.DataFrame(results)
    
    def plot_comparison(
        self,
        deberta_metrics: Dict,
        distilbert_metrics: Dict,
        speed_results: pd.DataFrame,
        output_dir: str = "comparison_results"
    ):
        """Create comparison plots"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # 1. Accuracy comparison
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        metrics_to_compare = ['accuracy', 'f1_weighted', 'f1_macro']
        models = ['DeBERTa', 'DistilBERT']
        
        x = np.arange(len(metrics_to_compare))
        width = 0.35
        
        deberta_values = [deberta_metrics[m] for m in metrics_to_compare]
        distilbert_values = [distilbert_metrics[m] for m in metrics_to_compare]
        
        ax.bar(x - width/2, deberta_values, width, label='DeBERTa', color='#1f77b4')
        ax.bar(x + width/2, distilbert_values, width, label='DistilBERT', color='#ff7f0e')
        
        ax.set_xlabel('Metrics')
        ax.set_ylabel('Score')
        ax.set_title('Model Performance Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(metrics_to_compare)
        ax.legend()
        ax.set_ylim(0, 1.1)
        
        # Add value labels
        for i, (d, s) in enumerate(zip(deberta_values, distilbert_values)):
            ax.text(i - width/2, d + 0.01, f'{d:.3f}', ha='center', va='bottom')
            ax.text(i + width/2, s + 0.01, f'{s:.3f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(output_path / 'performance_comparison.png', dpi=300)
        plt.close()
        
        # 2. Speed comparison
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Throughput by batch size
        for model in ['DeBERTa', 'DistilBERT']:
            model_data = speed_results[speed_results['model'] == model]
            avg_throughput = model_data.groupby('batch_size')['throughput_samples_per_sec'].mean()
            ax1.plot(avg_throughput.index, avg_throughput.values, marker='o', label=model, linewidth=2)
        
        ax1.set_xlabel('Batch Size')
        ax1.set_ylabel('Throughput (samples/sec)')
        ax1.set_title('Inference Throughput vs Batch Size')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Latency by sequence length
        for model in ['DeBERTa', 'DistilBERT']:
            model_data = speed_results[speed_results['model'] == model]
            avg_latency = model_data.groupby('sequence_length')['latency_ms_per_sample'].mean()
            ax2.plot(avg_latency.index, avg_latency.values, marker='s', label=model, linewidth=2)
        
        ax2.set_xlabel('Sequence Length')
        ax2.set_ylabel('Latency (ms/sample)')
        ax2.set_title('Inference Latency vs Sequence Length')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path / 'speed_comparison.png', dpi=300)
        plt.close()
        
        # 3. Model size and efficiency
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        models = ['DeBERTa', 'DistilBERT']
        sizes = [deberta_metrics['model_size_mb'], distilbert_metrics['model_size_mb']]
        accuracies = [deberta_metrics['accuracy'], distilbert_metrics['accuracy']]
        
        # Create scatter plot
        for i, (model, size, acc) in enumerate(zip(models, sizes, accuracies)):
            ax.scatter(size, acc, s=300, label=model, alpha=0.7)
            ax.annotate(model, (size, acc), xytext=(10, 5), textcoords='offset points')
        
        ax.set_xlabel('Model Size (MB)')
        ax.set_ylabel('Accuracy')
        ax.set_title('Model Efficiency: Size vs Performance')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(output_path / 'efficiency_comparison.png', dpi=300)
        plt.close()
        
        logger.info(f"Comparison plots saved to {output_path}")
    
    def generate_report(
        self,
        deberta_metrics: Dict,
        distilbert_metrics: Dict,
        speed_results: pd.DataFrame,
        output_path: str = "comparison_report.md"
    ):
        """Generate a detailed comparison report"""
        report = []
        report.append("# Model Comparison Report: DeBERTa vs DistilBERT\n")
        report.append(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Performance comparison
        report.append("## Performance Metrics\n")
        report.append("| Metric | DeBERTa | DistilBERT | Difference |\n")
        report.append("|--------|---------|------------|------------|\n")
        
        for metric in ['accuracy', 'f1_weighted', 'f1_macro', 'precision', 'recall']:
            if metric in deberta_metrics and metric in distilbert_metrics:
                d_val = deberta_metrics[metric]
                s_val = distilbert_metrics[metric]
                diff = s_val - d_val
                diff_pct = (diff / d_val) * 100 if d_val > 0 else 0
                report.append(f"| {metric} | {d_val:.4f} | {s_val:.4f} | "
                            f"{diff:+.4f} ({diff_pct:+.1f}%) |\n")
        
        # Speed comparison
        report.append("\n## Speed Metrics\n")
        report.append("| Metric | DeBERTa | DistilBERT | Speedup |\n")
        report.append("|--------|---------|------------|----------|\n")
        
        d_speed = deberta_metrics.get('samples_per_second', 0)
        s_speed = distilbert_metrics.get('samples_per_second', 0)
        speedup = s_speed / d_speed if d_speed > 0 else 0
        
        report.append(f"| Inference Speed (samples/sec) | {d_speed:.1f} | {s_speed:.1f} | {speedup:.2f}x |\n")
        report.append(f"| Latency (ms/sample) | {deberta_metrics.get('ms_per_sample', 0):.2f} | "
                     f"{distilbert_metrics.get('ms_per_sample', 0):.2f} | "
                     f"{1/speedup:.2f}x |\n")
        
        # Model size comparison
        report.append("\n## Model Size\n")
        report.append("| Metric | DeBERTa | DistilBERT | Reduction |\n")
        report.append("|--------|---------|------------|------------|\n")
        
        d_size = deberta_metrics['model_size_mb']
        s_size = distilbert_metrics['model_size_mb']
        size_reduction = (1 - s_size / d_size) * 100
        
        report.append(f"| Model Size (MB) | {d_size:.1f} | {s_size:.1f} | {size_reduction:.1f}% |\n")
        report.append(f"| Total Parameters | {deberta_metrics['total_parameters']:,} | "
                     f"{distilbert_metrics['total_parameters']:,} | "
                     f"{(1 - distilbert_metrics['total_parameters']/deberta_metrics['total_parameters'])*100:.1f}% |\n")
        
        # Summary
        report.append("\n## Summary\n")
        report.append(f"- **Performance**: DistilBERT achieves {(distilbert_metrics['accuracy']/deberta_metrics['accuracy'])*100:.1f}% "
                     f"of DeBERTa's accuracy\n")
        report.append(f"- **Speed**: DistilBERT is {speedup:.1f}x faster than DeBERTa\n")
        report.append(f"- **Size**: DistilBERT is {size_reduction:.1f}% smaller than DeBERTa\n")
        report.append(f"- **Efficiency**: DistilBERT offers excellent speed/size improvements with minimal accuracy loss\n")
        
        # Recommendations
        report.append("\n## Recommendations\n")
        
        accuracy_retention = (distilbert_metrics['accuracy'] / deberta_metrics['accuracy']) * 100
        
        if accuracy_retention >= 95:
            report.append("- **Use DistilBERT** for production deployment due to significant speed/size advantages\n")
        elif accuracy_retention >= 90:
            report.append("- **Consider DistilBERT** for most use cases where slight accuracy trade-off is acceptable\n")
        else:
            report.append("- **Use DeBERTa** when maximum accuracy is critical\n")
            report.append("- **Use DistilBERT** for edge deployment or high-throughput scenarios\n")
        
        # Write report
        with open(output_path, 'w') as f:
            f.writelines(report)
        
        logger.info(f"Report saved to {output_path}")
        
        return ''.join(report)


def main():
    """Main comparison function"""
    parser = argparse.ArgumentParser(description='Compare DeBERTa and DistilBERT models')
    parser.add_argument('--config', type=str, default='configs/ml_pipeline_config.yaml',
                       help='Configuration file path')
    parser.add_argument('--deberta-checkpoint', type=str,
                       help='Path to DeBERTa model checkpoint')
    parser.add_argument('--distilbert-checkpoint', type=str,
                       help='Path to DistilBERT model checkpoint')
    parser.add_argument('--test-data', type=str,
                       help='Path to test data (uses default test split if not provided)')
    parser.add_argument('--output-dir', type=str, default='comparison_results',
                       help='Output directory for results')
    parser.add_argument('--batch-size', type=int, default=32,
                       help='Batch size for evaluation')
    parser.add_argument('--benchmark-speed', action='store_true',
                       help='Run detailed speed benchmarks')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Initialize comparator
    comparator = ModelComparator(args.config)
    
    # Load models
    deberta_model, distilbert_model = comparator.load_models(
        deberta_checkpoint=args.deberta_checkpoint,
        distilbert_checkpoint=args.distilbert_checkpoint
    )
    
    # Get test dataloader
    test_loader = comparator.data_module.test_dataloader()
    
    # Evaluate models
    deberta_metrics = comparator.evaluate_model(deberta_model, test_loader, "DeBERTa")
    distilbert_metrics = comparator.evaluate_model(distilbert_model, test_loader, "DistilBERT")
    
    # Run speed benchmarks if requested
    if args.benchmark_speed:
        speed_results = []
        
        deberta_speed = comparator.benchmark_speed(deberta_model, "DeBERTa")
        speed_results.append(deberta_speed)
        
        distilbert_speed = comparator.benchmark_speed(distilbert_model, "DistilBERT")
        speed_results.append(distilbert_speed)
        
        speed_df = pd.concat(speed_results, ignore_index=True)
        speed_df.to_csv(output_dir / 'speed_benchmark_results.csv', index=False)
    else:
        # Create simple speed results from evaluation
        speed_data = []
        for model_name, metrics in [("DeBERTa", deberta_metrics), ("DistilBERT", distilbert_metrics)]:
            speed_data.append({
                'model': model_name,
                'batch_size': args.batch_size,
                'sequence_length': 128,
                'avg_time_ms': metrics.get('ms_per_sample', 0) * args.batch_size,
                'throughput_samples_per_sec': metrics.get('samples_per_second', 0),
                'latency_ms_per_sample': metrics.get('ms_per_sample', 0)
            })
        speed_df = pd.DataFrame(speed_data)
    
    # Save detailed metrics
    with open(output_dir / 'deberta_metrics.json', 'w') as f:
        json.dump(deberta_metrics, f, indent=2, default=str)
    
    with open(output_dir / 'distilbert_metrics.json', 'w') as f:
        json.dump(distilbert_metrics, f, indent=2, default=str)
    
    # Generate plots
    comparator.plot_comparison(deberta_metrics, distilbert_metrics, speed_df, args.output_dir)
    
    # Generate report
    report = comparator.generate_report(
        deberta_metrics,
        distilbert_metrics,
        speed_df,
        output_dir / 'comparison_report.md'
    )
    
    # Print summary
    print("\n" + "="*60)
    print("COMPARISON SUMMARY")
    print("="*60)
    print(f"DeBERTa Accuracy: {deberta_metrics['accuracy']:.4f}")
    print(f"DistilBERT Accuracy: {distilbert_metrics['accuracy']:.4f}")
    print(f"Accuracy Retention: {(distilbert_metrics['accuracy']/deberta_metrics['accuracy'])*100:.1f}%")
    print(f"Speed Improvement: {distilbert_metrics['samples_per_second']/deberta_metrics['samples_per_second']:.1f}x")
    print(f"Size Reduction: {(1 - distilbert_metrics['model_size_mb']/deberta_metrics['model_size_mb'])*100:.1f}%")
    print("="*60)
    
    print(f"\nFull report saved to {output_dir}")


if __name__ == "__main__":
    main()