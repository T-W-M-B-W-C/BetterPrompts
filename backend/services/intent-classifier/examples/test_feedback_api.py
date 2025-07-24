#!/usr/bin/env python3
"""Manual test script for the feedback API endpoint."""

import asyncio
import httpx
from rich import print
from rich.console import Console
from datetime import datetime

console = Console()

BASE_URL = "http://localhost:8001"


async def test_feedback_flow():
    """Test the complete feedback flow."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        console.print("[bold blue]Testing Intent Classifier Feedback API[/bold blue]\n")
        
        # Step 1: Classify a prompt
        test_prompt = "How do I implement a REST API in Python?"
        console.print(f"[yellow]1. Classifying prompt:[/yellow] '{test_prompt}'")
        
        classify_response = await client.post(
            f"{BASE_URL}/api/v1/intents/classify",
            json={"text": test_prompt}
        )
        
        if classify_response.status_code == 200:
            result = classify_response.json()
            console.print("[green]✓ Classification successful:[/green]")
            console.print(f"  - Intent: [cyan]{result['intent']}[/cyan]")
            console.print(f"  - Confidence: [cyan]{result['confidence']:.2f}[/cyan]")
            console.print(f"  - Complexity: [cyan]{result['complexity']}[/cyan]")
            console.print(f"  - Techniques: [cyan]{', '.join(result['suggested_techniques'])}[/cyan]")
        else:
            console.print(f"[red]✗ Classification failed: {classify_response.status_code}[/red]")
            return
        
        # Step 2: Submit correction feedback
        console.print("\n[yellow]2. Submitting correction feedback[/yellow]")
        
        feedback_data = {
            "text": test_prompt,
            "original_intent": result["intent"],
            "correct_intent": "code_generation",  # Correcting the intent
            "original_confidence": result["confidence"],
            "correct_complexity": "moderate",
            "correct_techniques": ["few_shot", "chain_of_thought", "code_examples"],
            "feedback_type": "correction",
            "user_id": "test_user_123"
        }
        
        feedback_response = await client.post(
            f"{BASE_URL}/api/v1/intents/feedback",
            json=feedback_data
        )
        
        if feedback_response.status_code == 200:
            feedback_result = feedback_response.json()
            console.print("[green]✓ Feedback submitted successfully:[/green]")
            console.print(f"  - Feedback ID: [cyan]{feedback_result['feedback_id']}[/cyan]")
            console.print(f"  - Cache Updated: [cyan]{feedback_result['cache_updated']}[/cyan]")
            console.print(f"  - Message: [cyan]{feedback_result['message']}[/cyan]")
        else:
            console.print(f"[red]✗ Feedback submission failed: {feedback_response.status_code}[/red]")
            return
        
        # Step 3: Re-classify to see if cache was updated
        console.print("\n[yellow]3. Re-classifying to check cache update[/yellow]")
        
        reclassify_response = await client.post(
            f"{BASE_URL}/api/v1/intents/classify",
            json={"text": test_prompt}
        )
        
        if reclassify_response.status_code == 200:
            updated_result = reclassify_response.json()
            console.print("[green]✓ Re-classification successful:[/green]")
            console.print(f"  - Intent: [cyan]{updated_result['intent']}[/cyan] (was: {result['intent']})")
            console.print(f"  - Confidence: [cyan]{updated_result['confidence']:.2f}[/cyan]")
            console.print(f"  - Complexity: [cyan]{updated_result['complexity']}[/cyan]")
            console.print(f"  - Techniques: [cyan]{', '.join(updated_result['suggested_techniques'])}[/cyan]")
            
            # Check if feedback was applied
            if updated_result['intent'] == feedback_data['correct_intent']:
                console.print("\n[green]✓ Feedback was successfully applied to cache![/green]")
            else:
                console.print("\n[yellow]ℹ Cache may not have been updated (caching might be disabled)[/yellow]")
        
        # Step 4: Get feedback statistics
        console.print("\n[yellow]4. Getting feedback statistics[/yellow]")
        
        stats_response = await client.get(f"{BASE_URL}/api/v1/intents/feedback/stats")
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            console.print("[green]✓ Feedback statistics:[/green]")
            console.print(f"  - Pending Feedback: [cyan]{stats['total_pending_feedback']}[/cyan]")
            console.print(f"  - Cache Enabled: [cyan]{stats['cache_enabled']}[/cyan]")
            console.print(f"  - Cache TTL: [cyan]{stats['cache_ttl_hours']} hours[/cyan]")
            
            if 'feedback_types' in stats:
                console.print(f"  - Corrections: [cyan]{stats['feedback_types'].get('corrections', 0)}[/cyan]")
                console.print(f"  - Confirmations: [cyan]{stats['feedback_types'].get('confirmations', 0)}[/cyan]")


async def test_batch_feedback():
    """Test submitting multiple feedback entries."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        console.print("\n[bold blue]Testing Batch Feedback Submission[/bold blue]\n")
        
        test_cases = [
            {
                "text": "Write a sorting algorithm",
                "original_intent": "question_answering",
                "correct_intent": "code_generation",
                "feedback_type": "correction"
            },
            {
                "text": "Explain machine learning concepts",
                "original_intent": "question_answering",
                "correct_intent": "education",
                "feedback_type": "correction"
            },
            {
                "text": "Translate this to French",
                "original_intent": "translation",
                "correct_intent": "translation",
                "feedback_type": "confirmation"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            console.print(f"[yellow]Submitting feedback {i}/{len(test_cases)}[/yellow]")
            
            feedback_data = {
                **test_case,
                "original_confidence": 0.8,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = await client.post(
                f"{BASE_URL}/api/v1/intents/feedback",
                json=feedback_data
            )
            
            if response.status_code == 200:
                result = response.json()
                console.print(f"[green]✓ Feedback {i} submitted: {result['feedback_id']}[/green]")
            else:
                console.print(f"[red]✗ Feedback {i} failed: {response.status_code}[/red]")


async def main():
    """Run all tests."""
    try:
        # Check service health first
        async with httpx.AsyncClient() as client:
            health = await client.get(f"{BASE_URL}/health")
            if health.status_code != 200:
                console.print("[red]Service is not healthy! Make sure intent-classifier is running.[/red]")
                return
        
        # Run tests
        await test_feedback_flow()
        await test_batch_feedback()
        
        console.print("\n[bold green]All tests completed![/bold green]")
        
    except httpx.ConnectError:
        console.print("[red]Cannot connect to service. Make sure it's running on http://localhost:8001[/red]")
    except Exception as e:
        console.print(f"[red]Test failed: {e}[/red]")


if __name__ == "__main__":
    asyncio.run(main())