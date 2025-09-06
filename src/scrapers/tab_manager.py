"""
TabManager for Playwright-based Scrapers

Handles:
- Clicking job links
- Waiting for new tab/popups
- Extracting the real job URL
- Closing tabs safely
"""

from playwright.sync_api import Page, ElementHandle, TimeoutError as PlaywrightTimeoutError
from typing import Optional
from rich.console import Console
import time

console = Console()


class TabManager:
    """Manages tab opening and URL extraction for job scrapers."""

    def __init__(self, popup_wait: float = 3.0):
        self.popup_wait = popup_wait  # seconds to wait for popup/tab

    def click_and_get_popup_url(
        self, link: ElementHandle, page: Page, job_number: str = ""
    ) -> Optional[str]:
        """
        Clicks a link, waits for a popup/tab, extracts the URL, and closes the tab.
        Returns the real job URL or None if failed.
        """
        try:
            with page.expect_popup() as popup_info:
                link.click(force=True)
                console.print(
                    f"[cyan]🖱️ Clicked job link (job {job_number}), waiting for popup...[/cyan]"
                )
            popup = popup_info.value
            time.sleep(self.popup_wait)  # Wait for the tab to load
            real_url = popup.url
            console.print(f"[green]✅ Popup/tab opened: {real_url[:60]}...[/green]")
            popup.close()
            return real_url
        except PlaywrightTimeoutError:
            console.print(f"[yellow]⚠️ Popup/tab did not open in time for job {job_number}[/yellow]")
            return None
        except Exception as e:
            console.print(
                f"[yellow]⚠️ Error during popup/tab handling for job {job_number}: {e}[/yellow]"
            )
            return None

