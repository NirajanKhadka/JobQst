"""
Configuration management for AutoJobAgent.
Uses Pydantic for type-safe settings and environment variable support.
"""
from pathlib import Path
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from pydantic.types import DirectoryPath, FilePath

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    APP_NAME: str = "AutoJobAgent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Paths
    BASE_DIR: DirectoryPath = Path(__file__).parent.parent.parent
    PROFILES_DIR: DirectoryPath = BASE_DIR / "profiles"
    OUTPUT_DIR: DirectoryPath = BASE_DIR / "output"
    LOGS_DIR: DirectoryPath = OUTPUT_DIR / "logs"
    
    # Browser settings
    DEFAULT_BROWSER: str = "opera"
    HEADLESS: bool = False
    BROWSER_TIMEOUT: int = 30000  # ms
    
    # LLM settings
    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "mistral"
    LLM_TIMEOUT: int = 120  # seconds
    
    # Scraper settings
    REQUEST_DELAY: float = 2.0  # seconds
    MAX_RETRIES: int = 3
    
    # ATS settings
    DEFAULT_ATS: str = "workday"
    
    class Config:
        env_prefix = "AJA_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @validator('PROFILES_DIR', 'OUTPUT_DIR', 'LOGS_DIR', pre=True)
    def ensure_dirs_exist(cls, v):
        """Ensure directories exist."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path

# Global settings instance
settings = Settings()
