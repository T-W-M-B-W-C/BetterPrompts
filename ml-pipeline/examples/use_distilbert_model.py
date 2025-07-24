#!/usr/bin/env python3
"""
Example script showing how to use the trained DistilBERT model for inference
"""

import sys
from pathlib import Path
import torch
from transformers import DistilBertTokenizer
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.models.distilbert_classifier_model import create_distilbert_model


class DistilBertIntentPredictor:
    """Simple wrapper for using the trained DistilBERT model"""
    
    def __init__(self, checkpoint_path: str, device: str = None):
        """Initialize the predictor
        
        Args:
            checkpoint_path: Path to the trained model checkpoint
            device: Device to use ('cuda', 'cpu', or None for auto-detect)
        """
        # Set device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        print(f"Using device: {self.device}")
        
        # Initialize tokenizer
        self.tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
        
        # Intent labels (should match your training data)
        self.intent_labels = [
            'chain_of_thought',
            'tree_of_thoughts', 
            'react',
            'self_consistency',
            'general_knowledge',
            'reasoning_and_logic',
            'creative_writing',
            'code_generation',
            'data_analysis',
            'other'
        ]
        
        # Load model
        self.model = create_distilbert_model(num_labels=len(self.intent_labels))
        
        # Load checkpoint
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(checkpoint)
        self.model.to(self.device)
        self.model.eval()
        
        print(f"Model loaded from {checkpoint_path}")
    
    def predict(self, text: str, return_all_scores: bool = False):
        """Predict intent for a given text
        
        Args:
            text: Input text to classify
            return_all_scores: If True, return scores for all intents
            
        Returns:
            Dictionary with prediction results
        """
        # Tokenize input
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=256  # DistilBERT works well with shorter sequences
        )
        
        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Get predictions
        start_time = time.time()
        
        with torch.no_grad():
            outputs = self.model.predict(**inputs)
        
        inference_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Get predicted intent
        intent_idx = outputs['intent_preds'].item()
        intent = self.intent_labels[intent_idx]
        
        # Get confidence scores
        intent_probs = outputs['intent_probs'][0].cpu().numpy()
        confidence = float(intent_probs[intent_idx])
        
        # Get complexity prediction
        complexity = float(outputs['complexity_preds'].cpu().numpy())
        
        result = {
            'intent': intent,
            'confidence': confidence,
            'complexity': complexity,
            'inference_time_ms': inference_time
        }
        
        if return_all_scores:
            result['all_scores'] = {
                label: float(score) 
                for label, score in zip(self.intent_labels, intent_probs)
            }
        
        return result
    
    def predict_batch(self, texts: list, batch_size: int = 32):
        """Predict intents for multiple texts
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            
        Returns:
            List of prediction results
        """
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Tokenize batch
            inputs = self.tokenizer(
                batch_texts,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=256
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get predictions
            with torch.no_grad():
                outputs = self.model.predict(**inputs)
            
            # Process results
            for j in range(len(batch_texts)):
                intent_idx = outputs['intent_preds'][j].item()
                intent = self.intent_labels[intent_idx]
                confidence = float(outputs['intent_probs'][j, intent_idx].cpu().numpy())
                complexity = float(outputs['complexity_preds'][j].cpu().numpy())
                
                results.append({
                    'text': batch_texts[j],
                    'intent': intent,
                    'confidence': confidence,
                    'complexity': complexity
                })
        
        return results


def main():
    """Example usage of the DistilBERT intent predictor"""
    
    # Example texts to classify
    test_prompts = [
        "Let's think about this step by step. First, we need to identify the main components.",
        "Generate a Python function that sorts a list of numbers using quicksort algorithm",
        "What are the main causes of climate change and how can we address them?",
        "Write a creative story about a robot learning to paint",
        "Analyze this sales data and identify the top performing products by region",
        "I need to solve this problem. Let me break it down into smaller parts and tackle each one.",
        "Create multiple solutions and then evaluate which one works best",
        "Given the context, react to the situation and determine the next action"
    ]
    
    # Initialize predictor (update path to your checkpoint)
    checkpoint_path = "models/distilbert/checkpoints/best_model/model.pt"
    
    try:
        predictor = DistilBertIntentPredictor(checkpoint_path)
    except FileNotFoundError:
        print(f"Checkpoint not found at {checkpoint_path}")
        print("Please train the model first using: python scripts/train_distilbert_classifier.py")
        return
    
    print("\n" + "="*60)
    print("DISTILBERT INTENT CLASSIFICATION EXAMPLES")
    print("="*60 + "\n")
    
    # Single prediction example
    print("Single Prediction Example:")
    print("-" * 40)
    
    example_text = test_prompts[0]
    result = predictor.predict(example_text, return_all_scores=True)
    
    print(f"Input: {example_text}")
    print(f"Predicted Intent: {result['intent']}")
    print(f"Confidence: {result['confidence']:.3f}")
    print(f"Complexity: {result['complexity']:.3f}")
    print(f"Inference Time: {result['inference_time_ms']:.2f} ms")
    
    print("\nTop 3 Intents:")
    scores = result['all_scores']
    top_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
    for intent, score in top_intents:
        print(f"  - {intent}: {score:.3f}")
    
    # Batch prediction example
    print("\n\nBatch Prediction Example:")
    print("-" * 40)
    
    start_time = time.time()
    batch_results = predictor.predict_batch(test_prompts)
    batch_time = (time.time() - start_time) * 1000
    
    print(f"Processed {len(test_prompts)} prompts in {batch_time:.2f} ms")
    print(f"Average time per prompt: {batch_time/len(test_prompts):.2f} ms\n")
    
    for result in batch_results:
        print(f"Text: {result['text'][:60]}...")
        print(f"  → Intent: {result['intent']} (confidence: {result['confidence']:.3f}, "
              f"complexity: {result['complexity']:.3f})")
        print()
    
    # Performance summary
    print("="*60)
    print("PERFORMANCE SUMMARY")
    print("="*60)
    print(f"Device: {predictor.device}")
    print(f"Model: DistilBERT-base-uncased")
    print(f"Average inference time: {batch_time/len(test_prompts):.2f} ms/sample")
    print(f"Throughput: {len(test_prompts)/(batch_time/1000):.1f} samples/second")


if __name__ == "__main__":
    main()