"""
Unit tests for GPU Ollama Client
Tests the GPU-accelerated Ollama client with mocked responses for reliability.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the client
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.ai.gpu_ollama_client import (
    GPUOllamaClient, 
    OllamaStatus, 
    JobAnalysisResult,
    get_gpu_ollama_client
)

class TestGPUOllamaClient:
    """Test suite for GPU Ollama Client."""
    
    @pytest.fixture
    def mock_ollama_available(self):
        """Mock Ollama library availability."""
        with patch('src.ai.gpu_ollama_client.OLLAMA_AVAILABLE', True):
            with patch('src.ai.gpu_ollama_client.Client') as mock_client:
                with patch('src.ai.gpu_ollama_client.ResponseError', Exception):
                    yield mock_client
    
    @pytest.fixture
    def mock_requests(self):
        """Mock requests for service status checks."""
        with patch('src.ai.gpu_ollama_client.requests') as mock_requests:
            yield mock_requests
    
    @pytest.fixture
    def client_with_mocks(self, mock_ollama_available, mock_requests):
        """Create client with all necessary mocks."""
        # Mock successful service status
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response
        
        # Mock client methods
        mock_client_instance = Mock()
        mock_client_instance.list.return_value = {'models': [{'name': 'llama3'}]}
        mock_client_instance.pull.return_value = None
        mock_ollama_available.return_value = mock_client_instance
        
        # Create client without validation
        with patch.object(GPUOllamaClient, '_validate_setup'):
            client = GPUOllamaClient()
            client.client = mock_client_instance
        
        return client, mock_client_instance
    
    def test_client_initialization_success(self, mock_ollama_available, mock_requests):
        """Test successful client initialization."""
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response
        
        mock_client_instance = Mock()
        mock_client_instance.list.return_value = {'models': [{'name': 'llama3'}]}
        mock_ollama_available.return_value = mock_client_instance
        
        client = GPUOllamaClient()
        
        assert client.host == "http://localhost:11434"
        assert client.model == "llama3"
        assert client.timeout == 30
        assert client.max_retries == 3
    
    def test_client_initialization_ollama_unavailable(self):
        """Test client initialization when Ollama library is unavailable."""
        with patch('src.ai.gpu_ollama_client.OLLAMA_AVAILABLE', False):
            with pytest.raises(ImportError, match="Ollama library not installed"):
                GPUOllamaClient()
    
    def test_check_service_status_available(self, mock_requests):
        """Test service status check when Ollama is available."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response
        
        with patch.object(GPUOllamaClient, '_validate_setup'):
            client = GPUOllamaClient()
        
        status = client.check_service_status()
        assert status == OllamaStatus.AVAILABLE
        mock_requests.get.assert_called_with("http://localhost:11434/api/version", timeout=5)
    
    def test_check_service_status_unavailable(self, mock_requests):
        """Test service status check when Ollama is unavailable."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests.get.return_value = mock_response
        
        with patch.object(GPUOllamaClient, '_validate_setup'):
            client = GPUOllamaClient()
        
        status = client.check_service_status()
        assert status == OllamaStatus.UNAVAILABLE
    
    def test_check_service_status_error(self, mock_requests):
        """Test service status check when request fails."""
        mock_requests.get.side_effect = Exception("Connection error")
        
        with patch.object(GPUOllamaClient, '_validate_setup'):
            client = GPUOllamaClient()
        
        status = client.check_service_status()
        assert status == OllamaStatus.ERROR
    
    def test_ensure_model_available_exists(self, client_with_mocks):
        """Test model availability check when model exists."""
        client, mock_client_instance = client_with_mocks
        
        mock_client_instance.list.return_value = {'models': [{'name': 'llama3'}]}
        
        result = client._ensure_model_available()
        assert result is True
        mock_client_instance.list.assert_called_once()
    
    def test_ensure_model_available_pull_needed(self, client_with_mocks):
        """Test model availability check when model needs to be pulled."""
        client, mock_client_instance = client_with_mocks
        
        # First call returns no models, second call returns the model
        mock_client_instance.list.side_effect = [
            {'models': []},
            {'models': [{'name': 'llama3'}]}
        ]
        mock_client_instance.pull.return_value = None
        
        result = client._ensure_model_available()
        assert result is True
        mock_client_instance.pull.assert_called_once_with('llama3')
    
    def test_ensure_model_available_pull_fails(self, client_with_mocks):
        """Test model availability check when pull fails."""
        client, mock_client_instance = client_with_mocks
        
        mock_client_instance.list.return_value = {'models': []}
        mock_client_instance.pull.side_effect = Exception("Pull failed")
        
        result = client._ensure_model_available()
        assert result is False
    
    def test_analyze_job_content_success(self, client_with_mocks):
        """Test successful job content analysis."""
        client, mock_client_instance = client_with_mocks
        
        # Mock successful chat response
        mock_response = {
            'message': {
                'content': json.dumps({
                    "required_skills": ["Python", "React", "AWS"],
                    "job_requirements": ["3+ years experience", "Bachelor's degree"],
                    "compatibility_score": 0.85,
                    "analysis_confidence": 0.92,
                    "extracted_benefits": ["Health insurance", "Remote work"],
                    "reasoning": "Good match for skills and experience"
                })
            }
        }
        mock_client_instance.chat.return_value = mock_response
        
        with patch('time.time', side_effect=[0.0, 1.5]):  # Mock time for processing_time
            result = client.analyze_job_content(
                "Software Engineer position requiring Python and React",
                "Software Engineer"
            )
        
        assert isinstance(result, JobAnalysisResult)
        assert result.required_skills == ["Python", "React", "AWS"]
        assert result.compatibility_score == 0.85
        assert result.analysis_confidence == 0.92
        assert result.model_used == "llama3"
        assert result.processing_time == 1.5
    
    def test_analyze_job_content_with_user_profile(self, client_with_mocks):
        """Test job content analysis with user profile."""
        client, mock_client_instance = client_with_mocks
        
        mock_response = {
            'message': {
                'content': json.dumps({
                    "required_skills": ["Python"],
                    "job_requirements": ["2+ years"],
                    "compatibility_score": 0.90,
                    "analysis_confidence": 0.95,
                    "extracted_benefits": ["Remote work"],
                    "reasoning": "Excellent match with user profile"
                })
            }
        }
        mock_client_instance.chat.return_value = mock_response
        
        user_profile = {
            "skills": ["Python", "Django"],
            "experience_years": 3,
            "location": "Toronto"
        }
        
        result = client.analyze_job_content(
            "Python developer position",
            "Python Developer",
            user_profile
        )
        
        assert result.compatibility_score == 0.90
        assert "user profile" in mock_client_instance.chat.call_args[1]['messages'][0]['content'].lower()
    
    def test_analyze_job_content_parse_error(self, client_with_mocks):
        """Test job content analysis with JSON parse error."""
        client, mock_client_instance = client_with_mocks
        
        # Mock response with invalid JSON
        mock_response = {
            'message': {
                'content': "Invalid JSON response"
            }
        }
        mock_client_instance.chat.return_value = mock_response
        
        result = client.analyze_job_content("Test job", "Test Title")
        
        assert isinstance(result, JobAnalysisResult)
        assert result.required_skills == []
        assert result.compatibility_score == 0.5
        assert result.analysis_confidence == 0.3
        assert "Failed to parse" in result.reasoning
    
    def test_analyze_job_content_chat_failure(self, client_with_mocks):
        """Test job content analysis when chat fails."""
        client, mock_client_instance = client_with_mocks
        
        mock_client_instance.chat.side_effect = Exception("Chat failed")
        
        result = client.analyze_job_content("Test job", "Test Title")
        
        assert isinstance(result, JobAnalysisResult)
        assert result.required_skills == []
        assert result.compatibility_score == 0.5
        assert result.analysis_confidence == 0.0
        assert "LLM analysis failed" in result.reasoning
    
    def test_extract_skills_success(self, client_with_mocks):
        """Test successful skill extraction."""
        client, mock_client_instance = client_with_mocks
        
        mock_response = {
            'message': {
                'content': '["Python", "JavaScript", "Docker"]'
            }
        }
        mock_client_instance.chat.return_value = mock_response
        
        skills = client.extract_skills("Job requiring Python, JavaScript, and Docker")
        
        assert skills == ["Python", "JavaScript", "Docker"]
    
    def test_extract_skills_invalid_json(self, client_with_mocks):
        """Test skill extraction with invalid JSON response."""
        client, mock_client_instance = client_with_mocks
        
        mock_response = {
            'message': {
                'content': 'Invalid JSON'
            }
        }
        mock_client_instance.chat.return_value = mock_response
        
        skills = client.extract_skills("Test job description")
        
        assert skills == []
    
    def test_calculate_compatibility_success(self, client_with_mocks):
        """Test successful compatibility calculation."""
        client, mock_client_instance = client_with_mocks
        
        mock_response = {
            'message': {
                'content': '0.85'
            }
        }
        mock_client_instance.chat.return_value = mock_response
        
        job_data = {
            'title': 'Software Engineer',
            'company': 'TechCorp',
            'description': 'Python developer position'
        }
        user_profile = {'skills': ['Python']}
        
        score = client.calculate_compatibility(job_data, user_profile)
        
        assert score == 0.85
    
    def test_calculate_compatibility_invalid_response(self, client_with_mocks):
        """Test compatibility calculation with invalid response."""
        client, mock_client_instance = client_with_mocks
        
        mock_response = {
            'message': {
                'content': 'not a number'
            }
        }
        mock_client_instance.chat.return_value = mock_response
        
        score = client.calculate_compatibility({}, {})
        
        assert score == 0.5  # Default fallback score
    
    def test_calculate_compatibility_out_of_range(self, client_with_mocks):
        """Test compatibility calculation with out-of-range values."""
        client, mock_client_instance = client_with_mocks
        
        # Test values outside 0-1 range
        test_cases = [
            ('1.5', 1.0),  # Above 1.0 should be clamped to 1.0
            ('-0.5', 0.0),  # Below 0.0 should be clamped to 0.0
            ('0.75', 0.75)  # Valid value should remain unchanged
        ]
        
        for response_value, expected_score in test_cases:
            mock_response = {
                'message': {
                    'content': response_value
                }
            }
            mock_client_instance.chat.return_value = mock_response
            
            score = client.calculate_compatibility({}, {})
            assert score == expected_score
    
    def test_chat_with_retry_success(self, client_with_mocks):
        """Test successful chat with retry logic."""
        client, mock_client_instance = client_with_mocks
        
        mock_response = {
            'message': {
                'content': 'Test response'
            }
        }
        mock_client_instance.chat.return_value = mock_response
        
        result = client._chat_with_retry("Test prompt")
        
        assert result == "Test response"
        mock_client_instance.chat.assert_called_once()
    
    def test_chat_with_retry_eventual_success(self, client_with_mocks):
        """Test chat with retry that succeeds after failures."""
        client, mock_client_instance = client_with_mocks
        
        # First call fails, second succeeds
        mock_client_instance.chat.side_effect = [
            Exception("First attempt fails"),
            {
                'message': {
                    'content': 'Success on retry'
                }
            }
        ]
        
        with patch('time.sleep'):  # Speed up test
            result = client._chat_with_retry("Test prompt")
        
        assert result == "Success on retry"
        assert mock_client_instance.chat.call_count == 2
    
    def test_chat_with_retry_all_attempts_fail(self, client_with_mocks):
        """Test chat with retry when all attempts fail."""
        client, mock_client_instance = client_with_mocks
        
        mock_client_instance.chat.side_effect = Exception("All attempts fail")
        
        with patch('time.sleep'):  # Speed up test
            with pytest.raises(RuntimeError, match="All retry attempts failed"):
                client._chat_with_retry("Test prompt")
        
        assert mock_client_instance.chat.call_count == 3  # max_retries
    
    def test_is_available(self, client_with_mocks):
        """Test availability check."""
        client, _ = client_with_mocks
        
        with patch.object(client, 'check_service_status') as mock_status:
            mock_status.return_value = OllamaStatus.AVAILABLE
            assert client.is_available() is True
            
            mock_status.return_value = OllamaStatus.UNAVAILABLE
            assert client.is_available() is False
    
    def test_get_health_info(self, client_with_mocks, mock_requests):
        """Test health information retrieval."""
        client, mock_client_instance = client_with_mocks
        
        # Mock service status
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [{'name': 'llama3'}]
        }
        mock_requests.get.return_value = mock_response
        
        # Mock model list
        mock_client_instance.list.return_value = {
            'models': [{'name': 'llama3'}, {'name': 'codellama'}]
        }
        
        health_info = client.get_health_info()
        
        assert health_info['status'] == 'available'
        assert health_info['host'] == 'http://localhost:11434'
        assert health_info['model'] == 'llama3'
        assert 'last_check' in health_info
        assert health_info['available_models'] == ['llama3', 'codellama']
    
    def test_get_gpu_ollama_client_convenience_function(self, mock_ollama_available, mock_requests):
        """Test convenience function for getting client."""
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response
        
        mock_client_instance = Mock()
        mock_client_instance.list.return_value = {'models': [{'name': 'codellama'}]}
        mock_ollama_available.return_value = mock_client_instance
        
        client = get_gpu_ollama_client(model="codellama")
        
        assert isinstance(client, GPUOllamaClient)
        assert client.model == "codellama"


class TestJobAnalysisResult:
    """Test suite for JobAnalysisResult dataclass."""
    
    def test_job_analysis_result_creation(self):
        """Test JobAnalysisResult creation and attributes."""
        result = JobAnalysisResult(
            required_skills=["Python", "React"],
            job_requirements=["3+ years experience"],
            compatibility_score=0.85,
            analysis_confidence=0.92,
            extracted_benefits=["Health insurance"],
            reasoning="Good match",
            processing_time=1.5,
            model_used="llama3"
        )
        
        assert result.required_skills == ["Python", "React"]
        assert result.job_requirements == ["3+ years experience"]
        assert result.compatibility_score == 0.85
        assert result.analysis_confidence == 0.92
        assert result.extracted_benefits == ["Health insurance"]
        assert result.reasoning == "Good match"
        assert result.processing_time == 1.5
        assert result.model_used == "llama3"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])