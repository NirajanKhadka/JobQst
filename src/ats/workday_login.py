from typing import Dict
from playwright.sync_api import Page
from rich.console import Console

console = Console()


class WorkdayLogin:
    def __init__(self, page: Page):
        self.page = page

    def handle_login(self, profile: Dict, job_url: str) -> bool:
        try:
            login_indicators = ["text='Sign In'", "input[type='email']", "input[type='password']"]
            needs_login = any(self.page.is_visible(selector) for selector in login_indicators)

            if not needs_login:
                console.print("[green]Already logged in or no login required[/green]")
                return True

            console.print("[yellow]Login required detected[/yellow]")
            return self._auto_fill_login(job_url)

        except Exception as e:
            console.print(f"[red]Error in login handling: {e}[/red]")
            return False

    def _auto_fill_login(self, job_url: str) -> bool:
        try:
            console.print("[cyan]Auto-filling login credentials...[/cyan]")
            domain = self._extract_domain_for_password(job_url)
            default_email = "Nirajan.tech@gmail.com"
            default_password = f"pwd@{domain}99"

            self.page.fill("input[type='email']", default_email)
            self.page.fill("input[type='password']", default_password)

            self.page.click("button:has-text('Sign In')")
            self.page.wait_for_timeout(5000)

            return self._check_login_success()

        except Exception as e:
            console.print(f"[red]Error in auto-fill login: {e}[/red]")
            return self._manual_login()

    def _extract_domain_for_password(self, url: str) -> str:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = parsed.netloc.split(".")[0]
        return domain.capitalize()

    def _manual_login(self) -> bool:
        console.print("[yellow]Please complete the login manually...[/yellow]")
        input("Press Enter to continue...")
        return self._check_login_success()

    def _check_login_success(self) -> bool:
        success_indicators = ["text='Apply'", "text='My Applications'"]
        self.page.wait_for_timeout(3000)
        return any(self.page.is_visible(indicator) for indicator in success_indicators)
