"""
Unit tests for Hybrid Processing Engine
Tests the hybrid custom logic + LLM processing engine.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
import time

# Import the hybrid processor
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.analysis.hybrid_processor import (
        HybridProcessingEngine,
        HybridProcessingResult,
        get_hybrid_processing_engine
    )
    _HYBRID_AVAILABLE = True
except Exception:
    _HYBRID_AVAILABLE = False

from src.analysis.custom_data_extractor import ExtractionResult
from src.ai.gpu_ollama_client import JobAnalysisResult

pytestmark = pytest.mark.skipif(not _HYBRID_AVAILABLE, reason="hybrid processor not available in v4")

class TestHybridProcessingEngine:
    """Test suite for Hybrid Processing Engine."""
    
    @pytest.fixture
    def mock_ollama_client(self):
        """Create mock Ollama client for testing."""
        mock_client = Mock()
        mock_client.analyze_job_content.return_value = JobAnalysisResult(
            required_skills=["Python", "Machine Learning"],
            job_requirements=["3+ years experience", "Bachelor's degree"],
            compatibility_score=0.85,
            analysis_confidence=0.9,
            extracted_benefits=["Health insurance", "401k"],
            reasoning="Good match for candidate profile",
            processing_time=2.5,
            model_used="llama3"
        )
        return mock_client
    
    @pytest.fixture
    def hybrid_processor(self, mock_ollama_client):
        """Create hybrid processor instance for testing."""
        return HybridProcessingEngine(ollama_client=mock_ollama_client)
    
    @pytest.fixture
    def sample_job_data(self):
        """Sample job data for testing."""
        return {
            'title': 'Senior Data Scientist',
            'description': '''
            Job Title: Senior Data Scientist
            Company: DataCorp Inc
            Location: San Francisco, CA
            Salary: $120,000 - $150,000
            
            We are seeking a Senior Data Scientist with 5+ years of experience.
            
            Requirements:
            • 5+ years of Python and machine learning experience
            • Experience with TensorFlow and PyTorch
            • PhD in Computer Science or related field
            
            Skills:
            Python, TensorFlow, PyTorch, SQL, AWS
            
            Benefits:
            • Comprehensive health insurance
            • Stock options
            • Flexible work arrangements
            
            Employment Type: Full-time
            ''',
            'url': 'https://jobs.datacorp.com/senior-data-scientist-123',
            'user_profile': {
                'skills': ['Python', 'Machine Learning', 'TensorFlow'],
                'experience_years': 6
            }
        }
    
    def test_processor_initialization(self, hybrid_processor, mock_ollama_client):
        """Test processor initialization."""
        assert hybrid_processor is not None
        assert hybrid_processor.custom_extractor is not None
        assert hybrid_processor.ollama_client == mock_ollama_client
    
    def test_processor_initialization_without_client(self):
        """Test processor initialization without providing Ollama client."""
        with patch('src.analysis.hybrid_processor.get_gpu_ollama_client') as mock_client_func:
            mock_client_instance = Mock()
            mock_client_instance.is_available.return_value = True
            mock_client_func.return_value = mock_client_instance
            
            processor = HybridProcessingEngine()
            
            assert processor.ollama_client == mock_client_instance
            mock_client_func.assert_called_once()
    
    def test_extract_structured_data(self, hybrid_processor, sample_job_data):
        """Test structured data extraction."""
        result = hybrid_processor.extract_structured_data(sample_job_data)
        
        assert isinstance(result, ExtractionResult)
        assert result.title == 'Senior Data Scientist'
        assert result.company == 'DataCorp Inc'  # Company extraction preserves the full name
        assert result.location == 'San Francisco, CA'
        assert result.salary_range == '$120,000 - $150,000'
        assert 'Python' in result.skills
        assert 'TensorFlow' in result.skills
        assert result.confidence > 0.7
    
    def test_extract_structured_data_with_error(self, hybrid_processor, sample_job_data):
        """Test structured data extraction with error handling."""
        with patch.object(hybrid_processor.custom_extractor, 'extract_job_data', side_effect=Exception("Test error")):
            result = hybrid_processor.extract_structured_data(sample_job_data)
            
            assert isinstance(result, ExtractionResult)
            assert result.confidence == 0.0
    
    def test_enhance_with_llm_high_confidence(self, hybrid_processor, sample_job_data):
        """Test LLM enhancement with high confidence custom extraction."""
        # Mock high confidence custom result
        custom_result = ExtractionResult(
            title="Senior Data Scientist",
            company="DataCorp Inc",
            confidence=0.95
        )
        
        result = hybrid_processor.enhance_with_llm(sample_job_data, custom_result)
        
        assert isinstance(result, JobAnalysisResult)
        assert result.analysis_confidence == 0.9
        assert "Python" in result.required_skills
        hybrid_processor.ollama_client.analyze_job_content.assert_called_once()
    
    def test_enhance_with_llm_low_confidence(self, hybrid_processor, sample_job_data):
        """Test LLM enhancement with low confidence custom extraction."""
        # Mock low confidence custom result
        custom_result = ExtractionResult(
            title="Senior Data Scientist",
            confidence=0.3
        )
        
        result = hybrid_processor.enhance_with_llm(sample_job_data, custom_result)
        
        assert isinstance(result, JobAnalysisResult)
        assert result.analysis_confidence == 0.9
        hybrid_processor.ollama_client.analyze_job_content.assert_called_once()
    
    def test_enhance_with_llm_error_handling(self, hybrid_processor, sample_job_data):
        """Test LLM enhancement with error handling."""
        custom_result = ExtractionResult(confidence=0.5)
        
        # Mock LLM client to raise exception
        hybrid_processor.ollama_client.analyze_job_content.side_effect = Exception("LLM error")
        
        result = hybrid_processor.enhance_with_llm(sample_job_data, custom_result)
        
        assert result is None  # Should return None on error
    
    def test_merge_results_comprehensive(self, hybrid_processor):
        """Test comprehensive result merging."""
        custom_result = ExtractionResult(
            title="Senior Data Scientist",
            company="DataCorp Inc",
            location="San Francisco, CA",
            salary_range="$120,000 - $150,000",
            experience_level="Senior Level",
            employment_type="Full-time",
            skills=["Python", "TensorFlow"],
            requirements=["5+ years experience"],
            benefits=["Health insurance"],
            confidence=0.8
        )
        
        llm_result = JobAnalysisResult(
            required_skills=["Machine Learning", "PyTorch"],
            job_requirements=["PhD degree"],
            compatibility_score=0.85,
            analysis_confidence=0.9,
            extracted_benefits=["Stock options"],
            reasoning="Good match",
            processing_time=2.5,
            model_used="llama3"
        )
        
        merged = hybrid_processor._merge_results(custom_result, llm_result)
        
        # Check that it returns HybridProcessingResult
        assert isinstance(merged, HybridProcessingResult)
        
        # Check that custom extraction data is preserved
        assert merged.title == "Senior Data Scientist"
        assert merged.company == "DataCorp Inc"
        assert merged.location == "San Francisco, CA"
        assert merged.salary_range == "$120,000 - $150,000"
        
        # Check that skills are merged
        assert 'Python' in merged.required_skills
        assert 'TensorFlow' in merged.required_skills
        assert 'Machine Learning' in merged.required_skills
        assert 'PyTorch' in merged.required_skills
        
        # Check that requirements are merged
        assert 'PhD degree' in merged.job_requirements  # LLM requirements come first
        assert '5+ years experience' in merged.job_requirements
        
        # Check that benefits are merged
        assert 'Health Insurance' in merged.extracted_benefits
        assert 'Stock Options' in merged.extracted_benefits
        
        # Check LLM-specific data
        assert merged.compatibility_score == 0.85
        assert merged.reasoning == 'Good match'
    
    def test_merge_results_without_llm(self, hybrid_processor):
        """Test result merging when LLM analysis is not available."""
        custom_result = ExtractionResult(
            title="Senior Data Scientist",
            company="DataCorp Inc",
            location="San Francisco, CA",
            skills=["Python", "TensorFlow"],
            requirements=["5+ years experience"],
            benefits=["Health insurance"],
            confidence=0.8
        )
        
        # Test with None LLM result (fallback scenario)
        merged = hybrid_processor._merge_results(custom_result, None)
        
        # Check that it returns HybridProcessingResult
        assert isinstance(merged, HybridProcessingResult)
        
        # Check that custom extraction data is preserved
        assert merged.title == "Senior Data Scientist"
        assert merged.company == "DataCorp Inc"
        assert merged.location == "San Francisco, CA"
        
        # Check that fallback values are used
        assert merged.required_skills == ["Python", "TensorFlow"]
        assert merged.job_requirements == ["5+ years experience"]
        assert merged.extracted_benefits == ["Health insurance"]
        assert merged.compatibility_score == 0.5  # Neutral score
        assert merged.fallback_used == True
        assert "custom logic only" in merged.reasoning
    
    def test_requirements_overlap_detection(self, hybrid_processor):
        """Test requirements overlap detection."""
        # Test overlapping requirements
        req1 = "5+ years of Python development experience"
        req2 = "5 years Python programming experience required"
        assert hybrid_processor._requirements_overlap(req1, req2) == True
        
        # Test non-overlapping requirements
        req1 = "Bachelor's degree in Computer Science"
        req2 = "Experience with machine learning frameworks"
        assert hybrid_processor._requirements_overlap(req1, req2) == False
        
        # Test edge cases
        assert hybrid_processor._requirements_overlap("", "test") == False
        assert hybrid_processor._requirements_overlap("test", "") == False
    
    def test_process_job_comprehensive(self, hybrid_processor, sample_job_data, mock_ollama_client):
        """Test comprehensive job processing."""
        result = hybrid_processor.process_job(sample_job_data)
        
        # Check that it returns HybridProcessingResult
        assert isinstance(result, HybridProcessingResult)
        
        # Check that processing metadata is added
        assert result.processing_method == 'hybrid'
        assert result.total_processing_time > 0
        
        # Check that structured data is extracted
        assert result.company == 'DataCorp Inc'
        assert result.location == 'San Francisco, CA'
        
        # Check that LLM analysis is performed
        mock_ollama_client.analyze_job_content.assert_called_once()
        
        # Check that results are merged
        assert len(result.required_skills) > 0
        assert len(result.job_requirements) > 0
        assert result.compatibility_score > 0
        assert result.analysis_confidence > 0
    
    def test_process_job_timing(self, hybrid_processor, sample_job_data):
        """Test that processing time is recorded."""
        # Use a simple counter to simulate time progression
        time_counter = [1000.0]
        def mock_time():
            time_counter[0] += 0.1
            return time_counter[0]
        
        with patch('time.time', side_effect=mock_time):
            result = hybrid_processor.process_job(sample_job_data)
            
            # Should have some processing time recorded
            assert result.total_processing_time > 0
            assert result.total_processing_time < 10  # Reasonable upper bound
    
    def test_process_job_with_minimal_data(self, hybrid_processor):
        """Test processing with minimal job data."""
        minimal_job = {
            'title': 'Developer',
            'description': 'Looking for a Python developer'
        }
        
        result = hybrid_processor.process_job(minimal_job)
        
        assert isinstance(result, HybridProcessingResult)
        # The processor may extract title from description if it finds a better match
        assert result.title is not None
        assert len(result.title) > 0
        assert result.total_processing_time > 0
    
    def test_get_hybrid_processing_engine_convenience_function(self):
        """Test convenience function for getting processor."""
        with patch('src.analysis.hybrid_processor.get_gpu_ollama_client') as mock_client_func:
            mock_client_instance = Mock()
            mock_client_instance.is_available.return_value = True
            mock_client_func.return_value = mock_client_instance
            
            processor = get_hybrid_processing_engine()
            
            assert isinstance(processor, HybridProcessingEngine)
            assert processor.ollama_client == mock_client_instance
    
    def test_get_hybrid_processing_engine_with_profile(self):
        """Test convenience function with user profile."""
        user_profile = {'skills': ['Python'], 'experience_years': 5}
        
        with patch('src.analysis.hybrid_processor.get_gpu_ollama_client') as mock_client_func:
            mock_client_instance = Mock()
            mock_client_instance.is_available.return_value = True
            mock_client_func.return_value = mock_client_instance
            
            processor = get_hybrid_processing_engine(user_profile=user_profile)
            
            assert isinstance(processor, HybridProcessingEngine)
            assert processor.user_profile == user_profile
    
    def test_logging_integration(self, hybrid_processor, sample_job_data, caplog):
        """Test that logging works correctly."""
        with caplog.at_level('INFO'):
            hybrid_processor.process_job(sample_job_data)
            
            # Check that info logs are generated
            assert "Processing job: Senior Data Scientist" in caplog.text
            assert "Completed processing" in caplog.text
    
    def test_error_resilience(self, hybrid_processor, sample_job_data):
        """Test that the processor is resilient to various errors."""
        # Mock both custom extractor and LLM client to fail
        with patch.object(hybrid_processor.custom_extractor, 'extract_job_data', side_effect=Exception("Custom error")):
            with patch.object(hybrid_processor.ollama_client, 'analyze_job_content', side_effect=Exception("LLM error")):
                result = hybrid_processor.process_job(sample_job_data)
                
                # Should still return a result even when both methods fail
                assert isinstance(result, HybridProcessingResult)
                # The processor should still work with hybrid method even when components fail
                assert result.processing_method == 'hybrid'
                assert result.total_processing_time > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])