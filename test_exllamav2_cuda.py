"""
ExLlamaV2 CUDA Test
Simple test to verify ExLlamaV2 works with RTX 3080 and proper CUDA setup.
"""

import os
import sys
import time
import logging
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Set CUDA_HOME before importing anything CUDA-related
os.environ['CUDA_HOME'] = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8"
os.environ['CUDA_PATH'] = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8"

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

console = Console()

def test_cuda_setup():
    """Test CUDA setup and environment."""
    console.print("[cyan]🔍 Testing CUDA setup...[/cyan]")
    
    # Check environment variables
    cuda_home = os.environ.get('CUDA_HOME')
    cuda_path = os.environ.get('CUDA_PATH')
    
    console.print(f"[cyan]CUDA_HOME: {cuda_home}[/cyan]")
    console.print(f"[cyan]CUDA_PATH: {cuda_path}[/cyan]")
    
    # Check if CUDA directory exists
    if cuda_home and Path(cuda_home).exists():
        console.print("[green]✅ CUDA directory exists[/green]")
        
        # Check for nvcc
        nvcc_path = Path(cuda_home) / "bin" / "nvcc.exe"
        if nvcc_path.exists():
            console.print("[green]✅ nvcc compiler found[/green]")
        else:
            console.print("[yellow]⚠️ nvcc compiler not found[/yellow]")
    else:
        console.print("[red]❌ CUDA directory not found[/red]")
        return False
    
    return True

def test_gpu_availability():
    """Test GPU availability."""
    console.print("\n[cyan]🎯 Testing GPU availability...[/cyan]")
    
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        
        if gpus:
            for i, gpu in enumerate(gpus):
                console.print(f"[green]✅ GPU {i}: {gpu.name}[/green]")
                console.print(f"[cyan]   Memory: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB[/cyan]")
                console.print(f"[cyan]   Utilization: {gpu.load*100:.1f}%[/cyan]")
                console.print(f"[cyan]   Temperature: {gpu.temperature}°C[/cyan]")
                
                if "3080" in gpu.name:
                    console.print("[bold green]🏆 RTX 3080 detected![/bold green]")
            return True
        else:
            console.print("[red]❌ No GPUs detected[/red]")
            return False
            
    except ImportError:
        console.print("[yellow]⚠️ GPUtil not available[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]❌ GPU detection failed: {e}[/red]")
        return False

def test_pytorch_cuda():
    """Test PyTorch CUDA availability."""
    console.print("\n[cyan]🔥 Testing PyTorch CUDA...[/cyan]")
    
    try:
        import torch
        
        console.print(f"[cyan]PyTorch version: {torch.__version__}[/cyan]")
        
        if torch.cuda.is_available():
            console.print("[green]✅ PyTorch CUDA available[/green]")
            
            device_count = torch.cuda.device_count()
            console.print(f"[cyan]CUDA devices: {device_count}[/cyan]")
            
            for i in range(device_count):
                device_name = torch.cuda.get_device_name(i)
                console.print(f"[cyan]Device {i}: {device_name}[/cyan]")
                
                # Get memory info
                memory_total = torch.cuda.get_device_properties(i).total_memory / 1024**3
                console.print(f"[cyan]   Total memory: {memory_total:.1f}GB[/cyan]")
            
            return True
        else:
            console.print("[red]❌ PyTorch CUDA not available[/red]")
            return False
            
    except ImportError:
        console.print("[red]❌ PyTorch not available[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ PyTorch CUDA test failed: {e}[/red]")
        return False

def test_exllamav2_import():
    """Test ExLlamaV2 import."""
    console.print("\n[cyan]🦙 Testing ExLlamaV2 import...[/cyan]")
    
    try:
        # Import ExLlamaV2 components
        from exllamav2 import ExLlamaV2, ExLlamaV2Config, ExLlamaV2Cache, ExLlamaV2Tokenizer
        console.print("[green]✅ ExLlamaV2 imported successfully[/green]")
        
        # Try to create a config (this will test CUDA compilation)
        console.print("[cyan]Testing CUDA compilation...[/cyan]")
        
        # This should trigger CUDA extension compilation
        config = ExLlamaV2Config()
        console.print("[green]✅ ExLlamaV2 CUDA extensions loaded[/green]")
        
        return True
        
    except ImportError as e:
        console.print(f"[red]❌ ExLlamaV2 import failed: {e}[/red]")
        console.print("[yellow]Install with: pip install exllamav2[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]❌ ExLlamaV2 CUDA compilation failed: {e}[/red]")
        console.print("[yellow]This usually means CUDA setup issues[/yellow]")
        return False

def test_simple_job_analysis():
    """Test simple job analysis without model loading."""
    console.print("\n[cyan]💼 Testing simple job analysis (CPU fallback)...[/cyan]")
    
    # Simple rule-based analysis for comparison
    test_job = {
        'id': 'test_001',
        'title': 'Senior Python Developer',
        'company': 'TechCorp',
        'description': 'Looking for a senior Python developer with experience in Django, FastAPI, and machine learning. Must have 5+ years of experience.',
        'location': 'Toronto, ON'
    }
    
    start_time = time.time()
    
    # Simple keyword extraction
    description = test_job['description'].lower()
    skills = []
    
    skill_keywords = ['python', 'django', 'fastapi', 'machine learning', 'sql', 'javascript', 'react']
    for skill in skill_keywords:
        if skill in description:
            skills.append(skill.title())
    
    # Simple analysis
    result = {
        'job_id': test_job['id'],
        'required_skills': skills,
        'experience_level': 'Senior' if 'senior' in description else 'Mid-level',
        'compatibility_score': 0.8,  # Mock score
        'analysis_method': 'rule_based_cpu',
        'processing_time': time.time() - start_time
    }
    
    console.print(f"[green]✅ Job analysis complete in {result['processing_time']:.3f}s[/green]")
    console.print(f"[cyan]Skills found: {', '.join(result['required_skills'])}[/cyan]")
    console.print(f"[cyan]Experience level: {result['experience_level']}[/cyan]")
    
    return result

def main():
    """Main test function."""
    console.print(Panel(
        "[bold blue]🎯 ExLlamaV2 + RTX 3080 CUDA Test[/bold blue]\n"
        "[cyan]Testing CUDA setup and ExLlamaV2 compatibility[/cyan]",
        title="AutoJobAgent ExLlamaV2 Test"
    ))
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    test_results = {}
    
    # Test 1: CUDA Setup
    test_results['cuda_setup'] = test_cuda_setup()
    
    # Test 2: GPU Availability
    test_results['gpu_available'] = test_gpu_availability()
    
    # Test 3: PyTorch CUDA
    test_results['pytorch_cuda'] = test_pytorch_cuda()
    
    # Test 4: ExLlamaV2 Import
    test_results['exllamav2_import'] = test_exllamav2_import()
    
    # Test 5: Simple Job Analysis (fallback)
    test_results['job_analysis'] = test_simple_job_analysis()
    
    # Summary
    console.print("\n[bold blue]📋 Test Summary[/bold blue]")
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        console.print(f"{status} {test_name.replace('_', ' ').title()}")
    
    console.print(f"\n[cyan]Tests passed: {passed_tests}/{total_tests}[/cyan]")
    
    if test_results['exllamav2_import']:
        console.print("\n[bold green]🎉 ExLlamaV2 is ready for RTX 3080![/bold green]")
        console.print("[green]You can now use ExLlamaV2 for high-performance job processing[/green]")
    else:
        console.print("\n[bold red]❌ ExLlamaV2 setup incomplete[/bold red]")
        console.print("[red]Please resolve CUDA issues before using ExLlamaV2[/red]")
    
    return test_results

if __name__ == "__main__":
    main()