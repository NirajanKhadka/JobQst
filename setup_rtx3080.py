"""
RTX 3080 Setup and Installation Script
Installs dependencies and configures RTX 3080 optimizations for job processing.
"""

import subprocess
import sys
import os
import platform
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        console.print("[red]❌ Python 3.8+ required for RTX 3080 optimizations[/red]")
        return False
    
    console.print(f"[green]✅ Python {version.major}.{version.minor}.{version.micro} is compatible[/green]")
    return True

def check_gpu_availability():
    """Check if NVIDIA GPU is available."""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            console.print("[green]✅ NVIDIA GPU detected[/green]")
            
            # Check for RTX 3080 specifically
            if "RTX 3080" in result.stdout:
                console.print("[bold green]🎯 RTX 3080 detected![/bold green]")
                return True
            else:
                console.print("[yellow]⚠️ NVIDIA GPU found but not RTX 3080[/yellow]")
                console.print("[yellow]RTX 3080 optimizations may still work with other GPUs[/yellow]")
                return True
        else:
            console.print("[red]❌ nvidia-smi failed - NVIDIA drivers may not be installed[/red]")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        console.print("[red]❌ nvidia-smi not found - NVIDIA drivers not installed[/red]")
        return False

def install_dependencies():
    """Install RTX 3080 optimization dependencies."""
    console.print("\n[cyan]📦 Installing RTX 3080 dependencies...[/cyan]")
    
    requirements_file = Path("requirements_rtx3080.txt")
    if not requirements_file.exists():
        console.print("[red]❌ requirements_rtx3080.txt not found[/red]")
        return False
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Installing dependencies...", total=None)
            
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                console.print("[green]✅ Dependencies installed successfully[/green]")
                return True
            else:
                console.print(f"[red]❌ Dependency installation failed: {result.stderr}[/red]")
                return False
                
    except subprocess.TimeoutExpired:
        console.print("[red]❌ Dependency installation timed out[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Dependency installation error: {e}[/red]")
        return False

def check_ollama_installation():
    """Check if Ollama is installed and running."""
    console.print("\n[cyan]🤖 Checking Ollama installation...[/cyan]")
    
    try:
        # Check if Ollama is installed
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            console.print(f"[green]✅ Ollama installed: {result.stdout.strip()}[/green]")
        else:
            console.print("[red]❌ Ollama not installed[/red]")
            console.print("[yellow]Install Ollama from: https://ollama.ai[/yellow]")
            return False
        
        # Check if Ollama service is running
        import requests
        try:
            response = requests.get("http://localhost:11434/api/version", timeout=5)
            if response.status_code == 200:
                console.print("[green]✅ Ollama service is running[/green]")
                return True
            else:
                console.print("[red]❌ Ollama service not responding[/red]")
                return False
        except requests.RequestException:
            console.print("[red]❌ Ollama service not running[/red]")
            console.print("[yellow]Start Ollama service: ollama serve[/yellow]")
            return False
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        console.print("[red]❌ Ollama not found[/red]")
        console.print("[yellow]Install Ollama from: https://ollama.ai[/yellow]")
        return False

def setup_ollama_model():
    """Setup Llama3 model for RTX 3080."""
    console.print("\n[cyan]🦙 Setting up Llama3 model...[/cyan]")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Pulling Llama3 model...", total=None)
            
            result = subprocess.run(['ollama', 'pull', 'llama3'], 
                                  capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                console.print("[green]✅ Llama3 model ready[/green]")
                return True
            else:
                console.print(f"[red]❌ Model setup failed: {result.stderr}[/red]")
                return False
                
    except subprocess.TimeoutExpired:
        console.print("[red]❌ Model setup timed out (this can take a while)[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Model setup error: {e}[/red]")
        return False

def test_rtx3080_setup():
    """Test RTX 3080 optimization setup."""
    console.print("\n[cyan]🧪 Testing RTX 3080 setup...[/cyan]")
    
    try:
        # Test GPU monitoring
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            console.print(f"[green]✅ GPU monitoring working: {gpu.name}[/green]")
            console.print(f"[cyan]   Memory: {gpu.memoryUsed:.0f}MB / {gpu.memoryTotal:.0f}MB[/cyan]")
            console.print(f"[cyan]   Utilization: {gpu.load*100:.1f}%[/cyan]")
        else:
            console.print("[yellow]⚠️ No GPUs detected by GPUtil[/yellow]")
        
        # Test Ollama connection
        import ollama
        client = ollama.Client()
        models = client.list()
        console.print(f"[green]✅ Ollama connection working[/green]")
        console.print(f"[cyan]   Available models: {len(models.get('models', []))}[/cyan]")
        
        return True
        
    except ImportError as e:
        console.print(f"[red]❌ Import error: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Setup test failed: {e}[/red]")
        return False

def main():
    """Main setup function."""
    console.print(Panel(
        "[bold blue]🚀 RTX 3080 Optimization Setup[/bold blue]\n"
        "[cyan]Setting up GPU-accelerated job processing[/cyan]",
        title="AutoJobAgent RTX 3080 Setup"
    ))
    
    setup_success = True
    
    # Check Python version
    if not check_python_version():
        setup_success = False
    
    # Check GPU availability
    if not check_gpu_availability():
        console.print("[yellow]⚠️ Continuing without GPU - optimizations may not work[/yellow]")
    
    # Install dependencies
    if not install_dependencies():
        setup_success = False
    
    # Check Ollama
    if not check_ollama_installation():
        setup_success = False
    
    # Setup model
    if setup_success and not setup_ollama_model():
        console.print("[yellow]⚠️ Model setup failed - you can try manually: ollama pull llama3[/yellow]")
    
    # Test setup
    if setup_success:
        test_rtx3080_setup()
    
    # Final status
    if setup_success:
        console.print("\n[bold green]🎉 RTX 3080 setup complete![/bold green]")
        console.print("[green]You can now run: python test_rtx3080_performance.py[/green]")
    else:
        console.print("\n[bold red]❌ RTX 3080 setup incomplete[/bold red]")
        console.print("[red]Please resolve the issues above and try again[/red]")
    
    return setup_success

if __name__ == "__main__":
    main()