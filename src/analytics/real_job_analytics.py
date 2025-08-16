#!/usr/bin/env python3
"""Real Job Analytics - Top Companies, Keywords, and Insights."""

from typing import Dict, List, Any
from collections import Counter
import re
from datetime import datetime


class RealJobAnalytics:
    """Real analytics based on actual job data."""
    
    def __init__(self, db):
        self.db = db
    
    def get_analytics_data(self) -> Dict[str, Any]:
        """Get real analytics data from job database."""
        try:
            all_jobs = self.db.get_jobs(limit=2000)
            
            if not all_jobs:
                return {'has_data': False, 'message': 'No jobs found'}
            
            return {
                'has_data': True,
                'total_jobs': len(all_jobs),
                'top_companies': self._get_top_companies(all_jobs),
                'top_keywords': self._get_top_keywords(all_jobs),
                'location_stats': self._get_location_stats(all_jobs),
                'recent_activity': self._get_recent_activity(all_jobs),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'has_data': False, 
                'error': str(e),
                'message': 'Error calculating analytics'
            }
    
    def _get_top_companies(self, jobs: List[Dict]) -> List[Dict[str, Any]]:
        """Get top companies by job count."""
        companies = Counter()
        
        for job in jobs:
            company = job.get('company', '').strip()
            if company and company.lower() not in ['unknown', 'n/a', '']:
                companies[company] += 1
        
        return [
            {
                'name': company, 
                'job_count': count, 
                'percentage': (count/len(jobs))*100
            }
            for company, count in companies.most_common(10)
        ]
    
    def _get_top_keywords(self, jobs: List[Dict]) -> List[Dict[str, Any]]:
        """Extract top keywords/skills from job descriptions."""
        tech_keywords = {
            'python', 'javascript', 'java', 'react', 'node', 'sql', 'aws',
            'docker', 'kubernetes', 'git', 'api', 'rest', 'mongodb',
            'postgresql', 'machine learning', 'ai', 'data science',
            'tensorflow', 'pytorch', 'pandas', 'numpy', 'flask', 'django',
            'vue', 'angular', 'typescript', 'css', 'html', 'agile', 'scrum'
        }
        
        keyword_counter = Counter()
        
        for job in jobs:
            text = (
                (job.get('title', '') + ' ' + 
                 job.get('description', '')).lower()
            )
            
            for keyword in tech_keywords:
                if keyword in text:
                    keyword_counter[keyword] += 1
        
        return [
            {
                'keyword': keyword, 
                'job_count': count, 
                'percentage': (count/len(jobs))*100
            }
            for keyword, count in keyword_counter.most_common(15)
        ]
    
    def _get_location_stats(self, jobs: List[Dict]) -> List[Dict[str, Any]]:
        """Get job distribution by location."""
        locations = Counter()
        
        for job in jobs:
            location = job.get('location', '').strip()
            if location and location.lower() not in ['unknown', 'n/a', '']:
                location = re.sub(r'[,\(].*', '', location).strip()
                locations[location] += 1
        
        return [
            {
                'location': location, 
                'job_count': count, 
                'percentage': (count/len(jobs))*100
            }
            for location, count in locations.most_common(8)
        ]
    
    def _get_recent_activity(self, jobs: List[Dict]) -> Dict[str, Any]:
        """Get recent job activity stats."""
        from datetime import timedelta
        
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        
        recent_week = 0
        
        for job in jobs:
            job_date_str = job.get('posting_date') or job.get('scraped_at', '')
            if job_date_str:
                try:
                    job_date = datetime.fromisoformat(
                        job_date_str.replace('Z', '+00:00')
                    )
                    if job_date > week_ago:
                        recent_week += 1
                except:
                    continue
        
        return {
            'jobs_7d': recent_week,
            'daily_average': recent_week / 7.0,
            'activity_trend': '↗️ Active'
        }


def get_real_job_analytics(db) -> RealJobAnalytics:
    """Get real job analytics instance."""
    return RealJobAnalytics(db)
