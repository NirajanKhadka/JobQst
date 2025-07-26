"""
Simple ExLlamaV2 + OpenHermes Performance Test
Clean test with 10 jobs using only ExLlamaV2 and OpenHermes model.
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

def check_requirements():
    """Check if ExLlamaV2 and dependencies are available."""
    console.print("[cyan]🔍 Checking ExLlamaV2 requirements...[/cyan]")
    
    requirements_met = True
    
    # Check ExLlamaV2
    try:
        from exllamav2 import ExLlamaV2, ExLlamaV2Config, ExLlamaV2Cache, ExLlamaV2Tokenizer, ExLlamaV2DynamicGenerator
        console.print("[green]✅ ExLlamaV2 available[/green]")
    except ImportError as e:
        console.print(f"[red]❌ ExLlamaV2 not available: {e}[/red]")
        console.print("[yellow]Install with: pip install exllamav2[/yellow]")
        requirements_met = False
    
    # Check PyTorch
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            console.print(f"[green]✅ PyTorch CUDA available: {gpu_name}[/green]")
            
            if "3080" in gpu_name:
                console.print("[bold green]🎯 RTX 3080 detected![/bold green]")
            
            total_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            console.print(f"[cyan]   VRAM: {total_memory:.1f}GB[/cyan]")
        else:
            console.print("[red]❌ CUDA not available[/red]")
            requirements_met = False
    except ImportError:
        console.print("[red]❌ PyTorch not available - install with: pip install torch[/red]")
        requirements_met = False
    
    # Check GPUtil
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            console.print(f"[green]✅ GPU monitoring: {gpu.name}[/green]")
            console.print(f"[cyan]   Utilization: {gpu.load*100:.1f}%[/cyan]")
            console.print(f"[cyan]   Memory: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB[/cyan]")
            console.print(f"[cyan]   Temperature: {gpu.temperature}°C[/cyan]")
    except ImportError:
        console.print("[yellow]⚠️ GPUtil not available - install with: pip install GPUtil[/yellow]")
    
    return requirements_met

def check_openhermes_model():
    """Check if OpenHermes model is available."""
    console.print("\n[cyan]🔍 Checking OpenHermes model...[/cyan]")
    
    # Common model paths
    model_paths = [
        "models/OpenHermes-2.5-Mistral-7B-GPTQ",
        "models/OpenHermes-2.5-Mistral-7B",
        "../models/OpenHermes-2.5-Mistral-7B-GPTQ",
        "C:/models/OpenHermes-2.5-Mistral-7B-GPTQ",
        "D:/models/OpenHermes-2.5-Mistral-7B-GPTQ"
    ]
    
    for model_path in model_paths:
        if Path(model_path).exists():
            console.print(f"[green]✅ OpenHermes model found: {model_path}[/green]")
            return model_path
    
    console.print("[red]❌ OpenHermes model not found[/red]")
    console.print("[yellow]Download from: https://huggingface.co/teknium/OpenHermes-2.5-Mistral-7B-GPTQ[/yellow]")
    console.print("[yellow]Place in: models/OpenHermes-2.5-Mistral-7B-GPTQ/[/yellow]")
    return None

def create_test_jobs(count: int = 10) -> List[Dict[str, Any]]:
    """Create test jobs for benchmarking."""
    console.print(f"[cyan]📝 Creating {count} test jobs...[/cyan]")
    
    job_templates = [
        {
            'title': 'Software Engineer',
            'company': 'TechCorp',
            'description': 'Looking for a software engineer with Python, JavaScript, React experience. Must have 3+ years of experience in web development and strong problem-solving skills.',
            'location': 'Toronto, ON',
            'status': 'scraped'
        },
        {
            'title': 'Data Scientist',
            'company': 'DataCorp', 
            'description': 'Data scientist role requiring Python, machine learning, pandas, numpy, and statistical analysis skills. PhD in Computer Science preferred with 5+ years experience.',
            'location': 'Vancouver, BC',
            'status': 'scraped'
        },
        {
            'title': 'DevOps Engineer',
            'company': 'CloudCorp',
            'description': 'DevOps engineer with AWS, Docker, Kubernetes, and CI/CD pipeline experience. Must know Terraform, Ansible, and have 4+ years of cloud infrastructure experience.',
            'location': 'Montreal, QC',
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

async def test_exllamav2_performance(test_jobs: List[Dict[str, Any]], model_path: str) -> Dict[str, Any]:
    """Test ExLlamaV2 + OpenHermes performance."""
    console.print("\n[cyan]🚀 Testing ExLlamaV2 + OpenHermes performance...[/cyan]")
    
    try:
        from src.ai.exllamav2_client import ExLlamaV2Client
        
        # Initialize ExLlamaV2 client
        console.print("[dim]Initializing ExLlamaV2 client...[/dim]")
        client = ExLlamaV2Client(
            model_path=model_path,
            max_batch_size=min(8, len(test_jobs)),
            max_seq_len=4096
        )
        
        start_time = time.time()
        
        # Process jobs in batch
        console.print("[dim]Processing jobs with ExLlamaV2...[/dim]")
        batch_result = await client.analyze_job_batch(test_jobs)
        
        processing_time = time.time() - start_time
        
        console.print(f"[green]✅ ExLlamaV2 test complete: {batch_result.jobs_per_second:.2f} jobs/sec[/green]")
        
        return {
            'jobs_processed': len(batch_result.job_results),
            'processing_time': batch_result.processing_time,
            'jobs_per_second': batch_result.jobs_per_second,
            'gpu_utilization': batch_result.gpu_utilization,
            'memory_used_gb': batch_result.memory_used_gb,
            'total_tokens_processed': batch_result.total_tokens_processed,
            'rtx3080_optimized': batch_result.rtx3080_optimized,
            'model_used': batch_result.model_used,
            'method': 'exllamav2_openhermes'
        }
        
    except ImportError as e:
        console.print(f"[red]❌ ExLlamaV2 client not available: {e}[/red]")
        return {'error': f'ExLlamaV2 client not available: {e}'}
    except Exception as e:
        console.print(f"[red]❌ ExLlamaV2 test failed: {e}[/red]")
        return {'error': str(e)}

async def test_basic_cpu_fallback(test_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Test basic CPU fallback for comparison."""
    console.print("\n[cyan]🔄 Testing basic CPU fallback...[/cyan]")
    
    start_time = time.time()
    results = []
    
    for i, job in enumerate(test_jobs):
        console.print(f"[dim]Processing job {i+1}/{len(test_jobs)}...[/dim]")
        
        # Simple rule-based analysis (CPU fallback)
        result = job.copy()
        result.update({
            'required_skills': ['Python', 'SQL'] if 'python' in job['description'].lower() else ['JavaScript'],
            'job_requirements': ['3+ years experience'],
            'compatibility_score': 0.6,
            'analysis_confidence': 0.4,
            'extracted_benefits': ['Health insurance'],
            'analysis_reasoning': 'Basic rule-based analysis',
            'processing_method': 'cpu_fallback',
            'processed_at': time.time()
        })
        results.append(result)
        
        # Simulate processing time
        await asyncio.sleep(0.1)
    
    processing_time = time.time() - start_time
    jobs_per_second = len(results) / processing_time if processing_time > 0 else 0
    
    console.print(f"[green]✅ CPU fallback complete: {jobs_per_second:.2f} jobs/sec[/green]")
    
    return {
        'jobs_processed': len(results),
        'processing_time': processing_time,
        'jobs_per_second': jobs_per_second,
        'method': 'cpu_fallback'
    }

def display_performance_comparison(exllamav2_result: Dict, cpu_result: Dict):
    """Display performance comparison."""
    console.print("\n[bold green]📊 Performance Comparison Results[/bold green]")
    
    # Create comparison table
    table = Table(title="CPU Fallback vs ExLlamaV2 + OpenHermes Performance")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("CPU Fallback", style="yellow")
    table.add_column("ExLlamaV2 + OpenHermes", style="green")
    table.add_column("Improvement", style="bold green")
    
    if 'error' not in exllamav2_result:
        # Both tests successful
        cpu_jps = cpu_result.get('jobs_per_second', 0)
        exllamav2_jps = exllamav2_result.get('jobs_per_second', 0)
        improvement = exllamav2_jps / cpu_jps if cpu_jps > 0 else 0
        
        table.add_row(
            "Jobs per Second",
            f"{cpu_jps:.2f}",
            f"{exllamav2_jps:.2f}",
            f"{improvement:.1f}x faster" if improvement > 1 else "No improvement"
        )
        
        table.add_row(
            "Processing Time",
            f"{cpu_result.get('processing_time', 0):.2f}s",
            f"{exllamav2_result.get('processing_time', 0):.2f}s",
            f"{((cpu_result.get('processing_time', 0) - exllamav2_result.get('processing_time', 0)) / cpu_result.get('processing_time', 1) * 100):.1f}% faster"
        )
        
        table.add_row(
            "GPU Utilization",
            "0% (CPU only)",
            f"{exllamav2_result.get('gpu_utilization', 0):.1f}%",
            "GPU accelerated"
        )
        
        table.add_row(
            "Memory Usage",
            "System RAM",
            f"{exllamav2_result.get('memory_used_gb', 0):.1f}GB VRAM",
            "Dedicated GPU memory"
        )
        
        table.add_row(
            "Model Quality",
            "Rule-based",
            f"{exllamav2_result.get('model_used', 'OpenHermes')}",
            "AI-powered analysis"
        )
        
        table.add_row(
            "Tokens Processed",
            "0 (no LLM)",
            f"{exllamav2_result.get('total_tokens_processed', 0):,}",
            "Advanced language processing"
        )
        
        console.print(table)
        
        # Performance summary
        if improvement > 10:
            console.print("[bold green]🏆 EXCELLENT: ExLlamaV2 + OpenHermes working perfectly![/bold green]")
        elif improvement > 5:
            console.print("[green]🥇 VERY GOOD: ExLlamaV2 + OpenHermes providing excellent performance[/green]")
        elif improvement > 2:
            console.print("[yellow]🥈 GOOD: ExLlamaV2 + OpenHermes providing good improvement[/yellow]")
        elif improvement > 1:
            console.print("[yellow]🥉 MODERATE: ExLlamaV2 + OpenHermes providing some improvement[/yellow]")
        else:
            console.print("[red]⚠️ POOR: ExLlamaV2 + OpenHermes may not be optimized properly[/red]")
            
    else:
        # ExLlamaV2 test failed
        table.add_row(
            "CPU Fallback",
            "✅ Success",
            "",
            ""
        )
        
        table.add_row(
            "ExLlamaV2 + OpenHermes", 
            "",
            f"❌ {exllamav2_result.get('error', 'Failed')}",
            ""
        )
        
        console.print(table)

async def main():
    """Main test function."""
    console.print(Panel(
        "[bold blue]🎯 ExLlamaV2 + OpenHermes Performance Test[/bold blue]\n"
        "[cyan]Testing RTX 3080 optimization with 10 jobs[/cyan]",
        title="AutoJobAgent ExLlamaV2 Test"
    ))
    
    # Check requirements
    if not check_requirements():
        console.print("[red]❌ Requirements not met. Please install missing dependencies.[/red]")
        return
    
    # Check OpenHermes model
    model_path = check_openhermes_model()
    if not model_path:
        console.print("[red]❌ OpenHermes model not found. Please download the model first.[/red]")
        return
    
    # Create test jobs
    test_jobs = create_test_jobs(10)
    
    # Test CPU fallback
    cpu_result = await test_basic_cpu_fallback(test_jobs)
    
    # Test ExLlamaV2 + OpenHermes
    exllamav2_result = await test_exllamav2_performance(test_jobs, model_path)
    
    # Display comparison
    display_performance_comparison(exllamav2_result, cpu_result)
    
    # Final summary
    console.print("\n[bold blue]📋 Test Summary[/bold blue]")
    console.print(f"[green]✅ CPU Fallback: {cpu_result.get('jobs_per_second', 0):.2f} jobs/sec[/green]")
    
    if 'error' not in exllamav2_result:
        console.print(f"[green]✅ ExLlamaV2 + OpenHermes: {exllamav2_result.get('jobs_per_second', 0):.2f} jobs/sec[/green]")
        console.print(f"[cyan]   GPU Utilization: {exllamav2_result.get('gpu_utilization', 0):.1f}%[/cyan]")
        console.print(f"[cyan]   VRAM Usage: {exllamav2_result.get('memory_used_gb', 0):.1f}GB[/cyan]")
        console.print(f"[cyan]   Tokens Processed: {exllamav2_result.get('total_tokens_processed', 0):,}[/cyan]")
        console.print(f"[cyan]   RTX 3080 Optimized: {exllamav2_result.get('rtx3080_optimized', False)}[/cyan]")
    else:
        console.print(f"[red]❌ ExLlamaV2 + OpenHermes failed: {exllamav2_result.get('error', 'Unknown error')}[/red]")
    
    console.print("\n[bold green]🎉 ExLlamaV2 + OpenHermes test complete![/bold green]")

if __name__ == "__main__":
    asyncio.run(main())