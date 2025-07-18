"""
Job Analyzer Module
Provides job analysis functionality for the AutoJobAgent system.
"""

from typing import Dict, List, Optional, Any
from rich.console import Console


class JobAnalyzer:
    """Analyzes job postings for relevance and compatibility."""

    def __init__(self, profile: Dict[str, Any]):
        self.profile = profile
        self.console = Console()

    def analyze_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single job for relevance and compatibility."""
        analysis = {
            "relevance_score": 0.0,
            "compatibility_score": 0.0,
            "recommendations": [],
            "risks": [],
            "match_factors": [],
        }

        # Combine all job text for comprehensive analysis
        job_text = " ".join(
            [
                job.get("title", ""),
                job.get("summary", ""),
                job.get("description", ""),
            ]
        ).lower()

        score = 0.0

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
                analysis["match_factors"].append(
                    f"Skills match: {len(skill_matches)}/{len(profile_skills)} skills found"
                )

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
                analysis["match_factors"].append(
                    f"Keywords match: {len(keyword_matches)}/{len(profile_keywords)} keywords found"
                )

        # Location analysis
        if job.get("location") and self.profile.get("location"):
            job_location = job["location"].lower()
            profile_location = self.profile["location"].lower()

            if profile_location in job_location or job_location in profile_location:
                score += 0.2
                analysis["match_factors"].append("Location match")

        # Experience level analysis
        if job.get("experience_level") and self.profile.get("experience_level"):
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
                analysis["match_factors"].append(f"Experience level match: {job_exp}")
            else:
                analysis["match_factors"].append(f"Experience level: {job_exp}")

        # Set both relevance and compatibility to the same calculated score
        analysis["relevance_score"] = min(1.0, score)
        analysis["compatibility_score"] = min(1.0, score)

        return analysis

    def analyze_jobs_batch(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze multiple jobs and return analysis results."""
        analyzed_jobs = []

        for job in jobs:
            analysis = self.analyze_job(job)
            job_with_analysis = {**job, "analysis": analysis}
            analyzed_jobs.append(job_with_analysis)

        return analyzed_jobs

    def get_recommendations(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get job recommendations based on analysis."""
        analyzed_jobs = self.analyze_jobs_batch(jobs)

        # Sort by relevance score
        recommended_jobs = sorted(
            analyzed_jobs, key=lambda x: x["analysis"]["relevance_score"], reverse=True
        )

        return recommended_jobs[:10]  # Return top 10 recommendations
