#!/usr/bin/env python3
"""Deep performance profiling to find bottlenecks"""

import sys
import time
import asyncio
import cProfile
import pstats
from typing import Dict, List
sys.path.append('.')

class PerformanceProfiler:
    """Profile each component to find bottlenecks"""
    
    def __init__(self):
        self.timings = {}
        self.bottlenecks = []
    
    async def profile_jobspy_scraping(self):
        """Profile JobSpy scraping performance"""
        print("🔍 PROFILING: JobSpy Scraping")
        
        try:
            from src.scrapers.jobspy_scraper_v2 import JobSpyImprovedScraper, JobSpyConfig
            
            config = JobSpyConfig(
                locations=["Toronto, ON"],
                search_terms=["python developer"],
                sites=["indeed"],
                results_per_search=10,
                hours_old=72,
                max_total_jobs=10
            )
            
            scraper = JobSpyImprovedScraper("test_profile", config)
            
            # Time each phase
            start_time = time.time()
            
            # Profile initialization
            init_time = time.time()
            self.timings['jobspy_init'] = init_time - start_time
            
            # Profile actual scraping
            scrape_start = time.time()
            jobs = await scraper.scrape_jobs_Improved(10)
            scrape_end = time.time()
            
            self.timings['jobspy_scraping'] = scrape_end - scrape_start
            self.timings['jobspy_jobs_found'] = len(jobs)
            self.timings['jobspy_jobs_per_sec'] = len(jobs) / (scrape_end - scrape_start)
            
            print(f"   Init time: {self.timings['jobspy_init']:.2f}s")
            print(f"   Scraping time: {self.timings['jobspy_scraping']:.2f}s")
            print(f"   Jobs found: {len(jobs)}")
            print(f"   Speed: {self.timings['jobspy_jobs_per_sec']:.2f} jobs/sec")
            
            return jobs
            
        except Exception as e:
            print(f"   ❌ JobSpy profiling failed: {e}")
            return []
    
    async def profile_ai_processing(self, jobs: List[Dict]):
        """Profile AI processing performance"""
        print("\n🧠 PROFILING: AI Processing")
        
        if not jobs:
            print("   ⚠️ No jobs to process")
            return []
        
        try:
            from src.analysis.two_stage_processor import get_two_stage_processor
            from src.utils.profile_helpers import load_profile
            
            # Load profile
            profile = load_profile("Nirajan") or {"skills": ["python"], "name": "test"}
            
            # Time processor initialization
            init_start = time.time()
            processor = get_two_stage_processor(profile, cpu_workers=4)
            init_end = time.time()
            
            self.timings['ai_init'] = init_end - init_start
            
            # Time Stage 1 processing
            stage1_start = time.time()
            stage1_results = processor.stage1_processor.process_jobs_batch(jobs[:5])  # Test with 5 jobs
            stage1_end = time.time()
            
            self.timings['stage1_time'] = stage1_end - stage1_start
            self.timings['stage1_jobs_per_sec'] = 5 / (stage1_end - stage1_start)
            
            # Time Stage 2 processing (if available)
            if processor.stage2_processor:
                stage2_start = time.time()
                # Process one job through Stage 2
                test_job = jobs[0] if jobs else {"title": "test", "description": "test python job"}
                test_s1 = stage1_results[0] if stage1_results else None
                
                if test_s1:
                    stage2_result = await asyncio.to_thread(
                        processor.stage2_processor.process_job_semantic, 
                        test_job, 
                        test_s1
                    )
                    stage2_end = time.time()
                    
                    self.timings['stage2_time'] = stage2_end - stage2_start
                    self.timings['stage2_jobs_per_sec'] = 1 / (stage2_end - stage2_start)
            
            print(f"   AI Init time: {self.timings['ai_init']:.2f}s")
            print(f"   Stage 1 time: {self.timings['stage1_time']:.2f}s")
            print(f"   Stage 1 speed: {self.timings['stage1_jobs_per_sec']:.2f} jobs/sec")
            
            if 'stage2_time' in self.timings:
                print(f"   Stage 2 time: {self.timings['stage2_time']:.2f}s")
                print(f"   Stage 2 speed: {self.timings['stage2_jobs_per_sec']:.2f} jobs/sec")
            
            return stage1_results
            
        except Exception as e:
            print(f"   ❌ AI processing profiling failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def profile_database_operations(self, jobs: List[Dict]):
        """Profile database save/load operations"""
        print("\n💾 PROFILING: Database Operations")
        
        try:
            from src.core.job_database import get_job_db
            
            db = get_job_db("test_profile")
            
            # Time database initialization
            init_start = time.time()
            # Database is already initialized above
            init_end = time.time()
            
            # Time job saving
            if jobs:
                save_start = time.time()
                for i, job in enumerate(jobs[:3]):  # Test with 3 jobs
                    job_data = {
                        'title': job.get('title', f'Test Job {i}'),
                        'company': job.get('company', f'Test Company {i}'),
                        'description': job.get('description', 'Test description'),
                        'url': job.get('url', f'https://test.com/job{i}'),
                        'location': job.get('location', 'Toronto, ON'),
                        'status': 'new'
                    }
                    db.add_job(job_data)
                save_end = time.time()
                
                self.timings['db_save_time'] = save_end - save_start
                self.timings['db_save_jobs_per_sec'] = 3 / (save_end - save_start)
                
                print(f"   Save time (3 jobs): {self.timings['db_save_time']:.2f}s")
                print(f"   Save speed: {self.timings['db_save_jobs_per_sec']:.2f} jobs/sec")
            
        except Exception as e:
            print(f"   ❌ Database profiling failed: {e}")
    
    def analyze_bottlenecks(self):
        """Analyze timing data to identify bottlenecks"""
        print("\n🎯 BOTTLENECK ANALYSIS")
        print("=" * 50)
        
        # Calculate total pipeline time
        total_time = 0
        components = []
        
        if 'jobspy_scraping' in self.timings:
            total_time += self.timings['jobspy_scraping']
            components.append(('JobSpy Scraping', self.timings['jobspy_scraping']))
        
        if 'ai_init' in self.timings:
            total_time += self.timings['ai_init']
            components.append(('AI Initialization', self.timings['ai_init']))
        
        if 'stage1_time' in self.timings:
            total_time += self.timings['stage1_time']
            components.append(('Stage 1 Processing', self.timings['stage1_time']))
        
        if 'stage2_time' in self.timings:
            # Extrapolate Stage 2 time for multiple jobs
            stage2_per_job = self.timings['stage2_time']
            estimated_stage2_total = stage2_per_job * 5  # For 5 jobs
            total_time += estimated_stage2_total
            components.append(('Stage 2 Processing (5 jobs)', estimated_stage2_total))
        
        if 'db_save_time' in self.timings:
            total_time += self.timings['db_save_time']
            components.append(('Database Operations', self.timings['db_save_time']))
        
        # Sort by time consumption
        components.sort(key=lambda x: x[1], reverse=True)
        
        print("Time breakdown (sorted by impact):")
        for component, time_taken in components:
            percentage = (time_taken / total_time * 100) if total_time > 0 else 0
            print(f"   {component}: {time_taken:.2f}s ({percentage:.1f}%)")
        
        print(f"\nTotal estimated time: {total_time:.2f}s")
        
        # Identify bottlenecks (>30% of total time)
        major_bottlenecks = [comp for comp, time_taken in components if (time_taken / total_time) > 0.3]
        
        if major_bottlenecks:
            print(f"\n🚨 MAJOR BOTTLENECKS (>30% of time):")
            for bottleneck in major_bottlenecks:
                print(f"   - {bottleneck}")
        
        return components, major_bottlenecks
    
    def suggest_optimizations(self, components, bottlenecks):
        """Suggest specific optimizations based on profiling"""
        print(f"\n🚀 OPTIMIZATION RECOMMENDATIONS")
        print("=" * 50)
        
        suggestions = []
        
        # Check JobSpy performance
        if 'jobspy_jobs_per_sec' in self.timings and self.timings['jobspy_jobs_per_sec'] < 2.0:
            suggestions.append({
                'component': 'JobSpy Scraping',
                'issue': f"Speed: {self.timings['jobspy_jobs_per_sec']:.1f} jobs/sec",
                'solutions': [
                    'Reduce search combinations',
                    'Use faster job sites (Indeed only)',
                    'Implement connection pooling',
                    'Cache recent results'
                ]
            })
        
        # Check AI processing
        if 'stage2_jobs_per_sec' in self.timings and self.timings['stage2_jobs_per_sec'] < 5.0:
            suggestions.append({
                'component': 'AI Processing (Stage 2)',
                'issue': f"Speed: {self.timings['stage2_jobs_per_sec']:.1f} jobs/sec",
                'solutions': [
                    'Implement true batch processing',
                    'Use smaller/faster models',
                    'Optimize GPU memory usage',
                    'Parallel processing with multiple GPUs'
                ]
            })
        
        # Check initialization overhead
        if 'ai_init' in self.timings and self.timings['ai_init'] > 2.0:
            suggestions.append({
                'component': 'AI Initialization',
                'issue': f"Slow startup: {self.timings['ai_init']:.1f}s",
                'solutions': [
                    'Model caching/persistence',
                    'Lazy loading',
                    'Pre-warmed model instances',
                    'Smaller model variants'
                ]
            })
        
        # Print suggestions
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion['component']}")
            print(f"   Issue: {suggestion['issue']}")
            print(f"   Solutions:")
            for solution in suggestion['solutions']:
                print(f"     - {solution}")
            print()
        
        return suggestions

async def main():
    """Run comprehensive performance profiling"""
    profiler = PerformanceProfiler()
    
    print("🔬 DEEP PERFORMANCE PROFILING")
    print("=" * 60)
    
    # Profile each component
    jobs = await profiler.profile_jobspy_scraping()
    await profiler.profile_ai_processing(jobs)
    await profiler.profile_database_operations(jobs)
    
    # Analyze results
    components, bottlenecks = profiler.analyze_bottlenecks()
    suggestions = profiler.suggest_optimizations(components, bottlenecks)
    
    print(f"\n🎯 NEXT STEPS:")
    if suggestions:
        print("Focus optimization efforts on the components above.")
        print("The biggest performance gains will come from addressing major bottlenecks.")
    else:
        print("System is well-optimized! Consider architectural improvements for further gains.")

if __name__ == "__main__":
    asyncio.run(main())