import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
import asyncio
from playwright.sync_api import sync_playwright
from pathlib import Path

BASE_URL = "https://jobs.towardsai.net/"



def get_jobs_bs4(limit: int = 11):
    """
    Scrape job listings from TowardsAI using requests + BeautifulSoup.
    Returns up to 'limit' jobs as a list of dicts.
    """
    response = requests.get(BASE_URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    jobs = []
    for a in soup.find_all('a', href=True):
        if isinstance(a, Tag):
            href = str(a['href'])
            if href.startswith('/job/'):
                title = a.get_text(strip=True)
                link = href
                if not link.startswith('http'):
                    link = BASE_URL.rstrip('/') + link
                jobs.append({"title": title, "link": link})
                if len(jobs) >= limit:
                    break
    return jobs


def fetch_job_links_playwright_and_save():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL, timeout=60000)
        page.wait_for_timeout(5000)  # Wait for JS to render
        links = []
        anchors = page.query_selector_all("a[href^='/job/']")
        for a in anchors:
            href = a.get_attribute('href')
            if href and href.startswith('/job/'):
                link = href
                if not link.startswith('http'):
                    link = BASE_URL.rstrip('/') + link
                links.append(link)
        browser.close()
    # Save links to file
    out_path = Path("towardsai_job_links.txt")
    with out_path.open("w", encoding="utf-8") as f:
        for link in sorted(set(links)):
            f.write(link + "\n")
    print(f"Saved {len(set(links))} job links to {out_path}")


def main():
    # Example: Use reliable keyword extraction utility (for future CLI integration)
    from src.utils.keyword_extractor import get_keywords_for_profile
    profile_path = "profiles/Nirajan/Nirajan.json"  # TODO: make dynamic for CLI
    try:
        keywords = get_keywords_for_profile(profile_path)
        print(f"[INFO] Loaded/extracted keywords: {keywords}")
    except Exception as e:
        print(f"[ERROR] Keyword extraction failed: {e}")
        keywords = []
    print("Choose scraping method:")
    print("1. Playwright (save job links to file)")
    print("2. Requests + BeautifulSoup (return up to 11 jobs)")
    choice = input("Enter 1 or 2: ").strip()
    if choice == '1':
        fetch_job_links_playwright_and_save()
    else:
        jobs = get_jobs_bs4(limit=11)
        print(f"[BS4] Found {len(jobs)} jobs:")
        for job in jobs:
            print(f"- {job['title']}: {job['link']}")

if __name__ == "__main__":
    main() 