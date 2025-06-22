#!/usr/bin/env python3
"""
Real-Time Job Cache - Modern, Simple In-Memory Cache
Provides instant access to the latest scraped jobs for real-time dashboard updates.
"""

import threading
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque

class JobCache:
    """
    Singleton in-memory cache for real-time job updates.
    Thread-safe and optimized for fast access.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(JobCache, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        with self._lock:
            if self._initialized:
                return
                
            # Use deque for efficient append/pop operations
            self._jobs = deque(maxlen=500)  # Keep last 500 jobs
            self._stats = {
                'total_added': 0,
                'total_retrieved': 0,
                'cache_hits': 0,
                'last_updated': None
            }
            self._initialized = True
    
    def add_job(self, job: Dict) -> None:
        """Add a job to the cache (thread-safe)."""
        with self._lock:
            # Add timestamp if not present
            if 'cached_at' not in job:
                job['cached_at'] = datetime.now().isoformat()
            
            self._jobs.append(job)
            self._stats['total_added'] += 1
            self._stats['last_updated'] = datetime.now().isoformat()
    
    def get_jobs(self, limit: int = 50, profile: Optional[str] = None) -> List[Dict]:
        """Get the latest jobs from cache (thread-safe)."""
        with self._lock:
            jobs = list(self._jobs)
            self._stats['total_retrieved'] += 1
            self._stats['cache_hits'] += 1
            
            # Filter by profile if specified
            if profile:
                jobs = [job for job in jobs if job.get('profile', '') == profile]
            
            # Return the most recent jobs
            return jobs[-limit:] if len(jobs) > limit else jobs
    
    def get_stats(self) -> Dict:
        """Get cache statistics (thread-safe)."""
        with self._lock:
            return {
                'cache_size': len(self._jobs),
                'total_added': self._stats['total_added'],
                'total_retrieved': self._stats['total_retrieved'],
                'cache_hits': self._stats['cache_hits'],
                'last_updated': self._stats['last_updated'],
                'max_size': self._jobs.maxlen
            }
    
    def clear(self) -> None:
        """Clear the cache (thread-safe)."""
        with self._lock:
            self._jobs.clear()
            self._stats['total_added'] = 0
            self._stats['total_retrieved'] = 0
            self._stats['cache_hits'] = 0
            self._stats['last_updated'] = None
    
    def get_recent_jobs(self, hours: int = 24) -> List[Dict]:
        """Get jobs from the last N hours (thread-safe)."""
        with self._lock:
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            recent_jobs = []
            
            for job in self._jobs:
                try:
                    cached_at = datetime.fromisoformat(job.get('cached_at', ''))
                    if cached_at.timestamp() > cutoff_time:
                        recent_jobs.append(job)
                except (ValueError, TypeError):
                    # If timestamp parsing fails, include the job
                    recent_jobs.append(job)
            
            return recent_jobs
    
    def get_jobs_by_keyword(self, keyword: str, limit: int = 50) -> List[Dict]:
        """Get jobs filtered by keyword (thread-safe)."""
        with self._lock:
            filtered_jobs = []
            for job in self._jobs:
                if keyword.lower() in job.get('title', '').lower():
                    filtered_jobs.append(job)
                    if len(filtered_jobs) >= limit:
                        break
            
            return filtered_jobs
    
    def get_jobs_by_site(self, site: str, limit: int = 50) -> List[Dict]:
        """Get jobs filtered by site (thread-safe)."""
        with self._lock:
            filtered_jobs = []
            for job in self._jobs:
                if job.get('site', '').lower() == site.lower():
                    filtered_jobs.append(job)
                    if len(filtered_jobs) >= limit:
                        break
            
            return filtered_jobs

# Global instance for easy access
job_cache = JobCache()

def add_job_to_cache(job: Dict) -> None:
    """Convenience function to add a job to the cache."""
    job_cache.add_job(job)

def get_latest_jobs(limit: int = 50, profile: Optional[str] = None) -> List[Dict]:
    """Convenience function to get latest jobs from cache."""
    return job_cache.get_jobs(limit, profile)

def get_cache_stats() -> Dict:
    """Convenience function to get cache statistics."""
    return job_cache.get_stats() 