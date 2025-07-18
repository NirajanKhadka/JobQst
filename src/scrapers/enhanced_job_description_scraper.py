#!/usr/bin/env python3
"""
Enhanced Job Description Scraper
Extracts detailed job descriptions, experience requirements, and generates summaries.
"""

import re
import time
import json
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from playwright.async_api import async_playwright, Page
from rich.console import Console
from rich.panel import Panel

console = Console()


class EnhancedJobDescriptionScraper:
    """Enhanced scraper for detailed job descriptions and experience requirements."""

    def __init__(self):
        self.experience_patterns = {
            "years": [
                r"(\d+)[\-\+]?\s*years?\s*of?\s*experience",
                r"(\d+)[\-\+]?\s*years?\s*in\s*the\s*field",
                r"(\d+)[\-\+]?\s*years?\s*relevant\s*experience",
                r"experience\s*level:\s*(\d+)[\-\+]?\s*years?",
                r"minimum\s*(\d+)[\-\+]?\s*years?\s*experience",
                r"(\d+)[\-\+]?\s*years?\s*minimum",
                r"(\d+)[\-\+]?\s*years?\s*required",
            ],
            "entry_level": [
                r"entry\s*level",
                r"entry-level",
                r"junior\s*level",
                r"graduate\s*level",
                r"new\s*grad",
                r"recent\s*graduate",
                r"0[\-\+]?\s*years?",
                r"1[\-\+]?\s*years?",
                r"2[\-\+]?\s*years?",
                r"no\s*experience\s*required",
                r"entry\s*position",
                r"junior\s*position",
            ],
            "senior_level": [
                r"senior\s*level",
                r"senior-level",
                r"lead\s*position",
                r"principal\s*level",
                r"manager\s*level",
                r"director\s*level",
                r"5[\+\+]?\s*years?",
                r"10[\+\+]?\s*years?",
                r"experienced\s*professional",
                r"expert\s*level",
            ],
        }

        self.skill_patterns = [
            r"proficiency\s*in\s*([^.,]+)",
            r"experience\s*with\s*([^.,]+)",
            r"knowledge\s*of\s*([^.,]+)",
            r"familiarity\s*with\s*([^.,]+)",
            r"strong\s*([^.,]+)\s*skills?",
            r"expertise\s*in\s*([^.,]+)",
            r"proficient\s*in\s*([^.,]+)",
            r"working\s*knowledge\s*of\s*([^.,]+)",
        ]

    async def scrape_job_description(self, job_url: str, page: Page) -> Dict[str, Any]:
        """
        Scrape detailed job description from a job URL.

        Args:
            job_url: URL of the job posting
            page: Playwright page instance

        Returns:
            Dictionary with detailed job information
        """
        try:
            console.print(f"[cyan]🔍 Scraping job description: {job_url}[/cyan]")

            # Navigate to job page
            await page.goto(job_url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)

            # Extract basic job information
            job_data = await self._extract_basic_info(page)

            # Extract detailed description
            description = await self._extract_job_description(page)
            job_data["description"] = description

            # Extract experience requirements
            experience_info = self._extract_experience_requirements(description)
            job_data["experience_requirements"] = experience_info

            # Extract skills and requirements
            skills_info = self._extract_skills_and_requirements(description)
            job_data["skills_requirements"] = skills_info

            # Generate summary
            summary = self._generate_job_summary(job_data)
            job_data["summary"] = summary

            # Extract additional metadata
            metadata = await self._extract_metadata(page)
            job_data.update(metadata)

            console.print(f"[green]✅ Successfully scraped job description[/green]")
            return job_data

        except Exception as e:
            console.print(f"[red]❌ Error scraping job description: {e}[/red]")
            return {"url": job_url, "error": str(e), "scraped_at": datetime.now().isoformat()}

    async def _extract_basic_info(self, page: Page) -> Dict[str, Any]:
        """Extract basic job information from the page."""
        basic_info = {
            "title": "",
            "company": "",
            "location": "",
            "job_type": "",
            "salary_range": "",
            "posted_date": "",
            "scraped_at": datetime.now().isoformat(),
        }

        try:
            # Common selectors for job information
            selectors = {
                "title": [
                    'h1[class*="title"]',
                    'h1[class*="job"]',
                    ".job-title",
                    ".title",
                    "h1",
                    '[data-testid="job-title"]',
                ],
                "company": [
                    '[class*="company"]',
                    ".company-name",
                    ".employer",
                    '[data-testid="company-name"]',
                ],
                "location": [
                    '[class*="location"]',
                    ".job-location",
                    ".location",
                    '[data-testid="location"]',
                ],
                "job_type": [
                    '[class*="type"]',
                    ".job-type",
                    ".employment-type",
                    '[data-testid="job-type"]',
                ],
                "salary_range": [
                    '[class*="salary"]',
                    ".salary",
                    ".compensation",
                    '[data-testid="salary"]',
                ],
                "posted_date": [
                    '[class*="date"]',
                    ".posted-date",
                    ".date-posted",
                    '[data-testid="posted-date"]',
                ],
            }

            for field, field_selectors in selectors.items():
                for selector in field_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            text = await element.text_content()
                            if text and text.strip():
                                basic_info[field] = text.strip()
                                break
                    except:
                        continue

        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting basic info: {e}[/yellow]")

        return basic_info

    async def _extract_job_description(self, page: Page) -> str:
        """Extract the full job description text."""
        description_selectors = [
            '[class*="description"]',
            ".job-description",
            ".description",
            '[class*="details"]',
            ".job-details",
            ".details",
            '[class*="content"]',
            ".job-content",
            ".content",
            "main",
            "article",
        ]

        for selector in description_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text and len(text.strip()) > 100:  # Minimum description length
                        return text.strip()
            except:
                continue

        return ""

    def _extract_experience_requirements(self, description: str) -> Dict[str, Any]:
        """Extract experience requirements from job description."""
        experience_info = {
            "years_required": None,
            "level": "unknown",
            "entry_level": False,
            "senior_level": False,
            "experience_text": "",
            "confidence": 0.0,
        }

        if not description:
            return experience_info

        description_lower = description.lower()

        # Check for years of experience
        for pattern in self.experience_patterns["years"]:
            matches = re.findall(pattern, description_lower, re.IGNORECASE)
            if matches:
                years = int(matches[0])
                experience_info["years_required"] = years
                experience_info["confidence"] += 0.4
                break

        # Check for entry level indicators
        entry_level_matches = 0
        for pattern in self.experience_patterns["entry_level"]:
            if re.search(pattern, description_lower, re.IGNORECASE):
                entry_level_matches += 1

        if entry_level_matches > 0:
            experience_info["entry_level"] = True
            experience_info["level"] = "entry"
            experience_info["confidence"] += 0.3

        # Check for senior level indicators
        senior_level_matches = 0
        for pattern in self.experience_patterns["senior_level"]:
            if re.search(pattern, description_lower, re.IGNORECASE):
                senior_level_matches += 1

        if senior_level_matches > 0:
            experience_info["senior_level"] = True
            experience_info["level"] = "senior"
            experience_info["confidence"] += 0.3

        # Extract experience-related text
        experience_sentences = []
        sentences = re.split(r"[.!?]", description)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(
                keyword in sentence_lower
                for keyword in ["experience", "years", "level", "senior", "junior", "entry"]
            ):
                experience_sentences.append(sentence.strip())

        experience_info["experience_text"] = " ".join(
            experience_sentences[:3]
        )  # First 3 relevant sentences

        return experience_info

    def _extract_skills_and_requirements(self, description: str) -> Dict[str, Any]:
        """Extract skills and requirements from job description."""
        skills_info = {
            "technical_skills": [],
            "soft_skills": [],
            "tools": [],
            "certifications": [],
            "education": "",
            "requirements_text": "",
        }

        if not description:
            return skills_info

        description_lower = description.lower()

        # Common technical skills
        technical_skills = [
            "python",
            "java",
            "javascript",
            "sql",
            "html",
            "css",
            "react",
            "angular",
            "vue",
            "node.js",
            "express",
            "django",
            "flask",
            "spring",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "gcp",
            "git",
            "jenkins",
            "jira",
            "confluence",
            "tableau",
            "power bi",
            "excel",
            "r",
            "matlab",
            "sas",
            "spss",
            "machine learning",
            "data analysis",
            "statistics",
            "etl",
            "data warehousing",
            "big data",
            "hadoop",
            "spark",
            "kafka",
            "redis",
            "mongodb",
            "postgresql",
            "mysql",
        ]

        # Common soft skills
        soft_skills = [
            "communication",
            "leadership",
            "teamwork",
            "problem solving",
            "analytical",
            "critical thinking",
            "time management",
            "organization",
            "adaptability",
            "creativity",
            "attention to detail",
            "multitasking",
            "collaboration",
        ]

        # Extract technical skills
        for skill in technical_skills:
            if skill in description_lower:
                skills_info["technical_skills"].append(skill)

        # Extract soft skills
        for skill in soft_skills:
            if skill in description_lower:
                skills_info["soft_skills"].append(skill)

        # Extract tools and technologies
        tool_patterns = [
            r"([A-Z][A-Za-z0-9]+\.js)",
            r"([A-Z][A-Za-z0-9]+\.py)",
            r"([A-Z][A-Za-z0-9]+\.net)",
            r"([A-Z][A-Za-z0-9]+\.io)",
            r"([A-Z][A-Za-z0-9]+\.com)",
        ]

        for pattern in tool_patterns:
            matches = re.findall(pattern, description)
            skills_info["tools"].extend(matches)

        # Extract education requirements
        education_keywords = ["bachelor", "master", "phd", "degree", "diploma", "certification"]
        education_sentences = []
        sentences = re.split(r"[.!?]", description)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in education_keywords):
                education_sentences.append(sentence.strip())

        skills_info["education"] = " ".join(education_sentences[:2])

        # Extract requirements text
        requirements_sentences = []
        sentences = re.split(r"[.!?]", description)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(
                keyword in sentence_lower
                for keyword in ["require", "must", "should", "prefer", "qualification"]
            ):
                requirements_sentences.append(sentence.strip())

        skills_info["requirements_text"] = " ".join(requirements_sentences[:5])

        return skills_info

    def _generate_job_summary(self, job_data: Dict[str, Any]) -> str:
        """Generate a concise summary of the job posting."""
        summary_parts = []

        # Basic info
        if job_data.get("title"):
            summary_parts.append(f"Position: {job_data['title']}")

        if job_data.get("company"):
            summary_parts.append(f"Company: {job_data['company']}")

        if job_data.get("location"):
            summary_parts.append(f"Location: {job_data['location']}")

        # Experience level
        experience = job_data.get("experience_requirements", {})
        if experience.get("years_required"):
            summary_parts.append(f"Experience: {experience['years_required']} years")
        elif experience.get("entry_level"):
            summary_parts.append("Experience: Entry level")
        elif experience.get("senior_level"):
            summary_parts.append("Experience: Senior level")

        # Key skills
        skills = job_data.get("skills_requirements", {})
        if skills.get("technical_skills"):
            top_skills = skills["technical_skills"][:5]
            summary_parts.append(f"Key Skills: {', '.join(top_skills)}")

        # Experience text if available
        if experience.get("experience_text"):
            summary_parts.append(f"Experience Details: {experience['experience_text'][:200]}...")

        return " | ".join(summary_parts)

    async def _extract_metadata(self, page: Page) -> Dict[str, Any]:
        """Extract additional metadata from the page."""
        metadata = {
            "ats_system": "unknown",
            "application_url": "",
            "benefits": [],
            "remote_work": False,
            "relocation": False,
        }

        try:
            # Detect ATS system from URL or page content
            url = page.url
            if "workday" in url.lower():
                metadata["ats_system"] = "workday"
            elif "lever" in url.lower():
                metadata["ats_system"] = "lever"
            elif "greenhouse" in url.lower():
                metadata["ats_system"] = "greenhouse"
            elif "bamboohr" in url.lower():
                metadata["ats_system"] = "bamboohr"
            elif "icims" in url.lower():
                metadata["ats_system"] = "icims"

            # Check for remote work indicators
            page_content = await page.content()
            if any(
                term in page_content.lower()
                for term in ["remote", "work from home", "wfh", "telecommute"]
            ):
                metadata["remote_work"] = True

            # Check for relocation assistance
            if any(
                term in page_content.lower()
                for term in ["relocation", "relocate", "moving assistance"]
            ):
                metadata["relocation"] = True

        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting metadata: {e}[/yellow]")

        return metadata


async def scrape_job_description_async(job_url: str) -> Dict[str, Any]:
    """
    Async function to scrape job description.

    Args:
        job_url: URL of the job posting

    Returns:
        Dictionary with detailed job information
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            scraper = EnhancedJobDescriptionScraper()
            result = await scraper.scrape_job_description(job_url, page)
            return result
        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    # Test the scraper
    import asyncio

    test_url = "https://www.example.com/job-posting"
    result = asyncio.run(scrape_job_description_async(test_url))
    console.print(f"[cyan]Test Result: {json.dumps(result, indent=2)}[/cyan]")
