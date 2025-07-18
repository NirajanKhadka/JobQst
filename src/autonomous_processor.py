#!/usr/bin/env python3
"""
Autonomous Job Processing System

This module orchestrates the end-to-end process of fetching, analyzing,
and updating job entries in the database without manual intervention.

It is designed to run as a standalone server, periodically processing new jobs.
"""

import asyncio
import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple

import aiohttp
from bs4 import BeautifulSoup

from core.job_database import ModernJobDatabase

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class JobContentExtractor:
    """Extracts detailed content from a job posting URL."""

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def extract_details(self, url: str) -> Dict[str, Any]:
        """Fetches and parses the job details from a URL."""
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                job_text = soup.get_text().lower()

                return {
                    "experience_level": self._extract_experience(job_text),
                    "salary_info": self._extract_salary(job_text),
                    "job_type": self._extract_job_type(job_text),
                    "requirements": self._extract_requirements(job_text),
                }
        except aiohttp.ClientError as e:
            logger.warning(f"HTTP error fetching {url}: {e}")
        except Exception as e:
            logger.error(f"Error extracting details from {url}: {e}")
        return {}

    def _extract_experience(self, text: str) -> str:
        patterns = {
            "entry": [r"entry.level", r"0-2 years", r"junior", r"graduate"],
            "mid": [r"2-5 years", r"mid.level", r"intermediate", r"3\+ years"],
            "senior": [r"5-8 years", r"senior", r"5\+ years", r"lead"],
            "expert": [r"8\+ years", r"10\+ years", r"expert", r"architect"],
        }
        scores = {level: sum(1 for p in ps if re.search(p, text)) for level, ps in patterns.items()}
        return max(scores, key=scores.get) if any(scores.values()) else "mid"

    def _extract_salary(self, text: str) -> str:
        patterns = [
            r"\$[\d,]+(?:k|,000)?\s*(?:-|to)\s*\$[\d,]+(?:k|,000)?",
            r"\$[\d,]+(?:k|,000)?",
        ]
        for pattern in patterns:
            if match := re.search(pattern, text, re.IGNORECASE):
                return match.group().strip()
        return ""

    def _extract_job_type(self, text: str) -> str:
        if any(word in text for word in ["remote", "work from home"]):
            return "remote"
        if "hybrid" in text:
            return "hybrid"
        return "onsite"

    def _extract_requirements(self, text: str) -> str:
        keywords = ["python", "java", "sql", "aws", "docker", "react"]
        return ", ".join([kw for kw in keywords if kw in text][:10])


class AutonomousJobAnalyzer:
    """Analyzes a job based on a rule-based scoring system."""

    def analyze(self, job: Dict[str, Any], extracted_details: Dict[str, Any]) -> Dict[str, Any]:
        """Performs rule-based analysis and scoring."""
        score = 0
        reasons = []

        # Score based on title
        title_score, title_reasons = self._score_title(job.get("title", ""))
        score += title_score
        reasons.extend(title_reasons)

        # Score based on other attributes
        # ... (add other scoring logic here for company, location, etc.) ...

        score = min(100, score)
        decision = "skip"
        if score >= 70:
            decision = "apply"
        elif score >= 45:
            decision = "review"

        return {
            "match_score": score,
            "decision": decision,
            "reasoning": "; ".join(reasons),
        }

    def _score_title(self, title: str) -> Tuple[int, List[str]]:
        title = title.lower()
        score = 0
        reasons = []
        keywords = {"software": 15, "developer": 15, "python": 10, "data": 12}
        for keyword, points in keywords.items():
            if keyword in title:
                score += points
                reasons.append(f"Title contains '{keyword}' (+{points})")
        return min(score, 30), reasons


class AutonomousProcessor:
    """Main orchestrator for the autonomous job processing workflow."""

    def __init__(self, profile_name: str = "Nirajan"):
        self.profile_name = profile_name
        self.db = ModernJobDatabase(f"profiles/{profile_name}/{profile_name}.db")
        self.is_running = False

    async def run_server(self, interval_minutes: int = 30):
        """Starts the continuous processing server."""
        logger.info(f"🚀 Starting Autonomous Server for profile '{self.profile_name}'.")
        self.is_running = True
        try:
            async with aiohttp.ClientSession() as session:
                while self.is_running:
                    await self.process_batch(session)
                    logger.info(f"💤 Waiting {interval_minutes} minutes for next cycle...")
                    await asyncio.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            logger.info("🛑 Server stopped by user.")
        except Exception as e:
            logger.critical(f"❌ Server error: {e}", exc_info=True)
        finally:
            self.is_running = False
            logger.info("✅ Server shut down gracefully.")

    async def process_batch(self, session: aiohttp.ClientSession, limit: int = 5):
        """Processes a single batch of unprocessed jobs."""
        logger.info(f"🤖 Processing batch of {limit} jobs...")
        unprocessed_jobs = self.db.get_jobs_by_status("scraped", limit)
        if not unprocessed_jobs:
            logger.info("No unprocessed jobs found.")
            return

        extractor = JobContentExtractor(session)
        analyzer = AutonomousJobAnalyzer()

        for job in unprocessed_jobs:
            details = await extractor.extract_details(job["url"])
            analysis = analyzer.analyze(job, details)

            full_analysis_data = {**job, **details, **analysis}
            self.db.update_job_with_analysis(job["job_id"], full_analysis_data)

            logger.info(f"Processed job {job['job_id']}: {analysis['decision']} (Score: {analysis['match_score']})")
            await asyncio.sleep(1)  # Respect server rate limits


async def main():
    """Main entry point for testing the processor."""
    processor = AutonomousProcessor("Nirajan")
    logger.info("🧪 Running a single batch test...")
    async with aiohttp.ClientSession() as session:
        await processor.process_batch(session, limit=5)
    logger.info("✅ Test batch finished.")

if __name__ == "__main__":
    # To run the continuous server:
    # processor = AutonomousProcessor("Nirajan")
    # asyncio.run(processor.run_server())
    asyncio.run(main())
