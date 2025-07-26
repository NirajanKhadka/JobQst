#!/usr/bin/env python3
"""
Unit tests for AI Service Reliability components
Tests OllamaConnectionChecker, EnhancedRuleBasedAnalyzer, and ReliableJobProcessorAnalyzer
"""

import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
import requests

# Import components to test
from src.services.ollama_connection_checker import OllamaConnectionChecker, ConnectionStatus
from src.ai.enhanced_rule_based_analyzer import (
    EnhancedRuleBasedAnalyzer, SkillMatcher, ExperienceMatcher
)
from src.ai.reliable_job_processor_analyzer import ReliableJobProcessorAnalyzer
from src.ai.ai_service_error_handler import AIServiceErrorHandler, RetryConfig, ErrorType
from src.utils.ai_service_logger import AIServiceLogger


class TestOllamaConnectionChecker:
    """Test cases for OllamaConnectionChecker"""
    
    def test_init(self):
        """Test initialization"""
        checker = OllamaConnectionChecker()
        assert checker.endpoint == "http://localhost:11434"
        assert checker.cache_duration == 30
        assert not checker._status.is_available
    
    def test_init_custom_params(self):
        """Test initialization with custom parameters"""
        checker = OllamaConnectionChecker("http://custom:8080", cache_duration=60)
        assert checker.endpoint == "http://custom:8080"
        assert checker.cache_duration == 60
    
    @patch('requests.get')
    def test_successful_connection(self, mock_get):
        """Test successful connection check"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [
                {'name': 'mistral:7b'},
                {'name': 'llama3:latest'}
            ]
        }
        mock_get.return_value = mock_response
        
        checker = OllamaConnectionChecker()
        result = checker.is_available(force_check=True)
        
        assert result is True
        assert checker._status.is_available is True
        assert len(checker._status.models_available) == 2
        assert 'mistral:7b' in checker._status.models_available
        assert checker.stats['successful_checks'] == 1
        assert checker.stats['consecutive_failures'] == 0
    
    @patch('requests.get')
    def test_connection_timeout(self, mock_get):
        """Test connection timeout handling"""
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")
        
        checker = OllamaConnectionChecker()
        result = checker.is_available(force_check=True)
        
        assert result is False
        assert checker._status.is_available is False
        assert "timeout" in checker._status.error_message.lower()
        assert checker.stats['failed_checks'] == 1
        assert checker.stats['consecutive_failures'] == 1
    
    @patch('requests.get')
    def test_connection_refused(self, mock_get):
        """Test connection refused handling"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        checker = OllamaConnectionChecker()
        result = checker.is_available(force_check=True)
        
        assert result is False
        assert "connection refused" in checker._status.error_message.lower()
    
    @patch('requests.get')
    def test_caching_behavior(self, mock_get):
        """Test connection result caching"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'models': []}
        mock_get.return_value = mock_response
        
        checker = OllamaConnectionChecker(cache_duration=1)
        
        # First call should make request
        result1 = checker.is_available()
        assert mock_get.call_count == 1
        
        # Second call should use cache
        result2 = checker.is_available()
        assert mock_get.call_count == 1  # No additional call
        assert result1 == result2
        
        # Wait for cache to expire
        time.sleep(1.1)
        
        # Third call should make new request
        result3 = checker.is_available()
        assert mock_get.call_count == 2
    
    def test_statistics(self):
        """Test statistics tracking"""
        checker = OllamaConnectionChecker()
        
        # Initial statistics
        stats = checker.get_statistics()
        assert stats['total_checks'] == 0
        assert stats['success_rate'] == 0
        
        # Reset statistics
        checker.reset_statistics()
        assert checker.stats['total_checks'] == 0


class TestSkillMatcher:
    """Test cases for SkillMatcher"""
    
    def test_init(self):
        """Test initialization"""
        skills = ['Python', 'SQL', 'Machine Learning']
        matcher = SkillMatcher(skills)
        assert 'python' in matcher.profile_skills
        assert 'sql' in matcher.profile_skills
        assert 'machine learning' in matcher.profile_skills
    
    def test_skill_extraction(self):
        """Test skill extraction from job text"""
        skills = ['Python', 'SQL', 'React']
        matcher = SkillMatcher(skills)
        
        job_text = "We need a Python developer with SQL experience and React knowledge"
        extracted = matcher.extract_job_skills(job_text)
        
        assert 'python' in extracted
        assert 'sql' in extracted
        assert 'react' in extracted
    
    def test_skill_synonyms(self):
        """Test skill synonym matching"""
        skills = ['JavaScript', 'Kubernetes', 'Machine Learning']
        matcher = SkillMatcher(skills)
        
        job_text = "Looking for JS developer with K8s and ML experience"
        extracted = matcher.extract_job_skills(job_text)
        
        assert 'javascript' in extracted
        assert 'kubernetes' in extracted
        assert 'machine learning' in extracted
    
    def test_calculate_match_high_score(self):
        """Test skill match calculation with high score"""
        skills = ['Python', 'SQL', 'Machine Learning', 'AWS']
        matcher = SkillMatcher(skills)
        
        job_text = "Senior Python developer with SQL, Machine Learning, and AWS experience"
        match = matcher.calculate_match(job_text)
        
        assert match.match_score > 0.8
        assert len(match.matched_skills) >= 3
        assert match.confidence > 0.5
    
    def test_calculate_match_low_score(self):
        """Test skill match calculation with low score"""
        skills = ['Python', 'SQL']
        matcher = SkillMatcher(skills)
        
        job_text = "Java developer with Spring Boot and MongoDB experience"
        match = matcher.calculate_match(job_text)
        
        assert match.match_score < 0.5
        assert len(match.matched_skills) == 0
        assert 'java' in match.missing_skills or 'spring' in match.missing_skills


class TestExperienceMatcher:
    """Test cases for ExperienceMatcher"""
    
    def test_init(self):
        """Test initialization"""
        matcher = ExperienceMatcher("Senior Developer")
        assert matcher.profile_level == 'senior'
    
    def test_experience_level_detection(self):
        """Test experience level detection from text"""
        matcher = ExperienceMatcher("Mid-level")
        
        # Test various job descriptions
        assert matcher._extract_job_experience_level("5+ years experience") == 'mid'
        assert matcher._extract_job_experience_level("entry level position") == 'entry'
        assert matcher._extract_job_experience_level("senior developer role") == 'senior'
        assert matcher._extract_job_experience_level("2-4 years experience") == 'junior'
    
    def test_compatibility_calculation(self):
        """Test experience compatibility calculation"""
        matcher = ExperienceMatcher("Senior")
        
        # Perfect match
        compatibility, score = matcher._calculate_compatibility('senior', 'senior')
        assert compatibility == 'perfect'
        assert score == 1.0
        
        # Close match
        compatibility, score = matcher._calculate_compatibility('senior', 'mid')
        assert compatibility == 'close'
        assert score == 0.8
        
        # Mismatch
        compatibility, score = matcher._calculate_compatibility('senior', 'entry')
        assert compatibility == 'mismatch'
        assert score == 0.3


class TestEnhancedRuleBasedAnalyzer:
    """Test cases for EnhancedRuleBasedAnalyzer"""
    
    def test_init(self):
        """Test initialization"""
        profile = {
            'skills': ['Python', 'SQL'],
            'experience_level': 'Senior',
            'remote_preference': True
        }
        analyzer = EnhancedRuleBasedAnalyzer(profile)
        assert analyzer.profile == profile
        assert analyzer.skill_matcher is not None
        assert analyzer.experience_matcher is not None
    
    def test_analyze_job_high_score(self):
        """Test job analysis with high compatibility score"""
        profile = {
            'skills': ['Python', 'SQL', 'Machine Learning', 'AWS'],
            'experience_level': 'Senior',
            'remote_preference': True,
            'preferred_locations': ['Toronto']
        }
        
        job = {
            'title': 'Senior Python Developer',
            'description': 'We need a senior Python developer with SQL, Machine Learning, and AWS experience. Remote work available.',
            'location': 'Remote',
            'company': 'Tech Corp'
        }
        
        analyzer = EnhancedRuleBasedAnalyzer(profile)
        result = analyzer.analyze_job(job)
        
        assert result['compatibility_score'] >= 0.6
        assert result['analysis_method'] == 'enhanced_rule_based'
        assert result['recommendation'] in ['recommend', 'highly_recommend']
        assert len(result['skill_matches']) > 0
        assert 'python' in [skill.lower() for skill in result['skill_matches']]
    
    def test_analyze_job_low_score(self):
        """Test job analysis with low compatibility score"""
        profile = {
            'skills': ['Python', 'Django'],
            'experience_level': 'Junior',
            'remote_preference': False
        }
        
        job = {
            'title': 'Senior Java Architect',
            'description': 'Looking for a senior Java architect with Spring Boot and microservices experience',
            'location': 'New York (On-site)',
            'company': 'Enterprise Corp'
        }
        
        analyzer = EnhancedRuleBasedAnalyzer(profile)
        result = analyzer.analyze_job(job)
        
        assert result['compatibility_score'] < 0.7
        assert result['experience_match'] in ['mismatch', 'acceptable']
        assert len(result['skill_gaps']) > 0


class TestReliableJobProcessorAnalyzer:
    """Test cases for ReliableJobProcessorAnalyzer"""
    
    def test_init(self):
        """Test initialization"""
        profile = {'skills': ['Python'], 'experience_level': 'Mid'}
        analyzer = ReliableJobProcessorAnalyzer(profile)
        
        assert analyzer.profile == profile
        assert analyzer.connection_checker is not None
        assert analyzer.enhanced_rule_based is not None
        assert analyzer.stats['total_analyses'] == 0
    
    @patch('src.ai.reliable_job_processor_analyzer.get_ollama_checker')
    def test_analyze_job_ai_unavailable(self, mock_get_checker):
        """Test job analysis when AI is unavailable"""
        # Mock connection checker to return False
        mock_checker = Mock()
        mock_checker.is_available.return_value = False
        mock_get_checker.return_value = mock_checker
        
        profile = {'skills': ['Python'], 'experience_level': 'Mid'}
        analyzer = ReliableJobProcessorAnalyzer(profile)
        
        job = {
            'title': 'Python Developer',
            'description': 'Python development role',
            'location': 'Remote'
        }
        
        result = analyzer.analyze_job(job)
        
        assert result['analysis_method'] == 'enhanced_rule_based'
        assert analyzer.stats['total_analyses'] == 1
        assert analyzer.stats['rule_based_used'] == 1
    
    def test_statistics_tracking(self):
        """Test statistics tracking"""
        profile = {'skills': ['Python'], 'experience_level': 'Mid'}
        analyzer = ReliableJobProcessorAnalyzer(profile)
        
        # Initial statistics
        stats = analyzer.get_analysis_statistics()
        assert stats['analyzer_stats']['total_analyses'] == 0
        
        # Reset statistics
        analyzer.reset_statistics()
        assert analyzer.stats['total_analyses'] == 0


class TestAIServiceErrorHandler:
    """Test cases for AIServiceErrorHandler"""
    
    def test_init(self):
        """Test initialization"""
        handler = AIServiceErrorHandler()
        assert handler.retry_config.max_attempts == 3
        assert handler.circuit_breaker is not None
    
    def test_error_classification(self):
        """Test error classification"""
        handler = AIServiceErrorHandler()
        
        # Test timeout error
        timeout_error = requests.exceptions.Timeout("Request timeout")
        error_info = handler.classify_error(timeout_error)
        assert error_info.error_type == ErrorType.TIMEOUT
        assert error_info.is_retryable is True
        
        # Test connection error
        conn_error = requests.exceptions.ConnectionError("Connection failed")
        error_info = handler.classify_error(conn_error)
        assert error_info.error_type == ErrorType.CONNECTION
        assert error_info.is_retryable is True
    
    def test_retry_delay_calculation(self):
        """Test retry delay calculation"""
        handler = AIServiceErrorHandler()
        
        # Test exponential backoff
        delay1 = handler.calculate_delay(0)  # First retry
        delay2 = handler.calculate_delay(1)  # Second retry
        delay3 = handler.calculate_delay(2)  # Third retry
        
        # Account for jitter (±25% of base delay)
        assert delay1 >= 0.75  # 1.0 - 25% jitter
        assert delay1 <= 1.25  # 1.0 + 25% jitter
        
        # Test that delays generally increase (allowing for jitter variation)
        assert delay2 >= 1.5  # 2.0 - 25% jitter (base * 2^1)
        assert delay3 >= 3.0  # 4.0 - 25% jitter (base * 2^2)
    
    def test_successful_execution(self):
        """Test successful function execution"""
        handler = AIServiceErrorHandler()
        
        def successful_function():
            return "success"
        
        result = handler.execute_with_retry_sync(successful_function)
        assert result == "success"
        
        stats = handler.get_statistics()
        assert stats['successful_calls'] == 1
        assert stats['failed_calls'] == 0
    
    def test_retry_on_failure(self):
        """Test retry behavior on failure"""
        handler = AIServiceErrorHandler(RetryConfig(max_attempts=3))
        
        call_count = 0
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.exceptions.ConnectionError("Connection failed")
            return "success"
        
        result = handler.execute_with_retry_sync(flaky_function)
        assert result == "success"
        assert call_count == 3
        
        stats = handler.get_statistics()
        assert stats['retried_calls'] == 2  # 2 retries before success


class TestAIServiceLogger:
    """Test cases for AIServiceLogger"""
    
    def test_init(self):
        """Test initialization"""
        logger = AIServiceLogger()
        assert logger.events == []
        assert logger.metrics['total_events'] == 0
    
    def test_log_connection_check(self):
        """Test connection check logging"""
        logger = AIServiceLogger()
        
        logger.log_connection_check("test_service", True, 100.0)
        
        assert len(logger.events) == 1
        assert logger.events[0].event_type == 'connection_check'
        assert logger.events[0].success is True
        assert logger.metrics['connection_checks'] == 1
    
    def test_log_analysis_attempt(self):
        """Test analysis attempt logging"""
        logger = AIServiceLogger()
        
        logger.log_analysis_attempt("test_service", True, 500.0, "mistral_7b", 0.75)
        
        assert len(logger.events) == 1
        assert logger.events[0].event_type == 'analysis_attempt'
        assert logger.events[0].metadata['compatibility_score'] == 0.75
        assert logger.metrics['analysis_attempts'] == 1
        assert logger.metrics['successful_analyses'] == 1
    
    def test_log_fallback_usage(self):
        """Test fallback usage logging"""
        logger = AIServiceLogger()
        
        logger.log_fallback_usage("mistral_7b", "rule_based", "Connection failed")
        
        assert len(logger.events) == 1
        assert logger.events[0].event_type == 'fallback'
        assert logger.metrics['fallback_uses'] == 1
    
    def test_metrics_calculation(self):
        """Test metrics calculation"""
        logger = AIServiceLogger()
        
        # Log some events
        logger.log_analysis_attempt("service1", True, 100.0, "ai", 0.8)
        logger.log_analysis_attempt("service2", False, 200.0, "ai", error_message="Failed")
        logger.log_analysis_attempt("service3", True, 150.0, "rule_based", 0.6)
        
        metrics = logger.get_metrics()
        assert metrics['analysis_attempts'] == 3
        assert metrics['successful_analyses'] == 2
        assert metrics['success_rate'] == 66.7  # 2/3 * 100
    
    def test_user_friendly_status(self):
        """Test user-friendly status generation"""
        logger = AIServiceLogger()
        
        # Log successful events
        for i in range(8):
            logger.log_analysis_attempt(f"service{i}", True, 100.0, "ai", 0.8)
        
        # Log some failures
        for i in range(2):
            logger.log_analysis_attempt(f"service{i}", False, 100.0, "ai", error_message="Failed")
        
        status = logger.get_user_friendly_status()
        assert "🟢" in status['status']  # Should be green (80% success rate)
        assert status['success_rate'] == 80.0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])