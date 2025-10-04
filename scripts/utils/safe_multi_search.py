#!/usr/bin/env python3
"""
Safe Multi-Profile Job Search Runner
Safely executes job searches across multiple profiles with IP protection.
"""

import sys
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add src to path
sys.path.append('src')

from utils.multi_profile_rate_limiter import (
    MultiProfileRateLimiter, 
    safe_multi_profile_search
)

console = Console()


def run_safe_multi_profile_search():
    """Run job searches safely across multiple profiles."""
    
    console.print("=== Safe Multi-Profile Job Search ===")
    console.print("This tool prevents IP blocking by managing request timing.")
    
    # Get available profiles
    profiles_dir = Path("profiles")
    if not profiles_dir.exists():
        console.print("[red]No profiles directory found![/red]")
        return
    
    available_profiles = [
        p.name for p in profiles_dir.iterdir() 
        if p.is_dir() and p.name != "__pycache__"
    ]
    
    if not available_profiles:
        console.print("[red]No profiles found![/red]")
        return
    
    # Show current safety status
    limiter = MultiProfileRateLimiter()
    status_report = limiter.get_status_report()
    
    table = Table(title="Profile Safety Status")
    table.add_column("Profile", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Daily Requests", style="yellow")
    table.add_column("Can Search", style="bold")
    
    safe_profiles = []
    for profile in available_profiles:
        if profile in status_report["profiles"]:
            profile_status = status_report["profiles"][profile]
            can_search = profile_status["can_request"]
            daily_count = profile_status["daily_requests"]
            daily_limit = profile_status["daily_limit"]
            
            status_color = "green" if can_search else "red"
            status_text = "Ready" if can_search else "Blocked"
            
            table.add_row(
                profile,
                f"[{status_color}]{status_text}[/{status_color}]",
                f"{daily_count}/{daily_limit}",
                "✅" if can_search else "❌"
            )
            
            if can_search:
                safe_profiles.append(profile)
        else:
            # New profile
            table.add_row(profile, "[green]Ready[/green]", "0/50", "✅")
            safe_profiles.append(profile)
    
    console.print(table)
    
    if not safe_profiles:
        console.print("\n[red]No profiles available for searching right now.[/red]")
        console.print("[yellow]All profiles are in cooldown or have reached daily limits.[/yellow]")
        return
    
    console.print(f"\n[green]{len(safe_profiles)} profiles ready for safe searching.[/green]")
    
    # Ask user which profiles to search
    console.print("\nAvailable profiles for searching:")
    for i, profile in enumerate(safe_profiles, 1):
        console.print(f"  {i}. {profile}")
    
    response = input("\nEnter profile numbers to search (e.g., '1,3,5' or 'all'): ").strip()
    
    if response.lower() == 'all':
        selected_profiles = safe_profiles
    else:
        try:
            indices = [int(x.strip()) - 1 for x in response.split(',')]
            selected_profiles = [safe_profiles[i] for i in indices if 0 <= i < len(safe_profiles)]
        except (ValueError, IndexError):
            console.print("[red]Invalid input![/red]")
            return
    
    if not selected_profiles:
        console.print("[red]No valid profiles selected![/red]")
        return
    
    console.print(f"\n[cyan]Selected profiles: {', '.join(selected_profiles)}[/cyan]")
    
    # Estimate time
    delay_per_profile = 60  # Conservative estimate
    total_time = len(selected_profiles) * delay_per_profile
    console.print(f"[yellow]Estimated time: {total_time//60} minutes[/yellow]")
    console.print("[dim]This includes safety delays to prevent IP blocking.[/dim]")
    
    proceed = input("\nProceed with safe multi-profile search? (y/n): ").strip().lower()
    if proceed != 'y':
        console.print("Search cancelled.")
        return
    
    # Define the search function
    def search_function(profile_name, **kwargs):
        """Run JobSpy pipeline for a profile."""
        import subprocess
        cmd = [
            "conda", "run", "-n", "auto_job", 
            "python", "main.py", profile_name,
            "--action", "jobspy-pipeline",
            "--jobspy-preset", "canada_comprehensive"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    # Execute safe search
    console.print("\n[bold blue]Starting Safe Multi-Profile Search[/bold blue]")
    results = safe_multi_profile_search(selected_profiles, search_function)
    
    # Show results
    console.print("\n=== Search Results ===")
    for profile, result in results.items():
        status = result["status"]
        if status == "success":
            console.print(f"✅ {profile}: Completed successfully")
        elif status == "skipped":
            console.print(f"⏭️ {profile}: Skipped - {result['reason']}")
        else:
            console.print(f"❌ {profile}: Error - {result.get('error', 'Unknown')}")


def show_safety_tips():
    """Show tips for safe multi-profile usage."""
    tips = [
        "Run profiles one at a time with 5+ minute gaps",
        "Don't exceed 50 searches per profile per day",
        "Use different search terms for each profile",
        "Avoid running all profiles at once",
        "Monitor for CAPTCHA or blocking messages",
        "Consider using VPN with different locations"
    ]
    
    console.print("\n=== IP Safety Tips ===")
    for i, tip in enumerate(tips, 1):
        console.print(f"{i}. {tip}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--tips":
        show_safety_tips()
    else:
        run_safe_multi_profile_search()
