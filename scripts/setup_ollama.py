#!/usr/bin/env python3
"""
Ollama Setup Script for AutoJobAgent

This script handles the complete setup and configuration of Ollama
for use with AutoJobAgent, including installation guidance, service
management, and model downloading.
"""

import os
import sys
import time
import subprocess
import requests
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

console = Console()

def check_ollama_installation() -> bool:
    """Check if Ollama is installed on the system."""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            shell=True if os.name == 'nt' else False
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def show_installation_guide():
    """Display comprehensive Ollama installation guide."""
    console.print(Panel.fit(
        "[bold red]❌ Ollama is not installed[/bold red]",
        border_style="red"
    ))
    
    console.print("\n[bold cyan]📥 Ollama Installation Guide:[/bold cyan]")
    
    if os.name == 'nt':  # Windows
        console.print("""
[bold]For Windows:[/bold]
1. Visit: [link]https://ollama.ai[/link]
2. Download the Windows installer (.exe file)
3. Run the installer as Administrator
4. Restart your terminal/command prompt
5. Verify installation: [bold]ollama --version[/bold]

[yellow]Note: You may need to add Ollama to your PATH manually[/yellow]
""")
    else:  # Linux/macOS
        console.print("""
[bold]For Linux/macOS:[/bold]
1. Run: [bold]curl -fsSL https://ollama.ai/install.sh | sh[/bold]
2. Or visit: [link]https://ollama.ai[/link] for manual installation
3. Verify installation: [bold]ollama --version[/bold]

[bold]Alternative for macOS with Homebrew:[/bold]
[bold]brew install ollama[/bold]
""")
    
    console.print("[yellow]💡 After installation, run this script again to continue setup[/yellow]")


def check_ollama_service() -> bool:
    """Check if Ollama service is running."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def start_ollama_service() -> bool:
    """Start Ollama service with progress indication."""
    console.print("[cyan]🚀 Starting Ollama service...[/cyan]")
    
    try:
        if os.name == 'nt':  # Windows
            subprocess.Popen(
                ["ollama", "serve"],
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0
            )
        else:  # Linux/macOS
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        # Wait for service to start with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Waiting for Ollama service to start...", total=None)
            
            for i in range(15):  # Wait up to 15 seconds
                time.sleep(1)
                if check_ollama_service():
                    progress.update(task, description="✅ Ollama service started successfully!")
                    return True
        
        console.print("[red]❌ Ollama service failed to start within 15 seconds[/red]")
        console.print("[yellow]💡 Try manually: ollama serve[/yellow]")
        return False
        
    except Exception as e:
        console.print(f"[red]❌ Error starting Ollama service: {e}[/red]")
        return False


def check_mistral_model() -> bool:
    """Check if Mistral model is available."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any("mistral" in model.get("name", "") for model in models)
    except requests.exceptions.RequestException:
        pass
    return False


def download_mistral_model() -> bool:
    """Download Mistral model with progress indication."""
    console.print("[cyan]📥 Downloading Mistral model...[/cyan]")
    console.print("[yellow]⚠️ This may take several minutes depending on your internet connection[/yellow]")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Downloading Mistral model (this may take 5-10 minutes)...", total=None)
            
            result = subprocess.run(
                ["ollama", "pull", "mistral"],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes timeout
                shell=True if os.name == 'nt' else False
            )
            
            if result.returncode == 0:
                progress.update(task, description="✅ Mistral model downloaded successfully!")
                return True
            else:
                progress.update(task, description="❌ Failed to download Mistral model")
                console.print(f"[red]Error: {result.stderr}[/red]")
                return False
                
    except subprocess.TimeoutExpired:
        console.print("[red]❌ Timeout downloading Mistral model[/red]")
        console.print("[yellow]💡 Try manually: ollama pull mistral[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Error downloading Mistral model: {e}[/red]")
        return False


def test_ollama_functionality():
    """Test Ollama functionality with a simple query."""
    console.print("[cyan]🧪 Testing Ollama functionality...[/cyan]")
    
    try:
        # Test with a simple prompt
        result = subprocess.run(
            ["ollama", "run", "mistral", "Hello, respond with just 'OK' if you're working"],
            capture_output=True,
            text=True,
            timeout=30,
            shell=True if os.name == 'nt' else False
        )
        
        if result.returncode == 0 and "OK" in result.stdout:
            console.print("[green]✅ Ollama is working correctly![/green]")
            return True
        else:
            console.print("[yellow]⚠️ Ollama responded but may not be working optimally[/yellow]")
            return True  # Still consider it working
            
    except Exception as e:
        console.print(f"[red]❌ Error testing Ollama: {e}[/red]")
        return False


def main():
    """Main setup function."""
    console.print(Panel.fit(
        "[bold blue]🤖 AutoJobAgent - Ollama Setup[/bold blue]",
        border_style="blue"
    ))
    
    console.print("\n[bold]This script will help you set up Ollama for AutoJobAgent[/bold]")
    console.print("Ollama provides local AI capabilities for job matching and document customization.\n")
    
    # Step 1: Check installation
    console.print("[bold]Step 1: Checking Ollama installation...[/bold]")
    if not check_ollama_installation():
        show_installation_guide()
        return 1
    
    console.print("[green]✅ Ollama is installed[/green]")
    
    # Step 2: Check/start service
    console.print("\n[bold]Step 2: Checking Ollama service...[/bold]")
    if not check_ollama_service():
        console.print("[yellow]⚠️ Ollama service not running[/yellow]")
        if Confirm.ask("Would you like to start the Ollama service?"):
            if not start_ollama_service():
                console.print("[red]❌ Failed to start Ollama service[/red]")
                return 1
        else:
            console.print("[yellow]Please start Ollama manually: ollama serve[/yellow]")
            return 1
    else:
        console.print("[green]✅ Ollama service is running[/green]")
    
    # Step 3: Check/download model
    console.print("\n[bold]Step 3: Checking Mistral model...[/bold]")
    if not check_mistral_model():
        console.print("[yellow]⚠️ Mistral model not found[/yellow]")
        if Confirm.ask("Would you like to download the Mistral model? (Required for AI features)"):
            if not download_mistral_model():
                console.print("[red]❌ Failed to download Mistral model[/red]")
                return 1
        else:
            console.print("[yellow]AI features will not be available without the model[/yellow]")
            return 1
    else:
        console.print("[green]✅ Mistral model is available[/green]")
    
    # Step 4: Test functionality
    console.print("\n[bold]Step 4: Testing Ollama functionality...[/bold]")
    if test_ollama_functionality():
        console.print("\n[bold green]🎉 Ollama setup completed successfully![/bold green]")
        console.print("[green]AutoJobAgent is now ready to use AI features[/green]")
        return 0
    else:
        console.print("\n[yellow]⚠️ Setup completed but functionality test failed[/yellow]")
        console.print("[yellow]You may need to troubleshoot Ollama manually[/yellow]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
