#!/usr/bin/env python3
"""
System Utilities for AutoJobAgent
Handles signal handling, SSL fixes, and system-level operations.
"""

import signal
import sys
import ssl
import certifi
from rich.console import Console
from typing import Dict, Any
import os
import subprocess
import time
import webbrowser
from pathlib import Path

console = Console()

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(_signum, _frame):
    """Handle keyboard interrupt gracefully."""
    global shutdown_requested
    shutdown_requested = True
    console.print("\n[yellow]Shutdown requested. Finishing current operation...[/yellow]")
    console.print("[yellow]Press Ctrl+C again to force quit[/yellow]")

    # Set up a second handler for force quit
    signal.signal(signal.SIGINT, force_quit_handler)


def force_quit_handler(_signum, _frame):
    """Force quit on second Ctrl+C."""
    console.print("\n[red]Force quit requested. Exiting immediately...[/red]")
    sys.exit(1)


def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, signal_handler)


def fix_ssl_cert_issue():
    """Fix SSL certificate issues."""
    try:
        # Set the SSL certificate path
        ssl._create_default_https_context = ssl._create_unverified_context
        os.environ["SSL_CERT_FILE"] = certifi.where()
        os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
        console.print("[green]✅ SSL certificate configuration updated[/green]")
    except Exception as e:
        console.print(f"[yellow]⚠️ SSL certificate fix failed: {e}[/yellow]")


def get_system_performance_info() -> Dict[str, Any]:
    """Get system performance information."""
    import psutil

    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024**3),
        }
    except ImportError:
        return {
            "error": "psutil not available",
            "cpu_percent": 0,
            "memory_percent": 0,
            "memory_available_gb": 0,
            "disk_percent": 0,
            "disk_free_gb": 0,
        }


def auto_start_dashboard() -> bool:
    """Automatically start the dashboard."""
    try:
        # Check if dashboard is already running
        import requests

        try:
            response = requests.get("http://localhost:8002/", timeout=2)
            if response.status_code == 200:
                console.print("[green]✅ Dashboard is already running[/green]")
                webbrowser.open("http://localhost:8002/")
                return True
        except requests.exceptions.RequestException:
            pass

        # Start dashboard
        console.print("[cyan]🚀 Starting dashboard...[/cyan]")

        # Import and start dashboard
        from src.dashboard.api import start_dashboard

        # Start in background
        import threading

        dashboard_thread = threading.Thread(target=start_dashboard, daemon=True)
        dashboard_thread.start()

        # Wait for dashboard to start
        for _ in range(10):
            time.sleep(1)
            try:
                response = requests.get("http://localhost:8002/", timeout=2)
                if response.status_code == 200:
                    console.print("[green]✅ Dashboard started successfully[/green]")
                    webbrowser.open("http://localhost:8002/")
                    return True
            except requests.exceptions.RequestException:
                continue

        console.print("[red]❌ Failed to start dashboard[/red]")
        return False

    except Exception as e:
        console.print(f"[red]❌ Error starting dashboard: {e}[/red]")
        return False


def is_senior_job(job_title: str) -> bool:
    """Check if job title indicates a senior position."""
    senior_keywords = [
        "senior",
        "sr.",
        "lead",
        "principal",
        "architect",
        "manager",
        "director",
        "head of",
        "chief",
        "vp",
        "vice president",
    ]

    title_lower = job_title.lower()
    return any(keyword in title_lower for keyword in senior_keywords)


def validate_profile_completeness(profile: Dict) -> Dict[str, Any]:
    """Validate profile completeness and return missing fields."""
    required_fields = {
        "name": "Full Name",
        "email": "Email Address",
        "phone": "Phone Number",
        "location": "Location",
        "resume_path": "Resume Path",
        "cover_letter_path": "Cover Letter Path",
    }

    missing_fields = []
    for field, display_name in required_fields.items():
        if not profile.get(field):
            missing_fields.append(display_name)

    return {
        "is_complete": len(missing_fields) == 0,
        "missing_fields": missing_fields,
        "completion_percentage": (
            (len(required_fields) - len(missing_fields)) / len(required_fields)
        )
        * 100,
    }


def prompt_continue() -> bool:
    """Prompt user to continue."""
    from rich.prompt import Confirm

    return Confirm.ask("Continue?")


def select_ats() -> str:
    """Let user select ATS system."""
    from rich.prompt import Prompt

    console.print("\n[bold cyan]Select ATS System:[/bold cyan]")
    ats_options = {
        "1": "workday",
        "2": "icims",
        "3": "greenhouse",
        "4": "lever",
        "5": "bamboohr",
        "6": "auto",
        "7": "manual",
    }

    for key, value in ats_options.items():
        console.print(f"  {key}: {value}")

    choice = Prompt.ask("Select ATS", choices=list(ats_options.keys()), default="6")
    return ats_options[choice]


def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information."""
    try:
        import psutil
        import platform

        # System info
        system_info: Dict[str, Any] = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
        }

        # Performance info
        performance_info = get_system_performance_info()
        system_info.update(performance_info)

        # Process info
        current_pid = os.getpid()
        process = psutil.Process(current_pid)
        system_info.update(
            {
                "process_id": current_pid,
                "process_memory_mb": process.memory_info().rss / (1024**2),
                "process_cpu_percent": process.cpu_percent(),
                "process_status": process.status(),
            }
        )

        return system_info

    except ImportError:
        return {
            "error": "psutil not available",
            "platform": platform.system() if "platform" in globals() else "Unknown",
            "python_version": platform.python_version() if "platform" in globals() else "Unknown",
        }
    except Exception as e:
        return {"error": str(e), "platform": "Unknown", "python_version": "Unknown"}
