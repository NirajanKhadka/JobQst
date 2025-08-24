#!/usr/bin/env python3
"""
AI Service Logger - Comprehensive logging and error reporting for AI services
Provides structured logging, user-friendly error messages, and diagnostic information
"""

import logging
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import traceback

# Configure structured logging
# Ensure logs directory exists before creating file handlers
Path("logs").mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/ai_service.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)


@dataclass
class AIServiceEvent:
    """Structured AI service event for logging"""
    timestamp: str
    event_type: str  # 'connection_check', 'analysis_attempt', 'fallback', 'error'
    service_name: str
    success: bool
    duration_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AIServiceLogger:
    """Comprehensive logging system for AI service interactions"""
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize AI service logger.
        
        Args:
            log_file: Optional custom log file path
        """
        self.log_file = log_file or "logs/ai_service_detailed.log"
        self.events: List[AIServiceEvent] = []
        self.max_events = 1000  # Keep last 1000 events in memory
        
        # Ensure log directory exists
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Performance metrics
        self.metrics = {
            'total_events': 0,
            'connection_checks': 0,
            'analysis_attempts': 0,
            'successful_analyses': 0,
            'fallback_uses': 0,
            'errors': 0,
            'average_response_time': 0.0
        }
        
        logger.info("AI Service Logger initialized")
    
    def log_connection_check(self, service_name: str, success: bool, 
                           duration_ms: float, error_message: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None):
        """
        Log AI service connection check.
        
        Args:
            service_name: Name of the AI service
            success: Whether connection was successful
            duration_ms: Connection check duration in milliseconds
            error_message: Error message if failed
            metadata: Additional metadata
        """
        event = AIServiceEvent(
            timestamp=datetime.now().isoformat(),
            event_type='connection_check',
            service_name=service_name,
            success=success,
            duration_ms=duration_ms,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        self._record_event(event)
        self.metrics['connection_checks'] += 1
        
        if success:
            logger.info(f"✅ {service_name} connection successful ({duration_ms:.1f}ms)")
        else:
            logger.warning(f"❌ {service_name} connection failed ({duration_ms:.1f}ms): {error_message}")
    
    def log_analysis_attempt(self, service_name: str, success: bool,
                           duration_ms: float, analysis_method: str,
                           compatibility_score: Optional[float] = None,
                           error_message: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None):
        """
        Log job analysis attempt.
        
        Args:
            service_name: Name of the AI service
            success: Whether analysis was successful
            duration_ms: Analysis duration in milliseconds
            analysis_method: Method used for analysis
            compatibility_score: Resulting compatibility score
            error_message: Error message if failed
            metadata: Additional metadata
        """
        event_metadata = metadata or {}
        event_metadata.update({
            'analysis_method': analysis_method,
            'compatibility_score': compatibility_score
        })
        
        event = AIServiceEvent(
            timestamp=datetime.now().isoformat(),
            event_type='analysis_attempt',
            service_name=service_name,
            success=success,
            duration_ms=duration_ms,
            error_message=error_message,
            metadata=event_metadata
        )
        
        self._record_event(event)
        self.metrics['analysis_attempts'] += 1
        
        if success:
            self.metrics['successful_analyses'] += 1
            score_text = f"score={compatibility_score:.3f}" if compatibility_score else "no score"
            logger.info(f"🎯 {service_name} analysis successful ({analysis_method}, {duration_ms:.1f}ms, {score_text})")
        else:
            logger.error(f"💥 {service_name} analysis failed ({analysis_method}, {duration_ms:.1f}ms): {error_message}")
    
    def log_fallback_usage(self, from_method: str, to_method: str, reason: str,
                          metadata: Optional[Dict[str, Any]] = None):
        """
        Log fallback from one analysis method to another.
        
        Args:
            from_method: Original analysis method
            to_method: Fallback analysis method
            reason: Reason for fallback
            metadata: Additional metadata
        """
        event_metadata = metadata or {}
        event_metadata.update({
            'from_method': from_method,
            'to_method': to_method,
            'reason': reason
        })
        
        event = AIServiceEvent(
            timestamp=datetime.now().isoformat(),
            event_type='fallback',
            service_name='system',
            success=True,
            error_message=reason,
            metadata=event_metadata
        )
        
        self._record_event(event)
        self.metrics['fallback_uses'] += 1
        
        logger.warning(f"🔄 Fallback: {from_method} → {to_method} ({reason})")
    
    def log_error(self, service_name: str, error_type: str, error_message: str,
                  exception: Optional[Exception] = None,
                  metadata: Optional[Dict[str, Any]] = None):
        """
        Log AI service error with detailed information.
        
        Args:
            service_name: Name of the AI service
            error_type: Type of error
            error_message: Error message
            exception: Original exception if available
            metadata: Additional metadata
        """
        event_metadata = metadata or {}
        event_metadata.update({
            'error_type': error_type,
            'traceback': traceback.format_exc() if exception else None
        })
        
        event = AIServiceEvent(
            timestamp=datetime.now().isoformat(),
            event_type='error',
            service_name=service_name,
            success=False,
            error_message=error_message,
            metadata=event_metadata
        )
        
        self._record_event(event)
        self.metrics['errors'] += 1
        
        logger.error(f"🚨 {service_name} error ({error_type}): {error_message}")
        
        if exception:
            logger.debug(f"Exception details: {traceback.format_exc()}")
    
    def _record_event(self, event: AIServiceEvent):
        """Record event to memory and file."""
        # Add to memory (with size limit)
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events.pop(0)
        
        # Update metrics
        self.metrics['total_events'] += 1
        
        # Update average response time
        if event.duration_ms:
            total_with_duration = sum(1 for e in self.events if e.duration_ms)
            if total_with_duration > 0:
                avg_duration = sum(e.duration_ms for e in self.events if e.duration_ms) / total_with_duration
                self.metrics['average_response_time'] = avg_duration
        
        # Write to file
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(asdict(event)) + '\n')
        except Exception as e:
            logger.error(f"Failed to write to log file: {e}")
    
    def get_recent_events(self, limit: int = 50, event_type: Optional[str] = None) -> List[AIServiceEvent]:
        """
        Get recent events.
        
        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type (optional)
            
        Returns:
            List of recent events
        """
        events = self.events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events[-limit:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        success_rate = 0
        if self.metrics['analysis_attempts'] > 0:
            success_rate = (self.metrics['successful_analyses'] / self.metrics['analysis_attempts']) * 100
        
        return {
            **self.metrics,
            'success_rate': round(success_rate, 1),
            'fallback_rate': round((self.metrics['fallback_uses'] / max(self.metrics['analysis_attempts'], 1)) * 100, 1),
            'error_rate': round((self.metrics['errors'] / max(self.metrics['total_events'], 1)) * 100, 1)
        }
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get error summary for the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Error summary dictionary
        """
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        recent_errors = [
            e for e in self.events 
            if e.event_type == 'error' and 
            datetime.fromisoformat(e.timestamp).timestamp() > cutoff_time
        ]
        
        # Group errors by type
        error_types = {}
        for error in recent_errors:
            error_type = error.metadata.get('error_type', 'unknown')
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(error)
        
        return {
            'total_errors': len(recent_errors),
            'error_types': {
                error_type: len(errors) 
                for error_type, errors in error_types.items()
            },
            'most_common_error': max(error_types.keys(), key=lambda k: len(error_types[k])) if error_types else None,
            'recent_errors': [
                {
                    'timestamp': e.timestamp,
                    'service': e.service_name,
                    'type': e.metadata.get('error_type', 'unknown'),
                    'message': e.error_message
                }
                for e in recent_errors[-10:]  # Last 10 errors
            ]
        }
    
    def get_user_friendly_status(self) -> Dict[str, Any]:
        """
        Get user-friendly status message for display.
        
        Returns:
            User-friendly status dictionary
        """
        metrics = self.get_metrics()
        recent_events = self.get_recent_events(10)
        
        # Determine overall status
        if metrics['success_rate'] >= 80:
            status = "🟢 AI services are working well"
            status_color = "green"
        elif metrics['success_rate'] >= 50:
            status = "🟡 AI services are experiencing some issues"
            status_color = "yellow"
        else:
            status = "🔴 AI services are having significant problems"
            status_color = "red"
        
        # Get recent issues
        recent_errors = [e for e in recent_events if not e.success]
        
        # Generate recommendations
        recommendations = []
        if metrics['error_rate'] > 20:
            recommendations.append("High error rate detected - check AI service configuration")
        if metrics['fallback_rate'] > 50:
            recommendations.append("Frequently falling back to rule-based analysis - check AI service connectivity")
        if metrics['average_response_time'] > 30000:
            recommendations.append("AI services are responding slowly - consider optimizing configuration")
        
        if not recommendations:
            recommendations.append("System is operating normally")
        
        return {
            'status': status,
            'status_color': status_color,
            'success_rate': metrics['success_rate'],
            'total_analyses': metrics['analysis_attempts'],
            'recent_errors_count': len(recent_errors),
            'average_response_time_ms': round(metrics['average_response_time'], 1),
            'recommendations': recommendations,
            'last_updated': datetime.now().isoformat()
        }
    
    def get_diagnostic_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive diagnostic report.
        
        Returns:
            Detailed diagnostic report
        """
        return {
            'summary': self.get_user_friendly_status(),
            'metrics': self.get_metrics(),
            'error_summary': self.get_error_summary(),
            'recent_events': [
                {
                    'timestamp': e.timestamp,
                    'type': e.event_type,
                    'service': e.service_name,
                    'success': e.success,
                    'duration_ms': e.duration_ms,
                    'message': e.error_message
                }
                for e in self.get_recent_events(20)
            ],
            'log_file': self.log_file,
            'total_events_logged': self.metrics['total_events']
        }
    
    def reset_metrics(self):
        """Reset all metrics and clear events."""
        self.events.clear()
        self.metrics = {
            'total_events': 0,
            'connection_checks': 0,
            'analysis_attempts': 0,
            'successful_analyses': 0,
            'fallback_uses': 0,
            'errors': 0,
            'average_response_time': 0.0
        }
        logger.info("AI service metrics reset")


# Global logger instance
_global_ai_logger = None

def get_ai_service_logger() -> AIServiceLogger:
    """Get or create global AI service logger."""
    global _global_ai_logger
    
    if _global_ai_logger is None:
        _global_ai_logger = AIServiceLogger()
    
    return _global_ai_logger


# Convenience functions for common logging operations
def log_ai_connection_check(service_name: str, success: bool, duration_ms: float, 
                           error_message: Optional[str] = None):
    """Log AI service connection check."""
    logger_instance = get_ai_service_logger()
    logger_instance.log_connection_check(service_name, success, duration_ms, error_message)


def log_ai_analysis(service_name: str, success: bool, duration_ms: float, 
                   analysis_method: str, compatibility_score: Optional[float] = None,
                   error_message: Optional[str] = None):
    """Log AI analysis attempt."""
    logger_instance = get_ai_service_logger()
    logger_instance.log_analysis_attempt(service_name, success, duration_ms, analysis_method, 
                                       compatibility_score, error_message)


def log_ai_fallback(from_method: str, to_method: str, reason: str):
    """Log fallback between analysis methods."""
    logger_instance = get_ai_service_logger()
    logger_instance.log_fallback_usage(from_method, to_method, reason)


def log_ai_error(service_name: str, error_type: str, error_message: str, 
                exception: Optional[Exception] = None):
    """Log AI service error."""
    logger_instance = get_ai_service_logger()
    logger_instance.log_error(service_name, error_type, error_message, exception)


if __name__ == "__main__":
    # Test functionality moved to tests/unit/test_ai_service_logger.py
    pass