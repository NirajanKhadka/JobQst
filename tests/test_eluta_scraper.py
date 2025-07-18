#!/usr/bin/env python3
"""
Isolated test for Eluta popup scraping logic
This test will help us debug and fix the popup URL extraction failure
"""

import asyncio
import pytest
from rich.console import Console
from playwright.async_api import async_playwright

console = Console()


class ElutaScrapingTester:
    """Dedicated test class for debugging Eluta scraping issues."""
    
    def __init__(self):
        self.test_url = "https://www.eluta.ca/search?q=MySQL&l=&posted=14&pg=1"
        
    async def test_basic_page_load(self):
        """Test 1: Can we load the Eluta search page?"""
        console.print("[bold blue]🧪 Test 1: Basic Page Load[/bold blue]")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(self.test_url, timeout=10000)
                await page.wait_for_load_state("domcontentloaded")
                
                title = await page.title()
                console.print(f"[green]✅ Page loaded successfully: {title}[/green]")
                return True
                
            except Exception as e:
                console.print(f"[red]❌ Page load failed: {e}[/red]")
                return False
            finally:
                await context.close()
                await browser.close()
    
    async def test_job_elements_detection(self):
        """Test 2: Can we find job elements on the page?"""
        console.print("[bold blue]🧪 Test 2: Job Elements Detection[/bold blue]")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(self.test_url, timeout=10000)
                await page.wait_for_load_state("domcontentloaded")
                
                # Try multiple potential selectors
                selectors = [
                    '.organic-job',
                    '.job-listing',
                    '.job-item',
                    '[data-job]',
                    '.result'
                ]
                
                for selector in selectors:
                    elements = await page.query_selector_all(selector)
                    console.print(f"[cyan]Selector '{selector}': {len(elements)} elements[/cyan]")
                    
                    if len(elements) > 0:
                        console.print(f"[green]✅ Found {len(elements)} job elements with '{selector}'[/green]")
                        return selector, elements[0]  # Return first working selector and element
                
                console.print(f"[red]❌ No job elements found with any selector[/red]")
                return None, None
                
            except Exception as e:
                console.print(f"[red]❌ Job detection failed: {e}[/red]")
                return None, None
            finally:
                await context.close()
                await browser.close()
    
    async def test_link_analysis(self):
        """Test 3: Analyze the links within job elements."""
        console.print("[bold blue]🧪 Test 3: Link Analysis in Job Elements[/bold blue]")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(self.test_url, timeout=10000)
                await page.wait_for_load_state("domcontentloaded")
                
                # Get job elements
                job_elements = await page.query_selector_all('.organic-job')
                
                if not job_elements:
                    console.print(f"[red]❌ No job elements found[/red]")
                    return False
                
                console.print(f"[cyan]Found {len(job_elements)} job elements[/cyan]")
                
                # Analyze first job element
                job_element = job_elements[0]
                job_text = await job_element.inner_text()
                console.print(f"[yellow]First job text preview: {job_text[:100]}...[/yellow]")
                
                # Get all links
                links = await job_element.query_selector_all("a")
                console.print(f"[cyan]Found {len(links)} links in first job[/cyan]")
                
                job_links_found = 0
                for i, link in enumerate(links):
                    href = await link.get_attribute("href")
                    text = await link.inner_text() if link else ""
                    
                    console.print(f"[yellow]Link {i+1}:[/yellow]")
                    console.print(f"  href: {href}")
                    console.print(f"  text: {text[:50]}...")
                    
                    # Test different job link patterns
                    patterns = ["job", "apply", "view", "details"]
                    for pattern in patterns:
                        if href and pattern in href.lower():
                            console.print(f"  [green]✅ Contains '{pattern}' - This is likely a job link![/green]")
                            job_links_found += 1
                            break
                    else:
                        console.print(f"  [dim]Not a job link[/dim]")
                
                if job_links_found > 0:
                    console.print(f"[green]✅ Found {job_links_found} potential job links[/green]")
                    return True
                else:
                    console.print(f"[red]❌ No job links found in first job element[/red]")
                    return False
                
            except Exception as e:
                console.print(f"[red]❌ Link analysis failed: {e}[/red]")
                return False
            finally:
                await context.close()
                await browser.close()
    
    async def test_popup_functionality(self):
        """Test 4: Test the actual popup functionality."""
        console.print("[bold blue]🧪 Test 4: Popup Functionality[/bold blue]")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(self.test_url, timeout=10000)
                await page.wait_for_load_state("domcontentloaded")
                
                # Get job elements
                job_elements = await page.query_selector_all('.organic-job')
                
                if not job_elements:
                    console.print(f"[red]❌ No job elements found[/red]")
                    return False
                
                job_element = job_elements[0]
                links = await job_element.query_selector_all("a")
                
                # Find any clickable link (be more flexible than just "job" in href)
                clickable_link = None
                for link in links:
                    href = await link.get_attribute("href")
                    if href and href.startswith("http"):  # Any external link
                        clickable_link = link
                        console.print(f"[cyan]Found clickable link: {href}[/cyan]")
                        break
                
                if not clickable_link:
                    console.print(f"[red]❌ No clickable links found[/red]")
                    return False
                
                # Test popup
                console.print(f"[cyan]🖱️ Testing popup click...[/cyan]")
                try:
                    async with page.expect_popup(timeout=5000) as popup_info:
                        await clickable_link.click()
                        await asyncio.sleep(2)  # Wait for popup
                    
                    popup = await popup_info.value
                    popup_url = popup.url
                    console.print(f"[green]✅ Popup opened successfully![/green]")
                    console.print(f"[green]Popup URL: {popup_url}[/green]")
                    
                    await popup.close()
                    return True
                    
                except Exception as popup_error:
                    console.print(f"[red]❌ Popup failed: {popup_error}[/red]")
                    
                    # Try direct navigation as fallback
                    href = await clickable_link.get_attribute("href")
                    console.print(f"[yellow]Trying direct navigation to: {href}[/yellow]")
                    await page.goto(href)
                    console.print(f"[yellow]✅ Direct navigation worked, final URL: {page.url}[/yellow]")
                    return False  # Popup failed but direct link worked
                
            except Exception as e:
                console.print(f"[red]❌ Popup test failed: {e}[/red]")
                return False
            finally:
                await context.close()
                await browser.close()
    
    async def run_all_tests(self):
        """Run all diagnostic tests."""
        console.print("[bold green]🚀 Starting Eluta Scraper Diagnostic Tests[/bold green]")
        
        tests = [
            ("Basic Page Load", self.test_basic_page_load),
            ("Job Elements Detection", self.test_job_elements_detection),
            ("Link Analysis", self.test_link_analysis),
            ("Popup Functionality", self.test_popup_functionality)
        ]
        
        results = {}
        for test_name, test_func in tests:
            console.print(f"\n{'='*60}")
            result = await test_func()
            results[test_name] = result
            console.print(f"[{'green' if result else 'red'}]Result: {'PASS' if result else 'FAIL'}[/{'green' if result else 'red'}]")
        
        # Summary
        console.print(f"\n{'='*60}")
        console.print("[bold blue]📊 Test Summary[/bold blue]")
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            console.print(f"{status} {test_name}")
        
        console.print(f"\n[bold]Overall: {passed}/{total} tests passed[/bold]")
        
        if passed == total:
            console.print("[bold green]🎉 All tests passed! The scraper should work.[/bold green]")
        else:
            console.print("[bold red]🚨 Some tests failed. Issues need to be fixed.[/bold red]")
        
        return results


async def main():
    """Run the diagnostic tests."""
    tester = ElutaScrapingTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
