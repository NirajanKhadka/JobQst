#!/usr/bin/env python3
"""
OllamaConnectionChecker - Fast service availability checking for Ollama services
Provides cached connection checking to avoid repeated failed attempts
"""

import time
import logging
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ConnectionStatus:
    """Connection status information"""
    is_available: bool
    last_check: float
    response_time_ms: Optional[float]
    error_message: Optional[str]
    models_available: list = None


class OllamaConnectionChecker:
    """Fast connection checking for Ollama services with caching and health monitoring"""
    
    def __init__(self, endpoint: str = "http://localhost:11434", cache_duration: int = 30):
        """
        Initialize connection checker.
        
        Args:
            endpoint: Ollama API endpoint
            cache_duration: Cache duration in seconds
        """
        self.endpoint = endpoint
        self.cache_duration = cache_duration
        self._status = ConnectionStatus(
            is_available=False,
            last_check=0,
            response_time_ms=None,
            error_message=None,
            models_available=[]
        )
        
        # Connection statistics
        self.stats = {
            'total_checks': 0,
            'successful_checks': 0,
            'failed_checks': 0,
            'average_response_time': 0.0,
            'last_successful_check': None,
            'consecutive_failures': 0
        }
    
    def is_available(self, force_check: bool = False) -> bool:
        """
        Check if Ollama is available with caching.
        
        Args:
            force_check: Force a new check ignoring cache
            
        Returns:
            True if Ollama is available, False otherwise
        """
        now = time.time()
        
        # Use cached result if still valid
        if (not force_check and 
            self._status.last_check and 
            now - self._status.last_check < self.cache_duration):
            return self._status.is_available
        
        # Perform new check
        return self._perform_health_check()
    
    def _perform_health_check(self) -> bool:
        """Perform actual health check against Ollama API."""
        start_time = time.time()
        self.stats['total_checks'] += 1
        
        try:
            # Check /api/tags endpoint with short timeout
            response = requests.get(
                f"{self.endpoint}/api/tags",
                timeout=3,
                headers={'Accept': 'application/json'}
            )
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if response.status_code == 200:
                # Parse available models
                try:
                    data = response.json()
                    models = [model.get('name', '') for model in data.get('models', [])]
                except:
                    models = []
                
                # Update successful status
                self._status = ConnectionStatus(
                    is_available=True,
                    last_check=time.time(),
                    response_time_ms=response_time,
                    error_message=None,
                    models_available=models
                )
                
                # Update statistics
                self.stats['successful_checks'] += 1
                self.stats['last_successful_check'] = datetime.now().isoformat()
                self.stats['consecutive_failures'] = 0
                
                # Update average response time
                total_successful = self.stats['successful_checks']
                current_avg = self.stats['average_response_time']
                self.stats['average_response_time'] = (
                    (current_avg * (total_successful - 1) + response_time) / total_successful
                )
                
                logger.debug(f"Ollama health check successful: {response_time:.1f}ms, {len(models)} models available")
                return True
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
                self._update_failed_status(error_msg)
                return False
                
        except requests.exceptions.Timeout:
            error_msg = "Connection timeout (3s)"
            self._update_failed_status(error_msg)
            return False
        except requests.exceptions.ConnectionError:
            error_msg = "Connection refused - Ollama not running"
            self._update_failed_status(error_msg)
            return False
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self._update_failed_status(error_msg)
            return False
    
    def _update_failed_status(self, error_message: str):
        """Update status for failed connection."""
        self._status = ConnectionStatus(
            is_available=False,
            last_check=time.time(),
            response_time_ms=None,
            error_message=error_message,
            models_available=[]
        )
        
        self.stats['failed_checks'] += 1
        self.stats['consecutive_failures'] += 1
        
        # Log based on failure count
        if self.stats['consecutive_failures'] == 1:
            logger.warning(f"Ollama connection failed: {error_message}")
        elif self.stats['consecutive_failures'] % 5 == 0:
            logger.error(f"Ollama connection failed {self.stats['consecutive_failures']} times: {error_message}")
    
    def get_status(self) -> ConnectionStatus:
        """Get current connection status."""
        return self._status
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            **self.stats,
            'success_rate': (
                self.stats['successful_checks'] / max(self.stats['total_checks'], 1) * 100
            ),
            'current_status': {
                'available': self._status.is_available,
                'last_check_ago': time.time() - self._status.last_check if self._status.last_check else None,
                'response_time_ms': self._status.response_time_ms,
                'error': self._status.error_message,
                'models_count': len(self._status.models_available) if self._status.models_available else 0
            }
        }
    
    def get_available_models(self) -> list:
        """Get list of available models (from last successful check)."""
        return self._status.models_available or []
    
    def reset_statistics(self):
        """Reset connection statistics."""
        self.stats = {
            'total_checks': 0,
            'successful_checks': 0,
            'failed_checks': 0,
            'average_response_time': 0.0,
            'last_successful_check': None,
            'consecutive_failures': 0
        }
        logger.info("Ollama connection statistics reset")
    
    def get_diagnostic_info(self) -> Dict[str, Any]:
        """Get comprehensive diagnostic information for troubleshooting."""
        return {
            'endpoint': self.endpoint,
            'cache_duration': self.cache_duration,
            'status': self.get_status().__dict__,
            'statistics': self.get_statistics(),
            'troubleshooting': {
                'common_issues': [
                    "Ollama not installed or not running",
                    "Ollama running on different port",
                    "Firewall blocking localhost:11434",
                    "Ollama service crashed or hung"
                ],
                'suggested_actions': [
                    "Check if Ollama is running: curl http://localhost:11434/api/tags",
                    "Restart Ollama service",
                    "Check Ollama logs for errors",
                    "Verify port 11434 is not blocked"
                ]
            }
        }


# Global instance for shared use
_global_checker = None

def get_ollama_checker(endpoint: str = "http://localhost:11434") -> OllamaConnectionChecker:
    """Get or create global Ollama connection checker."""
    global _global_checker
    
    if _global_checker is None or _global_checker.endpoint != endpoint:
        _global_checker = OllamaConnectionChecker(endpoint)
    
    return _global_checker


if __name__ == "__main__":
    # Test the connection checker
    checker = OllamaConnectionChecker()
    
    print("Testing Ollama connection...")
    is_available = checker.is_available()
    print(f"Available: {is_available}")
    
    status = checker.get_status()
    print(f"Status: {status}")
    
    stats = checker.get_statistics()
    print(f"Statistics: {stats}")
    
    if is_available:
        models = checker.get_available_models()
        print(f"Available models: {models}")