"""
Profile utilities for dashboard
Centralized profile validation and management
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def validate_profile_exists(profile_name: str) -> bool:
    """
    Validate that a profile exists
    
    Args:
        profile_name: Profile name to validate
        
    Returns:
        True if profile exists, False otherwise
    """
    try:
        from src.utils.profile_helpers import get_available_profiles
        
        available_profiles = get_available_profiles()
        return profile_name in available_profiles
    except Exception as e:
        logger.error(f"Error validating profile: {e}")
        return False


def get_available_profiles() -> List[str]:
    """
    Get list of available profiles
    
    Returns:
        List of profile names
    """
    try:
        from src.utils.profile_helpers import get_available_profiles as _get_profiles
        return _get_profiles()
    except Exception as e:
        logger.error(f"Error getting profiles: {e}")
        return []


def require_profile(profile_name: Optional[str]) -> str:
    """
    Ensure a profile name is provided and valid
    
    FALLBACK STRATEGY:
    - If "Nirajan" specified and exists -> use Nirajan
    - If "Nirajan" specified but missing -> error
    - If None or other name -> use "Demo" profile (auto-create if needed)
    
    Args:
        profile_name: Profile name (can be None)
        
    Returns:
        Validated profile name (Nirajan or Demo)
    """
    # Special case: Nirajan profile must exist if explicitly requested
    if profile_name == "Nirajan":
        if validate_profile_exists("Nirajan"):
            logger.info("[OK] Using Nirajan profile")
            return "Nirajan"
        else:
            raise ValueError(
                "Nirajan profile not found. Please create it first.\n"
                "Usage: python main.py Nirajan --action create-profile"
            )
    
    # All other cases: Use Demo profile (auto-create)
    demo_name = "Demo"
    
    if not validate_profile_exists(demo_name):
        logger.info("📊 Creating Demo profile for dashboard...")
        try:
            _create_demo_profile()
            logger.info("[OK] Demo profile created successfully")
        except Exception as e:
            logger.error(f"Failed to create Demo profile: {e}")
            # If demo creation fails, try any existing profile
            available = get_available_profiles()
            if available:
                fallback = available[0]
                logger.warning(f"⚠️ Using fallback profile: {fallback}")
                return fallback
            raise ValueError("No profiles available and Demo profile creation failed")
    
    logger.info(f"[OK] Using Demo profile (requested: {profile_name})")
    return demo_name


def _create_demo_profile() -> bool:
    """
    Create a demo profile for dashboard testing/preview
    
    Returns:
        True if created successfully
    """
    try:
        from src.core.user_profile_manager import UserProfileManager
        
        pm = UserProfileManager()
        
        demo_data = {
            "email": "demo@joblens.com",
            "phone": "+1 (555) 123-4567",
            "location": "Toronto, ON, Canada",
            "skills": [
                "Python", "SQL", "Data Analysis", "Machine Learning",
                "Pandas", "NumPy", "Tableau", "Power BI",
                "Git", "Docker", "AWS", "Problem Solving"
            ],
            "experience_years": 3,
            "education": "Bachelor's in Computer Science",
            "linkedin_url": "https://linkedin.com/in/demo",
            "settings": {
                "preferred_locations": ["Toronto", "Vancouver", "Montreal"],
                "job_types": ["Full-time", "Contract"],
                "remote_preference": "Hybrid",
                "salary_min": 60000,
                "salary_currency": "CAD"
            }
        }
        
        return pm.create_profile("Demo", demo_data)
    
    except Exception as e:
        logger.error(f"Error creating demo profile: {e}")
        return False


class ProfileRequiredError(Exception):
    """Raised when dashboard is launched without a profile"""
    pass
