"""
TorchServe Custom Handler for Intent Classification Model
Handles DeBERTa-v3 based intent classifier with complexity prediction
"""

import json
import logging
import os
import time
from abc import ABC
from typing import List, Dict, Any, Optional, Tuple

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from ts.torch_handler.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class IntentClassifierHandler(BaseHandler, ABC):
    """
    Custom handler for Intent Classification model.
    Handles preprocessing, inference, and postprocessing.
    """
    
    def __init__(self):
        super().__init__()
        self.initialized = False
        self.tokenizer = None
        self.model = None
        self.device = None
        self.max_length = 512
        
        # Intent labels
        self.intent_labels = [
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
        
        # Technique mapping
        self.technique_mapping = {
            "question_answering": ["chain_of_thought", "few_shot"],
            "creative_writing": ["temperature_control", "top_p_sampling"],
            "code_generation": ["structured_output", "step_by_step"],
            "data_analysis": ["tabular_cot", "structured_reasoning"],
            "reasoning": ["tree_of_thoughts", "self_consistency"],
            "summarization": ["extractive", "abstractive"],
            "translation": ["few_shot", "context_examples"],
            "conversation": ["persona", "context_window"],
            "task_planning": ["decomposition", "step_by_step"],
            "problem_solving": ["chain_of_thought", "tree_of_thoughts"]
        }
    
    def initialize(self, context):
        """Initialize the model and tokenizer."""
        properties = context.system_properties
        self.device = torch.device("cuda:" + str(properties.get("gpu_id")) 
                                 if torch.cuda.is_available() else "cpu")
        
        # Load model artifacts
        model_dir = properties.get("model_dir")
        
        # Initialize tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            os.path.join(model_dir, "tokenizer"),
            use_fast=True
        )
        
        # Load model
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_dir,
            num_labels=len(self.intent_labels),
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        self.model.to(self.device)
        self.model.eval()
        
        # Load config if exists
        config_path = os.path.join(model_dir, "config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
                self.max_length = self.config.get("max_length", 512)
        
        self.initialized = True
        logger.info(f"Model loaded successfully on device: {self.device}")
    
    def preprocess(self, data: List[Dict[str, Any]]) -> torch.Tensor:
        """
        Preprocess input data for inference.
        
        Args:
            data: List of input dictionaries with 'text' field
            
        Returns:
            Preprocessed tensor ready for inference
        """
        texts = []
        
        for item in data:
            if isinstance(item, dict):
                text = item.get("text", item.get("data", ""))
            elif isinstance(item, str):
                text = item
            else:
                text = str(item)
            
            # Clean and validate text
            text = text.strip()
            if not text:
                text = "empty"
            
            texts.append(text)
        
        # Tokenize batch
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        
        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        return inputs
    
    def inference(self, inputs: Dict[str, torch.Tensor]) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Run inference on preprocessed data.
        
        Args:
            inputs: Tokenized inputs
            
        Returns:
            Model outputs (logits and hidden states)
        """
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            
            # Get complexity score from auxiliary head if available
            complexity_score = None
            if hasattr(outputs, 'complexity_logits'):
                complexity_score = torch.sigmoid(outputs.complexity_logits)
            
        return logits, complexity_score
    
    def postprocess(self, outputs: Tuple[torch.Tensor, Optional[torch.Tensor]]) -> List[Dict[str, Any]]:
        """
        Postprocess model outputs into structured response.
        
        Args:
            outputs: Model outputs (logits and complexity scores)
            
        Returns:
            List of prediction dictionaries
        """
        logits, complexity_scores = outputs
        
        # Apply softmax to get probabilities
        probs = F.softmax(logits, dim=-1)
        
        # Get top predictions
        top_k = min(3, len(self.intent_labels))
        top_probs, top_indices = torch.topk(probs, top_k, dim=-1)
        
        batch_results = []
        
        for i in range(probs.shape[0]):
            # Primary prediction
            primary_idx = top_indices[i, 0].item()
            primary_intent = self.intent_labels[primary_idx]
            primary_confidence = top_probs[i, 0].item()
            
            # Get all class probabilities
            class_probs = {
                self.intent_labels[j]: float(probs[i, j])
                for j in range(len(self.intent_labels))
            }
            
            # Complexity assessment
            if complexity_scores is not None:
                complexity = float(complexity_scores[i].item())
                complexity_level = self._get_complexity_level(complexity)
            else:
                # Fallback complexity based on intent type
                complexity = self._estimate_complexity(primary_intent, primary_confidence)
                complexity_level = self._get_complexity_level(complexity)
            
            # Get recommended techniques
            techniques = self._get_recommended_techniques(
                primary_intent, 
                complexity_level,
                primary_confidence
            )
            
            result = {
                "intent": primary_intent,
                "confidence": float(primary_confidence),
                "complexity": {
                    "score": complexity,
                    "level": complexity_level
                },
                "techniques": techniques,
                "all_intents": class_probs,
                "top_intents": [
                    {
                        "intent": self.intent_labels[top_indices[i, j].item()],
                        "confidence": float(top_probs[i, j])
                    }
                    for j in range(top_k)
                ],
                "metadata": {
                    "model_version": "1.0",
                    "processing_time": time.time()
                }
            }
            
            batch_results.append(result)
        
        return batch_results
    
    def handle(self, data: List[Dict[str, Any]], context) -> List[Dict[str, Any]]:
        """
        Entry point for TorchServe request handling.
        
        Args:
            data: Input data from request
            context: TorchServe context
            
        Returns:
            Model predictions
        """
        start_time = time.time()
        
        try:
            # Preprocess
            inputs = self.preprocess(data)
            
            # Inference
            outputs = self.inference(inputs)
            
            # Postprocess
            results = self.postprocess(outputs)
            
            # Add timing info
            inference_time = time.time() - start_time
            for result in results:
                result["metadata"]["inference_time_ms"] = round(inference_time * 1000, 2)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in handler: {str(e)}", exc_info=True)
            return [{
                "error": str(e),
                "error_type": type(e).__name__,
                "status": "failed"
            }]
    
    def _get_complexity_level(self, score: float) -> str:
        """Convert complexity score to level."""
        if score < 0.33:
            return "simple"
        elif score < 0.67:
            return "moderate"
        else:
            return "complex"
    
    def _estimate_complexity(self, intent: str, confidence: float) -> float:
        """Estimate complexity when auxiliary head is not available."""
        complex_intents = {"reasoning", "problem_solving", "code_generation", "data_analysis"}
        simple_intents = {"translation", "summarization", "conversation"}
        
        if intent in complex_intents:
            base_complexity = 0.7
        elif intent in simple_intents:
            base_complexity = 0.3
        else:
            base_complexity = 0.5
        
        # Adjust based on confidence (lower confidence might indicate complexity)
        complexity_adjustment = (1 - confidence) * 0.2
        
        return min(1.0, base_complexity + complexity_adjustment)
    
    def _get_recommended_techniques(self, intent: str, complexity: str, confidence: float) -> List[Dict[str, Any]]:
        """Get recommended prompt engineering techniques."""
        base_techniques = self.technique_mapping.get(intent, ["general"])
        
        techniques = []
        for technique in base_techniques:
            technique_info = {
                "name": technique,
                "confidence": confidence,
                "description": self._get_technique_description(technique),
                "parameters": self._get_technique_parameters(technique, complexity)
            }
            techniques.append(technique_info)
        
        # Add complexity-specific techniques
        if complexity == "complex":
            techniques.append({
                "name": "step_by_step_breakdown",
                "confidence": 0.9,
                "description": "Break down complex tasks into manageable steps",
                "parameters": {"max_steps": 10, "detail_level": "high"}
            })
        
        return techniques
    
    def _get_technique_description(self, technique: str) -> str:
        """Get description for a technique."""
        descriptions = {
            "chain_of_thought": "Guide reasoning through step-by-step thinking",
            "few_shot": "Provide examples to guide model behavior",
            "tree_of_thoughts": "Explore multiple reasoning paths",
            "temperature_control": "Adjust creativity and randomness",
            "structured_output": "Format output in specific structure",
            "step_by_step": "Break down into sequential steps",
            "self_consistency": "Generate multiple solutions and select best",
            "tabular_cot": "Structured reasoning for data analysis",
            "persona": "Adopt specific role or perspective",
            "decomposition": "Break complex task into subtasks"
        }
        return descriptions.get(technique, f"Apply {technique} technique")
    
    def _get_technique_parameters(self, technique: str, complexity: str) -> Dict[str, Any]:
        """Get recommended parameters for a technique."""
        params = {
            "chain_of_thought": {"steps": 3 if complexity == "simple" else 7},
            "few_shot": {"examples": 2 if complexity == "simple" else 5},
            "temperature_control": {"temperature": 0.7, "top_p": 0.9},
            "tree_of_thoughts": {"branches": 3, "depth": 2 if complexity == "simple" else 4}
        }
        return params.get(technique, {})


# Create handler instance
_service = IntentClassifierHandler()