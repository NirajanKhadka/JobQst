"""
System Handler for AutoJobAgent CLI.

Handles all system operations including:
- Ollama setup and management
- System status and settings
- Profile management
- System health checks
"""

import subprocess
import time
import os
import requests
from typing import Dict, Optional
from pathlib import Path
import logging

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from src.utils import get_available_profiles

console = Console()

system_logger = logging.getLogger("system_orchestrator")
system_logger.setLevel(logging.INFO)
s_handler = logging.FileHandler("logs/system_orchestrator.log")
s_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
s_handler.setFormatter(s_formatter)
if not system_logger.hasHandlers():
    system_logger.addHandler(s_handler)

class SystemOrchestrator:
    """Orchestrates system sessions, wraps SystemHandler, and logs actions."""
    def __init__(self, profile: Dict):
        self.profile = profile
        self.handler = SystemHandler(profile)
        self.logger = system_logger

    def log(self, message, level="INFO"):
        if level == "INFO":
            self.logger.info(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "ERROR":
            self.logger.error(message)
        elif level == "CRITICAL":
            self.logger.critical(message)
        else:
            self.logger.info(message)

    def check_ollama_status(self):
        self.log(f"Checking Ollama status for profile: {self.profile.get('profile_name', 'Unknown')}", "INFO")
        try:
            result = self.handler.check_ollama_status()
            self.log(f"Ollama status checked: {result}", "INFO")
            return result
        except Exception as e:
            self.log(f"Ollama status check failed: {e}", "ERROR")
            raise


class SystemHandler:
    """Handles all system operations."""

    def __init__(self, profile: Dict):
        self.profile = profile

    def check_ollama_installation(self) -> bool:
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

    def install_ollama_guide(self) -> None:
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

    def check_ollama_service(self) -> bool:
        """Check if Ollama service is running."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def start_ollama_service(self) -> bool:
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
                if self.check_ollama_service():
                    console.print("[green]✅ Ollama service started successfully[/green]")
                    return True

            console.print("[red]❌ Ollama service failed to start[/red]")
            return False

        except Exception as e:
            console.print(f"[red]❌ Error starting Ollama service: {e}[/red]")
            return False

    def check_mistral_model(self) -> bool:
        """Check if Mistral model is available."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any("mistral" in model.get("name", "") for model in models)
        except requests.exceptions.RequestException:
            pass
        return False

    def download_mistral_model(self) -> bool:
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
            console.print(f"[red]❌ Error downloading model: {e}[/red]")
            return False

    def check_ollama_status(self) -> bool:
        """Check complete Ollama status."""
        console.print(Panel("🤖 Ollama Status Check", style="bold blue"))

        # Check installation
        if not self.check_ollama_installation():
            console.print("[red]❌ Ollama is not installed[/red]")
            self.install_ollama_guide()
            return False

        console.print("[green]✅ Ollama is installed[/green]")

        # Check service
        if not self.check_ollama_service():
            console.print("[yellow]⚠️ Ollama service is not running[/yellow]")
            if Prompt.ask("Start Ollama service?", choices=["y", "n"], default="y") == "y":
                if not self.start_ollama_service():
                    return False
            else:
                return False

        console.print("[green]✅ Ollama service is running[/green]")

        # Check Mistral model
        if not self.check_mistral_model():
            console.print("[yellow]⚠️ Mistral model is not available[/yellow]")
            if Prompt.ask("Download Mistral model?", choices=["y", "n"], default="y") == "y":
                if not self.download_mistral_model():
                    return False
            else:
                return False

        console.print("[green]✅ Mistral model is available[/green]")
        console.print("[bold green]🎉 Ollama is ready to use![/bold green]")
        return True

    def system_status_and_settings(self) -> None:
        """Show system status and settings."""
        console.print(Panel("⚙️ System Status & Settings", style="bold blue"))

        # Check Ollama status
        ollama_ready = self.check_ollama_status()

        # Show system information
        self.display_system_info()

        # Show profile information
        self.show_profile_info()

        # Show available profiles
        self.show_available_profiles()

        if ollama_ready:
            console.print("\n[bold green]✅ System is ready for job automation![/bold green]")
        else:
            console.print(
                "\n[bold yellow]⚠️ System needs configuration before automation[/bold yellow]"
            )

    def show_profile_info(self) -> None:
        """Show current profile information."""
        console.print(
            f"\n[bold]👤 Current Profile:[/bold] {self.profile.get('profile_name', 'Unknown')}"
        )

        # Create profile info table
        table = Table(title="Profile Information")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        profile_fields = [
            ("Name", self.profile.get("name", "Not set")),
            ("Email", self.profile.get("email", "Not set")),
            ("Phone", self.profile.get("phone", "Not set")),
            ("Location", self.profile.get("location", "Not set")),
            (
                "Keywords",
                ", ".join(self.profile.get("keywords", [])[:3])
                + ("..." if len(self.profile.get("keywords", [])) > 3 else ""),
            ),
            (
                "Skills",
                ", ".join(self.profile.get("skills", [])[:3])
                + ("..." if len(self.profile.get("skills", [])) > 3 else ""),
            ),
        ]

        for field, value in profile_fields:
            table.add_row(field, value)

        console.print(table)

    def show_available_profiles(self) -> None:
        """Show all available profiles."""
        profiles = get_available_profiles()

        if profiles:
            console.print(f"\n[bold]📁 Available Profiles ({len(profiles)}):[/bold]")
            for profile in profiles:
                status = "✅ Current" if profile == self.profile.get("profile_name") else "📁"
                console.print(f"  {status} {profile}")
        else:
            console.print("\n[yellow]No profiles found[/yellow]")

    def display_system_info(self) -> None:
        """Display system information."""
        console.print("[bold]💻 System Information:[/bold]")

        # Get system performance info
        perf_info = self.get_system_performance_info()

        if perf_info:
            table = Table(title="System Performance")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("CPU Usage", f"{perf_info.get('cpu_percent', 0):.1f}%")
            table.add_row("CPU Cores", str(perf_info.get("cpu_count", 0)))
            table.add_row("Memory Usage", f"{perf_info.get('memory_percent', 0):.1f}%")
            table.add_row("Available Memory", f"{perf_info.get('memory_available_gb', 0):.1f} GB")
            table.add_row("Disk Usage", f"{perf_info.get('disk_percent', 0):.1f}%")
            table.add_row("Free Disk Space", f"{perf_info.get('disk_free_gb', 0):.1f} GB")

            console.print(table)
        else:
            console.print("[yellow]System information not available[/yellow]")

    def get_system_performance_info(self) -> Dict:
        """Get system performance information."""
        try:
            import psutil

            # CPU information
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Memory information
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available / (1024**3)  # GB

            # Disk information
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent
            disk_free = disk.free / (1024**3)  # GB

            return {
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "memory_percent": memory_percent,
                "memory_available_gb": memory_available,
                "disk_percent": disk_percent,
                "disk_free_gb": disk_free,
            }
        except ImportError:
            console.print("[yellow]⚠️ psutil not available for system monitoring[/yellow]")
            return {}
        except Exception as e:
            console.print(f"[yellow]⚠️ Error getting system info: {e}[/yellow]")
            return {}

    def validate_profile_completeness(self) -> Dict:
        """Validate profile completeness."""
        required_fields = ["name", "email", "phone", "location", "keywords"]
        missing_fields = []

        for field in required_fields:
            if not self.profile.get(field):
                missing_fields.append(field)

        completeness = {
            "complete": len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "completion_percentage": (
                (len(required_fields) - len(missing_fields)) / len(required_fields)
            )
            * 100,
        }

        return completeness

    def show_profile_completeness(self) -> None:
        """Show profile completeness status."""
        completeness = self.validate_profile_completeness()

        console.print(
            f"\n[bold]📊 Profile Completeness: {completeness['completion_percentage']:.1f}%[/bold]"
        )

        if completeness["complete"]:
            console.print("[green]✅ Profile is complete and ready for automation[/green]")
        else:
            console.print(
                f"[yellow]⚠️ Missing fields: {', '.join(completeness['missing_fields'])}[/yellow]"
            )
            console.print("[yellow]💡 Complete your profile for better automation results[/yellow]")


def summarize_docs_command(args=None):
    """Summarize and update all core documentation files."""
    import subprocess

    result = subprocess.run(["python", "scripts/update_docs.py"], capture_output=True, text=True)
    if result.returncode == 0:
        print("[CLI] Documentation updated successfully.")
    else:
        print("[CLI] Documentation update failed:")
        print(result.stderr)

