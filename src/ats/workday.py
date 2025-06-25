from typing import Dict

from playwright.sync_api import Page
from rich.console import Console

from .base_submitter import BaseSubmitter
from .workday_login import WorkdayLogin
from .workday_form_filler import WorkdayFormFiller
import utils

console = Console()

class WorkdaySubmitter(BaseSubmitter):
    """
    Submitter for Workday ATS.
    Handles automation of job applications on Workday-based portals.
    """
    
    def submit(self, job: Dict, profile: Dict, resume_path: str, cover_letter_path: str) -> str:
        page = self.ctx.new_page()
        try:
            console.print(f"[green]Navigating to job URL: {job['url']}[/green]")
            page.goto(job["url"], timeout=30000)
            self.wait_for_navigation(page)
            self.check_for_captcha(page)

            login_handler = WorkdayLogin(page)
            if not login_handler.handle_login(profile, job["url"]):
                console.print("[yellow]Manual login may be required[/yellow]")

            page.wait_for_timeout(3000)

            if not self._click_apply_button_enhanced(page):
                console.print("[yellow]Could not find Apply button[/yellow]")
                return "Manual"

            form_filler = WorkdayFormFiller(page, profile, resume_path, cover_letter_path)
            return form_filler.fill_form()
            
        except utils.NeedsHumanException:
            console.print("[yellow]Human intervention required[/yellow]")
            self.wait_for_human(page, "Please complete the application manually")
            return "Manual"
        
        except Exception as e:
            console.print(f"[bold red]Workday submission error: {e}[/bold red]")
            return "Failed"
        
        finally:
            page.close()

    def _click_apply_button_enhanced(self, page: Page) -> bool:
        """Enhanced Apply button detection and clicking."""
        apply_selectors = [
            "button:has-text('Apply')", "a:has-text('Apply')",
            "button:has-text('Apply Now')", "a:has-text('Apply Now')",
            "[data-automation-id*='apply']"
        ]
        for selector in apply_selectors:
            try:
                if page.is_visible(selector):
                    page.click(selector)
                    page.wait_for_timeout(3000)
                    return True
            except Exception:
                continue
        return False
