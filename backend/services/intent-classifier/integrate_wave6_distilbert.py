#!/usr/bin/env python3
"""Integration script for Wave 6 with trained DistilBERT model.

This script shows how to:
1. Load the trained DistilBERT model from ml-pipeline/trained_models/final/
2. Deploy it to TorchServe (if available)
3. Use it with the adaptive router
"""

import os
import sys
import asyncio
import shutil
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.enhanced_classifier import EnhancedRuleBasedClassifier
from app.models.zero_shot_classifier import HybridClassifier, ZeroShotModelType
from app.models.adaptive_router import AdaptiveModelRouter
from app.core.config import settings


def prepare_local_distilbert():
    """Prepare the trained DistilBERT model for local use."""
    print("Preparing trained DistilBERT model...")
    
    # Path to the trained model
    trained_model_path = Path(__file__).parent.parent.parent.parent / "ml-pipeline" / "trained_models" / "final"
    
    if not trained_model_path.exists():
        print(f"❌ Trained model not found at: {trained_model_path}")
        return None
    
    print(f"✅ Found trained model at: {trained_model_path}")
    
    # Check for required files
    required_files = ["config.json", "model.safetensors", "tokenizer.json", "vocab.txt"]
    missing_files = [f for f in required_files if not (trained_model_path / f).exists()]
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return None
    
    print("✅ All required model files present")
    
    # Load model info
    try:
        import json
        with open(trained_model_path / "training_info.json", "r") as f:
            training_info = json.load(f)
        
        print(f"\n📊 Model Training Info:")
        print(f"  - Base Model: {training_info.get('base_model', 'distilbert-base-uncased')}")
        print(f"  - Final Accuracy: {training_info.get('eval_accuracy', 0):.4f}")
        print(f"  - Final F1 Score: {training_info.get('eval_f1', 0):.4f}")
        print(f"  - Training Duration: {training_info.get('train_runtime', 0):.1f}s")
        print(f"  - Trained on: {training_info.get('training_examples', 0)} examples")
    except Exception as e:
        print(f"⚠️  Could not load training info: {e}")
    
    return trained_model_path


def create_torchserve_mar(model_path: Path):
    """Create a Model Archive (MAR) file for TorchServe deployment."""
    print("\n🔧 Creating TorchServe Model Archive...")
    
    # This is a placeholder - in production, you'd use torch-model-archiver
    # For now, we'll assume TorchServe is already configured with the model
    print("ℹ️  TorchServe integration requires torch-model-archiver")
    print("ℹ️  Run: torch-model-archiver --model-name intent_classifier \\")
    print("       --version 1.0 --serialized-file model.safetensors \\")
    print("       --handler intent_handler.py --extra-files config.json,tokenizer.json")
    
    return True


class LocalDistilBERTClassifier:
    """Local DistilBERT classifier that mimics TorchServe interface."""
    
    def __init__(self, model_path: Path):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
    def initialize(self):
        """Load the model and tokenizer."""
        print(f"Loading DistilBERT from {self.model_path}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
        self.model = AutoModelForSequenceClassification.from_pretrained(str(self.model_path))
        self.model.to(self.device)
        self.model.eval()
        
        print(f"✅ Model loaded on {self.device}")
    
    async def classify(self, text: str):
        """Classify text using the local model."""
        # Tokenize
        inputs = self.tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=512,
            return_tensors="pt"
        ).to(self.device)
        
        # Inference
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)
            
        # Get prediction
        pred_idx = torch.argmax(probs, dim=-1).item()
        confidence = probs[0, pred_idx].item()
        
        # Intent labels (should match training)
        intent_labels = [
            "question_answering",
            "creative_writing",
            "code_generation",
            "data_analysis",
            "reasoning",
            "summarization",
            "translation",
            "conversation",
            "task_planning",
            "problem_solving",
        ]
        
        # Determine complexity based on confidence
        if confidence > 0.9:
            complexity = "simple"
        elif confidence > 0.7:
            complexity = "moderate"
        else:
            complexity = "complex"
        
        # Technique mapping
        technique_mapping = {
            "question_answering": ["analogical", "step_by_step", "few_shot"],
            "creative_writing": ["role_play", "emotional_appeal", "iterative_refinement"],
            "code_generation": ["chain_of_thought", "few_shot", "self_consistency"],
            "data_analysis": ["step_by_step", "chain_of_thought", "tree_of_thoughts"],
            "reasoning": ["chain_of_thought", "tree_of_thoughts", "self_consistency"],
            "summarization": ["few_shot", "iterative_refinement"],
            "translation": ["few_shot", "zero_shot"],
            "conversation": ["role_play", "emotional_appeal", "few_shot"],
            "task_planning": ["step_by_step", "tree_of_thoughts", "chain_of_thought"],
            "problem_solving": ["step_by_step", "chain_of_thought", "tree_of_thoughts"],
        }
        
        intent = intent_labels[pred_idx] if pred_idx < len(intent_labels) else "unknown"
        
        return {
            "intent": intent,
            "confidence": float(confidence),
            "complexity": {"level": complexity},
            "techniques": [{"name": t} for t in technique_mapping.get(intent, ["chain_of_thought"])],
            "metadata": {
                "tokens_used": len(self.tokenizer.encode(text)),
                "model": "distilbert-trained"
            }
        }


async def test_integrated_system():
    """Test the complete Wave 6 system with trained DistilBERT."""
    print("\n🚀 Testing Integrated Wave 6 System\n")
    
    # Prepare models
    model_path = prepare_local_distilbert()
    if not model_path:
        print("❌ Cannot proceed without trained model")
        return
    
    # Initialize classifiers
    print("\n📦 Initializing classifiers...")
    
    # Rule-based classifier
    rule_classifier = EnhancedRuleBasedClassifier()
    
    # Hybrid classifier (rules + zero-shot)
    hybrid_classifier = HybridClassifier(
        rule_classifier=rule_classifier,
        zero_shot_model=ZeroShotModelType.DEBERTA_V3_MNLI,
        rule_confidence_threshold=0.85
    )
    await hybrid_classifier.initialize()
    
    # Local DistilBERT classifier (simulating TorchServe)
    distilbert_classifier = LocalDistilBERTClassifier(model_path)
    distilbert_classifier.initialize()
    
    # Create mock TorchServe client
    class MockTorchServeClient:
        def __init__(self, classifier):
            self.classifier = classifier
            
        async def classify(self, text):
            return await self.classifier.classify(text)
    
    mock_torchserve = MockTorchServeClient(distilbert_classifier)
    
    # Initialize adaptive router
    router = AdaptiveModelRouter(
        rule_classifier=rule_classifier,
        hybrid_classifier=hybrid_classifier,
        torchserve_client=mock_torchserve,
        enable_ab_testing=True,
        ab_test_percentage=0.3
    )
    
    print("✅ All components initialized")
    
    # Test queries
    test_queries = [
        {
            "text": "What is 2+2?",
            "latency": "critical",
            "description": "Simple math (should use rules)"
        },
        {
            "text": "Explain the concept of recursion in programming with examples",
            "latency": "standard",
            "description": "Programming explanation (should use zero-shot)"
        },
        {
            "text": "Design a distributed system for real-time video streaming that can handle millions of concurrent users with low latency",
            "latency": "relaxed",
            "description": "Complex system design (should use DistilBERT)"
        },
        {
            "text": "Write a Python function to find the longest palindromic substring in a given string",
            "latency": "standard",
            "description": "Code generation (routing depends on confidence)"
        }
    ]
    
    print("\n🧪 Running classification tests...\n")
    
    for query in test_queries:
        print(f"📝 Query: {query['text'][:60]}...")
        print(f"   Description: {query['description']}")
        print(f"   Latency requirement: {query['latency']}")
        
        result, routing = await router.route_and_classify(
            text=query["text"],
            latency_requirement=query["latency"]
        )
        
        print(f"\n   🎯 Result:")
        print(f"      Intent: {result['intent']}")
        print(f"      Confidence: {result['confidence']:.3f}")
        print(f"      Model used: {routing.selected_model.value}")
        print(f"      Latency: {result['routing_metadata']['latency_ms']:.1f}ms")
        
        if routing.ab_test_group:
            print(f"      A/B test group: {routing.ab_test_group}")
        
        print(f"\n   📋 Routing reasons:")
        for reason in routing.reasons[:3]:  # Show first 3 reasons
            print(f"      - {reason}")
        
        print("\n" + "-"*80 + "\n")
    
    # Show statistics
    stats = router.get_routing_stats()
    print("📊 Routing Statistics:")
    print(f"   Total requests: {stats['total_requests']}")
    
    print(f"\n   Model distribution:")
    for model, data in stats['model_distribution'].items():
        print(f"      {model}: {data['count']} ({data['percentage']:.1f}%)")
    
    print("\n✅ Integration test completed!")
    print("\n💡 Next steps:")
    print("   1. Deploy the trained model to TorchServe")
    print("   2. Configure the intent-classifier service with TORCHSERVE_HOST")
    print("   3. Run the service with ENABLE_ADAPTIVE_ROUTING=true")
    print("   4. Monitor routing decisions via /api/v1/intents/routing/stats")


if __name__ == "__main__":
    asyncio.run(test_integrated_system())