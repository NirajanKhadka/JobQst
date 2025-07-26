#!/usr/bin/env python3
"""Test enhanced 2-worker system on ALL jobs with detailed error logging."""

import logging
import traceback
from src.core.job_database import get_job_db
from src.analysis.hybrid_processor import HybridProcessingEngine
from src.analysis.custom_data_extractor import CustomDataExtractor
from src.ai.gpu_ollama_client import get_gpu_ollama_client
import time

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_processing_errors.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_all_jobs_processing():
    """Test processing on ALL jobs in database with detailed error logging."""
    
    print("🔍 TESTING ALL JOBS IN DATABASE")
    print("=" * 60)
    
    # Get all jobs from Nirajan profile
    db = get_job_db('Nirajan')
    all_jobs = db.get_all_jobs()
    
    print(f"📊 Total jobs to test: {len(all_jobs)}")
    print(f"📝 Error log file: job_processing_errors.log")
    print("-" * 60)
    
    # Initialize processors
    try:
        custom_extractor = CustomDataExtractor()
        print("✅ Custom extractor initialized")
    except Exception as e:
        logger.error(f"Failed to initialize custom extractor: {e}")
        return
    
    try:
        # Try to initialize hybrid processor (may fail due to Ollama)
        hybrid_processor = HybridProcessingEngine()
        print("✅ Hybrid processor initialized")
        hybrid_available = True
    except Exception as e:
        logger.warning(f"Hybrid processor initialization failed: {e}")
        hybrid_processor = None
        hybrid_available = False
        print("⚠️ Hybrid processor not available - using custom logic only")
    
    # Process each job
    successful_jobs = 0
    failed_jobs = 0
    error_summary = {}
    
    for i, job in enumerate(all_jobs):
        job_id = job.get('job_id', f'unknown_{i}')
        job_url = job.get('url', 'NO_URL')
        job_title = job.get('title', 'NO_TITLE')
        
        print(f"\n🔄 Processing Job {i+1}/{len(all_jobs)}: {job_id}")
        print(f"   🔗 URL: {job_url}")
        print(f"   📝 Title: {job_title}")
        
        try:
            # Test custom extraction
            logger.info(f"Starting custom extraction for job {job_id} - URL: {job_url}")
            
            start_time = time.time()
            custom_result = custom_extractor.extract_job_data(job)
            custom_time = time.time() - start_time
            
            print(f"   ✅ Custom extraction: {custom_time:.2f}s, confidence: {custom_result.confidence:.2f}")
            logger.info(f"Custom extraction successful for {job_id}: confidence={custom_result.confidence:.2f}")
            
            # Test hybrid processing if available
            if hybrid_available:
                try:
                    logger.info(f"Starting hybrid processing for job {job_id}")
                    
                    start_time = time.time()
                    hybrid_result = hybrid_processor.process_job(job)
                    hybrid_time = time.time() - start_time
                    
                    print(f"   ✅ Hybrid processing: {hybrid_time:.2f}s, method: {hybrid_result.processing_method}")
                    logger.info(f"Hybrid processing successful for {job_id}: method={hybrid_result.processing_method}")
                    
                except Exception as e:
                    logger.error(f"HYBRID PROCESSING ERROR for job {job_id} (URL: {job_url}): {e}")
                    logger.error(f"Hybrid processing traceback for {job_id}: {traceback.format_exc()}")
                    print(f"   ❌ Hybrid processing failed: {str(e)[:100]}...")
                    
                    # Track error types
                    error_type = type(e).__name__
                    if error_type not in error_summary:
                        error_summary[error_type] = []
                    error_summary[error_type].append({
                        'job_id': job_id,
                        'url': job_url,
                        'title': job_title,
                        'error': str(e)[:200]
                    })
            
            successful_jobs += 1
            
        except Exception as e:
            failed_jobs += 1
            logger.error(f"CRITICAL ERROR processing job {job_id} (URL: {job_url}): {e}")
            logger.error(f"Full traceback for {job_id}: {traceback.format_exc()}")
            print(f"   ❌ CRITICAL FAILURE: {str(e)[:100]}...")
            
            # Track critical errors
            error_type = f"CRITICAL_{type(e).__name__}"
            if error_type not in error_summary:
                error_summary[error_type] = []
            error_summary[error_type].append({
                'job_id': job_id,
                'url': job_url,
                'title': job_title,
                'error': str(e)[:200]
            })
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 PROCESSING SUMMARY")
    print("=" * 60)
    print(f"✅ Successful jobs: {successful_jobs}")
    print(f"❌ Failed jobs: {failed_jobs}")
    print(f"📈 Success rate: {(successful_jobs/(successful_jobs+failed_jobs)*100):.1f}%")
    
    # Print error summary
    if error_summary:
        print(f"\n🚨 ERROR SUMMARY BY TYPE:")
        print("-" * 40)
        
        for error_type, errors in error_summary.items():
            print(f"\n❌ {error_type}: {len(errors)} occurrences")
            
            for error in errors[:3]:  # Show first 3 examples
                print(f"   📋 Job: {error['job_id']}")
                print(f"   🔗 URL: {error['url']}")
                print(f"   📝 Title: {error['title']}")
                print(f"   💥 Error: {error['error']}")
                print()
            
            if len(errors) > 3:
                print(f"   ... and {len(errors) - 3} more similar errors")
    
    print(f"\n📝 Detailed logs saved to: job_processing_errors.log")
    print("🔍 Check the log file for complete error details and stack traces")

def analyze_job_data_quality():
    """Analyze the quality of job data in the database."""
    
    print("\n" + "=" * 60)
    print("📊 JOB DATA QUALITY ANALYSIS")
    print("=" * 60)
    
    db = get_job_db('Nirajan')
    all_jobs = db.get_all_jobs()
    
    # Analyze data quality
    quality_stats = {
        'total_jobs': len(all_jobs),
        'has_title': 0,
        'has_description': 0,
        'has_url': 0,
        'has_company': 0,
        'description_length': [],
        'problematic_titles': [],
        'ats_systems': {}
    }
    
    for job in all_jobs:
        # Check basic fields
        if job.get('title'):
            quality_stats['has_title'] += 1
            
            # Check for problematic titles
            title = job.get('title', '')
            problematic = ['Job Position', 'Careers', 'Current Opportunities', 'Home Office']
            if any(prob in title for prob in problematic):
                quality_stats['problematic_titles'].append({
                    'job_id': job.get('job_id'),
                    'title': title,
                    'url': job.get('url', '')
                })
        
        if job.get('job_description') or job.get('description'):
            quality_stats['has_description'] += 1
            desc_len = len(job.get('job_description', '') + job.get('description', ''))
            quality_stats['description_length'].append(desc_len)
        
        if job.get('url'):
            quality_stats['has_url'] += 1
            
            # Identify ATS systems
            url = job.get('url', '')
            if 'myworkdayjobs.com' in url:
                quality_stats['ats_systems']['Workday'] = quality_stats['ats_systems'].get('Workday', 0) + 1
            elif 'bamboohr.com' in url:
                quality_stats['ats_systems']['BambooHR'] = quality_stats['ats_systems'].get('BambooHR', 0) + 1
            elif 'taleo.net' in url:
                quality_stats['ats_systems']['Taleo'] = quality_stats['ats_systems'].get('Taleo', 0) + 1
            elif 'ashbyhq.com' in url:
                quality_stats['ats_systems']['AshbyHQ'] = quality_stats['ats_systems'].get('AshbyHQ', 0) + 1
            else:
                quality_stats['ats_systems']['Other'] = quality_stats['ats_systems'].get('Other', 0) + 1
        
        if job.get('company'):
            quality_stats['has_company'] += 1
    
    # Print quality analysis
    total = quality_stats['total_jobs']
    print(f"📊 Data Completeness:")
    print(f"   📝 Has Title: {quality_stats['has_title']}/{total} ({quality_stats['has_title']/total*100:.1f}%)")
    print(f"   📄 Has Description: {quality_stats['has_description']}/{total} ({quality_stats['has_description']/total*100:.1f}%)")
    print(f"   🔗 Has URL: {quality_stats['has_url']}/{total} ({quality_stats['has_url']/total*100:.1f}%)")
    print(f"   🏢 Has Company: {quality_stats['has_company']}/{total} ({quality_stats['has_company']/total*100:.1f}%)")
    
    if quality_stats['description_length']:
        avg_desc_len = sum(quality_stats['description_length']) / len(quality_stats['description_length'])
        print(f"   📏 Avg Description Length: {avg_desc_len:.0f} characters")
    
    print(f"\n🏗️ ATS Systems Detected:")
    for ats, count in quality_stats['ats_systems'].items():
        print(f"   {ats}: {count} jobs")
    
    if quality_stats['problematic_titles']:
        print(f"\n⚠️ Problematic Titles Found: {len(quality_stats['problematic_titles'])}")
        for prob in quality_stats['problematic_titles'][:5]:
            print(f"   📋 {prob['job_id']}: '{prob['title']}'")
            print(f"      🔗 {prob['url']}")

if __name__ == "__main__":
    try:
        analyze_job_data_quality()
        test_all_jobs_processing()
    except Exception as e:
        logger.critical(f"Script execution failed: {e}")
        logger.critical(f"Script traceback: {traceback.format_exc()}")
        print(f"💥 Script failed: {e}")