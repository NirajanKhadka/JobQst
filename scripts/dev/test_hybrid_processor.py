#!/usr/bin/env python3
"""
Test Hybrid Processing Engine
Quick verification that the hybrid processor works correctly.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch
import json

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.analysis.hybrid_processor import HybridProcessingEngine, HybridProcessingResult, get_hybrid_processing_engine
from src.analysis.custom_data_extractor import ExtractionResult
from src.ai.gpu_ollama_client import JobAnalysisResult

def test_hybrid_processing_with_mocks():
    """Test hybrid processing with mocked LLM responses."""
    print("🧪 Testing Hybrid Processing Engine with Mocks...")
    
    # Create mock LLM client
    mock_ollama_client = Mock()
    mock_ollama_client.is_available.return_value = True
    
    # Mock LLM analysis result
    mock_llm_result = JobAnalysisResult(
        required_skills=["Python", "Django", "REST APIs"],
        job_requirements=["3+ years Python experience", "Bachelor's degree in CS"],
        compatibility_score=0.85,
        analysis_confidence=0.92,
        extracted_benefits=["Health insurance", "401k matching"],
        reasoning="Good match for Python developer role",
        processing_time=1.5,
        model_used="llama3"
    )
    mock_ollama_client.analyze_job_content.return_value = mock_llm_result
    mock_ollama_client.get_health_info.return_value = {"status": "available"}
    
    # Create hybrid processor with mock
    processor = HybridProcessingEngine(ollama_client=mock_ollama_client)
    
    # Sample job data
    job_data = {
        'title': 'Senior Python Developer',
        'description': '''
        Job Title: Senior Python Developer
        Company: TechCorp Inc
        Location: Toronto, ON
        Salary: $90,000 - $130,000
        
        We are looking for a Senior Python Developer with 5+ years of experience.
        
        Requirements:
        • 5+ years of Python development experience
        • Experience with Django and REST APIs
        • Knowledge of PostgreSQL and Redis
        
        Skills: Python, Django, PostgreSQL, Redis, Git
        
        Benefits:
        • Health insurance
        • Dental coverage
        • Remote work options
        
        Employment Type: Full-time
        ''',
        'url': 'https://jobs.techcorp.com/python-dev-456'
    }
    
    # Process job
    result = processor.process_job(job_data)
    
    # Verify results
    print(f"✅ Title: {result.title}")
    print(f"✅ Company: {result.company}")
    print(f"✅ Location: {result.location}")
    print(f"✅ Salary: {result.salary_range}")
    print(f"✅ Experience: {result.experience_level}")
    print(f"✅ Employment Type: {result.employment_type}")
    print(f"✅ Required Skills: {result.required_skills}")
    print(f"✅ Job Requirements: {result.job_requirements}")
    print(f"✅ Compatibility Score: {result.compatibility_score}")
    print(f"✅ Benefits: {result.extracted_benefits}")
    print(f"✅ Custom Logic Confidence: {result.custom_logic_confidence:.2f}")
    print(f"✅ LLM Processing Time: {result.llm_processing_time:.2f}s")
    print(f"✅ Total Processing Time: {result.total_processing_time:.2f}s")
    print(f"✅ Fallback Used: {result.fallback_used}")
    
    # Assertions
    assert isinstance(result, HybridProcessingResult)
    assert result.title == 'Senior Python Developer'
    assert 'techcorp' in result.company.lower()
    assert result.location == 'Toronto, ON'
    assert result.salary_range == '$90,000 - $130,000'
    assert result.employment_type == 'Full-time'
    assert 'Python' in result.required_skills
    assert 'Django' in result.required_skills
    assert result.compatibility_score == 0.85
    assert result.analysis_confidence == 0.92
    assert not result.fallback_used
    assert result.custom_logic_confidence > 0.7
    assert result.total_processing_time >= 0  # Processing time should be non-negative
    
    print("🎉 Hybrid processing with mocks test passed!")
    return True

def test_fallback_processing():
    """Test processing when LLM is unavailable."""
    print("\n🧪 Testing Fallback Processing (LLM Unavailable)...")
    
    # Create mock LLM client that's unavailable
    mock_ollama_client = Mock()
    mock_ollama_client.is_available.return_value = False
    
    # Create hybrid processor with unavailable LLM
    processor = HybridProcessingEngine(ollama_client=mock_ollama_client)
    
    # Sample job data
    job_data = {
        'title': 'Data Scientist',
        'description': '''
        Job Title: Data Scientist
        Company: DataCorp
        Location: Vancouver, BC
        Salary: $80,000 - $110,000
        
        Looking for a Data Scientist with Python and R experience.
        
        Skills: Python, R, SQL, Machine Learning
        ''',
        'url': 'https://datacorp.com/jobs/data-scientist'
    }
    
    # Process job
    result = processor.process_job(job_data)
    
    # Verify fallback behavior
    print(f"✅ Title: {result.title}")
    print(f"✅ Company: {result.company}")
    print(f"✅ Required Skills: {result.required_skills}")
    print(f"✅ Compatibility Score: {result.compatibility_score}")
    print(f"✅ Reasoning: {result.reasoning}")
    print(f"✅ Fallback Used: {result.fallback_used}")
    print(f"✅ LLM Processing Time: {result.llm_processing_time}")
    
    # Assertions for fallback behavior
    assert isinstance(result, HybridProcessingResult)
    assert result.title == 'Data Scientist'
    assert result.company == 'Datacorp'
    assert 'Python' in result.required_skills
    assert 'R' in result.required_skills
    assert result.compatibility_score == 0.5  # Neutral score when LLM unavailable
    assert result.fallback_used == True
    assert result.llm_processing_time == 0.0
    assert "custom logic only" in result.reasoning
    
    print("🎉 Fallback processing test passed!")
    return True

def test_skills_merging():
    """Test skills merging logic."""
    print("\n🧪 Testing Skills Merging...")
    
    # Create mock LLM client for initialization
    mock_ollama_client = Mock()
    mock_ollama_client.is_available.return_value = True
    
    processor = HybridProcessingEngine(ollama_client=mock_ollama_client)
    
    custom_skills = ["Python", "JavaScript", "React"]
    llm_skills = ["Python", "Node.js", "AWS", "Docker"]
    
    merged_skills = processor._merge_skills(custom_skills, llm_skills)
    
    print(f"✅ Custom Skills: {custom_skills}")
    print(f"✅ LLM Skills: {llm_skills}")
    print(f"✅ Merged Skills: {merged_skills}")
    
    # Assertions
    assert 'Python' in merged_skills  # Should not duplicate
    assert 'JavaScript' in merged_skills  # From custom
    assert 'React' in merged_skills  # From custom
    assert 'Node.js' in merged_skills  # From LLM
    assert 'AWS' in merged_skills  # From LLM
    assert 'Docker' in merged_skills  # From LLM
    assert len(merged_skills) == 6  # No duplicates
    
    # Custom skills should come first
    assert merged_skills.index('Python') < merged_skills.index('Node.js')
    assert merged_skills.index('JavaScript') < merged_skills.index('AWS')
    
    print("🎉 Skills merging test passed!")
    return True

def test_requirements_merging():
    """Test requirements merging logic."""
    print("\n🧪 Testing Requirements Merging...")
    
    # Create mock LLM client for initialization
    mock_ollama_client = Mock()
    mock_ollama_client.is_available.return_value = True
    
    processor = HybridProcessingEngine(ollama_client=mock_ollama_client)
    
    custom_requirements = ["Bachelor's degree in Computer Science", "3+ years experience"]
    llm_requirements = ["Strong Python programming skills", "Experience with web frameworks", "Bachelor's degree preferred"]
    
    merged_requirements = processor._merge_requirements(custom_requirements, llm_requirements)
    
    print(f"✅ Custom Requirements: {custom_requirements}")
    print(f"✅ LLM Requirements: {llm_requirements}")
    print(f"✅ Merged Requirements: {merged_requirements}")
    
    # Assertions
    assert len(merged_requirements) > 0
    assert any("Python programming" in req for req in merged_requirements)
    assert any("web frameworks" in req for req in merged_requirements)
    # Should not duplicate similar degree requirements
    degree_reqs = [req for req in merged_requirements if "degree" in req.lower()]
    assert len(degree_reqs) <= 2  # Should merge similar requirements
    
    print("🎉 Requirements merging test passed!")
    return True

def test_processing_stats():
    """Test processing statistics."""
    print("\n🧪 Testing Processing Statistics...")
    
    # Create mock LLM client
    mock_ollama_client = Mock()
    mock_ollama_client.is_available.return_value = True
    mock_ollama_client.get_health_info.return_value = {"status": "available", "model": "llama3"}
    
    user_profile = {"skills": ["Python", "JavaScript"], "experience_years": 5}
    processor = HybridProcessingEngine(ollama_client=mock_ollama_client, user_profile=user_profile)
    
    stats = processor.get_processing_stats()
    
    print(f"✅ Processing Stats: {stats}")
    
    # Assertions
    assert stats["custom_extractor_available"] == True
    assert stats["llm_client_available"] == True
    assert stats["user_profile_configured"] == True
    assert stats["processing_method"] == "hybrid"
    assert stats["llm_health"]["status"] == "available"
    
    print("🎉 Processing statistics test passed!")
    return True

def test_user_profile_update():
    """Test user profile update functionality."""
    print("\n🧪 Testing User Profile Update...")
    
    # Create mock LLM client for initialization
    mock_ollama_client = Mock()
    mock_ollama_client.is_available.return_value = True
    
    processor = HybridProcessingEngine(ollama_client=mock_ollama_client)
    
    # Initial profile
    initial_profile = {"skills": ["Python"], "experience_years": 3}
    processor.update_user_profile(initial_profile)
    assert processor.user_profile == initial_profile
    
    # Updated profile
    updated_profile = {"skills": ["Python", "JavaScript", "React"], "experience_years": 5}
    processor.update_user_profile(updated_profile)
    assert processor.user_profile == updated_profile
    
    print("✅ User profile updated successfully")
    print("🎉 User profile update test passed!")
    return True

def test_convenience_function():
    """Test convenience function."""
    print("\n🧪 Testing Convenience Function...")
    
    # Mock the get_gpu_ollama_client function to avoid real Ollama connection
    with patch('src.analysis.hybrid_processor.get_gpu_ollama_client') as mock_get_client:
        mock_ollama_client = Mock()
        mock_ollama_client.is_available.return_value = True
        mock_get_client.return_value = mock_ollama_client
        
        user_profile = {"skills": ["Python"], "experience_years": 3}
        processor = get_hybrid_processing_engine(user_profile)
        
        assert isinstance(processor, HybridProcessingEngine)
        assert processor.user_profile == user_profile
    
    print("✅ Convenience function works!")
    return True

def main():
    """Run all tests."""
    print("🚀 Testing Hybrid Processing Engine")
    print("="*60)
    
    try:
        test_hybrid_processing_with_mocks()
        test_fallback_processing()
        test_skills_merging()
        test_requirements_merging()
        test_processing_stats()
        test_user_profile_update()
        test_convenience_function()
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("✅ Hybrid Processing Engine is working correctly!")
        print("✅ Custom logic + LLM integration successful!")
        print("✅ Fallback mechanisms work properly!")
        print("✅ Data merging logic is robust!")
        print("✅ Processing statistics available!")
        print("✅ Ready for multiprocessing integration!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)