from pathlib import Path
import json
import time
from typing import Dict

class ResumeAnalyzer:
    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self.profile_dir = Path(f"profiles/{profile_name}")

    def needs_analysis(self) -> bool:
        """Checks if the resume needs to be re-analyzed."""
        resume_path = self.profile_dir / f"{self.profile_name}_Resume.docx"
        if not resume_path.exists():
            return False
        
        cache_file = self.profile_dir / ".resume_analysis_cache.json"
        if not cache_file.exists():
            return True
            
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
            
        return resume_path.stat().st_mtime > cache_data.get('last_analysis_time', 0)

    def analyze_and_update_profile(self, profile: Dict) -> Dict:
        """Analyzes the resume and updates the profile with extracted skills and keywords."""
        # This is a placeholder for the actual resume analysis logic.
        # In a real implementation, this would use NLP to extract skills.
        updated_profile = profile.copy()
        updated_profile['skills'] = ["Python", "SQL", "Data Analysis", "Pandas"]
        updated_profile['keywords'] = ["Data Analyst", "Business Analyst"]
        
        self._update_analysis_timestamp()
        return updated_profile

    def _update_analysis_timestamp(self):
        """Updates the analysis timestamp cache file."""
        cache_file = self.profile_dir / ".resume_analysis_cache.json"
        cache_data = {'last_analysis_time': time.time()}
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)