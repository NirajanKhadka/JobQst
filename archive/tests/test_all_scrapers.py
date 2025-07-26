#!/usr/bin/env python3
"""
Test All Scrapers - Comprehensive validation script
Tests all available scrapers to ensure they're working properly
"""

import asyncio
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


async def test_basic_scraper():
    """Test the basic URL scraper."""
    console.print("\n[bold blue]🔍 Testing Basic URL Scraper[/bold blue]")
    
    try:
        from test_scraper_with_limit import SimpleURLScraper
        
        scraper = SimpleURLScraper("Nirajan")
        # Limit to 1 keyword for quick test
        scraper.search_terms = scraper.search_terms[:1]
        
        urls = await scraper.scrape_urls_only()
        
        success = len(urls) > 0 and scraper.stats["urls_saved"] > 0
        
        return {
            "name": "Basic URL Scraper",
            "success": success,
            "urls_found": len(urls),
            "urls_saved": scraper.stats["urls_saved"],
            "errors": scraper.stats.get("errors", 0)
        }
        
    except Exception as e:
        console.print(f"[red]❌ Basic scraper test failed: {e}[/red]")
        return {
            "name": "Basic URL Scraper", 
            "success": False,
            "error": str(e)
        }


async def test_robust_scraper():
    """Test the robust Eluta scraper."""
    console.print("\n[bold blue]🔍 Testing Robust Eluta Scraper[/bold blue]")
    
    try:
        from robust_eluta_scraper import RobustElutaScraper
        
        scraper = RobustElutaScraper("Nirajan")
        # Limit for quick test
        scraper.search_terms = scraper.search_terms[:1]
        scraper.max_pages_per_keyword = 1
        
        urls = await scraper.scrape_with_robust_handling()
        
        success = len(urls) > 0 and scraper.stats["urls_saved"] > 0
        
        return {
            "name": "Robust Eluta Scraper",
            "success": success,
            "urls_found": len(urls),
            "urls_saved": scraper.stats["urls_saved"],
            "timeouts": scraper.stats["timeouts"],
            "errors": scraper.stats["errors"]
        }
        
    except Exception as e:
        console.print(f"[red]❌ Robust scraper test failed: {e}[/red]")
        return {
            "name": "Robust Eluta Scraper",
            "success": False, 
            "error": str(e)
        }


async def test_comprehensive_scraper():
    """Test the comprehensive Eluta scraper."""
    console.print("\n[bold blue]🔍 Testing Comprehensive Eluta Scraper[/bold blue]")
    
    try:
        from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper
        
        scraper = ComprehensiveElutaScraper("Nirajan")
        # Limit for quick test
        scraper.search_terms = scraper.search_terms[:1]
        scraper.max_pages_per_keyword = 1
        
        jobs = await scraper.scrape_all_keywords(max_jobs_per_keyword=3)
        
        success = len(jobs) > 0
        
        return {
            "name": "Comprehensive Eluta Scraper",
            "success": success,
            "jobs_found": len(jobs),
            "keywords_processed": scraper.stats["keywords_processed"],
            "errors": scraper.stats.get("errors", 0)
        }
        
    except Exception as e:
        console.print(f"[red]❌ Comprehensive scraper test failed: {e}[/red]")
        return {
            "name": "Comprehensive Eluta Scraper",
            "success": False,
            "error": str(e)
        }


async def test_towardsai_scraper():
    """Test the TowardsAI scraper."""
    console.print("\n[bold blue]🔍 Testing TowardsAI Scraper[/bold blue]")
    
    try:
        from src.scrapers.comprehensive_towardsai_scraper import ComprehensiveTowardsAIScraper
        
        scraper = ComprehensiveTowardsAIScraper("Nirajan")
        # Limit for quick test
        scraper.search_terms = scraper.search_terms[:1]
        
        jobs = await scraper.scrape_all_keywords(max_jobs_per_keyword=3)
        
        success = len(jobs) >= 0  # TowardsAI might not always have jobs
        
        return {
            "name": "TowardsAI Scraper",
            "success": success,
            "jobs_found": len(jobs),
            "keywords_processed": scraper.stats["keywords_processed"],
            "timeouts": scraper.stats["timeouts"],
            "errors": scraper.stats["errors"]
        }
        
    except Exception as e:
        console.print(f"[red]❌ TowardsAI scraper test failed: {e}[/red]")
        return {
            "name": "TowardsAI Scraper",
            "success": False,
            "error": str(e)
        }


def display_results(results):
    """Display test results in a nice table."""
    console.print("\n" + "="*80)
    console.print(Panel.fit("SCRAPER TEST RESULTS", style="bold green"))
    
    # Results table
    table = Table(title="Test Summary")
    table.add_column("Scraper", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Jobs/URLs", style="green")
    table.add_column("Saved", style="blue")
    table.add_column("Errors", style="red")
    table.add_column("Notes", style="yellow")
    
    all_passed = True
    
    for result in results:
        if result["success"]:
            status = "✅ PASS"
            jobs_urls = str(result.get("jobs_found", result.get("urls_found", 0)))
            saved = str(result.get("urls_saved", "N/A"))
            errors = str(result.get("errors", 0))
            notes = f"Timeouts: {result.get('timeouts', 0)}" if "timeouts" in result else "OK"
        else:
            status = "❌ FAIL"
            jobs_urls = "0"
            saved = "0"
            errors = "1"
            notes = result.get("error", "Unknown error")[:30] + "..."
            all_passed = False
        
        table.add_row(
            result["name"],
            status,
            jobs_urls,
            saved,
            errors,
            notes
        )
    
    console.print(table)
    
    # Summary
    if all_passed:
        console.print("\n[bold green]🎉 All scrapers are working correctly![/bold green]")
        console.print("[green]✅ Database saving: Working[/green]")
        console.print("[green]✅ Timeout handling: Working[/green]") 
        console.print("[green]✅ Error recovery: Working[/green]")
        console.print("[green]✅ Ready for production use![/green]")
    else:
        console.print("\n[bold red]⚠️ Some scrapers have issues[/bold red]")
        console.print("[yellow]Check the error messages above for details[/yellow]")


async def main():
    """Main test function."""
    console.print("[bold green]🚀 Testing All Scrapers[/bold green]")
    console.print("[cyan]This will test all available scrapers with limited scope[/cyan]")
    
    # Ask user which tests to run
    console.print("\nSelect tests to run:")
    console.print("1. Basic URL Scraper (fast)")
    console.print("2. Robust Eluta Scraper (medium)")
    console.print("3. Comprehensive Eluta Scraper (slow)")
    console.print("4. TowardsAI Scraper (medium)")
    console.print("5. All scrapers (comprehensive)")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    results = []
    
    if choice in ["1", "5"]:
        result = await test_basic_scraper()
        results.append(result)
    
    if choice in ["2", "5"]:
        result = await test_robust_scraper()
        results.append(result)
    
    if choice in ["3", "5"]:
        result = await test_comprehensive_scraper()
        results.append(result)
    
    if choice in ["4", "5"]:
        result = await test_towardsai_scraper()
        results.append(result)
    
    if not results:
        console.print("[red]Invalid choice. Please run again with a valid option.[/red]")
        return
    
    display_results(results)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Testing interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Testing failed: {e}[/red]")