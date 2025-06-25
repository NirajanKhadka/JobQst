import json
from pathlib import Path
from typing import List, Dict
from src.utils.profile_helpers import load_profile

def get_available_profiles() -> List[str]:
    """Gets a list of available profile names."""
    profiles_dir = Path("profiles")
    if not profiles_dir.exists():
        return []
    
    return [p.name for p in profiles_dir.iterdir() if p.is_dir()]

def load_profile(profile_name):
    """Stub: Load a profile by name."""
    return {'name': profile_name}

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