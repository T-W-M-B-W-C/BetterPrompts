"""Data validation module for ensuring quality of generated training data."""

import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict
import re
from datetime import datetime

from pydantic import BaseModel, ValidationError, Field, validator
from jsonschema import validate, ValidationError as JsonSchemaError
from loguru import logger

from prompt_templates import IntentType, AudienceLevel, ComplexityLevel


class ValidationResult(BaseModel):
    """Result of data validation."""
    is_valid: bool
    total_examples: int
    valid_examples: int
    invalid_examples: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)


class DataValidator:
    """Validates generated training data for quality and correctness."""
    
    def __init__(self):
        self.schema = self._create_json_schema()
        self.quality_rules = self._create_quality_rules()
        self.statistics = defaultdict(int)
    
    def _create_json_schema(self) -> Dict[str, Any]:
        """Create JSON schema for validation."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["metadata", "examples"],
            "properties": {
                "metadata": {
                    "type": "object",
                    "required": ["generated_at", "total_examples", "config", "statistics"],
                    "properties": {
                        "generated_at": {"type": "string"},
                        "total_examples": {"type": "integer", "minimum": 0},
                        "config": {"type": "object"},
                        "statistics": {"type": "object"},
                        "diversity_metrics": {"type": "object"}
                    }
                },
                "examples": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["text", "intent", "audience", "complexity", "confidence"],
                        "properties": {
                            "text": {"type": "string", "minLength": 1},
                            "intent": {
                                "type": "string",
                                "enum": [intent.value for intent in IntentType]
                            },
                            "audience": {
                                "type": "string",
                                "enum": [audience.value for audience in AudienceLevel]
                            },
                            "complexity": {
                                "type": "string",
                                "enum": [complexity.value for complexity in ComplexityLevel]
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0
                            },
                            "metadata": {"type": "object"},
                            "generated_at": {"type": "string"},
                            "generation_method": {"type": "string"}
                        }
                    }
                }
            }
        }
    
    def _create_quality_rules(self) -> List[Dict[str, Any]]:
        """Create quality validation rules."""
        return [
            {
                "name": "text_length",
                "description": "Text should be reasonable length",
                "min_length": 3,
                "max_length": 1000,
                "warning_threshold": 500
            },
            {
                "name": "confidence_range",
                "description": "Confidence should be realistic",
                "min_confidence": 0.3,
                "max_confidence": 0.99,
                "warning_low": 0.4,
                "warning_high": 0.95
            },
            {
                "name": "text_quality",
                "description": "Text should be well-formed",
                "min_words": 2,
                "max_repeated_words": 10,
                "min_unique_words_ratio": 0.3
            },
            {
                "name": "intent_matching",
                "description": "Text should match declared intent",
                "keywords": {
                    IntentType.QUESTION_ANSWERING.value: ["what", "how", "why", "when", "where", "who", "explain", "?"],
                    IntentType.CODE_GENERATION.value: ["code", "function", "implement", "program", "script", "algorithm"],
                    IntentType.CREATIVE_WRITING.value: ["write", "story", "poem", "create", "compose", "draft"],
                    IntentType.DATA_ANALYSIS.value: ["analyze", "data", "statistics", "metrics", "insights", "trends"],
                    IntentType.REASONING.value: ["reason", "logic", "conclude", "deduce", "infer", "prove"],
                    IntentType.SUMMARIZATION.value: ["summarize", "summary", "key points", "brief", "condensed"],
                    IntentType.TRANSLATION.value: ["translate", "translation", "language", "convert", "interpret"],
                    IntentType.CONVERSATION.value: ["chat", "talk", "discuss", "conversation", "dialogue"],
                    IntentType.TASK_PLANNING.value: ["plan", "schedule", "organize", "steps", "roadmap"],
                    IntentType.PROBLEM_SOLVING.value: ["solve", "problem", "fix", "issue", "solution", "troubleshoot"]
                }
            }
        ]
    
    def validate_json_structure(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate JSON structure against schema."""
        try:
            validate(instance=data, schema=self.schema)
            return True, []
        except JsonSchemaError as e:
            return False, [f"Schema validation error: {e.message}"]
    
    def validate_example(self, example: Dict[str, Any], index: int) -> Tuple[bool, List[str]]:
        """Validate a single example."""
        errors = []
        warnings = []
        
        # Get example fields
        text = example.get("text", "")
        intent = example.get("intent", "")
        audience = example.get("audience", "")
        complexity = example.get("complexity", "")
        confidence = example.get("confidence", 0.0)
        
        # Rule 1: Text length
        text_length = len(text)
        word_count = len(text.split())
        
        length_rule = next(r for r in self.quality_rules if r["name"] == "text_length")
        if text_length < length_rule["min_length"]:
            errors.append(f"Example {index}: Text too short ({text_length} chars)")
        elif text_length > length_rule["max_length"]:
            errors.append(f"Example {index}: Text too long ({text_length} chars)")
        elif text_length > length_rule["warning_threshold"]:
            warnings.append(f"Example {index}: Text is quite long ({text_length} chars)")
        
        # Rule 2: Confidence range
        conf_rule = next(r for r in self.quality_rules if r["name"] == "confidence_range")
        if confidence < conf_rule["min_confidence"]:
            errors.append(f"Example {index}: Confidence too low ({confidence:.2f})")
        elif confidence > conf_rule["max_confidence"]:
            errors.append(f"Example {index}: Confidence unrealistically high ({confidence:.2f})")
        elif confidence < conf_rule["warning_low"]:
            warnings.append(f"Example {index}: Low confidence ({confidence:.2f})")
        
        # Rule 3: Text quality
        quality_rule = next(r for r in self.quality_rules if r["name"] == "text_quality")
        if word_count < quality_rule["min_words"]:
            errors.append(f"Example {index}: Too few words ({word_count})")
        
        # Check for repeated words
        words = text.lower().split()
        word_counts = defaultdict(int)
        for word in words:
            word_counts[word] += 1
        
        max_repetitions = max(word_counts.values()) if word_counts else 0
        if max_repetitions > quality_rule["max_repeated_words"]:
            errors.append(f"Example {index}: Excessive word repetition (max {max_repetitions})")
        
        # Check unique words ratio
        if words:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < quality_rule["min_unique_words_ratio"]:
                warnings.append(f"Example {index}: Low word diversity (ratio: {unique_ratio:.2f})")
        
        # Rule 4: Intent matching
        intent_rule = next(r for r in self.quality_rules if r["name"] == "intent_matching")
        intent_keywords = intent_rule["keywords"].get(intent, [])
        
        # Check if any intent keywords are present
        text_lower = text.lower()
        has_keyword = any(keyword in text_lower for keyword in intent_keywords)
        
        # For question_answering, also check for question mark
        if intent == IntentType.QUESTION_ANSWERING.value and "?" not in text:
            warnings.append(f"Example {index}: Question intent without question mark")
        
        # Weak intent matching warning (not an error)
        if not has_keyword and intent_keywords:
            warnings.append(f"Example {index}: No clear keywords for intent '{intent}'")
        
        # Check for obviously wrong intent
        wrong_intent_indicators = {
            IntentType.CODE_GENERATION.value: ["write a story", "write a poem"],
            IntentType.CREATIVE_WRITING.value: ["write code", "implement function"],
            IntentType.TRANSLATION.value: ["analyze data", "solve problem"]
        }
        
        for wrong_intent, indicators in wrong_intent_indicators.items():
            if intent != wrong_intent and any(ind in text_lower for ind in indicators):
                errors.append(f"Example {index}: Text suggests '{wrong_intent}' but labeled as '{intent}'")
        
        # Update statistics
        self.statistics["total_processed"] += 1
        self.statistics[f"intent_{intent}"] = self.statistics.get(f"intent_{intent}", 0) + 1
        self.statistics[f"audience_{audience}"] = self.statistics.get(f"audience_{audience}", 0) + 1
        self.statistics[f"complexity_{complexity}"] = self.statistics.get(f"complexity_{complexity}", 0) + 1
        
        is_valid = len(errors) == 0
        return is_valid, errors + warnings
    
    def validate_dataset(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate entire dataset."""
        result = ValidationResult(
            is_valid=True,
            total_examples=0,
            valid_examples=0,
            invalid_examples=0
        )
        
        # Reset statistics
        self.statistics = defaultdict(int)
        
        # Validate JSON structure
        structure_valid, structure_errors = self.validate_json_structure(data)
        if not structure_valid:
            result.is_valid = False
            result.errors.extend([{"type": "structure", "message": err} for err in structure_errors])
            return result
        
        # Validate examples
        examples = data.get("examples", [])
        result.total_examples = len(examples)
        
        for i, example in enumerate(examples):
            is_valid, messages = self.validate_example(example, i)
            
            if is_valid:
                result.valid_examples += 1
            else:
                result.invalid_examples += 1
                result.is_valid = False
            
            # Separate errors and warnings
            for msg in messages:
                if "Warning" in msg or "Low" in msg or "quite long" in msg:
                    result.warnings.append(msg)
                else:
                    result.errors.append({"type": "example", "index": i, "message": msg})
        
        # Add statistics
        result.statistics = dict(self.statistics)
        
        # Generate recommendations
        result.recommendations = self._generate_recommendations(data, result)
        
        return result
    
    def _generate_recommendations(self, data: Dict[str, Any], result: ValidationResult) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Check error rate
        if result.total_examples > 0:
            error_rate = result.invalid_examples / result.total_examples
            if error_rate > 0.1:
                recommendations.append(f"High error rate ({error_rate:.1%}). Review generation process.")
            
            # Check warning rate
            warning_rate = len(result.warnings) / result.total_examples
            if warning_rate > 0.2:
                recommendations.append(f"Many warnings ({warning_rate:.1%}). Consider adjusting generation parameters.")
        
        # Check distribution balance
        metadata = data.get("metadata", {})
        diversity = metadata.get("diversity_metrics", {})
        
        if diversity:
            # Check audience coverage
            audience_dist = diversity.get("audience_distribution", {})
            if len(audience_dist) < len(AudienceLevel):
                missing = set(a.value for a in AudienceLevel) - set(audience_dist.keys())
                recommendations.append(f"Missing audience levels: {', '.join(missing)}")
            
            # Check uniqueness
            uniqueness = diversity.get("uniqueness_score", 0)
            if uniqueness < 0.7:
                recommendations.append(f"Low uniqueness score ({uniqueness:.2f}). Increase diversity.")
        
        # Check for specific issues
        if any("Too few words" in str(err) for err in result.errors):
            recommendations.append("Many examples are too short. Adjust minimum length requirements.")
        
        if any("No clear keywords" in warn for warn in result.warnings):
            recommendations.append("Many examples lack clear intent indicators. Improve prompt templates.")
        
        if not recommendations:
            recommendations.append("Dataset validation passed with good quality!")
        
        return recommendations
    
    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a JSON file containing training data."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return self.validate_dataset(data)
        
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                total_examples=0,
                valid_examples=0,
                invalid_examples=0,
                errors=[{"type": "json_decode", "message": str(e)}]
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                total_examples=0,
                valid_examples=0,
                invalid_examples=0,
                errors=[{"type": "file_error", "message": str(e)}]
            )
    
    def generate_validation_report(self, result: ValidationResult, output_path: Optional[Path] = None) -> str:
        """Generate a human-readable validation report."""
        report_lines = [
            "=" * 60,
            "Training Data Validation Report",
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Summary:",
            f"  Total Examples: {result.total_examples}",
            f"  Valid Examples: {result.valid_examples}",
            f"  Invalid Examples: {result.invalid_examples}",
            f"  Validation Status: {'PASSED' if result.is_valid else 'FAILED'}",
            ""
        ]
        
        if result.errors:
            report_lines.extend([
                "Errors:",
                "-" * 40
            ])
            for i, error in enumerate(result.errors[:20], 1):  # Show first 20 errors
                report_lines.append(f"  {i}. {error.get('message', str(error))}")
            if len(result.errors) > 20:
                report_lines.append(f"  ... and {len(result.errors) - 20} more errors")
            report_lines.append("")
        
        if result.warnings:
            report_lines.extend([
                "Warnings:",
                "-" * 40
            ])
            for i, warning in enumerate(result.warnings[:10], 1):  # Show first 10 warnings
                report_lines.append(f"  {i}. {warning}")
            if len(result.warnings) > 10:
                report_lines.append(f"  ... and {len(result.warnings) - 10} more warnings")
            report_lines.append("")
        
        if result.statistics:
            report_lines.extend([
                "Statistics:",
                "-" * 40
            ])
            for key, value in sorted(result.statistics.items()):
                report_lines.append(f"  {key}: {value}")
            report_lines.append("")
        
        if result.recommendations:
            report_lines.extend([
                "Recommendations:",
                "-" * 40
            ])
            for i, rec in enumerate(result.recommendations, 1):
                report_lines.append(f"  {i}. {rec}")
        
        report = "\n".join(report_lines)
        
        # Save to file if path provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Validation report saved to: {output_path}")
        
        return report


# Convenience functions
def validate_training_data(file_path: Path) -> ValidationResult:
    """Validate training data file."""
    validator = DataValidator()
    return validator.validate_file(file_path)


def validate_and_report(file_path: Path, report_path: Optional[Path] = None) -> Tuple[ValidationResult, str]:
    """Validate data and generate report."""
    validator = DataValidator()
    result = validator.validate_file(file_path)
    
    if report_path is None:
        report_path = file_path.with_suffix('.validation_report.txt')
    
    report = validator.generate_validation_report(result, report_path)
    return result, report


# Example usage
if __name__ == "__main__":
    # Example validation
    test_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_examples": 2,
            "config": {},
            "statistics": {}
        },
        "examples": [
            {
                "text": "How does machine learning work?",
                "intent": "question_answering",
                "audience": "beginner",
                "complexity": "simple",
                "confidence": 0.92,
                "metadata": {},
                "generated_at": datetime.now().isoformat(),
                "generation_method": "template"
            },
            {
                "text": "Write a Python function to sort a list",
                "intent": "code_generation",
                "audience": "intermediate",
                "complexity": "moderate",
                "confidence": 0.88,
                "metadata": {},
                "generated_at": datetime.now().isoformat(),
                "generation_method": "template"
            }
        ]
    }
    
    validator = DataValidator()
    result = validator.validate_dataset(test_data)
    report = validator.generate_validation_report(result)
    
    print(report)