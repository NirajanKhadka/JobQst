#!/usr/bin/env python3
"""
Get First Job Link from Eluta
Load the Eluta scraper and extract the link of the first job found.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Optional

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from playwright.sync_api import sync_playwright
    from rich.console import Console
    from rich.panel import Panel
    from src.scrapers.fast_eluta_producer import FastElutaProducer
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please install required dependencies:")
    print("pip install playwright rich")
    print("playwright install chromium")
    sys.exit(1)

console = Console()

def load_profile(profile_path: str = "profiles/Nirajan/Nirajan.json") -> Optional[Dict]:
    """Load user profile from JSON file."""
    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)
        console.print(f"[green]✅ Profile loaded: {profile.get('profile_name', 'Unknown')}[/green]")
        return profile
    except FileNotFoundError:
        console.print(f"[red]❌ Profile file not found: {profile_path}[/red]")
        return None
    except json.JSONDecodeError as e:
        console.print(f"[red]❌ Invalid JSON in profile: {e}[/red]")
        return None
    except Exception as e:
        console.print(f"[red]❌ Error loading profile: {e}[/red]")
        return None

def get_first_job_link(profile: Dict) -> Optional[str]:
    """Get the link of the first job from Eluta for the first keyword."""
    try:
        # Initialize producer
        producer = FastElutaProducer(profile)
        
        if not producer.keywords:
            console.print("[red]❌ No keywords found in profile[/red]")
            return None
        
        keyword = producer.keywords[0]
        console.print(f"[cyan]🔍 Searching for keyword: {keyword}[/cyan]")
        
        # Launch browser and get first job
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,  # Visible for debugging
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--disable-automation",
                    "--disable-extensions",
                    "--no-first-run",
                    "--disable-default-apps",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding"
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = context.new_page()
            
            # Build search URL
            import urllib.parse
            search_url = f"{producer.base_url}?q={urllib.parse.quote(keyword)}"
            console.print(f"[cyan]📍 Navigating to: {search_url}[/cyan]")
            
            # Navigate to search page
            page.goto(search_url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            
            # Wait a bit for content to load
            import time
            time.sleep(3)
            
            # Find job elements
            job_elements = page.query_selector_all(".organic-job")
            
            if not job_elements:
                console.print("[yellow]⚠️ No jobs found on the page[/yellow]")
                return None
            
            console.print(f"[green]✅ Found {len(job_elements)} jobs[/green]")
            
            # Get first job
            first_job_elem = job_elements[0]
            job_data = producer._extract_raw_job_data(first_job_elem, keyword, 1, 1)
            
            if job_data and job_data.get("url"):
                job_url = job_data["url"]
                console.print(f"[bold green]🎯 First job link: {job_url}[/bold green]")
                console.print(f"[cyan]📋 Job title: {job_data.get('title', 'N/A')}[/cyan]")
                console.print(f"[cyan]🏢 Company: {job_data.get('company', 'N/A')}[/cyan]")
                console.print(f"[cyan]📍 Location: {job_data.get('location', 'N/A')}[/cyan]")
                return job_url
            else:
                console.print("[yellow]⚠️ No URL found in first job[/yellow]")
                return None
                
    except Exception as e:
        console.print(f"[red]❌ Error getting job link: {e}[/red]")
        import traceback
        traceback.print_exc()
        return None

def check_dependencies():
    """Check if all required dependencies are available."""
    console.print(Panel("🔍 Checking Dependencies", style="bold blue"))
    
    dependencies = {
        "playwright": "Browser automation",
        "rich": "Console output formatting",
        "json": "JSON parsing (built-in)",
        "pathlib": "Path handling (built-in)",
        "urllib": "URL encoding (built-in)",
        "time": "Time delays (built-in)",
        "threading": "Threading (built-in)",
        "datetime": "Date/time (built-in)"
    }
    
    missing_deps = []
    
    for dep, description in dependencies.items():
        try:
            if dep in ["json", "pathlib", "urllib", "time", "threading", "datetime"]:
                # Built-in modules
                __import__(dep)
                console.print(f"[green]✅ {dep}: {description}[/green]")
            else:
                # External modules
                __import__(dep)
                console.print(f"[green]✅ {dep}: {description}[/green]")
        except ImportError:
            console.print(f"[red]❌ {dep}: {description} - MISSING[/red]")
            missing_deps.append(dep)
    
    if missing_deps:
        console.print(f"\n[yellow]⚠️ Missing dependencies: {', '.join(missing_deps)}[/yellow]")
        console.print("Install with: pip install " + " ".join(missing_deps))
        if "playwright" in missing_deps:
            console.print("Then run: playwright install chromium")
        return False
    else:
        console.print(f"\n[bold green]✅ All dependencies available![/bold green]")
        return True

def main():
    """Main function."""
    console.print(Panel("🎯 Get First Job Link from Eluta", style="bold blue"))
    
    # Check dependencies first
    if not check_dependencies():
        console.print("[red]❌ Dependencies check failed. Please install missing packages.[/red]")
        return
    
    # Load profile
    profile = load_profile()
    if not profile:
        console.print("[red]❌ Failed to load profile. Exiting.[/red]")
        return
    
    # Get first job link
    job_link = get_first_job_link(profile)
    
    if job_link:
        console.print(Panel(f"🎯 SUCCESS! First job link: {job_link}", style="bold green"))
    else:
        console.print(Panel("❌ Failed to get job link", style="bold red"))

if __name__ == "__main__":
    main() 