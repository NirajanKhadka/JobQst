"""
Lever ATS submitter implementation.
Handles job application automation for Lever-based job portals.
"""

from typing import Dict

from playwright.sync_api import Page
from rich.console import Console

from .base_submitter import BaseSubmitter
from src.core.exceptions import NeedsHumanException

console = Console()


class LeverSubmitter(BaseSubmitter):
    """
    Submitter for Lever ATS (FUTURE FEATURE).
    This is a stub implementation that will be developed in a future release.
    """

    def __init__(self, browser_context=None):
        self.browser_context = browser_context

    def submit(self, job: Dict, profile: Dict, resume_path: str, cover_letter_path: str) -> str:
        """
        Submit an application to Lever ATS.

        Args:
            job: Job dictionary with details
            profile: User profile dictionary
            resume_path: Path to the resume file
            cover_letter_path: Path to the cover letter file

        Returns:
            Status string (e.g., "Applied", "Failed", "Manual")
        """
        try:
            import logging
            from pathlib import Path
            from playwright.sync_api import sync_playwright
            
            logger = logging.getLogger(__name__)
            
            job_url = job.get('url', job.get('job_url', ''))
            if not job_url:
                logger.error("No job URL provided for Lever application")
                return "Failed"
            
            logger.info(f"Starting Lever ATS application for {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
            
            # Use existing browser context if available, otherwise create new one
            if self.browser_context:
                page = self.browser_context.new_page()
            else:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=False)  # Non-headless for debugging
                    context = browser.new_context()
                    page = context.new_page()
            
            try:
                # Navigate to job page
                logger.debug(f"Navigating to Lever job URL: {job_url}")
                page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)  # Wait for dynamic content
                
                # Look for "Apply" button - Lever usually has distinctive apply buttons
                apply_selectors = [
                    'a[data-qa="btn-apply"]',  # Lever's apply button
                    'button[data-qa="btn-apply"]',
                    'a.postings-btn-primary',
                    'button.postings-btn-primary',
                    'a[href*="apply"]',
                    'button:has-text("Apply")',
                    'a:has-text("Apply for this position")',
                    '.apply-button',
                    '.lever-apply-button'
                ]
                
                apply_button = None
                for selector in apply_selectors:
                    try:
                        apply_button = page.wait_for_selector(selector, timeout=3000)
                        if apply_button:
                            logger.debug(f"Found apply button with selector: {selector}")
                            break
                    except:
                        continue
                
                if not apply_button:
                    logger.warning("No apply button found on Lever job page")
                    return "Manual"
                
                # Click apply button
                apply_button.click()
                page.wait_for_timeout(3000)  # Wait for application form to load
                
                # Fill personal information
                personal_info = {
                    'name': profile.get('name', ''),
                    'email': profile.get('email', ''),
                    'phone': profile.get('phone', ''),
                    'linkedin': profile.get('linkedin_url', ''),
                    'website': profile.get('website', ''),
                    'location': profile.get('location', '')
                }
                
                # Common Lever form field selectors
                form_fields = {
                    'name': ['input[name*="name"]', 'input[placeholder*="name"]', '#name'],
                    'email': ['input[name*="email"]', 'input[type="email"]', '#email'],
                    'phone': ['input[name*="phone"]', 'input[type="tel"]', '#phone'],
                    'linkedin': ['input[name*="linkedin"]', 'input[placeholder*="linkedin"]'],
                    'website': ['input[name*="website"]', 'input[name*="portfolio"]'],
                    'location': ['input[name*="location"]', 'input[placeholder*="location"]']
                }
                
                # Fill available fields
                for field_name, selectors in form_fields.items():
                    value = personal_info.get(field_name, '')
                    if not value:
                        continue
                        
                    for selector in selectors:
                        try:
                            field = page.wait_for_selector(selector, timeout=2000)
                            if field:
                                field.clear()
                                field.fill(value)
                                logger.debug(f"Filled {field_name} field")
                                break
                        except:
                            continue
                
                # Handle resume upload
                if resume_path and Path(resume_path).exists():
                    upload_selectors = [
                        'input[type="file"][name*="resume"]',
                        'input[type="file"][accept*="pdf"]',
                        'input[type="file"]'
                    ]
                    
                    for selector in upload_selectors:
                        try:
                            file_input = page.wait_for_selector(selector, timeout=3000)
                            if file_input:
                                file_input.set_input_files(resume_path)
                                logger.info("Resume uploaded successfully")
                                page.wait_for_timeout(2000)  # Wait for upload
                                break
                        except:
                            continue
                
                # Handle cover letter upload or text area
                if cover_letter_path and Path(cover_letter_path).exists():
                    # Try file upload first
                    cover_letter_selectors = [
                        'input[type="file"][name*="cover"]',
                        'input[type="file"][name*="letter"]'
                    ]
                    
                    cover_letter_uploaded = False
                    for selector in cover_letter_selectors:
                        try:
                            file_input = page.wait_for_selector(selector, timeout=2000)
                            if file_input:
                                file_input.set_input_files(cover_letter_path)
                                logger.info("Cover letter uploaded successfully")
                                cover_letter_uploaded = True
                                break
                        except:
                            continue
                    
                    # If no file upload, try text area
                    if not cover_letter_uploaded:
                        text_selectors = [
                            'textarea[name*="cover"]',
                            'textarea[name*="letter"]',
                            'textarea[placeholder*="cover"]'
                        ]
                        
                        try:
                            # Read cover letter content if it's a text file
                            if cover_letter_path.endswith('.txt'):
                                cover_letter_text = Path(cover_letter_path).read_text(encoding='utf-8')
                                
                                for selector in text_selectors:
                                    try:
                                        textarea = page.wait_for_selector(selector, timeout=2000)
                                        if textarea:
                                            textarea.fill(cover_letter_text)
                                            logger.info("Cover letter text filled successfully")
                                            break
                                    except:
                                        continue
                        except Exception as e:
                            logger.warning(f"Could not fill cover letter text: {e}")
                
                # Handle additional questions/dropdowns
                # Lever often has custom questions - try to handle common ones
                try:
                    # Work authorization questions
                    auth_selectors = [
                        'select[name*="authorization"]',
                        'select[name*="visa"]',
                        'input[value*="Yes"][name*="authorization"]'
                    ]
                    
                    for selector in auth_selectors:
                        try:
                            element = page.wait_for_selector(selector, timeout=1000)
                            if element:
                                if element.tag_name.lower() == 'select':
                                    element.select_option(value="Yes")
                                else:
                                    element.click()
                                logger.debug("Answered work authorization question")
                                break
                        except:
                            continue
                    
                    # Sponsorship questions
                    sponsor_selectors = [
                        'select[name*="sponsor"]',
                        'input[value*="No"][name*="sponsor"]'
                    ]
                    
                    for selector in sponsor_selectors:
                        try:
                            element = page.wait_for_selector(selector, timeout=1000)
                            if element:
                                if element.tag_name.lower() == 'select':
                                    element.select_option(value="No")
                                else:
                                    element.click()
                                logger.debug("Answered sponsorship question")
                                break
                        except:
                            continue
                            
                except Exception as e:
                    logger.debug(f"Could not answer additional questions: {e}")
                
                # Look for submit button
                submit_selectors = [
                    'button[type="submit"]',
                    'button:has-text("Submit")',
                    'button:has-text("Apply")',
                    'button[data-qa="btn-submit"]',
                    'input[type="submit"]',
                    '.submit-button'
                ]
                
                submit_button = None
                for selector in submit_selectors:
                    try:
                        submit_button = page.wait_for_selector(selector, timeout=3000)
                        if submit_button and submit_button.is_enabled():
                            logger.debug(f"Found submit button with selector: {selector}")
                            break
                    except:
                        continue
                
                if not submit_button:
                    logger.warning("No submit button found - application may need manual completion")
                    return "Manual"
                
                # Submit the application
                submit_button.click()
                page.wait_for_timeout(5000)  # Wait for submission
                
                # Check for success indicators
                success_indicators = [
                    ':has-text("Thank you")',
                    ':has-text("Application submitted")',
                    ':has-text("We have received")',
                    ':has-text("Success")',
                    '.success-message',
                    '.confirmation'
                ]
                
                for indicator in success_indicators:
                    try:
                        if page.wait_for_selector(indicator, timeout=3000):
                            logger.info("Application submitted successfully to Lever ATS")
                            return "Applied"
                    except:
                        continue
                
                # Check for error indicators
                error_indicators = [
                    ':has-text("Error")',
                    ':has-text("Please")',
                    ':has-text("Required")',
                    '.error-message',
                    '.field-error'
                ]
                
                for indicator in error_indicators:
                    try:
                        if page.wait_for_selector(indicator, timeout=2000):
                            logger.warning("Application may have errors - needs manual review")
                            return "Manual"
                    except:
                        continue
                
                # If no clear success/error, check URL change
                if "thank" in page.url.lower() or "success" in page.url.lower():
                    logger.info("Application likely submitted based on URL change")
                    return "Applied"
                
                logger.warning("Application status unclear - marking as manual")
                return "Manual"
                
            finally:
                if not self.browser_context:
                    # Only close if we created our own browser
                    try:
                        page.close()
                        context.close()
                        browser.close()
                    except:
                        pass
        
        except Exception as e:
            logger.error(f"Error submitting Lever application: {e}")
            return "Failed"

