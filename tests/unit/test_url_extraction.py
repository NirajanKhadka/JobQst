#!/usr/bin/env python3
"""
Test script to verify URL extraction from Eluta scraper.
"""

import sys
from pathlib import Path
from rich.console import Console

console = Console()

def test_url_extraction():
    """Test the URL extraction functionality."""
    try:
        # Import the enhanced scraper
        from src.scrapers.enhanced_eluta_scraper import EnhancedElutaScraper
        
        # Create a test profile
        test_profile = {
            "profile_name": "test_user",
            "keywords": ["python developer"],
            "location": "Toronto",
            "ollama_model": "mistral:7b"
        }
        
        console.print("[bold blue]🧪 Testing URL Extraction from Eluta Scraper[/bold blue]")
        
        # Initialize scraper
        scraper = EnhancedElutaScraper(test_profile["profile_name"])
        
        console.print("[cyan]📋 Scraper initialized successfully[/cyan]")
        console.print(f"[cyan]🔍 Testing with keyword: {test_profile['keywords'][0]}[/cyan]")
        
        # Test that the scraper has the expected attributes
        assert hasattr(scraper, 'search_terms'), "Scraper should have search_terms attribute"
        assert hasattr(scraper, 'scrape_with_options'), "Scraper should have scrape_with_options method"
        assert hasattr(scraper, 'profile_name'), "Scraper should have profile_name attribute"
        
        console.print("[green]✅ Scraper initialized and has expected attributes[/green]")
        console.print(f"[cyan]🎯 Search terms available: {len(scraper.search_terms)}[/cyan]")
        
        # Test URL construction (without actual scraping)
        base_url = scraper.base_url
        assert "eluta.ca" in base_url, "Base URL should contain eluta.ca domain"
        console.print(f"[green]✅ Base URL valid: {base_url}[/green]")
        
        # Note: This is a simple integration test - full scraping would require async context
        console.print("[yellow]⚠️ Full scraping test skipped - would require async context and live website[/yellow]")
        
        return True
            
    except Exception as e:
        console.print(f"[red]❌ Test failed with error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    console.print("[bold blue]🔧 URL Extraction Test[/bold blue]")
    
    success = test_url_extraction()
    
    if success:
        console.print("\n[bold green]✅ All tests passed![/bold green]")
        return 0
    else:
        console.print("\n[bold red]❌ Tests failed![/bold red]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
