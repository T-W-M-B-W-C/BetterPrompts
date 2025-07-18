"""
Prompt generation engine that orchestrates technique application
"""

import time
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
from uuid import uuid4

from .models import (
    PromptGenerationRequest,
    PromptGenerationResponse,
    TechniqueType,
    ValidationResult,
    EnhancementMetrics
)
from .techniques import technique_registry
from .techniques.base import BaseTechnique
from .validators import PromptValidator
from .config import settings

logger = structlog.get_logger()


class PromptGenerationEngine:
    """Main engine for generating enhanced prompts"""
    
    def __init__(self):
        self.validator = PromptValidator()
        self.logger = logger.bind(component="engine")
        self._initialize_techniques()
        
    def _initialize_techniques(self):
        """Initialize all available techniques"""
        # Import technique classes
        from .techniques import (
            ChainOfThoughtTechnique,
            TreeOfThoughtsTechnique,
            FewShotTechnique,
            ZeroShotTechnique,
            RolePlayTechnique,
            StepByStepTechnique,
            StructuredOutputTechnique,
            EmotionalAppealTechnique,
            ConstraintsTechnique,
            AnalogicalTechnique
        )
        
        # Register techniques
        technique_classes = {
            TechniqueType.CHAIN_OF_THOUGHT: ChainOfThoughtTechnique,
            TechniqueType.TREE_OF_THOUGHTS: TreeOfThoughtsTechnique,
            TechniqueType.FEW_SHOT: FewShotTechnique,
            TechniqueType.ZERO_SHOT: ZeroShotTechnique,
            TechniqueType.ROLE_PLAY: RolePlayTechnique,
            TechniqueType.STEP_BY_STEP: StepByStepTechnique,
            TechniqueType.STRUCTURED_OUTPUT: StructuredOutputTechnique,
            TechniqueType.EMOTIONAL_APPEAL: EmotionalAppealTechnique,
            TechniqueType.CONSTRAINTS: ConstraintsTechnique,
            TechniqueType.ANALOGICAL: AnalogicalTechnique
        }
        
        # Load configurations and create instances
        for technique_type, technique_class in technique_classes.items():
            config = self._load_technique_config(technique_type.value)
            technique_registry.register(technique_type.value, technique_class)
            technique_registry.create_instance(technique_type.value, config)
            
        self.logger.info(f"Initialized {len(technique_classes)} techniques")
        
    def _load_technique_config(self, technique_id: str) -> Dict[str, Any]:
        """Load configuration for a specific technique"""
        # In production, this would load from YAML files or database
        # For now, return default config
        return {
            "name": technique_id,
            "enabled": True,
            "priority": 1,
            "parameters": {}
        }
        
    async def generate(self, request: PromptGenerationRequest) -> PromptGenerationResponse:
        """Generate an enhanced prompt"""
        start_time = time.time()
        generation_id = str(uuid4())
        
        self.logger.info(
            "Starting prompt generation",
            generation_id=generation_id,
            techniques=request.techniques,
            intent=request.intent
        )
        
        try:
            # Validate input
            validation_result = await self._validate_request(request)
            if not validation_result.is_valid:
                raise ValueError(f"Invalid request: {', '.join(validation_result.errors)}")
                
            # Prepare context
            context = self._prepare_context(request)
            
            # Apply techniques
            enhanced_prompt = await self._apply_techniques(
                request.text,
                request.techniques,
                context
            )
            
            # Post-process
            enhanced_prompt = self._post_process(enhanced_prompt, request)
            
            # Calculate metrics
            metrics = await self._calculate_metrics(
                request.text,
                enhanced_prompt,
                request.techniques
            )
            
            # Estimate tokens
            token_count = self._estimate_tokens(enhanced_prompt)
            
            # Build response - use aliases for API compatibility
            response = PromptGenerationResponse(
                text=enhanced_prompt,  # Will be aliased to enhanced_prompt
                model_version=settings.app_version,
                tokens_used=token_count,  # Will be aliased to token_count
                # Internal fields
                id=generation_id,
                original_text=request.text,
                techniques_applied=request.techniques,
                metadata={
                    "intent": request.intent,
                    "complexity": request.complexity,
                    "target_model": request.target_model,
                    "metrics": metrics.dict() if metrics else {}
                },
                generation_time_ms=(time.time() - start_time) * 1000,
                confidence_score=metrics.overall_quality if metrics else 0.85,
                warnings=validation_result.warnings
            )
            
            self.logger.info(
                "Prompt generation completed",
                generation_id=generation_id,
                time_ms=response.generation_time_ms,
                token_count=token_count
            )
            
            return response
            
        except Exception as e:
            self.logger.error(
                "Prompt generation failed",
                generation_id=generation_id,
                error=str(e),
                exc_info=True
            )
            raise
            
    async def _validate_request(self, request: PromptGenerationRequest) -> ValidationResult:
        """Validate the generation request"""
        return await self.validator.validate_prompt(
            request.text,
            {
                "techniques": request.techniques,
                "target_model": request.target_model,
                "max_tokens": request.max_tokens
            }
        )
        
    def _prepare_context(self, request: PromptGenerationRequest) -> Dict[str, Any]:
        """Prepare context for technique application"""
        context = {
            "intent": request.intent,
            "complexity": request.complexity,
            "target_model": request.target_model,
            "temperature": request.temperature or settings.default_temperature
        }
        
        # Merge with request context
        if request.context:
            context.update(request.context)
            
        # Add parameters
        if request.parameters:
            context["parameters"] = request.parameters
            
        return context
        
    async def _apply_techniques(
        self,
        text: str,
        techniques: List[str],
        context: Dict[str, Any]
    ) -> str:
        """Apply selected techniques to the text"""
        if not techniques:
            return text
            
        # Sort techniques by priority
        sorted_techniques = self._sort_techniques_by_priority(techniques)
        
        # Apply techniques sequentially
        result = text
        for technique_id in sorted_techniques:
            try:
                # Apply technique
                result = technique_registry.apply_technique(
                    technique_id,
                    result,
                    context
                )
                
                # Add delay to prevent rate limiting if needed
                if settings.enable_async_processing:
                    await asyncio.sleep(0.01)
                    
            except Exception as e:
                self.logger.error(
                    f"Failed to apply technique {technique_id}",
                    error=str(e),
                    exc_info=True
                )
                # Continue with other techniques
                continue
                
        return result
        
    def _sort_techniques_by_priority(self, techniques: List[str]) -> List[str]:
        """Sort techniques by their priority"""
        technique_priorities = []
        
        for technique_id in techniques:
            technique = technique_registry.get_instance(technique_id)
            if technique:
                priority = technique.priority
            else:
                priority = 0
            technique_priorities.append((technique_id, priority))
            
        # Sort by priority (higher first)
        technique_priorities.sort(key=lambda x: x[1], reverse=True)
        
        return [t[0] for t in technique_priorities]
        
    def _post_process(self, prompt: str, request: PromptGenerationRequest) -> str:
        """Post-process the generated prompt"""
        # Clean up excessive whitespace
        prompt = " ".join(prompt.split())
        
        # Apply length constraints
        if request.max_tokens:
            max_chars = request.max_tokens * 4  # Rough approximation
            if len(prompt) > max_chars:
                prompt = prompt[:max_chars].rsplit(" ", 1)[0] + "..."
                
        return prompt.strip()
        
    async def _calculate_metrics(
        self,
        original: str,
        enhanced: str,
        techniques: List[str]
    ) -> Optional[EnhancementMetrics]:
        """Calculate enhancement metrics"""
        try:
            # Calculate basic metrics
            clarity_score = self._calculate_clarity_score(original, enhanced)
            specificity_score = self._calculate_specificity_score(original, enhanced)
            coherence_score = self._calculate_coherence_score(enhanced)
            
            # Calculate technique effectiveness
            technique_effectiveness = {}
            for technique in techniques:
                effectiveness = self._calculate_technique_effectiveness(
                    technique,
                    original,
                    enhanced
                )
                technique_effectiveness[technique] = effectiveness
                
            # Calculate overall quality
            overall_quality = (
                clarity_score * 0.3 +
                specificity_score * 0.3 +
                coherence_score * 0.4
            )
            
            # Calculate improvement percentage
            improvement = ((len(enhanced) - len(original)) / len(original)) * 100
            improvement_percentage = min(max(improvement, -50), 200)  # Cap between -50% and 200%
            
            return EnhancementMetrics(
                clarity_score=clarity_score,
                specificity_score=specificity_score,
                coherence_score=coherence_score,
                technique_effectiveness=technique_effectiveness,
                overall_quality=overall_quality,
                improvement_percentage=improvement_percentage
            )
            
        except Exception as e:
            self.logger.error(f"Failed to calculate metrics: {e}")
            return None
            
    def _calculate_clarity_score(self, original: str, enhanced: str) -> float:
        """Calculate clarity improvement score"""
        # Simple heuristic based on structure and formatting
        score = 0.7  # Base score
        
        # Check for structured elements
        if "\n" in enhanced and "\n" not in original:
            score += 0.1
        if any(marker in enhanced for marker in ["1.", "•", "-", "Step"]):
            score += 0.1
        if enhanced.count("\n\n") > original.count("\n\n"):
            score += 0.1
            
        return min(score, 1.0)
        
    def _calculate_specificity_score(self, original: str, enhanced: str) -> float:
        """Calculate specificity improvement score"""
        # Check for specific instructions and details
        score = 0.6  # Base score
        
        specificity_markers = [
            "specifically", "exactly", "precisely", "follow these steps",
            "ensure", "must", "should", "format", "include", "provide"
        ]
        
        original_markers = sum(1 for marker in specificity_markers if marker in original.lower())
        enhanced_markers = sum(1 for marker in specificity_markers if marker in enhanced.lower())
        
        if enhanced_markers > original_markers:
            score += min((enhanced_markers - original_markers) * 0.1, 0.4)
            
        return min(score, 1.0)
        
    def _calculate_coherence_score(self, enhanced: str) -> float:
        """Calculate coherence score of enhanced prompt"""
        # Check for logical flow and structure
        score = 0.8  # Base score
        
        # Check for transitional elements
        transitions = ["first", "second", "then", "next", "finally", "therefore", "however"]
        transition_count = sum(1 for t in transitions if t in enhanced.lower())
        
        if transition_count >= 2:
            score += 0.1
        if transition_count >= 4:
            score += 0.1
            
        return min(score, 1.0)
        
    def _calculate_technique_effectiveness(
        self,
        technique: str,
        original: str,
        enhanced: str
    ) -> float:
        """Calculate effectiveness of a specific technique"""
        # Technique-specific effectiveness checks
        effectiveness_checks = {
            TechniqueType.CHAIN_OF_THOUGHT.value: lambda o, e: "step" in e.lower() and "think" in e.lower(),
            TechniqueType.FEW_SHOT.value: lambda o, e: "example" in e.lower() or "Example:" in e,
            TechniqueType.STRUCTURED_OUTPUT.value: lambda o, e: any(fmt in e for fmt in ["```", "|", "json", "format"]),
            TechniqueType.ROLE_PLAY.value: lambda o, e: "you are" in e.lower() or "expert" in e.lower(),
            TechniqueType.CONSTRAINTS.value: lambda o, e: "must" in e.lower() or "constraint" in e.lower()
        }
        
        if technique in effectiveness_checks:
            check_func = effectiveness_checks[technique]
            return 0.9 if check_func(original, enhanced) else 0.6
            
        # Default effectiveness
        return 0.75
        
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for the text"""
        # Simple estimation: ~4 characters per token
        # In production, use tiktoken or model-specific tokenizer
        return len(text) // 4