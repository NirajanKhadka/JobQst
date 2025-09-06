#!/usr/bin/env python3
"""
Ollama Manager for AutoJobAgent
Handles Ollama installation, service management, and model setup.

This module manages the Ollama LLM service for text generation and model management.

## Usage Pattern (Improved)
- Always call `ensure_ollama_running()` before using `generate_with_ollama()` to guarantee the service is available.
- This ensures reliable, automated LLM-powered document generation and avoids connection errors.

Example:
    from src.core.ollama_manager import ensure_ollama_running, generate_with_ollama
    if ensure_ollama_running():
        result = generate_with_ollama('Your prompt here')
        print(result)
    else:
        print('Ollama service could not be started.')

## Functions
- check_ollama_service(): Check if Ollama is running
- start_ollama_service(): Start Ollama service
- ensure_ollama_running(): Ensure Ollama is running (recommended)
- generate_with_ollama(): Generate text from Ollama (call after ensure_ollama_running)

This pattern is an improvement for reliability and automation.
"""

import subprocess
import os
import time
import requests
from rich.console import Console
from typing import Optional, List, Dict

console = Console()


def check_ollama_installation() -> bool:
    """Check if Ollama is installed on the system."""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            shell=True if os.name == "nt" else False,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def install_ollama_guide():
    """Display Ollama installation guide."""
    console.print("\n[bold red]❌ Ollama is not installed[/bold red]")
    console.print("\n[bold cyan]📥 Ollama Installation Guide:[/bold cyan]")

    if os.name == "nt":  # Windows
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
        if os.name == "nt":  # Windows
            # On Windows, try to start ollama serve
            subprocess.Popen(
                ["ollama", "serve"],
                shell=True,
                creationflags=(
                    subprocess.CREATE_NEW_CONSOLE
                    if hasattr(subprocess, "CREATE_NEW_CONSOLE")
                    else 0
                ),
            )
        else:  # Linux/macOS
            subprocess.Popen(
                ["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
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
            shell=True if os.name == "nt" else False,
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


def ensure_ollama_running() -> bool:
    """
    Ensure Ollama service is running. Starts it if not running.
    Returns True if running, False otherwise.
    """
    if check_ollama_service():
        return True
    return start_ollama_service()


def generate_with_ollama(prompt: str, model: str = "mistral") -> str:
    """
    Generate text from Ollama using the specified model and prompt.
    Always call ensure_ollama_running() before using this function.
    """
    url = "http://localhost:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()["response"]


class OllamaManager:
    """Manager class for Ollama operations."""

    def __init__(self):
        """Initialize the Ollama manager."""
        self.base_url = "http://localhost:11434"

    def get_available_models(self) -> List[Dict]:
        """
        Get list of available Ollama models.

        Returns:
            List of model dictionaries with name and other metadata
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
            else:
                console.print(f"[red]❌ Failed to get models: {response.status_code}[/red]")
                return []
        except requests.exceptions.RequestException as e:
            console.print(f"[red]❌ Error getting models: {e}[/red]")
            return []
        except Exception as e:
            console.print(f"[red]❌ Unexpected error getting models: {e}[/red]")
            return []

    def is_service_running(self) -> bool:
        """Check if Ollama service is running."""
        return check_ollama_service()

    def start_service(self) -> bool:
        """Start Ollama service."""
        return start_ollama_service()

    def check_model(self, model_name: str) -> bool:
        """Check if a specific model is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(model_name in model.get("name", "") for model in models)
        except requests.exceptions.RequestException:
            pass
        return False

