import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.core.job_database import get_job_db
    
    # Get Nirajan profile database
    db = get_job_db("Nirajan")
    
    # Get job count
    job_count = db.get_job_count()
    print(f"Total jobs in Nirajan profile: {job_count}")
    
    # Get all jobs
    all_jobs = db.get_all_jobs()
    print(f"All jobs count: {len(all_jobs)}")
    
    if all_jobs:
        print("\nSample job from Nirajan profile:")
        sample_job = all_jobs[0]
        print(f"ID: {sample_job.get('id', 'N/A')}")
        print(f"Title: {sample_job.get('title', 'N/A')}")
        print(f"Company: {sample_job.get('company', 'N/A')}")
        print(f"Location: {sample_job.get('location', 'N/A')}")
        print(f"Status: {sample_job.get('status', 'N/A')}")
        print(f"Description length: {len(sample_job.get('description', ''))}")
        
        # Show all available fields
        print(f"\nAvailable fields: {list(sample_job.keys())}")
    
    # Get job stats
    try:
        stats = db.get_job_stats()
        print(f"\nJob stats: {stats}")
    except Exception as e:
        print(f"Could not get stats: {e}")
        
except Exception as e:
    print(f"Error accessing Nirajan database: {e}")
    import traceback
    traceback.print_exc()