#!/usr/bin/env python3
"""
Debug script to test Eluta search and see what's happening.
"""

import time
import urllib.parse
from playwright.sync_api import sync_playwright
from rich.console import Console

console = Console()

def test_eluta_search():
    """Test basic Eluta search to see what's happening."""
    
    console.print("[bold blue]🔍 Testing Eluta Search Debug[/bold blue]")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Visible to see what's happening
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # Test different search approaches (no location - use Eluta default)
            test_cases = [
                {"keyword": "analyst"},
                {"keyword": "Data Analyst"},
                {"keyword": "Python"},
                {"keyword": "SQL"},
                {"keyword": "developer"},
            ]
            
            for i, test_case in enumerate(test_cases, 1):
                console.print(f"\n[bold cyan]--- Test Case {i}: {test_case['keyword']} (default location) ---[/bold cyan]")

                # Build search URL without location
                base_url = "https://www.eluta.ca/search"
                keyword = test_case["keyword"]

                search_url = f"{base_url}?q={urllib.parse.quote(keyword)}"
                
                console.print(f"[cyan]🌐 URL: {search_url}[/cyan]")
                
                # Navigate
                page.goto(search_url, timeout=30000)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(2)
                
                # Check for different selectors
                selectors_to_test = [
                    ".organic-job",
                    ".job-listing",
                    "[data-job-id]",
                    "a[href*='/job/']",
                    ".listing",
                    "article",
                    "div[class*='job']"
                ]
                
                found_any = False
                for selector in selectors_to_test:
                    elements = page.query_selector_all(selector)
                    if elements:
                        console.print(f"[green]✅ Found {len(elements)} elements with selector: {selector}[/green]")
                        found_any = True
                        
                        # Show first element text
                        if elements:
                            first_text = elements[0].inner_text().strip()[:100]
                            console.print(f"[cyan]📝 First element text: {first_text}...[/cyan]")
                    else:
                        console.print(f"[red]❌ No elements found with selector: {selector}[/red]")
                
                if not found_any:
                    console.print(f"[red]❌ NO JOB ELEMENTS FOUND AT ALL![/red]")
                    
                    # Check page title and content
                    title = page.title()
                    console.print(f"[yellow]📄 Page title: {title}[/yellow]")
                    
                    # Check if there's an error message or different page structure
                    body_text = page.locator("body").inner_text()[:500]
                    console.print(f"[yellow]📝 Page content preview: {body_text}...[/yellow]")
                
                # Wait a bit before next test
                time.sleep(2)
                
        finally:
            input("Press Enter to close browser...")
            browser.close()

if __name__ == "__main__":
    test_eluta_search()
