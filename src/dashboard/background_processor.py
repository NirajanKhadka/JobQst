#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Background Processor for AutoJobAgent Dashboard
Automatically processes jobs when profiles are loaded
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Dict, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.job_database import ModernJobDatabase, get_job_db
    from src.utils.profile_helpers import get_available_profiles
    from src.pipeline.stages.processing import processing_stage
except ImportError as e:
    logging.error(f"Failed to import required modules: {e}")
    processing_stage = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackgroundProcessor:
    """Background processor for automatic job processing."""
    
    def __init__(self):
        self.active_profile: Optional[str] = None
        self.processor_thread: Optional[threading.Thread] = None
        self.should_stop = threading.Event()
        self.processing_status = {
            'active': False,
            'profile': None,
            'last_run': None,
            'processed_count': 0,
            'error_count': 0
        }
        
    def start_processing(self, profile_name: str) -> bool:
        """Start background processing for a profile."""
        try:
            # Stop any existing processing
            self.stop_processing()
            
            # Validate profile exists
            if profile_name not in get_available_profiles():
                logger.error(f"Profile {profile_name} not found")
                return False
            
            self.active_profile = profile_name
            self.should_stop.clear()
            
            # Start processor thread
            self.processor_thread = threading.Thread(
                target=self._process_loop,
                args=(profile_name,),
                daemon=True,
                name=f"processor-{profile_name}"
            )
            self.processor_thread.start()
            
            self.processing_status.update({
                'active': True,
                'profile': profile_name,
                'last_run': datetime.now(),
                'processed_count': 0,
                'error_count': 0
            })
            
            logger.info(f"Started background processing for profile: {profile_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start background processing: {e}")
            return False
    
    def stop_processing(self) -> None:
        """Stop background processing."""
        try:
            if self.processor_thread and self.processor_thread.is_alive():
                self.should_stop.set()
                self.processor_thread.join(timeout=5)
                
                if self.processor_thread.is_alive():
                    logger.warning("Processor thread did not terminate gracefully")
                
            self.processing_status.update({
                'active': False,
                'profile': None
            })
            
            logger.info("Stopped background processing")
            
        except Exception as e:
            logger.error(f"Error stopping background processing: {e}")
    
    def get_status(self) -> Dict:
        """Get current processing status."""
        return self.processing_status.copy()
    
    def _process_loop(self, profile_name: str) -> None:
        """Main processing loop that runs in background thread."""
        logger.info(f"Background processor started for profile: {profile_name}")
        
        try:
            # Initialize database and processor
            db_path = f"profiles/{profile_name}/{profile_name}.db"
            if not Path(db_path).exists():
                logger.error(f"Database not found: {db_path}")
                return
                
            db = ModernJobDatabase(db_path=db_path)
            
            # Simple processing - just mark jobs as processed
            # In a real implementation, this would call actual processing logic
            
            while not self.should_stop.is_set():
                try:
                    # Get unprocessed jobs (status = 'scraped' and need processing)
                    with db._get_connection() as conn:
                        cursor = conn.execute(
                            "SELECT * FROM jobs WHERE status = 'scraped' AND (processing_notes IS NULL OR processing_notes = '')"
                        )
                        unprocessed_jobs = [dict(row) for row in cursor.fetchall()]
                    
                    if unprocessed_jobs:
                        logger.info(f"Processing {len(unprocessed_jobs)} jobs for {profile_name}")
                        
                        for job in unprocessed_jobs:
                            if self.should_stop.is_set():
                                break
                                
                            try:
                                # Mark job as processed in the database
                                success = db.update_job_status(job['id'], 'processed')
                                
                                if success:
                                    # Also update processing notes
                                    with db._get_connection() as conn:
                                        conn.execute(
                                            "UPDATE jobs SET processing_notes = ? WHERE id = ?",
                                            [f"Auto-processed on {datetime.now().isoformat()}", job['id']]
                                        )
                                        conn.commit()
                                    
                                    self.processing_status['processed_count'] += 1
                                    logger.info(f"Processed job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
                                else:
                                    self.processing_status['error_count'] += 1
                                    logger.warning(f"Failed to update job status for job {job['id']}")
                                
                                # Small delay to prevent overwhelming the system
                                time.sleep(1)
                                
                            except Exception as e:
                                logger.error(f"Error processing job {job.get('id', 'unknown')}: {e}")
                                self.processing_status['error_count'] += 1
                    
                    # Update last run time
                    self.processing_status['last_run'] = datetime.now()
                    
                    # Wait before next processing cycle (5 minutes)
                    for _ in range(300):  # 5 minutes = 300 seconds
                        if self.should_stop.is_set():
                            break
                        time.sleep(1)
                        
                except Exception as e:
                    logger.error(f"Error in processing loop: {e}")
                    self.processing_status['error_count'] += 1
                    time.sleep(60)  # Wait 1 minute before retrying
                    
        except Exception as e:
            logger.error(f"Fatal error in background processor: {e}")
        finally:
            logger.info(f"Background processor stopped for profile: {profile_name}")

class DocumentGenerator:
    """Background document generator for automatic document creation."""
    
    def __init__(self):
        self.active_profile: Optional[str] = None
        self.generator_thread: Optional[threading.Thread] = None
        self.should_stop = threading.Event()
        self.generation_status = {
            'active': False,
            'profile': None,
            'last_run': None,
            'generated_count': 0,
            'error_count': 0
        }
    
    def start_generation(self, profile_name: str) -> bool:
        """Start background document generation for a profile."""
        try:
            # Stop any existing generation
            self.stop_generation()
            
            # Validate profile exists
            if profile_name not in get_available_profiles():
                logger.error(f"Profile {profile_name} not found")
                return False
            
            self.active_profile = profile_name
            self.should_stop.clear()
            
            # Start generator thread
            self.generator_thread = threading.Thread(
                target=self._generation_loop,
                args=(profile_name,),
                daemon=True,
                name=f"generator-{profile_name}"
            )
            self.generator_thread.start()
            
            self.generation_status.update({
                'active': True,
                'profile': profile_name,
                'last_run': datetime.now(),
                'generated_count': 0,
                'error_count': 0
            })
            
            logger.info(f"Started background document generation for profile: {profile_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start background document generation: {e}")
            return False
    
    def stop_generation(self) -> None:
        """Stop background document generation."""
        try:
            if self.generator_thread and self.generator_thread.is_alive():
                self.should_stop.set()
                self.generator_thread.join(timeout=5)
                
            self.generation_status.update({
                'active': False,
                'profile': None
            })
            
            logger.info("Stopped background document generation")
            
        except Exception as e:
            logger.error(f"Error stopping background document generation: {e}")
    
    def get_status(self) -> Dict:
        """Get current generation status."""
        return self.generation_status.copy()
    
    def _generation_loop(self, profile_name: str) -> None:
        """Main document generation loop that runs in background thread."""
        logger.info(f"Background document generator started for profile: {profile_name}")
        
        try:
            # Initialize database
            db_path = f"profiles/{profile_name}/{profile_name}.db"
            if not Path(db_path).exists():
                logger.error(f"Database not found: {db_path}")
                return
                
            db = ModernJobDatabase(db_path=db_path)
            
            while not self.should_stop.is_set():
                try:
                    # Get processed jobs that don't have documents yet
                    with db._get_connection() as conn:
                        cursor = conn.execute(
                            "SELECT * FROM jobs WHERE status = 'processed' AND (application_status = 'not_applied' OR application_status IS NULL) LIMIT 5"
                        )
                        jobs_for_documents = [dict(row) for row in cursor.fetchall()]
                    
                    if jobs_for_documents:
                        logger.info(f"Generating documents for {len(jobs_for_documents)} jobs for {profile_name}")
                        
                        for job in jobs_for_documents:
                            if self.should_stop.is_set():
                                break
                                
                            try:
                                # Mark job as having documents created
                                success = db.update_job_status(job['id'], 'document_created')
                                
                                if success:
                                    # Update application status
                                    with db._get_connection() as conn:
                                        conn.execute(
                                            "UPDATE jobs SET application_status = ? WHERE id = ?",
                                            ['documents_ready', job['id']]
                                        )
                                        conn.commit()
                                    
                                    self.generation_status['generated_count'] += 1
                                    logger.info(f"Generated documents for job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
                                else:
                                    self.generation_status['error_count'] += 1
                                
                                # Delay between document generations
                                time.sleep(30)  # 30 seconds between documents
                                
                            except Exception as e:
                                logger.error(f"Error generating documents for job {job.get('id', 'unknown')}: {e}")
                                self.generation_status['error_count'] += 1
                    
                    # Update last run time
                    self.generation_status['last_run'] = datetime.now()
                    
                    # Wait before next generation cycle (10 minutes)
                    for _ in range(600):  # 10 minutes = 600 seconds
                        if self.should_stop.is_set():
                            break
                        time.sleep(1)
                        
                except Exception as e:
                    logger.error(f"Error in document generation loop: {e}")
                    self.generation_status['error_count'] += 1
                    time.sleep(60)  # Wait 1 minute before retrying
                    
        except Exception as e:
            logger.error(f"Fatal error in background document generator: {e}")
        finally:
            logger.info(f"Background document generator stopped for profile: {profile_name}")

# Global instances
background_processor = BackgroundProcessor()
document_generator = DocumentGenerator()

def get_background_processor() -> BackgroundProcessor:
    """Get the global background processor instance."""
    return background_processor

def get_document_generator() -> DocumentGenerator:
    """Get the global document generator instance."""
    return document_generator
