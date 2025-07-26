#!/usr/bin/env python3
"""
Test script to find correct selectors for job elements on Eluta
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

async def test_eluta_selectors():
    """Test different selectors to find job elements on Eluta."""
    try:
        print("🔍 Testing Eluta Selectors")
        print("=" * 50)
        
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await context.new_page()
            
            try:
                # Go to Eluta search page
                search_url = "https://www.eluta.ca/search?q=Python&l=&radius=25&co=CA&type=1&source=&from=&to=&s=3&su=1"
                print(f"🌐 Navigating to: {search_url}")
                
                await page.goto(search_url, wait_until="networkidle")
                await asyncio.sleep(5)  # Wait longer for content to load
                
                # Test different selectors
                selectors_to_test = [
                    ".job-result",
                    ".job",
                    ".result",
                    ".search-result",
                    ".job-listing",
                    ".listing",
                    "div[class*='job']",
                    "div[class*='result']",
                    "div[class*='listing']",
                    ".srp-job",
                    ".job-card",
                    ".result-item",
                    "article",
                    ".job-item",
                    ".search-result-item"
                ]
                
                print(f"\n🔍 Testing selectors:")
                for selector in selectors_to_test:
                    elements = await page.query_selector_all(selector)
                    print(f"  {selector}: {len(elements)} elements")
                    
                    if len(elements) > 0:
                        print(f"    ✅ Found {len(elements)} elements with {selector}")
                        # Show first element's class
                        first_element = elements[0]
                        class_attr = await first_element.get_attribute("class")
                        print(f"    📋 First element class: {class_attr}")
                        
                        # Get some text content
                        text_content = await first_element.inner_text()
                        print(f"    📄 Text preview: {text_content[:100]}...")
                        break
                
                # If no selectors worked, try to find any divs with job-related content
                print(f"\n🔍 Looking for any job-related content:")
                all_divs = await page.query_selector_all("div")
                print(f"  Total divs on page: {len(all_divs)}")
                
                # Look for divs with job-related text
                job_related_divs = []
                for i, div in enumerate(all_divs[:20]):  # Check first 20 divs
                    try:
                        text = await div.inner_text()
                        if any(keyword in text.lower() for keyword in ["python", "developer", "software", "data", "analyst"]):
                            class_attr = await div.get_attribute("class")
                            print(f"    Div {i}: class='{class_attr}' - text: {text[:50]}...")
                            job_related_divs.append(div)
                    except:
                        continue
                
                print(f"  Found {len(job_related_divs)} divs with job-related content")
                
                # Take a screenshot to see what's on the page
                await page.screenshot(path="eluta_page.png")
                print(f"  📸 Screenshot saved as eluta_page.png")
                
                # Get page title and URL
                title = await page.title()
                current_url = page.url
                print(f"\n📄 Page title: {title}")
                print(f"🌐 Current URL: {current_url}")
                
            finally:
                await browser.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_eluta_selectors()) 