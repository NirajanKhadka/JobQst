#!/usr/bin/env python3
"""
Quick test for Eluta URL extraction - 1 keyword, 1 page only.
"""

import asyncio
import json
from playwright.async_api import async_playwright
from rich.console import Console
from rich.table import Table

console = Console()

async def quick_eluta_test():
    """Quick test with 1 keyword and 1 page."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Test with just one keyword
            keyword = "Data Analyst"
            search_url = f"https://www.eluta.ca/search?q={keyword}&l=&posted=14&pg=1"
            
            console.print(f"[cyan]🔍 Testing: {keyword} - Page 1[/cyan]")
            console.print(f"[cyan]🌐 URL: {search_url}[/cyan]")
            
            # Navigate to page
            await page.goto(search_url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(3)
            
            # Try different selectors for job elements
            selectors_to_try = [
                ".organic-job",
                ".job-listing",
                ".job-item",
                "[data-testid='job-card']",
                ".search-result",
                "article",
                ".job"
            ]
            
            job_elements = []
            working_selector = None
            
            for selector in selectors_to_try:
                elements = await page.query_selector_all(selector)
                if elements:
                    job_elements = elements
                    working_selector = selector
                    console.print(f"[green]✅ Found {len(elements)} job elements with selector: {selector}[/green]")
                    break
            
            if not job_elements:
                console.print("[red]❌ No job elements found with any selector![/red]")
                # Show page content for debugging
                content = await page.content()
                console.print(f"[yellow]Page content length: {len(content)}[/yellow]")
                return
            
            # Test URL extraction on first 3 jobs
            jobs_with_urls = 0
            total_tested = min(3, len(job_elements))
            
            console.print(f"\n[cyan]🔗 Testing URL extraction on first {total_tested} jobs:[/cyan]")
            
            for i in range(total_tested):
                job_elem = job_elements[i]
                
                try:
                    # Get job title
                    title_elem = await job_elem.query_selector("h2, h3, .job-title, .title")
                    if title_elem:
                        title = await title_elem.inner_text()
                        title = title.strip()
                    else:
                        title = f"Job {i+1}"
                    
                    console.print(f"\n[blue]📋 Job {i+1}: {title[:50]}...[/blue]")
                    
                    # Try to find clickable link
                    link = await job_elem.query_selector("a[href]")
                    if link:
                        href = await link.get_attribute("href")
                        console.print(f"[yellow]🔗 Found link: {href}[/yellow]")
                        
                        # Try to get full URL
                        if href and not href.startswith("http"):
                            full_url = f"https://www.eluta.ca{href}" if href.startswith("/") else f"https://www.eluta.ca/{href}"
                        else:
                            full_url = href
                        
                        console.print(f"[green]✅ Full URL: {full_url}[/green]")
                        jobs_with_urls += 1
                        
                        # Test popup method
                        try:
                            console.print(f"[cyan]🔄 Testing popup method...[/cyan]")
                            
                            # Listen for popup
                            async with page.expect_popup(timeout=5000) as popup_info:
                                await link.click()
                            
                            popup = await popup_info.value
                            popup_url = popup.url
                            
                            console.print(f"[green]🎉 Popup opened! URL: {popup_url}[/green]")
                            
                            # Close popup
                            await popup.close()
                            console.print(f"[cyan]🗙 Closed popup[/cyan]")
                            
                        except Exception as popup_error:
                            console.print(f"[red]❌ Popup failed: {popup_error}[/red]")
                    else:
                        console.print(f"[red]❌ No link found[/red]")
                        
                except Exception as e:
                    console.print(f"[red]❌ Error processing job {i+1}: {e}[/red]")
            
            # Summary
            console.print(f"\n[bold cyan]📊 Test Summary:[/bold cyan]")
            console.print(f"   Total jobs found: {len(job_elements)}")
            console.print(f"   Jobs tested: {total_tested}")
            console.print(f"   Jobs with URLs: {jobs_with_urls}")
            console.print(f"   URL success rate: {jobs_with_urls/total_tested*100:.1f}%")
            
            if working_selector:
                console.print(f"   Working selector: {working_selector}")
            
        except Exception as e:
            console.print(f"[red]❌ Test failed: {e}[/red]")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(quick_eluta_test()) 