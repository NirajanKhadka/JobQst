#!/usr/bin/env python3
"""
Verified Job Processor - Only marks jobs as processed when all required fields are filled
Uses job verifier and enhanced tab management
"""

import asyncio
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
import sys
from typing import Dict, List, Any, Optional
from queue import Queue
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.job_database import get_job_db
from src.utils.job_verifier import get_job_verifier
from src.scrapers.enhanced_job_scraper_with_tab_management import scrape_job_with_proper_tab_management
from src.utils.profile_helpers import load_profile

# Try to import AI analyzer, but make it optional
try:
    from src.ai.reliable_job_processor_analyzer import ReliableJobProcessorAnalyzer
except ImportError:
    ReliableJobProcessorAnalyzer = None
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()
logger = logging.getLogger(__name__)

class VerifiedJobProcessor:
    """Job processor that only marks jobs as processed when all required fields are verified."""
    
    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self.db = get_job_db(profile_name)
        self.verifier = get_job_verifier()
        
        # Initialize AI analyzer if available
        if ReliableJobProcessorAnalyzer:
            try:
                # Load profile properly
                profile = load_profile(profile_name)
                self.ai_analyzer = ReliableJobProcessorAnalyzer(profile)
            except Exception as e:
                console.print(f"[yellow]⚠️ AI analyzer initialization failed: {e}[/yellow]")
                self.ai_analyzer = None
        else:
            self.ai_analyzer = None
        
        self.processing_stats = {
            'total_jobs': 0,
            'verified_complete': 0,
            'needs_processing': 0,
            'failed_scraping': 0,
            'ai_analyzed': 0,
            'processing_errors': 0
        }
        
        self.is_running = False
        self.processing_thread = None
        self.job_queue = Queue()
    
    def start_processing(self) -> bool:
        """Start the verified job processor."""
        if self.is_running:
            console.print("[yellow]⚠️ Processor is already running[/yellow]")
            return False
        
        try:
            self.is_running = True
            self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
            self.processing_thread.start()
            
            console.print("[green]✅ Verified job processor started[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to start processor: {e}[/red]")
            self.is_running = False
            return False
    
    def stop_processing(self):
        """Stop the job processor."""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        console.print("[yellow]⏹️ Verified job processor stopped[/yellow]")
    
    def add_jobs_for_verification(self) -> int:
        """Add jobs that need verification to the processing queue."""
        # Get all jobs that are not properly verified
        all_jobs = self.db.get_all_jobs()
        jobs_added = 0
        
        for job in all_jobs:
            verification = self.verifier.verify_job_completeness(job)
            
            # Add job to queue if it's not complete or marked as processed incorrectly
            if not verification['is_complete'] or job.get('status') == 'processed':
                # Only add if not already in queue
                if not any(queued_job['id'] == job['id'] for queued_job in list(self.job_queue.queue)):
                    self.job_queue.put(job)
                    jobs_added += 1
        
        console.print(f"[blue]📥 Added {jobs_added} jobs for verification[/blue]")
        return jobs_added
    
    def _processing_loop(self):
        """Main processing loop."""
        console.print("[blue]🔄 Starting verified processing loop[/blue]")
        
        while self.is_running:
            try:
                if not self.job_queue.empty():
                    job = self.job_queue.get(timeout=1)
                    asyncio.run(self._process_single_job(job))
                else:
                    time.sleep(1)  # Wait for jobs
                    
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                self.processing_stats['processing_errors'] += 1
                time.sleep(2)
    
    async def _process_single_job(self, job: Dict[str, Any]):
        """Process a single job with verification."""
        job_id = job.get('id')
        job_url = job.get('url')
        
        console.print(f"[blue]🔄 Processing job {job_id}: {job_url[:50]}...[/blue]")
        
        try:
            self.processing_stats['total_jobs'] += 1
            
            # Step 1: Verify current job completeness
            verification = self.verifier.verify_job_completeness(job)
            
            if verification['is_complete']:
                # Job is already complete, just update status if needed
                if job.get('status') != 'processed':
                    self.db.update_job(job_id, {'status': 'processed'})
                    console.print(f"[green]✅ Job {job_id} verified as complete[/green]")
                
                self.processing_stats['verified_complete'] += 1
                return
            
            # Step 2: Job needs processing - scrape missing data
            console.print(f"[yellow]🔍 Job {job_id} needs processing: {verification['missing_required']}[/yellow]")
            
            # Scrape job data with proper tab management
            scraped_data = await scrape_job_with_proper_tab_management(job_url)
            
            if not scraped_data.get('extraction_success'):
                console.print(f"[red]❌ Failed to scrape job {job_id}[/red]")
                self.processing_stats['failed_scraping'] += 1
                
                # Mark as needs_processing for retry later
                self.db.update_job(job_id, {
                    'status': 'needs_processing',
                    'processing_notes': f"Scraping failed: {scraped_data.get('error', 'Unknown error')}"
                })
                return
            
            # Step 3: Update job with scraped data
            update_data = {}
            
            # Map scraped data to database fields
            if scraped_data.get('title'):
                update_data['title'] = scraped_data['title']
            if scraped_data.get('company'):
                update_data['company'] = scraped_data['company']
            if scraped_data.get('description'):
                update_data['description'] = scraped_data['description']
            if scraped_data.get('location'):
                update_data['location'] = scraped_data['location']
            if scraped_data.get('salary'):
                update_data['salary'] = scraped_data['salary']
            if scraped_data.get('keywords'):
                update_data['keywords'] = ', '.join(scraped_data['keywords'])
            
            # Update job in database
            self.db.update_job(job_id, update_data)
            
            # Step 4: Re-verify job completeness after update
            updated_job = self.db.get_job_by_id(job_id)
            if not updated_job:
                console.print(f"[red]❌ Could not retrieve updated job {job_id}[/red]")
                return
            
            final_verification = self.verifier.verify_job_completeness(updated_job)
            
            # Step 5: Run AI analysis if job is complete enough
            if final_verification['is_complete'] or len(final_verification['missing_required']) <= 1:
                try:
                    ai_analysis = await self._run_ai_analysis(updated_job)
                    if ai_analysis:
                        self.processing_stats['ai_analyzed'] += 1
                        
                        # Update with AI analysis
                        ai_update = {
                            'match_score': ai_analysis.get('compatibility_score', 0.5),
                            'analysis_data': json.dumps(ai_analysis)
                        }
                        self.db.update_job(job_id, ai_update)
                        
                except Exception as e:
                    console.print(f"[yellow]⚠️ AI analysis failed for job {job_id}: {e}[/yellow]")
            
            # Step 6: Set final status based on verification
            if final_verification['is_complete']:
                final_status = 'processed'
                self.processing_stats['verified_complete'] += 1
                console.print(f"[green]✅ Job {job_id} fully processed and verified[/green]")
            else:
                final_status = 'needs_processing'
                self.processing_stats['needs_processing'] += 1
                console.print(f"[yellow]⚠️ Job {job_id} still needs processing: {final_verification['missing_required']}[/yellow]")
            
            # Update final status
            self.db.update_job(job_id, {
                'status': final_status,
                'processing_notes': f"Verified processing completed: {datetime.now().isoformat()}",
                'verification_data': json.dumps(final_verification)
            })
            
        except Exception as e:
            console.print(f"[red]❌ Error processing job {job_id}: {e}[/red]")
            self.processing_stats['processing_errors'] += 1
            
            # Mark job as error for manual review
            self.db.update_job(job_id, {
                'status': 'error',
                'processing_notes': f"Processing error: {str(e)}"
            })
    
    async def _run_ai_analysis(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run AI analysis on a job."""
        if not self.ai_analyzer:
            return None
            
        try:
            # Create job text for analysis
            job_text = f"""
            Title: {job.get('title', 'N/A')}
            Company: {job.get('company', 'N/A')}
            Location: {job.get('location', 'N/A')}
            Description: {job.get('description', 'N/A')[:1000]}...
            Keywords: {job.get('keywords', 'N/A')}
            """
            
            analysis = await self.ai_analyzer.analyze_job_async(job_text, job.get('url', ''))
            return analysis
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return None
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        verification_stats = self.verifier.get_verification_stats()
        
        return {
            'processing_stats': self.processing_stats,
            'verification_stats': verification_stats,
            'queue_size': self.job_queue.qsize(),
            'is_running': self.is_running,
            'timestamp': datetime.now().isoformat()
        }
    
    def print_stats_summary(self):
        """Print a summary of processing statistics."""
        stats = self.get_processing_stats()
        
        console.print(Panel.fit(
            f"""[bold blue]Verified Job Processor Statistics[/bold blue]
            
[green]✅ Verified Complete:[/green] {stats['processing_stats']['verified_complete']}
[yellow]🔄 Needs Processing:[/yellow] {stats['processing_stats']['needs_processing']}
[red]❌ Failed Scraping:[/red] {stats['processing_stats']['failed_scraping']}
[blue]🤖 AI Analyzed:[/blue] {stats['processing_stats']['ai_analyzed']}
[red]⚠️ Processing Errors:[/red] {stats['processing_stats']['processing_errors']}

[bold]Verification Success Rate:[/bold] {stats['verification_stats']['success_rate']:.1f}%
[bold]Queue Size:[/bold] {stats['queue_size']}
[bold]Status:[/bold] {'🟢 Running' if stats['is_running'] else '🔴 Stopped'}""",
            title="Processing Summary"
        ))

# Convenience function
def get_verified_job_processor(profile_name: str) -> VerifiedJobProcessor:
    """Get a verified job processor instance."""
    return VerifiedJobProcessor(profile_name)