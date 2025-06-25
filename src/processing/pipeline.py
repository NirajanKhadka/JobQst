import asyncio
import time
from typing import Dict, List, Callable
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

class DataPipeline:
    """Modern data pipeline with multiple stages."""
    
    def __init__(self, stages: List[Callable]):
        self.stages = stages
        self.metrics = ProcessingMetrics()
        
    async def execute(self, data: List[Dict]) -> List[Dict]:
        start_time = time.time()
        current_data = data
        
        for i, stage in enumerate(self.stages):
            try:
                if asyncio.iscoroutinefunction(stage):
                    current_data = await stage(current_data)
                else:
                    current_data = stage(current_data)
            except Exception as e:
                logger.error(f"Stage {i+1} failed: {e}")
                self.metrics.records_failed += len(current_data)
                break
        
        self.metrics.update_throughput(len(data), time.time() - start_time)
        return current_data