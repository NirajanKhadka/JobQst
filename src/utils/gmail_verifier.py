#!/usr/bin/env python3
"""
Gmail Application Verifier
Verifies job applications by checking Gmail for confirmation emails.
"""

import asyncio
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from playwright.async_api import async_playwright, Page

console = Console()

@dataclass
class ApplicationConfirmation:
    """Application confirmation found in Gmail."""
    job_title: Optional[str]
    company: Optional[str]
    email_subject: str
    email_sender: str
    received_time: str
    confirmation_type: str  # 'received', 'under_review', 'rejected', 'interview'
    email_content: str
    application_id: Optional[str]

class GmailVerifier:
    """
    Verifies job applications by checking Gmail for confirmation emails.
    """
    
    def __init__(self, email: str = "Nirajan.tech@gmail.com", password: str = None, profile_name: str = "default"):
        """
        Initialize Gmail verifier.
        
        Args:
            email: Gmail address to check
            password: Gmail password (will prompt if not provided)
            profile_name: Name of the profile for logging
        """
        self.email = email
        self.password = password
        self.profile_name = profile_name
        self.logged_in = False
        
        # Email patterns for different types of confirmations
        self.confirmation_patterns = {
            'received': [
                r'application.*received',
                r'thank you.*applying',
                r'we.*received.*application',
                r'application.*submitted',
                r'confirmation.*application'
            ],
            'under_review': [
                r'application.*under review',
                r'reviewing.*application',
                r'application.*being reviewed',
                r'next steps',
                r'application status'
            ],
            'rejected': [
                r'unfortunately',
                r'not.*selected',
                r'decided.*move forward',
                r'application.*unsuccessful',
                r'thank you.*interest.*however'
            ],
            'interview': [
                r'interview',
                r'next step.*interview',
                r'schedule.*call',
                r'phone.*screen',
                r'video.*call'
            ]
        }
        
        # Company email domains to look for
        self.job_domains = [
            'workday.com', 'greenhouse.io', 'lever.co', 'bamboohr.com',
            'smartrecruiters.com', 'jobvite.com', 'icims.com'
        ]
    
    async def login_to_gmail(self, page: Page) -> bool:
        """
        Login to Gmail using Playwright.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            console.print("[cyan]🔐 Logging into Gmail...[/cyan]")
            
            # Navigate to Gmail
            await page.goto("https://mail.google.com", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Check if already logged in
            try:
                await page.wait_for_selector('[data-testid="compose"]', timeout=5000)
                console.print("[green]✅ Already logged into Gmail[/green]")
                self.logged_in = True
                return True
            except:
                pass
            
            # Enter email
            email_input = await page.wait_for_selector('input[type="email"]', timeout=10000)
            await email_input.fill(self.email)
            await page.click('#identifierNext')
            await page.wait_for_timeout(2000)
            
            # Check for password input
            try:
                password_input = await page.wait_for_selector('input[type="password"]', timeout=10000)
                
                if not self.password:
                    console.print(f"[yellow]🔑 Please enter password for {self.email}[/yellow]")
                    self.password = input("Password: ")
                
                await password_input.fill(self.password)
                await page.click('#passwordNext')
                await page.wait_for_timeout(3000)
                
            except Exception as e:
                console.print(f"[yellow]⚠️ Password input not found or 2FA required: {e}[/yellow]")
                console.print("[yellow]Please complete login manually in the browser[/yellow]")
                input("Press Enter when logged in...")
            
            # Verify login success
            try:
                await page.wait_for_selector('[data-testid="compose"]', timeout=15000)
                console.print("[green]✅ Successfully logged into Gmail[/green]")
                self.logged_in = True
                return True
            except:
                console.print("[red]❌ Gmail login failed[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Gmail login error: {e}[/red]")
            return False
    
    async def check_recent_emails(self, page: Page, hours_back: int = 24) -> List[ApplicationConfirmation]:
        """
        Check recent emails for job application confirmations.
        
        Args:
            page: Playwright page object
            hours_back: How many hours back to check emails
            
        Returns:
            List of application confirmations found
        """
        if not self.logged_in:
            console.print("[red]❌ Not logged into Gmail[/red]")
            return []
        
        console.print(f"[cyan]📧 Checking emails from last {hours_back} hours...[/cyan]")
        
        confirmations = []
        
        try:
            # Wait for inbox to load
            await page.wait_for_selector('[role="main"]', timeout=10000)
            await page.wait_for_timeout(2000)
            
            # Get email list
            email_rows = await page.query_selector_all('[role="listitem"]')
            
            console.print(f"[cyan]📋 Found {len(email_rows)} emails to check[/cyan]")
            
            for i, row in enumerate(email_rows[:20]):  # Check first 20 emails
                try:
                    # Get email preview info
                    sender_elem = await row.query_selector('[email]')
                    subject_elem = await row.query_selector('[data-thread-id]')
                    
                    if not sender_elem or not subject_elem:
                        continue
                    
                    sender = await sender_elem.get_attribute('email') or await sender_elem.inner_text()
                    subject = await subject_elem.get_attribute('aria-label') or await subject_elem.inner_text()
                    
                    # Check if this looks like a job application email
                    if self._is_job_application_email(sender, subject):
                        console.print(f"[yellow]📧 Checking potential job email: {subject[:50]}...[/yellow]")
                        
                        # Click to open email
                        await row.click()
                        await page.wait_for_timeout(2000)
                        
                        # Extract email content
                        confirmation = await self._extract_email_details(page, sender, subject)
                        if confirmation:
                            confirmations.append(confirmation)
                        
                        # Go back to inbox
                        await page.keyboard.press('u')  # Gmail shortcut to go back to inbox
                        await page.wait_for_timeout(1000)
                
                except Exception as e:
                    console.print(f"[yellow]⚠️ Error processing email {i}: {e}[/yellow]")
                    continue
            
            return confirmations
            
        except Exception as e:
            console.print(f"[red]❌ Error checking emails: {e}[/red]")
            return []
    
    def _is_job_application_email(self, sender: str, subject: str) -> bool:
        """Check if email looks like a job application confirmation."""
        sender_lower = sender.lower()
        subject_lower = subject.lower()
        
        # Check for job-related keywords in subject
        job_keywords = [
            'application', 'thank you', 'received', 'confirmation', 'interview',
            'position', 'job', 'career', 'opportunity', 'hiring', 'recruitment'
        ]
        
        subject_has_keywords = any(keyword in subject_lower for keyword in job_keywords)
        
        # Check for known job platform domains
        domain_match = any(domain in sender_lower for domain in self.job_domains)
        
        # Check for company-like sender (not promotional)
        not_promotional = not any(word in sender_lower for word in [
            'noreply', 'no-reply', 'newsletter', 'marketing', 'promo'
        ])
        
        return (subject_has_keywords or domain_match) and not_promotional
    
    async def _extract_email_details(self, page: Page, sender: str, subject: str) -> Optional[ApplicationConfirmation]:
        """Extract details from an opened email."""
        try:
            # Wait for email content to load
            await page.wait_for_selector('[role="listitem"]', timeout=5000)
            
            # Get email content
            content_elem = await page.query_selector('[role="listitem"]')
            if content_elem:
                content = await content_elem.inner_text()
            else:
                content = ""
            
            # Get timestamp
            time_elem = await page.query_selector('[title*="GMT"]')
            received_time = ""
            if time_elem:
                received_time = await time_elem.get_attribute('title') or ""
            
            # Determine confirmation type
            confirmation_type = self._classify_email_type(subject, content)
            
            # Extract job details
            job_title = self._extract_job_title(subject, content)
            company = self._extract_company_name(sender, content)
            application_id = self._extract_application_id(content)
            
            return ApplicationConfirmation(
                job_title=job_title,
                company=company,
                email_subject=subject,
                email_sender=sender,
                received_time=received_time,
                confirmation_type=confirmation_type,
                email_content=content[:500],  # First 500 chars
                application_id=application_id
            )
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting email details: {e}[/yellow]")
            return None
    
    def _classify_email_type(self, subject: str, content: str) -> str:
        """Classify the type of application email."""
        text = f"{subject} {content}".lower()
        
        for email_type, patterns in self.confirmation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return email_type
        
        return 'received'  # Default to received
    
    def _extract_job_title(self, subject: str, content: str) -> Optional[str]:
        """Extract job title from email."""
        # Look for job title patterns
        patterns = [
            r'(?:position|role|job):\s*([^\n\r]+)',
            r'for the\s+([^\n\r]+?)\s+position',
            r'([A-Z][a-z\s]+(?:Engineer|Developer|Analyst|Manager|Specialist|Coordinator))'
        ]
        
        text = f"{subject} {content}"
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_company_name(self, sender: str, content: str) -> Optional[str]:
        """Extract company name from email."""
        # Try to get company from sender domain
        if '@' in sender:
            domain = sender.split('@')[1]
            # Remove common email domains
            if not any(common in domain for common in ['gmail', 'yahoo', 'outlook', 'hotmail']):
                company = domain.split('.')[0]
                return company.title()
        
        # Look for company name in content
        patterns = [
            r'(?:from|at|with)\s+([A-Z][a-zA-Z\s&]+(?:Inc|LLC|Corp|Company|Ltd))',
            r'([A-Z][a-zA-Z\s&]+)\s+(?:team|hiring|recruitment)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_application_id(self, content: str) -> Optional[str]:
        """Extract application ID from email content."""
        patterns = [
            r'(?:application|reference|id):\s*([A-Z0-9-]+)',
            r'(?:application|reference)\s+(?:number|id)\s*:\s*([A-Z0-9-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
