import json
from pathlib import Path
from typing import List, Dict
# from src.utils.profile_helpers import load_profile  # Removed circular import

def get_available_profiles() -> List[str]:
    """Gets a list of available profile names."""
    profiles_dir = Path("profiles")
    if not profiles_dir.exists():
        return []
    
    return [p.name for p in profiles_dir.iterdir() if p.is_dir()]

def load_profile(profile_name: str) -> Dict:
    """Load a profile by name from the JSON file."""
    try:
        profile_path = Path(f"profiles/{profile_name}/{profile_name}.json")
        if profile_path.exists():
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
                print(f"✅ Loaded profile: {profile_name}")
                print(f"Keywords: {profile_data.get('keywords', [])}")
                return profile_data
        else:
            print(f"⚠️ Profile file not found: {profile_path}")
            return {'name': profile_name}
    except Exception as e:
        print(f"❌ Error loading profile {profile_name}: {e}")
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