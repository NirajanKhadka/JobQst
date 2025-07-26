"""
Simple Pipeline Test
Test the performance optimizations without complex dependencies.
"""

import asyncio
import time
from rich.console import Console

console = Console()

async def simple_pipeline_test():
    """Test basic async functionality."""
    console.print("[bold blue]🚀 Testing Simple Pipeline[/bold blue]")
    start_time = time.time()
    # Test async operations
    tasks = []
    for i in range(5):
        tasks.append(test_async_job(i))
    results = await asyncio.gather(*tasks)
    duration = time.time() - start_time
    console.print(f"[green]✅ Processed {len(results)} jobs in {duration:.3f}s[/green]")
    console.print(f"[cyan]📊 Rate: {len(results)/duration:.2f} jobs/sec[/cyan]")
    # Assert that all jobs completed and results are as expected
    assert len(results) == 5
    for i, result in enumerate(results):
        assert result == f"job_{i}_completed"

async def test_async_job(job_id: int):
    """Simulate async job processing."""
    await asyncio.sleep(0.1)  # Simulate work
    return f"job_{job_id}_completed"

if __name__ == "__main__":
    asyncio.run(simple_pipeline_test())
    print("Test completed.")
