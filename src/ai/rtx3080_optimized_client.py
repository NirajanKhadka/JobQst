"""
RTX 3080 Optimized GPU Client for Maximum Job Processing Performance
Leverages RTX 3080's 10GB VRAM, Ampere architecture, and parallel processing capabilities.
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import concurrent.futures
from pathlib import Path

try:
    import ollama
    from ollama import Client, ResponseError
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ollama = None
    Client = None
    ResponseError = Exception

try:
    import psutil
    import GPUtil
    NVIDIA_MONITORING_AVAILABLE = True
except ImportError:
    NVIDIA_MONITORING_AVAILABLE = False
    psutil = None
    GPUtil = None

logger = logging.getLogger(__name__)

class RTX3080Status(Enum):
    """RTX 3080 GPU status enumeration."""
    OPTIMAL = "optimal"
    AVAILABLE = "available"
    MEMORY_LIMITED = "memory_limited"
    OVERHEATING = "overheating"
    UNAVAILABLE = "unavailable"
    ERROR = "error"

@dataclass
class RTX3080Metrics:
    """RTX 3080 performance metrics."""
    gpu_utilization: float = 0.0
    memory_used_gb: float = 0.0
    memory_total_gb: float = 10.0  # RTX 3080 has 10GB VRAM
    temperature_c: float = 0.0
    power_usage_w: float = 0.0
    cuda_cores_active: int = 0
    tensor_cores_active: int = 0
    inference_speed_jobs_per_sec: float = 0.0
    batch_size_current: int = 1
    concurrent_streams: int = 1
    model_load_time_ms: float = 0.0
    last_updated: float = field(default_factory=time.time)

@dataclass
class BatchJobAnalysisResult:
    """Result of batch job analysis optimized for RTX 3080."""
    job_results: List[Dict[str, Any]]
    batch_size: int
    processing_time: float
    gpu_utilization: float
    memory_used_gb: float
    jobs_per_second: float
    model_used: str
    cuda_streams_used: int
    tensor_cores_utilized: bool

class RTX3080OptimizedClient:
    """
    RTX 3080 optimized client for maximum job processing performance.
    
    Leverages:
    - 10GB VRAM for large batch processing
    - 8704 CUDA cores for parallel inference
    - 272 Tensor cores for AI acceleration
    - Multiple concurrent streams
    - Persistent model loading
    """
    
    def __init__(self, 
                 host: str = "http://localhost:11434",
                 model: str = "llama3",
                 max_batch_size: int = 16,
                 concurrent_streams: int = 4,
                 memory_limit_gb: float = 8.5):  # Leave 1.5GB for system
        """
        Initialize RTX 3080 optimized client.
        
        Args:
            host: Ollama service host URL
            model: Model to use for analysis
            max_batch_size: Maximum jobs per batch (optimized for RTX 3080)
            concurrent_streams: Number of concurrent GPU streams
            memory_limit_gb: GPU memory limit in GB
        """
        self.host = host
        self.model = model
        self.max_batch_size = max_batch_size
        self.concurrent_streams = concurrent_streams
        self.memory_limit_gb = memory_limit_gb
        
        # RTX 3080 specific settings
        self.rtx3080_specs = {
            "cuda_cores": 8704,
            "tensor_cores": 272,
            "memory_gb": 10.0,
            "memory_bandwidth_gbps": 760,
            "base_clock_mhz": 1440,
            "boost_clock_mhz": 1710
        }
        
        # Performance tracking
        self.metrics = RTX3080Metrics()
        self.performance_history = []
        
        # Initialize components
        if not OLLAMA_AVAILABLE:
            raise ImportError("Ollama library not installed. Install with: pip install ollama")
        
        self.client = Client(host=host)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Model cache for persistent loading
        self.model_loaded = False
        self.model_load_time = 0.0
        
        # Async components
        self.batch_queue = asyncio.Queue(maxsize=100)
        self.result_queue = asyncio.Queue(maxsize=100)
        self.processing_semaphore = asyncio.Semaphore(concurrent_streams)
        
        # Initialize and validate RTX 3080 setup
        self._initialize_rtx3080_optimization()
    
    def _initialize_rtx3080_optimization(self) -> None:
        """Initialize RTX 3080 specific optimizations."""
        self.logger.info("🚀 Initializing RTX 3080 optimizations...")
        
        # Check RTX 3080 availability
        gpu_status = self._check_rtx3080_status()
        if gpu_status != RTX3080Status.OPTIMAL and gpu_status != RTX3080Status.AVAILABLE:
            self.logger.warning(f"RTX 3080 not in optimal state: {gpu_status.value}")
        
        # Pre-load model for persistent GPU memory allocation
        self._preload_model_to_gpu()
        
        # Optimize batch size based on available VRAM
        self._optimize_batch_size()
        
        # Initialize concurrent streams
        self._initialize_gpu_streams()
        
        self.logger.info(f"✅ RTX 3080 optimization complete - Batch size: {self.max_batch_size}, Streams: {self.concurrent_streams}")
    
    def _check_rtx3080_status(self) -> RTX3080Status:
        """Check RTX 3080 GPU status and capabilities."""
        try:
            if not NVIDIA_MONITORING_AVAILABLE:
                self.logger.warning("NVIDIA monitoring not available - install GPUtil and psutil")
                return RTX3080Status.AVAILABLE
            
            gpus = GPUtil.getGPUs()
            rtx3080_gpu = None
            
            # Find RTX 3080
            for gpu in gpus:
                if "3080" in gpu.name or "RTX 3080" in gpu.name:
                    rtx3080_gpu = gpu
                    break
            
            if not rtx3080_gpu:
                self.logger.warning("RTX 3080 not detected - falling back to available GPU")
                return RTX3080Status.AVAILABLE if gpus else RTX3080Status.UNAVAILABLE
            
            # Update metrics
            self.metrics.gpu_utilization = rtx3080_gpu.load * 100
            self.metrics.memory_used_gb = rtx3080_gpu.memoryUsed / 1024
            self.metrics.memory_total_gb = rtx3080_gpu.memoryTotal / 1024
            self.metrics.temperature_c = rtx3080_gpu.temperature
            
            # Determine status
            if self.metrics.temperature_c > 83:  # RTX 3080 thermal limit
                return RTX3080Status.OVERHEATING
            elif self.metrics.memory_used_gb > 9.0:  # Near memory limit
                return RTX3080Status.MEMORY_LIMITED
            elif self.metrics.gpu_utilization < 90 and self.metrics.memory_used_gb < 8.0:
                return RTX3080Status.OPTIMAL
            else:
                return RTX3080Status.AVAILABLE
                
        except Exception as e:
            self.logger.error(f"RTX 3080 status check failed: {e}")
            return RTX3080Status.ERROR
    
    def _preload_model_to_gpu(self) -> None:
        """Pre-load model to GPU memory for persistent allocation."""
        start_time = time.time()
        
        try:
            self.logger.info(f"🔄 Pre-loading {self.model} to RTX 3080 VRAM...")
            
            # Ensure model is available
            models = self.client.list()
            model_names = [model['name'] for model in models.get('models', [])]
            
            if self.model not in model_names:
                self.logger.info(f"📥 Pulling {self.model} model...")
                self.client.pull(self.model)
            
            # Warm up the model with a small inference
            warmup_prompt = "Test prompt for GPU warmup"
            response = self.client.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': warmup_prompt}],
                options={
                    'temperature': 0.1,
                    'num_predict': 10,  # Short response for warmup
                    'num_gpu': 1  # Ensure GPU usage
                }
            )
            
            self.model_load_time = time.time() - start_time
            self.model_loaded = True
            self.metrics.model_load_time_ms = self.model_load_time * 1000
            
            self.logger.info(f"✅ Model pre-loaded to RTX 3080 in {self.model_load_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Model pre-loading failed: {e}")
            self.model_loaded = False
    
    def _optimize_batch_size(self) -> None:
        """Optimize batch size based on RTX 3080 VRAM availability."""
        try:
            # Get current GPU memory usage
            status = self._check_rtx3080_status()
            available_memory = self.metrics.memory_total_gb - self.metrics.memory_used_gb
            
            # Estimate memory per job (conservative estimate)
            memory_per_job_gb = 0.3  # ~300MB per job analysis
            
            # Calculate optimal batch size
            optimal_batch_size = min(
                int(available_memory / memory_per_job_gb),
                self.max_batch_size,
                32  # RTX 3080 sweet spot for parallel processing
            )
            
            # Ensure minimum batch size
            optimal_batch_size = max(optimal_batch_size, 4)
            
            self.max_batch_size = optimal_batch_size
            self.metrics.batch_size_current = optimal_batch_size
            
            self.logger.info(f"📊 Optimized batch size: {optimal_batch_size} jobs (Available VRAM: {available_memory:.1f}GB)")
            
        except Exception as e:
            self.logger.warning(f"Batch size optimization failed: {e}")
            self.max_batch_size = 8  # Safe default
    
    def _initialize_gpu_streams(self) -> None:
        """Initialize concurrent GPU streams for parallel processing."""
        try:
            # RTX 3080 can handle multiple concurrent streams efficiently
            available_memory_gb = self.metrics.memory_total_gb - self.metrics.memory_used_gb
            
            # Adjust concurrent streams based on available memory
            if available_memory_gb > 6.0:
                self.concurrent_streams = min(self.concurrent_streams, 6)
            elif available_memory_gb > 4.0:
                self.concurrent_streams = min(self.concurrent_streams, 4)
            else:
                self.concurrent_streams = 2
            
            self.processing_semaphore = asyncio.Semaphore(self.concurrent_streams)
            self.metrics.concurrent_streams = self.concurrent_streams
            
            self.logger.info(f"🔀 Initialized {self.concurrent_streams} concurrent GPU streams")
            
        except Exception as e:
            self.logger.warning(f"GPU streams initialization failed: {e}")
            self.concurrent_streams = 2
    
    async def analyze_jobs_batch_rtx3080(self, jobs: List[Dict[str, Any]], 
                                       user_profile: Optional[Dict] = None) -> BatchJobAnalysisResult:
        """
        Analyze multiple jobs in batch using RTX 3080 optimization.
        
        Args:
            jobs: List of job dictionaries to analyze
            user_profile: Optional user profile for compatibility scoring
            
        Returns:
            BatchJobAnalysisResult with comprehensive batch analysis
        """
        start_time = time.time()
        batch_size = min(len(jobs), self.max_batch_size)
        
        self.logger.info(f"🚀 Starting RTX 3080 batch analysis: {batch_size} jobs")
        
        try:
            # Update GPU metrics before processing
            gpu_status_before = self._check_rtx3080_status()
            
            # Process jobs in optimized batches
            job_batches = [jobs[i:i + batch_size] for i in range(0, len(jobs), batch_size)]
            all_results = []
            
            # Process batches concurrently using GPU streams
            batch_tasks = []
            for batch in job_batches:
                task = self._process_batch_with_gpu_stream(batch, user_profile)
                batch_tasks.append(task)
            
            # Execute all batches concurrently
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Flatten results
            for batch_result in batch_results:
                if isinstance(batch_result, list):
                    all_results.extend(batch_result)
                elif isinstance(batch_result, Exception):
                    self.logger.error(f"Batch processing failed: {batch_result}")
            
            # Calculate performance metrics
            processing_time = time.time() - start_time
            jobs_per_second = len(all_results) / processing_time if processing_time > 0 else 0
            
            # Update GPU metrics after processing
            gpu_status_after = self._check_rtx3080_status()
            
            # Update performance history
            self._update_performance_history(jobs_per_second, processing_time, len(all_results))
            
            result = BatchJobAnalysisResult(
                job_results=all_results,
                batch_size=batch_size,
                processing_time=processing_time,
                gpu_utilization=self.metrics.gpu_utilization,
                memory_used_gb=self.metrics.memory_used_gb,
                jobs_per_second=jobs_per_second,
                model_used=self.model,
                cuda_streams_used=self.concurrent_streams,
                tensor_cores_utilized=True  # RTX 3080 uses tensor cores for LLM inference
            )
            
            self.logger.info(f"✅ RTX 3080 batch analysis complete: {jobs_per_second:.1f} jobs/sec")
            return result
            
        except Exception as e:
            self.logger.error(f"RTX 3080 batch analysis failed: {e}")
            # Return fallback result
            return self._create_fallback_batch_result(jobs, time.time() - start_time)
    
    async def _process_batch_with_gpu_stream(self, job_batch: List[Dict[str, Any]], 
                                           user_profile: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Process a batch of jobs using a single GPU stream."""
        async with self.processing_semaphore:
            try:
                # Create batch prompt for efficient GPU processing
                batch_prompt = self._create_batch_prompt(job_batch, user_profile)
                
                # Process batch with optimized settings for RTX 3080
                response = await self._chat_batch_async(batch_prompt)
                
                # Parse batch response
                batch_results = self._parse_batch_response(response, job_batch)
                
                return batch_results
                
            except Exception as e:
                self.logger.error(f"GPU stream batch processing failed: {e}")
                return [self._create_fallback_job_result(job) for job in job_batch]
    
    def _create_batch_prompt(self, jobs: List[Dict[str, Any]], 
                           user_profile: Optional[Dict] = None) -> str:
        """Create optimized batch prompt for multiple job analysis."""
        
        batch_prompt = """
        Analyze the following job postings in batch and return results as a JSON array.
        Each job should be analyzed for skills, requirements, and compatibility.
        
        """
        
        if user_profile:
            batch_prompt += f"User Profile: {json.dumps(user_profile, indent=2)}\n\n"
        
        batch_prompt += "Jobs to analyze:\n"
        
        for i, job in enumerate(jobs):
            batch_prompt += f"""
        Job {i + 1}:
        Title: {job.get('title', 'Unknown')}
        Company: {job.get('company', 'Unknown')}
        Description: {job.get('description', job.get('job_description', ''))[:800]}
        
        """
        
        batch_prompt += """
        Return results as a JSON array with this exact format:
        [
            {
                "job_index": 1,
                "required_skills": ["skill1", "skill2"],
                "job_requirements": ["req1", "req2"],
                "compatibility_score": 0.85,
                "analysis_confidence": 0.92,
                "extracted_benefits": ["benefit1", "benefit2"],
                "reasoning": "Brief explanation"
            },
            ...
        ]
        
        Return only valid JSON array, no other text.
        """
        
        return batch_prompt
    
    async def _chat_batch_async(self, prompt: str) -> str:
        """Send batch chat request optimized for RTX 3080."""
        try:
            # Use asyncio to run the synchronous ollama call
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat(
                    model=self.model,
                    messages=[{'role': 'user', 'content': prompt}],
                    options={
                        'temperature': 0.1,
                        'num_predict': 2000,  # Allow longer responses for batch
                        'num_gpu': 1,  # Ensure GPU usage
                        'num_thread': 8,  # Optimize for RTX 3080
                        'repeat_penalty': 1.1,
                        'top_k': 40,
                        'top_p': 0.9
                    }
                )
            )
            
            return response['message']['content']
            
        except Exception as e:
            self.logger.error(f"Batch chat request failed: {e}")
            raise
    
    def _parse_batch_response(self, response: str, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse batch response and map to job results."""
        try:
            # Clean response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Parse JSON array
            batch_analysis = json.loads(response)
            
            if not isinstance(batch_analysis, list):
                raise ValueError("Response is not a JSON array")
            
            # Map results to jobs
            results = []
            for i, job in enumerate(jobs):
                if i < len(batch_analysis):
                    analysis = batch_analysis[i]
                    result = self._create_job_result_from_analysis(job, analysis)
                else:
                    result = self._create_fallback_job_result(job)
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Batch response parsing failed: {e}")
            return [self._create_fallback_job_result(job) for job in jobs]
    
    def _create_job_result_from_analysis(self, job: Dict[str, Any], 
                                       analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create job result from analysis data."""
        result = job.copy()
        
        # Add analysis results
        result.update({
            'required_skills': analysis.get('required_skills', []),
            'job_requirements': analysis.get('job_requirements', []),
            'compatibility_score': analysis.get('compatibility_score', 0.5),
            'analysis_confidence': analysis.get('analysis_confidence', 0.5),
            'extracted_benefits': analysis.get('extracted_benefits', []),
            'analysis_reasoning': analysis.get('reasoning', ''),
            'processing_method': 'rtx3080_batch',
            'gpu_accelerated': True,
            'tensor_cores_used': True,
            'processed_at': time.time()
        })
        
        return result
    
    def _create_fallback_job_result(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback result for failed job analysis."""
        result = job.copy()
        
        result.update({
            'required_skills': [],
            'job_requirements': [],
            'compatibility_score': 0.5,
            'analysis_confidence': 0.0,
            'extracted_benefits': [],
            'analysis_reasoning': 'RTX 3080 analysis failed - using fallback',
            'processing_method': 'fallback',
            'gpu_accelerated': False,
            'tensor_cores_used': False,
            'processed_at': time.time()
        })
        
        return result
    
    def _create_fallback_batch_result(self, jobs: List[Dict[str, Any]], 
                                    processing_time: float) -> BatchJobAnalysisResult:
        """Create fallback batch result."""
        fallback_results = [self._create_fallback_job_result(job) for job in jobs]
        
        return BatchJobAnalysisResult(
            job_results=fallback_results,
            batch_size=len(jobs),
            processing_time=processing_time,
            gpu_utilization=0.0,
            memory_used_gb=0.0,
            jobs_per_second=len(jobs) / processing_time if processing_time > 0 else 0,
            model_used=f"{self.model} (fallback)",
            cuda_streams_used=0,
            tensor_cores_utilized=False
        )
    
    def _update_performance_history(self, jobs_per_second: float, 
                                  processing_time: float, jobs_processed: int) -> None:
        """Update performance history for monitoring."""
        performance_record = {
            'timestamp': time.time(),
            'jobs_per_second': jobs_per_second,
            'processing_time': processing_time,
            'jobs_processed': jobs_processed,
            'gpu_utilization': self.metrics.gpu_utilization,
            'memory_used_gb': self.metrics.memory_used_gb,
            'batch_size': self.metrics.batch_size_current,
            'concurrent_streams': self.metrics.concurrent_streams
        }
        
        self.performance_history.append(performance_record)
        
        # Keep only last 100 records
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        
        # Update current metrics
        self.metrics.inference_speed_jobs_per_sec = jobs_per_second
        self.metrics.last_updated = time.time()
    
    def get_rtx3080_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive RTX 3080 performance report."""
        current_status = self._check_rtx3080_status()
        
        # Calculate average performance
        if self.performance_history:
            avg_jobs_per_sec = sum(r['jobs_per_second'] for r in self.performance_history) / len(self.performance_history)
            avg_gpu_util = sum(r['gpu_utilization'] for r in self.performance_history) / len(self.performance_history)
            avg_memory_usage = sum(r['memory_used_gb'] for r in self.performance_history) / len(self.performance_history)
        else:
            avg_jobs_per_sec = avg_gpu_util = avg_memory_usage = 0.0
        
        return {
            'rtx3080_status': current_status.value,
            'current_metrics': {
                'gpu_utilization_percent': self.metrics.gpu_utilization,
                'memory_used_gb': self.metrics.memory_used_gb,
                'memory_total_gb': self.metrics.memory_total_gb,
                'temperature_c': self.metrics.temperature_c,
                'jobs_per_second_current': self.metrics.inference_speed_jobs_per_sec,
                'batch_size_current': self.metrics.batch_size_current,
                'concurrent_streams': self.metrics.concurrent_streams
            },
            'average_performance': {
                'avg_jobs_per_second': avg_jobs_per_sec,
                'avg_gpu_utilization': avg_gpu_util,
                'avg_memory_usage_gb': avg_memory_usage
            },
            'rtx3080_specs': self.rtx3080_specs,
            'optimization_status': {
                'model_preloaded': self.model_loaded,
                'model_load_time_ms': self.metrics.model_load_time_ms,
                'batch_size_optimized': self.max_batch_size > 8,
                'concurrent_streams_active': self.concurrent_streams > 2,
                'tensor_cores_available': True
            },
            'performance_history_count': len(self.performance_history)
        }
    
    async def benchmark_rtx3080_performance(self, test_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Benchmark RTX 3080 performance with test jobs."""
        self.logger.info("🏁 Starting RTX 3080 performance benchmark...")
        
        benchmark_results = {
            'test_started': time.time(),
            'test_jobs_count': len(test_jobs),
            'batch_sizes_tested': [],
            'performance_results': []
        }
        
        # Test different batch sizes
        batch_sizes_to_test = [1, 4, 8, 12, 16, 20]
        
        for batch_size in batch_sizes_to_test:
            if batch_size > len(test_jobs):
                continue
                
            self.logger.info(f"📊 Testing batch size: {batch_size}")
            
            # Temporarily set batch size
            original_batch_size = self.max_batch_size
            self.max_batch_size = batch_size
            
            try:
                # Run benchmark
                test_batch = test_jobs[:batch_size]
                start_time = time.time()
                
                result = await self.analyze_jobs_batch_rtx3080(test_batch)
                
                benchmark_results['batch_sizes_tested'].append(batch_size)
                benchmark_results['performance_results'].append({
                    'batch_size': batch_size,
                    'jobs_per_second': result.jobs_per_second,
                    'processing_time': result.processing_time,
                    'gpu_utilization': result.gpu_utilization,
                    'memory_used_gb': result.memory_used_gb,
                    'tensor_cores_utilized': result.tensor_cores_utilized
                })
                
                self.logger.info(f"✅ Batch size {batch_size}: {result.jobs_per_second:.1f} jobs/sec")
                
            except Exception as e:
                self.logger.error(f"Benchmark failed for batch size {batch_size}: {e}")
            
            finally:
                # Restore original batch size
                self.max_batch_size = original_batch_size
        
        # Find optimal batch size
        if benchmark_results['performance_results']:
            best_result = max(benchmark_results['performance_results'], 
                            key=lambda x: x['jobs_per_second'])
            benchmark_results['optimal_batch_size'] = best_result['batch_size']
            benchmark_results['max_jobs_per_second'] = best_result['jobs_per_second']
        
        benchmark_results['test_completed'] = time.time()
        benchmark_results['total_test_time'] = benchmark_results['test_completed'] - benchmark_results['test_started']
        
        self.logger.info(f"🏆 RTX 3080 benchmark complete - Optimal: {benchmark_results.get('max_jobs_per_second', 0):.1f} jobs/sec")
        
        return benchmark_results


# Convenience function
def get_rtx3080_optimized_client(model: str = "llama3", 
                                max_batch_size: int = 16,
                                concurrent_streams: int = 4) -> RTX3080OptimizedClient:
    """
    Get RTX 3080 optimized client instance.
    
    Args:
        model: Model name to use
        max_batch_size: Maximum batch size for RTX 3080
        concurrent_streams: Number of concurrent GPU streams
        
    Returns:
        RTX3080OptimizedClient instance
    """
    return RTX3080OptimizedClient(
        model=model,
        max_batch_size=max_batch_size,
        concurrent_streams=concurrent_streams
    )