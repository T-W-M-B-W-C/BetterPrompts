"""
Unit tests for prompt validators
"""

import pytest
from unittest.mock import patch

from app.validators import PromptValidator
from app.models import ValidationResult
from app.config import settings


class TestPromptValidator:
    """Test the PromptValidator class"""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance"""
        return PromptValidator()
        
    @pytest.mark.asyncio
    async def test_validate_empty_prompt(self, validator):
        """Test validation of empty prompt"""
        result = await validator.validate_prompt("", {})
        
        assert not result.is_valid
        assert "Prompt text cannot be empty" in result.errors
        assert result.token_count == 0
        
    @pytest.mark.asyncio
    async def test_validate_whitespace_only_prompt(self, validator):
        """Test validation of whitespace-only prompt"""
        result = await validator.validate_prompt("   \n\t  ", {})
        
        assert not result.is_valid
        assert "Prompt text cannot be empty" in result.errors
        
    @pytest.mark.asyncio
    async def test_validate_too_long_prompt(self, validator):
        """Test validation of prompt exceeding max length"""
        # Create a prompt longer than max length
        long_prompt = "a" * (validator.max_length + 100)
        
        result = await validator.validate_prompt(long_prompt, {})
        
        assert not result.is_valid
        assert f"Prompt exceeds maximum length of {validator.max_length} characters" in result.errors
        
    @pytest.mark.asyncio
    async def test_validate_valid_prompt(self, validator):
        """Test validation of valid prompt"""
        prompt = "Explain the concept of machine learning in simple terms"
        context = {"techniques": ["chain_of_thought", "analogical"]}
        
        result = await validator.validate_prompt(prompt, context)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.token_count > 0
        assert 0 <= result.complexity_score <= 1
        assert 0 <= result.readability_score <= 1
        
    @pytest.mark.asyncio
    async def test_check_ambiguous_references(self, validator):
        """Test detection of ambiguous references"""
        prompt = "It is important that they understand this and that thing somehow"
        
        result = await validator.validate_prompt(prompt, {})
        
        assert result.is_valid  # Warnings don't make it invalid
        assert any("ambiguous references" in w for w in result.warnings)
        assert any("more specific" in s for s in result.suggestions)
        
    @pytest.mark.asyncio
    async def test_check_long_sentences(self, validator):
        """Test detection of overly long sentences"""
        # Create a very long sentence
        long_sentence = " ".join(["word"] * 50) + "."
        
        result = await validator.validate_prompt(long_sentence, {})
        
        assert any("very long" in w for w in result.warnings)
        assert any("shorter" in s for s in result.suggestions)
        
    @pytest.mark.asyncio
    async def test_check_short_prompt(self, validator):
        """Test detection of very short prompts"""
        prompt = "Do this"
        
        result = await validator.validate_prompt(prompt, {})
        
        assert any("very short" in w for w in result.warnings)
        assert any("more details" in s for s in result.suggestions)
        
    @pytest.mark.asyncio
    async def test_check_conflicting_instructions(self, validator):
        """Test detection of conflicting instructions"""
        prompt = "Only include the summary but not the details and also add comprehensive analysis"
        
        result = await validator.validate_prompt(prompt, {})
        
        assert any("conflicting" in w for w in result.warnings)
        assert any("consistency" in s for s in result.suggestions)
        
    @pytest.mark.asyncio
    async def test_validate_incompatible_techniques(self, validator):
        """Test validation of incompatible technique combinations"""
        prompt = "Test prompt"
        context = {"techniques": ["zero_shot", "few_shot"]}
        
        result = await validator.validate_prompt(prompt, context)
        
        assert result.is_valid  # Still valid, just with warnings
        assert any("conflict" in w for w in result.warnings)
        
    @pytest.mark.asyncio
    async def test_validate_too_many_techniques(self, validator):
        """Test validation with too many techniques"""
        prompt = "Test prompt"
        context = {
            "techniques": [
                "chain_of_thought", "tree_of_thoughts", "few_shot",
                "role_play", "step_by_step", "structured_output",
                "emotional_appeal"  # 7 techniques
            ]
        }
        
        result = await validator.validate_prompt(prompt, context)
        
        assert any("too many techniques" in w for w in result.warnings)
        
    @pytest.mark.asyncio
    async def test_validate_unknown_technique(self, validator):
        """Test validation with unknown technique"""
        prompt = "Test prompt"
        context = {"techniques": ["chain_of_thought", "unknown_technique"]}
        
        result = await validator.validate_prompt(prompt, context)
        
        assert not result.is_valid
        assert any("Unknown technique: unknown_technique" in e for e in result.errors)
        
    def test_calculate_complexity_score(self, validator):
        """Test complexity score calculation"""
        # Simple prompt
        simple = "What is AI?"
        score_simple = validator._calculate_complexity_score(simple)
        assert 0 <= score_simple <= 0.3
        
        # Moderate complexity
        moderate = "Explain the differences between supervised and unsupervised learning algorithms, including examples of each type and their use cases in real-world applications."
        score_moderate = validator._calculate_complexity_score(moderate)
        assert 0.3 < score_moderate <= 0.7
        
        # Complex prompt
        complex_prompt = """
        Design and implement a distributed machine learning system that can:
        1. Process streaming data from multiple sources
        2. Apply different algorithms (classification, clustering, regression)
        3. Handle fault tolerance and scalability
        4. Provide real-time predictions with sub-second latency
        5. Include monitoring and alerting capabilities
        
        The system should use microservices architecture with Docker containers,
        implement proper authentication and authorization, and integrate with
        existing data pipelines using Apache Kafka.
        """
        score_complex = validator._calculate_complexity_score(complex_prompt)
        assert score_complex > 0.7
        
    def test_calculate_readability_score(self, validator):
        """Test readability score calculation"""
        # Highly readable
        readable = "Write a simple function. It should add two numbers. Return the result."
        score_readable = validator._calculate_readability_score(readable)
        assert score_readable > 0.8
        
        # Less readable (long sentences, complex words)
        less_readable = "Implement a comprehensive multithreaded asynchronous processing mechanism that instantiates numerous concurrent execution contexts while maintaining transactional integrity across distributed heterogeneous systems."
        score_less = validator._calculate_readability_score(less_readable)
        assert score_less < score_readable
        
        # Structured format (should boost readability)
        structured = """
        Please complete the following:
        1. First task
        2. Second task
        3. Third task
        """
        score_structured = validator._calculate_readability_score(structured)
        assert score_structured > 0.8
        
    def test_estimate_tokens(self, validator):
        """Test token estimation"""
        # Test various text lengths
        short_text = "Hello world"
        medium_text = "This is a medium length prompt with several words in it for testing"
        long_text = "Lorem ipsum " * 50
        
        short_tokens = validator._estimate_tokens(short_text)
        medium_tokens = validator._estimate_tokens(medium_text)
        long_tokens = validator._estimate_tokens(long_text)
        
        # Basic sanity checks
        assert short_tokens < medium_tokens < long_tokens
        assert short_tokens > 0
        
        # Check approximation (roughly 1 token per 4 characters)
        assert abs(short_tokens - len(short_text) // 4) < 5
        
    def test_estimate_cost(self, validator):
        """Test cost estimation for different models"""
        token_count = 1000
        
        # Test known models
        cost_gpt4 = validator._estimate_cost(token_count, "gpt-4")
        cost_gpt35 = validator._estimate_cost(token_count, "gpt-3.5-turbo")
        cost_claude2 = validator._estimate_cost(token_count, "claude-2")
        
        assert cost_gpt4 > cost_gpt35  # GPT-4 is more expensive
        assert cost_gpt4 > cost_claude2
        assert all(cost > 0 for cost in [cost_gpt4, cost_gpt35, cost_claude2])
        
        # Test unknown model
        cost_unknown = validator._estimate_cost(token_count, "unknown-model")
        assert cost_unknown is None
        
        # Test no model specified
        cost_none = validator._estimate_cost(token_count, None)
        assert cost_none is None
        
    @pytest.mark.asyncio
    async def test_validate_with_all_checks(self, validator):
        """Test comprehensive validation with all checks"""
        prompt = """
        This is a comprehensive test prompt that includes various elements.
        It has multiple sentences of varying lengths. Some are short. 
        Others are quite long and include technical terminology like 
        algorithm optimization and architectural patterns.
        
        The prompt includes:
        - Structured elements
        - Technical terms
        - Varying complexity
        
        Please implement this but not that, and also ensure everything works.
        """
        
        context = {
            "techniques": ["chain_of_thought", "structured_output"],
            "target_model": "gpt-4",
            "max_tokens": 500
        }
        
        result = await validator.validate_prompt(prompt, context)
        
        assert result.is_valid
        assert result.token_count > 50
        assert result.complexity_score > 0.4
        assert result.readability_score > 0.5
        assert result.estimated_cost > 0
        
        # Should have some warnings due to conflicting instructions
        assert len(result.warnings) > 0
        
    @pytest.mark.asyncio
    async def test_validate_edge_cases(self, validator):
        """Test validation edge cases"""
        # Unicode and special characters
        unicode_prompt = "Explain 人工智能 and machine learning 🤖"
        result1 = await validator.validate_prompt(unicode_prompt, {})
        assert result1.is_valid
        
        # Only punctuation
        punct_prompt = "...??!!!"
        result2 = await validator.validate_prompt(punct_prompt, {})
        assert result2.is_valid  # Valid but likely has warnings
        
        # Extremely nested structure
        nested_prompt = "Do this (but first (check if (condition is (met))))"
        result3 = await validator.validate_prompt(nested_prompt, {})
        assert result3.is_valid
        assert result3.complexity_score > 0  # Nesting adds complexity