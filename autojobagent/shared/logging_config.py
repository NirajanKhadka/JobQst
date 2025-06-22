"""
Logging configuration for AutoJobAgent.
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Union

from ..shared.config import settings

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.DEBUG if settings.DEBUG else logging.INFO

# Log directory
LOG_DIR = settings.LOGS_DIR
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Main log file
LOG_FILE = LOG_DIR / "autojobagent.log"

# Error log file
ERROR_LOG_FILE = LOG_DIR / "error.log"

# Maximum log file size (10 MB)
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB

# Number of backup logs to keep
BACKUP_COUNT = 5

def configure_logging(
    log_file: Union[str, Path] = LOG_FILE,
    error_log_file: Union[str, Path] = ERROR_LOG_FILE,
    log_level: int = LOG_LEVEL,
    console_level: Optional[int] = None,
    file_level: Optional[int] = None,
):
    """
    Configure logging for the application.
    
    Args:
        log_file: Path to the main log file
        error_log_file: Path to the error log file
        log_level: Default log level
        console_level: Log level for console output (defaults to log_level)
        file_level: Log level for file output (defaults to log_level)
    """
    if console_level is None:
        console_level = log_level
    if file_level is None:
        file_level = log_level
    
    # Convert string paths to Path objects
    if isinstance(log_file, str):
        log_file = Path(log_file)
    if isinstance(error_log_file, str):
        error_log_file = Path(error_log_file)
    
    # Ensure log directories exist
    log_file.parent.mkdir(parents=True, exist_ok=True)
    error_log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(min(console_level, file_level))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(file_level)
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler (only errors)
    error_file_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_file_handler)
    
    # Configure third-party loggers
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # Log configuration
    logger = logging.getLogger(__name__)
    logger.info("Logging configured")
    logger.debug("Debug logging enabled")

# Configure logging when this module is imported
configure_logging()
