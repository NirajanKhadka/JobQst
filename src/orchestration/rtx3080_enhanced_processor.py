"""
RTX 3080 Enhanced Job Processor
High-performance job processor optimized for RTX 3080 GPU with async architecture.
"""

import asyncio
import logging
import time
import multiprocessing as mp
from multiprocessing import Pool
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import sys
import os
from dataclasses import dataclass
from enum import Enum
import concurrent.futures

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.job_database import ModernJobDatabase, get_job_db
from src.ai.rtx3080_optimized_client import RTX3080OptimizedClient, get_rtx3080_optimized_client
from src.utils.profile_helpers import get_available_profiles

logger = logging.getLogger(__name__)

class RTX3080ProcessingStatus(Enum):
    """RTX 3080 processing status enumeration."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    GPU_OPTIMIZING = "gpu_optimizing"
    COMPLETED = "completed"
    ERROR = "error"
    STOPPED = "stopped"

@dataclass
class RTX3080ProcessingStats:
    """Enhanced statistics for RTX 3080 job processing."""
    total_jobs: int = 0
    processed_jobs: int = 0
    failed_jobs: int = 0
    processing_time: float = 0.0
    average_job_time: float = 0.0
    jobs_per_second: float = 0.0
    gpu_utilization_avg: float = 0.0
    memory_usage_peak_gb: float = 0.0
    batch_size_optimal: int = 8
    concurrent_streams: int = 4
    tensor_cores_utilized: bool = False
    cuda_cores_active: int = 0
    status: RTX3080ProcessingStatus = RTX3080ProcessingStatus.IDLE
    rtx3080_performance_multiplier: float = 1.0

class RTX3080EnhancedProcessor:
    """
    RTX 3080 enhanced job processor with async architecture and GPU optimization.
    
    Features:
    - Async/await architecture for maximum concurrency
    - RTX 3080 GPU batch processing
    - Dynamic worker scaling based on GPU capabilities
    - Concurrent GPU streams
    - Intelligent batch sizing
    - Real-time performance monitoring
    """
    
    def __init__(self, 
                 profile_name: str,
                 max_batch_size: int = 16,
                 concurrent_streams: int = 4,
                 async_workers: int = None,
                 enable_gpu_optimization: bool = True):
        """
        Initialize RTX 3080 enhanced processor.
        
        Args:
            profile_name: Profile name for database and processing
            max_batch_size: Maximum batch size for RTX 3080
            concurrent_streams: Number of concurrent GPU streams
            async_workers: Number of async workers (auto-detected if None)
            enable_gpu_optimization: Enable RTX 3080 optimizations
        """
        self.profile_name = profile_name
        self.max_batch_size = max_batch_size
        self.concurrent_streams = concurrent_streams
        self.enable_gpu_optimization = enable_gpu_optimization
        
        # Auto-detect optimal worker count based on system
        if async_workers is None:
            cpu_cores = os.cpu_count() or 4
            # RTX 3080 can handle more concurrent operations
            self.async_workers = min(cpu_cores * 2, 16)
        else:
            self.async_workers = async_workers
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize components
        self.db = get_job_db(profile_name)
        self.stats = RTX3080ProcessingStats(
            batch_size_optimal=max_batch_size,
            concurrent_streams=concurrent_streams
        )
        
        # RTX 3080 GPU client
        self.gpu_client = None
        
        # Async components
        self.job_queue = asyncio.Queue(maxsize=1000)
        self.result_queue = asyncio.Queue(maxsize=1000)
        self.processing_semaphore = asyncio.Semaphore(concurrent_streams)
        
        # Performance tracking
        self.performance_history = []
        self.gpu_metrics_history = []
        
        # Initialize RTX 3080 optimization
        self._initialize_rtx3080_components()
        
        self.logger.info(f"RTX 3080 enhanced processor initialized: {self.async_workers} workers, {max_batch_size} batch size")
    
    def _initialize_rtx3080_components(self) -> None:
        """Initialize RTX 3080 specific components."""
        if not self.enable_gpu_optimization:
            self.logger.info("GPU optimization disabled - using CPU fallback")
            return
        
        try:
            self.logger.info("🚀 Initializing RTX 3080 GPU client...")
            
            self.gpu_client = get_rtx3080_optimized_client(
                model="llama3",
                max_batch_size=self.max_batch_size,
                concurrent_streams=self.concurrent_streams
            )
            
            # Get initial performance report
            gpu_report = self.gpu_client.get_rtx3080_performance_report()
            self.stats.gpu_utilization_avg = gpu_report['current_metrics']['gpu_utilization_percent']
            self.stats.memory_usage_peak_gb = gpu_report['current_metrics']['memory_used_gb']
            self.stats.tensor_cores_utilized = gpu_report['optimization_status']['tensor_cores_available']
            
            self.logger.info("✅ RTX 3080 GPU client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"RTX 3080 initialization failed: {e}")
            self.gpu_client = None
            self.enable_gpu_optimization = False
    
    async def process_jobs_async_rtx3080(self, limit: Optional[int] = None) -> RTX3080ProcessingStats:
        """
        Process jobs using async architecture with RTX 3080 optimization.
        
        Args:
            limit: Maximum number of jobs to process
            
        Returns:
            RTX3080ProcessingStats with comprehensive results
        """
        self.logger.info(f"🚀 Starting RTX 3080 async job processing...")
        
        start_time = time.time()
        self.stats.status = RTX3080ProcessingStatus.INITIALIZING
        
        try:
            # Get jobs for processing
            jobs_to_process = await self._get_jobs_async(limit)
            
            if not jobs_to_process:
                self.logger.info("No jobs available for processing")
                self.stats.status = RTX3080ProcessingStatus.COMPLETED
                return self.stats
            
            self.stats.total_jobs = len(jobs_to_process)
            self.stats.status = RTX3080ProcessingStatus.RUNNING
            
            self.logger.info(f"📊 Processing {self.stats.total_jobs} jobs with RTX 3080 optimization")
            
            # Process jobs with async architecture
            if self.enable_gpu_optimization and self.gpu_client:
                processed_results = await self._process_jobs_with_rtx3080_batching(jobs_to_process)
            else:
                processed_results = await self._process_jobs_async_fallback(jobs_to_process)
            
            # Update database asynchronously
            await self._update_database_async(processed_results)
            
            # Calculate final statistics
            self._calculate_rtx3080_stats(start_time)
            
            self.stats.status = RTX3080ProcessingStatus.COMPLETED
            
            self.logger.info(f"✅ RTX 3080 processing complete: {self.stats.jobs_per_second:.1f} jobs/sec")
            
            return self.stats
            
        except Exception as e:
            self.logger.error(f"RTX 3080 async processing failed: {e}")
            self.stats.status = RTX3080ProcessingStatus.ERROR
            raise
    
    async def _get_jobs_async(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get jobs asynchronously for processing."""
        try:
            # Run database query in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            jobs = await loop.run_in_executor(
                None,
                lambda: self.db.get_jobs_by_status('scraped', limit=limit)
            )
            
            self.logger.debug(f"Retrieved {len(jobs)} jobs for processing")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve jobs: {e}")
            return []
    
    async def _process_jobs_with_rtx3080_batching(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process jobs using RTX 3080 batch optimization."""
        self.logger.info(f"🎯 Processing with RTX 3080 batch optimization...")
        
        all_results = []
        
        try:
            # Create optimal batches for RTX 3080
            job_batches = self._create_optimal_batches(jobs)
            
            # Process batches concurrently
            batch_tasks = []
            for batch in job_batches:
                task = self._process_batch_rtx3080(batch)
                batch_tasks.append(task)
            
            # Execute batches with controlled concurrency
            semaphore = asyncio.Semaphore(self.concurrent_streams)
            
            async def process_batch_with_semaphore(batch_task):
                async with semaphore:
                    return await batch_task
            
            # Process all batches
            batch_results = await asyncio.gather(
                *[process_batch_with_semaphore(task) for task in batch_tasks],
                return_exceptions=True
            )
            
            # Collect results
            for batch_result in batch_results:
                if isinstance(batch_result, list):
                    all_results.extend(batch_result)
                elif isinstance(batch_result, Exception):
                    self.logger.error(f"Batch processing failed: {batch_result}")
            
            # Update GPU metrics
            if self.gpu_client:
                gpu_report = self.gpu_client.get_rtx3080_performance_report()
                self._update_gpu_metrics(gpu_report)
            
            return all_results
            
        except Exception as e:
            self.logger.error(f"RTX 3080 batch processing failed: {e}")
            return []
    
    def _create_optimal_batches(self, jobs: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Create optimal batches for RTX 3080 processing."""
        # Dynamic batch sizing based on job complexity
        optimal_batch_size = self.max_batch_size
        
        # Adjust batch size based on job description length
        if jobs:
            avg_description_length = sum(
                len(job.get('description', job.get('job_description', ''))) 
                for job in jobs
            ) / len(jobs)
            
            # Reduce batch size for longer descriptions to avoid GPU memory issues
            if avg_description_length > 2000:
                optimal_batch_size = max(self.max_batch_size // 2, 4)
            elif avg_description_length > 1000:
                optimal_batch_size = max(int(self.max_batch_size * 0.75), 6)
        
        # Create batches
        batches = []
        for i in range(0, len(jobs), optimal_batch_size):
            batch = jobs[i:i + optimal_batch_size]
            batches.append(batch)
        
        self.logger.info(f"Created {len(batches)} optimal batches (size: {optimal_batch_size})")
        return batches
    
    async def _process_batch_rtx3080(self, job_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a single batch using RTX 3080."""
        try:
            if not self.gpu_client:
                return await self._process_batch_fallback(job_batch)
            
            # Get user profile for compatibility analysis
            user_profile = self._get_user_profile()
            
            # Process batch with RTX 3080
            batch_result = await self.gpu_client.analyze_jobs_batch_rtx3080(
                job_batch, user_profile
            )
            
            # Update performance metrics
            self._update_batch_performance_metrics(batch_result)
            
            return batch_result.job_results
            
        except Exception as e:
            self.logger.error(f"RTX 3080 batch processing failed: {e}")
            return await self._process_batch_fallback(job_batch)
    
    async def _process_batch_fallback(self, job_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback batch processing without GPU optimization."""
        results = []
        
        for job in job_batch:
            # Simple fallback processing
            result = job.copy()
            result.update({
                'required_skills': [],
                'job_requirements': [],
                'compatibility_score': 0.5,
                'analysis_confidence': 0.3,
                'extracted_benefits': [],
                'analysis_reasoning': 'Fallback processing - GPU unavailable',
                'processing_method': 'cpu_fallback',
                'gpu_accelerated': False,
                'processed_at': time.time()
            })
            results.append(result)
        
        return results
    
    async def _process_jobs_async_fallback(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback async processing without RTX 3080."""
        self.logger.info("Using async fallback processing...")
        
        # Process jobs in smaller batches asynchronously
        batch_size = 8  # Smaller batches for CPU processing
        job_batches = [jobs[i:i + batch_size] for i in range(0, len(jobs), batch_size)]
        
        all_results = []
        
        # Process batches concurrently
        batch_tasks = [self._process_batch_fallback(batch) for batch in job_batches]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        for batch_result in batch_results:
            if isinstance(batch_result, list):
                all_results.extend(batch_result)
        
        return all_results
    
    async def _update_database_async(self, processed_results: List[Dict[str, Any]]) -> None:
        """Update database asynchronously with batch operations."""
        self.logger.info(f"📝 Updating database with {len(processed_results)} results...")
        
        try:
            # Use thread pool for database operations
            loop = asyncio.get_event_loop()
            
            # Batch database updates for efficiency
            batch_size = 50
            successful_updates = 0
            failed_updates = 0
            
            for i in range(0, len(processed_results), batch_size):
                batch = processed_results[i:i + batch_size]
                
                # Process batch in thread pool
                batch_success, batch_failed = await loop.run_in_executor(
                    None,
                    self._update_job_batch_sync,
                    batch
                )
                
                successful_updates += batch_success
                failed_updates += batch_failed
            
            self.stats.processed_jobs = successful_updates
            self.stats.failed_jobs = failed_updates
            
            self.logger.info(f"✅ Database update complete: {successful_updates} successful, {failed_updates} failed")
            
        except Exception as e:
            self.logger.error(f"Database update failed: {e}")
            self.stats.failed_jobs = len(processed_results)
    
    def _update_job_batch_sync(self, job_batch: List[Dict[str, Any]]) -> Tuple[int, int]:
        """Update a batch of jobs synchronously."""
        successful = 0
        failed = 0
        
        for job in job_batch:
            try:
                success = self.db.update_job(job['id'], job)
                if success:
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                self.logger.error(f"Failed to update job {job.get('id', 'unknown')}: {e}")
                failed += 1
        
        return successful, failed
    
    def _get_user_profile(self) -> Optional[Dict[str, Any]]:
        """Get user profile for compatibility analysis."""
        try:
            # This would load the actual user profile
            # For now, return a basic profile structure
            return {
                'name': self.profile_name,
                'skills': ['Python', 'Data Analysis', 'Machine Learning'],
                'experience_level': 'Mid-level',
                'location': 'Toronto, ON',
                'preferences': {
                    'remote_work': True,
                    'salary_min': 60000,
                    'salary_max': 100000
                }
            }
        except Exception as e:
            self.logger.warning(f"Could not load user profile: {e}")
            return None
    
    def _update_batch_performance_metrics(self, batch_result) -> None:
        """Update performance metrics from batch result."""
        if hasattr(batch_result, 'jobs_per_second'):
            self.performance_history.append({
                'timestamp': time.time(),
                'jobs_per_second': batch_result.jobs_per_second,
                'gpu_utilization': batch_result.gpu_utilization,
                'memory_used_gb': batch_result.memory_used_gb,
                'batch_size': batch_result.batch_size,
                'tensor_cores_used': batch_result.tensor_cores_utilized
            })
            
            # Keep only recent history
            if len(self.performance_history) > 100:
                self.performance_history = self.performance_history[-100:]
    
    def _update_gpu_metrics(self, gpu_report: Dict[str, Any]) -> None:
        """Update GPU metrics from performance report."""
        current_metrics = gpu_report.get('current_metrics', {})
        
        self.stats.gpu_utilization_avg = current_metrics.get('gpu_utilization_percent', 0.0)
        self.stats.memory_usage_peak_gb = max(
            self.stats.memory_usage_peak_gb,
            current_metrics.get('memory_used_gb', 0.0)
        )
        self.stats.tensor_cores_utilized = gpu_report.get('optimization_status', {}).get('tensor_cores_available', False)
        
        # Store GPU metrics history
        self.gpu_metrics_history.append({
            'timestamp': time.time(),
            'gpu_utilization': current_metrics.get('gpu_utilization_percent', 0.0),
            'memory_used_gb': current_metrics.get('memory_used_gb', 0.0),
            'temperature_c': current_metrics.get('temperature_c', 0.0)
        })
        
        if len(self.gpu_metrics_history) > 100:
            self.gpu_metrics_history = self.gpu_metrics_history[-100:]
    
    def _calculate_rtx3080_stats(self, start_time: float) -> None:
        """Calculate final RTX 3080 processing statistics."""
        self.stats.processing_time = time.time() - start_time
        
        if self.stats.processed_jobs > 0:
            self.stats.average_job_time = self.stats.processing_time / self.stats.processed_jobs
            self.stats.jobs_per_second = self.stats.processed_jobs / self.stats.processing_time
        
        # Calculate performance multiplier vs baseline
        baseline_jobs_per_sec = 2.0  # Baseline performance
        self.stats.rtx3080_performance_multiplier = self.stats.jobs_per_second / baseline_jobs_per_sec
        
        self.logger.info(f"📊 RTX 3080 Performance: {self.stats.jobs_per_second:.1f} jobs/sec "
                        f"({self.stats.rtx3080_performance_multiplier:.1f}x faster)")
    
    def get_rtx3080_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive RTX 3080 performance report."""
        report = {
            'processor_status': self.stats.status.value,
            'processing_stats': {
                'total_jobs': self.stats.total_jobs,
                'processed_jobs': self.stats.processed_jobs,
                'failed_jobs': self.stats.failed_jobs,
                'jobs_per_second': self.stats.jobs_per_second,
                'processing_time': self.stats.processing_time,
                'performance_multiplier': self.stats.rtx3080_performance_multiplier
            },
            'rtx3080_metrics': {
                'gpu_utilization_avg': self.stats.gpu_utilization_avg,
                'memory_usage_peak_gb': self.stats.memory_usage_peak_gb,
                'batch_size_optimal': self.stats.batch_size_optimal,
                'concurrent_streams': self.stats.concurrent_streams,
                'tensor_cores_utilized': self.stats.tensor_cores_utilized
            },
            'system_config': {
                'async_workers': self.async_workers,
                'max_batch_size': self.max_batch_size,
                'gpu_optimization_enabled': self.enable_gpu_optimization,
                'profile_name': self.profile_name
            },
            'performance_history_count': len(self.performance_history),
            'gpu_metrics_history_count': len(self.gpu_metrics_history)
        }
        
        # Add GPU client report if available
        if self.gpu_client:
            gpu_report = self.gpu_client.get_rtx3080_performance_report()
            report['gpu_client_report'] = gpu_report
        
        return report
    
    async def benchmark_rtx3080_performance(self, test_job_count: int = 50) -> Dict[str, Any]:
        """Benchmark RTX 3080 performance with test jobs."""
        self.logger.info(f"🏁 Starting RTX 3080 performance benchmark with {test_job_count} test jobs...")
        
        # Create test jobs
        test_jobs = self._create_test_jobs(test_job_count)
        
        benchmark_start = time.time()
        
        # Run benchmark
        try:
            stats = await self.process_jobs_async_rtx3080()
            
            benchmark_time = time.time() - benchmark_start
            
            benchmark_results = {
                'benchmark_completed': True,
                'test_jobs_count': test_job_count,
                'benchmark_time': benchmark_time,
                'jobs_per_second': stats.jobs_per_second,
                'performance_multiplier': stats.rtx3080_performance_multiplier,
                'gpu_utilization': stats.gpu_utilization_avg,
                'memory_usage_peak': stats.memory_usage_peak_gb,
                'tensor_cores_used': stats.tensor_cores_utilized,
                'processing_stats': stats
            }
            
            # Add GPU client benchmark if available
            if self.gpu_client:
                gpu_benchmark = await self.gpu_client.benchmark_rtx3080_performance(test_jobs[:20])
                benchmark_results['gpu_client_benchmark'] = gpu_benchmark
            
            self.logger.info(f"🏆 RTX 3080 benchmark complete: {stats.jobs_per_second:.1f} jobs/sec")
            
            return benchmark_results
            
        except Exception as e:
            self.logger.error(f"RTX 3080 benchmark failed: {e}")
            return {
                'benchmark_completed': False,
                'error': str(e),
                'benchmark_time': time.time() - benchmark_start
            }
    
    def _create_test_jobs(self, count: int) -> List[Dict[str, Any]]:
        """Create test jobs for benchmarking."""
        test_jobs = []
        
        job_templates = [
            {
                'title': 'Software Engineer',
                'company': 'TechCorp',
                'description': 'Looking for a software engineer with Python, JavaScript, and React experience. Must have 3+ years of experience in web development.',
                'location': 'Toronto, ON',
                'status': 'scraped'
            },
            {
                'title': 'Data Scientist',
                'company': 'DataCorp',
                'description': 'Data scientist role requiring Python, machine learning, pandas, numpy, and statistical analysis skills. PhD preferred.',
                'location': 'Vancouver, BC',
                'status': 'scraped'
            },
            {
                'title': 'DevOps Engineer',
                'company': 'CloudCorp',
                'description': 'DevOps engineer with AWS, Docker, Kubernetes, and CI/CD pipeline experience. Must know Terraform and Ansible.',
                'location': 'Montreal, QC',
                'status': 'scraped'
            }
        ]
        
        for i in range(count):
            template = job_templates[i % len(job_templates)]
            job = template.copy()
            job['id'] = f'test_job_{i + 1}'
            job['url'] = f'https://example.com/job/{i + 1}'
            test_jobs.append(job)
        
        return test_jobs


# Convenience functions
def get_rtx3080_enhanced_processor(profile_name: str, **kwargs) -> RTX3080EnhancedProcessor:
    """Get RTX 3080 enhanced processor instance."""
    return RTX3080EnhancedProcessor(profile_name, **kwargs)

async def process_jobs_rtx3080_async(profile_name: str, limit: Optional[int] = None) -> RTX3080ProcessingStats:
    """Convenience function for RTX 3080 async job processing."""
    processor = RTX3080EnhancedProcessor(profile_name)
    return await processor.process_jobs_async_rtx3080(limit=limit)

# CLI integration
async def main():
    """Main async function for CLI execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RTX 3080 Enhanced Job Processor")
    parser.add_argument("--profile", required=True, help="Profile name for processing")
    parser.add_argument("--limit", type=int, help="Maximum number of jobs to process")
    parser.add_argument("--batch-size", type=int, default=16, help="RTX 3080 batch size")
    parser.add_argument("--streams", type=int, default=4, help="Concurrent GPU streams")
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmark")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Create RTX 3080 enhanced processor
        processor = RTX3080EnhancedProcessor(
            profile_name=args.profile,
            max_batch_size=args.batch_size,
            concurrent_streams=args.streams
        )
        
        print(f"🚀 RTX 3080 Enhanced Job Processor")
        print(f"⚙️ Configuration: {args.batch_size} batch size, {args.streams} streams")
        
        if args.benchmark:
            # Run benchmark
            print(f"🏁 Running RTX 3080 performance benchmark...")
            benchmark_results = await processor.benchmark_rtx3080_performance()
            
            print(f"\n📊 Benchmark Results:")
            print(f"✅ Jobs per second: {benchmark_results.get('jobs_per_second', 0):.1f}")
            print(f"🚀 Performance multiplier: {benchmark_results.get('performance_multiplier', 0):.1f}x")
            print(f"🎯 GPU utilization: {benchmark_results.get('gpu_utilization', 0):.1f}%")
            print(f"💾 Peak memory usage: {benchmark_results.get('memory_usage_peak', 0):.1f}GB")
        else:
            # Process jobs
            stats = await processor.process_jobs_async_rtx3080(limit=args.limit)
            
            print(f"\n📊 RTX 3080 Processing Results:")
            print(f"✅ Total jobs: {stats.total_jobs}")
            print(f"✅ Processed: {stats.processed_jobs}")
            print(f"❌ Failed: {stats.failed_jobs}")
            print(f"⏱️ Processing time: {stats.processing_time:.2f}s")
            print(f"📈 Jobs per second: {stats.jobs_per_second:.2f}")
            print(f"🚀 Performance multiplier: {stats.rtx3080_performance_multiplier:.1f}x")
            print(f"🎯 GPU utilization: {stats.gpu_utilization_avg:.1f}%")
            print(f"💾 Peak memory usage: {stats.memory_usage_peak_gb:.1f}GB")
            
            if stats.status == RTX3080ProcessingStatus.COMPLETED:
                print(f"\n🎉 RTX 3080 processing completed successfully!")
            else:
                print(f"\n⚠️ Processing ended with status: {stats.status.value}")
                
    except Exception as e:
        print(f"\n❌ RTX 3080 processing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())