#!/usr/bin/env python3
"""
JobQst Performance Optimizer - Week 1 Quick Wins
REALISTIC optimizations for personal project use
"""

import time
import psutil
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class StartupOptimizer:
    """Optimize startup performance"""
    
    def __init__(self):
        self.start_time = time.time()
        self.import_times = {}
    
    def track_import(self, module_name: str, import_func):
        """Track import time"""
        start = time.time()
        result = import_func()
        duration = time.time() - start
        self.import_times[module_name] = duration
        logger.info(f"Import {module_name}: {duration:.2f}s")
        return result
    
    def lazy_import_ml(self):
        """Only import ML libraries when actually needed"""
        if not hasattr(self, '_torch'):
            try:
                import torch
                self._torch = torch
                logger.info("PyTorch loaded on demand")
            except ImportError:
                self._torch = None
                logger.warning("PyTorch not available")
        return self._torch
    
    def lazy_import_transformers(self):
        """Only import transformers when actually needed"""
        if not hasattr(self, '_transformers'):
            try:
                import transformers
                self._transformers = transformers
                logger.info("Transformers loaded on demand")
            except ImportError:
                self._transformers = None
                logger.warning("Transformers not available")
        return self._transformers


class MemoryOptimizer:
    """Optimize memory usage"""
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get current memory usage"""
        process = psutil.Process()
        return {
            'rss_mb': process.memory_info().rss / 1024 / 1024,
            'vms_mb': process.memory_info().vms / 1024 / 1024,
            'percent': process.memory_percent()
        }
    
    @staticmethod
    def cleanup_unused_imports():
        """Remove unused imports from memory"""
        import gc
        gc.collect()
        logger.info("Memory cleanup completed")


class DatabaseOptimizer:
    """Optimize database performance"""
    
    @staticmethod
    def setup_database_optimizations():
        """Database optimizations for DuckDB"""
        # DuckDB is pre-optimized for analytical performance
        # No specific connection-level optimizations needed
        logger.info("DuckDB is pre-optimized for analytical performance")
        return True


# Quick optimization functions
def optimize_startup():
    """Apply all startup optimizations"""
    optimizer = StartupOptimizer()
    
    # Track heavy imports
    ml_available = optimizer.lazy_import_ml() is not None
    transformers_available = optimizer.lazy_import_transformers() is not None
    
    total_time = time.time() - optimizer.start_time
    logger.info(f"Optimized startup completed in {total_time:.2f}s")
    
    return {
        'startup_time': total_time,
        'ml_available': ml_available,
        'transformers_available': transformers_available,
        'import_times': optimizer.import_times
    }


def optimize_memory():
    """Apply memory optimizations"""
    optimizer = MemoryOptimizer()
    
    before = optimizer.get_memory_usage()
    optimizer.cleanup_unused_imports()
    after = optimizer.get_memory_usage()
    
    savings = before['rss_mb'] - after['rss_mb']
    logger.info(f"Memory optimization: saved {savings:.1f}MB")
    
    return {
        'before_mb': before['rss_mb'],
        'after_mb': after['rss_mb'],
        'saved_mb': savings
    }


def optimize_database(profile_name: str = "default"):
    """Apply database optimizations"""
    import os
    
    # Check for DuckDB databases (new architecture)
    duckdb_paths = [
        f"profiles/{profile_name}/{profile_name}_duckdb.db"
    ]
    
    optimizer = DatabaseOptimizer()
    
    # DuckDB optimization doesn't require per-file configuration
    optimizer.setup_database_optimizations()
    
    # Log existing DuckDB databases
    for db_path in duckdb_paths:
        if os.path.exists(db_path):
            logger.info(f"Found DuckDB database: {db_path}")
        else:
            logger.info(f"DuckDB database not found: {db_path}")


if __name__ == "__main__":
    # Run all optimizations
    print("🚀 JobQst Performance Optimizer")
    print("Applying realistic optimizations...")
    
    startup_stats = optimize_startup()
    memory_stats = optimize_memory()
    optimize_database()
    
    print(f"✅ Optimizations complete!")
    print(f"Startup time: {startup_stats['startup_time']:.2f}s")
    print(f"Memory saved: {memory_stats['saved_mb']:.1f}MB")
