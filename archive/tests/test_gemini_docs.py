"""
Test script for the new Gemini-powered document generation.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

def test_gemini_document_generation():
    """Test the Gemini-powered document generation."""
    
    # Test data
    profile_data = {
        "name": "Nirajan Khadka",
        "email": "Nirajan.Tech@gmail.com",
        "phone": "437-344-5361",
        "location": "Mississauga, ON",
        "summary": "Experienced Data Analyst with 5+ years in data visualization, statistical analysis, and business intelligence. Proven track record of transforming complex data into actionable insights that drive business decisions.",
        "experience": "Data Analyst | ABC Company | 2020-Present\n• Analyzed large datasets using Python, SQL, and Tableau to identify trends and patterns\n• Created automated dashboards that improved decision-making efficiency by 40%\n• Collaborated with cross-functional teams to define and track key business metrics\n• Developed predictive models that increased forecast accuracy by 25%",
        "skills": "Python, SQL, Tableau, Power BI, Excel, R, Statistics, Machine Learning, Data Visualization, ETL, Database Management, A/B Testing, Predictive Modeling",
        "education": "Bachelor of Science in Statistics | University Name | 2018",
        "certifications": "Google Data Analytics Certificate, Tableau Desktop Specialist, Microsoft Power BI Data Analyst Associate"
    }
    
    job_data = {
        "company": "TechCorp Solutions",
        "title": "Senior Data Analyst",
        "description": "We are looking for a Senior Data Analyst to join our growing analytics team. The ideal candidate will have experience with Python, SQL, and data visualization tools. You will be responsible for analyzing large datasets, creating reports and dashboards, and providing insights to drive business decisions.",
        "requirements": "Bachelor's degree in Statistics, Computer Science, or related field. 3+ years of experience in data analysis. Proficiency in Python, SQL, and BI tools like Tableau or Power BI."
    }
    
    print("Testing Gemini Client...")
    
    try:
        from src.utils.gemini_client import GeminiClient
        
        gemini = GeminiClient()
        
        print("✅ Gemini client initialized successfully")
        
        # Test resume generation
        print("\n🔄 Generating resume...")
        resume_content = gemini.generate_resume(profile_data, job_data)
        
        if resume_content:
            print("✅ Resume generated successfully!")
            print("Preview (first 200 chars):")
            print(resume_content[:200] + "...")
            
            # Save to file
            resume_path = Path("test_resume_output.txt")
            with open(resume_path, 'w', encoding='utf-8') as f:
                f.write(resume_content)
            print(f"📄 Resume saved to: {resume_path}")
        else:
            print("❌ Resume generation failed")
        
        # Test cover letter generation
        print("\n🔄 Generating cover letter...")
        cover_letter_content = gemini.generate_cover_letter(profile_data, job_data)
        
        if cover_letter_content:
            print("✅ Cover letter generated successfully!")
            print("Preview (first 200 chars):")
            print(cover_letter_content[:200] + "...")
            
            # Save to file
            cover_letter_path = Path("test_cover_letter_output.txt")
            with open(cover_letter_path, 'w', encoding='utf-8') as f:
                f.write(cover_letter_content)
            print(f"📄 Cover letter saved to: {cover_letter_path}")
        else:
            print("❌ Cover letter generation failed")
    
    except Exception as e:
        print(f"❌ Error testing Gemini client: {e}")
    
    print("\nTesting Document Modifier...")
    
    try:
        from src.document_modifier.document_modifier import DocumentModifier
        
        # Test with default profile
        modifier = DocumentModifier("Nirajan")
        
        print("✅ DocumentModifier initialized successfully")
        
        # Test AI resume generation
        print("\n🔄 Testing AI resume generation...")
        resume_path = modifier.generate_ai_resume(job_data, profile_data)
        
        if resume_path and Path(resume_path).exists():
            print(f"✅ AI resume generated: {resume_path}")
        else:
            print("❌ AI resume generation failed")
        
        # Test AI cover letter generation
        print("\n🔄 Testing AI cover letter generation...")
        cover_letter_path = modifier.generate_ai_cover_letter(job_data, profile_data)
        
        if cover_letter_path and Path(cover_letter_path).exists():
            print(f"✅ AI cover letter generated: {cover_letter_path}")
        else:
            print("❌ AI cover letter generation failed")
            
        # Test template discovery
        print("\n🔄 Testing template discovery...")
        templates = modifier.get_available_templates()
        print(f"✅ Found {len(templates)} templates:")
        for template in templates:
            print(f"  - {template}")
    
    except Exception as e:
        print(f"❌ Error testing DocumentModifier: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nTesting Document Generator customize function...")
    
    try:
        from src.utils.document_generator import customize
        
        # Test with a simple template
        template = """Dear {company} Hiring Team,

I am writing to express my interest in the {job_title} position. With my background in data analysis, I believe I would be a valuable addition to your team.

Sincerely,
{name}"""
        
        result = customize(template, job_data, profile_data)
        
        print("✅ Document customization completed")
        print("Customized content preview:")
        print(result[:300] + "..." if len(result) > 300 else result)
        
        # Save result
        result_path = Path("test_customized_output.txt")
        with open(result_path, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"📄 Customized document saved to: {result_path}")
    
    except Exception as e:
        print(f"❌ Error testing document customization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing Gemini-powered Document Generation")
    print("=" * 50)
    test_gemini_document_generation()
    print("\n✅ Testing completed!")
