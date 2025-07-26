#!/usr/bin/env python3
"""
Enhanced Job Scraper with Proper Tab Management
Handles popup closing, content extraction, and proper tab cleanup
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from rich.console import Console
from rich.panel import Panel

console = Console()
logger = logging.getLogger(__name__)

class EnhancedJobScraperWithTabManagement:
    """Enhanced job scraper with proper tab management and popup handling."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.active_pages: List[Page] = []
        
        # Popup selectors for different sites
        self.popup_selectors = [
            # Generic cookie popups
            'button:has-text("Accept")',
            'button:has-text("Accept All")',
            'button:has-text("Accept Cookies")',
            'button:has-text("I Accept")',
            'button:has-text("OK")',
            'button:has-text("Got it")',
            'button:has-text("Continue")',
            
            # Workday specific
            '[data-automation-id="cookieBanner"] button',
            '[data-automation-id="legalNoticeAcceptButton"]',
            'button[data-automation-id="legalNoticeAcceptButton"]',
            
            # LinkedIn specific
            '.artdeco-global-alert-action',
            'button[action-type="ACCEPT"]',
            
            # Indeed specific
            '#onetrust-accept-btn-handler',
            '.onetrust-close-btn-handler',
            
            # Generic close buttons
            'button[aria-label="Close"]',
            'button[aria-label="Dismiss"]',
            '.close-button',
            '.modal-close',
            
            # GDPR/Privacy related
            'button:has-text("Accept and Continue")',
            'button:has-text("I Understand")',
            'button:has-text("Agree")',
        ]
        
        # Job content selectors for different ATS systems
        self.job_selectors = {
            'workday': {
                'title': '[data-automation-id="jobTitle"]',
                'company': '[data-automation-id="jobCompany"]',
                'location': '[data-automation-id="jobLocation"]',
                'description': '[data-automation-id="jobDescription"]',
                'requirements': '[data-automation-id="jobRequirements"]',
                'salary': '[data-automation-id="jobSalary"]',
            },
            'greenhouse': {
                'title': '.app-title',
                'company': '.company-name',
                'location': '.location',
                'description': '#job_description',
                'requirements': '.requirements',
            },
            'lever': {
                'title': '.posting-headline h2',
                'company': '.company-name',
                'location': '.location',
                'description': '.section-wrapper .content',
            },
            'generic': {
                'title': 'h1, .job-title, .title, [class*="title"]',
                'company': '.company, .company-name, [class*="company"]',
                'location': '.location, [class*="location"]',
                'description': '.description, .job-description, [class*="description"]',
                'salary': '.salary, [class*="salary"], [class*="compensation"]',
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.cleanup_all()
    
    async def initialize_browser(self):
        """Initialize browser with optimized settings."""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',  # Faster loading
                    '--disable-javascript',  # We'll enable per page if needed
                ]
            )
            
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            
            console.print("[green]✅ Browser initialized successfully[/green]")
            
        except Exception as e:
            console.print(f"[red]❌ Failed to initialize browser: {e}[/red]")
            raise
    
    async def create_new_page(self) -> Page:
        """Create a new page and track it."""
        if not self.context:
            await self.initialize_browser()
        
        page = await self.context.new_page()
        self.active_pages.append(page)
        
        # Set timeouts
        page.set_default_timeout(30000)  # 30 seconds
        page.set_default_navigation_timeout(30000)
        
        console.print(f"[blue]📄 Created new page (Total active: {len(self.active_pages)})[/blue]")
        return page
    
    async def close_page(self, page: Page):
        """Close a specific page and remove from tracking."""
        try:
            if page in self.active_pages:
                self.active_pages.remove(page)
            
            if not page.is_closed():
                await page.close()
            
            console.print(f"[yellow]🗑️ Closed page (Remaining active: {len(self.active_pages)})[/yellow]")
            
        except Exception as e:
            console.print(f"[red]⚠️ Error closing page: {e}[/red]")
    
    async def handle_popups_and_overlays(self, page: Page) -> bool:
        """Handle cookie popups and overlays that block content."""
        popups_handled = 0
        
        for selector in self.popup_selectors:
            try:
                # Wait briefly for popup to appear
                element = await page.wait_for_selector(selector, timeout=2000)
                if element:
                    # Check if element is visible and clickable
                    is_visible = await element.is_visible()
                    if is_visible:
                        await element.click()
                        await asyncio.sleep(1)  # Wait for popup to close
                        popups_handled += 1
                        console.print(f"[green]✅ Handled popup: {selector}[/green]")
                        break  # Only handle one popup at a time
                        
            except Exception:
                # Popup not found or not clickable, continue
                continue
        
        if popups_handled > 0:
            console.print(f"[green]✅ Handled {popups_handled} popup(s)[/green]")
            return True
        
        return False
    
    def detect_ats_system(self, url: str) -> str:
        """Detect ATS system from URL."""
        url_lower = url.lower()
        
        if 'workday' in url_lower:
            return 'workday'
        elif 'greenhouse' in url_lower:
            return 'greenhouse'
        elif 'lever' in url_lower:
            return 'lever'
        else:
            return 'generic'
    
    async def extract_job_data(self, page: Page, url: str) -> Dict[str, Any]:
        """Extract job data using ATS-specific selectors."""
        ats_system = self.detect_ats_system(url)
        selectors = self.job_selectors.get(ats_system, self.job_selectors['generic'])
        
        job_data = {
            'url': url,
            'ats_system': ats_system,
            'extraction_timestamp': datetime.now().isoformat(),
            'title': None,
            'company': None,
            'location': None,
            'description': None,
            'salary': None,
            'keywords': [],
            'extraction_success': False
        }
        
        extracted_fields = 0
        
        # Extract each field
        for field, selector in selectors.items():
            try:
                element = await page.wait_for_selector(selector, timeout=5000)
                if element:
                    text = await element.inner_text()
                    if text and text.strip():
                        job_data[field] = text.strip()
                        extracted_fields += 1
                        console.print(f"[green]✅ Extracted {field}: {text[:50]}...[/green]")
                    
            except Exception as e:
                console.print(f"[yellow]⚠️ Failed to extract {field}: {e}[/yellow]")
        
        # Extract keywords from description
        if job_data.get('description'):
            job_data['keywords'] = self.extract_keywords_from_text(job_data['description'])
        
        # Mark as successful if we got at least title and company
        job_data['extraction_success'] = (
            job_data.get('title') and 
            job_data.get('company') and
            extracted_fields >= 2
        )
        
        console.print(f"[blue]📊 Extracted {extracted_fields} fields from {ats_system} system[/blue]")
        return job_data
    
    def extract_keywords_from_text(self, text: str) -> List[str]:
        """Extract relevant keywords from job description."""
        if not text:
            return []
        
        # Common tech keywords to look for
        tech_keywords = [
            'python', 'java', 'javascript', 'react', 'node.js', 'sql', 'aws', 'docker',
            'kubernetes', 'machine learning', 'data science', 'analytics', 'tableau',
            'power bi', 'excel', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'git',
            'agile', 'scrum', 'devops', 'ci/cd', 'rest api', 'microservices'
        ]
        
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in tech_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords[:10]  # Limit to 10 keywords
    
    async def scrape_job_with_tab_management(self, job_url: str) -> Dict[str, Any]:
        """
        Scrape a job with proper tab management:
        1. Create new tab
        2. Handle popups
        3. Extract data
        4. Close tab
        """
        page = None
        
        try:
            console.print(f"[blue]🔄 Starting scrape for: {job_url}[/blue]")
            
            # Step 1: Create new page/tab
            page = await self.create_new_page()
            
            # Step 2: Navigate to job URL
            await page.goto(job_url, wait_until='domcontentloaded')
            console.print(f"[green]✅ Navigated to job page[/green]")
            
            # Step 3: Handle popups and overlays
            await self.handle_popups_and_overlays(page)
            
            # Step 4: Wait for content to load
            await asyncio.sleep(2)
            
            # Step 5: Extract job data
            job_data = await self.extract_job_data(page, job_url)
            
            # Step 6: Close the tab
            await self.close_page(page)
            page = None  # Mark as closed
            
            console.print(f"[green]✅ Successfully scraped job with tab cleanup[/green]")
            return job_data
            
        except Exception as e:
            console.print(f"[red]❌ Error scraping job: {e}[/red]")
            
            # Ensure tab is closed even on error
            if page:
                await self.close_page(page)
            
            return {
                'url': job_url,
                'extraction_success': False,
                'error': str(e),
                'extraction_timestamp': datetime.now().isoformat()
            }
    
    async def cleanup_all(self):
        """Clean up all resources."""
        try:
            # Close all active pages
            for page in self.active_pages.copy():
                await self.close_page(page)
            
            # Close context and browser
            if self.context:
                await self.context.close()
            
            if self.browser:
                await self.browser.close()
            
            console.print("[green]✅ All browser resources cleaned up[/green]")
            
        except Exception as e:
            console.print(f"[red]⚠️ Error during cleanup: {e}[/red]")

# Async function for easy usage
async def scrape_job_with_proper_tab_management(job_url: str) -> Dict[str, Any]:
    """Scrape a single job with proper tab management."""
    async with EnhancedJobScraperWithTabManagement() as scraper:
        return await scraper.scrape_job_with_tab_management(job_url)