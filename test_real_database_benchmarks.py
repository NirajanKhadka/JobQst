"""
Real Database Job Benchmarking System
Uses actual scraped jobs from the existing database for comprehensive benchmarks.
"""

import asyncio
import time
import sys
import gc
import sqlite3
import statistics
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.live import Live

# GPU and CUDA imports
try:
    import torch
    import torch.nn as nn
    from torch.cuda.amp import autocast, GradScaler
    from transformers import AutoTokenizer, AutoModel
    CUDA_AVAILABLE = torch.cuda.is_available()
    if CUDA_AVAILABLE:
        print(f"🚀 GPU: {torch.cuda.get_device_name(0)} ({torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB)")
except ImportError:
    CUDA_AVAILABLE = False
    print("⚠️ GPU libraries not available - using CPU mode")

# Monitoring
try:
    import psutil
    import GPUtil
    import pynvml
    pynvml.nvmlInit()
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

console = Console()

@dataclass
class RealJobData:
    """Real job data from the database."""
    id: str
    title: str
    company: str
    description: str
    location: str
    url: str
    salary_range: Optional[str] = None
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    posted_date: Optional[str] = None
    scraped_date: Optional[str] = None
    source: str = "database"
    
    def to_text(self) -> str:
        """Convert job to comprehensive text for processing."""
        parts = [
            f"Job Title: {self.title}",
            f"Company: {self.company}",
            f"Location: {self.location}",
            f"Description: {self.description}"
        ]
        
        if self.requirements:
            parts.append(f"Requirements: {self.requirements}")
        if self.benefits:
            parts.append(f"Benefits: {self.benefits}")
        if self.salary_range:
            parts.append(f"Salary: {self.salary_range}")
        
        return " | ".join(parts)

@dataclass
class ProcessingVariationMetrics:
    """Metrics for different processing variations."""
    variation_name: str
    total_jobs: int
    processing_time: float
    jobs_per_second: float
    
    # Memory metrics
    memory_peak_mb: float
    memory_average_mb: float
    memory_growth_mb: float
    
    # GPU metrics
    gpu_memory_used_mb: float = 0
    gpu_utilization_percent: float = 0
    cuda_memory_allocated_mb: float = 0
    cuda_memory_cached_mb: float = 0
    
    # Quality metrics
    skills_extracted_total: int = 0
    skills_per_job_avg: float = 0
    confidence_scores: List[float] = field(default_factory=list)
    confidence_average: float = 0
    confidence_std: float = 0
    
    # Analysis metrics
    reasoning_steps_total: int = 0
    compatibility_scores: List[float] = field(default_factory=list)
    compatibility_average: float = 0
    
    # System metrics
    cpu_usage_percent: float = 0
    batch_size_used: int = 1
    errors_count: int = 0
    success_rate: float = 1.0
    
    def calculate_efficiency_score(self) -> float:
        """Calculate overall efficiency score."""
        speed_score = min(self.jobs_per_second / 100, 1.0)
        quality_score = self.confidence_average
        memory_efficiency = max(0, 1 - (self.memory_peak_mb / 2000))
        
        return (speed_score * 0.4 + quality_score * 0.4 + memory_efficiency * 0.2)

class RealDatabaseJobFetcher:
    """Fetches real jobs from the existing database."""
    
    def __init__(self, db_path: str = "data/jobs.db"):
        self.db_path = db_path
        self._analyze_database_structure()
    
    def _analyze_database_structure(self):
        """Analyze the existing database structure."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            console.print(f"[cyan]📊 Database Analysis: Found {len(tables)} tables[/cyan]")
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                console.print(f"[green]Table '{table_name}': {len(columns)} columns[/green]")
                for col in columns:
                    console.print(f"  - {col[1]} ({col[2]})")
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                console.print(f"  [yellow]Rows: {count}[/yellow]")
            
            conn.close()
            
        except Exception as e:
            console.print(f"[red]❌ Database analysis failed: {e}[/red]")
    
    async def fetch_real_jobs(self, limit: int = 50) -> List[RealJobData]:
        """Fetch real jobs from the existing database."""
        console.print(f"[cyan]🔍 Fetching {limit} real jobs from database...[/cyan]")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Try different possible table structures
            possible_queries = [
                # Modern structure
                """
                SELECT id, title, company, description, location, url, 
                       salary_range, requirements, benefits, posted_date, scraped_date
                FROM jobs 
                ORDER BY scraped_date DESC 
                LIMIT ?
                """,
                # Alternative structure
                """
                SELECT id, title, company, description, location, url, 
                       NULL as salary_range, NULL as requirements, NULL as benefits, 
                       posted_date, created_at as scraped_date
                FROM jobs 
                ORDER BY created_at DESC 
                LIMIT ?
                """,
                # Basic structure
                """
                SELECT id, title, company, description, location, url, 
                       NULL, NULL, NULL, NULL, NULL
                FROM jobs 
                LIMIT ?
                """,
                # Minimal structure
                """
                SELECT COALESCE(id, rowid) as id, title, company, description, 
                       COALESCE(location, '') as location, COALESCE(url, '') as url,
                       NULL, NULL, NULL, NULL, NULL
                FROM jobs 
                LIMIT ?
                """
            ]
            
            jobs = []
            for query in possible_queries:
                try:
                    cursor.execute(query, (limit,))
                    rows = cursor.fetchall()
                    
                    if rows:
                        console.print(f"[green]✅ Successfully fetched {len(rows)} jobs using query variant[/green]")
                        
                        for row in rows:
                            # Handle different row lengths
                            job_data = list(row) + [None] * (11 - len(row))
                            
                            jobs.append(RealJobData(
                                id=str(job_data[0]) if job_data[0] else f"job_{len(jobs)+1}",
                                title=job_data[1] or "Unknown Title",
                                company=job_data[2] or "Unknown Company",
                                description=job_data[3] or "No description available",
                                location=job_data[4] or "Unknown Location",
                                url=job_data[5] or "",
                                salary_range=job_data[6],
                                requirements=job_data[7],
                                benefits=job_data[8],
                                posted_date=job_data[9],
                                scraped_date=job_data[10],
                                source="database"
                            ))
                        break
                        
                except sqlite3.Error as e:
                    console.print(f"[yellow]⚠️ Query variant failed: {e}[/yellow]")
                    continue
            
            conn.close()
            
            if not jobs:
                console.print("[red]❌ No jobs found in database[/red]")
                return []
            
            # Display sample of fetched jobs
            console.print(f"[green]✅ Successfully fetched {len(jobs)} real jobs from database[/green]")
            
            return jobs
            
        except Exception as e:
            console.print(f"[red]❌ Failed to fetch jobs from database: {e}[/red]")
            return []

class ProcessingVariation:
    """Base class for different processing variations."""
    
    def __init__(self, name: str, use_gpu: bool = False):
        self.name = name
        self.use_gpu = use_gpu and CUDA_AVAILABLE
        self.device = torch.device("cuda" if self.use_gpu else "cpu")
        
        # Load model if needed
        self.model = None
        self.tokenizer = None
        if self.use_gpu:
            self._load_model()
        
        # Skill patterns
        self.skill_patterns = {
            "programming": ["python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "php", "ruby"],
            "web": ["react", "angular", "vue", "django", "flask", "spring", "express", "node.js"],
            "database": ["sql", "mysql", "postgresql", "mongodb", "redis", "oracle"],
            "cloud": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform"],
            "data": ["pandas", "numpy", "tensorflow", "pytorch", "spark", "hadoop"],
            "mobile": ["ios", "android", "react native", "flutter", "swift", "kotlin"]
        }
    
    def _load_model(self):
        """Load transformer model for GPU processing."""
        try:
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            
            if self.use_gpu:
                self.model = self.model.to(self.device)
                self.model = self.model.half()
            
            self.model.eval()
            console.print(f"[green]✅ Model loaded for {self.name}[/green]")
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Model loading failed for {self.name}: {e}[/yellow]")
    
    async def process_jobs(self, jobs: List[RealJobData]) -> ProcessingVariationMetrics:
        """Process jobs using this variation's strategy."""
        raise NotImplementedError
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from job text."""
        text_lower = text.lower()
        found_skills = []
        
        for category, skills in self.skill_patterns.items():
            for skill in skills:
                if skill in text_lower:
                    found_skills.append(skill.title())
        
        return list(set(found_skills))  # Remove duplicates
    
    def _analyze_experience_level(self, text: str) -> str:
        """Analyze experience level from job text."""
        text_lower = text.lower()
        
        if any(term in text_lower for term in ["senior", "lead", "principal", "architect"]):
            return "Senior"
        elif any(term in text_lower for term in ["junior", "entry", "graduate", "intern"]):
            return "Junior"
        elif any(term in text_lower for term in ["mid", "intermediate"]):
            return "Mid-level"
        else:
            return "Mid-level"  # Default
    
    def _calculate_compatibility(self, skills: List[str], experience: str) -> float:
        """Calculate job compatibility score."""
        # Mock user profile
        user_skills = {"Python", "JavaScript", "React", "SQL", "AWS"}
        user_experience = "Mid-level"
        
        # Skill match
        job_skills_set = {skill.lower() for skill in skills}
        user_skills_lower = {skill.lower() for skill in user_skills}
        
        if job_skills_set:
            skill_match = len(job_skills_set & user_skills_lower) / len(job_skills_set)
        else:
            skill_match = 0.5
        
        # Experience match
        exp_scores = {"Junior": 1, "Mid-level": 2, "Senior": 3}
        user_score = exp_scores.get(user_experience, 2)
        job_score = exp_scores.get(experience, 2)
        exp_match = max(0, 1 - abs(user_score - job_score) * 0.3)
        
        return skill_match * 0.7 + exp_match * 0.3
    
    def _generate_confidence(self, skills: List[str], job: RealJobData) -> float:
        """Generate confidence score for analysis."""
        factors = []
        
        # Skills confidence
        factors.append(min(len(skills) / 8, 1.0))
        
        # Description quality
        desc_length = len(job.description) if job.description else 0
        factors.append(min(desc_length / 500, 1.0))
        
        # Data completeness
        completeness = sum([
            1 if job.title else 0,
            1 if job.company else 0,
            1 if job.location else 0,
            1 if job.url else 0
        ]) / 4
        factors.append(completeness)
        
        return sum(factors) / len(factors)

class CPUSequentialProcessor(ProcessingVariation):
    """CPU-based sequential processing."""
    
    def __init__(self):
        super().__init__("CPU Sequential", use_gpu=False)
    
    async def process_jobs(self, jobs: List[RealJobData]) -> ProcessingVariationMetrics:
        """Process jobs sequentially on CPU."""
        start_time = time.time()
        process = psutil.Process()
        memory_samples = [process.memory_info().rss / 1024 / 1024]
        
        all_skills = []
        all_confidences = []
        all_compatibilities = []
        reasoning_steps = 0
        errors = 0
        
        console.print(f"[cyan]🔄 {self.name}: Processing {len(jobs)} jobs sequentially...[/cyan]")
        
        for i, job in enumerate(jobs):
            try:
                # Sequential processing steps
                text = job.to_text()
                
                # Step 1: Extract skills
                skills = self._extract_skills(text)
                all_skills.append(skills)
                
                # Step 2: Analyze experience
                experience = self._analyze_experience_level(text)
                
                # Step 3: Calculate compatibility
                compatibility = self._calculate_compatibility(skills, experience)
                all_compatibilities.append(compatibility)
                
                # Step 4: Generate confidence
                confidence = self._generate_confidence(skills, job)
                all_confidences.append(confidence)
                
                reasoning_steps += 4
                
                # Memory sampling
                if i % 10 == 0:
                    memory_samples.append(process.memory_info().rss / 1024 / 1024)
                
                # Small delay to simulate processing
                await asyncio.sleep(0.001)
                
            except Exception as e:
                errors += 1
                console.print(f"[red]❌ Error processing job {job.id}: {e}[/red]")
        
        processing_time = time.time() - start_time
        
        # Calculate metrics
        total_skills = sum(len(skills) for skills in all_skills)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        avg_compatibility = sum(all_compatibilities) / len(all_compatibilities) if all_compatibilities else 0
        
        return ProcessingVariationMetrics(
            variation_name=self.name,
            total_jobs=len(jobs),
            processing_time=processing_time,
            jobs_per_second=len(jobs) / processing_time if processing_time > 0 else 0,
            memory_peak_mb=max(memory_samples),
            memory_average_mb=sum(memory_samples) / len(memory_samples),
            memory_growth_mb=memory_samples[-1] - memory_samples[0],
            skills_extracted_total=total_skills,
            skills_per_job_avg=total_skills / len(jobs) if jobs else 0,
            confidence_scores=all_confidences,
            confidence_average=avg_confidence,
            confidence_std=statistics.stdev(all_confidences) if len(all_confidences) > 1 else 0,
            reasoning_steps_total=reasoning_steps,
            compatibility_scores=all_compatibilities,
            compatibility_average=avg_compatibility,
            cpu_usage_percent=psutil.cpu_percent(),
            batch_size_used=1,
            errors_count=errors,
            success_rate=(len(jobs) - errors) / len(jobs) if jobs else 0
        )

class GPUBatchProcessor(ProcessingVariation):
    """GPU-based batch processing."""
    
    def __init__(self):
        super().__init__("GPU Batch", use_gpu=True)
        self.batch_size = 16 if self.use_gpu else 4
    
    async def process_jobs(self, jobs: List[RealJobData]) -> ProcessingVariationMetrics:
        """Process jobs in batches on GPU."""
        start_time = time.time()
        process = psutil.Process()
        memory_samples = [process.memory_info().rss / 1024 / 1024]
        
        all_skills = []
        all_confidences = []
        all_compatibilities = []
        reasoning_steps = 0
        errors = 0
        
        console.print(f"[cyan]🔄 {self.name}: Processing {len(jobs)} jobs in batches of {self.batch_size}...[/cyan]")
        
        # Process in batches
        for i in range(0, len(jobs), self.batch_size):
            batch = jobs[i:i + self.batch_size]
            
            try:
                # Batch processing
                batch_texts = [job.to_text() for job in batch]
                
                # GPU embeddings if available
                if self.model and self.tokenizer:
                    await self._extract_embeddings_batch(batch_texts)
                
                # Process each job in batch
                for job in batch:
                    text = job.to_text()
                    
                    skills = self._extract_skills(text)
                    all_skills.append(skills)
                    
                    experience = self._analyze_experience_level(text)
                    compatibility = self._calculate_compatibility(skills, experience)
                    all_compatibilities.append(compatibility)
                    
                    confidence = self._generate_confidence(skills, job)
                    all_confidences.append(confidence)
                    
                    reasoning_steps += 4
                
                # Memory cleanup
                if self.use_gpu:
                    torch.cuda.empty_cache()
                
                memory_samples.append(process.memory_info().rss / 1024 / 1024)
                await asyncio.sleep(0.01)
                
            except Exception as e:
                errors += len(batch)
                console.print(f"[red]❌ Batch processing error: {e}[/red]")
        
        processing_time = time.time() - start_time
        
        # GPU stats
        gpu_stats = self._get_gpu_stats()
        
        # Calculate metrics
        total_skills = sum(len(skills) for skills in all_skills)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        avg_compatibility = sum(all_compatibilities) / len(all_compatibilities) if all_compatibilities else 0
        
        return ProcessingVariationMetrics(
            variation_name=self.name,
            total_jobs=len(jobs),
            processing_time=processing_time,
            jobs_per_second=len(jobs) / processing_time if processing_time > 0 else 0,
            memory_peak_mb=max(memory_samples),
            memory_average_mb=sum(memory_samples) / len(memory_samples),
            memory_growth_mb=memory_samples[-1] - memory_samples[0],
            gpu_memory_used_mb=gpu_stats["memory_used"],
            gpu_utilization_percent=gpu_stats["utilization"],
            cuda_memory_allocated_mb=gpu_stats["cuda_allocated"],
            cuda_memory_cached_mb=gpu_stats["cuda_cached"],
            skills_extracted_total=total_skills,
            skills_per_job_avg=total_skills / len(jobs) if jobs else 0,
            confidence_scores=all_confidences,
            confidence_average=avg_confidence,
            confidence_std=statistics.stdev(all_confidences) if len(all_confidences) > 1 else 0,
            reasoning_steps_total=reasoning_steps,
            compatibility_scores=all_compatibilities,
            compatibility_average=avg_compatibility,
            cpu_usage_percent=psutil.cpu_percent(),
            batch_size_used=self.batch_size,
            errors_count=errors,
            success_rate=(len(jobs) - errors) / len(jobs) if jobs else 0
        )
    
    async def _extract_embeddings_batch(self, texts: List[str]):
        """Extract embeddings for batch of texts."""
        if not self.model or not self.tokenizer:
            return
        
        try:
            inputs = self.tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
            
            if self.use_gpu:
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                if self.use_gpu:
                    with autocast():
                        outputs = self.model(**inputs)
                else:
                    outputs = self.model(**inputs)
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Embedding extraction failed: {e}[/yellow]")
    
    def _get_gpu_stats(self) -> Dict[str, float]:
        """Get GPU statistics."""
        if not self.use_gpu or not MONITORING_AVAILABLE:
            return {"memory_used": 0, "utilization": 0, "cuda_allocated": 0, "cuda_cached": 0}
        
        try:
            stats = {
                "cuda_allocated": torch.cuda.memory_allocated(0) / 1024 / 1024,
                "cuda_cached": torch.cuda.memory_reserved(0) / 1024 / 1024,
                "memory_used": 0,
                "utilization": 0
            }
            
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                stats["memory_used"] = gpu.memoryUsed
                stats["utilization"] = gpu.load * 100
            
            return stats
        except:
            return {"memory_used": 0, "utilization": 0, "cuda_allocated": 0, "cuda_cached": 0}

class ParallelCPUProcessor(ProcessingVariation):
    """Parallel CPU processing with multiple workers."""
    
    def __init__(self):
        super().__init__("Parallel CPU", use_gpu=False)
        self.max_workers = min(8, psutil.cpu_count() or 4)
    
    async def process_jobs(self, jobs: List[RealJobData]) -> ProcessingVariationMetrics:
        """Process jobs in parallel on CPU."""
        start_time = time.time()
        process = psutil.Process()
        memory_samples = [process.memory_info().rss / 1024 / 1024]
        
        all_skills = []
        all_confidences = []
        all_compatibilities = []
        reasoning_steps = 0
        errors = 0
        
        console.print(f"[cyan]🔄 {self.name}: Processing {len(jobs)} jobs with {self.max_workers} workers...[/cyan]")
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_job_with_semaphore(job):
            async with semaphore:
                try:
                    text = job.to_text()
                    
                    skills = self._extract_skills(text)
                    experience = self._analyze_experience_level(text)
                    compatibility = self._calculate_compatibility(skills, experience)
                    confidence = self._generate_confidence(skills, job)
                    
                    return {
                        "skills": skills,
                        "compatibility": compatibility,
                        "confidence": confidence,
                        "reasoning_steps": 4
                    }
                except Exception as e:
                    console.print(f"[red]❌ Error processing job {job.id}: {e}[/red]")
                    return None
        
        # Process all jobs concurrently
        tasks = [process_job_with_semaphore(job) for job in jobs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect results
        for result in results:
            if result and not isinstance(result, Exception):
                all_skills.append(result["skills"])
                all_compatibilities.append(result["compatibility"])
                all_confidences.append(result["confidence"])
                reasoning_steps += result["reasoning_steps"]
            else:
                errors += 1
        
        processing_time = time.time() - start_time
        memory_samples.append(process.memory_info().rss / 1024 / 1024)
        
        # Calculate metrics
        total_skills = sum(len(skills) for skills in all_skills)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        avg_compatibility = sum(all_compatibilities) / len(all_compatibilities) if all_compatibilities else 0
        
        return ProcessingVariationMetrics(
            variation_name=self.name,
            total_jobs=len(jobs),
            processing_time=processing_time,
            jobs_per_second=len(jobs) / processing_time if processing_time > 0 else 0,
            memory_peak_mb=max(memory_samples),
            memory_average_mb=sum(memory_samples) / len(memory_samples),
            memory_growth_mb=memory_samples[-1] - memory_samples[0],
            skills_extracted_total=total_skills,
            skills_per_job_avg=total_skills / len(jobs) if jobs else 0,
            confidence_scores=all_confidences,
            confidence_average=avg_confidence,
            confidence_std=statistics.stdev(all_confidences) if len(all_confidences) > 1 else 0,
            reasoning_steps_total=reasoning_steps,
            compatibility_scores=all_compatibilities,
            compatibility_average=avg_compatibility,
            cpu_usage_percent=psutil.cpu_percent(),
            batch_size_used=self.max_workers,
            errors_count=errors,
            success_rate=(len(jobs) - errors) / len(jobs) if jobs else 0
        )

def display_comprehensive_comparison(metrics_list: List[ProcessingVariationMetrics], jobs: List[RealJobData]):
    """Display comprehensive comparison of all processing variations."""
    console.print("\n[bold green]🏆 Comprehensive Processing Variation Comparison[/bold green]")
    
    # Performance comparison table
    perf_table = Table(title="⚡ Performance Comparison")
    perf_table.add_column("Variation", style="cyan")
    perf_table.add_column("Jobs/Sec", style="yellow")
    perf_table.add_column("Total Time", style="green")
    perf_table.add_column("Success Rate", style="blue")
    perf_table.add_column("Efficiency", style="magenta")
    
    for metrics in metrics_list:
        perf_table.add_row(
            metrics.variation_name,
            f"{metrics.jobs_per_second:.2f}",
            f"{metrics.processing_time:.3f}s",
            f"{metrics.success_rate:.1%}",
            f"{metrics.calculate_efficiency_score():.1%}"
        )
    
    console.print(perf_table)
    
    # Resource utilization comparison
    resource_table = Table(title="💾 Resource Utilization")
    resource_table.add_column("Variation", style="cyan")
    resource_table.add_column("Peak Memory", style="yellow")
    resource_table.add_column("Memory Growth", style="green")
    resource_table.add_column("CPU Usage", style="blue")
    resource_table.add_column("GPU Memory", style="magenta")
    
    for metrics in metrics_list:
        gpu_mem = f"{metrics.gpu_memory_used_mb:.0f}MB" if metrics.gpu_memory_used_mb > 0 else "N/A"
        
        resource_table.add_row(
            metrics.variation_name,
            f"{metrics.memory_peak_mb:.1f}MB",
            f"{metrics.memory_growth_mb:.1f}MB",
            f"{metrics.cpu_usage_percent:.1f}%",
            gpu_mem
        )
    
    console.print(resource_table)
    
    # Analysis quality comparison
    quality_table = Table(title="🎯 Analysis Quality")
    quality_table.add_column("Variation", style="cyan")
    quality_table.add_column("Skills/Job", style="yellow")
    quality_table.add_column("Confidence", style="green")
    quality_table.add_column("Compatibility", style="blue")
    quality_table.add_column("Reasoning Steps", style="magenta")
    
    for metrics in metrics_list:
        quality_table.add_row(
            metrics.variation_name,
            f"{metrics.skills_per_job_avg:.1f}",
            f"{metrics.confidence_average:.1%}",
            f"{metrics.compatibility_average:.1%}",
            f"{metrics.reasoning_steps_total}"
        )
    
    console.print(quality_table)
    
    # Database job analysis
    db_table = Table(title="📊 Database Job Analysis")
    db_table.add_column("Metric", style="cyan")
    db_table.add_column("Value", style="yellow")
    db_table.add_column("Details", style="green")
    
    # Analyze job sources and types
    companies = [job.company for job in jobs if job.company]
    locations = [job.location for job in jobs if job.location]
    
    from collections import Counter
    company_counts = Counter(companies)
    location_counts = Counter(locations)
    
    db_table.add_row("Total Jobs Processed", str(len(jobs)), "From real database")
    db_table.add_row("Unique Companies", str(len(company_counts)), f"Top: {company_counts.most_common(1)[0][0] if company_counts else 'N/A'}")
    db_table.add_row("Unique Locations", str(len(location_counts)), f"Top: {location_counts.most_common(1)[0][0] if location_counts else 'N/A'}")
    
    # Job description analysis
    desc_lengths = [len(job.description) for job in jobs if job.description]
    if desc_lengths:
        avg_desc_length = sum(desc_lengths) / len(desc_lengths)
        db_table.add_row("Avg Description Length", f"{avg_desc_length:.0f} chars", f"Range: {min(desc_lengths)}-{max(desc_lengths)}")
    
    console.print(db_table)
    
    # Performance insights and recommendations
    console.print("\n[bold blue]💡 Performance Insights[/bold blue]")
    
    # Find best performer in each category
    fastest = max(metrics_list, key=lambda x: x.jobs_per_second)
    most_efficient_memory = min(metrics_list, key=lambda x: x.memory_peak_mb)
    highest_quality = max(metrics_list, key=lambda x: x.confidence_average)
    
    console.print(f"[green]🚀 Fastest Processing: {fastest.variation_name} ({fastest.jobs_per_second:.2f} jobs/sec)[/green]")
    console.print(f"[blue]💾 Most Memory Efficient: {most_efficient_memory.variation_name} ({most_efficient_memory.memory_peak_mb:.1f}MB peak)[/blue]")
    console.print(f"[yellow]🎯 Highest Quality: {highest_quality.variation_name} ({highest_quality.confidence_average:.1%} confidence)[/yellow]")
    
    # System recommendations
    console.print("\n[bold blue]🎯 System Recommendations[/bold blue]")
    
    if CUDA_AVAILABLE:
        gpu_metrics = [m for m in metrics_list if m.gpu_memory_used_mb > 0]
        if gpu_metrics:
            best_gpu = max(gpu_metrics, key=lambda x: x.jobs_per_second)
            console.print(f"[cyan]• GPU Acceleration: {best_gpu.variation_name} shows best GPU utilization[/cyan]")
        else:
            console.print("[cyan]• GPU Available but underutilized - consider GPU-optimized processing[/cyan]")
    else:
        console.print("[cyan]• No GPU available - CPU parallel processing recommended[/cyan]")
    
    # Memory recommendations
    max_memory = max(m.memory_peak_mb for m in metrics_list)
    if max_memory > 1000:
        console.print("[cyan]• High memory usage detected - consider batch size optimization[/cyan]")
    
    # Quality recommendations
    avg_confidence = sum(m.confidence_average for m in metrics_list) / len(metrics_list)
    if avg_confidence < 0.7:
        console.print("[cyan]• Low confidence scores - consider improving data quality or analysis algorithms[/cyan]")
    
    console.print(f"\n[bold green]🎉 Benchmark completed! Processed {len(jobs)} real database jobs[/bold green]")

async def main():
    """Main benchmarking function with real database jobs."""
    console.print(Panel(
        "[bold blue]🔬 Real Database Job Benchmarking System[/bold blue]\n"
        "[cyan]Processing real scraped jobs with multiple variations[/cyan]\n"
        "[yellow]CPU Sequential • GPU Batch • Parallel CPU • Memory Optimization[/yellow]",
        title="Real Database Benchmark"
    ))
    
    # Initialize database fetcher
    db_fetcher = RealDatabaseJobFetcher()
    
    # Fetch real jobs from database
    console.print("[cyan]🔍 Fetching real jobs from existing database...[/cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        fetch_task = progress.add_task("Fetching from database...", total=1)
        jobs = await db_fetcher.fetch_real_jobs(50)  # Fetch 50 real jobs
        progress.update(fetch_task, completed=1)
    
    if not jobs:
        console.print("[red]❌ No jobs found in database. Please run the scraper first.[/red]")
        return
    
    console.print(f"[green]✅ Successfully loaded {len(jobs)} real jobs from database[/green]")
    
    # Display job preview
    preview_table = Table(title="📋 Real Database Jobs Preview")
    preview_table.add_column("ID", style="cyan")
    preview_table.add_column("Title", style="yellow")
    preview_table.add_column("Company", style="green")
    preview_table.add_column("Location", style="blue")
    
    for job in jobs[:5]:  # Show first 5
        preview_table.add_row(
            str(job.id)[:10] + "..." if len(str(job.id)) > 10 else str(job.id),
            job.title[:30] + "..." if len(job.title) > 30 else job.title,
            job.company[:20] + "..." if len(job.company) > 20 else job.company,
            job.location[:15] + "..." if len(job.location) > 15 else job.location
        )
    
    if len(jobs) > 5:
        preview_table.add_row("...", f"+ {len(jobs) - 5} more jobs", "...", "...")
    
    console.print(preview_table)
    
    # Initialize processing variations
    variations = [
        CPUSequentialProcessor(),
        ParallelCPUProcessor(),
    ]
    
    # Add GPU processor if available
    if CUDA_AVAILABLE:
        variations.append(GPUBatchProcessor())
    
    console.print(f"\n[cyan]🚀 Testing {len(variations)} processing variations...[/cyan]")
    
    # Test each variation
    all_metrics = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        for variation in variations:
            task = progress.add_task(f"Testing {variation.name}...", total=1)
            
            try:
                console.print(f"\n[yellow]🔄 Running {variation.name}...[/yellow]")
                metrics = await variation.process_jobs(jobs)
                all_metrics.append(metrics)
                
                console.print(f"[green]✅ {variation.name} completed: "
                            f"{metrics.jobs_per_second:.2f} jobs/sec, "
                            f"{metrics.confidence_average:.1%} confidence[/green]")
                
            except Exception as e:
                console.print(f"[red]❌ {variation.name} failed: {e}[/red]")
            
            progress.update(task, completed=1)
            
            # Cleanup between variations
            gc.collect()
            if CUDA_AVAILABLE:
                torch.cuda.empty_cache()
            
            await asyncio.sleep(0.5)
    
    # Display comprehensive comparison
    if all_metrics:
        display_comprehensive_comparison(all_metrics, jobs)
    else:
        console.print("[red]❌ All processing variations failed[/red]")
    
    console.print("\n[bold green]🎉 Real database benchmarking completed![/bold green]")

if __name__ == "__main__":
    asyncio.run(main())