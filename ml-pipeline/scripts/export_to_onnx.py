#!/usr/bin/env python3
"""Export trained DistilBERT model to ONNX format for deployment."""

import argparse
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Tuple

import torch
import torch.onnx
import numpy as np
from transformers import AutoTokenizer
import onnx
import onnxruntime as ort
from loguru import logger

from src.models.distilbert_classifier import DistilBERTClassifier
from src.data.intent_dataset import INTENT_LABELS, COMPLEXITY_LABELS


class ONNXExporter:
    """Export PyTorch models to ONNX format."""
    
    def __init__(self, model_path: str, output_dir: str):
        """Initialize the exporter."""
        self.model_path = Path(model_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load model configuration
        config_path = self.model_path.parent / "config.json"
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.get("model_name", "distilbert-base-uncased")
        )
        
        # Load model
        self.model = self._load_model()
        self.model.eval()
        
        logger.info(f"Loaded model from {model_path}")
    
    def _load_model(self) -> DistilBERTClassifier:
        """Load the trained model."""
        model = DistilBERTClassifier(
            num_labels=len(INTENT_LABELS),
            model_name=self.config.get("model_name", "distilbert-base-uncased"),
            use_complexity_features=self.config.get("use_complexity_features", True),
            pooling_strategy=self.config.get("pooling_strategy", "cls"),
            dropout_rate=self.config.get("dropout_rate", 0.2),
            freeze_layers=self.config.get("freeze_layers", 0),
            predict_complexity=self.config.get("predict_complexity", True)
        )
        
        # Load state dict
        state_dict = torch.load(
            self.model_path / "pytorch_model.bin",
            map_location=torch.device("cpu")
        )
        model.load_state_dict(state_dict)
        
        return model
    
    def export_to_onnx(
        self,
        model_name: str = "distilbert_intent_classifier",
        opset_version: int = 14,
        optimize: bool = True
    ) -> str:
        """Export model to ONNX format."""
        logger.info("Starting ONNX export...")
        
        # Create dummy inputs
        dummy_inputs = self._create_dummy_inputs()
        
        # Define output path
        onnx_path = self.output_dir / f"{model_name}.onnx"
        
        # Export to ONNX
        logger.info(f"Exporting to {onnx_path}")
        
        # Dynamic axes for variable sequence length
        dynamic_axes = {
            'input_ids': {0: 'batch_size', 1: 'sequence'},
            'attention_mask': {0: 'batch_size', 1: 'sequence'},
            'intent_output': {0: 'batch_size'},
            'intent_logits': {0: 'batch_size'}
        }
        
        if self.config.get("use_complexity_features", True):
            dynamic_axes['complexity_output'] = {0: 'batch_size'}
            dynamic_axes['complexity_logits'] = {0: 'batch_size'}
        
        # Export
        torch.onnx.export(
            self.model,
            dummy_inputs,
            onnx_path,
            export_params=True,
            opset_version=opset_version,
            do_constant_folding=True,
            input_names=['input_ids', 'attention_mask'],
            output_names=['intent_output', 'intent_logits', 'complexity_output', 'complexity_logits']
            if self.config.get("use_complexity_features", True)
            else ['intent_output', 'intent_logits'],
            dynamic_axes=dynamic_axes,
            verbose=False
        )
        
        logger.info("ONNX export completed")
        
        # Verify the exported model
        self._verify_onnx_model(onnx_path)
        
        # Optimize if requested
        if optimize:
            onnx_path = self._optimize_onnx_model(onnx_path)
        
        # Save metadata
        self._save_metadata(model_name)
        
        return str(onnx_path)
    
    def _create_dummy_inputs(self) -> Tuple[torch.Tensor, torch.Tensor]:
        """Create dummy inputs for ONNX export."""
        # Create sample text
        sample_text = "How do I implement a neural network in PyTorch?"
        
        # Tokenize
        inputs = self.tokenizer(
            sample_text,
            padding="max_length",
            truncation=True,
            max_length=self.config.get("max_length", 128),
            return_tensors="pt"
        )
        
        return inputs["input_ids"], inputs["attention_mask"]
    
    def _verify_onnx_model(self, onnx_path: Path) -> None:
        """Verify the exported ONNX model."""
        logger.info("Verifying ONNX model...")
        
        # Check model validity
        onnx_model = onnx.load(onnx_path)
        onnx.checker.check_model(onnx_model)
        
        # Compare outputs with PyTorch
        self._compare_outputs(onnx_path)
        
        logger.info("ONNX model verification passed")
    
    def _compare_outputs(self, onnx_path: Path, tolerance: float = 1e-5) -> None:
        """Compare ONNX and PyTorch outputs."""
        # Create test inputs
        input_ids, attention_mask = self._create_dummy_inputs()
        
        # PyTorch inference
        with torch.no_grad():
            pytorch_outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
        
        # ONNX inference
        ort_session = ort.InferenceSession(str(onnx_path))
        ort_inputs = {
            'input_ids': input_ids.numpy(),
            'attention_mask': attention_mask.numpy()
        }
        ort_outputs = ort_session.run(None, ort_inputs)
        
        # Compare intent outputs
        pytorch_intent = pytorch_outputs['intent_logits'].numpy()
        onnx_intent = ort_outputs[1]  # intent_logits is second output
        
        intent_diff = np.abs(pytorch_intent - onnx_intent).max()
        logger.info(f"Intent logits max difference: {intent_diff}")
        
        if intent_diff > tolerance:
            logger.warning(f"Intent outputs differ by {intent_diff}, exceeding tolerance {tolerance}")
        
        # Compare complexity outputs if available
        if self.config.get("predict_complexity", True):
            pytorch_complexity = pytorch_outputs['complexity_logits'].numpy()
            onnx_complexity = ort_outputs[3]  # complexity_logits is fourth output
            
            complexity_diff = np.abs(pytorch_complexity - onnx_complexity).max()
            logger.info(f"Complexity logits max difference: {complexity_diff}")
            
            if complexity_diff > tolerance:
                logger.warning(f"Complexity outputs differ by {complexity_diff}, exceeding tolerance {tolerance}")
    
    def _optimize_onnx_model(self, onnx_path: Path) -> Path:
        """Optimize ONNX model for inference."""
        logger.info("Optimizing ONNX model...")
        
        from onnxruntime.transformers import optimizer
        
        optimized_path = self.output_dir / f"{onnx_path.stem}_optimized.onnx"
        
        # Optimize model
        optimizer.optimize_model(
            str(onnx_path),
            model_type='bert',
            num_heads=12,  # DistilBERT has 12 attention heads
            hidden_size=768,
            use_gpu=False,
            opt_level=1,
            output_path=str(optimized_path),
            optimization_options=optimizer.BertOptimizationOptions('all')
        )
        
        logger.info(f"Optimized model saved to {optimized_path}")
        
        # Compare file sizes
        original_size = onnx_path.stat().st_size / (1024 * 1024)  # MB
        optimized_size = optimized_path.stat().st_size / (1024 * 1024)  # MB
        
        logger.info(f"Original size: {original_size:.2f} MB")
        logger.info(f"Optimized size: {optimized_size:.2f} MB")
        logger.info(f"Size reduction: {(1 - optimized_size/original_size) * 100:.1f}%")
        
        return optimized_path
    
    def _save_metadata(self, model_name: str) -> None:
        """Save model metadata for deployment."""
        metadata = {
            "model_name": model_name,
            "model_type": "distilbert",
            "input_names": ["input_ids", "attention_mask"],
            "output_names": ["intent_output", "intent_logits", "complexity_output", "complexity_logits"]
            if self.config.get("use_complexity_features", True)
            else ["intent_output", "intent_logits"],
            "intent_labels": INTENT_LABELS,
            "complexity_labels": COMPLEXITY_LABELS if self.config.get("predict_complexity", True) else None,
            "max_length": self.config.get("max_length", 128),
            "tokenizer": self.config.get("model_name", "distilbert-base-uncased"),
            "export_config": {
                "opset_version": 14,
                "optimization_enabled": True,
                "export_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        metadata_path = self.output_dir / "onnx_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata saved to {metadata_path}")
    
    def benchmark_inference_speed(
        self,
        onnx_path: str,
        num_samples: int = 100,
        batch_size: int = 1
    ) -> Dict[str, float]:
        """Benchmark ONNX model inference speed."""
        logger.info(f"Benchmarking ONNX inference speed with {num_samples} samples...")
        
        # Create test data
        test_texts = [
            "How do I implement a neural network?",
            "Write a story about a robot",
            "Analyze this sales data",
            "Translate this to Spanish",
            "Plan a project timeline"
        ] * (num_samples // 5)
        
        # Initialize ONNX runtime
        ort_session = ort.InferenceSession(onnx_path)
        
        # Warm up
        for _ in range(10):
            inputs = self.tokenizer(
                test_texts[0],
                padding="max_length",
                truncation=True,
                max_length=self.config.get("max_length", 128),
                return_tensors="np"
            )
            _ = ort_session.run(None, {
                'input_ids': inputs["input_ids"],
                'attention_mask': inputs["attention_mask"]
            })
        
        # Benchmark
        times = []
        for i in range(0, len(test_texts), batch_size):
            batch = test_texts[i:i+batch_size]
            
            start = time.time()
            
            # Tokenize
            inputs = self.tokenizer(
                batch,
                padding="max_length",
                truncation=True,
                max_length=self.config.get("max_length", 128),
                return_tensors="np"
            )
            
            # Inference
            _ = ort_session.run(None, {
                'input_ids': inputs["input_ids"],
                'attention_mask': inputs["attention_mask"]
            })
            
            end = time.time()
            times.append(end - start)
        
        # Calculate metrics
        avg_time = np.mean(times)
        std_time = np.std(times)
        throughput = batch_size / avg_time
        
        results = {
            "avg_latency_ms": avg_time * 1000,
            "std_latency_ms": std_time * 1000,
            "throughput_samples_per_sec": throughput,
            "p50_latency_ms": np.percentile(times, 50) * 1000,
            "p95_latency_ms": np.percentile(times, 95) * 1000,
            "p99_latency_ms": np.percentile(times, 99) * 1000
        }
        
        logger.info(f"Average latency: {results['avg_latency_ms']:.2f} ms")
        logger.info(f"Throughput: {results['throughput_samples_per_sec']:.2f} samples/sec")
        
        return results


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Export DistilBERT model to ONNX")
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Path to trained model directory"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/onnx",
        help="Output directory for ONNX model"
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="distilbert_intent_classifier",
        help="Name for the exported model"
    )
    parser.add_argument(
        "--opset-version",
        type=int,
        default=14,
        help="ONNX opset version"
    )
    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="Skip ONNX optimization"
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Benchmark inference speed after export"
    )
    parser.add_argument(
        "--quantize",
        action="store_true",
        help="Apply dynamic quantization"
    )
    
    args = parser.parse_args()
    
    # Initialize exporter
    exporter = ONNXExporter(args.model_path, args.output_dir)
    
    # Export to ONNX
    onnx_path = exporter.export_to_onnx(
        model_name=args.model_name,
        opset_version=args.opset_version,
        optimize=not args.no_optimize
    )
    
    logger.info(f"Model exported to {onnx_path}")
    
    # Apply quantization if requested
    if args.quantize:
        from onnxruntime.quantization import quantize_dynamic, QuantType
        
        quantized_path = Path(onnx_path).parent / f"{Path(onnx_path).stem}_quantized.onnx"
        
        logger.info("Applying dynamic quantization...")
        quantize_dynamic(
            onnx_path,
            str(quantized_path),
            weight_type=QuantType.QInt8
        )
        
        # Compare sizes
        original_size = Path(onnx_path).stat().st_size / (1024 * 1024)
        quantized_size = quantized_path.stat().st_size / (1024 * 1024)
        
        logger.info(f"Original size: {original_size:.2f} MB")
        logger.info(f"Quantized size: {quantized_size:.2f} MB")
        logger.info(f"Size reduction: {(1 - quantized_size/original_size) * 100:.1f}%")
        
        onnx_path = str(quantized_path)
    
    # Benchmark if requested
    if args.benchmark:
        results = exporter.benchmark_inference_speed(onnx_path)
        
        # Save benchmark results
        benchmark_path = Path(args.output_dir) / "benchmark_results.json"
        with open(benchmark_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Benchmark results saved to {benchmark_path}")


if __name__ == "__main__":
    main()