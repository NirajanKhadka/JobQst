#!/usr/bin/env python3
"""
Optimization Configuration Utility
Automatically detects system capabilities and configures optimal settings
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel

from src.optimization.hardware_detector import get_hardware_info

console = Console()
logger = logging.getLogger(__name__)


class OptimizationConfigurator:
    """Auto-configure optimization settings based on system capabilities"""
    
    def __init__(self, config_path: str = "config/optimization_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
    def detect_and_configure(
        self, force_reconfigure: bool = False
    ) -> Dict[str, Any]:
        """
        Detect system capabilities and create optimal configuration
        
        Args:
            force_reconfigure: Force reconfiguration even if config exists
            
        Returns:
            Dictionary with optimal configuration settings
        """
        # Check if config already exists
        if self.config_path.exists() and not force_reconfigure:
            console.print(
                "[cyan]📋 Loading existing optimization configuration...[/cyan]"
            )
            return self._load_config()
        
        console.print(
            "[bold blue]🔍 Detecting System Capabilities...[/bold blue]"
        )
        
        # Detect hardware
        hw_info = get_hardware_info()
        # get_hardware_info returns a tuple (HardwareConfig, performance_stats)
        if isinstance(hw_info, tuple):
            hardware_info, _ = hw_info
        else:
            hardware_info = hw_info
        
        console.print("[green]✅ Hardware Detection Complete[/green]")
        try:
            console.print(
                f"[cyan]   Device: {hardware_info.device_name}[/cyan]"
            )
        except Exception:
            console.print("[yellow]   Device: Unknown[/yellow]")
        try:
            mem_gb = getattr(hardware_info, 'max_memory_gb', 0.0)
            console.print(f"[cyan]   Memory: {mem_gb:.1f}GB[/cyan]")
        except Exception:
            console.print("[yellow]   Memory: Unknown[/yellow]")
        try:
            tier = getattr(hardware_info, 'performance_tier', 'unknown')
            console.print(f"[cyan]   Performance Tier: {tier}[/cyan]")
        except Exception:
            pass
        
        # Generate optimal configuration
        config = self._generate_optimal_config(hardware_info)
        
        # Save configuration
        self._save_config(config)
        
        # Display configuration
        self._display_config(config)
        
        return config
    
    def _generate_optimal_config(self, hardware_info) -> Dict[str, Any]:
        """Generate optimal configuration based on hardware"""
        
        # Base configuration
        config = {
            "hardware": {
                "device": hardware_info.device,
                "device_name": hardware_info.device_name,
                "memory_gb": hardware_info.max_memory_gb,
                "performance_tier": hardware_info.performance_tier,
                "optimal_batch_size": hardware_info.optimal_batch_size
            },
            "processing": {
                "enable_optimization": True,
                "enable_batch_processing": hardware_info.device == "cuda",
                "cpu_workers": self._get_optimal_cpu_workers(hardware_info),
                "max_concurrent_stage2": self._get_optimal_stage2_concurrency(
                    hardware_info
                ),
                "batch_size": hardware_info.optimal_batch_size,
                "fallback_to_individual": True
            },
            "thresholds": {
                "phase1_threshold": 0.15,  # Will be dynamic
                "max_phase2_jobs": 20,     # Will be dynamic
                "compatibility_apply": 0.7,
                "compatibility_review": 0.4
            },
            "performance": {
                "target_jobs_per_second": self._get_target_performance(
                    hardware_info
                ),
                "max_processing_time": 300,  # 5 minutes max
                "enable_progress_bars": True
            },
            "auto_detected": True
        }
        
        return config
    
    def _get_optimal_cpu_workers(self, hardware_info) -> int:
        """Get optimal number of CPU workers"""
        if hardware_info.performance_tier == "high":
            return min(12, max(8, os.cpu_count() or 4))
        elif hardware_info.performance_tier == "medium":
            return min(10, max(6, (os.cpu_count() or 4) - 2))
        else:  # low
            return min(6, max(4, (os.cpu_count() or 4) // 2))
    
    def _get_optimal_stage2_concurrency(self, hardware_info) -> int:
        """Get optimal Stage 2 concurrency"""
        if hardware_info.device == "cuda":
            # Use max_memory_gb from HardwareConfig
            if hardware_info.max_memory_gb >= 8:
                return 3  # High-memory GPU
            elif hardware_info.max_memory_gb >= 4:
                return 2  # Medium-memory GPU
            else:
                return 1  # Low-memory GPU
        else:
            return 1  # CPU-only
    
    def _get_target_performance(self, hardware_info) -> float:
        """Get target performance (jobs/second)"""
        if hardware_info.performance_tier == "high":
            return 50.0
        elif hardware_info.performance_tier == "medium":
            return 25.0
        else:
            return 10.0
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            console.print(
                f"[green]✅ Configuration saved to {self.config_path}[/green]"
            )
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            console.print(f"[red]❌ Failed to save configuration: {e}[/red]")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            console.print(
                f"[green]✅ Configuration loaded from "
                f"{self.config_path}[/green]"
            )
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            console.print(f"[red]❌ Failed to load configuration: {e}[/red]")
            return {}
    
    def _display_config(self, config: Dict[str, Any]):
        """Display configuration in a nice format"""
        hardware = config.get("hardware", {})
        processing = config.get("processing", {})
        performance = config.get("performance", {})
        
        batch_enabled = processing.get('enable_batch_processing', False)
        batch_status = '✅ Enabled' if batch_enabled else '❌ Disabled'
        
        config_text = f"""[bold]Hardware Configuration:[/bold]
• Device: {hardware.get('device_name', 'Unknown')}
• Memory: {hardware.get('memory_gb', 0):.1f}GB
• Performance: {hardware.get('performance_tier', 'unknown').title()}

[bold]Processing Configuration:[/bold]
• CPU Workers: {processing.get('cpu_workers', 4)}
• Stage 2 Concurrency: {processing.get('max_concurrent_stage2', 1)}
• Batch Processing: {batch_status}
• Batch Size: {processing.get('batch_size', 16)}

[bold]Performance Targets:[/bold]
• Target Speed: {performance.get('target_jobs_per_second', 10):.0f} jobs/second
• Max Processing Time: {performance.get('max_processing_time', 300)} seconds"""
        
        console.print(Panel(
            config_text,
            title="🚀 Optimization Configuration",
            border_style="bold blue"
        ))
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration (load or create if doesn't exist)"""
        if self.config_path.exists():
            return self._load_config()
        else:
            return self.detect_and_configure()
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update specific configuration values"""
        try:
            config = self.get_config()
            
            # Deep merge updates
            def deep_merge(base: dict, updates: dict):
                for key, value in updates.items():
                    if (key in base and isinstance(base[key], dict)
                            and isinstance(value, dict)):
                        deep_merge(base[key], value)
                    else:
                        base[key] = value
            
            deep_merge(config, updates)
            
            self._save_config(config)
            console.print(
                "[green]✅ Configuration updated successfully[/green]"
            )
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to update configuration: {e}[/red]")
            return False


def auto_configure_optimization(
    force_reconfigure: bool = False
) -> Dict[str, Any]:
    """
    Auto-configure optimization settings for the current system
    
    Args:
        force_reconfigure: Force reconfiguration even if config exists
        
    Returns:
        Optimal configuration dictionary
    """
    configurator = OptimizationConfigurator()
    return configurator.detect_and_configure(force_reconfigure)


def get_optimization_config() -> Dict[str, Any]:
    """Get current optimization configuration"""
    configurator = OptimizationConfigurator()
    return configurator.get_config()


def create_optimized_processor_from_config(
    user_profile: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
):
    """
    Create optimized processor using configuration
    
    Args:
        user_profile: User profile dictionary
        config: Optional configuration (auto-detects if not provided)
        
    Returns:
        Configured optimized processor
    """
    if config is None:
        config = get_optimization_config()
    
    processing_config = config.get("processing", {})
    
    from src.optimization.integrated_processor import (
        create_optimized_processor
    )
    
    return create_optimized_processor(
        user_profile=user_profile,
        cpu_workers=processing_config.get("cpu_workers", 8),
        max_concurrent_stage2=processing_config.get("max_concurrent_stage2", 2)
    )


# CLI Interface
def main():
    """CLI interface for optimization configuration"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Configure JobLens Optimization"
    )
    parser.add_argument(
        "--reconfigure", action="store_true",
        help="Force reconfiguration"
    )
    parser.add_argument(
        "--show", action="store_true",
        help="Show current configuration"
    )
    
    args = parser.parse_args()
    
    configurator = OptimizationConfigurator()
    
    if args.show:
        config = configurator.get_config()
        configurator._display_config(config)
    else:
        config = configurator.detect_and_configure(args.reconfigure)
        console.print(
            "\n[bold green]🎉 Optimization configuration complete![/bold green]"
        )
        console.print(
            "[cyan]You can now use the optimized processor in your "
            "workflows.[/cyan]"
        )


if __name__ == "__main__":
    main()
