#!/usr/bin/env python3
"""
Debug Job Structure on Eluta
Examine the actual HTML structure of job elements to understand URL extraction.
"""

import json
import sys
import os
import urllib.parse
from pathlib import Path

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from playwright.sync_api import sync_playwright
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

console = Console()

def debug_job_structure():
    """Debug the structure of job elements on Eluta."""
    
    # Load profile
    try:
        with open("profiles/Nirajan/Nirajan.json", "r", encoding="utf-8") as f:
            profile = json.load(f)
        keyword = profile.get("keywords", ["Data Analyst"])[0]
    except Exception as e:
        console.print(f"[red]❌ Error loading profile: {e}[/red]")
        keyword = "Data Analyst"
    
    console.print(Panel("🔍 Debugging Eluta Job Structure", style="bold blue"))
    console.print(f"[cyan]🔍 Keyword: {keyword}[/cyan]")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = context.new_page()
        
        # Navigate to search page
        search_url = f"https://www.eluta.ca/search?q={urllib.parse.quote(keyword)}"
        console.print(f"[cyan]📍 Navigating to: {search_url}[/cyan]")
        
        page.goto(search_url, timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        
        import time
        time.sleep(3)
        
        # Find job elements
        job_elements = page.query_selector_all(".organic-job")
        
        if not job_elements:
            console.print("[red]❌ No job elements found[/red]")
            return
        
        console.print(f"[green]✅ Found {len(job_elements)} job elements[/green]")
        
        # Examine first job element
        first_job = job_elements[0]
        
        console.print("\n[bold yellow]1. BASIC TEXT CONTENT:[/bold yellow]")
        text_content = first_job.inner_text().strip()
        console.print(f"[cyan]Text content:[/cyan]")
        console.print(Syntax(text_content[:500] + "..." if len(text_content) > 500 else text_content, "text"))
        
        console.print("\n[bold yellow]2. HTML STRUCTURE:[/bold yellow]")
        html_content = first_job.inner_html()
        console.print(f"[cyan]HTML content (first 1000 chars):[/cyan]")
        console.print(Syntax(html_content[:1000] + "..." if len(html_content) > 1000 else html_content, "html"))
        
        console.print("\n[bold yellow]3. ALL LINKS IN JOB ELEMENT:[/bold yellow]")
        links = first_job.query_selector_all("a")
        console.print(f"[cyan]Found {len(links)} links:[/cyan]")
        
        for i, link in enumerate(links):
            href = link.get_attribute("href")
            text = link.inner_text().strip()
            console.print(f"[green]Link {i+1}:[/green]")
            console.print(f"  Text: {text}")
            console.print(f"  Href: {href}")
            console.print(f"  Classes: {link.get_attribute('class')}")
            console.print()
        
        console.print("\n[bold yellow]4. ALL ELEMENTS WITH HREF:[/bold yellow]")
        href_elements = first_job.query_selector_all("[href]")
        console.print(f"[cyan]Found {len(href_elements)} elements with href:[/cyan]")
        
        for i, elem in enumerate(href_elements):
            href = elem.get_attribute("href")
            tag_name = elem.evaluate("el => el.tagName.toLowerCase()")
            classes = elem.get_attribute("class")
            console.print(f"[green]Element {i+1}:[/green]")
            console.print(f"  Tag: {tag_name}")
            console.print(f"  Href: {href}")
            console.print(f"  Classes: {classes}")
            console.print()
        
        console.print("\n[bold yellow]5. CLICKABLE ELEMENTS:[/bold yellow]")
        clickable_selectors = [
            "a",
            "[onclick]",
            "[role='button']",
            ".clickable",
            ".job-link",
            ".title",
            "h2 a",
            "h3 a",
            ".job-title a"
        ]
        
        for selector in clickable_selectors:
            elements = first_job.query_selector_all(selector)
            if elements:
                console.print(f"[green]✅ {selector}: {len(elements)} elements[/green]")
                for elem in elements:
                    href = elem.get_attribute("href")
                    text = elem.inner_text().strip()
                    console.print(f"  - Text: {text[:50]}...")
                    console.print(f"  - Href: {href}")
            else:
                console.print(f"[red]❌ {selector}: No elements[/red]")
        
        console.print("\n[bold yellow]6. JOB TITLE ELEMENTS:[/bold yellow]")
        title_selectors = [
            "h1", "h2", "h3", "h4",
            ".title", ".job-title", ".position-title",
            "[class*='title']", "[class*='job']"
        ]
        
        for selector in title_selectors:
            elements = first_job.query_selector_all(selector)
            if elements:
                console.print(f"[green]✅ {selector}: {len(elements)} elements[/green]")
                for elem in elements:
                    text = elem.inner_text().strip()
                    href = elem.get_attribute("href")
                    console.print(f"  - Text: {text}")
                    console.print(f"  - Href: {href}")
        
        input("\nPress Enter to close browser...")
        browser.close()

if __name__ == "__main__":
    debug_job_structure() 