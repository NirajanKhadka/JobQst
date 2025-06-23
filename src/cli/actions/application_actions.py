"""
Application Actions for AutoJobAgent CLI.

Contains action processors for different application operations:
- Queue applications
- Specific URL applications
- CSV batch applications
"""

from typing import Dict
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from ..handlers.application_handler import ApplicationHandler

console = Console()


class ApplicationActions:
    """Handles all application action processing."""
    
    def __init__(self, profile: Dict):
        self.profile = profile
        self.application_handler = ApplicationHandler(profile)
    
    def apply_from_queue_action(self, args) -> None:
        """Handle apply from queue action."""
        console.print(Panel("📝 Apply from Queue", style="bold blue"))
        self.application_handler.apply_from_queue(args)
    
    def apply_to_specific_url_action(self, args) -> None:
        """Handle apply to specific URL action."""
        console.print(Panel("🎯 Apply to Specific URL", style="bold blue"))
        
        url = Prompt.ask("Enter job URL")
        if url:
            result = self.application_handler.apply_to_specific_job(url, args)
            console.print(f"[bold]Application Status:[/bold] {result}")
        else:
            console.print("[yellow]No URL provided[/yellow]")
    
    def apply_from_csv_action(self, args) -> None:
        """Handle apply from CSV action."""
        console.print(Panel("📊 Apply from CSV", style="bold blue"))
        
        csv_path = Prompt.ask("Enter CSV file path")
        if csv_path:
            self.application_handler.apply_from_csv(csv_path, args)
        else:
            console.print("[yellow]No CSV path provided[/yellow]")
    
    def select_ats_action(self) -> str:
        """Handle ATS selection action."""
        return self.application_handler.select_ats() 