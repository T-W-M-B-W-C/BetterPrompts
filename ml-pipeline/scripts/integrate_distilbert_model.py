#!/usr/bin/env python3
"""Integration script for using DistilBERT model in the intent classifier service."""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import torch
import numpy as np
from transformers import AutoTokenizer
import onnxruntime as ort
from loguru import logger

from src.data.intent_dataset import INTENT_LABELS, COMPLEXITY_LABELS


class DistilBERTIntentClassifier:
    """Intent classifier using fine-tuned DistilBERT model."""
    
    def __init__(
        self,
        model_path: str,
        use_onnx: bool = True,
        device: str = "cpu"
    ):
        """Initialize the classifier.
        
        Args:
            model_path: Path to model directory (PyTorch) or ONNX file
            use_onnx: Whether to use ONNX runtime for inference
            device: Device to use ('cpu' or 'cuda')
        """
        self.model_path = Path(model_path)
        self.use_onnx = use_onnx
        self.device = device
        
        # Load configuration
        if use_onnx:
            config_path = self.model_path.parent / "onnx_metadata.json"
        else:
            config_path = self.model_path / "config.json"
        
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize tokenizer
        tokenizer_name = self.config.get("tokenizer", "distilbert-base-uncased")
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        
        # Load model
        if use_onnx:
            self._load_onnx_model()
        else:
            self._load_pytorch_model()
        
        # Intent and complexity mappings
        self.intent_labels = INTENT_LABELS
        self.complexity_labels = COMPLEXITY_LABELS
        
        logger.info(f"Initialized DistilBERT classifier (ONNX: {use_onnx})")
    
    def _load_onnx_model(self) -> None:
        """Load ONNX model."""
        # Create inference session
        providers = ['CPUExecutionProvider']
        if self.device == "cuda" and 'CUDAExecutionProvider' in ort.get_available_providers():
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        
        self.session = ort.InferenceSession(str(self.model_path), providers=providers)
        
        # Get input/output names
        self.input_names = [inp.name for inp in self.session.get_inputs()]
        self.output_names = [out.name for out in self.session.get_outputs()]
        
        logger.info(f"Loaded ONNX model from {self.model_path}")
    
    def _load_pytorch_model(self) -> None:
        """Load PyTorch model."""
        from src.models.distilbert_classifier import DistilBERTClassifier
        
        # Initialize model
        self.model = DistilBERTClassifier(
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
            map_location=torch.device(self.device)
        )
        self.model.load_state_dict(state_dict)
        self.model.eval()
        
        if self.device == "cuda" and torch.cuda.is_available():
            self.model = self.model.cuda()
        
        logger.info(f"Loaded PyTorch model from {self.model_path}")
    
    def classify(
        self,
        text: str,
        return_all_scores: bool = False
    ) -> Dict[str, Any]:
        """Classify a single text.
        
        Args:
            text: Input text to classify
            return_all_scores: Whether to return scores for all classes
            
        Returns:
            Dictionary with classification results
        """
        # Tokenize input
        inputs = self.tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=self.config.get("max_length", 128),
            return_tensors="np" if self.use_onnx else "pt"
        )
        
        # Run inference
        if self.use_onnx:
            outputs = self._run_onnx_inference(inputs)
        else:
            outputs = self._run_pytorch_inference(inputs)
        
        # Process outputs
        results = self._process_outputs(outputs, return_all_scores)
        results["text"] = text
        results["model"] = "distilbert"
        results["inference_type"] = "onnx" if self.use_onnx else "pytorch"
        
        return results
    
    def classify_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        return_all_scores: bool = False
    ) -> List[Dict[str, Any]]:
        """Classify multiple texts.
        
        Args:
            texts: List of texts to classify
            batch_size: Batch size for processing
            return_all_scores: Whether to return scores for all classes
            
        Returns:
            List of classification results
        """
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Tokenize batch
            inputs = self.tokenizer(
                batch_texts,
                padding="max_length",
                truncation=True,
                max_length=self.config.get("max_length", 128),
                return_tensors="np" if self.use_onnx else "pt"
            )
            
            # Run inference
            if self.use_onnx:
                outputs = self._run_onnx_inference(inputs)
            else:
                outputs = self._run_pytorch_inference(inputs)
            
            # Process outputs for each text
            batch_size_actual = len(batch_texts)
            for j in range(batch_size_actual):
                text_outputs = {
                    'intent_logits': outputs['intent_logits'][j],
                    'intent_probs': outputs['intent_probs'][j]
                }
                
                if 'complexity_logits' in outputs:
                    text_outputs['complexity_logits'] = outputs['complexity_logits'][j]
                    text_outputs['complexity_probs'] = outputs['complexity_probs'][j]
                
                result = self._process_outputs(text_outputs, return_all_scores)
                result["text"] = batch_texts[j]
                result["model"] = "distilbert"
                result["inference_type"] = "onnx" if self.use_onnx else "pytorch"
                
                results.append(result)
        
        return results
    
    def _run_onnx_inference(self, inputs: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Run ONNX inference."""
        # Prepare inputs
        ort_inputs = {
            'input_ids': inputs['input_ids'],
            'attention_mask': inputs['attention_mask']
        }
        
        # Run inference
        outputs = self.session.run(self.output_names, ort_inputs)
        
        # Process outputs
        results = {
            'intent_output': outputs[0],
            'intent_logits': outputs[1]
        }
        
        if len(outputs) > 2:
            results['complexity_output'] = outputs[2]
            results['complexity_logits'] = outputs[3]
        
        # Calculate probabilities
        results['intent_probs'] = self._softmax(results['intent_logits'])
        if 'complexity_logits' in results:
            results['complexity_probs'] = self._softmax(results['complexity_logits'])
        
        return results
    
    def _run_pytorch_inference(self, inputs: Dict[str, torch.Tensor]) -> Dict[str, np.ndarray]:
        """Run PyTorch inference."""
        # Move to device
        if self.device == "cuda":
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        # Run inference
        with torch.no_grad():
            outputs = self.model(
                input_ids=inputs['input_ids'],
                attention_mask=inputs['attention_mask']
            )
        
        # Convert to numpy
        results = {
            'intent_logits': outputs['intent_logits'].cpu().numpy(),
            'intent_probs': torch.softmax(outputs['intent_logits'], dim=-1).cpu().numpy()
        }
        
        if 'complexity_logits' in outputs:
            results['complexity_logits'] = outputs['complexity_logits'].cpu().numpy()
            results['complexity_probs'] = torch.softmax(outputs['complexity_logits'], dim=-1).cpu().numpy()
        
        return results
    
    def _process_outputs(
        self,
        outputs: Dict[str, np.ndarray],
        return_all_scores: bool
    ) -> Dict[str, Any]:
        """Process model outputs into results."""
        # Get intent prediction
        intent_probs = outputs['intent_probs']
        if len(intent_probs.shape) > 1:
            intent_probs = intent_probs[0]  # Handle batch dimension
        
        intent_idx = np.argmax(intent_probs)
        intent = self.intent_labels[intent_idx]
        intent_confidence = float(intent_probs[intent_idx])
        
        results = {
            "intent": intent,
            "confidence": intent_confidence,
            "suggested_techniques": self._get_suggested_techniques(intent)
        }
        
        # Add complexity prediction if available
        if 'complexity_probs' in outputs:
            complexity_probs = outputs['complexity_probs']
            if len(complexity_probs.shape) > 1:
                complexity_probs = complexity_probs[0]  # Handle batch dimension
            
            complexity_idx = np.argmax(complexity_probs)
            complexity = self.complexity_labels[complexity_idx]
            complexity_confidence = float(complexity_probs[complexity_idx])
            
            results["complexity"] = complexity
            results["complexity_confidence"] = complexity_confidence
        else:
            # Default complexity based on intent
            results["complexity"] = self._estimate_complexity(intent)
        
        # Add all scores if requested
        if return_all_scores:
            results["all_intent_scores"] = {
                label: float(score)
                for label, score in zip(self.intent_labels, intent_probs)
            }
            
            if 'complexity_probs' in outputs:
                results["all_complexity_scores"] = {
                    label: float(score)
                    for label, score in zip(self.complexity_labels, complexity_probs)
                }
        
        # Add metadata
        results["tokens_used"] = 0  # Placeholder
        results["processing_time"] = 0  # Will be set by caller
        
        return results
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Compute softmax."""
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)
    
    def _get_suggested_techniques(self, intent: str) -> List[str]:
        """Get suggested techniques for an intent."""
        technique_map = {
            "question_answering": ["chain_of_thought", "few_shot", "retrieval_augmented"],
            "creative_writing": ["few_shot", "temperature_control", "iterative_refinement"],
            "code_generation": ["few_shot", "chain_of_thought", "test_driven"],
            "data_analysis": ["chain_of_thought", "structured_output", "step_by_step"],
            "reasoning": ["chain_of_thought", "tree_of_thoughts", "self_consistency"],
            "summarization": ["extractive", "abstractive", "hierarchical"],
            "translation": ["few_shot", "context_preservation", "style_matching"],
            "conversation": ["persona", "context_window", "response_diversity"],
            "task_planning": ["hierarchical", "dependency_analysis", "time_estimation"],
            "problem_solving": ["divide_and_conquer", "systematic_approach", "solution_verification"]
        }
        
        return technique_map.get(intent, ["generic"])
    
    def _estimate_complexity(self, intent: str) -> str:
        """Estimate complexity based on intent."""
        complexity_map = {
            "question_answering": "moderate",
            "creative_writing": "complex",
            "code_generation": "complex",
            "data_analysis": "complex",
            "reasoning": "complex",
            "summarization": "moderate",
            "translation": "moderate",
            "conversation": "simple",
            "task_planning": "complex",
            "problem_solving": "complex"
        }
        
        return complexity_map.get(intent, "moderate")
    
    def benchmark(self, test_texts: List[str], runs: int = 100) -> Dict[str, float]:
        """Benchmark inference speed."""
        # Warm up
        for _ in range(10):
            _ = self.classify(test_texts[0])
        
        # Benchmark single inference
        single_times = []
        for i in range(runs):
            text = test_texts[i % len(test_texts)]
            start = time.time()
            _ = self.classify(text)
            end = time.time()
            single_times.append(end - start)
        
        # Benchmark batch inference
        batch_times = []
        batch_size = 8
        for i in range(0, runs, batch_size):
            batch = test_texts[:batch_size]
            start = time.time()
            _ = self.classify_batch(batch, batch_size=batch_size)
            end = time.time()
            batch_times.append((end - start) / batch_size)
        
        return {
            "single_avg_ms": np.mean(single_times) * 1000,
            "single_p95_ms": np.percentile(single_times, 95) * 1000,
            "batch_avg_ms": np.mean(batch_times) * 1000,
            "batch_p95_ms": np.percentile(batch_times, 95) * 1000,
            "throughput_single": 1.0 / np.mean(single_times),
            "throughput_batch": 1.0 / np.mean(batch_times)
        }


def create_service_integration() -> str:
    """Create integration code for the intent classifier service."""
    integration_code = '''
# Integration for backend/services/intent-classifier/app/models/distilbert_ml_classifier.py

import os
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.config import settings
from app.core.logging import setup_logging
from scripts.integrate_distilbert_model import DistilBERTIntentClassifier

logger = setup_logging()


class DistilBERTMLClassifier:
    """ML-based intent classifier using fine-tuned DistilBERT."""
    
    def __init__(self):
        """Initialize the classifier."""
        self.classifier = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the DistilBERT model."""
        try:
            # Determine model path
            model_path = os.getenv("DISTILBERT_MODEL_PATH", "/app/models/distilbert")
            
            # Check if ONNX model exists
            onnx_path = Path(model_path) / "distilbert_intent_classifier.onnx"
            use_onnx = onnx_path.exists()
            
            if use_onnx:
                logger.info(f"Loading DistilBERT ONNX model from {onnx_path}")
                self.classifier = DistilBERTIntentClassifier(
                    model_path=str(onnx_path),
                    use_onnx=True,
                    device="cpu"  # Use CPU for service deployment
                )
            else:
                logger.info(f"Loading DistilBERT PyTorch model from {model_path}")
                self.classifier = DistilBERTIntentClassifier(
                    model_path=model_path,
                    use_onnx=False,
                    device="cpu"
                )
            
            logger.info("DistilBERT model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load DistilBERT model: {e}")
            self.classifier = None
    
    async def classify(self, text: str) -> Dict[str, Any]:
        """Classify intent using DistilBERT model."""
        if not self.classifier:
            raise RuntimeError("DistilBERT model not loaded")
        
        try:
            # Run classification
            result = self.classifier.classify(text, return_all_scores=False)
            
            # Format response to match expected structure
            return {
                "intent": result["intent"],
                "confidence": result["confidence"],
                "complexity": result["complexity"],
                "suggested_techniques": result["suggested_techniques"],
                "model_type": "distilbert_ml",
                "tokens_used": result.get("tokens_used", 0)
            }
            
        except Exception as e:
            logger.error(f"DistilBERT classification failed: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if model is healthy."""
        if not self.classifier:
            return False
        
        try:
            # Run a test classification
            result = self.classifier.classify("Test health check")
            return "intent" in result
        except Exception:
            return False


# Singleton instance
distilbert_classifier = DistilBERTMLClassifier()
'''
    
    return integration_code


def main():
    """Example usage and integration demo."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DistilBERT integration demo")
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Path to model (directory for PyTorch, .onnx file for ONNX)"
    )
    parser.add_argument(
        "--use-onnx",
        action="store_true",
        help="Use ONNX runtime"
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run benchmark"
    )
    parser.add_argument(
        "--generate-integration",
        action="store_true",
        help="Generate integration code"
    )
    
    args = parser.parse_args()
    
    if args.generate_integration:
        # Generate integration code
        code = create_service_integration()
        output_path = "distilbert_ml_classifier.py"
        with open(output_path, 'w') as f:
            f.write(code)
        logger.info(f"Integration code saved to {output_path}")
        return
    
    # Initialize classifier
    classifier = DistilBERTIntentClassifier(
        model_path=args.model_path,
        use_onnx=args.use_onnx,
        device="cuda" if torch.cuda.is_available() else "cpu"
    )
    
    # Test examples
    test_texts = [
        "How do I implement a neural network in PyTorch?",
        "Write a story about a robot learning to paint",
        "Analyze this sales data and identify trends",
        "Translate this paragraph to Spanish",
        "Can you explain quantum computing?"
    ]
    
    logger.info("Testing single classification:")
    for text in test_texts[:3]:
        start = time.time()
        result = classifier.classify(text)
        end = time.time()
        
        logger.info(f"\nText: {text}")
        logger.info(f"Intent: {result['intent']} (confidence: {result['confidence']:.3f})")
        logger.info(f"Complexity: {result['complexity']}")
        logger.info(f"Time: {(end - start) * 1000:.2f} ms")
    
    logger.info("\nTesting batch classification:")
    start = time.time()
    results = classifier.classify_batch(test_texts)
    end = time.time()
    
    for result in results:
        logger.info(f"\nText: {result['text'][:50]}...")
        logger.info(f"Intent: {result['intent']} (confidence: {result['confidence']:.3f})")
    
    logger.info(f"\nBatch time: {(end - start) * 1000:.2f} ms total")
    logger.info(f"Average per text: {(end - start) * 1000 / len(test_texts):.2f} ms")
    
    # Run benchmark if requested
    if args.benchmark:
        logger.info("\nRunning benchmark...")
        bench_results = classifier.benchmark(test_texts)
        
        logger.info("\nBenchmark Results:")
        logger.info(f"Single inference: {bench_results['single_avg_ms']:.2f} ms (avg), {bench_results['single_p95_ms']:.2f} ms (p95)")
        logger.info(f"Batch inference: {bench_results['batch_avg_ms']:.2f} ms (avg), {bench_results['batch_p95_ms']:.2f} ms (p95)")
        logger.info(f"Throughput: {bench_results['throughput_single']:.1f} samples/sec (single), {bench_results['throughput_batch']:.1f} samples/sec (batch)")


if __name__ == "__main__":
    main()