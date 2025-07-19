import pytest
from unittest.mock import Mock, patch
from app.models.intent_classifier import IntentClassifier
from app.models.schemas import IntentRequest, IntentResponse

class TestIntentClassifier:
    """Test suite for the Intent Classification service"""
    
    @pytest.fixture
    def classifier(self):
        """Create a mock classifier instance"""
        with patch('app.models.intent_classifier.pipeline') as mock_pipeline:
            mock_model = Mock()
            mock_pipeline.return_value = mock_model
            classifier = IntentClassifier()
            classifier.model = mock_model
            return classifier
    
    def test_classify_simple_prompt(self, classifier):
        """Test classification of simple prompts"""
        # Mock model response
        classifier.model.return_value = [{
            'label': 'information_retrieval',
            'score': 0.95
        }]
        
        request = IntentRequest(input="What is the capital of France?")
        result = classifier.classify(request)
        
        assert result.category == 'information_retrieval'
        assert result.complexity < 0.3
        assert result.confidence > 0.9
        assert len(result.sub_intents) == 0
    
    def test_classify_complex_prompt(self, classifier):
        """Test classification of complex multi-intent prompts"""
        # Mock model response for complex prompt
        classifier.model.return_value = [{
            'label': 'analysis',
            'score': 0.85
        }]
        
        complex_prompt = """
        Analyze the quarterly sales data, identify trends, 
        create visualizations, and provide recommendations 
        for improving performance in underperforming regions.
        """
        
        request = IntentRequest(input=complex_prompt)
        result = classifier.classify(request)
        
        assert result.category == 'analysis'
        assert result.complexity > 0.7
        assert len(result.sub_intents) > 0
        assert 'data_analysis' in result.sub_intents
        assert 'visualization' in result.sub_intents
    
    def test_classify_code_generation(self, classifier):
        """Test classification of code generation requests"""
        classifier.model.return_value = [{
            'label': 'code_generation',
            'score': 0.92
        }]
        
        request = IntentRequest(
            input="Write a Python function to sort a list using quicksort"
        )
        result = classifier.classify(request)
        
        assert result.category == 'code_generation'
        assert result.confidence > 0.9
        assert 'algorithm_implementation' in result.sub_intents
    
    def test_empty_input_handling(self, classifier):
        """Test handling of empty input"""
        request = IntentRequest(input="")
        
        with pytest.raises(ValueError, match="Input cannot be empty"):
            classifier.classify(request)
    
    def test_very_long_input_handling(self, classifier):
        """Test handling of very long inputs"""
        long_input = "x" * 10000  # Very long input
        request = IntentRequest(input=long_input)
        
        # Should truncate and still classify
        classifier.model.return_value = [{
            'label': 'other',
            'score': 0.5
        }]
        
        result = classifier.classify(request)
        assert result is not None
        assert result.category == 'other'
    
    @pytest.mark.parametrize("prompt,expected_category,min_complexity", [
        ("Hello", "greeting", 0.0),
        ("Explain quantum physics", "educational", 0.5),
        ("Debug this code: print('hello')", "debugging", 0.4),
        ("Write a business plan", "planning", 0.8),
        ("Translate to Spanish", "translation", 0.3),
    ])
    def test_various_prompt_types(self, classifier, prompt, expected_category, min_complexity):
        """Test classification of various prompt types"""
        classifier.model.return_value = [{
            'label': expected_category,
            'score': 0.8
        }]
        
        request = IntentRequest(input=prompt)
        result = classifier.classify(request)
        
        assert result.category == expected_category
        assert result.complexity >= min_complexity
    
    def test_confidence_threshold(self, classifier):
        """Test low confidence handling"""
        classifier.model.return_value = [{
            'label': 'unclear',
            'score': 0.3  # Low confidence
        }]
        
        request = IntentRequest(input="???")
        result = classifier.classify(request)
        
        assert result.category == 'unclear'
        assert result.confidence < 0.5
        assert result.requires_clarification is True
    
    def test_multi_label_classification(self, classifier):
        """Test handling of multi-label results"""
        classifier.model.return_value = [
            {'label': 'analysis', 'score': 0.7},
            {'label': 'visualization', 'score': 0.65},
            {'label': 'reporting', 'score': 0.6}
        ]
        
        request = IntentRequest(
            input="Analyze data and create charts for the report"
        )
        result = classifier.classify(request)
        
        assert result.category == 'analysis'  # Highest score
        assert 'visualization' in result.sub_intents
        assert 'reporting' in result.sub_intents