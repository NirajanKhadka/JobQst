"""
Comparison Test: No AI vs AI Processing
Shows the difference between fast parallel processing and GPU AI processing.
"""

import asyncio
import time
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Import job fetcher and job data class
from test_real_database_benchmarks import RealDatabaseJobFetcher, RealJobData

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


console = Console()

# Fetch 10 real jobs from the database (profile Nirajan is represented by the default user profile in processors)
async def fetch_real_jobs_from_db(limit: int = 10):
    fetcher = RealDatabaseJobFetcher(db_path="data/jobs.db")
    jobs = await fetcher.fetch_real_jobs(limit=limit)
    if not jobs:
        console.print("[red]❌ No jobs found in database. Please ensure jobs.db exists and is populated.[/red]")
    return jobs



async def test_no_ai_processing(jobs):
    """Test fast parallel processing without AI on real jobs."""
    console.print("[cyan]🚀 Testing Fast Parallel Processing (No AI) on real jobs...[/cyan]")
    try:
        from src.ai.parallel_job_processor import get_parallel_processor
        processor = get_parallel_processor(max_concurrent=16)
        start_time = time.time()
        result = await processor.process_jobs_async(jobs)
        processing_time = time.time() - start_time
        # Aggregate results for display
        job_results = result.job_results
        # Use the first job for sample details
        job_result = job_results[0] if job_results else {}
        return {
            'method': 'Fast Parallel (No AI)',
            'processing_time': processing_time,
            'jobs_per_second': result.metrics.jobs_per_second,
            'required_skills': job_result.get('required_skills', []),
            'experience_level': job_result.get('experience_level', 'Unknown'),
            'compatibility_score': job_result.get('compatibility_score', 0),
            'analysis_confidence': job_result.get('analysis_confidence', 0),
            'gpu_usage': 'None (CPU only)',
            'dependencies': 'Python standard library',
            'complexity': 'Simple',
            'num_jobs': len(jobs)
        }
    except Exception as e:
        console.print(f"[red]❌ No AI test failed: {e}[/red]")
        return None

async def test_ai_processing(jobs):
    """Test GPU AI processing on real jobs."""
    console.print("[cyan]🤖 Testing GPU AI Processing on real jobs...[/cyan]")
    try:
        from src.ai.gpu_job_processor import get_gpu_processor
        processor = get_gpu_processor()
        start_time = time.time()
        result = await processor.process_jobs_gpu_async(jobs)
        processing_time = time.time() - start_time
        job_results = result.job_results
        job_result = job_results[0] if job_results else {}
        return {
            'method': 'GPU AI Processing',
            'processing_time': processing_time,
            'jobs_per_second': result.metrics.jobs_per_second,
            'required_skills': job_result.get('required_skills', []),
            'experience_level': job_result.get('experience_level', 'Unknown'),
            'compatibility_score': job_result.get('compatibility_score', 0),
            'analysis_confidence': job_result.get('analysis_confidence', 0),
            'gpu_usage': f'{result.metrics.gpu_memory_used_mb:.0f}MB VRAM',
            'dependencies': 'Transformers, PyTorch, CUDA',
            'complexity': 'Complex',
            'num_jobs': len(jobs)
        }
    except Exception as e:
        console.print(f"[red]❌ AI test failed: {e}[/red]")
        return None

def display_comparison(no_ai_result, ai_result):
    """Display side-by-side comparison."""
    console.print("\n[bold green]📊 Detailed Comparison Results[/bold green]")
    
    # Performance comparison table
    perf_table = Table(title="Performance Comparison")
    perf_table.add_column("Metric", style="cyan")
    perf_table.add_column("No AI (Fast)", style="yellow")
    perf_table.add_column("AI (Smart)", style="green")
    perf_table.add_column("Winner", style="bold")
    
    if no_ai_result and ai_result:
        # Processing speed
        no_ai_speed = no_ai_result['jobs_per_second']
        ai_speed = ai_result['jobs_per_second']
        speed_winner = "No AI" if no_ai_speed > ai_speed else "AI"
        
        perf_table.add_row(
            "Jobs per Second",
            f"{no_ai_speed:.1f}",
            f"{ai_speed:.1f}",
            speed_winner
        )
        
        perf_table.add_row(
            "Processing Time",
            f"{no_ai_result['processing_time']:.3f}s",
            f"{ai_result['processing_time']:.3f}s",
            "No AI" if no_ai_result['processing_time'] < ai_result['processing_time'] else "AI"
        )
        
        perf_table.add_row(
            "GPU Usage",
            no_ai_result['gpu_usage'],
            ai_result['gpu_usage'],
            "Depends on needs"
        )
        
        perf_table.add_row(
            "Dependencies",
            no_ai_result['dependencies'],
            ai_result['dependencies'],
            "No AI (simpler)"
        )
        
        perf_table.add_row(
            "Complexity",
            no_ai_result['complexity'],
            ai_result['complexity'],
            "No AI (simpler)"
        )
        
        console.print(perf_table)
        
        # Analysis quality comparison
        quality_table = Table(title="Analysis Quality Comparison")
        quality_table.add_column("Aspect", style="cyan")
        quality_table.add_column("No AI Result", style="yellow")
        quality_table.add_column("AI Result", style="green")
        
        quality_table.add_row(
            "Skills Found",
            f"{len(no_ai_result['required_skills'])} skills",
            f"{len(ai_result['required_skills'])} skills"
        )
        
        quality_table.add_row(
            "Skills List",
            ", ".join(no_ai_result['required_skills'][:4]),
            ", ".join(ai_result['required_skills'][:4])
        )
        
        quality_table.add_row(
            "Experience Level",
            no_ai_result['experience_level'],
            ai_result['experience_level']
        )
        
        quality_table.add_row(
            "Compatibility Score",
            f"{no_ai_result['compatibility_score']:.1%}",
            f"{ai_result['compatibility_score']:.1%}"
        )
        
        quality_table.add_row(
            "Confidence",
            f"{no_ai_result['analysis_confidence']:.1%}",
            f"{ai_result['analysis_confidence']:.1%}"
        )
        
        console.print(quality_table)
        
        # Recommendations
        console.print("\n[bold blue]💡 Recommendations[/bold blue]")
        
        if no_ai_speed > ai_speed * 1.5:
            console.print("[yellow]🚀 For SPEED: Use No AI approach[/yellow]")
            console.print("[dim]   - 2x+ faster processing[/dim]")
            console.print("[dim]   - Simpler deployment[/dim]")
            console.print("[dim]   - Lower resource usage[/dim]")
        
        if len(ai_result['required_skills']) > len(no_ai_result['required_skills']):
            console.print("[green]🧠 For ACCURACY: Use AI approach[/green]")
            console.print("[dim]   - Better skill detection[/dim]")
            console.print("[dim]   - Semantic understanding[/dim]")
            console.print("[dim]   - Higher confidence scores[/dim]")
        
        console.print("\n[cyan]🎯 Choose based on your priorities:[/cyan]")
        console.print("[cyan]• Need maximum speed? → Use No AI[/cyan]")
        console.print("[cyan]• Need best accuracy? → Use AI[/cyan]")
        console.print("[cyan]• Want simplicity? → Use No AI[/cyan]")
        console.print("[cyan]• Have RTX 3080? → Consider AI[/cyan]")


async def main():
    """Main comparison test using 10 real jobs from the database."""
    console.print(Panel(
        "[bold blue]🔍 No AI vs AI Comparison Test[/bold blue]\n"
        "[cyan]Testing both approaches on 10 real jobs from the database[/cyan]",
        title="Processing Method Comparison"
    ))

    # Fetch 10 real jobs from the database
    jobs = await fetch_real_jobs_from_db(limit=10)
    if not jobs:
        return

    # Test both approaches
    no_ai_result = await test_no_ai_processing(jobs)
    ai_result = await test_ai_processing(jobs)

    # Display comparison
    if no_ai_result or ai_result:
        display_comparison(no_ai_result, ai_result)
    else:
        console.print("[red]❌ Both tests failed[/red]")

    console.print("\n[bold green]✅ Comparison complete![/bold green]")
    console.print("[cyan]You can use either approach based on your needs.[/cyan]")

if __name__ == "__main__":
    asyncio.run(main())