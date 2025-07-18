---
post_title: "Scraper Module Standards"
author1: "Nirajan Khadka"
post_slug: "scraper-standards"
microsoft_alias: "nirajank"
featured_image: ""
categories: ["standards", "scrapers"]
tags: ["scraper", "web scraping", "quality"]
ai_note: "Module-specific standards for scraper code and documentation."
summary: "Rules and best practices for all web scrapers in AutoJobAgent."
post_date: "2025-07-04"
---

> **Under any circumstances, the user should ask the AI to edit these standards.**

# 🗺️ Scraper Module Standards

## Purpose
This document defines all coding, documentation, and quality standards for web scrapers in AutoJobAgent. All scraper code must comply with these rules in addition to the overall project quality gates.

## Python Rules
- Use descriptive, intent-revealing names for all classes, functions, and variables.
- All scrapers must implement the common scraper interface.
- No global variables; use dependency injection for configuration.
- Use type hints for all functions and method signatures.
- All public functions/classes must have docstrings.
- Limit scraper methods to 30 lines or less.
- Handle all network errors and timeouts with retries and logging.
- Never hardcode credentials or API keys.
- Implement anti-captcha/anti-bot strategies where allowed (e.g., delays, user agents, headless detection avoidance).
- All scraped data must be validated and conform to a defined schema.
- All scrapers must expose health/heartbeat endpoints or logs for monitoring.
- All scrapers must have a documented update/maintenance strategy for site changes.

## Documentation & Comments
- Every scraper class must have a docstring explaining its target site and logic.
- Inline comments for any non-obvious parsing or anti-bot logic.
- Document all required environment variables or config options.

## Testing & Quality
- All scrapers must have unit tests for core logic and integration tests for site connectivity.
- No placeholder/fake data in production scrapers.
- All changes must be reviewed for anti-bot compliance and site terms.
- All scrapers must be monitored for health and error rates.

## Performance
- Use async or batch requests where possible.
- Minimize memory and bandwidth usage (avoid loading full pages if not needed).
- Profile scraper performance with cProfile or Py-Spy.

## Security
- Respect robots.txt and site rate limits.
- Validate and sanitize all scraped data.

---

> For project-wide quality gates, see DEVELOPMENT_STANDARDS.md.
