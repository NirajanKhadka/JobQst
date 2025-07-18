#!/usr/bin/env python3
"""
AutoJobAgent Neural Network Setup Script
Sets up the environment for Llama 3 8B retraining.

This script:
- Installs required dependencies
- Sets up the neural network environment
- Prepares initial training data
- Provides quick start instructions

Usage:
    python setup_neural_network.py
"""

import os
import sys
import subprocess
from pathlib import Path
import json
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

console = Console()

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        console.print("[red]❌ Python 3.8+ required for neural network training[/red]")
        return False
    
    console.print(f"[green]✅ Python {version.major}.{version.minor} detected[/green]")
    return True

def install_neural_network_dependencies():
    """Install neural network and ML dependencies."""
    console.print("[cyan]Installing neural network dependencies...[/cyan]")
    
    # Check if requirements file exists
    requirements_file = "requirements_neural_network.txt"
    if not Path(requirements_file).exists():
        console.print(f"[red]❌ {requirements_file} not found[/red]")
        return False
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Installing packages...", total=None)
            
            # Install requirements
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", requirements_file
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                console.print("[green]✅ Neural network dependencies installed successfully[/green]")
                return True
            else:
                console.print(f"[red]❌ Installation failed: {result.stderr}[/red]")
                return False
                
    except Exception as e:
        console.print(f"[red]❌ Installation error: {e}[/red]")
        return False

def check_gpu_availability():
    """Check GPU availability for training."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            
            console.print(f"[green]🚀 GPU Available: {gpu_name}[/green]")
            console.print(f"[green]   Memory: {gpu_memory:.1f}GB ({gpu_count} GPU(s))[/green]")
            
            if gpu_memory >= 20:
                console.print("[green]✅ Sufficient GPU memory for Llama 3 8B training[/green]")
                return "optimal"
            elif gpu_memory >= 12:
                console.print("[yellow]⚠️ Limited GPU memory - will use optimized settings[/yellow]")
                return "limited"
            else:
                console.print("[red]❌ Insufficient GPU memory for optimal training[/red]")
                return "insufficient"
        else:
            console.print("[yellow]⚠️ No GPU detected - training will be slow[/yellow]")
            return "cpu"
            
    except ImportError:
        console.print("[red]❌ PyTorch not installed - cannot check GPU[/red]")
        return "unknown"

def create_neural_network_config(gpu_status: str):
    """Create optimized configuration based on system capabilities."""
    
    # Base configuration
    if gpu_status == "optimal":
        config = {
            "model_name": "meta-llama/Meta-Llama-3-8B-Instruct",
            "batch_size": 4,
            "gradient_accumulation_steps": 8,
            "learning_rate": 2e-4,
            "num_epochs": 3,
            "max_length": 4096,
            "lora_r": 16,
            "lora_alpha": 32
        }
    elif gpu_status == "limited":
        config = {
            "model_name": "meta-llama/Meta-Llama-3-8B-Instruct",
            "batch_size": 2,
            "gradient_accumulation_steps": 16,
            "learning_rate": 1e-4,
            "num_epochs": 2,
            "max_length": 2048,
            "lora_r": 8,
            "lora_alpha": 16
        }
    else:  # CPU or insufficient GPU
        config = {
            "model_name": "meta-llama/Meta-Llama-3-8B-Instruct",
            "batch_size": 1,
            "gradient_accumulation_steps": 32,
            "learning_rate": 5e-5,
            "num_epochs": 1,
            "max_length": 1024,
            "lora_r": 4,
            "lora_alpha": 8
        }
    
    # Save configuration
    config_file = "neural_network_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    console.print(f"[green]✅ Configuration saved to {config_file}[/green]")
    return config_file

def setup_directories():
    """Setup required directories for neural network training."""
    directories = [
        "models",
        "data/neural_network",
        "logs/neural_network", 
        "checkpoints",
        "src/neural_network"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    console.print("[green]✅ Directories created[/green]")

def create_quick_start_script():
    """Create a quick start script for neural network training."""
    
    script_content = '''#!/usr/bin/env python3
"""
Quick Start Script for AutoJobAgent Llama 3 8B Training
"""

import subprocess
import sys
from pathlib import Path

def main():
    print("🚀 AutoJobAgent Llama 3 8B Quick Start")
    print("=====================================")
    
    # Check if training orchestrator exists
    orchestrator_path = Path("src/neural_network/training_orchestrator.py")
    if not orchestrator_path.exists():
        print("❌ Training orchestrator not found")
        return 1
    
    print("Choose an option:")
    print("1. Prepare training data from your AutoJobAgent profiles")
    print("2. Start Llama 3 8B training")
    print("3. Evaluate trained model")
    print("4. Interactive testing")
    print("5. Check training status")
    
    choice = input("Enter choice (1-5): ").strip()
    
    if choice == "1":
        cmd = [sys.executable, str(orchestrator_path), "--mode", "prepare"]
    elif choice == "2":
        cmd = [sys.executable, str(orchestrator_path), "--mode", "train"]
    elif choice == "3":
        cmd = [sys.executable, str(orchestrator_path), "--mode", "evaluate"]
    elif choice == "4":
        cmd = [sys.executable, str(orchestrator_path), "--mode", "interactive"]
    elif choice == "5":
        cmd = [sys.executable, str(orchestrator_path), "--mode", "status"]
    else:
        print("Invalid choice")
        return 1
    
    # Run the command
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd).returncode

if __name__ == "__main__":
    sys.exit(main())
'''
    
    script_file = "quick_start_neural_network.py"
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    # Make executable on Unix systems
    if sys.platform != "win32":
        os.chmod(script_file, 0o755)
    
    console.print(f"[green]✅ Quick start script created: {script_file}[/green]")
    return script_file

def display_next_steps(config_file: str, quick_start_script: str):
    """Display next steps for the user."""
    
    console.print(Panel(
        f"""[bold green]🎉 Neural Network Setup Complete![/bold green]

[bold cyan]Next Steps:[/bold cyan]

[bold]1. Prepare Training Data:[/bold]
   python src/neural_network/training_orchestrator.py --mode prepare

[bold]2. Start Training:[/bold]
   python src/neural_network/training_orchestrator.py --mode train --config {config_file}

[bold]3. Quick Start (Interactive):[/bold]
   python {quick_start_script}

[bold cyan]What's been set up:[/bold cyan]
✅ Neural network dependencies installed
✅ GPU detection and optimization
✅ Training configuration created
✅ Directory structure prepared
✅ Quick start script ready

[bold yellow]Important Notes:[/bold yellow]
• Training Llama 3 8B requires significant computational resources
• The training will process your existing AutoJobAgent job data
• First run will create sample data if no real data is available
• Training progress will be logged and checkpointed

[bold cyan]Need Help?[/bold cyan]
• Check status: python src/neural_network/training_orchestrator.py --mode status
• View configuration: cat {config_file}
• Interactive testing: python src/neural_network/training_orchestrator.py --mode interactive
""",
        title="Setup Complete",
        expand=False
    ))

def main():
    """Main setup function."""
    console.print(Panel(
        "[bold blue]🧠 AutoJobAgent Neural Network Setup[/bold blue]\n"
        "Setting up Llama 3 8B retraining environment...",
        title="Neural Network Setup",
        expand=False
    ))
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Install dependencies
    if Confirm.ask("Install neural network dependencies?"):
        if not install_neural_network_dependencies():
            console.print("[red]❌ Failed to install dependencies[/red]")
            return 1
    
    # Check GPU
    gpu_status = check_gpu_availability()
    
    # Setup directories
    setup_directories()
    
    # Create configuration
    config_file = create_neural_network_config(gpu_status)
    
    # Create quick start script
    quick_start_script = create_quick_start_script()
    
    # Display next steps
    display_next_steps(config_file, quick_start_script)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
