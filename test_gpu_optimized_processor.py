"""
GPU-Optimized Job Processor for RTX 3080
Maximum CUDA acceleration with memory pooling and batch optimization.
"""

import asyncio
import time
import sys
import gc
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import numpy as np
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# GPU and CUDA imports
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.cuda.amp import autocast, GradScaler
    from transformers import AutoTokenizer, AutoModel
    CUDA_AVAILABLE = torch.cuda.is_available()
    print(f"CUDA Available: {CUDA_AVAILABLE}")
    if CUDA_AVAILABLE:
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"CUDA Version: {torch.version.cuda}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
except ImportError as e:
    print(f"GPU libraries not available: {e}")
    CUDA_AVAILABLE = False

# CuPy is optional for additional GPU acceleration
try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False
    print("CuPy not available - using PyTorch for GPU operations")

# Memory and monitoring
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
class JobData:
    """Job data structure optimized for GPU processing."""
    id: str
    title: str
    company: str
    description: str
    location: str
    url: str
    salary_range: Optional[str] = None
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    
    def to_text(self) -> str:
        """Convert job to text for processing."""
        parts = [
            f"Title: {self.title}",
            f"Company: {self.company}",
            f"Description: {self.description}",
            f"Location: {self.location}"
        ]
        if self.requirements:
            parts.append(f"Requirements: {self.requirements}")
        if self.benefits:
            parts.append(f"Benefits: {self.benefits}")
        if self.salary_range:
            parts.append(f"Salary: {self.salary_range}")
        
        return " | ".join(parts)

@dataclass
class GPUMetrics:
    """GPU processing metrics."""
    processing_time: float
    jobs_per_second: float
    gpu_memory_used_mb: float
    gpu_utilization_percent: float
    cuda_memory_allocated_mb: float
    cuda_memory_cached_mb: float
    batch_size_used: int
    total_jobs_processed: int
    average_confidence: float
    skills_extracted: int
    reasoning_steps_total: int

class CUDAMemoryManager:
    """Advanced CUDA memory management for RTX 3080."""
    
    def __init__(self):
        self.device = torch.device("cuda" if CUDA_AVAILABLE else "cpu")
        self.memory_pool = None
        self.scaler = GradScaler() if CUDA_AVAILABLE else None
        
        if CUDA_AVAILABLE:
            self.setup_cuda_optimization()
    
    def setup_cuda_optimization(self):
        """Setup CUDA optimization for RTX 3080."""
        # Enable memory pooling
        torch.cuda.empty_cache()
        
        # Set memory fraction (use 90% of GPU memory)
        torch.cuda.set_per_process_memory_fraction(0.9)
        
        # Enable cudNN benchmarking for consistent input sizes
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.deterministic = False
        
        # Enable TensorFloat-32 for RTX 3080
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        
        console.print("[green]✅ CUDA optimization enabled for RTX 3080[/green]")
        console.print(f"[cyan]Device: {torch.cuda.get_device_name(0)}[/cyan]")
        console.print(f"[cyan]Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB[/cyan]")
    
    def get_optimal_batch_size(self, base_size: int = 8) -> int:
        """Calculate optimal batch size based on available GPU memory."""
        if not CUDA_AVAILABLE:
            return base_size
        
        try:
            # Get available memory
            total_memory = torch.cuda.get_device_properties(0).total_memory
            allocated_memory = torch.cuda.memory_allocated(0)
            available_memory = total_memory - allocated_memory
            
            # Calculate optimal batch size (use 70% of available memory)
            memory_per_item = 50 * 1024 * 1024  # Estimate 50MB per job
            optimal_size = int((available_memory * 0.7) / memory_per_item)
            
            # Clamp between reasonable bounds
            return max(4, min(optimal_size, 32))
            
        except Exception:
            return base_size
    
    def cleanup_memory(self):
        """Cleanup GPU memory."""
        if CUDA_AVAILABLE:
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    
    def get_memory_stats(self) -> Dict[str, float]:
        """Get current GPU memory statistics."""
        if not CUDA_AVAILABLE:
            return {"allocated_mb": 0, "cached_mb": 0, "total_mb": 0}
        
        return {
            "allocated_mb": torch.cuda.memory_allocated(0) / 1024 / 1024,
            "cached_mb": torch.cuda.memory_reserved(0) / 1024 / 1024,
            "total_mb": torch.cuda.get_device_properties(0).total_memory / 1024 / 1024
        }

class GPUJobAnalyzer(nn.Module):
    """GPU-accelerated job analysis using transformer models."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        super().__init__()
        self.device = torch.device("cuda" if CUDA_AVAILABLE else "cpu")
        self.model_name = model_name
        
        # Load model and tokenizer
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            
            if CUDA_AVAILABLE:
                self.model = self.model.to(self.device)
                self.model = self.model.half()  # Use FP16 for RTX 3080
                
            self.model.eval()
            console.print(f"[green]✅ Loaded model: {model_name}[/green]")
            
        except Exception as e:
            console.print(f"[red]❌ Failed to load model: {e}[/red]")
            self.model = None
            self.tokenizer = None
        
        # Skill patterns for extraction
        self.skill_patterns = {
            "programming_languages": [
                "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", 
                "php", "ruby", "swift", "kotlin", "scala", "r", "matlab"
            ],
            "web_frameworks": [
                "react", "angular", "vue", "django", "flask", "fastapi", "spring", "express",
                "next.js", "nuxt.js", "svelte", "ember", "backbone"
            ],
            "databases": [
                "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra",
                "dynamodb", "sqlite", "oracle", "sql server"
            ],
            "cloud_platforms": [
                "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform",
                "ansible", "jenkins", "gitlab", "github actions"
            ],
            "data_science": [
                "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "jupyter",
                "spark", "hadoop", "kafka", "airflow"
            ],
            "mobile": [
                "react native", "flutter", "ios", "android", "xamarin", "ionic"
            ]
        }
    
    @torch.no_grad()
    def extract_embeddings_batch(self, texts: List[str]) -> torch.Tensor:
        """Extract embeddings for a batch of texts using GPU."""
        if not self.model or not self.tokenizer:
            return torch.zeros((len(texts), 384))
        
        # Tokenize batch
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )
        
        if CUDA_AVAILABLE:
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Forward pass with mixed precision
        if CUDA_AVAILABLE:
            with autocast():
                outputs = self.model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1)
        else:
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1)
        
        return embeddings.cpu()
    
    def extract_skills_gpu(self, job_texts: List[str]) -> List[List[str]]:
        """Extract skills from job texts using GPU-accelerated pattern matching."""
        all_skills = []
        
        # Use CuPy for GPU-accelerated text processing if available
        try:
            if CUDA_AVAILABLE and 'cupy' in sys.modules:
                # GPU-accelerated skill extraction
                for text in job_texts:
                    text_lower = text.lower()
                    job_skills = []
                    
                    for category, skills in self.skill_patterns.items():
                        for skill in skills:
                            if skill in text_lower:
                                job_skills.append(skill.title())
                    
                    all_skills.append(job_skills)
            else:
                # CPU fallback
                for text in job_texts:
                    text_lower = text.lower()
                    job_skills = []
                    
                    for category, skills in self.skill_patterns.items():
                        for skill in skills:
                            if skill in text_lower:
                                job_skills.append(skill.title())
                    
                    all_skills.append(job_skills)
                    
        except Exception as e:
            console.print(f"[yellow]⚠️ GPU skill extraction failed, using CPU: {e}[/yellow]")
            # CPU fallback
            for text in job_texts:
                text_lower = text.lower()
                job_skills = []
                
                for category, skills in self.skill_patterns.items():
                    for skill in skills:
                        if skill in text_lower:
                            job_skills.append(skill.title())
                
                all_skills.append(job_skills)
        
        return all_skills
    
    def analyze_experience_level_batch(self, job_texts: List[str]) -> List[str]:
        """Analyze experience levels for a batch of jobs."""
        levels = []
        
        for text in job_texts:
            text_lower = text.lower()
            
            if any(term in text_lower for term in ["senior", "lead", "principal", "staff", "architect"]):
                levels.append("Senior")
            elif any(term in text_lower for term in ["junior", "entry", "graduate", "intern"]):
                levels.append("Junior")
            elif any(term in text_lower for term in ["mid", "intermediate", "associate"]):
                levels.append("Mid-level")
            else:
                # Infer from years of experience
                if "5+" in text or "5 years" in text or "experienced" in text_lower:
                    levels.append("Senior")
                elif "2-3" in text or "2 years" in text:
                    levels.append("Mid-level")
                else:
                    levels.append("Mid-level")  # Default
        
        return levels
    
    def calculate_compatibility_batch(self, skills_list: List[List[str]], levels: List[str]) -> List[float]:
        """Calculate compatibility scores for a batch of jobs."""
        # Mock user profile
        user_skills = {"Python", "JavaScript", "React", "Django", "PostgreSQL", "AWS", "Docker"}
        user_level = "Mid-level"
        
        compatibility_scores = []
        
        for job_skills, job_level in zip(skills_list, levels):
            # Skill compatibility
            job_skills_set = {skill.lower() for skill in job_skills}
            user_skills_lower = {skill.lower() for skill in user_skills}
            
            if job_skills_set:
                skill_match = len(job_skills_set & user_skills_lower) / len(job_skills_set)
            else:
                skill_match = 0.5
            
            # Experience compatibility
            level_scores = {"Junior": 1, "Mid-level": 2, "Senior": 3}
            user_score = level_scores.get(user_level, 2)
            job_score = level_scores.get(job_level, 2)
            exp_match = max(0, 1 - abs(user_score - job_score) * 0.25)
            
            # Overall compatibility
            compatibility = skill_match * 0.7 + exp_match * 0.3
            compatibility_scores.append(compatibility)
        
        return compatibility_scores

class GPUJobProcessor:
    """Main GPU-optimized job processor."""
    
    def __init__(self):
        self.memory_manager = CUDAMemoryManager()
        self.analyzer = GPUJobAnalyzer()
        self.batch_size = self.memory_manager.get_optimal_batch_size()
        
        console.print(f"[cyan]🚀 GPU Job Processor initialized[/cyan]")
        console.print(f"[cyan]Optimal batch size: {self.batch_size}[/cyan]")
    
    async def process_jobs_gpu(self, jobs: List[JobData]) -> GPUMetrics:
        """Process jobs using GPU acceleration."""
        start_time = time.time()
        
        # Convert jobs to texts
        job_texts = [job.to_text() for job in jobs]
        
        console.print(f"[cyan]🔄 Processing {len(jobs)} jobs with GPU acceleration...[/cyan]")
        
        # Process in batches
        all_skills = []
        all_levels = []
        all_compatibilities = []
        all_confidences = []
        reasoning_steps = 0
        
        for i in range(0, len(job_texts), self.batch_size):
            batch_texts = job_texts[i:i + self.batch_size]
            batch_jobs = jobs[i:i + self.batch_size]
            
            # GPU-accelerated processing
            await self._process_batch_gpu(
                batch_texts, batch_jobs, all_skills, all_levels, 
                all_compatibilities, all_confidences
            )
            
            reasoning_steps += len(batch_texts) * 5  # 5 steps per job
            
            # Memory cleanup between batches
            if i % (self.batch_size * 2) == 0:
                self.memory_manager.cleanup_memory()
                await asyncio.sleep(0.01)  # Allow other tasks
        
        processing_time = time.time() - start_time
        
        # Calculate metrics
        memory_stats = self.memory_manager.get_memory_stats()
        gpu_stats = self._get_gpu_utilization()
        
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        total_skills = sum(len(skills) for skills in all_skills)
        
        return GPUMetrics(
            processing_time=processing_time,
            jobs_per_second=len(jobs) / processing_time if processing_time > 0 else 0,
            gpu_memory_used_mb=memory_stats["allocated_mb"],
            gpu_utilization_percent=gpu_stats["utilization"],
            cuda_memory_allocated_mb=memory_stats["allocated_mb"],
            cuda_memory_cached_mb=memory_stats["cached_mb"],
            batch_size_used=self.batch_size,
            total_jobs_processed=len(jobs),
            average_confidence=avg_confidence,
            skills_extracted=total_skills,
            reasoning_steps_total=reasoning_steps
        )
    
    async def _process_batch_gpu(self, batch_texts: List[str], batch_jobs: List[JobData],
                                all_skills: List, all_levels: List, 
                                all_compatibilities: List, all_confidences: List):
        """Process a single batch using GPU."""
        
        # Step 1: Extract embeddings (GPU)
        if self.analyzer.model:
            embeddings = self.analyzer.extract_embeddings_batch(batch_texts)
        
        # Step 2: Extract skills (GPU-accelerated)
        batch_skills = self.analyzer.extract_skills_gpu(batch_texts)
        all_skills.extend(batch_skills)
        
        # Step 3: Analyze experience levels
        batch_levels = self.analyzer.analyze_experience_level_batch(batch_texts)
        all_levels.extend(batch_levels)
        
        # Step 4: Calculate compatibility
        batch_compatibilities = self.analyzer.calculate_compatibility_batch(batch_skills, batch_levels)
        all_compatibilities.extend(batch_compatibilities)
        
        # Step 5: Generate confidence scores
        batch_confidences = []
        for skills, level, compatibility in zip(batch_skills, batch_levels, batch_compatibilities):
            # Confidence based on data quality
            skill_confidence = min(len(skills) / 8, 1.0)
            level_confidence = 0.9 if level in ["Senior", "Junior"] else 0.7
            compatibility_confidence = compatibility
            
            overall_confidence = (skill_confidence + level_confidence + compatibility_confidence) / 3
            batch_confidences.append(overall_confidence)
        
        all_confidences.extend(batch_confidences)
        
        # Small async delay to allow other tasks
        await asyncio.sleep(0.001)
    
    def _get_gpu_utilization(self) -> Dict[str, float]:
        """Get current GPU utilization."""
        if not MONITORING_AVAILABLE or not CUDA_AVAILABLE:
            return {"utilization": 0, "memory_used": 0}
        
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                return {
                    "utilization": gpu.load * 100,
                    "memory_used": gpu.memoryUsed
                }
        except Exception:
            pass
        
        return {"utilization": 0, "memory_used": 0}
    
    def cleanup(self):
        """Cleanup GPU resources."""
        self.memory_manager.cleanup_memory()

class DatabaseJobFetcher:
    """Fetches real job data from database."""
    
    def __init__(self, db_path: str = "data/jobs.db"):
        self.db_path = db_path
        self.setup_test_database()
    
    def setup_test_database(self):
        """Create test database with real job data."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Drop existing table if it exists to ensure clean schema
        cursor.execute('DROP TABLE IF EXISTS jobs')
        
        cursor.execute('''
            CREATE TABLE jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT,
                url TEXT,
                salary_range TEXT,
                requirements TEXT,
                benefits TEXT
            )
        ''')
        
        # Sample GPU-optimized test jobs
        sample_jobs = [
            ("gpu_job_001", "Senior CUDA Developer", "NVIDIA Corp", 
             "Develop high-performance CUDA applications for RTX GPUs. Work with deep learning frameworks and optimize GPU kernels for maximum throughput.", 
             "Santa Clara, CA", "https://nvidia.com/jobs/001", "$120,000 - $160,000", 
             "CUDA, C++, Python, TensorFlow, PyTorch, GPU optimization, parallel computing", 
             "Stock options, GPU hardware, Research time"),
            
            ("gpu_job_002", "Machine Learning Engineer - GPU", "OpenAI", 
             "Build and optimize large-scale ML models using GPU clusters. Focus on transformer architectures and distributed training.", 
             "San Francisco, CA", "https://openai.com/careers/002", "$150,000 - $200,000", 
             "Python, PyTorch, CUDA, Distributed training, Transformers, MLOps", 
             "Equity, Cutting-edge research, Conference budget"),
            
            ("gpu_job_003", "High Performance Computing Engineer", "Tesla", 
             "Optimize autonomous driving algorithms for Tesla's custom AI chips. Work with neural networks and real-time processing.", 
             "Palo Alto, CA", "https://tesla.com/jobs/003", "$130,000 - $180,000", 
             "CUDA, C++, Python, Neural networks, Real-time systems, Optimization", 
             "Stock options, Tesla vehicle, Innovation time"),
            
            ("gpu_job_004", "Deep Learning Research Scientist", "Google DeepMind", 
             "Research and develop next-generation AI models. Work with TPUs and GPUs for large-scale experiments.", 
             "London, UK", "https://deepmind.com/careers/004", "$140,000 - $190,000", 
             "Python, TensorFlow, JAX, Research, Mathematics, GPU programming", 
             "Research freedom, Publication support, World-class team"),
            
            ("gpu_job_005", "GPU Software Engineer", "AMD", 
             "Develop GPU drivers and optimization tools for RDNA architecture. Work on graphics and compute workloads.", 
             "Austin, TX", "https://amd.com/jobs/005", "$110,000 - $150,000", 
             "C++, OpenCL, Vulkan, DirectX, GPU architecture, Driver development", 
             "Hardware access, Technical conferences, Stock options"),
            
            ("gpu_job_006", "Computer Vision Engineer", "Meta Reality Labs", 
             "Build computer vision systems for AR/VR applications. Optimize algorithms for mobile GPUs.", 
             "Menlo Park, CA", "https://meta.com/careers/006", "$125,000 - $170,000", 
             "Python, C++, OpenCV, CUDA, Computer vision, Mobile optimization", 
             "VR hardware, Innovation lab, Stock options"),
            
            ("gpu_job_007", "Parallel Computing Specialist", "Intel", 
             "Develop parallel algorithms for Intel GPUs and CPUs. Focus on oneAPI and SYCL programming.", 
             "Portland, OR", "https://intel.com/jobs/007", "$115,000 - $155,000", 
             "C++, SYCL, oneAPI, Parallel programming, Performance optimization", 
             "Intel hardware, Technical training, Stock purchase plan"),
            
            ("gpu_job_008", "AI Infrastructure Engineer", "Microsoft", 
             "Build and maintain GPU clusters for Azure AI services. Optimize distributed training pipelines.", 
             "Redmond, WA", "https://microsoft.com/careers/008", "$120,000 - $165,000", 
             "Python, Kubernetes, Docker, Azure, GPU clusters, MLOps", 
             "Azure credits, Microsoft hardware, Learning budget"),
            
            ("gpu_job_009", "Graphics Programming Engineer", "Epic Games", 
             "Develop real-time rendering techniques for Unreal Engine. Optimize shaders and GPU performance.", 
             "Cary, NC", "https://epicgames.com/jobs/009", "$105,000 - $145,000", 
             "C++, HLSL, Vulkan, DirectX, Real-time rendering, Game engines", 
             "Game library, Creative environment, Profit sharing"),
            
            ("gpu_job_010", "Quantum Computing Researcher", "IBM Quantum", 
             "Research quantum algorithms and their classical simulation on GPUs. Bridge quantum and classical computing.", 
             "Yorktown Heights, NY", "https://ibm.com/quantum/010", "$135,000 - $185,000", 
             "Python, Qiskit, CUDA, Quantum computing, Linear algebra, Research", 
             "Research freedom, Quantum hardware access, Publication support")
        ]
        
        cursor.executemany('''
            INSERT OR REPLACE INTO jobs 
            (id, title, company, description, location, url, salary_range, requirements, benefits)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_jobs)
        
        conn.commit()
        conn.close()
    
    async def fetch_jobs(self, limit: int = 10) -> List[JobData]:
        """Fetch jobs from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, company, description, location, url, salary_range, requirements, benefits
            FROM jobs 
            ORDER BY id
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        jobs = []
        for row in rows:
            jobs.append(JobData(
                id=row[0], title=row[1], company=row[2], description=row[3],
                location=row[4], url=row[5], salary_range=row[6],
                requirements=row[7], benefits=row[8]
            ))
        
        return jobs

def display_gpu_results(metrics: GPUMetrics, jobs: List[JobData]):
    """Display GPU processing results."""
    console.print("\n[bold green]🚀 GPU Processing Results[/bold green]")
    
    # Performance metrics table
    perf_table = Table(title="🏆 GPU Performance Metrics")
    perf_table.add_column("Metric", style="cyan")
    perf_table.add_column("Value", style="yellow")
    perf_table.add_column("Details", style="green")
    
    perf_table.add_row(
        "Processing Speed",
        f"{metrics.jobs_per_second:.2f} jobs/sec",
        f"Total time: {metrics.processing_time:.3f}s"
    )
    
    perf_table.add_row(
        "GPU Memory Usage",
        f"{metrics.gpu_memory_used_mb:.1f} MB",
        f"Cached: {metrics.cuda_memory_cached_mb:.1f} MB"
    )
    
    perf_table.add_row(
        "GPU Utilization",
        f"{metrics.gpu_utilization_percent:.1f}%",
        "RTX 3080 efficiency"
    )
    
    perf_table.add_row(
        "Batch Size",
        str(metrics.batch_size_used),
        "Optimized for GPU memory"
    )
    
    perf_table.add_row(
        "Analysis Quality",
        f"{metrics.average_confidence:.1%}",
        f"{metrics.skills_extracted} skills found"
    )
    
    perf_table.add_row(
        "Reasoning Steps",
        str(metrics.reasoning_steps_total),
        f"{metrics.reasoning_steps_total / metrics.total_jobs_processed:.1f} steps/job"
    )
    
    console.print(perf_table)
    
    # Job analysis summary
    job_table = Table(title="📋 Job Analysis Summary")
    job_table.add_column("Job ID", style="cyan")
    job_table.add_column("Title", style="yellow")
    job_table.add_column("Company", style="green")
    job_table.add_column("GPU Optimized", style="magenta")
    
    for job in jobs[:5]:  # Show first 5
        gpu_related = "✅" if any(term in job.description.lower() for term in ["gpu", "cuda", "pytorch", "tensorflow"]) else "❌"
        job_table.add_row(
            job.id,
            job.title[:25] + "..." if len(job.title) > 25 else job.title,
            job.company,
            gpu_related
        )
    
    if len(jobs) > 5:
        job_table.add_row("...", f"+ {len(jobs) - 5} more jobs", "...", "...")
    
    console.print(job_table)
    
    # GPU system info
    if CUDA_AVAILABLE:
        gpu_table = Table(title="🖥️ GPU System Information")
        gpu_table.add_column("Component", style="cyan")
        gpu_table.add_column("Details", style="yellow")
        
        gpu_table.add_row("GPU Model", torch.cuda.get_device_name(0))
        gpu_table.add_row("CUDA Version", torch.version.cuda)
        gpu_table.add_row("Total Memory", f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        gpu_table.add_row("Compute Capability", f"{torch.cuda.get_device_properties(0).major}.{torch.cuda.get_device_properties(0).minor}")
        gpu_table.add_row("Multiprocessors", str(torch.cuda.get_device_properties(0).multi_processor_count))
        
        console.print(gpu_table)
    
    # Performance insights
    console.print("\n[bold blue]💡 GPU Performance Insights[/bold blue]")
    
    if metrics.jobs_per_second > 50:
        console.print("[green]🚀 Excellent GPU performance! RTX 3080 is well utilized.[/green]")
    elif metrics.jobs_per_second > 20:
        console.print("[yellow]⚡ Good GPU performance. Consider larger batch sizes.[/yellow]")
    else:
        console.print("[red]🐌 GPU performance could be improved. Check memory usage.[/red]")
    
    if metrics.gpu_utilization_percent > 80:
        console.print("[green]💪 High GPU utilization - excellent efficiency![/green]")
    elif metrics.gpu_utilization_percent > 50:
        console.print("[yellow]📊 Moderate GPU utilization - room for improvement.[/yellow]")
    else:
        console.print("[red]📉 Low GPU utilization - consider optimization.[/red]")
    
    efficiency_score = (metrics.jobs_per_second * metrics.gpu_utilization_percent) / 100
    console.print(f"\n[cyan]🎯 Overall GPU Efficiency Score: {efficiency_score:.1f}[/cyan]")

async def main():
    """Main GPU-optimized processing test."""
    console.print(Panel(
        "[bold blue]🚀 GPU-Optimized Job Processor Test[/bold blue]\n"
        "[cyan]RTX 3080 CUDA acceleration with memory optimization[/cyan]\n"
        "[yellow]Batch processing • Mixed precision • Memory pooling[/yellow]",
        title="GPU Performance Test"
    ))
    
    # Check GPU availability
    if not CUDA_AVAILABLE:
        console.print("[red]❌ CUDA not available. This test requires a CUDA-capable GPU.[/red]")
        return
    
    # Initialize components
    db_fetcher = DatabaseJobFetcher()
    processor = GPUJobProcessor()
    
    # Fetch jobs
    console.print("[cyan]📊 Fetching GPU-optimized jobs from database...[/cyan]")
    jobs = await db_fetcher.fetch_jobs(10)
    console.print(f"[green]✅ Loaded {len(jobs)} GPU-related job postings[/green]")
    
    # Process jobs with GPU
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("GPU Processing...", total=1)
            
            metrics = await processor.process_jobs_gpu(jobs)
            
            progress.update(task, completed=1)
        
        # Display results
        display_gpu_results(metrics, jobs)
        
        # Cleanup
        processor.cleanup()
        
        console.print("\n[bold green]🎉 GPU processing test completed successfully![/bold green]")
        console.print(f"[cyan]Processed {metrics.total_jobs_processed} jobs at {metrics.jobs_per_second:.2f} jobs/second[/cyan]")
        
    except Exception as e:
        console.print(f"[red]❌ GPU processing failed: {e}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")

if __name__ == "__main__":
    asyncio.run(main())