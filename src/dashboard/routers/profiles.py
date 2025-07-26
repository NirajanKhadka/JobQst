"""
Profiles router for the AutoJobAgent Dashboard API.

This module provides REST API endpoints for profile-related operations including
profile listing, details retrieval, and profile management functionality.
"""

import logging
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.utils.profile_helpers import get_available_profiles, load_profile

# Set up router and logging
router = APIRouter()
logger = logging.getLogger(__name__)


class ProfileResponse(BaseModel):
    """Response model for profile data."""
    name: str
    profile_name: str
    keywords: Optional[List[str]] = []
    location: Optional[str] = None
    experience_level: Optional[str] = None
    status: str = "active"


@router.get("/profiles")
async def get_profiles() -> Dict[str, Any]:
    """
    Get list of all available profiles.
    
    Returns:
        Dictionary containing list of available profiles with basic info
        
    Raises:
        HTTPException: If profiles cannot be retrieved
    """
    try:
        profile_names = get_available_profiles()
        
        profiles_data = []
        for profile_name in profile_names:
            try:
                profile = load_profile(profile_name)
                if profile:
                    profile_info = {
                        "name": profile.get("name", profile_name),
                        "profile_name": profile_name,
                        "keywords": profile.get("keywords", []),
                        "location": profile.get("location", ""),
                        "experience_level": profile.get("experience_level", ""),
                        "status": "active"
                    }
                else:
                    # Profile directory exists but no valid profile file
                    profile_info = {
                        "name": profile_name,
                        "profile_name": profile_name,
                        "keywords": [],
                        "location": "",
                        "experience_level": "",
                        "status": "incomplete"
                    }
                profiles_data.append(profile_info)
            except Exception as e:
                logger.warning(f"Error loading profile {profile_name}: {e}")
                # Still include the profile but mark as error
                profiles_data.append({
                    "name": profile_name,
                    "profile_name": profile_name,
                    "keywords": [],
                    "location": "",
                    "experience_level": "",
                    "status": "error"
                })
        
        return {
            "profiles": profiles_data,
            "total_count": len(profiles_data),
            "active_count": len([p for p in profiles_data if p["status"] == "active"]),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving profiles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve profiles: {str(e)}")


@router.get("/profiles/{profile_name}")
async def get_profile_details(profile_name: str) -> Dict[str, Any]:
    """
    Get detailed information for a specific profile.
    
    Args:
        profile_name: Name of the profile to retrieve
        
    Returns:
        Dictionary containing detailed profile information
        
    Raises:
        HTTPException: If profile not found or cannot be retrieved
    """
    try:
        available_profiles = get_available_profiles()
        
        if profile_name not in available_profiles:
            raise HTTPException(
                status_code=404, 
                detail=f"Profile '{profile_name}' not found. Available profiles: {available_profiles}"
            )
        
        profile = load_profile(profile_name)
        
        if not profile:
            raise HTTPException(
                status_code=404, 
                detail=f"Profile '{profile_name}' exists but could not be loaded"
            )
        
        return {
            "profile": profile,
            "profile_name": profile_name,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving profile {profile_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve profile: {str(e)}")


@router.get("/profiles/check/{profile_name}")
async def check_profile_exists(profile_name: str) -> Dict[str, Any]:
    """
    Check if a specific profile exists and is valid.
    
    Args:
        profile_name: Name of the profile to check
        
    Returns:
        Dictionary containing profile existence and validity status
    """
    try:
        available_profiles = get_available_profiles()
        exists = profile_name in available_profiles
        
        if exists:
            profile = load_profile(profile_name)
            valid = profile is not None
            
            return {
                "profile_name": profile_name,
                "exists": exists,
                "valid": valid,
                "status": "found" if valid else "incomplete",
                "message": f"Profile '{profile_name}' {'is valid' if valid else 'exists but is incomplete'}"
            }
        else:
            return {
                "profile_name": profile_name,
                "exists": False,
                "valid": False,
                "status": "not_found",
                "message": f"Profile '{profile_name}' not found",
                "available_profiles": available_profiles
            }
            
    except Exception as e:
        logger.error(f"Error checking profile {profile_name}: {e}")
        return {
            "profile_name": profile_name,
            "exists": False,
            "valid": False,
            "status": "error",
            "message": f"Error checking profile: {str(e)}"
        }