#!/usr/bin/env python3
"""
Debug Eluta selectors to find the correct job element selector
"""

import asyncio
from playwright.async_api import async_playwright
from rich.console import Console

console = Console()

async def debug_eluta_selectors():
    """Debug Eluta page to find correct selectors"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        try:
            # Use the working URL
            url = "https://www.eluta.ca/search?q=Python&posted=14"
            console.print(f"[cyan]Loading: {url}[/cyan]")
            
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(3)
            
            # Try different selectors
            selectors_to_try = [
                ".result",
                ".job-result",
                ".organic-job",
                ".job-listing",
                ".job-item",
                "[data-job]",
                ".search-result",
                "article",
                ".listing",
                "div[class*='job']",
                "div[class*='result']",
                "li",
                ".row",
                "tr"
            ]
            
            console.print("\n[bold]Testing selectors:[/bold]")
            
            for selector in selectors_to_try:
                try:
                    elements = await page.query_selector_all(selector)
                    console.print(f"[cyan]{selector:20}[/cyan] -> [green]{len(elements)} elements[/green]")
                    
                    if len(elements) > 0 and len(elements) < 50:  # Reasonable number
                        # Try to extract text from first element
                        first_elem = elements[0]
                        text = await first_elem.text_content()
                        if text and len(text.strip()) > 10:
                            console.print(f"  [yellow]Sample text: {text.strip()[:100]}...[/yellow]")
                            
                except Exception as e:
                    console.print(f"[red]{selector:20} -> Error: {e}[/red]")
            
            # Get page HTML to analyze structure
            console.print("\n[bold]Getting page structure...[/bold]")
            
            # Look for common job-related class names
            html_content = await page.content()
            
            # Search for class names containing job-related keywords
            import re
            job_classes = re.findall(r'class="[^"]*(?:job|result|listing|organic)[^"]*"', html_content)
            unique_classes = list(set(job_classes))[:10]  # First 10 unique
            
            console.print("\n[bold]Found job-related classes:[/bold]")
            for cls in unique_classes:
                console.print(f"[yellow]{cls}[/yellow]")
            
            input("\nPress Enter to close browser...")
            
        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_eluta_selectors())