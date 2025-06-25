import asyncio
import time
from typing import Dict, List, AsyncGenerator
import logging

logger = logging.getLogger(__name__)

class ProcessingMetrics:
    """Real-time processing metrics."""
    def __init__(self):
        self.records_processed = 0
        self.records_failed = 0
        self.processing_time = 0.0
        self.throughput = 0.0

    def update_throughput(self, records: int, time_taken: float):
        self.records_processed += records
        self.processing_time += time_taken
        self.throughput = self.records_processed / self.processing_time if self.processing_time > 0 else 0

class BatchProcessor:
    """Batch processor with memory optimization."""
    
    def __init__(self, batch_size: int = 1000, max_memory_mb: int = 1024):
        self.batch_size = batch_size
        self.max_memory_mb = max_memory_mb
        self.metrics = ProcessingMetrics()
        
    async def process_batches(self, data_generator: AsyncGenerator[Dict, None]):
        batch = []
        async for item in data_generator:
            batch.append(item)
            if len(batch) >= self.batch_size or self._memory_usage_mb() > self.max_memory_mb:
                await self._process_batch(batch)
                batch = []
        if batch:
            await self._process_batch(batch)
    
    async def _process_batch(self, batch: List[Dict]):
        start_time = time.time()
        try:
            await self._process_batch_impl(batch)
            self.metrics.update_throughput(len(batch), time.time() - start_time)
        except Exception as e:
            self.metrics.records_failed += len(batch)
            logger.error(f"Batch processing error: {e}")
    
    async def _process_batch_impl(self, batch: List[Dict]):
        """To be overridden by subclasses."""
        pass
    
    def _memory_usage_mb(self) -> float:
        try:
            import psutil
            return psutil.Process().memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0