#!/usr/bin/env python3
"""
AI Service Configuration Management
Handles configuration for AI service endpoints, fallback priorities, and runtime settings
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AIServiceEndpoint:
    """AI service endpoint configuration"""
    name: str
    endpoint: str
    model: str
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    priority: int = 1  # Lower number = higher priority
    enabled: bool = True
    auth_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.auth_config is None:
            self.auth_config = {}


@dataclass
class AIServiceConfig:
    """Complete AI service configuration"""
    endpoints: List[AIServiceEndpoint]
    fallback_to_rule_based: bool = True
    rule_based_min_score: float = 0.6
    connection_check_interval: int = 30
    health_check_timeout: int = 5
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60


class AIServiceConfigManager:
    """Manages AI service configuration with environment variable support and runtime updates"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file or self._get_default_config_path()
        self.config: Optional[AIServiceConfig] = None
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        # Try workspace config first
        workspace_config = Path(".kiro/settings/ai_service_config.json")
        if workspace_config.exists():
            return str(workspace_config)
        
        # Try user config
        user_config = Path.home() / ".kiro/settings/ai_service_config.json"
        if user_config.exists():
            return str(user_config)
        
        # Default to workspace config (will be created)
        workspace_config.parent.mkdir(parents=True, exist_ok=True)
        return str(workspace_config)
    
    def _load_config(self):
        """Load configuration from file and environment variables."""
        try:
            # Load from file if exists
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                self.config = self._parse_config_data(config_data)
                logger.info(f"Loaded AI service config from {self.config_file}")
            else:
                # Create default configuration
                self.config = self._create_default_config()
                self._save_config()
                logger.info(f"Created default AI service config at {self.config_file}")
            
            # Apply environment variable overrides
            self._apply_env_overrides()
            
        except Exception as e:
            logger.error(f"Error loading AI service config: {e}")
            self.config = self._create_default_config()
    
    def _create_default_config(self) -> AIServiceConfig:
        """Create default AI service configuration."""
        endpoints = [
            AIServiceEndpoint(
                name="mistral_local",
                endpoint="http://localhost:11434",
                model="mistral:7b",
                timeout_seconds=30,
                max_retries=3,
                priority=1,
                enabled=True
            ),
            AIServiceEndpoint(
                name="llama_local",
                endpoint="http://localhost:11434",
                model="llama3:latest",
                timeout_seconds=30,
                max_retries=3,
                priority=2,
                enabled=True
            ),
            AIServiceEndpoint(
                name="gemini_cloud",
                endpoint="https://generativelanguage.googleapis.com",
                model="gemini-1.5-pro",
                timeout_seconds=60,
                max_retries=2,
                priority=3,
                enabled=False,  # Disabled by default, requires API key
                auth_config={"api_key_env": "GEMINI_API_KEY"}
            )
        ]
        
        return AIServiceConfig(
            endpoints=endpoints,
            fallback_to_rule_based=True,
            rule_based_min_score=0.6,
            connection_check_interval=30,
            health_check_timeout=5,
            enable_circuit_breaker=True,
            circuit_breaker_threshold=5,
            circuit_breaker_timeout=60
        )
    
    def _parse_config_data(self, config_data: Dict[str, Any]) -> AIServiceConfig:
        """Parse configuration data from dictionary."""
        endpoints = []
        for endpoint_data in config_data.get('endpoints', []):
            endpoints.append(AIServiceEndpoint(**endpoint_data))
        
        return AIServiceConfig(
            endpoints=endpoints,
            fallback_to_rule_based=config_data.get('fallback_to_rule_based', True),
            rule_based_min_score=config_data.get('rule_based_min_score', 0.6),
            connection_check_interval=config_data.get('connection_check_interval', 30),
            health_check_timeout=config_data.get('health_check_timeout', 5),
            enable_circuit_breaker=config_data.get('enable_circuit_breaker', True),
            circuit_breaker_threshold=config_data.get('circuit_breaker_threshold', 5),
            circuit_breaker_timeout=config_data.get('circuit_breaker_timeout', 60)
        )
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration."""
        if not self.config:
            return
        
        # Override endpoint URLs
        ollama_endpoint = os.getenv('OLLAMA_ENDPOINT')
        if ollama_endpoint:
            for endpoint in self.config.endpoints:
                if 'localhost:11434' in endpoint.endpoint:
                    endpoint.endpoint = ollama_endpoint
                    logger.info(f"Override {endpoint.name} endpoint: {ollama_endpoint}")
        
        # Override timeouts
        ai_timeout = os.getenv('AI_SERVICE_TIMEOUT')
        if ai_timeout:
            try:
                timeout_value = int(ai_timeout)
                for endpoint in self.config.endpoints:
                    endpoint.timeout_seconds = timeout_value
                logger.info(f"Override AI service timeout: {timeout_value}s")
            except ValueError:
                logger.warning(f"Invalid AI_SERVICE_TIMEOUT value: {ai_timeout}")
        
        # Override max retries
        max_retries = os.getenv('AI_SERVICE_MAX_RETRIES')
        if max_retries:
            try:
                retry_value = int(max_retries)
                for endpoint in self.config.endpoints:
                    endpoint.max_retries = retry_value
                logger.info(f"Override AI service max retries: {retry_value}")
            except ValueError:
                logger.warning(f"Invalid AI_SERVICE_MAX_RETRIES value: {max_retries}")
        
        # Enable/disable rule-based fallback
        enable_fallback = os.getenv('ENABLE_RULE_BASED_FALLBACK')
        if enable_fallback:
            self.config.fallback_to_rule_based = enable_fallback.lower() in ['true', '1', 'yes']
            logger.info(f"Override rule-based fallback: {self.config.fallback_to_rule_based}")
        
        # Override rule-based minimum score
        min_score = os.getenv('RULE_BASED_MIN_SCORE')
        if min_score:
            try:
                score_value = float(min_score)
                self.config.rule_based_min_score = score_value
                logger.info(f"Override rule-based min score: {score_value}")
            except ValueError:
                logger.warning(f"Invalid RULE_BASED_MIN_SCORE value: {min_score}")
        
        # Enable Gemini if API key is available
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if gemini_api_key:
            for endpoint in self.config.endpoints:
                if endpoint.name == 'gemini_cloud':
                    endpoint.enabled = True
                    logger.info("Enabled Gemini Cloud endpoint (API key found)")
    
    def _save_config(self):
        """Save current configuration to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Convert to dictionary
            config_dict = {
                'endpoints': [asdict(endpoint) for endpoint in self.config.endpoints],
                'fallback_to_rule_based': self.config.fallback_to_rule_based,
                'rule_based_min_score': self.config.rule_based_min_score,
                'connection_check_interval': self.config.connection_check_interval,
                'health_check_timeout': self.config.health_check_timeout,
                'enable_circuit_breaker': self.config.enable_circuit_breaker,
                'circuit_breaker_threshold': self.config.circuit_breaker_threshold,
                'circuit_breaker_timeout': self.config.circuit_breaker_timeout
            }
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            logger.info(f"Saved AI service config to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error saving AI service config: {e}")
    
    def get_config(self) -> AIServiceConfig:
        """Get current configuration."""
        return self.config
    
    def get_enabled_endpoints(self) -> List[AIServiceEndpoint]:
        """Get list of enabled endpoints sorted by priority."""
        if not self.config:
            return []
        
        enabled_endpoints = [ep for ep in self.config.endpoints if ep.enabled]
        return sorted(enabled_endpoints, key=lambda x: x.priority)
    
    def get_endpoint_by_name(self, name: str) -> Optional[AIServiceEndpoint]:
        """Get endpoint configuration by name."""
        if not self.config:
            return None
        
        for endpoint in self.config.endpoints:
            if endpoint.name == name:
                return endpoint
        
        return None
    
    def update_endpoint(self, name: str, **kwargs) -> bool:
        """
        Update endpoint configuration.
        
        Args:
            name: Endpoint name
            **kwargs: Configuration parameters to update
            
        Returns:
            bool: True if update successful
        """
        endpoint = self.get_endpoint_by_name(name)
        if not endpoint:
            logger.warning(f"Endpoint not found: {name}")
            return False
        
        try:
            for key, value in kwargs.items():
                if hasattr(endpoint, key):
                    setattr(endpoint, key, value)
                    logger.info(f"Updated {name}.{key} = {value}")
                else:
                    logger.warning(f"Unknown endpoint parameter: {key}")
            
            self._save_config()
            return True
            
        except Exception as e:
            logger.error(f"Error updating endpoint {name}: {e}")
            return False
    
    def reload_config(self) -> bool:
        """
        Reload configuration from file and environment variables.
        
        Returns:
            bool: True if reload successful
        """
        try:
            self._load_config()
            logger.info("AI service configuration reloaded")
            return True
        except Exception as e:
            logger.error(f"Error reloading AI service config: {e}")
            return False
    
    def get_diagnostic_info(self) -> Dict[str, Any]:
        """Get diagnostic information about current configuration."""
        if not self.config:
            return {'error': 'No configuration loaded'}
        
        return {
            'config_file': self.config_file,
            'config_exists': os.path.exists(self.config_file),
            'total_endpoints': len(self.config.endpoints),
            'enabled_endpoints': len(self.get_enabled_endpoints()),
            'endpoints': [
                {
                    'name': ep.name,
                    'endpoint': ep.endpoint,
                    'model': ep.model,
                    'enabled': ep.enabled,
                    'priority': ep.priority,
                    'timeout': ep.timeout_seconds
                }
                for ep in self.config.endpoints
            ],
            'fallback_enabled': self.config.fallback_to_rule_based,
            'rule_based_min_score': self.config.rule_based_min_score,
            'circuit_breaker_enabled': self.config.enable_circuit_breaker,
            'environment_overrides': {
                'OLLAMA_ENDPOINT': os.getenv('OLLAMA_ENDPOINT'),
                'AI_SERVICE_TIMEOUT': os.getenv('AI_SERVICE_TIMEOUT'),
                'AI_SERVICE_MAX_RETRIES': os.getenv('AI_SERVICE_MAX_RETRIES'),
                'ENABLE_RULE_BASED_FALLBACK': os.getenv('ENABLE_RULE_BASED_FALLBACK'),
                'RULE_BASED_MIN_SCORE': os.getenv('RULE_BASED_MIN_SCORE'),
                'GEMINI_API_KEY': 'SET' if os.getenv('GEMINI_API_KEY') else 'NOT_SET'
            }
        }


# Global configuration manager instance
_global_config_manager = None

def get_ai_service_config() -> AIServiceConfigManager:
    """Get or create global AI service configuration manager."""
    global _global_config_manager
    
    if _global_config_manager is None:
        _global_config_manager = AIServiceConfigManager()
    
    return _global_config_manager


if __name__ == "__main__":
    # Test the configuration manager
    config_manager = AIServiceConfigManager()
    
    print("AI Service Configuration:")
    config = config_manager.get_config()
    print(f"  Fallback to rule-based: {config.fallback_to_rule_based}")
    print(f"  Rule-based min score: {config.rule_based_min_score}")
    print(f"  Circuit breaker enabled: {config.enable_circuit_breaker}")
    
    print("\nEnabled Endpoints:")
    for endpoint in config_manager.get_enabled_endpoints():
        print(f"  {endpoint.name}: {endpoint.endpoint} (priority: {endpoint.priority})")
    
    print("\nDiagnostic Info:")
    diagnostics = config_manager.get_diagnostic_info()
    for key, value in diagnostics.items():
        print(f"  {key}: {value}")
