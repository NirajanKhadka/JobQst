#!/usr/bin/env python3
"""
Test Scraper - Only Save URLs to Database
This scraper only collects job URLs and saves them to the database for later processing.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List
from pathlib import Path

from rich.console import Console
from playwright.async_api import async_playwright

from src.core.job_database import get_job_db
from src.utils.profile_helpers import load_profile

console = Console()


class SimpleURLScraper:
    """Simple scraper that only collects job URLs."""

    def __init__(self, profile_name: str = "Nirajan"):
        """Initialize the URL scraper."""
        self.profile_name = profile_name
        self.profile = load_profile(profile_name)
        if not self.profile:
            raise ValueError(f"Profile '{profile_name}' not found!")
        self.db = get_job_db(profile_name)

        # Get keywords from profile
        self.keywords = self.profile.get("keywords", [])
        self.skills = self.profile.get("skills", [])
        all_terms = set(self.keywords + self.skills)

        self.search_terms = ["Data Scientist"]  # Only use 'Data Scientist' keyword
        console.print(f"[cyan]Testing with keywords: {self.search_terms}[/cyan]")

        # Scraping settings
        self.base_url = "https://www.eluta.ca/search"
        self.max_pages_per_keyword = 1  # Only 1 page for testing
        self.delay_between_requests = 2  # seconds

        # Results tracking
        self.processed_urls = set()
        self.stats = {
            "keywords_processed": 0,
            "pages_scraped": 0,
            "urls_found": 0,
            "urls_saved": 0,
            "duplicates_skipped": 0,
        }

    async def scrape_urls_only(self) -> List[str]:
        """Scrape job URLs only and save them to database."""
        console.print(f"[bold blue]🔍 Scraping URLs Only - Test Mode[/bold blue]")
        
        all_urls = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            # Set realistic headers
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                locale="en-US"
            )
            # Set cookies for eluta.ca
            cookies = [{
                "name": "_ga",
                "value": "GA1.2.123456789.1234567890",
                "domain": ".eluta.ca",
                "path": "/",
                "httpOnly": False,
                "secure": True
            }]
            await context.add_cookies(cookies)
            page = await context.new_page()

            try:
                for keyword in self.search_terms:
                    console.print(f"\n🔍 Searching: {keyword}")
                    keyword_urls = await self._scrape_keyword_urls(page, keyword)
                    all_urls.extend(keyword_urls)
                    self.stats["keywords_processed"] += 1
                    await asyncio.sleep(self.delay_between_requests)

                console.print(f"\n✅ Found {len(all_urls)} total URLs")
                return all_urls

            finally:
                await context.close()
                await browser.close()

    async def _scrape_keyword_urls(self, page, keyword: str) -> List[str]:
        """Scrape URLs for a specific keyword."""
        keyword_urls = []

        try:
            # Navigate to search page
            search_url = f"{self.base_url}?q={keyword.replace(' ', '+')}&l=&posted=14&pg=1"
            console.print(f"URL: {search_url}")
            await page.goto(search_url, wait_until="networkidle")
            await asyncio.sleep(2)

            # Find job elements
            job_elements = await page.query_selector_all("h2, h3")
            console.print(f"Found {len(job_elements)} job elements")

            # Process each job element to extract URLs only
            for i, job_element in enumerate(job_elements[:20]):  # Limit to 20 for more results
                try:
                    job_url = await self._extract_job_url_only(job_element, page, i+1)
                    if job_url and job_url not in self.processed_urls:
                        self.processed_urls.add(job_url)
                        keyword_urls.append(job_url)
                        self.stats["urls_found"] += 1
                        
                        # Save URL to database immediately
                        success = self._save_url_to_database(job_url, keyword)
                        if success:
                            self.stats["urls_saved"] += 1
                            console.print(f"✅ Saved URL {i+1}: {job_url[:60]}...")
                        else:
                            console.print(f"❌ Failed to save URL {i+1}")
                    else:
                        self.stats["duplicates_skipped"] += 1

                except Exception as e:
                    console.print(f"❌ Error processing job {i+1}: {e}")
                    continue

        except Exception as e:
            console.print(f"❌ Error scraping keyword '{keyword}': {e}")

        return keyword_urls

    async def _extract_job_url_only(self, job_element, page, job_number: int) -> str:
        """Extract only the job URL from a job element by clicking it with proper timeouts."""
        try:
            # Debug: Get the element text to see what we're working with
            element_text = await job_element.inner_text()
            console.print(f"[dim]Job {job_number} text: {element_text[:50]}...[/dim]")
            
            # Look for a clickable link within the job element
            link = await job_element.query_selector("a")
            
            if not link:
                # Look in parent container
                parent = await job_element.query_selector("..")
                if parent:
                    link = await parent.query_selector("a")
            
            if not link:
                console.print(f"[yellow]Job {job_number}: No clickable link found[/yellow]")
                return ""

            # Get the href attribute first to check
            href = await link.get_attribute("href")
            console.print(f"[cyan]Job {job_number}: Found href: {href}[/cyan]")

            # If it's a JavaScript placeholder (#!), we need to click it
            if href == "#!" or not href or href.startswith("#"):
                console.print(f"[cyan]Job {job_number}: JavaScript link detected, clicking...[/cyan]")
                
                try:
                    # Method 1: Try to open in new tab with timeout
                    async with page.expect_popup() as popup_info:
                        await asyncio.wait_for(link.click(modifiers=["Control"]), timeout=5)
                    
                    popup = await popup_info.value
                    await asyncio.wait_for(popup.wait_for_load_state("networkidle"), timeout=15)
                    
                    real_url = popup.url
                    await popup.close()
                    console.print(f"[dim]🗂️ Closed popup tab[/dim]")
                    
                    # Validate URL
                    if real_url and not any(skip in real_url for skip in ["/search?", "q=", "pg="]):
                        console.print(f"[green]Job {job_number}: Got real URL from popup: {real_url[:60]}...[/green]")
                        return real_url
                    else:
                        console.print(f"[yellow]Job {job_number}: Popup gave invalid URL[/yellow]")
                        return ""
                    
                except asyncio.TimeoutError:
                    console.print(f"[red]Job {job_number}: Popup method timeout - skipping[/red]")
                    return ""
                except Exception as popup_error:
                    console.print(f"[yellow]Job {job_number}: Popup method failed: {popup_error}[/yellow]")
                    
                    # Method 2: Click and navigate in same page with timeout
                    try:
                        current_url = page.url
                        await asyncio.wait_for(link.click(), timeout=5)
                        await asyncio.wait_for(page.wait_for_load_state("networkidle"), timeout=15)
                        new_url = page.url
                        
                        if new_url != current_url and not any(skip in new_url for skip in ["/search?", "q=", "pg="]):
                            console.print(f"[green]Job {job_number}: Got URL from navigation: {new_url[:60]}...[/green]")
                            # Navigate back to search results
                            await asyncio.wait_for(page.go_back(), timeout=10)
                            await asyncio.wait_for(page.wait_for_load_state("networkidle"), timeout=10)
                            return new_url
                        else:
                            console.print(f"[yellow]Job {job_number}: Navigation gave invalid URL[/yellow]")
                            return ""
                            
                    except asyncio.TimeoutError:
                        console.print(f"[red]Job {job_number}: Navigation method timeout - skipping[/red]")
                        # Try to go back anyway
                        try:
                            await page.go_back()
                        except:
                            pass
                        return ""
                    except Exception as click_error:
                        console.print(f"[red]Job {job_number}: Click method failed: {click_error}[/red]")
                        return ""
            
            # If it's a direct URL, use it
            elif href.startswith("/") and not any(skip in href for skip in ["/search?", "q=", "pg="]):
                full_url = "https://www.eluta.ca" + href
                console.print(f"[green]Job {job_number}: Direct relative URL: {full_url[:60]}...[/green]")
                return full_url
            elif href.startswith("http") and "eluta.ca" not in href:
                console.print(f"[green]Job {job_number}: Direct full URL: {href[:60]}...[/green]")
                return href
            else:
                console.print(f"[yellow]Job {job_number}: Unknown or invalid href format: {href}[/yellow]")
                return ""

        except Exception as e:
            console.print(f"❌ Error extracting URL for job {job_number}: {e}")
            return ""

    def _save_url_to_database(self, url: str, keyword: str) -> bool:
        """Save URL to database with minimal data."""
        try:
            job_data = {
                "title": "Pending Processing",  # Will be filled later
                "company": "Pending Processing",  # Will be filled later
                "location": "Unknown",
                "summary": "",
                "url": url,
                "search_keyword": keyword,
                "site": "eluta",
                "scraped_at": datetime.now().isoformat(),
                "applied": 0,
                "status": "scraped",  # Status: scraped -> processed -> document_created -> applied
                "experience_level": "Unknown",
                "keywords": keyword,
                "job_description": "",
                "salary_range": "",
                "job_type": "Unknown",
                "remote_option": "Unknown",
                "requirements": "",
                "benefits": "",
                "match_score": 0.0,
                "processing_notes": "URL scraped, awaiting detail extraction",
                "application_date": "",
                "application_status": "not_applied",
                "raw_data": {},
                "analysis_data": {}
            }
            
            return self.db.add_job(job_data)
            
        except Exception as e:
            console.print(f"❌ Error saving URL to database: {e}")
            return False

    def display_results(self):
        """Display scraping results."""
        console.print("\n" + "=" * 60)
        console.print("[bold green]📊 URL Scraping Results[/bold green]")
        console.print(f"Keywords processed: {self.stats['keywords_processed']}")
        console.print(f"URLs found: {self.stats['urls_found']}")
        console.print(f"URLs saved to database: {self.stats['urls_saved']}")
        console.print(f"Duplicates skipped: {self.stats['duplicates_skipped']}")
        
        # Check database
        jobs = self.db.get_all_jobs()
        console.print(f"Total jobs in database: {len(jobs)}")


async def main():
    """Main function to test URL-only scraping."""
    scraper = SimpleURLScraper("Nirajan")
    
    try:
        urls = await scraper.scrape_urls_only()
        scraper.display_results()
        
        console.print(f"\n✅ Scraping complete! Found {len(urls)} URLs")
        console.print("Next step: Run job processor to extract details from these URLs")
        
    except KeyboardInterrupt:
        console.print("\n⚠️ Scraping interrupted by user")
    except Exception as e:
        console.print(f"\n❌ Scraping failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())