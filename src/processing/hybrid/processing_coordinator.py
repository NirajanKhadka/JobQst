"""
Processing Coordinator

Coordinates rule-based and AI-powered job processing with intelligent
fallback strategies and performance optimization.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from ..extractors import (
    RuleBasedExtractor,
    RuleBasedExtractionResult,
    get_rule_based_extractor
)

logger = logging.getLogger(__name__)


class ProcessingStrategy(Enum):
    """Processing strategy options."""
    RULE_BASED_ONLY = "rule_based_only"
    AI_ONLY = "ai_only"
    HYBRID_FALLBACK = "hybrid_fallback"  # Rule-based first, AI if needed
    HYBRID_PARALLEL = "hybrid_parallel"  # Both in parallel


@dataclass
class ProcessingResult:
    """Comprehensive processing result from coordinated processing."""
    # Core extraction result
    extraction_result: RuleBasedExtractionResult
    
    # Processing metadata
    strategy_used: ProcessingStrategy = ProcessingStrategy.RULE_BASED_ONLY
    processing_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    
    # Performance metrics
    rule_based_time: float = 0.0
    ai_processing_time: float = 0.0
    fallback_triggered: bool = False
    
    # Quality metrics
    confidence_score: float = 0.0
    quality_indicators: Dict[str, bool] = field(default_factory=dict)


class JobProcessingCoordinator:
    """
    Central coordinator for job processing that integrates rule-based and AI approaches.
    Implements intelligent fallback strategies and performance optimization.
    """
    
    def __init__(self, 
                 strategy: ProcessingStrategy = ProcessingStrategy.HYBRID_FALLBACK,
                 confidence_threshold: float = 0.7,
                 search_client: Optional[Any] = None):
        """
        Initialize the processing coordinator.
        
        Args:
            strategy: Processing strategy to use
            confidence_threshold: Minimum confidence for rule-based success
            search_client: Optional web search client for validation
        """
        self.strategy = strategy
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize processors
        self.rule_based_extractor = get_rule_based_extractor(search_client)
        self.ai_processor = None  # Will be initialized when AI module is ready
        
        # Performance tracking
        self.processing_stats = {
            'total_jobs': 0,
            'rule_based_success': 0,
            'ai_fallback_used': 0,
            'average_processing_time': 0.0
        }
        
        self.logger.info(f"ProcessingCoordinator initialized with strategy: {strategy}")
    
    def process_job(self, job_data: Dict[str, Any]) -> ProcessingResult:
        """
        Process a single job using the configured strategy.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            ProcessingResult: Comprehensive processing result
        """
        start_time = time.time()
        
        try:
            if self.strategy == ProcessingStrategy.RULE_BASED_ONLY:
                return self._process_rule_based_only(job_data, start_time)
            elif self.strategy == ProcessingStrategy.HYBRID_FALLBACK:
                return self._process_hybrid_fallback(job_data, start_time)
            else:
                # For now, fallback to rule-based for unsupported strategies
                self.logger.warning(f"Strategy {self.strategy} not fully implemented, using rule-based")
                return self._process_rule_based_only(job_data, start_time)
                
        except Exception as e:
            self.logger.error(f"Critical error in process_job: {e}")
            return ProcessingResult(
                extraction_result=RuleBasedExtractionResult(),
                strategy_used=self.strategy,
                processing_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
        finally:
            self.processing_stats['total_jobs'] += 1
    
    def _process_rule_based_only(self, job_data: Dict[str, Any], start_time: float) -> ProcessingResult:
        """Process using rule-based extraction only."""
        rule_start = time.time()
        
        # Extract using rule-based approach
        extraction_result = self.rule_based_extractor.extract_job_data(job_data)
        
        rule_time = time.time() - rule_start
        total_time = time.time() - start_time
        
        # Evaluate quality
        quality_indicators = self._evaluate_quality(extraction_result)
        success = extraction_result.overall_confidence >= 0.3  # Lower threshold for rule-based only
        
        if success:
            self.processing_stats['rule_based_success'] += 1
        
        return ProcessingResult(
            extraction_result=extraction_result,
            strategy_used=ProcessingStrategy.RULE_BASED_ONLY,
            processing_time=total_time,
            success=success,
            rule_based_time=rule_time,
            confidence_score=extraction_result.overall_confidence,
            quality_indicators=quality_indicators
        )
    
    def _process_hybrid_fallback(self, job_data: Dict[str, Any], start_time: float) -> ProcessingResult:
        """Process using hybrid strategy with AI fallback."""
        # First try rule-based processing
        rule_start = time.time()
        extraction_result = self.rule_based_extractor.extract_job_data(job_data)
        rule_time = time.time() - rule_start
        
        # Check if rule-based result meets threshold
        if extraction_result.overall_confidence >= self.confidence_threshold:
            # Rule-based success, no need for AI fallback
            total_time = time.time() - start_time
            quality_indicators = self._evaluate_quality(extraction_result)
            
            self.processing_stats['rule_based_success'] += 1
            
            return ProcessingResult(
                extraction_result=extraction_result,
                strategy_used=ProcessingStrategy.HYBRID_FALLBACK,
                processing_time=total_time,
                success=True,
                rule_based_time=rule_time,
                confidence_score=extraction_result.overall_confidence,
                quality_indicators=quality_indicators
            )
        else:
            # Rule-based didn't meet threshold, would trigger AI fallback
            # For now, return rule-based result with fallback flag
            total_time = time.time() - start_time
            quality_indicators = self._evaluate_quality(extraction_result)
            
            self.logger.info(f"Rule-based confidence {extraction_result.overall_confidence:.2f} "
                           f"below threshold {self.confidence_threshold}, AI fallback would be triggered")
            
            # TODO: Implement AI fallback when AI processor is ready
            self.processing_stats['ai_fallback_used'] += 1
            
            return ProcessingResult(
                extraction_result=extraction_result,
                strategy_used=ProcessingStrategy.HYBRID_FALLBACK,
                processing_time=total_time,
                success=extraction_result.overall_confidence >= 0.3,  # Lower threshold
                rule_based_time=rule_time,
                fallback_triggered=True,
                confidence_score=extraction_result.overall_confidence,
                quality_indicators=quality_indicators
            )
    
    def _evaluate_quality(self, result: RuleBasedExtractionResult) -> Dict[str, bool]:
        """Evaluate the quality of extraction results."""
        return {
            'has_title': bool(result.title),
            'has_company': bool(result.company),
            'has_location': bool(result.location),
            'has_skills': bool(result.skills),
            'has_salary': bool(result.salary_range),
            'web_validated': bool(result.web_validated_fields),
            'high_confidence': result.overall_confidence >= 0.8,
            'medium_confidence': result.overall_confidence >= 0.5
        }
    
    def process_batch(self, jobs: List[Dict[str, Any]]) -> List[ProcessingResult]:
        """
        Process a batch of jobs efficiently.
        
        Args:
            jobs: List of job data dictionaries
            
        Returns:
            List of ProcessingResult objects
        """
        self.logger.info(f"Processing batch of {len(jobs)} jobs")
        
        results = []
        batch_start_time = time.time()
        
        for i, job_data in enumerate(jobs):
            try:
                result = self.process_job(job_data)
                results.append(result)
                
                # Log progress every 10 jobs
                if (i + 1) % 10 == 0:
                    self.logger.info(f"Processed {i + 1}/{len(jobs)} jobs")
                    
            except Exception as e:
                self.logger.error(f"Error processing job {i}: {e}")
                results.append(ProcessingResult(
                    extraction_result=RuleBasedExtractionResult(),
                    success=False,
                    error_message=str(e)
                ))
        
        batch_time = time.time() - batch_start_time
        avg_time = batch_time / len(jobs) if jobs else 0
        
        self.logger.info(f"Batch processing completed in {batch_time:.2f}s "
                        f"(avg: {avg_time:.3f}s per job)")
        
        return results
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        return {
            **self.processing_stats,
            'rule_based_success_rate': (
                self.processing_stats['rule_based_success'] / 
                max(self.processing_stats['total_jobs'], 1)
            ),
            'ai_fallback_rate': (
                self.processing_stats['ai_fallback_used'] / 
                max(self.processing_stats['total_jobs'], 1)
            )
        }
    
    def update_strategy(self, new_strategy: ProcessingStrategy):
        """Update the processing strategy."""
        old_strategy = self.strategy
        self.strategy = new_strategy
        self.logger.info(f"Strategy updated from {old_strategy} to {new_strategy}")
    
    def set_confidence_threshold(self, threshold: float):
        """Update the confidence threshold for hybrid processing."""
        if 0.0 <= threshold <= 1.0:
            old_threshold = self.confidence_threshold
            self.confidence_threshold = threshold
            self.logger.info(f"Confidence threshold updated from {old_threshold} to {threshold}")
        else:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")


# Convenience functions
def create_coordinator(strategy: ProcessingStrategy = ProcessingStrategy.HYBRID_FALLBACK,
                      confidence_threshold: float = 0.7,
                      search_client: Optional[Any] = None) -> JobProcessingCoordinator:
    """Create a configured processing coordinator."""
    return JobProcessingCoordinator(strategy, confidence_threshold, search_client)


def process_single_job(job_data: Dict[str, Any],
                      strategy: ProcessingStrategy = ProcessingStrategy.RULE_BASED_ONLY) -> ProcessingResult:
    """Process a single job with default coordinator."""
    coordinator = create_coordinator(strategy)
    return coordinator.process_job(job_data)
