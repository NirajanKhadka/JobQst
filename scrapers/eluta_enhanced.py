#!/usr/bin/env python3
"""
Enhanced Eluta Scraper with keyword-by-keyword search and date filtering
"""

import re
import time
import random
import urllib.parse
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Generator, List, Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from rich.console import Console

from .base_scraper import BaseJobScraper

console = Console()


class ElutaEnhancedScraper(BaseJobScraper):
    """
    Enhanced Eluta scraper that searches keywords one by one and filters by date.
    """
    
    def __init__(self, profile: Dict, **kwargs):
        # Extract comprehensive_mode before passing to parent
        self.comprehensive_mode = kwargs.pop('comprehensive_mode', False)

        # Extract deep_scraping mode for detailed job extraction
        self.deep_scraping = kwargs.pop('deep_scraping', True)  # Default to True for better data

        # Initialize base scraper with profile (without comprehensive_mode)
        super().__init__(profile, **kwargs)

        # Store individual keywords for one-by-one searching
        self.keywords = profile.get("keywords", [])

        self.site_name = "eluta_enhanced"
        self.base_url = "https://www.eluta.ca/search"
        self.requires_browser = True

        # Enhanced human-like delays with more randomization
        self.rate_limit_delay = (5, 15)  # Much slower, more human-like delays
        self.page_delay = (3, 8)  # Longer delay between pages
        self.search_delay = (2, 6)  # Longer delay between searches
        self.click_delay = (1, 4)  # Delay between clicks
        self.typing_delay = (0.1, 0.3)  # Delay between keystrokes

        # Date filtering - last 7 days
        self.max_age_days = 7
        self.cutoff_date = datetime.now() - timedelta(days=self.max_age_days)

        # Enhanced bot detection handling
        self.captcha_detected = False
        self.verification_needed = False
        self.session_cookies = []
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

        # Comprehensive scraping mode settings
        if self.comprehensive_mode:
            self.max_pages_per_keyword = 15  # More pages in comprehensive mode
            self.delay_between_pages = (2, 4)   # Longer delays to avoid detection
            self.delay_between_keywords = (3, 6)
            self.max_age_days = 14  # Look back further in comprehensive mode
        else:
            self.max_pages_per_keyword = 9   # Standard mode
            self.delay_between_pages = (1, 3)
            self.delay_between_keywords = (2, 4)

        # Session tracking
        self.session_stats = {
            'keywords_processed': 0,
            'pages_scraped': 0,
            'jobs_found': 0,
            'duplicates_skipped': 0,
            'errors_encountered': 0,
            'start_time': None,
            'end_time': None
        }

        console.print(f"[green]✅ Enhanced Eluta scraper initialized[/green]")
        console.print(f"[cyan]📅 Filtering jobs from last {self.max_age_days} days[/cyan]")
        console.print(f"[cyan]🔍 Will search {len(self.keywords)} keywords individually[/cyan]")
        if self.comprehensive_mode:
            console.print(f"[bold yellow]🚀 COMPREHENSIVE MODE: Up to {self.max_pages_per_keyword} pages per keyword[/bold yellow]")
    
    def scrape_jobs(self) -> Generator[Dict, None, None]:
        """
        Scrape jobs by searching each keyword individually with comprehensive mode support.
        """
        if not self.browser_context:
            console.print("[red]❌ Browser context required for Eluta Enhanced scraper[/red]")
            return

        # Initialize session tracking
        self.session_stats['start_time'] = datetime.now()
        console.print(f"\n[bold green]🚀 Starting {'COMPREHENSIVE' if self.comprehensive_mode else 'STANDARD'} Eluta scraping session[/bold green]")
        console.print(f"[cyan]📊 Target: {len(self.keywords)} keywords × up to {self.max_pages_per_keyword} pages each[/cyan]")

        page = self.browser_context.new_page()

        # Setup human-like browser behavior
        self._setup_human_like_browser(page)

        # Try to load previous session state
        session_restored = self._load_session_state()
        if session_restored:
            console.print("[green]✅ Previous session restored[/green]")
        else:
            # Start with homepage for natural behavior
            if not self._start_with_homepage(page):
                console.print("[yellow]⚠️ Homepage session failed, continuing anyway[/yellow]")

        try:
            # Search each keyword individually
            for keyword_index, keyword in enumerate(self.keywords, 1):
                console.print(f"\n[bold blue]🔍 Keyword {keyword_index}/{len(self.keywords)}: '{keyword}'[/bold blue]")

                # Check for bot detection before each keyword
                if self._check_for_bot_detection(page):
                    console.print("[yellow]🤖 Bot detection triggered, switching to manual mode[/yellow]")
                    if not self._handle_verification(page):
                        console.print("[red]❌ Could not resolve verification, stopping scraping[/red]")
                        break

                # Search this keyword through all pages
                keyword_jobs = 0
                for job in self._search_keyword(page, keyword):
                    keyword_jobs += 1
                    self.session_stats['jobs_found'] += 1
                    yield job

                self.session_stats['keywords_processed'] += 1
                console.print(f"[green]✅ Keyword '{keyword}' complete: {keyword_jobs} jobs found[/green]")

                # Progress update
                progress = (keyword_index / len(self.keywords)) * 100
                console.print(f"[bold cyan]📈 Overall Progress: {progress:.1f}% ({keyword_index}/{len(self.keywords)} keywords)[/bold cyan]")

                # Delay between keywords to avoid rate limiting
                if keyword_index < len(self.keywords):
                    delay_range = self.delay_between_keywords
                    delay = random.uniform(delay_range[0], delay_range[1])
                    console.print(f"[cyan]⏳ Waiting {delay:.1f}s before next keyword...[/cyan]")
                    time.sleep(delay)

        finally:
            # Save session state if scraping was successful
            if self.session_stats['jobs_found'] > 0:
                self._save_session_state()

            try:
                page.close()
            except:
                pass  # Ignore close errors

            # Final session summary
            self.session_stats['end_time'] = datetime.now()
            self._print_session_summary()

    def _setup_human_like_browser(self, page: Page) -> None:
        """Setup browser to behave more like a human user with advanced stealth."""
        try:
            # Advanced stealth script to avoid detection
            stealth_script = """
            // Remove webdriver traces completely
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });

            // Override automation detection
            delete navigator.__proto__.webdriver;

            // Mock realistic plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => ({
                    length: 5,
                    0: { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                    1: { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    2: { name: 'Native Client', filename: 'internal-nacl-plugin' },
                    3: { name: 'Chromium PDF Plugin', filename: 'internal-pdf-viewer' },
                    4: { name: 'Microsoft Edge PDF Plugin', filename: 'internal-pdf-viewer' }
                }),
                configurable: true
            });

            // Override languages with realistic values
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'en-CA'],
                configurable: true
            });

            // Add realistic chrome object
            if (!window.chrome) {
                window.chrome = {
                    runtime: {
                        onConnect: null,
                        onMessage: null
                    },
                    app: {
                        isInstalled: false,
                        InstallState: {
                            DISABLED: 'disabled',
                            INSTALLED: 'installed',
                            NOT_INSTALLED: 'not_installed'
                        },
                        RunningState: {
                            CANNOT_RUN: 'cannot_run',
                            READY_TO_RUN: 'ready_to_run',
                            RUNNING: 'running'
                        }
                    },
                    csi: function() {},
                    loadTimes: function() {
                        return {
                            requestTime: Date.now() / 1000 - Math.random() * 2,
                            startLoadTime: Date.now() / 1000 - Math.random() * 1.5,
                            commitLoadTime: Date.now() / 1000 - Math.random() * 1,
                            finishDocumentLoadTime: Date.now() / 1000 - Math.random() * 0.5,
                            finishLoadTime: Date.now() / 1000,
                            firstPaintTime: Date.now() / 1000 - Math.random() * 0.3,
                            firstPaintAfterLoadTime: 0,
                            navigationType: 'Other',
                            wasFetchedViaSpdy: false,
                            wasNpnNegotiated: false,
                            npnNegotiatedProtocol: 'unknown',
                            wasAlternateProtocolAvailable: false,
                            connectionInfo: 'http/1.1'
                        };
                    }
                };
            }

            // Override permissions with realistic responses
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => {
                const permission = parameters.name;
                if (permission === 'notifications') {
                    return Promise.resolve({ state: 'default' });
                } else if (permission === 'geolocation') {
                    return Promise.resolve({ state: 'prompt' });
                } else if (permission === 'camera') {
                    return Promise.resolve({ state: 'prompt' });
                } else if (permission === 'microphone') {
                    return Promise.resolve({ state: 'prompt' });
                }
                return originalQuery ? originalQuery(parameters) : Promise.resolve({ state: 'prompt' });
            };

            // Mock realistic screen properties
            Object.defineProperty(screen, 'availWidth', { get: () => 1366 });
            Object.defineProperty(screen, 'availHeight', { get: () => 728 });
            Object.defineProperty(screen, 'width', { get: () => 1366 });
            Object.defineProperty(screen, 'height', { get: () => 768 });
            Object.defineProperty(screen, 'colorDepth', { get: () => 24 });
            Object.defineProperty(screen, 'pixelDepth', { get: () => 24 });

            // Override Date.prototype.getTimezoneOffset to be consistent
            const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
            Date.prototype.getTimezoneOffset = function() {
                return 300; // EST timezone offset
            };

            // Add realistic battery API
            if (!navigator.getBattery) {
                navigator.getBattery = () => Promise.resolve({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 0.8 + Math.random() * 0.2
                });
            }

            // Mock realistic connection
            if (!navigator.connection) {
                navigator.connection = {
                    effectiveType: '4g',
                    rtt: 50 + Math.random() * 50,
                    downlink: 10 + Math.random() * 5,
                    saveData: false
                };
            }

            // Override toString methods to hide automation
            Function.prototype.toString = new Proxy(Function.prototype.toString, {
                apply: function(target, thisArg, argumentsList) {
                    if (thisArg && thisArg.name && thisArg.name.includes('webdriver')) {
                        return 'function webdriver() { [native code] }';
                    }
                    return target.apply(thisArg, argumentsList);
                }
            });
            """

            page.add_init_script(stealth_script)

            # Set realistic viewport with slight randomization
            viewports = [
                {"width": 1366, "height": 768},
                {"width": 1920, "height": 1080},
                {"width": 1440, "height": 900},
                {"width": 1536, "height": 864}
            ]
            viewport = random.choice(viewports)
            page.set_viewport_size(viewport)

            # Set random user agent
            user_agent = random.choice(self.user_agents)
            page.set_extra_http_headers({
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,en-CA;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0"
            })

            console.print("[green]✅ Advanced stealth browser behavior configured[/green]")
            console.print(f"[cyan]🖥️ Viewport: {viewport['width']}x{viewport['height']}[/cyan]")

        except Exception as e:
            console.print(f"[yellow]⚠️ Could not setup advanced stealth mode: {e}[/yellow]")

    def _human_like_navigation(self, page: Page, url: str) -> bool:
        """Navigate to URL with human-like behavior patterns."""
        try:
            console.print(f"[cyan]🌐 Human-like navigation to: {url}[/cyan]")

            # Random pre-navigation delay
            pre_delay = random.uniform(1, 3)
            console.print(f"[yellow]⏳ Pre-navigation pause: {pre_delay:.1f}s[/yellow]")
            time.sleep(pre_delay)

            # Navigate with timeout
            page.goto(url, timeout=45000, wait_until="domcontentloaded")

            # Human-like post-navigation behavior
            post_delay = random.uniform(2, 5)
            console.print(f"[yellow]⏳ Post-navigation pause: {post_delay:.1f}s[/yellow]")
            time.sleep(post_delay)

            # Simulate human reading behavior - scroll slightly
            try:
                page.evaluate("window.scrollTo(0, Math.random() * 200)")
                time.sleep(random.uniform(0.5, 1.5))
                page.evaluate("window.scrollTo(0, 0)")  # Back to top
                time.sleep(random.uniform(0.3, 0.8))
            except:
                pass

            # Wait for network to be idle
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except:
                console.print("[yellow]⚠️ Network still active, continuing anyway[/yellow]")

            return True

        except Exception as e:
            console.print(f"[red]❌ Navigation failed: {e}[/red]")
            return False

    def _human_like_click(self, page: Page, element) -> bool:
        """Click element with human-like behavior."""
        try:
            # Pre-click delay
            delay = random.uniform(*self.click_delay)
            console.print(f"[yellow]⏳ Pre-click pause: {delay:.1f}s[/yellow]")
            time.sleep(delay)

            # Scroll element into view if needed
            try:
                element.scroll_into_view_if_needed()
                time.sleep(random.uniform(0.2, 0.6))
            except:
                pass

            # Hover before clicking (human-like)
            try:
                element.hover()
                time.sleep(random.uniform(0.1, 0.4))
            except:
                pass

            # Click with human-like timing
            element.click()

            # Post-click delay
            post_delay = random.uniform(0.5, 1.5)
            time.sleep(post_delay)

            return True

        except Exception as e:
            console.print(f"[yellow]⚠️ Click failed: {e}[/yellow]")
            return False

    def _human_like_typing(self, page: Page, selector: str, text: str) -> bool:
        """Type text with human-like delays between keystrokes."""
        try:
            element = page.query_selector(selector)
            if not element:
                return False

            # Clear existing text
            element.click()
            page.keyboard.press("Control+a")
            time.sleep(random.uniform(0.1, 0.3))

            # Type character by character with human-like delays
            for char in text:
                element.type(char)
                delay = random.uniform(*self.typing_delay)
                time.sleep(delay)

            # Final pause after typing
            time.sleep(random.uniform(0.5, 1.2))
            return True

        except Exception as e:
            console.print(f"[yellow]⚠️ Typing failed: {e}[/yellow]")
            return False

    def _simulate_human_reading(self, page: Page) -> None:
        """Simulate human reading behavior with scrolling and pauses."""
        try:
            # Get page height
            page_height = page.evaluate("document.body.scrollHeight")
            viewport_height = page.evaluate("window.innerHeight")

            if page_height <= viewport_height:
                # Page fits in viewport, just pause
                time.sleep(random.uniform(2, 4))
                return

            # Scroll down in human-like chunks
            current_position = 0
            scroll_chunks = random.randint(3, 6)
            chunk_size = page_height // scroll_chunks

            for i in range(scroll_chunks):
                # Scroll to next position
                current_position += chunk_size + random.randint(-50, 50)
                current_position = min(current_position, page_height)

                page.evaluate(f"window.scrollTo(0, {current_position})")

                # Pause to "read"
                reading_time = random.uniform(1, 3)
                time.sleep(reading_time)

                if current_position >= page_height - viewport_height:
                    break

            # Scroll back to top
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            console.print(f"[yellow]⚠️ Reading simulation failed: {e}[/yellow]")

    def _check_for_bot_detection(self, page: Page) -> bool:
        """Check if Eluta has detected bot behavior."""
        try:
            # Common bot detection indicators
            bot_indicators = [
                # CAPTCHA selectors
                ".captcha",
                "#captcha",
                ".g-recaptcha",
                ".h-captcha",
                "iframe[src*='recaptcha']",
                "iframe[src*='hcaptcha']",
                "iframe[src*='captcha']",

                # Verification selectors
                "[data-testid*='verification']",
                ".verification",
                "#verification",

                # Challenge selectors
                ".challenge",
                "#challenge",
                "[data-testid*='challenge']",

                # Cloudflare selectors
                ".cf-browser-verification",
                "#cf-wrapper",
                ".cf-challenge",

                # Generic bot detection
                "[data-testid*='bot']",
                ".bot-detection",
                "#bot-check"
            ]

            for selector in bot_indicators:
                try:
                    if page.is_visible(selector, timeout=1000):
                        console.print(f"[yellow]🤖 Bot detection indicator found: {selector}[/yellow]")
                        return True
                except:
                    continue

            # Check page title for verification messages
            try:
                title = page.title().lower()
                verification_keywords = ['verification', 'captcha', 'challenge', 'bot', 'security']
                if any(keyword in title for keyword in verification_keywords):
                    console.print(f"[yellow]🤖 Bot detection in page title: {title}[/yellow]")
                    return True
            except:
                pass

            # Check for unusual page content
            try:
                page_text = page.inner_text('body').lower()
                if any(phrase in page_text for phrase in ['verify you are human', 'prove you are not a robot', 'security check']):
                    console.print("[yellow]🤖 Bot detection in page content[/yellow]")
                    return True
            except:
                pass

            return False

        except Exception as e:
            console.print(f"[yellow]⚠️ Error checking for bot detection: {e}[/yellow]")
            return False

    def _handle_verification(self, page: Page) -> bool:
        """Enhanced verification handling with better user experience."""
        try:
            console.print("\n[bold red]🚨 BOT DETECTION TRIGGERED[/bold red]")
            console.print("[yellow]Eluta has detected automated behavior and requires verification.[/yellow]")
            console.print("[cyan]This is normal - we'll handle it gracefully.[/cyan]")

            # Save current session state
            current_url = page.url
            current_cookies = self.browser_context.cookies()

            console.print(f"\n[bold cyan]📋 VERIFICATION INSTRUCTIONS:[/bold cyan]")
            console.print("[yellow]1. A new browser window will open[/yellow]")
            console.print("[yellow]2. Complete any CAPTCHA or verification challenge[/yellow]")
            console.print("[yellow]3. Wait until you can see job listings normally[/yellow]")
            console.print("[yellow]4. Return here and press Enter to continue[/yellow]")
            console.print("[yellow]5. Do NOT close the verification browser window yet[/yellow]")

            # Create a new visible browser context with enhanced stealth
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                # Launch with more realistic browser settings
                visible_browser = p.chromium.launch(
                    headless=False,
                    args=[
                        '--no-first-run',
                        '--no-default-browser-check',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-extensions-except',
                        '--disable-extensions',
                        '--disable-plugins',
                        '--disable-images',
                        '--disable-javascript',
                        '--disable-dev-shm-usage',
                        '--no-sandbox'
                    ]
                )

                visible_context = visible_browser.new_context(
                    user_agent=random.choice(self.user_agents),
                    viewport={"width": 1366, "height": 768},
                    locale="en-US",
                    timezone_id="America/Toronto"
                )

                visible_page = visible_context.new_page()

                # Setup stealth for the visible browser too
                self._setup_human_like_browser(visible_page)

                console.print(f"\n[bold green]🌐 Opening verification browser...[/bold green]")

                # Navigate to Eluta homepage first (more natural)
                visible_page.goto("https://www.eluta.ca", timeout=30000)
                time.sleep(random.uniform(2, 4))

                # Then navigate to the problematic URL
                visible_page.goto(current_url, timeout=30000)

                console.print(f"[bold cyan]🌐 Verification browser opened at: {current_url}[/bold cyan]")
                console.print("[bold yellow]👆 Please complete verification in the browser window above[/bold yellow]")
                console.print("[cyan]Take your time - there's no rush. Press Enter when ready to continue...[/cyan]")

                # Wait for user confirmation
                input()

                # Give user a moment to ensure verification is complete
                console.print("[cyan]🔍 Checking if verification was successful...[/cyan]")
                time.sleep(2)

                # Check if verification was successful
                verification_success = False
                for attempt in range(3):
                    if not self._check_for_bot_detection(visible_page):
                        console.print("[bold green]✅ Verification completed successfully![/bold green]")
                        verification_success = True
                        break
                    else:
                        if attempt < 2:
                            console.print(f"[yellow]⚠️ Verification still pending, attempt {attempt + 1}/3[/yellow]")
                            console.print("[yellow]Please ensure verification is complete, then press Enter...[/yellow]")
                            input()
                        else:
                            console.print("[red]❌ Verification still required after 3 attempts[/red]")

                if verification_success:
                    # Copy cookies and session data back to main session
                    try:
                        new_cookies = visible_context.cookies()
                        console.print(f"[cyan]🍪 Copying {len(new_cookies)} cookies to main session[/cyan]")

                        # Clear old cookies and add new ones
                        self.browser_context.clear_cookies()
                        self.browser_context.add_cookies(new_cookies)

                        # Store cookies for future use
                        self.session_cookies = new_cookies

                        console.print("[green]✅ Session data transferred successfully[/green]")

                    except Exception as e:
                        console.print(f"[yellow]⚠️ Could not transfer session data: {e}[/yellow]")

                # Ask user if they want to keep the verification browser open
                console.print("\n[cyan]🤔 Keep verification browser open for reference? (y/n)[/cyan]")
                keep_open = input().lower().startswith('y')

                if not keep_open:
                    visible_browser.close()
                    console.print("[cyan]🔒 Verification browser closed[/cyan]")
                else:
                    console.print("[cyan]🌐 Verification browser kept open for reference[/cyan]")
                    console.print("[yellow]⚠️ Remember to close it manually when done[/yellow]")

                return verification_success

        except Exception as e:
            console.print(f"[red]❌ Error during verification process: {e}[/red]")
            import traceback
            traceback.print_exc()
            return False

    def _save_session_state(self) -> None:
        """Save current session state for recovery."""
        try:
            if self.browser_context and self.session_cookies:
                session_file = f"profiles/{self.profile.get('profile_name', 'default')}/eluta_session.json"
                import os
                os.makedirs(os.path.dirname(session_file), exist_ok=True)

                session_data = {
                    "cookies": self.session_cookies,
                    "timestamp": datetime.now().isoformat(),
                    "user_agent": random.choice(self.user_agents)
                }

                import json
                with open(session_file, 'w') as f:
                    json.dump(session_data, f, indent=2)

                console.print(f"[cyan]💾 Session state saved to {session_file}[/cyan]")

        except Exception as e:
            console.print(f"[yellow]⚠️ Could not save session state: {e}[/yellow]")

    def _load_session_state(self) -> bool:
        """Load previous session state if available."""
        try:
            session_file = f"profiles/{self.profile.get('profile_name', 'default')}/eluta_session.json"

            if not os.path.exists(session_file):
                return False

            import json
            with open(session_file, 'r') as f:
                session_data = json.load(f)

            # Check if session is recent (within 24 hours)
            session_time = datetime.fromisoformat(session_data.get("timestamp", ""))
            if datetime.now() - session_time > timedelta(hours=24):
                console.print("[yellow]⚠️ Saved session is too old, starting fresh[/yellow]")
                return False

            # Restore cookies
            cookies = session_data.get("cookies", [])
            if cookies and self.browser_context:
                self.browser_context.add_cookies(cookies)
                self.session_cookies = cookies
                console.print(f"[green]✅ Restored session with {len(cookies)} cookies[/green]")
                return True

        except Exception as e:
            console.print(f"[yellow]⚠️ Could not load session state: {e}[/yellow]")

        return False

    def _start_with_homepage(self, page: Page) -> bool:
        """Start session by visiting homepage first (more natural behavior)."""
        try:
            console.print("[cyan]🏠 Starting with Eluta homepage for natural session...[/cyan]")

            # Visit homepage first
            if not self._human_like_navigation(page, "https://www.eluta.ca"):
                return False

            # Simulate browsing behavior
            time.sleep(random.uniform(2, 5))

            # Maybe click on a few elements to look more human
            try:
                # Look for safe elements to interact with
                safe_elements = page.query_selector_all("a[href*='/browse'], a[href*='/about'], a[href*='/help']")
                if safe_elements and random.random() < 0.3:  # 30% chance
                    element = random.choice(safe_elements)
                    self._human_like_click(page, element)
                    time.sleep(random.uniform(1, 3))
                    page.go_back()
                    time.sleep(random.uniform(1, 2))
            except:
                pass  # Ignore interaction errors

            console.print("[green]✅ Homepage session established[/green]")
            return True

        except Exception as e:
            console.print(f"[yellow]⚠️ Homepage session failed: {e}[/yellow]")
            return False
    
    def _search_keyword(self, page: Page, keyword: str) -> Generator[Dict, None, None]:
        """
        Search a single keyword through pages with comprehensive mode support.
        """
        page_num = 1
        jobs_found_for_keyword = 0
        max_pages = self.max_pages_per_keyword
        consecutive_old_pages = 0  # Track consecutive pages with mostly old jobs

        console.print(f"[bold cyan]🔍 Searching '{keyword}' - will scan up to page {max_pages} or until jobs older than {self.max_age_days} days[/bold cyan]")

        while page_num <= max_pages:
            console.print(f"[cyan]📄 Searching '{keyword}' - Page {page_num}/{max_pages}[/cyan]")
            self.session_stats['pages_scraped'] += 1

            # Get jobs from this page
            page_jobs = list(self._scrape_page(page, keyword, page_num))

            if not page_jobs:
                console.print(f"[yellow]⚠️ No more jobs found for '{keyword}' on page {page_num}[/yellow]")
                break

            # Filter by date and yield jobs
            recent_jobs = 0
            old_jobs = 0
            very_old_jobs = 0  # Jobs older than max_age_days

            for job in page_jobs:
                if self._is_job_recent(job):
                    jobs_found_for_keyword += 1
                    recent_jobs += 1
                    yield job
                else:
                    old_jobs += 1
                    # Check if job is very old (beyond our threshold)
                    if self._is_job_very_old(job):
                        very_old_jobs += 1
                    if not self.comprehensive_mode:  # Only log in standard mode to reduce noise
                        console.print(f"[yellow]⏰ Skipping old job: {job.get('title', 'Unknown')} ({job.get('posted_date', 'no date')})[/yellow]")

            console.print(f"[green]✅ Page {page_num}: {recent_jobs} recent jobs, {old_jobs} old jobs[/green]")

            # In comprehensive mode, be more aggressive about continuing
            if self.comprehensive_mode:
                # Only stop if we get 3 consecutive pages with mostly very old jobs
                if very_old_jobs > recent_jobs:
                    consecutive_old_pages += 1
                    console.print(f"[yellow]⚠️ Page {page_num} has mostly old jobs (consecutive: {consecutive_old_pages})[/yellow]")
                    if consecutive_old_pages >= 3:
                        console.print(f"[yellow]🛑 3 consecutive pages with old jobs, stopping[/yellow]")
                        break
                else:
                    consecutive_old_pages = 0  # Reset counter
            else:
                # Standard mode: stop earlier
                if very_old_jobs > 0:
                    console.print(f"[yellow]🛑 Found jobs older than {self.max_age_days} days on page {page_num}, stopping[/yellow]")
                    break

                # Also stop if we're getting mostly old jobs and we're past page 3
                if old_jobs > recent_jobs * 2 and page_num > 3:
                    console.print(f"[yellow]⚠️ Too many old jobs on page {page_num}, likely reached {self.max_age_days}+ day threshold[/yellow]")
                    break

            # Check if we should continue to next page
            if not self._has_next_page(page):
                console.print(f"[yellow]📄 No more pages for '{keyword}'[/yellow]")
                break

            page_num += 1

            # Delay between pages with mode-specific timing
            delay_range = self.delay_between_pages
            delay = random.uniform(delay_range[0], delay_range[1])
            console.print(f"[cyan]⏳ Waiting {delay:.1f}s before next page...[/cyan]")
            time.sleep(delay)

        console.print(f"[bold green]✅ Total recent jobs found for '{keyword}': {jobs_found_for_keyword} (scanned {page_num-1} pages)[/bold green]")
    
    def _scrape_page(self, page: Page, keyword: str, page_num: int) -> Generator[Dict, None, None]:
        """
        Scrape jobs from a single page for a specific keyword.
        """
        try:
            # Construct URL for this keyword and page using Eluta's format
            # Example: https://www.eluta.ca/search?q=analyst+sort%3Arank&pg=10
            encoded_keyword = urllib.parse.quote_plus(keyword)

            # Use Eluta's proper URL format without location (Canada-wide search)
            if page_num == 1:
                search_url = f"{self.base_url}?q={encoded_keyword}"
            else:
                search_url = f"{self.base_url}?q={encoded_keyword}+sort%3Arank&pg={page_num}"

            console.print(f"[green]🌐 Navigating to: {search_url}[/green]")

            # Use human-like navigation instead of direct goto
            if not self._human_like_navigation(page, search_url):
                console.print("[red]❌ Navigation failed, skipping this page[/red]")
                return

            # Check for bot detection after navigation
            if self._check_for_bot_detection(page):
                console.print("[yellow]🤖 Bot detection triggered during navigation[/yellow]")
                if not self._handle_verification(page):
                    console.print("[red]❌ Could not resolve verification, skipping this page[/red]")
                    return

            # Simulate human reading behavior
            self._simulate_human_reading(page)

            # Human-like delay before extracting content
            delay = random.uniform(*self.search_delay)
            console.print(f"[yellow]⏳ Content extraction delay: {delay:.1f}s[/yellow]")
            time.sleep(delay)
            
            # Wait for job results to load with multiple fallback selectors
            job_found = False
            selectors_to_try = [
                "a[href*='/job/']",  # Direct job links (highest priority)
                "a[href*='/direct/']",  # Direct application links
                "a[title]",  # Original selector
                ".job-listing",  # Job listing containers
                "[data-job-id]",  # Elements with job IDs
                "div[class*='job']",  # Generic job divs
                "article",  # Article elements (common for job listings)
                ".listing"  # Generic listing elements
            ]

            for selector in selectors_to_try:
                try:
                    page.wait_for_selector(selector, timeout=8000)
                    job_found = True
                    break
                except PlaywrightTimeoutError:
                    continue

            if not job_found:
                console.print(f"[yellow]⚠️ Timeout waiting for results on page {page_num}[/yellow]")
                # Try to continue anyway - maybe the page loaded but with different structure
                console.print(f"[cyan]🔍 Attempting to extract jobs anyway...[/cyan]")

            # Extract job elements - Eluta-specific approach
            # Eluta uses simple div elements containing job data, so we need to filter intelligently
            console.print("[cyan]🔍 Looking for job-containing divs...[/cyan]")

            # First, try to find job elements using more specific selectors
            job_elements = []

            # Strategy 1: Look for elements that contain actual job links (NOT review links)
            console.print("[cyan]🔍 Strategy 1: Looking for containers with actual job links...[/cyan]")

            # First, get all potential job containers
            all_containers = page.query_selector_all("div")
            console.print(f"[cyan]🔍 Scanning {len(all_containers)} div containers...[/cyan]")

            for container in all_containers:
                try:
                    # Check if this container has any links
                    all_links = container.query_selector_all("a")
                    if not all_links:
                        continue

                    # Check each link in the container
                    has_job_link = False
                    has_review_link = False
                    valid_job_link = None

                    for link in all_links:
                        href = link.get_attribute("href") or ""

                        # Check for review/employer page links (EXCLUDE these)
                        if any(bad_domain in href for bad_domain in [
                            'canadastop100.com', 'reviews.', 'top-employer', 'employer-review',
                            'company-profile', 'employer-profile', 'about-employer'
                        ]):
                            has_review_link = True
                            console.print(f"[red]❌ Found review link in container: {href}[/red]")
                            break  # Skip this entire container

                        # Check for actual job links (INCLUDE these)
                        if '/job/' in href and 'eluta.ca' in href:
                            has_job_link = True
                            valid_job_link = link
                            console.print(f"[green]✅ Found valid job link: {href}[/green]")

                    # Only add containers that have job links and NO review links
                    if has_job_link and not has_review_link and valid_job_link:
                        job_elements.append(container)
                        console.print(f"[bold green]✅ Added valid job container[/bold green]")
                    elif has_review_link:
                        console.print(f"[yellow]⚠️ Skipped container with review link[/yellow]")

                except Exception as e:
                    continue  # Skip problematic containers

            # Strategy 2: If we didn't find enough job containers, fall back to div scanning
            if len(job_elements) < 3:
                console.print(f"[yellow]⚠️ Only found {len(job_elements)} job containers, scanning all divs...[/yellow]")

                all_divs = page.query_selector_all("div")

                for div in all_divs:
                    try:
                        text = div.inner_text().strip()

                        # Skip empty or very short divs
                        if not text or len(text) < 30:
                            continue

                        # Skip navigation, header, and non-job elements
                        if any(skip_text in text.lower() for skip_text in [
                            'search jobs', 'find top employers', 'post job', 'advanced search',
                            'browse jobs', 'sort by', 'within', 'remote', 'salary', 'clear all',
                            'distance', 'date posted', 'popularity', 'job-level', 'category',
                            'full-time (', 'part-time (', 'canada\'s top 100 employers',
                            'advertise your jobs', 'dismiss', 'eluta does not contact',
                            'giving back is ingrained', 'equity is good medicine',
                            'questrade team focuses', 'computing - software', 'finance/banking',
                            'top employers for', 'scam', 'text message', 'personal information',
                            'top employer', 'employer review', 'company review', 'about this employer',
                            'visit company website', 'learn more about', 'employer profile'
                        ]):
                            continue

                        # Skip elements that contain review or employer page links
                        if any(bad_url in text.lower() for bad_url in [
                            'canadastop100.com', 'reviews.', 'top-employer', 'employer-review'
                        ]):
                            continue

                        # Look for job-like indicators
                        lines = [line.strip() for line in text.split('\n') if line.strip()]
                        if len(lines) < 2:  # Jobs should have at least title and company
                            continue

                        # Check if this looks like a job posting using scoring system
                        # Look for job title patterns in first line
                        first_line = lines[0].lower()
                        job_title_words = [
                            'analyst', 'developer', 'engineer', 'manager', 'specialist', 'coordinator',
                            'director', 'supervisor', 'lead', 'senior', 'junior', 'associate',
                            'consultant', 'advisor', 'officer', 'representative', 'technician'
                        ]

                        # Define indicator lists for scoring
                        company_indicators = [
                            'inc', 'ltd', 'corp', 'company', 'group', 'solutions', 'services',
                            'technologies', 'systems', 'bank', 'financial', 'insurance'
                        ]

                        location_indicators = [
                            'toronto', 'ontario', 'canada', 'remote', 'hybrid', 'on', 'bc', 'ab'
                        ]

                        time_indicators = ['ago', 'hour', 'day', 'week', 'posted', 'yesterday', 'today']

                        # Additional validation - must have multiple job indicators for quality
                        job_score = 0

                        # Score based on job title patterns
                        first_line = lines[0].lower()
                        if any(word in first_line for word in job_title_words):
                            job_score += 2

                        # Score based on company patterns
                        if len(lines) >= 2:
                            second_line = lines[1].lower()
                            if any(indicator in second_line for indicator in company_indicators):
                                job_score += 2

                        # Score based on location
                        if any(indicator in text.lower() for indicator in location_indicators):
                            job_score += 1

                        # Score based on time indicators
                        if any(indicator in text.lower() for indicator in time_indicators):
                            job_score += 1

                        # Score based on structure (multiple meaningful lines)
                        if len(lines) >= 3:
                            job_score += 1

                        # Only include if it has a high enough job score (minimum 3 points)
                        if job_score >= 3:
                            job_elements.append(div)

                    except Exception as e:
                        continue  # Skip problematic divs

            if not job_elements:
                console.print(f"[yellow]⚠️ No job elements found on page {page_num}[/yellow]")
                # Debug: print page content to understand structure
                if page_num == 1:  # Only debug first page
                    page_text = page.inner_text()[:500]
                    console.print(f"[yellow]Page content sample: {page_text}...[/yellow]")
                return
            
            console.print(f"[green]✅ Found {len(job_elements)} job containers on page {page_num}[/green]")
            
            # Extract each job with optional deep scraping
            console.print(f"[cyan]📋 Processing {len(job_elements)} job elements...[/cyan]")

            for i, job_elem in enumerate(job_elements, 1):
                try:
                    job = self._extract_job_from_element(job_elem, page)  # Pass page parameter
                    if job:
                        # Add keyword that found this job
                        job["found_by_keyword"] = keyword

                        # Perform deep scraping if enabled
                        if self.deep_scraping and job.get("url"):
                            console.print(f"[cyan]🔍 Deep scraping job {i}: {job['title']}[/cyan]")
                            enhanced_job = self._deep_scrape_job(page, job)
                            if enhanced_job:
                                job = enhanced_job
                                console.print(f"[green]✅ Deep scraped job {i}: Found real application URL[/green]")
                            else:
                                console.print(f"[yellow]⚠️ Deep scraping failed for job {i}, using basic data[/yellow]")

                        console.print(f"[green]✅ Extracted job {i}: {job['title']} at {job['company']}[/green]")
                        yield self.normalize_job(job)
                    else:
                        console.print(f"[yellow]⚠️ Could not extract job {i}[/yellow]")
                except Exception as e:
                    console.print(f"[red]❌ Error extracting job {i}: {e}[/red]")
                    if i <= 3:  # Show details for first few errors
                        import traceback
                        traceback.print_exc()
                    continue
        
        except Exception as e:
            console.print(f"[red]❌ Error scraping page {page_num} for '{keyword}': {e}[/red]")
    
    def _extract_job_from_element(self, job_elem, page: Page) -> Optional[Dict]:
        """
        Extract job data by clicking on the job element and getting the real application URL.
        This is the key fix - we click on each job posting to get the actual URL.
        """
        try:
            # Get all text from the element for basic info
            all_text = job_elem.inner_text().strip()
            if not all_text or len(all_text) < 10:
                return None

            # Extract basic info from the job element first
            title = ""
            company = "Unknown Company"
            location = ""

            # Try to find a clickable link in this element
            clickable_link = None

            try:
                # Look for clickable job links - be VERY strict about what we click
                console.print("[cyan]🔍 Looking for valid job links to click...[/cyan]")

                all_links = job_elem.query_selector_all("a")
                console.print(f"[cyan]Found {len(all_links)} links in job element[/cyan]")

                for link in all_links:
                    href = link.get_attribute("href") or ""
                    link_text = link.inner_text().strip()

                    console.print(f"[cyan]Examining link: {href} (text: '{link_text[:50]}...')")

                    # Skip empty or invalid links
                    if not href or href in ["#", "#!", "javascript:void(0)", "javascript:", ""]:
                        console.print(f"[yellow]⚠️ Skipping invalid link: {href}[/yellow]")
                        continue

                    # STRICT EXCLUSION: Skip any review/employer page links
                    if any(bad_domain in href for bad_domain in [
                        'canadastop100.com', 'reviews.', 'top-employer', 'employer-review',
                        'company-profile', 'employer-profile', 'about-employer', 'top100'
                    ]):
                        console.print(f"[red]❌ EXCLUDED review/employer link: {href}[/red]")
                        continue

                    # STRICT INCLUSION: Only accept actual job posting links
                    if '/job/' in href and 'eluta.ca' in href:
                        clickable_link = link
                        console.print(f"[bold green]🎯 Found valid job link: {href}[/bold green]")
                        break
                    else:
                        console.print(f"[yellow]⚠️ Not a job link: {href}[/yellow]")

                # If no valid job link found, this is not a real job posting
                if not clickable_link:
                    console.print(f"[red]❌ No valid job links found in element[/red]")
                    return None

                if not clickable_link:
                    console.print(f"[yellow]⚠️ No clickable link found in job element[/yellow]")
                    return None

                # Get title from link text or title attribute
                title = clickable_link.get_attribute("title") or clickable_link.inner_text().strip()

            except Exception as e:
                console.print(f"[yellow]⚠️ Error finding clickable link: {e}[/yellow]")
                return None

            # NOW THE KEY FIX: Click on the job posting and wait 3 seconds to get the real URL
            console.print(f"[cyan]🖱️ Human-like clicking on job posting: {title}[/cyan]")

            try:
                # Store the current page URL to return to it later
                search_results_url = page.url

                # Use human-like clicking behavior
                if not self._human_like_click(page, clickable_link):
                    console.print("[yellow]⚠️ Human-like click failed, trying direct click[/yellow]")
                    clickable_link.click()

                # Wait 3 seconds as requested by the user + additional human-like delay
                base_wait = 3.0
                additional_wait = random.uniform(0.5, 2.0)
                total_wait = base_wait + additional_wait
                console.print(f"[yellow]⏳ Waiting {total_wait:.1f}s for job page to load (3s + {additional_wait:.1f}s human variance)...[/yellow]")
                page.wait_for_timeout(int(total_wait * 1000))

                # Wait for the page to fully load with longer timeout
                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except:
                    console.print("[yellow]⚠️ Page still loading, continuing with extraction[/yellow]")

                # Now we're on the job details page - extract the real application URL
                real_job_url = page.url
                console.print(f"[green]✅ Got real job URL: {real_job_url}[/green]")

                # Try to find the real external application URL on this page
                external_apply_url = self._find_external_apply_url(page)
                if external_apply_url:
                    real_job_url = external_apply_url
                    console.print(f"[bold green]🎯 Found external apply URL: {external_apply_url}[/bold green]")

                # Go back to search results to continue with next job using human-like navigation
                console.print(f"[cyan]🔙 Returning to search results...[/cyan]")
                if not self._human_like_navigation(page, search_results_url):
                    # Fallback to direct navigation
                    page.goto(search_results_url)
                    page.wait_for_load_state("networkidle", timeout=10000)

                # Extract basic info from the original job element text
                lines = [line.strip() for line in all_text.split('\n') if line.strip()]

                # If no title from link, use first line of text
                if not title and lines:
                    title = lines[0]

                # Extract company and location from text patterns
                company = self._extract_company_name(real_job_url, lines, all_text)
                location = self._extract_location(lines)

            except Exception as e:
                console.print(f"[red]❌ Error clicking job or extracting details: {e}[/red]")
                # If clicking failed, try to extract what we can from the search results
                real_job_url = clickable_link.get_attribute("href")
                if real_job_url and real_job_url.startswith("/"):
                    real_job_url = f"https://www.eluta.ca{real_job_url}"
                job_details = {}

            # Extract basic info from the original job element text if not already extracted
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]

            # If no title from link, use first line of text
            if not title and lines:
                title = lines[0]

            # Look for posted date
            posted_date = ""
            for line in lines:
                if any(time_word in line.lower() for time_word in ["hour", "day", "week", "ago", "yesterday", "today"]):
                    posted_date = line
                    break

            # Create summary from remaining text
            summary = all_text
            if len(summary) > 300:
                summary = summary[:300] + "..."

            # More lenient validation - don't skip jobs with short titles
            if not title:
                title = "Job Opportunity"  # Fallback title

            # Clean up title (remove extra whitespace, newlines)
            title = " ".join(title.split())
            company = " ".join(company.split())
            location = " ".join(location.split())

            # Ensure we have a valid URL
            if not real_job_url:
                console.print(f"[red]❌ Could not find valid URL for job: {title} - skipping[/red]")
                return None

            # Add required fields for database compatibility
            job_data = {
                "title": title,
                "company": company,
                "location": location,
                "url": real_job_url,  # Use the real URL we got by clicking
                "apply_url": real_job_url,  # Same as URL for now
                "summary": summary,
                "posted_date": posted_date,
                "scraped_at": datetime.now().isoformat(),
                "site": "eluta_enhanced",
                "salary": "",
                "job_type": "",
                "full_description": summary,
                "requirements": [],
                "qualifications": [],
                "benefits": [],
                "apply_instructions": "",
                "skills_needed": [],
                "experience_level": "",
                "education_required": "",
                "deep_scraped": True  # We clicked and got the real URL
            }

            console.print(f"[bold green]✅ Successfully extracted job: {title} at {company}[/bold green]")
            return job_data

        except Exception as e:
            console.print(f"[red]❌ Error extracting job data: {e}[/red]")
            # Don't create fake URLs - just return None to skip jobs without valid URLs
            return None

    def normalize_job(self, raw_job: Dict) -> Dict:
        """
        Normalize a raw job dictionary to standard format with all required fields.
        """
        normalized = super().normalize_job(raw_job)

        # Add additional fields required by the database
        normalized.update({
            "scraped_at": raw_job.get("scraped_at", datetime.now().isoformat()),
            "site": "eluta_enhanced",
            "site_display": "Eluta",  # Clear display name for dashboard
            "full_description": raw_job.get("full_description", raw_job.get("summary", "")),
            "requirements": raw_job.get("requirements", []),
            "qualifications": raw_job.get("qualifications", []),
            "benefits": raw_job.get("benefits", []),
            "apply_instructions": raw_job.get("apply_instructions", ""),
            "skills_needed": raw_job.get("skills_needed", []),
            "experience_level": raw_job.get("experience_level", ""),
            "education_required": raw_job.get("education_required", ""),
            "deep_scraped": raw_job.get("deep_scraped", False)
        })

        return normalized

    def _extract_company_name(self, job_url: str, lines: List[str], all_text: str) -> str:
        """
        Enhanced company name extraction using multiple strategies.
        """
        try:
            # Strategy 1: Extract from URL if it contains company info
            if job_url and 'eluta.ca' in job_url:
                if '/company/' in job_url:
                    try:
                        company_part = job_url.split('/company/')[1].split('/')[0]
                        company_name = company_part.replace('-', ' ').replace('_', ' ').title()
                        if len(company_name) > 2 and company_name.lower() not in ['unknown', 'eluta', 'job', 'search']:
                            console.print(f"[green]✅ Company from URL: {company_name}[/green]")
                            return company_name
                    except:
                        pass

                # Try to extract from job URL path - but be more careful
                if '/job/' in job_url:
                    try:
                        url_parts = job_url.split('/')
                        for i, part in enumerate(url_parts):
                            if part == 'job' and i + 1 < len(url_parts):
                                potential_company = url_parts[i + 1].replace('-', ' ').title()
                                # More validation to avoid false positives
                                if (len(potential_company) > 3 and
                                    potential_company.lower() not in ['eluta', 'search', 'jobs', 'posting', 'details'] and
                                    not potential_company.isdigit()):
                                    console.print(f"[green]✅ Company from job URL: {potential_company}[/green]")
                                    return potential_company
                    except:
                        pass

            # Strategy 2: Look for company patterns in text lines
            for i, line in enumerate(lines):
                line_clean = line.replace("TOP EMPLOYER", "").strip()

                # Skip lines that are clearly not company names
                if any(word in line_clean.lower() for word in [
                    "ago", "hour", "day", "week", "posted", "apply", "job", "position",
                    "full time", "part time", "remote", "hybrid", "salary", "$", "eluta"
                ]):
                    continue

                # Company is often in the second line after title
                if i == 1 and line_clean and len(line_clean) > 2:
                    # Additional validation for company names
                    if (not any(char.isdigit() for char in line_clean[:10]) and  # No numbers at start
                        len(line_clean.split()) <= 6 and  # Not too long
                        line_clean.lower() not in ['unknown', 'eluta', 'company', 'employer']):  # Not generic
                        console.print(f"[green]✅ Company from line 2: {line_clean}[/green]")
                        return line_clean

                # Look for lines that look like company names
                if (len(line_clean) > 2 and len(line_clean) < 50 and
                    not line_clean.lower().startswith(('the ', 'a ', 'an ')) and
                    line_clean[0].isupper() and
                    line_clean.lower() not in ['unknown', 'eluta', 'company', 'employer']):

                    # Check if it contains company indicators
                    company_indicators = ['inc', 'ltd', 'corp', 'company', 'group', 'solutions', 'services', 'technologies', 'bank', 'financial', 'insurance', 'consulting']
                    if any(indicator in line_clean.lower() for indicator in company_indicators):
                        console.print(f"[green]✅ Company with indicator: {line_clean}[/green]")
                        return line_clean

            # Strategy 3: Look for company patterns in full text
            import re

            # Look for "at [Company Name]" patterns
            at_pattern = re.search(r'\bat\s+([A-Z][a-zA-Z\s&.,]+?)(?:\s+in\s+|\s+\-|\s*$)', all_text)
            if at_pattern:
                potential_company = at_pattern.group(1).strip()
                if len(potential_company) > 2 and len(potential_company) < 50:
                    return potential_company

            # Look for "Company: [Name]" patterns
            company_pattern = re.search(r'Company:\s*([A-Z][a-zA-Z\s&.,]+?)(?:\n|$)', all_text)
            if company_pattern:
                potential_company = company_pattern.group(1).strip()
                if len(potential_company) > 2:
                    return potential_company

            # Strategy 4: Fallback to second line if it looks reasonable
            if len(lines) >= 2:
                potential_company = lines[1].replace("TOP EMPLOYER", "").strip()
                if (potential_company and len(potential_company) > 2 and
                    potential_company.lower() not in ['unknown', 'eluta', 'company', 'employer'] and
                    not any(word in potential_company.lower() for word in ["ago", "hour", "day", "week", "posted", "eluta"])):
                    console.print(f"[yellow]⚠️ Fallback company from line 2: {potential_company}[/yellow]")
                    return potential_company

            # Strategy 5: Look for any capitalized words that might be company names
            for line in lines[1:4]:  # Check lines 2-4
                words = line.split()
                for word in words:
                    if (len(word) > 3 and word[0].isupper() and
                        word.lower() not in ['unknown', 'eluta', 'company', 'employer', 'posted', 'apply', 'job'] and
                        not any(char.isdigit() for char in word)):
                        console.print(f"[yellow]⚠️ Potential company word: {word}[/yellow]")
                        return word

            console.print(f"[red]❌ Could not extract company name, using fallback[/red]")
            return "Unknown Company"

        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting company name: {e}[/yellow]")
            return "Unknown Company"

    def _extract_location(self, lines: List[str]) -> str:
        """
        Enhanced location extraction.
        """
        try:
            # Look for location patterns in lines
            for i, line in enumerate(lines):
                line_clean = line.strip()

                # Skip lines that are clearly not locations
                if any(word in line_clean.lower() for word in [
                    "ago", "hour", "day", "week", "posted", "apply", "job", "position", "salary", "$"
                ]):
                    continue

                # Location is often in the third line, or after company
                if i >= 2 and line_clean:
                    # Check if it looks like a location (contains common location words)
                    location_indicators = [
                        'ontario', 'quebec', 'alberta', 'british columbia', 'bc', 'on', 'qc', 'ab',
                        'toronto', 'vancouver', 'montreal', 'calgary', 'ottawa', 'edmonton',
                        'canada', 'remote', 'hybrid', 'downtown', 'north', 'south', 'east', 'west',
                        'city', 'county', 'province', 'street', 'avenue', 'road', 'drive'
                    ]

                    if (any(indicator in line_clean.lower() for indicator in location_indicators) or
                        len(line_clean.split()) <= 4):  # Short phrases are often locations
                        return line_clean

            # Fallback to third line if available
            if len(lines) >= 3:
                potential_location = lines[2].strip()
                if (potential_location and
                    not any(word in potential_location.lower() for word in ["ago", "hour", "day", "week", "posted"])):
                    return potential_location

            return ""

        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting location: {e}[/yellow]")
            return ""

    def _deep_scrape_job(self, page: Page, job: Dict) -> Optional[Dict]:
        """
        Click into individual job posting to get detailed information.
        This is where we get the full job description, requirements, and application details.
        """
        try:
            job_url = job.get("url")
            if not job_url or job_url in ["#", "#!", ""]:
                console.print(f"[yellow]⚠️ No valid URL for job: {job.get('title', 'Unknown')} - skipping deep scrape[/yellow]")
                # Mark as processed but not deep scraped
                job["deep_scraped"] = False
                job["apply_url"] = ""  # No apply URL available
                return job

            console.print(f"[cyan]🌐 Opening job details: {job_url}[/cyan]")

            # Open job in new tab to avoid losing search results
            job_page = page.context.new_page()

            try:
                # Navigate to job details page
                job_page.goto(job_url, timeout=30000)
                job_page.wait_for_load_state("networkidle", timeout=20000)

                # Extract detailed job information
                detailed_info = self._extract_detailed_job_info(job_page)

                # Merge detailed info with basic job info
                job.update(detailed_info)
                job["deep_scraped"] = True

                console.print(f"[green]✅ Deep scraped: {job['title']} - Found {len(job.get('requirements', []))} requirements[/green]")

                return job

            except Exception as e:
                console.print(f"[yellow]⚠️ Failed to deep scrape {job['title']}: {e}[/yellow]")
                return job
            finally:
                # Always close the job details page
                try:
                    job_page.close()
                except:
                    pass

        except Exception as e:
            console.print(f"[red]❌ Error in deep scraping: {e}[/red]")
            return job

    def _print_session_summary(self):
        """Print comprehensive session summary."""
        try:
            if not self.session_stats['start_time']:
                return

            duration = self.session_stats['end_time'] - self.session_stats['start_time']
            duration_str = str(duration).split('.')[0]  # Remove microseconds

            console.print(f"\n[bold green]🎉 SCRAPING SESSION COMPLETE[/bold green]")
            console.print(f"[cyan]⏱️  Duration: {duration_str}[/cyan]")
            console.print(f"[cyan]🔍 Keywords processed: {self.session_stats['keywords_processed']}/{len(self.keywords)}[/cyan]")
            console.print(f"[cyan]📄 Pages scraped: {self.session_stats['pages_scraped']}[/cyan]")
            console.print(f"[cyan]💼 Jobs found: {self.session_stats['jobs_found']}[/cyan]")
            console.print(f"[cyan]🔄 Duplicates skipped: {self.session_stats['duplicates_skipped']}[/cyan]")
            console.print(f"[cyan]❌ Errors encountered: {self.session_stats['errors_encountered']}[/cyan]")

            if self.session_stats['pages_scraped'] > 0:
                avg_jobs_per_page = self.session_stats['jobs_found'] / self.session_stats['pages_scraped']
                console.print(f"[cyan]📊 Average jobs per page: {avg_jobs_per_page:.1f}[/cyan]")

            if duration.total_seconds() > 0:
                jobs_per_minute = (self.session_stats['jobs_found'] / duration.total_seconds()) * 60
                console.print(f"[cyan]⚡ Jobs per minute: {jobs_per_minute:.1f}[/cyan]")

            console.print(f"[bold yellow]🎯 Mode: {'COMPREHENSIVE' if self.comprehensive_mode else 'STANDARD'}[/bold yellow]")

        except Exception as e:
            console.print(f"[yellow]⚠️ Error printing session summary: {e}[/yellow]")

    def _extract_detailed_job_info(self, job_page: Page) -> Dict:
        """
        Extract detailed information from the job details page.
        """
        details = {
            "full_description": "",
            "requirements": [],
            "qualifications": [],
            "benefits": [],
            "salary": "",
            "job_type": "",
            "apply_instructions": "",
            "skills_needed": [],
            "experience_level": "",
            "education_required": "",
            "apply_url": ""
        }

        try:
            # Wait for content to load
            job_page.wait_for_timeout(2000)

            # Get the full job description
            description_selectors = [
                ".job-description",
                ".job-content",
                ".description",
                "[class*='description']",
                ".job-details",
                "main",
                ".content"
            ]

            full_description = ""
            for selector in description_selectors:
                try:
                    desc_elem = job_page.query_selector(selector)
                    if desc_elem:
                        full_description = desc_elem.inner_text().strip()
                        if len(full_description) > 100:  # Found substantial content
                            break
                except:
                    continue

            if not full_description:
                # Fallback: get all text from the page
                full_description = job_page.inner_text()

            details["full_description"] = full_description

            # Extract requirements and qualifications
            requirements, qualifications = self._parse_job_requirements(full_description)
            details["requirements"] = requirements
            details["qualifications"] = qualifications

            # Extract skills
            details["skills_needed"] = self._extract_skills(full_description)

            # Extract salary information
            details["salary"] = self._extract_salary(full_description)

            # Extract job type
            details["job_type"] = self._extract_job_type(full_description)

            # Extract experience level
            details["experience_level"] = self._extract_experience_level(full_description)

            # Extract education requirements
            details["education_required"] = self._extract_education_requirements(full_description)

            # Find apply button/link
            apply_url = self._find_apply_url(job_page)
            if apply_url:
                details["apply_url"] = apply_url

            # Extract application instructions
            details["apply_instructions"] = self._extract_apply_instructions(full_description)

        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting detailed job info: {e}[/yellow]")

        return details

    def _is_job_recent(self, job: Dict) -> bool:
        """
        Check if a job was posted within the last 7 days.
        """
        posted_date = job.get("posted_date", "")
        
        if not posted_date:
            # If no date info, assume it's recent
            return True
        
        # Parse relative dates like "2 hours ago", "3 days ago"
        posted_date_lower = posted_date.lower()
        
        if "hour" in posted_date_lower:
            return True  # Posted today
        
        if "day" in posted_date_lower:
            # Extract number of days
            match = re.search(r'(\d+)\s*day', posted_date_lower)
            if match:
                days_ago = int(match.group(1))
                return days_ago <= self.max_age_days
            return True  # If we can't parse, assume recent
        
        if "week" in posted_date_lower:
            match = re.search(r'(\d+)\s*week', posted_date_lower)
            if match:
                weeks_ago = int(match.group(1))
                return weeks_ago == 1  # Only 1 week ago is acceptable
            return False  # Multiple weeks ago
        
        # If we can't determine, assume it's recent
        return True

    def _is_job_very_old(self, job: Dict) -> bool:
        """
        Check if a job is older than 7 days (our cutoff threshold).
        """
        posted_date = job.get("posted_date", "")

        if not posted_date:
            return False  # If no date info, assume it's not very old

        posted_date_lower = posted_date.lower()

        if "week" in posted_date_lower:
            match = re.search(r'(\d+)\s*week', posted_date_lower)
            if match:
                weeks_ago = int(match.group(1))
                return weeks_ago >= 1  # 1+ weeks is considered very old
            return True  # "weeks ago" without number is very old

        if "day" in posted_date_lower:
            match = re.search(r'(\d+)\s*day', posted_date_lower)
            if match:
                days_ago = int(match.group(1))
                return days_ago > 7  # More than 7 days is very old

        return False

    def _extract_experience_level(self, description: str) -> str:
        """
        Extract experience level requirements from job description.
        Returns: 'entry', 'junior', 'mid', 'senior', 'lead', 'unknown'
        """
        if not description:
            return "unknown"

        desc_lower = description.lower()

        # Entry level indicators
        entry_patterns = [
            r'entry.?level',
            r'0.?2?\s*years?\s*(?:of\s*)?experience',
            r'fresh\s*graduate',
            r'new\s*graduate',
            r'recent\s*graduate',
            r'no\s*experience\s*(?:required|necessary)',
            r'junior\s*(?:level)?',
            r'trainee',
            r'intern(?:ship)?',
            r'associate\s*(?:level)?',
            r'1.?2\s*years?\s*(?:of\s*)?experience',
            r'up\s*to\s*2\s*years?',
            r'less\s*than\s*3\s*years?'
        ]

        # Senior level indicators (to exclude)
        senior_patterns = [
            r'senior',
            r'lead(?:er)?',
            r'principal',
            r'director',
            r'manager',
            r'head\s*of',
            r'chief',
            r'5\+?\s*years?',
            r'[5-9]\s*years?',
            r'10\+?\s*years?',
            r'extensive\s*experience',
            r'proven\s*track\s*record'
        ]

        # Check for entry level patterns
        for pattern in entry_patterns:
            if re.search(pattern, desc_lower):
                return "entry"

        # Check for senior level patterns
        for pattern in senior_patterns:
            if re.search(pattern, desc_lower):
                return "senior"

        # Look for specific year ranges
        year_matches = re.findall(r'(\d+)(?:\s*[-–]\s*(\d+))?\s*years?\s*(?:of\s*)?experience', desc_lower)
        for match in year_matches:
            min_years = int(match[0])
            max_years = int(match[1]) if match[1] else min_years

            if min_years <= 2:
                return "entry"
            elif min_years >= 5:
                return "senior"
            else:
                return "mid"

        return "unknown"

    def _is_suitable_for_profile(self, job: Dict) -> bool:
        """
        Check if job is suitable for the profile (entry-level/1-2 years experience).
        """
        # Check title for senior indicators
        title = job.get("title", "").lower()
        senior_title_keywords = ["senior", "lead", "principal", "director", "manager", "head", "chief"]

        for keyword in senior_title_keywords:
            if keyword in title:
                console.print(f"[yellow]❌ Skipping senior role: {job.get('title', 'Unknown')}[/yellow]")
                return False

        # Check experience level from description
        experience_level = job.get("experience_level", "unknown")

        if experience_level == "entry":
            console.print(f"[green]✅ Entry-level job: {job.get('title', 'Unknown')}[/green]")
            return True
        elif experience_level == "senior":
            console.print(f"[yellow]❌ Senior-level job: {job.get('title', 'Unknown')}[/yellow]")
            return False

        # If unknown, check description for experience requirements
        full_description = job.get("full_description", "")
        if full_description:
            desc_lower = full_description.lower()

            # Look for explicit experience requirements
            if any(pattern in desc_lower for pattern in [
                "5+ years", "5 years", "6+ years", "7+ years", "8+ years", "9+ years", "10+ years",
                "extensive experience", "proven track record", "leadership experience"
            ]):
                console.print(f"[yellow]❌ High experience requirement: {job.get('title', 'Unknown')}[/yellow]")
                return False

            # Look for entry-level indicators
            if any(pattern in desc_lower for pattern in [
                "entry level", "fresh graduate", "new graduate", "0-2 years", "1-2 years",
                "junior", "trainee", "associate level", "no experience required"
            ]):
                console.print(f"[green]✅ Entry-level indicators: {job.get('title', 'Unknown')}[/green]")
                return True

        # Default: if we can't determine, include it (better to have false positives)
        console.print(f"[cyan]? Unknown experience level, including: {job.get('title', 'Unknown')}[/cyan]")
        return True

    def _parse_job_requirements(self, description: str) -> tuple:
        """
        Parse job description to extract requirements and qualifications.
        """
        requirements = []
        qualifications = []

        # Split into lines for analysis
        lines = description.split('\n')

        # Look for requirement sections
        requirement_keywords = [
            'requirements', 'required', 'must have', 'essential', 'mandatory',
            'responsibilities', 'duties', 'what you will do', 'key responsibilities'
        ]

        qualification_keywords = [
            'qualifications', 'preferred', 'nice to have', 'desired', 'ideal',
            'education', 'degree', 'certification', 'experience'
        ]

        current_section = None

        for line in lines:
            line_lower = line.lower().strip()

            # Check if this line starts a requirements section
            if any(keyword in line_lower for keyword in requirement_keywords):
                current_section = 'requirements'
                continue
            elif any(keyword in line_lower for keyword in qualification_keywords):
                current_section = 'qualifications'
                continue

            # Extract bullet points or numbered items
            if line.strip() and (line.strip().startswith('•') or
                               line.strip().startswith('-') or
                               line.strip().startswith('*') or
                               re.match(r'^\d+\.', line.strip())):

                clean_line = re.sub(r'^[•\-*\d\.]\s*', '', line.strip())
                if len(clean_line) > 10:  # Ignore very short items
                    if current_section == 'requirements':
                        requirements.append(clean_line)
                    elif current_section == 'qualifications':
                        qualifications.append(clean_line)
                    else:
                        # If no section identified, add to requirements by default
                        requirements.append(clean_line)

        return requirements[:10], qualifications[:10]  # Limit to 10 items each

    def _extract_skills(self, description: str) -> list:
        """
        Extract technical skills and tools from job description.
        """
        skills = []
        description_lower = description.lower()

        # Common technical skills to look for
        skill_patterns = [
            # Programming languages
            r'\b(python|java|javascript|c\+\+|c#|php|ruby|go|rust|swift|kotlin)\b',
            # Data tools
            r'\b(sql|mysql|postgresql|mongodb|redis|elasticsearch)\b',
            r'\b(pandas|numpy|scipy|matplotlib|seaborn|plotly)\b',
            r'\b(tableau|power bi|qlik|looker|d3\.js)\b',
            # Cloud platforms
            r'\b(aws|azure|gcp|google cloud|amazon web services)\b',
            # Frameworks
            r'\b(react|angular|vue|django|flask|spring|express)\b',
            # Other tools
            r'\b(docker|kubernetes|git|jenkins|terraform|ansible)\b',
            r'\b(excel|powerpoint|word|office 365|google workspace)\b'
        ]

        for pattern in skill_patterns:
            matches = re.findall(pattern, description_lower)
            skills.extend(matches)

        # Remove duplicates and return
        return list(set(skills))[:15]  # Limit to 15 skills

    def _extract_salary(self, description: str) -> str:
        """
        Extract salary information from job description.
        """
        # Look for salary patterns
        salary_patterns = [
            r'\$[\d,]+\s*-\s*\$[\d,]+',
            r'\$[\d,]+k?\s*-\s*\$?[\d,]+k?',
            r'salary:?\s*\$?[\d,]+k?',
            r'compensation:?\s*\$?[\d,]+k?',
            r'pay:?\s*\$?[\d,]+k?'
        ]

        for pattern in salary_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0)

        return ""

    def _extract_job_type(self, description: str) -> str:
        """
        Extract job type (full-time, part-time, contract, etc.)
        """
        description_lower = description.lower()

        job_types = {
            'full-time': ['full time', 'full-time', 'fulltime', 'permanent'],
            'part-time': ['part time', 'part-time', 'parttime'],
            'contract': ['contract', 'contractor', 'temporary', 'temp'],
            'remote': ['remote', 'work from home', 'wfh', 'telecommute'],
            'hybrid': ['hybrid', 'flexible work'],
            'internship': ['intern', 'internship', 'co-op', 'coop']
        }

        for job_type, keywords in job_types.items():
            if any(keyword in description_lower for keyword in keywords):
                return job_type

        return ""



    def _extract_education_requirements(self, description: str) -> str:
        """
        Extract education requirements.
        """
        description_lower = description.lower()

        education_patterns = [
            r'bachelor\'?s?\s*degree',
            r'master\'?s?\s*degree',
            r'phd|doctorate',
            r'high school|diploma',
            r'associate\'?s?\s*degree',
            r'certification',
            r'degree in ([\w\s]+)'
        ]

        for pattern in education_patterns:
            match = re.search(pattern, description_lower)
            if match:
                return match.group(0)

        return ""

    def _find_apply_url(self, job_page: Page) -> str:
        """
        Find the actual company application URL by looking for apply buttons and external links.
        This extracts the real company application URL (like Lever, Workday, etc.) instead of the Eluta URL.
        """
        try:
            # Wait for page to fully load
            job_page.wait_for_load_state("networkidle", timeout=10000)

            console.print("[cyan]🔍 Searching for external application URLs...[/cyan]")

            # Strategy 1: Look for direct external URLs in links (without requiring specific text)
            external_url_selectors = [
                # Specific ATS systems
                "a[href*='workday.com']",
                "a[href*='myworkday.com']",
                "a[href*='wd1.myworkdayjobs.com']",
                "a[href*='greenhouse.io']",
                "a[href*='boards.greenhouse.io']",
                "a[href*='lever.co']",
                "a[href*='jobs.lever.co']",
                "a[href*='icims.com']",
                "a[href*='bamboohr.com']",
                "a[href*='smartrecruiters.com']",
                "a[href*='jobvite.com']",
                "a[href*='ultipro.com']",
                "a[href*='successfactors.com']",
                "a[href*='taleo.net']",

                # Generic external job sites
                "a[href*='careers.']",
                "a[href*='jobs.']",
                "a[href*='/careers/']",
                "a[href*='/jobs/']",
                "a[href*='/apply']",

                # Any external HTTP link (not eluta.ca)
                "a[href^='http']:not([href*='eluta.ca'])"
            ]

            found_urls = []

            for selector in external_url_selectors:
                try:
                    elements = job_page.query_selector_all(selector)
                    for elem in elements:
                        href = elem.get_attribute('href')
                        if href and href not in ['#', '#!', 'javascript:void(0)', 'javascript:']:
                            # Clean up the URL
                            if href.startswith('//'):
                                href = f"https:{href}"
                            elif href.startswith('/') and not href.startswith('//'):
                                continue  # Skip relative URLs to eluta.ca

                            # Validate it's an external URL AND NOT a review/employer page
                            if (href.startswith('http') and
                                'eluta.ca' not in href and
                                href not in found_urls):

                                # CRITICAL: Exclude review and employer page URLs
                                if any(bad_domain in href for bad_domain in [
                                    'canadastop100.com', 'reviews.', 'top-employer', 'employer-review',
                                    'company-profile', 'employer-profile', 'about-employer', 'top100'
                                ]):
                                    link_text = elem.inner_text().strip()
                                    console.print(f"[red]❌ EXCLUDED review/employer URL: {href} (text: '{link_text}')[/red]")
                                    continue

                                # This is a valid external job application URL
                                found_urls.append(href)
                                link_text = elem.inner_text().strip()
                                console.print(f"[bold green]🎯 Found valid external apply URL: {href} (text: '{link_text}')[/bold green]")
                except Exception:
                    continue

            # Strategy 2: If we found multiple URLs, prioritize by ATS system quality
            if found_urls:
                # Prioritize known good ATS systems
                priority_domains = [
                    'workday.com', 'myworkday.com', 'wd1.myworkdayjobs.com',
                    'greenhouse.io', 'boards.greenhouse.io',
                    'lever.co', 'jobs.lever.co',
                    'icims.com', 'bamboohr.com', 'smartrecruiters.com'
                ]

                for domain in priority_domains:
                    for url in found_urls:
                        if domain in url:
                            # Final validation - ensure it's not a review URL
                            if not any(bad_domain in url for bad_domain in [
                                'canadastop100.com', 'reviews.', 'top-employer', 'employer-review',
                                'company-profile', 'employer-profile', 'about-employer', 'top100'
                            ]):
                                console.print(f"[bold green]✅ Selected priority ATS URL: {url}[/bold green]")
                                return url
                            else:
                                console.print(f"[red]❌ Priority URL failed validation: {url}[/red]")

                # If no priority ATS found, return the first valid external URL
                for url in found_urls:
                    # Final validation - ensure it's not a review URL
                    if not any(bad_domain in url for bad_domain in [
                        'canadastop100.com', 'reviews.', 'top-employer', 'employer-review',
                        'company-profile', 'employer-profile', 'about-employer', 'top100'
                    ]):
                        console.print(f"[bold green]✅ Selected validated external URL: {url}[/bold green]")
                        return url
                    else:
                        console.print(f"[red]❌ URL failed final validation: {url}[/red]")

                console.print(f"[red]❌ All found URLs were review/employer pages[/red]")

            # Strategy 3: Look for clickable elements that might trigger navigation to external sites
            console.print("[yellow]⚠️ No direct external URLs found, looking for clickable apply elements...[/yellow]")

            clickable_selectors = [
                "button:has-text('Apply')",
                "button:has-text('View Job')",
                "button:has-text('View Details')",
                "a:has-text('Apply Now')",
                "a:has-text('Apply')",
                ".apply-button",
                ".apply-link",
                "[class*='apply'][class*='button']",
                "[class*='apply'][class*='link']"
            ]

            for selector in clickable_selectors:
                try:
                    elem = job_page.query_selector(selector)
                    if elem and elem.is_visible():
                        console.print(f"[cyan]🔄 Found clickable apply element: {selector}[/cyan]")

                        # Try to click and capture any popup or navigation
                        try:
                            with job_page.expect_popup(timeout=3000) as popup_info:
                                elem.click()

                            popup = popup_info.value
                            if popup:
                                popup_url = popup.url
                                popup.close()
                                if 'eluta.ca' not in popup_url:
                                    console.print(f"[bold green]✅ Found external URL via popup: {popup_url}[/bold green]")
                                    return popup_url
                        except:
                            # No popup, check if page navigated
                            job_page.wait_for_timeout(2000)
                            current_url = job_page.url
                            if 'eluta.ca' not in current_url:
                                console.print(f"[bold green]✅ Found external URL via navigation: {current_url}[/bold green]")
                                return current_url

                except Exception:
                    continue

            # Fallback: Return the current page URL (Eluta job page)
            current_url = job_page.url
            console.print(f"[yellow]⚠️ No external apply URL found, using Eluta page: {current_url}[/yellow]")
            return current_url

        except Exception as e:
            console.print(f"[yellow]⚠️ Error finding apply URL: {e}[/yellow]")
            return job_page.url if hasattr(job_page, 'url') else ""

    def _extract_apply_instructions(self, description: str) -> str:
        """
        Extract application instructions from job description.
        """
        # Look for application instruction sections
        instruction_patterns = [
            r'how to apply:(.+?)(?:\n\n|\n[A-Z]|$)',
            r'application process:(.+?)(?:\n\n|\n[A-Z]|$)',
            r'to apply:(.+?)(?:\n\n|\n[A-Z]|$)',
            r'apply by:(.+?)(?:\n\n|\n[A-Z]|$)'
        ]

        for pattern in instruction_patterns:
            match = re.search(pattern, description, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return ""

    def _has_next_page(self, page: Page) -> bool:
        """
        Check if there's a next page available on Eluta.
        Since we know the URL format (pg=X), we can always try the next page.
        """
        try:
            # Check if there are any job results on current page
            # Look for actual job indicators instead of all divs
            job_indicators = page.query_selector_all("a[href*='/job/'], a[href*='/direct/'], div[class*='job']")
            if len(job_indicators) > 5:  # If we found job-related content
                console.print(f"[cyan]📄 Found content on page, assuming more pages exist[/cyan]")
                return True

            # Look for pagination indicators as backup
            pagination_selectors = [
                "a[href*='pg=']",  # Look for page parameter links
                ".pagination",
                ".pager",
                "[class*='page']"
            ]

            for selector in pagination_selectors:
                try:
                    elem = page.query_selector(selector)
                    if elem:
                        console.print(f"[cyan]📄 Found pagination element: {selector}[/cyan]")
                        return True
                except:
                    continue

            console.print(f"[yellow]📄 No clear pagination indicators, will try next page anyway[/yellow]")
            return True  # Always try next page until we hit our limit or find no jobs

        except Exception as e:
            console.print(f"[yellow]⚠️ Error checking pagination: {e}[/yellow]")
            return True  # Default to trying next page

    def _extract_job_details_from_page(self, page: Page) -> Dict:
        """
        Extract basic job details from the current job page.
        This is a simplified version that gets basic info.
        """
        details = {
            "full_description": "",
            "salary": "",
            "job_type": "",
            "apply_instructions": ""
        }

        try:
            # Get the page content
            page_text = page.inner_text()

            # Extract full description (first 1000 chars)
            if len(page_text) > 100:
                details["full_description"] = page_text[:1000] + "..." if len(page_text) > 1000 else page_text

            # Look for salary information
            import re
            salary_patterns = [
                r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?(?:\s*per\s*year|\s*annually|\s*/year)?',
                r'[\d,]+k(?:\s*-\s*[\d,]+k)?(?:\s*per\s*year|\s*annually)?',
                r'salary:?\s*\$?[\d,]+(?:\s*-\s*\$?[\d,]+)?'
            ]

            for pattern in salary_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    details["salary"] = match.group(0)
                    break

            # Look for job type
            job_type_patterns = [
                r'full.?time', r'part.?time', r'contract', r'temporary',
                r'permanent', r'remote', r'hybrid', r'on.?site'
            ]

            for pattern in job_type_patterns:
                if re.search(pattern, page_text, re.IGNORECASE):
                    details["job_type"] = re.search(pattern, page_text, re.IGNORECASE).group(0)
                    break

        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting job details: {e}[/yellow]")

        return details

    def _find_external_apply_url(self, page: Page) -> Optional[str]:
        """
        Find the real external application URL on the job details page.
        This looks for direct links to company career pages, ATS systems, etc.
        """
        try:
            console.print(f"[cyan]🔍 Looking for external apply URL on job page...[/cyan]")

            # Strategy 1: Look for direct external URLs in links
            external_url_selectors = [
                # Specific ATS systems
                "a[href*='workday.com']",
                "a[href*='myworkday.com']",
                "a[href*='wd1.myworkdayjobs.com']",
                "a[href*='greenhouse.io']",
                "a[href*='boards.greenhouse.io']",
                "a[href*='lever.co']",
                "a[href*='jobs.lever.co']",
                "a[href*='icims.com']",
                "a[href*='bamboohr.com']",
                "a[href*='smartrecruiters.com']",
                "a[href*='jobvite.com']",
                "a[href*='ultipro.com']",
                "a[href*='successfactors.com']",
                "a[href*='taleo.net']",

                # Generic external job sites
                "a[href*='careers.']",
                "a[href*='jobs.']",
                "a[href*='/careers/']",
                "a[href*='/jobs/']",
                "a[href*='/apply']",

                # Apply buttons with external links
                "a:has-text('Apply Now')",
                "a:has-text('Apply')",
                "button:has-text('Apply')",

                # Any external HTTP link (not eluta.ca)
                "a[href^='http']:not([href*='eluta.ca'])"
            ]

            found_urls = []

            for selector in external_url_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    for elem in elements:
                        href = elem.get_attribute('href')
                        if href and href not in ['#', '#!', 'javascript:void(0)', 'javascript:']:
                            # Clean up the URL
                            if href.startswith('//'):
                                href = f"https:{href}"
                            elif href.startswith('/') and not href.startswith('//'):
                                continue  # Skip relative URLs to eluta.ca

                            # Validate it's an external URL AND NOT a review/employer page
                            if (href.startswith('http') and
                                'eluta.ca' not in href and
                                href not in found_urls):

                                # CRITICAL: Exclude review and employer page URLs
                                if any(bad_domain in href for bad_domain in [
                                    'canadastop100.com', 'reviews.', 'top-employer', 'employer-review',
                                    'company-profile', 'employer-profile', 'about-employer', 'top100'
                                ]):
                                    link_text = elem.inner_text().strip()
                                    console.print(f"[red]❌ EXCLUDED review/employer URL: {href} (text: '{link_text}')[/red]")
                                    continue

                                # This is a valid external job application URL
                                found_urls.append(href)
                                link_text = elem.inner_text().strip()
                                console.print(f"[bold green]🎯 Found valid external apply URL: {href} (text: '{link_text}')[/bold green]")
                except Exception:
                    continue

            # Return the first valid external URL found (double-check it's not a review URL)
            if found_urls:
                for url in found_urls:
                    # Final validation - ensure it's not a review URL
                    if not any(bad_domain in url for bad_domain in [
                        'canadastop100.com', 'reviews.', 'top-employer', 'employer-review',
                        'company-profile', 'employer-profile', 'about-employer', 'top100'
                    ]):
                        console.print(f"[bold green]✅ Returning validated external apply URL: {url}[/bold green]")
                        return url
                    else:
                        console.print(f"[red]❌ Final validation failed for URL: {url}[/red]")

                console.print(f"[red]❌ All found URLs were review/employer pages, returning None[/red]")
                return None

            # Strategy 2: Look for clickable elements that might trigger navigation
            console.print("[yellow]⚠️ No direct external URLs found, looking for clickable apply elements...[/yellow]")

            clickable_selectors = [
                "button:has-text('Apply')",
                "button:has-text('View Job')",
                "button:has-text('View Details')",
                "a:has-text('Apply Now')",
                "a:has-text('Apply')",
                ".apply-button",
                ".apply-link",
                "[class*='apply'][class*='button']",
                "[class*='apply'][class*='link']"
            ]

            for selector in clickable_selectors:
                try:
                    elem = page.query_selector(selector)
                    if elem and elem.is_visible():
                        console.print(f"[cyan]🔄 Found clickable apply element: {selector}[/cyan]")

                        # Try to click and capture any popup or navigation
                        try:
                            with page.expect_popup(timeout=3000) as popup_info:
                                elem.click()

                            popup = popup_info.value
                            if popup:
                                popup_url = popup.url
                                popup.close()
                                if 'eluta.ca' not in popup_url:
                                    console.print(f"[bold green]✅ Found external URL via popup: {popup_url}[/bold green]")
                                    return popup_url
                        except:
                            # No popup, check if page navigated
                            page.wait_for_timeout(2000)
                            current_url = page.url
                            if 'eluta.ca' not in current_url:
                                console.print(f"[bold green]✅ Found external URL via navigation: {current_url}[/bold green]")
                                return current_url

                except Exception:
                    continue

            console.print(f"[yellow]⚠️ No external apply URL found on job page[/yellow]")
            return None

        except Exception as e:
            console.print(f"[yellow]⚠️ Error finding external apply URL: {e}[/yellow]")
            return None
