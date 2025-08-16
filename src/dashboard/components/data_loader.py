"""
Improved Data Loader for AutoJobAgent Dashboard

This module provides Improved data loading functionality with AI analysis integration,
ensuring all job data includes comprehensive analysis results for the dashboard.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.core.job_database import get_job_db
from src.utils.profile_helpers import load_profile
from src.ai.Improved_job_analyzer import ImprovedJobAnalyzer

logger = logging.getLogger(__name__)


def load_job_data(profile_name: str) -> pd.DataFrame:
    """
    Load job data with Improved AI analysis for the dashboard.
    
    Args:
        profile_name: Name of the profile to load data for
        
    Returns:
        DataFrame with enhanced job data including AI analysis
    """
    try:
        # Load profile
        profile = load_profile(profile_name)
        if not profile:
            logger.error(f"Profile {profile_name} not found")
            return pd.DataFrame()
        
        # Get job database
        job_db = get_job_db(profile_name)
        if not job_db:
            logger.error(f"Job database for {profile_name} not found")
            return pd.DataFrame()
        
        # Get all jobs
        jobs = job_db.get_all_jobs()
        if not jobs:
            logger.info(f"No jobs found for profile {profile_name}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(jobs)
        
        # Enhance data with AI analysis if not already present
        df = _enhance_job_data(df, profile)
        
        # Add computed fields
        df = _add_computed_fields(df)
        
        logger.info(f"Loaded {len(df)} jobs for profile {profile_name}")
        return df
        
    except Exception as e:
        logger.error(f"Error loading job data for {profile_name}: {e}")
        return pd.DataFrame()


def _enhance_job_data(df: pd.DataFrame, profile: Dict) -> pd.DataFrame:
    """
    Enhance job data with AI analysis and additional fields.
    
    Args:
        df: Original job DataFrame
        profile: User profile
        
    Returns:
        Improved DataFrame
    """
    try:
        # Initialize enhanced job analyzer
        analyzer = ImprovedJobAnalyzer(profile, use_llama=True, fallback_to_rule_based=True)
        
        # Add AI analysis for jobs that don't have it
        Improved_jobs = []
        
        for idx, row in df.iterrows():
            job_dict = row.to_dict()
            
            # Check if job already has AI analysis
            if "llm_analysis" not in job_dict or not job_dict["llm_analysis"]:
                try:
                    # Perform AI analysis
                    analysis = analyzer.analyze_job(job_dict)
                    job_dict["llm_analysis"] = analysis
                    job_dict["compatibility_score"] = analysis.get("compatibility_score", 0.5)
                    job_dict["confidence"] = analysis.get("confidence", 0.8)
                except Exception as e:
                    logger.warning(f"AI analysis failed for job {job_dict.get('title', 'Unknown')}: {e}")
                    # Add default analysis
                    job_dict["llm_analysis"] = _create_default_analysis()
                    job_dict["compatibility_score"] = 0.5
                    job_dict["confidence"] = 0.5
            else:
                # Ensure compatibility_score is present
                if "compatibility_score" not in job_dict:
                    analysis = job_dict.get("llm_analysis", {})
                    job_dict["compatibility_score"] = analysis.get("compatibility_score", 0.5)
                
                if "confidence" not in job_dict:
                    analysis = job_dict.get("llm_analysis", {})
                    job_dict["confidence"] = analysis.get("confidence", 0.8)
            
            Improved_jobs.append(job_dict)
        
        # Convert back to DataFrame
        Improved_df = pd.DataFrame(Improved_jobs)
        
        return Improved_df
        
    except Exception as e:
        logger.error(f"Error enhancing job data: {e}")
        return df


def _create_default_analysis() -> Dict[str, Any]:
    """
    Create a default analysis when AI analysis fails.
    
    Returns:
        Default analysis dictionary
    """
    return {
        "compatibility_score": 0.5,
        "confidence": 0.5,
        "skill_matches": [],
        "skill_gaps": [],
        "experience_match": "unknown",
        "location_match": "unknown",
        "cultural_fit": 0.5,
        "growth_potential": 0.5,
        "recommendation": "consider",
        "reasoning": "Analysis not available"
    }


def _add_computed_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add computed fields to the DataFrame.
    
    Args:
        df: Job DataFrame
        
    Returns:
        DataFrame with computed fields
    """
    try:
        # Add status text for display
        if "status" in df.columns:
            status_mapping = {
                "new": "New",
                "scraped": "Scraped",
                "processed": "Processed",
                "document_created": "Document Created",
                "applied": "Applied"
            }
            df["status_text"] = df["status"].map(status_mapping).fillna("Unknown")
        
        # Add priority based on AI score
        if "compatibility_score" in df.columns:
            def get_priority(score):
                if score >= 0.8:
                    return "High"
                elif score >= 0.6:
                    return "Medium"
                else:
                    return "Low"
            
            df["priority"] = df["compatibility_score"].apply(get_priority)
        
        # Add experience level if not present
        if "experience_level" not in df.columns:
            df["experience_level"] = "Not Specified"
        
        # Add location if not present
        if "location" not in df.columns:
            df["location"] = "Not Specified"
        
        # Add salary range if not present
        if "salary_range" not in df.columns:
            df["salary_range"] = "Not Specified"
        
        # Add created_at if not present
        if "created_at" not in df.columns:
            df["created_at"] = pd.Timestamp.now()
        
        # Add application status if not present
        if "application_status" not in df.columns:
            df["application_status"] = "not_applied"
        
        return df
        
    except Exception as e:
        logger.error(f"Error adding computed fields: {e}")
        return df


def get_job_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get summary statistics for the job data.
    
    Args:
        df: Job DataFrame
        
    Returns:
        Dictionary with summary statistics
    """
    if df.empty:
        return {
            "total_jobs": 0,
            "applied_jobs": 0,
            "success_rate": 0.0,
            "avg_ai_score": 0.0,
            "high_matches": 0,
            "companies": 0
        }
    
    try:
        stats = {
            "total_jobs": len(df),
            "applied_jobs": len(df[df.get("application_status", "") == "applied"]),
            "success_rate": 0.0,  # Would need to calculate from actual results
            "avg_ai_score": df.get("compatibility_score", pd.Series([0.5])).mean(),
            "high_matches": len(df[df.get("compatibility_score", 0) >= 0.8]),
            "companies": df.get("company", pd.Series()).nunique()
        }
        
        # Calculate success rate if we have application data
        if stats["applied_jobs"] > 0:
            # This would need to be calculated from actual application results
            stats["success_rate"] = 0.0
        
        return stats
        
    except Exception as e:
        logger.error(f"Error calculating summary stats: {e}")
        return {
            "total_jobs": len(df),
            "applied_jobs": 0,
            "success_rate": 0.0,
            "avg_ai_score": 0.0,
            "high_matches": 0,
            "companies": 0
        }


def get_available_profiles() -> List[str]:
    """
    Get list of available profiles.
    
    Returns:
        List of profile names
    """
    try:
        profiles_dir = Path("profiles")
        if not profiles_dir.exists():
            return []
        
        profile_files = list(profiles_dir.glob("*.json"))
        profile_names = [f.stem for f in profile_files]
        
        return sorted(profile_names)
        
    except Exception as e:
        logger.error(f"Error getting available profiles: {e}")
        return []


def load_profile_data(profile_name: str) -> Dict[str, Any]:
    """
    Load profile data with additional computed fields.
    
    Args:
        profile_name: Name of the profile
        
    Returns:
        Dictionary with profile data
    """
    try:
        profile = load_profile(profile_name)
        if not profile:
            return {}
        
        # Add computed fields
        profile["profile_name"] = profile_name
        
        # Load job statistics
        df = load_job_data(profile_name)
        stats = get_job_summary_stats(df)
        profile["job_stats"] = stats
        
        return profile
        
    except Exception as e:
        logger.error(f"Error loading profile data for {profile_name}: {e}")
        return {}
