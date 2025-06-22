"""
LinkedIn Job Scraper
Specialized scraper for LinkedIn job listings.
"""

import time
from typing import Dict, Generator
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from rich.console import Console

from .base_scraper import BaseJobScraper

console = Console()


class LinkedInScraper(BaseJobScraper):
    """
    Specialized scraper for LinkedIn job listings.
    Requires browser context and handles LinkedIn's authentication.
    """
    
    def __init__(self, profile: Dict, **kwargs):
        super().__init__(profile, **kwargs)
        self.site_name = "LinkedIn"
        self.base_url = "https://www.linkedin.com/jobs/search"
        self.requires_browser = True  # LinkedIn requires JavaScript and login
        self.rate_limit_delay = (3.0, 5.0)  # LinkedIn is very strict
        self.is_logged_in = False
    
    def scrape_jobs(self) -> Generator[Dict, None, None]:
        """
        Scrape jobs from LinkedIn using Playwright browser context.
        
        Yields:
            Normalized job dictionaries
        """
        if not self.browser_context:
            console.print("[yellow]LinkedIn scraper requires browser context. Skipping.[/yellow]")
            return
        
        # Check if we need to login
        if not self._check_login_status():
            console.print("[yellow]LinkedIn login required. Please login manually in the browser.[/yellow]")
            self._prompt_for_login()
        
        yield from self._scrape_with_browser()
    
    def _check_login_status(self) -> bool:
        """Check if user is logged into LinkedIn."""
        page = self.browser_context.new_page()
        
        try:
            page.goto("https://www.linkedin.com/feed", timeout=15000)
            
            # Check for login indicators
            if page.query_selector("nav.global-nav"):
                self.is_logged_in = True
                console.print("[green]LinkedIn login detected[/green]")
                return True
            else:
                console.print("[yellow]LinkedIn login required[/yellow]")
                return False
                
        except Exception as e:
            console.print(f"[yellow]Error checking LinkedIn login: {e}[/yellow]")
            return False
        finally:
            page.close()
    
    def _prompt_for_login(self) -> None:
        """Prompt user to login to LinkedIn."""
        page = self.browser_context.new_page()
        
        try:
            page.goto("https://www.linkedin.com/login", timeout=30000)
            console.print("[yellow]Please login to LinkedIn in the browser window.[/yellow]")
            console.print("[yellow]Press Enter after you have successfully logged in...[/yellow]")
            input()
            
            # Verify login
            if self._check_login_status():
                console.print("[green]LinkedIn login successful![/green]")
            else:
                console.print("[red]LinkedIn login failed. Scraping may not work properly.[/red]")
                
        except Exception as e:
            console.print(f"[red]Error during LinkedIn login: {e}[/red]")
        finally:
            page.close()
    
    def _scrape_with_browser(self) -> Generator[Dict, None, None]:
        """
        Scrape LinkedIn using Playwright browser context.
        """
        page_num = self.current_index // 25 + 1  # LinkedIn shows 25 jobs per page
        console.print(f"[cyan]Scraping LinkedIn (page {page_num})[/cyan]")
        
        page = self.browser_context.new_page()
        
        try:
            # Construct LinkedIn jobs search URL
            search_url = (
                f"{self.base_url}"
                f"?keywords={self.search_terms}"
                f"&location={self.city}"
                f"&start={self.current_index}"
            )
            
            console.print(f"[green]Navigating to: {search_url}[/green]")
            page.goto(search_url, timeout=30000)
            
            # Wait for job results to load
            try:
                page.wait_for_selector("div.jobs-search__results-list, .job-result-card", timeout=15000)
            except PlaywrightTimeoutError:
                console.print("[yellow]Timeout waiting for LinkedIn results[/yellow]")
                return
            
            # Handle potential CAPTCHA or rate limiting
            if page.query_selector("div.challenge-page"):
                console.print("[yellow]LinkedIn CAPTCHA detected. Please solve manually.[/yellow]")
                input("Press Enter after solving CAPTCHA...")
            
            # Scroll to load more jobs (LinkedIn uses infinite scroll)
            self._scroll_to_load_jobs(page)
            
            # Extract job listings
            job_elements = page.query_selector_all("div.job-result-card, .jobs-search-results__list-item")
            
            if not job_elements:
                console.print("[yellow]No job elements found on LinkedIn[/yellow]")
                return
            
            console.print(f"[green]Found {len(job_elements)} jobs on LinkedIn[/green]")
            
            for job_elem in job_elements:
                try:
                    job = self._extract_job_from_element(job_elem)
                    if job:
                        yield self.normalize_job(job)
                except Exception as e:
                    console.print(f"[yellow]Error extracting LinkedIn job: {e}[/yellow]")
                    continue
            
            # Update pagination
            self.current_index += 25
            
        except Exception as e:
            console.print(f"[red]Error scraping LinkedIn: {e}[/red]")
        finally:
            page.close()
    
    def _scroll_to_load_jobs(self, page) -> None:
        """Scroll down to trigger LinkedIn's infinite scroll loading."""
        try:
            # Scroll down multiple times to load more jobs
            for i in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
                
                # Check if "Show more jobs" button exists and click it
                show_more_btn = page.query_selector("button.infinite-scroller__show-more-button")
                if show_more_btn and show_more_btn.is_visible():
                    show_more_btn.click()
                    time.sleep(3)
                    
        except Exception as e:
            console.print(f"[yellow]Error during scrolling: {e}[/yellow]")
    
    def _extract_job_from_element(self, job_elem) -> Dict:
        """
        Extract job data from a LinkedIn job element.
        
        Args:
            job_elem: Playwright element representing a job listing
            
        Returns:
            Job dictionary or None if extraction fails
        """
        try:
            # Extract job title and URL
            title_elem = job_elem.query_selector("h3.job-result-card__title a, .job-title a")
            title = title_elem.inner_text().strip() if title_elem else ""
            
            job_url = title_elem.get_attribute("href") if title_elem else ""
            if job_url and not job_url.startswith("http"):
                job_url = f"https://www.linkedin.com{job_url}"
            
            # Extract company name
            company_elem = job_elem.query_selector("h4.job-result-card__subtitle a, .company-name a")
            company = company_elem.inner_text().strip() if company_elem else ""
            
            # Extract location
            location_elem = job_elem.query_selector("span.job-result-card__location, .job-location")
            location = location_elem.inner_text().strip() if location_elem else ""
            
            # Extract job summary/snippet
            summary_elem = job_elem.query_selector("p.job-result-card__snippet, .job-summary")
            summary = summary_elem.inner_text().strip() if summary_elem else ""
            
            # Extract posted date
            date_elem = job_elem.query_selector("time.job-result-card__listdate, .posted-date")
            posted_date = date_elem.get_attribute("datetime") or date_elem.inner_text() if date_elem else ""
            
            # Extract job type (if available)
            job_type_elem = job_elem.query_selector(".job-type, .employment-type")
            job_type = job_type_elem.inner_text().strip() if job_type_elem else ""
            
            # Extract seniority level (if available)
            seniority_elem = job_elem.query_selector(".seniority-level")
            seniority = seniority_elem.inner_text().strip() if seniority_elem else ""
            
            # Validate required fields
            if not title or not company:
                console.print(f"[yellow]Skipping LinkedIn job with missing title or company[/yellow]")
                return None
            
            return {
                "title": title,
                "company": company,
                "location": location,
                "url": job_url,
                "summary": summary,
                "posted_date": posted_date,
                "job_type": job_type,
                "seniority_level": seniority,
            }
            
        except Exception as e:
            console.print(f"[yellow]Error extracting LinkedIn job data: {e}[/yellow]")
            return None
    
    def get_job_details(self, job_url: str) -> Dict:
        """
        Get detailed job information from a specific LinkedIn job URL.
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            Dictionary with detailed job information
        """
        if not self.browser_context:
            console.print("[yellow]Browser context required for job details[/yellow]")
            return {}
        
        page = self.browser_context.new_page()
        
        try:
            console.print(f"[cyan]Getting LinkedIn job details from: {job_url}[/cyan]")
            page.goto(job_url, timeout=30000)
            
            # Wait for job details to load
            page.wait_for_selector("div.jobs-description, .job-description", timeout=10000)
            
            # Extract detailed job description
            desc_elem = page.query_selector("div.jobs-description__content, .job-description")
            full_description = desc_elem.inner_text() if desc_elem else ""
            
            # Extract company information
            company_elem = page.query_selector("div.jobs-company, .company-info")
            company_info = company_elem.inner_text() if company_elem else ""
            
            # Extract skills if available
            skills_section = page.query_selector("section.jobs-skills, .skills-section")
            skills = []
            if skills_section:
                skill_elements = skills_section.query_selector_all("span.jobs-skill, .skill-item")
                skills = [elem.inner_text().strip() for elem in skill_elements]
            
            # Extract salary range if available
            salary_elem = page.query_selector(".jobs-details__salary, .salary-range")
            salary = salary_elem.inner_text().strip() if salary_elem else ""
            
            return {
                "full_description": full_description,
                "company_info": company_info,
                "skills": skills,
                "salary": salary,
            }
            
        except Exception as e:
            console.print(f"[yellow]Error getting LinkedIn job details: {e}[/yellow]")
            return {}
        finally:
            page.close()
    
    def apply_to_job(self, job_url: str) -> bool:
        """
        Attempt to apply to a LinkedIn job (if Easy Apply is available).
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            True if application was successful, False otherwise
        """
        if not self.browser_context:
            console.print("[yellow]Browser context required for job application[/yellow]")
            return False
        
        page = self.browser_context.new_page()
        
        try:
            page.goto(job_url, timeout=30000)
            
            # Look for Easy Apply button
            easy_apply_btn = page.query_selector("button.jobs-apply-button--top-card")
            
            if easy_apply_btn and "Easy Apply" in easy_apply_btn.inner_text():
                console.print("[green]Easy Apply button found![/green]")
                easy_apply_btn.click()
                
                # Handle the Easy Apply flow
                # This would need to be implemented based on the specific form fields
                console.print("[yellow]Easy Apply flow not fully implemented yet[/yellow]")
                return False
            else:
                console.print("[yellow]Easy Apply not available for this job[/yellow]")
                return False
                
        except Exception as e:
            console.print(f"[red]Error applying to LinkedIn job: {e}[/red]")
            return False
        finally:
            page.close()
