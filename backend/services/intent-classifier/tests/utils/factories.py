"""Test data factories for intent-classifier tests."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import random
import hashlib
from faker import Faker
from pydantic_factories import ModelFactory

# We'll define factories once we have the actual Pydantic models
# For now, we'll use dictionary-based factories

fake = Faker()


class IntentClassificationFactory:
    """Factory for creating intent classification test data."""
    
    @staticmethod
    def create_prompt(
        intent_type: Optional[str] = None,
        complexity: Optional[str] = None,
        domain: Optional[str] = None,
        length: str = "medium"
    ) -> str:
        """Create a realistic prompt for testing."""
        prompts_by_intent = {
            "generate_code": [
                "Write a Python function to {action} {object}",
                "Create a {language} class that {functionality}",
                "Implement {algorithm} in {language}",
                "Build a {type} that {action} {data}"
            ],
            "explain_concept": [
                "Explain {concept} in simple terms",
                "What is {technology} and how does it work?",
                "Help me understand {topic}",
                "Can you explain the difference between {item1} and {item2}?"
            ],
            "debug_error": [
                "I'm getting this error: {error}. My code: {code}",
                "Why is my {component} not working? Error: {error}",
                "Help me fix this {language} error: {error}",
                "Debug this code: {code}"
            ],
            "analyze_data": [
                "Analyze this {data_type} data and find {pattern}",
                "What trends do you see in {dataset}?",
                "Create visualizations for {data}",
                "Perform {analysis_type} analysis on {data}"
            ],
            "answer_question": [
                "What is {question}?",
                "How do I {action}?",
                "When should I use {technology}?",
                "Why does {phenomenon} happen?"
            ],
            "create_content": [
                "Write a {content_type} about {topic}",
                "Create {creative_work} that {characteristics}",
                "Generate {format} content for {audience}",
                "Compose a {type} with {requirements}"
            ]
        }
        
        # Select intent type
        if not intent_type:
            intent_type = random.choice(list(prompts_by_intent.keys()))
        
        # Get template
        templates = prompts_by_intent.get(intent_type, ["Generate a test prompt"])
        template = random.choice(templates)
        
        # Fill in placeholders
        placeholders = {
            "action": fake.word(ext_word_list=["calculate", "process", "transform", "validate", "parse"]),
            "object": fake.word(ext_word_list=["data", "file", "array", "string", "number"]),
            "language": random.choice(["Python", "JavaScript", "Java", "Go", "TypeScript"]),
            "functionality": fake.bs(),
            "algorithm": random.choice(["quicksort", "binary search", "DFS", "BFS", "dijkstra"]),
            "type": random.choice(["API", "function", "class", "service", "component"]),
            "data": fake.word(ext_word_list=["JSON", "CSV", "XML", "database records"]),
            "concept": fake.word(ext_word_list=["recursion", "polymorphism", "microservices", "machine learning"]),
            "technology": fake.word(ext_word_list=["Docker", "Kubernetes", "React", "GraphQL"]),
            "topic": fake.bs(),
            "item1": fake.word(),
            "item2": fake.word(),
            "error": f"{fake.word()}Error: {fake.sentence(nb_words=5)}",
            "code": f"```\\n{fake.text(max_nb_chars=100)}\\n```",
            "component": random.choice(["button", "form", "API", "database connection"]),
            "data_type": random.choice(["sales", "user", "performance", "financial"]),
            "pattern": random.choice(["trends", "anomalies", "correlations", "outliers"]),
            "dataset": f"{fake.word()} dataset",
            "analysis_type": random.choice(["statistical", "time series", "regression", "clustering"]),
            "question": fake.sentence(nb_words=6).rstrip('.') + "?",
            "phenomenon": fake.bs(),
            "content_type": random.choice(["blog post", "article", "story", "report"]),
            "creative_work": random.choice(["poem", "story", "song", "script"]),
            "characteristics": fake.sentence(nb_words=4),
            "format": random.choice(["marketing", "technical", "educational", "entertainment"]),
            "audience": random.choice(["developers", "students", "professionals", "general public"]),
            "requirements": fake.sentence(nb_words=5)
        }
        
        prompt = template
        for key, value in placeholders.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))
        
        # Adjust length
        if length == "short":
            prompt = prompt[:50]
        elif length == "long":
            prompt = prompt + " " + fake.paragraph(nb_sentences=5)
        
        return prompt
    
    @staticmethod
    def create_classification_result(
        prompt: Optional[str] = None,
        override_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a complete classification result."""
        if not prompt:
            prompt = IntentClassificationFactory.create_prompt()
        
        # Base result
        result = {
            "prompt": prompt,
            "intent": random.choice([
                "generate_code", "explain_concept", "debug_error",
                "analyze_data", "answer_question", "create_content"
            ]),
            "confidence": round(random.uniform(0.7, 0.99), 2),
            "sub_intent": random.choice(["technical", "creative", "analytical", None]),
            "complexity": random.choice(["simple", "intermediate", "complex"]),
            "domain": random.choice(["programming", "science", "business", "general"]),
            "suggested_techniques": random.sample([
                "chain_of_thought", "few_shot", "zero_shot", "tree_of_thoughts",
                "self_consistency", "step_by_step", "role_play"
            ], k=random.randint(1, 3)),
            "metadata": {
                "model_version": "1.0.0",
                "inference_time_ms": random.randint(20, 150),
                "token_count": len(prompt.split()),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Apply overrides
        if override_fields:
            result.update(override_fields)
        
        return result
    
    @staticmethod
    def create_user_context(
        user_type: str = "regular",
        history_length: int = 10
    ) -> Dict[str, Any]:
        """Create user context for testing."""
        contexts = {
            "regular": {
                "user_id": f"user_{fake.uuid4()[:8]}",
                "session_id": f"session_{fake.uuid4()[:8]}",
                "preferences": {
                    "preferred_techniques": random.sample(["chain_of_thought", "few_shot"], k=1),
                    "complexity_preference": "intermediate"
                },
                "usage_stats": {
                    "total_requests": random.randint(50, 500),
                    "average_confidence": round(random.uniform(0.8, 0.95), 2)
                }
            },
            "new": {
                "user_id": f"new_user_{fake.uuid4()[:8]}",
                "session_id": f"session_{fake.uuid4()[:8]}",
                "preferences": {},
                "usage_stats": {
                    "total_requests": 0,
                    "average_confidence": 0.0
                }
            },
            "power": {
                "user_id": f"power_user_{fake.uuid4()[:8]}",
                "session_id": f"session_{fake.uuid4()[:8]}",
                "preferences": {
                    "preferred_techniques": ["tree_of_thoughts", "chain_of_thought", "self_consistency"],
                    "complexity_preference": "complex",
                    "domains": ["programming", "science"]
                },
                "usage_stats": {
                    "total_requests": random.randint(1000, 5000),
                    "average_confidence": round(random.uniform(0.9, 0.98), 2)
                }
            },
            "api": {
                "api_key": f"sk-{fake.uuid4().replace('-', '')}",
                "organization_id": f"org_{fake.uuid4()[:8]}",
                "usage_stats": {
                    "total_requests": random.randint(10000, 100000),
                    "rate_limit": 1000,
                    "current_usage": random.randint(0, 500)
                }
            }
        }
        
        context = contexts.get(user_type, contexts["regular"]).copy()
        
        # Add history
        if history_length > 0 and user_type != "new":
            context["history"] = [
                {
                    "prompt": IntentClassificationFactory.create_prompt(),
                    "intent": random.choice(["generate_code", "explain_concept", "answer_question"]),
                    "timestamp": (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat()
                }
                for i in range(history_length)
            ]
        
        return context
    
    @staticmethod
    def create_batch_prompts(
        size: int = 10,
        mixed_intents: bool = True
    ) -> List[str]:
        """Create a batch of prompts for testing."""
        if mixed_intents:
            return [
                IntentClassificationFactory.create_prompt(
                    intent_type=random.choice([
                        "generate_code", "explain_concept", "debug_error",
                        "analyze_data", "answer_question", "create_content"
                    ])
                )
                for _ in range(size)
            ]
        else:
            # All same intent
            intent = random.choice(["generate_code", "explain_concept", "answer_question"])
            return [
                IntentClassificationFactory.create_prompt(intent_type=intent)
                for _ in range(size)
            ]
    
    @staticmethod
    def create_cache_entry(
        prompt: str,
        ttl_seconds: int = 3600
    ) -> Dict[str, Any]:
        """Create a cache entry for testing."""
        result = IntentClassificationFactory.create_classification_result(prompt)
        
        return {
            "key": f"intent:v1:{hashlib.sha256(prompt.encode()).hexdigest()[:16]}",
            "value": result,
            "ttl": ttl_seconds,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()
        }
    
    @staticmethod
    def create_performance_metrics(
        num_requests: int = 100
    ) -> Dict[str, Any]:
        """Create performance metrics for testing."""
        return {
            "total_requests": num_requests,
            "successful_requests": int(num_requests * 0.98),
            "failed_requests": int(num_requests * 0.02),
            "average_latency_ms": round(random.uniform(50, 150), 2),
            "p95_latency_ms": round(random.uniform(150, 300), 2),
            "p99_latency_ms": round(random.uniform(300, 500), 2),
            "cache_hit_rate": round(random.uniform(0.3, 0.7), 2),
            "average_confidence": round(random.uniform(0.85, 0.95), 2),
            "intent_distribution": {
                "generate_code": int(num_requests * 0.25),
                "explain_concept": int(num_requests * 0.20),
                "debug_error": int(num_requests * 0.15),
                "analyze_data": int(num_requests * 0.15),
                "answer_question": int(num_requests * 0.15),
                "create_content": int(num_requests * 0.10)
            }
        }