"""
Real GPU Processing Test with 2 Jobs
Tests actual GPU acceleration using Transformers + RTX 3080.
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
    """Create 2 test jobs for GPU processing."""
    return [
        {
            'id': 'gpu_job_001',
            'title': 'Senior Machine Learning Engineer',
            'company': 'AI Innovations Corp',
            'description': '''
            We are seeking a Senior Machine Learning Engineer to join our cutting-edge AI team.
            The ideal candidate will have extensive experience with deep learning, neural networks,
            and large-scale ML systems.
            
            Key Responsibilities:
            - Design and implement machine learning models using TensorFlow and PyTorch
            - Work with large datasets and distributed computing systems
            - Optimize model performance and deployment pipelines
            - Collaborate with data scientists and software engineers
            
            Requirements:
            - PhD or Master's in Computer Science, Machine Learning, or related field
            - 7+ years of experience in machine learning and AI
            - Expert knowledge of Python, TensorFlow, PyTorch, and scikit-learn
            - Experience with cloud platforms (AWS, GCP, Azure)
            - Strong background in statistics and mathematics
            - Experience with MLOps and model deployment
            
            Benefits:
            - Competitive salary $150,000 - $200,000
            - Equity package and stock options
            - Comprehensive health insurance
            - Remote work flexibility
            - Annual conference and learning budget
            - State-of-the-art GPU workstations
            ''',
            'location': 'San Francisco, CA (Remote OK)',
            'url': 'https://example.com/gpu-job/001',
            'status': 'scraped'
        },
        {
            'id': 'gpu_job_002',
            'title': 'Full Stack Developer - React & Node.js',
            'company': 'WebTech Solutions',
            'description': '''
            Join our dynamic development team as a Full Stack Developer! We're building
            next-generation web applications using modern JavaScript technologies.
            
            What you'll do:
            - Develop responsive web applications using React and TypeScript
            - Build scalable backend APIs with Node.js and Express
            - Work with databases (PostgreSQL, MongoDB)
            - Implement CI/CD pipelines and DevOps practices
            - Collaborate in an Agile development environment
            
            Requirements:
            - Bachelor's degree in Computer Science or equivalent experience
            - 4+ years of JavaScript development experience
            - Proficiency in React, Node.js, and TypeScript
            - Experience with SQL and NoSQL databases
            - Knowledge of Docker, Kubernetes, and cloud services
            - Understanding of RESTful APIs and GraphQL
            
            What we offer:
            - Salary range: $90,000 - $130,000
            - Flexible working hours and remote options
            - Health, dental, and vision insurance
            - Professional development opportunities
            - Modern tech stack and tools
            - Collaborative and innovative work environment
            ''',
            'location': 'Austin, TX',
            'url': 'https://example.com/gpu-job/002',
            'status': 'scraped'
        }
    ]

async def test_gpu_processing():
    """Test real GPU processing with Transformers."""
    console.print(Panel(
        "[bold blue]🎯 Real GPU Processing Test[/bold blue]\n"
        "[cyan]Using Transformers + RTX 3080 for actual AI processing[/cyan]",
        title="GPU-Accelerated Job Analysis"
    ))
    
    # Create test jobs
    test_jobs = create_test_jobs()
    console.print(f"[cyan]📝 Created {len(test_jobs)} test jobs for GPU processing[/cyan]")
    
    try:
        # Import GPU processor
        from src.ai.gpu_job_processor import get_gpu_processor
        
        console.print("[cyan]🚀 Initializing GPU processor with Transformers...[/cyan]")
        
        # Initialize GPU processor
        processor = get_gpu_processor(
            model_name="distilbert-base-uncased",  # Fast BERT model
            batch_size=8  # Optimized for RTX 3080
        )
        
        console.print(f"[green]✅ GPU processor initialized on {processor.device}[/green]")
        
        # Process jobs using real GPU acceleration
        console.print("[cyan]⚡ Processing jobs with GPU acceleration...[/cyan]")
        result = await processor.process_jobs_gpu_async(test_jobs)
        
        # Display results
        console.print(f"\n[bold green]📊 GPU Processing Results[/bold green]")
        
        # Performance metrics table
        metrics_table = Table(title="GPU Performance Metrics")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")
        
        metrics_table.add_row("Jobs Processed", str(result.metrics.jobs_processed))
        metrics_table.add_row("Processing Time", f"{result.metrics.processing_time:.3f}s")
        metrics_table.add_row("Jobs per Second", f"{result.metrics.jobs_per_second:.1f}")
        metrics_table.add_row("GPU Utilization", f"{result.metrics.gpu_utilization:.1f}%")
        metrics_table.add_row("GPU Memory Used", f"{result.metrics.gpu_memory_used_mb:.0f}MB")
        metrics_table.add_row("Model Inference Time", f"{result.metrics.model_inference_time:.3f}s")
        metrics_table.add_row("Tokens Processed", f"{result.metrics.total_tokens_processed:,}")
        metrics_table.add_row("GPU Speedup", f"{result.metrics.gpu_speedup:.1f}x")
        metrics_table.add_row("Success Rate", f"{result.success_rate:.1%}")
        
        console.print(metrics_table)
        
        # Job analysis results
        console.print(f"\n[bold blue]🤖 AI-Powered Job Analysis Results[/bold blue]")
        
        for i, job_result in enumerate(result.job_results, 1):
            console.print(f"\n[bold cyan]Job {i}: {job_result['title']}[/bold cyan]")
            console.print(f"[yellow]Company:[/yellow] {job_result['company']}")
            console.print(f"[yellow]Experience Level:[/yellow] {job_result.get('experience_level', 'Unknown')}")
            
            skills = job_result.get('required_skills', [])
            if skills:
                console.print(f"[yellow]AI-Extracted Skills:[/yellow] {', '.join(skills[:6])}")
                if len(skills) > 6:
                    console.print(f"[dim]   ... and {len(skills) - 6} more[/dim]")
            
            console.print(f"[yellow]Compatibility Score:[/yellow] {job_result.get('compatibility_score', 0):.1%}")
            console.print(f"[yellow]AI Confidence:[/yellow] {job_result.get('analysis_confidence', 0):.1%}")
            
            salary_info = job_result.get('salary_info', {})
            if salary_info.get('salary_mentioned'):
                console.print(f"[yellow]Salary:[/yellow] {salary_info.get('salary_range', 'Mentioned')}")
            
            inference_time = job_result.get('inference_time', 0)
            console.print(f"[yellow]GPU Inference Time:[/yellow] {inference_time:.3f}s")
            
            reasoning = job_result.get('analysis_reasoning', '')
            if reasoning:
                console.print(f"[yellow]AI Analysis:[/yellow] {reasoning}")
            
            processing_method = job_result.get('processing_method', 'unknown')
            console.print(f"[yellow]Processing Method:[/yellow] {processing_method}")
        
        # Error reporting
        if result.errors:
            console.print(f"\n[bold red]⚠️ Errors ({len(result.errors)}):[/bold red]")
            for error in result.errors:
                console.print(f"[red]  • {error}[/red]")
        
        # Performance analysis
        console.print(f"\n[bold green]🎉 GPU Processing Complete![/bold green]")
        
        if result.metrics.gpu_utilization > 50:
            console.print("[bold green]🏆 EXCELLENT: High GPU utilization achieved![/bold green]")
        elif result.metrics.gpu_utilization > 20:
            console.print("[green]🥇 VERY GOOD: Good GPU utilization[/green]")
        elif result.metrics.gpu_utilization > 5:
            console.print("[yellow]🥈 MODERATE: Some GPU usage detected[/yellow]")
        else:
            console.print("[yellow]🥉 LOW: Minimal GPU utilization[/yellow]")
        
        console.print(f"[cyan]Processed {result.metrics.jobs_processed} jobs in {result.metrics.processing_time:.3f}s[/cyan]")
        console.print(f"[cyan]GPU throughput: {result.metrics.jobs_per_second:.1f} jobs/sec[/cyan]")
        console.print(f"[cyan]Processed {result.metrics.total_tokens_processed:,} tokens with GPU acceleration[/cyan]")
        
        # Get performance report
        perf_report = processor.get_performance_report()
        console.print(f"\n[bold blue]📈 GPU Performance Report[/bold blue]")
        console.print(f"[cyan]Device: {perf_report['gpu_config']['device']}[/cyan]")
        console.print(f"[cyan]Model: {perf_report['gpu_config']['model_name']}[/cyan]")
        console.print(f"[cyan]CUDA Available: {perf_report['gpu_config']['cuda_available']}[/cyan]")
        console.print(f"[cyan]Average Inference Time: {perf_report['performance_stats']['avg_inference_time']:.3f}s[/cyan]")
        
        return result
        
    except ImportError as e:
        console.print(f"[red]❌ Import error: {e}[/red]")
        console.print("[yellow]Make sure the GPU processor module is available[/yellow]")
        return None
    except Exception as e:
        console.print(f"[red]❌ GPU processing failed: {e}[/red]")
        import traceback
        console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
        return None

async def main():
    """Main test function."""
    result = await test_gpu_processing()
    
    if result:
        console.print("\n[bold blue]✅ GPU Test completed successfully![/bold blue]")
        console.print("[cyan]This demonstrates REAL GPU acceleration using:[/cyan]")
        console.print("[cyan]• Transformers library with BERT models[/cyan]")
        console.print("[cyan]• CUDA acceleration on RTX 3080[/cyan]")
        console.print("[cyan]• Semantic understanding of job descriptions[/cyan]")
        console.print("[cyan]• AI-powered skill extraction and analysis[/cyan]")
    else:
        console.print("\n[bold red]❌ GPU test failed![/bold red]")

if __name__ == "__main__":
    asyncio.run(main())