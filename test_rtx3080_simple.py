"""
Simple RTX 3080 Performance Test
Quick test with 10 jobs to validate RTX 3080 optimizations.
"""

import asyncio
import time
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

console = Console()

def check_system_requirements():
    """Check if system requirements are met."""
    console.print("[cyan]🔍 Checking system requirements...[/cyan]")
    
    requirements_met = True
    
    # Check psutil
    try:
        import psutil
        console.print("[green]✅ psutil available[/green]")
    except ImportError:
        console.print("[red]❌ psutil not available - install with: pip install psutil[/red]")
        requirements_met = False
    
    # Check GPUtil
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            console.print(f"[green]✅ GPU detected: {gpu.name}[/green]")
            console.print(f"[cyan]   Memory: {gpu.memoryUsed:.0f}MB / {gpu.memoryTotal:.0f}MB[/cyan]")
            console.print(f"[cyan]   Utilization: {gpu.load*100:.1f}%[/cyan]")
            console.print(f"[cyan]   Temperature: {gpu.temperature}°C[/cyan]")
            
            # Check if it's RTX 3080
            if "3080" in gpu.name:
                console.print("[bold green]🎯 RTX 3080 detected![/bold green]")
            else:
                console.print(f"[yellow]⚠️ GPU is {gpu.name}, not RTX 3080[/yellow]")
        else:
            console.print("[yellow]⚠️ No GPUs detected[/yellow]")
    except ImportError:
        console.print("[red]❌ GPUtil not available - install with: pip install GPUtil[/red]")
        requirements_met = False
    except Exception as e:
        console.print(f"[yellow]⚠️ GPU check failed: {e}[/yellow]")
    
    # Check ollama
    try:
        import ollama
        console.print("[green]✅ ollama library available[/green]")
        
        # Test connection
        try:
            client = ollama.Client()
            models = client.list()
            console.print(f"[green]✅ Ollama service running with {len(models.get('models', []))} models[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Ollama service not running: {e}[/yellow]")
            console.print("[yellow]Start with: ollama serve[/yellow]")
    except ImportError:
        console.print("[red]❌ ollama not available - install with: pip install ollama[/red]")
        requirements_met = False
    
    return requirements_met

def create_test_jobs(count: int = 10) -> List[Dict[str, Any]]:
    """Create test jobs for benchmarking."""
    console.print(f"[cyan]📝 Creating {count} test jobs...[/cyan]")
    
    job_templates = [
        {
            'title': 'Software Engineer',
            'company': 'TechCorp',
            'description': 'Looking for a software engineer with Python, JavaScript experience. 3+ years required.',
            'location': 'Toronto, ON',
            'status': 'scraped'
        },
        {
            'title': 'Data Scientist',
            'company': 'DataCorp', 
            'description': 'Data scientist with Python, machine learning, pandas, numpy skills. PhD preferred.',
            'location': 'Vancouver, BC',
            'status': 'scraped'
        }
    ]
    
    test_jobs = []
    for i in range(count):
        template = job_templates[i % len(job_templates)]
        job = template.copy()
        job['id'] = f'test_job_{i + 1:03d}'
        job['url'] = f'https://example.com/job/{i + 1}'
        test_jobs.append(job)
    
    console.print(f"[green]✅ Created {len(test_jobs)} test jobs[/green]")
    return test_jobs

async def test_basic_ollama_performance(test_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Test basic Ollama performance without RTX 3080 optimizations."""
    console.print("\n[cyan]🔄 Testing basic Ollama performance...[/cyan]")
    
    try:
        import ollama
        client = ollama.Client()
        
        start_time = time.time()
        results = []
        
        for i, job in enumerate(test_jobs):
            console.print(f"[dim]Processing job {i+1}/{len(test_jobs)}...[/dim]")
            
            prompt = f"""
            Analyze this job posting and extract key information:
            
            Title: {job['title']}
            Company: {job['company']}
            Description: {job['description']}
            
            Return JSON with: required_skills, experience_level, compatibility_score (0-1)
            """
            
            try:
                response = client.chat(
                    model="llama3",
                    messages=[{'role': 'user', 'content': prompt}],
                    options={'temperature': 0.1}
                )
                
                result = job.copy()
                result['analysis'] = response['message']['content'][:100] + "..."
                result['processed_at'] = time.time()
                results.append(result)
                
            except Exception as e:
                console.print(f"[red]❌ Job {i+1} failed: {e}[/red]")
                result = job.copy()
                result['analysis'] = f"Failed: {e}"
                result['processed_at'] = time.time()
                results.append(result)
        
        processing_time = time.time() - start_time
        jobs_per_second = len(results) / processing_time if processing_time > 0 else 0
        
        console.print(f"[green]✅ Basic test complete: {jobs_per_second:.2f} jobs/sec[/green]")
        
        return {
            'jobs_processed': len(results),
            'processing_time': processing_time,
            'jobs_per_second': jobs_per_second,
            'method': 'basic_ollama'
        }
        
    except Exception as e:
        console.print(f"[red]❌ Basic Ollama test failed: {e}[/red]")
        return {'error': str(e)}

async def test_rtx3080_optimized_performance(test_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Test RTX 3080 optimized performance."""
    console.print("\n[cyan]🚀 Testing RTX 3080 optimized performance...[/cyan]")
    
    try:
        # Try to import RTX 3080 optimized client
        from src.ai.rtx3080_optimized_client import get_rtx3080_optimized_client
        
        # Initialize RTX 3080 client
        gpu_client = get_rtx3080_optimized_client(
            model="llama3",
            max_batch_size=min(8, len(test_jobs)),  # Smaller batch for test
            concurrent_streams=2
        )
        
        start_time = time.time()
        
        # Process jobs in batch
        batch_result = await gpu_client.analyze_jobs_batch_rtx3080(test_jobs)
        
        processing_time = time.time() - start_time
        
        console.print(f"[green]✅ RTX 3080 test complete: {batch_result.jobs_per_second:.2f} jobs/sec[/green]")
        
        return {
            'jobs_processed': len(batch_result.job_results),
            'processing_time': batch_result.processing_time,
            'jobs_per_second': batch_result.jobs_per_second,
            'gpu_utilization': batch_result.gpu_utilization,
            'memory_used_gb': batch_result.memory_used_gb,
            'tensor_cores_utilized': batch_result.tensor_cores_utilized,
            'cuda_streams_used': batch_result.cuda_streams_used,
            'method': 'rtx3080_optimized'
        }
        
    except ImportError as e:
        console.print(f"[yellow]⚠️ RTX 3080 modules not available: {e}[/yellow]")
        return {'error': f'RTX 3080 modules not available: {e}'}
    except Exception as e:
        console.print(f"[red]❌ RTX 3080 test failed: {e}[/red]")
        return {'error': str(e)}

def display_performance_comparison(basic_result: Dict, rtx3080_result: Dict):
    """Display performance comparison."""
    console.print("\n[bold green]📊 Performance Comparison Results[/bold green]")
    
    # Create comparison table
    table = Table(title="Basic vs RTX 3080 Optimized Performance")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Basic Ollama", style="yellow")
    table.add_column("RTX 3080 Optimized", style="green")
    table.add_column("Improvement", style="bold green")
    
    if 'error' not in basic_result and 'error' not in rtx3080_result:
        # Both tests successful
        basic_jps = basic_result.get('jobs_per_second', 0)
        rtx3080_jps = rtx3080_result.get('jobs_per_second', 0)
        improvement = rtx3080_jps / basic_jps if basic_jps > 0 else 0
        
        table.add_row(
            "Jobs per Second",
            f"{basic_jps:.2f}",
            f"{rtx3080_jps:.2f}",
            f"{improvement:.1f}x faster" if improvement > 1 else "No improvement"
        )
        
        table.add_row(
            "Processing Time",
            f"{basic_result.get('processing_time', 0):.2f}s",
            f"{rtx3080_result.get('processing_time', 0):.2f}s",
            f"{((basic_result.get('processing_time', 0) - rtx3080_result.get('processing_time', 0)) / basic_result.get('processing_time', 1) * 100):.1f}% faster"
        )
        
        table.add_row(
            "GPU Utilization",
            "N/A (CPU only)",
            f"{rtx3080_result.get('gpu_utilization', 0):.1f}%",
            "GPU accelerated"
        )
        
        table.add_row(
            "Memory Usage",
            "System RAM",
            f"{rtx3080_result.get('memory_used_gb', 0):.1f}GB VRAM",
            "Dedicated GPU memory"
        )
        
        table.add_row(
            "Tensor Cores",
            "Not available",
            "✅ Used" if rtx3080_result.get('tensor_cores_utilized', False) else "❌ Not used",
            "AI acceleration"
        )
        
        console.print(table)
        
        # Performance summary
        if improvement > 5:
            console.print("[bold green]🏆 EXCELLENT: RTX 3080 optimizations working perfectly![/bold green]")
        elif improvement > 2:
            console.print("[green]🥇 GOOD: RTX 3080 optimizations providing significant improvement[/green]")
        elif improvement > 1.2:
            console.print("[yellow]🥈 MODERATE: RTX 3080 optimizations providing some improvement[/yellow]")
        else:
            console.print("[red]🥉 POOR: RTX 3080 optimizations may not be working properly[/red]")
            
    else:
        # One or both tests failed
        table.add_row(
            "Basic Ollama",
            "✅ Success" if 'error' not in basic_result else f"❌ {basic_result.get('error', 'Failed')}",
            "",
            ""
        )
        
        table.add_row(
            "RTX 3080 Optimized", 
            "",
            "✅ Success" if 'error' not in rtx3080_result else f"❌ {rtx3080_result.get('error', 'Failed')}",
            ""
        )
        
        console.print(table)

async def main():
    """Main test function."""
    console.print(Panel(
        "[bold blue]🎯 RTX 3080 Simple Performance Test[/bold blue]\n"
        "[cyan]Testing with 10 jobs to validate optimizations[/cyan]",
        title="AutoJobAgent RTX 3080 Quick Test"
    ))
    
    # Check system requirements
    if not check_system_requirements():
        console.print("[red]❌ System requirements not met. Please install missing dependencies.[/red]")
        return
    
    # Create test jobs
    test_jobs = create_test_jobs(10)
    
    # Test basic Ollama performance
    basic_result = await test_basic_ollama_performance(test_jobs)
    
    # Test RTX 3080 optimized performance
    rtx3080_result = await test_rtx3080_optimized_performance(test_jobs)
    
    # Display comparison
    display_performance_comparison(basic_result, rtx3080_result)
    
    # Final summary
    console.print("\n[bold blue]📋 Test Summary[/bold blue]")
    if 'error' not in basic_result:
        console.print(f"[green]✅ Basic Ollama: {basic_result.get('jobs_per_second', 0):.2f} jobs/sec[/green]")
    else:
        console.print(f"[red]❌ Basic Ollama failed: {basic_result.get('error', 'Unknown error')}[/red]")
    
    if 'error' not in rtx3080_result:
        console.print(f"[green]✅ RTX 3080 Optimized: {rtx3080_result.get('jobs_per_second', 0):.2f} jobs/sec[/green]")
        console.print(f"[cyan]   GPU Utilization: {rtx3080_result.get('gpu_utilization', 0):.1f}%[/cyan]")
        console.print(f"[cyan]   VRAM Usage: {rtx3080_result.get('memory_used_gb', 0):.1f}GB[/cyan]")
    else:
        console.print(f"[red]❌ RTX 3080 Optimized failed: {rtx3080_result.get('error', 'Unknown error')}[/red]")
    
    console.print("\n[bold green]🎉 RTX 3080 simple test complete![/bold green]")

if __name__ == "__main__":
    asyncio.run(main())