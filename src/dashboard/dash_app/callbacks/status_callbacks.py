"""
Application Status Callbacks
Handle status dropdown interactions and database updates
"""

import logging
from datetime import datetime
from dash import Input, Output, State, callback, no_update, ALL, MATCH
import dash_bootstrap_components as dbc
from dash import html

from ..services.data_service import DataService
from ..utils.profile_manager import get_profile_manager

logger = logging.getLogger(__name__)


@callback(
    Output({"type": "status-dropdown", "index": MATCH}, "label"),
    Output({"type": "status-dropdown", "index": MATCH}, "color"),
    [Input({"type": "status-option", "status": ALL, "job_id": MATCH}, "n_clicks")],
    [State({"type": "status-dropdown", "index": MATCH}, "id")],
    prevent_initial_call=True,
)
def update_job_status(status_clicks, dropdown_id):
    """
    Update job application status when dropdown option is clicked.

    Args:
        status_clicks: List of clicks for status options
        dropdown_id: ID of the status dropdown

    Returns:
        tuple: Updated label and color for dropdown
    """
    try:
        # Get the clicked status from callback context
        if not any(status_clicks):
            return no_update, no_update

        ctx = callback.callback_context
        if not ctx.triggered:
            return no_update, no_update

        # Parse the triggered input to get status and job_id
        triggered_input = ctx.triggered[0]["prop_id"]
        input_dict = eval(triggered_input.split(".")[0])
        new_status = input_dict["status"]
        job_id = input_dict["job_id"]

        # Update database
        data_service = DataService()
        profile_manager = get_profile_manager()
        current_profile = profile_manager.get_current_profile()

        if not current_profile:
            logger.error("No current profile available for status update")
            return no_update, no_update

        # Update job status in database
        success = data_service.update_job_status(
            profile_name=current_profile,
            job_id=job_id,
            new_status=new_status,
            update_date=datetime.now(),
        )

        if not success:
            logger.error(f"Failed to update status for job {job_id}")
            return no_update, no_update

        # Status options with icons and colors
        status_options = {
            "not_applied": {"label": "🎯 Not Applied", "color": "secondary"},
            "interested": {"label": "💡 Interested", "color": "info"},
            "applied": {"label": "📤 Applied", "color": "success"},
            "interview": {"label": "📞 Interview", "color": "warning"},
            "offer": {"label": "🎉 Offer", "color": "danger"},
            "rejected": {"label": "❌ Rejected", "color": "dark"},
            "withdrawn": {"label": "🚫 Withdrawn", "color": "secondary"},
        }

        status_info = status_options.get(new_status, status_options["not_applied"])

        logger.info(f"Updated job {job_id} status to {new_status}")

        return status_info["label"], status_info["color"]

    except Exception as e:
        logger.error(f"Error updating job status: {str(e)}")
        return no_update, no_update


@callback(
    Output("jobs-table-data", "data"),
    [Input("jobs-status-filter", "value")],
    [State("jobs-table-data", "data")],
    prevent_initial_call=True,
)
def filter_jobs_by_status(selected_status, current_data):
    """
    Filter jobs table based on application status.

    Args:
        selected_status: Selected status filter value
        current_data: Current jobs table data

    Returns:
        list: Filtered jobs data
    """
    try:
        if not current_data or selected_status == "all":
            return current_data

        # Filter jobs by status
        filtered_data = [
            job
            for job in current_data
            if job.get("application_status", "not_applied") == selected_status
        ]

        logger.info(
            f"Filtered jobs by status '{selected_status}': " f"{len(filtered_data)} jobs found"
        )

        return filtered_data

    except Exception as e:
        logger.error(f"Error filtering jobs by status: {str(e)}")
        return current_data or []


@callback(
    [
        Output("total-jobs-metric", "children"),
        Output("applied-jobs-metric", "children"),
        Output("interview-jobs-metric", "children"),
        Output("offer-jobs-metric", "children"),
    ],
    [
        Input("jobs-refresh-btn", "n_clicks"),
        Input({"type": "status-option", "status": ALL, "job_id": ALL}, "n_clicks"),
    ],
    prevent_initial_call=True,
)
def update_status_metrics(refresh_clicks, status_updates):
    """
    Update job status metrics when statuses change.

    Args:
        refresh_clicks: Refresh button clicks
        status_updates: Status dropdown updates

    Returns:
        tuple: Updated metric values
    """
    try:
        data_service = DataService()
        profile_manager = get_profile_manager()
        current_profile = profile_manager.get_current_profile()

        if not current_profile:
            return "0", "0", "0", "0"

        # Get job statistics by status
        stats = data_service.get_job_status_statistics(current_profile)

        total_jobs = stats.get("total", 0)
        applied_jobs = stats.get("applied", 0)
        interview_jobs = stats.get("interview", 0)
        offer_jobs = stats.get("offer", 0)

        return (str(total_jobs), str(applied_jobs), str(interview_jobs), str(offer_jobs))

    except Exception as e:
        logger.error(f"Error updating status metrics: {str(e)}")
        return "0", "0", "0", "0"


@callback(
    Output("application-tracking-alerts", "children"),
    [Input({"type": "status-option", "status": "applied", "job_id": ALL}, "n_clicks")],
    prevent_initial_call=True,
)
def show_application_success_alert(applied_clicks):
    """
    Show success alert when job status is updated to 'applied'.

    Args:
        applied_clicks: Clicks on 'applied' status options

    Returns:
        dbc.Alert: Success notification
    """
    try:
        if not any(applied_clicks):
            return []

        return [
            dbc.Alert(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    (
                        "Application status updated successfully! "
                        "Good luck with your application!"
                    ),
                ],
                color="success",
                dismissable=True,
                duration=4000,
                className="mt-3",
            )
        ]

    except Exception as e:
        logger.error(f"Error showing application alert: {str(e)}")
        return []


# Additional helper function for status tracking
def get_status_statistics(profile_name: str) -> dict:
    """
    Get job application status statistics for dashboard metrics.

    Args:
        profile_name: Profile to get statistics for

    Returns:
        dict: Status statistics
    """
    try:
        data_service = DataService()
        return data_service.get_job_status_statistics(profile_name)
    except Exception as e:
        logger.error(f"Error getting status statistics: {str(e)}")
        return {
            "total": 0,
            "not_applied": 0,
            "interested": 0,
            "applied": 0,
            "interview": 0,
            "offer": 0,
            "rejected": 0,
            "withdrawn": 0,
        }


def register_status_callbacks(app):
    """Register status tracking callbacks with the app"""
    # Callbacks are already registered with @callback decorator
    # This function exists for consistency with other callback modules
    pass
