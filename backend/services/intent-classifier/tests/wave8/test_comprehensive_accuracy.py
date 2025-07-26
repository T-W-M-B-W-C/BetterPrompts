#!/usr/bin/env python3
"""
Wave 8: Comprehensive Accuracy Testing
Tests 200+ examples across all 10 intent types with various audiences and complexity levels
"""

import json
import time
import statistics
from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import defaultdict
import requests

@dataclass
class TestCase:
    text: str
    expected_intent: str
    expected_audience: str
    expected_complexity: str
    description: str

@dataclass
class TestResult:
    test_case: TestCase
    actual_intent: str
    actual_audience: str
    actual_complexity: str
    confidence: float
    model_used: str
    latency_ms: float
    passed: bool
    
class ComprehensiveAccuracyTester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.results: List[TestResult] = []
        
    def create_test_cases(self) -> List[TestCase]:
        """Create 200+ diverse test cases across all intent types"""
        test_cases = []
        
        # 1. QUESTION_ANSWERING (25 examples)
        qa_cases = [
            TestCase("What is photosynthesis?", "question_answering", "beginner", "simple", "Basic science question"),
            TestCase("Explain quantum entanglement", "question_answering", "expert", "complex", "Advanced physics"),
            TestCase("How do plants make food?", "question_answering", "child", "simple", "Child-friendly science"),
            TestCase("What are the implications of Gödel's incompleteness theorems?", "question_answering", "expert", "complex", "Mathematical philosophy"),
            TestCase("Why is the sky blue?", "question_answering", "beginner", "simple", "Common question"),
            TestCase("Describe the mechanisms of CRISPR-Cas9 gene editing", "question_answering", "expert", "complex", "Biotechnology"),
            TestCase("What happens when you mix baking soda and vinegar?", "question_answering", "child", "simple", "Simple chemistry"),
            TestCase("How does blockchain consensus work?", "question_answering", "expert", "complex", "Technical question"),
            TestCase("What causes seasons?", "question_answering", "beginner", "medium", "Earth science"),
            TestCase("Explain the Heisenberg uncertainty principle", "question_answering", "expert", "complex", "Quantum mechanics"),
            TestCase("How do airplanes fly?", "question_answering", "beginner", "medium", "Engineering basics"),
            TestCase("What is the difference between ML and AI?", "question_answering", "beginner", "medium", "Tech concepts"),
            TestCase("How do vaccines work?", "question_answering", "beginner", "medium", "Medical science"),
            TestCase("Explain p-value in statistics", "question_answering", "expert", "complex", "Statistical concept"),
            TestCase("What makes thunder?", "question_answering", "child", "simple", "Weather phenomenon"),
            TestCase("How does Wi-Fi work?", "question_answering", "beginner", "medium", "Technology"),
            TestCase("What is dark matter?", "question_answering", "expert", "complex", "Astrophysics"),
            TestCase("Why do we dream?", "question_answering", "beginner", "medium", "Neuroscience"),
            TestCase("How do magnets work?", "question_answering", "child", "simple", "Physics for kids"),
            TestCase("Explain Kubernetes architecture", "question_answering", "expert", "complex", "Cloud computing"),
            TestCase("What causes earthquakes?", "question_answering", "beginner", "medium", "Geology"),
            TestCase("How does photosynthesis convert CO2 to oxygen?", "question_answering", "beginner", "medium", "Biology process"),
            TestCase("What is recursion in programming?", "question_answering", "beginner", "medium", "CS concept"),
            TestCase("Explain the double-slit experiment", "question_answering", "expert", "complex", "Quantum physics"),
            TestCase("How do birds fly?", "question_answering", "child", "simple", "Animal science"),
        ]
        
        # 2. PROBLEM_SOLVING (25 examples)
        ps_cases = [
            TestCase("How can I fix my computer that won't turn on?", "problem_solving", "beginner", "medium", "Tech troubleshooting"),
            TestCase("Design a distributed cache invalidation strategy", "problem_solving", "expert", "complex", "System design"),
            TestCase("My toy is broken, how can I fix it?", "problem_solving", "child", "simple", "Child problem"),
            TestCase("Optimize this SQL query for better performance", "problem_solving", "expert", "complex", "Database optimization"),
            TestCase("How to remove a red wine stain?", "problem_solving", "beginner", "simple", "Household problem"),
            TestCase("Debug this memory leak in production", "problem_solving", "expert", "complex", "Software debugging"),
            TestCase("I lost my homework, what should I do?", "problem_solving", "child", "simple", "School problem"),
            TestCase("Reduce AWS costs by 50% without impacting performance", "problem_solving", "expert", "complex", "Cloud optimization"),
            TestCase("My plant is dying, how can I save it?", "problem_solving", "beginner", "medium", "Gardening issue"),
            TestCase("Implement a lock-free concurrent queue", "problem_solving", "expert", "complex", "Advanced programming"),
            TestCase("How to organize my messy room?", "problem_solving", "child", "simple", "Organization"),
            TestCase("Fix CORS issues in microservices architecture", "problem_solving", "expert", "complex", "Web development"),
            TestCase("My car is making a strange noise", "problem_solving", "beginner", "medium", "Auto troubleshooting"),
            TestCase("Scale Elasticsearch cluster to handle 1TB/day", "problem_solving", "expert", "complex", "Big data"),
            TestCase("How to stop my dog from barking?", "problem_solving", "beginner", "medium", "Pet training"),
            TestCase("Resolve circular dependency in Spring Boot", "problem_solving", "expert", "complex", "Framework issue"),
            TestCase("I can't sleep at night, what can I do?", "problem_solving", "beginner", "medium", "Health issue"),
            TestCase("Optimize React app bundle size", "problem_solving", "expert", "complex", "Frontend optimization"),
            TestCase("My friend is mad at me", "problem_solving", "child", "simple", "Social problem"),
            TestCase("Troubleshoot Kubernetes pod crash loops", "problem_solving", "expert", "complex", "Container orchestration"),
            TestCase("How to save money on groceries?", "problem_solving", "beginner", "simple", "Budget management"),
            TestCase("Debug race condition in multithreaded code", "problem_solving", "expert", "complex", "Concurrency issue"),
            TestCase("My computer is running slowly", "problem_solving", "beginner", "medium", "Performance issue"),
            TestCase("Implement blue-green deployment strategy", "problem_solving", "expert", "complex", "DevOps problem"),
            TestCase("How to make friends at a new school?", "problem_solving", "child", "simple", "Social challenge"),
        ]
        
        # 3. CREATIVE_WRITING (20 examples)
        cw_cases = [
            TestCase("Write a story about a magical forest", "creative_writing", "beginner", "medium", "Fiction prompt"),
            TestCase("Compose a haiku about machine learning", "creative_writing", "expert", "complex", "Technical poetry"),
            TestCase("Tell me a bedtime story about a brave bunny", "creative_writing", "child", "simple", "Children's story"),
            TestCase("Write a dystopian short story with unreliable narrator", "creative_writing", "expert", "complex", "Advanced fiction"),
            TestCase("Create a poem about spring", "creative_writing", "beginner", "simple", "Nature poetry"),
            TestCase("Write a technical blog post about GraphQL", "creative_writing", "expert", "medium", "Technical writing"),
            TestCase("Make up a story about talking animals", "creative_writing", "child", "simple", "Fantasy for kids"),
            TestCase("Draft a compelling product launch email", "creative_writing", "beginner", "medium", "Marketing copy"),
            TestCase("Write a sonnet in iambic pentameter", "creative_writing", "expert", "complex", "Classical poetry"),
            TestCase("Create a superhero origin story", "creative_writing", "beginner", "medium", "Comic narrative"),
            TestCase("Write a children's book about sharing", "creative_writing", "child", "simple", "Educational story"),
            TestCase("Compose a technical whitepaper introduction", "creative_writing", "expert", "complex", "Business writing"),
            TestCase("Write a mystery story opening", "creative_writing", "beginner", "medium", "Genre fiction"),
            TestCase("Create a limerick about coding", "creative_writing", "beginner", "simple", "Humorous poetry"),
            TestCase("Write a sci-fi flash fiction", "creative_writing", "expert", "complex", "Speculative fiction"),
            TestCase("Tell a funny story about a cat", "creative_writing", "child", "simple", "Animal story"),
            TestCase("Write compelling ad copy for SaaS", "creative_writing", "expert", "medium", "Copywriting"),
            TestCase("Create a horror story atmosphere", "creative_writing", "beginner", "medium", "Mood writing"),
            TestCase("Write a fairy tale with a twist", "creative_writing", "beginner", "medium", "Reimagined classic"),
            TestCase("Compose an epic fantasy prologue", "creative_writing", "expert", "complex", "World-building"),
        ]
        
        # 4. CODE_GENERATION (20 examples)
        cg_cases = [
            TestCase("Write a Python function to reverse a string", "code_generation", "beginner", "simple", "Basic algorithm"),
            TestCase("Implement a red-black tree in Rust", "code_generation", "expert", "complex", "Advanced data structure"),
            TestCase("Make a simple calculator in Scratch", "code_generation", "child", "simple", "Visual programming"),
            TestCase("Create a distributed rate limiter using Redis", "code_generation", "expert", "complex", "System design code"),
            TestCase("Write a JavaScript function to sort an array", "code_generation", "beginner", "simple", "Basic sorting"),
            TestCase("Implement RAFT consensus algorithm", "code_generation", "expert", "complex", "Distributed systems"),
            TestCase("Create a React component for a button", "code_generation", "beginner", "medium", "Frontend component"),
            TestCase("Write a SQL query to find duplicates", "code_generation", "beginner", "medium", "Database query"),
            TestCase("Implement LRU cache with O(1) operations", "code_generation", "expert", "complex", "Efficient algorithm"),
            TestCase("Create a simple HTML webpage", "code_generation", "beginner", "simple", "Web basics"),
            TestCase("Write a GraphQL resolver with DataLoader", "code_generation", "expert", "complex", "API development"),
            TestCase("Make a for loop that counts to 10", "code_generation", "child", "simple", "Programming basics"),
            TestCase("Implement WebSocket chat server", "code_generation", "expert", "complex", "Real-time communication"),
            TestCase("Write a regex to validate email", "code_generation", "beginner", "medium", "Pattern matching"),
            TestCase("Create a neural network in PyTorch", "code_generation", "expert", "complex", "Machine learning"),
            TestCase("Write a bash script to backup files", "code_generation", "beginner", "medium", "System scripting"),
            TestCase("Implement B+ tree for database index", "code_generation", "expert", "complex", "Database internals"),
            TestCase("Create a CSS animation", "code_generation", "beginner", "medium", "Web animation"),
            TestCase("Write async/await error handling", "code_generation", "beginner", "medium", "Modern JavaScript"),
            TestCase("Implement lock-free queue in C++", "code_generation", "expert", "complex", "Concurrent programming"),
        ]
        
        # 5. SUMMARIZATION (20 examples)
        sum_cases = [
            TestCase("Summarize this article about climate change", "summarization", "beginner", "medium", "News summary"),
            TestCase("Provide executive summary of quarterly financials", "summarization", "expert", "complex", "Business summary"),
            TestCase("Tell me what this story is about in simple words", "summarization", "child", "simple", "Story summary"),
            TestCase("Synthesize these research papers on quantum computing", "summarization", "expert", "complex", "Academic summary"),
            TestCase("Give me the main points of this email", "summarization", "beginner", "simple", "Email summary"),
            TestCase("Summarize the key findings of this medical study", "summarization", "expert", "complex", "Scientific summary"),
            TestCase("What happened in this chapter?", "summarization", "child", "simple", "Book summary"),
            TestCase("Condense this technical documentation", "summarization", "expert", "medium", "Tech docs summary"),
            TestCase("Summarize this movie plot", "summarization", "beginner", "simple", "Entertainment summary"),
            TestCase("Abstract for this machine learning paper", "summarization", "expert", "complex", "Research abstract"),
            TestCase("Give me the highlights of this sports game", "summarization", "beginner", "simple", "Sports summary"),
            TestCase("Summarize architectural design decisions", "summarization", "expert", "complex", "Technical summary"),
            TestCase("What's the main idea of this paragraph?", "summarization", "child", "simple", "Reading comprehension"),
            TestCase("TL;DR of this Reddit thread", "summarization", "beginner", "simple", "Social media summary"),
            TestCase("Synthesize competing economic theories", "summarization", "expert", "complex", "Academic synthesis"),
            TestCase("Summarize this cooking recipe", "summarization", "beginner", "simple", "Recipe overview"),
            TestCase("Key takeaways from this conference talk", "summarization", "expert", "medium", "Professional summary"),
            TestCase("What did we learn in class today?", "summarization", "child", "simple", "Lesson summary"),
            TestCase("Distill this legal document", "summarization", "expert", "complex", "Legal summary"),
            TestCase("Main points of this how-to guide", "summarization", "beginner", "medium", "Tutorial summary"),
        ]
        
        # 6. TRANSLATION (20 examples)
        tr_cases = [
            TestCase("Translate 'Hello world' to Spanish", "translation", "beginner", "simple", "Basic translation"),
            TestCase("Translate this technical manual to German", "translation", "expert", "complex", "Technical translation"),
            TestCase("How do you say 'thank you' in French?", "translation", "child", "simple", "Simple phrase"),
            TestCase("Translate this legal contract preserving nuances", "translation", "expert", "complex", "Legal translation"),
            TestCase("Convert this to British English", "translation", "beginner", "simple", "Dialect conversion"),
            TestCase("Translate medical terminology accurately", "translation", "expert", "complex", "Medical translation"),
            TestCase("What's 'cat' in different languages?", "translation", "child", "simple", "Word translation"),
            TestCase("Localize this software UI for Japan", "translation", "expert", "complex", "Software localization"),
            TestCase("Translate this recipe to Italian", "translation", "beginner", "medium", "Culinary translation"),
            TestCase("Translate poetry preserving meter and rhyme", "translation", "expert", "complex", "Literary translation"),
            TestCase("How do you say 'I love you' in sign language?", "translation", "beginner", "medium", "Non-verbal translation"),
            TestCase("Translate technical API documentation", "translation", "expert", "complex", "Technical docs translation"),
            TestCase("What does 'bonjour' mean?", "translation", "child", "simple", "Basic vocabulary"),
            TestCase("Translate marketing copy for cultural adaptation", "translation", "expert", "complex", "Marketing localization"),
            TestCase("Convert American to metric units", "translation", "beginner", "simple", "Unit conversion"),
            TestCase("Translate ancient Greek text", "translation", "expert", "complex", "Classical translation"),
            TestCase("Translate this email to Portuguese", "translation", "beginner", "medium", "Business translation"),
            TestCase("What's this emoji mean in words?", "translation", "child", "simple", "Symbol translation"),
            TestCase("Translate scientific paper abstracts", "translation", "expert", "complex", "Academic translation"),
            TestCase("Convert programming comments to English", "translation", "beginner", "medium", "Code documentation"),
        ]
        
        # 7. CONVERSATION (20 examples)
        conv_cases = [
            TestCase("Hi, how are you today?", "conversation", "beginner", "simple", "Casual greeting"),
            TestCase("Let's discuss the implications of AGI on society", "conversation", "expert", "complex", "Deep discussion"),
            TestCase("Can we be friends?", "conversation", "child", "simple", "Friendly chat"),
            TestCase("Debate the merits of different distributed consensus algorithms", "conversation", "expert", "complex", "Technical debate"),
            TestCase("Tell me about your day", "conversation", "beginner", "simple", "Small talk"),
            TestCase("Analyze the philosophical implications of consciousness", "conversation", "expert", "complex", "Philosophy discussion"),
            TestCase("Do you like puppies?", "conversation", "child", "simple", "Kid conversation"),
            TestCase("Let's chat about the weather", "conversation", "beginner", "simple", "Casual topic"),
            TestCase("Discuss microservices vs monoliths", "conversation", "expert", "complex", "Architecture debate"),
            TestCase("What's your favorite color?", "conversation", "child", "simple", "Personal preference"),
            TestCase("How was your weekend?", "conversation", "beginner", "simple", "Weekend chat"),
            TestCase("Examine the ethics of AI decision-making", "conversation", "expert", "complex", "Ethics discussion"),
            TestCase("Want to play a game?", "conversation", "child", "simple", "Play invitation"),
            TestCase("Let's talk about hobbies", "conversation", "beginner", "medium", "Interest discussion"),
            TestCase("Debate quantum supremacy claims", "conversation", "expert", "complex", "Scientific debate"),
            TestCase("What do you think about school?", "conversation", "child", "simple", "School chat"),
            TestCase("Share your thoughts on remote work", "conversation", "beginner", "medium", "Work discussion"),
            TestCase("Analyze geopolitical tensions", "conversation", "expert", "complex", "Politics discussion"),
            TestCase("Nice weather we're having", "conversation", "beginner", "simple", "Weather small talk"),
            TestCase("Discuss the future of humanity", "conversation", "expert", "complex", "Futurism discussion"),
        ]
        
        # 8. TASK_PLANNING (20 examples)
        tp_cases = [
            TestCase("Help me plan a birthday party", "task_planning", "beginner", "medium", "Event planning"),
            TestCase("Design a microservices migration strategy", "task_planning", "expert", "complex", "Technical planning"),
            TestCase("Plan my day at the playground", "task_planning", "child", "simple", "Activity planning"),
            TestCase("Create a disaster recovery plan for our infrastructure", "task_planning", "expert", "complex", "Business continuity"),
            TestCase("Organize my weekly schedule", "task_planning", "beginner", "simple", "Time management"),
            TestCase("Plan a machine learning project roadmap", "task_planning", "expert", "complex", "Project planning"),
            TestCase("Help me pack for vacation", "task_planning", "beginner", "medium", "Travel planning"),
            TestCase("Design a scalable data pipeline architecture", "task_planning", "expert", "complex", "System planning"),
            TestCase("Plan a fun weekend", "task_planning", "child", "simple", "Weekend activities"),
            TestCase("Create a software release plan", "task_planning", "expert", "complex", "Release management"),
            TestCase("Organize my study schedule", "task_planning", "beginner", "medium", "Study planning"),
            TestCase("Plan cloud migration strategy", "task_planning", "expert", "complex", "Infrastructure planning"),
            TestCase("Plan a treasure hunt game", "task_planning", "child", "simple", "Game planning"),
            TestCase("Create a meal prep plan", "task_planning", "beginner", "simple", "Meal planning"),
            TestCase("Design incident response runbook", "task_planning", "expert", "complex", "Operations planning"),
            TestCase("Plan a garden layout", "task_planning", "beginner", "medium", "Garden design"),
            TestCase("Architect a real-time analytics system", "task_planning", "expert", "complex", "System architecture"),
            TestCase("Plan my homework schedule", "task_planning", "child", "simple", "Homework planning"),
            TestCase("Create a fitness routine", "task_planning", "beginner", "medium", "Exercise planning"),
            TestCase("Plan zero-downtime database migration", "task_planning", "expert", "complex", "Database planning"),
        ]
        
        # 9. EXPLANATION (20 examples)
        exp_cases = [
            TestCase("Explain how the internet works", "explanation", "beginner", "medium", "Technology explanation"),
            TestCase("Explain the CAP theorem and its implications", "explanation", "expert", "complex", "Distributed systems theory"),
            TestCase("Explain why we need to brush our teeth", "explanation", "child", "simple", "Health explanation"),
            TestCase("Explain ACID properties in database transactions", "explanation", "expert", "complex", "Database theory"),
            TestCase("Explain how to tie shoelaces", "explanation", "beginner", "simple", "Practical explanation"),
            TestCase("Explain monads in functional programming", "explanation", "expert", "complex", "Programming concept"),
            TestCase("Explain why the sun rises", "explanation", "child", "simple", "Natural phenomenon"),
            TestCase("Explain how credit cards work", "explanation", "beginner", "medium", "Financial explanation"),
            TestCase("Explain Byzantine fault tolerance", "explanation", "expert", "complex", "Distributed computing"),
            TestCase("Explain the water cycle", "explanation", "beginner", "simple", "Science explanation"),
            TestCase("Explain type theory in programming languages", "explanation", "expert", "complex", "Computer science"),
            TestCase("Explain why we have seasons", "explanation", "child", "simple", "Earth science"),
            TestCase("Explain how GPS works", "explanation", "beginner", "medium", "Technology explanation"),
            TestCase("Explain homomorphic encryption", "explanation", "expert", "complex", "Cryptography"),
            TestCase("Explain how plants grow", "explanation", "child", "simple", "Biology basics"),
            TestCase("Explain stock market basics", "explanation", "beginner", "medium", "Finance explanation"),
            TestCase("Explain Turing completeness", "explanation", "expert", "complex", "Computation theory"),
            TestCase("Explain why we sleep", "explanation", "beginner", "simple", "Biology explanation"),
            TestCase("Explain container orchestration", "explanation", "expert", "complex", "DevOps concept"),
            TestCase("Explain how airplanes stay up", "explanation", "child", "simple", "Physics for kids"),
        ]
        
        # 10. GENERAL_ASSISTANCE (20 examples)
        ga_cases = [
            TestCase("I need help with something", "general_assistance", "beginner", "simple", "Vague request"),
            TestCase("Assist with optimizing our CI/CD pipeline", "general_assistance", "expert", "complex", "DevOps help"),
            TestCase("Can you help me?", "general_assistance", "child", "simple", "General help"),
            TestCase("Help me understand this codebase", "general_assistance", "expert", "medium", "Code assistance"),
            TestCase("I'm looking for advice", "general_assistance", "beginner", "simple", "Advice seeking"),
            TestCase("Guide me through system design interview prep", "general_assistance", "expert", "complex", "Career help"),
            TestCase("I need help with my homework", "general_assistance", "child", "simple", "School help"),
            TestCase("Assist with debugging this issue", "general_assistance", "beginner", "medium", "Debug assistance"),
            TestCase("Help optimize our Kubernetes cluster", "general_assistance", "expert", "complex", "Infrastructure help"),
            TestCase("Can you give me some tips?", "general_assistance", "beginner", "simple", "Tips request"),
            TestCase("Assist with architectural decisions", "general_assistance", "expert", "complex", "Architecture help"),
            TestCase("Help me with this", "general_assistance", "child", "simple", "Unspecific help"),
            TestCase("Guide me through this process", "general_assistance", "beginner", "medium", "Process guidance"),
            TestCase("Assist with performance profiling", "general_assistance", "expert", "complex", "Performance help"),
            TestCase("I'm stuck and need help", "general_assistance", "beginner", "simple", "Stuck situation"),
            TestCase("Help me choose the right technology stack", "general_assistance", "expert", "complex", "Tech selection"),
            TestCase("Can you help me learn?", "general_assistance", "child", "simple", "Learning help"),
            TestCase("Provide guidance on best practices", "general_assistance", "beginner", "medium", "Best practices"),
            TestCase("Assist with distributed tracing setup", "general_assistance", "expert", "complex", "Monitoring help"),
            TestCase("Just help me out here", "general_assistance", "beginner", "simple", "Casual help request"),
        ]
        
        # Add ambiguous/edge cases (15 examples)
        edge_cases = [
            TestCase("Tell me about quantum computing and how to implement it", "question_answering", "expert", "complex", "Mixed QA/Code"),
            TestCase("Why doesn't my code work and how do I fix it?", "problem_solving", "beginner", "medium", "Mixed PS/Debug"),
            TestCase("Explain and write a sorting algorithm", "code_generation", "beginner", "medium", "Mixed Explain/Code"),
            TestCase("Plan how to solve this problem", "task_planning", "beginner", "medium", "Mixed Plan/Solve"),
            TestCase("Translate and explain this phrase", "translation", "beginner", "medium", "Mixed Translate/Explain"),
            TestCase("Summarize and critique this article", "summarization", "expert", "complex", "Mixed Summary/Analysis"),
            TestCase("Write a story explaining photosynthesis", "creative_writing", "beginner", "medium", "Mixed Creative/Explain"),
            TestCase("Help me understand and fix this", "general_assistance", "beginner", "medium", "Vague assistance"),
            TestCase("Create a plan to learn programming", "task_planning", "beginner", "medium", "Learning plan"),
            TestCase("Debug this: print('Hello')", "problem_solving", "beginner", "simple", "Trivial debug"),
            TestCase("What do you think about explaining recursion?", "explanation", "beginner", "medium", "Meta explanation"),
            TestCase("How would you solve and code this?", "problem_solving", "beginner", "medium", "Mixed solve/code"),
            TestCase("Analyze and summarize this data", "summarization", "expert", "complex", "Data analysis"),
            TestCase("Let's plan to write a story", "task_planning", "beginner", "medium", "Creative planning"),
            TestCase("Explain how to translate this concept", "explanation", "expert", "complex", "Meta translation"),
        ]
        
        # Combine all test cases
        test_cases.extend(qa_cases)
        test_cases.extend(ps_cases)
        test_cases.extend(cw_cases)
        test_cases.extend(cg_cases)
        test_cases.extend(sum_cases)
        test_cases.extend(tr_cases)
        test_cases.extend(conv_cases)
        test_cases.extend(tp_cases)
        test_cases.extend(exp_cases)
        test_cases.extend(ga_cases)
        test_cases.extend(edge_cases)
        
        return test_cases
    
    def run_single_test(self, test_case: TestCase, user_id: str = "test_user") -> TestResult:
        """Run a single test case against the classifier"""
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/intents/classify",
                json={"text": test_case.text, "user_id": user_id},
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            latency_ms = (time.time() - start_time) * 1000
            
            # Check if results match expected
            intent_match = data["intent"] == test_case.expected_intent
            audience_match = data.get("audience", "").lower() == test_case.expected_audience.lower()
            complexity_match = data.get("complexity", "").lower() == test_case.expected_complexity.lower()
            
            passed = intent_match  # Primary criterion is intent matching
            
            return TestResult(
                test_case=test_case,
                actual_intent=data["intent"],
                actual_audience=data.get("audience", "unknown"),
                actual_complexity=data.get("complexity", "unknown"),
                confidence=data.get("confidence", 0.0),
                model_used=data.get("model_used", "unknown"),
                latency_ms=latency_ms,
                passed=passed
            )
            
        except Exception as e:
            return TestResult(
                test_case=test_case,
                actual_intent="ERROR",
                actual_audience="ERROR",
                actual_complexity="ERROR",
                confidence=0.0,
                model_used="ERROR",
                latency_ms=(time.time() - start_time) * 1000,
                passed=False
            )
    
    def run_all_tests(self, test_cases: List[TestCase]) -> None:
        """Run all test cases and collect results"""
        print(f"Running {len(test_cases)} test cases...")
        
        for i, test_case in enumerate(test_cases):
            if i % 10 == 0:
                print(f"Progress: {i}/{len(test_cases)} ({i/len(test_cases)*100:.1f}%)")
            
            result = self.run_single_test(test_case)
            self.results.append(result)
            
            # Add small delay to avoid overwhelming the service
            time.sleep(0.1)
        
        print(f"Completed {len(test_cases)} tests")
    
    def analyze_results(self) -> Dict:
        """Analyze test results and generate metrics"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        
        # Overall metrics
        overall_accuracy = passed_tests / total_tests if total_tests > 0 else 0
        
        # Per-intent metrics
        intent_metrics = defaultdict(lambda: {"total": 0, "passed": 0, "latencies": []})
        for result in self.results:
            intent = result.test_case.expected_intent
            intent_metrics[intent]["total"] += 1
            if result.passed:
                intent_metrics[intent]["passed"] += 1
            intent_metrics[intent]["latencies"].append(result.latency_ms)
        
        # Calculate per-intent accuracy and latency
        intent_summary = {}
        for intent, metrics in intent_metrics.items():
            accuracy = metrics["passed"] / metrics["total"] if metrics["total"] > 0 else 0
            latencies = metrics["latencies"]
            intent_summary[intent] = {
                "accuracy": accuracy,
                "total_tests": metrics["total"],
                "passed_tests": metrics["passed"],
                "avg_latency_ms": statistics.mean(latencies),
                "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
                "p99_latency_ms": sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0,
            }
        
        # Model usage statistics
        model_usage = defaultdict(int)
        model_latencies = defaultdict(list)
        for result in self.results:
            model = result.model_used
            model_usage[model] += 1
            model_latencies[model].append(result.latency_ms)
        
        model_summary = {}
        for model, count in model_usage.items():
            latencies = model_latencies[model]
            model_summary[model] = {
                "usage_count": count,
                "usage_percentage": count / total_tests if total_tests > 0 else 0,
                "avg_latency_ms": statistics.mean(latencies) if latencies else 0,
                "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
            }
        
        # Audience detection accuracy
        audience_correct = sum(1 for r in self.results 
                             if r.actual_audience.lower() == r.test_case.expected_audience.lower())
        audience_accuracy = audience_correct / total_tests if total_tests > 0 else 0
        
        # Complexity detection accuracy
        complexity_correct = sum(1 for r in self.results 
                               if r.actual_complexity.lower() == r.test_case.expected_complexity.lower())
        complexity_accuracy = complexity_correct / total_tests if total_tests > 0 else 0
        
        # Find failed tests for analysis
        failed_tests = [r for r in self.results if not r.passed]
        
        return {
            "overall_metrics": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "overall_accuracy": overall_accuracy,
                "audience_accuracy": audience_accuracy,
                "complexity_accuracy": complexity_accuracy,
            },
            "intent_metrics": intent_summary,
            "model_metrics": model_summary,
            "failed_tests": [
                {
                    "text": r.test_case.text,
                    "expected": r.test_case.expected_intent,
                    "actual": r.actual_intent,
                    "confidence": r.confidence,
                    "model": r.model_used,
                    "description": r.test_case.description
                }
                for r in failed_tests[:10]  # Show first 10 failures
            ]
        }
    
    def generate_report(self, analysis: Dict) -> str:
        """Generate a comprehensive test report"""
        report = []
        report.append("=" * 80)
        report.append("WAVE 8: COMPREHENSIVE ACCURACY TEST REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Overall metrics
        om = analysis["overall_metrics"]
        report.append("OVERALL METRICS:")
        report.append(f"  Total Tests: {om['total_tests']}")
        report.append(f"  Passed Tests: {om['passed_tests']}")
        report.append(f"  Overall Accuracy: {om['overall_accuracy']:.2%}")
        report.append(f"  Audience Detection Accuracy: {om['audience_accuracy']:.2%}")
        report.append(f"  Complexity Detection Accuracy: {om['complexity_accuracy']:.2%}")
        report.append("")
        
        # Per-intent accuracy
        report.append("PER-INTENT ACCURACY:")
        for intent, metrics in sorted(analysis["intent_metrics"].items()):
            report.append(f"  {intent}:")
            report.append(f"    Accuracy: {metrics['accuracy']:.2%} ({metrics['passed_tests']}/{metrics['total_tests']})")
            report.append(f"    Avg Latency: {metrics['avg_latency_ms']:.1f}ms")
            report.append(f"    P95 Latency: {metrics['p95_latency_ms']:.1f}ms")
            report.append(f"    P99 Latency: {metrics['p99_latency_ms']:.1f}ms")
        report.append("")
        
        # Model usage
        report.append("MODEL USAGE STATISTICS:")
        for model, metrics in sorted(analysis["model_metrics"].items()):
            report.append(f"  {model}:")
            report.append(f"    Usage: {metrics['usage_percentage']:.1%} ({metrics['usage_count']} requests)")
            report.append(f"    Avg Latency: {metrics['avg_latency_ms']:.1f}ms")
            report.append(f"    P95 Latency: {metrics['p95_latency_ms']:.1f}ms")
        report.append("")
        
        # Sample failures
        if analysis["failed_tests"]:
            report.append("SAMPLE FAILED TESTS:")
            for i, failure in enumerate(analysis["failed_tests"], 1):
                report.append(f"  {i}. Text: \"{failure['text']}\"")
                report.append(f"     Expected: {failure['expected']}, Actual: {failure['actual']}")
                report.append(f"     Confidence: {failure['confidence']:.2f}, Model: {failure['model']}")
                report.append(f"     Description: {failure['description']}")
        report.append("")
        
        # Performance vs target
        report.append("PERFORMANCE VS TARGETS:")
        report.append(f"  ✓ Overall Accuracy Target (>90%): {'PASS' if om['overall_accuracy'] >= 0.90 else 'FAIL'} ({om['overall_accuracy']:.2%})")
        report.append(f"  ✓ Audience Detection Target (>92%): {'PASS' if om['audience_accuracy'] >= 0.92 else 'FAIL'} ({om['audience_accuracy']:.2%})")
        report.append(f"  ✓ Complexity Detection Target (>88%): {'PASS' if om['complexity_accuracy'] >= 0.88 else 'FAIL'} ({om['complexity_accuracy']:.2%})")
        
        return "\n".join(report)

def main():
    """Run comprehensive accuracy tests"""
    tester = ComprehensiveAccuracyTester()
    
    # Create test cases
    print("Creating test cases...")
    test_cases = tester.create_test_cases()
    print(f"Created {len(test_cases)} test cases")
    
    # Run tests
    print("\nRunning tests...")
    start_time = time.time()
    tester.run_all_tests(test_cases)
    total_time = time.time() - start_time
    print(f"Total test time: {total_time:.1f} seconds")
    
    # Analyze results
    print("\nAnalyzing results...")
    analysis = tester.analyze_results()
    
    # Generate report
    report = tester.generate_report(analysis)
    print("\n" + report)
    
    # Save detailed results
    with open("accuracy_test_results.json", "w") as f:
        json.dump({
            "test_cases": [
                {
                    "text": tc.text,
                    "expected_intent": tc.expected_intent,
                    "expected_audience": tc.expected_audience,
                    "expected_complexity": tc.expected_complexity,
                    "description": tc.description
                }
                for tc in test_cases
            ],
            "results": [
                {
                    "test": r.test_case.text,
                    "expected": r.test_case.expected_intent,
                    "actual": r.actual_intent,
                    "audience_expected": r.test_case.expected_audience,
                    "audience_actual": r.actual_audience,
                    "complexity_expected": r.test_case.expected_complexity,
                    "complexity_actual": r.actual_complexity,
                    "confidence": r.confidence,
                    "model": r.model_used,
                    "latency_ms": r.latency_ms,
                    "passed": r.passed
                }
                for r in tester.results
            ],
            "analysis": analysis
        }, f, indent=2)
    print("\nDetailed results saved to accuracy_test_results.json")

if __name__ == "__main__":
    main()