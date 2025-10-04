"""
JobQst Dash Dashboard Application
Main entry point for the interactive dashboard
"""

import sys
import logging
from pathlib import Path

# Load environment variables first
from dotenv import load_dotenv

load_dotenv()

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Dashboard component imports - using absolute imports only
from src.dashboard.dash_app.components.streamlined_sidebar import create_streamlined_sidebar
from src.dashboard.dash_app.layouts.ranked_jobs_layout import create_ranked_jobs_layout
from src.dashboard.dash_app.layouts.job_browser_layout import create_job_browser_layout
from src.dashboard.dash_app.layouts.job_tracker_layout import create_job_tracker_layout
from src.dashboard.dash_app.layouts.market_insights_layout import create_market_insights_layout
from src.dashboard.dash_app.layouts.scraper_control_layout import create_scraper_control_layout

# Legacy imports (for advanced mode)
from src.dashboard.dash_app.layouts.jobs_layout import create_jobs_layout
from src.dashboard.dash_app.layouts.analytics_layout import create_analytics_layout
from src.dashboard.dash_app.layouts.scraping_layout import create_scraping_layout
from src.dashboard.dash_app.layouts.processing_layout import create_processing_layout
from src.dashboard.dash_app.layouts.system_layout import create_system_layout

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Dashboard imports loaded successfully")

# Callback imports
try:
    from src.dashboard.dash_app.callbacks.jobs_callbacks import register_jobs_callbacks
    from src.dashboard.dash_app.callbacks.analytics_callbacks import register_analytics_callbacks
    from src.dashboard.dash_app.callbacks.scraping_callbacks import register_scraping_callbacks
    from src.dashboard.dash_app.callbacks.processing_callbacks import register_processing_callbacks
    from src.dashboard.dash_app.callbacks.system_callbacks import register_system_callbacks
    from src.dashboard.dash_app.callbacks.settings_callbacks import register_settings_callbacks
except ImportError as e:
    logger.warning(f"Some callbacks could not be imported: {e}")

# Initialize Dash app
dashboard = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.CYBORG,  # Dark theme
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/" + "6.0.0/css/all.min.css",
    ],
    suppress_callback_exceptions=True,
    title="JobQst Dashboard",
)

# Define the main layout
dashboard.layout = dbc.Container(
    [
        # Data stores
        dcc.Store(id="profile-store", storage_type="session"),
        dcc.Store(id="jobs-data-store", storage_type="session"),
        dcc.Store(id="settings-store", storage_type="session"),
        dcc.Store(id="processing-quick-log-store", data={}, storage_type="session"),
        dcc.Interval(id="auto-refresh-interval", interval=30000, n_intervals=0, max_intervals=-1),
        # Download component for CSV export
        dcc.Download(id="jobs-csv-download"),
        # Header
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.H1(
                                    [
                                        html.I(className="fas fa-rocket me-3 text-primary"),
                                        "JobQst Dashboard",
                                    ],
                                    className="mb-0",
                                ),
                                html.Div(
                                    [
                                        dbc.Badge("Profile:", className="me-2"),
                                        dbc.Badge(
                                            id="current-profile-badge",
                                            color="primary",
                                            className="me-3",
                                            children="Loading...",
                                        ),
                                        dbc.Switch(
                                            id="auto-refresh-switch",
                                            label="Auto-refresh",
                                            value=True,
                                            className="me-3",
                                        ),
                                        dbc.Badge(
                                            id="system-status-badge",
                                            color="success",
                                            children="System OK",
                                        ),
                                    ],
                                    className="d-flex align-items-center",
                                ),
                            ],
                            className="d-flex justify-content-between " + "align-items-center py-3",
                        )
                    ]
                )
            ],
            className="border-bottom mb-4",
        ),
        # Main content area
        dbc.Row(
            [
                # Sidebar
                dbc.Col([create_streamlined_sidebar()], width=3, className="pe-4"),
                # Main content - Load home page immediately
                dbc.Col([
                    dcc.Loading(
                        id="page-loading",
                        type="default",
                        children=html.Div(
                            id="page-content",
                            children=create_ranked_jobs_layout()  # Load home page directly
                        )
                    )
                ], width=9),
            ],
            className="h-100",
        ),
        # Footer
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Hr(className="border-secondary"),
                        html.P(
                            [
                                "JobQst Dashboard • ",
                                html.Small(id="last-updated", children="Last updated: --"),
                            ],
                            className="text-light text-center mb-0",
                        ),
                    ]
                )
            ]
        ),
    ],
    fluid=True,
    className="h-100 bg-dark text-light",
)


# Main navigation callback - 5-tab navigation (Home, Job Browser, Job Tracker, Market Insights, Settings)
@dashboard.callback(
    Output("page-content", "children"),
    [
        Input("nav-home", "n_clicks"),
        Input("nav-job-browser", "n_clicks"),
        Input("nav-job-tracker", "n_clicks"),
        Input("nav-market-insights", "n_clicks"),
        Input("nav-scraper", "n_clicks"),
    ],
    prevent_initial_call=False,
)
def display_page(home_clicks, browser_clicks, tracker_clicks, insights_clicks, settings_clicks):
    """Handle navigation between dashboard pages"""
    ctx = dash.callback_context
    
    logger.info(f"display_page called - triggered: {ctx.triggered}")
    logger.info(f"  home_clicks={home_clicks}, browser_clicks={browser_clicks}")

    if not ctx.triggered or ctx.triggered[0]["value"] is None:
        # Default to Home (Ranked Jobs for now)
        logger.info("Loading default page: Ranked Jobs (Home)")
        try:
            # Verify profile is set before creating layout
            if not hasattr(dashboard, 'profile_name') or dashboard.profile_name is None:
                logger.error("No profile set on dashboard when loading default page")
                return html.Div([
                    dbc.Alert(
                        [
                            html.H4("Profile Not Set", className="alert-heading"),
                            html.P("Dashboard profile has not been configured."),
                            html.P("Please restart dashboard with: python main.py <ProfileName> --action dashboard"),
                        ],
                        color="warning",
                    )
                ])
            
            logger.info(f"Creating layout for profile: {dashboard.profile_name}")
            layout = create_ranked_jobs_layout()
            logger.info(f"[OK] Default layout created successfully: {type(layout)}")
            return layout
        except Exception as e:
            logger.error(f"[ERROR] Error loading default page: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return html.Div([
                dbc.Alert(
                    [
                        html.H4("Error Loading Home Page", className="alert-heading"),
                        html.P(f"Error: {str(e)}"),
                        html.Hr(),
                        html.Pre(traceback.format_exc(), className="small"),
                    ],
                    color="danger",
                )
            ])

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    try:
        logger.info(f"Navigation triggered: {button_id}")
        if button_id == "nav-home":
            return create_ranked_jobs_layout()
        elif button_id == "nav-job-browser":
            return create_job_browser_layout()
        elif button_id == "nav-job-tracker":
            return create_job_tracker_layout()
        elif button_id == "nav-market-insights":
            return create_market_insights_layout()
        elif button_id == "nav-scraper":
            return create_scraper_control_layout()
        else:
            # Default fallback
            logger.warning(f"Unknown navigation button: {button_id}, loading home")
            return create_ranked_jobs_layout()
    except Exception as e:
        logger.error(f"Error loading page {button_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return html.Div(
            [
                dbc.Alert(
                    [
                        html.H4("Page Load Error", className="alert-heading"),
                        html.P(f"Error loading page: {str(e)}"),
                        html.Hr(),
                        html.Pre(traceback.format_exc(), className="small"),
                    ],
                    color="danger",
                )
            ]
        )


# Profile management removed - profile is set when launching dashboard
# The profile is now passed as a parameter and stored in the app instance
@dashboard.callback(
    [Output("current-profile-display", "children"), Output("profile-store", "data"), Output("current-profile-badge", "children")],
    Input("auto-refresh-interval", "n_intervals"),
    prevent_initial_call=False,
)
def set_static_profile(n_intervals):
    """Set static profile - no switching allowed"""
    try:
        # Profile MUST be set when dashboard is launched
        if not hasattr(dashboard, "profile_name") or dashboard.profile_name is None:
            error_msg = "ERROR: No Profile"
            logger.error("Dashboard launched without profile_name set!")
            return error_msg, {"current_profile": None, "error": "No profile set"}, error_msg
        
        profile_name = dashboard.profile_name
        logger.info(f"Profile callback triggered: {profile_name}")
        return profile_name, {"current_profile": profile_name}, profile_name
    except Exception as e:
        logger.error(f"Error in profile callback: {e}")
        error_msg = f"ERROR: {str(e)}"
        return error_msg, {"current_profile": None, "error": str(e)}, error_msg


# System status callback
@dashboard.callback(
    Output("system-status-badge", "children"),
    Output("system-status-badge", "color"),
    Input("auto-refresh-interval", "n_intervals"),
)
def update_system_status(n_intervals):
    """Update system status indicator"""
    try:
        # Basic health check - can be expanded
        from src.dashboard.dash_app.utils.data_loader import DataLoader

        data_loader = DataLoader()

        # Try to load some basic data
        profiles = data_loader.get_available_profiles()

        if profiles:
            return "System OK", "success"
        else:
            return "No Profiles", "warning"

    except Exception as e:
        logger.error(f"System health check failed: {e}")
        return "System Error", "danger"


# Last updated timestamp callback
@dashboard.callback(
    Output("last-updated", "children"), Input("auto-refresh-interval", "n_intervals")
)
def update_timestamp(n_intervals):
    """Update last updated timestamp"""
    from datetime import datetime

    return f"Last updated: {datetime.now().strftime('%H:%M:%S')}"


# Sidebar quick stats callback
@dashboard.callback(
    [
        Output("sidebar-stat-total", "children"),
        Output("sidebar-stat-rcip", "children"),
        Output("sidebar-stat-tracked", "children"),
    ],
    Input("auto-refresh-interval", "n_intervals"),
)
def update_sidebar_stats(n_intervals):
    """Update sidebar quick statistics"""
    try:
        from src.dashboard.dash_app.utils.data_loader import DataLoader

        # Profile MUST be set when dashboard is launched
        if not hasattr(dashboard, "profile_name") or dashboard.profile_name is None:
            logger.error("Cannot update stats: No profile set")
            return "--", "--", "--"
        
        profile_name = dashboard.profile_name
        data_loader = DataLoader()
        stats = data_loader.get_job_stats(profile_name)

        total = stats.get("total_jobs", 0)
        rcip = stats.get("rcip_jobs", 0)
        tracked = stats.get("tracked_jobs", 0)

        return str(total), str(rcip), str(tracked)
    except Exception as e:
        logger.error(f"Error updating sidebar stats: {e}")
        return "--", "--", "--"


# Register all callbacks
try:
    # Register all main dashboard callbacks
    # register_jobs_callbacks(dashboard)  # Disabled - using ranked_jobs_callbacks instead
    register_analytics_callbacks(dashboard)
    register_scraping_callbacks(dashboard)
    register_processing_callbacks(dashboard)
    register_system_callbacks(dashboard)
    register_settings_callbacks(dashboard)

    # Register job tracker callbacks
    try:
        from src.dashboard.dash_app.callbacks.job_tracker_callbacks import (
            register_job_tracker_callbacks,
        )

        register_job_tracker_callbacks(dashboard)
        logger.info("Job tracker callbacks registered")
    except ImportError as e:
        logger.warning(f"Job tracker callbacks not available: {e}")

    # Register ranked jobs callbacks
    try:
        from src.dashboard.dash_app.callbacks.ranked_jobs_callbacks import (
            register_ranked_jobs_callbacks,
        )

        register_ranked_jobs_callbacks(dashboard)
        logger.info("Ranked jobs callbacks registered")
    except ImportError as e:
        logger.warning(f"Ranked jobs callbacks not available: {e}")
    
    # NOTE: Job browser callbacks are registered later in set_dashboard_profile()
    # because they require a profile to be set first

    logger.info("All callbacks registered successfully (except profile-dependent ones)")
except Exception as e:
    logger.error(f"Error registering callbacks: {e}")
    logger.info("Some features may not be available")


def set_dashboard_profile(profile_name: str):
    """
    Set the profile name for the dashboard instance
    
    Args:
        profile_name: Profile name (required, must be valid)
        
    Raises:
        ValueError: If profile is invalid
    """
    from src.dashboard.utils.profile_utils import require_profile
    
    # Validate profile exists
    profile_name = require_profile(profile_name)
    
    dashboard.profile_name = profile_name
    logger.info(f"[OK] Dashboard profile set to: {profile_name}")
    
    # Now register profile-dependent callbacks (job browser)
    try:
        from src.dashboard.dash_app.callbacks.job_browser_callbacks import (
            register_job_browser_callbacks,
        )
        
        register_job_browser_callbacks(dashboard, profile_name)
        logger.info(f"[OK] Job browser callbacks registered for profile: {profile_name}")
    except ImportError as e:
        logger.warning(f"Job browser callbacks not available: {e}")
    except Exception as e:
        logger.error(f"Error registering job browser callbacks: {e}")


if __name__ == "__main__":
    logger.info("Starting JobQst Dashboard...")
    logger.info("Dashboard available at: http://127.0.0.1:8050")

    dashboard.run(debug=True, host="127.0.0.1", port=8050)
