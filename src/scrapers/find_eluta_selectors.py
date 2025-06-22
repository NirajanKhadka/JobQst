#!/usr/bin/env python3
"""
Focused Eluta Selector Discovery
This script specifically finds the correct CSS selectors for Eluta job elements.
"""

import time
from playwright.sync_api import sync_playwright
from rich.console import Console
from rich.panel import Panel

console = Console()

def find_eluta_selectors():
    """Find the exact selectors for Eluta job elements."""
    
    console.print(Panel("🎯 Finding Eluta Job Selectors", style="bold blue"))
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # Navigate to Eluta search
            search_url = "https://www.eluta.ca/search?q=analyst&l=Toronto"
            console.print(f"[cyan]🌐 Navigating to: {search_url}[/cyan]")
            page.goto(search_url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)
            
            # Get page HTML for analysis
            console.print("[cyan]📋 Analyzing HTML structure...[/cyan]")
            
            # Method 1: Look for common job listing patterns
            console.print("\n[bold yellow]METHOD 1: Common Job Patterns[/bold yellow]")
            
            common_selectors = [
                "div[class*='job']",
                "div[class*='listing']", 
                "div[class*='result']",
                "div[class*='item']",
                "div[class*='card']",
                "article",
                ".job",
                ".listing",
                ".result",
                ".item"
            ]
            
            for selector in common_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if 5 <= len(elements) <= 50:  # Reasonable number for job listings
                        console.print(f"[green]✅ {selector}: {len(elements)} elements[/green]")
                        
                        # Test first element
                        if elements:
                            first_elem = elements[0]
                            text = first_elem.inner_text().strip()[:100]
                            console.print(f"   Sample text: {text}...")
                except:
                    pass
            
            # Method 2: Look for elements containing job-like text
            console.print("\n[bold yellow]METHOD 2: Text-Based Detection[/bold yellow]")
            
            # Look for elements containing typical job words
            job_keywords = ["analyst", "toronto", "company", "employer"]
            
            for keyword in job_keywords:
                try:
                    # Find elements containing this keyword
                    elements = page.query_selector_all(f"div:has-text('{keyword}')")
                    if elements:
                        console.print(f"[cyan]Found {len(elements)} divs containing '{keyword}'[/cyan]")
                        
                        # Check their parent structure
                        for i, elem in enumerate(elements[:3]):
                            parent = elem.query_selector("xpath=..")
                            if parent:
                                parent_class = parent.get_attribute("class") or "no-class"
                                console.print(f"   Element {i+1} parent class: {parent_class}")
                except:
                    pass
            
            # Method 3: Inspect actual page source
            console.print("\n[bold yellow]METHOD 3: Page Source Inspection[/bold yellow]")
            
            # Get a portion of the page source to analyze
            page_content = page.content()
            
            # Look for class patterns in the HTML
            import re
            class_matches = re.findall(r'class="([^"]*job[^"]*)"', page_content, re.IGNORECASE)
            class_matches.extend(re.findall(r'class="([^"]*listing[^"]*)"', page_content, re.IGNORECASE))
            class_matches.extend(re.findall(r'class="([^"]*result[^"]*)"', page_content, re.IGNORECASE))
            
            unique_classes = list(set(class_matches))
            console.print(f"[cyan]Found {len(unique_classes)} job-related classes:[/cyan]")
            for cls in unique_classes[:10]:  # Show first 10
                console.print(f"   .{cls}")
            
            # Method 4: Interactive inspection
            console.print("\n[bold yellow]METHOD 4: Interactive Inspection[/bold yellow]")
            console.print("[cyan]Browser is open. Please:[/cyan]")
            console.print("[yellow]1. Right-click on a job listing[/yellow]")
            console.print("[yellow]2. Select 'Inspect Element'[/yellow]")
            console.print("[yellow]3. Note the class names and structure[/yellow]")
            console.print("[yellow]4. Look for clickable elements[/yellow]")
            
            # Wait for user input
            user_selector = input("\n[cyan]Enter the CSS selector you found (or press Enter to skip): [/cyan]")
            
            if user_selector.strip():
                console.print(f"\n[cyan]Testing user-provided selector: {user_selector}[/cyan]")
                try:
                    elements = page.query_selector_all(user_selector)
                    console.print(f"[green]✅ Found {len(elements)} elements with your selector![/green]")
                    
                    if elements:
                        # Test the first few elements
                        for i, elem in enumerate(elements[:3]):
                            console.print(f"\n[cyan]Element {i+1}:[/cyan]")
                            text = elem.inner_text().strip()
                            console.print(f"Text: {text[:200]}...")
                            
                            # Look for links
                            links = elem.query_selector_all("a")
                            console.print(f"Links: {len(links)}")
                            for link in links[:2]:
                                href = link.get_attribute("href") or "no-href"
                                link_text = link.inner_text().strip()[:30]
                                console.print(f"  {href} ('{link_text}...')")
                            
                            # Test clicking
                            console.print(f"[yellow]Testing click on element {i+1}...[/yellow]")
                            try:
                                original_url = page.url
                                elem.click()
                                time.sleep(1)  # Your suggested 1 second wait
                                new_url = page.url
                                
                                if new_url != original_url:
                                    console.print(f"[green]✅ Click worked! New URL: {new_url}[/green]")
                                    
                                    # Go back for next test
                                    page.go_back()
                                    time.sleep(1)
                                else:
                                    console.print(f"[yellow]⚠️ No navigation occurred[/yellow]")
                            except Exception as e:
                                console.print(f"[red]❌ Click failed: {e}[/red]")
                            
                            if i < 2:  # Don't ask for last element
                                input("Press Enter to test next element...")
                
                except Exception as e:
                    console.print(f"[red]❌ Selector test failed: {e}[/red]")
            
            # Method 5: Try common Eluta-specific patterns
            console.print("\n[bold yellow]METHOD 5: Eluta-Specific Patterns[/bold yellow]")
            
            eluta_patterns = [
                "div[data-job]",
                "div[data-id]", 
                "div[id*='job']",
                ".job-listing",
                ".search-result",
                ".job-item",
                "div.listing",
                "div.result"
            ]
            
            for pattern in eluta_patterns:
                try:
                    elements = page.query_selector_all(pattern)
                    if elements:
                        console.print(f"[green]✅ {pattern}: {len(elements)} elements[/green]")
                except:
                    pass
            
            input("\nPress Enter to close browser...")
            
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()

def main():
    """Main function."""
    console.print(Panel("🎯 Eluta Selector Discovery Tool", style="bold blue"))
    console.print("[cyan]This tool will help you find the exact CSS selectors for Eluta job listings.[/cyan]")
    console.print("[yellow]You'll be able to inspect the page manually and test selectors.[/yellow]")
    
    input("\nPress Enter to start...")
    
    find_eluta_selectors()
    
    console.print("\n[bold green]🎉 Selector discovery complete![/bold green]")

if __name__ == "__main__":
    main()
