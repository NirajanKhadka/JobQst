#!/usr/bin/env python3
"""
Analyze Eluta HTML Structure - Focus on Job Data and Posted Dates
"""

import time
import re
from playwright.sync_api import sync_playwright
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def analyze_eluta_structure():
    """Analyze Eluta HTML structure to understand job data extraction."""
    
    console.print(Panel("🔍 Eluta HTML Structure Analysis", style="bold blue"))
    console.print("[cyan]Analyzing job listings and posted date extraction[/cyan]")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # Navigate to Eluta search with analyst keyword
            search_url = "https://www.eluta.ca/search?q=analyst"
            console.print(f"[cyan]🌐 Navigating to: {search_url}[/cyan]")
            page.goto(search_url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(5)  # Wait for content to load
            
            # Check if we hit a verification page
            if "verification" in page.title().lower():
                console.print("[yellow]⚠️ Hit verification page, waiting for redirect...[/yellow]")
                time.sleep(10)
                page.wait_for_load_state("domcontentloaded")
            
            console.print(f"[green]✅ Page loaded: {page.title()}[/green]")
            
            # 1. Analyze job containers
            console.print("\n[bold yellow]1. JOB CONTAINER ANALYSIS[/bold yellow]")
            
            # Look for .organic-job containers
            organic_jobs = page.query_selector_all(".organic-job")
            console.print(f"[green]✅ Found {len(organic_jobs)} .organic-job containers[/green]")
            
            if organic_jobs:
                # Analyze first job in detail
                first_job = organic_jobs[0]
                console.print(f"\n[bold cyan]FIRST JOB ANALYSIS:[/bold cyan]")
                
                # Get full HTML of first job
                job_html = first_job.inner_html()
                console.print(f"[dim]HTML length: {len(job_html)} characters[/dim]")
                
                # Get text content
                job_text = first_job.inner_text()
                lines = [line.strip() for line in job_text.split('\n') if line.strip()]
                console.print(f"[green]Text lines ({len(lines)}):[/green]")
                for i, line in enumerate(lines):
                    console.print(f"  {i+1}: {line}")
                
                # 2. Analyze posted date patterns
                console.print(f"\n[bold yellow]2. POSTED DATE ANALYSIS[/bold yellow]")
                
                # Look for date patterns in the text
                date_patterns = [
                    r'(\d+)\s*(day|days)\s*ago',
                    r'(\d+)\s*(hour|hours)\s*ago',
                    r'(\d+)\s*(minute|minutes)\s*ago',
                    r'(\d+)\s*(week|weeks)\s*ago',
                    r'(\d+)\s*(month|months)\s*ago',
                    r'(\d+)\s*(year|years)\s*ago'
                ]
                
                for pattern in date_patterns:
                    matches = re.findall(pattern, job_text.lower())
                    if matches:
                        console.print(f"[green]✅ Found date pattern '{pattern}': {matches}[/green]")
                
                # 3. Analyze HTML structure for date elements
                console.print(f"\n[bold yellow]3. HTML STRUCTURE ANALYSIS[/bold yellow]")
                
                # Look for elements that might contain dates
                date_selectors = [
                    "span[class*='date']",
                    "span[class*='time']",
                    "span[class*='posted']",
                    "div[class*='date']",
                    "div[class*='time']",
                    "div[class*='posted']",
                    "time",
                    "[datetime]",
                    "[data-date]",
                    "[title*='date']",
                    "[title*='posted']"
                ]
                
                for selector in date_selectors:
                    try:
                        elements = first_job.query_selector_all(selector)
                        if elements:
                            console.print(f"[green]✅ Found {len(elements)} elements with selector '{selector}'[/green]")
                            for elem in elements[:3]:  # Show first 3
                                text = elem.inner_text().strip()
                                title = elem.get_attribute('title') or ''
                                datetime_attr = elem.get_attribute('datetime') or ''
                                console.print(f"  Text: '{text}' | Title: '{title}' | Datetime: '{datetime_attr}'")
                    except:
                        pass
                
                # 4. Analyze all text for date-like content
                console.print(f"\n[bold yellow]4. TEXT CONTENT DATE ANALYSIS[/bold yellow]")
                
                # Look for any text that looks like a date
                all_text = first_job.inner_text()
                words = all_text.split()
                
                date_indicators = []
                for i, word in enumerate(words):
                    word_lower = word.lower()
                    if any(indicator in word_lower for indicator in ['ago', 'day', 'hour', 'minute', 'week', 'month', 'year']):
                        # Get context around this word
                        start = max(0, i-2)
                        end = min(len(words), i+3)
                        context = ' '.join(words[start:end])
                        date_indicators.append(context)
                
                if date_indicators:
                    console.print(f"[green]✅ Found {len(date_indicators)} potential date indicators:[/green]")
                    for indicator in date_indicators:
                        console.print(f"  '{indicator}'")
                
                # 5. Analyze job title links
                console.print(f"\n[bold yellow]5. JOB TITLE LINK ANALYSIS[/bold yellow]")
                
                links = first_job.query_selector_all("a")
                console.print(f"[green]Found {len(links)} links in job container[/green]")
                
                for i, link in enumerate(links):
                    link_text = link.inner_text().strip()
                    href = link.get_attribute('href') or ''
                    title_attr = link.get_attribute('title') or ''
                    
                    console.print(f"  Link {i+1}:")
                    console.print(f"    Text: '{link_text}'")
                    console.print(f"    Href: '{href}'")
                    console.print(f"    Title: '{title_attr}'")
                
                # 6. Test date extraction logic
                console.print(f"\n[bold yellow]6. DATE EXTRACTION TEST[/bold yellow]")
                
                # Simulate the current extraction logic
                extracted_data = extract_job_data_from_element(first_job)
                console.print(f"[green]Extracted job data:[/green]")
                for key, value in extracted_data.items():
                    console.print(f"  {key}: {value}")
                
                # 7. Test date filtering
                console.print(f"\n[bold yellow]7. DATE FILTERING TEST[/bold yellow]")
                
                is_recent = is_job_recent_enough(extracted_data.get('posted_date', ''))
                console.print(f"[{'green' if is_recent else 'red'}]Job is {'recent' if is_recent else 'too old'} (14-day filter)[/{'green' if is_recent else 'red'}]")
            
            else:
                console.print("[red]❌ No .organic-job containers found[/red]")
                
                # Try alternative selectors
                alternative_selectors = [
                    "div[class*='job']",
                    "div[class*='listing']",
                    "article",
                    ".job",
                    ".listing"
                ]
                
                for selector in alternative_selectors:
                    elements = page.query_selector_all(selector)
                    if elements:
                        console.print(f"[yellow]Found {len(elements)} elements with '{selector}'[/yellow]")
            
        except Exception as e:
            console.print(f"[red]❌ Analysis error: {e}[/red]")
            import traceback
            traceback.print_exc()
        
        finally:
            input("\nPress Enter to close browser...")
            browser.close()

def extract_job_data_from_element(job_elem):
    """Extract job data from a job element (simulating current logic)."""
    try:
        text = job_elem.inner_text().strip()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        job_data = {
            "title": lines[0] if lines else "",
            "company": "",
            "location": "",
            "posted_date": "",
            "summary": ""
        }
        
        # Parse company (remove "TOP EMPLOYER" tag)
        if len(lines) > 1:
            company_line = lines[1]
            job_data["company"] = company_line.replace("TOP EMPLOYER", "").strip()
        
        # Parse location
        if len(lines) > 2:
            job_data["location"] = lines[2]
        
        # Parse summary
        if len(lines) > 3:
            job_data["summary"] = " ".join(lines[3:])[:200]
        
        # Extract posted date from text
        posted_date = extract_posted_date(text)
        job_data["posted_date"] = posted_date
        
        return job_data
        
    except Exception as e:
        console.print(f"[red]Error extracting job data: {e}[/red]")
        return {}

def extract_posted_date(text):
    """Extract posted date from job text."""
    text_lower = text.lower()
    
    # Look for date patterns
    patterns = [
        r'(\d+)\s*(day|days)\s*ago',
        r'(\d+)\s*(hour|hours)\s*ago',
        r'(\d+)\s*(minute|minutes)\s*ago',
        r'(\d+)\s*(week|weeks)\s*ago',
        r'(\d+)\s*(month|months)\s*ago',
        r'(\d+)\s*(year|years)\s*ago'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            number = int(match.group(1))
            unit = match.group(2)
            return f"{number} {unit} ago"
    
    return ""

def is_job_recent_enough(posted_date):
    """Check if job is recent enough (within 14 days)."""
    if not posted_date:
        return True  # Include if no date found
    
    posted_date_lower = posted_date.lower()
    
    # Check for hours/minutes (always recent)
    if "hour" in posted_date_lower or "minute" in posted_date_lower:
        return True
    
    # Check for days
    if "day" in posted_date_lower:
        match = re.search(r'(\d+)\s*day', posted_date_lower)
        if match:
            days_ago = int(match.group(1))
            return days_ago <= 14
    
    # Check for weeks
    if "week" in posted_date_lower:
        match = re.search(r'(\d+)\s*week', posted_date_lower)
        if match:
            weeks_ago = int(match.group(1))
            return weeks_ago <= 2  # 2 weeks = 14 days
    
    # Check for months/years (too old)
    if "month" in posted_date_lower or "year" in posted_date_lower:
        return False
    
    return True  # Default to include if unclear

if __name__ == "__main__":
    analyze_eluta_structure() 