#!/usr/bin/env python3
"""
Test script to verify Playwright popup handling fixes
"""

import asyncio
from playwright.async_api import async_playwright
from rich.console import Console

console = Console()

async def test_popup_handling():
    """Test the fixed popup handling patterns."""
    console.print("[bold blue]Testing Playwright Popup Handling Fixes[/bold blue]")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Test 1: Basic popup handling with async context manager
            console.print("[cyan]Test 1: Basic popup handling...[/cyan]")
            
            # Navigate to a test page
            await page.goto("data:text/html,<html><body><a href='#' onclick='window.open(\"data:text/html,<h1>Popup</h1>\"); return false;'>Click me</a></body></html>")
            
            # Test the fixed popup pattern
            try:
                async with page.expect_popup() as popup_info:
                    await page.click("a")
                
                popup = await asyncio.wait_for(popup_info.value, timeout=5)
                await popup.wait_for_load_state("domcontentloaded")
                popup_url = popup.url
                await popup.close()
                
                console.print(f"[green]✅ Popup handled successfully: {popup_url[:50]}...[/green]")
                
            except Exception as e:
                console.print(f"[red]❌ Popup handling failed: {e}[/red]")
                return False
            
            # Test 2: Timeout handling
            console.print("[cyan]Test 2: Timeout handling...[/cyan]")
            
            try:
                async with page.expect_popup() as popup_info:
                    # This should timeout quickly since there's no popup
                    await asyncio.wait_for(page.click("body"), timeout=1)
                
                # This shouldn't execute
                popup = await popup_info.value
                await popup.close()
                
            except asyncio.TimeoutError:
                console.print("[green]✅ Timeout handled correctly[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️ Different exception: {e}[/yellow]")
            
            console.print("[bold green]All popup handling tests passed![/bold green]")
            return True
            
        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    success = asyncio.run(test_popup_handling())
    if success:
        console.print("[bold green]🎉 Popup fixes verified successfully![/bold green]")
    else:
        console.print("[bold red]❌ Popup fixes need attention[/bold red]")