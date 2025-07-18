from typing import Dict, Any, Optional, List
from .base import BaseTechnique


class FewShotTechnique(BaseTechnique):
    """
    Few-shot learning technique
    
    This technique provides examples of input-output pairs to help
    the model understand the desired format and behavior.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.default_template = """Here are some examples of the task:

{% for example in examples %}
Example {{ loop.index }}:
Input: {{ example.input }}
Output: {{ example.output }}
{% if example.explanation %}
Explanation: {{ example.explanation }}
{% endif %}

{% endfor %}
Now, for the following input:
Input: {{ text }}
Output:"""
        
        if not self.template:
            self.template = self.default_template
            
        self.min_examples = self.parameters.get("min_examples", 2)
        self.max_examples = self.parameters.get("max_examples", 5)
        
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Apply few-shot learning technique"""
        text = self.clean_text(text)
        
        # Get examples from context or use defaults
        examples = []
        if context and "examples" in context:
            examples = context["examples"]
        elif context and "task_type" in context:
            examples = self._get_default_examples(context["task_type"])
        
        if not examples:
            self.logger.warning("No examples provided for few-shot learning")
            # Fallback to zero-shot with instruction
            return f"{text}\n\nPlease provide a clear and detailed response."
        
        # Limit examples to max_examples
        examples = examples[:self.max_examples]
        
        return self.render_template(self.template, {
            "text": text,
            "examples": examples
        })
    
    def validate_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate if few-shot is appropriate"""
        # Check if we have examples
        if context and "examples" in context:
            examples = context["examples"]
            if len(examples) < self.min_examples:
                self.logger.warning(f"Too few examples: {len(examples)} < {self.min_examples}")
                return False
            return True
            
        # Check if we can generate default examples
        if context and "task_type" in context:
            return True
            
        self.logger.warning("No examples or task type provided for few-shot learning")
        return False
    
    def _get_default_examples(self, task_type: str) -> List[Dict[str, str]]:
        """Get default examples based on task type"""
        default_examples = {
            "classification": [
                {
                    "input": "The movie was absolutely fantastic! Best I've seen all year.",
                    "output": "Positive",
                    "explanation": "Strong positive language indicates positive sentiment"
                },
                {
                    "input": "The service was terrible and the food was cold.",
                    "output": "Negative",
                    "explanation": "Negative descriptors indicate negative sentiment"
                }
            ],
            "summarization": [
                {
                    "input": "The quick brown fox jumps over the lazy dog. This pangram contains all letters of the English alphabet. It is commonly used for testing fonts and keyboards.",
                    "output": "A pangram containing all English letters, used for testing fonts and keyboards.",
                    "explanation": "Captures the key information concisely"
                }
            ],
            "translation": [
                {
                    "input": "Hello, how are you today?",
                    "output": "Bonjour, comment allez-vous aujourd'hui?",
                    "explanation": "English to French translation"
                }
            ],
            "code_generation": [
                {
                    "input": "Write a function to calculate factorial",
                    "output": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)",
                    "explanation": "Recursive implementation of factorial"
                }
            ],
            "question_answering": [
                {
                    "input": "What is the capital of France?",
                    "output": "The capital of France is Paris.",
                    "explanation": "Direct answer to factual question"
                }
            ]
        }
        
        return default_examples.get(task_type, [])