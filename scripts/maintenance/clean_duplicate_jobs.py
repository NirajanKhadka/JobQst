#!/usr/bin/env python3
"""
Clean duplicate jobs and verify data integrity
"""

import sys
sys.path.insert(0, 'src')

from src.core.job_database import get_job_db
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_duplicate_jobs(profile_name='Nirajan'):
    """Clean duplicate jobs based on URL and title+company combinations."""
    
    print(f"🧹 Starting duplicate cleanup for profile: {profile_name}")
    
    db = get_job_db(profile_name)
    all_jobs = db.get_jobs(limit=5000)
    
    print(f"📊 Found {len(all_jobs)} total jobs")
    
    # Track duplicates by URL
    url_tracker = {}
    url_duplicates = []
    
    # Track duplicates by title+company
    title_company_tracker = {}
    title_company_duplicates = []
    
    # First pass: identify duplicates
    for job in all_jobs:
        job_id = job.get('id')
        url = job.get('url', '').strip()
        title = job.get('title', '').strip().lower()
        company = job.get('company', '').strip().lower()
        
        # Check URL duplicates
        if url:
            if url in url_tracker:
                print(f"🔍 Found URL duplicate: {url}")
                url_duplicates.append({
                    'duplicate_id': job_id,
                    'original_id': url_tracker[url],
                    'url': url
                })
            else:
                url_tracker[url] = job_id
        
        # Check title+company duplicates
        if title and company:
            key = f"{title}|||{company}"
            if key in title_company_tracker:
                print(f"🔍 Found title+company duplicate: {title} at {company}")
                title_company_duplicates.append({
                    'duplicate_id': job_id,
                    'original_id': title_company_tracker[key],
                    'title': title,
                    'company': company
                })
            else:
                title_company_tracker[key] = job_id
    
    print(f"\n📈 Duplicate Analysis:")
    print(f"  URL duplicates found: {len(url_duplicates)}")
    print(f"  Title+Company duplicates found: {len(title_company_duplicates)}")
    
    # Create removal plan (prioritize keeping jobs with more data)
    jobs_to_remove = set()
    
    # Handle URL duplicates
    for dup in url_duplicates:
        # Get both jobs to compare
        original = None
        duplicate = None
        
        for job in all_jobs:
            if job.get('id') == dup['original_id']:
                original = job
            elif job.get('id') == dup['duplicate_id']:
                duplicate = job
        
        if original and duplicate:
            # Keep the one with more complete data
            original_score = calculate_completeness_score(original)
            duplicate_score = calculate_completeness_score(duplicate)
            
            if duplicate_score > original_score:
                # Keep duplicate, remove original
                jobs_to_remove.add(dup['original_id'])
                print(f"  📝 Will remove original {dup['original_id']} (score: {original_score}) keep duplicate {dup['duplicate_id']} (score: {duplicate_score})")
            else:
                # Keep original, remove duplicate
                jobs_to_remove.add(dup['duplicate_id'])
                print(f"  📝 Will remove duplicate {dup['duplicate_id']} (score: {duplicate_score}) keep original {dup['original_id']} (score: {original_score})")
    
    # Handle title+company duplicates (only if not already handled by URL)
    for dup in title_company_duplicates:
        if dup['duplicate_id'] not in jobs_to_remove and dup['original_id'] not in jobs_to_remove:
            # Get both jobs to compare
            original = None
            duplicate = None
            
            for job in all_jobs:
                if job.get('id') == dup['original_id']:
                    original = job
                elif job.get('id') == dup['duplicate_id']:
                    duplicate = job
            
            if original and duplicate:
                # Keep the one with more complete data
                original_score = calculate_completeness_score(original)
                duplicate_score = calculate_completeness_score(duplicate)
                
                if duplicate_score > original_score:
                    jobs_to_remove.add(dup['original_id'])
                    print(f"  📝 Will remove original {dup['original_id']} (title+company dup)")
                else:
                    jobs_to_remove.add(dup['duplicate_id'])
                    print(f"  📝 Will remove duplicate {dup['duplicate_id']} (title+company dup)")
    
    print(f"\n🗑️ Total jobs to remove: {len(jobs_to_remove)}")
    
    # Ask for confirmation
    if jobs_to_remove:
        response = input(f"\nRemove {len(jobs_to_remove)} duplicate jobs? (y/N): ")
        if response.lower() == 'y':
            # Remove duplicates
            removed_count = 0
            for job_id in jobs_to_remove:
                try:
                    # Note: You'll need to implement a delete method in your database class
                    # For now, we'll just mark them as filtered_out
                    result = db.update_job_status(job_id, 'duplicate_removed')
                    if result:
                        removed_count += 1
                except Exception as e:
                    print(f"❌ Error removing job {job_id}: {e}")
            
            print(f"✅ Successfully removed {removed_count} duplicate jobs")
        else:
            print("❌ Duplicate removal cancelled")
    
    # Final status
    remaining_jobs = db.get_jobs(limit=5000)
    print(f"\n📊 Final status:")
    print(f"  Jobs remaining: {len(remaining_jobs)}")
    
    # Status breakdown
    status_counts = {}
    for job in remaining_jobs:
        status = job.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"  Status distribution:")
    for status, count in sorted(status_counts.items()):
        print(f"    {status}: {count}")

def calculate_completeness_score(job):
    """Calculate how complete a job record is."""
    score = 0
    
    # Basic fields
    if job.get('title'): score += 1
    if job.get('company'): score += 1
    if job.get('location'): score += 1
    if job.get('url'): score += 1
    
    # Detailed fields
    if job.get('job_description'): score += 2
    if job.get('salary_range'): score += 1
    if job.get('requirements'): score += 1
    if job.get('benefits'): score += 1
    
    # Analysis fields
    if job.get('match_score', 0) > 0: score += 2
    if job.get('analysis_data'): score += 1
    if job.get('status') != 'new': score += 1
    
    return score

if __name__ == "__main__":
    clean_duplicate_jobs()
