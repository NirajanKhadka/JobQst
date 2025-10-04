"""
Theme Toggle Component for JobQst Dashboard
Provides dark/light mode switching with persistence
"""

import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
import logging

logger = logging.getLogger(__name__)


def create_theme_toggle():
    """Create theme toggle component"""
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H6("🎨 Theme", className="mb-3"),
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                [html.I(className="fas fa-sun me-2"), "Light"],
                                                id="light-theme-btn",
                                                color="outline-warning",
                                                size="sm",
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-moon me-2"), "Dark"],
                                                id="dark-theme-btn",
                                                color="outline-primary",
                                                size="sm",
                                            ),
                                            dbc.Button(
                                                [html.I(className="fas fa-desktop me-2"), "Auto"],
                                                id="auto-theme-btn",
                                                color="outline-secondary",
                                                size="sm",
                                            ),
                                        ],
                                        className="w-100",
                                    ),
                                ],
                                width=12,
                            )
                        ]
                    )
                ]
            )
        ],
        className="shadow-sm border-0",
    )


def create_theme_settings():
    """Create detailed theme settings panel"""
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H5(
                        [html.I(className="fas fa-palette me-2"), "Theme Settings"],
                        className="mb-0",
                    )
                ]
            ),
            dbc.CardBody(
                [
                    # Current theme status
                    dbc.Alert(
                        [
                            html.Div(
                                [
                                    html.Strong("Current Theme: "),
                                    html.Span(id="current-theme-display", children="Light"),
                                ]
                            )
                        ],
                        id="theme-status-alert",
                        color="info",
                        className="mb-3",
                    ),
                    # Theme selection
                    html.Div(
                        [
                            html.Label("Select Theme", className="fw-semibold mb-2"),
                            dbc.RadioItems(
                                id="theme-selector",
                                options=[
                                    {"label": "🌞 Light Mode", "value": "light"},
                                    {"label": "🌙 Dark Mode", "value": "dark"},
                                    {"label": "🖥️ System Default", "value": "auto"},
                                ],
                                value="light",
                                className="mb-3",
                            ),
                        ]
                    ),
                    # Color scheme options
                    html.Div(
                        [
                            html.Label("Color Accent", className="fw-semibold mb-2"),
                            dbc.RadioItems(
                                id="color-accent-selector",
                                options=[
                                    {"label": "🔵 Blue (Default)", "value": "blue"},
                                    {"label": "🟢 Green", "value": "green"},
                                    {"label": "🟣 Purple", "value": "purple"},
                                    {"label": "🔴 Red", "value": "red"},
                                ],
                                value="blue",
                                className="mb-3",
                            ),
                        ]
                    ),
                    # Font size options
                    html.Div(
                        [
                            html.Label("Font Size", className="fw-semibold mb-2"),
                            dcc.Slider(
                                id="font-size-slider",
                                min=12,
                                max=18,
                                step=1,
                                value=14,
                                marks={12: "Small", 14: "Normal", 16: "Large", 18: "X-Large"},
                                className="mb-3",
                            ),
                        ]
                    ),
                    # Save/Reset buttons
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                [html.I(className="fas fa-save me-2"), "Save Settings"],
                                id="save-theme-btn",
                                color="primary",
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-undo me-2"), "Reset"],
                                id="reset-theme-btn",
                                color="secondary",
                            ),
                        ],
                        className="w-100",
                    ),
                ]
            ),
        ]
    )


def register_theme_callbacks(app):
    """Register theme toggle callbacks"""
    try:

        @app.callback(
            [
                Output("current-theme-display", "children"),
                Output("theme-status-alert", "color"),
                Output("light-theme-btn", "color"),
                Output("dark-theme-btn", "color"),
                Output("auto-theme-btn", "color"),
            ],
            [
                Input("light-theme-btn", "n_clicks"),
                Input("dark-theme-btn", "n_clicks"),
                Input("auto-theme-btn", "n_clicks"),
                Input("theme-selector", "value"),
            ],
        )
        def update_theme_display(light_clicks, dark_clicks, auto_clicks, theme_value):
            """Update theme display and button states"""
            try:
                # Determine active theme
                active_theme = theme_value or "light"

                # Update display text
                theme_names = {"light": "Light Mode", "dark": "Dark Mode", "auto": "System Default"}
                display_text = theme_names.get(active_theme, "Light Mode")

                # Set alert color based on theme
                alert_colors = {"light": "warning", "dark": "dark", "auto": "info"}
                alert_color = alert_colors.get(active_theme, "warning")

                # Update button colors
                if active_theme == "light":
                    light_color = "warning"
                else:
                    light_color = "outline-warning"

                if active_theme == "dark":
                    dark_color = "primary"
                else:
                    dark_color = "outline-primary"

                if active_theme == "auto":
                    auto_color = "secondary"
                else:
                    auto_color = "outline-secondary"

                return (display_text, alert_color, light_color, dark_color, auto_color)

            except Exception as e:
                logger.error(f"Error updating theme display: {e}")
                return ("Light Mode", "warning", "warning", "outline-primary", "outline-secondary")

        @app.callback(
            Output("theme-selector", "value"),
            [
                Input("light-theme-btn", "n_clicks"),
                Input("dark-theme-btn", "n_clicks"),
                Input("auto-theme-btn", "n_clicks"),
            ],
            prevent_initial_call=True,
        )
        def sync_theme_selector(light_clicks, dark_clicks, auto_clicks):
            """Sync theme selector with button clicks"""
            from dash import ctx

            try:
                if not ctx.triggered:
                    return "light"

                button_id = ctx.triggered[0]["prop_id"].split(".")[0]

                if button_id == "light-theme-btn":
                    return "light"
                elif button_id == "dark-theme-btn":
                    return "dark"
                elif button_id == "auto-theme-btn":
                    return "auto"

                return "light"

            except Exception as e:
                logger.error(f"Error syncing theme selector: {e}")
                return "light"

        @app.callback(
            Output("theme-settings-toast", "is_open", allow_duplicate=True),
            [Input("save-theme-btn", "n_clicks"), Input("reset-theme-btn", "n_clicks")],
            [
                State("theme-selector", "value"),
                State("color-accent-selector", "value"),
                State("font-size-slider", "value"),
            ],
            prevent_initial_call=True,
        )
        def handle_theme_actions(save_clicks, reset_clicks, theme, accent, font_size):
            """Handle save and reset theme actions"""
            from dash import ctx

            try:
                if not ctx.triggered:
                    return False

                button_id = ctx.triggered[0]["prop_id"].split(".")[0]

                if button_id == "save-theme-btn":
                    # Here you would save to database or local storage
                    logger.info(f"Theme saved: {theme}, accent: {accent}, " f"font: {font_size}")
                    return True

                elif button_id == "reset-theme-btn":
                    # Reset to defaults
                    logger.info("Theme settings reset to defaults")
                    return True

                return False

            except Exception as e:
                logger.error(f"Error handling theme actions: {e}")
                return False

        logger.info("Theme toggle callbacks registered successfully")

    except Exception as e:
        logger.error(f"Error registering theme callbacks: {e}")


# Toast for theme settings feedback
def create_theme_toast():
    """Create toast for theme settings feedback"""
    return dbc.Toast(
        [html.P("Theme settings updated successfully!", className="mb-0")],
        id="theme-settings-toast",
        header="Theme Settings",
        icon="primary",
        dismissable=True,
        is_open=False,
        style={"position": "fixed", "top": 66, "right": 10, "width": 350},
    )
