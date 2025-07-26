#!/usr/bin/env python3
"""Analyze the job processing workflow and logic in detail."""

from src.core.job_database import get_job_db
from src.analysis.custom_data_extractor import CustomDataExtractor
from src.analysis.hybrid_processor import HybridProcessingEngine
import json

def analyze_job_processing():
    print("🔍 DETAILED JOB PROCESSING ANALYSIS")
    print("=" * 60)
    
    # Get a real job from database
    db = get_job_db('Nirajan')
    jobs = db.get_all_jobs()
    
    if not jobs:
        print("❌ No jobs found in database")
        return
    
    # Analyze first job in detail
    job = jobs[0]
    print(f"📋 ANALYZING JOB: {job.get('job_id', 'N/A')}")
    print("-" * 40)
    
    # Show raw job data structure
    print("🗂️ RAW JOB DATA STRUCTURE:")
    important_fields = ['job_id', 'title', 'company', 'location', 'summary', 'url', 'job_description', 'description', 'status', 'site']
    for field in important_fields:
        value = job.get(field, 'NOT_FOUND')
        if isinstance(value, str) and len(value) > 100:
            value = value[:100] + "..."
        print(f"  {field}: {value}")
    
    print("\n" + "=" * 60)
    print("🔧 CUSTOM DATA EXTRACTOR ANALYSIS")
    print("-" * 40)
    
    # Test custom data extractor
    extractor = CustomDataExtractor()
    
    try:
        result = extractor.extract_job_data(job)
        print(f"✅ Extraction successful with confidence: {result.confidence:.2f}")
        print(f"📝 Extracted Title: '{result.title}'")
        print(f"🏢 Extracted Company: '{result.company}'")
        print(f"📍 Extracted Location: '{result.location}'")
        print(f"💰 Extracted Salary: '{result.salary_range}'")
        print(f"📊 Extracted Experience: '{result.experience_level}'")
        print(f"💼 Extracted Employment Type: '{result.employment_type}'")
        print(f"🛠️ Extracted Skills: {result.skills}")
        print(f"📋 Extracted Requirements: {result.requirements}")
        print(f"🎁 Extracted Benefits: {result.benefits}")
        
    except Exception as e:
        print(f"❌ Custom extraction failed: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 TITLE EXTRACTION ANALYSIS")
    print("-" * 40)
    
    # Analyze title extraction specifically
    description = job.get('description') or job.get('job_description', '')
    title = job.get('title', '')
    url = job.get('url', '')
    
    print(f"📝 Original Title Field: '{title}'")
    print(f"🔗 Job URL: '{url}'")
    print(f"📄 Description Length: {len(description)} characters")
    print(f"📄 Description Preview: '{description[:200]}...'")
    
    # Test title extraction patterns
    full_text = f"{title}\n{description}"
    extracted_title = extractor.extract_title(full_text, title)
    print(f"🎯 Extracted Title Result: '{extracted_title}'")
    
    print("\n" + "=" * 60)
    print("🏢 COMPANY EXTRACTION ANALYSIS")
    print("-" * 40)
    
    extracted_company = extractor.extract_company(full_text, url)
    company_from_url = extractor._extract_company_from_url(url) if url else None
    
    print(f"🏢 Original Company Field: '{job.get('company', 'N/A')}'")
    print(f"🔗 Company from URL: '{company_from_url}'")
    print(f"🎯 Extracted Company Result: '{extracted_company}'")
    
    print("\n" + "=" * 60)
    print("⚠️ ISSUES IDENTIFIED")
    print("-" * 40)
    
    issues = []
    
    if not title or len(title.strip()) < 5:
        issues.append("❌ Title field is empty or too short")
    
    if title in ['Job Position', 'Careers', 'Home Office Toronto On']:
        issues.append(f"❌ Title '{title}' appears to be a scraping error or placeholder")
    
    if not description or len(description.strip()) < 50:
        issues.append("❌ Job description is missing or too short")
    
    if not job.get('company') or len(job.get('company', '').strip()) < 2:
        issues.append("❌ Company field is missing or invalid")
    
    if not url or not url.startswith('http'):
        issues.append("❌ Invalid or missing job URL")
    
    if issues:
        for issue in issues:
            print(f"  {issue}")
    else:
        print("  ✅ No obvious issues detected")
    
    print("\n" + "=" * 60)
    print("🔧 RECOMMENDED FIXES")
    print("-" * 40)
    
    print("1. 🕷️ FIX SCRAPING LOGIC:")
    print("   - Improve CSS selectors for job titles")
    print("   - Add validation to reject invalid titles")
    print("   - Extract full job descriptions, not just summaries")
    
    print("2. 🧹 DATA CLEANING:")
    print("   - Add title validation patterns")
    print("   - Clean up company names from URLs")
    print("   - Normalize location data")
    
    print("3. ✅ VALIDATION RULES:")
    print("   - Reject jobs with generic titles like 'Job Position'")
    print("   - Require minimum description length")
    print("   - Validate company names aren't just domain names")
    
    print("4. 🔄 PROCESSING LOGIC:")
    print("   - Add fallback title extraction from description")
    print("   - Improve regex patterns for structured data")
    print("   - Add confidence scoring for extraction quality")

if __name__ == "__main__":
    analyze_job_processing()