"""
Market Analyzer Utility Module
Analyzes job market data for salary trends, hiring companies, skills demand, and trends.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from collections import Counter
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """Analyze job market data for insights and trends."""
    
    # Common skills to track
    TRACKED_SKILLS = [
        'python', 'java', 'javascript', 'sql', 'r', 'c++', 'c#',
        'react', 'angular', 'vue', 'node', 'django', 'flask',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes',
        'machine learning', 'deep learning', 'ai', 'nlp',
        'data analysis', 'data science', 'analytics',
        'tableau', 'power bi', 'excel', 'pandas', 'numpy',
        'git', 'agile', 'scrum', 'ci/cd'
    ]
    
    def __init__(self, jobs_data: List[Dict[str, Any]]):
        """
        Initialize market analyzer with jobs data.
        
        Args:
            jobs_data: List of job dictionaries
        """
        self.jobs_data = jobs_data
        self.total_jobs = len(jobs_data)
    
    def calculate_salary_range(self) -> Dict[str, Any]:
        """
        Calculate salary statistics from job data.
        
        Returns:
            Dictionary with min, max, median, average salary and distribution
        """
        salaries = []
        
        for job in self.jobs_data:
            salary_min = job.get('salary_min')
            salary_max = job.get('salary_max')
            
            if salary_min and salary_max:
                # Use average of min and max
                avg_salary = (salary_min + salary_max) / 2
                salaries.append({
                    'min': salary_min,
                    'max': salary_max,
                    'avg': avg_salary
                })
        
        if not salaries:
            return {
                'min': 0,
                'max': 0,
                'median': 0,
                'average': 0,
                'count': 0,
                'distribution': []
            }
        
        # Calculate statistics
        all_avgs = [s['avg'] for s in salaries]
        all_avgs.sort()
        
        median_salary = all_avgs[len(all_avgs) // 2] if all_avgs else 0
        average_salary = sum(all_avgs) / len(all_avgs) if all_avgs else 0
        
        # Create salary distribution buckets
        distribution = self._create_salary_distribution(all_avgs)
        
        return {
            'min': min(s['min'] for s in salaries),
            'max': max(s['max'] for s in salaries),
            'median': round(median_salary, 2),
            'average': round(average_salary, 2),
            'count': len(salaries),
            'distribution': distribution
        }
    
    def _create_salary_distribution(self, salaries: List[float]) -> List[Dict[str, Any]]:
        """Create salary distribution buckets."""
        if not salaries:
            return []
        
        # Define salary ranges
        ranges = [
            (0, 50000, '$0-50k'),
            (50000, 75000, '$50k-75k'),
            (75000, 100000, '$75k-100k'),
            (100000, 125000, '$100k-125k'),
            (125000, 150000, '$125k-150k'),
            (150000, float('inf'), '$150k+')
        ]
        
        distribution = []
        for min_sal, max_sal, label in ranges:
            count = sum(1 for s in salaries if min_sal <= s < max_sal)
            if count > 0:
                distribution.append({
                    'range': label,
                    'count': count,
                    'percentage': round(count / len(salaries) * 100, 1)
                })
        
        return distribution
    
    def get_top_hiring_companies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top companies by number of job postings.
        
        Args:
            limit: Maximum number of companies to return
            
        Returns:
            List of companies with job counts and trend indicators
        """
        company_counts = Counter()
        
        for job in self.jobs_data:
            company = job.get('company', '').strip()
            if company and company.lower() != 'unknown':
                company_counts[company] += 1
        
        # Get top companies
        top_companies = []
        for company, count in company_counts.most_common(limit):
            # Calculate trend (simplified - compare to average)
            avg_jobs_per_company = self.total_jobs / len(company_counts) if company_counts else 0
            trend = 'growing' if count > avg_jobs_per_company * 1.2 else 'stable'
            
            top_companies.append({
                'company': company,
                'job_count': count,
                'percentage': round(count / self.total_jobs * 100, 1) if self.total_jobs > 0 else 0,
                'trend': trend
            })
        
        return top_companies
    
    def analyze_skills_demand(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Analyze skills demand from job descriptions.
        
        Args:
            limit: Maximum number of skills to return
            
        Returns:
            List of skills with frequency counts and priority
        """
        skill_counts = Counter()
        
        for job in self.jobs_data:
            description = job.get('description', '').lower()
            title = job.get('title', '').lower()
            
            # Combine title and description for skill matching
            text = f"{title} {description}"
            
            # Count skill occurrences
            for skill in self.TRACKED_SKILLS:
                if skill.lower() in text:
                    skill_counts[skill] += 1
        
        # Get top skills
        top_skills = []
        for skill, count in skill_counts.most_common(limit):
            percentage = round(count / self.total_jobs * 100, 1) if self.total_jobs > 0 else 0
            
            # Classify priority based on frequency
            if percentage >= 30:
                priority = 'high'
            elif percentage >= 15:
                priority = 'medium'
            else:
                priority = 'low'
            
            top_skills.append({
                'skill': skill.title(),
                'count': count,
                'percentage': percentage,
                'priority': priority
            })
        
        return top_skills
    
    def detect_hiring_trends(self) -> Dict[str, Any]:
        """
        Detect hiring trends from job posting dates.
        
        Returns:
            Dictionary with trend analysis
        """
        # Group jobs by posted date
        date_counts = Counter()
        
        for job in self.jobs_data:
            posted_date = job.get('posted_date')
            if posted_date:
                try:
                    # Parse date
                    if isinstance(posted_date, str):
                        date_obj = datetime.fromisoformat(posted_date.replace('Z', '+00:00'))
                    else:
                        date_obj = posted_date
                    
                    # Group by week
                    week_key = date_obj.strftime('%Y-W%U')
                    date_counts[week_key] += 1
                except Exception as e:
                    logger.debug(f"Error parsing date {posted_date}: {e}")
                    continue
        
        if not date_counts:
            return {
                'trend': 'stable',
                'weekly_average': 0,
                'recent_activity': 'low'
            }
        
        # Calculate trend
        weeks = sorted(date_counts.keys())
        if len(weeks) >= 2:
            recent_avg = sum(date_counts[w] for w in weeks[-2:]) / 2
            older_avg = sum(date_counts[w] for w in weeks[:-2]) / max(len(weeks) - 2, 1)
            
            if recent_avg > older_avg * 1.2:
                trend = 'growing'
            elif recent_avg < older_avg * 0.8:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        weekly_average = sum(date_counts.values()) / len(date_counts) if date_counts else 0
        
        # Recent activity
        recent_jobs = sum(date_counts[w] for w in weeks[-1:]) if weeks else 0
        if recent_jobs > weekly_average * 1.5:
            recent_activity = 'high'
        elif recent_jobs < weekly_average * 0.5:
            recent_activity = 'low'
        else:
            recent_activity = 'moderate'
        
        return {
            'trend': trend,
            'weekly_average': round(weekly_average, 1),
            'recent_activity': recent_activity,
            'total_weeks': len(weeks)
        }
    
    def get_market_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive market summary.
        
        Returns:
            Dictionary with all market insights
        """
        return {
            'salary_analysis': self.calculate_salary_range(),
            'top_companies': self.get_top_hiring_companies(10),
            'skills_demand': self.analyze_skills_demand(15),
            'hiring_trends': self.detect_hiring_trends(),
            'total_jobs': self.total_jobs
        }
