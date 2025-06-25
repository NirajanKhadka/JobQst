#!/usr/bin/env python3
"""
Test script for the new multi-browser Eluta scraper.
Tests 2 browser contexts, then can be modified to test 3.
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

def test_multi_browser_scraper(max_workers=2):
    """Test the multi-browser scraper with specified number of workers."""
    console.print(f"\n[bold blue]🧪 Testing Multi-Browser Scraper with {max_workers} browser contexts[/bold blue]")
    
    # Load profile
    profile = load_profile()
    if not profile:
        return False
    
    # Limit keywords for testing
    test_keywords = profile.get("keywords", [])[:1]  # Test with first 1 keyword only
    profile["keywords"] = test_keywords
    
    console.print(f"[cyan]🔍 Testing with keywords: {', '.join(test_keywords)}[/cyan]")
    
    try:
        # Create multi-browser scraper with anti-detection
        scraper = ComprehensiveElutaScraper(
            profile,
            max_workers=max_workers,
            max_jobs_per_keyword=10,  # Reasonable limit for testing
            max_pages_per_keyword=2,  # 2 pages for testing
            enable_deep_analysis=True
        )
        
        # Run scraping
        jobs = list(scraper.scrape_jobs())
        
        # Display results
        if jobs:
            console.print(f"\n[bold green]✅ Multi-browser scraping successful![/bold green]")
            console.print(f"[green]📊 Found {len(jobs)} jobs total[/green]")
            
            # Show job breakdown by keyword
            keyword_counts = {}
            for job in jobs:
                keyword = job.get("search_keyword", "Unknown")
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
            
            console.print(f"\n[cyan]📈 Jobs by keyword:[/cyan]")
            for keyword, count in keyword_counts.items():
                console.print(f"  • {keyword}: {count} jobs")
            
            # Show match scores if available
            match_scores = [job.get("match_score", 0) for job in jobs if job.get("match_score")]
            if match_scores:
                avg_score = sum(match_scores) / len(match_scores)
                console.print(f"\n[cyan]🎯 Average match score: {avg_score:.2f}[/cyan]")
            
            # Show sample jobs
            console.print(f"\n[cyan]📋 Sample jobs:[/cyan]")
            for i, job in enumerate(jobs[:3]):
                console.print(f"  {i+1}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                console.print(f"     📍 {job.get('location', 'N/A')} | 🔗 {job.get('site', 'N/A')}")
                if job.get("match_score"):
                    console.print(f"     🎯 Match: {job.get('match_score', 0):.2f}")
                console.print()
            
            return True
        else:
            console.print(f"[yellow]⚠️ No jobs found with {max_workers} browser contexts[/yellow]")
            return False
            
    except Exception as e:
        console.print(f"[red]❌ Multi-browser scraping failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    console.print("[bold]🧪 Multi-Browser Scraper Test Suite[/bold]")
    
    # Test with 2 browser contexts
    console.print("\n" + "="*60)
    success_2 = test_multi_browser_scraper(max_workers=2)
    
    if success_2:
        console.print(f"\n[green]✅ 2 browser contexts test: PASSED[/green]")
        
        # Ask if user wants to test 3 browser contexts
        console.print(f"\n[cyan]🤔 2 browser contexts worked! Want to test 3 browser contexts?[/cyan]")
        console.print(f"[yellow]Note: This will test if 3 browser contexts improve performance[/yellow]")
        
        try:
            response = input("Test 3 browser contexts? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                console.print("\n" + "="*60)
                success_3 = test_multi_browser_scraper(max_workers=3)
                
                if success_3:
                    console.print(f"\n[green]✅ 3 browser contexts test: PASSED[/green]")
                    console.print(f"[cyan]💡 You can now use 3 browser contexts for better performance![/cyan]")
                else:
                    console.print(f"\n[yellow]⚠️ 3 browser contexts test: FAILED[/yellow]")
                    console.print(f"[cyan]💡 Stick with 2 browser contexts for stability[/cyan]")
            else:
                console.print(f"[cyan]👍 Sticking with 2 browser contexts[/cyan]")
                
        except KeyboardInterrupt:
            console.print(f"\n[yellow]Test interrupted by user[/yellow]")
    else:
        console.print(f"\n[red]❌ 2 browser contexts test: FAILED[/red]")
        console.print(f"[yellow]💡 Try fixing the issues before testing 3 browser contexts[/yellow]")
    
    console.print(f"\n[bold]🏁 Test suite completed![/bold]")

if __name__ == "__main__":
    main()
