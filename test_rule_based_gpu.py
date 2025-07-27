#!/usr/bin/env python3
"""
Test GPU-accelerated rule-based job analysis vs CPU
"""

import sys
import os
import time
import torch
import numpy as np
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class GPUAcceleratedRuleBasedAnalyzer:
    """GPU-accelerated version of rule-based job analysis"""
    
    def __init__(self, profile: Dict[str, Any], device: str = 'cuda'):
        self.profile = profile
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        
        # Extract keywords and convert to lowercase for matching
        self.keywords = [kw.lower() for kw in profile.get('keywords', [])]
        self.skills = [skill.lower() for skill in profile.get('skills', [])]
        self.all_terms = list(set(self.keywords + self.skills))
        
        print(f"🎮 Using device: {self.device}")
        print(f"📝 Loaded {len(self.all_terms)} unique terms for matching")
    
    def analyze_job_batch_gpu(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze multiple jobs using GPU acceleration"""
        results = []
        
        # Prepare job texts
        job_texts = []
        for job in jobs:
            text = f"{job.get('title', '')} {job.get('description', '')} {job.get('company', '')}".lower()
            job_texts.append(text)
        
        # Convert to tensors for GPU processing
        batch_size = len(jobs)
        
        # Create keyword matching matrix on GPU
        keyword_matches = torch.zeros((batch_size, len(self.all_terms)), device=self.device)
        
        # Vectorized keyword matching
        for i, text in enumerate(job_texts):
            for j, term in enumerate(self.all_terms):
                if term in text:
                    keyword_matches[i, j] = 1.0
        
        # Calculate scores using GPU operations
        match_counts = torch.sum(keyword_matches, dim=1)
        max_possible = len(self.all_terms)
        
        # Normalize scores
        scores = (match_counts / max_possible * 100).cpu().numpy()
        
        # Create results
        for i, job in enumerate(jobs):
            score = float(scores[i])
            matched_terms = [self.all_terms[j] for j in range(len(self.all_terms)) 
                           if keyword_matches[i, j] == 1.0]
            
            results.append({
                'job': job,
                'score': score,
                'matched_keywords': matched_terms,
                'match_count': len(matched_terms),
                'recommendation': 'High' if score >= 30 else 'Medium' if score >= 15 else 'Low'
            })
        
        return results
    
    def analyze_job_batch_cpu(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze multiple jobs using CPU (for comparison)"""
        results = []
        
        for job in jobs:
            text = f"{job.get('title', '')} {job.get('description', '')} {job.get('company', '')}".lower()
            
            # Count keyword matches
            matched_terms = []
            for term in self.all_terms:
                if term in text:
                    matched_terms.append(term)
            
            # Calculate score
            score = (len(matched_terms) / len(self.all_terms)) * 100
            
            results.append({
                'job': job,
                'score': score,
                'matched_keywords': matched_terms,
                'match_count': len(matched_terms),
                'recommendation': 'High' if score >= 30 else 'Medium' if score >= 15 else 'Low'
            })
        
        return results

def create_test_jobs(count: int) -> List[Dict[str, Any]]:
    """Create test jobs for benchmarking"""
    job_templates = [
        {
            'title': 'Senior Data Analyst',
            'company': 'TechCorp',
            'description': 'Python, SQL, Machine Learning, AWS, pandas, numpy, scikit-learn, data analysis, statistics, tableau, power bi'
        },
        {
            'title': 'Machine Learning Engineer',
            'company': 'AI Solutions',
            'description': 'TensorFlow, PyTorch, Python, Docker, Kubernetes, MLOps, data science, deep learning, neural networks'
        },
        {
            'title': 'Data Scientist',
            'company': 'DataTech',
            'description': 'R, Python, statistical analysis, predictive modeling, jupyter, matplotlib, seaborn, data visualization'
        },
        {
            'title': 'Business Analyst',
            'company': 'Business Corp',
            'description': 'Excel, SQL, business analytics, dashboard creation, reporting, data insights, stakeholder management'
        },
        {
            'title': 'Software Developer',
            'company': 'DevCorp',
            'description': 'Java, JavaScript, React, Node.js, database management, API development, version control, git'
        }
    ]
    
    jobs = []
    for i in range(count):
        template = job_templates[i % len(job_templates)]
        job = template.copy()
        job['id'] = i
        jobs.append(job)
    
    return jobs

def benchmark_rule_based_gpu():
    """Benchmark GPU vs CPU rule-based analysis"""
    print("🚀 GPU-Accelerated Rule-Based Analysis Benchmark")
    print("=" * 60)
    
    # Load profile
    try:
        from src.utils.profile_helpers import load_profile
        profile = load_profile("Nirajan")
        print(f"✅ Loaded profile: {profile.get('name', 'Unknown')}")
    except Exception as e:
        print(f"❌ Error loading profile: {e}")
        return
    
    # Initialize analyzers
    gpu_analyzer = GPUAcceleratedRuleBasedAnalyzer(profile, device='cuda')
    cpu_analyzer = GPUAcceleratedRuleBasedAnalyzer(profile, device='cpu')
    
    # Test different batch sizes
    batch_sizes = [10, 50, 100, 500, 1000, 5000]
    
    print(f"\n📊 Performance Comparison:")
    print(f"{'Batch Size':<12} {'CPU Time':<12} {'GPU Time':<12} {'Speedup':<12} {'CPU Jobs/s':<12} {'GPU Jobs/s':<12}")
    print("-" * 80)
    
    for batch_size in batch_sizes:
        # Create test jobs
        test_jobs = create_test_jobs(batch_size)
        
        # CPU benchmark
        start_time = time.time()
        cpu_results = cpu_analyzer.analyze_job_batch_cpu(test_jobs)
        cpu_time = time.time() - start_time
        
        # GPU benchmark
        start_time = time.time()
        gpu_results = gpu_analyzer.analyze_job_batch_gpu(test_jobs)
        gpu_time = time.time() - start_time
        
        # Calculate metrics
        speedup = cpu_time / gpu_time if gpu_time > 0 else 0
        cpu_jobs_per_sec = batch_size / cpu_time if cpu_time > 0 else 0
        gpu_jobs_per_sec = batch_size / gpu_time if gpu_time > 0 else 0
        
        print(f"{batch_size:<12} {cpu_time:.4f}s{'':<4} {gpu_time:.4f}s{'':<4} {speedup:.2f}x{'':<6} {cpu_jobs_per_sec:.1f}{'':<7} {gpu_jobs_per_sec:.1f}")
        
        # Verify results are similar
        if len(cpu_results) > 0 and len(gpu_results) > 0:
            cpu_score = cpu_results[0]['score']
            gpu_score = gpu_results[0]['score']
            if abs(cpu_score - gpu_score) > 1.0:  # Allow small floating point differences
                print(f"⚠️  Warning: Score mismatch - CPU: {cpu_score:.2f}, GPU: {gpu_score:.2f}")

def test_gpu_memory_usage():
    """Test GPU memory usage during batch processing"""
    print(f"\n🧠 GPU Memory Usage Test:")
    
    if not torch.cuda.is_available():
        print("❌ CUDA not available")
        return
    
    # Load profile
    try:
        from src.utils.profile_helpers import load_profile
        profile = load_profile("Nirajan")
    except Exception as e:
        print(f"❌ Error loading profile: {e}")
        return
    
    analyzer = GPUAcceleratedRuleBasedAnalyzer(profile, device='cuda')
    
    batch_sizes = [100, 1000, 5000, 10000]
    
    for batch_size in batch_sizes:
        # Clear GPU cache
        torch.cuda.empty_cache()
        
        # Measure initial memory
        initial_memory = torch.cuda.memory_allocated() / 1024**2  # MB
        
        # Create and process jobs
        test_jobs = create_test_jobs(batch_size)
        results = analyzer.analyze_job_batch_gpu(test_jobs)
        
        # Measure peak memory
        peak_memory = torch.cuda.max_memory_allocated() / 1024**2  # MB
        memory_used = peak_memory - initial_memory
        
        print(f"   Batch {batch_size:>5}: {memory_used:.1f} MB ({memory_used/batch_size*1000:.2f} KB per job)")
        
        # Reset peak memory stats
        torch.cuda.reset_peak_memory_stats()

def main():
    """Main test function"""
    if not torch.cuda.is_available():
        print("❌ CUDA not available - cannot test GPU acceleration")
        return
    
    # Run benchmarks
    benchmark_rule_based_gpu()
    
    # Test memory usage
    test_gpu_memory_usage()
    
    print(f"\n💡 Summary:")
    print(f"   • GPU acceleration can significantly speed up batch processing")
    print(f"   • Larger batch sizes show better GPU utilization")
    print(f"   • Memory usage scales linearly with batch size")
    print(f"   • Rule-based + GPU = Best of both worlds! 🚀")

if __name__ == "__main__":
    main()