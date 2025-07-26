#!/usr/bin/env python3
"""
Robust Job Scraper with Popup Handling
Focuses on extracting job details from Workday, Greenhouse, and Lever ATS systems
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import asyncio
import json
from playwright.async_api import async_playwright
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import sqlite3
from datetime import datetime

console = Console()

async def scrape_job_details(url, page):
    """Scrape job details using a robust approach with popup handling."""
    
    job_data = {
        "title": "",
        "company": "",
        "location": "",
        "salary_range": "",
        "job_description": "",
        "job_type": "",
        "keywords": "",
        "requirements": "",
        "benefits": "",
        "remote_option": "Unknown",
        "scraped_at": datetime.now().isoformat()
    }
    
    try:
        # Navigate to the page
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(2)
        
        # Handle cookie popups
        await handle_cookie_popups(page)
        
        # Wait for content to load
        await asyncio.sleep(1)
        
        # Determine ATS type
        ats_type = determine_ats_type(url)
        
        # Extract job details based on ATS type
        if ats_type == "workday":
            await extract_workday_job_details(page, job_data)
        elif ats_type == "greenhouse":
            await extract_greenhouse_job_details(page, job_data)
        elif ats_type == "lever":
            await extract_lever_job_details(page, job_data)
        else:
            # Generic extraction
            await extract_generic_job_details(page, job_data)
        
        # Extract keywords from job description
        if job_data["job_description"]:
            job_data["keywords"] = extract_keywords(job_data["job_description"])
        
        # Check for remote indicators
        if "remote" in job_data["job_description"].lower() or "work from home" in job_data["job_description"].lower():
            job_data["remote_option"] = "Remote"
            
        return job_data
        
    except Exception as e:
        console.print(f"[red]❌ Error scraping job details: {e}[/red]")
        return job_data

def determine_ats_type(url):
    """Determine the ATS type from the URL."""
    url_lower = url.lower()
    
    if "workday" in url_lower:
        return "workday"
    elif "greenhouse" in url_lower:
        return "greenhouse"
    elif "lever.co" in url_lower:
        return "lever"
    else:
        return "generic"

async def handle_cookie_popups(page):
    """Handle common cookie consent popups."""
    try:
        # Common cookie accept button selectors
        cookie_selectors = [
            'button:has-text("Accept")',
            'button:has-text("Accept All")',
            'button:has-text("Accept Cookies")',
            'button:has-text("I Accept")',
            'button:has-text("Allow All")',
            'button:has-text("Allow")',
            'button:has-text("Agree")',
            'button:has-text("Agree to All")',
            'button:has-text("OK")',
            'button:has-text("Continue")',
            'button:has-text("Got it")',
            'button:has-text("I understand")',
            'button:has-text("I agree")',
            'a:has-text("Accept")',
            'a:has-text("Accept All")',
            '[id*="accept"]',
            '[class*="accept"]',
            '[id*="cookie-accept"]',
            '[class*="cookie-accept"]',
            '[aria-label*="Accept"]',
            '[aria-label*="accept"]',
            '[data-testid*="accept"]',
        ]
        
        for selector in cookie_selectors:
            try:
                # Check if selector exists with a short timeout
                button = await page.wait_for_selector(selector, timeout=1000)
                if button:
                    console.print(f"[yellow]🍪 Found cookie popup, accepting...[/yellow]")
                    await button.click()
                    await asyncio.sleep(1)  # Wait for popup to disappear
                    return True
            except:
                continue
                
        return False
    except Exception as e:
        console.print(f"[yellow]⚠️ Error handling cookie popups: {e}[/yellow]")
        return False

async def extract_workday_job_details(page, job_data):
    """Extract job details from Workday ATS."""
    try:
        # Title
        title_selector = '[data-automation-id="jobTitle"]'
        title = await extract_text(page, title_selector)
        if title:
            job_data["title"] = title
            
        # Company
        company_selector = '[data-automation-id="companyTitle"]'
        company = await extract_text(page, company_selector)
        if company:
            job_data["company"] = company
            
        # Location
        location_selector = '[data-automation-id="location"]'
        location = await extract_text(page, location_selector)
        if location:
            job_data["location"] = location
            
        # Job Description
        description_selector = '[data-automation-id="jobDescription"]'
        description = await extract_text(page, description_selector)
        if description:
            job_data["job_description"] = description
            
        # Salary - often not directly available in Workday
        salary_selector = '[data-automation-id="formField-compensationRange"]'
        salary = await extract_text(page, salary_selector)
        if salary:
            job_data["salary_range"] = salary
            
        # Job Type
        job_type_selector = '[data-automation-id="formField-employmentType"]'
        job_type = await extract_text(page, job_type_selector)
        if job_type:
            job_data["job_type"] = job_type
            
        # If we still don't have a title, try a more generic approach
        if not job_data["title"]:
            title = await extract_text(page, "h1")
            if title:
                job_data["title"] = title
                
        # If we still don't have a description, try to get all content
        if not job_data["job_description"]:
            main_content = await extract_text(page, "main")
            if main_content:
                job_data["job_description"] = main_content
                
    except Exception as e:
        console.print(f"[yellow]⚠️ Error extracting Workday job details: {e}[/yellow]")

async def extract_greenhouse_job_details(page, job_data):
    """Extract job details from Greenhouse ATS."""
    try:
        # Title
        title_selector = '.app-title'
        title = await extract_text(page, title_selector)
        if title:
            job_data["title"] = title
            
        # Company
        company_selector = '.company'
        company = await extract_text(page, company_selector)
        if company:
            job_data["company"] = company
            
        # Location
        location_selector = '.location'
        location = await extract_text(page, location_selector)
        if location:
            job_data["location"] = location
            
        # Job Description
        description_selector = '#content'
        description = await extract_text(page, description_selector)
        if description:
            job_data["job_description"] = description
            
        # If we still don't have a title, try a more generic approach
        if not job_data["title"]:
            title = await extract_text(page, "h1")
            if title:
                job_data["title"] = title
                
    except Exception as e:
        console.print(f"[yellow]⚠️ Error extracting Greenhouse job details: {e}[/yellow]")

async def extract_lever_job_details(page, job_data):
    """Extract job details from Lever ATS."""
    try:
        # Title
        title_selector = '.posting-headline h2'
        title = await extract_text(page, title_selector)
        if title:
            job_data["title"] = title
            
        # Company
        company_selector = '.posting-headline h2 + div'
        company = await extract_text(page, company_selector)
        if company:
            job_data["company"] = company
            
        # Location
        location_selector = '.location'
        location = await extract_text(page, location_selector)
        if location:
            job_data["location"] = location
            
        # Job Description
        description_selector = '.posting-description'
        description = await extract_text(page, description_selector)
        if description:
            job_data["job_description"] = description
            
        # If we still don't have a title, try a more generic approach
        if not job_data["title"]:
            title = await extract_text(page, "h1")
            if title:
                job_data["title"] = title
                
    except Exception as e:
        console.print(f"[yellow]⚠️ Error extracting Lever job details: {e}[/yellow]")

async def extract_generic_job_details(page, job_data):
    """Extract job details using generic selectors."""
    try:
        # Title - try common selectors
        title_selectors = ["h1", ".job-title", ".title", '[class*="title"]']
        for selector in title_selectors:
            title = await extract_text(page, selector)
            if title:
                job_data["title"] = title
                break
                
        # Company - try common selectors
        company_selectors = [".company", ".company-name", '[class*="company"]']
        for selector in company_selectors:
            company = await extract_text(page, selector)
            if company:
                job_data["company"] = company
                break
                
        # Location - try common selectors
        location_selectors = [".location", ".job-location", '[class*="location"]']
        for selector in location_selectors:
            location = await extract_text(page, selector)
            if location:
                job_data["location"] = location
                break
                
        # Job Description - try common selectors
        description_selectors = [
            ".job-description", 
            '[class*="description"]', 
            ".description", 
            "main", 
            "article", 
            '[class*="content"]'
        ]
        for selector in description_selectors:
            description = await extract_text(page, selector)
            if description and len(description) > 100:
                job_data["job_description"] = description
                break
                
        # Salary - try common selectors
        salary_selectors = [".salary", ".compensation", '[class*="salary"]']
        for selector in salary_selectors:
            salary = await extract_text(page, selector)
            if salary:
                job_data["salary_range"] = salary
                break
                
        # If we still don't have a description, try to get the body content
        if not job_data["job_description"]:
            body_content = await extract_text(page, "body")
            if body_content:
                # Try to clean up the body content
                lines = body_content.split("\n")
                filtered_lines = [line for line in lines if len(line.strip()) > 20]  # Only keep substantial lines
                job_data["job_description"] = "\n".join(filtered_lines)
                
    except Exception as e:
        console.print(f"[yellow]⚠️ Error extracting generic job details: {e}[/yellow]")

async def extract_text(page, selector):
    """Extract text from a selector with error handling."""
    try:
        element = await page.query_selector(selector)
        if element:
            text = await element.text_content()
            if text:
                return text.strip()
    except Exception:
        pass
    return ""

def extract_keywords(text):
    """Extract keywords from job description."""
    keywords = []
    
    # Common technical skills to look for
    tech_skills = [
        "python", "java", "javascript", "sql", "html", "css", "react", "angular", "vue",
        "node.js", "express", "django", "flask", "spring", "docker", "kubernetes",
        "aws", "azure", "gcp", "git", "jenkins", "jira", "confluence", "tableau",
        "power bi", "excel", "r", "matlab", "sas", "spss", "machine learning",
        "data analysis", "statistics", "etl", "data warehousing", "big data",
        "hadoop", "spark", "kafka", "redis", "mongodb", "postgresql", "mysql"
    ]
    
    # Check for each skill in the text
    text_lower = text.lower()
    for skill in tech_skills:
        if skill in text_lower:
            keywords.append(skill)
            
    return ", ".join(keywords[:10])  # Return top 10 keywords

async def process_job_url(url):
    """Process a single job URL."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            console.print(f"[cyan]🔍 Processing job URL: {url}[/cyan]")
            job_data = await scrape_job_details(url, page)
            
            console.print(f"[green]✅ Successfully processed job URL[/green]")
            console.print(f"[yellow]Title: {job_data.get('title', 'MISSING')}[/yellow]")
            console.print(f"[yellow]Company: {job_data.get('company', 'MISSING')}[/yellow]")
            console.print(f"[yellow]Location: {job_data.get('location', 'MISSING')}[/yellow]")
            console.print(f"[yellow]Description length: {len(job_data.get('job_description', ''))}[/yellow]")
            console.print(f"[yellow]Keywords: {job_data.get('keywords', 'MISSING')}[/yellow]")
            
            return job_data
            
        finally:
            await context.close()
            await browser.close()

async def process_pending_jobs(profile_name="Nirajan", limit=5):
    """Process pending jobs from the database."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        task = progress.add_task("🚀 Processing pending jobs...", total=None)
        
        # Connect to the database
        db_path = f"profiles/{profile_name}/{profile_name}.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get pending jobs
        progress.update(task, description="📊 Fetching pending jobs from database...")
        cursor.execute("""
            SELECT id, url, title 
            FROM jobs 
            WHERE (job_description IS NULL OR job_description = '') 
               OR (title = 'Unknown Title' OR title = 'Job from URL')
            LIMIT ?
        """, (limit,))
        
        pending_jobs = cursor.fetchall()
        
        if not pending_jobs:
            progress.update(task, description="📭 No pending jobs found")
            console.print("[yellow]📭 No pending jobs found in database[/yellow]")
            return
            
        console.print(f"[cyan]📋 Found {len(pending_jobs)} pending jobs[/cyan]")
        
        # Process each job
        processed_count = 0
        for job_id, url, title in pending_jobs:
            progress.update(task, description=f"🔍 Processing job {job_id}: {title[:30]}...")
            
            try:
                job_data = await process_job_url(url)
                
                if job_data and job_data.get("title"):
                    # Update the database
                    cursor.execute("""
                        UPDATE jobs SET 
                            title = ?,
                            company = ?,
                            location = ?,
                            job_description = ?,
                            salary_range = ?,
                            job_type = ?,
                            keywords = ?,
                            requirements = ?,
                            benefits = ?,
                            remote_option = ?,
                            status = 'processed',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        job_data.get("title", title),
                        job_data.get("company", ""),
                        job_data.get("location", ""),
                        job_data.get("job_description", ""),
                        job_data.get("salary_range", ""),
                        job_data.get("job_type", ""),
                        job_data.get("keywords", ""),
                        job_data.get("requirements", ""),
                        job_data.get("benefits", ""),
                        job_data.get("remote_option", "Unknown"),
                        job_id
                    ))
                    
                    conn.commit()
                    processed_count += 1
                    progress.update(task, description=f"✅ Updated job {job_id}: {job_data.get('title')[:30]}...")
                else:
                    progress.update(task, description=f"⚠️ Failed to extract data for job {job_id}")
                    
            except Exception as e:
                console.print(f"[red]❌ Error processing job {job_id}: {e}[/red]")
                continue
                
        progress.update(task, description=f"🎉 Processed {processed_count} out of {len(pending_jobs)} jobs")
        console.print(f"[bold green]🎉 Successfully processed {processed_count} out of {len(pending_jobs)} jobs![/bold green]")
        
        conn.close()

async def main():
    console.print(Panel(
        "[bold blue]🚀 Robust Job Scraper with Popup Handling[/bold blue]\n"
        "[cyan]Processing pending jobs from database...[/cyan]",
        title="JOB PROCESSOR",
        style="bold blue"
    ))
    
    await process_pending_jobs(limit=10)
    
    console.print("[bold green]✅ Job processing complete![/bold green]")
    console.print("[cyan]💡 Check the dashboard to see updated job data[/cyan]")

if __name__ == "__main__":
    asyncio.run(main())