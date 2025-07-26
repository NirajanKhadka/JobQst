#!/usr/bin/env python3
"""
Test script to check the correct Eluta.ca URL format
"""

import asyncio
from playwright.async_api import async_playwright
from rich.console import Console

console = Console()

async def test_eluta_urls():
    """Test different Eluta URL formats to find the working one"""
    
    test_urls = [
        # Current scraper URL
        "https://www.eluta.ca/search?q=Python&l=&radius=25&co=CA&type=1&source=&from=&to=&s=3&su=1",
        
        # Simple URL
        "https://www.eluta.ca/search?q=Python",
        
        # With location (Canada)
        "https://www.eluta.ca/search?q=Python&l=Canada",
        
        # With posted date (last 14 days)
        "https://www.eluta.ca/search?q=Python&posted=14",
        
        # Combined
        "https://www.eluta.ca/search?q=Python&l=Canada&posted=14",
        
        # Try the main search page first
        "https://www.eluta.ca/search",
        
        # Try jobs page
        "https://www.eluta.ca/jobs"
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        try:
            for i, url in enumerate(test_urls, 1):
                console.print(f"\n[bold]Test {i}: Testing URL[/bold]")
                console.print(f"[cyan]{url}[/cyan]")
                
                try:
                    await page.goto(url, timeout=15000)
                    await page.wait_for_load_state("domcontentloaded")
                    await asyncio.sleep(2)
                    
                    # Check page title
                    title = await page.title()
                    console.print(f"[green]✅ Page loaded: {title}[/green]")
                    
                    # Check for job results
                    job_elements = await page.query_selector_all(".job-result, .organic-job, .job-listing, .job-item, [data-job], .result")
                    console.print(f"[yellow]Found {len(job_elements)} potential job elements[/yellow]")
                    
                    # Check for search form
                    search_form = await page.query_selector("form, .search-form, #search-form")
                    if search_form:
                        console.print("[blue]✅ Search form found[/blue]")
                    
                    # Check for any error messages
                    error_elements = await page.query_selector_all(".error, .no-results, .not-found")
                    if error_elements:
                        console.print(f"[red]⚠️ Found {len(error_elements)} error elements[/red]")
                    
                    # Wait for user input to continue
                    input(f"Press Enter to continue to next URL...")
                    
                except Exception as e:
                    console.print(f"[red]❌ Failed to load: {e}[/red]")
                    
        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_eluta_urls())