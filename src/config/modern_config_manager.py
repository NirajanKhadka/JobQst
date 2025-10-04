"""
Modern configuration management for JobQst
Centralized, environment-aware, and validated configuration
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Environment types"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class DatabaseType(Enum):
    """Database types"""

    DUCKDB = "duckdb"
    POSTGRESQL = "postgresql"


@dataclass
class DatabaseConfig:
    """Database configuration"""

    type: DatabaseType = DatabaseType.DUCKDB
    url: Optional[str] = None
    host: str = "localhost"
    port: int = 5432
    database: str = "jobqst"
    username: str = "jobqst"
    password: str = ""
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False

    def get_url(self) -> str:
        """Get database URL"""
        if self.url:
            return self.url

        if self.type == DatabaseType.DUCKDB:
            return "duckdb:///data/jobs_duckdb.db"
        elif self.type == DatabaseType.POSTGRESQL:
            return (
                f"postgresql://{self.username}:{self.password}"
                f"@{self.host}:{self.port}/{self.database}"
            )

        raise ValueError(f"Unsupported database type: {self.type}")


@dataclass
class ScrapingConfig:
    """Scraping configuration"""

    max_workers: int = 4
    delay_between_requests: float = 2.0
    timeout: int = 30
    headless: bool = True
    user_agent: str = "JobQst/1.0"
    retry_attempts: int = 3
    rate_limit_per_minute: int = 30

    # JobSpy specific
    jobspy_sites: List[str] = None
    jobspy_max_jobs_per_site: int = 100
    jobspy_country: str = "Canada"

    def __post_init__(self):
        if self.jobspy_sites is None:
            self.jobspy_sites = ["indeed", "linkedin", "glassdoor"]


@dataclass
class DashboardConfig:
    """Dashboard configuration"""

    host: str = "0.0.0.0"
    port: int = 8050
    debug: bool = False
    auto_reload: bool = True
    title: str = "JobQst Dashboard"
    theme: str = "bootstrap"
    cache_timeout: int = 300  # 5 minutes

    # Feature flags
    enable_ai_analysis: bool = True
    enable_real_time_updates: bool = True
    enable_export_features: bool = True


@dataclass
class AIConfig:
    """AI and ML configuration"""

    enable_heavy_processing: bool = False
    lazy_load_models: bool = True
    cache_embeddings: bool = True
    similarity_threshold: float = 0.7
    batch_size: int = 32
    max_tokens: int = 512

    # Model settings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    openai_api_key: Optional[str] = None
    use_local_models: bool = True


@dataclass
class PerformanceConfig:
    """Performance and optimization settings"""

    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour
    max_memory_usage_mb: int = 2048
    gc_frequency: int = 100

    # Async settings
    max_concurrent_tasks: int = 50
    task_timeout: int = 300  # 5 minutes

    # Monitoring
    enable_metrics: bool = True
    metrics_interval: int = 60  # seconds


@dataclass
class JobQstConfig:
    """Main application configuration"""

    environment: Environment = Environment.DEVELOPMENT
    database: DatabaseConfig = None
    scraping: ScrapingConfig = None
    dashboard: DashboardConfig = None
    ai: AIConfig = None
    performance: PerformanceConfig = None

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = "logs/jobqst.log"

    def __post_init__(self):
        """Initialize nested configs"""
        if self.database is None:
            self.database = DatabaseConfig()
        if self.scraping is None:
            self.scraping = ScrapingConfig()
        if self.dashboard is None:
            self.dashboard = DashboardConfig()
        if self.ai is None:
            self.ai = AIConfig()
        if self.performance is None:
            self.performance = PerformanceConfig()


class ConfigManager:
    """Configuration manager with environment support"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self._config: Optional[JobQstConfig] = None
        self._environment = self._detect_environment()

    def _detect_environment(self) -> Environment:
        """Detect current environment"""
        env_var = os.getenv("JOBQST_ENV", "development").lower()
        try:
            return Environment(env_var)
        except ValueError:
            logger.warning(f"Unknown environment: {env_var}, using development")
            return Environment.DEVELOPMENT

    def load_config(self, config_path: Optional[str] = None) -> JobQstConfig:
        """Load configuration from file or environment"""
        if config_path is None:
            config_path = self.config_dir / f"{self._environment.value}.json"

        config_path = Path(config_path)

        if config_path.exists():
            config_data = self._load_config_file(config_path)
        else:
            logger.info(f"Config file not found: {config_path}, using defaults")
            config_data = {}

        # Override with environment variables
        config_data = self._apply_env_overrides(config_data)

        # Create config object
        self._config = self._create_config_from_dict(config_data)

        # Validate configuration
        self._validate_config()

        return self._config

    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from JSON or YAML file"""
        try:
            with open(config_path, "r") as f:
                if config_path.suffix.lower() in [".yaml", ".yml"]:
                    return yaml.safe_load(f) or {}
                else:  # JSON
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config file {config_path}: {e}")
            return {}

    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides"""
        env_mappings = {
            "DATABASE_URL": ("database", "url"),
            "DATABASE_TYPE": ("database", "type"),
            "SCRAPING_MAX_WORKERS": ("scraping", "max_workers"),
            "SCRAPING_DELAY": ("scraping", "delay_between_requests"),
            "DASHBOARD_PORT": ("dashboard", "port"),
            "DASHBOARD_HOST": ("dashboard", "host"),
            "AI_ENABLE_HEAVY_PROCESSING": ("ai", "enable_heavy_processing"),
            "OPENAI_API_KEY": ("ai", "openai_api_key"),
            "LOG_LEVEL": ("log_level",),
            "CACHE_TTL": ("performance", "cache_ttl"),
        }

        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_value(config_data, config_path, value)

        return config_data

    def _set_nested_value(self, data: Dict[str, Any], path: tuple, value: str):
        """Set nested configuration value"""
        current = data
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Type conversion
        final_key = path[-1]
        if final_key in ["max_workers", "port", "cache_ttl"]:
            value = int(value)
        elif final_key in ["delay_between_requests"]:
            value = float(value)
        elif final_key in ["enable_heavy_processing", "debug", "headless"]:
            value = value.lower() in ("true", "1", "yes", "on")

        current[final_key] = value

    def _create_config_from_dict(self, data: Dict[str, Any]) -> JobQstConfig:
        """Create config object from dictionary"""
        # Create nested config objects
        config_kwargs = {}

        if "database" in data:
            config_kwargs["database"] = DatabaseConfig(**data["database"])

        if "scraping" in data:
            config_kwargs["scraping"] = ScrapingConfig(**data["scraping"])

        if "dashboard" in data:
            config_kwargs["dashboard"] = DashboardConfig(**data["dashboard"])

        if "ai" in data:
            config_kwargs["ai"] = AIConfig(**data["ai"])

        if "performance" in data:
            config_kwargs["performance"] = PerformanceConfig(**data["performance"])

        # Add top-level settings
        for key in ["environment", "log_level", "log_file"]:
            if key in data:
                config_kwargs[key] = data[key]

        return JobQstConfig(**config_kwargs)

    def _validate_config(self):
        """Validate configuration settings"""
        if not self._config:
            raise ValueError("No configuration loaded")

        # Database validation
        if self._config.database.type == DatabaseType.POSTGRESQL:
            if not self._config.database.password and self._environment == Environment.PRODUCTION:
                logger.warning("PostgreSQL password not set in production")

        # Performance validation
        if self._config.scraping.max_workers > 10:
            logger.warning("High number of scraping workers may cause rate limiting")

        # AI validation
        if self._config.ai.enable_heavy_processing and not self._config.ai.lazy_load_models:
            logger.warning("Heavy processing enabled without lazy loading")

    def save_config(self, config_path: Optional[str] = None):
        """Save current configuration to file"""
        if not self._config:
            raise ValueError("No configuration to save")

        if config_path is None:
            config_path = self.config_dir / f"{self._environment.value}.json"

        config_dict = asdict(self._config)

        with open(config_path, "w") as f:
            json.dump(config_dict, f, indent=2, default=str)

        logger.info(f"Configuration saved to {config_path}")

    def get_config(self) -> JobQstConfig:
        """Get current configuration"""
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def create_default_configs(self):
        """Create default configuration files for all environments"""
        environments = {
            Environment.DEVELOPMENT: {
                "database": {"type": "duckdb"},
                "dashboard": {"debug": True, "port": 8050},
                "ai": {"enable_heavy_processing": False},
                "log_level": "DEBUG",
            },
            Environment.TESTING: {
                "database": {"type": "duckdb", "url": "duckdb:///test_duckdb.db"},
                "dashboard": {"debug": True, "port": 8051},
                "scraping": {"max_workers": 2},
                "log_level": "INFO",
            },
            Environment.PRODUCTION: {
                "database": {"type": "postgresql"},
                "dashboard": {"debug": False, "port": 8080},
                "ai": {"enable_heavy_processing": True},
                "performance": {"enable_metrics": True},
                "log_level": "INFO",
            },
        }

        for env, config_data in environments.items():
            config_path = self.config_dir / f"{env.value}.json"
            with open(config_path, "w") as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"Created default config: {config_path}")


# Global config manager instance
config_manager = ConfigManager()


def get_config() -> JobQstConfig:
    """Get the global configuration"""
    return config_manager.get_config()


def load_config(config_path: Optional[str] = None) -> JobQstConfig:
    """Load configuration from file"""
    return config_manager.load_config(config_path)


def setup_logging(config: JobQstConfig):
    """Setup logging based on configuration"""
    log_level = getattr(logging, config.log_level.upper())

    # Create formatter
    formatter = logging.Formatter("%(asctime)s [%(levelname)8s] %(name)s: %(message)s")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # File handler (if specified)
    handlers = [console_handler]
    if config.log_file:
        log_path = Path(config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(level=log_level, handlers=handlers, force=True)

    logger.info(f"Logging configured: level={config.log_level}, file={config.log_file}")


# Example usage
if __name__ == "__main__":
    # Create default configurations
    config_manager.create_default_configs()

    # Load and display config
    config = get_config()
    print(f"Environment: {config.environment}")
    print(f"Database URL: {config.database.get_url()}")
    print(f"Dashboard: {config.dashboard.host}:{config.dashboard.port}")
    print(f"Scraping workers: {config.scraping.max_workers}")
