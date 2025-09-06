#!/usr/bin/env python3
"""
Two-Stage Job Processing Architecture

Stage 1: Fast Processor (10 workers)
- Basic data extraction (title, company, location, salary)
- Rule-based skill matching and filtering
- Compatibility scoring based on keyword matching
- Language and seniority filtering

Stage 2: Extended Processor
- Additional skill extraction using keyword patterns
- Basic sentiment analysis using keyword indicators
- Improved compatibility scoring with weighted factors
"""

import os
import asyncio
import time
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# PERFORMANCE FIX: Lazy import for heavy AI libraries
# Check if heavy AI is disabled via environment variables
if os.environ.get("DISABLE_HEAVY_AI") == "1":
    TORCH_AVAILABLE = False
    torch = None
    AutoTokenizer = None
    AutoModel = None
else:
    # Conditional torch import for GPU support (lazy loaded when needed)
    try:
        import torch
        from transformers import AutoTokenizer, AutoModel
        TORCH_AVAILABLE = True
    except ImportError:
        TORCH_AVAILABLE = False
        torch = None
        AutoTokenizer = None
        AutoModel = None

import numpy as np
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from .custom_data_extractor import CustomDataExtractor, get_custom_data_extractor
from .custom_extractor import CustomExtractor, get_Improved_custom_extractor

console = Console()
logger = logging.getLogger(__name__)

@dataclass
class Stage1Result:
    """Result from Stage 1 CPU-bound processing"""
    # Basic extracted data
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    experience_level: Optional[str] = None
    employment_type: Optional[str] = None
    
    # Improved fields
    remote_work_option: Optional[str] = None  # "remote", "hybrid", "on-site", "not_specified"
    job_posted_date: Optional[str] = None     # When the job was posted
    application_deadline: Optional[str] = None  # Application deadline if mentioned
    required_years_experience: Optional[str] = None  # "0-2", "3-5", "5+", etc.
    education_requirements: Optional[str] = None     # Degree requirements
    industry: Optional[str] = None            # Tech, Finance, Healthcare, etc.
    
    # Fast analysis
    basic_skills: List[str] = None
    basic_requirements: List[str] = None
    basic_compatibility: float = 0.0
    
    # Filtering flags
    is_french: bool = False
    is_senior: bool = False
    passes_basic_filter: bool = True
    
    # Processing metadata
    processing_time: float = 0.0
    confidence: float = 0.0
    worker_id: int = 0
    
    def __post_init__(self):
        if self.basic_skills is None:
            self.basic_skills = []
        if self.basic_requirements is None:
            self.basic_requirements = []

@dataclass
class Stage2Result:
    """Result from Stage 2 CPU-based semantic processing"""
    # Improved Text analysis
    semantic_skills: List[str] = None
    contextual_requirements: List[str] = None
    semantic_compatibility: float = 0.0
    
    # Improved analysis
    job_sentiment: str = "neutral"  # positive, neutral, negative
    skill_embeddings: Optional[np.ndarray] = None
    contextual_understanding: str = ""
    
    # Benefits and perks
    extracted_benefits: List[str] = None
    company_culture: str = ""
    
    # Processing metadata
    processing_time: float = 0.0
    gpu_memory_used: float = 0.0
    model_confidence: float = 0.0
    
    def __post_init__(self):
        if self.semantic_skills is None:
            self.semantic_skills = []
        if self.contextual_requirements is None:
            self.contextual_requirements = []
        if self.extracted_benefits is None:
            self.extracted_benefits = []

@dataclass
class TwoStageResult:
    """Combined result from both processing stages"""
    # Job identification
    job_id: str = ""
    url: str = ""
    
    # Original job data (added to fix job_data access)
    job_data: Dict[str, Any] = None
    
    # Stage 1 results
    stage1: Stage1Result = None
    
    # Stage 2 results (optional - only if passed Stage 1)
    stage2: Optional[Stage2Result] = None
    
    # Final combined analysis
    final_compatibility: float = 0.0
    final_skills: List[str] = None
    final_requirements: List[str] = None
    recommendation: str = "review"  # apply, review, skip
    
    # Processing metadata
    total_processing_time: float = 0.0
    stages_completed: int = 1
    processing_method: str = "two_stage"
    
    def __post_init__(self):
        if self.final_skills is None:
            self.final_skills = []
        if self.final_requirements is None:
            self.final_requirements = []
        if self.job_data is None:
            self.job_data = {}


class Stage1CPUProcessor:
    """
    Stage 1: CPU-bound Fast Processor
    
    Handles basic data extraction and filtering using 10 workers.
    Fast, rule-based processing to filter out unsuitable jobs.
    """
    
    def __init__(self, user_profile: Dict[str, Any], max_workers: int = 10):
        self.user_profile = user_profile
        self.max_workers = max_workers
        self.extractor = get_Improved_custom_extractor()
        
        # Pre-compile patterns for speed
        self._compile_filter_patterns()
        
        logger.info(f"Stage 1 CPU Processor initialized with {max_workers} workers")
    
    def _extract_Improved_fields(self, job_data: Dict[str, Any], job_text: str) -> Dict[str, Optional[str]]:
        """Extract Improved fields from job data"""
        from datetime import datetime, timedelta
        
        # 1. Remote Work Options
        remote_work_option = self._detect_remote_work(job_text)
        
        # 2. Job Posted Date
        job_posted_date = self._extract_posted_date(job_data, job_text)
        
        # 3. Application Deadline
        application_deadline = self._extract_deadline(job_text)
        
        # 4. Required Years of Experience
        required_years_experience = self._extract_experience_years(job_text)
        
        # 5. Education Requirements
        education_requirements = self._extract_education_requirements(job_text)
        
        # 9. Industry
        industry = self._detect_industry(job_data, job_text)
        
        return {
            'remote_work_option': remote_work_option,
            'job_posted_date': job_posted_date,
            'application_deadline': application_deadline,
            'required_years_experience': required_years_experience,
            'education_requirements': education_requirements,
            'industry': industry
        }
    
    def _detect_remote_work(self, job_text: str) -> str:
        """Detect remote work options"""
        remote_patterns = [
            (r'\b(fully remote|100% remote|remote work|work from home|wfh)\b', 'remote'),
            (r'\b(hybrid|flexible work|remote-friendly|partial remote)\b', 'hybrid'),
            (r'\b(on-site|onsite|office-based|in-person|no remote)\b', 'on-site'),
        ]
        
        for pattern, work_type in remote_patterns:
            if re.search(pattern, job_text, re.IGNORECASE):
                return work_type
        
        return 'not_specified'
    
    def _extract_posted_date(self, job_data: Dict[str, Any], job_text: str) -> Optional[str]:
        """Extract job posted date"""
        import re
        from datetime import datetime, timedelta
        
        # Check if date is in job_data
        for date_field in ['date_posted', 'posted_date', 'created_at', 'scraped_at']:
            if job_data.get(date_field):
                return str(job_data[date_field])
        
        # Look for relative dates in text
        relative_patterns = [
            (r'posted (\d+) days? ago', lambda m: (datetime.now() - timedelta(days=int(m.group(1)))).strftime('%Y-%m-%d')),
            (r'posted (\d+) hours? ago', lambda m: (datetime.now() - timedelta(hours=int(m.group(1)))).strftime('%Y-%m-%d')),
            (r'posted today', lambda m: datetime.now().strftime('%Y-%m-%d')),
            (r'posted yesterday', lambda m: (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')),
        ]
        
        for pattern, date_func in relative_patterns:
            match = re.search(pattern, job_text, re.IGNORECASE)
            if match:
                try:
                    return date_func(match)
                except:
                    continue
        
        return None
    
    def _extract_deadline(self, job_text: str) -> Optional[str]:
        """Extract application deadline"""
        import re
        
        deadline_patterns = [
            r'apply by ([^.]+)',
            r'deadline[:\s]+([^.]+)',
            r'applications close[:\s]+([^.]+)',
            r'closing date[:\s]+([^.]+)',
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, job_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_experience_years(self, job_text: str) -> Optional[str]:
        """Extract required years of experience"""
        import re
        
        experience_patterns = [
            (r'(\d+)\+?\s*years?\s*(?:of\s*)?experience', lambda m: f"{m.group(1)}+ years"),
            (r'(\d+)-(\d+)\s*years?\s*(?:of\s*)?experience', lambda m: f"{m.group(1)}-{m.group(2)} years"),
            (r'minimum\s*(\d+)\s*years?', lambda m: f"{m.group(1)}+ years"),
            (r'at least\s*(\d+)\s*years?', lambda m: f"{m.group(1)}+ years"),
            (r'entry.level|junior|graduate|new grad', lambda m: "0-2 years"),
            (r'senior|lead|principal', lambda m: "5+ years"),
        ]
        
        for pattern, format_func in experience_patterns:
            match = re.search(pattern, job_text, re.IGNORECASE)
            if match:
                try:
                    return format_func(match)
                except:
                    continue
        
        return None
    
    def _extract_education_requirements(self, job_text: str) -> Optional[str]:
        """Extract education requirements"""
        import re
        
        education_patterns = [
            (r'bachelor.?s?\s*degree', 'Bachelor\'s Degree'),
            (r'master.?s?\s*degree', 'Master\'s Degree'),
            (r'phd|doctorate', 'PhD/Doctorate'),
            (r'high school|diploma', 'High School/Diploma'),
            (r'college|university', 'College/University'),
            (r'degree\s*(?:in|related to)\s*([^.]+)', lambda m: f"Degree in {m.group(1).strip()}"),
        ]
        
        for pattern, education in education_patterns:
            if callable(education):
                match = re.search(pattern, job_text, re.IGNORECASE)
                if match:
                    try:
                        return education(match)
                    except:
                        continue
            else:
                if re.search(pattern, job_text, re.IGNORECASE):
                    return education
        
        return None
    
    def _detect_industry(self, job_data: Dict[str, Any], job_text: str) -> Optional[str]:
        """Detect industry from job data"""
        import re
        
        # Industry keywords mapping
        industry_keywords = {
            'Technology': ['tech', 'software', 'it ', 'saas', 'cloud', 'ai ', 'ml ', 'data science', 'cybersecurity'],
            'Finance': ['bank', 'financial', 'fintech', 'investment', 'trading', 'insurance', 'credit'],
            'Healthcare': ['health', 'medical', 'hospital', 'pharma', 'biotech', 'clinical'],
            'E-commerce': ['ecommerce', 'e-commerce', 'retail', 'marketplace', 'shopping'],
            'Consulting': ['consulting', 'advisory', 'professional services'],
            'Education': ['education', 'university', 'school', 'learning', 'training'],
            'Manufacturing': ['manufacturing', 'automotive', 'industrial', 'production'],
            'Media': ['media', 'advertising', 'marketing', 'publishing', 'entertainment'],
            'Government': ['government', 'public sector', 'municipal', 'federal'],
            'Non-profit': ['non-profit', 'nonprofit', 'charity', 'foundation'],
        }
        
        # Check company name and job description
        combined_text = f"{job_data.get('company', '')} {job_text}".lower()
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                return industry
        
        return 'Other'
    
    def _compile_filter_patterns(self):
        """Pre-compile regex patterns for fast filtering"""
        import re
        
        # French language patterns
        self.french_patterns = [
            re.compile(r'\b(français|québec|montreal|bilingue)\b', re.IGNORECASE),
            re.compile(r'\b(french|bilingual|quebec)\b', re.IGNORECASE)
        ]
        
        # Senior/Lead patterns
        self.senior_patterns = [
            re.compile(r'\b(senior|lead|principal|staff|architect)\b', re.IGNORECASE),
            re.compile(r'\b(manager|director|head of|chief)\b', re.IGNORECASE)
        ]
        
        # Skill patterns from user profile
        user_skills = self.user_profile.get('skills', [])
        self.skill_patterns = [
            re.compile(rf'\b{re.escape(skill)}\b', re.IGNORECASE) 
            for skill in user_skills
        ]
    
    def process_job_fast(self, job_data: Dict[str, Any], worker_id: int = 0) -> Stage1Result:
        """Fast processing of a single job"""
        start_time = time.time()
        
        try:
            # Extract basic data using Improved extractor
            extraction_result = self.extractor.extract_job_data(job_data)
            
            # Fast filtering checks
            job_text = f"{job_data.get('title', '')} {job_data.get('description', '')}".lower()
            
            is_french = any(pattern.search(job_text) for pattern in self.french_patterns)
            is_senior = any(pattern.search(job_text) for pattern in self.senior_patterns)
            
            # Fast skill matching
            matched_skills = []
            for skill, pattern in zip(self.user_profile.get('skills', []), self.skill_patterns):
                if pattern.search(job_text):
                    matched_skills.append(skill)
            
            # Extract Improved fields
            Improved_fields = self._extract_Improved_fields(job_data, job_text)
            
            # More generous basic compatibility scoring
            user_skills = self.user_profile.get('skills', [])
            skill_match_ratio = len(matched_skills) / max(len(user_skills), 1)
            
            # Base score from skill matches
            base_score = skill_match_ratio * 0.6 + 0.3  # Higher base score
            
            # Bonus for relevant job titles
            title_lower = job_data.get('title', '').lower()
            title_bonus = 0.0
            relevant_titles = ['analyst', 'developer', 'data', 'python', 'junior', 'entry', 'associate']
            for term in relevant_titles:
                if term in title_lower:
                    title_bonus += 0.1
            
            # Bonus for company recognition
            company_lower = job_data.get('company', '').lower()
            if any(term in company_lower for term in ['tech', 'software', 'data', 'analytics']):
                title_bonus += 0.05
            
            basic_compatibility = min(0.95, base_score + title_bonus)
            
            # More lenient filtering for users with fewer skills
            passes_filter = (
                not is_french and  # Keep French filter (language barrier)
                basic_compatibility > 0.15 and  # Much lower threshold
                (len(matched_skills) > 0 or basic_compatibility > 0.25)  # Allow 0 skills if good compatibility
            )
            
            # Special case: Allow some senior positions if they seem entry-friendly
            if is_senior and basic_compatibility > 0.4:
                senior_friendly_terms = ['junior', 'entry', 'associate', 'coordinator', 'analyst']
                job_text_lower = job_text.lower()
                if any(term in job_text_lower for term in senior_friendly_terms):
                    passes_filter = True
                    console.print(f"[cyan]🎯 Allowing senior position due to entry-friendly terms[/cyan]")
            
            result = Stage1Result(
                title=extraction_result.title,
                company=extraction_result.company,
                location=extraction_result.location,
                salary_range=extraction_result.salary_range,
                experience_level=extraction_result.experience_level,
                employment_type=extraction_result.employment_type,
                # Improved fields
                remote_work_option=Improved_fields['remote_work_option'],
                job_posted_date=Improved_fields['job_posted_date'],
                application_deadline=Improved_fields['application_deadline'],
                required_years_experience=Improved_fields['required_years_experience'],
                education_requirements=Improved_fields['education_requirements'],
                industry=Improved_fields['industry'],
                # Analysis results
                basic_skills=matched_skills,
                basic_requirements=extraction_result.requirements[:5],  # Top 5 only
                basic_compatibility=basic_compatibility,
                is_french=is_french,
                is_senior=is_senior,
                passes_basic_filter=passes_filter,
                processing_time=time.time() - start_time,
                confidence=extraction_result.overall_confidence,
                worker_id=worker_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Stage 1 processing error: {e}")
            return Stage1Result(
                title=job_data.get('title', 'Unknown'),
                company=job_data.get('company', 'Unknown'),
                passes_basic_filter=False,
                processing_time=time.time() - start_time,
                confidence=0.0,
                worker_id=worker_id
            )
    
    def process_jobs_batch(self, jobs: List[Dict[str, Any]]) -> List[Stage1Result]:
        """Process multiple jobs using thread pool. Preserve input order."""
        console.print(f"[cyan]🚀 Stage 1: Processing {len(jobs)} jobs with {self.max_workers} CPU workers[/cyan]")
        
        # Prepare results list to preserve ordering
        ordered_results: List[Optional[Stage1Result]] = [None] * len(jobs)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all jobs with index tracking
            future_to_index = {
                executor.submit(self.process_job_fast, job, i % self.max_workers): i
                for i, job in enumerate(jobs)
            }
            
            # Collect results with progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task("Stage 1 Processing...", total=len(jobs))
                
                for future in as_completed(future_to_index):
                    idx = future_to_index[future]
                    result = future.result()
                    ordered_results[idx] = result
                    progress.advance(task)
        
        # Ensure no None remains (fallback, should not happen)
        results: List[Stage1Result] = [r for r in ordered_results if r is not None]
        
        # Filter results that pass basic checks
        passed_jobs = [r for r in results if r.passes_basic_filter]
        
        console.print(f"[green]✅ Stage 1 Complete: {len(passed_jobs)}/{len(jobs)} jobs passed basic filter[/green]")
        
        return results


class Stage2GPUProcessor:
    """
    Stage 2: Text Analysis Processor
    
    Handles Improved Text analysis using transformers.
    Only processes jobs that passed Stage 1 filtering.
    """
    
    def __init__(self, user_profile: Dict[str, Any], model_name: str = "distilbert-base-uncased"):
        self.user_profile = user_profile
        self.model_name = model_name
        
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is not available. Install it with: pip install torch transformers")
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize transformer model
        self._initialize_model()
        
        logger.info(f"Stage 2 GPU Processor initialized on {self.device}")
    
    def _initialize_model(self):
        """Initialize transformer model and tokenizer"""
        try:
            console.print(f"[cyan]🤖 Loading transformer model: {self.model_name}[/cyan]")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
            self.model.eval()  # Set to evaluation mode
            
            console.print(f"[green]✅ Model loaded on {self.device}[/green]")
            
        except Exception as e:
            logger.error(f"Failed to initialize transformer model: {e}")
            self.tokenizer = None
            self.model = None
    
    def _get_embeddings(self, text: str) -> Optional[np.ndarray]:
        """Get embeddings for text using transformer model"""
        if not self.model or not self.tokenizer:
            return None
        
        try:
            # Tokenize and encode
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                truncation=True, 
                padding=True, 
                max_length=512
            ).to(self.device)
            
            # Get Text features
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use mean pooling of last hidden states
                embeddings = outputs.last_hidden_state.mean(dim=1)
            
            return embeddings.cpu().numpy()
            
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            return None
    
    def _extract_semantic_skills(self, job_description: str) -> List[str]:
        """Extract skills using semantic understanding"""
        # This is a simplified version - in production, you'd use more effective NLP
        common_skills = [
            "python", "javascript", "java", "sql", "aws", "docker", "kubernetes",
            "machine learning", "data analysis", "react", "node.js", "git",
            "agile", "scrum", "tensorflow", "pytorch", "pandas", "numpy"
        ]
        
        job_text = job_description.lower()
        found_skills = []
        
        for skill in common_skills:
            if skill.lower() in job_text:
                found_skills.append(skill)
        
        return found_skills[:10]  # Top 10 skills
    
    def _analyze_sentiment(self, job_description: str) -> str:
        """Analyze job description sentiment"""
        positive_words = ["exciting", "innovative", "growth", "opportunity", "benefits", "flexible"]
        negative_words = ["demanding", "pressure", "overtime", "strict", "challenging"]
        
        job_text = job_description.lower()
        
        positive_count = sum(1 for word in positive_words if word in job_text)
        negative_count = sum(1 for word in negative_words if word in job_text)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def process_job_semantic(self, job_data: Dict[str, Any], stage1_result: Stage1Result) -> Stage2Result:
        """Improved semantic processing of a job"""
        start_time = time.time()
        gpu_memory_before = 0
        
        try:
            if TORCH_AVAILABLE and torch.cuda.is_available():
                gpu_memory_before = torch.cuda.memory_allocated() / 1024**2  # MB
            
            job_description = job_data.get('description', '')
            
            # Semantic skill extraction
            semantic_skills = self._extract_semantic_skills(job_description)
            
            # Get embeddings for compatibility analysis
            skill_embeddings = self._get_embeddings(job_description)
            
            # Sentiment analysis
            sentiment = self._analyze_sentiment(job_description)
            
            # Enhanced compatibility using embeddings
            semantic_compatibility = stage1_result.basic_compatibility
            if skill_embeddings is not None:
                # In production, you'd compare with user profile embeddings
                semantic_compatibility = min(0.95, stage1_result.basic_compatibility * 1.2)
            
            # Extract benefits and culture info
            benefits = self._extract_benefits(job_description)
            culture = self._analyze_culture(job_description)
            
            # Contextual understanding
            context = f"Job focuses on {', '.join(semantic_skills[:3])} with {sentiment} outlook"
            
            gpu_memory_after = 0
            if TORCH_AVAILABLE and torch.cuda.is_available():
                gpu_memory_after = torch.cuda.memory_allocated() / 1024**2  # MB
            
            result = Stage2Result(
                semantic_skills=semantic_skills,
                contextual_requirements=stage1_result.basic_requirements,  # Improved in production
                semantic_compatibility=semantic_compatibility,
                job_sentiment=sentiment,
                skill_embeddings=skill_embeddings,
                contextual_understanding=context,
                extracted_benefits=benefits,
                company_culture=culture,
                processing_time=time.time() - start_time,
                gpu_memory_used=gpu_memory_after - gpu_memory_before,
                model_confidence=0.85  # Would be calculated from model outputs
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Stage 2 processing error: {e}")
            return Stage2Result(
                processing_time=time.time() - start_time,
                model_confidence=0.0
            )
    
    def _extract_benefits(self, job_description: str) -> List[str]:
        """Extract benefits from job description"""
        benefit_keywords = [
            "health insurance", "dental", "vision", "401k", "retirement",
            "vacation", "pto", "remote work", "flexible hours", "bonus"
        ]
        
        job_text = job_description.lower()
        found_benefits = []
        
        for benefit in benefit_keywords:
            if benefit in job_text:
                found_benefits.append(benefit.title())
        
        return found_benefits
    
    def _analyze_culture(self, job_description: str) -> str:
        """Analyze company culture from description"""
        culture_indicators = {
            "collaborative": ["team", "collaborate", "together", "partnership"],
            "innovative": ["innovation", "Modern", "latest", "modern"],
            "fast-paced": ["fast-paced", "dynamic", "agile", "rapid"],
            "traditional": ["established", "stable", "traditional", "conservative"]
        }
        
        job_text = job_description.lower()
        culture_scores = {}
        
        for culture, keywords in culture_indicators.items():
            score = sum(1 for keyword in keywords if keyword in job_text)
            culture_scores[culture] = score
        
        if culture_scores:
            return max(culture_scores, key=culture_scores.get)
        return "unknown"


class TwoStageJobProcessor:
    """
    Main Two-Stage Job Processing System
    
    Orchestrates both CPU and GPU processing stages.
    """
    
    def __init__(self, user_profile: Dict[str, Any], cpu_workers: int = 10, max_concurrent_stage2: int = 2):
        self.user_profile = user_profile
        self.cpu_workers = cpu_workers
        self.max_concurrent_stage2 = max(1, int(max_concurrent_stage2))
        
        # Initialize Stage 1 processor (always available)
        self.stage1_processor = Stage1CPUProcessor(user_profile, cpu_workers)
        
        # Initialize Stage 2 processor only if torch is available
        self.stage2_processor = None
        self.gpu_available = TORCH_AVAILABLE
        
        if TORCH_AVAILABLE:
            try:
                self.stage2_processor = Stage2GPUProcessor(user_profile)
                console.print(f"[bold blue]🚀 Two-Stage Job Processor Initialized[/bold blue]")
                console.print(f"[cyan]   Stage 1: {cpu_workers} CPU workers for fast processing[/cyan]")
                console.print(f"[cyan]   Stage 2: GPU Text analysis with transformers[/cyan]")
                console.print(f"[cyan]   Concurrency: {self.max_concurrent_stage2} parallel Stage 2 jobs[/cyan]")
            except Exception as e:
                logger.warning(f"Could not initialize GPU processor: {e}")
                console.print(f"[bold yellow]⚡ Single-Stage Job Processor Initialized (CPU Only)[/bold yellow]")
                console.print(f"[cyan]   Stage 1: {cpu_workers} CPU workers for fast processing[/cyan]")
                console.print(f"[yellow]   Stage 2: Disabled (GPU/Torch not available)[/yellow]")
        else:
            console.print(f"[bold yellow]⚡ Single-Stage Job Processor Initialized (CPU Only)[/bold yellow]")
            console.print(f"[cyan]   Stage 1: {cpu_workers} CPU workers for fast processing[/cyan]")
            console.print(f"[yellow]   Stage 2: Disabled (PyTorch not installed)[/yellow]")
    
    async def process_jobs(self, jobs: List[Dict[str, Any]]) -> List[TwoStageResult]:
        """Process jobs through both stages with parallel Stage 2 processing (semaphore-limited)."""
        total_start_time = time.time()
        
        console.print(f"\n[bold blue]🎯 Processing {len(jobs)} jobs through two-stage pipeline[/bold blue]")
        
        # Stage 1: CPU-bound fast processing (thread pool inside)
        stage1_results = self.stage1_processor.process_jobs_batch(jobs)
        
        # Filter jobs that passed Stage 1 (preserved order with corresponding jobs)
        passed_jobs: List[Tuple[Dict[str, Any], Stage1Result, int]] = [
            (job, result, idx)
            for idx, (job, result) in enumerate(zip(jobs, stage1_results))
            if result.passes_basic_filter
        ]
        
        console.print(f"[yellow]🔄 Stage 2: Processing {len(passed_jobs)} jobs that passed Stage 1[/yellow]")
        
        final_results: List[TwoStageResult] = []
        
        # Stage 2 available: run concurrently with semaphore limit
        if self.stage2_processor is not None:
            semaphore = asyncio.Semaphore(self.max_concurrent_stage2)

            async def process_single(idx: int, job: Dict[str, Any], s1: Stage1Result) -> TwoStageResult:
                async with semaphore:
                    # Offload synchronous GPU/CPU-bound work to a thread to keep loop responsive
                    s2: Stage2Result = await asyncio.to_thread(self.stage2_processor.process_job_semantic, job, s1)
                    combined = self._combine_results(job, s1, s2, idx)
                    return combined
            
            # Create tasks for all passed jobs
            tasks = [
                asyncio.create_task(process_single(idx, job, s1), name=f"stage2_job_{idx}")
                for (job, s1, idx) in passed_jobs
            ]
            
            # Consume tasks as they complete to update progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task("Stage 2 GPU Processing...", total=len(tasks))
                
                for coro in asyncio.as_completed(tasks):
                    try:
                        res: TwoStageResult = await coro
                        final_results.append(res)
                    finally:
                        progress.advance(task)
        else:
            # No Stage 2 available: fall back to Stage 1-only results
            for i, (job, stage1_result, _) in enumerate(passed_jobs):
                stage2_result = Stage2Result(
                    semantic_skills=stage1_result.basic_skills,
                    contextual_requirements=stage1_result.basic_requirements,
                    semantic_compatibility=stage1_result.basic_compatibility,
                    processing_time=0.0,
                    model_confidence=0.0
                )
                combined_result = self._combine_results(job, stage1_result, stage2_result, i)
                final_results.append(combined_result)
        
        # Add jobs that didn't pass Stage 1 (with Stage 1 results only)
        for job, stage1_result in zip(jobs, stage1_results):
            if not stage1_result.passes_basic_filter:
                combined_result = TwoStageResult(
                    job_id=job.get('id', f'job_{len(final_results)}'),
                    url=job.get('url', ''),
                    job_data=job,  # Add job_data
                    stage1=stage1_result,
                    stage2=None,
                    final_compatibility=stage1_result.basic_compatibility,
                    final_skills=stage1_result.basic_skills,
                    final_requirements=stage1_result.basic_requirements,
                    recommendation="skip",
                    total_processing_time=stage1_result.processing_time,
                    stages_completed=1
                )
                final_results.append(combined_result)
        
        total_time = time.time() - total_start_time
        
        # Display summary
        self._display_processing_summary(final_results, total_time)
        
        return final_results
    
    def _combine_results(self, job: Dict[str, Any], stage1: Stage1Result, 
                        stage2: Stage2Result, job_index: int) -> TwoStageResult:
        """Combine results from both stages"""
        
        # Merge skills (Stage 1 + Stage 2), filtering out None values
        all_skills = (stage1.basic_skills or []) + (stage2.semantic_skills or [])
        final_skills = list(set(skill for skill in all_skills if skill))
        
        # Use Stage 2 compatibility if available, otherwise Stage 1
        final_compatibility = stage2.semantic_compatibility
        
        # Determine recommendation
        if final_compatibility >= 0.7:
            recommendation = "apply"
        elif final_compatibility >= 0.4:
            recommendation = "review"
        else:
            recommendation = "skip"
        
        return TwoStageResult(
            job_id=job.get('id', f'job_{job_index}'),
            url=job.get('url', ''),
            job_data=job,  # Add job_data
            stage1=stage1,
            stage2=stage2,
            final_compatibility=final_compatibility,
            final_skills=final_skills,
            final_requirements=stage2.contextual_requirements,
            recommendation=recommendation,
            total_processing_time=stage1.processing_time + stage2.processing_time,
            stages_completed=2
        )
    
    def _display_processing_summary(self, results: List[TwoStageResult], total_time: float):
        """Display processing summary"""
        stage1_only = len([r for r in results if r.stages_completed == 1])
        stage2_complete = len([r for r in results if r.stages_completed == 2])
        
        apply_count = len([r for r in results if r.recommendation == "apply"])
        review_count = len([r for r in results if r.recommendation == "review"])
        skip_count = len([r for r in results if r.recommendation == "skip"])
        
        console.print(f"\n[bold green]🎉 Two-Stage Processing Complete![/bold green]")
        console.print(f"[cyan]📊 Processing Summary:[/cyan]")
        console.print(f"   Total Jobs: {len(results)}")
        console.print(f"   Stage 1 Only: {stage1_only}")
        console.print(f"   Stage 2 Complete: {stage2_complete}")
        console.print(f"   Total Time: {total_time:.2f}s")
        console.print(f"   Speed: {len(results)/total_time:.1f} jobs/sec")
        
        console.print(f"\n[cyan]🎯 Recommendations:[/cyan]")
        console.print(f"   Apply: {apply_count}")
        console.print(f"   Review: {review_count}")
        console.print(f"   Skip: {skip_count}")


# Convenience function
def get_two_stage_processor(user_profile: Dict[str, Any], cpu_workers: int = 10, max_concurrent_stage2: int = 2) -> TwoStageJobProcessor:
    """Get configured two-stage job processor"""
    return TwoStageJobProcessor(user_profile, cpu_workers, max_concurrent_stage2)


# Test function
async def test_two_stage_processing():
    """Test the two-stage processing system"""
    from ..utils.profile_helpers import load_profile
    
    profile = load_profile("Nirajan")
    processor = get_two_stage_processor(profile, cpu_workers=10, max_concurrent_stage2=2)
    
    # Test jobs
    test_jobs = [
        {
            "id": "1",
            "title": "Python Developer",
            "company": "TechCorp",
            "description": "Python, Django, AWS, machine learning, data analysis",
            "url": "https://example.com/job1"
        },
        {
            "id": "2", 
            "title": "Senior Software Architect",
            "company": "BigCorp",
            "description": "Lead development team, 10+ years experience",
            "url": "https://example.com/job2"
        }
    ]
    
    results = await processor.process_jobs(test_jobs)
    
    console.print(f"\n[green]✅ Test complete: {len(results)} jobs processed[/green]")
    for result in results:
        console.print(f"   {result.stage1.title}: {result.recommendation} ({result.final_compatibility:.2f})")


if __name__ == "__main__":
    asyncio.run(test_two_stage_processing())
