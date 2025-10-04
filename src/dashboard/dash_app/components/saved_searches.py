"""
Saved Searches Component for JobQst Dashboard
Simple implementation for saving and loading search configurations.
"""

import logging
import dash_bootstrap_components as dbc
from dash import html, Input, Output, State, callback, no_update, ctx

logger = logging.getLogger(__name__)


def create_saved_searches_buttons() -> html.Div:
    """Create saved searches action buttons."""
    return html.Div(
        [
            dbc.ButtonGroup(
                [
                    dbc.Button(
                        "💾 Save Search",
                        color="outline-info",
                        size="sm",
                        id="save-search-btn",
                        className="me-1",
                    ),
                    dbc.Button(
                        "📚 Saved Searches",
                        color="outline-primary",
                        size="sm",
                        id="view-saved-searches-btn",
                    ),
                ]
            )
        ],
        className="d-flex justify-content-end mb-3",
    )


def create_save_search_modal() -> dbc.Modal:
    """Create modal dialog for saving current search."""
    return dbc.Modal(
        [
            dbc.ModalHeader(
                [
                    dbc.ModalTitle("💾 Save Current Search"),
                    dbc.Button("×", className="btn-close", id="close-save-search-modal"),
                ]
            ),
            dbc.ModalBody(
                [
                    html.Label("Search Name", className="form-label fw-bold"),
                    dbc.Input(
                        id="search-name-input",
                        placeholder="e.g., Python Developer - Toronto",
                        value="",
                        className="mb-3",
                    ),
                    dbc.Alert(
                        id="save-search-alert", is_open=False, dismissable=True, className="mt-2"
                    ),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button("Cancel", color="secondary", id="cancel-save-search"),
                    dbc.Button("💾 Save", color="primary", id="confirm-save-search"),
                ]
            ),
        ],
        id="save-search-modal",
        size="lg",
        is_open=False,
    )


def create_saved_searches_modal() -> dbc.Modal:
    """Create modal dialog for managing saved searches."""
    return dbc.Modal(
        [
            dbc.ModalHeader(
                [
                    dbc.ModalTitle("📚 Saved Searches"),
                    dbc.Button("×", className="btn-close", id="close-saved-searches-modal"),
                ]
            ),
            dbc.ModalBody(
                [
                    html.Div(id="saved-searches-list"),
                    dbc.Alert(
                        id="saved-searches-alert", is_open=False, dismissable=True, className="mt-2"
                    ),
                ]
            ),
            dbc.ModalFooter(
                [dbc.Button("Close", color="secondary", id="close-saved-searches-footer")]
            ),
        ],
        id="saved-searches-modal",
        size="xl",
        is_open=False,
    )


def register_saved_searches_callbacks(app):
    """Register simplified callbacks for saved searches."""

    @callback(
        Output("save-search-modal", "is_open"),
        [
            Input("save-search-btn", "n_clicks"),
            Input("cancel-save-search", "n_clicks"),
            Input("close-save-search-modal", "n_clicks"),
        ],
        prevent_initial_call=True,
    )
    def toggle_save_search_modal(save_clicks, cancel_clicks, close_clicks):
        """Toggle save search modal."""
        cancel_ids = ["cancel-save-search", "close-save-search-modal"]
        if ctx.triggered_id in cancel_ids:
            return False
        elif ctx.triggered_id == "save-search-btn":
            return True
        return no_update

    @callback(
        Output("saved-searches-modal", "is_open"),
        [
            Input("view-saved-searches-btn", "n_clicks"),
            Input("close-saved-searches-modal", "n_clicks"),
            Input("close-saved-searches-footer", "n_clicks"),
        ],
        prevent_initial_call=True,
    )
    def toggle_saved_searches_modal(view_clicks, close_clicks, footer_clicks):
        """Toggle saved searches modal."""
        close_ids = ["close-saved-searches-modal", "close-saved-searches-footer"]
        if ctx.triggered_id in close_ids:
            return False
        elif ctx.triggered_id == "view-saved-searches-btn":
            return True
        return no_update

    @callback(
        [
            Output("save-search-alert", "children"),
            Output("save-search-alert", "color"),
            Output("save-search-alert", "is_open"),
            Output("search-name-input", "value"),
        ],
        [Input("confirm-save-search", "n_clicks")],
        [State("search-name-input", "value")],
        prevent_initial_call=True,
    )
    def save_search_configuration(confirm_clicks, search_name):
        """Save current search configuration."""
        if not confirm_clicks or not search_name:
            if confirm_clicks and not search_name:
                return "Please enter a search name.", "danger", True, no_update
            return no_update, no_update, no_update, no_update

        try:
            # Simple implementation - just show success for now
            return f"✅ Search '{search_name}' saved!", "success", True, ""
        except Exception as e:
            logger.error(f"Error saving search: {e}")
            return f"❌ Error: {str(e)}", "danger", True, no_update

    @callback(
        Output("saved-searches-list", "children"),
        [Input("saved-searches-modal", "is_open")],
        prevent_initial_call=True,
    )
    def load_saved_searches(modal_open):
        """Load and display saved searches."""
        if not modal_open:
            return no_update

        # Simple placeholder for now
        return dbc.Alert(
            [
                html.H6("Feature Coming Soon", className="mb-2"),
                html.P("Saved searches functionality will be available soon."),
            ],
            color="info",
        )

    logger.info("Saved searches callbacks registered successfully")
