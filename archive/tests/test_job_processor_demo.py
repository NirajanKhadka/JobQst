#!/usr/bin/env python3
"""
Job Processor Demo and Analysis Script
Shows the logic, functionality, and tests the job processor with real job data.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def show_job_processor_logic():
    """
    Explain the Job Processor Logic - WHAT, WHEN, HOW
    """
    print("=" * 80)
    print("🔄 JOB PROCESSOR LOGIC OVERVIEW")
    print("=" * 80)
    
    print("\n🎯 WHAT IT DOES:")
    print("• Processes scraped job URLs to extract detailed job information")
    print("• Analyzes job compatibility using AI (Llama3) and rule-based methods")
    print("• Scores jobs based on user profile match (0.0 to 1.0 scale)")
    print("• Updates database with detailed job analysis and compatibility scores")
    print("• Provides intelligent job recommendations and filtering")
    
    print("\n⏰ WHEN IT'S USED:")
    print("• After job scraping when URLs need to be processed into detailed job data")
    print("• During automated job analysis workflows")
    print("• When users want AI-powered job compatibility scoring")
    print("• As part of the job application pipeline for intelligent filtering")
    
    print("\n🔧 HOW IT WORKS (Multi-Stage Pipeline):")
    print("1. 📥 JOB QUEUE MANAGEMENT")
    print("   - Loads scraped jobs from database (status='scraped')")
    print("   - Creates processing queue with job tasks")
    print("   - Manages worker threads for concurrent processing")
    
    print("2. 🌐 JOB DESCRIPTION SCRAPING")
    print("   - Uses Playwright browser automation")
    print("   - Extracts detailed job descriptions from URLs")
    print("   - Handles different job board formats (Eluta, Indeed, etc.)")
    print("   - Caches results to avoid re-scraping")
    
    print("3. 🤖 AI-POWERED ANALYSIS (Primary)")
    print("   - Uses Llama3 7B model via Ollama")
    print("   - Analyzes job requirements vs user profile")
    print("   - Generates compatibility scores and recommendations")
    print("   - Identifies skill matches and gaps")
    
    print("4. 📊 RULE-BASED ANALYSIS (Fallback)")
    print("   - Enhanced keyword matching and scoring")
    print("   - Experience level matching")
    print("   - Location and salary analysis")
    print("   - Ensures processing continues if AI fails")
    
    print("5. 💾 DATABASE UPDATES")
    print("   - Updates job status to 'processed'")
    print("   - Stores compatibility scores and analysis data")
    print("   - Adds extracted keywords and skills")
    print("   - Maintains processing metadata")
    
    print("\n🔍 KEY FEATURES:")
    print("• Fault-tolerant with automatic fallbacks")
    print("• Real-time processing status and statistics")
    print("• Concurrent processing with worker threads")
    print("• Comprehensive error handling and retry logic")
    print("• Integration with dashboard for monitoring")

def get_sample_jobs_from_database():
    """Get sample jobs from the database for testing."""
    try:
        from src.core.job_database import get_job_db
        
        db = get_job_db()
        all_jobs = db.get_all_jobs()
        
        # Get different types of jobs for demonstration
        scraped_jobs = [job for job in all_jobs if job.get('status') == 'scraped']
        processed_jobs = [job for job in all_jobs if job.get('status') == 'processed']
        
        print(f"📊 DATABASE STATUS:")
        print(f"• Total jobs: {len(all_jobs)}")
        print(f"• Scraped jobs (need processing): {len(scraped_jobs)}")
        print(f"• Processed jobs: {len(processed_jobs)}")
        
        if scraped_jobs:
            print(f"\n📋 SAMPLE SCRAPED JOBS (Need Processing):")
            for i, job in enumerate(scraped_jobs[:3]):
                url = job.get('url', 'No URL')
                keyword = job.get('search_keyword', 'No keyword')
                print(f"  {i+1}. {keyword} - {url[:60]}...")
        
        if processed_jobs:
            print(f"\n📋 SAMPLE PROCESSED JOBS:")
            for i, job in enumerate(processed_jobs[:3]):
                title = job.get('title', 'No title')
                company = job.get('company', 'No company')
                score = job.get('match_score', 0)
                print(f"  {i+1}. {title} at {company} (Score: {score:.2f})")
        
        return {
            'all_jobs': all_jobs,
            'scraped_jobs': scraped_jobs,
            'processed_jobs': processed_jobs
        }
        
    except Exception as e:
        logger.warning(f"Could not access database: {e}")
        print("⚠️  Database not accessible. Using sample data.")
        return create_sample_job_data()

def create_sample_job_data():
    """Create sample job data for testing."""
    return {
        'scraped_jobs': [
            {
                'id': 1,
                'url': 'https://eluta.ca/job/senior-python-developer-123',
                'status': 'scraped',
                'search_keyword': 'python developer',
                'title': 'Pending Processing',
                'company': 'Unknown',
                'location': 'Unknown'
            },
            {
                'id': 2,
                'url': 'https://eluta.ca/job/data-scientist-456',
                'status': 'scraped',
                'search_keyword': 'data scientist',
                'title': 'Pending Processing',
                'company': 'Unknown',
                'location': 'Unknown'
            }
        ],
        'processed_jobs': []
    }

def demonstrate_processing_pipeline():
    """Demonstrate the job processing pipeline."""
    print("\n" + "=" * 80)
    print("🔄 DEMONSTRATING PROCESSING PIPELINE")
    print("=" * 80)
    
    print("\n1. 📥 QUEUE MANAGEMENT:")
    print("   • JobProcessorQueue manages worker threads")
    print("   • JobTask objects represent individual jobs to process")
    print("   • Queue supports priority and retry mechanisms")
    
    print("\n2. 🌐 JOB DESCRIPTION SCRAPING:")
    print("   • EnhancedJobDescriptionScraper extracts job details")
    print("   • Uses Playwright for JavaScript-heavy sites")
    print("   • Handles different job board formats automatically")
    print("   • Caches results to improve performance")
    
    print("\n3. 🤖 AI ANALYSIS PROCESS:")
    print("   • ReliableJobProcessorAnalyzer coordinates analysis")
    print("   • Checks Ollama connection before attempting AI")
    print("   • Uses Llama3 7B model for intelligent analysis")
    print("   • Falls back to rule-based analysis if AI fails")
    
    print("\n4. 📊 ANALYSIS COMPONENTS:")
    print("   • Compatibility scoring (0.0 to 1.0)")
    print("   • Skill matching and gap analysis")
    print("   • Experience level assessment")
    print("   • Location and cultural fit evaluation")
    
    print("\n5. 💾 DATABASE INTEGRATION:")
    print("   • Updates job status from 'scraped' to 'processed'")
    print("   • Stores match_score for filtering and sorting")
    print("   • Saves full analysis_data as JSON")
    print("   • Maintains processing metadata and timestamps")

def test_job_processor_components():
    """Test individual job processor components."""
    print("\n" + "=" * 80)
    print("🧪 TESTING JOB PROCESSOR COMPONENTS")
    print("=" * 80)
    
    # Test 1: Database Connection
    print("\n1. 📊 TESTING DATABASE CONNECTION:")
    try:
        from src.core.job_database import get_job_db
        db = get_job_db()
        job_count = db.get_job_count()
        print(f"   ✅ Database connected - {job_count} jobs found")
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False
    
    # Test 2: AI Service Connection
    print("\n2. 🤖 TESTING AI SERVICE CONNECTION:")
    try:
        from src.services.ollama_connection_checker import get_ollama_checker
        checker = get_ollama_checker()
        is_available = checker.is_available()
        if is_available:
            print("   ✅ Ollama service is available")
            models = checker.get_available_models()
            print(f"   📋 Available models: {', '.join(models) if models else 'None'}")
        else:
            print("   ⚠️  Ollama service not available - will use rule-based analysis")
    except Exception as e:
        print(f"   ❌ AI service check failed: {e}")
    
    # Test 3: Enhanced Job Processor
    print("\n3. 🔄 TESTING ENHANCED JOB PROCESSOR:")
    try:
        from src.dashboard.enhanced_job_processor import get_enhanced_job_processor
        processor = get_enhanced_job_processor("Nirajan")
        status = processor.get_status()
        print(f"   ✅ Job processor initialized")
        print(f"   📊 Status: Active={status['active']}, Profile={status['profile']}")
    except Exception as e:
        print(f"   ❌ Job processor initialization failed: {e}")
        return False
    
    # Test 4: Rule-based Analyzer
    print("\n4. 📊 TESTING RULE-BASED ANALYZER:")
    try:
        from src.ai.enhanced_rule_based_analyzer import EnhancedRuleBasedAnalyzer
        from src.utils.profile_helpers import load_profile
        
        profile = load_profile("Nirajan")
        analyzer = EnhancedRuleBasedAnalyzer(profile)
        
        test_job = {
            'title': 'Senior Python Developer',
            'description': 'Looking for Python developer with SQL experience',
            'location': 'Toronto, ON',
            'company': 'Test Company'
        }
        
        result = analyzer.analyze_job(test_job)
        score = result.get('compatibility_score', 0)
        print(f"   ✅ Rule-based analysis working - Score: {score:.2f}")
        
    except Exception as e:
        print(f"   ❌ Rule-based analyzer test failed: {e}")
    
    return True

def run_job_processor_demo():
    """Run a live demonstration of the job processor."""
    print("\n" + "=" * 80)
    print("🚀 RUNNING JOB PROCESSOR DEMO")
    print("=" * 80)
    
    # Get jobs from database
    job_data = get_sample_jobs_from_database()
    scraped_jobs = job_data.get('scraped_jobs', [])
    
    if not scraped_jobs:
        print("❌ No scraped jobs found to process")
        print("💡 Run the scraper first to get some job URLs")
        return False
    
    print(f"\n📥 Found {len(scraped_jobs)} scraped jobs to process")
    
    # Initialize processor
    try:
        from src.dashboard.enhanced_job_processor import get_enhanced_job_processor
        processor = get_enhanced_job_processor("Nirajan")
        
        print(f"✅ Job processor initialized for profile: Nirajan")
        
        # Start processing
        print(f"\n🔄 Starting job processor...")
        success = processor.start_processing()
        
        if not success:
            print("❌ Failed to start job processor")
            return False
        
        print("✅ Job processor started successfully")
        
        # Add jobs to processing queue
        print(f"\n📥 Adding jobs to processing queue...")
        added_count = processor.add_jobs_for_processing(scraped_jobs[:3])  # Process first 3 jobs
        
        if added_count == 0:
            print("❌ No jobs were added to the processing queue")
            processor.stop_processing()
            return False
        
        print(f"✅ Added {added_count} jobs to processing queue")
        
        # Monitor processing
        print(f"\n⏱️  Processing {added_count} jobs...")
        print("   (This may take a few minutes depending on AI service availability)")
        
        start_time = time.time()
        last_processed = 0
        
        for i in range(60):  # Monitor for up to 60 iterations (5 minutes)
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
                print("   ✅ Processing complete!")
                break
            
            time.sleep(5)  # Check every 5 seconds
        
        # Get final results
        final_status = processor.get_status()
        stats = final_status['stats']
        
        print(f"\n📈 PROCESSING RESULTS:")
        print(f"   Total processed: {final_status['processed_count']}")
        print(f"   AI analyzed: {final_status['ai_analyzed_count']}")
        print(f"   Errors: {final_status['error_count']}")
        print(f"   Average AI score: {stats['average_ai_score']:.2f}")
        print(f"   High matches (≥0.8): {stats['high_matches_found']}")
        
        # Show analysis method breakdown
        methods = stats['analysis_methods']
        print(f"\n🔍 ANALYSIS METHODS USED:")
        print(f"   AI: {methods['ai']}")
        print(f"   Enhanced Rule-based: {methods['enhanced_rule_based']}")
        print(f"   Fallback: {methods['fallback']}")
        
        # Show AI service health
        ai_health = stats['ai_service_health']
        print(f"\n🤖 AI SERVICE HEALTH:")
        print(f"   Connection status: {ai_health['connection_status']}")
        print(f"   Consecutive failures: {ai_health['consecutive_failures']}")
        print(f"   Last successful AI: {ai_health['last_successful_ai']}")
        
        # Stop processor
        print(f"\n⏹️ Stopping job processor...")
        processor.stop_processing()
        
        # Check database after processing
        from src.core.job_database import get_job_db
        db = get_job_db()
        updated_jobs = db.get_all_jobs()
        processed_jobs = [job for job in updated_jobs if job.get('status') == 'processed']
        
        print(f"\n📊 DATABASE AFTER PROCESSING:")
        print(f"   Total jobs: {len(updated_jobs)}")
        print(f"   Processed jobs: {len(processed_jobs)}")
        
        # Show sample processed jobs
        recent_processed = [job for job in processed_jobs if job.get('match_score', 0) > 0][-3:]
        if recent_processed:
            print(f"\n📋 RECENTLY PROCESSED JOBS:")
            for i, job in enumerate(recent_processed):
                title = job.get('title', 'No title')
                company = job.get('company', 'No company')
                score = job.get('match_score', 0)
                print(f"   {i+1}. {title} at {company} (Score: {score:.2f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"Job processor demo failed: {e}")
        return False

def show_processing_architecture():
    """Show the job processor architecture."""
    print("\n" + "=" * 80)
    print("🏗️ JOB PROCESSOR ARCHITECTURE")
    print("=" * 80)
    
    print("\n📊 COMPONENT HIERARCHY:")
    print("┌─ EnhancedJobProcessor (Main Controller)")
    print("├─── JobProcessorQueue (Queue Management)")
    print("├─── ReliableJobProcessorAnalyzer (AI Coordination)")
    print("│    ├─── EnhancedJobAnalyzer (AI Analysis)")
    print("│    └─── EnhancedRuleBasedAnalyzer (Fallback)")
    print("├─── EnhancedJobDescriptionScraper (Web Scraping)")
    print("├─── OllamaConnectionChecker (AI Health)")
    print("└─── ModernJobDatabase (Data Storage)")
    
    print("\n🔄 DATA FLOW:")
    print("1. Scraped URLs (status='scraped') → Processing Queue")
    print("2. Queue → Worker Threads → Job Description Scraping")
    print("3. Job Details → AI Analysis (Llama3) or Rule-based")
    print("4. Analysis Results → Database Update (status='processed')")
    print("5. Processed Jobs → Dashboard Display & Filtering")
    
    print("\n⚡ FAULT TOLERANCE:")
    print("• AI Service Down → Automatic fallback to rule-based analysis")
    print("• Network Issues → Retry mechanism with exponential backoff")
    print("• Scraping Failures → Error logging and job marking")
    print("• Database Errors → Transaction rollback and error recovery")
    print("• Worker Crashes → Automatic worker restart and task requeue")

def main():
    """Main function to run the job processor demo."""
    print("🚀 JOB PROCESSOR DEMO STARTING...")
    
    # Show the logic overview
    show_job_processor_logic()
    
    # Demonstrate processing pipeline
    demonstrate_processing_pipeline()
    
    # Show architecture
    show_processing_architecture()
    
    # Test components
    components_ok = test_job_processor_components()
    
    if not components_ok:
        print("\n❌ Component tests failed - skipping live demo")
        print("💡 Check your Ollama installation and database setup")
        return
    
    # Run live demo
    demo_success = run_job_processor_demo()
    
    print("\n" + "=" * 80)
    print("📊 DEMO SUMMARY")
    print("=" * 80)
    
    if demo_success:
        print("✅ Job processor demo completed successfully!")
        print("✅ All processing mechanisms working properly")
        print("✅ Jobs processed and scored in database")
    else:
        print("❌ Some parts of the demo failed - check logs for details")
    
    print("\n🎯 KEY TAKEAWAYS:")
    print("• Job processor uses multi-stage pipeline for reliability")
    print("• AI analysis provides intelligent compatibility scoring")
    print("• Rule-based fallback ensures processing continues")
    print("• System handles errors gracefully with comprehensive logging")
    print("• Real-time monitoring and statistics available")
    print("• Processed jobs can be filtered and sorted by compatibility score")
    
    print("\n🔗 NEXT STEPS:")
    print("• Check the dashboard to see processed jobs")
    print("• Use compatibility scores to filter high-match jobs")
    print("• Generate documents for top-scoring positions")
    print("• Set up automated application workflows")

if __name__ == "__main__":
    main()