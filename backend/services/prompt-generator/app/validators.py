"""
Prompt validation and scoring utilities
"""

import re
from typing import Dict, Any, List, Optional
import structlog

from .models import ValidationResult
from .config import settings

logger = structlog.get_logger()


class PromptValidator:
    """Validates and scores prompts"""
    
    def __init__(self):
        self.logger = logger.bind(component="validator")
        self.max_length = settings.max_prompt_length
        
    async def validate_prompt(self, text: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate a prompt and its context"""
        errors = []
        warnings = []
        suggestions = []
        
        # Basic validation
        if not text or not text.strip():
            errors.append("Prompt text cannot be empty")
            
        if len(text) > self.max_length:
            errors.append(f"Prompt exceeds maximum length of {self.max_length} characters")
            
        # Token estimation
        token_count = self._estimate_tokens(text)
        
        # Check for potential issues
        issues = self._check_common_issues(text)
        warnings.extend(issues["warnings"])
        suggestions.extend(issues["suggestions"])
        
        # Validate techniques
        if "techniques" in context:
            technique_issues = self._validate_techniques(context["techniques"])
            errors.extend(technique_issues["errors"])
            warnings.extend(technique_issues["warnings"])
            
        # Calculate scores
        complexity_score = self._calculate_complexity_score(text)
        readability_score = self._calculate_readability_score(text)
        
        # Estimate cost (if API keys are configured)
        estimated_cost = self._estimate_cost(token_count, context.get("target_model"))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            token_count=token_count,
            estimated_cost=estimated_cost,
            complexity_score=complexity_score,
            readability_score=readability_score
        )
        
    def _check_common_issues(self, text: str) -> Dict[str, List[str]]:
        """Check for common prompt issues"""
        warnings = []
        suggestions = []
        
        # Check for ambiguity
        ambiguous_phrases = [
            "it", "this", "that", "they", "them",
            "something", "somehow", "somewhere"
        ]
        text_lower = text.lower()
        ambiguous_count = sum(1 for phrase in ambiguous_phrases if phrase in text_lower.split())
        
        if ambiguous_count > 3:
            warnings.append("Prompt contains ambiguous references that may reduce clarity")
            suggestions.append("Consider being more specific about what you're referring to")
            
        # Check for excessive complexity
        sentence_count = len(re.findall(r'[.!?]+', text))
        avg_sentence_length = len(text.split()) / max(sentence_count, 1)
        
        if avg_sentence_length > 30:
            warnings.append("Sentences are very long, which may reduce clarity")
            suggestions.append("Consider breaking long sentences into shorter, clearer ones")
            
        # Check for missing context
        if len(text.split()) < 10:
            warnings.append("Prompt is very short and may lack necessary context")
            suggestions.append("Consider adding more details about what you want")
            
        # Check for conflicting instructions
        conflicting_patterns = [
            (r'\bbut\s+not\b', r'\band\s+also\b'),
            (r'\bonly\b.*\balso\b', r'\bjust\b.*\badditionally\b')
        ]
        
        for pattern1, pattern2 in conflicting_patterns:
            if re.search(pattern1, text_lower) and re.search(pattern2, text_lower):
                warnings.append("Prompt may contain conflicting instructions")
                suggestions.append("Review your requirements for consistency")
                break
                
        return {"warnings": warnings, "suggestions": suggestions}
        
    def _validate_techniques(self, techniques: List[str]) -> Dict[str, List[str]]:
        """Validate selected techniques"""
        errors = []
        warnings = []
        
        # Check for incompatible techniques
        incompatible_pairs = [
            ("zero_shot", "few_shot"),
            ("chain_of_thought", "tree_of_thoughts")  # Can use both but may be redundant
        ]
        
        for tech1, tech2 in incompatible_pairs:
            if tech1 in techniques and tech2 in techniques:
                warnings.append(f"Techniques '{tech1}' and '{tech2}' may conflict with each other")
                
        # Check for too many techniques
        if len(techniques) > 5:
            warnings.append("Using too many techniques may make the prompt overly complex")
            
        # Check for unknown techniques
        valid_techniques = [
            "chain_of_thought", "tree_of_thoughts", "few_shot", "zero_shot",
            "role_play", "step_by_step", "structured_output", "emotional_appeal",
            "constraints", "analogical"
        ]
        
        for technique in techniques:
            if technique not in valid_techniques:
                errors.append(f"Unknown technique: {technique}")
                
        return {"errors": errors, "warnings": warnings}
        
    def _calculate_complexity_score(self, text: str) -> float:
        """Calculate complexity score (0-1)"""
        score = 0.0
        
        # Length factor
        word_count = len(text.split())
        if word_count > 50:
            score += 0.2
        if word_count > 100:
            score += 0.1
        if word_count > 200:
            score += 0.1
            
        # Sentence complexity
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        if avg_sentence_length > 20:
            score += 0.2
            
        # Technical terms and jargon
        technical_indicators = [
            "algorithm", "optimize", "implement", "architecture",
            "framework", "protocol", "interface", "component"
        ]
        tech_count = sum(1 for term in technical_indicators if term in text.lower())
        score += min(tech_count * 0.05, 0.2)
        
        # Nested structures (parentheses, brackets)
        nesting_count = text.count("(") + text.count("[") + text.count("{")
        score += min(nesting_count * 0.02, 0.2)
        
        return min(score, 1.0)
        
    def _calculate_readability_score(self, text: str) -> float:
        """Calculate readability score (0-1) - higher is more readable"""
        score = 1.0
        
        # Sentence length penalty
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_sentence_length > 20:
                score -= 0.2
            if avg_sentence_length > 30:
                score -= 0.2
                
        # Word complexity penalty
        words = text.split()
        long_words = [w for w in words if len(w) > 10]
        if len(long_words) / max(len(words), 1) > 0.2:
            score -= 0.2
            
        # Punctuation complexity
        complex_punctuation = sum(1 for char in text if char in ";:()[]{}—")
        if complex_punctuation > len(sentences) * 2:
            score -= 0.1
            
        # Clear structure bonus
        if any(marker in text for marker in ["1.", "2.", "•", "-", "Step"]):
            score += 0.1
            
        return max(min(score, 1.0), 0.0)
        
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count"""
        # Simple approximation: ~4 characters per token
        # In production, use tiktoken or model-specific tokenizer
        return len(text) // 4
        
    def _estimate_cost(self, token_count: int, model: Optional[str]) -> Optional[float]:
        """Estimate API cost based on token count and model"""
        if not model:
            return None
            
        # Approximate costs per 1K tokens (input + output)
        cost_per_1k = {
            "gpt-4": 0.06,
            "gpt-3.5-turbo": 0.002,
            "claude-2": 0.01,
            "claude-instant": 0.001
        }
        
        if model in cost_per_1k:
            # Assume output will be similar length to input
            total_tokens = token_count * 2
            return (total_tokens / 1000) * cost_per_1k[model]
            
        return None