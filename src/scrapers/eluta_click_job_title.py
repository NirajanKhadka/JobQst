#!/usr/bin/env python3
"""
Eluta Job Title Click Test
1. Scrape content to find job titles
2. Click specifically on job title elements
3. Wait 1 second for new tab
4. Capture URL from new tab
"""

import time
from playwright.sync_api import sync_playwright
from rich.console import Console

console = Console()

def test_job_title_clicking():
    """Test clicking specifically on job title elements."""
    
    console.print("🔍 Testing Job Title Clicking on Eluta")
    console.print("Step 1: Scrape content to find job titles")
    console.print("Step 2: Click specifically on job title elements")
    console.print("Step 3: Wait 1 second for new tab")
    console.print("Step 4: Capture URL from new tab")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Navigate to Eluta search
            url = "https://www.eluta.ca/search?q=analyst&l=Toronto"
            console.print(f"\n📍 Going to: {url}")
            
            page.goto(url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)
            
            # Step 1: Scrape content to find job containers
            console.print("\n🔍 Step 1: Finding job containers...")
            job_elements = page.query_selector_all(".organic-job")
            console.print(f"✅ Found {len(job_elements)} job containers")
            
            if not job_elements:
                console.print("❌ No job containers found!")
                return
            
            # Process each job container
            for i, job_elem in enumerate(job_elements[:3]):
                console.print(f"\n--- Processing Job {i+1} ---")
                
                # Step 1: Extract job data first
                text = job_elem.inner_text().strip()
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                
                if lines:
                    job_title = lines[0]
                    console.print(f"📋 Job Title: {job_title}")
                    
                    # Step 2: Find clickable job title element within this container
                    console.print("🔍 Looking for clickable job title element...")
                    
                    # Try different selectors for job title links
                    title_selectors = [
                        "a",  # Any link
                        "a:first-child",  # First link
                        "h1 a", "h2 a", "h3 a",  # Title in heading
                        ".job-title a", ".title a",  # Title with class
                        "a[href]"  # Link with href
                    ]
                    
                    title_link = None
                    for selector in title_selectors:
                        try:
                            potential_links = job_elem.query_selector_all(selector)
                            for link in potential_links:
                                link_text = link.inner_text().strip()
                                # Check if this link contains the job title or part of it
                                if link_text and (link_text in job_title or job_title.startswith(link_text[:20])):
                                    title_link = link
                                    console.print(f"✅ Found job title link: '{link_text[:50]}...'")
                                    break
                            if title_link:
                                break
                        except:
                            continue
                    
                    # If no specific title link found, try the first link in the container
                    if not title_link:
                        console.print("⚠️ No specific title link found, trying first link...")
                        all_links = job_elem.query_selector_all("a")
                        if all_links:
                            title_link = all_links[0]
                            link_text = title_link.inner_text().strip()
                            console.print(f"🔗 Using first link: '{link_text[:50]}...'")
                    
                    if title_link:
                        # Step 3: Set up new tab listener
                        console.print("🎯 Setting up new tab listener...")
                        new_page = None
                        
                        def handle_new_page(page_obj):
                            nonlocal new_page
                            new_page = page_obj
                            console.print("🆕 New tab detected!")
                        
                        context.on("page", handle_new_page)
                        
                        # Get href for debugging
                        href = title_link.get_attribute("href") or "no-href"
                        console.print(f"🔗 Link href: {href}")
                        
                        # Step 3: Click on the job title link
                        console.print("🖱️ Clicking on job title link...")
                        try:
                            title_link.click()
                            
                            # Step 4: Wait 1 second as suggested
                            console.print("⏳ Waiting 1 second for new tab...")
                            time.sleep(1)
                            
                            # Check if new tab opened
                            if new_page:
                                console.print("✅ New tab opened!")
                                
                                # Wait for new tab to load
                                try:
                                    new_page.wait_for_load_state("domcontentloaded", timeout=5000)
                                    time.sleep(0.5)
                                except:
                                    console.print("⚠️ New tab still loading...")
                                
                                # Get URL from new tab
                                new_tab_url = new_page.url
                                console.print(f"🎯 New tab URL: {new_tab_url}")
                                
                                # Get page title
                                try:
                                    new_tab_title = new_page.title()
                                    console.print(f"📄 New tab title: {new_tab_title[:100]}...")
                                except:
                                    console.print("⚠️ Could not get new tab title")
                                
                                # Check for external apply links in new tab
                                try:
                                    external_links = new_page.query_selector_all("a[href^='http']:not([href*='eluta.ca'])")
                                    console.print(f"🌐 External links in new tab: {len(external_links)}")
                                    
                                    for j, ext_link in enumerate(external_links[:2]):
                                        ext_href = ext_link.get_attribute("href")
                                        ext_text = ext_link.inner_text().strip()[:30]
                                        console.print(f"  External {j+1}: {ext_href}")
                                        console.print(f"    Text: '{ext_text}...'")
                                except Exception as e:
                                    console.print(f"⚠️ Error checking external links: {e}")
                                
                                # Close new tab
                                try:
                                    new_page.close()
                                    console.print("🗑️ Closed new tab")
                                except:
                                    pass
                                
                            else:
                                console.print("❌ No new tab opened")
                                
                                # Check if current page changed
                                current_url = page.url
                                console.print(f"Current URL: {current_url}")
                                
                                if current_url != url:
                                    console.print("🔄 Page navigation occurred instead of new tab")
                                    # Go back
                                    page.go_back()
                                    time.sleep(1)
                                else:
                                    console.print("⚠️ No navigation at all")
                            
                        except Exception as e:
                            console.print(f"❌ Click failed: {e}")
                        
                        # Remove event listener
                        context.remove_listener("page", handle_new_page)
                        new_page = None
                        
                    else:
                        console.print("❌ No clickable title link found in this job container")
                else:
                    console.print("❌ No text content found in job container")
                
                # Wait before next job
                if i < 2:
                    console.print("⏳ Waiting before next job...")
                    time.sleep(2)
            
            # Auto-close browser after processing (no user input required)
            console.print("\n✅ Job processing complete, closing browser...")

        except Exception as e:
            console.print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            browser.close()

def main():
    """Main test function."""
    console.print("🧪 Eluta Job Title Click Test")
    console.print("This test will:")
    console.print("1. Find job containers (.organic-job)")
    console.print("2. Extract job titles from each container")
    console.print("3. Find and click on the specific job title link")
    console.print("4. Wait 1 second for new tab to open")
    console.print("5. Capture the URL from the new tab")
    
    input("\nPress Enter to start test...")
    
    test_job_title_clicking()
    
    console.print("\n✅ Test complete!")

if __name__ == "__main__":
    main()
