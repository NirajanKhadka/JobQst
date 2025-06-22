#!/usr/bin/env python3
"""
Eluta New Tab Test - Capture URL from new tab that opens after clicking
Based on user guidance that clicking opens a new tab after 1 second.
"""

import time
from playwright.sync_api import sync_playwright
from rich.console import Console

console = Console()

def test_new_tab_capture():
    """Test capturing URLs from new tabs that open when clicking Eluta jobs."""
    
    console.print("🔍 Testing Eluta New Tab URL Capture")
    console.print("Based on your guidance that clicking opens new tab after 1 second")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Navigate to Eluta search
            url = "https://www.eluta.ca/search?q=analyst&l=Toronto"
            console.print(f"📍 Going to: {url}")
            
            page.goto(url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)
            
            # Find job elements
            console.print("🔍 Looking for .organic-job elements...")
            job_elements = page.query_selector_all(".organic-job")
            console.print(f"✅ Found {len(job_elements)} job elements")
            
            if not job_elements:
                console.print("❌ No job elements found!")
                return
            
            # Test clicking on first few jobs to capture new tab URLs
            for i, job_elem in enumerate(job_elements[:3]):
                console.print(f"\n--- Testing Job {i+1} ---")
                
                # Get job title for reference
                text = job_elem.inner_text().strip()
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                job_title = lines[0] if lines else "Unknown Job"
                console.print(f"Job: {job_title[:50]}...")
                
                # Set up new tab listener BEFORE clicking
                console.print("🎯 Setting up new tab listener...")
                
                # Method 1: Listen for new page/tab
                new_page = None
                def handle_new_page(page_obj):
                    nonlocal new_page
                    new_page = page_obj
                    console.print(f"🆕 New tab detected!")
                
                context.on("page", handle_new_page)
                
                # Click on the job element
                console.print("🖱️ Clicking on job element...")
                job_elem.click()
                
                # Wait 1 second as you suggested
                console.print("⏳ Waiting 1 second for new tab...")
                time.sleep(1)
                
                # Check if new tab opened
                if new_page:
                    console.print("✅ New tab opened!")
                    
                    # Wait a bit more for the new tab to load
                    try:
                        new_page.wait_for_load_state("domcontentloaded", timeout=5000)
                        time.sleep(1)
                    except:
                        console.print("⚠️ New tab still loading, continuing...")
                    
                    # Get the URL from the new tab
                    new_tab_url = new_page.url
                    console.print(f"🎯 New tab URL: {new_tab_url}")
                    
                    # Get page title for verification
                    try:
                        new_tab_title = new_page.title()
                        console.print(f"📄 New tab title: {new_tab_title}")
                    except:
                        console.print("⚠️ Could not get new tab title")
                    
                    # Look for apply buttons or external links in new tab
                    try:
                        apply_buttons = new_page.query_selector_all("a:has-text('Apply'), button:has-text('Apply')")
                        console.print(f"🔗 Apply buttons in new tab: {len(apply_buttons)}")
                        
                        external_links = new_page.query_selector_all("a[href^='http']:not([href*='eluta.ca'])")
                        console.print(f"🌐 External links in new tab: {len(external_links)}")
                        
                        # Show first few external links
                        for j, link in enumerate(external_links[:2]):
                            href = link.get_attribute("href")
                            link_text = link.inner_text().strip()[:30]
                            console.print(f"  External {j+1}: {href} ('{link_text}...')")
                    except Exception as e:
                        console.print(f"⚠️ Error checking new tab content: {e}")
                    
                    # Close the new tab to clean up
                    try:
                        new_page.close()
                        console.print("🗑️ Closed new tab")
                    except:
                        pass
                    
                    new_page = None
                else:
                    console.print("❌ No new tab opened")
                    
                    # Alternative: Check if current page URL changed
                    current_url = page.url
                    if current_url != url:
                        console.print(f"🔄 Current page URL changed to: {current_url}")
                        # Go back to search results
                        page.go_back()
                        time.sleep(1)
                    else:
                        console.print("⚠️ No navigation occurred at all")
                
                # Remove the event listener
                context.remove_listener("page", handle_new_page)
                
                # Wait a bit before next job
                if i < 2:
                    console.print("⏳ Waiting before next job...")
                    time.sleep(2)
            
            input("\nPress Enter to close browser...")
            
        except Exception as e:
            console.print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()

def test_alternative_method():
    """Alternative method using expect_popup."""
    
    console.print("\n🔍 Testing Alternative Method - expect_popup")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Navigate to Eluta search
            url = "https://www.eluta.ca/search?q=analyst&l=Toronto"
            page.goto(url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)
            
            # Find job elements
            job_elements = page.query_selector_all(".organic-job")
            console.print(f"✅ Found {len(job_elements)} job elements")
            
            if job_elements:
                console.print("🖱️ Testing expect_popup method...")
                
                first_job = job_elements[0]
                
                # Use expect_popup to catch new tab
                try:
                    with page.expect_popup(timeout=3000) as popup_info:
                        first_job.click()
                        time.sleep(1)  # Your suggested 1 second wait
                    
                    popup = popup_info.value
                    popup_url = popup.url
                    console.print(f"✅ Popup captured! URL: {popup_url}")
                    
                    # Get popup title
                    popup_title = popup.title()
                    console.print(f"📄 Popup title: {popup_title}")
                    
                    popup.close()
                    
                except Exception as e:
                    console.print(f"❌ expect_popup failed: {e}")
            
            input("\nPress Enter to close browser...")
            
        except Exception as e:
            console.print(f"❌ Error: {e}")
        
        finally:
            browser.close()

def main():
    """Main test function."""
    console.print("🧪 Eluta New Tab URL Capture Test")
    console.print("Testing your guidance that clicking opens new tab after 1 second")
    console.print("We'll try to capture the URL from that new tab")
    
    input("\nPress Enter to start test...")
    
    test_new_tab_capture()
    
    console.print("\n🔄 Trying alternative method...")
    test_alternative_method()
    
    console.print("\n✅ Tests complete!")

if __name__ == "__main__":
    main()
