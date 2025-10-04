#!/usr/bin/env python3
"""
Improved Error Handling System for AutoJobAgent
Provides comprehensive error handling, retry mechanisms, fallback strategies, and detailed logging.
"""

import functools
import time
import traceback
import logging
import json
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("error_logs.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


class ErrorTracker:
    """Track and analyze errors across the application."""

    def __init__(self):
        self.errors = []
        self.error_counts = {}
        self.recovery_stats = {}

    def log_error(
        self, error: Exception, context: Dict, operation: str, recovery_attempted: bool = False
    ):
        """Log an error with context information."""
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "recovery_attempted": recovery_attempted,
            "stack_trace": traceback.format_exc(),
        }

        self.errors.append(error_info)

        # Update error counts
        error_key = f"{operation}:{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # Log to file
        logger.error(f"Error in {operation}: {error}", extra={"context": context})

    def get_error_summary(self) -> Dict:
        """Get summary of errors and patterns."""
        return {
            "total_errors": len(self.errors),
            "error_counts": self.error_counts,
            "recovery_stats": self.recovery_stats,
            "recent_errors": self.errors[-10:] if self.errors else [],
        }

    def save_error_report(self, filepath: str = "error_report.json"):
        """Save detailed error report to file."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": self.get_error_summary(),
            "all_errors": self.errors,
        }

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)

        console.print(f"[green]📊 Error report saved to {filepath}[/green]")


# Create global instance
error_tracker = ErrorTracker()

# Import the better implementations from error_tolerance_handler
from src.utils.error_tolerance_handler import (
    with_retry,
    with_fallback,
    safe_execute,
    get_error_tolerance_handler,
)


class reliableOperations:
    """Collection of reliable operations with built-in error handling."""

    @staticmethod
    @with_retry(max_attempts=3)
    def read_file(filepath: Union[str, Path], encoding: str = "utf-8") -> str:
        """reliablely read a file with retry logic."""
        with open(filepath, "r", encoding=encoding) as f:
            return f.read()

    @staticmethod
    @with_retry(max_attempts=3)
    def write_file(filepath: Union[str, Path], content: str, encoding: str = "utf-8") -> bool:
        """reliablely write to a file with retry logic."""
        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding=encoding) as f:
            f.write(content)
        return True

    @staticmethod
    @with_retry(max_attempts=3)
    def load_json(filepath: Union[str, Path]) -> Dict:
        """reliablely load JSON with retry logic."""
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    @with_retry(max_attempts=3)
    def save_json(data: Dict, filepath: Union[str, Path]) -> bool:
        """reliablely save JSON with retry logic."""
        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return True


# Create global instance
reliable_ops = reliableOperations()


def display_error_dashboard():
    """Display error tracking dashboard."""
    summary = error_tracker.get_error_summary()

    console.print("\n[bold blue]🚨 Error Tracking Dashboard[/bold blue]")

    # Summary table
    summary_table = Table(title="Error Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="magenta")

    summary_table.add_row("Total Errors", str(summary["total_errors"]))
    summary_table.add_row("Unique Error Types", str(len(summary["error_counts"])))
    summary_table.add_row("Successful Recoveries", str(sum(summary["recovery_stats"].values())))

    console.print(summary_table)

    # Top errors table
    if summary["error_counts"]:
        error_table = Table(title="Most Common Errors")
        error_table.add_column("Operation:Error", style="cyan")
        error_table.add_column("Count", style="magenta")

        sorted_errors = sorted(summary["error_counts"].items(), key=lambda x: x[1], reverse=True)
        for error_key, count in sorted_errors[:10]:
            error_table.add_row(error_key, str(count))

        console.print(error_table)

    # Recent errors
    if summary["recent_errors"]:
        console.print("\n[bold yellow]📋 Recent Errors:[/bold yellow]")
        for error in summary["recent_errors"][-5:]:
            console.print(
                f"  • {error['timestamp']}: {error['operation']} - {error['error_type']}: {error['error_message']}"
            )

    # Main functionality moved to CLI module or tests
    # Import and use the functions directly

    @with_retry(max_attempts=2)
    def test_retry_function():
        import random

        if random.random() < 0.7:  # 70% chance of failure
            raise ValueError("Random test error")
        return "Success!"

    # Test retry mechanism
    try:
        result = test_retry_function()
        console.print(f"[green]✅ Test result: {result}[/green]")
    except Exception as e:
        console.print(f"[red]❌ Test failed: {e}[/red]")

    # Display dashboard
    display_error_dashboard()

    # Save error report
    error_tracker.save_error_report()
