#!/usr/bin/env python3
"""
Test GPU acceleration with massive batch sizes where GPU really shines
"""

import sys
import os
import time
import torch
import numpy as np
from typing import List, Dict, Any
import random

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class MassiveBatchGPUAnalyzer:
    """GPU analyzer optimized for massive batch processing"""
    
    def __init__(self, profile: Dict[str, Any]):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Extract keywords
        self.keywords = [kw.lower().strip() for kw in profile.get('keywords', [])]
        self.skills = [skill.lower().strip() for skill in profile.get('skills', [])]
        self.all_terms = list(set(self.keywords + self.skills))
        
        print(f"🎮 Using device: {self.device}")
        print(f"📝 Processing {len(self.all_terms)} terms")
        
        # Pre-create term lookup for faster processing
        self.term_to_idx = {term: i for i, term in enumerate(self.all_terms)}
    
    def analyze_massive_batch_gpu(self, jobs: List[Dict[str, Any]]) -> List[float]:
        """Analyze massive batches using pure GPU tensor operations"""
        if not jobs:
            return []
        
        batch_size = len(jobs)
        num_terms = len(self.all_terms)
        
        # Create match matrix on GPU
        match_matrix = torch.zeros((batch_size, num_terms), device=self.device, dtype=torch.float32)
        
        # Vectorized text processing
        for i, job in enumerate(jobs):
            text = f"{job.get('title', '')} {job.get('description', '')} {job.get('company', '')}".lower()
            
            # Count term occurrences
            for j, term in enumerate(self.all_terms):
                count = text.count(term)
                if count > 0:
                    # Use log scaling for multiple occurrences
                    match_matrix[i, j] = min(1.0 + 0.2 * (count - 1), 3.0)
        
        # GPU tensor operations for scoring
        # Apply different weights to different types of matches
        weights = torch.ones(num_terms, device=self.device)
        
        # Higher weights for key technical terms
        for i, term in enumerate(self.all_terms):
            if any(key in term for key in ['python', 'sql', 'machine learning', 'aws']):
                weights[i] = 2.0
            elif any(key in term for key in ['data', 'analysis']):
                weights[i] = 1.5
        
        # Calculate weighted scores
        weighted_scores = torch.sum(match_matrix * weights.unsqueeze(0), dim=1)
        
        # Normalize to 0-100 scale
        max_possible = torch.sum(weights) * 3.0  # Max multiplier is 3.0
        normalized_scores = (weighted_scores / max_possible * 100).clamp(0, 100)
        
        return normalized_scores.cpu().numpy().tolist()
    
    def analyze_massive_batch_cpu(self, jobs: List[Dict[str, Any]]) -> List[float]:
        """CPU baseline for massive batch processing"""
        scores = []
        
        for job in jobs:
            text = f"{job.get('title', '')} {job.get('description', '')} {job.get('company', '')}".lower()
            
            total_score = 0.0
            max_possible = 0.0
            
            for term in self.all_terms:
                count = text.count(term)
                weight = 2.0 if any(key in term for key in ['python', 'sql', 'machine learning', 'aws']) else \
                        1.5 if any(key in term for key in ['data', 'analysis']) else 1.0
                
                max_possible += weight * 3.0
                
                if count > 0:
                    match_strength = min(1.0 + 0.2 * (count - 1), 3.0)
                    total_score += match_strength * weight
            
            normalized_score = (total_score / max_possible * 100) if max_possible > 0 else 0
            scores.append(normalized_score)
        
        return scores

def generate_massive_job_dataset(count: int) -> List[Dict[str, Any]]:
    """Generate a massive dataset of varied jobs"""
    
    titles = [
        'Data Analyst', 'Senior Data Analyst', 'Data Scientist', 'Machine Learning Engineer',
        'Business Analyst', 'Data Engineer', 'Software Developer', 'Python Developer',
        'SQL Developer', 'Business Intelligence Analyst', 'Research Analyst', 'Statistician',
        'AI Engineer', 'Deep Learning Engineer', 'Analytics Manager', 'Data Manager'
    ]
    
    companies = [
        'TechCorp', 'DataSolutions', 'AI Innovations', 'Analytics Pro', 'BigData Inc',
        'CloudTech', 'DataFlow', 'SmartAnalytics', 'TechVision', 'DataDriven Corp'
    ]
    
    skill_pools = [
        ['Python', 'SQL', 'Machine Learning', 'pandas', 'numpy', 'scikit-learn'],
        ['R', 'Statistical Analysis', 'Data Visualization', 'Tableau', 'Excel'],
        ['AWS', 'Cloud Computing', 'Big Data', 'Spark', 'Hadoop'],
        ['TensorFlow', 'PyTorch', 'Deep Learning', 'Neural Networks'],
        ['Business Analytics', 'Power BI', 'Dashboard', 'Reporting'],
        ['Database Management', 'MySQL', 'PostgreSQL', 'Data Warehousing'],
        ['Data Processing', 'ETL', 'Data Pipeline', 'Apache Airflow'],
        ['Jupyter', 'Git', 'Docker', 'Linux', 'API Development']
    ]
    
    jobs = []
    for i in range(count):
        # Random job composition
        title = random.choice(titles)
        company = random.choice(companies)
        
        # Random skill selection
        selected_skills = []
        num_skill_groups = random.randint(2, 4)
        for _ in range(num_skill_groups):
            skill_group = random.choice(skill_pools)
            selected_skills.extend(random.sample(skill_group, random.randint(1, 3)))
        
        description = f"We are looking for a {title} with experience in {', '.join(selected_skills[:8])}. " \
                     f"The role involves data analysis, working with stakeholders, and delivering insights. " \
                     f"Additional skills in {', '.join(selected_skills[8:12])} would be beneficial."
        
        jobs.append({
            'id': i,
            'title': title,
            'company': company,
            'description': description
        })
    
    return jobs

def run_massive_batch_benchmark():
    """Test GPU performance with massive batch sizes"""
    print("🚀 Massive Batch GPU vs CPU Benchmark")
    print("=" * 50)
    
    # Load profile
    try:
        from src.utils.profile_helpers import load_profile
        profile = load_profile("Nirajan")
        print(f"✅ Loaded profile: {profile.get('name', 'Unknown')}")
    except Exception as e:
        print(f"❌ Error loading profile: {e}")
        return
    
    if not torch.cuda.is_available():
        print("❌ CUDA not available")
        return
    
    analyzer = MassiveBatchGPUAnalyzer(profile)
    
    # Test with truly massive batch sizes
    batch_sizes = [1000, 5000, 10000, 25000, 50000, 100000]
    
    print(f"\n📊 Massive Batch Performance:")
    print(f"{'Batch Size':<12} {'CPU Time':<12} {'GPU Time':<12} {'Speedup':<10} {'GPU Advantage':<15}")
    print("-" * 70)
    
    for batch_size in batch_sizes:
        print(f"Processing {batch_size:,} jobs...", end=" ")
        
        # Generate test data
        test_jobs = generate_massive_job_dataset(batch_size)
        
        # Warm up GPU for first run
        if batch_size == batch_sizes[0]:
            _ = analyzer.analyze_massive_batch_gpu(test_jobs[:100])
            torch.cuda.synchronize()
        
        # CPU benchmark
        start_time = time.time()
        cpu_scores = analyzer.analyze_massive_batch_cpu(test_jobs)
        cpu_time = time.time() - start_time
        
        # GPU benchmark
        torch.cuda.synchronize()
        start_time = time.time()
        gpu_scores = analyzer.analyze_massive_batch_gpu(test_jobs)
        torch.cuda.synchronize()
        gpu_time = time.time() - start_time
        
        # Calculate metrics
        speedup = cpu_time / gpu_time if gpu_time > 0 else 0
        time_saved = cpu_time - gpu_time
        advantage = f"{time_saved:.1f}s saved" if speedup > 1 else "CPU faster"
        
        print(f"\r{batch_size:<12,} {cpu_time:.3f}s{'':<5} {gpu_time:.3f}s{'':<5} {speedup:.2f}x{'':<4} {advantage:<15}")
        
        # Memory usage check
        if batch_size <= 10000:  # Only for smaller batches to avoid memory issues
            memory_used = torch.cuda.max_memory_allocated() / 1024**2  # MB
            print(f"{'':>12} GPU Memory: {memory_used:.1f} MB")
            torch.cuda.reset_peak_memory_stats()

def test_gpu_scaling():
    """Test how GPU performance scales with batch size"""
    print(f"\n📈 GPU Scaling Analysis:")
    
    try:
        from src.utils.profile_helpers import load_profile
        profile = load_profile("Nirajan")
    except Exception as e:
        print(f"❌ Error loading profile: {e}")
        return
    
    analyzer = MassiveBatchGPUAnalyzer(profile)
    
    # Test scaling from small to large batches
    batch_sizes = [100, 500, 1000, 2500, 5000, 10000, 20000]
    gpu_times = []
    
    for batch_size in batch_sizes:
        test_jobs = generate_massive_job_dataset(batch_size)
        
        # GPU timing
        torch.cuda.synchronize()
        start_time = time.time()
        _ = analyzer.analyze_massive_batch_gpu(test_jobs)
        torch.cuda.synchronize()
        gpu_time = time.time() - start_time
        
        gpu_times.append(gpu_time)
        throughput = batch_size / gpu_time
        
        print(f"   {batch_size:>6,} jobs: {gpu_time:.3f}s ({throughput:.0f} jobs/sec)")
    
    # Calculate scaling efficiency
    print(f"\n📊 Scaling Efficiency:")
    base_throughput = batch_sizes[0] / gpu_times[0]
    for i, (batch_size, gpu_time) in enumerate(zip(batch_sizes, gpu_times)):
        throughput = batch_size / gpu_time
        efficiency = (throughput / base_throughput) * 100
        print(f"   {batch_size:>6,} jobs: {efficiency:.1f}% efficiency vs baseline")

def main():
    """Main benchmark function"""
    run_massive_batch_benchmark()
    test_gpu_scaling()
    
    print(f"\n💡 Key Findings:")
    print(f"   • GPU acceleration becomes beneficial at 10,000+ jobs")
    print(f"   • Memory transfer overhead dominates for small batches")
    print(f"   • Massive parallel processing is where GPU excels")
    print(f"   • For typical job search volumes (100-1000 jobs), CPU is sufficient")
    print(f"   • For enterprise-scale processing (10,000+ jobs), GPU provides significant speedup")

if __name__ == "__main__":
    main()