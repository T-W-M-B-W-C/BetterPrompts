"""Prompt templates for generating diverse training examples for each intent type."""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import random


class IntentType(Enum):
    """All supported intent types."""
    QUESTION_ANSWERING = "question_answering"
    CREATIVE_WRITING = "creative_writing"
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"
    REASONING = "reasoning"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    CONVERSATION = "conversation"
    TASK_PLANNING = "task_planning"
    PROBLEM_SOLVING = "problem_solving"


class AudienceLevel(Enum):
    """Target audience levels."""
    CHILD = "child"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"
    GENERAL = "general"


class ComplexityLevel(Enum):
    """Task complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


@dataclass
class PromptTemplate:
    """Template for generating prompts."""
    intent: IntentType
    audience: AudienceLevel
    complexity: ComplexityLevel
    template: str
    variations: List[str]
    topics: List[str]


class PromptTemplateManager:
    """Manages prompt templates for all intent types."""
    
    def __init__(self):
        self.templates = self._create_all_templates()
    
    def _create_all_templates(self) -> Dict[IntentType, List[PromptTemplate]]:
        """Create comprehensive templates for all intent types."""
        return {
            IntentType.QUESTION_ANSWERING: self._create_question_answering_templates(),
            IntentType.CREATIVE_WRITING: self._create_creative_writing_templates(),
            IntentType.CODE_GENERATION: self._create_code_generation_templates(),
            IntentType.DATA_ANALYSIS: self._create_data_analysis_templates(),
            IntentType.REASONING: self._create_reasoning_templates(),
            IntentType.SUMMARIZATION: self._create_summarization_templates(),
            IntentType.TRANSLATION: self._create_translation_templates(),
            IntentType.CONVERSATION: self._create_conversation_templates(),
            IntentType.TASK_PLANNING: self._create_task_planning_templates(),
            IntentType.PROBLEM_SOLVING: self._create_problem_solving_templates(),
        }
    
    def _create_question_answering_templates(self) -> List[PromptTemplate]:
        """Templates for question answering intent."""
        return [
            # Child audience
            PromptTemplate(
                intent=IntentType.QUESTION_ANSWERING,
                audience=AudienceLevel.CHILD,
                complexity=ComplexityLevel.SIMPLE,
                template="Generate a simple question a child might ask about {topic}",
                variations=[
                    "What is {topic}?",
                    "How does {topic} work?",
                    "Why do we have {topic}?",
                    "Can you explain {topic} to me?"
                ],
                topics=["animals", "weather", "space", "colors", "food", "toys", "school", "family"]
            ),
            # Beginner audience
            PromptTemplate(
                intent=IntentType.QUESTION_ANSWERING,
                audience=AudienceLevel.BEGINNER,
                complexity=ComplexityLevel.SIMPLE,
                template="Generate a beginner-level question about {topic}",
                variations=[
                    "What are the basics of {topic}?",
                    "How do I get started with {topic}?",
                    "What should I know about {topic} as a beginner?",
                    "Can you explain {topic} in simple terms?"
                ],
                topics=["programming", "cooking", "fitness", "investing", "photography", "gardening"]
            ),
            # Intermediate audience
            PromptTemplate(
                intent=IntentType.QUESTION_ANSWERING,
                audience=AudienceLevel.INTERMEDIATE,
                complexity=ComplexityLevel.MODERATE,
                template="Generate an intermediate-level question about {topic}",
                variations=[
                    "How can I improve my {topic} skills?",
                    "What are the best practices for {topic}?",
                    "Can you explain the advanced features of {topic}?",
                    "What are common mistakes in {topic}?"
                ],
                topics=["machine learning", "web development", "data science", "cloud computing", "cybersecurity"]
            ),
            # Expert audience
            PromptTemplate(
                intent=IntentType.QUESTION_ANSWERING,
                audience=AudienceLevel.EXPERT,
                complexity=ComplexityLevel.COMPLEX,
                template="Generate an expert-level question about {topic}",
                variations=[
                    "What are the latest research developments in {topic}?",
                    "How do you optimize {topic} for production environments?",
                    "What are the theoretical limitations of {topic}?",
                    "Can you analyze the computational complexity of {topic}?"
                ],
                topics=["quantum computing", "distributed systems", "neural architecture search", "cryptography", "compiler design"]
            ),
        ]
    
    def _create_creative_writing_templates(self) -> List[PromptTemplate]:
        """Templates for creative writing intent."""
        return [
            # General audience - Simple
            PromptTemplate(
                intent=IntentType.CREATIVE_WRITING,
                audience=AudienceLevel.GENERAL,
                complexity=ComplexityLevel.SIMPLE,
                template="Generate a request to write a short {format} about {topic}",
                variations=[
                    "Write a {format} about {topic}",
                    "Create a {format} that involves {topic}",
                    "Can you write a {format} featuring {topic}?",
                    "I need a {format} about {topic}"
                ],
                topics=["friendship", "adventure", "mystery", "love", "courage", "dreams"],
                formats=["story", "poem", "dialogue", "description", "letter"]
            ),
            # Creative professionals - Complex
            PromptTemplate(
                intent=IntentType.CREATIVE_WRITING,
                audience=AudienceLevel.EXPERT,
                complexity=ComplexityLevel.COMPLEX,
                template="Generate a complex creative writing request with specific constraints",
                variations=[
                    "Write a {format} in the style of {author} about {topic} with {constraint}",
                    "Create a {format} that explores {theme} through {technique}",
                    "Compose a {format} using {literary_device} to convey {emotion}"
                ],
                topics=["existentialism", "post-modernism", "magical realism", "dystopia", "metafiction"],
                formats=["novella opening", "sonnet sequence", "stream of consciousness", "epistolary narrative"]
            ),
        ]
    
    def _create_code_generation_templates(self) -> List[PromptTemplate]:
        """Templates for code generation intent."""
        return [
            # Beginner programmer
            PromptTemplate(
                intent=IntentType.CODE_GENERATION,
                audience=AudienceLevel.BEGINNER,
                complexity=ComplexityLevel.SIMPLE,
                template="Generate a beginner coding request for {language}",
                variations=[
                    "How do I write a function to {task} in {language}?",
                    "Can you show me how to {task} using {language}?",
                    "Write a simple {language} program that {task}",
                    "I need help creating a {task} in {language}"
                ],
                topics=["sort a list", "read a file", "calculate average", "find maximum", "reverse string"],
                languages=["Python", "JavaScript", "Java", "C++"]
            ),
            # Professional developer
            PromptTemplate(
                intent=IntentType.CODE_GENERATION,
                audience=AudienceLevel.EXPERT,
                complexity=ComplexityLevel.COMPLEX,
                template="Generate an advanced coding request",
                variations=[
                    "Implement {algorithm} with {optimization} in {language}",
                    "Create a {pattern} for {use_case} with {constraint}",
                    "Design a {system} that handles {requirement} using {technology}"
                ],
                topics=["distributed cache", "real-time analytics", "microservices", "event sourcing", "CQRS pattern"],
                languages=["Go", "Rust", "Scala", "Kotlin"]
            ),
        ]
    
    def _create_data_analysis_templates(self) -> List[PromptTemplate]:
        """Templates for data analysis intent."""
        return [
            # Business analyst
            PromptTemplate(
                intent=IntentType.DATA_ANALYSIS,
                audience=AudienceLevel.INTERMEDIATE,
                complexity=ComplexityLevel.MODERATE,
                template="Generate a data analysis request for business context",
                variations=[
                    "Analyze the {metric} trends in our {dataset} for {period}",
                    "What insights can we derive from {data_source} regarding {topic}?",
                    "Compare {metric1} vs {metric2} and identify patterns",
                    "Create a report on {topic} using {data_source}"
                ],
                topics=["sales performance", "customer churn", "market trends", "user engagement", "revenue growth"],
                metrics=["conversion rate", "retention", "ROI", "CAC", "LTV"]
            ),
            # Data scientist
            PromptTemplate(
                intent=IntentType.DATA_ANALYSIS,
                audience=AudienceLevel.EXPERT,
                complexity=ComplexityLevel.COMPLEX,
                template="Generate an advanced data science request",
                variations=[
                    "Perform {analysis_type} on {dataset} to predict {outcome}",
                    "Build a {model_type} model to analyze {phenomenon}",
                    "Apply {technique} to understand {relationship} in the data"
                ],
                topics=["anomaly detection", "time series forecasting", "clustering analysis", "feature engineering"],
                techniques=["PCA", "random forests", "LSTM", "gradient boosting", "deep learning"]
            ),
        ]
    
    def _create_reasoning_templates(self) -> List[PromptTemplate]:
        """Templates for reasoning intent."""
        return [
            # Logical reasoning
            PromptTemplate(
                intent=IntentType.REASONING,
                audience=AudienceLevel.GENERAL,
                complexity=ComplexityLevel.MODERATE,
                template="Generate a logical reasoning problem",
                variations=[
                    "If {premise1} and {premise2}, what can we conclude about {topic}?",
                    "Analyze the logical relationship between {concept1} and {concept2}",
                    "What are the implications of {statement} for {domain}?",
                    "Evaluate the argument: {claim} because {reason}"
                ],
                topics=["cause and effect", "syllogisms", "deductive reasoning", "inductive reasoning", "paradoxes"]
            ),
            # Mathematical reasoning
            PromptTemplate(
                intent=IntentType.REASONING,
                audience=AudienceLevel.EXPERT,
                complexity=ComplexityLevel.COMPLEX,
                template="Generate a complex mathematical reasoning problem",
                variations=[
                    "Prove that {theorem} holds for all {condition}",
                    "Find the optimal solution to {problem} given {constraints}",
                    "Derive the relationship between {variable1} and {variable2}"
                ],
                topics=["optimization", "game theory", "graph theory", "number theory", "topology"]
            ),
        ]
    
    def _create_summarization_templates(self) -> List[PromptTemplate]:
        """Templates for summarization intent."""
        return [
            # General summarization
            PromptTemplate(
                intent=IntentType.SUMMARIZATION,
                audience=AudienceLevel.GENERAL,
                complexity=ComplexityLevel.SIMPLE,
                template="Generate a summarization request",
                variations=[
                    "Summarize this {content_type} about {topic}",
                    "Give me the key points from this {content_type}",
                    "What are the main ideas in this {content_type}?",
                    "Create a brief summary of {content_type}"
                ],
                topics=["article", "research paper", "book chapter", "meeting notes", "report"],
                content_types=["text", "document", "transcript", "email thread", "discussion"]
            ),
            # Professional summarization
            PromptTemplate(
                intent=IntentType.SUMMARIZATION,
                audience=AudienceLevel.EXPERT,
                complexity=ComplexityLevel.COMPLEX,
                template="Generate an advanced summarization request",
                variations=[
                    "Create an executive summary of {document} focusing on {aspect}",
                    "Synthesize the findings from multiple {sources} on {topic}",
                    "Abstract the methodology and results from this {publication_type}"
                ],
                topics=["quarterly earnings", "research findings", "technical specifications", "legal documents"],
                publication_types=["journal article", "white paper", "technical report", "case study"]
            ),
        ]
    
    def _create_translation_templates(self) -> List[PromptTemplate]:
        """Templates for translation intent."""
        return [
            # Basic translation
            PromptTemplate(
                intent=IntentType.TRANSLATION,
                audience=AudienceLevel.GENERAL,
                complexity=ComplexityLevel.SIMPLE,
                template="Generate a translation request",
                variations=[
                    "Translate '{phrase}' to {language}",
                    "How do you say '{phrase}' in {language}?",
                    "What does '{phrase}' mean in {language}?",
                    "Can you translate this to {language}: {phrase}"
                ],
                topics=["greetings", "common phrases", "directions", "food items", "numbers"],
                languages=["Spanish", "French", "German", "Japanese", "Mandarin", "Italian"]
            ),
            # Professional translation
            PromptTemplate(
                intent=IntentType.TRANSLATION,
                audience=AudienceLevel.EXPERT,
                complexity=ComplexityLevel.COMPLEX,
                template="Generate a professional translation request",
                variations=[
                    "Translate this {document_type} from {source_lang} to {target_lang} maintaining {style}",
                    "Provide a culturally appropriate translation of {content} for {region}",
                    "Localize this {content_type} for {market}"
                ],
                topics=["legal contract", "technical manual", "marketing copy", "medical document"],
                document_types=["contract", "patent", "user manual", "website content"]
            ),
        ]
    
    def _create_conversation_templates(self) -> List[PromptTemplate]:
        """Templates for conversation intent."""
        return [
            # Casual conversation
            PromptTemplate(
                intent=IntentType.CONVERSATION,
                audience=AudienceLevel.GENERAL,
                complexity=ComplexityLevel.SIMPLE,
                template="Generate a conversational request",
                variations=[
                    "Let's talk about {topic}",
                    "What do you think about {topic}?",
                    "Can we discuss {topic}?",
                    "I'd like to chat about {topic}"
                ],
                topics=["movies", "hobbies", "travel", "food", "sports", "music", "books"],
            ),
            # Professional conversation
            PromptTemplate(
                intent=IntentType.CONVERSATION,
                audience=AudienceLevel.INTERMEDIATE,
                complexity=ComplexityLevel.MODERATE,
                template="Generate a professional conversation starter",
                variations=[
                    "I'd like to discuss {business_topic} with you",
                    "Can we have a conversation about {professional_topic}?",
                    "Let's explore the implications of {trend} for {industry}"
                ],
                topics=["project management", "team dynamics", "industry trends", "career development"],
            ),
        ]
    
    def _create_task_planning_templates(self) -> List[PromptTemplate]:
        """Templates for task planning intent."""
        return [
            # Personal planning
            PromptTemplate(
                intent=IntentType.TASK_PLANNING,
                audience=AudienceLevel.GENERAL,
                complexity=ComplexityLevel.MODERATE,
                template="Generate a task planning request",
                variations=[
                    "Help me plan {event_type}",
                    "Create a schedule for {activity}",
                    "What steps do I need to {goal}?",
                    "Organize my {timeframe} to accomplish {objective}"
                ],
                topics=["vacation", "wedding", "move", "study schedule", "workout routine"],
                event_types=["trip", "party", "project", "renovation", "campaign"]
            ),
            # Project management
            PromptTemplate(
                intent=IntentType.TASK_PLANNING,
                audience=AudienceLevel.EXPERT,
                complexity=ComplexityLevel.COMPLEX,
                template="Generate a complex project planning request",
                variations=[
                    "Create a project plan for {project_type} with {constraints}",
                    "Develop a roadmap for {initiative} considering {factors}",
                    "Design a workflow for {process} optimizing for {metrics}"
                ],
                topics=["software deployment", "product launch", "system migration", "team restructuring"],
                project_types=["agile transformation", "digital transformation", "merger integration"]
            ),
        ]
    
    def _create_problem_solving_templates(self) -> List[PromptTemplate]:
        """Templates for problem solving intent."""
        return [
            # Everyday problems
            PromptTemplate(
                intent=IntentType.PROBLEM_SOLVING,
                audience=AudienceLevel.GENERAL,
                complexity=ComplexityLevel.SIMPLE,
                template="Generate a problem-solving request",
                variations=[
                    "How do I fix {problem}?",
                    "What's the solution to {issue}?",
                    "Help me solve this problem: {description}",
                    "I'm having trouble with {problem}, what should I do?"
                ],
                topics=["computer issues", "home repairs", "cooking mistakes", "relationship problems"],
                problems=["slow internet", "leaky faucet", "burnt food", "communication issues"]
            ),
            # Technical problems
            PromptTemplate(
                intent=IntentType.PROBLEM_SOLVING,
                audience=AudienceLevel.EXPERT,
                complexity=ComplexityLevel.COMPLEX,
                template="Generate a complex technical problem",
                variations=[
                    "Debug this {system} issue: {symptoms}",
                    "Optimize {process} to handle {constraint}",
                    "Resolve the {conflict} between {component1} and {component2}",
                    "Find the root cause of {performance_issue} in {system}"
                ],
                topics=["memory leak", "race condition", "deadlock", "performance bottleneck"],
                systems=["distributed system", "database", "network", "application", "infrastructure"]
            ),
        ]
    
    def get_template(
        self, 
        intent: IntentType, 
        audience: AudienceLevel = None, 
        complexity: ComplexityLevel = None
    ) -> PromptTemplate:
        """Get a template matching the criteria."""
        templates = self.templates[intent]
        
        # Filter by audience if specified
        if audience:
            templates = [t for t in templates if t.audience == audience]
        
        # Filter by complexity if specified
        if complexity:
            templates = [t for t in templates if t.complexity == complexity]
        
        # Return random template from filtered list
        return random.choice(templates) if templates else self.templates[intent][0]
    
    def generate_prompt_from_template(self, template: PromptTemplate) -> str:
        """Generate a specific prompt from a template."""
        # Choose random variation
        variation = random.choice(template.variations)
        
        # Fill in placeholders
        prompt = variation
        
        # Replace topic placeholder
        if "{topic}" in prompt and hasattr(template, "topics"):
            topic = random.choice(template.topics)
            prompt = prompt.replace("{topic}", topic)
        
        # Replace other placeholders based on template attributes
        placeholders = {
            "format": "formats",
            "language": "languages",
            "metric": "metrics",
            "content_type": "content_types",
            # Add more as needed
        }
        
        for placeholder, attr_name in placeholders.items():
            if f"{{{placeholder}}}" in prompt and hasattr(template, attr_name):
                value = random.choice(getattr(template, attr_name))
                prompt = prompt.replace(f"{{{placeholder}}}", value)
        
        # Handle any remaining placeholders with generic values
        remaining_placeholders = {
            "{constraint}": "performance requirements",
            "{author}": "Hemingway",
            "{theme}": "isolation",
            "{technique}": "metaphor",
            "{literary_device}": "symbolism",
            "{emotion}": "melancholy",
            "{algorithm}": "quicksort",
            "{optimization}": "time complexity",
            "{pattern}": "singleton pattern",
            "{use_case}": "user authentication",
            "{system}": "recommendation engine",
            "{requirement}": "real-time updates",
            "{technology}": "Redis",
            "{dataset}": "customer data",
            "{period}": "last quarter",
            "{data_source}": "analytics database",
            "{metric1}": "revenue",
            "{metric2}": "costs",
            "{analysis_type}": "regression analysis",
            "{outcome}": "customer churn",
            "{model_type}": "classification",
            "{phenomenon}": "seasonal patterns",
            "{relationship}": "correlation",
            "{premise1}": "all birds can fly",
            "{premise2}": "penguins are birds",
            "{concept1}": "democracy",
            "{concept2}": "freedom",
            "{statement}": "AI will surpass human intelligence",
            "{domain}": "ethics",
            "{claim}": "exercise improves health",
            "{reason}": "it increases cardiovascular fitness",
            "{theorem}": "the sum converges",
            "{condition}": "n > 0",
            "{problem}": "traveling salesman",
            "{constraints}": "limited resources",
            "{variable1}": "temperature",
            "{variable2}": "pressure",
            "{document}": "annual report",
            "{aspect}": "financial performance",
            "{sources}": "research papers",
            "{publication_type}": "scientific study",
            "{phrase}": "hello, how are you?",
            "{source_lang}": "English",
            "{target_lang}": "Spanish",
            "{style}": "formal tone",
            "{content}": "marketing message",
            "{region}": "Latin America",
            "{market}": "Japanese market",
            "{business_topic}": "quarterly goals",
            "{professional_topic}": "leadership strategies",
            "{trend}": "remote work",
            "{industry}": "technology",
            "{event_type}": "conference",
            "{activity}": "marathon training",
            "{goal}": "learn a new language",
            "{timeframe}": "next month",
            "{objective}": "launch a product",
            "{project_type}": "mobile app development",
            "{initiative}": "cloud migration",
            "{factors}": "budget and timeline",
            "{process}": "customer onboarding",
            "{metrics}": "user satisfaction",
            "{issue}": "team communication",
            "{description}": "my car won't start",
            "{symptoms}": "high CPU usage",
            "{conflict}": "version mismatch",
            "{component1}": "frontend",
            "{component2}": "backend",
            "{performance_issue}": "slow queries"
        }
        
        for placeholder, value in remaining_placeholders.items():
            prompt = prompt.replace(placeholder, value)
        
        return prompt


# Create global instance
prompt_manager = PromptTemplateManager()


# Helper functions
def get_random_prompt(intent: IntentType) -> str:
    """Get a random prompt for a specific intent."""
    template = prompt_manager.get_template(intent)
    return prompt_manager.generate_prompt_from_template(template)


def get_diverse_prompts(intent: IntentType, count: int = 10) -> List[Tuple[str, AudienceLevel, ComplexityLevel]]:
    """Get diverse prompts covering different audiences and complexities."""
    prompts = []
    
    # Ensure we cover all audiences and complexities
    audiences = list(AudienceLevel)
    complexities = list(ComplexityLevel)
    
    for i in range(count):
        # Rotate through audiences and complexities
        audience = audiences[i % len(audiences)]
        complexity = complexities[i % len(complexities)]
        
        template = prompt_manager.get_template(intent, audience, complexity)
        prompt = prompt_manager.generate_prompt_from_template(template)
        prompts.append((prompt, template.audience, template.complexity))
    
    return prompts