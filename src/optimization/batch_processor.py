#!/usr/bin/env python3
"""
High-Performance Batch Processing for Phase 2
Implements efficient batching for GPU/CPU processing with smart fallbacks
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
import numpy as np

try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .hardware_detector import get_hardware_info
from .dynamic_thresholds import get_optimal_processing_config

console = Console()
logger = logging.getLogger(__name__)


class BatchProcessor:
    """High-performance batch processor for Phase 2"""
    
    def __init__(self, user_profile: Dict[str, Any]):
        self.user_profile = user_profile
        self.hardware_config, self.performance_stats = get_hardware_info()
        
        # Initialize model and tokenizer
        self.model = None
        self.tokenizer = None
        self.device = None
        
        if TORCH_AVAILABLE:
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize model with optimal device configuration"""
        try:
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            self.device = torch.device(self.hardware_config.device)
            
            console.print(f"[cyan]🤖 Loading model on {self.device}...[/cyan]")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name).to(self.device)
            
            # Enable optimizations
            if self.device.type == "cuda":
                self.model = self.model.half()  # Use FP16 for speed
                torch.backends.cudnn.benchmark = True
            elif self.device.type == "mps":
                # MPS-specific optimizations
                torch.backends.mps.allow_fallback = True
            
            self.model.eval()  # Set to evaluation mode
            
            console.print(f"[green]✅ Model loaded on {self.hardware_config.device_name}[/green]")
            
        except Exception as e:
            logger.error(f"Model initialization failed: {e}")
            self.model = None
            self.tokenizer = None
    
    async def process_jobs_batch(
        self, 
        jobs_with_stage1: List[Tuple[Dict[str, Any], Any]],
        config: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Process multiple jobs in optimized batches"""
        
        if not jobs_with_stage1:
            return []
        
        # Get optimal configuration
        total_jobs = len(jobs_with_stage1)
        threshold_config, estimates = get_optimal_processing_config(total_jobs)
        
        console.print(f"[bold blue]🚀 Batch Processing {total_jobs} jobs[/bold blue]")
        console.print(f"[cyan]   Device: {self.hardware_config.device_name}[/cyan]")
        console.print(f"[cyan]   Batch Size: {threshold_config.phase2_batch_size}[/cyan]")
        console.print(f"[cyan]   Estimated Time: {estimates['estimated_total_time']:.1f}s[/cyan]")
        
        # Process in batches
        batch_size = threshold_config.phase2_batch_size
        all_results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            
            task = progress.add_task("Processing batches...", total=total_jobs)
            
            for i in range(0, total_jobs, batch_size):
                batch = jobs_with_stage1[i:i + batch_size]
                
                try:
                    # Process batch based on available hardware
                    if self.model is not None and TORCH_AVAILABLE:
                        batch_results = await self._process_batch_gpu(batch)
                    else:
                        batch_results = await self._process_batch_cpu(batch)
                    
                    all_results.extend(batch_results)
                    progress.update(task, advance=len(batch))
                    
                except Exception as e:
                    logger.error(f"Batch processing failed: {e}")
                    # Fallback to individual processing
                    batch_results = await self._process_batch_fallback(batch)
                    all_results.extend(batch_results)
                    progress.update(task, advance=len(batch))
        
        return all_results
    
    async def _process_batch_gpu(
        self, 
        batch: List[Tuple[Dict[str, Any], Any]]
    ) -> List[Dict[str, Any]]:
        """GPU-optimized batch processing"""
        
        def process_batch_sync():
            """Synchronous GPU processing in a thread"""
            job_descriptions = []
            batch_data = []
            
            # Prepare batch data
            for job_data, stage1_result in batch:
                description = job_data.get('description', '')
                job_descriptions.append(description)
                batch_data.append((job_data, stage1_result))
            
            # Batch tokenization
            inputs = self.tokenizer(
                job_descriptions,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(self.device)
            
            # Batch inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1)
                
                # Move to CPU and convert to numpy
                embeddings_np = embeddings.cpu().numpy()
            
            # Process results
            results = []
            for idx, (job_data, stage1_result) in enumerate(batch_data):
                embedding = embeddings_np[idx]
                result = self._create_stage2_result(
                    job_data, stage1_result, embedding
                )
                results.append(result)
            
            return results
        
        # Run GPU processing in thread to avoid blocking event loop
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            results = await loop.run_in_executor(executor, process_batch_sync)
        
        return results
    
    async def _process_batch_cpu(
        self, 
        batch: List[Tuple[Dict[str, Any], Any]]
    ) -> List[Dict[str, Any]]:
        """CPU-optimized batch processing with parallel workers"""
        
        def process_single_cpu(job_data, stage1_result):
            """Process single job on CPU"""
            return self._create_stage2_result_cpu(job_data, stage1_result)
        
        # Use ThreadPoolExecutor for CPU parallelism
        max_workers = min(len(batch), self.hardware_config.optimal_batch_size)
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            tasks = [
                loop.run_in_executor(executor, process_single_cpu, job_data, stage1_result)
                for job_data, stage1_result in batch
            ]
            results = await asyncio.gather(*tasks)
        
        return results
    
    async def _process_batch_fallback(
        self, 
        batch: List[Tuple[Dict[str, Any], Any]]
    ) -> List[Dict[str, Any]]:
        """Fallback processing for when batch processing fails"""
        
        results = []
        for job_data, stage1_result in batch:
            try:
                result = self._create_stage2_result_basic(job_data, stage1_result)
                results.append(result)
            except Exception as e:
                logger.error(f"Fallback processing failed for job: {e}")
                # Create minimal result
                results.append(self._create_minimal_result(job_data, stage1_result))
        
        return results
    
    def _create_stage2_result(
        self, 
        job_data: Dict[str, Any], 
        stage1_result: Any, 
        embedding: np.ndarray
    ) -> Dict[str, Any]:
        """Create comprehensive Stage 2 result with embeddings"""
        
        description = job_data.get('description', '')
        
        # Semantic skill extraction using embeddings
        semantic_skills = self._extract_skills_from_embedding(embedding, description)
        
        # Enhanced compatibility scoring
        semantic_compatibility = self._calculate_semantic_compatibility(
            embedding, stage1_result, semantic_skills
        )
        
        # Sentiment analysis
        sentiment = self._analyze_sentiment_simple(description)
        
        return {
            'semantic_skills': semantic_skills,
            'semantic_compatibility': semantic_compatibility,
            'job_sentiment': sentiment,
            'skill_embeddings': embedding.tolist(),
            'contextual_understanding': f"Job focuses on {', '.join(semantic_skills[:3])}",
            'processing_method': 'gpu_batch',
            'processing_time': 0.0  # Will be calculated at batch level
        }
    
    def _create_stage2_result_cpu(
        self, 
        job_data: Dict[str, Any], 
        stage1_result: Any
    ) -> Dict[str, Any]:
        """Create Stage 2 result using CPU-only methods"""
        
        description = job_data.get('description', '')
        
        # Rule-based skill extraction
        semantic_skills = self._extract_skills_rule_based(description)
        
        # Simple compatibility boost
        semantic_compatibility = getattr(stage1_result, 'basic_compatibility', 0.5) * 1.1
        
        # Simple sentiment analysis
        sentiment = self._analyze_sentiment_simple(description)
        
        return {
            'semantic_skills': semantic_skills,
            'semantic_compatibility': min(0.95, semantic_compatibility),
            'job_sentiment': sentiment,
            'skill_embeddings': None,
            'contextual_understanding': f"CPU analysis: {len(semantic_skills)} skills found",
            'processing_method': 'cpu_batch',
            'processing_time': 0.0
        }
    
    def _create_stage2_result_basic(
        self, 
        job_data: Dict[str, Any], 
        stage1_result: Any
    ) -> Dict[str, Any]:
        """Create basic Stage 2 result as fallback"""
        
        return {
            'semantic_skills': [],
            'semantic_compatibility': getattr(stage1_result, 'basic_compatibility', 0.5),
            'job_sentiment': 'neutral',
            'skill_embeddings': None,
            'contextual_understanding': 'Basic processing',
            'processing_method': 'fallback',
            'processing_time': 0.0
        }
    
    def _create_minimal_result(
        self, 
        job_data: Dict[str, Any], 
        stage1_result: Any
    ) -> Dict[str, Any]:
        """Create minimal result when everything fails"""
        
        return {
            'semantic_skills': [],
            'semantic_compatibility': 0.5,
            'job_sentiment': 'unknown',
            'skill_embeddings': None,
            'contextual_understanding': 'Error in processing',
            'processing_method': 'error_fallback',
            'processing_time': 0.0
        }
    
    def _extract_skills_from_embedding(
        self, 
        embedding: np.ndarray, 
        description: str
    ) -> List[str]:
        """Extract skills using embedding similarity"""
        # Simplified implementation - in practice, you'd compare with skill embeddings
        skills = []
        
        # Use simple keyword extraction as baseline
        common_skills = [
            'python', 'javascript', 'java', 'sql', 'react', 'node.js',
            'aws', 'docker', 'kubernetes', 'git', 'linux', 'machine learning'
        ]
        
        description_lower = description.lower()
        for skill in common_skills:
            if skill in description_lower:
                skills.append(skill)
        
        return skills[:10]  # Limit to top 10 skills
    
    def _extract_skills_rule_based(self, description: str) -> List[str]:
        """Extract skills using rule-based approach"""
        skills = []
        
        # Enhanced skill patterns
        skill_patterns = {
            'python': r'\bpython\b',
            'javascript': r'\b(javascript|js)\b',
            'react': r'\breact\b',
            'sql': r'\bsql\b',
            'aws': r'\b(aws|amazon web services)\b',
            'docker': r'\bdocker\b',
            'git': r'\bgit\b',
            'machine learning': r'\b(machine learning|ml)\b'
        }
        
        import re
        description_lower = description.lower()
        
        for skill, pattern in skill_patterns.items():
            if re.search(pattern, description_lower):
                skills.append(skill)
        
        return skills
    
    def _calculate_semantic_compatibility(
        self, 
        embedding: np.ndarray, 
        stage1_result: Any, 
        skills: List[str]
    ) -> float:
        """Calculate enhanced compatibility using semantic information"""
        
        base_compatibility = getattr(stage1_result, 'basic_compatibility', 0.5)
        
        # Boost based on skill count
        skill_boost = min(0.2, len(skills) * 0.02)
        
        # Combine scores
        semantic_compatibility = base_compatibility + skill_boost
        
        return min(0.95, semantic_compatibility)
    
    def _analyze_sentiment_simple(self, description: str) -> str:
        """Simple sentiment analysis using keywords"""
        
        positive_keywords = ['exciting', 'innovative', 'growth', 'opportunity', 'dynamic']
        negative_keywords = ['challenging', 'demanding', 'pressure', 'tight deadlines']
        
        description_lower = description.lower()
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in description_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in description_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
