#!/usr/bin/env python3
"""
Smart Hardware Detection for Cross-Platform Optimization
Supports Windows (CUDA), Mac (MPS), and CPU-only systems
"""

import platform
import logging
from typing import Tuple, Dict, Any
from dataclasses import dataclass

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

logger = logging.getLogger(__name__)

@dataclass
class HardwareConfig:
    device: str
    device_name: str
    optimal_batch_size: int
    max_memory_gb: float
    performance_tier: str  # "high", "medium", "low"
    phase2_timeout: int    # seconds per batch
    
class HardwareDetector:
    """Smart hardware detection and optimization"""
    
    @staticmethod
    def detect_optimal_config() -> HardwareConfig:
        """Detect the best hardware configuration for this system"""
        
        if not TORCH_AVAILABLE:
            return HardwareConfig(
                device="cpu", 
                device_name="CPU Only (PyTorch not available)",
                optimal_batch_size=4,
                max_memory_gb=8.0,
                performance_tier="low",
                phase2_timeout=30
            )
        
        # GPU Detection with prioritization
        if torch.cuda.is_available():
            return HardwareDetector._configure_cuda()
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return HardwareDetector._configure_mps()
        else:
            return HardwareDetector._configure_cpu()
    
    @staticmethod
    def _configure_cuda() -> HardwareConfig:
        """Configure for NVIDIA GPU (Windows/Linux)"""
        try:
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
            gpu_name = torch.cuda.get_device_name(0)
            
            # High-end GPU (RTX 3080+, A100, etc.)
            if gpu_memory >= 10:
                batch_size = 32
                tier = "high"
                timeout = 10
            # Mid-range GPU (GTX 1660, RTX 3060, etc.)
            elif gpu_memory >= 6:
                batch_size = 16
                tier = "medium"
                timeout = 15
            # Low-end GPU
            else:
                batch_size = 8
                tier = "medium"
                timeout = 20
                
            return HardwareConfig(
                device="cuda",
                device_name=f"NVIDIA {gpu_name} ({gpu_memory:.1f}GB)",
                optimal_batch_size=batch_size,
                max_memory_gb=gpu_memory * 0.8,  # 80% usage limit
                performance_tier=tier,
                phase2_timeout=timeout
            )
        except Exception as e:
            logger.warning(f"CUDA detection failed: {e}")
            return HardwareDetector._configure_cpu()
    
    @staticmethod
    def _configure_mps() -> HardwareConfig:
        """Configure for Mac Metal Performance Shaders"""
        try:
            # Mac MPS - optimized for Apple Silicon
            system_info = platform.processor()
            is_apple_silicon = "arm" in system_info.lower() or "apple" in system_info.lower()
            
            if is_apple_silicon:
                # M1 Pro/Max/Ultra have more memory and cores
                batch_size = 12
                memory = 16.0
                tier = "medium"
                timeout = 12
            else:
                # Regular M1 or Intel Mac
                batch_size = 8
                memory = 8.0
                tier = "medium"  
                timeout = 15
                
            return HardwareConfig(
                device="mps",
                device_name=f"Mac Metal GPU ({system_info})",
                optimal_batch_size=batch_size,
                max_memory_gb=memory,
                performance_tier=tier,
                phase2_timeout=timeout
            )
        except Exception as e:
            logger.warning(f"MPS detection failed: {e}")
            return HardwareDetector._configure_cpu()
    
    @staticmethod
    def _configure_cpu() -> HardwareConfig:
        """Configure for CPU-only processing"""
        import multiprocessing
        import psutil
        
        cpu_count = multiprocessing.cpu_count()
        available_memory = psutil.virtual_memory().available / (1024**3)  # GB
        
        # Optimize batch size based on CPU cores and memory
        if cpu_count >= 8 and available_memory >= 16:
            batch_size = 8
            tier = "medium"
            timeout = 25
        elif cpu_count >= 4 and available_memory >= 8:
            batch_size = 4
            tier = "low"
            timeout = 35
        else:
            batch_size = 2
            tier = "low"
            timeout = 45
            
        return HardwareConfig(
            device="cpu",
            device_name=f"CPU ({cpu_count} cores, {available_memory:.1f}GB RAM)",
            optimal_batch_size=batch_size,
            max_memory_gb=available_memory * 0.6,  # 60% usage limit
            performance_tier=tier,
            phase2_timeout=timeout
        )
    
    @staticmethod
    def benchmark_performance() -> Dict[str, float]:
        """Quick performance benchmark for the current hardware"""
        config = HardwareDetector.detect_optimal_config()
        
        if not TORCH_AVAILABLE:
            return {"cpu_score": 1.0, "estimated_jobs_per_second": 2.0}
        
        # Simple tensor operations benchmark
        import time
        device = torch.device(config.device)
        
        try:
            # Create test tensors
            start_time = time.time()
            for _ in range(10):
                x = torch.randn(100, 768, device=device)
                y = torch.randn(768, 100, device=device)
                z = torch.matmul(x, y)
                if device.type == "cuda":
                    torch.cuda.synchronize()
            
            benchmark_time = time.time() - start_time
            score = 10.0 / benchmark_time  # Higher is better
            
            # Estimate jobs per second for Phase 2
            if config.performance_tier == "high":
                jobs_per_second = score * 5
            elif config.performance_tier == "medium":
                jobs_per_second = score * 3
            else:
                jobs_per_second = score * 1
                
            return {
                "benchmark_score": score,
                "estimated_jobs_per_second": jobs_per_second,
                "benchmark_time": benchmark_time
            }
            
        except Exception as e:
            logger.warning(f"Benchmark failed: {e}")
            return {"benchmark_score": 1.0, "estimated_jobs_per_second": 2.0}

# Global instance for easy access
hardware_config = HardwareDetector.detect_optimal_config()
performance_stats = HardwareDetector.benchmark_performance()

def get_hardware_info() -> Tuple[HardwareConfig, Dict[str, float]]:
    """Get hardware configuration and performance stats"""
    return hardware_config, performance_stats

