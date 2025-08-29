#!/usr/bin/env python3
"""Generate training data using templates only (no OpenAI required)."""

import json
import random
from datetime import datetime
from pathlib import Path

# Intent templates
TEMPLATES = {
    "question_answering": [
        "What is {topic}?",
        "How does {topic} work?",
        "Can you explain {topic} to me?",
        "What are the benefits of {topic}?",
        "Why is {topic} important?",
        "When should I use {topic}?",
        "What's the difference between {topic1} and {topic2}?",
        "How do I get started with {topic}?",
        "What are common mistakes with {topic}?",
        "Can you give me examples of {topic}?"
    ],
    "creative_writing": [
        "Write a short story about {topic}",
        "Create a poem about {topic}",
        "Write a dialogue between {character1} and {character2}",
        "Describe a scene involving {topic}",
        "Write a letter from {person1} to {person2}",
        "Create a fairy tale about {topic}",
        "Write a news article about {event}",
        "Compose a song about {topic}",
        "Write a movie plot about {topic}",
        "Create a character description for {character}"
    ],
    "code_generation": [
        "Write a function to {task} in {language}",
        "Create a class for {object} with {features}",
        "Implement {algorithm} in {language}",
        "Write code to {task} using {framework}",
        "Create an API endpoint for {functionality}",
        "Write a script to {task}",
        "Implement a {pattern} pattern for {use_case}",
        "Create a React component for {feature}",
        "Write SQL query to {task}",
        "Create unit tests for {function}"
    ],
    "data_analysis": [
        "Analyze the {metric} trends in this data",
        "What insights can we get from {dataset}?",
        "Compare {metric1} and {metric2} in the data",
        "Find patterns in {data_type} data",
        "Create a report on {topic} from the data",
        "What correlations exist in {dataset}?",
        "Identify outliers in {metric}",
        "Summarize the key findings from {analysis}",
        "What factors influence {outcome}?",
        "Predict {metric} based on historical data"
    ],
    "reasoning": [
        "If {premise1} and {premise2}, what can we conclude?",
        "Explain the logic behind {statement}",
        "What are the implications of {fact}?",
        "Solve this problem: {problem_description}",
        "What's the best approach to {situation}?",
        "Analyze the cause and effect of {event}",
        "What are the pros and cons of {option}?",
        "How would you reason through {scenario}?",
        "What assumptions are made in {argument}?",
        "Evaluate the validity of {claim}"
    ],
    "summarization": [
        "Summarize this article about {topic}",
        "Give me the key points from this {document_type}",
        "What are the main ideas in this text?",
        "Create a brief summary of {content}",
        "Condense this {document_type} into bullet points",
        "What's the TL;DR of this {content}?",
        "Extract the important information from {source}",
        "Summarize the findings of this {study_type}",
        "Give me a one-paragraph summary of {topic}",
        "What are the takeaways from this {content_type}?"
    ],
    "translation": [
        "Translate '{phrase}' to {language}",
        "How do you say '{phrase}' in {language}?",
        "What does '{foreign_phrase}' mean in English?",
        "Translate this sentence to {language}: {sentence}",
        "Convert this {document_type} to {language}",
        "What's the {language} equivalent of '{phrase}'?",
        "Translate and explain '{phrase}' in {language}",
        "How would a native {language} speaker say '{phrase}'?",
        "Translate this paragraph to {language}",
        "What's the literal translation of '{foreign_phrase}'?"
    ],
    "conversation": [
        "Let's talk about {topic}",
        "What do you think about {topic}?",
        "I'd like to discuss {topic} with you",
        "Can we chat about {topic}?",
        "Tell me your thoughts on {topic}",
        "I'm curious about your opinion on {topic}",
        "Let's have a conversation about {topic}",
        "What's your take on {topic}?",
        "I want to explore {topic} with you",
        "Can you share your perspective on {topic}?"
    ],
    "task_planning": [
        "Help me plan {event}",
        "Create a schedule for {activity}",
        "What steps do I need to {goal}?",
        "Organize my {timeframe} to accomplish {objective}",
        "Plan a {project_type} project",
        "Create a roadmap for {goal}",
        "Help me prioritize tasks for {objective}",
        "Design a workflow for {process}",
        "Create a timeline for {project}",
        "Plan the implementation of {initiative}"
    ],
    "problem_solving": [
        "How do I fix {problem}?",
        "What's the solution to {issue}?",
        "Help me solve this problem: {description}",
        "I'm having trouble with {problem}, what should I do?",
        "Find a solution for {challenge}",
        "How can I resolve {issue}?",
        "What's the best way to handle {problem}?",
        "Debug this issue: {error_description}",
        "Troubleshoot {system} problem",
        "How do I overcome {obstacle}?"
    ]
}

# Placeholder values for templates
PLACEHOLDERS = {
    "topic": ["machine learning", "climate change", "blockchain", "quantum computing", "artificial intelligence",
              "renewable energy", "space exploration", "genetics", "cybersecurity", "robotics"],
    "topic1": ["Python", "Java", "supervised learning", "TCP", "REST API"],
    "topic2": ["JavaScript", "C++", "unsupervised learning", "UDP", "GraphQL"],
    "task": ["sort a list", "validate email", "parse JSON", "encrypt data", "compress files",
             "search text", "filter data", "calculate statistics", "process images", "handle errors"],
    "language": ["Python", "JavaScript", "Java", "C++", "Go", "Rust", "TypeScript", "Ruby"],
    "character": ["detective", "scientist", "explorer", "teacher", "astronaut"],
    "character1": ["Alice", "Bob", "Sarah", "John", "Emma"],
    "character2": ["Charlie", "Diana", "Michael", "Lisa", "David"],
    "person1": ["a student", "a CEO", "a parent", "a friend", "a mentor"],
    "person2": ["a teacher", "an employee", "a child", "a colleague", "a mentee"],
    "event": ["conference", "wedding", "product launch", "workshop", "celebration"],
    "object": ["User", "Product", "Order", "Payment", "Session"],
    "features": ["authentication", "CRUD operations", "validation", "serialization", "caching"],
    "algorithm": ["quicksort", "binary search", "BFS", "dynamic programming", "hashing"],
    "framework": ["React", "Django", "Express", "Spring", "Flask"],
    "functionality": ["user registration", "data export", "search", "authentication", "file upload"],
    "pattern": ["singleton", "factory", "observer", "decorator", "strategy"],
    "use_case": ["database connection", "logging", "authentication", "caching", "API client"],
    "feature": ["dashboard", "login form", "data table", "navigation menu", "search bar"],
    "function": ["calculateTotal", "validateInput", "processData", "handleError", "formatDate"],
    "metric": ["revenue", "user engagement", "conversion rate", "performance", "satisfaction"],
    "metric1": ["sales", "traffic", "costs", "efficiency", "quality"],
    "metric2": ["profits", "conversions", "revenue", "productivity", "ratings"],
    "dataset": ["customer data", "sales records", "user behavior", "financial data", "survey results"],
    "data_type": ["time series", "categorical", "numerical", "text", "geospatial"],
    "analysis": ["market research", "performance review", "trend analysis", "customer segmentation", "risk assessment"],
    "outcome": ["customer churn", "sales", "user satisfaction", "product adoption", "revenue growth"],
    "premise1": ["all birds can fly", "the market is efficient", "users prefer simplicity"],
    "premise2": ["penguins are birds", "information is freely available", "the interface is complex"],
    "statement": ["correlation implies causation", "bigger is always better", "automation reduces jobs"],
    "fact": ["AI is advancing rapidly", "climate is changing", "data is growing exponentially"],
    "problem_description": ["optimize resource allocation", "reduce processing time", "improve accuracy"],
    "situation": ["team conflict", "budget constraints", "technical debt", "scaling challenges"],
    "scenario": ["system failure", "data breach", "market crash", "product launch"],
    "argument": ["free market economics", "universal basic income", "renewable energy transition"],
    "claim": ["technology improves life", "remote work is more productive", "AI will create more jobs"],
    "option": ["cloud migration", "microservices", "outsourcing", "automation"],
    "document_type": ["report", "article", "paper", "presentation", "email"],
    "content": ["research findings", "meeting notes", "technical documentation", "news article"],
    "content_type": ["video", "podcast", "blog post", "lecture", "interview"],
    "source": ["research paper", "news article", "technical document", "case study"],
    "study_type": ["clinical trial", "market research", "user study", "scientific experiment"],
    "phrase": ["hello, how are you?", "thank you very much", "see you tomorrow", "good morning"],
    "foreign_phrase": ["bonjour", "arigatou", "gracias", "guten tag", "ciao"],
    "sentence": ["The meeting is scheduled for tomorrow", "Please send the report by Friday"],
    "timeframe": ["week", "month", "quarter", "day", "year"],
    "objective": ["increase sales", "improve efficiency", "reduce costs", "launch product"],
    "project_type": ["software", "marketing", "research", "construction", "event"],
    "goal": ["learn a new skill", "start a business", "get fit", "write a book", "travel the world"],
    "process": ["customer onboarding", "product development", "quality assurance", "hiring"],
    "project": ["website redesign", "app development", "market expansion", "system upgrade"],
    "initiative": ["digital transformation", "sustainability program", "diversity initiative"],
    "problem": ["slow performance", "login issues", "data inconsistency", "connection timeout"],
    "issue": ["bug in code", "server down", "payment failure", "access denied"],
    "description": ["application crashes on startup", "data not syncing", "users can't log in"],
    "challenge": ["scaling to millions of users", "reducing latency", "improving accuracy"],
    "error_description": ["null pointer exception", "timeout error", "authentication failed"],
    "system": ["database", "network", "application", "server", "API"],
    "obstacle": ["limited resources", "technical limitations", "time constraints", "skill gaps"]
}

def fill_template(template: str) -> str:
    """Fill a template with random placeholders."""
    result = template
    
    # Find all placeholders in the template
    import re
    placeholders = re.findall(r'\{(\w+)\}', template)
    
    # Replace each placeholder
    for placeholder in placeholders:
        if placeholder in PLACEHOLDERS:
            value = random.choice(PLACEHOLDERS[placeholder])
            result = result.replace(f"{{{placeholder}}}", value)
    
    return result

def generate_examples(intent: str, count: int) -> list:
    """Generate examples for a specific intent using templates."""
    examples = []
    templates = TEMPLATES[intent]
    
    for i in range(count):
        # Select a random template
        template = random.choice(templates)
        
        # Fill the template
        text = fill_template(template)
        
        # Determine complexity
        complexity = random.choice(["simple", "moderate", "complex"])
        audience = random.choice(["general", "beginner", "intermediate", "expert"])
        
        example = {
            "text": text,
            "intent": intent,
            "audience": audience,
            "complexity": complexity,
            "confidence": round(random.uniform(0.7, 0.95), 2),
            "metadata": {
                "generation_method": "template",
                "template_used": template
            },
            "generated_at": datetime.now().isoformat()
        }
        
        examples.append(example)
    
    return examples

def main():
    """Main function."""
    print("Template-based Training Data Generator")
    print("=" * 40)
    
    # Configuration
    examples_per_intent = 100  # Generate 100 examples per intent
    output_file = "template_training_data.json"
    
    all_examples = []
    
    # Generate examples for each intent
    for intent in TEMPLATES.keys():
        print(f"Generating {examples_per_intent} examples for {intent}...")
        examples = generate_examples(intent, examples_per_intent)
        all_examples.extend(examples)
        print(f"  ✓ Generated {len(examples)} examples")
    
    # Add some edge cases
    print("\nGenerating edge cases...")
    edge_cases = [
        {"text": "?", "intent": "question_answering", "audience": "general", "complexity": "simple",
         "confidence": 0.3, "metadata": {"generation_method": "edge_case", "type": "minimal"}},
        {"text": "help", "intent": "problem_solving", "audience": "general", "complexity": "simple",
         "confidence": 0.4, "metadata": {"generation_method": "edge_case", "type": "vague"}},
        {"text": "explain quantum computing to a 5 year old", "intent": "question_answering",
         "audience": "child", "complexity": "complex", "confidence": 0.9,
         "metadata": {"generation_method": "edge_case", "type": "audience_mismatch"}},
        {"text": "wat is the differance between AI and ML", "intent": "question_answering",
         "audience": "general", "complexity": "moderate", "confidence": 0.8,
         "metadata": {"generation_method": "edge_case", "type": "typos"}},
    ]
    
    for edge_case in edge_cases:
        edge_case["generated_at"] = datetime.now().isoformat()
        all_examples.append(edge_case)
    
    print(f"  ✓ Added {len(edge_cases)} edge cases")
    
    # Shuffle examples
    random.shuffle(all_examples)
    
    # Create dataset
    dataset = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_examples": len(all_examples),
            "config": {
                "examples_per_intent": examples_per_intent,
                "generation_method": "template",
                "edge_cases": len(edge_cases)
            },
            "statistics": {
                "by_intent": {},
                "by_audience": {},
                "by_complexity": {}
            }
        },
        "examples": all_examples
    }
    
    # Calculate statistics
    for example in all_examples:
        intent = example["intent"]
        audience = example["audience"]
        complexity = example["complexity"]
        
        dataset["metadata"]["statistics"]["by_intent"][intent] = \
            dataset["metadata"]["statistics"]["by_intent"].get(intent, 0) + 1
        dataset["metadata"]["statistics"]["by_audience"][audience] = \
            dataset["metadata"]["statistics"]["by_audience"].get(audience, 0) + 1
        dataset["metadata"]["statistics"]["by_complexity"][complexity] = \
            dataset["metadata"]["statistics"]["by_complexity"].get(complexity, 0) + 1
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Dataset saved to: {output_file}")
    print(f"✓ Total examples: {len(all_examples)}")
    print("\nStatistics:")
    print(f"  By intent: {dataset['metadata']['statistics']['by_intent']}")
    print(f"  By audience: {dataset['metadata']['statistics']['by_audience']}")
    print(f"  By complexity: {dataset['metadata']['statistics']['by_complexity']}")
    
    # Show samples
    print("\nSample examples:")
    for i in range(min(3, len(all_examples))):
        example = all_examples[i]
        print(f"\n{i+1}. Intent: {example['intent']}")
        print(f"   Text: {example['text']}")
        print(f"   Audience: {example['audience']}, Complexity: {example['complexity']}")

if __name__ == "__main__":
    main()