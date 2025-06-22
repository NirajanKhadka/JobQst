#!/usr/bin/env python3
"""
Example usage of the Enhanced Error Tracking and Manual Review System.
This script demonstrates how to integrate the new tracking features into job applications.
"""

import time
from datetime import datetime
from rich.console import Console

# Import the new enhanced tracking modules
from enhanced_status_tracker import EnhancedStatusTracker
from manual_review_manager import ManualReviewManager
from realtime_error_tracker import get_error_tracker, track_error, resolve_error

console = Console()


def example_successful_application():
    """
    Example of tracking a successful job application with detailed logging.
    """
    console.print("\n[bold blue]🎯 Example: Successful Job Application Tracking[/bold blue]")
    
    # Sample job data
    job_data = {
        'id': 12345,
        'title': 'Senior Data Analyst',
        'company': 'TechCorp Inc.',
        'url': 'https://techcorp.com/careers/senior-data-analyst',
        'location': 'Toronto, ON'
    }
    
    # Initialize enhanced status tracker
    tracker = EnhancedStatusTracker("ExampleProfile")
    
    # Start tracking the application
    tracking_id = tracker.start_application_tracking(job_data, "workday")
    console.print(f"[green]✅ Started tracking: {tracking_id}[/green]")
    
    # Simulate application steps
    console.print("[cyan]📝 Simulating application steps...[/cyan]")
    
    # Step 1: Navigate to job posting
    tracker.log_application_step(
        tracking_id, 
        "navigate_to_job", 
        {"url": job_data['url'], "load_time": 2.3}, 
        success=True
    )
    time.sleep(1)
    
    # Step 2: Click apply button
    tracker.log_application_step(
        tracking_id, 
        "click_apply_button", 
        {"button_text": "Apply Now", "redirect_url": "https://techcorp.workday.com/apply"}, 
        success=True
    )
    time.sleep(1)
    
    # Step 3: Fill personal information
    tracker.log_form_interaction(tracking_id, "first_name", "John", "text")
    tracker.log_form_interaction(tracking_id, "last_name", "Doe", "text")
    tracker.log_form_interaction(tracking_id, "email", "john.doe@email.com", "email")
    tracker.log_form_interaction(tracking_id, "phone", "+1-416-555-0123", "tel")
    
    tracker.log_application_step(
        tracking_id, 
        "fill_personal_info", 
        {"fields_filled": 4}, 
        success=True
    )
    time.sleep(1)
    
    # Step 4: Answer screening questions
    tracker.log_screening_question(
        tracking_id,
        "Are you authorized to work in Canada?",
        "Yes",
        "yes_no"
    )
    
    tracker.log_screening_question(
        tracking_id,
        "How many years of experience do you have with Python?",
        "5+ years",
        "multiple_choice"
    )
    
    tracker.log_screening_question(
        tracking_id,
        "What is your expected salary range?",
        "$80,000 - $100,000 CAD",
        "text"
    )
    
    tracker.log_application_step(
        tracking_id, 
        "answer_screening_questions", 
        {"questions_answered": 3}, 
        success=True
    )
    time.sleep(1)
    
    # Step 5: Upload documents
    tracker.logger.log_document_upload("resume", "/path/to/resume.pdf", success=True)
    tracker.logger.log_document_upload("cover_letter", "/path/to/cover_letter.pdf", success=True)
    
    tracker.log_application_step(
        tracking_id, 
        "upload_documents", 
        {"documents_uploaded": 2}, 
        success=True
    )
    time.sleep(1)
    
    # Step 6: Submit application
    tracker.log_application_step(
        tracking_id, 
        "submit_application", 
        {"confirmation_number": "APP-2025-001234"}, 
        success=True
    )
    
    # Finish tracking with success
    result = tracker.finish_application_tracking(
        tracking_id,
        "success",
        "Application submitted successfully with confirmation number APP-2025-001234",
        application_details={
            "confirmation_number": "APP-2025-001234",
            "submission_timestamp": datetime.now().isoformat()
        }
    )
    
    console.print(f"[bold green]🎉 Application completed successfully![/bold green]")
    console.print(f"[green]Duration: {result['application_details']['application_duration']} seconds[/green]")
    console.print(f"[green]Steps completed: {result['application_details']['step_count']}[/green]")


def example_failed_application_with_manual_review():
    """
    Example of tracking a failed job application that requires manual review.
    """
    console.print("\n[bold red]❌ Example: Failed Job Application with Manual Review[/bold red]")
    
    # Sample job data
    job_data = {
        'id': 12346,
        'title': 'Software Engineer',
        'company': 'StartupXYZ',
        'url': 'https://startupxyz.com/careers/software-engineer',
        'location': 'Vancouver, BC'
    }
    
    # Initialize enhanced status tracker
    tracker = EnhancedStatusTracker("ExampleProfile")
    
    # Start real-time error tracking
    error_tracker = get_error_tracker("ExampleProfile")
    error_tracker.start_monitoring()
    
    # Start tracking the application
    tracking_id = tracker.start_application_tracking(job_data, "greenhouse")
    console.print(f"[yellow]⚠️ Started tracking: {tracking_id}[/yellow]")
    
    # Simulate application steps that lead to failure
    console.print("[cyan]📝 Simulating application steps with errors...[/cyan]")
    
    # Step 1: Navigate to job posting (success)
    tracker.log_application_step(
        tracking_id, 
        "navigate_to_job", 
        {"url": job_data['url'], "load_time": 1.8}, 
        success=True
    )
    time.sleep(1)
    
    # Step 2: Click apply button (success)
    tracker.log_application_step(
        tracking_id, 
        "click_apply_button", 
        {"button_text": "Apply", "redirect_url": "https://startupxyz.greenhouse.io/apply"}, 
        success=True
    )
    time.sleep(1)
    
    # Step 3: Fill personal information (success)
    tracker.log_form_interaction(tracking_id, "first_name", "Jane", "text")
    tracker.log_form_interaction(tracking_id, "last_name", "Smith", "text")
    tracker.log_form_interaction(tracking_id, "email", "jane.smith@email.com", "email")
    
    tracker.log_application_step(
        tracking_id, 
        "fill_personal_info", 
        {"fields_filled": 3}, 
        success=True
    )
    time.sleep(1)
    
    # Step 4: Encounter CAPTCHA challenge
    captcha_error_id = f"captcha_{int(time.time())}"
    
    # Track the error in real-time
    track_error(
        error_id=captcha_error_id,
        error_type="captcha",
        error_message="reCAPTCHA challenge detected - requires manual solving",
        context={
            "captcha_type": "reCAPTCHA v2",
            "url": "https://startupxyz.greenhouse.io/apply",
            "step": "form_submission"
        },
        severity="high",
        job_info=job_data
    )
    
    # Log the error in application tracking
    tracker.log_application_error(
        tracking_id,
        "reCAPTCHA challenge detected - requires manual solving",
        "captcha",
        context={
            "captcha_type": "reCAPTCHA v2",
            "url": "https://startupxyz.greenhouse.io/apply",
            "step": "form_submission"
        },
        requires_manual_review=True
    )
    
    # Step 5: Attempt to continue but fail
    tracker.log_application_step(
        tracking_id, 
        "attempt_form_submission", 
        {"error": "CAPTCHA not solved"}, 
        success=False
    )
    
    # Finish tracking with failure
    result = tracker.finish_application_tracking(
        tracking_id,
        "failed",
        "Application failed due to CAPTCHA challenge requiring manual intervention",
        application_details={
            "failure_point": "captcha_verification",
            "retry_count": 1,
            "user_intervention_required": True,
            "intervention_details": "User needs to manually solve reCAPTCHA challenge"
        }
    )
    
    console.print(f"[bold red]❌ Application failed![/bold red]")
    console.print(f"[red]Failure reason: CAPTCHA challenge[/red]")
    console.print(f"[yellow]📋 Added to manual review queue[/yellow]")
    
    # Simulate manual resolution later
    console.print("\n[cyan]🔧 Simulating manual resolution...[/cyan]")
    time.sleep(2)
    
    # Resolve the error
    resolve_error(
        captcha_error_id,
        "CAPTCHA solved manually by user, application resubmitted successfully"
    )
    
    console.print(f"[green]✅ Error {captcha_error_id} resolved![/green]")


def example_manual_review_management():
    """
    Example of managing the manual review queue.
    """
    console.print("\n[bold orange]📋 Example: Manual Review Queue Management[/bold orange]")
    
    # Initialize manual review manager
    manager = ManualReviewManager("ExampleProfile")
    
    # Display current review queue
    console.print("[cyan]Current manual review queue:[/cyan]")
    manager.display_review_queue("pending")
    
    # Get review statistics
    stats = manager.get_review_statistics()
    console.print(f"\n[blue]📊 Review Queue Statistics:[/blue]")
    console.print(f"[blue]Total items: {stats['total']}[/blue]")
    console.print(f"[blue]By status: {stats['by_status']}[/blue]")
    console.print(f"[blue]By type: {stats['by_type']}[/blue]")
    console.print(f"[blue]By priority: {stats['by_priority']}[/blue]")


def example_realtime_error_monitoring():
    """
    Example of real-time error monitoring and statistics.
    """
    console.print("\n[bold purple]🔍 Example: Real-time Error Monitoring[/bold purple]")
    
    # Get error tracker
    error_tracker = get_error_tracker("ExampleProfile")
    
    # Get error statistics
    stats = error_tracker.get_error_statistics()
    
    console.print(f"[purple]📊 Error Statistics:[/purple]")
    console.print(f"[purple]Total active errors: {stats['total_active']}[/purple]")
    console.print(f"[purple]By severity: {stats['by_severity']}[/purple]")
    console.print(f"[purple]By type: {stats['by_type']}[/purple]")
    console.print(f"[purple]Monitoring status: {stats['monitoring_status']}[/purple]")
    
    # Get active errors
    active_errors = error_tracker.get_active_errors()
    
    if active_errors:
        console.print(f"\n[purple]🚨 Active Errors ({len(active_errors)}):[/purple]")
        for error in active_errors[:5]:  # Show first 5
            console.print(f"[red]• {error['type']}: {error['message'][:50]}...[/red]")
            console.print(f"  [dim]Count: {error['count']}, Severity: {error['severity']}[/dim]")
    else:
        console.print("[green]✅ No active errors![/green]")


def main():
    """
    Main function to run all examples.
    """
    console.print("[bold blue]🚀 Enhanced Error Tracking System Examples[/bold blue]")
    console.print("[dim]This script demonstrates the new enhanced tracking features[/dim]")
    
    try:
        # Run examples
        example_successful_application()
        example_failed_application_with_manual_review()
        example_manual_review_management()
        example_realtime_error_monitoring()
        
        console.print("\n[bold green]🎉 All examples completed successfully![/bold green]")
        console.print("[cyan]Check your dashboard to see the tracked applications and errors.[/cyan]")
        
    except Exception as e:
        console.print(f"[red]❌ Error running examples: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


if __name__ == "__main__":
    main()
