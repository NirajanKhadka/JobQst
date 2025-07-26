"""
Quick Start: Fast Job Processing (No AI Required)
Simple, fast, and reliable job analysis without GPU dependencies.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ai.parallel_job_processor import get_parallel_processor

async def process_jobs_simple(jobs):
    """Process jobs with fast parallel processing (no AI)."""
    
    # Initialize processor - works on any machine
    processor = get_parallel_processor(
        max_workers=8,      # CPU threads
        max_concurrent=16   # Async concurrency
    )
    
    # Process jobs
    result = await processor.process_jobs_async(jobs)
    
    return result

# Example usage
async def main():
    # Your job data
    jobs = [
        {
            'id': 'job_001',
            'title': 'Python Developer',
            'company': 'TechCorp',
            'description': 'Looking for Python developer with Django experience...',
            'location': 'Toronto, ON'
        }
        # Add more jobs...
    ]
    
    # Process jobs (no AI, no GPU needed)
    result = await process_jobs_simple(jobs)
    
    # Get results
    for job_result in result.job_results:
        print(f"Job: {job_result['title']}")
        print(f"Skills: {job_result['required_skills']}")
        print(f"Experience: {job_result['experience_level']}")
        print(f"Score: {job_result['compatibility_score']:.1%}")
        print("---")

if __name__ == "__main__":
    asyncio.run(main())