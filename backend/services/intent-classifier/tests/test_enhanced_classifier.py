"""
Test suite for Enhanced Rule-Based Classifier
Tests 50+ diverse examples covering all intent types and edge cases
"""

import pytest
from typing import List, Tuple
from backend.services.intent_classifier.app.models.enhanced_classifier import (
    EnhancedRuleBasedClassifier, 
    AudienceLevel
)


class TestEnhancedClassifier:
    """Comprehensive tests for the enhanced rule-based classifier"""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance"""
        return EnhancedRuleBasedClassifier()
    
    def test_question_answering_intents(self, classifier):
        """Test question answering intent detection"""
        test_cases = [
            # Basic questions
            ("What is machine learning?", "question_answering", 0.8),
            ("How does photosynthesis work?", "question_answering", 0.8),
            ("Can you explain quantum computing?", "question_answering", 0.85),
            ("Tell me about the French Revolution", "question_answering", 0.8),
            
            # Child-oriented questions
            ("Explain gravity to a 5 year old", "question_answering", 0.9),
            ("What is rain? (explain like I'm 5)", "question_answering", 0.9),
            ("Tell me about dinosaurs in simple terms for kids", "question_answering", 0.9),
            
            # Complex questions
            ("Walk me through the process of DNA replication", "question_answering", 0.85),
            ("Why does the stock market fluctuate?", "question_answering", 0.8),
            ("How do neural networks learn?", "question_answering", 0.8),
        ]
        
        for text, expected_intent, min_confidence in test_cases:
            result = classifier.classify(text)
            assert result.intent == expected_intent, f"Failed for: {text}"
            assert result.confidence >= min_confidence, f"Low confidence for: {text}"
    
    def test_creative_writing_intents(self, classifier):
        """Test creative writing intent detection"""
        test_cases = [
            ("Write a story about a magical forest", "creative_writing", 0.85),
            ("Create a poem about the ocean", "creative_writing", 0.85),
            ("Help me write an essay on climate change", "creative_writing", 0.8),
            ("Draft a blog post about productivity tips", "creative_writing", 0.8),
            ("Compose a children's story about friendship", "creative_writing", 0.9),
            ("Generate a creative story with dragons", "creative_writing", 0.85),
        ]
        
        for text, expected_intent, min_confidence in test_cases:
            result = classifier.classify(text)
            assert result.intent == expected_intent, f"Failed for: {text}"
            assert result.confidence >= min_confidence, f"Low confidence for: {text}"
    
    def test_code_generation_intents(self, classifier):
        """Test code generation intent detection"""
        test_cases = [
            ("Write a Python function to calculate fibonacci numbers", "code_generation", 0.9),
            ("Create a JavaScript function for sorting arrays", "code_generation", 0.9),
            ("Implement a binary search algorithm in Java", "code_generation", 0.9),
            ("Code for connecting to a database in Python", "code_generation", 0.85),
            ("Write SQL query to find top customers", "code_generation", 0.9),
            ("Create a REST API endpoint in Node.js", "code_generation", 0.85),
            ("Debug this Python code for me", "code_generation", 0.8),
        ]
        
        for text, expected_intent, min_confidence in test_cases:
            result = classifier.classify(text)
            assert result.intent == expected_intent, f"Failed for: {text}"
            assert result.confidence >= min_confidence, f"Low confidence for: {text}"
    
    def test_data_analysis_intents(self, classifier):
        """Test data analysis intent detection"""
        test_cases = [
            ("Analyze the sales data for Q3", "data_analysis", 0.85),
            ("Create a chart showing revenue trends", "data_analysis", 0.85),
            ("Find patterns in customer behavior data", "data_analysis", 0.85),
            ("Generate insights from this dataset", "data_analysis", 0.8),
            ("Statistical analysis of survey results", "data_analysis", 0.85),
            ("Examine the correlation between variables", "data_analysis", 0.8),
        ]
        
        for text, expected_intent, min_confidence in test_cases:
            result = classifier.classify(text)
            assert result.intent == expected_intent, f"Failed for: {text}"
            assert result.confidence >= min_confidence, f"Low confidence for: {text}"
    
    def test_translation_intents(self, classifier):
        """Test translation intent detection"""
        test_cases = [
            ("Translate this to Spanish", "translation", 0.9),
            ("How do you say 'hello' in French?", "translation", 0.9),
            ("Convert this text from English to German", "translation", 0.9),
            ("Translate 'I love you' into Japanese", "translation", 0.95),
            ("What's this in Italian?", "translation", 0.85),
        ]
        
        for text, expected_intent, min_confidence in test_cases:
            result = classifier.classify(text)
            assert result.intent == expected_intent, f"Failed for: {text}"
            assert result.confidence >= min_confidence, f"Low confidence for: {text}"
    
    def test_audience_detection(self, classifier):
        """Test audience level detection"""
        test_cases = [
            ("Explain quantum physics to a 5 year old", AudienceLevel.CHILD),
            ("Tell me about space like I'm a kid", AudienceLevel.CHILD),
            ("I'm a beginner, how does coding work?", AudienceLevel.BEGINNER),
            ("Give me an advanced explanation of neural networks", AudienceLevel.EXPERT),
            ("Explain this in simple terms for children", AudienceLevel.CHILD),
            ("I'm new to this, can you help?", AudienceLevel.BEGINNER),
            ("Provide a technical deep-dive into the algorithm", AudienceLevel.EXPERT),
            ("Just a regular explanation please", AudienceLevel.GENERAL),
        ]
        
        for text, expected_audience in test_cases:
            result = classifier.classify(text)
            assert result.audience == expected_audience, f"Wrong audience for: {text}"
    
    def test_complexity_detection(self, classifier):
        """Test complexity level detection"""
        test_cases = [
            ("What is water?", "simple"),
            ("Explain quantum computing to a 5 year old", "simple"),  # Child audience forces simple
            ("Analyze the economic implications of monetary policy on emerging markets", "complex"),
            ("Write a basic Python function", "moderate"),
            ("Create a comprehensive analysis of multiple data sources with statistical validation", "complex"),
            ("How does a car work?", "moderate"),
        ]
        
        for text, expected_complexity in test_cases:
            result = classifier.classify(text)
            assert result.complexity == expected_complexity, f"Wrong complexity for: {text}"
    
    def test_edge_cases(self, classifier):
        """Test edge cases and ambiguous inputs"""
        test_cases = [
            # Very short inputs
            ("hi", "conversation", 0.2, 0.5),
            ("test", "conversation", 0.2, 0.5),
            
            # Mixed intent signals
            ("Write code to analyze data", ["code_generation", "data_analysis"], 0.7, 1.0),
            ("Explain how to write Python code", ["question_answering", "code_generation"], 0.7, 1.0),
            ("Create a plan to solve this problem", ["task_planning", "problem_solving"], 0.7, 1.0),
            
            # Ambiguous requests
            ("Help me with this", "conversation", 0.2, 0.5),
            ("Can you do something for me?", "conversation", 0.2, 0.5),
        ]
        
        for test_case in test_cases:
            if len(test_case) == 4:
                text, expected_intents, min_conf, max_conf = test_case
                if isinstance(expected_intents, list):
                    # Multiple acceptable intents
                    result = classifier.classify(text)
                    assert result.intent in expected_intents, f"Intent not in expected list for: {text}"
                    assert min_conf <= result.confidence <= max_conf, f"Confidence out of range for: {text}"
                else:
                    # Single intent
                    text, expected_intent, min_conf, max_conf = test_case
                    result = classifier.classify(text)
                    assert result.intent == expected_intent, f"Failed for: {text}"
                    assert min_conf <= result.confidence <= max_conf, f"Confidence out of range for: {text}"
    
    def test_confidence_scoring(self, classifier):
        """Test confidence scoring accuracy"""
        # High confidence cases (clear, unambiguous)
        high_confidence = [
            "Write a Python function to sort a list",
            "Translate 'hello world' to Spanish",
            "Summarize this article for me",
        ]
        
        for text in high_confidence:
            result = classifier.classify(text)
            assert result.confidence >= 0.8, f"Expected high confidence for: {text}"
        
        # Low confidence cases (vague, ambiguous)
        low_confidence = [
            "Help",
            "Do something",
            "What about this?",
        ]
        
        for text in low_confidence:
            result = classifier.classify(text)
            assert result.confidence <= 0.5, f"Expected low confidence for: {text}"
    
    def test_pattern_matching_quality(self, classifier):
        """Test the quality of pattern matching"""
        test_cases = [
            ("Can you explain machine learning to me?", ["phrase:can you explain", "keyword:explain"]),
            ("Write Python code for data analysis", ["keyword:code", "keyword:python", "keyword:analyze", "keyword:data"]),
            ("I'm a beginner learning to code", ["keyword:code", "beginner"]),
        ]
        
        for text, expected_patterns in test_cases:
            result = classifier.classify(text)
            # Check that at least some expected patterns were matched
            matched_types = [p.split(':')[0] for p in result.matched_patterns]
            assert any(pt.split(':')[0] in matched_types for pt in expected_patterns), \
                f"Expected pattern types not found for: {text}"
    
    def test_metadata_completeness(self, classifier):
        """Test that metadata is properly populated"""
        text = "Write a Python function to analyze data"
        result = classifier.classify(text)
        
        assert "method" in result.metadata
        assert result.metadata["method"] == "enhanced_rules"
        assert "all_matches" in result.metadata
        assert len(result.metadata["all_matches"]) <= 3  # Top 3 matches
        
        # Verify all_matches format
        for intent, score in result.metadata["all_matches"]:
            assert isinstance(intent, str)
            assert isinstance(score, (int, float))
            assert 0 <= score <= 1


def run_comprehensive_tests():
    """Run all tests and provide summary"""
    classifier = EnhancedRuleBasedClassifier()
    test_suite = TestEnhancedClassifier()
    
    print("Running Enhanced Classifier Tests...")
    print("=" * 60)
    
    test_methods = [
        ("Question Answering", test_suite.test_question_answering_intents),
        ("Creative Writing", test_suite.test_creative_writing_intents),
        ("Code Generation", test_suite.test_code_generation_intents),
        ("Data Analysis", test_suite.test_data_analysis_intents),
        ("Translation", test_suite.test_translation_intents),
        ("Audience Detection", test_suite.test_audience_detection),
        ("Complexity Detection", test_suite.test_complexity_detection),
        ("Edge Cases", test_suite.test_edge_cases),
        ("Confidence Scoring", test_suite.test_confidence_scoring),
        ("Pattern Matching", test_suite.test_pattern_matching_quality),
        ("Metadata", test_suite.test_metadata_completeness),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_method in test_methods:
        try:
            test_method(classifier)
            print(f"✅ {test_name}: PASSED")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_name}: FAILED - {str(e)}")
            failed += 1
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {str(e)}")
            failed += 1
    
    print("=" * 60)
    print(f"Total Tests: {len(test_methods)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(test_methods))*100:.1f}%")
    
    return passed, failed


if __name__ == "__main__":
    # Run tests when script is executed directly
    run_comprehensive_tests()