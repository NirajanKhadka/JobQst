"""
Experience Filter for Job Analysis
Analyzes job postings to determine experience level requirements.
"""

import re
from typing import Dict, List, Optional
from rich.console import Console

console = Console()


class ExperienceAnalyzer:
    """Analyzes job postings to determine experience level requirements."""
    
    def __init__(self):
        self.entry_level_indicators = [
            'entry level', 'junior', 'graduate', 'new grad', 'recent graduate',
            'associate', 'trainee', 'intern', 'co-op', 'student',
            '0-1 years', '0-2 years', '1-2 years', 'no experience required',
            'fresh graduate', 'entry-level', 'beginner'
        ]
        
        self.senior_level_indicators = [
            'senior', 'sr.', 'lead', 'principal', 'architect', 'manager',
            'director', 'head of', 'chief', 'vp', 'vice president',
            '5+ years', '7+ years', '10+ years', '3+ years', '4+ years',
            'experienced', 'expert', 'specialist'
        ]
    
    def analyze_experience_level(self, title: str, description: str) -> str:
        """
        Analyze job title and description to determine experience level.
        
        Returns: 'entry', 'mid', 'senior', or 'unknown'
        """
        text = f"{title} {description}".lower()
        
        # Check for entry level indicators
        for indicator in self.entry_level_indicators:
            if indicator in text:
                return 'entry'
        
        # Check for senior level indicators
        for indicator in self.senior_level_indicators:
            if indicator in text:
                return 'senior'
        
        # Check for specific year requirements
        year_matches = re.findall(r'(\d+)(?:\s*[-–]\s*(\d+))?\s*years?\s*(?:of\s*)?experience', text)
        for match in year_matches:
            min_years = int(match[0])
            max_years = int(match[1]) if match[1] else min_years
            
            if min_years <= 2:
                return 'entry'
            elif min_years >= 5:
                return 'senior'
            else:
                return 'mid'
        
        # Default to mid-level if unclear
        return 'mid'
    
    def is_suitable_for_profile(self, job: Dict) -> bool:
        """
        Check if job is suitable for the user's profile.
        Currently focuses on entry-level and some mid-level positions.
        """
        title = job.get('title', '')
        description = job.get('summary', '') or job.get('full_description', '')
        
        experience_level = self.analyze_experience_level(title, description)
        
        # Accept entry-level and some mid-level positions
        return experience_level in ['entry', 'mid']
    
    def get_experience_score(self, job: Dict) -> float:
        """
        Get a score (0-1) indicating how suitable the job is based on experience.
        Higher score = more suitable.
        """
        title = job.get('title', '')
        description = job.get('summary', '') or job.get('full_description', '')
        
        experience_level = self.analyze_experience_level(title, description)
        
        if experience_level == 'entry':
            return 1.0
        elif experience_level == 'mid':
            return 0.7
        elif experience_level == 'senior':
            return 0.2
        else:
            return 0.5  # Unknown, give moderate score
    
    def filter_suitable_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Filter a list of jobs to only include suitable ones."""
        suitable_jobs = []
        
        for job in jobs:
            if self.is_suitable_for_profile(job):
                suitable_jobs.append(job)
        
        return suitable_jobs
    
    def analyze_job_batch(self, jobs: List[Dict]) -> Dict:
        """Analyze a batch of jobs and return statistics."""
        stats = {
            'total': len(jobs),
            'entry': 0,
            'mid': 0,
            'senior': 0,
            'unknown': 0,
            'suitable': 0
        }
        
        for job in jobs:
            title = job.get('title', '')
            description = job.get('summary', '') or job.get('full_description', '')
            
            level = self.analyze_experience_level(title, description)
            stats[level] += 1
            
            if self.is_suitable_for_profile(job):
                stats['suitable'] += 1
        
        return stats


def test_experience_analyzer():
    """Test the experience analyzer with sample jobs."""
    analyzer = ExperienceAnalyzer()
    
    test_jobs = [
        {
            'title': 'Junior Data Analyst',
            'summary': 'Entry level position for recent graduates. 0-2 years experience required.'
        },
        {
            'title': 'Senior Software Engineer',
            'summary': 'Looking for experienced developer with 5+ years of experience.'
        },
        {
            'title': 'Data Analyst',
            'summary': 'Analyze data and create reports. Python and SQL experience preferred.'
        }
    ]
    
    console.print("[bold]Testing Experience Analyzer[/bold]")
    
    for job in test_jobs:
        level = analyzer.analyze_experience_level(job['title'], job['summary'])
        suitable = analyzer.is_suitable_for_profile(job)
        score = analyzer.get_experience_score(job)
        
        console.print(f"Job: {job['title']}")
        console.print(f"  Level: {level}")
        console.print(f"  Suitable: {suitable}")
        console.print(f"  Score: {score:.1f}")
        console.print()


if __name__ == "__main__":
    test_experience_analyzer()
