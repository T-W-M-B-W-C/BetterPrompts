"""Diversity strategies for generating varied training examples."""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import random
import hashlib
from collections import defaultdict

from prompt_templates import (
    IntentType, 
    AudienceLevel, 
    ComplexityLevel,
    PromptTemplateManager
)
from loguru import logger


@dataclass
class DiversityMetrics:
    """Metrics for measuring diversity in generated examples."""
    audience_distribution: Dict[AudienceLevel, int]
    complexity_distribution: Dict[ComplexityLevel, int]
    length_distribution: Dict[str, int]  # short, medium, long
    uniqueness_score: float  # 0-1, based on unique n-grams
    topic_coverage: float  # 0-1, based on topics covered
    style_variety: float  # 0-1, based on writing styles


class DiversityStrategy:
    """Strategies for ensuring diversity in generated examples."""
    
    def __init__(self):
        self.template_manager = PromptTemplateManager()
        self.used_examples = set()  # Track generated examples to avoid duplicates
        self.topic_usage = defaultdict(int)  # Track topic usage
        self.style_modifiers = self._create_style_modifiers()
        self.complexity_modifiers = self._create_complexity_modifiers()
    
    def _create_style_modifiers(self) -> Dict[str, List[str]]:
        """Create style modifiers for different contexts."""
        return {
            "formal": [
                "Please provide a formal",
                "I would like to request",
                "Could you kindly",
                "It would be appreciated if you could",
                "I am seeking assistance with"
            ],
            "casual": [
                "Hey, can you",
                "I need help with",
                "Quick question:",
                "Just wondering",
                "Could you"
            ],
            "technical": [
                "Implement",
                "Analyze",
                "Evaluate",
                "Optimize",
                "Design"
            ],
            "urgent": [
                "I urgently need",
                "ASAP:",
                "This is time-sensitive:",
                "Critical:",
                "High priority:"
            ],
            "polite": [
                "Would you mind",
                "If possible, could you",
                "When you have a moment",
                "I'd be grateful if",
                "Please, at your convenience"
            ],
            "direct": [
                "I want",
                "Give me",
                "Show me",
                "Tell me",
                "Explain"
            ]
        }
    
    def _create_complexity_modifiers(self) -> Dict[ComplexityLevel, Dict[str, Any]]:
        """Create modifiers for different complexity levels."""
        return {
            ComplexityLevel.SIMPLE: {
                "connectors": ["and", "but", "so"],
                "sentence_count": (1, 2),
                "word_count": (5, 20),
                "technical_terms": 0,
                "nested_concepts": False
            },
            ComplexityLevel.MODERATE: {
                "connectors": ["however", "therefore", "additionally", "furthermore"],
                "sentence_count": (2, 4),
                "word_count": (20, 50),
                "technical_terms": (1, 3),
                "nested_concepts": True
            },
            ComplexityLevel.COMPLEX: {
                "connectors": ["consequently", "moreover", "nevertheless", "notwithstanding"],
                "sentence_count": (3, 6),
                "word_count": (50, 150),
                "technical_terms": (3, 7),
                "nested_concepts": True,
                "multi_part": True
            }
        }
    
    def generate_diverse_prompt(
        self,
        intent: IntentType,
        audience: AudienceLevel,
        complexity: ComplexityLevel,
        force_unique: bool = True
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate a diverse prompt with metadata."""
        
        # Get base template
        template = self.template_manager.get_template(intent, audience, complexity)
        base_prompt = self.template_manager.generate_prompt_from_template(template)
        
        # Apply diversity strategies
        diverse_prompt = self._apply_diversity_strategies(
            base_prompt, 
            intent, 
            audience, 
            complexity
        )
        
        # Ensure uniqueness if required
        if force_unique:
            attempts = 0
            while self._get_prompt_hash(diverse_prompt) in self.used_examples and attempts < 10:
                diverse_prompt = self._apply_diversity_strategies(
                    base_prompt, 
                    intent, 
                    audience, 
                    complexity
                )
                attempts += 1
            
            self.used_examples.add(self._get_prompt_hash(diverse_prompt))
        
        # Generate metadata
        metadata = {
            "intent": intent.value,
            "audience": audience.value,
            "complexity": complexity.value,
            "length": len(diverse_prompt.split()),
            "style": self._detect_style(diverse_prompt),
            "has_multiple_parts": self._has_multiple_parts(diverse_prompt),
            "technical_level": self._assess_technical_level(diverse_prompt),
            "confidence_expected": self._estimate_confidence(intent, audience, complexity)
        }
        
        return diverse_prompt, metadata
    
    def _apply_diversity_strategies(
        self,
        prompt: str,
        intent: IntentType,
        audience: AudienceLevel,
        complexity: ComplexityLevel
    ) -> str:
        """Apply various diversity strategies to a prompt."""
        
        # Strategy 1: Add style modifiers
        if random.random() < 0.6:  # 60% chance to add style
            style = random.choice(list(self.style_modifiers.keys()))
            modifier = random.choice(self.style_modifiers[style])
            prompt = f"{modifier} {prompt.lower()}"
        
        # Strategy 2: Add context or constraints
        if complexity in [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX]:
            if random.random() < 0.5:
                prompt = self._add_context(prompt, intent, audience)
        
        # Strategy 3: Vary sentence structure
        if complexity == ComplexityLevel.COMPLEX and random.random() < 0.4:
            prompt = self._complexify_structure(prompt, complexity)
        
        # Strategy 4: Add audience-specific elements
        prompt = self._add_audience_elements(prompt, audience)
        
        # Strategy 5: Add domain-specific variations
        if intent in [IntentType.CODE_GENERATION, IntentType.DATA_ANALYSIS]:
            prompt = self._add_technical_variations(prompt, complexity)
        
        return prompt
    
    def _add_context(self, prompt: str, intent: IntentType, audience: AudienceLevel) -> str:
        """Add contextual information to the prompt."""
        contexts = {
            IntentType.QUESTION_ANSWERING: [
                "I'm researching this for a project.",
                "I need this for my work.",
                "I'm trying to understand this better.",
                "This came up in a discussion."
            ],
            IntentType.CODE_GENERATION: [
                "I'm building a web application.",
                "This is for a data processing pipeline.",
                "I need this for a microservice.",
                "This is part of a larger system."
            ],
            IntentType.DATA_ANALYSIS: [
                "We have a dataset with 1M records.",
                "This is for quarterly reporting.",
                "We need insights for decision-making.",
                "The data comes from multiple sources."
            ],
            IntentType.CREATIVE_WRITING: [
                "This is for a creative writing class.",
                "I'm working on a novel.",
                "This is for a blog post.",
                "I need this for a presentation."
            ]
        }
        
        if intent in contexts and random.random() < 0.5:
            context = random.choice(contexts[intent])
            prompt = f"{prompt} {context}"
        
        return prompt
    
    def _complexify_structure(self, prompt: str, complexity: ComplexityLevel) -> str:
        """Add complexity to the sentence structure."""
        modifiers = self.complexity_modifiers[complexity]
        
        # Add multiple parts
        if modifiers.get("multi_part") and random.random() < 0.6:
            additions = [
                "Also, please include",
                "Additionally, I need",
                "Furthermore, consider",
                "Moreover, ensure that"
            ]
            
            additional_requirements = [
                "examples to illustrate the concepts",
                "best practices and common pitfalls",
                "performance considerations",
                "alternative approaches",
                "pros and cons of different methods"
            ]
            
            addition = random.choice(additions)
            requirement = random.choice(additional_requirements)
            prompt = f"{prompt} {addition} {requirement}."
        
        return prompt
    
    def _add_audience_elements(self, prompt: str, audience: AudienceLevel) -> str:
        """Add elements specific to the target audience."""
        audience_elements = {
            AudienceLevel.CHILD: [
                "in simple words",
                "like I'm 5 years old",
                "with fun examples",
                "using things I know"
            ],
            AudienceLevel.BEGINNER: [
                "for someone new to this",
                "with basic examples",
                "step by step",
                "assuming no prior knowledge"
            ],
            AudienceLevel.EXPERT: [
                "with technical details",
                "including edge cases",
                "with performance analysis",
                "considering scalability"
            ]
        }
        
        if audience in audience_elements and random.random() < 0.3:
            element = random.choice(audience_elements[audience])
            prompt = f"{prompt} {element}"
        
        return prompt
    
    def _add_technical_variations(self, prompt: str, complexity: ComplexityLevel) -> str:
        """Add technical variations for technical intents."""
        if complexity == ComplexityLevel.COMPLEX:
            technical_additions = [
                "with O(n log n) time complexity",
                "using design patterns",
                "following SOLID principles",
                "with error handling",
                "including unit tests",
                "with documentation"
            ]
            
            if random.random() < 0.4:
                addition = random.choice(technical_additions)
                prompt = f"{prompt} {addition}"
        
        return prompt
    
    def _get_prompt_hash(self, prompt: str) -> str:
        """Get a hash of the prompt for uniqueness checking."""
        return hashlib.md5(prompt.encode()).hexdigest()
    
    def _detect_style(self, prompt: str) -> str:
        """Detect the style of a prompt."""
        prompt_lower = prompt.lower()
        
        for style, modifiers in self.style_modifiers.items():
            for modifier in modifiers:
                if modifier.lower() in prompt_lower:
                    return style
        
        return "neutral"
    
    def _has_multiple_parts(self, prompt: str) -> bool:
        """Check if prompt has multiple parts."""
        indicators = ["also", "additionally", "furthermore", "moreover", "and", "plus"]
        return any(indicator in prompt.lower() for indicator in indicators)
    
    def _assess_technical_level(self, prompt: str) -> int:
        """Assess technical level of prompt (0-10)."""
        technical_terms = [
            "algorithm", "optimize", "complexity", "architecture", "framework",
            "implementation", "performance", "scalability", "distributed", "async",
            "machine learning", "neural network", "API", "database", "encryption"
        ]
        
        count = sum(1 for term in technical_terms if term in prompt.lower())
        return min(count * 2, 10)  # Scale to 0-10
    
    def _estimate_confidence(
        self, 
        intent: IntentType, 
        audience: AudienceLevel, 
        complexity: ComplexityLevel
    ) -> float:
        """Estimate expected confidence for this type of prompt."""
        # Base confidence by intent
        base_confidence = {
            IntentType.QUESTION_ANSWERING: 0.90,
            IntentType.CODE_GENERATION: 0.85,
            IntentType.CREATIVE_WRITING: 0.88,
            IntentType.DATA_ANALYSIS: 0.82,
            IntentType.REASONING: 0.80,
            IntentType.SUMMARIZATION: 0.87,
            IntentType.TRANSLATION: 0.92,
            IntentType.CONVERSATION: 0.85,
            IntentType.TASK_PLANNING: 0.83,
            IntentType.PROBLEM_SOLVING: 0.84
        }
        
        confidence = base_confidence.get(intent, 0.85)
        
        # Adjust for audience
        audience_adjustment = {
            AudienceLevel.CHILD: 0.05,
            AudienceLevel.BEGINNER: 0.03,
            AudienceLevel.INTERMEDIATE: 0,
            AudienceLevel.EXPERT: -0.05,
            AudienceLevel.GENERAL: 0
        }
        
        confidence += audience_adjustment.get(audience, 0)
        
        # Adjust for complexity
        complexity_adjustment = {
            ComplexityLevel.SIMPLE: 0.05,
            ComplexityLevel.MODERATE: 0,
            ComplexityLevel.COMPLEX: -0.08
        }
        
        confidence += complexity_adjustment.get(complexity, 0)
        
        # Add some random variation
        confidence += random.uniform(-0.05, 0.05)
        
        return max(0.6, min(0.99, confidence))
    
    def calculate_diversity_metrics(self, examples: List[Dict[str, Any]]) -> DiversityMetrics:
        """Calculate diversity metrics for a set of examples."""
        audience_dist = defaultdict(int)
        complexity_dist = defaultdict(int)
        length_dist = {"short": 0, "medium": 0, "long": 0}
        
        all_texts = []
        unique_ngrams = set()
        
        for example in examples:
            metadata = example.get("metadata", {})
            
            # Count distributions
            audience = metadata.get("audience")
            if audience:
                audience_dist[AudienceLevel(audience)] += 1
            
            complexity = metadata.get("complexity")
            if complexity:
                complexity_dist[ComplexityLevel(complexity)] += 1
            
            # Length distribution
            text = example.get("text", "")
            word_count = len(text.split())
            if word_count < 20:
                length_dist["short"] += 1
            elif word_count < 50:
                length_dist["medium"] += 1
            else:
                length_dist["long"] += 1
            
            all_texts.append(text)
            
            # Collect n-grams for uniqueness
            words = text.lower().split()
            for i in range(len(words) - 2):
                unique_ngrams.add(" ".join(words[i:i+3]))
        
        # Calculate uniqueness score
        total_possible_ngrams = sum(max(0, len(text.split()) - 2) for text in all_texts)
        uniqueness_score = len(unique_ngrams) / max(1, total_possible_ngrams)
        
        # Topic coverage (simplified - based on intent variety)
        intents = set(ex.get("intent") for ex in examples if ex.get("intent"))
        topic_coverage = len(intents) / len(IntentType)
        
        # Style variety (based on detected styles)
        styles = set(ex.get("metadata", {}).get("style") for ex in examples)
        style_variety = len(styles) / 6  # We have 6 style types
        
        return DiversityMetrics(
            audience_distribution=dict(audience_dist),
            complexity_distribution=dict(complexity_dist),
            length_distribution=length_dist,
            uniqueness_score=uniqueness_score,
            topic_coverage=topic_coverage,
            style_variety=style_variety
        )


# Edge case generator
class EdgeCaseGenerator:
    """Generator for edge cases and ambiguous examples."""
    
    def __init__(self):
        self.ambiguous_patterns = self._create_ambiguous_patterns()
    
    def _create_ambiguous_patterns(self) -> List[Dict[str, Any]]:
        """Create patterns for ambiguous examples."""
        return [
            {
                "pattern": "mixed_intent",
                "description": "Prompts that could belong to multiple intents",
                "examples": [
                    ("Analyze this story and tell me what it means", 
                     [IntentType.DATA_ANALYSIS, IntentType.SUMMARIZATION, IntentType.REASONING]),
                    ("Write code to solve this math problem",
                     [IntentType.CODE_GENERATION, IntentType.PROBLEM_SOLVING, IntentType.REASONING]),
                    ("Translate this algorithm into plain English",
                     [IntentType.TRANSLATION, IntentType.SUMMARIZATION, IntentType.QUESTION_ANSWERING])
                ]
            },
            {
                "pattern": "vague_request",
                "description": "Prompts that are intentionally vague",
                "examples": [
                    ("Help me with this", None),
                    ("I need something for my project", None),
                    ("Can you do the thing we discussed?", None)
                ]
            },
            {
                "pattern": "typos_and_errors",
                "description": "Prompts with common typos and grammatical errors",
                "examples": [
                    ("how do i right a function to sort a list", IntentType.CODE_GENERATION),
                    ("wat is the differance between AI and ML", IntentType.QUESTION_ANSWERING),
                    ("plz explain quantum compuitng simple terms", IntentType.QUESTION_ANSWERING)
                ]
            },
            {
                "pattern": "extreme_length",
                "description": "Very short or very long prompts",
                "examples": [
                    ("?", None),
                    ("help", None),
                    ("explain", IntentType.QUESTION_ANSWERING),
                    # Very long prompt would be generated dynamically
                ]
            },
            {
                "pattern": "multiple_languages",
                "description": "Prompts mixing multiple languages",
                "examples": [
                    ("Please explique comment fonctionne machine learning", IntentType.QUESTION_ANSWERING),
                    ("Write a function para calcular el promedio", IntentType.CODE_GENERATION),
                    ("Translate '你好' and explain what it means", IntentType.TRANSLATION)
                ]
            },
            {
                "pattern": "emotional_context",
                "description": "Prompts with strong emotional context",
                "examples": [
                    ("I'm so frustrated! Why doesn't my code work?!", IntentType.PROBLEM_SOLVING),
                    ("This is urgent!!! I need this analysis NOW!", IntentType.DATA_ANALYSIS),
                    ("I'm completely lost. Can you help me understand recursion?", IntentType.QUESTION_ANSWERING)
                ]
            }
        ]
    
    def generate_edge_case(self, pattern_type: str = None) -> Tuple[str, Optional[IntentType], Dict[str, Any]]:
        """Generate an edge case example."""
        if pattern_type:
            patterns = [p for p in self.ambiguous_patterns if p["pattern"] == pattern_type]
        else:
            patterns = self.ambiguous_patterns
        
        if not patterns:
            patterns = self.ambiguous_patterns
        
        pattern = random.choice(patterns)
        
        if pattern["pattern"] == "extreme_length" and random.random() < 0.5:
            # Generate a very long prompt
            base = "I need help with a complex problem involving "
            topics = [
                "machine learning", "data analysis", "system design",
                "algorithm optimization", "database queries", "API design"
            ]
            
            parts = []
            for _ in range(random.randint(5, 10)):
                topic = random.choice(topics)
                detail = f"specifically regarding {topic} and how it relates to "
                parts.append(detail)
            
            prompt = base + "".join(parts) + "the overall system performance."
            intent = IntentType.PROBLEM_SOLVING
            metadata = {"edge_case_type": "extreme_length_long", "word_count": len(prompt.split())}
        
        else:
            example = random.choice(pattern["examples"])
            prompt = example[0]
            intent = example[1] if isinstance(example[1], IntentType) else None
            
            metadata = {
                "edge_case_type": pattern["pattern"],
                "ambiguous": isinstance(example[1], list),
                "possible_intents": [i.value for i in example[1]] if isinstance(example[1], list) else []
            }
        
        return prompt, intent, metadata
    
    def generate_ambiguous_example(self) -> Tuple[str, List[IntentType], Dict[str, Any]]:
        """Generate an intentionally ambiguous example."""
        ambiguous_examples = [
            {
                "prompt": "Can you help me understand and implement a solution for this?",
                "intents": [IntentType.QUESTION_ANSWERING, IntentType.CODE_GENERATION, IntentType.PROBLEM_SOLVING],
                "primary_intent": IntentType.PROBLEM_SOLVING,
                "confidence_range": (0.3, 0.5)
            },
            {
                "prompt": "Analyze the following and provide insights with examples",
                "intents": [IntentType.DATA_ANALYSIS, IntentType.REASONING, IntentType.QUESTION_ANSWERING],
                "primary_intent": IntentType.DATA_ANALYSIS,
                "confidence_range": (0.4, 0.6)
            },
            {
                "prompt": "I need you to process this information and create something useful",
                "intents": [IntentType.SUMMARIZATION, IntentType.CREATIVE_WRITING, IntentType.DATA_ANALYSIS],
                "primary_intent": IntentType.DATA_ANALYSIS,
                "confidence_range": (0.3, 0.5)
            },
            {
                "prompt": "Show me how to approach this problem step by step",
                "intents": [IntentType.TASK_PLANNING, IntentType.PROBLEM_SOLVING, IntentType.QUESTION_ANSWERING],
                "primary_intent": IntentType.PROBLEM_SOLVING,
                "confidence_range": (0.5, 0.7)
            },
            {
                "prompt": "Can you break this down and explain what's happening?",
                "intents": [IntentType.QUESTION_ANSWERING, IntentType.REASONING, IntentType.SUMMARIZATION],
                "primary_intent": IntentType.QUESTION_ANSWERING,
                "confidence_range": (0.4, 0.6)
            }
        ]
        
        example = random.choice(ambiguous_examples)
        
        metadata = {
            "edge_case_type": "intentionally_ambiguous",
            "possible_intents": [i.value for i in example["intents"]],
            "expected_confidence_range": example["confidence_range"],
            "primary_intent": example["primary_intent"].value
        }
        
        return example["prompt"], example["intents"], metadata