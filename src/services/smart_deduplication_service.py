#!/usr/bin/env python3
"""
Smart Deduplication Service for JobLens
Intelligently merges duplicate jobs from multiple sources while preserving the most complete data.

Features:
- Multi-criteria duplicate detection (URL, title+company, title+location)
- Intelligent data merging (keeps most complete descriptions, all unique URLs)
- Source tracking for all job sites
- Conflict resolution with preference for more complete data
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime
import json
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class SmartDeduplicationService:
    """Service for intelligent job deduplication and merging."""
    
    def __init__(self):
        self.duplicate_criteria = {
            'url_match': 1.0,           # Exact URL match
            'title_company_match': 0.9,  # Title + Company match
            'title_location_match': 0.8, # Title + Location match (if no company)
            'fuzzy_title_company': 0.85, # Fuzzy title + exact company
        }
        
    def find_and_merge_duplicates(self, jobs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Find duplicates and merge them intelligently.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            Tuple of (merged_jobs, stats)
        """
        if not jobs:
            return jobs, {'total_jobs': 0, 'duplicates_found': 0, 'jobs_merged': 0}
        
        stats = {
            'total_jobs': len(jobs),
            'duplicates_found': 0,
            'jobs_merged': 0,
            'url_duplicates': 0,
            'title_company_duplicates': 0,
            'title_location_duplicates': 0,
            'fuzzy_duplicates': 0
        }
        
        # Create job groups - each group contains potential duplicates
        job_groups = []
        processed_indices = set()
        
        for i, job in enumerate(jobs):
            if i in processed_indices:
                continue
                
            # Start a new group with this job
            current_group = [i]
            processed_indices.add(i)
            
            # Find all jobs that are duplicates of this one
            for j, other_job in enumerate(jobs[i+1:], start=i+1):
                if j in processed_indices:
                    continue
                    
                duplicate_type = self._check_duplicate(job, other_job)
                if duplicate_type:
                    current_group.append(j)
                    processed_indices.add(j)
                    stats['duplicates_found'] += 1
                    stats[f'{duplicate_type}_duplicates'] += 1
            
            job_groups.append(current_group)
        
        # Merge each group
        merged_jobs = []
        for group in job_groups:
            if len(group) == 1:
                # No duplicates, keep as is
                merged_jobs.append(jobs[group[0]])
            else:
                # Merge the duplicates
                group_jobs = [jobs[i] for i in group]
                merged_job = self._merge_job_group(group_jobs)
                merged_jobs.append(merged_job)
                stats['jobs_merged'] += len(group) - 1
        
        logger.info(f"Deduplication complete: {stats['total_jobs']} -> {len(merged_jobs)} jobs "
                   f"({stats['duplicates_found']} duplicates merged)")
        
        return merged_jobs, stats
    
    def _check_duplicate(self, job1: Dict[str, Any], job2: Dict[str, Any]) -> Optional[str]:
        """
        Check if two jobs are duplicates and return the type of duplicate.
        
        Returns:
            String indicating duplicate type or None if not duplicates
        """
        # URL match (highest priority)
        url1 = self._normalize_url(job1.get('url', ''))
        url2 = self._normalize_url(job2.get('url', ''))
        if url1 and url2 and url1 == url2:
            return 'url'
        
        # Title + Company match
        title1 = self._normalize_text(job1.get('title', ''))
        title2 = self._normalize_text(job2.get('title', ''))
        company1 = self._normalize_text(job1.get('company', ''))
        company2 = self._normalize_text(job2.get('company', ''))
        
        if title1 and title2 and company1 and company2:
            if title1 == title2 and company1 == company2:
                return 'title_company'
            
            # Fuzzy title match with exact company
            if company1 == company2:
                similarity = SequenceMatcher(None, title1, title2).ratio()
                if similarity >= 0.85:  # 85% similarity threshold
                    return 'fuzzy'
        
        # Title + Location match (if no company info)
        location1 = self._normalize_text(job1.get('location', ''))
        location2 = self._normalize_text(job2.get('location', ''))
        
        if title1 and title2 and location1 and location2:
            if not company1 and not company2:  # Only if no company info
                if title1 == title2 and location1 == location2:
                    return 'title_location'
        
        return None
    
    def _merge_job_group(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge a group of duplicate jobs into a single job with the best data.
        
        Args:
            jobs: List of duplicate job dictionaries
            
        Returns:
            Merged job dictionary
        """
        if len(jobs) == 1:
            return jobs[0]
        
        # Use the job with the highest completeness score as base
        base_job = max(jobs, key=self._calculate_completeness_score)
        merged_job = base_job.copy()
        
        # Collect all unique sources and URLs
        sources = set()
        urls = set()
        sites = set()
        
        for job in jobs:
            # Collect sources
            if job.get('site'):
                sources.add(job['site'])
                sites.add(job['site'])
            
            # Collect URLs
            if job.get('url'):
                urls.add(job['url'])
        
        # Merge text fields by taking the longest/most complete version
        text_fields = ['description', 'job_description', 'summary', 'requirements', 'benefits']
        for field in text_fields:
            longest_text = ""
            for job in jobs:
                text = job.get(field, '') or ''
                if len(text) > len(longest_text):
                    longest_text = text
            if longest_text:
                merged_job[field] = longest_text
        
        # Merge list fields (skills, keywords, etc.)
        list_fields = ['keywords', 'required_skills', 'skills']
        for field in list_fields:
            unique_items = set()
            for job in jobs:
                value = job.get(field)
                if value:
                    if isinstance(value, str):
                        # Try to parse as JSON list or split by common delimiters
                        try:
                            items = json.loads(value)
                            if isinstance(items, list):
                                unique_items.update(items)
                            else:
                                unique_items.add(str(items))
                        except:
                            # Split by common delimiters
                            items = re.split(r'[,;|]', value)
                            unique_items.update(item.strip() for item in items if item.strip())
                    elif isinstance(value, list):
                        unique_items.update(value)
            if unique_items:
                merged_job[field] = list(unique_items)
        
        # Handle numeric fields (take the higher value for salary, scores)
        numeric_fields = ['match_score', 'compatibility_score', 'analysis_confidence']
        for field in numeric_fields:
            max_value = 0
            for job in jobs:
                value = job.get(field, 0) or 0
                if isinstance(value, (int, float)) and value > max_value:
                    max_value = value
            if max_value > 0:
                merged_job[field] = max_value
        
        # Add deduplication metadata
        merged_job['sources'] = list(sources)
        merged_job['source_urls'] = list(urls)
        merged_job['source_sites'] = list(sites)
        merged_job['merged_from_count'] = len(jobs)
        merged_job['merged_at'] = datetime.now().isoformat()
        merged_job['deduplication_method'] = 'smart_merge'
        
        # Update status to indicate this is a merged job
        merged_job['status'] = 'merged'
        
        logger.debug(f"Merged {len(jobs)} duplicate jobs: {merged_job.get('title', 'Unknown')} "
                    f"from sources: {', '.join(sources)}")
        
        return merged_job
    
    def _calculate_completeness_score(self, job: Dict[str, Any]) -> float:
        """
        Calculate how complete a job record is (0.0 to 1.0).
        Higher scores indicate more complete job data.
        """
        score = 0.0
        max_score = 0.0
        
        # Essential fields (higher weight)
        essential_fields = {
            'title': 0.2,
            'company': 0.15,
            'location': 0.1,
            'url': 0.1,
            'description': 0.15,
            'job_description': 0.15
        }
        
        for field, weight in essential_fields.items():
            max_score += weight
            value = job.get(field, '')
            if value and str(value).strip():
                if field in ['description', 'job_description']:
                    # Score based on length for text fields
                    text_length = len(str(value))
                    if text_length > 500:
                        score += weight
                    elif text_length > 200:
                        score += weight * 0.8
                    elif text_length > 50:
                        score += weight * 0.5
                    else:
                        score += weight * 0.2
                else:
                    score += weight
        
        # Additional fields (lower weight)
        additional_fields = {
            'salary_range': 0.05,
            'job_type': 0.03,
            'experience_level': 0.03,
            'requirements': 0.05,
            'benefits': 0.04
        }
        
        for field, weight in additional_fields.items():
            max_score += weight
            value = job.get(field, '')
            if value and str(value).strip():
                score += weight
        
        return score / max_score if max_score > 0 else 0.0
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison."""
        if not url:
            return ''
        
        url = url.strip().lower()
        
        # Remove common URL parameters that don't affect job identity
        remove_params = ['utm_source', 'utm_medium', 'utm_campaign', 'ref', 'source']
        for param in remove_params:
            if f'{param}=' in url:
                url = re.sub(f'[?&]{param}=[^&]*', '', url)
        
        # Normalize trailing slashes
        if url.endswith('/') and url != 'https://' and url != 'http://':
            url = url.rstrip('/')
        
        return url
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ''
        
        # Convert to lowercase and strip whitespace
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common punctuation that doesn't affect meaning
        text = re.sub(r'[.,;:!?()]', '', text)
        
        return text
    
    def get_duplicate_report(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a report about duplicates without merging them.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            Dictionary with duplicate analysis results
        """
        report = {
            'total_jobs': len(jobs),
            'duplicate_groups': [],
            'statistics': {
                'url_duplicates': 0,
                'title_company_duplicates': 0,
                'title_location_duplicates': 0,
                'fuzzy_duplicates': 0,
                'total_duplicates': 0
            }
        }
        
        processed_indices = set()
        
        for i, job in enumerate(jobs):
            if i in processed_indices:
                continue
            
            duplicate_group = [i]
            duplicate_types = []
            
            for j, other_job in enumerate(jobs[i+1:], start=i+1):
                if j in processed_indices:
                    continue
                
                duplicate_type = self._check_duplicate(job, other_job)
                if duplicate_type:
                    duplicate_group.append(j)
                    duplicate_types.append(duplicate_type)
                    processed_indices.add(j)
                    report['statistics'][f'{duplicate_type}_duplicates'] += 1
            
            if len(duplicate_group) > 1:
                processed_indices.add(i)
                report['duplicate_groups'].append({
                    'indices': duplicate_group,
                    'types': duplicate_types,
                    'primary_job': {
                        'title': job.get('title', 'Unknown'),
                        'company': job.get('company', 'Unknown'),
                        'url': job.get('url', '')
                    }
                })
        
        report['statistics']['total_duplicates'] = len(report['duplicate_groups'])
        
        return report
