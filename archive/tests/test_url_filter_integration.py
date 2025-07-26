#!/usr/bin/env python3
"""
Test URL Filter Integration
Verify that the URL filter is working correctly in the scraper
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.simple_url_filter import get_simple_url_filter
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def test_url_filter():
    """Test the URL filter with various job URLs."""
    console.print(Panel.fit("[bold blue]Testing URL Filter Integration[/bold blue]", title="URL Filter Test"))
    
    url_filter = get_simple_url_filter()
    
    # Test URLs - mix of valid and invalid
    test_urls = [
        # Valid URLs
        ("https://jobs.bombardier.com/job/Dorval-Analyst%2C-Data-%26-Business-Intelligence-Québ-H4S-1Y9/1220672601", "Valid Bombardier URL"),
        ("https://cibc.wd3.myworkdayjobs.com/en-US/search/job/Toronto-ON/Sr-AI-Scientist--Advanced-Analytics-and-AI_2516129", "Valid CIBC Workday URL"),
        ("https://jobs.lever.co/mistplay/df64833b-21a5-4a18-9675-3915369b8f2f", "Valid Lever URL"),
        ("https://job-boards.greenhouse.io/geotab/jobs/4568956008", "Valid Greenhouse URL"),
        
        # Invalid URLs (should be filtered out)
        ("https://www.eluta.ca/job/1", "Broken Eluta URL #1"),
        ("https://www.eluta.ca/job/2", "Broken Eluta URL #2"),
        ("https://www.eluta.ca/hosted/nmqwk/cost-control-specialist", "Eluta Hosted URL"),
        ("https://example.com", "Too short URL"),
        ("https://test.com/", "Just domain with slash"),
    ]
    
    # Create results table
    results_table = Table(title="URL Filter Test Results")
    results_table.add_column("URL", style="cyan", max_width=50)
    results_table.add_column("Description", style="yellow")
    results_table.add_column("Valid", style="green")
    results_table.add_column("Reason", style="red")
    
    valid_count = 0
    invalid_count = 0
    
    for url, description in test_urls:
        is_valid = url_filter.is_valid_job_url(url)
        
        if is_valid:
            valid_count += 1
            results_table.add_row(
                url[:47] + "..." if len(url) > 50 else url,
                description,
                "✅ PASS",
                ""
            )
        else:
            invalid_count += 1
            reason = url_filter.get_invalid_reason(url)
            results_table.add_row(
                url[:47] + "..." if len(url) > 50 else url,
                description,
                "❌ FAIL",
                reason
            )
    
    console.print(results_table)
    
    # Summary
    console.print(f"\n[bold]Test Summary:[/bold]")
    console.print(f"[green]✅ Valid URLs: {valid_count}[/green]")
    console.print(f"[red]❌ Invalid URLs: {invalid_count}[/red]")
    
    # Expected results check
    expected_valid = 4  # Bombardier, CIBC, Lever, Greenhouse
    expected_invalid = 5  # 3 Eluta + 2 short URLs
    
    if valid_count == expected_valid and invalid_count == expected_invalid:
        console.print(f"[bold green]🎉 All tests passed! Filter working correctly.[/bold green]")
        return True
    else:
        console.print(f"[bold red]❌ Test failed! Expected {expected_valid} valid, {expected_invalid} invalid[/bold red]")
        return False

def test_scraper_integration():
    """Test that the scraper has the URL filter integrated."""
    console.print(Panel.fit("[bold blue]Testing Scraper Integration[/bold blue]", title="Integration Test"))
    
    try:
        from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper
        
        # Initialize scraper
        scraper = ComprehensiveElutaScraper("Nirajan")
        
        # Check if URL filter is available
        if hasattr(scraper, 'url_filter'):
            console.print("[green]✅ URL filter successfully integrated in scraper[/green]")
            
            # Test the filter
            test_url = "https://www.eluta.ca/job/1"
            is_valid = scraper.url_filter.is_valid_job_url(test_url)
            
            if not is_valid:
                console.print(f"[green]✅ Scraper correctly identifies broken URL as invalid[/green]")
                return True
            else:
                console.print(f"[red]❌ Scraper failed to identify broken URL as invalid[/red]")
                return False
        else:
            console.print("[red]❌ URL filter not found in scraper[/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]❌ Error testing scraper integration: {e}[/red]")
        return False

def main():
    """Main test function."""
    console.print(Panel.fit(
        "[bold blue]URL Filter Integration Test[/bold blue]\n\n"
        "This test verifies:\n"
        "1. URL filter correctly identifies valid/invalid URLs\n"
        "2. Scraper has URL filter integrated\n"
        "3. Broken Eluta URLs are properly filtered out\n\n"
        "Expected: 4 valid URLs, 5 invalid URLs",
        title="Test Overview"
    ))
    
    # Run tests
    filter_test_passed = test_url_filter()
    integration_test_passed = test_scraper_integration()
    
    # Final result
    if filter_test_passed and integration_test_passed:
        console.print(Panel.fit(
            "[bold green]🎉 ALL TESTS PASSED! 🎉[/bold green]\n\n"
            "✅ URL filter working correctly\n"
            "✅ Scraper integration successful\n"
            "✅ Broken Eluta URLs will be filtered out\n\n"
            "The scraper is now ready for reliable operation!",
            title="SUCCESS"
        ))
    else:
        console.print(Panel.fit(
            "[bold red]❌ SOME TESTS FAILED[/bold red]\n\n"
            "Please check the integration and fix any issues.",
            title="FAILURE"
        ))

if __name__ == "__main__":
    main()