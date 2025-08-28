#!/usr/bin/env python3
"""
Optimization Setup Command
Simple command to configure JobLens optimization for your system
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.utils.optimization_configurator import auto_configure_optimization
from rich.console import Console

console = Console()

def main():
    """Main setup function"""
    console.print("[bold blue]🚀 JobLens Optimization Setup[/bold blue]")
    console.print("[cyan]Configuring optimization for your system...[/cyan]\n")
    
    try:
        config = auto_configure_optimization(force_reconfigure=True)
        
        console.print("\n[bold green]✅ Optimization setup complete![/bold green]")
        console.print("[cyan]Your JobLens will now use optimized processing by default.[/cyan]")
        
        if config.get("processing", {}).get("enable_batch_processing"):
            console.print("[green]🚀 GPU acceleration enabled![/green]")
        else:
            console.print("[yellow]⚡ CPU-only mode configured[/yellow]")
            
        console.print("\n[bold]Next steps:[/bold]")
        console.print("• Run: [cyan]python main.py YourProfile --action analyze-jobs[/cyan]")
        console.print("• The system will automatically use optimized processing")
        
    except Exception as e:
        console.print(f"[red]❌ Setup failed: {e}[/red]")
        console.print("[yellow]💡 Falling back to standard processing[/yellow]")

if __name__ == "__main__":
    main()
