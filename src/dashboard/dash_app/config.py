"""
Configuration module for JobLens Dash Dashboard
"""
import os
from pathlib import Path

# Dashboard Configuration
DASHBOARD_CONFIG = {
    'title': 'JobLens - AI-Powered Job Search Dashboard',
    'port': 8050,
    'debug': True,
    'host': '0.0.0.0',
    'theme': 'bootstrap',
    'auto_refresh_interval': 30000,  # milliseconds
    'max_jobs_display': 1000,
    'default_profile': 'Nirajan'
}

# Database Configuration
DATABASE_CONFIG = {
    'sqlite_path': Path(__file__).parent.parent.parent.parent / 'data' / 'jobs.db',
    'profiles_path': Path(__file__).parent.parent.parent.parent / 'profiles',
    # Use environment variable to determine database type
    'use_postgresql': os.getenv('DATABASE_TYPE', 'sqlite') == 'postgresql'
}

# Styling Configuration
COLORS = {
    'primary': '#2c3e50',
    'secondary': '#3498db',
    'success': '#27ae60',
    'warning': '#f39c12',
    'danger': '#e74c3c',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#1a1a1a',
    'background': '#ffffff',
    'surface': '#f5f5f5',
    'text_primary': '#2c3e50',
    'text_secondary': '#6c757d'
}

# API Configuration
API_CONFIG = {
    'base_url': os.environ.get('JOBLENS_API_BASE', 'http://127.0.0.1:8000'),
    'timeout': 30,
    'retry_attempts': 3
}

# Processing Configuration
PROCESSING_CONFIG = {
    'default_batch_size': 10,
    'max_concurrent_jobs': 5,
    'min_match_score': 60,
    'auto_process': False,
    'smart_filtering': True
}

# Cache Configuration
CACHE_CONFIG = {
    'ttl': 300,  # seconds
    'max_size': 100,  # MB
    'enabled': True
}