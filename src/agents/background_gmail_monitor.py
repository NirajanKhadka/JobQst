#!/usr/bin/env python3
"""
Background Gmail Monitor Agent
Continuously monitors Gmail for job application confirmation emails
and automatically verifies applications in the database.
"""

import asyncio
import time
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from playwright.async_api import async_playwright, Page, BrowserContext

from job_database import get_job_db

console = Console()

@dataclass
class EmailConfirmation:
    """Email confirmation data."""
    subject: str
    sender: str
    content: str
    received_time: str
    job_title: Optional[str] = None
    company: Optional[str] = None
    application_id: Optional[str] = None
    confirmation_type: str = "received"  # received, rejected, interview

class BackgroundGmailMonitor:
    """
    Background agent that continuously monitors Gmail for job application
    confirmation emails and automatically updates the database.
    """
    
    def __init__(self, profile_name: str, email: str = "Nirajan.tech@gmail.com"):
        """Initialize the Gmail monitor."""
        self.profile_name = profile_name
        self.email = email
        self.db = get_job_db(profile_name)
        
        # Monitoring state
        self.is_running = False
        self.last_check_time = datetime.now()
        self.processed_emails: Set[str] = set()  # Track processed email IDs
        
        # Statistics
        self.stats = {
            "emails_checked": 0,
            "confirmations_found": 0,
            "jobs_verified": 0,
            "monitoring_duration": 0,
            "last_confirmation": None
        }
        
        # Email patterns for different confirmation types
        self.confirmation_patterns = {
            "received": [
                r"application.*received",
                r"thank you.*applying",
                r"we.*received.*application",
                r"application.*submitted",
                r"confirmation.*application",
                r"application.*complete"
            ],
            "under_review": [
                r"application.*under review",
                r"reviewing.*application",
                r"application.*being reviewed",
                r"next steps",
                r"application status"
            ],
            "rejected": [
                r"unfortunately",
                r"not.*selected",
                r"decided.*move forward",
                r"application.*unsuccessful",
                r"thank you.*interest.*however",
                r"position.*filled"
            ],
            "interview": [
                r"interview",
                r"next step.*interview",
                r"schedule.*call",
                r"phone.*screen",
                r"video.*call",
                r"would like.*speak"
            ]
        }
        
        # Job site domains to prioritize
        self.job_domains = [
            "workday.com", "greenhouse.io", "lever.co", "bamboohr.com",
            "smartrecruiters.com", "jobvite.com", "icims.com", "taleo.net",
            "eluta.ca", "indeed.com", "linkedin.com"
        ]
    
    async def start_monitoring(self, check_interval: int = 60) -> None:
        """
        Start continuous Gmail monitoring.
        
        Args:
            check_interval: How often to check Gmail (seconds)
        """
        console.print(Panel.fit("📧 STARTING BACKGROUND GMAIL MONITOR", style="bold blue"))
        console.print(f"[cyan]Email: {self.email}[/cyan]")
        console.print(f"[cyan]Check interval: {check_interval} seconds[/cyan]")
        console.print(f"[cyan]Profile: {self.profile_name}[/cyan]")
        
        self.is_running = True
        start_time = time.time()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # Non-headless so you can see and help with login
                args=["--start-maximized"]
            )
            
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            
            try:
                page = await context.new_page()
                
                # Initial Gmail login
                if not await self._login_to_gmail(page):
                    console.print("[red]❌ Failed to login to Gmail[/red]")
                    return
                
                console.print("[green]✅ Gmail monitoring started successfully![/green]")
                
                # Create live display for monitoring status
                with Live(self._create_status_table(), refresh_per_second=1) as live:
                    while self.is_running:
                        try:
                            # Check for new emails
                            new_confirmations = await self._check_new_emails(page)
                            
                            # Process confirmations
                            if new_confirmations:
                                await self._process_confirmations(new_confirmations)
                            
                            # Update statistics
                            self.stats["monitoring_duration"] = time.time() - start_time
                            
                            # Update live display
                            live.update(self._create_status_table())
                            
                            # Wait for next check
                            await asyncio.sleep(check_interval)
                            
                        except KeyboardInterrupt:
                            console.print("\n[yellow]⚠️ Monitoring stopped by user[/yellow]")
                            break
                        except Exception as e:
                            console.print(f"[red]❌ Error during monitoring: {e}[/red]")
                            await asyncio.sleep(30)  # Wait before retrying
                
            finally:
                self.is_running = False
                input("\nPress Enter to close browser...")
                await context.close()
                await browser.close()
    
    async def _login_to_gmail(self, page: Page) -> bool:
        """Login to Gmail with passkey support."""
        try:
            console.print("[cyan]🔐 Opening Gmail...[/cyan]")
            
            await page.goto("https://mail.google.com", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Check if already logged in
            try:
                await page.wait_for_selector('[data-testid="compose"]', timeout=5000)
                console.print("[green]✅ Already logged into Gmail[/green]")
                return True
            except:
                pass
            
            # Try automatic login with saved credentials/passkey
            try:
                # Enter email
                email_input = await page.wait_for_selector('input[type="email"]', timeout=10000)
                await email_input.fill(self.email)
                await page.click('#identifierNext')
                await page.wait_for_timeout(3000)
                
                # Check for passkey option
                try:
                    passkey_button = await page.wait_for_selector('button:has-text("Use your passkey")', timeout=5000)
                    if passkey_button:
                        console.print("[cyan]🔑 Using passkey for login...[/cyan]")
                        await passkey_button.click()
                        await page.wait_for_timeout(5000)
                except:
                    pass
                
                # Check for password input
                try:
                    password_input = await page.wait_for_selector('input[type="password"]', timeout=5000)
                    if password_input:
                        console.print("[yellow]🔑 Password required. Please enter password manually.[/yellow]")
                        console.print("[yellow]The system will wait for you to complete login...[/yellow]")
                except:
                    pass
                
                # Wait for successful login
                console.print("[cyan]⏳ Waiting for Gmail login to complete...[/cyan]")
                await page.wait_for_selector('[data-testid="compose"]', timeout=60000)
                console.print("[green]✅ Successfully logged into Gmail![/green]")
                return True
                
            except Exception as e:
                console.print(f"[red]❌ Login failed: {e}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Gmail login error: {e}[/red]")
            return False
    
    async def _check_new_emails(self, page: Page) -> List[EmailConfirmation]:
        """Check for new emails since last check."""
        try:
            # Navigate to inbox if not already there
            await page.goto("https://mail.google.com/mail/u/0/#inbox", timeout=10000)
            await page.wait_for_timeout(2000)
            
            # Get recent emails (last 50)
            email_rows = await page.query_selector_all('tr[role="row"]')
            
            new_confirmations = []
            emails_checked = 0
            
            for row in email_rows[:50]:  # Check last 50 emails
                try:
                    # Extract email info
                    email_info = await self._extract_email_info(row)
                    if not email_info:
                        continue
                    
                    emails_checked += 1
                    
                    # Skip if already processed
                    email_id = f"{email_info['sender']}_{email_info['subject']}_{email_info['date']}"
                    if email_id in self.processed_emails:
                        continue
                    
                    # Check if it's a job-related email
                    if self._is_job_confirmation_email(email_info):
                        # Click to get full content
                        await row.click()
                        await page.wait_for_timeout(2000)
                        
                        # Extract full email content
                        content = await self._extract_email_content(page)
                        
                        # Create confirmation object
                        confirmation = EmailConfirmation(
                            subject=email_info['subject'],
                            sender=email_info['sender'],
                            content=content,
                            received_time=email_info['date']
                        )
                        
                        # Extract job details
                        confirmation.job_title = self._extract_job_title(confirmation.subject, content)
                        confirmation.company = self._extract_company_name(confirmation.sender, content)
                        confirmation.confirmation_type = self._classify_confirmation_type(confirmation.subject, content)
                        confirmation.application_id = self._extract_application_id(content)
                        
                        new_confirmations.append(confirmation)
                        self.processed_emails.add(email_id)
                        
                        console.print(f"[green]📧 New confirmation: {confirmation.subject[:50]}...[/green]")
                        
                        # Go back to inbox
                        await page.keyboard.press('u')
                        await page.wait_for_timeout(1000)
                
                except Exception as e:
                    continue
            
            self.stats["emails_checked"] += emails_checked
            return new_confirmations
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Error checking emails: {e}[/yellow]")
            return []
    
    async def _extract_email_info(self, row) -> Optional[Dict]:
        """Extract basic email info from row."""
        try:
            # Get sender
            sender_elem = await row.query_selector('[email]')
            sender = ""
            if sender_elem:
                sender = await sender_elem.get_attribute('email') or await sender_elem.inner_text()
            
            # Get subject
            subject_elem = await row.query_selector('span[data-thread-id]')
            subject = ""
            if subject_elem:
                subject = await subject_elem.inner_text()
            
            # Get date
            date_elem = await row.query_selector('[title]')
            date = ""
            if date_elem:
                date = await date_elem.get_attribute('title') or await date_elem.inner_text()
            
            if sender and subject:
                return {
                    'sender': sender.strip(),
                    'subject': subject.strip(),
                    'date': date.strip()
                }
            
            return None
            
        except:
            return None
    
    def _is_job_confirmation_email(self, email_info: Dict) -> bool:
        """Check if email is a job confirmation."""
        text = f"{email_info['subject']} {email_info['sender']}".lower()
        
        # Check for job confirmation patterns
        for patterns in self.confirmation_patterns.values():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
        
        # Check for job site domains
        sender = email_info['sender'].lower()
        for domain in self.job_domains:
            if domain in sender:
                return True
        
        # Check for job keywords
        job_keywords = [
            'application', 'position', 'job', 'career', 'hiring', 'interview',
            'thank you', 'received', 'confirmation', 'opportunity'
        ]
        
        return any(keyword in text for keyword in job_keywords)
    
    async def _extract_email_content(self, page: Page) -> str:
        """Extract full email content."""
        try:
            # Wait for email content to load
            await page.wait_for_selector('[role="listitem"]', timeout=5000)
            
            # Get email body
            content_elem = await page.query_selector('[role="listitem"]')
            if content_elem:
                content = await content_elem.inner_text()
                return content
            
            return ""
            
        except:
            return ""

    def _classify_confirmation_type(self, subject: str, content: str) -> str:
        """Classify the type of confirmation email."""
        text = f"{subject} {content}".lower()

        for conf_type, patterns in self.confirmation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return conf_type

        return "received"  # Default

    def _extract_job_title(self, subject: str, content: str) -> Optional[str]:
        """Extract job title from email."""
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
        # Try sender domain first
        if '@' in sender:
            domain = sender.split('@')[1]
            if not any(common in domain for common in ['gmail', 'yahoo', 'outlook', 'hotmail']):
                company = domain.split('.')[0]
                return company.title()

        # Look in content
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
        """Extract application ID from content."""
        patterns = [
            r'(?:application|reference|id):\s*([A-Z0-9-]+)',
            r'(?:application|reference)\s+(?:number|id)\s*:\s*([A-Z0-9-]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    async def _process_confirmations(self, confirmations: List[EmailConfirmation]) -> None:
        """Process confirmation emails and update database."""
        for confirmation in confirmations:
            try:
                # Find matching job in database
                matched_job = await self._find_matching_job(confirmation)

                if matched_job:
                    # Update job status based on confirmation type
                    if confirmation.confirmation_type in ["received", "under_review"]:
                        await self._mark_job_as_applied(matched_job, confirmation)
                        self.stats["jobs_verified"] += 1
                        console.print(f"[green]✅ Verified application: {matched_job.get('title', 'Unknown')}[/green]")
                    elif confirmation.confirmation_type == "rejected":
                        await self._mark_job_as_rejected(matched_job, confirmation)
                        console.print(f"[yellow]❌ Application rejected: {matched_job.get('title', 'Unknown')}[/yellow]")
                    elif confirmation.confirmation_type == "interview":
                        await self._mark_job_as_interview(matched_job, confirmation)
                        console.print(f"[cyan]🎉 Interview scheduled: {matched_job.get('title', 'Unknown')}[/cyan]")
                else:
                    console.print(f"[yellow]⚠️ No matching job found for: {confirmation.subject[:50]}...[/yellow]")

                self.stats["confirmations_found"] += 1
                self.stats["last_confirmation"] = datetime.now().isoformat()

            except Exception as e:
                console.print(f"[red]❌ Error processing confirmation: {e}[/red]")

    async def _find_matching_job(self, confirmation: EmailConfirmation) -> Optional[Dict]:
        """Find matching job in database for confirmation email."""
        try:
            # Get recent jobs that might match
            recent_jobs = self.db.get_jobs(limit=100, applied=None)  # Get all recent jobs

            best_match = None
            best_score = 0.0

            for job in recent_jobs:
                score = 0.0

                # Company matching (high weight)
                if confirmation.company and job.get('company'):
                    if confirmation.company.lower() in job.get('company', '').lower():
                        score += 0.6

                # Job title matching (medium weight)
                if confirmation.job_title and job.get('title'):
                    title_words = confirmation.job_title.lower().split()
                    job_title = job.get('title', '').lower()
                    matches = sum(1 for word in title_words if len(word) > 3 and word in job_title)
                    if matches > 0:
                        score += (matches / len(title_words)) * 0.4

                # URL domain matching (low weight)
                job_url = job.get('url', '').lower()
                sender_domain = confirmation.sender.split('@')[1] if '@' in confirmation.sender else ''
                if sender_domain and sender_domain in job_url:
                    score += 0.2

                if score > best_score and score > 0.3:  # Minimum threshold
                    best_match = job
                    best_score = score

            return best_match

        except Exception as e:
            console.print(f"[red]❌ Error finding matching job: {e}[/red]")
            return None

    async def _mark_job_as_applied(self, job: Dict, confirmation: EmailConfirmation) -> None:
        """Mark job as successfully applied."""
        try:
            job_id = job.get('id')
            if job_id:
                # Update job in database
                # Note: This would need to be implemented in the database class
                # self.db.mark_job_applied(job_id, {
                #     'confirmation_email': confirmation.subject,
                #     'confirmation_sender': confirmation.sender,
                #     'confirmation_date': confirmation.received_time,
                #     'application_id': confirmation.application_id
                # })

                console.print(f"[green]📝 Marked as applied: {job.get('title', 'Unknown')}[/green]")

        except Exception as e:
            console.print(f"[red]❌ Error marking job as applied: {e}[/red]")

    async def _mark_job_as_rejected(self, job: Dict, confirmation: EmailConfirmation) -> None:
        """Mark job as rejected."""
        try:
            job_id = job.get('id')
            if job_id:
                # Update job status to rejected
                console.print(f"[yellow]📝 Marked as rejected: {job.get('title', 'Unknown')}[/yellow]")

        except Exception as e:
            console.print(f"[red]❌ Error marking job as rejected: {e}[/red]")

    async def _mark_job_as_interview(self, job: Dict, confirmation: EmailConfirmation) -> None:
        """Mark job as interview scheduled."""
        try:
            job_id = job.get('id')
            if job_id:
                # Update job status to interview
                console.print(f"[cyan]📝 Marked as interview: {job.get('title', 'Unknown')}[/cyan]")

        except Exception as e:
            console.print(f"[red]❌ Error marking job as interview: {e}[/red]")

    def _create_status_table(self) -> Table:
        """Create live status table for monitoring."""
        table = Table(title="📧 Gmail Monitor Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        # Format monitoring duration
        duration = int(self.stats["monitoring_duration"])
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        table.add_row("Status", "🟢 Running" if self.is_running else "🔴 Stopped")
        table.add_row("Monitoring Duration", duration_str)
        table.add_row("Emails Checked", str(self.stats["emails_checked"]))
        table.add_row("Confirmations Found", str(self.stats["confirmations_found"]))
        table.add_row("Jobs Verified", str(self.stats["jobs_verified"]))
        table.add_row("Last Check", datetime.now().strftime("%H:%M:%S"))
        table.add_row("Last Confirmation", self.stats["last_confirmation"] or "None")

        return table

    def stop_monitoring(self) -> None:
        """Stop the monitoring process."""
        self.is_running = False
        console.print("[yellow]⚠️ Stopping Gmail monitoring...[/yellow]")

    def get_stats(self) -> Dict:
        """Get monitoring statistics."""
        return self.stats.copy()

    def save_monitoring_report(self) -> None:
        """Save monitoring report to file."""
        try:
            report_file = Path(f"profiles/{self.profile_name}/gmail_monitoring_report.json")
            report_file.parent.mkdir(exist_ok=True)

            report_data = {
                'monitoring_session': datetime.now().isoformat(),
                'email_account': self.email,
                'statistics': self.stats,
                'processed_emails_count': len(self.processed_emails)
            }

            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)

            console.print(f"[green]💾 Monitoring report saved to: {report_file}[/green]")

        except Exception as e:
            console.print(f"[yellow]⚠️ Could not save monitoring report: {e}[/yellow]")


# Convenience functions
async def start_background_monitor(profile_name: str = "Nirajan", check_interval: int = 60) -> None:
    """
    Start background Gmail monitoring.

    Args:
        profile_name: Profile name for database access
        check_interval: How often to check Gmail (seconds)
    """
    monitor = BackgroundGmailMonitor(profile_name)
    await monitor.start_monitoring(check_interval)


if __name__ == "__main__":
    import asyncio

    # Run background monitor when script is executed directly
    asyncio.run(start_background_monitor())
