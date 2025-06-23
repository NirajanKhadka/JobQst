#!/usr/bin/env python3
"""
Ollama Manager for AutoJobAgent
Handles Ollama installation, service management, and model setup.
"""

import subprocess
import os
import time
import requests
from rich.console import Console
from typing import Optional

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


def install_ollama_guide():
    """Display Ollama installation guide."""
    console.print("\n[bold red]❌ Ollama is not installed[/bold red]")
    console.print("\n[bold cyan]📥 Ollama Installation Guide:[/bold cyan]")

    if os.name == 'nt':  # Windows
        console.print("1. Visit: [link]https://ollama.ai[/link]")
        console.print("2. Download the Windows installer")
        console.print("3. Run the installer as Administrator")
        console.print("4. Restart your terminal/command prompt")
        console.print("5. Run: [bold]ollama --version[/bold] to verify")
    else:  # Linux/macOS
        console.print("1. Run: [bold]curl -fsSL https://ollama.ai/install.sh | sh[/bold]")
        console.print("2. Or visit: [link]https://ollama.ai[/link] for manual installation")

    console.print("\n[yellow]💡 After installation, run this command again[/yellow]")


def check_ollama_service() -> bool:
    """Check if Ollama service is running."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def start_ollama_service() -> bool:
    """Start Ollama service."""
    console.print("[cyan]🚀 Starting Ollama service...[/cyan]")

    try:
        if os.name == 'nt':  # Windows
            # On Windows, try to start ollama serve
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

        # Wait for service to start
        console.print("[cyan]⏳ Waiting for Ollama service to start...[/cyan]")
        for _ in range(10):  # Wait up to 10 seconds
            time.sleep(1)
            if check_ollama_service():
                console.print("[green]✅ Ollama service started successfully[/green]")
                return True

        console.print("[red]❌ Ollama service failed to start[/red]")
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
    """Download Mistral model."""
    console.print("[cyan]📥 Downloading Mistral model (this may take a few minutes)...[/cyan]")

    try:
        result = subprocess.run(
            ["ollama", "pull", "mistral"],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes timeout for model download
            shell=True if os.name == 'nt' else False
        )

        if result.returncode == 0:
            console.print("[green]✅ Mistral model downloaded successfully[/green]")
            return True
        else:
            console.print(f"[red]❌ Failed to download Mistral model: {result.stderr}[/red]")
            return False

    except subprocess.TimeoutExpired:
        console.print("[red]❌ Model download timed out[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Error downloading Mistral model: {e}[/red]")
        return False


def check_ollama_status() -> bool:
    """Check complete Ollama status and setup if needed."""
    console.print("[cyan]🔍 Checking Ollama status...[/cyan]")

    # Check if Ollama is installed
    if not check_ollama_installation():
        install_ollama_guide()
        return False

    # Check if service is running
    if not check_ollama_service():
        console.print("[yellow]⚠️ Ollama service is not running[/yellow]")
        if not start_ollama_service():
            return False

    # Check if Mistral model is available
    if not check_mistral_model():
        console.print("[yellow]⚠️ Mistral model not found[/yellow]")
        if not download_mistral_model():
            return False

    console.print("[green]✅ Ollama is ready to use[/green]")
    return True


def setup_ollama_if_needed() -> bool:
    """Setup Ollama if not already configured."""
    return check_ollama_status() 