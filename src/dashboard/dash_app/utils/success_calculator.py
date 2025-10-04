"""
Application success prediction utility for dashboard enhancements.
Provides rule-based success prediction using skill matching.
"""

from typing import Dict, List, Optional, Tuple
import logging
from collections import Counter, defaultdict

from .skill_analyzer import (
    extract_skills_from_text,
    normalize_user_skills,
    calculate_skill_coverage
)

logger = logging.getLogger(__name__)


# ============================================================================
# Job Role Categorization
# ============================================================================

JOB_ROLE_KEYWORDS = {
    "Data Analyst": [
        r"data analyst", r"business analyst", r"analytics", r"reporting analyst",
        r"data specialist"
    ],
    "Data Scientist": [
        r"data scientist", r"machine learning", r"ml engineer", r"ai engineer",
        r"research scientist"
    ],
    "Data Engineer": [
        r"data engineer", r"etl", r"pipeline", r"big data engineer",
        r"data infrastructure"
    ],
    "Business Intelligence": [
        r"business intelligence", r"bi analyst", r"bi developer", r"tableau",
        r"power bi"
    ],
    "Software Engineer": [
        r"software engineer", r"software developer", r"backend", r"frontend",
        r"full stack"
    ],
    "Database Administrator": [
        r"database administrator", r"dba", r"database engineer", r"sql admin"
    ],
    "Product Analyst": [
        r"product analyst", r"product manager", r"product owner", r"product data"
    ],
    "Research Analyst": [
        r"research analyst", r"market research", r"quantitative analyst",
        r"research associate"
    ]
}


def categorize_job_role(job_title: str) -> str:
    """
    Categorize a job title into a role category.
    
    Args:
        job_title: Job title string
    
    Returns:
        Role category name or "Other"
    """
    import re
    
    if not job_title:
        return "Other"
    
    title_lower = job_title.lower()
    
    for role, keywords in JOB_ROLE_KEYWORDS.items():
        for keyword in keywords:
            if re.search(keyword, title_lower):
                return role
    
    return "Other"


# ============================================================================
# Success Prediction Functions
# ============================================================================

def calculate_success_probability(
    user_skills: List[str],
    job_skills: List[str],
    user_experience_years: Optional[int] = None,
    job_experience_required: Optional[int] = None
) -> Tuple[float, str]:
    """
    Calculate success probability for a single job.
    
    Args:
        user_skills: List of user's skills
        job_skills: List of required job skills
        user_experience_years: User's years of experience
        job_experience_required: Required years of experience
    
    Returns:
        Tuple of (probability 0-100, confidence level)
    """
    # Base probability from skill coverage
    skill_coverage = calculate_skill_coverage(user_skills, job_skills)
    probability = skill_coverage
    
    # Adjust for experience if available
    if user_experience_years is not None and job_experience_required is not None:
        if user_experience_years >= job_experience_required:
            # Bonus for meeting experience requirement
            probability = min(100, probability + 10)
        elif user_experience_years >= job_experience_required * 0.75:
            # Small bonus for being close
            probability = min(100, probability + 5)
        else:
            # Penalty for not meeting experience
            probability = max(0, probability - 10)
    
    # Determine confidence level
    if len(job_skills) >= 5:
        confidence = "high"
    elif len(job_skills) >= 3:
        confidence = "medium"
    else:
        confidence = "low"
    
    return round(probability, 1), confidence


def predict_success_by_role(
    user_skills: List[str],
    jobs: List[Dict],
    user_experience_years: Optional[int] = None
) -> List[Dict]:
    """
    Predict application success probability for different job roles.
    
    Args:
        user_skills: List of user's current skills
        jobs: List of job dictionaries
        user_experience_years: User's years of experience
    
    Returns:
        List of prediction dictionaries with:
            - job_type: str (e.g., "Data Analyst roles")
            - percentage: float (success probability 0-100)
            - reason: str (explanation of the prediction)
            - matched_skills: List[str]
            - missing_skills: List[str]
            - confidence: str (high/medium/low)
            - job_count: int (number of jobs in this category)
    """
    try:
        if not jobs:
            logger.warning("No jobs provided for success prediction")
            return []
        
        # Normalize user skills
        user_skills_normalized = normalize_user_skills(user_skills)
        
        # Group jobs by role
        jobs_by_role = defaultdict(list)
        for job in jobs:
            title = job.get("title", "")
            role = categorize_job_role(title)
            jobs_by_role[role].append(job)
        
        # Calculate predictions for each role
        predictions = []
        
        for role, role_jobs in jobs_by_role.items():
            if role == "Other" and len(role_jobs) < 3:
                continue  # Skip "Other" if too few jobs
            
            # Extract skills from all jobs in this role
            all_role_skills = set()
            for job in role_jobs:
                description = job.get("description", "") or ""
                title = job.get("title", "") or ""
                combined_text = f"{title} {description}"
                job_skills = extract_skills_from_text(combined_text)
                all_role_skills.update(job_skills)
            
            # Calculate skill match
            matched_skills = user_skills_normalized.intersection(all_role_skills)
            missing_skills = all_role_skills - user_skills_normalized
            
            # Calculate success probability
            if all_role_skills:
                skill_match_percentage = (len(matched_skills) / len(all_role_skills)) * 100
            else:
                skill_match_percentage = 50.0  # Default if no skills detected
            
            # Adjust based on number of jobs
            if len(role_jobs) >= 10:
                confidence = "high"
            elif len(role_jobs) >= 5:
                confidence = "medium"
            else:
                confidence = "low"
            
            # Generate reason
            if skill_match_percentage >= 70:
                reason = (
                    f"Strong match! You have {len(matched_skills)} out of "
                    f"{len(all_role_skills)} key skills for {role} positions."
                )
            elif skill_match_percentage >= 50:
                reason = (
                    f"Good potential. You have {len(matched_skills)} key skills, "
                    f"but consider learning {len(missing_skills)} more to improve your chances."
                )
            else:
                reason = (
                    f"Developing match. Focus on gaining {len(missing_skills)} "
                    f"additional skills to be more competitive for {role} roles."
                )
            
            predictions.append({
                "job_type": f"{role} roles",
                "percentage": round(skill_match_percentage, 1),
                "reason": reason,
                "matched_skills": sorted(list(matched_skills))[:10],  # Top 10
                "missing_skills": sorted(list(missing_skills))[:10],  # Top 10
                "confidence": confidence,
                "job_count": len(role_jobs)
            })
        
        # Sort by percentage (descending)
        predictions.sort(key=lambda x: x["percentage"], reverse=True)
        
        logger.info(f"Generated {len(predictions)} role-based predictions")
        return predictions
    
    except Exception as e:
        logger.error(f"Error in success prediction: {e}", exc_info=True)
        return []


def calculate_overall_success_score(
    user_skills: List[str],
    jobs: List[Dict],
    user_experience_years: Optional[int] = None
) -> Dict:
    """
    Calculate overall success score across all jobs.
    
    Args:
        user_skills: List of user's skills
        jobs: List of job dictionaries
        user_experience_years: User's years of experience
    
    Returns:
        Dictionary with:
            - overall_score: float (0-100)
            - high_match_count: int (jobs with >70% match)
            - medium_match_count: int (jobs with 50-70% match)
            - low_match_count: int (jobs with <50% match)
            - recommendation: str
    """
    try:
        if not jobs:
            return {
                "overall_score": 0.0,
                "high_match_count": 0,
                "medium_match_count": 0,
                "low_match_count": 0,
                "recommendation": "No jobs available for analysis"
            }
        
        user_skills_normalized = normalize_user_skills(user_skills)
        
        match_scores = []
        high_match = 0
        medium_match = 0
        low_match = 0
        
        for job in jobs:
            description = job.get("description", "") or ""
            title = job.get("title", "") or ""
            combined_text = f"{title} {description}"
            
            job_skills = extract_skills_from_text(combined_text)
            
            if job_skills:
                matched = user_skills_normalized.intersection(job_skills)
                score = (len(matched) / len(job_skills)) * 100
                match_scores.append(score)
                
                if score >= 70:
                    high_match += 1
                elif score >= 50:
                    medium_match += 1
                else:
                    low_match += 1
        
        # Calculate overall score
        overall_score = sum(match_scores) / len(match_scores) if match_scores else 0.0
        
        # Generate recommendation
        if overall_score >= 70:
            recommendation = (
                "Excellent! You're well-positioned for most of these roles. "
                "Focus on applying to high-match positions."
            )
        elif overall_score >= 50:
            recommendation = (
                "Good foundation. Consider upskilling in 2-3 key areas to "
                "increase your competitiveness."
            )
        else:
            recommendation = (
                "Focus on skill development. Identify the most in-demand skills "
                "and create a learning plan."
            )
        
        return {
            "overall_score": round(overall_score, 1),
            "high_match_count": high_match,
            "medium_match_count": medium_match,
            "low_match_count": low_match,
            "recommendation": recommendation
        }
    
    except Exception as e:
        logger.error(f"Error calculating overall success score: {e}", exc_info=True)
        return {
            "overall_score": 0.0,
            "high_match_count": 0,
            "medium_match_count": 0,
            "low_match_count": 0,
            "recommendation": "Error calculating success score"
        }


def get_top_matching_jobs(
    user_skills: List[str],
    jobs: List[Dict],
    top_n: int = 10
) -> List[Dict]:
    """
    Get top N jobs that best match user's skills.
    
    Args:
        user_skills: List of user's skills
        jobs: List of job dictionaries
        top_n: Number of top jobs to return
    
    Returns:
        List of job dictionaries with added 'match_score' field
    """
    try:
        user_skills_normalized = normalize_user_skills(user_skills)
        
        jobs_with_scores = []
        
        for job in jobs:
            description = job.get("description", "") or ""
            title = job.get("title", "") or ""
            combined_text = f"{title} {description}"
            
            job_skills = extract_skills_from_text(combined_text)
            
            if job_skills:
                matched = user_skills_normalized.intersection(job_skills)
                score = (len(matched) / len(job_skills)) * 100
            else:
                score = 0.0
            
            job_copy = job.copy()
            job_copy["calculated_match_score"] = round(score, 1)
            job_copy["matched_skills_count"] = len(matched) if job_skills else 0
            jobs_with_scores.append(job_copy)
        
        # Sort by match score
        jobs_with_scores.sort(key=lambda x: x["calculated_match_score"], reverse=True)
        
        return jobs_with_scores[:top_n]
    
    except Exception as e:
        logger.error(f"Error getting top matching jobs: {e}", exc_info=True)
        return []


def generate_application_strategy(
    user_skills: List[str],
    jobs: List[Dict],
    user_experience_years: Optional[int] = None
) -> Dict:
    """
    Generate application strategy recommendations.
    
    Args:
        user_skills: List of user's skills
        jobs: List of job dictionaries
        user_experience_years: User's years of experience
    
    Returns:
        Dictionary with strategy recommendations
    """
    try:
        predictions = predict_success_by_role(user_skills, jobs, user_experience_years)
        overall = calculate_overall_success_score(user_skills, jobs, user_experience_years)
        
        # Find best role match
        best_role = predictions[0] if predictions else None
        
        # Generate strategy
        strategy = {
            "primary_focus": best_role["job_type"] if best_role else "General roles",
            "application_priority": [],
            "skill_development_plan": [],
            "estimated_success_rate": overall["overall_score"]
        }
        
        # Application priority
        if overall["high_match_count"] > 0:
            strategy["application_priority"].append(
                f"Apply immediately to {overall['high_match_count']} high-match positions"
            )
        
        if overall["medium_match_count"] > 0:
            strategy["application_priority"].append(
                f"Tailor resume for {overall['medium_match_count']} medium-match positions"
            )
        
        # Skill development plan
        if predictions:
            top_missing = predictions[0]["missing_skills"][:3]
            if top_missing:
                strategy["skill_development_plan"] = [
                    f"Learn {skill} to improve match for {predictions[0]['job_type']}"
                    for skill in top_missing
                ]
        
        return strategy
    
    except Exception as e:
        logger.error(f"Error generating application strategy: {e}", exc_info=True)
        return {
            "primary_focus": "Unknown",
            "application_priority": [],
            "skill_development_plan": [],
            "estimated_success_rate": 0.0
        }
