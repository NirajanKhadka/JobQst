#!/usr/bin/env python3
"""
Config Loader Utility - Base class for loading and caching configuration files
Part of the Config-Driven Architecture Pattern

This module provides a centralized, type-safe way to load configuration files
with caching, validation, and error handling.

Usage:
    from src.utils.config_loader import ConfigLoader
    
    loader = ConfigLoader()
    job_config = loader.load_config("job_matching_config.json")
    salary_config = loader.load_config("salary_config.json")
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class ConfigMetadata:
    """Metadata about a loaded configuration"""
    filename: str
    version: str
    last_updated: str
    load_time_ms: float
    config_path: Path
    is_cached: bool = False


class ConfigLoader:
    """
    Centralized configuration loader with caching and validation
    
    Features:
    - LRU caching for performance
    - Automatic path resolution
    - JSON schema validation support
    - Error handling and fallback
    - Performance monitoring
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize config loader
        
        Args:
            config_dir: Path to config directory (defaults to project root/config)
        """
        if config_dir is None:
            # Auto-detect config directory from project root
            project_root = Path(__file__).parent.parent.parent
            self.config_dir = project_root / "config"
        else:
            self.config_dir = Path(config_dir)
        
        if not self.config_dir.exists():
            logger.warning(f"Config directory not found: {self.config_dir}")
            self.config_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ConfigLoader initialized with config_dir: {self.config_dir}")
    
    @lru_cache(maxsize=32)
    def load_config(self, config_filename: str, validate: bool = True) -> Dict[str, Any]:
        """
        Load configuration file with caching
        
        Args:
            config_filename: Name of config file (e.g., "job_matching_config.json")
            validate: Whether to validate the config structure
        
        Returns:
            Dictionary containing configuration data
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        start_time = time.time()
        config_path = self.config_dir / config_filename
        
        logger.debug(f"Loading config: {config_filename}")
        
        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            load_time_ms = (time.time() - start_time) * 1000
            
            # Validate config structure if requested
            if validate:
                self._validate_config(config_data, config_filename)
            
            logger.info(
                f"Config loaded successfully: {config_filename} "
                f"(version: {config_data.get('version', 'unknown')}, "
                f"load_time: {load_time_ms:.2f}ms)"
            )
            
            return config_data
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file {config_filename}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading config {config_filename}: {e}")
            raise
    
    def _validate_config(self, config_data: Dict[str, Any], config_filename: str) -> None:
        """
        Validate configuration structure
        
        Args:
            config_data: Loaded configuration dictionary
            config_filename: Name of config file for error messages
        """
        # Check for required metadata fields
        required_fields = ["version", "description"]
        missing_fields = [field for field in required_fields if field not in config_data]
        
        if missing_fields:
            logger.warning(
                f"Config {config_filename} missing recommended fields: {missing_fields}"
            )
        
        # Validate version format (should be semantic versioning)
        version = config_data.get("version", "")
        if version and not self._is_valid_version(version):
            logger.warning(f"Config {config_filename} has invalid version format: {version}")
    
    def _is_valid_version(self, version: str) -> bool:
        """Check if version string follows semantic versioning (X.Y.Z)"""
        parts = version.split(".")
        return len(parts) == 3 and all(part.isdigit() for part in parts)
    
    def reload_config(self, config_filename: str) -> Dict[str, Any]:
        """
        Force reload a configuration file (bypasses cache)
        
        Args:
            config_filename: Name of config file to reload
        
        Returns:
            Reloaded configuration dictionary
        """
        # Clear cache for this specific config
        self.load_config.cache_clear()
        logger.info(f"Reloaded config: {config_filename}")
        return self.load_config(config_filename)
    
    def get_config_metadata(self, config_filename: str) -> ConfigMetadata:
        """
        Get metadata about a configuration file
        
        Args:
            config_filename: Name of config file
        
        Returns:
            ConfigMetadata object with file information
        """
        config_path = self.config_dir / config_filename
        config_data = self.load_config(config_filename)
        
        return ConfigMetadata(
            filename=config_filename,
            version=config_data.get("version", "unknown"),
            last_updated=config_data.get("last_updated", "unknown"),
            load_time_ms=0.0,  # Would need to track separately
            config_path=config_path,
            is_cached=True
        )
    
    def list_available_configs(self) -> list[str]:
        """
        List all available configuration files in the config directory
        
        Returns:
            List of config filenames
        """
        if not self.config_dir.exists():
            return []
        
        config_files = [
            f.name for f in self.config_dir.glob("*.json")
            if f.is_file() and not f.name.startswith(".")
        ]
        
        logger.info(f"Found {len(config_files)} config files in {self.config_dir}")
        return sorted(config_files)
    
    def clear_cache(self) -> None:
        """Clear the configuration cache"""
        self.load_config.cache_clear()
        logger.info("Configuration cache cleared")
    
    @staticmethod
    def build_lookup_dict(items: list[str]) -> Dict[str, str]:
        """
        Build O(1) lookup dictionary from list of items
        
        This is useful for converting skill lists, keyword lists, etc.
        into fast lookup structures.
        
        Args:
            items: List of strings to convert
        
        Returns:
            Dictionary with lowercase keys mapping to original values
        
        Example:
            >>> items = ["Python", "JavaScript", "SQL"]
            >>> lookup = ConfigLoader.build_lookup_dict(items)
            >>> "python" in lookup  # O(1) lookup
            True
            >>> lookup["python"]
            'Python'
        """
        return {item.lower(): item for item in items if item}
    
    @staticmethod
    def build_skill_variations_dict(skill_synonyms: Dict[str, list[str]]) -> Dict[str, str]:
        """
        Build reverse lookup dict for skill variations
        
        Takes skill_synonyms from config and creates a dict where each
        variation maps back to the canonical skill name.
        
        Args:
            skill_synonyms: Dict of canonical_name -> [variations]
        
        Returns:
            Dict of variation_lower -> canonical_name
        
        Example:
            >>> synonyms = {"javascript": ["js", "javascript", "node"]}
            >>> variations = ConfigLoader.build_skill_variations_dict(synonyms)
            >>> variations["js"]
            'javascript'
            >>> variations["node"]
            'javascript'
        """
        variations = {}
        for canonical_name, synonyms in skill_synonyms.items():
            for synonym in synonyms:
                variations[synonym.lower()] = canonical_name
        return variations
    
    def get_config_section(
        self,
        config_filename: str,
        section_path: str,
        default: Any = None
    ) -> Any:
        """
        Get a specific section from a config file using dot notation
        
        Args:
            config_filename: Config file to load
            section_path: Path to section using dots (e.g., "matching_weights.skill_match")
            default: Default value if section not found
        
        Returns:
            Value at the specified path or default
        
        Example:
            >>> loader.get_config_section(
            ...     "job_matching_config.json",
            ...     "matching_weights.skill_match"
            ... )
            0.40
        """
        config = self.load_config(config_filename)
        
        # Navigate through nested dictionary
        current = config
        for key in section_path.split("."):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                logger.debug(f"Section path not found: {section_path}")
                return default
        
        return current


class JobMatchingConfig(ConfigLoader):
    """Specialized loader for job matching configuration"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        super().__init__(config_dir)
        self._config = None
        self._skill_variations = None
    
    @property
    def config(self) -> Dict[str, Any]:
        """Lazy load and cache the job matching config"""
        if self._config is None:
            self._config = self.load_config("job_matching_config.json")
        return self._config
    
    @property
    def skill_variations(self) -> Dict[str, str]:
        """Build and cache skill variations lookup dict"""
        if self._skill_variations is None:
            skill_synonyms = self.config.get("skill_synonyms", {})
            self._skill_variations = self.build_skill_variations_dict(skill_synonyms)
        return self._skill_variations
    
    def get_matching_weights(self) -> Dict[str, float]:
        """Get matching weights for score calculation"""
        return self.config.get("matching_weights", {})
    
    def get_readiness_criteria(self) -> Dict[str, Any]:
        """Get application readiness criteria"""
        return self.config.get("readiness_criteria", {})


class SalaryConfig(ConfigLoader):
    """Specialized loader for salary parsing configuration"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        super().__init__(config_dir)
        self._config = None
    
    @property
    def config(self) -> Dict[str, Any]:
        """Lazy load and cache the salary config"""
        if self._config is None:
            self._config = self.load_config("salary_config.json")
        return self._config
    
    def get_salary_patterns(self) -> Dict[str, Any]:
        """Get salary extraction patterns"""
        return self.config.get("salary_patterns", {})
    
    def get_period_mappings(self) -> Dict[str, Any]:
        """Get period conversion mappings"""
        return self.config.get("period_mappings", {})


# Singleton instances for easy importing
_job_matching_config = None
_salary_config = None


def get_job_matching_config() -> JobMatchingConfig:
    """Get singleton instance of JobMatchingConfig"""
    global _job_matching_config
    if _job_matching_config is None:
        _job_matching_config = JobMatchingConfig()
    return _job_matching_config


def get_salary_config() -> SalaryConfig:
    """Get singleton instance of SalaryConfig"""
    global _salary_config
    if _salary_config is None:
        _salary_config = SalaryConfig()
    return _salary_config


if __name__ == "__main__":
    # Test the config loader
    logging.basicConfig(level=logging.INFO)
    
    loader = ConfigLoader()
    print(f"Config directory: {loader.config_dir}")
    print(f"Available configs: {loader.list_available_configs()}")
    
    # Test loading job matching config
    try:
        job_config = loader.load_config("job_matching_config.json")
        print(f"\nJob Matching Config Version: {job_config.get('version')}")
        print(f"Matching Weights: {job_config.get('matching_weights')}")
    except Exception as e:
        print(f"Error loading config: {e}")
