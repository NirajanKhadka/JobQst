#!/usr/bin/env python3
"""
Analytics Service for JobLens
Provides insights and statistics about job search data, trends, and performance.

Features:
- Job trends analysis (jobs per week, top companies, frequent skills)
- Application tracking and success rates
- Skill demand analysis
- Location and remote work trends
- Match score distributions
- Export functionality (CSV, JSON)
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
import csv
from pathlib import Path

logger = logging.getLogger(__name__)


class JobAnalyticsService:
    """Service for analyzing job search data and generating insights."""
    
    def __init__(self, db):
        self.db = db
        
    def generate_comprehensive_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate a comprehensive analytics report."""
        
        # Get jobs from the specified time period
        jobs = self._get_recent_jobs(days)
        
        if not jobs:
            return {
                'status': 'no_data',
                'message': f'No jobs found in the last {days} days',
                'period_days': days
            }
        
        report = {
            'period_days': days,
            'generated_at': datetime.now().isoformat(),
            'total_jobs': len(jobs),
            'overview': self._generate_overview(jobs),
            'trends': self._analyze_trends(jobs, days),
            'companies': self._analyze_companies(jobs),
            'skills': self._analyze_skills(jobs),
            'locations': self._analyze_locations(jobs),
            'applications': self._analyze_applications(jobs),
            'match_scores': self._analyze_match_scores(jobs),
            'job_types': self._analyze_job_types(jobs),
            'recommendations': self._generate_recommendations(jobs)
        }
        
        logger.info(f"Analytics report generated: {len(jobs)} jobs analyzed "
                   f"over {days} days")
        
        return report
    
    def _get_recent_jobs(self, days: int) -> List[Dict[str, Any]]:
        """Get jobs from the recent time period."""
        try:
            # Use the database method to get recent jobs
            return self.db.get_jobs(limit=1000)  # Adjust limit as needed
        except Exception as e:
            logger.error(f"Error getting recent jobs: {e}")
            return []
    
    def _generate_overview(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate high-level overview statistics."""
        applied_jobs = [job for job in jobs if job.get('applied', 0) == 1]
        bookmarked_jobs = [job for job in jobs if job.get('is_bookmarked', 0) == 1]
        
        # Calculate average match score
        match_scores = [job.get('match_score', 0) or job.get('compatibility_score', 0) 
                       for job in jobs]
        avg_match_score = sum(match_scores) / len(match_scores) if match_scores else 0
        
        # Get status distribution
        status_counts = Counter(job.get('status', 'unknown') for job in jobs)
        
        return {
            'total_jobs': len(jobs),
            'applied_jobs': len(applied_jobs),
            'bookmarked_jobs': len(bookmarked_jobs),
            'application_rate': len(applied_jobs) / len(jobs) * 100 if jobs else 0,
            'bookmark_rate': len(bookmarked_jobs) / len(jobs) * 100 if jobs else 0,
            'average_match_score': avg_match_score,
            'status_distribution': dict(status_counts),
            'unique_companies': len(set(job.get('company', 'Unknown') for job in jobs)),
            'unique_locations': len(set(job.get('location', 'Unknown') for job in jobs))
        }
    
    def _analyze_trends(self, jobs: List[Dict[str, Any]], days: int) -> Dict[str, Any]:
        """Analyze job posting trends over time."""
        # Group jobs by date
        jobs_by_date = defaultdict(int)
        
        for job in jobs:
            scraped_at = job.get('scraped_at', '') or job.get('created_at', '')
            if scraped_at:
                try:
                    # Parse different date formats
                    if 'T' in scraped_at:
                        date = datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
                    else:
                        date = datetime.strptime(scraped_at, '%Y-%m-%d %H:%M:%S')
                    
                    date_key = date.strftime('%Y-%m-%d')
                    jobs_by_date[date_key] += 1
                except Exception:
                    continue
        
        # Calculate weekly trends
        weekly_data = self._group_by_week(jobs_by_date)
        
        # Calculate daily average
        daily_avg = len(jobs) / days if days > 0 else 0
        
        return {
            'daily_average': daily_avg,
            'jobs_by_date': dict(jobs_by_date),
            'weekly_trends': weekly_data,
            'peak_day': max(jobs_by_date.items(), key=lambda x: x[1]) if jobs_by_date else None,
            'trend_direction': self._calculate_trend_direction(weekly_data)
        }
    
    def _analyze_companies(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze company-related statistics."""
        company_counts = Counter(job.get('company', 'Unknown') for job in jobs)
        company_counts.pop('Unknown', None)  # Remove unknown companies
        
        # Company application rates
        company_apps = defaultdict(lambda: {'total': 0, 'applied': 0})
        for job in jobs:
            company = job.get('company', 'Unknown')
            if company != 'Unknown':
                company_apps[company]['total'] += 1
                if job.get('applied', 0) == 1:
                    company_apps[company]['applied'] += 1
        
        # Calculate application rates
        company_app_rates = {}
        for company, data in company_apps.items():
            if data['total'] > 0:
                rate = (data['applied'] / data['total']) * 100
                company_app_rates[company] = rate
        
        return {
            'top_companies': dict(company_counts.most_common(10)),
            'total_unique_companies': len(company_counts),
            'company_application_rates': dict(sorted(company_app_rates.items(), 
                                                   key=lambda x: x[1], reverse=True)[:10]),
            'companies_with_multiple_jobs': len([c for c, count in company_counts.items() 
                                               if count > 1])
        }
    
    def _analyze_skills(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze skill demand and trends."""
        all_skills = []
        
        # Extract skills from various fields
        for job in jobs:
            # From keywords field
            keywords = job.get('keywords', '')
            if isinstance(keywords, str):
                try:
                    skill_list = json.loads(keywords)
                    if isinstance(skill_list, list):
                        all_skills.extend(skill_list)
                except:
                    # Split by common delimiters
                    skills = [s.strip() for s in keywords.split(',')]
                    all_skills.extend(skills)
            elif isinstance(keywords, list):
                all_skills.extend(keywords)
            
            # From required_skills field
            req_skills = job.get('required_skills', '')
            if req_skills:
                if isinstance(req_skills, str):
                    try:
                        skill_list = json.loads(req_skills)
                        if isinstance(skill_list, list):
                            all_skills.extend(skill_list)
                    except:
                        skills = [s.strip() for s in req_skills.split(',')]
                        all_skills.extend(skills)
                elif isinstance(req_skills, list):
                    all_skills.extend(req_skills)
        
        # Clean and count skills
        cleaned_skills = [skill.strip().lower() for skill in all_skills 
                         if skill and skill.strip()]
        skill_counts = Counter(cleaned_skills)
        
        # Group skills by category
        skill_categories = self._categorize_skills(skill_counts)
        
        return {
            'top_skills': dict(skill_counts.most_common(20)),
            'total_unique_skills': len(skill_counts),
            'skill_categories': skill_categories,
            'emerging_skills': self._identify_emerging_skills(jobs),
            'skill_demand_trend': self._analyze_skill_trends(jobs)
        }
    
    def _analyze_locations(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze location and remote work trends."""
        location_counts = Counter(job.get('location', 'Unknown') for job in jobs)
        location_counts.pop('Unknown', None)
        
        # Analyze location types
        location_type_counts = Counter(job.get('location_type', 'unknown') for job in jobs)
        
        # Calculate remote work percentage
        remote_jobs = location_type_counts.get('remote', 0)
        hybrid_jobs = location_type_counts.get('hybrid', 0)
        total_jobs = len(jobs)
        
        remote_percentage = (remote_jobs / total_jobs * 100) if total_jobs > 0 else 0
        hybrid_percentage = (hybrid_jobs / total_jobs * 100) if total_jobs > 0 else 0
        flexible_percentage = remote_percentage + hybrid_percentage
        
        # Analyze city/region patterns
        cities = self._extract_cities_from_locations(location_counts)
        
        return {
            'top_locations': dict(location_counts.most_common(10)),
            'location_types': dict(location_type_counts),
            'remote_work_stats': {
                'remote_percentage': remote_percentage,
                'hybrid_percentage': hybrid_percentage,
                'flexible_work_percentage': flexible_percentage,
                'onsite_percentage': 100 - flexible_percentage
            },
            'top_cities': cities,
            'location_diversity': len(location_counts)
        }
    
    def _analyze_applications(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze application patterns and success rates."""
        applied_jobs = [job for job in jobs if job.get('applied', 0) == 1]
        
        if not applied_jobs:
            return {
                'total_applications': 0,
                'application_rate': 0,
                'status_distribution': {},
                'response_rate': 0
            }
        
        # Application status distribution
        app_status_counts = Counter(
            job.get('application_status', 'not_applied') for job in applied_jobs
        )
        
        # Response rate (applications that moved beyond 'applied')
        responded_apps = len([job for job in applied_jobs 
                             if job.get('application_status', 'applied') != 'applied'])
        response_rate = (responded_apps / len(applied_jobs) * 100) if applied_jobs else 0
        
        # Time-based application analysis
        app_by_date = defaultdict(int)
        for job in applied_jobs:
            app_date = job.get('application_date', '')
            if app_date:
                try:
                    date = datetime.fromisoformat(app_date).strftime('%Y-%m-%d')
                    app_by_date[date] += 1
                except:
                    continue
        
        return {
            'total_applications': len(applied_jobs),
            'application_rate': len(applied_jobs) / len(jobs) * 100 if jobs else 0,
            'status_distribution': dict(app_status_counts),
            'response_rate': response_rate,
            'applications_by_date': dict(app_by_date),
            'average_applications_per_week': len(applied_jobs) / 4 if applied_jobs else 0
        }
    
    def _analyze_match_scores(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze match score distributions and patterns."""
        match_scores = []
        
        for job in jobs:
            score = job.get('match_score', 0) or job.get('compatibility_score', 0)
            if score and score > 0:
                match_scores.append(float(score))
        
        if not match_scores:
            return {
                'average_score': 0,
                'score_distribution': {},
                'high_score_jobs': 0,
                'total_scored_jobs': 0
            }
        
        # Calculate score distribution
        score_ranges = {
            '0.9-1.0': len([s for s in match_scores if s >= 0.9]),
            '0.8-0.9': len([s for s in match_scores if 0.8 <= s < 0.9]),
            '0.7-0.8': len([s for s in match_scores if 0.7 <= s < 0.8]),
            '0.6-0.7': len([s for s in match_scores if 0.6 <= s < 0.7]),
            '0.5-0.6': len([s for s in match_scores if 0.5 <= s < 0.6]),
            'Below 0.5': len([s for s in match_scores if s < 0.5])
        }
        
        high_score_jobs = len([s for s in match_scores if s >= 0.8])
        
        return {
            'average_score': sum(match_scores) / len(match_scores),
            'median_score': sorted(match_scores)[len(match_scores) // 2],
            'score_distribution': score_ranges,
            'high_score_jobs': high_score_jobs,
            'high_score_percentage': (high_score_jobs / len(match_scores) * 100),
            'total_scored_jobs': len(match_scores)
        }
    
    def _analyze_job_types(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze job types and employment patterns."""
        job_types = Counter(job.get('job_type', 'Unknown') for job in jobs)
        employment_types = Counter(job.get('employment_type', 'Unknown') for job in jobs)
        experience_levels = Counter(job.get('experience_level', 'Unknown') for job in jobs)
        
        return {
            'job_types': dict(job_types),
            'employment_types': dict(employment_types),
            'experience_levels': dict(experience_levels),
            'full_time_percentage': (job_types.get('Full-time', 0) / len(jobs) * 100) if jobs else 0
        }
    
    def _generate_recommendations(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate actionable recommendations based on analysis."""
        recommendations = {
            'skills_to_learn': [],
            'companies_to_target': [],
            'application_strategy': [],
            'search_optimization': []
        }
        
        # Skill recommendations based on demand
        skill_counts = Counter()
        for job in jobs:
            keywords = job.get('keywords', '')
            if isinstance(keywords, str):
                try:
                    skills = json.loads(keywords)
                    if isinstance(skills, list):
                        skill_counts.update(skill.lower() for skill in skills)
                except:
                    skills = [s.strip().lower() for s in keywords.split(',')]
                    skill_counts.update(skills)
        
        top_skills = [skill for skill, count in skill_counts.most_common(10)]
        recommendations['skills_to_learn'] = top_skills[:5]
        
        # Company recommendations (companies with multiple jobs)
        company_counts = Counter(job.get('company', '') for job in jobs)
        multi_job_companies = [company for company, count in company_counts.items() 
                              if count > 1 and company]
        recommendations['companies_to_target'] = multi_job_companies[:5]
        
        # Application strategy recommendations
        applied_jobs = [job for job in jobs if job.get('applied', 0) == 1]
        application_rate = len(applied_jobs) / len(jobs) * 100 if jobs else 0
        
        if application_rate < 5:
            recommendations['application_strategy'].append(
                "Consider applying to more positions - current application rate is low"
            )
        elif application_rate > 20:
            recommendations['application_strategy'].append(
                "Focus on quality over quantity - high application rate detected"
            )
        
        # Search optimization recommendations
        high_score_jobs = [job for job in jobs 
                          if (job.get('match_score', 0) or job.get('compatibility_score', 0)) >= 0.8]
        
        if len(high_score_jobs) / len(jobs) < 0.3 if jobs else False:
            recommendations['search_optimization'].append(
                "Refine search keywords to find better matching positions"
            )
        
        return recommendations
    
    def export_analytics(self, report: Dict[str, Any], format: str = 'json', 
                        output_path: Optional[str] = None) -> str:
        """Export analytics report to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if not output_path:
            output_path = f"analytics_report_{timestamp}.{format}"
        
        try:
            if format.lower() == 'json':
                with open(output_path, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
            
            elif format.lower() == 'csv':
                # Export key metrics to CSV
                with open(output_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Write overview metrics
                    writer.writerow(['Metric', 'Value'])
                    for key, value in report.get('overview', {}).items():
                        writer.writerow([key, value])
                    
                    # Write top companies
                    writer.writerow([])
                    writer.writerow(['Top Companies', 'Job Count'])
                    for company, count in report.get('companies', {}).get('top_companies', {}).items():
                        writer.writerow([company, count])
            
            logger.info(f"Analytics report exported to: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error exporting analytics report: {e}")
            raise
    
    # Helper methods
    def _group_by_week(self, daily_data: Dict[str, int]) -> Dict[str, int]:
        """Group daily data by week."""
        weekly_data = defaultdict(int)
        
        for date_str, count in daily_data.items():
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
                week_start = date - timedelta(days=date.weekday())
                week_key = week_start.strftime('%Y-W%U')
                weekly_data[week_key] += count
            except:
                continue
        
        return dict(weekly_data)
    
    def _calculate_trend_direction(self, weekly_data: Dict[str, int]) -> str:
        """Calculate if trend is increasing, decreasing, or stable."""
        if len(weekly_data) < 2:
            return 'insufficient_data'
        
        weeks = sorted(weekly_data.items())
        if len(weeks) < 2:
            return 'stable'
        
        recent_avg = sum(count for _, count in weeks[-2:]) / 2
        earlier_avg = sum(count for _, count in weeks[:-2]) / max(1, len(weeks) - 2)
        
        if recent_avg > earlier_avg * 1.1:
            return 'increasing'
        elif recent_avg < earlier_avg * 0.9:
            return 'decreasing'
        else:
            return 'stable'
    
    def _categorize_skills(self, skill_counts: Counter) -> Dict[str, Dict[str, int]]:
        """Categorize skills into technology groups."""
        categories = {
            'Programming Languages': ['python', 'javascript', 'java', 'c++', 'c#'],
            'Web Technologies': ['react', 'angular', 'vue', 'html', 'css'],
            'Databases': ['sql', 'mysql', 'postgresql', 'mongodb'],
            'Cloud & DevOps': ['aws', 'azure', 'docker', 'kubernetes'],
            'Data Science': ['machine learning', 'pandas', 'numpy', 'tensorflow']
        }
        
        categorized = defaultdict(dict)
        
        for category, category_skills in categories.items():
            for skill in category_skills:
                if skill in skill_counts:
                    categorized[category][skill] = skill_counts[skill]
        
        return dict(categorized)
    
    def _identify_emerging_skills(self, jobs: List[Dict[str, Any]]) -> List[str]:
        """Identify potentially emerging skills (placeholder for now)."""
        # This could be enhanced with time-based analysis
        return ['ai', 'blockchain', 'kubernetes', 'typescript', 'graphql']
    
    def _analyze_skill_trends(self, jobs: List[Dict[str, Any]]) -> Dict[str, str]:
        """Analyze skill demand trends (placeholder for now)."""
        return {
            'ai_ml': 'increasing',
            'cloud': 'stable',
            'mobile': 'decreasing'
        }
    
    def _extract_cities_from_locations(self, location_counts: Counter) -> Dict[str, int]:
        """Extract city names from location strings."""
        cities = defaultdict(int)
        
        for location, count in location_counts.items():
            # Simple city extraction (could be enhanced)
            parts = location.split(',')
            if parts:
                city = parts[0].strip()
                cities[city] += count
        
        return dict(sorted(cities.items(), key=lambda x: x[1], reverse=True)[:10])
