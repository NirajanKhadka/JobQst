#!/usr/bin/env python3
"""
Simple test scraper without AI analysis
"""

import asyncio
from src.core.job_database import get_job_db
from src.utils.profile_helpers import load_profile
from playwright.async_api import async_playwright
from rich.console import Console

console = Console()

async def simple_scrape_test():
    """Simple scraping test without AI analysis"""
    console.print("[bold blue]🧪 Simple Scraping Test[/bold blue]")
    
    # Load profile
    profile = load_profile("Nirajan")
    if not profile:
        console.print("[red]❌ Profile not found[/red]")
        return
    
    # Get database
    db = get_job_db("Nirajan")
    
    # Use just 2 keywords for testing
    test_keywords = ["Python", "Data Analyst"]
    console.print(f"[cyan]Testing with keywords: {test_keywords}[/cyan]")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        try:
            jobs_found = []
            
            for keyword in test_keywords:
                console.print(f"\n[bold]🔍 Searching: {keyword}[/bold]")
                
                # Search URL
                search_url = f"https://www.eluta.ca/search?q={keyword}&l=&posted=14&pg=1"
                console.print(f"[cyan]URL: {search_url}[/cyan]")
                
                await page.goto(search_url, timeout=30000)
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)
                
                # Find job elements
                job_elements = await page.query_selector_all(".organic-job")
                console.print(f"[green]Found {len(job_elements)} job elements[/green]")
                
                # Extract basic info from first 3 jobs
                for i, job_elem in enumerate(job_elements[:3]):
                    try:
                        # Extract title
                        title_elem = await job_elem.query_selector(".organic-job__title")
                        title = await title_elem.text_content() if title_elem else "Unknown Title"
                        
                        # Extract company
                        company_elem = await job_elem.query_selector(".organic-job__company")
                        company = await company_elem.text_content() if company_elem else "Unknown Company"
                        
                        # Extract location
                        location_elem = await job_elem.query_selector(".organic-job__location")
                        location = await location_elem.text_content() if location_elem else "Unknown Location"
                        
                        # Create job data
                        job_data = {
                            "title": (title or "Unknown Title").strip(),
                            "company": (company or "Unknown Company").strip(),
                            "location": (location or "Unknown Location").strip(),
                            "url": f"https://www.eluta.ca/job/{i+1}",
                            "search_keyword": keyword,
                            "status": "scraped",
                            "scraped_at": "2025-01-19T20:50:00Z"
                        }
                        
                        jobs_found.append(job_data)
                        console.print(f"[green]✅ {(title or 'Unknown')[:40]} at {(company or 'Unknown')[:20]}[/green]")
                        
                    except Exception as e:
                        console.print(f"[red]❌ Error extracting job {i}: {e}[/red]")
                
                await asyncio.sleep(1)
            
            # Save to database
            if jobs_found:
                console.print(f"\n[bold]💾 Saving {len(jobs_found)} jobs to database...[/bold]")
                for job in jobs_found:
                    db.add_job(job)
                console.print("[green]✅ Jobs saved to database![/green]")
            else:
                console.print("[yellow]⚠️ No jobs found[/yellow]")
                
        finally:
            console.print("\n[yellow]⏸️ Press Enter to close browser...[/yellow]")
            input()
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(simple_scrape_test()) 