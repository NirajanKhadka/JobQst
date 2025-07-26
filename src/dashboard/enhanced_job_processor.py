#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Job Processor for AutoJobAgent Dashboard
Integrates AI analysis with comprehensive job processing and dashboard updates
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Dict, List, Any, Optional, Callable
from queue import Queue
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.job_database import get_job_db, ModernJobDatabase
    from src.utils.profile_helpers import get_available_profiles, load_profile
    from src.ai.enhanced_job_analyzer import EnhancedJobAnalyzer
    from src.ai.reliable_job_processor_analyzer import ReliableJobProcessorAnalyzer
    from src.core.job_processor_queue import JobProcessorQueue, JobTask
    from src.scrapers.enhanced_job_description_scraper import EnhancedJobDescriptionScraper
    from src.core.text_utils import extract_keywords
    from src.utils.job_analysis_metadata import get_job_analysis_metadata_handler
except ImportError as e:
    logging.error(f"Failed to import required modules: {e}")
    # Fallback imports
    try:
        from src.ai.reliable_job_processor_analyzer import ReliableJobProcessorAnalyzer
    except ImportError:
        ReliableJobProcessorAnalyzer = None

try:
    from src.core.job_processor_queue import JobProcessorQueue, JobTask
except ImportError as e:
    logging.error(f"Failed to import JobTask or JobProcessorQueue: {e}")
    JobTask = None  # Fallback to None for debugging
    JobProcessorQueue = None

# Configure logging - reduce verbosity
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class EnhancedJobProcessor:
    """Enhanced job processor with AI analysis integration and dashboard updates."""
    
    def __init__(self, profile_name: str = "Nirajan"):
        self.profile_name = profile_name
        self.profile = load_profile(profile_name)
        self.db = get_job_db(profile_name)
        
        # Initialize reliable AI analyzer with OpenHermes 2.5 primary
        if ReliableJobProcessorAnalyzer is not None:
            self.ai_analyzer = ReliableJobProcessorAnalyzer(
                profile=self.profile,
                ollama_endpoint="http://localhost:11434",
                enable_ai_fallback=True
            )
            logger.info("Using ReliableJobProcessorAnalyzer with OpenHermes 2.5 for fault-tolerant analysis")
        else:
            # Fallback to legacy analyzer with OpenHermes 2.5 primary
            self.ai_analyzer = EnhancedJobAnalyzer(
                profile=self.profile,
                use_mistral=True,  # This now uses OpenHermes 2.5
                fallback_to_llama=True,
                fallback_to_rule_based=True
            )
            logger.warning("ReliableJobProcessorAnalyzer not available, using legacy EnhancedJobAnalyzer with OpenHermes 2.5")
        
        # Initialize job scraper
        self.job_scraper = EnhancedJobDescriptionScraper()
        
        # Initialize metadata handler
        self.metadata_handler = get_job_analysis_metadata_handler()
        
        # Processing status
        self.processing_status = {
            'active': False,
            'profile': profile_name,
            'last_run': None,
            'processed_count': 0,
            'error_count': 0,
            'ai_analyzed_count': 0,
            'avg_processing_time': 0.0,
            'queue_size': 0
        }
        
        # Processing queue
        self.processing_queue = Queue()
        self.result_queue = Queue()
        
        # Threading
        self.processing_thread = None
        self.should_stop = threading.Event()
        
        # Dashboard callback
        self.dashboard_callback: Optional[Callable] = None
        
        # Statistics
        self.stats = {
            'total_jobs_processed': 0,
            'jobs_with_ai_analysis': 0,
            'average_ai_score': 0.0,
            'high_matches_found': 0,
            'processing_errors': 0,
            'start_time': None,
            'last_update': None,
            'analysis_methods': {
                'ai': 0,
                'enhanced_rule_based': 0,
                'fallback': 0
            },
            'ai_service_health': {
                'last_successful_ai': None,
                'consecutive_failures': 0,
                'connection_status': 'unknown'
            }
        }
    
    def set_dashboard_callback(self, callback: Callable):
        """Set callback function for dashboard updates."""
        self.dashboard_callback = callback
    
    def start_processing(self) -> bool:
        """Start enhanced job processing."""
        try:
            if self.processing_status['active']:
                logger.info("Processing already active")
                return True
            
            self.should_stop.clear()
            
            # Start processing thread
            self.processing_thread = threading.Thread(
                target=self._processing_loop,
                daemon=True,
                name=f"enhanced-processor-{self.profile_name}"
            )
            self.processing_thread.start()
            
            self.processing_status.update({
                'active': True,
                'last_run': datetime.now(),
                'processed_count': 0,
                'error_count': 0,
                'ai_analyzed_count': 0
            })
            
            self.stats['start_time'] = datetime.now().isoformat()
            
            logger.info(f"Started enhanced job processing for profile: {self.profile_name}")
            self._update_dashboard()
            return True
            
        except Exception as e:
            logger.error(f"Failed to start enhanced job processing: {e}")
            return False
    
    def stop_processing(self) -> bool:
        """Stop enhanced job processing."""
        try:
            self.should_stop.set()
            
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5)
            
            self.processing_status['active'] = False
            logger.info(f"Stopped enhanced job processing for profile: {self.profile_name}")
            self._update_dashboard()
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop enhanced job processing: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current processing status."""
        return {
            **self.processing_status,
            'stats': self.stats,
            'queue_size': self.processing_queue.qsize()
        }
    
    def add_jobs_for_processing(self, jobs: List[Dict[str, Any]]) -> int:
        """Add jobs to the processing queue."""
        added_count = 0
        
        for job in jobs:
            try:
                # Create job task
                job_task = JobTask(
                    job_url=job.get('url', ''),
                    job_id=job.get('id', ''),
                    title=job.get('title', ''),
                    company=job.get('company', ''),
                    location=job.get('location', ''),
                    search_keyword=job.get('search_keyword', '')
                )
                
                self.processing_queue.put(job_task)
                added_count += 1
                
            except Exception as e:
                logger.error(f"Failed to add job to queue: {e}")
                self.processing_status['error_count'] += 1
        
        self.processing_status['queue_size'] = self.processing_queue.qsize()
        logger.info(f"Added {added_count} jobs to processing queue")
        return added_count
    
    def _processing_loop(self):
        """Main processing loop."""
        logger.info(f"Enhanced processing loop started for profile: {self.profile_name}")
        
        while not self.should_stop.is_set():
            try:
                # Get job from queue with timeout
                try:
                    job_task = self.processing_queue.get(timeout=1)
                except:
                    continue
                
                # Process the job
                start_time = time.time()
                success = self._process_single_job(job_task)
                processing_time = time.time() - start_time
                
                # Update statistics
                self.processing_status['processed_count'] += 1
                self.stats['total_jobs_processed'] += 1
                
                if success:
                    # Update average processing time
                    current_avg = self.processing_status['avg_processing_time']
                    total_processed = self.processing_status['processed_count']
                    new_avg = ((current_avg * (total_processed - 1)) + processing_time) / total_processed
                    self.processing_status['avg_processing_time'] = new_avg
                else:
                    self.processing_status['error_count'] += 1
                    self.stats['processing_errors'] += 1
                
                # Update last run time
                self.processing_status['last_run'] = datetime.now()
                self.stats['last_update'] = datetime.now().isoformat()
                
                # Update dashboard periodically
                if self.processing_status['processed_count'] % 5 == 0:  # Every 5 jobs
                    self._update_dashboard()
                
                # Mark task as done
                self.processing_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                self.processing_status['error_count'] += 1
                self.stats['processing_errors'] += 1
        
        logger.info("Enhanced processing loop stopped")
    
    def _process_single_job(self, job_task: JobTask) -> bool:
        """Process a single job with AI analysis."""
        try:
            logger.info(f"Processing job: {job_task.title} at {job_task.company}")
            
            # Get job from database
            job_data = self.db.get_job_by_id(job_task.job_id)
            if not job_data:
                logger.warning(f"Job not found in database: {job_task.job_id}")
                return False
            
            # Enhance job description if needed
            enhanced_job = self._enhance_job_description(job_data)
            
            # Perform AI analysis
            ai_analysis = self._perform_ai_analysis(enhanced_job)
            
            # Update job with analysis results
            success = self._update_job_with_analysis(job_data, enhanced_job, ai_analysis)
            
            if success:
                self.processing_status['ai_analyzed_count'] += 1
                self.stats['jobs_with_ai_analysis'] += 1
                
                # Update average AI score
                ai_score = ai_analysis.get('compatibility_score', 0.5)
                current_avg = self.stats['average_ai_score']
                total_analyzed = self.stats['jobs_with_ai_analysis']
                new_avg = ((current_avg * (total_analyzed - 1)) + ai_score) / total_analyzed
                self.stats['average_ai_score'] = new_avg
                
                # Count high matches
                if ai_score >= 0.8:
                    self.stats['high_matches_found'] += 1
                
                logger.info(f"Successfully processed job: {job_task.title} (AI Score: {ai_score:.2f})")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing job {job_task.job_id}: {e}")
            return False
    
    def _enhance_job_description(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance job description with additional details."""
        try:
            enhanced_job = job_data.copy()
            
            # Extract keywords from description
            if job_data.get('description'):
                keywords = extract_keywords(job_data['description'], max_keywords=20)
                enhanced_job['extracted_keywords'] = keywords
            
            # Extract skills from description
            if job_data.get('description'):
                skills = extract_keywords(job_data['description'], max_keywords=15)
                enhanced_job['extracted_skills'] = skills
            
            # Add processing metadata
            enhanced_job['processing_timestamp'] = datetime.now().isoformat()
            enhanced_job['processor_version'] = 'enhanced_v1.0'
            
            return enhanced_job
            
        except Exception as e:
            logger.error(f"Error enhancing job description: {e}")
            return job_data
    
    def _perform_ai_analysis(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform AI analysis on job data with enhanced tracking."""
        try:
            # Use reliable job analyzer
            analysis_result = self.ai_analyzer.analyze_job(job_data)
            
            # Ensure all required fields are present
            if not analysis_result:
                analysis_result = self._create_default_analysis()
            
            # Track analysis method used
            analysis_method = analysis_result.get('analysis_method', 'unknown')
            # Map OpenHermes method to stats tracking
            if analysis_method == 'openhermes_2_5':
                self.stats['analysis_methods']['ai'] += 1
            elif analysis_method in ['mistral_7b', 'llama3']:
                self.stats['analysis_methods']['ai'] += 1
            elif analysis_method == 'enhanced_rule_based':
                self.stats['analysis_methods']['enhanced_rule_based'] += 1
            else:
                self.stats['analysis_methods']['fallback'] += 1
            
            # Update AI service health tracking
            if analysis_method in ['openhermes_2_5', 'mistral_7b', 'llama3']:
                self.stats['ai_service_health']['last_successful_ai'] = datetime.now().isoformat()
                self.stats['ai_service_health']['consecutive_failures'] = 0
                self.stats['ai_service_health']['connection_status'] = 'connected'
            elif analysis_method == 'enhanced_rule_based':
                self.stats['ai_service_health']['consecutive_failures'] += 1
                if self.stats['ai_service_health']['consecutive_failures'] >= 3:
                    self.stats['ai_service_health']['connection_status'] = 'disconnected'
            
            # Add analysis metadata
            analysis_result['analysis_timestamp'] = datetime.now().isoformat()
            analysis_result['analyzer_version'] = 'reliable_v1.0'
            analysis_result['profile_used'] = self.profile_name
            
            # Get analyzer statistics if available
            if hasattr(self.ai_analyzer, 'get_analysis_statistics'):
                try:
                    analyzer_stats = self.ai_analyzer.get_analysis_statistics()
                    analysis_result['analyzer_stats'] = analyzer_stats
                except Exception as stats_error:
                    logger.debug(f"Could not get analyzer statistics: {stats_error}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error performing AI analysis: {e}")
            # Update failure tracking
            self.stats['ai_service_health']['consecutive_failures'] += 1
            return self._create_default_analysis()
    
    def _create_default_analysis(self) -> Dict[str, Any]:
        """Create default analysis when AI analysis fails."""
        return {
            'compatibility_score': 0.7,
            'confidence': 0.7,
            'skill_matches': [],
            'skill_gaps': [],
            'experience_match': 'unknown',
            'location_match': 'unknown',
            'cultural_fit': 0.5,
            'growth_potential': 0.5,
            'recommendation': 'consider',
            'reasoning': 'Analysis not available - using default values',
            'analysis_timestamp': datetime.now().isoformat(),
            'analyzer_version': 'enhanced_v1.0_fallback',
            'profile_used': self.profile_name
        }
    
    def _update_job_with_analysis(self, original_job: Dict[str, Any], enhanced_job: Dict[str, Any], ai_analysis: Dict[str, Any]) -> bool:
        """Update job in database with enhanced data and AI analysis."""
        try:
            # Only update fields that exist in the database schema
            updated_job = {
                'match_score': ai_analysis.get('compatibility_score', 0.5),
                'status': 'processed',
                'processing_notes': f"Enhanced processing completed on {datetime.now().isoformat()}",
                'analysis_data': json.dumps(ai_analysis)  # Store full analysis as JSON
            }
            
            # Add extracted keywords if available
            if enhanced_job.get('extracted_keywords'):
                updated_job['keywords'] = ', '.join(enhanced_job['extracted_keywords'][:10])  # Limit to 10 keywords
            
            # Update job in database
            success = self.db.update_job(original_job['id'], updated_job)
            
            if success:
                logger.info(f"Successfully updated job {original_job['id']} with AI analysis")
            else:
                logger.warning(f"Failed to update job {original_job['id']} in database")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating job with analysis: {e}")
            return False
    
    def _update_dashboard(self):
        """Update dashboard with current processing status."""
        if self.dashboard_callback:
            try:
                dashboard_data = {
                    'type': 'enhanced_job_processing_update',
                    'profile': self.profile_name,
                    'processing_status': self.processing_status,
                    'stats': self.stats,
                    'timestamp': datetime.now().isoformat()
                }
                self.dashboard_callback(dashboard_data)
            except Exception as e:
                logger.warning(f"Dashboard update error: {e}")
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get comprehensive processing summary."""
        return {
            'profile': self.profile_name,
            'status': self.processing_status,
            'statistics': self.stats,
            'queue_info': {
                'queue_size': self.processing_queue.qsize(),
                'is_active': self.processing_status['active']
            },
            'ai_analysis_summary': {
                'total_analyzed': self.stats['jobs_with_ai_analysis'],
                'average_score': self.stats['average_ai_score'],
                'high_matches': self.stats['high_matches_found'],
                'success_rate': (self.stats['jobs_with_ai_analysis'] / max(self.stats['total_jobs_processed'], 1)) * 100
            }
        }
    
    def process_scraped_jobs(self) -> int:
        """Process all scraped jobs (status='scraped') with AI analysis."""
        try:
            # Get all jobs with status 'scraped' (URLs only, need processing)
            scraped_jobs = []
            all_jobs = self.db.get_all_jobs()
            
            for job in all_jobs:
                if job.get('status') == 'scraped' and job.get('title') == 'Pending Processing':
                    scraped_jobs.append(job)
            
            logger.info(f"Found {len(scraped_jobs)} scraped jobs to process")
            
            if not scraped_jobs:
                logger.info("No scraped jobs found to process")
                return 0
            
            # Add jobs to processing queue
            added_count = self.add_jobs_for_processing(scraped_jobs)
            
            logger.info(f"Added {added_count} scraped jobs for AI processing")
            return added_count
            
        except Exception as e:
            logger.error(f"Error processing scraped jobs: {e}")
            return 0

    def reprocess_jobs_with_ai(self, job_ids: List[str] = None) -> int:
        """Reprocess specific jobs or all jobs with AI analysis."""
        try:
            if job_ids:
                # Reprocess specific jobs
                jobs_to_process = []
                for job_id in job_ids:
                    job_data = self.db.get_job_by_id(job_id)
                    if job_data:
                        jobs_to_process.append(job_data)
            else:
                # Reprocess all jobs without AI analysis
                jobs_to_process = self.db.get_jobs_by_status('scraped')
            
            # Add jobs to processing queue
            added_count = self.add_jobs_for_processing(jobs_to_process)
            
            logger.info(f"Added {added_count} jobs for AI reprocessing")
            return added_count
            
        except Exception as e:
            logger.error(f"Error reprocessing jobs: {e}")
            return 0


# Global instance
_enhanced_processor = None

def get_enhanced_job_processor(profile_name: str = "Nirajan") -> EnhancedJobProcessor:
    """Get or create enhanced job processor instance."""
    global _enhanced_processor
    
    if _enhanced_processor is None or _enhanced_processor.profile_name != profile_name:
        _enhanced_processor = EnhancedJobProcessor(profile_name)
    
    return _enhanced_processor

def start_enhanced_processing(profile_name: str = "Nirajan") -> bool:
    """Start enhanced job processing for a profile."""
    processor = get_enhanced_job_processor(profile_name)
    return processor.start_processing()

def stop_enhanced_processing() -> bool:
    """Stop enhanced job processing."""
    global _enhanced_processor
    
    if _enhanced_processor:
        return _enhanced_processor.stop_processing()
    
    return True

def get_enhanced_processing_status(profile_name: str = "Nirajan") -> Dict[str, Any]:
    """Get enhanced processing status."""
    processor = get_enhanced_job_processor(profile_name)
    return processor.get_status() 