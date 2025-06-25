import os
import sys
import time
import json
import importlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class SystemHealthMonitor:
    """
    Comprehensive system health monitoring with automatic recovery.
    Monitors all critical components and provides recovery mechanisms.
    """
    
    def __init__(self, config_path: str = "health_config.json"):
        self.config_path = Path(config_path)
        self.health_log_path = Path("health_logs")
        self.health_log_path.mkdir(exist_ok=True)
        
        self.config = self._load_or_create_config()
        
        self.last_check_time = None
        self.health_status: Dict[str, Any] = {}
        self.recovery_attempts: Dict[str, Any] = {}
        
        console.print("[green]🏥 System Health Monitor initialized[/green]")
    
    def _load_or_create_config(self) -> Dict:
        default_config = {
            "check_interval_seconds": 300,
            "max_recovery_attempts": 3,
            "auto_recovery_enabled": True,
            "components_to_monitor": [
                "database", "disk", "memory", "browser",
                "network", "ollama", "permissions", "dependencies"
            ]
        }
        
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            for key, value in default_config.items():
                config.setdefault(key, value)
            return config
        
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config
    
    def run_comprehensive_health_check(self) -> Dict[str, Dict]:
        console.print("[bold blue]🔍 Running Comprehensive Health Check[/bold blue]")
        health_results = {}
        
        for component in self.config["components_to_monitor"]:
            try:
                console.print(f"[cyan]Checking {component}...[/cyan]")
                module = importlib.import_module(f"src.health_checks.{component}")
                check_func = getattr(module, f"check_{component}_health", None) or getattr(module, f"check_{component}")
                health_results[component] = check_func(self.config)
            except Exception as e:
                health_results[component] = {
                    "status": "error", "message": f"Health check failed: {str(e)}"
                }
        
        self.health_status = health_results
        self.last_check_time = datetime.now()
        self._log_health_results(health_results)
        self._display_health_results(health_results)
        
        if self.config["auto_recovery_enabled"]:
            self._attempt_automatic_recovery(health_results)
            
        return health_results
    
    def _display_health_results(self, results: Dict[str, Dict]) -> None:
        table = Table(title="System Health Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Message", style="white")
        
        for component, result in results.items():
            status = result.get("status", "unknown")
            message = result.get("message", "No message")
            
            status_colors = {"healthy": "green", "warning": "yellow", "critical": "red"}
            status_display = f"[{status_colors.get(status, 'gray')}]{status.upper()}[/]"
            
            table.add_row(component.title(), status_display, message)
        
        console.print(table)
    
    def _log_health_results(self, results: Dict[str, Dict]) -> None:
        log_file = self.health_log_path / f"health_{datetime.now().strftime('%Y%m%d')}.json"
        log_entry = {"timestamp": datetime.now().isoformat(), "results": results}
        
        logs = []
        if log_file.exists():
            with open(log_file, 'r') as f:
                logs = json.load(f)
        
        logs.append(log_entry)
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)

    def _attempt_automatic_recovery(self, results: Dict[str, Dict]):
        # Placeholder for recovery logic
        pass

if __name__ == "__main__":
    health_monitor = SystemHealthMonitor()
    health_monitor.run_comprehensive_health_check()
