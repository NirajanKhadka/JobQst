#!/usr/bin/env python3
"""
Big Data Patterns for Job Automation - Modern Python Features
Inspired by Apache Kafka, Apache Spark, and modern data engineering practices.
"""

import asyncio
import json
import time
import threading
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, AsyncGenerator, Callable, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from queue import Queue, Empty, PriorityQueue
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp
from functools import wraps, lru_cache
import weakref
import pickle
import gzip
import hashlib
from collections import defaultdict, deque
import itertools
import operator
from contextlib import asynccontextmanager, contextmanager

# Modern Python imports
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.layout import Layout
from rich.text import Text
from pydantic import BaseModel, Field, validator, root_validator
from typing_extensions import TypedDict, Literal

console = Console()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataStreamType(Enum):
    """Data stream types for different processing patterns."""
    BATCH = "batch"
    STREAMING = "streaming"
    MICRO_BATCH = "micro_batch"
    REAL_TIME = "real_time"

class ProcessingPattern(Enum):
    """Big data processing patterns."""
    MAP_REDUCE = "map_reduce"
    STREAM_PROCESSING = "stream_processing"
    BATCH_PROCESSING = "batch_processing"
    LAMBDA_ARCHITECTURE = "lambda_architecture"
    KAPPA_ARCHITECTURE = "kappa_architecture"

@dataclass
class DataChunk:
    """Data chunk for batch processing."""
    id: str
    data: List[Dict]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)
    priority: int = 0
    
    def __post_init__(self):
        if not self.id:
            self.id = hashlib.md5(f"{self.timestamp}{len(self.data)}".encode()).hexdigest()[:8]

@dataclass
class ProcessingMetrics:
    """Real-time processing metrics."""
    start_time: datetime = field(default_factory=datetime.now)
    records_processed: int = 0
    records_failed: int = 0
    processing_time: float = 0.0
    throughput: float = 0.0
    latency: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    
    def update_throughput(self, records: int, time_taken: float):
        """Update throughput metrics."""
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
        self._lock = threading.Lock()
        
    async def process_stream(self, data_stream: AsyncGenerator[Dict, None]):
        """Process data stream with backpressure control."""
        self.running = True
        
        async for data in data_stream:
            if not self.running:
                break
                
            # Check backpressure
            if len(self.buffer) >= self.max_buffer_size * 0.8:
                await asyncio.sleep(0.1)  # Backpressure delay
                
            # Add to buffer
            with self._lock:
                self.buffer.append(data)
            
            # Process if buffer is full or rate limit reached
            if len(self.buffer) >= self.processing_rate:
                await self._process_batch()
                
        # Process remaining data
        if self.buffer:
            await self._process_batch()
    
    async def _process_batch(self):
        """Process a batch of data."""
        start_time = time.time()
        
        with self._lock:
            batch = list(itertools.islice(self.buffer, self.processing_rate))
            for _ in range(len(batch)):
                self.buffer.popleft()
        
        # Process batch
        processed = 0
        failed = 0
        
        for item in batch:
            try:
                await self._process_item(item)
                processed += 1
            except Exception as e:
                failed += 1
                logger.error(f"Processing error: {e}")
        
        # Update metrics
        time_taken = time.time() - start_time
        self.metrics.update_throughput(processed, time_taken)
        self.metrics.records_failed += failed
    
    async def _process_item(self, item: Dict):
        """Process a single item (to be overridden)."""
        pass

class BatchProcessor:
    """Batch processor with memory optimization."""
    
    def __init__(self, batch_size: int = 1000, max_memory_mb: int = 1024):
        self.batch_size = batch_size
        self.max_memory_mb = max_memory_mb
        self.metrics = ProcessingMetrics()
        
    async def process_batches(self, data_generator: AsyncGenerator[Dict, None]):
        """Process data in batches with memory management."""
        batch = []
        batch_start = time.time()
        
        async for item in data_generator:
            batch.append(item)
            
            # Check if batch is full or memory limit reached
            if len(batch) >= self.batch_size or self._memory_usage_mb() > self.max_memory_mb:
                await self._process_batch(batch)
                batch = []
                batch_start = time.time()
        
        # Process remaining batch
        if batch:
            await self._process_batch(batch)
    
    async def _process_batch(self, batch: List[Dict]):
        """Process a batch of data."""
        start_time = time.time()
        
        try:
            # Process batch (to be overridden)
            await self._process_batch_impl(batch)
            
            # Update metrics
            time_taken = time.time() - start_time
            self.metrics.update_throughput(len(batch), time_taken)
            
        except Exception as e:
            self.metrics.records_failed += len(batch)
            logger.error(f"Batch processing error: {e}")
    
    async def _process_batch_impl(self, batch: List[Dict]):
        """Process batch implementation (to be overridden)."""
        pass
    
    def _memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

class MapReduceProcessor:
    """MapReduce pattern implementation."""
    
    def __init__(self, num_reducers: int = 4):
        self.num_reducers = num_reducers
        self.metrics = ProcessingMetrics()
        
    async def map_reduce(self, data: List[Dict], map_func: Callable, reduce_func: Callable):
        """Execute MapReduce pattern."""
        start_time = time.time()
        
        # Map phase
        mapped_data = await self._map_phase(data, map_func)
        
        # Shuffle phase
        shuffled_data = self._shuffle_phase(mapped_data)
        
        # Reduce phase
        results = await self._reduce_phase(shuffled_data, reduce_func)
        
        # Update metrics
        time_taken = time.time() - start_time
        self.metrics.update_throughput(len(data), time_taken)
        
        return results
    
    async def _map_phase(self, data: List[Dict], map_func: Callable) -> List[tuple]:
        """Execute map phase."""
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(executor, map_func, item)
                for item in data
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        # Filter out exceptions
        mapped_data = []
        for result in results:
            if isinstance(result, Exception):
                self.metrics.records_failed += 1
            else:
                mapped_data.extend(result if isinstance(result, list) else [result])
        
        return mapped_data
    
    def _shuffle_phase(self, mapped_data: List[tuple]) -> Dict[Any, List]:
        """Execute shuffle phase."""
        shuffled = defaultdict(list)
        
        for key, value in mapped_data:
            shuffled[key].append(value)
        
        return dict(shuffled)
    
    async def _reduce_phase(self, shuffled_data: Dict[Any, List], reduce_func: Callable):
        """Execute reduce phase."""
        with ThreadPoolExecutor(max_workers=self.num_reducers) as executor:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(executor, reduce_func, key, values)
                for key, values in shuffled_data.items()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        # Filter out exceptions
        reduced_data = []
        for result in results:
            if isinstance(result, Exception):
                self.metrics.records_failed += 1
            else:
                reduced_data.append(result)
        
        return reduced_data

class DataPipeline:
    """Modern data pipeline with multiple stages."""
    
    def __init__(self, stages: List[Callable], config: Dict = None):
        self.stages = stages
        self.config = config or {}
        self.metrics = ProcessingMetrics()
        self.running = False
        
    async def execute(self, data: List[Dict]) -> List[Dict]:
        """Execute the pipeline."""
        self.running = True
        start_time = time.time()
        
        current_data = data
        
        for i, stage in enumerate(self.stages):
            if not self.running:
                break
                
            try:
                stage_start = time.time()
                
                # Execute stage
                if asyncio.iscoroutinefunction(stage):
                    current_data = await stage(current_data)
                else:
                    current_data = stage(current_data)
                
                stage_time = time.time() - stage_start
                logger.info(f"Stage {i+1} completed in {stage_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Stage {i+1} failed: {e}")
                self.metrics.records_failed += len(current_data)
                break
        
        # Update metrics
        total_time = time.time() - start_time
        self.metrics.update_throughput(len(data), total_time)
        
        return current_data

class CacheManager:
    """Intelligent caching with TTL and LRU."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = {}
        self.access_times = {}
        self._lock = threading.Lock()
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key in self.cache:
                # Check TTL
                if time.time() - self.access_times[key] > self.default_ttl:
                    del self.cache[key]
                    del self.access_times[key]
                    return None
                
                # Update access time
                self.access_times[key] = time.time()
                return self.cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Set value in cache."""
        with self._lock:
            # Evict if cache is full
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            self.cache[key] = value
            self.access_times[key] = time.time()
    
    def _evict_lru(self):
        """Evict least recently used item."""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[lru_key]
        del self.access_times[lru_key]

class MetricsCollector:
    """Real-time metrics collection and aggregation."""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self._lock = threading.Lock()
        
    def record_metric(self, name: str, value: Union[int, float], tags: Dict = None):
        """Record a metric."""
        with self._lock:
            key = f"{name}_{json.dumps(tags or {}, sort_keys=True)}"
            self.metrics[key].append({
                'value': value,
                'timestamp': datetime.now().isoformat(),
                'tags': tags or {}
            })
    
    def increment_counter(self, name: str, value: int = 1, tags: Dict = None):
        """Increment a counter."""
        with self._lock:
            key = f"{name}_{json.dumps(tags or {}, sort_keys=True)}"
            self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, tags: Dict = None):
        """Set a gauge value."""
        with self._lock:
            key = f"{name}_{json.dumps(tags or {}, sort_keys=True)}"
            self.gauges[key] = value
    
    def get_summary(self) -> Dict:
        """Get metrics summary."""
        with self._lock:
            summary = {
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'metrics': {}
            }
            
            for key, values in self.metrics.items():
                if values:
                    summary['metrics'][key] = {
                        'count': len(values),
                        'min': min(v['value'] for v in values),
                        'max': max(v['value'] for v in values),
                        'avg': sum(v['value'] for v in values) / len(values)
                    }
            
            return summary

# Decorators for modern Python patterns
def retry(max_attempts: int = 3, delay: float = 1.0):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (2 ** attempt))
            
            raise last_exception
        return wrapper
    return decorator

def circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 60):
    """Circuit breaker pattern decorator."""
    def decorator(func):
        failures = 0
        last_failure_time = 0
        state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal failures, last_failure_time, state
            
            current_time = time.time()
            
            # Check if circuit is open
            if state == "OPEN":
                if current_time - last_failure_time > recovery_timeout:
                    state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Success - reset circuit
                if state == "HALF_OPEN":
                    state = "CLOSED"
                failures = 0
                return result
                
            except Exception as e:
                failures += 1
                last_failure_time = current_time
                
                if failures >= failure_threshold:
                    state = "OPEN"
                
                raise e
        
        return wrapper
    return decorator

def rate_limiter(max_calls: int, time_window: float):
    """Rate limiting decorator."""
    def decorator(func):
        calls = deque()
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_time = time.time()
            
            # Remove old calls outside the time window
            while calls and current_time - calls[0] > time_window:
                calls.popleft()
            
            # Check if rate limit exceeded
            if len(calls) >= max_calls:
                sleep_time = time_window - (current_time - calls[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            # Record call
            calls.append(current_time)
            
            # Execute function
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Utility functions
@lru_cache(maxsize=128)
def hash_data(data: str) -> str:
    """Hash data for caching."""
    return hashlib.md5(data.encode()).hexdigest()

def compress_data(data: bytes) -> bytes:
    """Compress data using gzip."""
    return gzip.compress(data)

def decompress_data(data: bytes) -> bytes:
    """Decompress data using gzip."""
    return gzip.decompress(data)

def serialize_data(data: Any) -> bytes:
    """Serialize data using pickle."""
    return pickle.dumps(data)

def deserialize_data(data: bytes) -> Any:
    """Deserialize data using pickle."""
    return pickle.loads(data)

# Context managers
@asynccontextmanager
async def pipeline_context(pipeline_name: str):
    """Context manager for pipeline execution."""
    start_time = time.time()
    logger.info(f"Starting pipeline: {pipeline_name}")
    
    try:
        yield
    except Exception as e:
        logger.error(f"Pipeline {pipeline_name} failed: {e}")
        raise
    finally:
        duration = time.time() - start_time
        logger.info(f"Pipeline {pipeline_name} completed in {duration:.2f}s")

@contextmanager
def resource_manager(resource_name: str):
    """Context manager for resource management."""
    logger.info(f"Acquiring resource: {resource_name}")
    
    try:
        yield
    finally:
        logger.info(f"Releasing resource: {resource_name}")

# Example usage functions
async def example_stream_processing():
    """Example of stream processing."""
    async def data_stream():
        for i in range(1000):
            yield {"id": i, "data": f"record_{i}"}
            await asyncio.sleep(0.01)
    
    processor = StreamProcessor(max_buffer_size=1000, processing_rate=100)
    
    class JobProcessor(StreamProcessor):
        async def _process_item(self, item: Dict):
            # Simulate job processing
            await asyncio.sleep(0.001)
            logger.info(f"Processed job: {item['id']}")
    
    job_processor = JobProcessor()
    await job_processor.process_stream(data_stream())

async def example_map_reduce():
    """Example of MapReduce processing."""
    data = [{"id": i, "value": i * 2} for i in range(100)]
    
    def map_func(item):
        return [(item["value"] % 3, item["value"])]
    
    def reduce_func(key, values):
        return {"key": key, "sum": sum(values), "count": len(values)}
    
    processor = MapReduceProcessor(num_reducers=4)
    results = await processor.map_reduce(data, map_func, reduce_func)
    
    console.print(f"MapReduce results: {results}")

async def example_pipeline():
    """Example of data pipeline."""
    def stage1(data):
        return [{"id": item["id"], "processed": True} for item in data]
    
    def stage2(data):
        return [{"id": item["id"], "enriched": True} for item in data]
    
    async def stage3(data):
        await asyncio.sleep(0.1)  # Simulate async processing
        return [{"id": item["id"], "final": True} for item in data]
    
    pipeline = DataPipeline([stage1, stage2, stage3])
    
    input_data = [{"id": i} for i in range(10)]
    results = await pipeline.execute(input_data)
    
    console.print(f"Pipeline results: {results}")

if __name__ == "__main__":
    # Run examples
    asyncio.run(example_stream_processing())
    asyncio.run(example_map_reduce())
    asyncio.run(example_pipeline())
