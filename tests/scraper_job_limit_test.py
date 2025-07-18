"""
Unified Scraper Test Script
Tests each main scraper to verify it can return at least 11 jobs.
"""

from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper
from src.scrapers.monster_enhanced import MonsterEnhancedScraper
from src.scrapers.linkedin_enhanced import LinkedInEnhancedScraper
from src.scrapers.jobbank_enhanced import JobBankEnhancedScraper
from src.scrapers.indeed_enhanced import EnhancedIndeedScraper
from src.scrapers.towardsai_scraper import get_jobs_bs4

PROFILE = "Nirajan"
KEYWORDS = ["Python", "Data Analyst", "SQL"]
JOB_LIMIT = 11


def test_scraper(scraper, keywords=None):
    print(f"\nTesting {scraper.__class__.__name__}...")
    try:
        if keywords:
            jobs = scraper.scrape_jobs(keywords)
        else:
            jobs = scraper.scrape_jobs([])
        print(f"Returned {len(jobs)} jobs.")
        assert len(jobs) >= JOB_LIMIT, f"Expected at least {JOB_LIMIT} jobs, got {len(jobs)}"
        print("[PASS]")
    except Exception as e:
        print(f"[FAIL] {e}")


def test_towardsai():
    print("\nTesting TowardsAI scraper...")
    try:
        jobs = get_jobs_bs4(limit=JOB_LIMIT)
        print(f"Returned {len(jobs)} jobs.")
        assert len(jobs) >= JOB_LIMIT, f"Expected at least {JOB_LIMIT} jobs, got {len(jobs)}"
        print("[PASS]")
    except Exception as e:
        print(f"[FAIL] {e}")


def main():
    test_scraper(ComprehensiveElutaScraper(PROFILE), KEYWORDS)
    test_scraper(MonsterEnhancedScraper(PROFILE), KEYWORDS)
    test_scraper(LinkedInEnhancedScraper(PROFILE), KEYWORDS)
    test_scraper(JobBankEnhancedScraper(PROFILE), KEYWORDS)
    test_scraper(EnhancedIndeedScraper(PROFILE), KEYWORDS)
    test_towardsai()

if __name__ == "__main__":
    main()
