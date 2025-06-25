import asyncio
from collections import deque
import time
from typing import Dict, AsyncGenerator
import itertools
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

class StreamProcessor:
    """Stream processor with backpressure handling."""
    
    def __init__(self, max_buffer_size: int = 10000, processing_rate: int = 1000):
        self.max_buffer_size = max_buffer_size
        self.processing_rate = processing_rate
        self.buffer = deque(maxlen=max_buffer_size)
        self.metrics = ProcessingMetrics()
        self.running = False

    async def process_stream(self, data_stream: AsyncGenerator[Dict, None]):
        self.running = True
        async for data in data_stream:
            if not self.running:
                break
            
            if len(self.buffer) >= self.max_buffer_size * 0.8:
                await asyncio.sleep(0.1)
            
            self.buffer.append(data)
            
            if len(self.buffer) >= self.processing_rate:
                await self._process_batch()
                
        if self.buffer:
            await self._process_batch()
    
    async def _process_batch(self):
        start_time = time.time()
        batch = list(itertools.islice(self.buffer, self.processing_rate))
        for _ in range(len(batch)):
            self.buffer.popleft()
        
        processed, failed = 0, 0
        for item in batch:
            try:
                await self._process_item(item)
                processed += 1
            except Exception as e:
                failed += 1
                logger.error(f"Processing error: {e}")
        
        self.metrics.update_throughput(processed, time.time() - start_time)
        self.metrics.records_failed += failed
    
    async def _process_item(self, item: Dict):
        """To be overridden by subclasses."""
        pass