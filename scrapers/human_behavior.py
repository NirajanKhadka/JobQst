"""
Human-like behavior module for web scraping.
Implements slower, human-mimicking approaches with proper delays, cookie handling, and tab management.
Based on user memories for click-and-popup job scraping.
"""

import time
import random
import json
from typing import Dict, Tuple, Optional, List, Any
from playwright.sync_api import Page, BrowserContext
from rich.console import Console

console = Console()


class HumanBehaviorConfig:
    """Configuration for human-like behavior patterns."""
    
    def __init__(self, **kwargs):
        # Enhanced human-like behavior settings as per memories
        self.delays = {
            "page_load": kwargs.get("page_load", (2.0, 4.0)),      # Wait after page loads
            "between_jobs": kwargs.get("between_jobs", (1.0, 2.0)), # 1-second delays as per memories
            "between_pages": kwargs.get("between_pages", (2.0, 4.0)), # Wait between pages
            "popup_wait": kwargs.get("popup_wait", 3.0),           # Fixed 3-second wait for popups
            "pre_click": kwargs.get("pre_click", (0.2, 0.5)),      # Wait before clicking
            "post_hover": kwargs.get("post_hover", (0.1, 0.3)),    # Wait after hovering
            "keyword_switch": kwargs.get("keyword_switch", (2.0, 4.0)), # Wait between keywords
            "context_startup": kwargs.get("context_startup", (3.0, 5.0)), # Wait between browser contexts
            "tab_handling": kwargs.get("tab_handling", (0.5, 1.0)), # Wait for tab operations
        }
        
        # Cookie-based approach settings
        self.cookie_settings = {
            "save_cookies": kwargs.get("save_cookies", True),
            "cookie_file": kwargs.get("cookie_file", "scrapers/cookies.json"),
            "session_persistence": kwargs.get("session_persistence", True)
        }
        
        # Tab handling settings for job links that open in new tabs
        self.tab_settings = {
            "max_open_tabs": kwargs.get("max_open_tabs", 3),
            "close_tabs_immediately": kwargs.get("close_tabs_immediately", True),
            "handle_popup_tabs": kwargs.get("handle_popup_tabs", True)
        }


class HumanBehaviorMixin:
    """
    Mixin class to add human-like behavior to scrapers.
    Implements slower, human-mimicking approaches as per user memories.
    """
    
    def __init__(self, *args, **kwargs):
        try:
            super().__init__(*args, **kwargs)
        except TypeError:
            pass
        self.human_config = HumanBehaviorConfig(**kwargs)
        self.open_tabs: List[Page] = []
        self.cookies_loaded = False
        self.click_popup_framework = UniversalClickPopupFramework(getattr(self, 'site_name', 'generic'))
        
    def human_delay(self, delay_type: str, custom_range: Optional[Tuple[float, float]] = None) -> float:
        """
        Apply human-like delay with randomization.
        
        Args:
            delay_type: Type of delay from config
            custom_range: Optional custom delay range
            
        Returns:
            Actual delay applied
        """
        if custom_range:
            delay = random.uniform(*custom_range)
        elif delay_type in self.human_config.delays:
            delay_config = self.human_config.delays[delay_type]
            if isinstance(delay_config, tuple):
                delay = random.uniform(*delay_config)
            else:
                delay = delay_config
        else:
            delay = random.uniform(1.0, 2.0)  # Default delay
            
        console.print(f"[yellow]⏳ Human-like {delay_type} delay: {delay:.1f}s[/yellow]")
        time.sleep(delay)
        return delay
    
    def human_click_with_popup(self, element, page: Page, job_id: str = "unknown") -> Optional[str]:
        """
        Enhanced click-and-popup method with 3-second wait as per memories.
        
        Args:
            element: Element to click
            page: Page object
            job_id: Job identifier for logging
            
        Returns:
            URL from popup or None
        """
        try:
            console.print(f"[cyan]🖱️ Human-like clicking for job {job_id}...[/cyan]")
            
            # Add human-like pre-click behavior
            try:
                # Scroll element into view if needed
                element.scroll_into_view_if_needed()
                self.human_delay("pre_click")
                
                # Hover before clicking (human-like)
                element.hover()
                self.human_delay("post_hover")
            except Exception as e:
                console.print(f"[yellow]⚠️ Pre-click behavior failed: {e}[/yellow]")
            
            # Enhanced expect_popup method with 3-second wait as requested
            with page.expect_popup(timeout=8000) as popup_info:
                element.click()
                # KEY: Fixed 3-second wait as specified in memories
                console.print(f"[yellow]⏳ Waiting {self.human_config.delays['popup_wait']} seconds for popup to fully load (as per memories)...[/yellow]")
                time.sleep(self.human_config.delays["popup_wait"])
            
            popup = popup_info.value
            popup_url = popup.url
            
            # Enhanced popup handling with validation
            if popup_url and "eluta.ca" not in popup_url:
                console.print(f"[green]✅ Got external ATS URL: {popup_url[:60]}...[/green]")
            else:
                console.print(f"[cyan]📋 Got job URL: {popup_url[:60]}...[/cyan]")
            
            # Handle tab management
            self._handle_popup_tab(popup, job_id)
            
            return popup_url
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Human click-and-popup failed for job {job_id}: {e}[/yellow]")
            return None
    
    def _handle_popup_tab(self, popup: Page, job_id: str):
        """Handle popup tab according to user preferences."""
        try:
            if self.human_config.tab_settings["close_tabs_immediately"]:
                # Close popup immediately as per current implementation
                popup.close()
                console.print(f"[cyan]🗙 Closed popup tab for job {job_id}[/cyan]")
            else:
                # Keep track of open tabs
                self.open_tabs.append(popup)
                console.print(f"[cyan]📑 Keeping popup tab open for job {job_id}[/cyan]")
                
                # Close oldest tabs if too many are open
                if len(self.open_tabs) > self.human_config.tab_settings["max_open_tabs"]:
                    oldest_tab = self.open_tabs.pop(0)
                    try:
                        oldest_tab.close()
                        console.print(f"[cyan]🗙 Closed oldest tab to manage tab count[/cyan]")
                    except:
                        pass
                        
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not handle popup tab: {e}[/yellow]")
    
    def save_cookies(self, context: BrowserContext):
        """Save cookies for session persistence (cookie-based approach)."""
        if not self.human_config.cookie_settings["save_cookies"]:
            return
            
        try:
            cookies = context.cookies()
            cookie_file = self.human_config.cookie_settings["cookie_file"]
            
            with open(cookie_file, 'w') as f:
                json.dump(cookies, f, indent=2)
                
            console.print(f"[green]🍪 Saved {len(cookies)} cookies to {cookie_file}[/green]")
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not save cookies: {e}[/yellow]")
    
    def load_cookies(self, context: BrowserContext):
        """Load cookies for session persistence (cookie-based approach)."""
        if not self.human_config.cookie_settings["save_cookies"] or self.cookies_loaded:
            return
            
        try:
            cookie_file = self.human_config.cookie_settings["cookie_file"]
            
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
                
            context.add_cookies(cookies)
            self.cookies_loaded = True
            console.print(f"[green]🍪 Loaded {len(cookies)} cookies from {cookie_file}[/green]")
            
        except FileNotFoundError:
            console.print(f"[yellow]🍪 No cookie file found - starting fresh session[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not load cookies: {e}[/yellow]")
    
    def cleanup_tabs(self):
        """Clean up any remaining open tabs."""
        for tab in self.open_tabs:
            try:
                tab.close()
            except:
                pass
        self.open_tabs.clear()
        console.print(f"[cyan]🗙 Cleaned up all open tabs[/cyan]")
    
    def human_page_navigation(self, page: Page, url: str, wait_for_load: bool = True):
        """
        Navigate to page with human-like behavior.
        
        Args:
            page: Page object
            url: URL to navigate to
            wait_for_load: Whether to wait for page load
        """
        try:
            console.print(f"[cyan]🌐 Navigating to: {url[:60]}...[/cyan]")
            
            page.goto(url, timeout=30000)
            
            if wait_for_load:
                page.wait_for_load_state("domcontentloaded")
                self.human_delay("page_load")
                
        except Exception as e:
            console.print(f"[red]❌ Navigation failed: {e}[/red]")
            raise
    
    def human_scroll_and_wait(self, page: Page, element=None):
        """Scroll to element and wait (human-like behavior)."""
        try:
            if element:
                element.scroll_into_view_if_needed()
            else:
                # Random scroll
                page.evaluate("window.scrollBy(0, Math.random() * 500)")
                
            self.human_delay("pre_click")
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Scroll behavior failed: {e}[/yellow]")


class UniversalClickPopupFramework:
    """
    Universal click-and-popup framework for different job sites.
    Maintains site-specific optimizations while providing consistent interface.
    """

    def __init__(self, site_name: str = "generic"):
        self.site_name = site_name.lower()
        self.site_configs = self._get_site_configs()
        self.current_config = self.site_configs.get(self.site_name, self.site_configs["generic"])

    def _get_site_configs(self) -> Dict:
        """Get site-specific configurations for click-and-popup behavior."""
        return {
            "eluta": {
                "job_selector": ".organic-job",
                "link_selector": "a",
                "link_text_min_length": 10,
                "popup_timeout": 8000,
                "popup_wait": 3.0,
                "link_validation": lambda href: "/job/" in href or "/direct/" in href,
                "job_keywords": ["analyst", "developer", "engineer", "manager", "specialist"],
                "external_url_check": lambda url: "eluta.ca" not in url
            },
            "indeed": {
                "job_selector": "[data-jk]",
                "link_selector": "h2 a",
                "link_text_min_length": 5,
                "popup_timeout": 10000,
                "popup_wait": 2.0,
                "link_validation": lambda href: "/viewjob" in href,
                "job_keywords": ["analyst", "developer", "engineer", "manager"],
                "external_url_check": lambda url: "indeed.ca" not in url and "indeed.com" not in url
            },
            "jobbank": {
                "job_selector": ".job-posting",
                "link_selector": "a.job-title",
                "link_text_min_length": 8,
                "popup_timeout": 6000,
                "popup_wait": 2.5,
                "link_validation": lambda href: "/job/" in href,
                "job_keywords": ["analyst", "developer", "engineer", "manager"],
                "external_url_check": lambda url: "jobbank.gc.ca" not in url
            },
            "linkedin": {
                "job_selector": ".job-search-card",
                "link_selector": ".job-search-card__title a",
                "link_text_min_length": 6,
                "popup_timeout": 12000,
                "popup_wait": 3.5,
                "link_validation": lambda href: "/jobs/view/" in href,
                "job_keywords": ["analyst", "developer", "engineer", "manager"],
                "external_url_check": lambda url: "linkedin.com" not in url
            },
            "monster": {
                "job_selector": ".job-card",
                "link_selector": ".job-title a",
                "link_text_min_length": 7,
                "popup_timeout": 8000,
                "popup_wait": 2.0,
                "link_validation": lambda href: "/job/" in href,
                "job_keywords": ["analyst", "developer", "engineer", "manager"],
                "external_url_check": lambda url: "monster.ca" not in url
            },
            "generic": {
                "job_selector": ".job",
                "link_selector": "a",
                "link_text_min_length": 5,
                "popup_timeout": 8000,
                "popup_wait": 3.0,
                "link_validation": lambda href: True,
                "job_keywords": ["analyst", "developer", "engineer", "manager"],
                "external_url_check": lambda url: True
            }
        }

    def find_job_elements(self, page: Page) -> List:
        """Find job elements using site-specific selector."""
        try:
            selector = self.current_config["job_selector"]
            elements = page.query_selector_all(selector)
            console.print(f"[cyan]🔍 Found {len(elements)} job elements using {self.site_name} selector: {selector}[/cyan]")
            return elements
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not find job elements for {self.site_name}: {e}[/yellow]")
            return []

    def find_best_job_link(self, job_element) -> Optional[Any]:
        """Find the best job link within a job element using site-specific logic."""
        try:
            config = self.current_config
            links = job_element.query_selector_all(config["link_selector"])

            best_link = None
            best_score = 0

            for link in links:
                score = self._score_job_link(link, config)
                if score > best_score:
                    best_score = score
                    best_link = link

            if best_link:
                link_text = best_link.inner_text().strip()[:50]
                console.print(f"[green]✅ Selected best link (score: {best_score}): {link_text}...[/green]")

            return best_link

        except Exception as e:
            console.print(f"[yellow]⚠️ Could not find job link: {e}[/yellow]")
            return None

    def _score_job_link(self, link, config: Dict) -> int:
        """Score a job link based on site-specific criteria."""
        score = 0

        try:
            link_text = link.inner_text().strip()
            href = link.get_attribute("href") or ""

            # Text length check
            if len(link_text) >= config["link_text_min_length"]:
                score += 10

            # Href validation
            if config["link_validation"](href):
                score += 20

            # Job keyword check
            text_lower = link_text.lower()
            for keyword in config["job_keywords"]:
                if keyword in text_lower:
                    score += 5
                    break

            # Prefer longer, more descriptive text
            if len(link_text) > 20:
                score += 5

            # Avoid navigation links
            nav_keywords = ["next", "previous", "page", "more", "view all"]
            if any(nav in text_lower for nav in nav_keywords):
                score -= 10

        except Exception:
            score = 0

        return score

    def execute_click_popup(self, link_element, page: Page, job_id: str, human_behavior=None) -> Optional[str]:
        """Execute click-and-popup with site-specific optimizations."""
        try:
            config = self.current_config
            console.print(f"[cyan]🖱️ Executing {self.site_name} click-and-popup for job {job_id}...[/cyan]")

            # Pre-click behavior (human-like if available)
            if human_behavior:
                human_behavior.human_scroll_and_wait(page, link_element)
            else:
                try:
                    link_element.scroll_into_view_if_needed()
                    time.sleep(0.3)
                    link_element.hover()
                    time.sleep(0.2)
                except:
                    pass

            # Execute click with popup expectation
            with page.expect_popup(timeout=config["popup_timeout"]) as popup_info:
                link_element.click()
                console.print(f"[yellow]⏳ Waiting {config['popup_wait']}s for {self.site_name} popup...[/yellow]")
                time.sleep(config["popup_wait"])

            popup = popup_info.value
            popup_url = popup.url

            # Validate popup URL
            if config["external_url_check"](popup_url):
                console.print(f"[green]✅ Got external URL: {popup_url[:60]}...[/green]")
            else:
                console.print(f"[cyan]📋 Got {self.site_name} URL: {popup_url[:60]}...[/cyan]")

            # Close popup
            try:
                popup.close()
                console.print(f"[cyan]🗙 Closed {self.site_name} popup for job {job_id}[/cyan]")
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not close popup: {e}[/yellow]")

            return popup_url

        except Exception as e:
            console.print(f"[yellow]⚠️ {self.site_name} click-and-popup failed for job {job_id}: {e}[/yellow]")
            return None


class HumanLikeJobScraper(HumanBehaviorMixin):
    """
    Base class for human-like job scrapers.
    Combines human behavior with job scraping functionality.
    """

    def __init__(self, profile: Dict, **kwargs):
        super().__init__(profile, **kwargs)

        # Initialize universal click-popup framework
        site_name = getattr(self, 'site_name', 'generic')
        self.click_popup_framework = UniversalClickPopupFramework(site_name)

        console.print(f"[green]✅ Human-like behavior enabled with 1-second delays and 3-second popup waits[/green]")
        console.print(f"[cyan]🍪 Cookie-based session persistence: {self.human_config.cookie_settings['save_cookies']}[/cyan]")
        console.print(f"[cyan]📑 Tab handling: {self.human_config.tab_settings['close_tabs_immediately']}[/cyan]")
        console.print(f"[cyan]🎯 Universal click-popup framework: {site_name}[/cyan]")

    def universal_extract_job_url(self, job_element, page: Page, job_id: str) -> Optional[str]:
        """
        Universal method to extract job URL using click-and-popup.
        Works across different job sites with site-specific optimizations.
        """
        try:
            # Find the best job link using site-specific logic
            job_link = self.click_popup_framework.find_best_job_link(job_element)

            if not job_link:
                console.print(f"[yellow]⚠️ No suitable job link found for job {job_id}[/yellow]")
                return None

            # Execute click-and-popup with human behavior
            popup_url = self.click_popup_framework.execute_click_popup(
                job_link, page, job_id, human_behavior=self
            )

            return popup_url

        except Exception as e:
            console.print(f"[red]❌ Universal job URL extraction failed for job {job_id}: {e}[/red]")
            return None
