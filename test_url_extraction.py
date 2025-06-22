#!/usr/bin/env python3
"""
Test URL extraction from Eluta job listings.
"""

import asyncio
from playwright.async_api import async_playwright
from rich.console import Console

console = Console()

async def test_url_extraction():
    """Test URL extraction from a single job listing."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Navigate to Eluta search
            search_url = "https://www.eluta.ca/search?q=Data%20Analyst&l=&posted=14&pg=1"
            console.print(f"[cyan]🌐 Navigating to: {search_url}[/cyan]")
            
            await page.goto(search_url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(3)
            
            # Find job elements
            job_elements = await page.query_selector_all(".organic-job")
            console.print(f"[green]✅ Found {len(job_elements)} job listings[/green]")
            
            if not job_elements:
                console.print("[red]❌ No job elements found[/red]")
                return
            
            # Test with first job
            first_job = job_elements[0]
            
            # Get job text
            job_text = await first_job.inner_text()
            lines = [line.strip() for line in job_text.split('\n') if line.strip()]
            job_title = lines[0] if lines else "Unknown"
            
            console.print(f"[cyan]📋 Testing with job: {job_title}[/cyan]")
            
            # Find links in the job element
            links = await first_job.query_selector_all("a")
            console.print(f"[cyan]🔍 Found {len(links)} links in job element[/cyan]")
            
            for i, link in enumerate(links):
                link_text = await link.inner_text()
                href = await link.get_attribute("href")
                console.print(f"[yellow]Link {i+1}:[/yellow]")
                console.print(f"  Text: {link_text[:50]}...")
                console.print(f"  Href: {href}")
                
                # Try clicking this link
                if link_text and len(link_text) > 10:
                    console.print(f"[cyan]🖱️ Clicking link with text: {link_text[:30]}...[/cyan]")
                    
                    try:
                        # Get current URL
                        original_url = page.url
                        console.print(f"[yellow]Original URL: {original_url}[/yellow]")
                        
                        # Try expect_popup
                        async with page.expect_popup(timeout=5000) as popup_info:
                            await link.click()
                        
                        popup = await popup_info.value
                        popup_url = popup.url
                        
                        console.print(f"[green]✅ Popup opened![/green]")
                        console.print(f"[green]Popup URL: {popup_url}[/green]")
                        
                        # Close popup
                        await popup.close()
                        console.print(f"[cyan]🗙 Closed popup[/cyan]")
                        
                        break
                        
                    except Exception as e:
                        console.print(f"[red]❌ Popup method failed: {e}[/red]")
                        
                        # Try regular click
                        try:
                            await link.click()
                            await asyncio.sleep(2)
                            new_url = page.url
                            
                            if new_url != original_url:
                                console.print(f"[green]✅ Navigation occurred![/green]")
                                console.print(f"[green]New URL: {new_url}[/green]")
                                
                                # Go back
                                await page.go_back()
                                await asyncio.sleep(1)
                            else:
                                console.print(f"[yellow]⚠️ No navigation occurred[/yellow]")
                                
                        except Exception as click_error:
                            console.print(f"[red]❌ Regular click also failed: {click_error}[/red]")
            
            # Wait for user input
            input("\nPress Enter to close browser...")
            
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_url_extraction()) 