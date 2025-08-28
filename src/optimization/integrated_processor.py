#!/usr/bin/env python3
"""
Integrated Optimization for Two-Stage Processor
Respects existing worker architecture while adding batch processing
optimization
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Tuple

# Import existing components
from src.analysis.two_stage_processor import (
    TwoStageJobProcessor, Stage1Result, Stage2Result, TwoStageResult
)
from src.optimization.hardware_detector import get_hardware_info
from src.optimization.dynamic_thresholds import get_optimal_processing_config
from src.optimization.batch_processor import BatchProcessor

from rich.console import Console
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
)

console = Console()
logger = logging.getLogger(__name__)


class OptimizedTwoStageProcessor(TwoStageJobProcessor):
    """
    Optimized version of TwoStageJobProcessor that maintains compatibility
    while adding batch processing and cross-platform optimizations
    """
    
    def __init__(
        self,
        user_profile: Dict[str, Any],
        cpu_workers: int = None,
        max_concurrent_stage2: int = None
    ):
        # Get hardware configuration for optimal defaults
        self.hardware_config, self.performance_stats = get_hardware_info()
        
        # Set optimal defaults based on hardware if not specified
        if cpu_workers is None:
            # Cap workers based on hardware batch size
            cpu_workers = min(
                10, max(4, self.hardware_config.optimal_batch_size)
            )
        
        if max_concurrent_stage2 is None:
            # Dynamic concurrency based on hardware performance
            if self.hardware_config.performance_tier == "high":
                max_concurrent_stage2 = 4
            elif self.hardware_config.performance_tier == "medium":
                max_concurrent_stage2 = 2
            else:
                max_concurrent_stage2 = 1
        
        # Initialize parent class with optimized parameters
        super().__init__(user_profile, cpu_workers, max_concurrent_stage2)
        
        # Add batch processor for Stage 2 optimization
        self.batch_processor = None
        if self.stage2_processor is not None:
            try:
                self.batch_processor = BatchProcessor(user_profile)
                console.print(
                    "[green]✅ Batch processor initialized for "
                    f"{self.hardware_config.device_name}[/green]"
                )
            except Exception as e:
                logger.warning(f"Batch processor initialization failed: {e}")
                console.print(
                    "[yellow]⚠️ Falling back to individual processing[/yellow]"
                )
        
        # Display optimization info
        console.print(
            "[bold blue]🚀 Optimized Two-Stage Processor Initialized"
            "[/bold blue]"
        )
        console.print(
            f"[cyan]   Hardware: {self.hardware_config.device_name}[/cyan]"
        )
        console.print(f"[cyan]   Stage 1 Workers: {cpu_workers}[/cyan]")
        console.print(
            f"[cyan]   Stage 2 Concurrency: {max_concurrent_stage2}[/cyan]"
        )
        batch_status = "Enabled" if self.batch_processor else "Disabled"
        console.print(
            f"[cyan]   Batch Processing: {batch_status}[/cyan]"
        )
    
    async def process_jobs(
        self, jobs: List[Dict[str, Any]]
    ) -> List[TwoStageResult]:
        """
        Enhanced job processing with dynamic thresholds and batch optimization
        Maintains compatibility with existing worker architecture
        """
        total_start_time = time.time()
        
        # Get optimal configuration for this job batch
        config, estimates = get_optimal_processing_config(
            len(jobs),
            user_preferences={
                "speed_priority": 0.6,  # Default balanced approach
                "quality_minimum": 0.4,
                "max_processing_time": 60,
            },
        )
        
        console.print(
            f"\n[bold blue]🎯 Processing {len(jobs)} jobs through optimized "
            "two-stage pipeline[/bold blue]"
        )
        console.print(
            f"[cyan]   Estimated time: "
            f"{estimates.get('estimated_total_time', 'unknown'):.1f}s[/cyan]"
        )
        console.print(
            f"[cyan]   Phase 1 threshold: {config.phase1_threshold:.2f}[/cyan]"
        )
        console.print(
            f"[cyan]   Max Phase 2 jobs: {config.max_phase2_jobs}[/cyan]"
        )
        
        # Stage 1: CPU-bound fast processing (unchanged - already optimized)
        stage1_results = self.stage1_processor.process_jobs_batch(jobs)
        
        # Apply dynamic filtering based on optimized thresholds
        passed_jobs: List[Tuple[Dict[str, Any], Stage1Result, int]] = []
        for idx, (job, result) in enumerate(zip(jobs, stage1_results)):
            # Use dynamic threshold instead of fixed basic filter
            if (
                result.passes_basic_filter
                and result.basic_compatibility >= config.phase1_threshold
                and len(passed_jobs) < config.max_phase2_jobs
            ):
                passed_jobs.append((job, result, idx))
        
        console.print(
            f"[yellow]🔄 Stage 2: Processing {len(passed_jobs)} jobs "
            f"(threshold: {config.phase1_threshold:.2f})[/yellow]"
        )
        
        final_results: List[TwoStageResult] = []
        
        # Decide on processing strategy
        if self.stage2_processor is None:
            # No Stage 2 available - use Stage 1 results only
            final_results = self._create_stage1_only_results(
                jobs, stage1_results
            )
        elif self.batch_processor is not None and len(passed_jobs) >= 4:
            # Use batch processing for efficiency (4+ jobs threshold)
            final_results = await self._process_with_batch_optimization(
                jobs, stage1_results, passed_jobs, config
            )
        else:
            # Fall back to individual processing (existing logic)
            final_results = await self._process_with_individual_workers(
                jobs, stage1_results, passed_jobs
            )
        
        # Performance reporting
        total_time = time.time() - total_start_time
        console.print(
            "\n[bold green]✅ Processing completed in "
            f"{total_time:.1f}s[/bold green]"
        )
        console.print(
            f"[green]   Jobs processed: {len(final_results)}[/green]"
        )
        console.print(f"[green]   Stage 2 jobs: {len(passed_jobs)}[/green]")
        console.print(
            "[green]   Performance: "
            f"{len(jobs)/total_time:.1f} jobs/second[/green]"
        )
        
        return final_results
    
    async def _process_with_batch_optimization(
        self,
        jobs: List[Dict[str, Any]],
        stage1_results: List[Stage1Result],
        passed_jobs: List[Tuple[Dict[str, Any], Stage1Result, int]],
        config: Any
    ) -> List[TwoStageResult]:
        """Process using optimized batch processing"""
        
        console.print(
            f"[cyan]🚀 Using batch processing ("
            f"{config.phase2_batch_size} jobs/batch)[/cyan]"
        )
        
        # Prepare jobs for batch processing
        jobs_with_stage1 = [(job, s1) for job, s1, _ in passed_jobs]
        
        try:
            # Use batch processor
            stage2_batch_results = await self.batch_processor.\
                process_jobs_batch(
                    jobs_with_stage1,
                    {"batch_size": config.phase2_batch_size},
                )
            
            # Combine results
            final_results = []
            stage2_index = 0
            
            for idx, (job, s1) in enumerate(zip(jobs, stage1_results)):
                if any(
                    original_idx == idx for _, _, original_idx in passed_jobs
                ):
                    # Job was processed in Stage 2
                    if stage2_index < len(stage2_batch_results):
                        s2_data = stage2_batch_results[stage2_index]
                        s2 = self._convert_batch_result_to_stage2(s2_data)
                        combined = self._combine_results(job, s1, s2, idx)
                        stage2_index += 1
                    else:
                        # Fallback if batch processing had issues
                        combined = self._create_stage1_only_result(
                            job, s1, idx
                        )
                else:
                    # Job only went through Stage 1
                    combined = self._create_stage1_only_result(job, s1, idx)
                
                final_results.append(combined)
            
            return final_results
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            console.print(
                "[red]❌ Batch processing failed, falling back to "
                "individual processing[/red]"
            )
            # Fall back to individual processing
            return await self._process_with_individual_workers(
                jobs, stage1_results, passed_jobs
            )
    
    async def _process_with_individual_workers(
        self,
        jobs: List[Dict[str, Any]],
        stage1_results: List[Stage1Result],
        passed_jobs: List[Tuple[Dict[str, Any], Stage1Result, int]]
    ) -> List[TwoStageResult]:
        """Process using existing individual worker logic (fallback)"""
        
        console.print(
            "[cyan]⚙️ Using individual processing (semaphore: "
            f"{self.max_concurrent_stage2})[/cyan]"
        )
        
        # Use existing semaphore-based individual processing
        final_results: List[TwoStageResult] = []
        semaphore = asyncio.Semaphore(self.max_concurrent_stage2)

        async def process_single(
            idx: int, job: Dict[str, Any], s1: Stage1Result
        ) -> TwoStageResult:
            async with semaphore:
                # Use existing individual processing logic
                s2: Stage2Result = await asyncio.to_thread(
                    self.stage2_processor.process_job_semantic, job, s1
                )
                combined = self._combine_results(job, s1, s2, idx)
                return combined

        # Create tasks for passed jobs and keep original index in result
        async def process_single_wrapped(
            orig_idx: int,
            job: Dict[str, Any],
            s1: Stage1Result,
        ) -> Tuple[int, TwoStageResult]:
            res = await process_single(orig_idx, job, s1)
            return orig_idx, res

        tasks: List[asyncio.Task] = []
        for (job, s1, original_idx) in passed_jobs:
            t = asyncio.create_task(
                process_single_wrapped(original_idx, job, s1),
                name=f"stage2_job_{original_idx}"
            )
            tasks.append(t)
        
        # Process with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task(
                "Stage 2 Processing...", total=len(tasks)
            )
            stage2_lookup: Dict[int, TwoStageResult] = {}
            for fut in asyncio.as_completed(tasks):
                try:
                    original_idx, result = await fut
                    stage2_lookup[original_idx] = result
                    progress.update(task, advance=1)
                except Exception as e:
                    logger.error(
                        f"Individual processing task failed: {e}"
                    )
                    progress.update(task, advance=1)
        
        # Combine all results (Stage 1 + Stage 2)
        for idx, (job, s1) in enumerate(zip(jobs, stage1_results)):
            if idx in stage2_lookup:
                final_results.append(stage2_lookup[idx])
            else:
                # Create Stage 1 only result
                combined = self._create_stage1_only_result(job, s1, idx)
                final_results.append(combined)
        
        return final_results
    
    def _create_stage1_only_results(
        self,
        jobs: List[Dict[str, Any]],
        stage1_results: List[Stage1Result],
    ) -> List[TwoStageResult]:
        """Create results when Stage 2 is not available"""
        
        final_results = []
        for idx, (job, s1) in enumerate(zip(jobs, stage1_results)):
            combined = self._create_stage1_only_result(job, s1, idx)
            final_results.append(combined)
        
        return final_results
    
    def _create_stage1_only_result(
        self,
        job: Dict[str, Any],
        s1: Stage1Result,
        idx: int,
    ) -> TwoStageResult:
        """Create a TwoStageResult from Stage 1 only"""
        
        from src.analysis.two_stage_processor import TwoStageResult
        
        return TwoStageResult(
            job_id=job.get('id', f'job_{idx}'),
            url=job.get('url', ''),
            job_data=job,
            stage1=s1,
            stage2=None,
            final_compatibility=s1.basic_compatibility,
            final_skills=s1.basic_skills,
            final_requirements=s1.basic_requirements,
            recommendation=(
                "review" if s1.basic_compatibility >= 0.4 else "skip"
            ),
            total_processing_time=s1.processing_time,
            stages_completed=1,
            processing_method="stage1_only"
        )
    
    def _convert_batch_result_to_stage2(
        self, batch_result: Dict[str, Any]
    ) -> Stage2Result:
        """Convert batch processing result to Stage2Result format"""
        
        from src.analysis.two_stage_processor import Stage2Result
        
        return Stage2Result(
            semantic_skills=batch_result.get('semantic_skills', []),
            contextual_requirements=[],  # Can be enhanced
            semantic_compatibility=batch_result.get(
                'semantic_compatibility', 0.5
            ),
            job_sentiment=batch_result.get('job_sentiment', 'neutral'),
            skill_embeddings=batch_result.get('skill_embeddings'),
            contextual_understanding=batch_result.get(
                'contextual_understanding', ''
            ),
            extracted_benefits=[],  # Can be enhanced
            company_culture="unknown",  # Can be enhanced
            processing_time=batch_result.get('processing_time', 0.0),
            gpu_memory_used=0.0
        )


# Factory function for easy integration
def create_optimized_processor(
    user_profile: Dict[str, Any],
    force_individual: bool = False,
    **kwargs
) -> TwoStageJobProcessor:
    """
    Factory function to create either optimized or original processor
    
    Args:
        user_profile: User profile configuration
        force_individual: Force individual processing (disable batching)
        **kwargs: Additional arguments passed to processor
    
    Returns:
        TwoStageJobProcessor instance (optimized or original)
    """
    
    if force_individual:
        # Return original processor for compatibility
        console.print(
            "[yellow]⚠️ Using individual processing mode "
            "(compatibility)[/yellow]"
        )
        return TwoStageJobProcessor(user_profile, **kwargs)
    
    try:
        # Return optimized processor
        return OptimizedTwoStageProcessor(user_profile, **kwargs)
    except Exception as e:
        logger.error(f"Optimized processor initialization failed: {e}")
        console.print(
            "[red]❌ Optimization failed, falling back to "
            "original processor[/red]"
        )
        return TwoStageJobProcessor(user_profile, **kwargs)
