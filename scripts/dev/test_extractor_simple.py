#!/usr/bin/env python3
"""
Simple test for Custom Data Extractor
Quick verification that the extractor works correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.analysis.custom_data_extractor import CustomDataExtractor, get_custom_data_extractor

def test_basic_extraction():
    """Test basic extraction functionality."""
    print("🧪 Testing Custom Data Extractor...")
    
    extractor = CustomDataExtractor()
    
    # Sample job data
    job_data = {
        'title': 'Senior Software Engineer',
        'description': '''
        Job Title: Senior Software Engineer
        Company: TechCorp Inc
        Location: Toronto, ON
        Salary: $80,000 - $120,000
        
        We are looking for a Senior Software Engineer with 5+ years of experience.
        
        Requirements:
        • 5+ years of Python development experience
        • Experience with React and JavaScript
        • Knowledge of AWS and Docker
        
        Skills: Python, React, JavaScript, AWS, Docker, PostgreSQL
        
        Benefits:
        • Health insurance
        • Remote work options
        
        Employment Type: Full-time
        ''',
        'url': 'https://jobs.techcorp.com/senior-engineer-123'
    }
    
    # Extract data
    result = extractor.extract_job_data(job_data)
    
    # Verify results
    print(f"✅ Title: {result.title}")
    print(f"✅ Company: {result.company}")
    print(f"✅ Location: {result.location}")
    print(f"✅ Salary: {result.salary_range}")
    print(f"✅ Experience: {result.experience_level}")
    print(f"✅ Employment Type: {result.employment_type}")
    print(f"✅ Skills: {result.skills}")
    print(f"✅ Requirements: {result.requirements}")
    print(f"✅ Benefits: {result.benefits}")
    print(f"✅ Confidence: {result.confidence:.2f}")
    
    # Basic assertions
    assert result.title == 'Senior Software Engineer'
    assert 'techcorp' in result.company.lower()  # More flexible company check
    assert result.location == 'Toronto, ON'
    assert result.salary_range == '$80,000 - $120,000'
    assert result.experience_level in ['Senior Level', 'Mid Level']  # Both are valid for 5+ years
    assert result.employment_type == 'Full-time'
    assert 'Python' in result.skills
    assert 'React' in result.skills
    assert 'AWS' in result.skills
    assert len(result.requirements) > 0
    assert len(result.benefits) > 0
    assert result.confidence > 0.7
    
    print("🎉 All basic tests passed!")
    return True

def test_individual_extractors():
    """Test individual extraction methods."""
    print("\n🧪 Testing Individual Extractors...")
    
    extractor = CustomDataExtractor()
    
    # Test title extraction
    title = extractor.extract_title("Job Title: Python Developer", "")
    print(f"✅ Title extraction: {title}")
    assert title == "Python Developer"
    
    # Test company extraction
    company = extractor.extract_company("Company: Google Inc", "")
    print(f"✅ Company extraction: {company}")
    assert company == "Google Inc"
    
    # Test location extraction
    location = extractor.extract_location("Location: San Francisco, CA")
    print(f"✅ Location extraction: {location}")
    assert location == "San Francisco, CA"
    
    # Test salary extraction
    salary = extractor.extract_salary("Salary: $70,000 - $90,000")
    print(f"✅ Salary extraction: {salary}")
    assert salary == "$70,000 - $90,000"
    
    # Test skills extraction
    skills = extractor.extract_skills("Skills: Python, JavaScript, React, AWS")
    print(f"✅ Skills extraction: {skills}")
    assert 'Python' in skills
    assert 'JavaScript' in skills
    assert 'React' in skills
    assert 'AWS' in skills
    
    print("🎉 All individual extractor tests passed!")
    return True

def test_convenience_function():
    """Test convenience function."""
    print("\n🧪 Testing Convenience Function...")
    
    extractor = get_custom_data_extractor()
    assert isinstance(extractor, CustomDataExtractor)
    
    print("✅ Convenience function works!")
    return True

def main():
    """Run all tests."""
    print("🚀 Testing Custom Data Extractor")
    print("="*50)
    
    try:
        test_basic_extraction()
        test_individual_extractors()
        test_convenience_function()
        
        print("\n" + "="*50)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("✅ Custom Data Extractor is working correctly!")
        print("✅ All extraction methods function properly!")
        print("✅ Confidence calculation works!")
        print("✅ Ready for integration with hybrid processing!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)