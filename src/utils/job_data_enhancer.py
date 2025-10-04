"""
Job Data Enhancer Module
Provides job data enhancement and enrichment functionality.
"""

from typing import Dict, List, Optional, Any
from rich.console import Console
import re


class JobDataEnhancer:
    """Enhances job data with additional information and analysis."""

    def __init__(self, profile: Dict[str, Any], enable_rcip: bool = True):
        self.profile = profile
        self.console = Console()
        self.enable_rcip = enable_rcip

        # Initialize RCIP service if enabled
        if self.enable_rcip:
            try:
                from src.services.rcip_enrichment_service import get_rcip_service

                self.rcip_service = get_rcip_service()
            except Exception as e:
                self.console.print(
                    f"[yellow]Warning: Could not initialize RCIP service: {e}[/yellow]"
                )
                self.rcip_service = None
        else:
            self.rcip_service = None

    def enhance_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance a single job with additional data."""
        Improved_job = {**job}

        # Extract salary information
        Improved_job["salary_info"] = self.extract_salary_info(job)

        # Extract experience level
        Improved_job["experience_level"] = self.extract_experience_level(job)

        # Extract skills (FIXED: was missing this call)
        Improved_job["extracted_skills"] = self.extract_skills(job)

        # Calculate relevance score (FIXED: pass Improved_job with extracted_skills)
        Improved_job["relevance_score"] = self.calculate_relevance_score(Improved_job)

        # Add location analysis
        Improved_job["location_analysis"] = self.analyze_location(job)

        # Add company analysis
        Improved_job["company_analysis"] = self.analyze_company(job)

        # Apply RCIP enrichment if enabled
        if self.rcip_service:
            try:
                Improved_job = self.rcip_service.enrich_job(Improved_job)
            except Exception as e:
                self.console.print(f"[yellow]Warning: RCIP enrichment failed for job: {e}[/yellow]")

        return Improved_job

    def enhance_jobs_batch(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance multiple jobs."""
        Improved_jobs = []

        for job in jobs:
            Improved_job = self.enhance_job(job)
            Improved_jobs.append(Improved_job)

        return Improved_jobs

    def extract_salary_info(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Extract salary information from job description."""
        salary_info = {
            "min_salary": None,
            "max_salary": None,
            "currency": "USD",
            "period": "yearly",
            "confidence": "low",
        }

        description = job.get("description", "")
        title = job.get("title", "")

        # Look for salary patterns
        salary_patterns = [
            r"\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*-\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*to\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*-\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|dollars?)",
        ]

        for pattern in salary_patterns:
            matches = re.findall(pattern, description + " " + title, re.IGNORECASE)
            if matches:
                try:
                    min_val = float(matches[0][0].replace(",", ""))
                    max_val = float(matches[0][1].replace(",", ""))
                    salary_info.update(
                        {"min_salary": min_val, "max_salary": max_val, "confidence": "medium"}
                    )
                    break
                except (ValueError, IndexError):
                    continue

        return salary_info

    def extract_experience_level(self, job: Dict[str, Any]) -> str:
        """Extract experience level from job description."""
        description = job.get("description", "").lower()
        title = job.get("title", "").lower()
        text = description + " " + title

        # Experience level keywords
        levels = {
            "entry": [
                "entry level",
                "junior",
                "0-2 years",
                "1-2 years",
                "new grad",
                "recent graduate",
            ],
            "mid": ["mid level", "intermediate", "3-5 years", "4-6 years", "experienced"],
            "senior": ["senior", "lead", "5+ years", "6+ years", "expert", "principal"],
            "executive": ["executive", "director", "vp", "vice president", "chief", "c-level"],
        }

        for level, keywords in levels.items():
            if any(keyword in text for keyword in keywords):
                return level

        return "unknown"

    def extract_skills(self, job: Dict[str, Any]) -> List[str]:
        """Extract skills from job description."""
        # Combine all available text fields for comprehensive analysis
        job_text = " ".join(
            [
                job.get("title", ""),
                job.get("summary", ""),
                job.get("description", ""),
            ]
        ).lower()

        # Common programming languages and technologies
        skills = [
            "python",
            "javascript",
            "java",
            "c++",
            "c#",
            "php",
            "ruby",
            "go",
            "rust",
            "html",
            "css",
            "react",
            "angular",
            "vue",
            "node.js",
            "django",
            "flask",
            "sql",
            "mongodb",
            "postgresql",
            "mysql",
            "redis",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "gcp",
            "git",
            "jenkins",
            "agile",
            "scrum",
            # Data analysis skills
            "pandas",
            "numpy",
            "tableau",
            "power bi",
            "excel",
            "r",
            "sas",
            "spss",
            "machine learning",
            "data analysis",
            "statistics",
            "analytics",
        ]

        found_skills = []
        for skill in skills:
            if skill in job_text:
                found_skills.append(skill)

        return found_skills

    def calculate_relevance_score(self, job: Dict[str, Any]) -> float:
        """Calculate relevance score based on profile match."""
        score = 0.0

        # Combine all job text for comprehensive analysis
        job_text = " ".join(
            [
                job.get("title", ""),
                job.get("summary", ""),
                job.get("description", ""),
            ]
        ).lower()

        # Skill matching analysis
        if self.profile.get("skills") and job_text:
            profile_skills = [skill.lower() for skill in self.profile["skills"]]
            skill_matches = []

            for skill in profile_skills:
                if skill in job_text:
                    skill_matches.append(skill)

            if skill_matches:
                skill_score = len(skill_matches) / len(profile_skills)
                score += min(0.5, skill_score)  # Cap at 0.5 for skills

        # Keyword matching analysis
        if self.profile.get("keywords") and job_text:
            profile_keywords = [kw.lower() for kw in self.profile["keywords"]]
            keyword_matches = []

            for keyword in profile_keywords:
                if keyword in job_text:
                    keyword_matches.append(keyword)

            if keyword_matches:
                keyword_score = len(keyword_matches) / len(profile_keywords)
                score += min(0.3, keyword_score * 0.3)  # Cap at 0.3 for keywords

        # Location match
        if self.profile.get("location") and job.get("location"):
            profile_location = self.profile["location"].lower()
            job_location = job["location"].lower()

            if profile_location in job_location or job_location in profile_location:
                score += 0.2

        # Experience level match
        if self.profile.get("experience_level") and job.get("experience_level"):
            job_exp = job["experience_level"].lower()
            profile_exp = self.profile["experience_level"].lower()

            # Normalize experience levels for comparison
            exp_mapping = {
                "entry level": "entry",
                "junior": "entry",
                "mid level": "mid",
                "intermediate": "mid",
                "senior": "senior",
                "lead": "senior",
            }

            normalized_job_exp = exp_mapping.get(job_exp, job_exp)
            normalized_profile_exp = exp_mapping.get(profile_exp, profile_exp)

            if normalized_job_exp == normalized_profile_exp:
                score += 0.1

        return min(1.0, score)

    def analyze_location(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze job location."""
        location = job.get("location", "")

        analysis = {
            "is_remote": False,
            "is_hybrid": False,
            "is_onsite": True,
            "country": "unknown",
            "city": "unknown",
        }

        if not location:
            return analysis

        location_lower = location.lower()

        # Check for remote indicators
        remote_indicators = ["remote", "work from home", "wfh", "virtual", "telecommute"]
        if any(indicator in location_lower for indicator in remote_indicators):
            analysis["is_remote"] = True
            analysis["is_onsite"] = False

        # Check for hybrid indicators
        hybrid_indicators = ["hybrid", "flexible", "partially remote"]
        if any(indicator in location_lower for indicator in hybrid_indicators):
            analysis["is_hybrid"] = True
            analysis["is_onsite"] = False

        return analysis

    def analyze_company(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze company information."""
        company = job.get("company", "")

        analysis = {"size": "unknown", "industry": "unknown", "type": "unknown"}

        if not company:
            return analysis

        # Basic company analysis (can be Improved with external APIs)
        company_lower = company.lower()

        # Check for company size indicators
        if any(word in company_lower for word in ["startup", "small", "early stage"]):
            analysis["size"] = "small"
        elif any(word in company_lower for word in ["enterprise", "large", "fortune"]):
            analysis["size"] = "large"
        else:
            analysis["size"] = "medium"

        return analysis
