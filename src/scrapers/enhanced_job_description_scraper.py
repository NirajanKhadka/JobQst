"""
Enhanced Job Description Scraper - Base Implementation
Provides job description scraping functionality for external sites.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from playwright.async_api import Page

from .base_scraper import BaseJobScraper

logger = logging.getLogger(__name__)


class ImprovedJobDescriptionScraper:
    """
    Enhanced job description scraper with improved extraction methods.
    """

    def __init__(self):
        self.stats = {"total_processed": 0, "successful_extractions": 0, "failed_extractions": 0}

    async def scrape_job_description(self, job_url: str, page: Page) -> Optional[Dict[str, Any]]:
        """
        Scrape job description from a job URL.

        Args:
            job_url: URL of the job posting
            page: Playwright page instance

        Returns:
            Dictionary with job data or None if failed
        """
        try:
            self.stats["total_processed"] += 1

            # Navigate to job URL
            await page.goto(job_url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)  # Allow page to fully load

            # Extract job data
            job_data = await self._extract_job_data(page, job_url)

            if job_data:
                self.stats["successful_extractions"] += 1
                logger.info(f"Successfully scraped: {job_data.get('title', 'Unknown')}")
                return job_data
            else:
                self.stats["failed_extractions"] += 1
                logger.warning(f"Failed to extract job data from: {job_url}")
                return None

        except Exception as e:
            self.stats["failed_extractions"] += 1
            logger.error(f"Error scraping job description from {job_url}: {e}")
            return None

    async def _extract_job_data(self, page: Page, job_url: str) -> Optional[Dict[str, Any]]:
        """Extract job data from the page."""
        try:
            # Extract title
            title = await self._extract_title(page)
            if not title:
                return None

            # Extract company
            company = await self._extract_company(page)

            # Extract location
            location = await self._extract_location(page)

            # Extract description
            description = await self._extract_description(page)

            # Extract salary if available
            salary = await self._extract_salary(page)

            return {
                "title": title,
                "company": company or "Unknown Company",
                "location": location or "Unknown Location",
                "description": description or "",
                "salary": salary or "",
                "url": job_url,
                "scraped_at": datetime.now().isoformat(),
                "source": "external",
            }

        except Exception as e:
            logger.error(f"Error extracting job data: {e}")
            return None

    async def _extract_title(self, page: Page) -> Optional[str]:
        """Extract job title from page."""
        selectors = [
            "h1",
            "[data-testid*='title']",
            ".job-title",
            ".position-title",
            ".title",
            "h2",
        ]

        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and len(text.strip()) > 3:
                        return text.strip()
            except:
                continue

        return None

    async def _extract_company(self, page: Page) -> Optional[str]:
        """Extract company name from page."""
        selectors = [
            "[data-testid*='company']",
            ".company-name",
            ".employer",
            ".company",
            "h2",
            "h3",
        ]

        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and len(text.strip()) > 1:
                        return text.strip()
            except:
                continue

        return None

    async def _extract_location(self, page: Page) -> Optional[str]:
        """Extract location from page."""
        selectors = ["[data-testid*='location']", ".location", ".job-location", ".address"]

        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and len(text.strip()) > 1:
                        return text.strip()
            except:
                continue

        return None

    async def _extract_description(self, page: Page) -> Optional[str]:
        """Extract job description from page."""
        selectors = [
            "[data-testid*='description']",
            ".job-description",
            ".description",
            ".content",
            ".job-details",
        ]

        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and len(text.strip()) > 50:
                        return text.strip()
            except:
                continue

        return None

    async def _extract_salary(self, page: Page) -> Optional[str]:
        """Extract salary information from page."""
        selectors = ["[data-testid*='salary']", ".salary", ".compensation", ".pay"]

        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and ("$" in text or "salary" in text.lower()):
                        return text.strip()
            except:
                continue

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        return self.stats.copy()
