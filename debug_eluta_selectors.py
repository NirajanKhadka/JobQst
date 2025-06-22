#!/usr/bin/env python3
"""
Debug Eluta page selectors to find the correct job element selectors.
"""

import asyncio
from playwright.async_api import async_playwright
from rich.console import Console

console = Console()

async def debug_selectors():
    """Debug what selectors are available on Eluta."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Navigate to Eluta search
            search_url = "https://www.eluta.ca/search?q=Data%20Analyst&l=&posted=14&pg=1"
            console.print(f"[cyan]🌐 Navigating to: {search_url}[/cyan]")
            
            await page.goto(search_url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(5)
            
            # Check for different selectors
            selectors_to_test = [
                ".organic-job",
                ".job-item",
                ".job-listing",
                ".listing",
                "article",
                "div[class*='job']",
                "div[class*='listing']",
                "div[class*='result']",
                "[data-job-id]",
                "a[href*='/job/']"
            ]
            
            for selector in selectors_to_test:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        console.print(f"[green]✅ {selector}: {len(elements)} elements[/green]")
                        
                        # Show first element text
                        if len(elements) > 0:
                            first_text = await elements[0].inner_text()
                            console.print(f"   Sample: {first_text[:100]}...")
                    else:
                        console.print(f"[red]❌ {selector}: 0 elements[/red]")
                except Exception as e:
                    console.print(f"[yellow]⚠️ {selector}: Error - {e}[/yellow]")
            
            # Get page title and URL
            title = await page.title()
            url = page.url
            console.print(f"\n[cyan]Page title: {title}[/cyan]")
            console.print(f"[cyan]Current URL: {url}[/cyan]")
            
            # Check if we got redirected or hit a CAPTCHA
            if "captcha" in title.lower() or "captcha" in url.lower():
                console.print("[red]❌ CAPTCHA detected![/red]")
            
            # Wait for user input
            input("\nPress Enter to close browser...")
            
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_selectors()) 