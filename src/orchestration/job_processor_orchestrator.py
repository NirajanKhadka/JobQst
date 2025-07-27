#!/usr/bin/env python3
"""
Job Processor Orchestrator - Batch Analysis System
Consumes from processing queue and performs batch analysis with GPU enhancement.

Features:
- Configurable batch sizes for optimal performance
- Multiple analysis methods (rule-based, GPU-enhanced)
- Real-time progress tracking
- Error recovery and retry logic
- Performance optimization
- Integration with application queue
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

from ..core.job_database import get_job_db
from ..ai.enhanced_rule_based_analyzer import EnhancedRuleBasedAnalyzer
from ..pipeline.optimized_job_queue import OptimizedJobQueue
from ..utils.profile_helpers import load_profile

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class ProcessorMetrics:
    """Metrics for the job processor orchestrator."""
    total_jobs_processed: int = 0
    total_jobs_analyzed: int = 0
    total_jobs_queued: int = 0
    total_failures: int = 0
    total_retries: int = 0
    avg_analysis_time: float = 0.0
    avg_batch_time: float = 0.0
    batches_processed: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    success_rate: float = 0.0
    analysis_methods_used: Dict[str, int] = None


class JobProcessorOrchestrator:
    """
    Job processor orchestrator with batch analysis and GPU enhancement.
    
    Features:
    - Configurable batch sizes for optimal performance
    - Multiple analysis methods (rule-based, GPU-enhanced)
    - Real-time progress tracking
    - Error recovery and retry logic
    - Performance optimization
    - Integration with application queue
    """
    
    def __init__(self, profile_name: str, batch_size: int = 20, 
                 analysis_method: str = "hybrid", gpu_enabled: bool = True,
                 compatibility_threshold: float = 0.7):
        self.profile_name = profile_name
        self.batch_size = batch_size
        self.analysis_method = analysis_method
        self.gpu_enabled = gpu_enabled
        self.compatibility_threshold = compatibility_threshold
        
        # Initialize components
        self.db = get_job_db(profile_name)
        self.profile = load_profile(profile_name) or {}
        self.processing_queue = OptimizedJobQueue("job_processing")
        self.application_queue = OptimizedJobQueue("application_queue")
        
        # Initialize analyzers
        self.rule_analyzer = EnhancedRuleBasedAnalyzer(self.profile)
        self.gpu_analyzer = None
        if gpu_enabled:
            self.gpu_analyzer = self._initialize_gpu_analyzer()
        
        # Metrics tracking
        self.metrics = ProcessorMetrics()
        self.metrics.start_time = datetime.now()
        self.metrics.analysis_methods_used = {}
        
        # Processing state
        self.is_running = False
        self.processing_task = None
        
        # Progress tracking
        self.progress = None
        self.progress_task = None
        
        logger.info(f"JobProcessorOrchestrator initialized: batch_size={batch_size}, method={analysis_method}")
    
    def _initialize_gpu_analyzer(self):
        """Initialize GPU analyzer if available."""
        try:
            from ..ai.gpu_enhanced_analyzer import GPUEnhancedAnalyzer
            return GPUEnhancedAnalyzer(self.profile)
        except ImportError:
            logger.warning("GPU analyzer not available, using rule-based only")
            return None
    
    async def start(self):
        """Start the job processor orchestrator."""
        if self.is_running:
            logger.warning("Job processor orchestrator is already running")
            return
        
        console.print(f"[bold blue]🚀 Starting Job Processor Orchestrator[/bold blue]")
        console.print(f"[cyan]Batch size: {self.batch_size} | Method: {self.analysis_method} | GPU: {self.gpu_enabled}[/cyan]")
        
        # Start queues
        await self.processing_queue.start()
        await self.application_queue.start()
        
        # Start progress tracking
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        )
        self.progress.start()
        
        # Start processing
        self.is_running = True
        self.processing_task = asyncio.create_task(self._processing_loop())
        
        logger.info("Job processor orchestrator started")
    
    async def stop(self):
        """Stop the job processor orchestrator."""
        if not self.is_running:
            return
        
        console.print("[yellow]🛑 Stopping Job Processor Orchestrator...[/yellow]")
        
        # Stop processing
        self.is_running = False
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        # Stop progress tracking
        if self.progress:
            self.progress.stop()
        
        # Stop queues
        await self.processing_queue.stop()
        await self.application_queue.stop()
        
        # Update final metrics
        self.metrics.end_time = datetime.now()
        if self.metrics.total_jobs_processed > 0:
            self.metrics.success_rate = (self.metrics.total_jobs_analyzed / self.metrics.total_jobs_processed) * 100
        
        logger.info("Job processor orchestrator stopped")
    
    async def _processing_loop(self):
        """Main processing loop that consumes jobs from the queue."""
        while self.is_running:
            try:
                # Collect batch of jobs
                batch = await self._collect_batch()
                
                if batch:
                    # Process batch
                    await self._process_batch(batch)
                else:
                    # No jobs available, wait a bit
                    await asyncio.sleep(1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(5)
    
    async def _collect_batch(self) -> List[Dict[str, Any]]:
        """
        Collect a batch of jobs from the processing queue.
        
        Returns:
            List of job dictionaries
        """
        batch = []
        start_time = time.time()
        
        try:
            # Collect jobs up to batch size or timeout
            while len(batch) < self.batch_size and (time.time() - start_time) < 10:
                job = await self.processing_queue.dequeue_job(timeout=1)
                if job:
                    batch.append(job)
                else:
                    # No more jobs available
                    break
            
            if batch:
                logger.debug(f"Collected batch of {len(batch)} jobs")
            
            return batch
            
        except Exception as e:
            logger.error(f"Error collecting batch: {e}")
            return []
    
    async def _process_batch(self, batch: List[Dict[str, Any]]):
        """
        Process a batch of jobs.
        
        Args:
            batch: List of job dictionaries to process
        """
        batch_start_time = time.time()
        
        try:
            console.print(f"[cyan]📊 Processing batch of {len(batch)} jobs...[/cyan]")
            
            # Create progress task for this batch
            progress_task = self.progress.add_task(
                f"[cyan]Analyzing {len(batch)} jobs...",
                total=len(batch)
            )
            
            # Process each job in the batch
            processed_jobs = []
            for job in batch:
                try:
                    processed_job = await self._analyze_job(job)
                    if processed_job:
                        processed_jobs.append(processed_job)
                    
                    # Update progress
                    self.progress.advance(progress_task)
                    
                except Exception as e:
                    logger.error(f"Error processing job {job.get('id', 'unknown')}: {e}")
                    self.metrics.total_failures += 1
            
            # Update database and queue good matches
            await self._update_database_and_queue(processed_jobs)
            
            # Update metrics
            batch_time = time.time() - batch_start_time
            self.metrics.batches_processed += 1
            self.metrics.total_jobs_processed += len(batch)
            self.metrics.total_jobs_analyzed += len(processed_jobs)
            
            # Update average batch time
            if self.metrics.avg_batch_time == 0:
                self.metrics.avg_batch_time = batch_time
            else:
                self.metrics.avg_batch_time = (self.metrics.avg_batch_time + batch_time) / 2
            
            console.print(f"[green]✅ Processed batch: {len(processed_jobs)}/{len(batch)} jobs analyzed[/green]")
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            self.metrics.total_failures += len(batch)
    
    async def _analyze_job(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a single job with the selected analysis method.
        
        Args:
            job: Job data dictionary
            
        Returns:
            Analyzed job dictionary or None if failed
        """
        start_time = time.time()
        job_id = job.get('id', 'unknown')
        
        try:
            logger.debug(f"Analyzing job {job_id}")
            
            # Choose analysis method
            if self.analysis_method == "hybrid" and self.gpu_analyzer:
                # Use hybrid analysis (rule-based + GPU enhancement)
                analyzed_job = await self._hybrid_analysis(job)
                method_used = "hybrid"
            elif self.analysis_method == "gpu" and self.gpu_analyzer:
                # Use GPU analysis only
                analyzed_job = await self._gpu_analysis(job)
                method_used = "gpu"
            else:
                # Use rule-based analysis only
                analyzed_job = await self._rule_based_analysis(job)
                method_used = "rule_based"
            
            if analyzed_job:
                # Update analysis metadata
                analyzed_job['analyzed_at'] = datetime.now().isoformat()
                analyzed_job['analysis_method'] = method_used
                analyzed_job['analysis_time'] = time.time() - start_time
                analyzed_job['status'] = 'analyzed'
                
                # Track analysis method usage
                self.metrics.analysis_methods_used[method_used] = \
                    self.metrics.analysis_methods_used.get(method_used, 0) + 1
                
                # Update average analysis time
                analysis_time = time.time() - start_time
                if self.metrics.avg_analysis_time == 0:
                    self.metrics.avg_analysis_time = analysis_time
                else:
                    self.metrics.avg_analysis_time = (self.metrics.avg_analysis_time + analysis_time) / 2
                
                logger.debug(f"Successfully analyzed job {job_id} using {method_used}")
                return analyzed_job
            else:
                logger.warning(f"Analysis failed for job {job_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing job {job_id}: {e}")
            return None
    
    async def _rule_based_analysis(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Perform rule-based analysis on job."""
        try:
            analysis_result = self.rule_analyzer.analyze_job(job)
            
            analyzed_job = job.copy()
            analyzed_job.update(analysis_result)
            
            return analyzed_job
            
        except Exception as e:
            logger.error(f"Rule-based analysis failed: {e}")
            return None
    
    async def _gpu_analysis(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Perform GPU-enhanced analysis on job."""
        try:
            if not self.gpu_analyzer:
                logger.warning("GPU analyzer not available, falling back to rule-based")
                return await self._rule_based_analysis(job)
            
            analysis_result = await self.gpu_analyzer.analyze_job_hybrid(job)
            
            analyzed_job = job.copy()
            analyzed_job.update(analysis_result)
            
            return analyzed_job
            
        except Exception as e:
            logger.error(f"GPU analysis failed: {e}")
            # Fallback to rule-based analysis
            return await self._rule_based_analysis(job)
    
    async def _hybrid_analysis(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Perform hybrid analysis (rule-based + GPU enhancement) on job."""
        try:
            # First, do rule-based analysis
            rule_result = await self._rule_based_analysis(job)
            if not rule_result:
                return None
            
            # Then enhance with GPU if available
            if self.gpu_analyzer:
                try:
                    gpu_enhancement = await self.gpu_analyzer.enhance_analysis(rule_result)
                    if gpu_enhancement:
                        rule_result.update(gpu_enhancement)
                except Exception as e:
                    logger.warning(f"GPU enhancement failed, using rule-based only: {e}")
            
            return rule_result
            
        except Exception as e:
            logger.error(f"Hybrid analysis failed: {e}")
            return None
    
    async def _update_database_and_queue(self, processed_jobs: List[Dict[str, Any]]):
        """
        Update database with analysis results and queue good matches for application.
        
        Args:
            processed_jobs: List of processed job dictionaries
        """
        try:
            queued_count = 0
            
            for job in processed_jobs:
                try:
                    # Update job in database
                    success = self.db.update_job(job.get('id'), job)
                    if success:
                        # Check if job should be queued for application
                        compatibility_score = job.get('compatibility_score', 0)
                        recommendation = job.get('recommendation', 'skip')
                        
                        if (compatibility_score >= self.compatibility_threshold or 
                            recommendation in ['highly_recommend', 'recommend']):
                            
                            # Update status to queued for application
                            job['status'] = 'queued_for_application'
                            self.db.update_job(job.get('id'), job)
                            
                            # Enqueue to application queue
                            await self.application_queue.enqueue_job(job, priority=5)
                            queued_count += 1
                            self.metrics.total_jobs_queued += 1
                    
                except Exception as e:
                    logger.error(f"Error updating job {job.get('id', 'unknown')}: {e}")
                    self.metrics.total_failures += 1
            
            if queued_count > 0:
                console.print(f"[green]📋 Queued {queued_count} jobs for application[/green]")
            
        except Exception as e:
            logger.error(f"Error updating database and queue: {e}")
    
    def _display_results(self):
        """Display processing results."""
        duration = (self.metrics.end_time - self.metrics.start_time).total_seconds()
        
        table = Table(title="Job Processor Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Jobs Processed", str(self.metrics.total_jobs_processed))
        table.add_row("Jobs Analyzed", str(self.metrics.total_jobs_analyzed))
        table.add_row("Jobs Queued for Application", str(self.metrics.total_jobs_queued))
        table.add_row("Failures", str(self.metrics.total_failures))
        table.add_row("Batches Processed", str(self.metrics.batches_processed))
        table.add_row("Success Rate", f"{self.metrics.success_rate:.1f}%")
        table.add_row("Average Analysis Time", f"{self.metrics.avg_analysis_time:.2f}s")
        table.add_row("Average Batch Time", f"{self.metrics.avg_batch_time:.2f}s")
        table.add_row("Total Duration", f"{duration:.1f}s")
        table.add_row("Jobs per Second", f"{self.metrics.total_jobs_processed / max(duration, 1):.1f}")
        
        # Add analysis methods used
        if self.metrics.analysis_methods_used:
            methods_str = ", ".join([f"{method}: {count}" for method, count in self.metrics.analysis_methods_used.items()])
            table.add_row("Analysis Methods Used", methods_str)
        
        console.print(table)
    
    async def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "orchestrator_name": "JobProcessorOrchestrator",
            "profile_name": self.profile_name,
            "batch_size": self.batch_size,
            "analysis_method": self.analysis_method,
            "gpu_enabled": self.gpu_enabled,
            "is_running": self.is_running,
            "metrics": asdict(self.metrics),
            "processing_queue_stats": await self.processing_queue.get_queue_stats(),
            "application_queue_stats": await self.application_queue.get_queue_stats()
        }


# Convenience functions
async def create_job_processor_orchestrator(profile_name: str, batch_size: int = 20) -> JobProcessorOrchestrator:
    """Create a job processor orchestrator."""
    return JobProcessorOrchestrator(profile_name, batch_size)


async def process_jobs_with_orchestrator(profile_name: str, batch_size: int = 20) -> Dict[str, Any]:
    """Process jobs using the job processor orchestrator."""
    orchestrator = JobProcessorOrchestrator(profile_name, batch_size)
    await orchestrator.start()
    
    try:
        # Let it run for a while or until no more jobs
        await asyncio.sleep(30)  # Run for 30 seconds or implement job completion detection
    finally:
        await orchestrator.stop()
        orchestrator._display_results()
    
    return asdict(orchestrator.metrics) 