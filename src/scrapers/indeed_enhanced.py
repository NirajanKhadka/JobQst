"""
Enhanced Indeed Scraper for AutoJobAgent.

This module provides an enhanced version of the Indeed scraper with
improved error handling, better job data extraction, and advanced features.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from src.utils import profile_helpers
from src.core.job_database import get_job_db

logger = logging.getLogger(__name__)


class EnhancedIndeedScraper:
    """Enhanced Indeed scraper with improved functionality."""
    
    def __init__(self, profile: Optional[Dict] = None, **kwargs):
        self.profile = profile or {}
        self.profile_name = profile.get('profile_name', 'default') if profile else 'default'
        self.db = get_job_db(self.profile_name)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        # Configuration
        self.max_pages = kwargs.get('max_pages', 5)
        self.max_jobs = kwargs.get('max_jobs', 10)
        self.delay_between_clicks = kwargs.get('delay_between_clicks', 1.0)
        self.timeout = kwargs.get('timeout', 30000)
        
        # Statistics
        self.jobs_scraped = 0
        self.jobs_saved = 0
        self.errors = []
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.setup_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def setup_browser(self) -> None:
        """Setup browser and context."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            self.page = await self.context.new_page()
            await self.page.set_default_timeout(self.timeout)
            
            logger.info("✅ Browser setup completed")
            
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Cleanup browser resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("✅ Browser cleanup completed")
        except Exception as e:
            logger.error(f"❌ Browser cleanup error: {e}")
    
    async def scrape_jobs(self, keywords: List[str], location: Optional[str] = None) -> List[Dict]:
        """
        Scrape jobs from Indeed based on keywords and location.
        
        Args:
            keywords: List of search keywords
            location: Optional location filter
            
        Returns:
            List of scraped job data
        """
        scraped_jobs = []
        
        try:
            for keyword in keywords:
                logger.info(f"🔍 Scraping Indeed jobs for keyword: {keyword}")
                
                keyword_jobs = await self._scrape_keyword_jobs(keyword, location)
                scraped_jobs.extend(keyword_jobs)
                
                if len(scraped_jobs) >= self.max_jobs:
                    break
            
            logger.info(f"✅ Indeed scraping completed: {len(scraped_jobs)} jobs found")
            return scraped_jobs
            
        except Exception as e:
            logger.error(f"❌ Indeed scraping failed: {e}")
            self.errors.append(str(e))
            return scraped_jobs
    
    async def _scrape_keyword_jobs(self, keyword: str, location: Optional[str] = None) -> List[Dict]:
        """Scrape jobs for a specific keyword from Indeed."""
        jobs = []
        
        try:
            for page_num in range(1, self.max_pages + 1):
                logger.info(f"📄 Scraping Indeed page {page_num} for '{keyword}'")
                
                # Build search URL
                search_url = self._build_search_url(keyword, location, page_num)
                
                # Navigate to search page
                if self.page:
                    await self.page.goto(search_url)
                    await self.page.wait_for_load_state('networkidle')
                    
                    # Extract jobs from current page
                    page_jobs = await self._extract_jobs_from_page()
                    jobs.extend(page_jobs)
                    
                    logger.info(f"📊 Indeed page {page_num}: {len(page_jobs)} jobs found")
                    
                    # Check if we have enough jobs
                    if len(jobs) >= self.max_jobs:
                        break
                    
                    # Check if there's a next page
                    if not await self._has_next_page():
                        break
                    
                    # Delay between pages
                    await asyncio.sleep(self.delay_between_clicks)
            
            return jobs[:self.max_jobs]
            
        except Exception as e:
            logger.error(f"❌ Error scraping Indeed keyword '{keyword}': {e}")
            self.errors.append(f"Indeed keyword '{keyword}': {str(e)}")
            return jobs
    
    def _build_search_url(self, keyword: str, location: Optional[str], page: int) -> str:
        """Build Indeed search URL."""
        base_url = "https://ca.indeed.com/jobs"
        
        # URL parameters
        params = {
            'q': keyword,
            'start': (page - 1) * 10  # Indeed uses start parameter for pagination
        }
        
        if location:
            params['l'] = location
        
        # Build query string
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    async def _extract_jobs_from_page(self) -> List[Dict]:
        """Extract job data from current Indeed page."""
        jobs = []
        
        try:
            if not self.page:
                return jobs
                
            # Wait for job listings to load
            await self.page.wait_for_selector('[data-jk]', timeout=10000)
            
            # Get all job elements
            job_elements = await self.page.query_selector_all('[data-jk]')
            
            for job_elem in job_elements:
                try:
                    job_data = await self._extract_job_data(job_elem)
                    if job_data:
                        jobs.append(job_data)
                        self.jobs_scraped += 1
                        
                        # Save to database
                        if await self._save_job(job_data):
                            self.jobs_saved += 1
                        
                        # Delay between job extractions
                        await asyncio.sleep(self.delay_between_clicks)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error extracting Indeed job data: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Error extracting Indeed jobs from page: {e}")
            return jobs
    
    async def _extract_job_data(self, job_elem) -> Optional[Dict]:
        """Extract data from a single Indeed job element."""
        try:
            # Extract basic job information
            title_elem = await job_elem.query_selector('h2 a')
            title = await title_elem.text_content() if title_elem else "Unknown Title"
            
            company_elem = await job_elem.query_selector('[data-testid="company-name"]')
            company = await company_elem.text_content() if company_elem else "Unknown Company"
            
            location_elem = await job_elem.query_selector('[data-testid="job-location"]')
            location = await location_elem.text_content() if location_elem else "Unknown Location"
            
            # Extract job URL
            job_url = await self._extract_job_url(job_elem)
            
            # Create job data
            job_data = {
                'title': title.strip(),
                'company': company.strip(),
                'location': location.strip(),
                'url': job_url,
                'source': 'indeed_enhanced',
                'scraped_at': time.time(),
                'profile_name': self.profile_name
            }
            
            return job_data
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting Indeed job data: {e}")
            return None
    
    async def _extract_job_url(self, job_elem) -> str:
        """Extract job URL from Indeed job element."""
        try:
            if not self.page:
                return ""
                
            # Get the job link
            link_elem = await job_elem.query_selector('h2 a')
            if link_elem:
                href = await link_elem.get_attribute('href')
                if href:
                    # Make relative URLs absolute
                    if href.startswith('/'):
                        return f"https://ca.indeed.com{href}"
                    return href
            
            return ""
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting Indeed job URL: {e}")
            return ""
    
    async def _save_job(self, job_data: Dict) -> bool:
        """Save job to database."""
        try:
            # Check for duplicates by URL
            existing_jobs = self.db.get_jobs()
            for existing_job in existing_jobs:
                if existing_job.get('url') == job_data['url']:
                    logger.info(f"🔄 Duplicate Indeed job found, skipping: {job_data['title']}")
                    return False
            
            # Save job
            self.db.add_job(job_data)
            logger.info(f"✅ Indeed job saved: {job_data['title']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving Indeed job: {e}")
            return False
    
    async def _has_next_page(self) -> bool:
        """Check if there's a next page available on Indeed."""
        try:
            if not self.page:
                return False
            next_button = await self.page.query_selector('[aria-label="Next Page"]')
            return next_button is not None
        except Exception:
            return False
    
    def get_statistics(self) -> Dict:
        """Get scraping statistics."""
        return {
            'jobs_scraped': self.jobs_scraped,
            'jobs_saved': self.jobs_saved,
            'errors': len(self.errors),
            'error_details': self.errors
        }


# Convenience function for easy usage
async def scrape_indeed_jobs(keywords: List[str], profile_name: str = "default", **kwargs) -> List[Dict]:
    """
    Convenience function to scrape Indeed jobs.
    
    Args:
        keywords: List of search keywords
        profile_name: Profile name for database storage
        **kwargs: Additional scraper configuration
        
    Returns:
        List of scraped job data
    """
    profile = {'profile_name': profile_name}
    
    async with EnhancedIndeedScraper(profile, **kwargs) as scraper:
        jobs = await scraper.scrape_jobs(keywords)
        stats = scraper.get_statistics()
        
        logger.info(f"📊 Indeed scraping completed: {stats}")
        return jobs


# Alias for backward compatibility
IndeedEnhancedScraper = EnhancedIndeedScraper 