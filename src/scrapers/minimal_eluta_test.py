#!/usr/bin/env python3
"""
Minimal Eluta Test - Just extract basic job data
Focus on proving the .organic-job selector works for data extraction.
"""

import time
import re
from playwright.sync_api import sync_playwright
from rich.console import Console

console = Console()

def test_basic_extraction():
    """Test basic job data extraction from Eluta."""
    
    console.print("🔍 Testing Basic Eluta Job Extraction")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Navigate to Eluta search
            url = "https://www.eluta.ca/search?q=analyst&l=Toronto"
            console.print(f"📍 Going to: {url}")
            
            page.goto(url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)
            
            # Find job elements using discovered selector
            console.print("🔍 Looking for .organic-job elements...")
            job_elements = page.query_selector_all(".organic-job")
            
            console.print(f"✅ Found {len(job_elements)} job elements")
            
            # Extract data from first few jobs
            for i, job_elem in enumerate(job_elements[:3]):
                console.print(f"\n--- Job {i+1} ---")
                
                # Get raw text
                text = job_elem.inner_text().strip()
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                
                console.print(f"Raw text lines ({len(lines)}):")
                for j, line in enumerate(lines[:5]):  # Show first 5 lines
                    console.print(f"  {j+1}: {line}")
                
                # Try to parse structure
                if len(lines) >= 3:
                    title = lines[0]
                    company = lines[1].replace("TOP EMPLOYER", "").strip()
                    location = lines[2]
                    
                    # Extract salary if present
                    salary_match = re.search(r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?', title)
                    if salary_match:
                        salary = salary_match.group(0)
                        title = title.replace(salary, "").strip()
                    else:
                        salary = "Not specified"
                    
                    console.print(f"📋 Parsed data:")
                    console.print(f"  Title: {title}")
                    console.print(f"  Company: {company}")
                    console.print(f"  Location: {location}")
                    console.print(f"  Salary: {salary}")
                else:
                    console.print("⚠️ Not enough lines to parse")
            
            # Test simple clicking (your suggestion)
            if job_elements:
                console.print(f"\n🖱️ Testing simple click on first job...")
                first_job = job_elements[0]
                
                original_url = page.url
                console.print(f"Original URL: {original_url}")
                
                # Click and wait 1 second as you suggested
                first_job.click()
                time.sleep(1)
                
                new_url = page.url
                console.print(f"New URL: {new_url}")
                
                if new_url != original_url:
                    console.print("✅ Click worked! Navigation occurred.")
                    
                    # Check what's on the new page
                    page_title = page.title()
                    console.print(f"Page title: {page_title}")
                    
                    # Look for apply buttons
                    apply_buttons = page.query_selector_all("a:has-text('Apply'), button:has-text('Apply')")
                    console.print(f"Apply buttons found: {len(apply_buttons)}")
                    
                    # Look for external links
                    external_links = page.query_selector_all("a[href^='http']:not([href*='eluta.ca'])")
                    console.print(f"External links found: {len(external_links)}")
                    
                    for link in external_links[:3]:
                        href = link.get_attribute("href")
                        text = link.inner_text().strip()[:30]
                        console.print(f"  External: {href} ('{text}...')")
                    
                else:
                    console.print("⚠️ No navigation occurred")
                    
                    # Try clicking on links within the job element
                    links = first_job.query_selector_all("a")
                    console.print(f"Links in job element: {len(links)}")
                    
                    for j, link in enumerate(links[:2]):
                        href = link.get_attribute("href") or "no-href"
                        text = link.inner_text().strip()[:20]
                        console.print(f"  Link {j+1}: {href} ('{text}...')")
                        
                        if href and href != "#!":
                            console.print(f"🔗 Trying to click link {j+1}...")
                            try:
                                link.click()
                                time.sleep(1)
                                
                                new_url = page.url
                                if new_url != original_url:
                                    console.print(f"✅ Link {j+1} worked: {new_url}")
                                    break
                            except Exception as e:
                                console.print(f"❌ Link {j+1} failed: {e}")
            
            input("\nPress Enter to close browser...")
            
        except Exception as e:
            console.print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()

def main():
    """Main test function."""
    console.print("🧪 Minimal Eluta Extraction Test")
    console.print("This test focuses on basic data extraction using the .organic-job selector")
    console.print("Based on your suggestion that Eluta is simply scrapable with click and wait 1 sec")
    
    input("\nPress Enter to start test...")
    
    test_basic_extraction()
    
    console.print("\n✅ Test complete!")

if __name__ == "__main__":
    main()
