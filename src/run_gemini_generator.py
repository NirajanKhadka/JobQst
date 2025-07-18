"""
User-friendly interface for Gemini Resume Generator
Run this script to interactively generate resumes and cover letters
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

try:
    from gemini_resume_generator import GeminiResumeGenerator
from src.utils.profile_helpers import load_profile
except ImportError:
    print("❌ Error: Required packages not installed")
    print("Run install_gemini.bat first to install dependencies")
    sys.exit(1)

def load_profile(profile_path: str = "profiles/nirajan_profile.json"):
    """Load candidate profile from JSON file"""
    if os.path.exists(profile_path):
        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_profile(profile: dict, profile_path: str = "profiles/nirajan_profile.json"):
    """Save candidate profile to JSON file"""
    os.makedirs(os.path.dirname(profile_path), exist_ok=True)
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

def get_candidate_profile():
    """Get candidate profile from user input or file"""
    
    print("\n" + "="*60)
    print("CANDIDATE PROFILE SETUP")
    print("="*60)
    
    # Try to load existing profile
    profile = load_profile()
    
    if profile:
        print(f"Found existing profile for: {profile.get('name', 'Unknown')}")
        use_existing = input("Use existing profile? (y/n): ").strip().lower()
        if use_existing == 'y':
            return profile
    
    print("\nEnter your profile information:")
    
    profile = {}
    profile['name'] = input("Full Name: ").strip()
    profile['email'] = input("Email: ").strip()
    profile['phone'] = input("Phone: ").strip()
    profile['location'] = input("Location (City, State): ").strip()
    
    print("\nProfessional Summary (2-3 sentences):")
    profile['summary'] = input("> ").strip()
    
    print("\nWork Experience (press Enter twice when done):")
    experience_lines = []
    while True:
        line = input("> ")
        if line.strip() == "" and len(experience_lines) > 0:
            break
        if line.strip():
            experience_lines.append(line)
    profile['experience'] = '\n'.join(experience_lines)
    
    print("\nSkills (comma-separated):")
    profile['skills'] = input("> ").strip()
    
    print("\nEducation:")
    profile['education'] = input("> ").strip()
    
    print("\nCertifications (optional):")
    profile['certifications'] = input("> ").strip()
    
    # Save profile
    save_profile(profile)
    print("✅ Profile saved!")
    
    return profile

def get_job_info():
    """Get job description and company info"""
    
    print("\n" + "="*60)
    print("JOB INFORMATION")
    print("="*60)
    
    company_name = input("Company Name: ").strip()
    
    print("\nJob Description (paste the full job posting, press Enter twice when done):")
    job_lines = []
    while True:
        line = input("> ")
        if line.strip() == "" and len(job_lines) > 0:
            break
        if line.strip():
            job_lines.append(line)
    
    job_description = '\n'.join(job_lines)
    
    return company_name, job_description

def main():
    """Main interactive interface"""
    
    print("🚀 GEMINI RESUME & COVER LETTER GENERATOR")
    print("="*60)
    print("Generate tailored resumes and cover letters using AI")
    print()
    
    try:
        # Initialize generator
        generator = GeminiResumeGenerator()
        print("✅ Gemini API connected successfully")
        
        # Get candidate profile
        profile = get_candidate_profile()
        
        # Get job information
        company_name, job_description = get_job_info()
        
        # Generate documents
        print("\n" + "="*60)
        print("GENERATING DOCUMENTS")
        print("="*60)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_company = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_company = safe_company.replace(' ', '_').lower()
        
        output_filename = f"{profile['name'].replace(' ', '_').lower()}_{safe_company}_{timestamp}"
        
        print(f"🔄 Generating resume and cover letter for {company_name}...")
        print("This may take 30-60 seconds...")
        
        results = generator.generate_and_save(
            candidate_profile=profile,
            job_description=job_description,
            company_name=company_name,
            output_filename=output_filename
        )
        
        print("\n🎉 DOCUMENTS GENERATED SUCCESSFULLY!")
        print("="*60)
        print(f"📄 Resume PDF: {results['resume']}")
        print(f"📄 Cover Letter PDF: {results['cover_letter']}")
        print(f"📁 Text versions saved in: output/")
        
        # Ask if user wants to generate more
        while True:
            another = input("\nGenerate documents for another job? (y/n): ").strip().lower()
            if another == 'y':
                company_name, job_description = get_job_info()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_company = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_company = safe_company.replace(' ', '_').lower()
                output_filename = f"{profile['name'].replace(' ', '_').lower()}_{safe_company}_{timestamp}"
                
                print(f"🔄 Generating documents for {company_name}...")
                results = generator.generate_and_save(
                    candidate_profile=profile,
                    job_description=job_description,
                    company_name=company_name,
                    output_filename=output_filename
                )
                
                print(f"✅ Documents generated: {results['resume']}")
                print(f"✅ Cover letter: {results['cover_letter']}")
                
            elif another == 'n':
                break
            else:
                print("Please enter 'y' or 'n'")
        
        print("\n👋 Thank you for using Gemini Resume Generator!")
        print("Your documents are ready in the 'output' folder.")
        
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check your .env file contains the correct API key")
        print("2. Ensure you have an internet connection")
        print("3. Verify your Gemini API key is valid")
        
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
