#!/usr/bin/env python3
"""
Quick test to verify Eluta scraping works without location parameter.
"""

import json
from rich.console import Console
from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper

console = Console()

def load_profile():
    """Load the Nirajan profile for testing."""
    try:
        with open("profiles/Nirajan/Nirajan.json", "r") as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[red]❌ Error loading profile: {e}[/red]")
        return None

def test_no_location_scraping():
    """Test scraping without location parameter."""
    console.print("[bold blue]🧪 Testing Eluta Scraping WITHOUT Location Parameter[/bold blue]")
    
    # Load profile
    profile = load_profile()
    if not profile:
        return False
    
    # Use only 3 keywords for quick testing
    test_keywords = ["analyst", "python", "sql"]
    profile["keywords"] = test_keywords
    
    console.print(f"[cyan]🔍 Testing keywords: {', '.join(test_keywords)}[/cyan]")
    console.print(f"[cyan]📍 Using Eluta's default location (no location parameter)[/cyan]")
    
    try:
        # Create scraper with single browser context for maximum stealth
        scraper = ComprehensiveElutaScraper(
            profile,
            max_workers=1,  # Single browser context for stealth
            max_jobs_per_keyword=5,  # Small limit for testing
            max_pages_per_keyword=1,  # Just 1 page for quick test
            enable_deep_analysis=False  # Disable for speed
        )
        
        # Run scraping
        jobs = list(scraper.scrape_jobs())
        
        # Display results
        if jobs:
            console.print(f"\n[bold green]✅ SUCCESS! Found {len(jobs)} jobs without location parameter![/bold green]")
            
            # Show sample jobs
            console.print(f"\n[cyan]📋 Sample jobs found:[/cyan]")
            for i, job in enumerate(jobs[:3]):
                console.print(f"  {i+1}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                console.print(f"     📍 {job.get('location', 'N/A')} | 🔍 Keyword: {job.get('search_keyword', 'N/A')}")
                console.print()
            
            return True
        else:
            console.print(f"[yellow]⚠️ No jobs found - may still have detection issues[/yellow]")
            return False
            
    except Exception as e:
        console.print(f"[red]❌ Scraping failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_no_location_scraping()
    
    if success:
        console.print(f"\n[bold green]🎉 No-location scraping works! Ready to use in main application.[/bold green]")
    else:
        console.print(f"\n[bold red]❌ Still having issues. May need further debugging.[/bold red]")
