"""
Profile management utilities for AutoJobAgent.
Handles loading, validation, and management of user profiles.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Union
from rich.console import Console

# from src.utils.profile_helpers import load_profile  # Removed circular import

console = Console()

# Singleton pattern to prevent duplicate initialization
_profile_cache = {}
_initialized_profiles = set()


def get_available_profiles() -> List[str]:
    """Gets a list of available profile names."""
    profiles_dir = Path("profiles")
    if not profiles_dir.exists():
        return []

    return [p.name for p in profiles_dir.iterdir() if p.is_dir()]


def get_profile_path(profile_name: str) -> Path:
    """Get the path to a profile directory.

    Args:
        profile_name: Name of the profile

    Returns:
        Path to the profile directory
    """
    return Path(f"profiles/{profile_name}")


def load_profile(profile_name: str) -> Optional[Dict]:
    """
    Load a profile by name with caching and duplicate prevention.

    Args:
        profile_name: Name of the profile to load

    Returns:
        Profile dictionary or None if not found
    """
    # Check cache first
    if profile_name in _profile_cache:
        return _profile_cache[profile_name]

    # Check if already initialized to prevent duplicate messages
    if profile_name in _initialized_profiles:
        return _profile_cache.get(profile_name)

    # Mark as initialized to prevent duplicate messages
    _initialized_profiles.add(profile_name)

    # Load profile from file
    profile = _load_profile_from_file(profile_name)

    if profile:
        # Cache the profile
        _profile_cache[profile_name] = profile
        # Only print message once per profile
        console.print(f"[green]Loaded profile: {profile.get('name', profile_name)}[/green]")
        console.print(f"[cyan]Keywords: {profile.get('keywords', [])}[/cyan]")

    return profile


def _load_profile_from_file(profile_name: str) -> Optional[Dict]:
    """
    Load profile from file without printing messages.

    Args:
        profile_name: Name of the profile to load

    Returns:
        Profile dictionary or None if not found
    """
    try:
        profile_path = Path(f"profiles/{profile_name}/{profile_name}.json")
        if profile_path.exists():
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
            return profile_data
        else:
            return None
    except Exception as e:
        print(f"❌ Error loading profile {profile_name}: {e}")
        return None


def ensure_profile_files(profile: Dict) -> bool:
    """Ensures that the necessary resume and cover letter files exist for a profile."""
    profile_name = profile.get("profile_name", "default")
    profile_dir = Path(f"profiles/{profile_name}")

    resume_path = profile_dir / f"{profile_name}_Resume.pdf"
    if not resume_path.exists():
        # Try to find a docx and convert it
        docx_resume = profile_dir / f"{profile_name}_Resume.docx"
        if docx_resume.exists():
            # Placeholder for conversion logic
            print(f"Found {docx_resume}, would convert to PDF here.")
        else:
            return False

    return True

