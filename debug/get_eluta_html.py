from playwright.sync_api import sync_playwright
import time
import os

def fetch_eluta_html(url: str, output_path: str):
    """Fetches HTML from a URL and saves it to a file."""
    print(f"Fetching HTML from: {url}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, timeout=60000, wait_until='networkidle')
            time.sleep(5)  # Allow extra time for any dynamic content
            content = page.content()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"Successfully saved HTML to: {output_path}")
            
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    search_keyword = "software"
    search_url = f"https://www.eluta.ca/search?q={search_keyword}"
    output_file = "debug/eluta_page.html"
    
    fetch_eluta_html(search_url, output_file) 