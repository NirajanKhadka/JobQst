"""
Master/Slave Job Processing System
Handles the backlog of unprocessed jobs with efficient parallel processing.
"""

import asyncio
import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import os
from dataclasses import dataclass
from enum import Enum
import queue
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class JobTask:
    job_id: int
    job_data: dict
    status: JobStatus
    assigned_worker: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

class JobProcessorMaster:
    def __init__(self, profile_name: str, max_workers: int = 4):
        self.profile_name = profile_name
        self.max_workers = max_workers
        self.job_queue = queue.Queue()
        self.completed_jobs = queue.Queue()
        self.failed_jobs = queue.Queue()
        self.workers = {}
        self.stats = {
            "total_jobs": 0,
            "processed_jobs": 0,
            "failed_jobs": 0,
            "skipped_jobs": 0,
            "start_time": None,
            "end_time": None
        }
        self.running = False
        self.db_path = f"profiles/{profile_name}/{profile_name}.db"
        self.lock = threading.Lock()
        
        # Initialize database
        self.initialize_processing_database()
    
    def initialize_processing_database(self):
        """Initialize database for job processing tracking."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create job processing table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_processing (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER,
                    status TEXT,
                    assigned_worker TEXT,
                    started_at DATETIME,
                    completed_at DATETIME,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs (id)
                )
            """)
            
            # Create processing stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    total_jobs INTEGER,
                    processed_jobs INTEGER,
                    failed_jobs INTEGER,
                    skipped_jobs INTEGER,
                    start_time DATETIME,
                    end_time DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info(f"Job processing database initialized for profile {self.profile_name}")
            
        except Exception as e:
            logger.error(f"Error initializing processing database: {e}")
    
    def load_unprocessed_jobs(self) -> List[JobTask]:
        """Load all unprocessed jobs from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First, check what columns exist in the jobs table
            cursor.execute("PRAGMA table_info(jobs)")
            columns_info = cursor.fetchall()
            existing_columns = [col[1] for col in columns_info]
            
            # Build dynamic query based on existing columns
            select_columns = []
            if 'id' in existing_columns:
                select_columns.append('j.id')
            if 'title' in existing_columns:
                select_columns.append('j.title')
            if 'company' in existing_columns:
                select_columns.append('j.company')
            if 'location' in existing_columns:
                select_columns.append('j.location')
            if 'description' in existing_columns:
                select_columns.append('j.description')
            if 'url' in existing_columns:
                select_columns.append('j.url')
            if 'site' in existing_columns:
                select_columns.append('j.site')
            if 'scraped_at' in existing_columns:
                select_columns.append('j.scraped_at')
            if 'experience_level' in existing_columns:
                select_columns.append('j.experience_level')
            if 'salary_range' in existing_columns:
                select_columns.append('j.salary_range')
            if 'job_type' in existing_columns:
                select_columns.append('j.job_type')
            if 'remote_work' in existing_columns:
                select_columns.append('j.remote_work')
            if 'requirements' in existing_columns:
                select_columns.append('j.requirements')
            if 'benefits' in existing_columns:
                select_columns.append('j.benefits')
            
            # If no columns found, return empty list
            if not select_columns:
                logger.warning("No columns found in jobs table")
                conn.close()
                return []
            
            # Build and execute query
            query = f"""
                SELECT {', '.join(select_columns)}
                FROM jobs j
                LEFT JOIN job_processing jp ON j.id = jp.job_id
                WHERE jp.id IS NULL OR jp.status IN ('failed', 'pending')
                ORDER BY j.scraped_at DESC
            """
            
            cursor.execute(query)
            
            jobs = []
            for row in cursor.fetchall():
                # Create job data dictionary based on available columns
                job_data = {}
                for i, col_name in enumerate([col.split('.')[-1] for col in select_columns]):
                    job_data[col_name] = row[i]
                
                # Ensure we have at least an ID
                if 'id' not in job_data:
                    continue
                
                job_task = JobTask(
                    job_id=job_data['id'],
                    job_data=job_data,
                    status=JobStatus.PENDING
                )
                jobs.append(job_task)
            
            conn.close()
            logger.info(f"Loaded {len(jobs)} unprocessed jobs for profile {self.profile_name}")
            return jobs
            
        except Exception as e:
            logger.error(f"Error loading unprocessed jobs: {e}")
            return []
    
    def start_processing(self):
        """Start the master job processing system."""
        try:
            logger.info(f"🚀 Starting Job Processing Master for profile {self.profile_name}")
            
            # Load unprocessed jobs
            unprocessed_jobs = self.load_unprocessed_jobs()
            self.stats["total_jobs"] = len(unprocessed_jobs)
            self.stats["start_time"] = datetime.now()
            
            if not unprocessed_jobs:
                logger.info("No unprocessed jobs found")
                return
            
            logger.info(f"📊 Found {len(unprocessed_jobs)} jobs to process")
            
            # Add jobs to queue
            for job in unprocessed_jobs:
                self.job_queue.put(job)
            
            # Start workers
            self.running = True
            self.start_workers()
            
            # Start monitoring
            self.start_monitoring()
            
            # Wait for completion
            self.wait_for_completion()
            
        except Exception as e:
            logger.error(f"Error starting job processing: {e}")
    
    def start_workers(self):
        """Start worker processes."""
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                for i in range(self.max_workers):
                    worker_name = f"worker-{i+1}"
                    future = executor.submit(self.worker_process, worker_name)
                    self.workers[worker_name] = future
                    logger.info(f"Started worker {worker_name}")
            
        except Exception as e:
            logger.error(f"Error starting workers: {e}")
    
    def worker_process(self, worker_name: str):
        """Worker process that processes jobs from the queue."""
        logger.info(f"🔄 Worker {worker_name} started")
        
        while self.running:
            try:
                # Get job from queue with timeout
                try:
                    job_task = self.job_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Process the job
                self.process_job(job_task, worker_name)
                
                # Mark task as done
                self.job_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in worker {worker_name}: {e}")
                time.sleep(1)
        
        logger.info(f"🛑 Worker {worker_name} stopped")
    
    def process_job(self, job_task: JobTask, worker_name: str):
        """Process a single job."""
        try:
            # Update job status
            job_task.status = JobStatus.PROCESSING
            job_task.assigned_worker = worker_name
            job_task.started_at = datetime.now()
            
            # Log processing start
            logger.info(f"🔄 Processing job {job_task.job_id} ({job_task.job_data['title']}) with {worker_name}")
            
            # Perform job analysis
            analysis_result = self.analyze_job(job_task.job_data)
            
            # Generate documents if needed
            if analysis_result.get("should_apply", False):
                documents = self.generate_documents(job_task.job_data, analysis_result)
                
                # Update job with analysis results
                self.update_job_with_analysis(job_task.job_id, analysis_result, documents)
            
            # Mark as completed
            job_task.status = JobStatus.COMPLETED
            job_task.completed_at = datetime.now()
            
            # Update stats
            with self.lock:
                self.stats["processed_jobs"] += 1
            
            logger.info(f"✅ Completed job {job_task.job_id} with {worker_name}")
            
        except Exception as e:
            # Handle failure
            job_task.status = JobStatus.FAILED
            job_task.error_message = str(e)
            job_task.retry_count += 1
            
            with self.lock:
                self.stats["failed_jobs"] += 1
            
            logger.error(f"❌ Failed to process job {job_task.job_id}: {e}")
            
            # Retry if possible
            if job_task.retry_count < job_task.max_retries:
                logger.info(f"🔄 Retrying job {job_task.job_id} (attempt {job_task.retry_count + 1})")
                job_task.status = JobStatus.PENDING
                self.job_queue.put(job_task)
        
        finally:
            # Save processing record
            self.save_processing_record(job_task)
    
    def analyze_job(self, job_data: dict) -> dict:
        """Analyze a job using AI to determine relevance and requirements."""
        try:
            # Import job analyzer
            from src.utils.job_analyzer import JobAnalyzer
            
            analyzer = JobAnalyzer()
            
            # Analyze job relevance
            relevance_score = analyzer.analyze_job_relevance(job_data)
            
            # Extract requirements
            requirements = analyzer.extract_requirements(job_data.get("description", ""))
            
            # Determine if should apply
            should_apply = relevance_score > 0.7  # Threshold for application
            
            return {
                "relevance_score": relevance_score,
                "requirements": requirements,
                "should_apply": should_apply,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing job: {e}")
            return {
                "relevance_score": 0.0,
                "requirements": [],
                "should_apply": False,
                "error": str(e),
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def generate_documents(self, job_data: dict, analysis_result: dict) -> dict:
        """Generate customized documents for the job."""
        try:
            # Import document generator
            from src.utils.document_generator import DocumentGenerator
            
            generator = DocumentGenerator()
            
            # Generate customized resume
            resume_path = generator.generate_customized_resume(
                job_data, 
                analysis_result.get("requirements", [])
            )
            
            # Generate cover letter
            cover_letter_path = generator.generate_cover_letter(
                job_data, 
                analysis_result
            )
            
            return {
                "resume_path": resume_path,
                "cover_letter_path": cover_letter_path,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating documents: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    def update_job_with_analysis(self, job_id: int, analysis_result: dict, documents: dict):
        """Update job record with analysis results."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Add analysis columns if they don't exist
            cursor.execute("PRAGMA table_info(jobs)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "analysis_result" not in columns:
                cursor.execute("ALTER TABLE jobs ADD COLUMN analysis_result TEXT")
            if "documents" not in columns:
                cursor.execute("ALTER TABLE jobs ADD COLUMN documents TEXT")
            if "processed_at" not in columns:
                cursor.execute("ALTER TABLE jobs ADD COLUMN processed_at DATETIME")
            
            # Update job with analysis
            cursor.execute("""
                UPDATE jobs 
                SET analysis_result = ?, documents = ?, processed_at = ?
                WHERE id = ?
            """, (
                json.dumps(analysis_result),
                json.dumps(documents),
                datetime.now().isoformat(),
                job_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating job with analysis: {e}")
    
    def save_processing_record(self, job_task: JobTask):
        """Save job processing record to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO job_processing 
                (job_id, status, assigned_worker, started_at, completed_at, error_message, retry_count, max_retries)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_task.job_id,
                job_task.status.value,
                job_task.assigned_worker,
                job_task.started_at.isoformat() if job_task.started_at else None,
                job_task.completed_at.isoformat() if job_task.completed_at else None,
                job_task.error_message,
                job_task.retry_count,
                job_task.max_retries
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving processing record: {e}")
    
    def start_monitoring(self):
        """Start monitoring thread for progress tracking."""
        def monitor():
            while self.running:
                try:
                    # Calculate progress
                    total = self.stats["total_jobs"]
                    processed = self.stats["processed_jobs"]
                    failed = self.stats["failed_jobs"]
                    
                    if total > 0:
                        progress = (processed + failed) / total * 100
                        logger.info(f"📊 Progress: {progress:.1f}% ({processed + failed}/{total}) - "
                                  f"✅ {processed} completed, ❌ {failed} failed")
                    
                    time.sleep(10)  # Update every 10 seconds
                    
                except Exception as e:
                    logger.error(f"Error in monitoring: {e}")
                    time.sleep(10)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def wait_for_completion(self):
        """Wait for all jobs to be processed."""
        try:
            # Wait for queue to be empty
            self.job_queue.join()
            
            # Stop workers
            self.running = False
            
            # Wait for workers to finish
            for worker_name, future in self.workers.items():
                try:
                    future.result(timeout=30)
                except Exception as e:
                    logger.error(f"Error waiting for worker {worker_name}: {e}")
            
            # Final stats
            self.stats["end_time"] = datetime.now()
            duration = self.stats["end_time"] - self.stats["start_time"]
            
            logger.info(f"🎉 Job processing completed!")
            logger.info(f"📊 Final Stats:")
            logger.info(f"   Total jobs: {self.stats['total_jobs']}")
            logger.info(f"   Processed: {self.stats['processed_jobs']}")
            logger.info(f"   Failed: {self.stats['failed_jobs']}")
            logger.info(f"   Duration: {duration}")
            
            # Save final stats
            self.save_final_stats()
            
        except Exception as e:
            logger.error(f"Error waiting for completion: {e}")
    
    def save_final_stats(self):
        """Save final processing statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            session_id = f"session_{int(time.time())}"
            
            cursor.execute("""
                INSERT INTO processing_stats 
                (session_id, total_jobs, processed_jobs, failed_jobs, skipped_jobs, start_time, end_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                self.stats["total_jobs"],
                self.stats["processed_jobs"],
                self.stats["failed_jobs"],
                self.stats["skipped_jobs"],
                self.stats["start_time"].isoformat(),
                self.stats["end_time"].isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"📈 Processing stats saved with session ID: {session_id}")
            
        except Exception as e:
            logger.error(f"Error saving final stats: {e}")
    
    def get_processing_stats(self) -> dict:
        """Get current processing statistics."""
        return {
            "profile": self.profile_name,
            "running": self.running,
            "stats": self.stats.copy(),
            "queue_size": self.job_queue.qsize(),
            "active_workers": len([w for w in self.workers.values() if not w.done()])
        }

def start_job_processing(profile_name: str, max_workers: int = 4):
    """Start job processing for a profile."""
    try:
        processor = JobProcessorMaster(profile_name, max_workers)
        processor.start_processing()
        return processor
    except Exception as e:
        logger.error(f"Error starting job processing: {e}")
        return None

if __name__ == "__main__":
    import sys
    profile_name = sys.argv[1] if len(sys.argv) > 1 else "Nirajan"
    max_workers = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    
    print(f"🚀 Starting Job Processing Master")
    print(f"📊 Profile: {profile_name}")
    print(f"👥 Workers: {max_workers}")
    
    processor = start_job_processing(profile_name, max_workers) 