import asyncio
import time
from collections import defaultdict
from typing import Dict, List, Callable, Any
from concurrent.futures import ThreadPoolExecutor

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

class MapReduceProcessor:
    """MapReduce pattern implementation."""
    
    def __init__(self, num_reducers: int = 4):
        self.num_reducers = num_reducers
        self.metrics = ProcessingMetrics()
        
    async def map_reduce(self, data: List[Dict], map_func: Callable, reduce_func: Callable):
        start_time = time.time()
        
        mapped_data = await self._map_phase(data, map_func)
        shuffled_data = self._shuffle_phase(mapped_data)
        results = await self._reduce_phase(shuffled_data, reduce_func)
        
        self.metrics.update_throughput(len(data), time.time() - start_time)
        return results
    
    async def _map_phase(self, data: List[Dict], map_func: Callable) -> List[tuple]:
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            tasks = [loop.run_in_executor(executor, map_func, item) for item in data]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        mapped_data = [res for res in results if not isinstance(res, Exception)]
        self.metrics.records_failed += len(results) - len(mapped_data)
        return [item for sublist in mapped_data for item in sublist]
    
    def _shuffle_phase(self, mapped_data: List[tuple]) -> Dict[Any, List]:
        shuffled = defaultdict(list)
        for key, value in mapped_data:
            shuffled[key].append(value)
        return dict(shuffled)
    
    async def _reduce_phase(self, shuffled_data: Dict[Any, List], reduce_func: Callable):
        with ThreadPoolExecutor(max_workers=self.num_reducers) as executor:
            loop = asyncio.get_event_loop()
            tasks = [loop.run_in_executor(executor, reduce_func, key, values) for key, values in shuffled_data.items()]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        reduced_data = [res for res in results if not isinstance(res, Exception)]
        self.metrics.records_failed += len(results) - len(reduced_data)
        return reduced_data