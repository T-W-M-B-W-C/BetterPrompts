"""Main data generator for creating synthetic training data."""

import asyncio
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import random

from loguru import logger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from tqdm.asyncio import tqdm

from openai_client import create_openai_client, GenerationRequest
from prompt_templates import IntentType, AudienceLevel, ComplexityLevel, prompt_manager
from diversity_strategies import DiversityStrategy, EdgeCaseGenerator, DiversityMetrics
from data_validator import DataValidator


console = Console()


class TrainingDataGenerator:
    """Orchestrates the generation of synthetic training data."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the generator with all components."""
        self.openai_client = create_openai_client(api_key)
        self.diversity_strategy = DiversityStrategy()
        self.edge_case_generator = EdgeCaseGenerator()
        self.validator = DataValidator()
        
        # Generation statistics
        self.stats = defaultdict(int)
        self.generated_examples = []
        
        # Configuration
        self.config = {
            "examples_per_intent": 1000,
            "edge_cases": 2000,
            "batch_size": 10,
            "temperature": 0.8,
            "max_retries": 3,
            "diversity_threshold": 0.8
        }
    
    async def generate_single_example(
        self,
        intent: IntentType,
        audience: AudienceLevel,
        complexity: ComplexityLevel,
        use_openai: bool = True
    ) -> Dict[str, Any]:
        """Generate a single training example."""
        
        # Get diverse prompt from templates
        prompt_text, metadata = self.diversity_strategy.generate_diverse_prompt(
            intent, audience, complexity
        )
        
        if use_openai:
            # Create generation prompt for OpenAI
            generation_prompt = self._create_generation_prompt(
                intent, audience, complexity, prompt_text
            )
            
            # Generate using OpenAI
            request = GenerationRequest(
                prompt=generation_prompt,
                temperature=self.config["temperature"],
                max_tokens=150,
                model="gpt-3.5-turbo"
            )
            
            try:
                response = await self.openai_client.generate_single(request)
                generated_text = response.text.strip()
                
                # Sometimes OpenAI returns the prompt wrapped in quotes
                if generated_text.startswith('"') and generated_text.endswith('"'):
                    generated_text = generated_text[1:-1]
                
                # Update metadata with OpenAI generation info
                metadata["generation_method"] = "openai"
                metadata["model_used"] = response.model
                metadata["tokens_used"] = response.total_tokens
                
            except Exception as e:
                logger.warning(f"OpenAI generation failed: {e}. Using template.")
                generated_text = prompt_text
                metadata["generation_method"] = "template_fallback"
        else:
            # Use template-generated prompt directly
            generated_text = prompt_text
            metadata["generation_method"] = "template"
        
        # Create the example
        example = {
            "text": generated_text,
            "intent": intent.value,
            "audience": audience.value,
            "complexity": complexity.value,
            "confidence": metadata.get("confidence_expected", 0.85),
            "metadata": metadata,
            "generated_at": datetime.now().isoformat()
        }
        
        # Update statistics
        self.stats["total_generated"] += 1
        self.stats[f"intent_{intent.value}"] += 1
        self.stats[f"audience_{audience.value}"] += 1
        self.stats[f"complexity_{complexity.value}"] += 1
        
        return example
    
    def _create_generation_prompt(
        self,
        intent: IntentType,
        audience: AudienceLevel,
        complexity: ComplexityLevel,
        base_example: str
    ) -> str:
        """Create a prompt for OpenAI to generate variations."""
        
        audience_descriptions = {
            AudienceLevel.CHILD: "a young child (5-10 years old)",
            AudienceLevel.BEGINNER: "someone new to the topic",
            AudienceLevel.INTERMEDIATE: "someone with moderate knowledge",
            AudienceLevel.EXPERT: "an expert in the field",
            AudienceLevel.GENERAL: "a general audience"
        }
        
        complexity_descriptions = {
            ComplexityLevel.SIMPLE: "simple and straightforward",
            ComplexityLevel.MODERATE: "moderately complex with some detail",
            ComplexityLevel.COMPLEX: "complex with multiple parts or requirements"
        }
        
        intent_descriptions = {
            IntentType.QUESTION_ANSWERING: "asking a question that needs an answer",
            IntentType.CREATIVE_WRITING: "requesting creative writing",
            IntentType.CODE_GENERATION: "asking for code to be written",
            IntentType.DATA_ANALYSIS: "requesting data analysis",
            IntentType.REASONING: "asking for logical reasoning or problem solving",
            IntentType.SUMMARIZATION: "asking for a summary of content",
            IntentType.TRANSLATION: "requesting translation between languages",
            IntentType.CONVERSATION: "initiating or continuing a conversation",
            IntentType.TASK_PLANNING: "asking for help planning or organizing tasks",
            IntentType.PROBLEM_SOLVING: "asking for help solving a specific problem"
        }
        
        prompt = f"""Generate a realistic user prompt that is {intent_descriptions[intent]}.

The prompt should be:
- Suitable for {audience_descriptions[audience]}
- {complexity_descriptions[complexity]}
- Natural and realistic, like something a real user would ask
- Different from this example but similar in nature: "{base_example}"

Generate only the user prompt text, nothing else. Do not include any explanation or metadata."""
        
        return prompt
    
    async def generate_intent_examples(
        self,
        intent: IntentType,
        count: int,
        use_openai: bool = True,
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """Generate examples for a specific intent with diversity."""
        examples = []
        
        # Ensure diversity across audiences and complexities
        audiences = list(AudienceLevel)
        complexities = list(ComplexityLevel)
        
        # Distribution strategy
        # 40% general audience, 60% split among others
        audience_weights = {
            AudienceLevel.GENERAL: 0.4,
            AudienceLevel.BEGINNER: 0.2,
            AudienceLevel.INTERMEDIATE: 0.2,
            AudienceLevel.EXPERT: 0.1,
            AudienceLevel.CHILD: 0.1
        }
        
        # 50% moderate, 30% simple, 20% complex
        complexity_weights = {
            ComplexityLevel.MODERATE: 0.5,
            ComplexityLevel.SIMPLE: 0.3,
            ComplexityLevel.COMPLEX: 0.2
        }
        
        for i in range(count):
            # Select audience and complexity based on weights
            audience = random.choices(
                list(audience_weights.keys()),
                weights=list(audience_weights.values())
            )[0]
            
            complexity = random.choices(
                list(complexity_weights.keys()),
                weights=list(complexity_weights.values())
            )[0]
            
            # Generate example
            example = await self.generate_single_example(
                intent, audience, complexity, use_openai
            )
            
            examples.append(example)
            
            if progress_callback:
                progress_callback(i + 1, count)
            
            # Small delay to avoid rate limits
            if use_openai and (i + 1) % 10 == 0:
                await asyncio.sleep(0.5)
        
        return examples
    
    async def generate_edge_cases(
        self,
        count: int,
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """Generate edge cases and ambiguous examples."""
        edge_cases = []
        
        # Types of edge cases to generate
        edge_case_types = [
            "mixed_intent",
            "vague_request",
            "typos_and_errors",
            "extreme_length",
            "multiple_languages",
            "emotional_context"
        ]
        
        for i in range(count):
            # Randomly select edge case type
            case_type = random.choice(edge_case_types)
            
            if case_type == "mixed_intent" and random.random() < 0.5:
                # Generate ambiguous example
                prompt, intents, metadata = self.edge_case_generator.generate_ambiguous_example()
                
                # Pick primary intent
                primary_intent = random.choice(intents) if intents else IntentType.QUESTION_ANSWERING
                
                example = {
                    "text": prompt,
                    "intent": primary_intent.value,
                    "audience": AudienceLevel.GENERAL.value,
                    "complexity": ComplexityLevel.MODERATE.value,
                    "confidence": random.uniform(0.4, 0.7),  # Lower confidence for ambiguous
                    "metadata": {
                        **metadata,
                        "is_edge_case": True,
                        "generation_method": "edge_case_generator"
                    },
                    "generated_at": datetime.now().isoformat()
                }
            else:
                # Generate regular edge case
                prompt, intent, metadata = self.edge_case_generator.generate_edge_case(case_type)
                
                # Assign intent if not provided
                if intent is None:
                    intent = random.choice(list(IntentType))
                
                example = {
                    "text": prompt,
                    "intent": intent.value if isinstance(intent, IntentType) else intent,
                    "audience": AudienceLevel.GENERAL.value,
                    "complexity": ComplexityLevel.MODERATE.value,
                    "confidence": random.uniform(0.3, 0.8),
                    "metadata": {
                        **metadata,
                        "is_edge_case": True,
                        "generation_method": "edge_case_generator"
                    },
                    "generated_at": datetime.now().isoformat()
                }
            
            edge_cases.append(example)
            
            if progress_callback:
                progress_callback(i + 1, count)
            
            # Update statistics
            self.stats["edge_cases_generated"] += 1
        
        return edge_cases
    
    async def generate_full_dataset(
        self,
        examples_per_intent: int = 1000,
        edge_case_count: int = 2000,
        use_openai: bool = True,
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Generate the complete training dataset."""
        console.print("[bold blue]Starting synthetic data generation...[/bold blue]")
        
        all_examples = []
        
        # Generate examples for each intent
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            # Create main task
            main_task = progress.add_task(
                "[cyan]Generating training data...", 
                total=len(IntentType) + 1  # +1 for edge cases
            )
            
            # Generate for each intent
            for intent in IntentType:
                intent_task = progress.add_task(
                    f"[green]Generating {intent.value} examples...",
                    total=examples_per_intent
                )
                
                # Progress callback
                def update_progress(current, total):
                    progress.update(intent_task, completed=current)
                
                # Generate examples
                examples = await self.generate_intent_examples(
                    intent,
                    examples_per_intent,
                    use_openai,
                    update_progress
                )
                
                all_examples.extend(examples)
                progress.update(main_task, advance=1)
                
                # Log progress
                logger.info(f"Generated {len(examples)} examples for {intent.value}")
            
            # Generate edge cases
            edge_task = progress.add_task(
                "[yellow]Generating edge cases...",
                total=edge_case_count
            )
            
            def update_edge_progress(current, total):
                progress.update(edge_task, completed=current)
            
            edge_cases = await self.generate_edge_cases(
                edge_case_count,
                update_edge_progress
            )
            
            all_examples.extend(edge_cases)
            progress.update(main_task, advance=1)
        
        # Shuffle examples
        random.shuffle(all_examples)
        
        # Calculate diversity metrics
        diversity_metrics = self.diversity_strategy.calculate_diversity_metrics(all_examples)
        
        # Create final dataset
        dataset = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_examples": len(all_examples),
                "config": {
                    "examples_per_intent": examples_per_intent,
                    "edge_cases": edge_case_count,
                    "use_openai": use_openai,
                    "temperature": self.config["temperature"]
                },
                "statistics": dict(self.stats),
                "diversity_metrics": {
                    "audience_distribution": diversity_metrics.audience_distribution,
                    "complexity_distribution": diversity_metrics.complexity_distribution,
                    "length_distribution": diversity_metrics.length_distribution,
                    "uniqueness_score": diversity_metrics.uniqueness_score,
                    "topic_coverage": diversity_metrics.topic_coverage,
                    "style_variety": diversity_metrics.style_variety
                }
            },
            "examples": all_examples
        }
        
        # Validate the dataset
        validation_result = self.validator.validate_dataset(dataset)
        
        if not validation_result.is_valid:
            console.print("[bold red]Warning: Dataset validation failed![/bold red]")
            console.print(f"Errors: {len(validation_result.errors)}")
            console.print(f"Warnings: {len(validation_result.warnings)}")
        else:
            console.print("[bold green]Dataset validation passed![/bold green]")
        
        # Save to file if path provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, indent=2, ensure_ascii=False)
            console.print(f"[bold green]Dataset saved to: {output_path}[/bold green]")
            
            # Save validation report
            report_path = output_path.with_suffix('.validation_report.txt')
            self.validator.generate_validation_report(validation_result, report_path)
        
        # Print summary
        self._print_summary(dataset, diversity_metrics, validation_result)
        
        return dataset
    
    def _print_summary(
        self,
        dataset: Dict[str, Any],
        diversity_metrics: DiversityMetrics,
        validation_result
    ):
        """Print generation summary."""
        console.print("\n[bold cyan]Generation Summary:[/bold cyan]")
        console.print(f"Total examples generated: {dataset['metadata']['total_examples']}")
        console.print(f"Valid examples: {validation_result.valid_examples}")
        console.print(f"Invalid examples: {validation_result.invalid_examples}")
        
        console.print("\n[bold cyan]Intent Distribution:[/bold cyan]")
        intent_counts = defaultdict(int)
        for example in dataset['examples']:
            intent_counts[example['intent']] += 1
        
        for intent, count in sorted(intent_counts.items()):
            console.print(f"  {intent}: {count}")
        
        console.print("\n[bold cyan]Diversity Metrics:[/bold cyan]")
        console.print(f"  Uniqueness score: {diversity_metrics.uniqueness_score:.2f}")
        console.print(f"  Topic coverage: {diversity_metrics.topic_coverage:.2f}")
        console.print(f"  Style variety: {diversity_metrics.style_variety:.2f}")
        
        console.print("\n[bold cyan]Audience Distribution:[/bold cyan]")
        for audience, count in diversity_metrics.audience_distribution.items():
            console.print(f"  {audience.value}: {count}")
        
        console.print("\n[bold cyan]Complexity Distribution:[/bold cyan]")
        for complexity, count in diversity_metrics.complexity_distribution.items():
            console.print(f"  {complexity.value}: {count}")


# Example usage
async def main():
    """Example usage of the data generator."""
    generator = TrainingDataGenerator()
    
    # Generate small test dataset
    dataset = await generator.generate_full_dataset(
        examples_per_intent=10,  # Small for testing
        edge_case_count=20,
        use_openai=False,  # Use templates only for testing
        output_path=Path("test_training_data.json")
    )
    
    console.print(f"\n[bold green]Generated {len(dataset['examples'])} examples![/bold green]")


if __name__ == "__main__":
    asyncio.run(main())