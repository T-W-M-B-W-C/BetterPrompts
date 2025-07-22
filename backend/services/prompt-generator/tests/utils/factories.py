"""Test data factories for prompt-generator tests."""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import random
from faker import Faker

from .constants import (
    TechniqueType, IntentType, ModelProvider,
    TECHNIQUE_COMPATIBILITY, TECHNIQUE_TEMPLATES,
    TEST_PROMPTS_BY_INTENT
)

fake = Faker()


class PromptFactory:
    """Factory for creating prompt-related test data."""
    
    @staticmethod
    def create_prompt_by_intent(
        intent: Optional[IntentType] = None,
        complexity: str = "medium"
    ) -> str:
        """Create a realistic prompt based on intent."""
        if intent is None:
            intent = random.choice(list(IntentType))
        
        # Get prompts for this intent
        prompts = TEST_PROMPTS_BY_INTENT.get(
            intent,
            ["Generate a test prompt for " + intent.value]
        )
        
        base_prompt = random.choice(prompts)
        
        # Adjust complexity
        if complexity == "simple":
            return base_prompt
        elif complexity == "complex":
            # Add more context and requirements
            additions = [
                f" Please be detailed and comprehensive.",
                f" Include examples and best practices.",
                f" Consider edge cases and error handling.",
                f" Optimize for {fake.word(ext_word_list=['performance', 'readability', 'maintainability'])}."
            ]
            return base_prompt + random.choice(additions)
        
        return base_prompt
    
    @staticmethod
    def create_enhanced_prompt(
        original_prompt: str,
        technique: TechniqueType,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create an enhanced prompt using a specific technique."""
        template = TECHNIQUE_TEMPLATES.get(technique, "{original_prompt}")
        
        # Create placeholders based on technique
        placeholders = PromptFactory._get_technique_placeholders(technique, original_prompt)
        
        # Apply template
        enhanced = template
        for key, value in placeholders.items():
            enhanced = enhanced.replace(f"{{{key}}}", str(value))
        
        return enhanced
    
    @staticmethod
    def _get_technique_placeholders(
        technique: TechniqueType,
        original_prompt: str
    ) -> Dict[str, str]:
        """Get placeholders for technique templates."""
        placeholders = {"original_prompt": original_prompt}
        
        if technique == TechniqueType.CHAIN_OF_THOUGHT:
            placeholders.update({
                "problem_aspect": fake.bs(),
                "key_factors": fake.sentence(nb_words=6),
                "relationships": fake.sentence(nb_words=5),
                "conclusion_action": fake.sentence(nb_words=4)
            })
        
        elif technique == TechniqueType.FEW_SHOT:
            placeholders.update({
                "example1_input": fake.sentence(nb_words=8),
                "example1_output": fake.sentence(nb_words=10),
                "example2_input": fake.sentence(nb_words=8),
                "example2_output": fake.sentence(nb_words=10)
            })
        
        elif technique == TechniqueType.TREE_OF_THOUGHTS:
            for i in range(1, 4):
                placeholders.update({
                    f"approach{i}_description": fake.sentence(nb_words=8),
                    f"approach{i}_pros": fake.sentence(nb_words=6),
                    f"approach{i}_cons": fake.sentence(nb_words=6)
                })
        
        elif technique == TechniqueType.STEP_BY_STEP:
            for i in range(1, 5):
                placeholders[f"step{i}_description"] = fake.sentence(nb_words=8)
        
        elif technique == TechniqueType.ROLE_PLAY:
            placeholders.update({
                "role_description": fake.job(),
                "domain": fake.word(ext_word_list=["technology", "science", "business", "education"])
            })
        
        elif technique == TechniqueType.STRUCTURED_OUTPUT:
            placeholders.update({
                "overview_section": fake.sentence(nb_words=12),
                "point1": fake.sentence(nb_words=8),
                "point2": fake.sentence(nb_words=8),
                "point3": fake.sentence(nb_words=8),
                "details_section": fake.paragraph(nb_sentences=3),
                "summary_section": fake.sentence(nb_words=10)
            })
        
        return placeholders
    
    @staticmethod
    def create_generation_scenario(
        scenario_type: str = "standard"
    ) -> Dict[str, Any]:
        """Create a complete generation scenario for testing."""
        scenarios = {
            "standard": {
                "original_prompt": PromptFactory.create_prompt_by_intent(),
                "intent": random.choice(list(IntentType)).value,
                "techniques": random.sample(
                    [t.value for t in TechniqueType],
                    k=random.randint(1, 3)
                ),
                "expected_success": True
            },
            "complex": {
                "original_prompt": PromptFactory.create_prompt_by_intent(
                    complexity="complex"
                ),
                "intent": IntentType.ANALYZE_DATA.value,
                "techniques": [
                    TechniqueType.CHAIN_OF_THOUGHT.value,
                    TechniqueType.TREE_OF_THOUGHTS.value,
                    TechniqueType.STRUCTURED_OUTPUT.value
                ],
                "expected_success": True
            },
            "simple": {
                "original_prompt": "What is 2+2?",
                "intent": IntentType.ANSWER_QUESTION.value,
                "techniques": [TechniqueType.ZERO_SHOT.value],
                "expected_success": True
            },
            "creative": {
                "original_prompt": "Write a poem about coding",
                "intent": IntentType.CREATE_CONTENT.value,
                "techniques": [
                    TechniqueType.ROLE_PLAY.value,
                    TechniqueType.EMOTIONAL_APPEAL.value
                ],
                "expected_success": True
            },
            "incompatible": {
                "original_prompt": "Debug this code error",
                "intent": IntentType.DEBUG_ERROR.value,
                "techniques": [TechniqueType.EMOTIONAL_APPEAL.value],
                "expected_success": False,
                "expected_error": "incompatible_technique"
            }
        }
        
        return scenarios.get(scenario_type, scenarios["standard"])


class TechniqueFactory:
    """Factory for creating technique-related test data."""
    
    @staticmethod
    def create_technique_config(
        technique: TechniqueType,
        enabled: bool = True,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a technique configuration."""
        config = {
            "name": technique.value,
            "enabled": enabled,
            "parameters": {
                "temperature": random.uniform(0.1, 1.0),
                "max_tokens": random.randint(100, 1000),
                "detail_level": random.choice(["low", "medium", "high"])
            },
            "effectiveness_scores": {}
        }
        
        # Add effectiveness scores for compatible intents
        for intent in IntentType:
            if technique.value in TECHNIQUE_COMPATIBILITY.get(intent, []):
                config["effectiveness_scores"][intent.value] = random.uniform(0.7, 0.95)
            else:
                config["effectiveness_scores"][intent.value] = random.uniform(0.3, 0.6)
        
        # Apply custom parameters
        if custom_params:
            config["parameters"].update(custom_params)
        
        return config
    
    @staticmethod
    def create_technique_metrics(
        technique: TechniqueType,
        num_uses: int = 100
    ) -> Dict[str, Any]:
        """Create metrics for a technique."""
        return {
            "technique": technique.value,
            "total_uses": num_uses,
            "success_rate": random.uniform(0.85, 0.98),
            "average_improvement_score": random.uniform(0.6, 0.9),
            "average_generation_time_ms": random.randint(100, 500),
            "user_satisfaction_score": random.uniform(4.0, 5.0),
            "intent_performance": {
                intent.value: {
                    "uses": random.randint(10, 30),
                    "success_rate": random.uniform(0.8, 0.95)
                }
                for intent in IntentType
                if technique.value in TECHNIQUE_COMPATIBILITY.get(intent, [])
            }
        }


class UserContextFactory:
    """Factory for creating user context data."""
    
    @staticmethod
    def create_user_context(
        user_type: str = "regular",
        include_history: bool = True
    ) -> Dict[str, Any]:
        """Create user context for testing."""
        contexts = {
            "regular": {
                "user_id": f"user_{fake.uuid4()[:8]}",
                "session_id": f"session_{fake.uuid4()[:8]}",
                "preferences": {
                    "preferred_techniques": random.sample(
                        [t.value for t in TechniqueType],
                        k=random.randint(2, 4)
                    ),
                    "preferred_model": random.choice(["gpt-4", "claude-3"]),
                    "complexity_preference": "intermediate"
                },
                "usage_stats": {
                    "total_generations": random.randint(50, 500),
                    "favorite_intents": random.sample(
                        [i.value for i in IntentType],
                        k=3
                    )
                }
            },
            "power": {
                "user_id": f"power_{fake.uuid4()[:8]}",
                "session_id": f"session_{fake.uuid4()[:8]}",
                "preferences": {
                    "preferred_techniques": [
                        TechniqueType.CHAIN_OF_THOUGHT.value,
                        TechniqueType.TREE_OF_THOUGHTS.value,
                        TechniqueType.SELF_CONSISTENCY.value
                    ],
                    "preferred_model": "gpt-4",
                    "complexity_preference": "complex",
                    "custom_parameters": {
                        "temperature": 0.8,
                        "max_tokens": 2000
                    }
                },
                "usage_stats": {
                    "total_generations": random.randint(1000, 5000),
                    "favorite_intents": [
                        IntentType.ANALYZE_DATA.value,
                        IntentType.GENERATE_CODE.value
                    ]
                }
            },
            "new": {
                "user_id": f"new_{fake.uuid4()[:8]}",
                "session_id": f"session_{fake.uuid4()[:8]}",
                "preferences": {},
                "usage_stats": {
                    "total_generations": 0,
                    "favorite_intents": []
                }
            }
        }
        
        context = contexts.get(user_type, contexts["regular"]).copy()
        
        # Add generation history if requested
        if include_history and user_type != "new":
            context["history"] = [
                {
                    "prompt": PromptFactory.create_prompt_by_intent(),
                    "techniques_used": random.sample(
                        [t.value for t in TechniqueType],
                        k=random.randint(1, 3)
                    ),
                    "satisfaction_score": random.randint(3, 5),
                    "timestamp": (
                        datetime.now(timezone.utc) - timedelta(hours=i)
                    ).isoformat()
                }
                for i in range(random.randint(5, 20))
            ]
        
        return context


class ModelFactory:
    """Factory for creating model-related test data."""
    
    @staticmethod
    def create_model_config(
        provider: ModelProvider,
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a model configuration."""
        configs = {
            ModelProvider.OPENAI: {
                "provider": "openai",
                "model": model_name or random.choice(["gpt-4", "gpt-3.5-turbo"]),
                "temperature": 0.7,
                "max_tokens": 2000,
                "top_p": 0.9,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            },
            ModelProvider.ANTHROPIC: {
                "provider": "anthropic",
                "model": model_name or random.choice(["claude-3-opus", "claude-3-sonnet"]),
                "temperature": 0.7,
                "max_tokens": 2000,
                "top_k": 40
            }
        }
        
        return configs.get(provider, configs[ModelProvider.OPENAI])
    
    @staticmethod
    def create_model_response(
        provider: ModelProvider,
        content: Optional[str] = None,
        tokens_used: Optional[Tuple[int, int]] = None
    ) -> Dict[str, Any]:
        """Create a mock model response."""
        if content is None:
            content = fake.paragraph(nb_sentences=5)
        
        if tokens_used is None:
            prompt_tokens = random.randint(50, 200)
            completion_tokens = random.randint(50, 300)
        else:
            prompt_tokens, completion_tokens = tokens_used
        
        if provider == ModelProvider.OPENAI:
            return {
                "id": f"chatcmpl-{fake.uuid4()[:8]}",
                "object": "chat.completion",
                "created": int(datetime.now(timezone.utc).timestamp()),
                "model": "gpt-4",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens
                }
            }
        
        elif provider == ModelProvider.ANTHROPIC:
            return {
                "id": f"msg_{fake.uuid4()[:8]}",
                "type": "message",
                "role": "assistant",
                "content": [{
                    "type": "text",
                    "text": content
                }],
                "model": "claude-3-opus",
                "stop_reason": "end_turn",
                "usage": {
                    "input_tokens": prompt_tokens,
                    "output_tokens": completion_tokens
                }
            }
        
        return {"content": content}