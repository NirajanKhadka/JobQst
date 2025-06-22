#!/usr/bin/env python3
"""
Eluta Fixed Timing Test
Fix the timing issue - new tabs ARE opening, just need better timing handling.
"""

import time
from playwright.sync_api import sync_playwright
from rich.console import Console

console = Console()

def test_fixed_timing():
    """Test with proper timing to catch new tabs."""
    
    console.print("🔍 Testing Eluta with Fixed Timing")
    console.print("New tabs ARE opening - just need better timing!")
    
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
            
            # Find job containers
            job_elements = page.query_selector_all(".organic-job")
            console.print(f"✅ Found {len(job_elements)} job containers")
            
            if not job_elements:
                return
            
            # Test first job with better timing
            for i, job_elem in enumerate(job_elements[:2]):
                console.print(f"\n--- Testing Job {i+1} with Better Timing ---")
                
                # Extract job title
                text = job_elem.inner_text().strip()
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                job_title = lines[0] if lines else "Unknown"
                console.print(f"📋 Job: {job_title[:60]}...")
                
                # Find job title link
                links = job_elem.query_selector_all("a")
                title_link = None
                
                for link in links:
                    link_text = link.inner_text().strip()
                    if link_text and len(link_text) > 10:  # Likely a job title
                        title_link = link
                        console.print(f"🔗 Found title link: '{link_text[:40]}...'")
                        break
                
                if not title_link:
                    console.print("❌ No title link found")
                    continue
                
                # Method 1: Use expect_popup with longer timeout
                console.print("🎯 Method 1: Using expect_popup...")
                try:
                    with page.expect_popup(timeout=5000) as popup_info:
                        console.print("🖱️ Clicking title link...")
                        title_link.click()
                        console.print("⏳ Waiting for popup...")
                    
                    popup = popup_info.value
                    popup_url = popup.url
                    console.print(f"✅ SUCCESS! Popup URL: {popup_url}")
                    
                    # Get popup title
                    try:
                        popup_title = popup.title()
                        console.print(f"📄 Popup title: {popup_title[:80]}...")
                    except:
                        console.print("⚠️ Could not get popup title")
                    
                    # Look for external links in popup
                    try:
                        external_links = popup.query_selector_all("a[href^='http']:not([href*='eluta.ca'])")
                        console.print(f"🌐 External links in popup: {len(external_links)}")
                        
                        for j, ext_link in enumerate(external_links[:3]):
                            ext_href = ext_link.get_attribute("href")
                            ext_text = ext_link.inner_text().strip()[:25]
                            console.print(f"  {j+1}. {ext_href}")
                            console.print(f"     Text: '{ext_text}...'")
                    except Exception as e:
                        console.print(f"⚠️ Error checking external links: {e}")
                    
                    # Close popup
                    popup.close()
                    console.print("🗑️ Closed popup")
                    
                except Exception as e:
                    console.print(f"❌ expect_popup failed: {e}")
                    
                    # Method 2: Manual new page detection with longer wait
                    console.print("🎯 Method 2: Manual detection with longer wait...")
                    
                    new_page = None
                    pages_before = len(context.pages)
                    
                    def handle_new_page(page_obj):
                        nonlocal new_page
                        new_page = page_obj
                        console.print("🆕 New page detected!")
                    
                    context.on("page", handle_new_page)
                    
                    try:
                        # Click and wait longer
                        title_link.click()
                        console.print("⏳ Waiting up to 3 seconds for new page...")
                        
                        # Wait in small increments to catch the new page
                        for wait_time in range(30):  # 3 seconds total, check every 0.1s
                            time.sleep(0.1)
                            if new_page:
                                break
                        
                        if new_page:
                            console.print("✅ SUCCESS! New page detected")
                            
                            # Wait for it to load
                            try:
                                new_page.wait_for_load_state("domcontentloaded", timeout=3000)
                            except:
                                pass
                            
                            new_url = new_page.url
                            console.print(f"🎯 New page URL: {new_url}")
                            
                            new_page.close()
                        else:
                            console.print("❌ No new page detected")
                            
                            # Check if current page changed
                            current_url = page.url
                            if current_url != url:
                                console.print(f"🔄 Current page changed: {current_url}")
                                page.go_back()
                                time.sleep(1)
                    
                    except Exception as e2:
                        console.print(f"❌ Manual method failed: {e2}")
                    
                    context.remove_listener("page", handle_new_page)
                
                # Wait before next job
                if i < 1:
                    console.print("⏳ Waiting before next job...")
                    time.sleep(2)
            
            input("\nPress Enter to close browser...")
            
        except Exception as e:
            console.print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()

def main():
    """Main test function."""
    console.print("🧪 Eluta Fixed Timing Test")
    console.print("The previous test showed that new tabs ARE opening!")
    console.print("We just need to fix the timing to catch them properly.")
    console.print("This test uses:")
    console.print("1. expect_popup with longer timeout")
    console.print("2. Manual detection with incremental waiting")
    
    input("\nPress Enter to start test...")
    
    test_fixed_timing()
    
    console.print("\n✅ Test complete!")

if __name__ == "__main__":
    main()
