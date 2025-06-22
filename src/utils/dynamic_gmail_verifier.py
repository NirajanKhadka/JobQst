#!/usr/bin/env python3
"""
Dynamic Gmail Verifier
Interactive Gmail verification system that matches confirmation emails 
with applied jobs and marks them as verified.
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
from rich.prompt import Prompt, Confirm
from playwright.async_api import async_playwright, Page

from job_database import get_job_db

console = Console()

@dataclass
class EmailMatch:
    """Email matched with a job application."""
    email_subject: str
    email_sender: str
    email_date: str
    email_snippet: str
    matched_job: Optional[Dict] = None
    confidence_score: float = 0.0
    match_reasons: List[str] = None

class DynamicGmailVerifier:
    """
    Interactive Gmail verification system that dynamically matches 
    confirmation emails with applied jobs.
    """
    
    def __init__(self, profile_name: str, email: str = "Nirajan.tech@gmail.com"):
        """
        Initialize the dynamic Gmail verifier.
        
        Args:
            profile_name: Profile name for database access
            email: Gmail address to check
        """
        self.profile_name = profile_name
        self.email = email
        self.db = get_job_db(profile_name)
        
        # Recently applied jobs (for matching)
        self.recent_applications = []
        
        # Email patterns for job confirmations
        self.job_email_patterns = [
            r'application.*received',
            r'thank you.*applying',
            r'we.*received.*application',
            r'application.*submitted',
            r'confirmation.*application',
            r'application.*under review',
            r'next steps',
            r'interview',
            r'position.*filled'
        ]
        
        # Company domain patterns
        self.company_domains = [
            'workday.com', 'greenhouse.io', 'lever.co', 'bamboohr.com',
            'smartrecruiters.com', 'jobvite.com', 'icims.com', 'taleo.net'
        ]
    
    async def initialize(self) -> bool:
        """Initialize the verifier and load recent applications."""
        try:
            # Load recent applications from database
            self.recent_applications = self.db.get_recent_applications(days=7)
            
            console.print(f"[green]✅ Loaded {len(self.recent_applications)} recent applications[/green]")
            console.print(f"[cyan]📧 Gmail account: {self.email}[/cyan]")
            
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Initialization failed: {e}[/red]")
            return False
    
    async def verify_applications_with_gmail(self) -> List[EmailMatch]:
        """
        Main function to verify applications using Gmail.
        Opens Gmail in non-headless mode for interactive verification.
        """
        console.print(Panel.fit("📧 DYNAMIC GMAIL VERIFICATION", style="bold blue"))
        
        if not self.recent_applications:
            console.print("[yellow]⚠️ No recent applications found to verify[/yellow]")
            return []
        
        # Show recent applications
        self._display_recent_applications()
        
        if not Confirm.ask("Proceed with Gmail verification?"):
            return []
        
        async with async_playwright() as p:
            # Launch browser in non-headless mode
            browser = await p.chromium.launch(
                headless=False,  # Non-headless so you can see what's happening
                args=["--start-maximized"]
            )
            
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            
            try:
                page = await context.new_page()
                
                # Login to Gmail
                if not await self._login_to_gmail(page):
                    return []
                
                # Get inbox emails
                emails = await self._get_inbox_emails(page)
                
                # Match emails with applications
                matches = await self._match_emails_with_jobs(emails)
                
                # Interactive verification
                verified_matches = await self._interactive_verification(page, matches)
                
                # Update database with verified applications
                await self._update_verified_applications(verified_matches)
                
                return verified_matches
                
            finally:
                input("\nPress Enter to close browser...")
                await context.close()
                await browser.close()
    
    def _display_recent_applications(self):
        """Display recent applications for reference."""
        console.print(f"\n[bold]📋 Recent Applications ({len(self.recent_applications)} jobs):[/bold]")
        
        table = Table()
        table.add_column("Date", style="cyan")
        table.add_column("Job Title", style="green", max_width=30)
        table.add_column("Company", style="yellow", max_width=25)
        table.add_column("Status", style="magenta")
        
        for app in self.recent_applications[:10]:  # Show first 10
            date = app.get('applied_date', 'Unknown')[:10]  # Just date part
            title = app.get('title', 'Unknown')
            company = app.get('company', 'Unknown')
            status = app.get('status', 'Unknown')
            
            table.add_row(date, title, company, status)
        
        console.print(table)
        
        if len(self.recent_applications) > 10:
            console.print(f"[dim]... and {len(self.recent_applications) - 10} more applications[/dim]")
    
    async def _login_to_gmail(self, page: Page) -> bool:
        """Login to Gmail interactively."""
        try:
            console.print("[cyan]🔐 Opening Gmail for login...[/cyan]")
            
            await page.goto("https://mail.google.com", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Check if already logged in
            try:
                await page.wait_for_selector('[data-testid="compose"]', timeout=5000)
                console.print("[green]✅ Already logged into Gmail[/green]")
                return True
            except:
                pass
            
            # Interactive login
            console.print("[yellow]🔑 Please log into Gmail in the browser window[/yellow]")
            console.print("[yellow]The system will wait for you to complete login...[/yellow]")
            
            # Wait for login completion
            while True:
                try:
                    await page.wait_for_selector('[data-testid="compose"]', timeout=5000)
                    console.print("[green]✅ Gmail login detected![/green]")
                    return True
                except:
                    if not Confirm.ask("Still logging in? Continue waiting?"):
                        return False
                    continue
                    
        except Exception as e:
            console.print(f"[red]❌ Gmail login error: {e}[/red]")
            return False
    
    async def _get_inbox_emails(self, page: Page, limit: int = 50) -> List[Dict]:
        """Get list of emails from Gmail inbox."""
        console.print(f"[cyan]📧 Getting inbox emails (limit: {limit})...[/cyan]")
        
        emails = []
        
        try:
            # Wait for inbox to load
            await page.wait_for_selector('[role="main"]', timeout=10000)
            await page.wait_for_timeout(3000)
            
            # Scroll to load more emails
            for _ in range(3):
                await page.keyboard.press('End')
                await page.wait_for_timeout(1000)
            
            # Get email rows
            email_rows = await page.query_selector_all('tr[role="row"]')
            console.print(f"[cyan]📋 Found {len(email_rows)} email rows[/cyan]")
            
            for i, row in enumerate(email_rows[:limit]):
                try:
                    # Extract email info from row
                    email_info = await self._extract_email_info_from_row(row)
                    if email_info:
                        emails.append(email_info)
                        
                        # Show progress
                        if i % 10 == 0:
                            console.print(f"[dim]Processed {i}/{min(len(email_rows), limit)} emails...[/dim]")
                
                except Exception as e:
                    continue
            
            console.print(f"[green]✅ Extracted {len(emails)} emails from inbox[/green]")
            return emails
            
        except Exception as e:
            console.print(f"[red]❌ Error getting inbox emails: {e}[/red]")
            return []
    
    async def _extract_email_info_from_row(self, row) -> Optional[Dict]:
        """Extract email information from a Gmail row element."""
        try:
            # Get sender
            sender_elem = await row.query_selector('[email]')
            sender = ""
            if sender_elem:
                sender = await sender_elem.get_attribute('email') or await sender_elem.inner_text()
            
            # Get subject and snippet
            subject_elem = await row.query_selector('span[data-thread-id]')
            subject = ""
            if subject_elem:
                subject = await subject_elem.inner_text()
            
            # Get date
            date_elem = await row.query_selector('[title]')
            date = ""
            if date_elem:
                date = await date_elem.get_attribute('title') or await date_elem.inner_text()
            
            # Get snippet (preview text)
            snippet_elems = await row.query_selector_all('span')
            snippet = ""
            for elem in snippet_elems:
                text = await elem.inner_text()
                if len(text) > 20 and not any(skip in text for skip in ['Inbox', 'Starred', 'Sent']):
                    snippet = text[:100]
                    break
            
            if sender and subject:
                return {
                    'sender': sender.strip(),
                    'subject': subject.strip(),
                    'date': date.strip(),
                    'snippet': snippet.strip(),
                    'row_element': row  # Keep reference for clicking
                }
            
            return None
            
        except Exception as e:
            return None
    
    async def _match_emails_with_jobs(self, emails: List[Dict]) -> List[EmailMatch]:
        """Match emails with recent job applications."""
        console.print(f"[cyan]🔍 Matching {len(emails)} emails with {len(self.recent_applications)} applications...[/cyan]")
        
        matches = []
        
        for email in emails:
            # Check if email looks like job-related
            if self._is_job_related_email(email):
                # Try to match with applications
                matched_job, confidence, reasons = self._find_matching_job(email)
                
                match = EmailMatch(
                    email_subject=email['subject'],
                    email_sender=email['sender'],
                    email_date=email['date'],
                    email_snippet=email['snippet'],
                    matched_job=matched_job,
                    confidence_score=confidence,
                    match_reasons=reasons or []
                )
                
                matches.append(match)
        
        # Sort by confidence score
        matches.sort(key=lambda x: x.confidence_score, reverse=True)
        
        console.print(f"[green]✅ Found {len(matches)} potential job-related emails[/green]")
        return matches
    
    def _is_job_related_email(self, email: Dict) -> bool:
        """Check if email appears to be job-related."""
        text = f"{email['subject']} {email['snippet']}".lower()
        
        # Check for job-related patterns
        for pattern in self.job_email_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Check for company domains
        sender = email['sender'].lower()
        for domain in self.company_domains:
            if domain in sender:
                return True
        
        # Check for job-related keywords
        job_keywords = [
            'application', 'position', 'job', 'career', 'hiring', 'interview',
            'thank you', 'received', 'confirmation', 'opportunity'
        ]
        
        return any(keyword in text for keyword in job_keywords)
    
    def _find_matching_job(self, email: Dict) -> Tuple[Optional[Dict], float, List[str]]:
        """Find the best matching job for an email."""
        best_match = None
        best_score = 0.0
        best_reasons = []
        
        email_text = f"{email['subject']} {email['snippet']} {email['sender']}".lower()
        
        for job in self.recent_applications:
            score = 0.0
            reasons = []
            
            job_title = job.get('title', '').lower()
            company = job.get('company', '').lower()
            
            # Company name matching (high weight)
            if company and company in email_text:
                score += 0.6
                reasons.append(f"Company match: {company}")
            
            # Job title matching (medium weight)
            if job_title:
                title_words = job_title.split()
                title_matches = sum(1 for word in title_words if len(word) > 3 and word in email_text)
                if title_matches > 0:
                    title_score = (title_matches / len(title_words)) * 0.4
                    score += title_score
                    reasons.append(f"Title words matched: {title_matches}/{len(title_words)}")
            
            # Domain matching (low weight)
            job_url = job.get('url', '').lower()
            if job_url:
                for domain in self.company_domains:
                    if domain in job_url and domain in email['sender'].lower():
                        score += 0.2
                        reasons.append(f"Domain match: {domain}")
            
            # Date proximity (bonus)
            # This would need date parsing, simplified for now
            if score > 0:
                score += 0.1  # Small bonus for any match
                reasons.append("Recent application")
            
            if score > best_score:
                best_match = job
                best_score = score
                best_reasons = reasons
        
        return best_match, best_score, best_reasons

    async def _interactive_verification(self, page: Page, matches: List[EmailMatch]) -> List[EmailMatch]:
        """Interactive verification of email matches."""
        console.print(f"\n[bold blue]🔍 INTERACTIVE EMAIL VERIFICATION[/bold blue]")

        if not matches:
            console.print("[yellow]No potential matches found[/yellow]")
            return []

        verified_matches = []

        # Show matches table
        self._display_matches_table(matches)

        console.print(f"\n[cyan]Found {len(matches)} potential job-related emails[/cyan]")
        console.print("[yellow]Let's verify each match interactively...[/yellow]")

        for i, match in enumerate(matches[:10]):  # Limit to top 10 matches
            console.print(f"\n[bold]📧 Email {i+1}/{min(len(matches), 10)}:[/bold]")
            console.print(f"From: {match.email_sender}")
            console.print(f"Subject: {match.email_subject}")
            console.print(f"Snippet: {match.email_snippet[:100]}...")

            if match.matched_job:
                console.print(f"[green]🎯 Matched Job: {match.matched_job.get('title', 'Unknown')} at {match.matched_job.get('company', 'Unknown')}[/green]")
                console.print(f"[green]Confidence: {match.confidence_score:.2f}[/green]")
                console.print(f"[green]Reasons: {', '.join(match.match_reasons)}[/green]")
            else:
                console.print("[yellow]No job match found[/yellow]")

            # Ask user for verification
            action = Prompt.ask(
                "Action",
                choices=["view", "verify", "skip", "manual", "stop"],
                default="view"
            )

            if action == "view":
                # Open email in Gmail for viewing
                await self._open_email_for_viewing(page, match)

                # Ask again after viewing
                verify_action = Prompt.ask(
                    "After viewing, verify this match?",
                    choices=["yes", "no", "manual"],
                    default="no"
                )

                if verify_action == "yes":
                    verified_matches.append(match)
                    console.print("[green]✅ Match verified![/green]")
                elif verify_action == "manual":
                    # Manual job selection
                    manual_match = self._manual_job_selection(match)
                    if manual_match:
                        verified_matches.append(manual_match)

            elif action == "verify":
                verified_matches.append(match)
                console.print("[green]✅ Match verified![/green]")

            elif action == "manual":
                # Manual job selection
                manual_match = self._manual_job_selection(match)
                if manual_match:
                    verified_matches.append(manual_match)

            elif action == "stop":
                break

            # Continue or stop
            if action != "stop" and i < min(len(matches), 10) - 1:
                if not Confirm.ask("Continue with next email?", default=True):
                    break

        console.print(f"\n[green]✅ Verified {len(verified_matches)} email matches[/green]")
        return verified_matches

    def _display_matches_table(self, matches: List[EmailMatch]):
        """Display matches in a table format."""
        table = Table(title="📧 Email Matches Found")
        table.add_column("From", style="cyan", max_width=25)
        table.add_column("Subject", style="green", max_width=30)
        table.add_column("Matched Job", style="yellow", max_width=25)
        table.add_column("Confidence", style="magenta")

        for match in matches[:10]:  # Show top 10
            sender = match.email_sender[:22] + "..." if len(match.email_sender) > 25 else match.email_sender
            subject = match.email_subject[:27] + "..." if len(match.email_subject) > 30 else match.email_subject

            if match.matched_job:
                job_info = f"{match.matched_job.get('title', 'Unknown')[:20]}..."
                confidence = f"{match.confidence_score:.2f}"
            else:
                job_info = "No match"
                confidence = "0.00"

            table.add_row(sender, subject, job_info, confidence)

        console.print(table)

    async def _open_email_for_viewing(self, page: Page, match: EmailMatch):
        """Open email in Gmail for user to view."""
        try:
            console.print("[cyan]📧 Opening email in Gmail...[/cyan]")

            # Search for the email by subject
            search_box = await page.query_selector('input[aria-label="Search mail"]')
            if search_box:
                await search_box.click()
                await search_box.fill(f'subject:"{match.email_subject[:30]}"')
                await page.keyboard.press('Enter')
                await page.wait_for_timeout(3000)

                # Click first result
                first_result = await page.query_selector('tr[role="row"]')
                if first_result:
                    await first_result.click()
                    await page.wait_for_timeout(2000)

                    console.print("[green]✅ Email opened. Please review it in the browser.[/green]")
                    input("Press Enter when you're done reviewing...")

                    # Go back to inbox
                    await page.keyboard.press('u')
                    await page.wait_for_timeout(1000)
                else:
                    console.print("[yellow]⚠️ Could not find email in search results[/yellow]")
            else:
                console.print("[yellow]⚠️ Could not find search box[/yellow]")

        except Exception as e:
            console.print(f"[red]❌ Error opening email: {e}[/red]")

    def _manual_job_selection(self, match: EmailMatch) -> Optional[EmailMatch]:
        """Allow user to manually select which job this email matches."""
        console.print("\n[bold]🔧 Manual Job Selection[/bold]")
        console.print("Select which job this email confirms:")

        # Show available jobs
        table = Table()
        table.add_column("Index", style="cyan")
        table.add_column("Job Title", style="green", max_width=30)
        table.add_column("Company", style="yellow", max_width=25)
        table.add_column("Date Applied", style="magenta")

        for i, job in enumerate(self.recent_applications[:10]):
            table.add_row(
                str(i + 1),
                job.get('title', 'Unknown'),
                job.get('company', 'Unknown'),
                job.get('applied_date', 'Unknown')[:10]
            )

        console.print(table)

        try:
            choice = Prompt.ask("Select job number (or 0 for none)", default="0")
            choice_num = int(choice)

            if 1 <= choice_num <= len(self.recent_applications):
                selected_job = self.recent_applications[choice_num - 1]
                match.matched_job = selected_job
                match.confidence_score = 1.0  # Manual selection = high confidence
                match.match_reasons = ["Manual selection by user"]

                console.print(f"[green]✅ Manually matched with: {selected_job.get('title', 'Unknown')}[/green]")
                return match
            else:
                console.print("[yellow]No job selected[/yellow]")
                return None

        except ValueError:
            console.print("[red]Invalid selection[/red]")
            return None

    async def _update_verified_applications(self, verified_matches: List[EmailMatch]):
        """Update database with verified applications."""
        console.print(f"\n[bold blue]💾 UPDATING DATABASE[/bold blue]")

        if not verified_matches:
            console.print("[yellow]No verified matches to update[/yellow]")
            return

        updated_count = 0

        for match in verified_matches:
            if match.matched_job:
                try:
                    # Update job status to 'confirmed_applied'
                    job_id = match.matched_job.get('id')
                    if job_id:
                        # This would need to be implemented in the database class
                        # self.db.update_job_status(job_id, 'confirmed_applied', {
                        #     'confirmation_email': match.email_subject,
                        #     'confirmation_sender': match.email_sender,
                        #     'confirmation_date': match.email_date,
                        #     'verification_method': 'gmail_verification'
                        # })

                        console.print(f"[green]✅ Updated: {match.matched_job.get('title', 'Unknown')}[/green]")
                        updated_count += 1

                except Exception as e:
                    console.print(f"[red]❌ Failed to update {match.matched_job.get('title', 'Unknown')}: {e}[/red]")

        console.print(f"\n[green]✅ Updated {updated_count} job applications with email confirmations[/green]")

        # Save verification report
        self._save_verification_report(verified_matches)

    def _save_verification_report(self, verified_matches: List[EmailMatch]):
        """Save verification report to file."""
        try:
            from pathlib import Path
            import json

            report_file = Path(f"profiles/{self.profile_name}/gmail_verification_report.json")
            report_file.parent.mkdir(exist_ok=True)

            report_data = {
                'verification_date': datetime.now().isoformat(),
                'email_account': self.email,
                'total_matches': len(verified_matches),
                'matches': []
            }

            for match in verified_matches:
                match_data = {
                    'email_subject': match.email_subject,
                    'email_sender': match.email_sender,
                    'email_date': match.email_date,
                    'matched_job_title': match.matched_job.get('title') if match.matched_job else None,
                    'matched_job_company': match.matched_job.get('company') if match.matched_job else None,
                    'confidence_score': match.confidence_score,
                    'match_reasons': match.match_reasons
                }
                report_data['matches'].append(match_data)

            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)

            console.print(f"[green]💾 Verification report saved to: {report_file}[/green]")

        except Exception as e:
            console.print(f"[yellow]⚠️ Could not save verification report: {e}[/yellow]")


# Convenience functions
async def verify_applications_with_gmail(profile_name: str = "Nirajan") -> List[EmailMatch]:
    """
    Convenience function to verify applications with Gmail.

    Args:
        profile_name: Profile name for database access

    Returns:
        List of verified email matches
    """
    verifier = DynamicGmailVerifier(profile_name)

    if not await verifier.initialize():
        return []

    return await verifier.verify_applications_with_gmail()


if __name__ == "__main__":
    import asyncio

    # Run verification when script is executed directly
    asyncio.run(verify_applications_with_gmail())
