#!/usr/bin/env python3
"""
Fixed Eluta Scraper - Using the correct URL format
"""

import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from rich.console import Console
from src.core.job_database import get_job_db
from src.utils.profile_helpers import load_profile

console = Console()

async def scrape_eluta_jobs(profile_name="Nirajan", keywords=None, max_jobs=11):
    """
    Scrape jobs from Eluta using the correct URL format
    """
    console.print(f"[bold blue]🔍 Scraping Eluta for {profile_name}[/bold blue]")
    
    # Load profile
    profile = load_profile(profile_name)
    if not profile:
        console.print(f"[red]❌ Profile '{profile_name}' not found[/red]")
        return []
    
    # Use provided keywords or default from profile
    if not keywords:
        keywords = ["Data Analyst", "Python"]  # Default 2 keywords as requested
    
    console.print(f"[cyan]Keywords: {keywords}[/cyan]")
    console.print(f"[cyan]Target: {max_jobs} jobs total[/cyan]")
    
    # Get database
    db = get_job_db(profile_name)
    
    jobs_found = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        try:
            for keyword in keywords:
                console.print(f"\n[bold]🔍 Searching: {keyword}[/bold]")
                
                # Use the working URL format from your test
                search_url = f"https://www.eluta.ca/search?q={keyword}&posted=14"
                console.print(f"[cyan]URL: {search_url}[/cyan]")
                
                await page.goto(search_url, timeout=30000)
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(3)
                
                # Find job elements (using the correct selector from debug)
                job_elements = await page.query_selector_all(".organic-job")
                console.print(f"[green]Found {len(job_elements)} job elements[/green]")
                
                # Extract jobs (limit per keyword to reach total target)
                jobs_per_keyword = max_jobs // len(keywords)
                for i, job_elem in enumerate(job_elements[:jobs_per_keyword]):
                    try:
                        # Extract title - try multiple selectors
                        title_elem = await job_elem.query_selector("h3 a, .job-title a, .title a, h2 a")
                        if not title_elem:
                            title_elem = await job_elem.query_selector("h3, h2, .job-title, .title")
                        title = await title_elem.text_content() if title_elem else "Unknown Title"
                        title = title.strip() if title else "Unknown Title"
                        
                        # Extract company - try multiple selectors and fallback to text parsing
                        company_elem = await job_elem.query_selector(".company, .employer, .org")
                        if not company_elem:
                            # Parse from job element text
                            all_text = await job_elem.text_content()
                            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                            # Company is usually after title, look for non-location text
                            company = "Unknown Company"
                            for line in lines[1:]:  # Skip first line (title)
                                if not any(province in line for province in ['ON', 'BC', 'AB', 'QC', 'MB', 'SK', 'NS', 'NB']):
                                    if len(line) > 3 and len(line) < 50:  # Reasonable company name length
                                        company = line
                                        break
                        else:
                            company = await company_elem.text_content()
                        company = company.strip() if company else "Unknown Company"
                        
                        # Extract location - try multiple selectors and text parsing
                        location_elem = await job_elem.query_selector(".location, .loc, .where")
                        if not location_elem:
                            # Look for location patterns in text
                            all_text = await job_elem.text_content()
                            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                            location = "Unknown Location"
                            for line in lines:
                                if any(province in line for province in ['ON', 'BC', 'AB', 'QC', 'MB', 'SK', 'NS', 'NB']):
                                    location = line
                                    break
                                elif any(city in line.lower() for city in ['toronto', 'montreal', 'vancouver', 'calgary', 'ottawa']):
                                    location = line
                                    break
                        else:
                            location = await location_elem.text_content()
                        location = location.strip() if location else "Unknown Location"
                        
                        # Extract URL
                        url_elem = await job_elem.query_selector("h3 a, .job-title a, .title a")
                        job_url = await url_elem.get_attribute("href") if url_elem else ""
                        if job_url and job_url.startswith("/"):
                            job_url = f"https://www.eluta.ca{job_url}"
                        
                        # Create job data
                        job_data = {
                            "title": (title or "Unknown Title").strip(),
                            "company": (company or "Unknown Company").strip(),
                            "location": (location or "Unknown Location").strip(),
                            "url": job_url,
                            "apply_url": job_url,
                            "source": "eluta.ca",
                            "search_keyword": keyword,
                            "status": "scraped",
                            "scraped_at": datetime.now().isoformat(),
                            "posted_date": "Within 14 days",
                            "description": f"Job found via keyword: {keyword}"
                        }
                        
                        jobs_found.append(job_data)
                        console.print(f"[green]✅ {i+1}. {(title or 'Unknown')[:50]} at {(company or 'Unknown')[:25]}[/green]")
                        
                        # Stop if we've reached our target
                        if len(jobs_found) >= max_jobs:
                            break
                            
                    except Exception as e:
                        console.print(f"[red]❌ Error extracting job {i+1}: {e}[/red]")
                
                # Stop if we've reached our target
                if len(jobs_found) >= max_jobs:
                    break
                    
                await asyncio.sleep(2)
            
            # Save to database
            if jobs_found:
                console.print(f"\n[bold]💾 Saving {len(jobs_found)} jobs to database...[/bold]")
                for job in jobs_found:
                    db.add_job(job)
                console.print(f"[green]✅ {len(jobs_found)} jobs saved to database![/green]")
                
                # Show summary
                console.print(f"\n[bold blue]📊 Summary for {profile_name}:[/bold blue]")
                console.print(f"[cyan]Keywords used: {keywords}[/cyan]")
                console.print(f"[cyan]Jobs found: {len(jobs_found)}/{max_jobs}[/cyan]")
                console.print(f"[cyan]Database: profiles/{profile_name}/{profile_name}.db[/cyan]")
            else:
                console.print("[yellow]⚠️ No jobs found[/yellow]")
                
        finally:
            await context.close()
            await browser.close()
    
    return jobs_found

if __name__ == "__main__":
    # Run for Nirajan with 2 keywords, target 11 jobs
    asyncio.run(scrape_eluta_jobs("Nirajan", ["Data Analyst", "Python"], 11))