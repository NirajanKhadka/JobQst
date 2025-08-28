#!/usr/bin/env python3
"""
Quick verification test for optimized processor
"""

import asyncio
import time
from src.utils.profile_helpers import load_profile
from src.optimization.integrated_processor import create_optimized_processor

async def quick_test():
    """Quick test to verify optimization works"""
    print("🧪 Quick Optimization Test")
    
    # Load profile
    profile = load_profile("Nirajan")
    if not profile:
        print("❌ Failed to load profile")
        return False
    
    print(f"✅ Profile loaded: {profile['name']}")
    
    # Create 3 test jobs
    test_jobs = [
        {
            'id': 'test1',
            'title': 'Python Developer',
            'company': 'TechCorp',
            'location': 'Toronto, ON',
            'url': 'https://example.com/1',
            'description': 'Python, SQL, AWS experience required.',
            'salary': '$80k-100k'
        },
        {
            'id': 'test2', 
            'title': 'Senior Software Engineer',
            'company': 'StartupXYZ',
            'location': 'Remote',
            'url': 'https://example.com/2',
            'description': 'React, Node.js, JavaScript, Python skills needed.',
            'salary': '$90k-120k'
        },
        {
            'id': 'test3',
            'title': 'Junior Developer',
            'company': 'BigCorp',
            'location': 'Toronto, ON', 
            'url': 'https://example.com/3',
            'description': 'Entry level position. Training provided.',
            'salary': '$50k-65k'
        }
    ]
    
    print(f"🚀 Testing with {len(test_jobs)} jobs...")
    
    # Create processor
    processor = create_optimized_processor(
        user_profile=profile,
        cpu_workers=4,
        max_concurrent_stage2=1
    )
    
    # Process jobs
    start_time = time.time()
    results = await processor.process_jobs(test_jobs)
    total_time = time.time() - start_time
    
    # Analyze results
    apply_jobs = [r for r in results if r.recommendation == "apply"]
    review_jobs = [r for r in results if r.recommendation == "review"]
    
    print(f"\n✅ Test Results:")
    print(f"   Processing time: {total_time:.2f}s")
    print(f"   Jobs to apply: {len(apply_jobs)}")
    print(f"   Jobs to review: {len(review_jobs)}")
    print(f"   Performance: {len(test_jobs)/total_time:.1f} jobs/second")
    
    if apply_jobs:
        print(f"   Top match: {apply_jobs[0].stage1.title} ({apply_jobs[0].final_compatibility:.2f})")
    
    return len(results) == len(test_jobs)

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Optimization test {'passed' if success else 'failed'}")
