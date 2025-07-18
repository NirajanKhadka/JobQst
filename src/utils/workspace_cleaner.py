"""
Workspace Cleaner Utility for AutoJobAgent

This module provides a simple interface for cleaning up the workspace
from within the main application.
"""

import os
import shutil
import glob
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class WorkspaceCleaner:
    """Simple workspace cleaner for AutoJobAgent"""

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root).resolve()
        self.stats = {"files_removed": 0, "directories_removed": 0, "bytes_freed": 0, "errors": 0}

    def clean_cache_files(self) -> Dict:
        """Clean Python cache files and temporary files"""
        logger.info("Cleaning cache files...")

        # Remove __pycache__ directories
        for root, dirs, files in os.walk(self.workspace_root):
            if "__pycache__" in dirs:
                pycache_path = Path(root) / "__pycache__"
                try:
                    # Calculate size before removal
                    total_size = sum(
                        f.stat().st_size for f in pycache_path.rglob("*") if f.is_file()
                    )
                    shutil.rmtree(pycache_path)
                    self.stats["directories_removed"] += 1
                    self.stats["bytes_freed"] += total_size
                    logger.debug(f"Removed: {pycache_path}")
                except Exception as e:
                    logger.error(f"Error removing {pycache_path}: {e}")
                    self.stats["errors"] += 1

        # Remove .pytest_cache
        pytest_cache = self.workspace_root / ".pytest_cache"
        if pytest_cache.exists():
            try:
                total_size = sum(f.stat().st_size for f in pytest_cache.rglob("*") if f.is_file())
                shutil.rmtree(pytest_cache)
                self.stats["directories_removed"] += 1
                self.stats["bytes_freed"] += total_size
                logger.debug(f"Removed: {pytest_cache}")
            except Exception as e:
                logger.error(f"Error removing {pytest_cache}: {e}")
                self.stats["errors"] += 1

        return self.stats

    def clean_temp_files(self) -> Dict:
        """Clean temporary files"""
        logger.info("Cleaning temporary files...")

        # Files to remove
        temp_patterns = [
            "dashboard.pid",
            "dashboard_api_response.json",
            "error_logs.log",
            "file_size_report.txt",
            "*.backup.*",
            "test_results*.txt",
            "import_errors*.txt",
            "*_errors_summary.txt",
            # "ssl_fix.py",  # Excluded - essential for application
        ]

        for pattern in temp_patterns:
            pattern_path = self.workspace_root / pattern
            for file_path in glob.glob(str(pattern_path), recursive=True):
                path = Path(file_path)
                if path.is_file():
                    try:
                        size = path.stat().st_size
                        path.unlink()
                        self.stats["files_removed"] += 1
                        self.stats["bytes_freed"] += size
                        logger.debug(f"Removed: {path}")
                    except Exception as e:
                        logger.error(f"Error removing {path}: {e}")
                        self.stats["errors"] += 1

        return self.stats

    def clean_empty_directories(self) -> Dict:
        """Remove empty directories"""
        logger.info("Cleaning empty directories...")

        for root, dirs, files in os.walk(self.workspace_root, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if dir_path.exists() and not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        self.stats["directories_removed"] += 1
                        logger.debug(f"Removed empty directory: {dir_path}")
                except Exception as e:
                    logger.debug(f"Could not remove directory {dir_path}: {e}")

        return self.stats

    def cleanup(self) -> Dict:
        """Perform complete cleanup"""
        logger.info(f"Starting workspace cleanup for: {self.workspace_root}")

        self.clean_cache_files()
        self.clean_temp_files()
        self.clean_empty_directories()

        logger.info(
            f"Cleanup completed: {self.stats['files_removed']} files, "
            f"{self.stats['directories_removed']} directories, "
            f"{self.format_bytes(self.stats['bytes_freed'])} freed"
        )

        return self.stats

    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes into human readable format"""
        value = float(bytes_value)
        for unit in ["B", "KB", "MB", "GB"]:
            if value < 1024.0:
                return f"{value:.1f} {unit}"
            value /= 1024.0
        return f"{value:.1f} TB"


def cleanup_workspace(workspace_root: str = ".") -> Dict:
    """
    Simple function to clean up workspace

    Args:
        workspace_root: Root directory to clean (default: current directory)

    Returns:
        Dictionary with cleanup statistics
    """
    cleaner = WorkspaceCleaner(workspace_root)
    return cleaner.cleanup()


def cleanup_cache_only(workspace_root: str = ".") -> Dict:
    """
    Clean only cache files (safer option)

    Args:
        workspace_root: Root directory to clean (default: current directory)

    Returns:
        Dictionary with cleanup statistics
    """
    cleaner = WorkspaceCleaner(workspace_root)
    return cleaner.clean_cache_files()


if __name__ == "__main__":
    # Test the cleaner
    import logging

    logging.basicConfig(level=logging.INFO)

    stats = cleanup_workspace()
    print(f"Cleanup completed: {stats}")
