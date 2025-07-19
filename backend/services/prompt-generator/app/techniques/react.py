"""
ReAct (Reasoning + Acting) Prompt Engineering Technique.

This technique interleaves reasoning and acting to solve complex tasks
by combining chain-of-thought reasoning with action planning and execution.
It's particularly effective for tasks requiring multiple steps and external interactions.
"""

import re
from typing import Dict, Any, Optional, List
from .base import BaseTechnique


class ReactTechnique(BaseTechnique):
    """
    ReAct technique implementation.
    
    Combines reasoning traces with action plans to solve complex tasks
    through an iterative process of thinking, acting, and observing results.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the ReAct technique."""
        super().__init__(config)
        
        # Default template for ReAct prompting
        self.default_template = """{{ original_prompt }}

I'll solve this using the ReAct (Reasoning + Acting) approach, which combines thinking with action:

{% if initial_analysis %}
**Initial Analysis:**
{{ initial_analysis }}
{% endif %}

**ReAct Process:**

{% for i in range(num_steps) %}
Step {{ i + 1 }}:
Thought {{ i + 1 }}: {{ thought_prompts[i] }}
[Reasoning about the current situation, what we know, and what we need to do next]

Action {{ i + 1 }}: {{ action_prompts[i] }}
[Specific action to take based on the reasoning]

Observation {{ i + 1 }}: [Expected result or information gained from the action]

{% endfor %}

{% if allow_iterations %}
**Iteration Check:**
If the goal hasn't been achieved, continue with additional Thought-Action-Observation cycles:
- Analyze what worked and what didn't
- Adjust the approach based on observations
- Continue until the task is complete or maximum iterations reached
{% endif %}

**Final Answer:**
Based on the ReAct process above, synthesize all observations and reasoning to provide the final answer:
[Complete solution incorporating all insights gained through the process]

{% if include_reflection %}
**Reflection:**
- What worked well in this approach?
- What challenges were encountered?
- How could the process be improved?
{% endif %}"""
        
        # Use provided template or default
        if not self.template:
            self.template = self.default_template
            
        # Default prompts for different types of thoughts and actions
        self.thought_templates = {
            'analysis': "I need to analyze the current state and identify what information is missing",
            'planning': "I should plan the next action based on what I've learned so far",
            'evaluation': "Let me evaluate the results and determine if I'm closer to the solution",
            'synthesis': "I'll synthesize the information gathered to form a conclusion",
            'debugging': "Something unexpected happened, I need to understand why and adjust",
            'verification': "I should verify that my current understanding is correct"
        }
        
        self.action_templates = {
            'search': "Search for information about",
            'calculate': "Calculate",
            'query': "Query",
            'analyze': "Analyze",
            'compare': "Compare",
            'test': "Test the hypothesis that",
            'implement': "Implement",
            'verify': "Verify"
        }
    
    def apply(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Apply the ReAct technique to the input text.
        
        Args:
            text: The original prompt or task
            context: Additional context including:
                - num_steps: Number of reasoning-action steps (default: 3)
                - task_type: Type of task for optimization
                - available_tools: List of available tools/actions
                - allow_iterations: Whether to allow dynamic iterations
                - include_reflection: Whether to include reflection section
                - initial_analysis: Optional initial analysis text
        
        Returns:
            Enhanced prompt with ReAct structure
        """
        try:
            # Clean the input text
            clean_text = self.clean_text(text)
            
            # Extract parameters from context
            context = context or {}
            num_steps = min(context.get('num_steps', 3), 6)  # Cap at 6 for token efficiency
            task_type = context.get('task_type', 'general')
            available_tools = context.get('available_tools', [])
            allow_iterations = context.get('allow_iterations', True)
            include_reflection = context.get('include_reflection', False)
            initial_analysis = context.get('initial_analysis', '')
            
            # Generate thought and action prompts
            thought_prompts = self._generate_thought_prompts(task_type, num_steps)
            action_prompts = self._generate_action_prompts(
                task_type, num_steps, available_tools
            )
            
            # Prepare template variables
            template_vars = {
                'original_prompt': clean_text,
                'num_steps': num_steps,
                'thought_prompts': thought_prompts,
                'action_prompts': action_prompts,
                'allow_iterations': allow_iterations,
                'include_reflection': include_reflection,
                'initial_analysis': initial_analysis
            }
            
            # Render the template
            enhanced_prompt = self.render_template(self.template, template_vars)
            
            self.logger.debug(
                f"Applied ReAct with {num_steps} steps for task type: {task_type}"
            )
            
            return enhanced_prompt
            
        except Exception as e:
            self.logger.error(f"Error applying ReAct technique: {str(e)}")
            return text
    
    def validate_input(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate if the input is suitable for ReAct technique.
        
        Best suited for:
        - Multi-step problems
        - Tasks requiring information gathering
        - Problems needing iterative refinement
        - Tasks with external dependencies
        - Complex decision-making scenarios
        
        Args:
            text: The input text to validate
            context: Additional context
        
        Returns:
            True if suitable for ReAct, False otherwise
        """
        if not text or len(text.strip()) < 20:
            self.logger.debug("Text too short for ReAct technique")
            return False
        
        # Keywords indicating multi-step processes
        multistep_keywords = [
            'step', 'process', 'procedure', 'implement', 'build',
            'create', 'develop', 'design', 'plan', 'strategy',
            'how to', 'guide', 'tutorial', 'workflow'
        ]
        
        # Keywords indicating need for information gathering
        info_keywords = [
            'research', 'find', 'search', 'gather', 'collect',
            'investigate', 'explore', 'discover', 'identify',
            'determine', 'figure out', 'understand'
        ]
        
        # Keywords indicating iterative tasks
        iterative_keywords = [
            'optimize', 'improve', 'refine', 'iterate', 'enhance',
            'debug', 'troubleshoot', 'fix', 'solve', 'resolve'
        ]
        
        text_lower = text.lower()
        
        # Check for multi-step indicators
        has_multistep = any(keyword in text_lower for keyword in multistep_keywords)
        has_info_need = any(keyword in text_lower for keyword in info_keywords)
        has_iteration = any(keyword in text_lower for keyword in iterative_keywords)
        
        # ReAct is valuable for tasks that need reasoning + action
        if has_multistep or has_info_need or has_iteration:
            self.logger.debug("Input suitable for ReAct: multi-step or iterative task")
            return True
        
        # Check context for explicit indicators
        if context:
            task_type = context.get('task_type', '').lower()
            suitable_types = [
                'implementation', 'debugging', 'research', 
                'problem-solving', 'planning', 'analysis'
            ]
            if any(t in task_type for t in suitable_types):
                self.logger.debug(f"Input suitable for ReAct: task type {task_type}")
                return True
            
            # If tools are available, ReAct can be useful
            if context.get('available_tools'):
                self.logger.debug("Input suitable for ReAct: tools available")
                return True
        
        # For complex questions that likely need multiple steps
        if '?' in text and len(text.split()) > 15:
            # Count complexity indicators
            complexity_score = 0
            complexity_words = ['and', 'then', 'after', 'before', 'while', 'if']
            for word in complexity_words:
                complexity_score += text_lower.count(word)
            
            if complexity_score >= 3:
                self.logger.debug("Input suitable for ReAct: complex multi-part question")
                return True
        
        self.logger.debug("Input not ideal for ReAct technique")
        return False
    
    def _generate_thought_prompts(self, task_type: str, num_steps: int) -> List[str]:
        """Generate task-specific thought prompts."""
        thought_sequences = {
            'implementation': [
                self.thought_templates['analysis'],
                self.thought_templates['planning'],
                self.thought_templates['evaluation'],
                self.thought_templates['synthesis'],
                self.thought_templates['verification'],
                self.thought_templates['debugging']
            ],
            'debugging': [
                self.thought_templates['analysis'],
                self.thought_templates['debugging'],
                self.thought_templates['planning'],
                self.thought_templates['verification'],
                self.thought_templates['evaluation'],
                self.thought_templates['synthesis']
            ],
            'research': [
                self.thought_templates['analysis'],
                self.thought_templates['planning'],
                self.thought_templates['evaluation'],
                self.thought_templates['synthesis'],
                self.thought_templates['verification'],
                self.thought_templates['planning']
            ],
            'problem-solving': [
                self.thought_templates['analysis'],
                self.thought_templates['planning'],
                self.thought_templates['evaluation'],
                self.thought_templates['debugging'],
                self.thought_templates['synthesis'],
                self.thought_templates['verification']
            ],
            'general': [
                self.thought_templates['analysis'],
                self.thought_templates['planning'],
                self.thought_templates['evaluation'],
                self.thought_templates['synthesis'],
                self.thought_templates['verification'],
                self.thought_templates['planning']
            ]
        }
        
        sequence = thought_sequences.get(task_type, thought_sequences['general'])
        return sequence[:num_steps]
    
    def _generate_action_prompts(
        self, 
        task_type: str, 
        num_steps: int, 
        available_tools: List[str]
    ) -> List[str]:
        """Generate task-specific action prompts."""
        # If specific tools are available, prioritize them
        if available_tools:
            action_prompts = []
            for i in range(num_steps):
                if i < len(available_tools):
                    tool = available_tools[i]
                    action_prompts.append(f"Use {tool} to")
                else:
                    # Cycle through available tools if more steps than tools
                    tool = available_tools[i % len(available_tools)]
                    action_prompts.append(f"Use {tool} again to")
            return action_prompts
        
        # Otherwise, use task-specific action sequences
        action_sequences = {
            'implementation': [
                self.action_templates['analyze'] + " the requirements",
                self.action_templates['implement'] + " the core functionality",
                self.action_templates['test'] + " the implementation works correctly",
                self.action_templates['verify'] + " all requirements are met",
                self.action_templates['implement'] + " error handling and edge cases",
                self.action_templates['test'] + " the complete solution"
            ],
            'debugging': [
                self.action_templates['analyze'] + " the error or issue",
                self.action_templates['test'] + " the issue can be reproduced",
                self.action_templates['search'] + " similar issues and solutions",
                self.action_templates['implement'] + " a potential fix",
                self.action_templates['verify'] + " the fix resolves the issue",
                self.action_templates['test'] + " no new issues were introduced"
            ],
            'research': [
                self.action_templates['search'] + " relevant information",
                self.action_templates['analyze'] + " the gathered data",
                self.action_templates['compare'] + " different sources and perspectives",
                self.action_templates['verify'] + " the accuracy of findings",
                self.action_templates['query'] + " additional specific details",
                self.action_templates['analyze'] + " the complete findings"
            ],
            'problem-solving': [
                self.action_templates['analyze'] + " the problem structure",
                self.action_templates['search'] + " similar problems and solutions",
                self.action_templates['calculate'] + " or work through a solution",
                self.action_templates['test'] + " the solution is correct",
                self.action_templates['verify'] + " edge cases are handled",
                self.action_templates['implement'] + " the final solution"
            ],
            'general': [
                self.action_templates['analyze'] + " the current situation",
                self.action_templates['search'] + " necessary information",
                self.action_templates['implement'] + " the approach",
                self.action_templates['test'] + " the results",
                self.action_templates['verify'] + " the outcome meets requirements",
                self.action_templates['analyze'] + " the final results"
            ]
        }
        
        sequence = action_sequences.get(task_type, action_sequences['general'])
        return sequence[:num_steps]