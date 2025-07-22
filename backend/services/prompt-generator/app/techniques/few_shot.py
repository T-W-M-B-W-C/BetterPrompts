from typing import Dict, Any, Optional, List, Union, Tuple
from .base import BaseTechnique
from ..utils import complexity_string_to_float, complexity_float_to_string
import random
import re
from collections import Counter
import math


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
        
        # Intent to task type mapping for backward compatibility
        self.intent_to_task_type = {
            # Direct mappings
            "classification": "classification",
            "summarization": "summarization",
            "translation": "translation",
            "code_generation": "code_generation",
            "question_answering": "question_answering",
            "analysis": "analysis",
            "generation": "generation",
            "reasoning": "reasoning",
            
            # Extended mappings for project intents
            "creative_writing": "generation",
            "data_analysis": "analysis",
            "conversation": "question_answering",
            "task_planning": "reasoning",
            "problem_solving": "reasoning",
            "explaining": "analysis",
            "brainstorming": "generation",
            "analyzing": "analysis",
            "creative": "generation"
        }
        
        # Complexity-based example adjustment
        self.complexity_multipliers = {
            "simple": 0.8,    # Fewer examples for simple tasks
            "moderate": 1.0,  # Default number
            "complex": 1.2    # More examples for complex tasks
        }
        
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
    
    def _select_examples(self, text: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Intelligently select the most relevant examples based on intent and content"""
        examples = []
        context = context or {}
        
        # First, try to get custom examples from context
        if "examples" in context:
            examples = context["examples"]
            self.logger.info(f"Using {len(examples)} custom examples from context")
        else:
            # Get intent-based examples
            intent = context.get("intent", "general")
            complexity = context.get("complexity", "moderate")
            
            # Map intent to task type for backward compatibility
            task_type = self.intent_to_task_type.get(intent, intent)
            
            # Try intent-specific examples first
            examples = self._get_intent_specific_examples(intent, complexity)
            
            # Fallback to task-type examples if no intent-specific ones
            if not examples:
                examples = self._get_default_examples(task_type)
                self.logger.info(f"Using default examples for task type: {task_type} (mapped from intent: {intent})")
            else:
                self.logger.info(f"Using intent-specific examples for intent: {intent}, complexity: {complexity}")
        
        # Apply advanced similarity-based selection if we have more examples than needed
        if len(examples) > self.max_examples:
            examples = self._select_by_advanced_similarity(examples, text, context)
        
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
        context = context or {}
        task_instruction = ""
        
        # Try intent first, then task_type
        intent = context.get("intent")
        task_type = context.get("task_type")
        
        # Map intent to instruction
        intent_instructions = {
            # Direct intent mappings
            "explaining": "Please provide a clear explanation of the following:",
            "problem_solving": "Please solve the following problem step by step:",
            "brainstorming": "Please generate creative ideas for the following:",
            "creative_writing": "Please create a creative response for:",
            "code_generation": "Please generate code based on the following description:",
            "question_answering": "Please answer the following question:",
            "data_analysis": "Please analyze the following data or information:",
            "reasoning": "Please provide logical reasoning for the following:",
            "summarization": "Please provide a concise summary of the following:",
            "translation": "Please translate the following text:",
            "conversation": "Please respond conversationally to:",
            "task_planning": "Please create a plan for the following task:",
            "analyzing": "Please analyze the following:",
            "creative": "Please provide a creative response to:"
        }
        
        # Try intent-based instruction first
        if intent and intent in intent_instructions:
            task_instruction = intent_instructions[intent]
        # Fallback to task type
        elif task_type:
            task_instructions = {
                "classification": "Please classify the following input into the appropriate category:",
                "summarization": "Please provide a concise summary of the following text:",
                "translation": "Please translate the following text:",
                "code_generation": "Please generate code based on the following description:",
                "question_answering": "Please answer the following question:",
                "analysis": "Please analyze the following input and provide insights:",
                "generation": "Please generate a response based on the following input:",
                "reasoning": "Please provide logical reasoning for the following:"
            }
            task_instruction = task_instructions.get(
                task_type, 
                "Please process the following input appropriately:"
            )
        else:
            # Generic instruction
            task_instruction = "Please provide a helpful response to the following:"
        
        # Add complexity-based guidance
        complexity = context.get("complexity", "moderate")
        complexity_guidance = {
            "simple": "\nKeep your response clear and concise.",
            "moderate": "\nProvide a balanced and well-structured response.",
            "complex": "\nProvide a comprehensive and detailed response with thorough analysis."
        }
        
        guidance = complexity_guidance.get(complexity, "")
        
        return f"""{task_instruction}

Input: {text}
{guidance}

Please ensure your response is clear, accurate, and directly addresses the request."""
    
    def _adjust_examples_by_complexity(self, examples: List[Dict[str, str]], complexity: str) -> List[Dict[str, str]]:
        """Adjust the number of examples based on complexity"""
        # Convert string complexity to float if needed
        if isinstance(complexity, str):
            multiplier = self.complexity_multipliers.get(complexity, 1.0)
        else:
            # If numeric, map to multiplier
            complexity_val = complexity if isinstance(complexity, float) else complexity_string_to_float(str(complexity))
            if complexity_val <= 0.33:
                multiplier = self.complexity_multipliers["simple"]
            elif complexity_val <= 0.66:
                multiplier = self.complexity_multipliers["moderate"]
            else:
                multiplier = self.complexity_multipliers["complex"]
        
        # Calculate adjusted number of examples
        target_count = int(self.optimal_examples * multiplier)
        target_count = max(self.min_examples, min(target_count, self.max_examples))
        
        # Adjust the list
        if len(examples) > target_count:
            return examples[:target_count]
        return examples
    
    def _get_intent_specific_examples(self, intent: str, complexity: str) -> List[Dict[str, str]]:
        """Get examples specifically tailored for the given intent and complexity"""
        # This method provides more granular examples based on specific intents
        intent_examples = {
            "explaining": [
                {
                    "input": "Explain quantum computing to a beginner",
                    "output": "Quantum computing is like having a super-powerful calculator that can try many solutions at once. While regular computers use bits (0 or 1), quantum computers use 'qubits' that can be both 0 and 1 simultaneously. This allows them to solve certain complex problems much faster.",
                    "explanation": "Uses analogies and avoids technical jargon for beginner-friendly explanation"
                },
                {
                    "input": "Explain the concept of recursion in programming",
                    "output": "Recursion is when a function calls itself to solve a problem. Think of it like Russian nesting dolls - each doll contains a smaller version of itself. In programming, we break down big problems into smaller, similar problems until we reach a simple case we can solve directly.",
                    "explanation": "Combines technical definition with relatable analogy"
                }
            ],
            "problem_solving": [
                {
                    "input": "Find the optimal route for visiting 5 cities with minimum distance",
                    "output": "This is the Traveling Salesman Problem. For 5 cities:\n1. Calculate distances between all city pairs\n2. Generate all possible routes (5! = 120 permutations)\n3. Calculate total distance for each route\n4. Select the route with minimum total distance\nFor larger problems, use heuristics like nearest neighbor or genetic algorithms.",
                    "explanation": "Systematic approach with scalability considerations"
                },
                {
                    "input": "Debug why my web app is running slowly",
                    "output": "To debug performance issues:\n1. Use browser DevTools to check network requests and load times\n2. Profile JavaScript execution to find bottlenecks\n3. Check for memory leaks in the console\n4. Analyze server response times\n5. Review database queries for optimization\n6. Test with performance monitoring tools",
                    "explanation": "Step-by-step debugging methodology"
                }
            ],
            "brainstorming": [
                {
                    "input": "Generate ideas for a sustainable product startup",
                    "output": "Here are innovative sustainable product ideas:\n1. Biodegradable phone cases from mushroom mycelium\n2. Solar-powered portable water purifiers\n3. Upcycled fashion from ocean plastic\n4. Edible food packaging from seaweed\n5. Smart composting systems with app integration\n6. Bamboo-based alternatives to plastic products",
                    "explanation": "Diverse, creative ideas focusing on sustainability"
                },
                {
                    "input": "Brainstorm features for a productivity app",
                    "output": "Productivity app features:\n1. AI-powered task prioritization\n2. Pomodoro timer with music integration\n3. Collaborative workspaces with real-time sync\n4. Voice-to-task conversion\n5. Habit tracking with gamification\n6. Calendar integration with smart scheduling\n7. Focus mode blocking distractions",
                    "explanation": "Mix of innovative and proven productivity features"
                }
            ],
            "creative_writing": [
                {
                    "input": "Write an opening line for a mystery novel",
                    "output": "The last thing Detective Sarah Chen expected to find in her morning coffee was a USB drive containing evidence of her own murder—scheduled for next Tuesday.",
                    "explanation": "Creates intrigue with an impossible scenario"
                },
                {
                    "input": "Create a tagline for an eco-friendly brand",
                    "output": "\"Tomorrow's Earth, Today's Choice\" - emphasizing both future impact and present responsibility in just four powerful words.",
                    "explanation": "Concise, memorable, and values-driven"
                }
            ]
        }
        
        # Get examples for the specific intent
        examples = intent_examples.get(intent, [])
        
        # If we have complexity-specific filtering, we could enhance this further
        # For now, return all examples for the intent
        return examples
    
    def _select_by_advanced_similarity(self, examples: List[Dict[str, str]], text: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Advanced similarity scoring using multiple factors"""
        scored_examples = []
        
        # Extract features from input text
        text_lower = text.lower()
        text_words = set(text_lower.split())
        text_length = len(text)
        
        # Get intent and complexity for scoring
        intent = context.get("intent", "general")
        complexity = context.get("complexity", "moderate")
        
        for example in examples:
            score = 0.0
            
            # 1. Lexical similarity (30%)
            example_input = example.get("input", "").lower()
            example_words = set(example_input.split())
            common_words = text_words.intersection(example_words)
            lexical_score = len(common_words) / max(len(text_words), 1)
            score += lexical_score * 0.3
            
            # 2. Length similarity (20%)
            length_diff = abs(len(example_input) - text_length)
            length_score = 1.0 / (1.0 + length_diff / 100)
            score += length_score * 0.2
            
            # 3. Semantic patterns (25%)
            patterns_score = self._calculate_semantic_similarity(text, example_input)
            score += patterns_score * 0.25
            
            # 4. Question type matching (15%)
            if self._match_question_type(text, example_input):
                score += 0.15
            
            # 5. Complexity matching (10%)
            example_complexity = example.get("complexity", "moderate")
            if example_complexity == complexity:
                score += 0.1
            
            scored_examples.append((score, example))
        
        # Sort by score and return top examples
        scored_examples.sort(key=lambda x: x[0], reverse=True)
        return [example for _, example in scored_examples[:self.max_examples]]
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        # Extract semantic features
        features = {
            "question_words": ["what", "why", "how", "when", "where", "who", "which"],
            "action_words": ["create", "build", "write", "implement", "design", "develop", "make"],
            "analysis_words": ["analyze", "compare", "evaluate", "assess", "examine", "investigate"],
            "explanation_words": ["explain", "describe", "define", "clarify", "elaborate"]
        }
        
        score = 0.0
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        for category, words in features.items():
            text1_has = any(word in text1_lower for word in words)
            text2_has = any(word in text2_lower for word in words)
            if text1_has and text2_has:
                score += 0.25
        
        return score
    
    def _match_question_type(self, text1: str, text2: str) -> bool:
        """Check if two texts have the same question type"""
        question_patterns = [
            (r'^(what|what\'s)\s+is\b', 'definition'),
            (r'^how\s+(do|does|to|can)\b', 'how-to'),
            (r'^why\s+(is|does|do)\b', 'reasoning'),
            (r'^(can|could|would|should)\s+\w+\b', 'possibility'),
            (r'^(list|name|give|provide)\s+\w+\b', 'enumeration')
        ]
        
        text1_type = None
        text2_type = None
        
        for pattern, q_type in question_patterns:
            if re.match(pattern, text1.lower()):
                text1_type = q_type
            if re.match(pattern, text2.lower()):
                text2_type = q_type
        
        return text1_type == text2_type and text1_type is not None
    
    def validate_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate if few-shot is appropriate for the input"""
        # Check basic text validity
        if not text or len(text.strip()) < 3:
            self.logger.warning("Input text too short for few-shot learning")
            return False
        
        context = context or {}
        
        # Check if we have custom examples
        if "examples" in context:
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
        
        # Check if we have intent or task_type for default examples
        intent = context.get("intent")
        task_type = context.get("task_type")
        
        if intent:
            # Map intent to task type
            mapped_task_type = self.intent_to_task_type.get(intent, intent)
            # Check if we have examples for this intent or mapped task type
            if intent in ["explaining", "problem_solving", "brainstorming", "creative_writing"] or mapped_task_type in self._get_supported_task_types():
                self.logger.info(f"Few-shot learning available for intent '{intent}'")
                return True
        
        if task_type and task_type in self._get_supported_task_types():
            self.logger.info(f"Few-shot learning available for task type '{task_type}'")
            return True
        
        # Few-shot can still be useful even without specific examples
        # Check if the prompt suggests it would benefit from examples
        few_shot_indicators = [
            "example", "show me", "demonstrate", "how to", "like this",
            "similar to", "format", "structure", "pattern", "template"
        ]
        
        text_lower = text.lower()
        if any(indicator in text_lower for indicator in few_shot_indicators):
            self.logger.info("Text contains few-shot indicators, enabling technique")
            return True
        
        # Log informational message instead of warning since we can still apply the technique
        self.logger.info(f"Few-shot learning will use generic examples for intent='{intent}', task_type='{task_type}'")
        return True  # Few-shot can work with generic examples
    
    def _get_supported_task_types(self) -> List[str]:
        """Get list of task types with available examples"""
        return [
            "classification", "summarization", "translation", 
            "code_generation", "question_answering", "analysis", 
            "generation", "reasoning"
        ]
    
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
            "supported_task_types": self._get_supported_task_types(),
            "supported_intents": list(self.intent_to_task_type.keys())
        })
        return metadata
    
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Apply few-shot learning technique with advanced example selection"""
        text = self.clean_text(text)
        context = context or {}
        
        # Extract intent and complexity for dynamic selection
        intent = context.get("intent", "general")
        complexity = context.get("complexity", "moderate")
        
        # Get examples using intelligent selection
        examples = self._select_examples(text, context)
        
        if not examples:
            self.logger.warning(f"No examples available for intent '{intent}' with complexity '{complexity}'")
            # Fallback to instruction-based prompt
            return self._create_fallback_prompt(text, context)
        
        # Adjust number of examples based on complexity
        examples = self._adjust_examples_by_complexity(examples, complexity)
        
        # Enhance examples with chain-of-thought if enabled
        if self.use_chain_of_thought:
            examples = self._add_chain_of_thought(examples)
        
        # Optionally randomize example order
        if self.randomize_order and len(examples) > 2:
            examples = self._smart_randomize(examples)
        
        self.logger.info(
            f"Applied few-shot with {len(examples)} examples for intent='{intent}', "
            f"complexity='{complexity}', format='{self.format_style}'"
        )
        
        # Render the prompt with selected examples
        return self.render_template(self.template, {
            "text": text,
            "examples": examples,
            "include_explanations": self.include_explanations,
            "delimiter": self.delimiter
        })