"""
Keyword Cloud Callbacks
Handle keyword filtering interactions
"""

import logging
from dash import Input, Output, State, no_update, ALL, ctx
import dash_bootstrap_components as dbc
from dash import html

logger = logging.getLogger(__name__)


def register_keyword_cloud_callbacks(app):
    """Register all keyword cloud related callbacks."""

    @app.callback(
        [
            Output("selected-keywords-store", "data"),
            Output("keyword-filter-summary", "children"),
            Output("keyword-filter-alert", "style"),
        ],
        [
            Input({"type": "keyword-filter-badge", "keyword": ALL}, "n_clicks"),
            Input("clear-keyword-filters-btn", "n_clicks"),
        ],
        [State("selected-keywords-store", "data")],
    )
    def handle_keyword_filtering(badge_clicks, clear_clicks, selected_keywords):
        """Handle keyword badge clicks and clear button."""
        try:
            if not ctx.triggered:
                return no_update, no_update, no_update

            # Get the current selected keywords
            if selected_keywords is None:
                selected_keywords = []

            # Check which component triggered the callback
            trigger_id = ctx.triggered[0]["prop_id"]

            if "clear-keyword-filters-btn" in trigger_id:
                # Clear all filters
                return [], "", {"display": "none"}

            elif "keyword-filter-badge" in trigger_id:
                # Parse the clicked keyword from the trigger
                if badge_clicks and any(badge_clicks):
                    # Find which badge was clicked
                    for i, clicks in enumerate(badge_clicks):
                        if clicks:
                            # Extract keyword from pattern matching
                            # This is simplified - in practice, you'd need
                            # to parse the trigger_id more carefully
                            break

                    # For now, let's extract from the trigger_id string
                    import json

                    trigger_dict = json.loads(trigger_id.split(".")[0].replace("'", '"'))
                    clicked_keyword = trigger_dict["keyword"]

                    # Toggle keyword selection
                    if clicked_keyword in selected_keywords:
                        selected_keywords.remove(clicked_keyword)
                    else:
                        selected_keywords.append(clicked_keyword)

                    # Update summary
                    if selected_keywords:
                        summary = html.Div(
                            [
                                html.Strong(f"Filtering by {len(selected_keywords)} " f"skills: "),
                                html.Span(", ".join(selected_keywords)),
                            ]
                        )
                        alert_style = {"display": "block"}
                    else:
                        summary = ""
                        alert_style = {"display": "none"}

                    return selected_keywords, summary, alert_style

            return no_update, no_update, no_update

        except Exception as e:
            logger.error(f"Error in keyword filtering: {str(e)}")
            return selected_keywords or [], "", {"display": "none"}

    @app.callback(
        Output("selected-keywords-display", "children"), [Input("selected-keywords-store", "data")]
    )
    def update_selected_keywords_display(selected_keywords):
        """Update the display of selected keywords."""
        try:
            if not selected_keywords:
                return ""

            # Create badges for selected keywords
            keyword_badges = []
            for keyword in selected_keywords:
                badge = dbc.Badge(
                    [
                        keyword,
                        html.Button(
                            "×",
                            className="btn-close btn-close-white ms-1",
                            style={"fontSize": "0.7rem"},
                            id={"type": "remove-keyword", "keyword": keyword},
                        ),
                    ],
                    color="success",
                    className="me-2 mb-2 selected-keyword-badge",
                    style={"fontSize": "0.9rem", "padding": "0.5rem 0.7rem"},
                )
                keyword_badges.append(badge)

            return html.Div(
                [
                    html.Small("Active filters:", className="text-muted me-2"),
                    html.Div(keyword_badges, className="d-inline"),
                ]
            )

        except Exception as e:
            logger.error(f"Error updating selected keywords display: {str(e)}")
            return ""

    @app.callback(
        Output("selected-keywords-store", "data", allow_duplicate=True),
        [Input({"type": "remove-keyword", "keyword": ALL}, "n_clicks")],
        [State("selected-keywords-store", "data")],
        prevent_initial_call=True,
    )
    def remove_keyword_filter(remove_clicks, selected_keywords):
        """Remove individual keyword from filters."""
        try:
            if not ctx.triggered or not any(remove_clicks or []):
                return no_update

            # Find which remove button was clicked
            trigger_id = ctx.triggered[0]["prop_id"]
            import json

            trigger_dict = json.loads(trigger_id.split(".")[0].replace("'", '"'))
            keyword_to_remove = trigger_dict["keyword"]

            # Remove the keyword
            if selected_keywords and keyword_to_remove in selected_keywords:
                selected_keywords.remove(keyword_to_remove)

            return selected_keywords or []

        except Exception as e:
            logger.error(f"Error removing keyword filter: {str(e)}")
            return selected_keywords or []

    # Add callback to update keyword cloud based on job data
    @app.callback(Output("keyword-cloud-panel", "children"), [Input("jobs-table-data", "data")])
    def update_keyword_cloud(jobs_data):
        """Update keyword cloud when job data changes."""
        try:
            from ..components.keyword_cloud import create_keyword_cloud_panel

            if not jobs_data:
                jobs_data = []

            return create_keyword_cloud_panel(jobs_data)

        except Exception as e:
            logger.error(f"Error updating keyword cloud: {str(e)}")
            return html.Div("Error loading keyword cloud")

    # Filter jobs table based on selected keywords
    @app.callback(
        Output("jobs-table-data", "data", allow_duplicate=True),
        [Input("selected-keywords-store", "data")],
        [State("jobs-table-original-data", "data")],
        prevent_initial_call=True,
    )
    def filter_jobs_by_keywords(selected_keywords, original_jobs_data):
        """Filter jobs table based on selected keywords."""
        try:
            from ..components.keyword_cloud import get_jobs_matching_keywords

            if not original_jobs_data:
                return []

            if not selected_keywords:
                # No filters, return all jobs
                return original_jobs_data

            # Filter jobs by keywords
            filtered_jobs = get_jobs_matching_keywords(original_jobs_data, selected_keywords)

            logger.info(
                f"Filtered jobs by keywords {selected_keywords}: "
                f"{len(filtered_jobs)} jobs found"
            )

            return filtered_jobs

        except Exception as e:
            logger.error(f"Error filtering jobs by keywords: {str(e)}")
            return original_jobs_data or []

    logger.info("Keyword cloud callbacks registered successfully")
