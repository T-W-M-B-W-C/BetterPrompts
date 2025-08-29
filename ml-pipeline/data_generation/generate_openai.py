#!/usr/bin/env python3
"""Generate training data using OpenAI with cleaner parallel processing progress."""

import json
import os
import sys
import time
from datetime import datetime
from collections import deque
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

# Try to import required packages
try:
    import openai
except ImportError:
    print("Error: openai package not installed!")
    print("Please run: pip install openai")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    print("Error: tqdm package not installed!")
    print("Please run: pip install tqdm")
    sys.exit(1)

# Check for API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not found in environment!")
    print("Please set it with: export OPENAI_API_KEY=your-key-here")
    sys.exit(1)

# Configure OpenAI
client = openai.OpenAI(api_key=api_key)

# Intent types
INTENTS = [
    "question_answering",
    "creative_writing", 
    "code_generation",
    "data_analysis",
    "reasoning",
    "summarization",
    "translation",
    "conversation",
    "task_planning",
    "problem_solving"
]

# Audience and complexity levels
AUDIENCES = ["child", "beginner", "intermediate", "expert", "general"]
COMPLEXITIES = ["simple", "moderate", "complex"]

class ThreadSafeRateLimiter:
    """Thread-safe rate limiter for OpenAI API calls."""
    def __init__(self, max_requests_per_minute=3500):
        self.max_requests_per_minute = max_requests_per_minute
        self.request_times = deque()
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """Wait if we're approaching rate limit."""
        with self.lock:
            now = time.time()
            
            # Remove requests older than 1 minute
            while self.request_times and self.request_times[0] < now - 60:
                self.request_times.popleft()
            
            # If we're at the limit, wait until the oldest request expires
            if len(self.request_times) >= self.max_requests_per_minute:
                sleep_time = 60 - (now - self.request_times[0]) + 0.1
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            # Record this request
            self.request_times.append(now)

# Create rate limiter (GPT-3.5-turbo Tier 2: 3500 req/min)
rate_limiter = ThreadSafeRateLimiter(max_requests_per_minute=3500)

# Thread-safe progress counter
class ProgressCounter:
    def __init__(self):
        self.count = 0
        self.lock = threading.Lock()
    
    def increment(self):
        with self.lock:
            self.count += 1
            return self.count

def generate_prompt_for_intent(intent, audience, complexity):
    """Generate a specific prompt based on intent, audience, and complexity."""
    
    intent_descriptions = {
        "question_answering": "a question seeking information or explanation",
        "creative_writing": "a request for creative writing like stories or poems",
        "code_generation": "a request to write code or programming solutions",
        "data_analysis": "a request to analyze data or extract insights",
        "reasoning": "a request requiring logical reasoning or problem-solving",
        "summarization": "a request to summarize or condense information",
        "translation": "a request to translate text between languages",
        "conversation": "a conversational prompt or discussion starter",
        "task_planning": "a request for planning or organizing tasks",
        "problem_solving": "a request to solve a specific problem"
    }
    
    audience_descriptions = {
        "child": "a young child (5-10 years old) using simple language",
        "beginner": "someone new to the topic with basic vocabulary",
        "intermediate": "someone with moderate knowledge",
        "expert": "an expert using technical terminology",
        "general": "a general audience"
    }
    
    complexity_descriptions = {
        "simple": "very simple and straightforward",
        "moderate": "moderately complex with some detail",
        "complex": "complex with multiple parts or technical requirements"
    }
    
    prompt = f"""Generate a realistic user prompt that is {intent_descriptions[intent]}.

The prompt should be:
- Suitable for {audience_descriptions[audience]}
- {complexity_descriptions[complexity].capitalize()}
- Natural and realistic, like something a real user would ask
- Diverse and unique

Generate only the user's prompt text, nothing else. Do not include any explanation or metadata."""
    
    return prompt

def generate_single_example(args):
    """Generate a single example (used by thread pool)."""
    intent, index, examples_per_intent = args
    
    # Rotate through audiences and complexities for diversity
    audience = AUDIENCES[index % len(AUDIENCES)]
    complexity = COMPLEXITIES[index % len(COMPLEXITIES)]
    
    # Add some randomness
    if index % 3 == 0:
        audience = "general"
    if index % 4 == 0:
        complexity = "moderate"
    
    # Rate limiting
    rate_limiter.wait_if_needed()
    
    try:
        # Generate the prompt
        generation_prompt = generate_prompt_for_intent(intent, audience, complexity)
        
        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates diverse, realistic user prompts."},
                {"role": "user", "content": generation_prompt}
            ],
            temperature=0.9,
            max_tokens=150
        )
        
        text = response.choices[0].message.content.strip()
        
        # Remove quotes if present
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        
        # Create example
        example = {
            "text": text,
            "intent": intent,
            "audience": audience,
            "complexity": complexity,
            "confidence": 0.85 + (0.1 if complexity == "simple" else -0.05 if complexity == "complex" else 0),
            "metadata": {
                "generation_method": "openai",
                "model": "gpt-3.5-turbo",
                "temperature": 0.9
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return ("success", example)
        
    except Exception as e:
        return ("error", f"Error on {intent} example {index + 1}: {e}")

def generate_examples_parallel(examples_per_intent=10, max_workers=10):
    """Generate examples for all intents using parallel processing with cleaner progress."""
    all_examples = []
    total_to_generate = examples_per_intent * len(INTENTS)
    errors = []
    
    print(f"Generating {examples_per_intent} examples per intent using OpenAI...")
    print(f"Total examples to generate: {total_to_generate}")
    print(f"Parallel workers: {max_workers}")
    print("Rate limiting: Automatic (up to 3500 requests/minute)")
    print("-" * 50)
    
    # Single progress bar for overall progress
    pbar = tqdm(total=total_to_generate, desc="Generating examples", unit="example", 
                ncols=100, smoothing=0.1)
    
    # Process all intents in one batch to avoid multiple progress bars
    all_tasks = []
    for intent in INTENTS:
        for i in range(examples_per_intent):
            all_tasks.append((intent, i, examples_per_intent))
    
    # Results organized by intent
    results_by_intent = {intent: [] for intent in INTENTS}
    
    # Use ThreadPoolExecutor for parallel generation
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(generate_single_example, task): task 
            for task in all_tasks
        }
        
        # Process completed futures
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            intent = task[0]
            
            try:
                status, result = future.result()
                
                if status == "error":
                    errors.append(result)
                else:
                    results_by_intent[intent].append(result)
                
                pbar.update(1)
                
            except Exception as e:
                errors.append(f"Unexpected error: {e}")
                pbar.update(1)
    
    pbar.close()
    
    # Compile all examples in order
    print("\nCompiling results by intent:")
    for intent in INTENTS:
        intent_examples = results_by_intent[intent]
        all_examples.extend(intent_examples)
        print(f"  ✓ {intent}: {len(intent_examples)} examples")
    
    # Add edge cases
    print("\nGenerating edge cases...")
    edge_cases = [
        {"text": "?", "intent": "question_answering", "confidence": 0.3},
        {"text": "help", "intent": "problem_solving", "confidence": 0.4},
        {"text": "I need something but I'm not sure what", "intent": "conversation", "confidence": 0.5},
        {"text": "Can you help me with a thing that involves stuff?", "intent": "problem_solving", "confidence": 0.4},
        {"text": "Write code to analyze data and create a summary", "intent": "code_generation", "confidence": 0.6},
        {"text": "Translate this and then summarize it", "intent": "translation", "confidence": 0.6},
        {"text": "What's the weather like today and can you plan my schedule?", "intent": "task_planning", "confidence": 0.5},
        {"text": "Tell me a story about why AI is important", "intent": "creative_writing", "confidence": 0.7},
        {"text": "How do I solve this: x^2 + 5x + 6 = 0?", "intent": "reasoning", "confidence": 0.9},
        {"text": "Analyze the trends in my sales data and create a report", "intent": "data_analysis", "confidence": 0.8},
        {"text": "helo world", "intent": "conversation", "confidence": 0.4},
        {"text": "What is the meaning of life, the universe, and everything?", "intent": "question_answering", "confidence": 0.8},
        {"text": "Generate a function that creates more functions", "intent": "code_generation", "confidence": 0.7},
        {"text": "Explain this to me like I'm five and also write a poem about it", "intent": "creative_writing", "confidence": 0.5},
        {"text": "Is this a question or a statement", "intent": "reasoning", "confidence": 0.4},
        {"text": "Summarize translate and analyze this", "intent": "summarization", "confidence": 0.5},
        {"text": "Plan a task to solve a problem by reasoning through data", "intent": "task_planning", "confidence": 0.4},
        {"text": "I don't know what I want but I need help with something technical", "intent": "problem_solving", "confidence": 0.3},
        {"text": "Convert this to Spanish and then explain what it means", "intent": "translation", "confidence": 0.6},
        {"text": "Can you do multiple things at once for me please", "intent": "conversation", "confidence": 0.4}
    ]
    
    for edge_case in edge_cases:
        edge_case.update({
            "audience": "general",
            "complexity": "simple",
            "metadata": {
                "generation_method": "edge_case",
                "type": "ambiguous"
            },
            "generated_at": datetime.now().isoformat()
        })
        all_examples.append(edge_case)
    
    print(f"✓ Added {len(edge_cases)} edge cases")
    
    if errors:
        print(f"\n⚠️  {len(errors)} errors occurred during generation")
        if len(errors) < 10:
            for error in errors:
                print(f"   - {error}")
    
    return all_examples

def main():
    """Main function."""
    # Parse command line arguments
    examples_per_intent = 1000  # Default to 1000 examples per intent
    output_file = "openai_training_data.json"
    max_workers = 8  # Default number of parallel workers
    
    if len(sys.argv) > 1:
        try:
            examples_per_intent = int(sys.argv[1])
        except ValueError:
            print("Usage: python generate_openai_parallel_clean.py [examples_per_intent] [output_file] [max_workers]")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    if len(sys.argv) > 3:
        try:
            max_workers = int(sys.argv[3])
            # Cap workers at 50 to prevent UI issues
            if max_workers > 50:
                print(f"Warning: Capping workers at 50 (requested {max_workers})")
                max_workers = 50
        except ValueError:
            max_workers = 10
    
    print("OpenAI Training Data Generator (Clean Parallel Processing)")
    print("=" * 58)
    print(f"Examples per intent: {examples_per_intent}")
    print(f"Output file: {output_file}")
    print(f"Max parallel workers: {max_workers}")
    
    # Estimate cost and time
    total_examples = examples_per_intent * len(INTENTS)
    estimated_cost = total_examples * 0.0015
    # With parallelization, time estimate based on API response time and worker count
    estimated_time = (total_examples / max_workers) * 0.3 / 60  
    
    print(f"Estimated cost: ${estimated_cost:.2f} (for {total_examples} examples)")
    print(f"Estimated time: {estimated_time:.1f} minutes (with {max_workers} parallel workers)")
    print("Starting generation in 3 seconds... (Ctrl+C to cancel)")
    
    try:
        time.sleep(3)
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    start_time = time.time()
    
    # Generate examples
    all_examples = generate_examples_parallel(examples_per_intent, max_workers)
    
    # Calculate statistics
    stats = {
        "by_intent": {},
        "by_audience": {},
        "by_complexity": {}
    }
    
    for example in all_examples:
        if "error" not in example:  # Skip error entries
            intent = example["intent"]
            audience = example["audience"]
            complexity = example["complexity"]
            
            stats["by_intent"][intent] = stats["by_intent"].get(intent, 0) + 1
            stats["by_audience"][audience] = stats["by_audience"].get(audience, 0) + 1
            stats["by_complexity"][complexity] = stats["by_complexity"].get(complexity, 0) + 1
    
    # Create dataset
    dataset = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_examples": len(all_examples),
            "generation_time_seconds": time.time() - start_time,
            "config": {
                "examples_per_intent": examples_per_intent,
                "model": "gpt-3.5-turbo",
                "temperature": 0.9,
                "use_openai": True,
                "parallel_workers": max_workers,
                "rate_limiting": "automatic"
            },
            "statistics": stats,
            "estimated_cost": f"${len(all_examples) * 0.0015:.2f}"
        },
        "examples": all_examples
    }
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Dataset saved to: {output_file}")
    print(f"✓ Total examples: {len(all_examples)}")
    print(f"✓ Generation time: {time.time() - start_time:.1f} seconds")
    print(f"✓ Actual time: {(time.time() - start_time) / 60:.1f} minutes")
    print(f"✓ Average time per example: {(time.time() - start_time) / len(all_examples):.2f} seconds")
    print(f"✓ Speedup from parallelization: ~{min(max_workers, total_examples)}x")
    print("\nStatistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Show samples
    print("\nSample examples:")
    sample_count = min(5, len([e for e in all_examples if "error" not in e]))
    shown = 0
    for example in all_examples:
        if "error" not in example and shown < sample_count:
            shown += 1
            print(f"\n{shown}. Intent: {example['intent']}")
            print(f"   Text: {example['text'][:100]}...")
            print(f"   Audience: {example['audience']}, Complexity: {example['complexity']}")

if __name__ == "__main__":
    main()