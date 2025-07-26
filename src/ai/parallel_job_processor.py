"""
Parallel Job Processor for RTX 3080
High-performance job processing using parallel/async approaches.
Optimized for RTX 3080 systems without CUDA compilation issues.
"""

import asyncio
import time
import logging
import concurrent.futures
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
from pathlib import Path

try:
    import GPUtil
    GPU_MONITORING_AVAILABLE = True
except ImportError:
    GPU_MONITORING_AVAILABLE = False
    GPUtil = None

logger = logging.getLogger(__name__)

@dataclass
class ProcessingMetrics:
    """Processing performance metrics."""
    jobs_processed: int
    processing_time: float
    jobs_per_second: float
    method: str
    workers_used: int
    gpu_utilization: float = 0.0
    memory_used_mb: float = 0.0
    cpu_cores_used: int = 0

@dataclass
class BatchProcessingResult:
    """Result of batch job processing."""
    job_results: List[Dict[str, Any]]
    metrics: ProcessingMetrics
    success_rate: float
    errors: List[str]

class ParallelJobProcessor:
    """
    High-performance parallel job processor optimized for RTX 3080.
    
    Uses CPU parallelization and async processing to maximize throughput
    without requiring complex CUDA compilation.
    """
    
    def __init__(self, 
                 max_workers: int = 8,
                 max_concurrent: int = 16,
                 processing_timeout: float = 30.0):
        """
        Initialize parallel job processor.
        
        Args:
            max_workers: Maximum thread pool workers
            max_concurrent: Maximum async concurrent tasks
            processing_timeout: Timeout for job processing
        """
        self.max_workers = max_workers
        self.max_concurrent = max_concurrent
        self.processing_timeout = processing_timeout
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Performance tracking
        self.total_jobs_processed = 0
        self.total_processing_time = 0.0
        self.processing_history = []
        
        # Skill extraction patterns
        self.skill_patterns = {
            'Python': ['python', 'django', 'flask', 'fastapi', 'pandas', 'numpy'],
            'JavaScript': ['javascript', 'js', 'react', 'vue', 'angular', 'node.js', 'typescript'],
            'SQL': ['sql', 'mysql', 'postgresql', 'database', 'mongodb'],
            'Machine Learning': ['ml', 'machine learning', 'ai', 'tensorflow', 'pytorch', 'scikit'],
            'Cloud': ['aws', 'azure', 'gcp', 'cloud', 'docker', 'kubernetes'],
            'Data Science': ['data science', 'analytics', 'statistics', 'r programming'],
            'DevOps': ['devops', 'ci/cd', 'jenkins', 'terraform', 'ansible'],
            'Java': ['java', 'spring', 'hibernate', 'maven', 'gradle'],
            'C++': ['c++', 'cpp', 'c plus plus'],
            'Go': ['golang', 'go programming'],
            'Rust': ['rust programming', 'rust language'],
            'PHP': ['php', 'laravel', 'symfony', 'wordpress'],
            'Ruby': ['ruby', 'rails', 'ruby on rails'],
            'Swift': ['swift', 'ios development', 'xcode'],
            'Kotlin': ['kotlin', 'android development']
        }
        
        self.logger.info(f"Initialized ParallelJobProcessor: {max_workers} workers, {max_concurrent} concurrent")
    
    def analyze_job_detailed(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detailed job analysis using advanced pattern matching.
        
        Args:
            job: Job dictionary to analyze
            
        Returns:
            Analyzed job with extracted information
        """
        try:
            description = job.get('description', '').lower()
            title = job.get('title', '').lower()
            company = job.get('company', '').lower()
            
            # Extract required skills
            required_skills = []
            for skill, patterns in self.skill_patterns.items():
                if any(pattern in description or pattern in title for pattern in patterns):
                    required_skills.append(skill)
            
            # Extract experience level
            experience_level = self._extract_experience_level(description, title)
            
            # Extract salary information
            salary_info = self._extract_salary_info(description)
            
            # Extract benefits
            benefits = self._extract_benefits(description)
            
            # Extract job requirements
            requirements = self._extract_requirements(description)
            
            # Calculate compatibility score
            compatibility_score = self._calculate_compatibility_score(
                required_skills, experience_level, description
            )
            
            # Determine analysis confidence
            analysis_confidence = self._calculate_confidence(
                required_skills, description, title
            )
            
            # Create result
            result = job.copy()
            result.update({
                'required_skills': required_skills,
                'job_requirements': requirements,
                'experience_level': experience_level,
                'salary_info': salary_info,
                'extracted_benefits': benefits,
                'compatibility_score': compatibility_score,
                'analysis_confidence': analysis_confidence,
                'analysis_reasoning': self._generate_reasoning(required_skills, experience_level),
                'processing_method': 'parallel_detailed',
                'processed_at': time.time()
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Job analysis failed: {e}")
            return self._create_fallback_result(job, str(e))
    
    def _extract_experience_level(self, description: str, title: str) -> str:
        """Extract experience level from job description."""
        text = f"{description} {title}"
        
        if any(term in text for term in ['senior', 'sr.', 'lead', '5+ years', '7+ years', '10+ years']):
            return 'Senior'
        elif any(term in text for term in ['mid', 'intermediate', '3+ years', '4+ years', '2-5 years']):
            return 'Mid-level'
        elif any(term in text for term in ['junior', 'jr.', 'entry', 'graduate', '0-2 years', 'new grad']):
            return 'Junior'
        else:
            return 'Mid-level'  # Default
    
    def _extract_salary_info(self, description: str) -> Dict[str, Any]:
        """Extract salary information from description."""
        import re
        
        # Look for salary patterns
        salary_patterns = [
            r'\$(\d{2,3}),?(\d{3})\s*-\s*\$(\d{2,3}),?(\d{3})',  # $80,000 - $120,000
            r'\$(\d{2,3})k\s*-\s*\$(\d{2,3})k',  # $80k - $120k
            r'(\d{2,3}),?(\d{3})\s*-\s*(\d{2,3}),?(\d{3})',  # 80,000 - 120,000
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return {
                    'salary_mentioned': True,
                    'salary_range': match.group(0),
                    'extracted_from': 'description'
                }
        
        return {'salary_mentioned': False}
    
    def _extract_benefits(self, description: str) -> List[str]:
        """Extract benefits from job description."""
        benefit_keywords = {
            'Health Insurance': ['health insurance', 'medical', 'dental', 'vision'],
            'Remote Work': ['remote', 'work from home', 'wfh', 'telecommute'],
            'Flexible Hours': ['flexible', 'flex time', 'work-life balance'],
            'Vacation': ['vacation', 'pto', 'paid time off', 'holidays'],
            'Retirement': ['401k', 'retirement', 'pension', 'rrsp'],
            'Stock Options': ['stock options', 'equity', 'shares'],
            'Professional Development': ['training', 'conferences', 'learning', 'development'],
            'Gym Membership': ['gym', 'fitness', 'wellness'],
            'Free Food': ['free lunch', 'snacks', 'catered meals']
        }
        
        benefits = []
        for benefit, keywords in benefit_keywords.items():
            if any(keyword in description for keyword in keywords):
                benefits.append(benefit)
        
        return benefits
    
    def _extract_requirements(self, description: str) -> List[str]:
        """Extract job requirements from description."""
        requirements = []
        
        # Education requirements
        if any(term in description for term in ['bachelor', 'degree', 'university', 'college']):
            requirements.append('Bachelor\'s degree preferred')
        
        if any(term in description for term in ['master', 'msc', 'phd', 'doctorate']):
            requirements.append('Advanced degree preferred')
        
        # Experience requirements
        import re
        exp_match = re.search(r'(\d+)\+?\s*years?\s*(?:of\s*)?experience', description)
        if exp_match:
            years = exp_match.group(1)
            requirements.append(f'{years}+ years of experience')
        
        # Certification requirements
        if any(term in description for term in ['certification', 'certified', 'license']):
            requirements.append('Professional certification preferred')
        
        return requirements
    
    def _calculate_compatibility_score(self, skills: List[str], experience: str, description: str) -> float:
        """Calculate job compatibility score."""
        score = 0.5  # Base score
        
        # Skill bonus
        score += min(0.3, len(skills) * 0.05)
        
        # Experience level bonus
        if experience == 'Senior':
            score += 0.1
        elif experience == 'Mid-level':
            score += 0.15
        else:  # Junior
            score += 0.2
        
        # Remote work bonus
        if any(term in description for term in ['remote', 'work from home']):
            score += 0.1
        
        return min(0.95, score)
    
    def _calculate_confidence(self, skills: List[str], description: str, title: str) -> float:
        """Calculate analysis confidence score."""
        confidence = 0.6  # Base confidence
        
        # More skills = higher confidence
        confidence += min(0.2, len(skills) * 0.03)
        
        # Longer description = higher confidence
        if len(description) > 500:
            confidence += 0.1
        elif len(description) > 200:
            confidence += 0.05
        
        # Clear title = higher confidence
        if any(term in title for term in ['developer', 'engineer', 'analyst', 'manager']):
            confidence += 0.1
        
        return min(0.95, confidence)
    
    def _generate_reasoning(self, skills: List[str], experience: str) -> str:
        """Generate analysis reasoning."""
        if not skills:
            return "Limited technical skills mentioned in job description"
        
        skill_text = ', '.join(skills[:3])  # Top 3 skills
        if len(skills) > 3:
            skill_text += f" and {len(skills) - 3} more"
        
        return f"{experience} level position requiring {skill_text}"
    
    def _create_fallback_result(self, job: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Create fallback result for failed analysis."""
        result = job.copy()
        result.update({
            'required_skills': [],
            'job_requirements': [],
            'experience_level': 'Unknown',
            'salary_info': {'salary_mentioned': False},
            'extracted_benefits': [],
            'compatibility_score': 0.5,
            'analysis_confidence': 0.0,
            'analysis_reasoning': f'Analysis failed: {error}',
            'processing_method': 'fallback',
            'processed_at': time.time(),
            'error': error
        })
        return result
    
    async def process_jobs_async(self, jobs: List[Dict[str, Any]]) -> BatchProcessingResult:
        """
        Process jobs using async approach for maximum performance.
        
        Args:
            jobs: List of jobs to process
            
        Returns:
            BatchProcessingResult with metrics
        """
        start_time = time.time()
        gpu_util_before = self._get_gpu_utilization()
        
        self.logger.info(f"Starting async processing of {len(jobs)} jobs")
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_job_with_semaphore(job: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                # Run CPU-bound task in thread pool
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self.analyze_job_detailed, job)
        
        try:
            # Process all jobs concurrently
            tasks = [process_job_with_semaphore(job) for job in jobs]
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.processing_timeout
            )
            
            # Separate successful results from errors
            successful_results = []
            errors = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    errors.append(f"Job {i}: {str(result)}")
                    # Create fallback result
                    fallback = self._create_fallback_result(jobs[i], str(result))
                    successful_results.append(fallback)
                else:
                    successful_results.append(result)
            
            processing_time = time.time() - start_time
            jobs_per_second = len(successful_results) / processing_time if processing_time > 0 else 0
            success_rate = (len(successful_results) - len(errors)) / len(jobs) if jobs else 0
            
            # Update tracking
            self.total_jobs_processed += len(successful_results)
            self.total_processing_time += processing_time
            
            # Create metrics
            metrics = ProcessingMetrics(
                jobs_processed=len(successful_results),
                processing_time=processing_time,
                jobs_per_second=jobs_per_second,
                method='async_parallel',
                workers_used=self.max_concurrent,
                gpu_utilization=self._get_gpu_utilization(),
                memory_used_mb=self._get_gpu_memory_used(),
                cpu_cores_used=self.max_workers
            )
            
            self.logger.info(f"Async processing complete: {jobs_per_second:.1f} jobs/sec")
            
            return BatchProcessingResult(
                job_results=successful_results,
                metrics=metrics,
                success_rate=success_rate,
                errors=errors
            )
            
        except asyncio.TimeoutError:
            self.logger.error(f"Processing timeout after {self.processing_timeout}s")
            raise
        except Exception as e:
            self.logger.error(f"Async processing failed: {e}")
            raise
    
    def process_jobs_parallel(self, jobs: List[Dict[str, Any]]) -> BatchProcessingResult:
        """
        Process jobs using thread pool for parallel execution.
        
        Args:
            jobs: List of jobs to process
            
        Returns:
            BatchProcessingResult with metrics
        """
        start_time = time.time()
        
        self.logger.info(f"Starting parallel processing of {len(jobs)} jobs")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            try:
                # Submit all jobs
                future_to_job = {
                    executor.submit(self.analyze_job_detailed, job): job 
                    for job in jobs
                }
                
                results = []
                errors = []
                
                for future in concurrent.futures.as_completed(future_to_job, timeout=self.processing_timeout):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        job = future_to_job[future]
                        errors.append(f"Job {job.get('id', 'unknown')}: {str(e)}")
                        # Create fallback result
                        fallback = self._create_fallback_result(job, str(e))
                        results.append(fallback)
                
                processing_time = time.time() - start_time
                jobs_per_second = len(results) / processing_time if processing_time > 0 else 0
                success_rate = (len(results) - len(errors)) / len(jobs) if jobs else 0
                
                # Create metrics
                metrics = ProcessingMetrics(
                    jobs_processed=len(results),
                    processing_time=processing_time,
                    jobs_per_second=jobs_per_second,
                    method='thread_parallel',
                    workers_used=self.max_workers,
                    gpu_utilization=self._get_gpu_utilization(),
                    memory_used_mb=self._get_gpu_memory_used(),
                    cpu_cores_used=self.max_workers
                )
                
                self.logger.info(f"Parallel processing complete: {jobs_per_second:.1f} jobs/sec")
                
                return BatchProcessingResult(
                    job_results=results,
                    metrics=metrics,
                    success_rate=success_rate,
                    errors=errors
                )
                
            except concurrent.futures.TimeoutError:
                self.logger.error(f"Processing timeout after {self.processing_timeout}s")
                raise
    
    def _get_gpu_utilization(self) -> float:
        """Get current GPU utilization."""
        try:
            if GPU_MONITORING_AVAILABLE and GPUtil:
                gpus = GPUtil.getGPUs()
                if gpus:
                    return gpus[0].load * 100
        except Exception:
            pass
        return 0.0
    
    def _get_gpu_memory_used(self) -> float:
        """Get current GPU memory usage in MB."""
        try:
            if GPU_MONITORING_AVAILABLE and GPUtil:
                gpus = GPUtil.getGPUs()
                if gpus:
                    return gpus[0].memoryUsed
        except Exception:
            pass
        return 0.0
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        avg_jobs_per_second = (
            self.total_jobs_processed / self.total_processing_time 
            if self.total_processing_time > 0 else 0
        )
        
        return {
            'processor_config': {
                'max_workers': self.max_workers,
                'max_concurrent': self.max_concurrent,
                'processing_timeout': self.processing_timeout
            },
            'performance_stats': {
                'total_jobs_processed': self.total_jobs_processed,
                'total_processing_time': self.total_processing_time,
                'average_jobs_per_second': avg_jobs_per_second
            },
            'current_status': {
                'gpu_utilization': self._get_gpu_utilization(),
                'memory_used_mb': self._get_gpu_memory_used()
            },
            'skill_patterns_count': len(self.skill_patterns)
        }


# Convenience functions
def get_parallel_processor(max_workers: int = 8, max_concurrent: int = 16) -> ParallelJobProcessor:
    """
    Get parallel job processor instance.
    
    Args:
        max_workers: Maximum thread pool workers
        max_concurrent: Maximum async concurrent tasks
        
    Returns:
        ParallelJobProcessor instance
    """
    return ParallelJobProcessor(
        max_workers=max_workers,
        max_concurrent=max_concurrent
    )

async def process_jobs_fast(jobs: List[Dict[str, Any]], 
                          max_concurrent: int = 16) -> BatchProcessingResult:
    """
    Fast job processing using async approach.
    
    Args:
        jobs: List of jobs to process
        max_concurrent: Maximum concurrent tasks
        
    Returns:
        BatchProcessingResult with metrics
    """
    processor = get_parallel_processor(max_concurrent=max_concurrent)
    return await processor.process_jobs_async(jobs)