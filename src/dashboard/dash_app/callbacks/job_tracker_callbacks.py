"""
Job Tracker Callbacks - Enhanced job application tracking
Handles Kanban board, notes, interviews, and status updates
"""

import sys
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

import dash
from dash import html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

try:
    from src.core.user_profile_manager import UserProfileManager
    from src.core.duckdb_database import DuckDBJobDatabase
    from src.dashboard.dash_app.layouts.job_tracker_layout import create_job_card
except ImportError as e:
    logger.warning(f"Import warning in job tracker callbacks: {e}")


def register_job_tracker_callbacks(app, profile_name: str = None):
    """Register all job tracker related callbacks
    
    Args:
        app: Dash app instance
        profile_name: Current user profile name
    """

    @app.callback(
        [
            Output("total-applications-stat", "children"),
            Output("active-interviews-stat", "children"),
            Output("pending-responses-stat", "children"),
            Output("success-rate-stat", "children"),
            Output("deadline-tracker-container", "children")
        ],
        [
            Input("dashboard-interval", "n_intervals"),
            Input("tracker-refresh-btn", "n_clicks")
        ],
        prevent_initial_call=False,
    )
    def update_tracker_stats(n_intervals, refresh_clicks):
        """Update job tracker statistics"""
        try:
            # Get current profile
            current_profile = profile_name or (app.profile_name if hasattr(app, "profile_name") else None)
            
            if not current_profile:
                logger.error("No profile set")
                return "--", "--", "--", "--", html.Div("Error: No profile configured")

            # Get database
            db = DuckDBJobDatabase(profile_name=current_profile)

            # Get basic stats
            total_query = "SELECT COUNT(*) as count FROM jobs"
            total_df = db.conn.execute(total_query).df()
            total_applications = total_df["count"].iloc[0] if not total_df.empty else 0

            # Get applications with actual application_date
            applied_query = """
                SELECT COUNT(*) as count FROM jobs 
                WHERE application_status IN ('applied', 'interviewing', 'offer')
            """
            applied_df = db.conn.execute(applied_query).df()
            applications = applied_df["count"].iloc[0] if not applied_df.empty else 0

            # Get interviews
            interview_query = """
                SELECT COUNT(*) as count FROM jobs 
                WHERE application_status = 'interviewing'
            """
            interview_df = db.conn.execute(interview_query).df()
            interviews = interview_df["count"].iloc[0] if not interview_df.empty else 0

            # Get pending responses (applied but no response)
            pending_query = """
                SELECT COUNT(*) as count FROM jobs 
                WHERE application_status = 'applied' 
                AND response_date IS NULL
            """
            pending_df = db.conn.execute(pending_query).df()
            pending = pending_df["count"].iloc[0] if not pending_df.empty else 0

            # Calculate success rate
            success_rate = 0
            if applications > 0:
                success_query = """
                    SELECT COUNT(*) as count FROM jobs 
                    WHERE application_status IN ('offer', 'accepted')
                """
                success_df = db.conn.execute(success_query).df()
                success_count = success_df["count"].iloc[0] if not success_df.empty else 0
                success_rate = round((success_count / applications) * 100, 1)

            # Get upcoming deadlines for deadline tracker
            deadline_query = """
                SELECT id, title, company, application_status, 
                       interview_date, response_deadline, application_date
                FROM jobs 
                WHERE (interview_date IS NOT NULL OR response_deadline IS NOT NULL)
                  AND application_status NOT IN ('closed', 'rejected')
                ORDER BY COALESCE(interview_date, response_deadline) ASC
                LIMIT 10
            """
            
            try:
                deadline_df = db.conn.execute(deadline_query).df()
                deadlines = []
                
                for _, row in deadline_df.iterrows():
                    deadline_date = row.get('interview_date') or row.get('response_deadline')
                    if pd.notna(deadline_date):
                        deadlines.append({
                            'job_title': row['title'],
                            'company': row['company'],
                            'deadline': deadline_date,
                            'type': 'interview' if pd.notna(row.get('interview_date')) else 'response',
                            'status': row['application_status']
                        })
                
                # Create deadline tracker component
                from src.dashboard.dash_app.components.application_pipeline import create_deadline_tracker
                deadline_tracker = create_deadline_tracker(deadlines)
                
            except Exception as e:
                logger.error(f"Error loading deadlines: {e}")
                deadline_tracker = html.Div()

            return str(applications), str(interviews), str(pending), f"{success_rate}%", deadline_tracker

        except Exception as e:
            logger.error(f"Error updating tracker stats: {e}")
            return "0", "0", "0", "0%", html.Div()

    @app.callback(
        [
            Output(f"pipeline-column-{status}", "children")
            for status in ["interested", "applied", "interview", "offer", "rejected"]
        ],
        [
            Input("job-tracker-data", "data"),
            Input("tracker-refresh-btn", "n_clicks")
        ],
        prevent_initial_call=False,
    )
    def update_pipeline_columns(tracker_data, refresh_clicks):
        """Update application pipeline columns with enhanced cards"""
        try:
            # Get current profile
            current_profile = profile_name or (app.profile_name if hasattr(app, "profile_name") else None)
            
            if not current_profile:
                logger.error("No profile set")
                return [[] for _ in range(5)]
            db = DuckDBJobDatabase(profile_name=current_profile)

            # Map pipeline statuses to database statuses
            status_map = {
                "interested": ["discovered", "interested"],
                "applied": ["applied"],
                "interview": ["interviewing"],
                "offer": ["offer"],
                "rejected": ["closed", "rejected"]
            }
            
            columns = []

            for pipeline_status, db_statuses in status_map.items():
                status_list = "', '".join(db_statuses)
                query = f"""
                    SELECT id, title, company, location, salary_range, 
                           date_posted, application_status, application_date,
                           fit_score, notes
                    FROM jobs 
                    WHERE application_status IN ('{status_list}')
                    ORDER BY application_date DESC NULLS LAST, date_posted DESC
                    LIMIT 10
                """

                try:
                    df = db.conn.execute(query).df()
                    
                    # Import application card component
                    from src.dashboard.dash_app.components.application_pipeline import create_application_card
                    
                    cards = []
                    for _, job in df.iterrows():
                        application_data = {
                            "job_id": job["id"],
                            "job_title": job["title"],
                            "company": job["company"],
                            "location": job["location"],
                            "salary_range": job.get("salary_range"),
                            "applied_date": job.get("application_date"),
                            "match_score": job.get("fit_score"),
                            "notes": job.get("notes", "")[:100] if pd.notna(job.get("notes")) else "",
                            "status": pipeline_status
                        }
                        cards.append(create_application_card(application_data))

                    columns.append(cards if cards else [
                        html.Div(
                            html.P("No applications", className="text-muted text-center small py-3"),
                            className="empty-column"
                        )
                    ])

                except Exception as e:
                    logger.error(f"Error loading {pipeline_status} jobs: {e}")
                    columns.append([html.Div(
                        html.P("Error loading", className="text-danger text-center small py-3")
                    )])

            return columns

        except Exception as e:
            logger.error(f"Error updating pipeline columns: {e}")
            return [[] for _ in range(5)]

    @app.callback(
        Output("activity-timeline", "children"),
        [Input("dashboard-interval", "n_intervals")],
        prevent_initial_call=False,
    )
    def update_activity_timeline(n_intervals):
        """Update recent activity timeline"""
        try:
            # Get current profile
            current_profile = profile_name or (app.profile_name if hasattr(app, "profile_name") else None)
            
            if not current_profile:
                logger.error("No profile set")
                return []
            db = DuckDBJobDatabase(profile_name=current_profile)

            # Get recent activities (last 10)
            query = """
                SELECT title, company, application_status, 
                       application_date, last_updated, response_date
                FROM jobs 
                WHERE application_date IS NOT NULL 
                   OR response_date IS NOT NULL
                ORDER BY COALESCE(response_date, application_date, last_updated) DESC
                LIMIT 10
            """

            df = db.conn.execute(query).df()

            if df.empty:
                return [html.P("No recent activity", className="text-muted text-center py-4")]

            timeline_items = []
            for _, activity in df.iterrows():
                # Determine activity type and date
                if pd.notna(activity["response_date"]):
                    activity_type = "Response received"
                    activity_date = activity["response_date"]
                    icon = "fas fa-reply"
                    color = "success"
                elif pd.notna(activity["application_date"]):
                    activity_type = "Applied"
                    activity_date = activity["application_date"]
                    icon = "fas fa-paper-plane"
                    color = "primary"
                else:
                    activity_type = "Updated"
                    activity_date = activity["last_updated"]
                    icon = "fas fa-edit"
                    color = "info"

                timeline_item = dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [html.I(className=f"{icon} fa-lg text-{color}")],
                                            width=2,
                                            className="d-flex align-items-center",
                                        ),
                                        dbc.Col(
                                            [
                                                html.H6(
                                                    f"{activity_type}: {activity['title']}",
                                                    className="mb-1",
                                                ),
                                                html.P(
                                                    f"at {activity['company']}",
                                                    className="text-muted small mb-1",
                                                ),
                                                html.Small(
                                                    str(activity_date), className="text-muted"
                                                ),
                                            ],
                                            width=10,
                                        ),
                                    ]
                                )
                            ]
                        )
                    ],
                    className="mb-2 border-0 shadow-sm",
                )

                timeline_items.append(timeline_item)

            return timeline_items

        except Exception as e:
            logger.error(f"Error updating activity timeline: {e}")
            return [html.P("Error loading activity", className="text-danger text-center py-4")]

    @app.callback(
        Output("job-details-modal", "is_open"),
        [
            Input({"type": "job-card", "job_id": dash.dependencies.ALL}, "n_clicks"),
            Input("close-job-modal", "n_clicks"),
        ],
        [State("job-details-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_job_modal(job_card_clicks, close_clicks, is_open):
        """Toggle job details modal"""
        ctx = callback_context

        if not ctx.triggered:
            return False

        trigger_id = ctx.triggered[0]["prop_id"]

        if "job-card" in trigger_id and any(job_card_clicks):
            return True
        elif "close-job-modal" in trigger_id:
            return False

        return is_open

    @app.callback(
        Output("filters-collapse", "is_open"),
        [Input("filter-toggle-btn", "n_clicks")],
        [State("filters-collapse", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_filters(n_clicks, is_open):
        """Toggle filters sidebar"""
        if n_clicks:
            return not is_open
        return is_open
