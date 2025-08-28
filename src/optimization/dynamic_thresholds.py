#!/usr/bin/env python3
"""
Dynamic Threshold Strategy for 2-Phase Processing
Adapts thresholds based on job volume, hardware performance, and quality requirements
"""

import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
from .hardware_detector import get_hardware_info

logger = logging.getLogger(__name__)


@dataclass
class ThresholdConfig:
    phase1_threshold: float      # Minimum score to pass Phase 1
    phase2_batch_size: int       # Optimal batch size for Phase 2
    quality_target: float        # Target quality score (0.0-1.0)
    max_phase2_jobs: int         # Maximum jobs to process in Phase 2
    timeout_seconds: int         # Maximum time for Phase 2 processing


class DynamicThresholdManager:
    """Smart threshold management based on conditions"""
    
    def __init__(self):
        self.hardware_config, self.performance_stats = get_hardware_info()
        
    def calculate_optimal_thresholds(
        self, 
        total_jobs: int,
        user_preferences: Dict[str, float] = None
    ) -> ThresholdConfig:
        """Calculate optimal thresholds based on job volume and hardware"""
        
        # Default user preferences
        if user_preferences is None:
            user_preferences = {
                "speed_priority": 0.6,      # 0.0 = quality focus, 1.0 = speed focus
                "quality_minimum": 0.4,     # Minimum acceptable quality
                "max_processing_time": 60   # Maximum seconds to spend
            }
        
        # Base thresholds by job volume
        if total_jobs >= 200:
            # High volume: Be more selective
            base_threshold = 0.40
            max_phase2_ratio = 0.15  # Process top 15%
            quality_target = 0.75
        elif total_jobs >= 100:
            # Medium-high volume: Balanced approach
            base_threshold = 0.30
            max_phase2_ratio = 0.25  # Process top 25%
            quality_target = 0.70
        elif total_jobs >= 50:
            # Medium volume: Standard approach
            base_threshold = 0.25
            max_phase2_ratio = 0.40  # Process top 40%
            quality_target = 0.65
        elif total_jobs >= 20:
            # Low-medium volume: More permissive
            base_threshold = 0.20
            max_phase2_ratio = 0.60  # Process top 60%
            quality_target = 0.60
        else:
            # Low volume: Process most jobs
            base_threshold = 0.15
            max_phase2_ratio = 0.80  # Process top 80%
            quality_target = 0.55
        
        # Adjust based on hardware performance
        hardware_multiplier = self._get_hardware_multiplier()
        adjusted_threshold = base_threshold * hardware_multiplier
        
        # Adjust based on user preferences
        speed_priority = user_preferences.get("speed_priority", 0.6)
        if speed_priority > 0.7:
            # User wants speed: Raise threshold, reduce Phase 2 load
            adjusted_threshold *= 1.2
            max_phase2_ratio *= 0.8
        elif speed_priority < 0.3:
            # User wants quality: Lower threshold, increase Phase 2 load
            adjusted_threshold *= 0.8
            max_phase2_ratio *= 1.2
        
        # Calculate final values
        max_phase2_jobs = min(
            int(total_jobs * max_phase2_ratio),
            self._get_max_phase2_capacity()
        )
        
        return ThresholdConfig(
            phase1_threshold=max(0.1, min(0.6, adjusted_threshold)),
            phase2_batch_size=self.hardware_config.optimal_batch_size,
            quality_target=quality_target,
            max_phase2_jobs=max_phase2_jobs,
            timeout_seconds=self._calculate_timeout(max_phase2_jobs)
        )
    
    def _get_hardware_multiplier(self) -> float:
        """Get threshold multiplier based on hardware performance"""
        if self.hardware_config.performance_tier == "high":
            # High-end hardware: Can afford to process more jobs
            return 0.85
        elif self.hardware_config.performance_tier == "medium":
            # Medium hardware: Balanced approach
            return 1.0
        else:
            # Low-end hardware: Be more selective
            return 1.3
    
    def _get_max_phase2_capacity(self) -> int:
        """Calculate maximum Phase 2 jobs based on hardware"""
        jobs_per_second = self.performance_stats.get("estimated_jobs_per_second", 2.0)
        max_time = 60  # Maximum 60 seconds for Phase 2
        return int(jobs_per_second * max_time)
    
    def _calculate_timeout(self, phase2_jobs: int) -> int:
        """Calculate appropriate timeout for Phase 2 processing"""
        jobs_per_second = self.performance_stats.get("estimated_jobs_per_second", 2.0)
        estimated_time = phase2_jobs / jobs_per_second
        
        # Add 50% buffer for safety
        return int(estimated_time * 1.5)
    
    def should_enable_phase2(self, total_jobs: int) -> bool:
        """Determine if Phase 2 should be enabled at all"""
        
        # Always enable for small batches (user likely wants quality)
        if total_jobs <= 10:
            return True
        
        # Check if hardware can handle it efficiently
        if self.hardware_config.performance_tier == "low" and total_jobs > 50:
            logger.warning(f"Phase 2 may be slow for {total_jobs} jobs on this hardware")
            return False
        
        # Check if PyTorch is available
        if self.hardware_config.device == "cpu" and "PyTorch not available" in self.hardware_config.device_name:
            logger.warning("Phase 2 disabled: PyTorch not available")
            return False
        
        return True
    
    def get_performance_estimate(self, config: ThresholdConfig) -> Dict[str, float]:
        """Estimate processing time and quality for given configuration"""
        
        # Phase 1 estimates (fast)
        phase1_time = 0.01 * config.max_phase2_jobs  # ~10ms per job
        
        # Phase 2 estimates 
        jobs_per_second = self.performance_stats.get("estimated_jobs_per_second", 2.0)
        phase2_time = config.max_phase2_jobs / jobs_per_second
        
        total_time = phase1_time + phase2_time
        
        # Quality estimate based on threshold
        quality_estimate = min(0.95, config.phase1_threshold + 0.3)
        
        return {
            "estimated_total_time": total_time,
            "estimated_phase1_time": phase1_time,
            "estimated_phase2_time": phase2_time,
            "estimated_quality": quality_estimate,
            "phase2_jobs": config.max_phase2_jobs
        }


# Usage example function
def get_optimal_processing_config(
    total_jobs: int,
    user_preferences: Dict[str, float] = None
) -> Tuple[ThresholdConfig, Dict[str, float]]:
    """Get optimal processing configuration for given job count"""
    
    manager = DynamicThresholdManager()
    
    if not manager.should_enable_phase2(total_jobs):
        # Phase 1 only configuration
        return ThresholdConfig(
            phase1_threshold=0.1,
            phase2_batch_size=0,
            quality_target=0.5,
            max_phase2_jobs=0,
            timeout_seconds=0
        ), {"estimated_total_time": total_jobs * 0.01, "phase2_enabled": False}
    
    config = manager.calculate_optimal_thresholds(total_jobs, user_preferences)
    estimates = manager.get_performance_estimate(config)
    
    return config, estimates
