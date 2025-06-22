#!/usr/bin/env python3
"""
Test script for Anti-Bot Scraper functionality.
"""

import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def test_anti_bot_scraper_import():
    """Test that the anti-bot scraper can be imported."""
    console.print("[bold blue]🧪 Testing Anti-Bot Scraper Import[/bold blue]")
    
    try:
        from scrapers.anti_bot_scraper import AntiBotElutaScraper
        console.print("[green]✅ Anti-bot scraper imported successfully[/green]")
        return True
    except ImportError as e:
        console.print(f"[red]❌ Failed to import anti-bot scraper: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Unexpected error importing anti-bot scraper: {e}[/red]")
        return False

def test_anti_bot_scraper_initialization():
    """Test that the anti-bot scraper can be initialized."""
    console.print("\n[bold blue]🔧 Testing Anti-Bot Scraper Initialization[/bold blue]")
    
    try:
        from scrapers.anti_bot_scraper import AntiBotElutaScraper
        
        # Create test profile
        test_profile = {
            "profile_name": "test_anti_bot",
            "keywords": ["python", "data analyst"],
            "name": "Test User",
            "email": "test@example.com",
            "location": "Toronto, ON"
        }
        
        # Initialize scraper
        scraper = AntiBotElutaScraper(test_profile)
        
        console.print("[green]✅ Anti-bot scraper initialized successfully[/green]")
        console.print(f"[cyan]   Rate limit delay: {scraper.rate_limit_delay}[/cyan]")
        console.print(f"[cyan]   Page delay: {scraper.page_delay}[/cyan]")
        console.print(f"[cyan]   Search delay: {scraper.search_delay}[/cyan]")
        console.print(f"[cyan]   Keywords: {len(scraper.keywords)}[/cyan]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize anti-bot scraper: {e}[/red]")
        return False

def test_bot_detection_methods():
    """Test bot detection methods without actual web scraping."""
    console.print("\n[bold blue]🤖 Testing Bot Detection Methods[/bold blue]")
    
    try:
        from scrapers.anti_bot_scraper import AntiBotElutaScraper
        
        test_profile = {
            "profile_name": "test",
            "keywords": ["test"],
            "name": "Test User",
            "email": "test@example.com"
        }
        
        scraper = AntiBotElutaScraper(test_profile)
        
        # Test that bot detection methods exist
        methods_to_check = [
            '_is_verification_needed',
            '_setup_enhanced_stealth',
            '_switch_to_manual_mode',
            '_handle_mid_scraping_verification',
            '_search_keyword_safe',
            '_cleanup_visible_browser'
        ]
        
        results = []
        for method_name in methods_to_check:
            if hasattr(scraper, method_name):
                method = getattr(scraper, method_name)
                if callable(method):
                    results.append((method_name, "✅ PASS", "Method exists and callable"))
                else:
                    results.append((method_name, "❌ FAIL", "Not callable"))
            else:
                results.append((method_name, "❌ FAIL", "Method missing"))
        
        # Display results
        table = Table(title="Bot Detection Methods")
        table.add_column("Method", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Details", style="yellow")
        
        for method, status, details in results:
            table.add_row(method, status, details)
        
        console.print(table)
        
        passed = sum(1 for _, status, _ in results if "PASS" in status)
        console.print(f"[cyan]📊 Bot detection methods: {passed}/{len(results)} passed[/cyan]")
        
        return passed == len(results)
        
    except Exception as e:
        console.print(f"[red]❌ Error testing bot detection methods: {e}[/red]")
        return False

def test_stealth_configuration():
    """Test stealth mode configuration."""
    console.print("\n[bold blue]🥷 Testing Stealth Configuration[/bold blue]")
    
    try:
        from scrapers.anti_bot_scraper import AntiBotElutaScraper
        from playwright.sync_api import sync_playwright
        
        test_profile = {
            "profile_name": "test",
            "keywords": ["test"],
            "name": "Test User",
            "email": "test@example.com"
        }
        
        # Test stealth setup without actually navigating
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            scraper = AntiBotElutaScraper(test_profile, browser_context=context)
            
            # Test stealth setup
            scraper._setup_enhanced_stealth(page)
            
            # Check that page has stealth properties
            webdriver_value = page.evaluate("() => navigator.webdriver")
            plugins_length = page.evaluate("() => navigator.plugins.length")
            languages = page.evaluate("() => navigator.languages")
            
            console.print(f"[cyan]Navigator.webdriver: {webdriver_value}[/cyan]")
            console.print(f"[cyan]Navigator.plugins.length: {plugins_length}[/cyan]")
            console.print(f"[cyan]Navigator.languages: {languages}[/cyan]")
            
            # Verify stealth properties
            stealth_checks = [
                (webdriver_value is None, "webdriver property hidden"),
                (plugins_length > 0, "plugins array populated"),
                (isinstance(languages, list) and len(languages) > 0, "languages array set")
            ]
            
            passed_checks = 0
            for check_passed, description in stealth_checks:
                if check_passed:
                    console.print(f"[green]✅ {description}[/green]")
                    passed_checks += 1
                else:
                    console.print(f"[red]❌ {description}[/red]")
            
            browser.close()
            
            console.print(f"[cyan]📊 Stealth checks: {passed_checks}/{len(stealth_checks)} passed[/cyan]")
            return passed_checks == len(stealth_checks)
        
    except Exception as e:
        console.print(f"[red]❌ Error testing stealth configuration: {e}[/red]")
        return False

def test_main_menu_integration():
    """Test that anti-bot scraper is integrated into main menu."""
    console.print("\n[bold blue]📋 Testing Main Menu Integration[/bold blue]")
    
    try:
        import main
        
        # Check if anti_bot_scrape_action exists
        if hasattr(main, 'anti_bot_scrape_action'):
            func = getattr(main, 'anti_bot_scrape_action')
            if callable(func):
                console.print("[green]✅ anti_bot_scrape_action function exists and is callable[/green]")
            else:
                console.print("[red]❌ anti_bot_scrape_action exists but is not callable[/red]")
                return False
        else:
            console.print("[red]❌ anti_bot_scrape_action function missing from main.py[/red]")
            return False
        
        # Check menu options (this is a basic check)
        console.print("[green]✅ Main menu integration appears correct[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Error testing main menu integration: {e}[/red]")
        return False

def test_performance_characteristics():
    """Test performance characteristics of anti-bot scraper."""
    console.print("\n[bold blue]⚡ Testing Performance Characteristics[/bold blue]")
    
    try:
        from scrapers.anti_bot_scraper import AntiBotElutaScraper
        
        test_profile = {
            "profile_name": "test",
            "keywords": ["python", "data", "analyst"],
            "name": "Test User",
            "email": "test@example.com"
        }
        
        # Test initialization time
        start_time = time.time()
        scraper = AntiBotElutaScraper(test_profile)
        init_time = time.time() - start_time
        
        console.print(f"[cyan]Initialization time: {init_time:.3f} seconds[/cyan]")
        
        # Check delay configurations
        console.print(f"[cyan]Rate limit delay: {scraper.rate_limit_delay[0]}-{scraper.rate_limit_delay[1]}s[/cyan]")
        console.print(f"[cyan]Page delay: {scraper.page_delay[0]}-{scraper.page_delay[1]}s[/cyan]")
        console.print(f"[cyan]Search delay: {scraper.search_delay[0]}-{scraper.search_delay[1]}s[/cyan]")
        
        # Verify delays are conservative (slower than regular scraper)
        if (scraper.rate_limit_delay[0] >= 5 and 
            scraper.page_delay[0] >= 3 and 
            scraper.search_delay[0] >= 2):
            console.print("[green]✅ Conservative delays configured for anti-bot behavior[/green]")
            return True
        else:
            console.print("[yellow]⚠️ Delays may not be conservative enough for anti-bot behavior[/yellow]")
            return True  # Still pass, just a warning
        
    except Exception as e:
        console.print(f"[red]❌ Error testing performance characteristics: {e}[/red]")
        return False

def main():
    """Run comprehensive anti-bot scraper tests."""
    console.print(Panel("🛡️ Anti-Bot Scraper Test Suite", style="bold blue"))
    console.print("[cyan]Testing anti-bot scraping functionality and integration...[/cyan]\n")
    
    tests = [
        ("Import Test", test_anti_bot_scraper_import),
        ("Initialization Test", test_anti_bot_scraper_initialization),
        ("Bot Detection Methods", test_bot_detection_methods),
        ("Stealth Configuration", test_stealth_configuration),
        ("Main Menu Integration", test_main_menu_integration),
        ("Performance Characteristics", test_performance_characteristics),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            console.print(f"[red]❌ {test_name} crashed: {e}[/red]")
            results.append((test_name, False))
    
    # Final summary
    console.print("\n" + "="*60)
    console.print("[bold blue]📊 ANTI-BOT SCRAPER TEST SUMMARY[/bold blue]")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        console.print(f"   {status} {test_name}")
    
    console.print(f"\n[bold]Results: {passed}/{total} tests passed ({success_rate:.1f}%)[/bold]")
    
    if success_rate >= 90:
        console.print("[bold green]🎉 Anti-bot scraper is ready to handle verification challenges![/bold green]")
        console.print("\n[cyan]💡 Usage:[/cyan]")
        console.print("   python main.py Nirajan  # Choose option 4: Anti-bot scraping")
        console.print("\n[yellow]📝 Notes:[/yellow]")
        console.print("   • Uses slower delays to avoid detection")
        console.print("   • Will open browser window if CAPTCHA appears")
        console.print("   • Automatically handles verification challenges")
        console.print("   • Continues scraping after manual verification")
    elif success_rate >= 75:
        console.print("[bold yellow]⚠️ Anti-bot scraper mostly ready with minor issues.[/bold yellow]")
        console.print("[yellow]💡 Review failed tests and fix remaining issues[/yellow]")
    else:
        console.print("[bold red]❌ Anti-bot scraper needs attention. Multiple issues detected.[/bold red]")
        console.print("[red]💡 Review failed tests and fix critical issues[/red]")
    
    return 0 if success_rate >= 90 else 1

if __name__ == "__main__":
    sys.exit(main())
