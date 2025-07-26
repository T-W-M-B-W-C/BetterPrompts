"""Tests for the Wave 6 Adaptive Model Router."""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from app.models.adaptive_router import (
    AdaptiveModelRouter,
    ModelType,
    ModelMetrics,
    RoutingDecision
)
from app.models.enhanced_classifier import EnhancedRuleBasedClassifier, ClassificationResult, AudienceLevel
from app.models.zero_shot_classifier import HybridClassifier


class TestAdaptiveModelRouter:
    """Test cases for adaptive model routing."""
    
    @pytest.fixture
    def mock_rule_classifier(self):
        """Create a mock rule-based classifier."""
        classifier = Mock(spec=EnhancedRuleBasedClassifier)
        
        # Mock classification result
        result = Mock(spec=ClassificationResult)
        result.intent = "question_answering"
        result.confidence = 0.9
        result.complexity = "simple"
        result.audience = AudienceLevel.GENERAL
        result.metadata = {"suggested_techniques": ["few_shot"]}
        
        classifier.classify.return_value = result
        return classifier
    
    @pytest.fixture
    def mock_hybrid_classifier(self):
        """Create a mock hybrid classifier."""
        classifier = AsyncMock(spec=HybridClassifier)
        
        # Mock async classification result
        classifier.classify.return_value = {
            "intent": "code_generation",
            "confidence": 0.85,
            "complexity": "moderate",
            "suggested_techniques": ["chain_of_thought", "few_shot"],
            "audience": "general",
            "classification_method": "zero_shot",
            "tokens_used": 100,
        }
        
        return classifier
    
    @pytest.fixture
    def mock_torchserve_client(self):
        """Create a mock TorchServe client."""
        client = AsyncMock()
        
        # Mock classification result
        client.classify.return_value = {
            "intent": "data_analysis",
            "confidence": 0.95,
            "complexity": {"level": "complex"},
            "techniques": [{"name": "tree_of_thoughts"}, {"name": "chain_of_thought"}],
            "metadata": {"tokens_used": 200},
        }
        
        return client
    
    @pytest.fixture
    def adaptive_router(self, mock_rule_classifier, mock_hybrid_classifier, mock_torchserve_client):
        """Create an adaptive router with mocked components."""
        return AdaptiveModelRouter(
            rule_classifier=mock_rule_classifier,
            hybrid_classifier=mock_hybrid_classifier,
            torchserve_client=mock_torchserve_client,
            enable_ab_testing=True,
            ab_test_percentage=0.5  # 50% for easier testing
        )
    
    @pytest.mark.asyncio
    async def test_routing_with_high_rule_confidence(self, adaptive_router):
        """Test that high rule confidence selects rule-based model."""
        # Mock high confidence for rules
        adaptive_router.rule_classifier.classify.return_value.confidence = 0.9
        
        result, decision = await adaptive_router.route_and_classify(
            text="What is the capital of France?",
            latency_requirement="critical",
            min_confidence=0.7
        )
        
        # Should use rules due to high confidence and critical latency
        assert decision.selected_model == ModelType.RULES
        assert result["intent"] == "question_answering"
        assert result["confidence"] == 0.9
        assert "routing_metadata" in result
    
    @pytest.mark.asyncio
    async def test_routing_with_low_rule_confidence(self, adaptive_router):
        """Test that low rule confidence triggers upgrade to zero-shot."""
        # Mock low confidence for rules
        adaptive_router.rule_classifier.classify.return_value.confidence = 0.6
        
        # Disable A/B testing for predictable results
        adaptive_router.enable_ab_testing = False
        
        result, decision = await adaptive_router.route_and_classify(
            text="Write a complex algorithm for sorting",
            latency_requirement="standard",
            min_confidence=0.7
        )
        
        # Should upgrade to zero-shot due to low rule confidence
        assert decision.selected_model == ModelType.ZERO_SHOT
        assert result["intent"] == "code_generation"
        assert result["confidence"] == 0.85
    
    @pytest.mark.asyncio
    async def test_routing_with_relaxed_latency(self, adaptive_router):
        """Test that relaxed latency allows DistilBERT usage."""
        # Disable A/B testing
        adaptive_router.enable_ab_testing = False
        
        result, decision = await adaptive_router.route_and_classify(
            text="Analyze this complex dataset and provide insights",
            latency_requirement="relaxed",
            min_confidence=0.8
        )
        
        # Should use DistilBERT with relaxed latency
        assert decision.selected_model == ModelType.DISTILBERT
        assert result["intent"] == "data_analysis"
        assert result["confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_ab_testing_group_assignment(self, adaptive_router):
        """Test A/B testing group assignment."""
        results = []
        
        # Run multiple requests to get different A/B groups
        for i in range(20):
            result, decision = await adaptive_router.route_and_classify(
                text=f"Test query {i}",
                latency_requirement="standard"
            )
            if decision.ab_test_group:
                results.append(decision.ab_test_group)
        
        # Should have some A/B test assignments
        assert len(results) > 0
        assert len(set(results)) > 1  # Multiple groups
        
        # Check that all groups are valid
        valid_groups = {"control", "aggressive_rules", "balanced", "quality_first"}
        assert all(group in valid_groups for group in results)
    
    @pytest.mark.asyncio
    async def test_latency_tracking(self, adaptive_router):
        """Test that latency is properly tracked."""
        # Run a classification
        result, decision = await adaptive_router.route_and_classify(
            text="Test query for latency tracking",
            latency_requirement="standard"
        )
        
        # Check latency is recorded
        model_metrics = adaptive_router.metrics[decision.selected_model]
        assert len(model_metrics.recent_latencies) > 0
        assert model_metrics.latency_p50 > 0
        
        # Run more to update percentiles
        for i in range(10):
            await adaptive_router.route_and_classify(
                text=f"Test query {i}",
                latency_requirement="standard"
            )
        
        # Check percentiles are updated
        assert model_metrics.latency_p50 > 0
        assert model_metrics.latency_p95 >= model_metrics.latency_p50
        assert model_metrics.latency_p99 >= model_metrics.latency_p95
    
    @pytest.mark.asyncio
    async def test_fallback_on_torchserve_failure(self, adaptive_router):
        """Test fallback to zero-shot when TorchServe fails."""
        # Make TorchServe fail
        adaptive_router.torchserve_client.classify.side_effect = Exception("TorchServe error")
        
        # Disable A/B testing and force DistilBERT selection
        adaptive_router.enable_ab_testing = False
        adaptive_router.confidence_thresholds[ModelType.RULES] = 0.99  # Force upgrade
        
        result, decision = await adaptive_router.route_and_classify(
            text="Complex query requiring DistilBERT",
            latency_requirement="relaxed"
        )
        
        # Should fall back to zero-shot
        assert result["intent"] == "code_generation"  # From zero-shot mock
        assert result["confidence"] == 0.85
    
    def test_routing_stats(self, adaptive_router):
        """Test routing statistics generation."""
        # Add some mock history
        adaptive_router.routing_history = [
            {
                "timestamp": time.time(),
                "text_length": 50,
                "model": "rules",
                "latency": 15.0,
                "confidence": 0.9,
                "ab_group": "control",
            },
            {
                "timestamp": time.time(),
                "text_length": 100,
                "model": "zero_shot",
                "latency": 120.0,
                "confidence": 0.85,
                "ab_group": "balanced",
            },
        ]
        
        # Update metrics
        adaptive_router.metrics[ModelType.RULES].total_requests = 10
        adaptive_router.metrics[ModelType.ZERO_SHOT].total_requests = 5
        
        stats = adaptive_router.get_routing_stats()
        
        assert stats["total_requests"] == 15
        assert "model_distribution" in stats
        assert "average_latencies" in stats
        assert "ab_test_groups" in stats
        
        # Check A/B test group stats
        assert "control" in stats["ab_test_groups"]
        assert "balanced" in stats["ab_test_groups"]
        assert stats["ab_test_groups"]["control"]["count"] == 1
        assert stats["ab_test_groups"]["balanced"]["count"] == 1
    
    def test_update_confidence_threshold(self, adaptive_router):
        """Test updating confidence thresholds."""
        # Update threshold
        adaptive_router.update_confidence_threshold(ModelType.RULES, 0.8)
        
        assert adaptive_router.confidence_thresholds[ModelType.RULES] == 0.8
        
        # Test invalid threshold
        with pytest.raises(ValueError):
            adaptive_router.update_confidence_threshold(ModelType.RULES, 1.5)
    
    def test_update_accuracy_estimate(self, adaptive_router):
        """Test updating accuracy estimates."""
        # Update accuracy
        adaptive_router.update_accuracy_estimate(ModelType.ZERO_SHOT, 0.88)
        
        assert adaptive_router.metrics[ModelType.ZERO_SHOT].accuracy_estimate == 0.88
        
        # Test invalid accuracy
        with pytest.raises(ValueError):
            adaptive_router.update_accuracy_estimate(ModelType.ZERO_SHOT, -0.1)
    
    @pytest.mark.asyncio
    async def test_consistent_user_ab_assignment(self, adaptive_router):
        """Test that users get consistent A/B test assignments."""
        user_id = "test_user_123"
        groups = []
        
        # Run multiple requests with same user ID
        for i in range(10):
            result, decision = await adaptive_router.route_and_classify(
                text=f"Test query {i}",
                latency_requirement="standard",
                user_id=user_id
            )
            if decision.ab_test_group:
                groups.append(decision.ab_test_group)
        
        # All assignments should be the same for the same user
        if groups:
            assert all(group == groups[0] for group in groups)
    
    @pytest.mark.asyncio
    async def test_quality_first_strategy(self, adaptive_router):
        """Test quality-first A/B testing strategy."""
        # Force quality-first strategy
        with patch.object(adaptive_router, '_route_quality_first') as mock_quality:
            mock_quality.return_value = RoutingDecision(
                selected_model=ModelType.DISTILBERT,
                confidence_threshold=0.0,
                expected_latency=400.0,
                reasons=["Strategy: Quality-first with DistilBERT preference"],
                ab_test_group="quality_first"
            )
            
            # Enable A/B testing with 100% chance
            adaptive_router.ab_test_percentage = 1.0
            adaptive_router.ab_test_groups = {"quality_first": mock_quality}
            
            result, decision = await adaptive_router.route_and_classify(
                text="Test quality-first strategy",
                latency_requirement="critical"  # Even with critical latency
            )
            
            # Should still use DistilBERT
            assert decision.selected_model == ModelType.DISTILBERT
            assert decision.ab_test_group == "quality_first"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])