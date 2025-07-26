#!/usr/bin/env python3
"""
Test script for robust scrapers with timeout handling
Tests both the updated Eluta scraper and new TowardsAI scraper
"""

import asyncio
from rich.console import Console
from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper
from src.scrapers.comprehensive_towardsai_scraper import ComprehensiveTowardsAIScraper

console = Console()


async def test_eluta_scraper():
    """Test the updated Eluta scraper with timeout fixes."""
    console.print("\n[bold blue]🔍 Testing Updated Eluta Scraper[/bold blue]")
    
    try:
        scraper = ComprehensiveElutaScraper("Nirajan")
        
        # Test with limited keywords for quick testing
        original_keywords = scraper.search_terms
        scraper.search_terms = original_keywords[:2]  # Only test first 2 keywords
        scraper.max_pages_per_keyword = 1  # Only 1 page per keyword for testing
        
        console.print(f"[cyan]Testing with keywords: {scraper.search_terms}[/cyan]")
        
        jobs = await scraper.scrape_all_keywords(max_jobs_per_keyword=5)
        
        console.print(f"[green]✅ Eluta test completed! Found {len(jobs)} jobs[/green]")
        console.print(f"[cyan]Timeouts handled: {scraper.stats.get('timeouts', 0)}[/cyan]")
        console.print(f"[cyan]Errors handled: {scraper.stats.get('errors', 0)}[/cyan]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Eluta scraper test failed: {e}[/red]")
        return False


async def test_towardsai_scraper():
    """Test the new TowardsAI scraper."""
    console.print("\n[bold blue]🔍 Testing New TowardsAI Scraper[/bold blue]")
    
    try:
        scraper = ComprehensiveTowardsAIScraper("Nirajan")
        
        # Test with limited keywords for quick testing
        original_keywords = scraper.search_terms
        scraper.search_terms = original_keywords[:2]  # Only test first 2 keywords
        
        console.print(f"[cyan]Testing with keywords: {scraper.search_terms}[/cyan]")
        
        jobs = await scraper.scrape_all_keywords(max_jobs_per_keyword=5)
        
        console.print(f"[green]✅ TowardsAI test completed! Found {len(jobs)} jobs[/green]")
        console.print(f"[cyan]Timeouts handled: {scraper.stats.get('timeouts', 0)}[/cyan]")
        console.print(f"[cyan]Errors handled: {scraper.stats.get('errors', 0)}[/cyan]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ TowardsAI scraper test failed: {e}[/red]")
        return False


async def main():
    """Main test function."""
    console.print("[bold green]🚀 Testing Robust Scrapers with Timeout Handling[/bold green]")
    
    # Test selection
    console.print("\nSelect test to run:")
    console.print("1. Test updated Eluta scraper (with timeout fixes)")
    console.print("2. Test new TowardsAI scraper")
    console.print("3. Test both scrapers")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    results = []
    
    if choice in ["1", "3"]:
        console.print("\n" + "="*60)
        eluta_result = await test_eluta_scraper()
        results.append(("Eluta", eluta_result))
    
    if choice in ["2", "3"]:
        console.print("\n" + "="*60)
        towardsai_result = await test_towardsai_scraper()
        results.append(("TowardsAI", towardsai_result))
    
    # Summary
    console.print("\n" + "="*60)
    console.print("[bold green]📊 Test Results Summary[/bold green]")
    
    for scraper_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        console.print(f"{scraper_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        console.print("\n[bold green]🎉 All tests passed! Scrapers are robust and ready.[/bold green]")
    else:
        console.print("\n[bold red]⚠️ Some tests failed. Check the logs above.[/bold red]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Testing interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Testing failed: {e}[/red]")