"""
Scraping callbacks for JobLens Dashboard
Handle job scraping interactions and status updates
"""
import logging
import threading
from datetime import datetime
from dash import Input, Output, State, no_update, callback_context

logger = logging.getLogger(__name__)


def register_scraping_callbacks(app):
    """Register all scraping-related callbacks"""
    
    @app.callback(
        [Output('scraping-logs', 'value'),
         Output('jobs-found-count', 'children'),
         Output('last-scrape-status', 'children'),
         Output('active-scrapers', 'children')],
        [Input('start-jobspy-pipeline-btn', 'n_clicks'),
         Input('quick-scrape-btn', 'n_clicks'),
         Input('start-custom-scrape-btn', 'n_clicks'),
         Input('refresh-scrape-status-btn', 'n_clicks')],
        [State('profile-store', 'data'),
         State('scrape-keywords', 'value'),
         State('scrape-sites', 'value'),
         State('scrape-country', 'value'),
         State('max-jobs-per-site', 'value'),
         State('scrape-location', 'value'),
         State('scraping-options', 'value')],
        prevent_initial_call=True
    )
    def handle_scraping_actions(jobspy_clicks, quick_clicks, custom_clicks,
                                refresh_clicks, profile_data, keywords,
                                sites, country, max_jobs, location, options):
        """Handle scraping button clicks and status updates"""
        
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        try:
            profile_name = (profile_data.get('selected_profile')
                            if profile_data else 'Nirajan')
            
            if button_id == 'start-jobspy-pipeline-btn':
                return start_jobspy_pipeline(profile_name)
            
            elif button_id == 'quick-scrape-btn':
                return start_quick_scrape(profile_name)
            
            elif button_id == 'start-custom-scrape-btn':
                return start_custom_scrape(
                    profile_name, keywords, sites, country,
                    max_jobs, location, options
                )
            
            elif button_id == 'refresh-scrape-status-btn':
                return refresh_scraping_status(profile_name)
            
        except Exception as e:
            error_msg = f"Error in scraping action: {str(e)}"
            logger.error(error_msg)
            return error_msg, "Error", "Error", "0"
        
        return no_update, no_update, no_update, no_update


def start_jobspy_pipeline(profile_name):
    """Start the JobSpy pipeline with default settings"""
    try:
        log_message = (f"Starting JobSpy pipeline for {profile_name}...\n"
                       f"Using comprehensive USA preset\n"
                       f"Sites: Indeed, LinkedIn, Glassdoor, ZipRecruiter\n"
                       f"Status: Initializing scrapers...")
        
        # Start the scraping in a background thread
        threading.Thread(
            target=run_jobspy_pipeline,
            args=(profile_name,),
            daemon=True
        ).start()
        
        current_time = datetime.now().strftime("%H:%M:%S")
        
        return (log_message, "Starting...", current_time, "4")
        
    except Exception as e:
        error_msg = f"Failed to start JobSpy pipeline: {str(e)}"
        logger.error(error_msg)
        return (error_msg, "Error", "Error", "0")


def start_quick_scrape(profile_name):
    """Start a quick scrape with minimal settings"""
    try:
        log_message = (f"Starting quick scrape for {profile_name}...\n"
                       f"Using default keywords and settings\n"
                       f"Sites: Indeed only (fast mode)\n"
                       f"Max jobs: 25 per keyword\n"
                       f"Status: Launching scraper...")
        
        # Start quick scraping in background
        threading.Thread(
            target=run_quick_scrape,
            args=(profile_name,),
            daemon=True
        ).start()
        
        current_time = datetime.now().strftime("%H:%M:%S")
        
        return (log_message, "Starting...", current_time, "1")
        
    except Exception as e:
        error_msg = f"Failed to start quick scrape: {str(e)}"
        logger.error(error_msg)
        return (error_msg, "Error", "Error", "0")


def start_custom_scrape(profile_name, keywords, sites, country,
                        max_jobs, location, options):
    """Start custom scraping with user-specified settings"""
    try:
        sites_list = sites if sites else ['indeed']
        keywords_list = [k.strip() for k in keywords.split(',')
                         if k.strip()] if keywords else ['python']
        
        options_str = ', '.join(options) if options else 'None'
        log_message = (f"Starting custom scrape for {profile_name}...\n"
                       f"Keywords: {', '.join(keywords_list)}\n"
                       f"Sites: {', '.join(sites_list)}\n"
                       f"Country: {country}\n"
                       f"Location: {location}\n"
                       f"Max jobs per site: {max_jobs}\n"
                       f"Options: {options_str}\n"
                       f"Status: Configuring scrapers...")
        
        # Start custom scraping in background
        threading.Thread(
            target=run_custom_scrape,
            args=(profile_name, keywords_list, sites_list, country,
                  max_jobs, location, options),
            daemon=True
        ).start()
        
        current_time = datetime.now().strftime("%H:%M:%S")
        
        return (log_message, "Starting...", current_time, str(len(sites_list)))
        
    except Exception as e:
        error_msg = f"Failed to start custom scrape: {str(e)}"
        logger.error(error_msg)
        return (error_msg, "Error", "Error", "0")


def refresh_scraping_status(profile_name):
    """Refresh the current scraping status"""
    try:
        # Get current status from the system
        log_message = f"Refreshing status for {profile_name}...\n"
        
        # Try to get real status from the scraping system
        try:
            from src.core.job_database import get_job_db
            db = get_job_db(profile_name)
            recent_jobs = db.get_jobs(limit=10)
            
            if recent_jobs:
                latest_job = recent_jobs[0]
                scraped_time = latest_job.get('scraped_at', 'Unknown')
                jobs_count = len(recent_jobs)
                
                log_message += (f"Last successful scrape: {scraped_time}\n"
                                f"Recent jobs found: {jobs_count}\n"
                                f"Database status: Connected\n"
                                f"Ready for new scraping...")
                
                return (log_message, str(jobs_count), scraped_time, "0")
            else:
                log_message += ("No recent jobs found\n"
                                "Database status: Connected but empty\n"
                                "Ready for scraping...")
                return (log_message, "0", "Never", "0")
                
        except Exception as db_error:
            log_message += (f"Database connection error: {str(db_error)}\n"
                            "Status: Offline")
            return (log_message, "Error", "Error", "0")
        
    except Exception as e:
        error_msg = f"Failed to refresh status: {str(e)}"
        logger.error(error_msg)
        return (error_msg, "Error", "Error", "0")


# Background scraping functions

def run_jobspy_pipeline(profile_name):
    """Run the JobSpy pipeline in background"""
    try:
        import subprocess
        import sys
        
        # Get the project root directory
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent.parent.parent
        main_py = project_root / "main.py"
        
        # Run the JobSpy pipeline command
        cmd = [
            sys.executable, str(main_py), profile_name,
            "--action", "jobspy-pipeline",
            "--jobspy-preset", "usa_comprehensive",
            "--sites", "indeed,linkedin,glassdoor,zip_recruiter"
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )
        
        if result.returncode == 0:
            logger.info(f"JobSpy pipeline completed successfully "
                       f"for {profile_name}")
            
            # Auto-process the scraped jobs using the modern two-stage processor
            logger.info("Starting auto-processing with two-stage processor...")
            process_cmd = [
                sys.executable, str(main_py), profile_name,
                "--action", "analyze-jobs"
            ]
            
            try:
                process_result = subprocess.run(
                    process_cmd,
                    cwd=str(project_root),
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
                
                if process_result.returncode == 0:
                    logger.info(f"Auto-processing completed successfully for {profile_name}")
                else:
                    logger.error(f"Auto-processing failed: {process_result.stderr}")
                    
            except Exception as proc_e:
                logger.error(f"Error during auto-processing: {str(proc_e)}")
                
        else:
            logger.error(f"JobSpy pipeline failed for {profile_name}: "
                        f"{result.stderr}")
            
    except Exception as e:
        logger.error(f"Error running JobSpy pipeline: {str(e)}")


def run_quick_scrape(profile_name):
    """Run a quick scrape in background"""
    try:
        import subprocess
        import sys
        
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent.parent.parent
        main_py = project_root / "main.py"
        
        cmd = [
            sys.executable, str(main_py), profile_name,
            "--action", "scrape",
            "--keywords", "python,software engineer",
            "--max-jobs", "25"
        ]
        
        logger.info(f"Running quick scrape: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            logger.info(f"Quick scrape completed for {profile_name}")
            
            # Auto-process the scraped jobs
            logger.info("Starting auto-processing after quick scrape...")
            process_cmd = [
                sys.executable, str(main_py), profile_name,
                "--action", "analyze-jobs"
            ]
            
            try:
                process_result = subprocess.run(
                    process_cmd,
                    cwd=str(project_root),
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if process_result.returncode == 0:
                    logger.info(f"Quick scrape auto-processing completed for {profile_name}")
                else:
                    logger.error(f"Quick scrape auto-processing failed: {process_result.stderr}")
                    
            except Exception as proc_e:
                logger.error(f"Error during quick scrape auto-processing: {str(proc_e)}")
                
        else:
            logger.error(f"Quick scrape failed for {profile_name}: "
                        f"{result.stderr}")
            
    except Exception as e:
        logger.error(f"Error running quick scrape: {str(e)}")


def run_custom_scrape(profile_name, keywords, sites, country,
                     max_jobs, location, options):
    """Run custom scraping in background"""
    try:
        import subprocess
        import sys
        
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent.parent.parent
        main_py = project_root / "main.py"
        
        # Build command based on parameters
        cmd = [
            sys.executable, str(main_py), profile_name,
            "--action", "scrape",
            "--keywords", ",".join(keywords),
            "--max-jobs", str(max_jobs)
        ]
        
        if location:
            cmd.extend(["--location", location])
        
        logger.info(f"Running custom scrape: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )
        
        if result.returncode == 0:
            logger.info(f"Custom scrape completed for {profile_name}")
            
            # Auto-process if option is enabled
            if options and 'auto_process' in options:
                logger.info("Starting auto-processing...")
                process_cmd = [
                    sys.executable, str(main_py), profile_name,
                    "--action", "analyze-jobs"
                ]
                
                subprocess.run(
                    process_cmd,
                    cwd=str(project_root),
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
        else:
            logger.error(f"Custom scrape failed for {profile_name}: "
                        f"{result.stderr}")
            
    except Exception as e:
        logger.error(f"Error running custom scrape: {str(e)}")
