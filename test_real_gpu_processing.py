"""
Real GPU Processing Test
Uses Transformers library with CUDA for actual GPU acceleration.
"""

import torch
import time
from rich.console import Console
from rich.panel import Panel

console = Console()

def test_gpu_availability():
    """Test if GPU is actually available and working."""
    console.print("[cyan]🔍 Testing GPU availability...[/cyan]")
    
    # Check CUDA availability
    if not torch.cuda.is_available():
        console.print("[red]❌ CUDA not available[/red]")
        return False
    
    # Get GPU info
    device_count = torch.cuda.device_count()
    console.print(f"[green]✅ CUDA available with {device_count} device(s)[/green]")
    
    for i in range(device_count):
        gpu_name = torch.cuda.get_device_name(i)
        memory_total = torch.cuda.get_device_properties(i).total_memory / 1024**3
        console.print(f"[cyan]   GPU {i}: {gpu_name} ({memory_total:.1f}GB)[/cyan]")
        
        if "3080" in gpu_name:
            console.print("[bold green]🎯 RTX 3080 detected![/bold green]")
    
    return True

def test_gpu_computation():
    """Test actual GPU computation."""
    console.print("\n[cyan]⚡ Testing GPU computation...[/cyan]")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    console.print(f"[cyan]Using device: {device}[/cyan]")
    
    # Create test tensors
    size = 1000
    a = torch.randn(size, size, device=device)
    b = torch.randn(size, size, device=device)
    
    # Time GPU computation
    start_time = time.time()
    for _ in range(10):
        c = torch.matmul(a, b)
        torch.cuda.synchronize()  # Wait for GPU to finish
    gpu_time = time.time() - start_time
    
    console.print(f"[green]✅ GPU computation: {gpu_time:.3f}s for 10 matrix multiplications[/green]")
    
    # Compare with CPU
    a_cpu = a.cpu()
    b_cpu = b.cpu()
    
    start_time = time.time()
    for _ in range(10):
        c_cpu = torch.matmul(a_cpu, b_cpu)
    cpu_time = time.time() - start_time
    
    console.print(f"[yellow]CPU computation: {cpu_time:.3f}s for 10 matrix multiplications[/yellow]")
    
    speedup = cpu_time / gpu_time if gpu_time > 0 else 1
    console.print(f"[bold green]🚀 GPU Speedup: {speedup:.1f}x faster than CPU[/bold green]")
    
    return speedup > 1

def test_transformers_gpu():
    """Test if we can use Transformers library with GPU."""
    console.print("\n[cyan]🤖 Testing Transformers with GPU...[/cyan]")
    
    try:
        from transformers import pipeline, AutoTokenizer, AutoModel
        
        # Check if we can load a small model on GPU
        device = 0 if torch.cuda.is_available() else -1
        
        console.print("[dim]Loading small model for testing...[/dim]")
        
        # Use a small, fast model for testing
        model_name = "distilbert-base-uncased"
        
        # Test tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        console.print("[green]✅ Tokenizer loaded[/green]")
        
        # Test model loading on GPU
        if device >= 0:
            model = AutoModel.from_pretrained(model_name).to(f"cuda:{device}")
            console.print(f"[green]✅ Model loaded on GPU {device}[/green]")
            
            # Test inference
            test_text = "This is a test job description for a Python developer position."
            inputs = tokenizer(test_text, return_tensors="pt").to(f"cuda:{device}")
            
            start_time = time.time()
            with torch.no_grad():
                outputs = model(**inputs)
            inference_time = time.time() - start_time
            
            console.print(f"[green]✅ GPU inference: {inference_time:.3f}s[/green]")
            console.print(f"[cyan]Output shape: {outputs.last_hidden_state.shape}[/cyan]")
            
            return True
        else:
            console.print("[yellow]⚠️ No GPU available for Transformers[/yellow]")
            return False
            
    except ImportError:
        console.print("[red]❌ Transformers library not available[/red]")
        console.print("[yellow]Install with: pip install transformers[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Transformers GPU test failed: {e}[/red]")
        return False

def main():
    """Main test function."""
    console.print(Panel(
        "[bold blue]🎯 Real GPU Processing Test[/bold blue]\n"
        "[cyan]Testing actual GPU acceleration with your RTX 3080[/cyan]",
        title="GPU Acceleration Test"
    ))
    
    # Test 1: GPU Availability
    gpu_available = test_gpu_availability()
    
    if not gpu_available:
        console.print("\n[bold red]❌ GPU not available - cannot proceed with GPU tests[/bold red]")
        return
    
    # Test 2: GPU Computation
    gpu_working = test_gpu_computation()
    
    # Test 3: Transformers with GPU
    transformers_working = test_transformers_gpu()
    
    # Summary
    console.print("\n[bold blue]📋 Test Summary[/bold blue]")
    console.print(f"[green]✅ GPU Available: {gpu_available}[/green]")
    console.print(f"[green]✅ GPU Computation: {gpu_working}[/green]")
    console.print(f"[green]✅ Transformers GPU: {transformers_working}[/green]")
    
    if gpu_available and gpu_working:
        console.print("\n[bold green]🎉 Your RTX 3080 is working and ready for GPU acceleration![/bold green]")
        
        if transformers_working:
            console.print("[green]You can use Transformers library for real AI processing[/green]")
        else:
            console.print("[yellow]Install transformers for AI model processing: pip install transformers[/yellow]")
    else:
        console.print("\n[bold red]❌ GPU acceleration not working properly[/bold red]")

if __name__ == "__main__":
    main()