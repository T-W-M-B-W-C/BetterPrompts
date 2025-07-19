from typing import Dict, Any, Optional, List, Union
from .base import BaseTechnique
import random


class FewShotTechnique(BaseTechnique):
    """
    Few-shot learning technique with advanced features
    
    This technique provides carefully selected examples of input-output pairs 
    to help the model understand the desired format, behavior, and task context.
    
    Features:
    - Smart example selection based on similarity
    - Multiple formatting styles (input/output, XML-like, delimiter-based)
    - Dynamic example ordering for better learning
    - Chain-of-thought integration option
    - Task-specific example repositories
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Configuration parameters
        self.min_examples = self.parameters.get("min_examples", 2)
        self.max_examples = self.parameters.get("max_examples", 5)
        self.optimal_examples = self.parameters.get("optimal_examples", 3)
        self.format_style = self.parameters.get("format_style", "input_output")  # input_output, xml, delimiter
        self.delimiter = self.parameters.get("delimiter", "###")
        self.include_explanations = self.parameters.get("include_explanations", True)
        self.randomize_order = self.parameters.get("randomize_order", False)
        self.use_chain_of_thought = self.parameters.get("use_chain_of_thought", False)
        
        # Template selection based on format style
        self.templates = {
            "input_output": self._get_input_output_template(),
            "xml": self._get_xml_template(),
            "delimiter": self._get_delimiter_template()
        }
        
        if not self.template:
            self.template = self.templates.get(self.format_style, self.templates["input_output"])
    
    def _get_input_output_template(self) -> str:
        """Get INPUT/OUTPUT format template"""
        return """Below are {{ examples|length }} examples demonstrating the task:

{% for example in examples %}
Example {{ loop.index }}:
INPUT: {{ example.input }}
OUTPUT: {{ example.output }}
{% if example.explanation and include_explanations %}
REASONING: {{ example.explanation }}
{% endif %}
{% if not loop.last %}

{% endif %}
{% endfor %}

Now, for your task:
INPUT: {{ text }}
OUTPUT:"""
    
    def _get_xml_template(self) -> str:
        """Get XML-like format template"""
        return """Here are {{ examples|length }} examples of the task:

{% for example in examples %}
<example number="{{ loop.index }}">
  <input>{{ example.input }}</input>
  <output>{{ example.output }}</output>
  {% if example.explanation and include_explanations %}
  <reasoning>{{ example.explanation }}</reasoning>
  {% endif %}
</example>
{% if not loop.last %}

{% endif %}
{% endfor %}

Now process this input:
<input>{{ text }}</input>
<output>"""
    
    def _get_delimiter_template(self) -> str:
        """Get delimiter-based format template"""
        return """I'll show you {{ examples|length }} examples of how to complete this task:

{% for example in examples %}
{{ delimiter }} Example {{ loop.index }} {{ delimiter }}
Query: {{ example.input }}
Response: {{ example.output }}
{% if example.explanation and include_explanations %}
Rationale: {{ example.explanation }}
{% endif %}
{% if not loop.last %}

{% endif %}
{% endfor %}

{{ delimiter }} Your Task {{ delimiter }}
Query: {{ text }}
Response:"""
        
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Apply few-shot learning technique with advanced example selection"""
        text = self.clean_text(text)
        
        # Get examples using intelligent selection
        examples = self._select_examples(text, context)
        
        if not examples:
            self.logger.warning("No examples available for few-shot learning")
            # Fallback to instruction-based prompt
            return self._create_fallback_prompt(text, context)
        
        # Enhance examples with chain-of-thought if enabled
        if self.use_chain_of_thought:
            examples = self._add_chain_of_thought(examples)
        
        # Optionally randomize example order
        if self.randomize_order and len(examples) > 2:
            examples = self._smart_randomize(examples)
        
        # Render the prompt with selected examples
        return self.render_template(self.template, {
            "text": text,
            "examples": examples,
            "include_explanations": self.include_explanations,
            "delimiter": self.delimiter
        })
    
    def _select_examples(self, text: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Intelligently select the most relevant examples"""
        examples = []
        
        # First, try to get custom examples from context
        if context and "examples" in context:
            examples = context["examples"]
            self.logger.info(f"Using {len(examples)} custom examples from context")
        
        # If no custom examples, try task-specific defaults
        elif context and "task_type" in context:
            examples = self._get_default_examples(context["task_type"])
            self.logger.info(f"Using default examples for task type: {context['task_type']}")
        
        # Apply similarity-based selection if we have more examples than needed
        if len(examples) > self.max_examples:
            examples = self._select_by_similarity(examples, text)
        
        # Ensure we have the optimal number of examples
        if len(examples) > self.optimal_examples:
            examples = examples[:self.optimal_examples]
        
        return examples
    
    def _select_by_similarity(self, examples: List[Dict[str, str]], text: str) -> List[Dict[str, str]]:
        """Select examples based on similarity to the input text"""
        # Simple keyword-based similarity scoring
        text_lower = text.lower()
        scored_examples = []
        
        for example in examples:
            score = 0
            example_text = (example.get("input", "") + " " + example.get("output", "")).lower()
            
            # Count common words (simple similarity metric)
            text_words = set(text_lower.split())
            example_words = set(example_text.split())
            common_words = text_words.intersection(example_words)
            score = len(common_words) / max(len(text_words), 1)
            
            scored_examples.append((score, example))
        
        # Sort by score and return top examples
        scored_examples.sort(key=lambda x: x[0], reverse=True)
        return [example for _, example in scored_examples[:self.max_examples]]
    
    def _add_chain_of_thought(self, examples: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Add chain-of-thought reasoning to examples if not present"""
        enhanced_examples = []
        
        for example in examples:
            enhanced_example = example.copy()
            
            # If no explanation exists, try to generate a simple one
            if not enhanced_example.get("explanation"):
                # This is a placeholder - in production, you might use an LLM to generate explanations
                enhanced_example["explanation"] = "Step-by-step reasoning process applied to reach the output."
            
            enhanced_examples.append(enhanced_example)
        
        return enhanced_examples
    
    def _smart_randomize(self, examples: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Randomize examples while keeping the best one first"""
        if not examples:
            return examples
        
        # Keep the first example (assumed to be the best) and shuffle the rest
        first_example = examples[0]
        rest = examples[1:]
        random.shuffle(rest)
        
        return [first_example] + rest
    
    def _create_fallback_prompt(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Create a fallback prompt when no examples are available"""
        task_instruction = ""
        
        if context and "task_type" in context:
            task_instructions = {
                "classification": "Please classify the following input into the appropriate category.",
                "summarization": "Please provide a concise summary of the following text.",
                "translation": "Please translate the following text.",
                "code_generation": "Please generate code based on the following description.",
                "question_answering": "Please answer the following question.",
                "analysis": "Please analyze the following input and provide insights.",
                "generation": "Please generate a response based on the following input."
            }
            task_instruction = task_instructions.get(
                context["task_type"], 
                "Please process the following input appropriately."
            )
        
        return f"""{task_instruction}

Input: {text}

Please provide a clear, well-structured response."""
    
    def validate_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate if few-shot is appropriate"""
        # Check basic text validity
        if not text or len(text.strip()) < 3:
            self.logger.warning("Input text too short for few-shot learning")
            return False
        
        # Check if we have examples
        if context and "examples" in context:
            examples = context["examples"]
            if len(examples) < self.min_examples:
                self.logger.warning(f"Too few examples: {len(examples)} < {self.min_examples}")
                return False
            
            # Validate example structure
            for i, example in enumerate(examples):
                if not isinstance(example, dict):
                    self.logger.error(f"Example {i} is not a dictionary")
                    return False
                if "input" not in example or "output" not in example:
                    self.logger.error(f"Example {i} missing required 'input' or 'output' fields")
                    return False
            
            return True
            
        # Check if we can generate default examples
        if context and "task_type" in context:
            return True
            
        self.logger.warning("No examples or task type provided for few-shot learning")
        return False
    
    def _get_default_examples(self, task_type: str) -> List[Dict[str, str]]:
        """Get comprehensive default examples based on task type"""
        default_examples = {
            "classification": [
                {
                    "input": "The movie was absolutely fantastic! Best I've seen all year.",
                    "output": "Positive",
                    "explanation": "Strong positive adjectives ('fantastic', 'best') and emphatic language indicate positive sentiment"
                },
                {
                    "input": "The service was terrible and the food was cold.",
                    "output": "Negative",
                    "explanation": "Negative descriptors ('terrible', 'cold') clearly express dissatisfaction"
                },
                {
                    "input": "The product works as expected, nothing special but gets the job done.",
                    "output": "Neutral",
                    "explanation": "Balanced language without strong positive or negative indicators"
                },
                {
                    "input": "While the plot was weak, the cinematography was breathtaking.",
                    "output": "Mixed",
                    "explanation": "Contains both negative ('weak') and positive ('breathtaking') elements"
                }
            ],
            "summarization": [
                {
                    "input": "The quick brown fox jumps over the lazy dog. This pangram contains all letters of the English alphabet. It is commonly used for testing fonts and keyboards.",
                    "output": "A pangram containing all English letters, used for testing fonts and keyboards.",
                    "explanation": "Extracts the main concept and purpose while removing redundant details"
                },
                {
                    "input": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn for themselves.",
                    "output": "Machine learning enables systems to learn from data and improve autonomously without explicit programming.",
                    "explanation": "Captures the core definition and key characteristic in a concise manner"
                },
                {
                    "input": "The meeting discussed quarterly financial results, highlighting a 15% increase in revenue, 8% reduction in costs, and plans for expanding into three new markets in Asia.",
                    "output": "Quarterly meeting reported 15% revenue growth, 8% cost reduction, and Asian market expansion plans.",
                    "explanation": "Preserves key metrics and strategic initiatives while condensing the narrative"
                }
            ],
            "translation": [
                {
                    "input": "Hello, how are you today?",
                    "output": "Bonjour, comment allez-vous aujourd'hui?",
                    "explanation": "English to French - formal greeting translation"
                },
                {
                    "input": "The weather is beautiful today.",
                    "output": "Il fait beau aujourd'hui.",
                    "explanation": "English to French - idiomatic weather expression"
                },
                {
                    "input": "Thank you for your help.",
                    "output": "Merci pour votre aide.",
                    "explanation": "English to French - polite expression of gratitude"
                }
            ],
            "code_generation": [
                {
                    "input": "Write a function to calculate factorial",
                    "output": "def factorial(n):\n    if n < 0:\n        raise ValueError('Factorial not defined for negative numbers')\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)",
                    "explanation": "Recursive implementation with input validation for edge cases"
                },
                {
                    "input": "Create a function to check if a string is a palindrome",
                    "output": "def is_palindrome(s):\n    # Remove spaces and convert to lowercase\n    cleaned = ''.join(s.split()).lower()\n    return cleaned == cleaned[::-1]",
                    "explanation": "Handles spaces and case-insensitive comparison"
                },
                {
                    "input": "Write a function to find the maximum value in a list",
                    "output": "def find_max(lst):\n    if not lst:\n        raise ValueError('Cannot find max of empty list')\n    max_val = lst[0]\n    for val in lst[1:]:\n        if val > max_val:\n            max_val = val\n    return max_val",
                    "explanation": "Iterative approach with empty list handling"
                }
            ],
            "question_answering": [
                {
                    "input": "What is the capital of France?",
                    "output": "The capital of France is Paris.",
                    "explanation": "Direct factual answer with complete sentence structure"
                },
                {
                    "input": "How does photosynthesis work?",
                    "output": "Photosynthesis is the process where plants convert sunlight, water, and carbon dioxide into glucose and oxygen. Chlorophyll in leaves captures light energy, which drives chemical reactions in chloroplasts.",
                    "explanation": "Explains the process with key components and mechanism"
                },
                {
                    "input": "What are the main causes of climate change?",
                    "output": "The main causes of climate change include greenhouse gas emissions from burning fossil fuels, deforestation, industrial processes, and agriculture. These activities increase CO2 and other heat-trapping gases in the atmosphere.",
                    "explanation": "Lists multiple causes with brief explanations"
                }
            ],
            "analysis": [
                {
                    "input": "Analyze the trend: Sales Q1: $100K, Q2: $120K, Q3: $115K, Q4: $140K",
                    "output": "Overall upward trend with 40% annual growth. Q3 showed a slight dip (-4.2%) but recovered strongly in Q4 (+21.7%). The trend suggests positive momentum with minor volatility.",
                    "explanation": "Identifies pattern, calculates key metrics, and provides interpretation"
                },
                {
                    "input": "Compare Python and JavaScript for web development",
                    "output": "Python excels in backend development with frameworks like Django/Flask, offering clean syntax and robust libraries. JavaScript dominates frontend and enables full-stack development with Node.js. Python is better for data-heavy applications, while JavaScript provides better real-time performance.",
                    "explanation": "Balanced comparison highlighting strengths and use cases"
                }
            ],
            "generation": [
                {
                    "input": "Write a professional email declining a meeting invitation",
                    "output": "Subject: Unable to Attend - [Meeting Name]\n\nDear [Name],\n\nThank you for inviting me to [meeting]. Unfortunately, I have a prior commitment and won't be able to attend. \n\nWould it be possible to receive the meeting notes afterward? I'm also happy to schedule a brief catch-up if needed.\n\nBest regards,\n[Your name]",
                    "explanation": "Polite, professional tone with alternative solutions"
                },
                {
                    "input": "Create a product description for wireless headphones",
                    "output": "Experience premium audio freedom with our wireless headphones. Featuring active noise cancellation, 30-hour battery life, and crystal-clear sound quality. Comfortable memory foam ear cushions and foldable design make them perfect for travel. Bluetooth 5.0 ensures stable connectivity up to 30 feet.",
                    "explanation": "Highlights key features and benefits in engaging language"
                }
            ],
            "reasoning": [
                {
                    "input": "If all roses are flowers, and some flowers fade quickly, do all roses fade quickly?",
                    "output": "No, all roses do not necessarily fade quickly. While all roses are flowers, only some flowers fade quickly. Roses are a subset of flowers, but they may not be part of the subset that fades quickly.",
                    "explanation": "Logical analysis distinguishing between universal and particular statements"
                },
                {
                    "input": "Should a company prioritize growth or profitability?",
                    "output": "The priority depends on the company's stage and market conditions. Early-stage companies often prioritize growth to capture market share, while mature companies focus on profitability. Ideally, sustainable growth with a path to profitability balances long-term success with financial stability.",
                    "explanation": "Considers multiple factors and provides nuanced perspective"
                }
            ]
        }
        
        return default_examples.get(task_type, self._get_generic_examples())
    
    def _get_generic_examples(self) -> List[Dict[str, str]]:
        """Get generic examples when task type is unknown"""
        return [
            {
                "input": "Explain the concept of machine learning",
                "output": "Machine learning is a type of artificial intelligence that enables computers to learn from data without being explicitly programmed. It uses algorithms to identify patterns, make decisions, and improve performance through experience.",
                "explanation": "Clear, concise explanation of a technical concept"
            },
            {
                "input": "What are the benefits of regular exercise?",
                "output": "Regular exercise provides numerous benefits including improved cardiovascular health, stronger muscles and bones, better mental health, weight management, increased energy levels, and reduced risk of chronic diseases.",
                "explanation": "Comprehensive list of benefits in a structured format"
            },
            {
                "input": "How to make a cup of coffee?",
                "output": "1. Boil water to 195-205°F\n2. Measure 2 tablespoons of ground coffee per 6 oz of water\n3. Place coffee in filter\n4. Pour hot water over grounds slowly\n5. Let it brew for 4-5 minutes\n6. Serve and enjoy",
                "explanation": "Step-by-step instructions with specific measurements"
            }
        ]
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get enhanced metadata including configuration details"""
        metadata = super().get_metadata()
        metadata.update({
            "min_examples": self.min_examples,
            "max_examples": self.max_examples,
            "optimal_examples": self.optimal_examples,
            "format_style": self.format_style,
            "include_explanations": self.include_explanations,
            "use_chain_of_thought": self.use_chain_of_thought,
            "supported_task_types": list(self._get_default_examples("").keys()) if hasattr(self, '_get_default_examples') else []
        })
        return metadata