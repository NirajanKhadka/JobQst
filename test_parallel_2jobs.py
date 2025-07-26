"""
Test Parallel Processing with 2 Jobs
Demonstrates high-performance job processing optimized for RTX 3080.
"""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

console = Console()

def create_test_jobs():
    """Create 2 test jobs for parallel processing."""
    return [
        {
            'id': 'job_001',
            'title': 'Senior Python Developer',
            'company': 'TechCorp Inc.',
            'description': '''
            We are looking for a Senior Python Developer to join our growing team. 
            The ideal candidate will have 5+ years of experience with Python, Django, 
            FastAPI, and machine learning frameworks like TensorFlow or PyTorch.
            
            Requirements:
            - Bachelor's degree in Computer Science or related field
            - 5+ years of Python development experience
            - Experience with Django, FastAPI, Flask
            - Knowledge of machine learning and data science
            - Experience with AWS, Docker, and Kubernetes
            - Strong problem-solving skills
            
            Benefits:
            - Competitive salary $120,000 - $150,000
            - Health insurance and dental coverage
            - Remote work options
            - Flexible working hours
            - Professional development budget
            - Stock options
            ''',
            'location': 'Toronto, ON',
            'url': 'https://example.com/job/001',
            'status': 'scraped'
        },
        {
            'id': 'job_002', 
            'title': 'Full Stack JavaScript Developer',
            'company': 'WebSolutions Ltd.',
            'description': '''
            Join our dynamic team as a Full Stack JavaScript Developer! We're seeking 
            a mid-level developer with 3+ years of experience in modern web technologies.
            
            Tech Stack:
            - Frontend: React, TypeScript, Next.js
            - Backend: Node.js, Express, MongoDB
            - DevOps: Docker, AWS, CI/CD pipelines
            - Testing: Jest, Cypress
            
            Requirements:
            - 3+ years of JavaScript development
            - Experience with React and Node.js
            - Knowledge of TypeScript
            - Database experience (MongoDB, PostgreSQL)
            - Understanding of RESTful APIs and GraphQL
            
            What we offer:
            - Salary range: $80,000 - $110,000
            - Work from home flexibility
            - Health and dental benefits
            - Annual learning budget
            - Gym membership
            - Catered lunches
            ''',
            'location': 'Vancouver, BC',
            'url': 'https://example.com/job/002', 
            'status': 'scraped'
        }
    ]

async def test_parallel_processing():
    """Test parallel job processing."""
    console.print(Panel(
        "[bold blue]🎯 Parallel Job Processing Test[/bold blue]\n"
        "[cyan]Testing 2 jobs in parallel with RTX 3080 optimization[/cyan]",
        title="AutoJobAgent Parallel Test"
    ))
    
    # Create test jobs
    test_jobs = create_test_jobs()
    console.print(f"[cyan]📝 Created {len(test_jobs)} test jobs[/cyan]")
    
    try:
        # Import and use parallel processor
        from src.ai.parallel_job_processor import get_parallel_processor
        
        # Initialize processor optimized for RTX 3080
        processor = get_parallel_processor(
            max_workers=8,      # Use 8 workers for RTX 3080
            max_concurrent=16   # High concurrency for async processing
        )
        
        console.print("[cyan]🚀 Starting parallel processing...[/cyan]")
        
        # Process jobs using async approach
        result = await processor.process_jobs_async(test_jobs)
        
        # Display results
        console.print(f"\n[bold green]📊 Processing Results[/bold green]")
        
        # Performance metrics table
        metrics_table = Table(title="Performance Metrics")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")
        
        metrics_table.add_row("Jobs Processed", str(result.metrics.jobs_processed))
        metrics_table.add_row("Processing Time", f"{result.metrics.processing_time:.3f}s")
        metrics_table.add_row("Jobs per Second", f"{result.metrics.jobs_per_second:.1f}")
        metrics_table.add_row("Success Rate", f"{result.success_rate:.1%}")
        metrics_table.add_row("Method", result.metrics.method)
        metrics_table.add_row("Workers Used", str(result.metrics.workers_used))
        metrics_table.add_row("GPU Utilization", f"{result.metrics.gpu_utilization:.1f}%")
        
        console.print(metrics_table)
        
        # Job analysis results
        console.print(f"\n[bold blue]📋 Job Analysis Results[/bold blue]")
        
        for i, job_result in enumerate(result.job_results, 1):
            console.print(f"\n[bold cyan]Job {i}: {job_result['title']}[/bold cyan]")
            console.print(f"[yellow]Company:[/yellow] {job_result['company']}")
            console.print(f"[yellow]Experience Level:[/yellow] {job_result.get('experience_level', 'Unknown')}")
            
            skills = job_result.get('required_skills', [])
            if skills:
                console.print(f"[yellow]Required Skills:[/yellow] {', '.join(skills[:5])}")
                if len(skills) > 5:
                    console.print(f"[dim]   ... and {len(skills) - 5} more[/dim]")
            
            console.print(f"[yellow]Compatibility Score:[/yellow] {job_result.get('compatibility_score', 0):.1%}")
            console.print(f"[yellow]Analysis Confidence:[/yellow] {job_result.get('analysis_confidence', 0):.1%}")
            
            benefits = job_result.get('extracted_benefits', [])
            if benefits:
                console.print(f"[yellow]Benefits:[/yellow] {', '.join(benefits[:3])}")
            
            salary_info = job_result.get('salary_info', {})
            if salary_info.get('salary_mentioned'):
                console.print(f"[yellow]Salary:[/yellow] {salary_info.get('salary_range', 'Mentioned')}")
            
            reasoning = job_result.get('analysis_reasoning', '')
            if reasoning:
                console.print(f"[yellow]Analysis:[/yellow] {reasoning}")
        
        # Error reporting
        if result.errors:
            console.print(f"\n[bold red]⚠️ Errors ({len(result.errors)}):[/bold red]")
            for error in result.errors:
                console.print(f"[red]  • {error}[/red]")
        
        # Performance summary
        console.print(f"\n[bold green]🎉 Processing Complete![/bold green]")
        
        if result.metrics.jobs_per_second > 50:
            console.print("[bold green]🏆 EXCELLENT: High-performance processing achieved![/bold green]")
        elif result.metrics.jobs_per_second > 20:
            console.print("[green]🥇 VERY GOOD: Efficient parallel processing[/green]")
        elif result.metrics.jobs_per_second > 10:
            console.print("[yellow]🥈 GOOD: Decent parallel performance[/yellow]")
        else:
            console.print("[yellow]🥉 MODERATE: Basic parallel processing[/yellow]")
        
        console.print(f"[cyan]Processed {result.metrics.jobs_processed} jobs in {result.metrics.processing_time:.3f}s[/cyan]")
        console.print(f"[cyan]Achieved {result.metrics.jobs_per_second:.1f} jobs/sec throughput[/cyan]")
        
        return result
        
    except ImportError as e:
        console.print(f"[red]❌ Import error: {e}[/red]")
        console.print("[yellow]Make sure the parallel processor module is available[/yellow]")
        return None
    except Exception as e:
        console.print(f"[red]❌ Processing failed: {e}[/red]")
        return None

async def main():
    """Main test function."""
    result = await test_parallel_processing()
    
    if result:
        console.print("\n[bold blue]✅ Test completed successfully![/bold blue]")
        console.print("[cyan]This demonstrates high-performance job processing[/cyan]")
        console.print("[cyan]optimized for RTX 3080 systems without CUDA compilation issues.[/cyan]")
    else:
        console.print("\n[bold red]❌ Test failed![/bold red]")

if __name__ == "__main__":
    asyncio.run(main())