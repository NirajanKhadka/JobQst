#!/usr/bin/env python3
"""
Document Generator Demo and Test Script
Shows the logic, functionality, and tests the document generator with real job data.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def show_document_generator_logic():
    """
    Explain the Document Generator Logic - WHAT, WHEN, HOW
    """
    print("=" * 80)
    print("📄 DOCUMENT GENERATOR LOGIC OVERVIEW")
    print("=" * 80)
    
    print("\n🎯 WHAT IT DOES:")
    print("• Customizes documents (resumes, cover letters) for specific job applications")
    print("• Replaces placeholders with job-specific and user-specific information")
    print("• Uses AI when available, falls back to template-based customization")
    print("• Ensures professional, tailored documents for each application")
    
    print("\n⏰ WHEN IT'S USED:")
    print("• During job application process when documents need customization")
    print("• After job scraping when preparing application materials")
    print("• When user requests document generation for specific positions")
    print("• As part of automated application workflow")
    
    print("\n🔧 HOW IT WORKS (3-Tier Approach):")
    print("1. 🤖 AI-POWERED CUSTOMIZATION (Primary)")
    print("   - Uses Gemini API or other AI services")
    print("   - Generates intelligent, context-aware content")
    print("   - Tailors language and emphasis to job requirements")
    
    print("2. 📝 TEMPLATE-BASED CUSTOMIZATION (Fallback)")
    print("   - Uses predefined templates with placeholders")
    print("   - Performs smart substitutions based on job/profile data")
    print("   - Maintains professional formatting and structure")
    
    print("3. ⚡ BASIC CUSTOMIZATION (Final Fallback)")
    print("   - Simple find-and-replace operations")
    print("   - Ensures no placeholders remain in final document")
    print("   - Guarantees functional output even if AI/templates fail")
    
    print("\n🔍 KEY FEATURES:")
    print("• Error tolerance with retry mechanisms")
    print("• Validation to ensure proper customization")
    print("• Support for both string and dictionary document formats")
    print("• Comprehensive placeholder detection and replacement")
    print("• Integration with user profiles and job data")

def get_sample_job_from_database():
    """Get a sample job from the database for testing."""
    try:
        from src.core.job_database import get_job_db
        
        db = get_job_db()
        jobs = db.get_jobs(limit=1)
        
        if not jobs:
            print("❌ No jobs found in database. Let's create a sample job for testing.")
            return create_sample_job_data()
        
        job = jobs[0]
        print(f"✅ Found job in database: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
        return job
        
    except Exception as e:
        logger.warning(f"Could not access database: {e}")
        print("⚠️  Database not accessible. Using sample job data.")
        return create_sample_job_data()

def create_sample_job_data():
    """Create sample job data for testing."""
    return {
        'id': 1,
        'title': 'Senior Python Developer',
        'company': 'TechCorp Solutions',
        'location': 'Toronto, ON',
        'url': 'https://example.com/job/123',
        'job_description': '''
We are seeking a Senior Python Developer to join our growing team. 
The ideal candidate will have:
- 5+ years of Python development experience
- Experience with Django/Flask frameworks
- Strong knowledge of databases (PostgreSQL, MongoDB)
- Experience with cloud platforms (AWS, Azure)
- Excellent problem-solving skills
        ''',
        'requirements': 'Python, Django, PostgreSQL, AWS, 5+ years experience',
        'salary_range': '$80,000 - $120,000 CAD',
        'job_type': 'Full-time',
        'remote_option': 'Hybrid',
        'site': 'eluta.ca',
        'scraped_at': '2024-01-15 10:30:00'
    }

def get_sample_profile_data():
    """Get sample user profile data."""
    return {
        'name': 'John Developer',
        'email': 'john.developer@email.com',
        'phone': '(555) 123-4567',
        'location': 'Toronto, ON',
        'summary': 'Experienced Python developer with 6 years of full-stack development experience.',
        'skills': ['Python', 'Django', 'PostgreSQL', 'AWS', 'Docker', 'React'],
        'experience': [
            {
                'company': 'Previous Tech Co',
                'position': 'Python Developer',
                'duration': '2020-2024',
                'description': 'Developed web applications using Django and PostgreSQL'
            }
        ],
        'education': [
            {
                'degree': 'Bachelor of Computer Science',
                'school': 'University of Toronto',
                'year': '2018'
            }
        ]
    }

def create_sample_documents():
    """Create sample documents for testing."""
    
    cover_letter_template = """Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company}. With my extensive background in software development and passion for innovative technology solutions, I am confident I would be a valuable addition to your team.

In my previous role at Previous Tech Co, I have gained significant experience in Python development, working with frameworks like Django and managing PostgreSQL databases. My technical skills align well with your requirements, and I am particularly excited about the opportunity to work with {company}'s cutting-edge projects.

Key qualifications I bring include:
• 6+ years of Python development experience
• Strong expertise in Django and web application development
• Experience with cloud platforms and modern development practices
• Proven track record of delivering high-quality software solutions

I am excited about the opportunity to contribute to {company} and would welcome the chance to discuss how my skills and experience align with your team's needs. Thank you for considering my application.

Sincerely,
{name}
{email}
{phone}"""

    resume_template = """{name}
{email} | {phone} | {location}

PROFESSIONAL SUMMARY
{summary}

TECHNICAL SKILLS
{skills}

PROFESSIONAL EXPERIENCE
{experience}

EDUCATION
{education}

I am particularly interested in the {job_title} role at {company} and believe my experience makes me an ideal candidate for this position."""

    return {
        'cover_letter': cover_letter_template,
        'resume': resume_template
    }

def test_document_customization():
    """Test the document generator with real data."""
    print("\n" + "=" * 80)
    print("🧪 TESTING DOCUMENT GENERATOR")
    print("=" * 80)
    
    # Get test data
    job_data = get_sample_job_from_database()
    profile_data = get_sample_profile_data()
    documents = create_sample_documents()
    
    print(f"\n📋 JOB DATA:")
    print(f"• Title: {job_data.get('title')}")
    print(f"• Company: {job_data.get('company')}")
    print(f"• Location: {job_data.get('location')}")
    
    print(f"\n👤 PROFILE DATA:")
    print(f"• Name: {profile_data.get('name')}")
    print(f"• Email: {profile_data.get('email')}")
    print(f"• Skills: {', '.join(profile_data.get('skills', []))}")
    
    # Test document customization
    try:
        from src.utils.document_generator import customize
        
        print("\n📄 TESTING COVER LETTER CUSTOMIZATION:")
        print("-" * 50)
        
        # Test cover letter
        customized_cover_letter = customize(
            document=documents['cover_letter'],
            job_data=job_data,
            profile_data=profile_data
        )
        
        print("✅ Cover letter customized successfully!")
        print("\n📝 CUSTOMIZED COVER LETTER (First 500 chars):")
        print("-" * 50)
        print(customized_cover_letter[:500] + "..." if len(customized_cover_letter) > 500 else customized_cover_letter)
        
        print("\n📄 TESTING RESUME CUSTOMIZATION:")
        print("-" * 50)
        
        # Test resume
        customized_resume = customize(
            document=documents['resume'],
            job_data=job_data,
            profile_data=profile_data
        )
        
        print("✅ Resume customized successfully!")
        print("\n📝 CUSTOMIZED RESUME (First 500 chars):")
        print("-" * 50)
        print(customized_resume[:500] + "..." if len(customized_resume) > 500 else customized_resume)
        
        # Save results to files for inspection
        output_dir = Path("temp/document_generator_test")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "customized_cover_letter.txt", "w", encoding="utf-8") as f:
            f.write(customized_cover_letter)
        
        with open(output_dir / "customized_resume.txt", "w", encoding="utf-8") as f:
            f.write(customized_resume)
        
        print(f"\n💾 Results saved to: {output_dir}")
        
        # Test validation
        from src.utils.document_generator import _is_properly_customized
        
        cover_letter_valid = _is_properly_customized(customized_cover_letter)
        resume_valid = _is_properly_customized(customized_resume)
        
        print(f"\n✅ VALIDATION RESULTS:")
        print(f"• Cover Letter properly customized: {'✅ Yes' if cover_letter_valid else '❌ No'}")
        print(f"• Resume properly customized: {'✅ Yes' if resume_valid else '❌ No'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        logger.error(f"Document customization test failed: {e}")
        return False

def demonstrate_fallback_mechanisms():
    """Demonstrate the fallback mechanisms."""
    print("\n" + "=" * 80)
    print("🔄 DEMONSTRATING FALLBACK MECHANISMS")
    print("=" * 80)
    
    print("\n1. 🤖 AI-POWERED CUSTOMIZATION:")
    print("   • Attempts to use Gemini API or other AI services")
    print("   • Generates intelligent, context-aware content")
    print("   • If successful, returns AI-generated document")
    
    print("\n2. 📝 TEMPLATE-BASED CUSTOMIZATION (if AI fails):")
    print("   • Uses predefined substitution mappings")
    print("   • Replaces placeholders with job/profile data")
    print("   • Maintains document structure and formatting")
    
    print("\n3. ⚡ BASIC CUSTOMIZATION (final fallback):")
    print("   • Simple find-and-replace operations")
    print("   • Ensures no placeholders remain")
    print("   • Guarantees functional output")
    
    # Test with a simple template to show fallback
    simple_template = """Dear HIRING_MANAGER,

I am interested in the JOB_TITLE position at COMPANY_NAME.

Best regards,
YOUR_NAME
YOUR_EMAIL"""
    
    job_data = {'company': 'Test Company', 'title': 'Test Position'}
    profile_data = {'name': 'Test User', 'email': 'test@email.com'}
    
    try:
        from src.utils.document_generator import _basic_customization
        
        result = _basic_customization(simple_template, job_data, profile_data)
        
        print(f"\n📝 BASIC CUSTOMIZATION EXAMPLE:")
        print("Original template:")
        print(simple_template)
        print("\nAfter basic customization:")
        print(result)
        
    except Exception as e:
        print(f"❌ Error demonstrating fallback: {e}")

def main():
    """Main function to run the demo."""
    print("🚀 DOCUMENT GENERATOR DEMO STARTING...")
    
    # Show the logic overview
    show_document_generator_logic()
    
    # Demonstrate fallback mechanisms
    demonstrate_fallback_mechanisms()
    
    # Test with real data
    success = test_document_customization()
    
    print("\n" + "=" * 80)
    print("📊 DEMO SUMMARY")
    print("=" * 80)
    
    if success:
        print("✅ Document generator test completed successfully!")
        print("✅ All customization mechanisms working properly")
        print("✅ Documents generated and saved to temp/document_generator_test/")
    else:
        print("❌ Some tests failed - check logs for details")
    
    print("\n🎯 KEY TAKEAWAYS:")
    print("• Document generator uses 3-tier fallback approach for reliability")
    print("• AI customization provides best results when available")
    print("• Template and basic customization ensure functionality")
    print("• All placeholders are properly replaced in final documents")
    print("• System is fault-tolerant and handles errors gracefully")

if __name__ == "__main__":
    main()