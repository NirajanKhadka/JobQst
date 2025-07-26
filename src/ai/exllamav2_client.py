"""
ExLlamaV2 Client for RTX 3080 Optimized Job Processing
Pure ExLlamaV2 implementation with OpenHermes model for maximum RTX 3080 performance.
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

try:
    from exllamav2 import (
        ExLlamaV2, 
        ExLlamaV2Config, 
        ExLlamaV2Cache, 
        ExLlamaV2Tokenizer,
        ExLlamaV2DynamicGenerator
    )
    EXLLAMAV2_AVAILABLE = True
except ImportError:
    EXLLAMAV2_AVAILABLE = False
    ExLlamaV2 = None
    ExLlamaV2Config = None
    ExLlamaV2Cache = None
    ExLlamaV2Tokenizer = None
    ExLlamaV2DynamicGenerator = None

try:
    import torch
    import GPUtil
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    GPUtil = None

logger = logging.getLogger(__name__)

@dataclass
class JobAnalysisResult:
    """Result of job analysis with ExLlamaV2."""
    required_skills: List[str]
    job_requirements: List[str]
    compatibility_score: float
    analysis_confidence: float
    extracted_benefits: List[str]
    reasoning: str
    processing_time: float
    model_used: str
    gpu_memory_used_mb: float
    tokens_processed: int

@dataclass
class BatchJobAnalysisResult:
    """Result of batch job analysis with ExLlamaV2."""
    job_results: List[Dict[str, Any]]
    batch_size: int
    processing_time: float
    gpu_utilization: float
    memory_used_gb: float
    jobs_per_second: float
    model_used: str
    total_tokens_processed: int
    rtx3080_optimized: bool

class ExLlamaV2Client:
    """
    ExLlamaV2 client optimized for RTX 3080 with OpenHermes model.
    
    Features:
    - Direct GPU memory management
    - Batch processing for RTX 3080
    - OpenHermes model optimization
    - Real-time GPU monitoring
    """
    
    def __init__(self, 
                 model_path: str = None,
                 max_seq_len: int = 4096,
                 max_batch_size: int = 8,
                 gpu_split: Optional[List[float]] = None):
        """
        Initialize ExLlamaV2 client for RTX 3080.
        
        Args:
            model_path: Path to OpenHermes model directory
            max_seq_len: Maximum sequence length
            max_batch_size: Maximum batch size for RTX 3080
            gpu_split: GPU memory split (None for auto)
        """
        if not EXLLAMAV2_AVAILABLE:
            raise ImportError("ExLlamaV2 not available. Install with: pip install exllamav2")
        
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch not available. Install with: pip install torch")
        
        self.model_path = model_path or self._find_openhermes_model()
        self.max_seq_len = max_seq_len
        self.max_batch_size = max_batch_size
        self.gpu_split = gpu_split
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # ExLlamaV2 components
        self.config = None
        self.model = None
        self.cache = None
        self.tokenizer = None
        self.generator = None
        
        # Performance tracking
        self.total_tokens_processed = 0
        self.total_jobs_processed = 0
        self.initialization_time = 0.0
        
        # Initialize ExLlamaV2
        self._initialize_exllamav2()
    
    def _find_openhermes_model(self) -> str:
        """Find OpenHermes model path."""
        # Common OpenHermes model locations
        possible_paths = [
            "models/OpenHermes-2.5-Mistral-7B-GPTQ",
            "models/OpenHermes-2.5-Mistral-7B",
            "../models/OpenHermes-2.5-Mistral-7B-GPTQ",
            "C:/models/OpenHermes-2.5-Mistral-7B-GPTQ",
            "D:/models/OpenHermes-2.5-Mistral-7B-GPTQ"
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                self.logger.info(f"Found OpenHermes model at: {path}")
                return path
        
        # Default path - user needs to download model
        default_path = "models/OpenHermes-2.5-Mistral-7B-GPTQ"
        self.logger.warning(f"OpenHermes model not found. Please download to: {default_path}")
        return default_path
    
    def _initialize_exllamav2(self) -> None:
        """Initialize ExLlamaV2 components for RTX 3080."""
        start_time = time.time()
        
        try:
            self.logger.info("🚀 Initializing ExLlamaV2 for RTX 3080...")
            
            # Check RTX 3080 availability
            self._check_rtx3080()
            
            # Initialize config
            self.logger.info(f"📁 Loading config from: {self.model_path}")
            self.config = ExLlamaV2Config()
            self.config.model_dir = self.model_path
            self.config.prepare()
            
            # Set RTX 3080 optimizations
            self.config.max_seq_len = self.max_seq_len
            self.config.scale_pos_emb = 1.0
            self.config.scale_alpha_value = 1.0
            
            # Initialize model
            self.logger.info("🧠 Loading ExLlamaV2 model...")
            self.model = ExLlamaV2(self.config)
            
            # Set GPU split for RTX 3080 (10GB VRAM)
            if self.gpu_split is None:
                # Auto-detect optimal GPU split for RTX 3080
                self.gpu_split = [8.5]  # Use 8.5GB, leave 1.5GB for system
            
            self.logger.info(f"💾 Loading model to RTX 3080 VRAM: {self.gpu_split}GB")
            self.model.load(self.gpu_split)
            
            # Initialize tokenizer
            self.logger.info("🔤 Loading tokenizer...")
            self.tokenizer = ExLlamaV2Tokenizer(self.config)
            
            # Initialize cache for RTX 3080
            self.logger.info("🗄️ Initializing cache...")
            self.cache = ExLlamaV2Cache(self.model, lazy=True)
            
            # Initialize generator
            self.logger.info("⚡ Initializing generator...")
            self.generator = ExLlamaV2DynamicGenerator(
                model=self.model,
                cache=self.cache,
                tokenizer=self.tokenizer
            )
            
            self.initialization_time = time.time() - start_time
            
            self.logger.info(f"✅ ExLlamaV2 initialized in {self.initialization_time:.2f}s")
            self._log_gpu_status()
            
        except Exception as e:
            self.logger.error(f"ExLlamaV2 initialization failed: {e}")
            raise
    
    def _check_rtx3080(self) -> None:
        """Check RTX 3080 availability and status."""
        try:
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA not available")
            
            gpu_name = torch.cuda.get_device_name(0)
            self.logger.info(f"🎯 GPU detected: {gpu_name}")
            
            if "3080" in gpu_name:
                self.logger.info("🏆 RTX 3080 detected - optimal performance expected")
            else:
                self.logger.warning(f"⚠️ GPU is {gpu_name}, not RTX 3080 - performance may vary")
            
            # Check VRAM
            total_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            self.logger.info(f"💾 Total VRAM: {total_memory:.1f}GB")
            
            if total_memory < 8.0:
                self.logger.warning("⚠️ Less than 8GB VRAM - may need to reduce batch size")
            
        except Exception as e:
            self.logger.error(f"GPU check failed: {e}")
            raise
    
    def _log_gpu_status(self) -> None:
        """Log current GPU status."""
        try:
            if GPUtil:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    self.logger.info(f"📊 GPU Status: {gpu.load*100:.1f}% utilization, "
                                   f"{gpu.memoryUsed}MB / {gpu.memoryTotal}MB VRAM, "
                                   f"{gpu.temperature}°C")
        except Exception as e:
            self.logger.debug(f"Could not get GPU status: {e}")
    
    async def analyze_job_batch(self, jobs: List[Dict[str, Any]], 
                              user_profile: Optional[Dict] = None) -> BatchJobAnalysisResult:
        """
        Analyze multiple jobs in batch using ExLlamaV2.
        
        Args:
            jobs: List of job dictionaries to analyze
            user_profile: Optional user profile for compatibility scoring
            
        Returns:
            BatchJobAnalysisResult with comprehensive batch analysis
        """
        start_time = time.time()
        batch_size = min(len(jobs), self.max_batch_size)
        
        self.logger.info(f"🚀 Starting ExLlamaV2 batch analysis: {batch_size} jobs")
        
        try:
            # Get initial GPU status
            gpu_util_before = self._get_gpu_utilization()
            memory_before = self._get_gpu_memory_used()
            
            # Process jobs in batch
            all_results = []
            total_tokens = 0
            
            # Create batches for processing
            job_batches = [jobs[i:i + batch_size] for i in range(0, len(jobs), batch_size)]
            
            for batch in job_batches:
                batch_results, batch_tokens = await self._process_job_batch(batch, user_profile)
                all_results.extend(batch_results)
                total_tokens += batch_tokens
            
            # Calculate performance metrics
            processing_time = time.time() - start_time
            jobs_per_second = len(all_results) / processing_time if processing_time > 0 else 0
            
            # Get final GPU status
            gpu_util_after = self._get_gpu_utilization()
            memory_after = self._get_gpu_memory_used()
            
            # Update tracking
            self.total_tokens_processed += total_tokens
            self.total_jobs_processed += len(all_results)
            
            result = BatchJobAnalysisResult(
                job_results=all_results,
                batch_size=batch_size,
                processing_time=processing_time,
                gpu_utilization=max(gpu_util_before, gpu_util_after),
                memory_used_gb=memory_after / 1024,
                jobs_per_second=jobs_per_second,
                model_used="OpenHermes-2.5-Mistral-7B",
                total_tokens_processed=total_tokens,
                rtx3080_optimized=True
            )
            
            self.logger.info(f"✅ ExLlamaV2 batch analysis complete: {jobs_per_second:.1f} jobs/sec")
            return result
            
        except Exception as e:
            self.logger.error(f"ExLlamaV2 batch analysis failed: {e}")
            return self._create_fallback_batch_result(jobs, time.time() - start_time)
    
    async def _process_job_batch(self, job_batch: List[Dict[str, Any]], 
                               user_profile: Optional[Dict] = None) -> Tuple[List[Dict[str, Any]], int]:
        """Process a batch of jobs with ExLlamaV2."""
        try:
            # Create batch prompt
            batch_prompt = self._create_batch_prompt(job_batch, user_profile)
            
            # Generate response with ExLlamaV2
            response, tokens_used = await self._generate_response(batch_prompt)
            
            # Parse batch response
            batch_results = self._parse_batch_response(response, job_batch)
            
            return batch_results, tokens_used
            
        except Exception as e:
            self.logger.error(f"Job batch processing failed: {e}")
            fallback_results = [self._create_fallback_job_result(job) for job in job_batch]
            return fallback_results, 0
    
    def _create_batch_prompt(self, jobs: List[Dict[str, Any]], 
                           user_profile: Optional[Dict] = None) -> str:
        """Create optimized batch prompt for OpenHermes."""
        
        system_prompt = """You are an expert job analyst. Analyze job postings and extract key information in JSON format."""
        
        user_prompt = "Analyze these job postings and return a JSON array:\n\n"
        
        for i, job in enumerate(jobs):
            user_prompt += f"""Job {i + 1}:
Title: {job.get('title', 'Unknown')}
Company: {job.get('company', 'Unknown')}
Description: {job.get('description', job.get('job_description', ''))[:500]}

"""
        
        user_prompt += """Return JSON array with this format:
[
    {
        "job_index": 1,
        "required_skills": ["Python", "SQL"],
        "job_requirements": ["3+ years experience"],
        "compatibility_score": 0.85,
        "analysis_confidence": 0.9,
        "extracted_benefits": ["Health insurance"],
        "reasoning": "Good match for skills"
    }
]

Return only valid JSON, no other text."""
        
        # Format for OpenHermes
        full_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        return full_prompt
    
    async def _generate_response(self, prompt: str) -> Tuple[str, int]:
        """Generate response using ExLlamaV2."""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def _generate():
                # Tokenize input
                input_ids = self.tokenizer.encode(prompt)
                tokens_used = input_ids.shape[-1]
                
                # Generate response
                with torch.no_grad():
                    output = self.generator.generate(
                        input_ids=input_ids,
                        max_new_tokens=1000,
                        temperature=0.1,
                        top_p=0.9,
                        top_k=40,
                        repetition_penalty=1.1,
                        stop_conditions=[self.tokenizer.eos_token_id]
                    )
                
                # Decode response
                response = self.tokenizer.decode(output[0])
                
                # Extract only the assistant response
                if "<|im_start|>assistant\n" in response:
                    response = response.split("<|im_start|>assistant\n")[-1]
                if "<|im_end|>" in response:
                    response = response.split("<|im_end|>")[0]
                
                return response.strip(), tokens_used
            
            return await loop.run_in_executor(None, _generate)
            
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")
            return "", 0
    
    def _parse_batch_response(self, response: str, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse batch response from ExLlamaV2."""
        try:
            # Clean response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Parse JSON
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
        
        result.update({
            'required_skills': analysis.get('required_skills', []),
            'job_requirements': analysis.get('job_requirements', []),
            'compatibility_score': analysis.get('compatibility_score', 0.5),
            'analysis_confidence': analysis.get('analysis_confidence', 0.5),
            'extracted_benefits': analysis.get('extracted_benefits', []),
            'analysis_reasoning': analysis.get('reasoning', ''),
            'processing_method': 'exllamav2_openhermes',
            'gpu_accelerated': True,
            'rtx3080_optimized': True,
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
            'analysis_reasoning': 'ExLlamaV2 analysis failed - using fallback',
            'processing_method': 'fallback',
            'gpu_accelerated': False,
            'rtx3080_optimized': False,
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
            model_used="OpenHermes-2.5-Mistral-7B (fallback)",
            total_tokens_processed=0,
            rtx3080_optimized=False
        )
    
    def _get_gpu_utilization(self) -> float:
        """Get current GPU utilization."""
        try:
            if GPUtil:
                gpus = GPUtil.getGPUs()
                if gpus:
                    return gpus[0].load * 100
        except Exception:
            pass
        return 0.0
    
    def _get_gpu_memory_used(self) -> float:
        """Get current GPU memory usage in MB."""
        try:
            if GPUtil:
                gpus = GPUtil.getGPUs()
                if gpus:
                    return gpus[0].memoryUsed
        except Exception:
            pass
        return 0.0
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        return {
            'model_info': {
                'model_path': self.model_path,
                'model_name': 'OpenHermes-2.5-Mistral-7B',
                'max_seq_len': self.max_seq_len,
                'max_batch_size': self.max_batch_size
            },
            'performance_stats': {
                'initialization_time': self.initialization_time,
                'total_jobs_processed': self.total_jobs_processed,
                'total_tokens_processed': self.total_tokens_processed,
                'average_tokens_per_job': self.total_tokens_processed / max(self.total_jobs_processed, 1)
            },
            'gpu_status': {
                'gpu_utilization': self._get_gpu_utilization(),
                'memory_used_mb': self._get_gpu_memory_used(),
                'rtx3080_optimized': True
            },
            'exllamav2_status': {
                'available': EXLLAMAV2_AVAILABLE,
                'model_loaded': self.model is not None,
                'generator_ready': self.generator is not None
            }
        }


# Convenience function
def get_exllamav2_client(model_path: str = None, 
                        max_batch_size: int = 8) -> ExLlamaV2Client:
    """
    Get ExLlamaV2 client instance.
    
    Args:
        model_path: Path to OpenHermes model
        max_batch_size: Maximum batch size for RTX 3080
        
    Returns:
        ExLlamaV2Client instance
    """
    return ExLlamaV2Client(
        model_path=model_path,
        max_batch_size=max_batch_size
    )