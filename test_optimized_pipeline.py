#!/usr/bin/env python3
"""
Test script for the optimized job processing pipeline.
Tests the new components: OptimizedJobQueue, DescriptionFetcherOrchestrator, and JobProcessorOrchestrator.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.table import Table

console = Console()


async def test_optimized_job_queue():
    """Test the OptimizedJobQueue functionality."""
    console.print("[bold blue]🧪 Testing OptimizedJobQueue...[/bold blue]")
    
    try:
        from src.pipeline.optimized_job_queue import OptimizedJobQueue
        
        # Create queue
        queue = OptimizedJobQueue("test_queue", max_size=100)
        await queue.start()
        
        # Test enqueue
        test_job = {"id": "test_1", "title": "Test Job", "url": "https://example.com"}
        success = await queue.enqueue_job(test_job, priority=1)
        
        if success:
            console.print("[green]✅ Enqueue test passed[/green]")
        else:
            console.print("[red]❌ Enqueue test failed[/red]")
            return False
        
        # Test dequeue
        job = await queue.dequeue_job(timeout=5)
        if job and job.get("id") == "test_1":
            console.print("[green]✅ Dequeue test passed[/green]")
        else:
            console.print("[red]❌ Dequeue test failed[/red]")
            return False
        
        # Test stats
        stats = await queue.get_queue_stats()
        if stats and "queue_name" in stats:
            console.print("[green]✅ Stats test passed[/green]")
        else:
            console.print("[red]❌ Stats test failed[/red]")
            return False
        
        # Cleanup
        await queue.stop()
        console.print("[green]✅ OptimizedJobQueue tests completed successfully[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ OptimizedJobQueue test failed: {e}[/red]")
        return False


async def test_description_fetcher_orchestrator():
    """Test the DescriptionFetcherOrchestrator functionality."""
    console.print("[bold blue]🧪 Testing DescriptionFetcherOrchestrator...[/bold blue]")
    
    try:
        from src.orchestration.description_fetcher_orchestrator import DescriptionFetcherOrchestrator
        
        # Create orchestrator with minimal workers for testing
        orchestrator = DescriptionFetcherOrchestrator("test_profile", num_workers=2)
        
        # Test initialization
        if orchestrator.num_workers == 2:
            console.print("[green]✅ Initialization test passed[/green]")
        else:
            console.print("[red]❌ Initialization test failed[/red]")
            return False
        
        # Test stats
        stats = await orchestrator.get_orchestrator_stats()
        if stats and "orchestrator_name" in stats:
            console.print("[green]✅ Stats test passed[/green]")
        else:
            console.print("[red]❌ Stats test failed[/red]")
            return False
        
        console.print("[green]✅ DescriptionFetcherOrchestrator tests completed successfully[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ DescriptionFetcherOrchestrator test failed: {e}[/red]")
        return False


async def test_job_processor_orchestrator():
    """Test the JobProcessorOrchestrator functionality."""
    console.print("[bold blue]🧪 Testing JobProcessorOrchestrator...[/bold blue]")
    
    try:
        from src.orchestration.job_processor_orchestrator import JobProcessorOrchestrator
        
        # Create orchestrator
        orchestrator = JobProcessorOrchestrator("test_profile", batch_size=5)
        
        # Test initialization
        if orchestrator.batch_size == 5:
            console.print("[green]✅ Initialization test passed[/green]")
        else:
            console.print("[red]❌ Initialization test failed[/red]")
            return False
        
        # Test stats
        stats = await orchestrator.get_orchestrator_stats()
        if stats and "orchestrator_name" in stats:
            console.print("[green]✅ Stats test passed[/green]")
        else:
            console.print("[red]❌ Stats test failed[/red]")
            return False
        
        console.print("[green]✅ JobProcessorOrchestrator tests completed successfully[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ JobProcessorOrchestrator test failed: {e}[/red]")
        return False


async def test_configuration():
    """Test the configuration file loading."""
    console.print("[bold blue]🧪 Testing Configuration...[/bold blue]")
    
    try:
        config_path = Path("config/optimized_pipeline_config.json")
        
        if config_path.exists():
            console.print("[green]✅ Configuration file exists[/green]")
            
            # Test JSON parsing
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            if "description_fetcher" in config and "job_processor" in config:
                console.print("[green]✅ Configuration parsing test passed[/green]")
                return True
            else:
                console.print("[red]❌ Configuration structure test failed[/red]")
                return False
        else:
            console.print("[red]❌ Configuration file not found[/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]❌ Configuration test failed: {e}[/red]")
        return False


async def run_all_tests():
    """Run all tests for the optimized pipeline."""
    console.print("[bold green]🚀 Starting Optimized Pipeline Tests[/bold green]")
    console.print("=" * 60)
    
    test_results = []
    
    # Test 1: OptimizedJobQueue
    result1 = await test_optimized_job_queue()
    test_results.append(("OptimizedJobQueue", result1))
    
    # Test 2: DescriptionFetcherOrchestrator
    result2 = await test_description_fetcher_orchestrator()
    test_results.append(("DescriptionFetcherOrchestrator", result2))
    
    # Test 3: JobProcessorOrchestrator
    result3 = await test_job_processor_orchestrator()
    test_results.append(("JobProcessorOrchestrator", result3))
    
    # Test 4: Configuration
    result4 = await test_configuration()
    test_results.append(("Configuration", result4))
    
    # Display results
    console.print("\n[bold blue]📊 Test Results Summary[/bold blue]")
    console.print("=" * 60)
    
    table = Table()
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    
    for component, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        table.add_row(component, status)
    
    console.print(table)
    
    # Overall result
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    console.print(f"\n[bold]Overall: {passed}/{total} tests passed[/bold]")
    
    if passed == total:
        console.print("[bold green]🎉 All tests passed! Optimized pipeline is ready.[/bold green]")
        return True
    else:
        console.print("[bold red]⚠️ Some tests failed. Please check the implementation.[/bold red]")
        return False


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())
    
    if success:
        console.print("\n[bold green]✅ Optimized pipeline implementation is complete and working![/bold green]")
        console.print("[cyan]💡 You can now use the new optimized pipeline with:[/cyan]")
        console.print("[cyan]   python main.py Nirajan --action process-jobs[/cyan]")
    else:
        console.print("\n[bold red]❌ Some issues found. Please fix before using in production.[/bold red]")
        sys.exit(1) 