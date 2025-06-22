#!/usr/bin/env python3
"""
Anti-Bot Eluta Scraper
Specialized scraper that handles bot detection gracefully and opens browser for manual verification.
"""

import time
import random
from typing import Dict, List, Generator, Optional
from playwright.sync_api import sync_playwright, Page, BrowserContext
from rich.console import Console
from rich.prompt import Confirm

from .eluta_enhanced import ElutaEnhancedScraper

console = Console()

class AntiBotElutaScraper(ElutaEnhancedScraper):
    """
    Enhanced Eluta scraper with advanced bot detection handling.
    
    Features:
    - Automatic bot detection
    - Manual verification support
    - Human-like behavior patterns
    - Graceful fallback to visible browser
    """
    
    def __init__(self, profile: Dict, **kwargs):
        super().__init__(profile, **kwargs)
        
        # Anti-bot specific settings
        self.verification_mode = False
        self.visible_browser = None
        self.visible_context = None
        
        # More conservative delays to avoid detection
        self.rate_limit_delay = (5, 12)  # Slower delays
        self.page_delay = (3, 7)  # Longer page delays
        self.search_delay = (2, 5)  # Longer search delays
        
        console.print("[bold green]🛡️ Anti-Bot Eluta Scraper initialized[/bold green]")
        console.print("[cyan]Will automatically handle verification challenges[/cyan]")
    
    def scrape_jobs(self) -> Generator[Dict, None, None]:
        """
        Enhanced scraping with automatic bot detection handling.
        """
        console.print(f"\n[bold blue]🛡️ Starting Anti-Bot Scraping Session[/bold blue]")
        console.print("[cyan]Will switch to manual mode if verification is needed[/cyan]")
        
        try:
            # Start with headless mode
            yield from self._scrape_with_detection()
            
        except Exception as e:
            console.print(f"[red]❌ Anti-bot scraping error: {e}[/red]")
        finally:
            self._cleanup_visible_browser()
    
    def _scrape_with_detection(self) -> Generator[Dict, None, None]:
        """Scrape with continuous bot detection monitoring."""
        
        page = self.browser_context.new_page()
        self._setup_enhanced_stealth(page)
        
        try:
            for keyword_index, keyword in enumerate(self.keywords, 1):
                console.print(f"\n[bold blue]🔍 Keyword {keyword_index}/{len(self.keywords)}: '{keyword}'[/bold blue]")
                
                # Check for bot detection before each keyword
                if self._is_verification_needed(page):
                    console.print("[yellow]🤖 Verification needed, switching to manual mode[/yellow]")
                    
                    # Switch to visible browser for verification
                    if self._switch_to_manual_mode(page, keyword):
                        console.print("[green]✅ Manual verification completed, continuing[/green]")
                        # Continue with visible browser
                        page = self.visible_context.new_page()
                    else:
                        console.print("[red]❌ Manual verification failed, stopping[/red]")
                        break
                
                # Scrape this keyword
                keyword_jobs = 0
                for job in self._search_keyword_safe(page, keyword):
                    keyword_jobs += 1
                    yield job
                    
                    # Check for bot detection after every few jobs
                    if keyword_jobs % 5 == 0:
                        if self._is_verification_needed(page):
                            console.print("[yellow]🤖 Verification needed mid-scraping[/yellow]")
                            if not self._handle_mid_scraping_verification(page):
                                console.print("[red]❌ Could not resolve verification[/red]")
                                return
                
                console.print(f"[green]✅ Completed '{keyword}': {keyword_jobs} jobs[/green]")
                
                # Human-like delay between keywords
                delay = random.uniform(8, 15)
                console.print(f"[cyan]⏳ Resting {delay:.1f}s before next keyword...[/cyan]")
                time.sleep(delay)
                
        finally:
            try:
                page.close()
            except:
                pass
    
    def _setup_enhanced_stealth(self, page: Page) -> None:
        """Setup enhanced stealth mode with more human-like behavior."""
        try:
            # Enhanced stealth script
            enhanced_stealth = """
            // Remove all automation indicators
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Override plugins with realistic values
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                    {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                    {name: 'Native Client', filename: 'internal-nacl-plugin'}
                ],
            });
            
            // Realistic language settings
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'en-CA'],
            });
            
            // Add realistic chrome object
            window.chrome = {
                runtime: {
                    onConnect: null,
                    onMessage: null,
                },
                app: {
                    isInstalled: false,
                },
                csi: function() { return {}; },
                loadTimes: function() { 
                    return {
                        requestTime: Date.now() / 1000,
                        startLoadTime: Date.now() / 1000,
                        commitLoadTime: Date.now() / 1000,
                        finishDocumentLoadTime: Date.now() / 1000,
                        finishLoadTime: Date.now() / 1000,
                        firstPaintTime: Date.now() / 1000,
                        firstPaintAfterLoadTime: 0,
                        navigationType: 'Other'
                    };
                }
            };
            
            // Override permissions API
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Add realistic screen properties
            Object.defineProperty(screen, 'availTop', { get: () => 0 });
            Object.defineProperty(screen, 'availLeft', { get: () => 0 });
            """
            
            page.add_init_script(enhanced_stealth)
            
            # Set realistic viewport
            page.set_viewport_size({"width": 1366, "height": 768})
            
            # Add realistic headers
            page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9,en-CA;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            })
            
            console.print("[green]✅ Enhanced stealth mode configured[/green]")
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not setup enhanced stealth: {e}[/yellow]")
    
    def _is_verification_needed(self, page: Page) -> bool:
        """Enhanced bot detection with more indicators."""
        try:
            # Extended list of bot detection indicators
            verification_indicators = [
                # CAPTCHA
                ".captcha", "#captcha", ".g-recaptcha", ".h-captcha",
                "iframe[src*='recaptcha']", "iframe[src*='hcaptcha']", "iframe[src*='captcha']",
                
                # Verification
                ".verification", "#verification", "[data-testid*='verification']",
                ".verify", "#verify", "[data-testid*='verify']",
                
                # Challenge
                ".challenge", "#challenge", "[data-testid*='challenge']",
                ".security-check", "#security-check",
                
                # Cloudflare
                ".cf-browser-verification", "#cf-wrapper", ".cf-challenge",
                ".cf-checking", ".cf-spinner",
                
                # Bot detection
                ".bot-detection", "#bot-check", "[data-testid*='bot']",
                ".anti-bot", "#anti-bot",
                
                # Rate limiting
                ".rate-limit", "#rate-limit", ".too-many-requests",
                
                # Access denied
                ".access-denied", "#access-denied", ".forbidden"
            ]
            
            for indicator in verification_indicators:
                try:
                    if page.is_visible(indicator, timeout=500):
                        console.print(f"[yellow]🤖 Verification indicator found: {indicator}[/yellow]")
                        return True
                except:
                    continue
            
            # Check page title and content
            try:
                title = page.title().lower()
                verification_keywords = [
                    'verification', 'captcha', 'challenge', 'bot', 'security',
                    'access denied', 'forbidden', 'rate limit', 'too many requests'
                ]
                if any(keyword in title for keyword in verification_keywords):
                    console.print(f"[yellow]🤖 Verification in title: {title}[/yellow]")
                    return True
            except:
                pass
            
            # Check for suspicious page content
            try:
                page_text = page.inner_text('body').lower()
                verification_phrases = [
                    'verify you are human', 'prove you are not a robot',
                    'security check', 'access denied', 'too many requests',
                    'rate limited', 'suspicious activity', 'automated traffic'
                ]
                if any(phrase in page_text for phrase in verification_phrases):
                    console.print("[yellow]🤖 Verification phrase in content[/yellow]")
                    return True
            except:
                pass
            
            return False
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Error checking verification: {e}[/yellow]")
            return False
    
    def _switch_to_manual_mode(self, current_page: Page, keyword: str) -> bool:
        """Switch to visible browser for manual verification."""
        try:
            console.print("\n[bold yellow]🚨 SWITCHING TO MANUAL MODE[/bold yellow]")
            console.print("[cyan]Opening visible browser for verification...[/cyan]")
            
            # Get current URL
            current_url = current_page.url
            
            # Create visible browser
            with sync_playwright() as p:
                self.visible_browser = p.chromium.launch(
                    headless=False,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-infobars',
                        '--start-maximized'
                    ]
                )
                self.visible_context = self.visible_browser.new_context(
                    viewport={'width': 1366, 'height': 768},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                visible_page = self.visible_context.new_page()
                
                # Navigate to the problematic URL
                visible_page.goto(current_url)
                
                console.print(f"\n[bold cyan]🌐 Browser opened at: {current_url}[/bold cyan]")
                console.print("[yellow]Please complete any verification/CAPTCHA in the browser.[/yellow]")
                console.print("[yellow]Once you can see job listings, press Enter to continue...[/yellow]")
                
                # Wait for user confirmation
                input()
                
                # Verify that verification was successful
                if not self._is_verification_needed(visible_page):
                    console.print("[green]✅ Verification successful![/green]")
                    
                    # Copy session data
                    cookies = self.visible_context.cookies()
                    self.browser_context.add_cookies(cookies)
                    
                    return True
                else:
                    console.print("[red]❌ Verification still required[/red]")
                    return False
            
        except Exception as e:
            console.print(f"[red]❌ Error switching to manual mode: {e}[/red]")
            return False
    
    def _handle_mid_scraping_verification(self, page: Page) -> bool:
        """Handle verification that appears during scraping."""
        console.print("[yellow]🤖 Mid-scraping verification detected[/yellow]")
        
        # Ask user if they want to continue with manual verification
        if Confirm.ask("Open browser for manual verification?"):
            return self._switch_to_manual_mode(page, "current")
        else:
            console.print("[yellow]⚠️ Skipping verification, scraping may be limited[/yellow]")
            return False
    
    def _search_keyword_safe(self, page: Page, keyword: str) -> Generator[Dict, None, None]:
        """Safe keyword search with verification handling."""
        try:
            # Use the parent class method but with additional safety checks
            for job in self._search_keyword(page, keyword):
                # Check for verification after each job
                if random.random() < 0.1:  # 10% chance to check
                    if self._is_verification_needed(page):
                        console.print("[yellow]🤖 Verification needed during job extraction[/yellow]")
                        if not self._handle_mid_scraping_verification(page):
                            return
                
                yield job
                
                # Human-like delay between jobs
                time.sleep(random.uniform(1, 3))
                
        except Exception as e:
            console.print(f"[red]❌ Error in safe keyword search: {e}[/red]")
    
    def _cleanup_visible_browser(self):
        """Clean up visible browser resources."""
        try:
            if self.visible_browser and self.visible_browser.is_connected():
                self.visible_browser.close()
                console.print("[green]✅ Visible browser closed[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Error closing visible browser: {e}[/yellow]")
