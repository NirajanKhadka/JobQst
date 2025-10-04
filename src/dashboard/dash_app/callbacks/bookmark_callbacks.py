"""
Bookmark callbacks for JobQst Dashboard
Handle smart bookmarking system interactions
"""

import logging
from dash import Input, Output, no_update, callback_context, State, html, ALL
import pandas as pd

logger = logging.getLogger(__name__)

# Import services
try:
    from ..utils.data_loader import DataLoader  # noqa: F401

    SERVICES_AVAILABLE = True
except ImportError:
    logger.warning("Services not fully available for bookmark callbacks")
    SERVICES_AVAILABLE = False


def get_bookmarked_jobs_data(profile_name: str) -> pd.DataFrame:
    """Get bookmarked jobs data from database"""
    try:
        if not SERVICES_AVAILABLE:
            return pd.DataFrame()

        # Get database instance
        from ...core.job_database import get_job_db

        db = get_job_db(profile_name)

        if hasattr(db, "get_bookmarked_jobs"):
            bookmarked_jobs = db.get_bookmarked_jobs(profile_name)
            return pd.DataFrame(bookmarked_jobs)
        else:
            logger.warning("Bookmark functionality not available in database")
            return pd.DataFrame()

    except Exception as e:
        logger.error(f"Error loading bookmarked jobs: {e}")
        return pd.DataFrame()


def register_bookmark_callbacks(app):
    """Register all bookmark-related callbacks"""

    def get_data_loader():
        """Get DataLoader instance for the app"""
        try:
            from ..utils.data_loader import DataLoader

            return DataLoader()
        except ImportError:
            logger.warning("DataLoader not available")
            return None

    @app.callback(
        Output("bookmarks-grid", "children"),
        [
            Input("bookmark-status-filter", "value"),
            Input("bookmark-search", "value"),
            Input("bookmarks-refresh-btn", "n_clicks"),
        ],
    )
    def update_bookmarks_grid(status_filter, search_term, refresh_clicks):
        """Update the bookmarks grid based on filters"""
        try:
            # Get current profile
            data_loader = get_data_loader()
            if not data_loader:
                return html.Div(
                    [html.P("Data loader not available", className="text-danger text-center mt-4")]
                )

            # Get profile from app instance
            if not hasattr(app, "profile_name") or app.profile_name is None:
                logger.error("No profile set on app instance")
                return []
            
            profile_name = app.profile_name
            if hasattr(data_loader, "get_current_profile"):
                current_profile = data_loader.get_current_profile()
                profile_name = current_profile or profile_name
            if not profile_name:
                return html.Div(
                    [html.P("No profile selected", className="text-muted text-center mt-4")]
                )

            # Load bookmarked jobs
            df = get_bookmarked_jobs_data(profile_name)

            if df.empty:
                return html.Div(
                    [
                        html.Div(
                            [
                                html.I(className="fas fa-bookmark fa-3x " "text-muted mb-3"),
                                html.H5("No bookmarks yet", className="text-muted"),
                                html.P(
                                    "Start bookmarking promising jobs " "to see them here",
                                    className="text-muted small",
                                ),
                            ],
                            className="text-center mt-5",
                        )
                    ]
                )

            # Apply filters
            filtered_df = apply_bookmark_filters(df, status_filter, search_term)

            if filtered_df.empty:
                return html.Div(
                    [
                        html.P(
                            "No bookmarks match your filters",
                            className="text-muted text-center mt-4",
                        )
                    ]
                )

            # Generate bookmark cards
            return create_bookmark_cards(filtered_df)

        except Exception as e:
            logger.error(f"Error updating bookmarks grid: {e}")
            return html.Div(
                [html.P("Error loading bookmarks", className="text-danger text-center mt-4")]
            )

    @app.callback(
        Output({"type": "bookmark-btn", "job_id": ALL}, "children"),
        Output({"type": "bookmark-btn", "job_id": ALL}, "color"),
        [Input({"type": "bookmark-btn", "job_id": ALL}, "n_clicks")],
        [State({"type": "bookmark-btn", "job_id": ALL}, "id")],
    )
    def handle_bookmark_toggle(n_clicks_list, btn_ids):
        """Handle bookmark toggle clicks"""
        try:
            ctx = callback_context
            if not ctx.triggered:
                return no_update, no_update

            # Get current profile
            data_loader = get_data_loader()
            if not data_loader:
                return no_update, no_update

            # Get profile from app instance
            if not hasattr(app, "profile_name") or app.profile_name is None:
                logger.error("No profile set on app instance")
                return []
            
            profile_name = app.profile_name
            if hasattr(data_loader, "get_current_profile"):
                current_profile = data_loader.get_current_profile()
                profile_name = current_profile or profile_name

            # Find which button was clicked
            trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
            clicked_id = eval(trigger_id)
            job_id = clicked_id["job_id"]

            # Get database instance
            from ...core.job_database import get_job_db

            db = get_job_db(profile_name)

            if not hasattr(db, "add_bookmark"):
                logger.warning("Bookmark functionality not available")
                return no_update, no_update

            # Check current bookmark status
            bookmarked_jobs = db.get_bookmarked_jobs(profile_name)
            is_bookmarked = any(job["id"] == job_id for job in bookmarked_jobs)

            # Toggle bookmark status
            if is_bookmarked:
                success = db.remove_bookmark(job_id, profile_name)
            else:
                success = db.add_bookmark(job_id, profile_name)

            if not success:
                logger.error(f"Failed to toggle bookmark for job {job_id}")
                return no_update, no_update

            # Update all button states
            updated_bookmarks = db.get_bookmarked_jobs(profile_name)
            bookmarked_ids = {job["id"] for job in updated_bookmarks}

            icons = []
            colors = []
            for btn_id in btn_ids:
                job_id = btn_id["job_id"]
                if job_id in bookmarked_ids:
                    icons.append("❤️")
                    colors.append("primary")
                else:
                    icons.append("🤍")
                    colors.append("outline-primary")

            return icons, colors

        except Exception as e:
            logger.error(f"Error handling bookmark toggle: {e}")
            return no_update, no_update


def apply_bookmark_filters(df: pd.DataFrame, status_filter: str, search_term: str) -> pd.DataFrame:
    """Apply filters to bookmarked jobs dataframe"""
    filtered_df = df.copy()

    # Status filter
    if status_filter and status_filter != "all":
        filtered_df = filtered_df[filtered_df["application_status"] == status_filter]

    # Search filter
    if search_term:
        mask = (
            filtered_df["title"].str.contains(search_term, case=False, na=False)
            | filtered_df["company"].str.contains(search_term, case=False, na=False)
            | filtered_df["location"].str.contains(search_term, case=False, na=False)
            | filtered_df["bookmark_notes"].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask]

    return filtered_df


def create_bookmark_cards(df: pd.DataFrame) -> list:
    """Create bookmark cards from filtered dataframe"""
    from ..components.job_cards import create_enhanced_job_card
    import dash_bootstrap_components as dbc

    cards = []
    for _, job in df.iterrows():
        # Add bookmark-specific enhancements
        job_dict = job.to_dict()
        job_dict["is_bookmarked"] = True
        job_dict["bookmark_metadata"] = {
            "bookmark_date": job.get("bookmark_date"),
            "notes": job.get("bookmark_notes"),
            "tags": job.get("tags"),
            "priority": job.get("bookmark_priority", 3),
        }

        # Create enhanced card with bookmark info
        card = create_enhanced_job_card(job_dict, show_bookmark_info=True)
        cards.append(dbc.Col(card, width=12, className="mb-3"))

    return cards
