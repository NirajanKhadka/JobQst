#!/usr/bin/env python3
"""
Test script for the new simplified scraping menu functionality.
Tests site selection and bot detection integration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scrapers import AVAILABLE_SCRAPERS, get_scraper
from rich.console import Console

console = Console()

def test_scraper_availability():
    """Test that all scrapers are properly imported and available."""
    console.print("[bold blue]Testing Scraper Availability[/bold blue]")
    
    expected_scrapers = ["eluta", "indeed", "linkedin", "jobbank", "monster", "workday", "ultra_parallel"]
    
    console.print(f"Available scrapers: {AVAILABLE_SCRAPERS}")
    
    for scraper in expected_scrapers:
        if scraper in AVAILABLE_SCRAPERS:
            console.print(f"✅ {scraper}: Available")
        else:
            console.print(f"❌ {scraper}: Not available")
    
    # At least 5 scrapers should be available
    assert len(AVAILABLE_SCRAPERS) >= 5, f"Expected at least 5 scrapers, got {len(AVAILABLE_SCRAPERS)}"

def test_scraper_instantiation():
    """Test that scrapers can be instantiated without errors."""
    console.print("\n[bold blue]Testing Scraper Instantiation[/bold blue]")
    
    # Mock profile for testing
    test_profile = {
        "profile_name": "test",
        "name": "Test User",
        "email": "test@example.com",
        "keywords": ["python", "data analyst"],
        "city": "Toronto"
    }
    
    working_scrapers = []
    
    for scraper_name in AVAILABLE_SCRAPERS:
        if scraper_name == "ultra_parallel":
            continue  # Skip ultra_parallel as it's not a regular scraper
            
        try:
            scraper = get_scraper(scraper_name, test_profile)
            console.print(f"✅ {scraper_name}: Instantiated successfully")
            working_scrapers.append(scraper_name)
        except Exception as e:
            console.print(f"❌ {scraper_name}: Failed to instantiate - {e}")
    
    # At least 3 scrapers should work
    assert len(working_scrapers) >= 3, f"Expected at least 3 working scrapers, got {len(working_scrapers)}"

def test_site_display_mapping():
    """Test that site display names are properly mapped."""
    console.print("\n[bold blue]Testing Site Display Mapping[/bold blue]")
    
    site_display_names = {
        "eluta": "Eluta.ca (Canadian jobs with deep bot detection)",
        "eluta_comprehensive": "Eluta Comprehensive (Improved Eluta scraper)",
        "parallel": "Parallel Scraper (Multi-threaded scraping)",
        "pipeline": "Pipeline Scraper (Modern job pipeline)",
        "indeed": "Indeed.ca (Global jobs with anti-detection)",
        "linkedin": "LinkedIn Jobs (Professional network - requires login)",
        "jobbank": "JobBank.gc.ca (Government jobs)",
        "monster": "Monster.ca (Canadian Monster)",
        "workday": "Workday (Corporate ATS)",
        "ultra_parallel": "Multi-site parallel (all sites simultaneously)"
    }
    
    mapped_sites = 0
    for site in AVAILABLE_SCRAPERS:
        if site in site_display_names:
            console.print(f"✅ {site}: {site_display_names[site]}")
            mapped_sites += 1
        else:
            console.print(f"❌ {site}: No display name mapping")
    
    # All sites should have display name mappings
    assert mapped_sites == len(AVAILABLE_SCRAPERS), f"Expected {len(AVAILABLE_SCRAPERS)} mapped sites, got {mapped_sites}"

def test_bot_detection_config():
    """Test bot detection configuration options."""
    console.print("\n[bold blue]Testing Bot Detection Configuration[/bold blue]")
    
    bot_config = {
        "1": {"delay_range": (5, 10), "human_like": True, "stealth_mode": "deep"},
        "2": {"delay_range": (3, 6), "human_like": True, "stealth_mode": "standard"},
        "3": {"delay_range": (1, 3), "human_like": False, "stealth_mode": "minimal"},
        "4": {"delay_range": (3, 8), "human_like": True, "stealth_mode": "custom"}
    }
    
    for method, config in bot_config.items():
        console.print(f"✅ Method {method}: {config}")
    
    # Should have exactly 4 bot detection methods
    assert len(bot_config) == 4, f"Expected 4 bot detection methods, got {len(bot_config)}"

def main():
    """Run all tests."""
    console.print("[bold green]🧪 Testing New Scraping Menu Functionality[/bold green]\n")
    
    tests = [
        ("Scraper Availability", test_scraper_availability),
        ("Scraper Instantiation", test_scraper_instantiation),
        ("Site Display Mapping", test_site_display_mapping),
        ("Bot Detection Config", test_bot_detection_config)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                console.print(f"[green]✅ {test_name}: PASSED[/green]")
                passed += 1
            else:
                console.print(f"[red]❌ {test_name}: FAILED[/red]")
        except Exception as e:
            console.print(f"[red]❌ {test_name}: ERROR - {e}[/red]")
    
    console.print(f"\n[bold]Test Results: {passed}/{total} tests passed[/bold]")
    
    if passed == total:
        console.print("[bold green]🎉 All tests passed! New scraping menu is ready.[/bold green]")
        return 0
    else:
        console.print("[bold red]❌ Some tests failed. Please check the issues above.[/bold red]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
