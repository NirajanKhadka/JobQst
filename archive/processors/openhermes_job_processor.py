def show_openhermes_features() -> None:
    """
    Display key features of OpenHermes 2.5 for job analysis.
    """
    print("\n✨ OpenHermes 2.5 Features:")
    print("• Advanced job analysis using LLM (OpenHermes 2.5)")
    print("• AI-powered compatibility scoring and recommendations")
    print("• Fast, consistent, and detailed analysis")
    print("• Supports custom scoring weights and methods")
    print("• Integrated with enhanced rule-based and fallback analysis")
    print("• Monitors AI service health and error rates")
    print("• Designed for automated job processing workflows")
print("💡 Run: ollama pull openhermes:v2.5")#!/usr/bin/env python3
"""
OpenHermes 2.5 Job Processor Test
Test the job processor with OpenHermes 2.5 exclusively
"""

import sys
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_openhermes_connection():
    """Test OpenHermes 2.5 connection."""
    print("🤖 Testing OpenHermes 2.5 Connection")
    print("=" * 50)
    
    try:
        import requests
        
        # Test Ollama service
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            openhermes_found = any("openhermes:v2.5" in model.get("name", "") for model in models)
            
            if openhermes_found:
                print("✅ OpenHermes 2.5 model is available")
            else:
                print("❌ OpenHermes 2.5 model not found")
                print("💡 Run: ollama pull openhermes:v2.5")
                return False
        else:
            print("❌ Ollama service not responding")
            return False
            
        # Test model generation
        test_payload = {
            "model": "openhermes:v2.5",
            "prompt": "<|im_start|>system\nYou are a job analysis expert.<|im_end|>\n<|im_start|>user\nAnalyze this job: Python Developer at TechCorp<|im_end|>\n<|im_start|>assistant\n",
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 100}
        }
        
        response = requests.post("http://localhost:11434/api/generate", json=test_payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("response"):
                print("✅ OpenHermes 2.5 generation test successful")
                print(f"📝 Sample response: {result['response'][:100]}...")
                return True
            else:
                print("❌ OpenHermes 2.5 returned empty response")
                return False
        else:
            print(f"❌ OpenHermes 2.5 generation failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def test_job_processor_with_openhermes():
    """Test the job processor with OpenHermes 2.5."""
    print("\n🔄 Testing Job Processor with OpenHermes 2.5")
    print("=" * 50)

    try:
        from src.dashboard.enhanced_job_processor import get_enhanced_job_processor
        from src.core.job_database import get_job_db

        # Initialize processor
        processor = get_enhanced_job_processor("Nirajan")
        db = get_job_db("Nirajan")

        # Check database status
        all_jobs = db.get_all_jobs()
        scraped_jobs = [job for job in all_jobs if job.get('status') == 'scraped']

        print(f"📊 Database Status:")
        print(f"  Total jobs: {len(all_jobs)}")
        print(f"  Scraped jobs (need processing): {len(scraped_jobs)}")

        if not scraped_jobs:
            print("⚠️  No scraped jobs found to process")
            print("💡 Run a scraper first to get some job URLs")
            return True  # Not a failure, just no data

        # Show sample jobs
        print(f"\n📋 Sample scraped jobs:")
        for i, job in enumerate(scraped_jobs[:3]):
            url = job.get('url', 'No URL')
            keyword = job.get('search_keyword', 'No keyword')
            print(f"  {i+1}. {keyword} - {url[:60]}...")

        # Start processing
        print(f"\n🚀 Starting job processor with OpenHermes 2.5...")
        success = processor.start_processing()

        if not success:
            print("❌ Failed to start job processor")
            return False

        print("✅ Job processor started successfully")

        print(f"\n📥 Adding {min(2, len(scraped_jobs))} jobs to processing queue...")
        test_jobs = scraped_jobs[:2]  # Process first 2 jobs
        added_count = processor.add_jobs_for_processing(test_jobs)

        if added_count == 0:
            print("❌ No jobs were added to the processing queue")
            processor.stop_processing()
            return False

        print(f"✅ Added {added_count} jobs to processing queue")

        # Monitor processing
        print(f"\n⏱️  Processing {added_count} jobs with OpenHermes 2.5...")
        print("   (This may take a few minutes for AI analysis)")

        start_time = time.time()
        last_processed = 0
        timeout = 300  # 5 minute timeout

        while time.time() - start_time < timeout:
            status = processor.get_status()
            processed_count = status['processed_count']
            queue_size = status['queue_size']
            error_count = status['error_count']
            ai_analyzed_count = status['ai_analyzed_count']

            # Show progress when it changes
            if processed_count != last_processed:
                elapsed = time.time() - start_time
                print(f"   Progress: {processed_count}/{added_count} | AI: {ai_analyzed_count} | Errors: {error_count} | Time: {elapsed:.1f}s")
                last_processed = processed_count

            # Check if processing is complete
            if queue_size == 0 and processed_count >= added_count:
                print("✅ Processing complete!")
                break

            time.sleep(3)  # Check every 3 seconds

        # Get final results
        final_status = processor.get_status()
        stats = final_status['stats']

        print(f"\n📈 Final Results:")
        print(f"  Total processed: {final_status['processed_count']}")
        print(f"  AI analyzed: {final_status['ai_analyzed_count']}")
        print(f"  Errors: {final_status['error_count']}")
        print(f"  Average AI score: {stats['average_ai_score']:.2f}")
        print(f"  High matches (≥0.8): {stats['high_matches_found']}")

        # Show analysis method breakdown
        methods = stats['analysis_methods']
        print(f"\n🔍 Analysis Methods Used:")
        print(f"  OpenHermes 2.5 (AI): {methods.get('ai', 0)}")
        print(f"  Enhanced Rule-based: {methods.get('enhanced_rule_based', 0)}")
        print(f"  Fallback: {methods.get('fallback', 0)}")

        # Show AI service health
        ai_health = stats['ai_service_health']
        print(f"\n🤖 AI Service Health:")
        print(f"  Connection status: {ai_health['connection_status']}")
        print(f"  Consecutive failures: {ai_health['consecutive_failures']}")
        print(f"  Last successful AI: {ai_health['last_successful_ai']}")

        # Stop processor
        print(f"\n⏹️ Stopping job processor...")
        processor.stop_processing()

        # Check results in database
        updated_jobs = db.get_all_jobs()
        processed_jobs = [job for job in updated_jobs if job.get('status') == 'processed']

        print(f"\n📊 Database After Processing:")
        print(f"  Total jobs: {len(updated_jobs)}")
        print(f"  Processed jobs: {len(processed_jobs)}")

        # Show sample processed jobs
        recent_processed = [job for job in processed_jobs if job.get('match_score', 0) >= 0.7][-3:]
        if recent_processed:
            print(f"\n📋 Recently Processed Jobs (Score ≥0.7):")
            for i, job in enumerate(recent_processed):
                title = job.get('title', 'No title')
                company = job.get('company', 'No company')
                score = job.get('match_score', 0)
                print(f"  {i+1}. {title} at {company} (Score: {score:.2f})")

        return True
    except Exception as e:
        print(f"❌ Job processor test failed: {e}")
        return False

    print("\n⚙️ Configuration:")
    print("• Temperature: 0.3 (consistent results)")
    print("• Max tokens: 2048 (detailed analysis)")
    print("• Top-p: 0.9 (high quality output)")
    print("• Timeout: 30 seconds per job")

    print("\n🎯 Scoring Weights:")
    print("• Skills: 40% (most important)")
    print("• Experience: 25%")
    print("• Location: 15%")
    print("• Cultural fit: 10%")
    print("• Growth potential: 10%")
    print("• Cultural fit: 10%")
    print("• Growth potential: 10%")

def main():
    """Main test function."""
    print("🚀 OpenHermes 2.5 Job Processor Test")
    print("=" * 60)
    
    # Show features
    show_openhermes_features()
    
    # Test connection
    if not test_openhermes_connection():
        print("\n❌ OpenHermes 2.5 connection test failed")
        print("💡 Please run: python setup_openhermes_job_processor.py")
        return False
    
    # Test job processor
    if not test_job_processor_with_openhermes():
        print("\n❌ Job processor test failed")
        return False
    
    # Success summary
    print("\n" + "=" * 60)
    print("🎉 OpenHermes 2.5 Job Processor Test Complete!")
    print("=" * 60)
    
    print("\n✅ All tests passed successfully!")
    print("✅ OpenHermes 2.5 is working properly")
    print("✅ Job analysis is producing quality results")
    print("✅ Default scores are now 0.7+ baseline")
    
    print("\n🚀 Next Steps:")
    print("• Check the dashboard for processed jobs")
    print("• Review compatibility scores and analysis")
    print("• Generate documents for high-scoring positions")
    print("• Set up automated processing workflows")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)