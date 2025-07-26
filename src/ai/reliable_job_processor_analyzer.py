#!/usr/bin/env python3
"""
ReliableJobProcessorAnalyzer - Fault-tolerant drop-in replacement for EnhancedJobAnalyzer
Integrates with job processor orchestration to provide reliable AI analysis with fallbacks
"""

import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from src.services.ollama_connection_checker import get_ollama_checker
from src.ai.enhanced_rule_based_analyzer import EnhancedRuleBasedAnalyzer

# Try to import existing AI analyzers
try:
    from src.ai.enhanced_job_analyzer import EnhancedJobAnalyzer
except ImportError:
    EnhancedJobAnalyzer = None

try:
    from src.ai.enhanced_job_analyzer import EnhancedJobAnalyzer as LegacyEnhancedJobAnalyzer
    if EnhancedJobAnalyzer is None:
        EnhancedJobAnalyzer = LegacyEnhancedJobAnalyzer
except ImportError:
    pass

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


@dataclass
class AnalysisAttempt:
    """Record of an analysis attempt"""
    method: str
    success: bool
    duration_ms: float
    error_message: Optional[str] = None
    score: Optional[float] = None


class ReliableJobProcessorAnalyzer:
    """
    Fault-tolerant job analyzer that serves as a drop-in replacement for EnhancedJobAnalyzer.
    Provides reliable analysis with proper fallbacks and integration with job processor orchestration.
    """
    
    def __init__(self, profile: Dict[str, Any], 
                 ollama_endpoint: str = "http://localhost:11434",
                 enable_ai_fallback: bool = True):
        """
        Initialize reliable job processor analyzer.
        
        Args:
            profile: User profile dictionary
            ollama_endpoint: Ollama API endpoint
            enable_ai_fallback: Whether to attempt AI analysis before rule-based
        """
        self.profile = profile
        self.ollama_endpoint = ollama_endpoint
        self.enable_ai_fallback = enable_ai_fallback
        
        # Initialize components
        self.connection_checker = get_ollama_checker(ollama_endpoint)
        self.enhanced_rule_based = EnhancedRuleBasedAnalyzer(profile)
        self.ai_analyzer = None  # Lazy initialization
        
        # Analysis statistics
        self.stats = {
            'total_analyses': 0,
            'ai_successful': 0,
            'rule_based_used': 0,
            'connection_failures': 0,
            'ai_failures': 0,
            'average_ai_time': 0.0,
            'average_rule_time': 0.0,
            'last_ai_success': None,
            'consecutive_ai_failures': 0
        }
        
        # Recent analysis attempts for debugging
        self.recent_attempts: List[AnalysisAttempt] = []
        self.max_recent_attempts = 10
        
        logger.info(f"ReliableJobProcessorAnalyzer initialized for profile: {profile.get('name', 'unknown')}")
    
    def analyze_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze job compatibility using the best available method with fault tolerance.
        
        Args:
            job: Job posting dictionary
            
        Returns:
            Analysis result dictionary compatible with existing job processor
        """
        self.stats['total_analyses'] += 1
        analysis_start = time.time()
        
        # Try AI analysis first if enabled and connection is available
        if self.enable_ai_fallback and self._should_try_ai_analysis():
            ai_result = self._try_ai_analysis(job)
            if ai_result:
                self._record_successful_analysis('ai', analysis_start, ai_result.get('compatibility_score'))
                return ai_result
        
        # Fall back to enhanced rule-based analysis
        logger.info("Using enhanced rule-based analysis")
        rule_result = self._perform_rule_based_analysis(job)
        self._record_successful_analysis('rule_based', analysis_start, rule_result.get('compatibility_score'))
        
        return rule_result
    
    def _should_try_ai_analysis(self) -> bool:
        """Determine if we should attempt AI analysis."""
        # Skip if too many consecutive failures
        if self.stats['consecutive_ai_failures'] >= 5:
            logger.debug("Skipping AI analysis due to consecutive failures")
            return False
        
        # Check connection availability
        if not self.connection_checker.is_available():
            self.stats['connection_failures'] += 1
            logger.debug("Skipping AI analysis - Ollama not available")
            return False
        
        return True
    
    def _try_ai_analysis(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Attempt AI analysis with proper error handling."""
        start_time = time.time()
        
        try:
            # Lazy initialize AI analyzer
            if self.ai_analyzer is None:
                self._initialize_ai_analyzer()
            
            if self.ai_analyzer is None:
                logger.warning("AI analyzer not available")
                return None
            
            # Perform AI analysis with timeout protection
            result = self.ai_analyzer.analyze_job(job)
            
            if result and isinstance(result, dict):
                # Validate result has required fields
                if 'compatibility_score' in result:
                    duration_ms = (time.time() - start_time) * 1000
                    self._record_attempt('ai', True, duration_ms, score=result.get('compatibility_score'))
                    
                    # Update statistics
                    self.stats['ai_successful'] += 1
                    self.stats['consecutive_ai_failures'] = 0
                    self.stats['last_ai_success'] = time.time()
                    
                    # Update average AI time
                    total_ai = self.stats['ai_successful']
                    current_avg = self.stats['average_ai_time']
                    self.stats['average_ai_time'] = ((current_avg * (total_ai - 1)) + duration_ms) / total_ai
                    
                    logger.info(f"AI analysis successful: score={result.get('compatibility_score'):.3f}, time={duration_ms:.1f}ms")
                    return result
                else:
                    logger.warning("AI analysis returned invalid result format")
                    return None
            else:
                logger.warning("AI analysis returned None or invalid type")
                return None
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            self._record_attempt('ai', False, duration_ms, error_message=error_msg)
            
            # Update failure statistics
            self.stats['ai_failures'] += 1
            self.stats['consecutive_ai_failures'] += 1
            
            logger.warning(f"AI analysis failed: {error_msg}")
            return None
    
    def _initialize_ai_analyzer(self):
        """Initialize AI analyzer with error handling."""
        try:
            if EnhancedJobAnalyzer is not None:
                self.ai_analyzer = EnhancedJobAnalyzer(
                    profile=self.profile,
                    use_mistral=True,
                    fallback_to_llama=True,
                    fallback_to_rule_based=False  # We handle rule-based fallback ourselves
                )
                logger.info("AI analyzer initialized successfully")
            else:
                logger.warning("EnhancedJobAnalyzer not available - AI analysis disabled")
        except Exception as e:
            logger.error(f"Failed to initialize AI analyzer: {e}")
            self.ai_analyzer = None
    
    def _perform_rule_based_analysis(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Perform enhanced rule-based analysis."""
        start_time = time.time()
        
        try:
            result = self.enhanced_rule_based.analyze_job(job)
            
            duration_ms = (time.time() - start_time) * 1000
            self._record_attempt('rule_based', True, duration_ms, score=result.get('compatibility_score'))
            
            # Update statistics
            self.stats['rule_based_used'] += 1
            
            # Update average rule-based time
            total_rule = self.stats['rule_based_used']
            current_avg = self.stats['average_rule_time']
            self.stats['average_rule_time'] = ((current_avg * (total_rule - 1)) + duration_ms) / total_rule
            
            logger.debug(f"Rule-based analysis: score={result.get('compatibility_score'):.3f}, time={duration_ms:.1f}ms")
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            self._record_attempt('rule_based', False, duration_ms, error_message=error_msg)
            
            logger.error(f"Rule-based analysis failed: {error_msg}")
            
            # Return minimal fallback result
            return self._create_fallback_result(job)
    
    def _create_fallback_result(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Create minimal fallback result when all analysis methods fail."""
        return {
            'compatibility_score': 0.7,
            'confidence': 0.1,
            'skill_matches': [],
            'skill_gaps': [],
            'experience_match': 'unknown',
            'location_match': 'unknown',
            'cultural_fit': 0.5,
            'growth_potential': 0.5,
            'recommendation': 'consider',
            'reasoning': 'Analysis failed - using fallback values',
            'analysis_method': 'fallback',
            'analysis_timestamp': time.time(),
            'error': 'All analysis methods failed'
        }
    
    def _record_attempt(self, method: str, success: bool, duration_ms: float, 
                       error_message: Optional[str] = None, score: Optional[float] = None):
        """Record analysis attempt for debugging."""
        attempt = AnalysisAttempt(
            method=method,
            success=success,
            duration_ms=duration_ms,
            error_message=error_message,
            score=score
        )
        
        self.recent_attempts.append(attempt)
        
        # Keep only recent attempts
        if len(self.recent_attempts) > self.max_recent_attempts:
            self.recent_attempts.pop(0)
    
    def _record_successful_analysis(self, method: str, start_time: float, score: Optional[float]):
        """Record successful analysis completion."""
        duration_ms = (time.time() - start_time) * 1000
        score_str = f"{score:.3f}" if score is not None else "N/A"
        logger.info(f"Job analysis completed: method={method}, score={score_str}, time={duration_ms:.1f}ms")
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get comprehensive analysis statistics."""
        connection_stats = self.connection_checker.get_statistics()
        
        return {
            'analyzer_stats': self.stats.copy(),
            'connection_stats': connection_stats,
            'recent_attempts': [
                {
                    'method': attempt.method,
                    'success': attempt.success,
                    'duration_ms': round(attempt.duration_ms, 1),
                    'error': attempt.error_message,
                    'score': round(attempt.score, 3) if attempt.score else None
                }
                for attempt in self.recent_attempts[-5:]  # Last 5 attempts
            ],
            'health_summary': {
                'ai_success_rate': (self.stats['ai_successful'] / max(self.stats['total_analyses'], 1)) * 100,
                'connection_success_rate': connection_stats.get('success_rate', 0),
                'primary_method': 'ai' if self.stats['ai_successful'] > self.stats['rule_based_used'] else 'rule_based',
                'last_ai_success_ago': (time.time() - self.stats['last_ai_success']) if self.stats['last_ai_success'] else None
            }
        }
    
    def get_diagnostic_info(self) -> Dict[str, Any]:
        """Get diagnostic information for troubleshooting."""
        return {
            'analyzer_config': {
                'profile_name': self.profile.get('name', 'unknown'),
                'ollama_endpoint': self.ollama_endpoint,
                'ai_fallback_enabled': self.enable_ai_fallback,
                'ai_analyzer_available': self.ai_analyzer is not None
            },
            'statistics': self.get_analysis_statistics(),
            'connection_diagnostics': self.connection_checker.get_diagnostic_info(),
            'recommendations': self._get_health_recommendations()
        }
    
    def _get_health_recommendations(self) -> List[str]:
        """Get health recommendations based on current statistics."""
        recommendations = []
        
        # Connection issues
        if self.stats['connection_failures'] > 5:
            recommendations.append("High connection failure rate - check if Ollama is running")
        
        # AI analysis issues
        if self.stats['consecutive_ai_failures'] >= 3:
            recommendations.append("Multiple AI analysis failures - check Ollama models and configuration")
        
        # Performance issues
        if self.stats['average_ai_time'] > 30000:  # 30 seconds
            recommendations.append("AI analysis is slow - consider optimizing Ollama configuration")
        
        # Success rate issues
        ai_success_rate = (self.stats['ai_successful'] / max(self.stats['total_analyses'], 1)) * 100
        if ai_success_rate < 50 and self.stats['total_analyses'] > 10:
            recommendations.append("Low AI success rate - consider using rule-based analysis as primary method")
        
        if not recommendations:
            recommendations.append("System is operating normally")
        
        return recommendations
    
    def reset_statistics(self):
        """Reset analysis statistics."""
        self.stats = {
            'total_analyses': 0,
            'ai_successful': 0,
            'rule_based_used': 0,
            'connection_failures': 0,
            'ai_failures': 0,
            'average_ai_time': 0.0,
            'average_rule_time': 0.0,
            'last_ai_success': None,
            'consecutive_ai_failures': 0
        }
        self.recent_attempts.clear()
        self.connection_checker.reset_statistics()
        logger.info("Analysis statistics reset")


# Backward compatibility function
def create_reliable_analyzer(profile: Dict[str, Any], **kwargs) -> ReliableJobProcessorAnalyzer:
    """Create a reliable job processor analyzer with backward compatibility."""
    return ReliableJobProcessorAnalyzer(profile, **kwargs)


if __name__ == "__main__":
    # Test the reliable analyzer
    test_profile = {
        'name': 'test_user',
        'skills': ['Python', 'SQL', 'Machine Learning'],
        'experience_level': 'Senior'
    }
    
    test_job = {
        'title': 'Senior Python Developer',
        'description': 'Looking for a senior Python developer with SQL and ML experience',
        'location': 'Remote',
        'company': 'Test Company'
    }
    
    analyzer = ReliableJobProcessorAnalyzer(test_profile)
    
    print("Testing ReliableJobProcessorAnalyzer...")
    result = analyzer.analyze_job(test_job)
    
    print("\nAnalysis Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    print("\nStatistics:")
    stats = analyzer.get_analysis_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nDiagnostic Info:")
    diagnostics = analyzer.get_diagnostic_info()
    for key, value in diagnostics.items():
        print(f"  {key}: {value}")