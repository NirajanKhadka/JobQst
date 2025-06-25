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
            "match_factors": []
        }
        
        # Basic analysis logic
        if job.get("title") and self.profile.get("skills"):
            title_lower = job["title"].lower()
            skills = [skill.lower() for skill in self.profile["skills"]]
            
            # Check for skill matches
            skill_matches = sum(1 for skill in skills if skill in title_lower)
            if skill_matches > 0:
                analysis["relevance_score"] = min(1.0, skill_matches / len(skills))
                analysis["match_factors"].append(f"Skills match: {skill_matches} skills found")
        
        # Location analysis
        if job.get("location") and self.profile.get("location"):
            job_location = job["location"].lower()
            profile_location = self.profile["location"].lower()
            
            if profile_location in job_location or job_location in profile_location:
                analysis["compatibility_score"] += 0.3
                analysis["match_factors"].append("Location match")
        
        # Experience level analysis
        if job.get("experience_level"):
            analysis["match_factors"].append(f"Experience level: {job['experience_level']}")
        
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
            analyzed_jobs, 
            key=lambda x: x["analysis"]["relevance_score"], 
            reverse=True
        )
        
        return recommended_jobs[:10]  # Return top 10 recommendations 