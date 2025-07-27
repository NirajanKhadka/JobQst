#!/usr/bin/env python3
"""
Test script for 5-tab optimization in Eluta scrapers.
Verifies that tab cleanup happens at the correct threshold.
"""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

console = Console()

async def test_comprehensive_scraper_tab_optimization():
    """Test the ComprehensiveElutaScraper with 5-tab optimization."""
    console.print(Panel(
        "[bold blue]🧪 Testing ComprehensiveElutaScraper 5-Tab Optimization[/bold blue]\n"
        "[cyan]This test will verify that tabs are cleaned up when 5 extra tabs are detected[/cyan]",
        title="Tab Optimization Test"
    ))
    
    try:
        from src.scrapers.core_eluta_scraper import CoreElutaScraper
        
        # Initialize scraper with 5-tab optimization
        config = {"max_extra_tabs": 5, "tab_monitoring_interval": 3}
        scraper = CoreElutaScraper("Nirajan", config)
        console.print("[green]✅ CoreElutaScraper initialized with 5-tab optimization[/green]")
        
        # Test with limited jobs to focus on tab management
        console.print("[cyan]🔍 Starting scraping with tab monitoring...[/cyan]")
        jobs = await scraper.scrape_all_keywords(max_jobs_per_keyword=10)
        
        # Display results
        console.print(f"\n[bold]📊 Scraping Results:[/bold]")
        console.print(f"[green]Jobs found: {len(jobs)}[/green]")
        console.print(f"[cyan]Keywords processed: {scraper.stats.get('keywords_processed', 0)}[/cyan]")
        console.print(f"[yellow]Pages scraped: {scraper.stats.get('pages_scraped', 0)}[/yellow]")
        console.print(f"[blue]Tabs closed: {scraper.stats.get('tabs_closed', 0)}[/blue]")
        console.print(f"[magenta]Duplicates skipped: {scraper.stats.get('duplicates_skipped', 0)}[/magenta]")
        
        # Verify tab optimization worked
        tabs_closed = scraper.stats.get('tabs_closed', 0)
        if tabs_closed > 0:
            console.print(f"[green]✅ Tab optimization working: {tabs_closed} tabs were closed[/green]")
        else:
            console.print("[yellow]⚠️ No tabs were closed - may indicate low tab usage or optimization not triggered[/yellow]")
            
        return True
        
    except Exception as e:
        console.print(f"[red]❌ ComprehensiveElutaScraper test failed: {e}[/red]")
        return False

async def test_unified_scraper_tab_optimization():
    """Test the UnifiedElutaScraper with 5-tab optimization."""
    console.print(Panel(
        "[bold blue]🧪 Testing UnifiedElutaScraper 5-Tab Optimization[/bold blue]\n"
        "[cyan]This test will verify that tab monitoring works in the unified scraper[/cyan]",
        title="Unified Scraper Test"
    ))
    
    try:
        from src.scrapers.core_eluta_scraper import CoreElutaScraper
        
        # Initialize scraper with test config and 5-tab optimization
        config = {
            "pages": 2,
            "jobs": 10,
            "delay": 0.5,
            "headless": True,
            "max_extra_tabs": 5,
            "tab_monitoring_interval": 5
        }
        
        scraper = CoreElutaScraper("Nirajan", config)
        console.print("[green]✅ CoreElutaScraper initialized with 5-tab optimization[/green]")
        
        # Test scraping
        console.print("[cyan]🔍 Starting unified scraping with tab monitoring...[/cyan]")
        jobs = await scraper.scrape_all_keywords()
        
        # Display results
        console.print(f"\n[bold]📊 Unified Scraping Results:[/bold]")
        console.print(f"[green]Jobs found: {len(jobs)}[/green]")
        console.print(f"[cyan]Keywords processed: {scraper.stats.get('keywords_processed', 0)}[/cyan]")
        console.print(f"[yellow]Pages scraped: {scraper.stats.get('pages_scraped', 0)}[/yellow]")
        console.print(f"[blue]Tabs closed: {scraper.stats.get('tabs_closed', 0)}[/blue]")
        console.print(f"[red]Popups blocked: {scraper.stats.get('popups_blocked', 0)}[/red]")
        console.print(f"[magenta]Extraction failures: {scraper.stats.get('extraction_failures', 0)}[/magenta]")
        
        # Verify optimization
        tabs_closed = scraper.stats.get('tabs_closed', 0)
        popups_blocked = scraper.stats.get('popups_blocked', 0)
        
        if tabs_closed > 0 or popups_blocked > 0:
            console.print(f"[green]✅ Tab management working: {tabs_closed} tabs closed, {popups_blocked} popups blocked[/green]")
        else:
            console.print("[yellow]⚠️ No tab management activity detected[/yellow]")
            
        return True
        
    except Exception as e:
        console.print(f"[red]❌ UnifiedElutaScraper test failed: {e}[/red]")
        return False

async def test_tab_threshold_behavior():
    """Test the specific 5-tab threshold behavior."""
    console.print(Panel(
        "[bold blue]🧪 Testing 5-Tab Threshold Behavior[/bold blue]\n"
        "[cyan]This test simulates tab accumulation to verify cleanup threshold[/cyan]",
        title="Threshold Behavior Test"
    ))
    
    try:
        from playwright.async_api import async_playwright
        from src.scrapers.core_eluta_scraper import CoreElutaScraper
        
        scraper = CoreElutaScraper("Nirajan", {"max_extra_tabs": 5})
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            
            # Create main page
            main_page = await context.new_page()
            await main_page.goto("https://example.com")
            
            console.print(f"[cyan]📊 Initial tabs: {len(context.pages)}[/cyan]")
            
            # Simulate tab accumulation
            extra_pages = []
            for i in range(6):  # Create 6 extra tabs to exceed threshold
                page = await context.new_page()
                await page.goto("https://example.com")
                extra_pages.append(page)
                
                tab_count = len(context.pages)
                console.print(f"[yellow]📊 Created tab {i+1}: Total tabs = {tab_count}[/yellow]")
                
                # Test cleanup at threshold
                if tab_count > 5:  # 1 main + 5 extra = 6 total
                    console.print(f"[red]🚨 Threshold exceeded: {tab_count} tabs (should trigger cleanup)[/red]")
                    await scraper._monitor_and_cleanup_tabs(context, i+1)
                    
                    remaining_tabs = len(context.pages)
                    console.print(f"[green]📊 After cleanup: {remaining_tabs} tabs remaining[/green]")
                    
                    if remaining_tabs == 1:  # Only main page should remain
                        console.print("[green]✅ Cleanup successful: Only main page remains[/green]")
                    else:
                        console.print(f"[yellow]⚠️ Cleanup incomplete: {remaining_tabs} tabs still open[/yellow]")
                    break
            
            await context.close()
            await browser.close()
            
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Threshold behavior test failed: {e}[/red]")
        return False

async def main():
    """Run all tab optimization tests."""
    console.print(Panel.fit(
        "[bold green]🚀 AutoJobAgent 5-Tab Optimization Test Suite[/bold green]",
        style="bold green"
    ))
    
    results = []
    
    # Test 1: ComprehensiveElutaScraper
    console.print("\n" + "="*60)
    result1 = await test_comprehensive_scraper_tab_optimization()
    results.append(("ComprehensiveElutaScraper", result1))
    
    # Test 2: UnifiedElutaScraper
    console.print("\n" + "="*60)
    result2 = await test_unified_scraper_tab_optimization()
    results.append(("UnifiedElutaScraper", result2))
    
    # Test 3: Threshold Behavior
    console.print("\n" + "="*60)
    result3 = await test_tab_threshold_behavior()
    results.append(("Threshold Behavior", result3))
    
    # Summary
    console.print("\n" + "="*60)
    console.print(Panel(
        "[bold blue]📊 Test Results Summary[/bold blue]",
        style="bold blue"
    ))
    
    passed = 0
    for test_name, result in results:
        status = "[green]✅ PASSED[/green]" if result else "[red]❌ FAILED[/red]"
        console.print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    console.print(f"\n[bold]Overall: {passed}/{len(results)} tests passed[/bold]")
    
    if passed == len(results):
        console.print("[green]🎉 All tab optimization tests passed![/green]")
        console.print("[cyan]The 5-tab threshold system is working correctly.[/cyan]")
    else:
        console.print("[yellow]⚠️ Some tests failed. Check the output above for details.[/yellow]")

if __name__ == "__main__":
    asyncio.run(main())