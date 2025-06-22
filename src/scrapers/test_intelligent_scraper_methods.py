#!/usr/bin/env python3
"""
Test script to verify IntelligentJobScraper class methods.
"""

from rich.console import Console
from rich.panel import Panel

console = Console()

def test_intelligent_scraper_methods():
    """Test that IntelligentJobScraper has the required methods."""
    console.print(Panel("🧪 Testing IntelligentJobScraper Methods", style="bold blue"))
    
    try:
        from intelligent_scraper import IntelligentJobScraper
        
        # Create instance
        scraper = IntelligentJobScraper("Nirajan")
        
        # Test methods
        methods_to_test = [
            'run_scraping',
            'scrape_with_enhanced_scrapers', 
            'get_scraper_for_site'
        ]
        
        results = []
        for method_name in methods_to_test:
            if hasattr(scraper, method_name):
                console.print(f"[green]✅ {method_name}: Method found[/green]")
                results.append((method_name, True))
            else:
                console.print(f"[red]❌ {method_name}: Method missing[/red]")
                results.append((method_name, False))
        
        # Test method signatures
        console.print("\n[cyan]Testing method signatures...[/cyan]")
        
        import inspect
        
        if hasattr(scraper, 'run_scraping'):
            sig = inspect.signature(scraper.run_scraping)
            params = list(sig.parameters.keys())
            console.print(f"[green]✅ run_scraping signature: {params}[/green]")
        
        if hasattr(scraper, 'scrape_with_enhanced_scrapers'):
            sig = inspect.signature(scraper.scrape_with_enhanced_scrapers)
            params = list(sig.parameters.keys())
            console.print(f"[green]✅ scrape_with_enhanced_scrapers signature: {params}[/green]")
        
        if hasattr(scraper, 'get_scraper_for_site'):
            sig = inspect.signature(scraper.get_scraper_for_site)
            params = list(sig.parameters.keys())
            console.print(f"[green]✅ get_scraper_for_site signature: {params}[/green]")
        
        # Summary
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        console.print(f"\n[bold]Results: {passed}/{total} methods found[/bold]")
        
        if passed == total:
            console.print("[bold green]🎉 All IntelligentJobScraper methods implemented![/bold green]")
            return True
        else:
            console.print(f"[bold yellow]⚠️ {total - passed} method(s) still missing[/bold yellow]")
            return False
            
    except Exception as e:
        console.print(f"[red]❌ Error testing IntelligentJobScraper methods: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    success = test_intelligent_scraper_methods()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
