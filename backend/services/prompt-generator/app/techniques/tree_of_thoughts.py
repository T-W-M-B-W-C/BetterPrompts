from typing import Dict, Any, Optional, List
from .base import BaseTechnique


class TreeOfThoughtsTechnique(BaseTechnique):
    """
    Tree of Thoughts (ToT) prompting technique
    
    This technique explores multiple reasoning paths and evaluates
    different approaches before selecting the best solution.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.default_template = """{{ text }}

Let's explore multiple approaches to this problem:

Approach 1: {{ approach_1 }}
- Pros: [List advantages]
- Cons: [List disadvantages]
- Viability: [Rate 1-10]

Approach 2: {{ approach_2 }}
- Pros: [List advantages]
- Cons: [List disadvantages]
- Viability: [Rate 1-10]

Approach 3: {{ approach_3 }}
- Pros: [List advantages]
- Cons: [List disadvantages]
- Viability: [Rate 1-10]

After evaluating all approaches, select the most promising one and develop it fully:

Selected Approach: [Choose best approach]
Detailed Solution:"""
        
        if not self.template:
            self.template = self.default_template
            
        self.num_branches = self.parameters.get("num_branches", 3)
        self.evaluation_criteria = self.parameters.get("evaluation_criteria", [
            "feasibility", "efficiency", "completeness", "clarity"
        ])
        
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Apply Tree of Thoughts technique"""
        text = self.clean_text(text)
        
        # Generate approach suggestions based on context
        approaches = self._generate_approaches(text, context)
        
        # Build the template variables
        template_vars = {
            "text": text,
            "approach_1": approaches[0] if len(approaches) > 0 else "Traditional method",
            "approach_2": approaches[1] if len(approaches) > 1 else "Alternative method",
            "approach_3": approaches[2] if len(approaches) > 2 else "Creative method"
        }
        
        # If custom evaluation criteria provided
        if context and "evaluation_criteria" in context:
            self.evaluation_criteria = context["evaluation_criteria"]
            
        # Use advanced template if we have specific criteria
        if len(self.evaluation_criteria) > 0:
            return self._apply_advanced_template(text, approaches, context)
            
        return self.render_template(self.template, template_vars)
    
    def validate_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate if Tree of Thoughts is appropriate"""
        # ToT is best for complex problems with multiple solution paths
        
        # Check text length - too short inputs don't benefit from ToT
        if len(text.split()) < 15:
            self.logger.warning("Input too short for Tree of Thoughts")
            return False
            
        # Check for problem-solving indicators
        problem_keywords = [
            "solve", "solution", "approach", "method", "strategy",
            "plan", "design", "implement", "create", "develop",
            "optimize", "improve", "fix", "resolve", "determine"
        ]
        
        text_lower = text.lower()
        has_problem = any(keyword in text_lower for keyword in problem_keywords)
        
        if not has_problem:
            self.logger.info("No clear problem-solving task detected")
            
        return True
    
    def _generate_approaches(self, text: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Generate different approaches based on the problem type"""
        approaches = []
        
        if context and "problem_type" in context:
            problem_type = context["problem_type"]
            approaches = self._get_approaches_by_type(problem_type)
        else:
            # Default approaches
            approaches = [
                "Direct approach - tackle the problem head-on",
                "Analytical approach - break down into components",
                "Creative approach - think outside conventional methods"
            ]
            
        # Add custom approaches if provided
        if context and "suggested_approaches" in context:
            approaches.extend(context["suggested_approaches"])
            
        return approaches[:self.num_branches]
    
    def _get_approaches_by_type(self, problem_type: str) -> List[str]:
        """Get approach suggestions based on problem type"""
        approach_map = {
            "optimization": [
                "Greedy approach - make locally optimal choices",
                "Dynamic programming - solve overlapping subproblems",
                "Heuristic approach - use practical shortcuts"
            ],
            "design": [
                "Top-down design - start with high-level structure",
                "Bottom-up design - build from components",
                "Iterative design - refine through cycles"
            ],
            "analysis": [
                "Quantitative analysis - focus on metrics and data",
                "Qualitative analysis - examine patterns and themes",
                "Comparative analysis - contrast different elements"
            ],
            "debugging": [
                "Systematic elimination - rule out possibilities",
                "Root cause analysis - trace to origin",
                "Divide and conquer - isolate problem areas"
            ]
        }
        
        return approach_map.get(problem_type, [
            "Systematic approach",
            "Innovative approach",
            "Hybrid approach"
        ])
    
    def _apply_advanced_template(self, text: str, approaches: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """Apply advanced ToT template with detailed evaluation"""
        advanced_template = """{{ text }}

Let's systematically explore {{ num_approaches }} different approaches:

{% for approach in approaches %}
### Approach {{ loop.index }}: {{ approach }}

Analysis:
{% for criterion in evaluation_criteria %}
- {{ criterion }}: [Evaluate on scale 1-10 with justification]
{% endfor %}

Implementation sketch:
[Outline how this approach would work]

{% endfor %}

### Comparative Analysis:
Compare all approaches across key dimensions:
{{ evaluation_criteria|join(', ') }}

### Recommendation:
Based on the analysis, the optimal approach is: [Select and justify]

### Detailed Implementation:
[Provide complete solution using the selected approach]"""
        
        return self.render_template(advanced_template, {
            "text": text,
            "num_approaches": len(approaches),
            "approaches": approaches,
            "evaluation_criteria": self.evaluation_criteria
        })