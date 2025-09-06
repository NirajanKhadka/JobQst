#!/usr/bin/env python3
"""Simple performance monitoring"""

import time
import psutil
import sys

def monitor_performance():
    """Monitor system performance during pipeline execution"""
    print("📊 PERFORMANCE MONITORING")
    print("=" * 40)
    
    # CPU and Memory info
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    print(f"CPU Usage: {cpu_percent:.1f}%")
    print(f"Memory Usage: {memory.percent:.1f}%")
    print(f"Available Memory: {memory.available / (1024**3):.1f}GB")
    
    # GPU info if available
    try:
        import torch
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            gpu_allocated = torch.cuda.memory_allocated(0) / (1024**3)
            gpu_cached = torch.cuda.memory_reserved(0) / (1024**3)
            
            print(f"GPU Memory Total: {gpu_memory:.1f}GB")
            print(f"GPU Memory Allocated: {gpu_allocated:.1f}GB")
            print(f"GPU Memory Cached: {gpu_cached:.1f}GB")
    except:
        pass
    
    print("\n✅ System ready for high-performance processing!")

if __name__ == "__main__":
    monitor_performance()