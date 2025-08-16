#!/usr/bin/env python3
"""
Improved logging system for AutoJobAgent
Creates structured, rotated logs with better formatting
"""

import sys
sys.path.insert(0, 'src')

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import json
import traceback

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record):
        # Create structured log entry
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if present
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'message', 'exc_info', 'exc_text', 'stack_info']:
                log_entry['extra'] = log_entry.get('extra', {})
                log_entry['extra'][key] = value
        
        return json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))

class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter for console output."""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record):
        # Color codes for different log levels
        colors = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m', # Magenta
        }
        reset = '\033[0m'
        
        # Format the record
        formatted = super().format(record)
        
        # Add color for console output
        if record.levelname in colors:
            formatted = f"{colors[record.levelname]}{formatted}{reset}"
        
        return formatted

def setup_logging():
    """Set up comprehensive logging system."""
    
    # Create logs directory
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 1. Console Handler (Human readable)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(HumanReadableFormatter())
    root_logger.addHandler(console_handler)
    
    # 2. Main Application Log (Structured JSON)
    main_handler = logging.handlers.RotatingFileHandler(
        filename=logs_dir / 'application.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    main_handler.setLevel(logging.DEBUG)
    main_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(main_handler)
    
    # 3. Error Log (Errors and exceptions only)
    error_handler = logging.handlers.RotatingFileHandler(
        filename=logs_dir / 'errors.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(error_handler)
    
    # 4. Dashboard-specific logs
    dashboard_logger = logging.getLogger('dashboard')
    dashboard_handler = logging.handlers.RotatingFileHandler(
        filename=logs_dir / 'dashboard.log',
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    dashboard_handler.setFormatter(StructuredFormatter())
    dashboard_logger.addHandler(dashboard_handler)
    dashboard_logger.propagate = True  # Also send to root logger
    
    # 5. Job Processing logs
    job_logger = logging.getLogger('job_processing')
    job_handler = logging.handlers.RotatingFileHandler(
        filename=logs_dir / 'job_processing.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    job_handler.setFormatter(StructuredFormatter())
    job_logger.addHandler(job_handler)
    job_logger.propagate = True
    
    # 6. Scraping logs
    scraping_logger = logging.getLogger('scraping')
    scraping_handler = logging.handlers.RotatingFileHandler(
        filename=logs_dir / 'scraping.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    scraping_handler.setFormatter(StructuredFormatter())
    scraping_logger.addHandler(scraping_handler)
    scraping_logger.propagate = True
    
    # 7. Database logs
    db_logger = logging.getLogger('database')
    db_handler = logging.handlers.RotatingFileHandler(
        filename=logs_dir / 'database.log',
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    db_handler.setFormatter(StructuredFormatter())
    db_logger.addHandler(db_handler)
    db_logger.propagate = True
    
    # Log the setup completion
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized", extra={
        'handlers_count': len(root_logger.handlers),
        'log_directory': str(logs_dir.absolute())
    })

def log_system_info():
    """Log system information for debugging."""
    import psutil
    import platform
    
    logger = logging.getLogger('system')
    
    # System info
    system_info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
        'memory_available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
        'disk_free_gb': round(psutil.disk_usage('.').free / (1024**3), 2)
    }
    
    logger.info("System information", extra=system_info)

def log_database_info():
    """Log database status information."""
    try:
        from src.core.job_database import get_job_db
        from src.utils.profile_helpers import get_available_profiles
        
        logger = logging.getLogger('database')
        
        profiles = get_available_profiles()
        logger.info(f"Available profiles: {profiles}")
        
        for profile in profiles:
            try:
                db = get_job_db(profile)
                jobs = db.get_jobs(limit=5000)
                
                # Status distribution
                status_counts = {}
                for job in jobs:
                    status = job.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                logger.info(f"Profile status", extra={
                    'profile': profile,
                    'total_jobs': len(jobs),
                    'status_distribution': status_counts
                })
                
            except Exception as e:
                logger.error(f"Error checking profile {profile}", extra={
                    'profile': profile,
                    'error': str(e)
                })
    
    except Exception as e:
        logger = logging.getLogger('database')
        logger.error(f"Error logging database info: {e}")

def test_logging():
    """Test the logging system."""
    loggers = [
        logging.getLogger('dashboard'),
        logging.getLogger('job_processing'),
        logging.getLogger('scraping'),
        logging.getLogger('database')
    ]
    
    for logger in loggers:
        logger.debug(f"Debug message from {logger.name}")
        logger.info(f"Info message from {logger.name}")
        logger.warning(f"Warning message from {logger.name}")
        
        # Test exception logging
        try:
            raise ValueError(f"Test exception from {logger.name}")
        except Exception:
            logger.exception(f"Exception caught in {logger.name}")

if __name__ == "__main__":
    print("🔧 Setting up improved logging system...")
    setup_logging()
    
    print("📊 Logging system information...")
    log_system_info()
    
    print("💾 Logging database information...")
    log_database_info()
    
    print("🧪 Testing logging system...")
    test_logging()
    
    print("✅ Logging system setup complete!")
    print("\nLog files created in 'logs/' directory:")
    logs_dir = Path('logs')
    for log_file in logs_dir.glob('*.log'):
        print(f"  - {log_file.name}")
