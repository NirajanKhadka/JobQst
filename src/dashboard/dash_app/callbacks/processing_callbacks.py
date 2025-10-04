"""
Processing callbacks for JobQst Dashboard
Handle job processing controls and monitoring
"""

import logging
import sys
from pathlib import Path
from dash import Input, Output, State, callback_context, no_update
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# Global processing state
_processing_state = {
    "is_running": False,
    "jobs_processed": 0,
    "jobs_total": 0,
    "current_job": "",
    "errors": 0,
    "log_messages": [],
}


def register_processing_callbacks(app):
    """Register all processing-related callbacks"""

    @app.callback(
        Output("processing-quick-log-store", "data"),
        Input("quick-process", "n_clicks"),
        State("profile-store", "data"),
        prevent_initial_call=True,
    )
    def quick_process(start_clicks, profile_data):
        """Trigger analyze-jobs run and stash output in store."""
        if not start_clicks:
            return no_update
        # Get profile from profile_data or app instance
        if profile_data and profile_data.get("selected_profile"):
            profile_name = profile_data.get("selected_profile")
        elif hasattr(app, "profile_name") and app.profile_name:
            profile_name = app.profile_name
        else:
            logger.error("No profile available for processing")
            return html.Div("Error: No profile configured", className="text-danger")
        try:
            import subprocess
            import sys as _sys
            from pathlib import Path

            project_root = Path(__file__).parent.parent.parent.parent.parent
            main_py = project_root / "main.py"
            cmd = [_sys.executable, str(main_py), profile_name, "--action", "analyze-jobs"]
            result = subprocess.run(
                cmd, cwd=str(project_root), capture_output=True, text=True, timeout=1800
            )
            if result.returncode == 0:
                return {
                    "message": (
                        f"Processing complete for {profile_name}.\n"
                        f"Output:\n{result.stdout[-1000:]}"
                    )
                }
            return {
                "message": (
                    f"Processing failed (code {result.returncode}).\n"
                    f"Error:\n{result.stderr[-1000:]}"
                )
            }
        except Exception as e:
            logger.error(f"Quick process error: {e}")
            return {"message": f"Quick process failed: {e}"}

    @app.callback(
        [
            Output("queue-status", "children"),
            Output("processing-status", "children"),
            Output("completed-count", "children"),
            Output("error-count", "children"),
        ],
        Input("auto-refresh-interval", "n_intervals"),
    )
    def update_processing_status(n_intervals):
        """Update processing status indicators"""
        try:
            # Check actual processing status from database and system
            from src.core.job_database import get_job_db

            # Use current profile from global state or default
            # Get profile from app instance
            if not hasattr(app, "profile_name") or app.profile_name is None:
                logger.error("No profile set on app instance")
                return {"status": "error", "message": "No profile configured"}
            
            profile_name = app.profile_name

            db = get_job_db(profile_name)
            _ = db.get_job_count()

            is_running = _processing_state["is_running"]
            queue_status = "Ready" if not is_running else "Processing"
            processing_status = "Running" if is_running else "Idle"
            completed_count = str(_processing_state["jobs_processed"])
            error_count = str(_processing_state["errors"])

            return (queue_status, processing_status, completed_count, error_count)

        except Exception as e:
            logger.error(f"Error updating processing status: {e}")
            return "Error", "Error", "Error", "Error"

    @app.callback(
        [
            Output("overall-progress", "value"),
            Output("batch-progress", "value"),
            Output("processing-log", "children"),
        ],
        [
            Input("start-processing-btn", "n_clicks"),
            Input("pause-processing-btn", "n_clicks"),
            Input("stop-processing-btn", "n_clicks"),
            Input("auto-refresh-interval", "n_intervals"),
        ],
        [
            State("processing-method", "value"),
            State("batch-size", "value"),
            State("max-jobs", "value"),
            State("processing-options", "value"),
            State("processing-quick-log-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def handle_processing_actions(
        start_clicks,
        pause_clicks,
        stop_clicks,
        n_intervals,
        method,
        batch_size,
        max_jobs,
        options,
        quick_log_store,
    ):
        """Handle processing start/pause/stop actions"""
        try:
            ctx = callback_context
            if not ctx.triggered:
                return 0, 0, "Processing system ready..."

            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

            if button_id == "start-processing-btn" and start_clicks:
                # Start actual processing
                return _start_processing(method, batch_size, max_jobs, options)

            elif button_id == "pause-processing-btn" and pause_clicks:
                return _pause_processing()

            elif button_id == "stop-processing-btn" and stop_clicks:
                return _stop_processing()

            # Auto-refresh - update current progress
            if _processing_state["is_running"]:
                progress = 0
                if _processing_state["jobs_total"] > 0:
                    progress = int(
                        (_processing_state["jobs_processed"] / _processing_state["jobs_total"])
                        * 100
                    )

                log_messages = _processing_state["log_messages"][-10:]
                # Include quick process latest message if present
                if quick_log_store and quick_log_store.get("message"):
                    log_messages.append(quick_log_store["message"])
                combined = "\n".join(log_messages)
                return progress, 50, combined

            base_msg = "Processing system ready..."
            if quick_log_store and quick_log_store.get("message"):
                base_msg += "\n" + quick_log_store["message"]
            return 0, 0, base_msg

        except Exception as e:
            logger.error(f"Error handling processing actions: {e}")
            return 0, 0, f"Error: {str(e)}"

    @app.callback(Output("processing-method", "value"), Input("profile-selector", "value"))
    def update_default_processing_method(profile):
        """Update default processing method based on profile"""
        try:
            # Load profile-specific settings
            return "two_stage"
        except Exception as e:
            logger.error(f"Error updating processing method: {e}")
            return "two_stage"


def _start_processing(method, batch_size, max_jobs, options):
    """Start the job processing pipeline"""
    try:
        _processing_state["is_running"] = True
        _processing_state["jobs_processed"] = 0
        _processing_state["errors"] = 0
        _processing_state["log_messages"] = []

        log_message = f"""Processing started with settings:
- Method: {method}
- Batch Size: {batch_size}
- Max Jobs: {max_jobs}
- Options: {', '.join(options) if options else 'None'}
- Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}

Initializing job processor...
Loading job queue...
Starting analysis pipeline..."""

        _processing_state["log_messages"].append(log_message)

        # Start processing in background (simplified for UI demo)
        # In production, this would be a background task
        _processing_state["jobs_total"] = max_jobs or 100

        return 10, 0, log_message

    except Exception as e:
        logger.error(f"Error starting processing: {e}")
        _processing_state["is_running"] = False
        return 0, 0, f"Failed to start processing: {str(e)}"


def _pause_processing():
    """Pause the processing pipeline"""
    _processing_state["is_running"] = False
    log_message = f"Processing paused at {time.strftime('%H:%M:%S')}"
    _processing_state["log_messages"].append(log_message)

    current_progress = 0
    if _processing_state["jobs_total"] > 0:
        current_progress = int(
            (_processing_state["jobs_processed"] / _processing_state["jobs_total"]) * 100
        )

    return current_progress, 50, log_message


def _stop_processing():
    """Stop the processing pipeline"""
    _processing_state["is_running"] = False
    _processing_state["jobs_processed"] = 0
    _processing_state["jobs_total"] = 0

    log_message = f"Processing stopped at {time.strftime('%H:%M:%S')}"
    _processing_state["log_messages"] = [log_message]

    return 0, 0, log_message
