from typing import Dict, Any, Optional, List, Tuple
from .base import BaseTechnique
from ..utils import complexity_string_to_float, complexity_float_to_string
import re


class StepByStepTechnique(BaseTechnique):
    """
    Advanced Step-by-step instruction technique
    
    This technique breaks down complex tasks into clear, sequential steps
    with support for sub-steps, progress tracking, and intent-aware generation.
    
    Features:
    - Dynamic step generation based on intent and complexity
    - Sub-step support for complex tasks
    - Progress tracking and verification steps
    - Conditional steps based on context
    - Time estimates for each step
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Configuration options
        self.min_steps = self.parameters.get("min_steps", 3)
        self.max_steps = self.parameters.get("max_steps", 10)
        self.include_sub_steps = self.parameters.get("include_sub_steps", True)
        self.include_time_estimates = self.parameters.get("include_time_estimates", False)
        self.include_progress_tracking = self.parameters.get("include_progress_tracking", True)
        
        # Intent to task type mapping
        self.intent_to_task_type = {
            "explaining": "explanation",
            "problem_solving": "problem_solving",
            "brainstorming": "ideation",
            "creative_writing": "creation",
            "code_generation": "implementation",
            "question_answering": "analysis",
            "data_analysis": "analysis",
            "reasoning": "logical_reasoning",
            "summarization": "synthesis",
            "translation": "transformation",
            "conversation": "interaction",
            "task_planning": "planning",
            "analyzing": "analysis",
            "creative": "creation"
        }
        
        # Complexity multipliers for step count
        self.complexity_step_multipliers = {
            "simple": 0.7,    # Fewer steps
            "moderate": 1.0,  # Standard steps
            "complex": 1.3    # More detailed steps
        }
        
        # Templates for different formats
        self.templates = {
            "standard": self._get_standard_template(),
            "detailed": self._get_detailed_template(),
            "checklist": self._get_checklist_template()
        }
        
        self.format_style = self.parameters.get("format_style", "standard")
        
        if not self.template:
            self.template = self.templates.get(self.format_style, self.templates["standard"])
    
    def _get_standard_template(self) -> str:
        """Standard step-by-step template"""
        return """{{ text }}

Please complete this task by following these steps:

{% for step in steps %}
Step {{ loop.index }}: {{ step.description }}
{%- if step.sub_steps %}
{% for sub_step in step.sub_steps %}
   {{ loop.index }}. {{ sub_step }}
{%- endfor %}
{%- endif %}
{%- if step.time_estimate %}
   ⏱️ Estimated time: {{ step.time_estimate }}
{%- endif %}
{% if not loop.last %}

{% endif %}
{%- endfor %}

{{ additional_instructions }}

{% if progress_tracking %}
📊 Track your progress by checking off each step as you complete it.
{% endif %}

Begin with Step 1 and work through each step sequentially."""
    
    def _get_detailed_template(self) -> str:
        """Detailed template with explanations"""
        return """{{ text }}

🎯 Objective: Complete this task systematically using the following detailed steps:

{% for step in steps %}
### Step {{ loop.index }}: {{ step.description }}
{%- if step.explanation %}
💡 Why this step: {{ step.explanation }}
{%- endif %}
{%- if step.sub_steps %}

Sub-steps:
{% for sub_step in step.sub_steps %}
   • {{ sub_step }}
{%- endfor %}
{%- endif %}
{%- if step.time_estimate %}

⏱️ Time estimate: {{ step.time_estimate }}
{%- endif %}
{%- if step.tips %}

💡 Tips: {{ step.tips }}
{%- endif %}
{% if not loop.last %}

---

{% endif %}
{%- endfor %}

{{ additional_instructions }}

{% if verification_steps %}
### ✅ Verification Steps:
{% for vstep in verification_steps %}
{{ loop.index }}. {{ vstep }}
{%- endfor %}
{% endif %}

Remember to take your time and ensure quality at each step."""
    
    def _get_checklist_template(self) -> str:
        """Checklist-style template"""
        return """{{ text }}

Complete the following checklist in order:

{% for step in steps %}
☐ Step {{ loop.index }}: {{ step.description }}
{%- if step.sub_steps %}
{% for sub_step in step.sub_steps %}
  ☐ {{ sub_step }}
{%- endfor %}
{%- endif %}
{% endfor %}

{{ additional_instructions }}

✓ Check off each item as you complete it.
✓ Don't skip steps - they build on each other.
✓ If you get stuck, review previous steps."""
            
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Apply advanced step-by-step technique"""
        text = self.clean_text(text)
        context = context or {}
        
        # Extract intent and complexity
        intent = context.get("intent", "general")
        complexity = context.get("complexity", "moderate")
        
        # Generate or use provided steps
        steps = []
        additional_instructions = ""
        verification_steps = []
        
        if "steps" in context:
            # Use provided steps but enhance them
            steps = self._enhance_steps(context["steps"], complexity)
        else:
            # Generate steps based on intent and complexity
            steps = self._generate_advanced_steps(text, intent, complexity, context)
        
        # Add verification steps
        if "verification_steps" in context:
            verification_steps = context["verification_steps"]
        else:
            verification_steps = self._generate_verification_steps(intent, steps)
        
        # Additional instructions based on complexity
        additional_instructions = self._get_additional_instructions(complexity, intent)
        
        if not steps:
            # Fallback to generic instruction
            return f"{text}\n\nPlease approach this task systematically, breaking it down into clear steps."
        
        self.logger.info(
            f"Applied step-by-step with {len(steps)} steps for intent='{intent}', "
            f"complexity='{complexity}', format='{self.format_style}'"
        )
        
        # Check if format style is specified in context
        format_style = context.get("format_style", self.format_style)
        include_time_estimates = context.get("include_time_estimates", self.include_time_estimates)
        
        # Update configuration if specified in context
        if format_style != self.format_style or include_time_estimates != self.include_time_estimates:
            # Temporarily update for this request
            template = self.templates.get(format_style, self.templates["standard"])
            
            # Re-generate steps with time estimates if needed
            if include_time_estimates and not steps[0].get("time_estimate"):
                for step in steps:
                    step["time_estimate"] = self._estimate_step_time(step["description"], complexity)
        else:
            template = self.template
        
        # Prepare template variables
        template_vars = {
            "text": text,
            "steps": steps,
            "additional_instructions": additional_instructions.strip(),
            "progress_tracking": self.include_progress_tracking,
            "verification_steps": verification_steps
        }
        
        return self.render_template(template, template_vars)
    
    def validate_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate if step-by-step is appropriate"""
        # Check if task is complex enough to benefit from steps
        complexity_indicators = [
            "multiple", "several", "various", "steps", "process",
            "procedure", "workflow", "sequence", "stages", "phases",
            "implement", "create", "build", "design", "analyze"
        ]
        
        text_lower = text.lower()
        is_multi_step = any(indicator in text_lower for indicator in complexity_indicators)
        
        # Also check text length as an indicator
        word_count = len(text.split())
        if word_count < 10 and not is_multi_step:
            self.logger.info("Task appears too simple for step-by-step breakdown")
        
        # Check complexity if provided
        if context and "complexity" in context:
            complexity = context["complexity"]
            if isinstance(complexity, str) and complexity == "simple":
                # Even simple tasks can benefit from clear steps
                self.logger.info("Simple task will receive streamlined steps")
        
        return True
    
    def _enhance_steps(self, steps: List[Any], complexity: str) -> List[Dict[str, Any]]:
        """Enhance provided steps with additional metadata"""
        enhanced_steps = []
        
        for i, step in enumerate(steps):
            if isinstance(step, str):
                enhanced_step = {
                    "description": step,
                    "sub_steps": [],
                    "time_estimate": None,
                    "explanation": None,
                    "tips": None
                }
            else:
                # Already a dict, ensure it has all fields
                enhanced_step = {
                    "description": step.get("description", str(step)),
                    "sub_steps": step.get("sub_steps", []),
                    "time_estimate": step.get("time_estimate"),
                    "explanation": step.get("explanation"),
                    "tips": step.get("tips")
                }
            
            enhanced_steps.append(enhanced_step)
        
        return enhanced_steps
    
    def _generate_advanced_steps(
        self, 
        text: str, 
        intent: str, 
        complexity: str, 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate advanced steps based on intent and complexity"""
        # Map intent to task type
        task_type = self.intent_to_task_type.get(intent, intent)
        
        # Get base steps for the task type
        base_steps = self._get_steps_by_type(task_type, text)
        
        # Adjust step count based on complexity
        target_steps = self._calculate_step_count(len(base_steps), complexity)
        
        # Generate enhanced steps with metadata
        enhanced_steps = []
        for i, step_desc in enumerate(base_steps[:target_steps]):
            step = {
                "description": step_desc,
                "sub_steps": [],
                "time_estimate": None,
                "explanation": None,
                "tips": None
            }
            
            # Add sub-steps for complex tasks
            if complexity == "complex" and self.include_sub_steps:
                step["sub_steps"] = self._generate_sub_steps(step_desc, task_type)
            
            # Add time estimates if enabled
            if self.include_time_estimates:
                step["time_estimate"] = self._estimate_step_time(step_desc, complexity)
            
            # Add explanations for detailed format
            if self.format_style == "detailed":
                step["explanation"] = self._generate_step_explanation(step_desc, task_type)
                step["tips"] = self._generate_step_tips(step_desc, task_type)
            
            enhanced_steps.append(step)
        
        return enhanced_steps
    
    def _calculate_step_count(self, base_count: int, complexity: str) -> int:
        """Calculate the appropriate number of steps based on complexity"""
        multiplier = self.complexity_step_multipliers.get(complexity, 1.0)
        target = int(base_count * multiplier)
        return max(self.min_steps, min(target, self.max_steps))
    
    def _generate_sub_steps(self, step_description: str, task_type: str) -> List[str]:
        """Generate sub-steps for a main step"""
        # Define sub-step patterns based on common step types
        sub_step_patterns = {
            "identify": [
                "List all relevant elements",
                "Categorize by importance",
                "Note any dependencies"
            ],
            "create": [
                "Set up the basic structure",
                "Add core functionality",
                "Include error handling"
            ],
            "analyze": [
                "Collect relevant data",
                "Look for patterns",
                "Document findings"
            ],
            "implement": [
                "Write the initial code",
                "Add validation",
                "Include tests"
            ],
            "test": [
                "Create test cases",
                "Run the tests",
                "Document results"
            ],
            "optimize": [
                "Measure current performance",
                "Identify bottlenecks",
                "Apply improvements"
            ]
        }
        
        # Find matching pattern
        step_lower = step_description.lower()
        for key, sub_steps in sub_step_patterns.items():
            if key in step_lower:
                return sub_steps[:2]  # Return 2 sub-steps max
        
        return []
    
    def _estimate_step_time(self, step_description: str, complexity: str) -> str:
        """Estimate time for a step based on its description and complexity"""
        # Time estimates based on step keywords
        time_patterns = {
            "simple": {
                "research": "5-10 minutes",
                "create": "10-15 minutes",
                "implement": "15-30 minutes",
                "test": "5-10 minutes",
                "document": "5-10 minutes",
                "default": "5-15 minutes"
            },
            "moderate": {
                "research": "15-30 minutes",
                "create": "30-45 minutes",
                "implement": "45-60 minutes",
                "test": "15-30 minutes",
                "document": "15-20 minutes",
                "default": "20-40 minutes"
            },
            "complex": {
                "research": "30-60 minutes",
                "create": "1-2 hours",
                "implement": "2-4 hours",
                "test": "30-60 minutes",
                "document": "30-45 minutes",
                "default": "45-90 minutes"
            }
        }
        
        time_map = time_patterns.get(complexity, time_patterns["moderate"])
        step_lower = step_description.lower()
        
        for key, time_est in time_map.items():
            if key in step_lower:
                return time_est
        
        return time_map["default"]
    
    def _generate_step_explanation(self, step_description: str, task_type: str) -> str:
        """Generate an explanation for why a step is important"""
        explanations = {
            "identify": "This helps establish a clear understanding of the scope",
            "research": "Gathering information prevents mistakes and saves time later",
            "plan": "A good plan ensures efficient execution and reduces rework",
            "create": "Building the foundation properly ensures stability",
            "implement": "Careful implementation reduces bugs and maintenance",
            "test": "Testing ensures reliability and catches issues early",
            "optimize": "Optimization improves user experience and efficiency",
            "document": "Documentation helps future maintenance and collaboration"
        }
        
        step_lower = step_description.lower()
        for key, explanation in explanations.items():
            if key in step_lower:
                return explanation
        
        return "This step ensures thorough completion of the task"
    
    def _generate_step_tips(self, step_description: str, task_type: str) -> str:
        """Generate helpful tips for a step"""
        tips = {
            "identify": "Make a checklist to ensure nothing is missed",
            "research": "Use multiple sources and verify information",
            "plan": "Consider edge cases and potential obstacles",
            "create": "Start simple and iterate",
            "implement": "Follow best practices and coding standards",
            "test": "Test both happy paths and edge cases",
            "optimize": "Measure before and after to verify improvements",
            "document": "Write for your future self or a new team member"
        }
        
        step_lower = step_description.lower()
        for key, tip in tips.items():
            if key in step_lower:
                return tip
        
        return None
    
    def _generate_verification_steps(self, intent: str, steps: List[Dict[str, Any]]) -> List[str]:
        """Generate verification steps based on the intent and main steps"""
        verification_templates = {
            "implementation": [
                "Verify all requirements have been met",
                "Run tests to ensure functionality works correctly",
                "Check for edge cases and error handling"
            ],
            "analysis": [
                "Review findings for completeness",
                "Verify conclusions are supported by data",
                "Check for any missed aspects"
            ],
            "creation": [
                "Ensure the output meets specifications",
                "Test with real-world scenarios",
                "Get feedback if possible"
            ],
            "problem_solving": [
                "Confirm the problem is fully resolved",
                "Test the solution thoroughly",
                "Document any limitations"
            ],
            "explanation": [
                "Verify clarity and completeness",
                "Check that examples are relevant",
                "Ensure accessibility for the target audience"
            ]
        }
        
        task_type = self.intent_to_task_type.get(intent, "general")
        return verification_templates.get(task_type, [
            "Review the completed work",
            "Verify all requirements are met",
            "Check quality and completeness"
        ])
    
    def _get_additional_instructions(self, complexity: str, intent: str) -> str:
        """Generate additional instructions based on complexity and intent"""
        instructions = []
        
        # Complexity-based instructions
        if complexity == "complex":
            instructions.append("⚠️ This is a complex task - take breaks between major steps if needed.")
        elif complexity == "simple":
            instructions.append("💡 This is straightforward - you should be able to complete it quickly.")
        
        # Intent-based instructions
        intent_instructions = {
            "code_generation": "💻 Remember to test your code as you go.",
            "problem_solving": "🔍 If stuck, try breaking the problem down further.",
            "creative_writing": "✨ Let your creativity flow while following the structure.",
            "analysis": "📊 Be thorough and objective in your analysis."
        }
        
        if intent in intent_instructions:
            instructions.append(intent_instructions[intent])
        
        return "\n".join(instructions)
    
    def _generate_steps(self, text: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Generate steps based on the task type"""
        if context and "task_type" in context:
            return self._get_steps_by_type(context["task_type"], text)
            
        # Try to infer task type from text
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["analyze", "analysis", "examine"]):
            return self._get_steps_by_type("analysis", text)
        elif any(word in text_lower for word in ["create", "build", "develop", "design"]):
            return self._get_steps_by_type("creation", text)
        elif any(word in text_lower for word in ["solve", "fix", "debug", "troubleshoot"]):
            return self._get_steps_by_type("problem_solving", text)
        elif any(word in text_lower for word in ["explain", "describe", "teach"]):
            return self._get_steps_by_type("explanation", text)
        else:
            return self._get_generic_steps()
    
    def _get_steps_by_type(self, task_type: str, text: str) -> List[str]:
        """Get task-specific steps with comprehensive coverage"""
        steps_map = {
            "analysis": [
                "Identify the key components or elements to analyze",
                "Gather relevant data and context",
                "Examine relationships and patterns",
                "Evaluate findings against criteria",
                "Draw conclusions and insights",
                "Provide recommendations if applicable"
            ],
            "creation": [
                "Define requirements and constraints",
                "Research and gather necessary resources",
                "Create initial design or outline",
                "Implement the core functionality",
                "Refine and optimize the solution",
                "Test and validate the result"
            ],
            "problem_solving": [
                "Clearly define the problem and its scope",
                "Identify root causes or contributing factors",
                "Generate potential solutions",
                "Evaluate each solution's feasibility and impact",
                "Implement the chosen solution",
                "Verify the problem is resolved and document learnings"
            ],
            "explanation": [
                "Introduce the topic with context",
                "Break down complex concepts into simple parts",
                "Provide concrete examples or analogies",
                "Address common questions or misconceptions",
                "Summarize key points",
                "Suggest next steps or applications"
            ],
            "implementation": [
                "Review requirements and specifications",
                "Plan the implementation approach and architecture",
                "Set up necessary environment or dependencies",
                "Implement core functionality incrementally",
                "Add error handling and edge cases",
                "Test thoroughly and document the implementation"
            ],
            "ideation": [
                "Define the problem or opportunity space",
                "Research existing solutions and inspirations",
                "Generate diverse ideas without judgment",
                "Group and categorize ideas by theme",
                "Evaluate and prioritize promising concepts",
                "Develop top ideas into actionable proposals"
            ],
            "logical_reasoning": [
                "Identify the premises and assumptions",
                "Clarify the logical structure",
                "Examine each step of reasoning",
                "Check for logical fallacies or gaps",
                "Test conclusions against evidence",
                "Document the reasoning chain"
            ],
            "synthesis": [
                "Review all source materials",
                "Identify key themes and patterns",
                "Extract essential information",
                "Organize content logically",
                "Create a cohesive summary",
                "Ensure completeness and accuracy"
            ],
            "transformation": [
                "Understand the source format and content",
                "Identify the target format requirements",
                "Map elements between formats",
                "Perform the transformation",
                "Validate accuracy and completeness",
                "Polish and finalize the output"
            ],
            "interaction": [
                "Understand the context and participants",
                "Establish clear communication goals",
                "Listen actively and respond thoughtfully",
                "Adapt style to the audience",
                "Ensure mutual understanding",
                "Follow up on action items"
            ],
            "planning": [
                "Define objectives and success criteria",
                "Identify resources and constraints",
                "Break down into phases or milestones",
                "Create timeline with dependencies",
                "Identify risks and mitigation strategies",
                "Document the plan clearly"
            ]
        }
        
        return steps_map.get(task_type, self._get_generic_steps())
    
    def _get_generic_steps(self) -> List[str]:
        """Get generic steps for unknown task types"""
        return [
            "Understand the requirements and objectives",
            "Plan your approach",
            "Execute the main task",
            "Review and refine the output",
            "Ensure all requirements are met"
        ]