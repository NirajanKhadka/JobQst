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

# Local imports
try:
    # Try absolute imports first
    try:
        from src.dashboard.dash_app.components.sidebar import (
            create_sidebar
        )
        from src.dashboard.dash_app.layouts.jobs_layout import (
            create_jobs_layout
        )
        from src.dashboard.dash_app.layouts.analytics_layout import (
            create_analytics_layout
        )
        from src.dashboard.dash_app.layouts.scraping_layout import (
            create_scraping_layout
        )
        from src.dashboard.dash_app.layouts.processing_layout import (
            create_processing_layout
        )
        from src.dashboard.dash_app.layouts.system_layout import (
            create_system_layout
        )
        from src.dashboard.dash_app.layouts.settings_layout import (
            create_settings_layout
        )

        # Callback imports
        from src.dashboard.dash_app.callbacks.jobs_callbacks import (
            register_jobs_callbacks
        )
        from src.dashboard.dash_app.callbacks.analytics_callbacks import (
            register_analytics_callbacks
        )
        from src.dashboard.dash_app.callbacks.scraping_callbacks import (
            register_scraping_callbacks
        )
        from src.dashboard.dash_app.callbacks.processing_callbacks import (
            register_processing_callbacks
        )
        from src.dashboard.dash_app.callbacks.system_callbacks import (
            register_system_callbacks
        )
        from src.dashboard.dash_app.callbacks.settings_callbacks import (
            register_settings_callbacks
        )
        
        import_method = "absolute"
    except ImportError:
        # Fallback to relative imports
        from .components.sidebar import create_sidebar
        from .layouts.jobs_layout import create_jobs_layout
        from .layouts.enhanced_analytics_layout import (
            create_enhanced_analytics_layout as create_analytics_layout
        )
        from .layouts.scraping_layout import create_scraping_layout
        from .layouts.processing_layout import create_processing_layout
        from .layouts.system_layout import create_system_layout
        from .layouts.settings_layout import create_settings_layout

        # Callback imports
        from .callbacks.jobs_callbacks import register_jobs_callbacks
        from .callbacks.enhanced_analytics_callbacks import (
            register_enhanced_analytics_callbacks as register_analytics_callbacks
        )
        from .callbacks.scraping_callbacks import (
            register_scraping_callbacks
        )
        from .callbacks.processing_callbacks import (
            register_processing_callbacks
        )
        from .callbacks.system_callbacks import register_system_callbacks
        from .callbacks.settings_callbacks import (
            register_settings_callbacks
        )
        
        import_method = "relative"
except ImportError as e:
    print(f"Import error: {e}")
    print("Some features may not be available")
    # Create fallback functions
    
    def create_sidebar():
        return html.Div([
            html.H5("Sidebar"),
            html.P("Using fallback - import failed")
        ])
    
    def create_jobs_layout():
        return html.Div([html.H3("Jobs Layout"), html.P("Import failed")])
    
    def create_analytics_layout():
        return html.Div([html.H3("Analytics Layout"),
                        html.P("Import failed")])

    def create_processing_layout():
        return html.Div([html.H3("Processing Layout"),
                        html.P("Import failed")])

    def create_system_layout():
        return html.Div([html.H3("System Layout"), html.P("Import failed")])

    def create_settings_layout():
        return html.Div([html.H3("Settings Layout"),
                        html.P("Import failed")])

    def register_jobs_callbacks(app):
        pass

    def register_analytics_callbacks(app):
        pass

    def register_processing_callbacks(app):
        pass

    def register_system_callbacks(app):
        pass

    def register_settings_callbacks(app):
        pass

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log import success
try:
    logger.info(f"Dashboard imports successful using {import_method} imports")
except NameError:
    logger.info("Dashboard imports failed - using fallback functions")

# Initialize Dash app
dashboard = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.CYBORG,  # Dark theme
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/" +
        "6.0.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True,
    title="JobQst Dashboard"
)

# Define the main layout
dashboard.layout = dbc.Container([
    # Data stores
    dcc.Store(id='profile-store', storage_type='session'),
    dcc.Store(id='jobs-data-store', storage_type='session'),
    dcc.Store(id='settings-store', storage_type='session'),
    dcc.Store(
        id='processing-quick-log-store',
        data={},
        storage_type='session'
    ),
    dcc.Interval(id='auto-refresh-interval', interval=30000, n_intervals=0),
    
    # Download component for CSV export
    dcc.Download(id="jobs-csv-download"),
    
    # Header
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1([
                    html.I(className="fas fa-rocket me-3 text-primary"),
                    "JobQst Dashboard"
                ], className="mb-0"),
                html.Div([
                    dbc.Badge("Profile:", className="me-2"),
                    dbc.Badge(
                        id="current-profile-badge",
                        color="primary",
                        className="me-3"
                    ),
                    dbc.Switch(
                        id="auto-refresh-switch",
                        label="Auto-refresh",
                        value=True,
                        className="me-3"
                    ),
                    dbc.Badge(
                        id="system-status-badge",
                        color="success",
                        children="System OK"
                    )
                ], className="d-flex align-items-center")
            ], className="d-flex justify-content-between " +
               "align-items-center py-3")
        ])
    ], className="border-bottom mb-4"),
    
    # Main content area
    dbc.Row([
        # Sidebar
        dbc.Col([
            create_sidebar() if 'create_sidebar' in globals() else html.Div([
                html.H5("Sidebar Unavailable"),
                html.P("Import error - some features may not work"),
                html.P("Using default profile: Nirajan",
                       className="text-muted")
            ])
        ], width=3, className="pe-4"),        # Main content
        dbc.Col([
            html.Div(id="page-content")
        ], width=9)
    ], className="h-100"),
    
    # Footer
    dbc.Row([
        dbc.Col([
            html.Hr(className="border-secondary"),
            html.P([
                "JobQst Dashboard • ",
                html.Small(id="last-updated", children="Last updated: --")
            ], className="text-light text-center mb-0")
        ])
    ])
], fluid=True, className="h-100 bg-dark text-light")


# Main navigation callback
@dashboard.callback(
    Output('page-content', 'children'),
    [Input('nav-home', 'n_clicks'),
     Input('nav-job-tracker', 'n_clicks'),
     Input('nav-jobs', 'n_clicks'),
     Input('nav-analytics', 'n_clicks'),
     Input('nav-utilities', 'n_clicks'),
     Input('nav-scraping', 'n_clicks'),
     Input('nav-processing', 'n_clicks'),
     Input('nav-system', 'n_clicks'),
     Input('nav-settings', 'n_clicks')],
    prevent_initial_call=False
)
def display_page(home_clicks, tracker_clicks, jobs_clicks, analytics_clicks,
                 utilities_clicks, scraping_clicks, processing_clicks, 
                 system_clicks, settings_clicks):
    """Handle navigation between pages"""
    ctx = dash.callback_context
    
    if not ctx.triggered:
        # Load enhanced home layout by default
        try:
            from .layouts.enhanced_home_layout_new import (
                create_enhanced_home_layout
            )
            return create_enhanced_home_layout()
        except ImportError:
            return create_jobs_layout()
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if button_id == 'nav-home':
            from .layouts.enhanced_home_layout_new import (
                create_enhanced_home_layout
            )
            return create_enhanced_home_layout()
        elif button_id == 'nav-job-tracker':
            from .layouts.job_tracker_layout import create_job_tracker_layout
            return create_job_tracker_layout()
        elif button_id == 'nav-jobs':
            return create_jobs_layout()
        elif button_id == 'nav-analytics':
            return create_analytics_layout()
        elif button_id == 'nav-utilities':
            from .layouts.utilities_layout import create_utilities_layout
            return create_utilities_layout()
        elif button_id == 'nav-scraping':
            return create_scraping_layout()
        elif button_id == 'nav-processing':
            return create_processing_layout()
        elif button_id == 'nav-system':
            return create_system_layout()
        elif button_id == 'nav-settings':
            return create_settings_layout()
        else:
            from .layouts.enhanced_home_layout_new import (
                create_enhanced_home_layout
            )
            return create_enhanced_home_layout()
    except Exception as e:
        logger.error(f"Error loading page: {e}")
        return html.Div([
            dbc.Alert([
                html.H4("Page Load Error", className="alert-heading"),
                html.P(f"Error loading page: {str(e)}"),
                html.P("Please check the logs for more details.",
                       className="mb-0")
            ], color="danger")
        ])
# Profile management removed - profile is set when launching dashboard
# The profile is now passed as a parameter and stored in the app instance
try:
    @dashboard.callback(
        [Output('current-profile-display', 'children'),
         Output('profile-store', 'data')],
        Input('auto-refresh-interval', 'n_intervals'),
        prevent_initial_call=False
    )
    def set_static_profile(n_intervals):
        """Set static profile - no switching allowed"""
        profile_name = getattr(dashboard, 'profile_name', 'Nirajan')
        return profile_name, {'current_profile': profile_name}
except Exception as e:
    logger.error(f"Profile display callback registration failed: {e}")
    # Register a fallback callback that sets default profile
    
    @dashboard.callback(
        [Output('current-profile-display', 'children'),
         Output('profile-store', 'data')],
        Input('auto-refresh-interval', 'n_intervals'),
        prevent_initial_call=False
    )
    def update_profile_fallback(n_intervals):
        """Fallback profile update - sets default profile"""
        default_profile = getattr(dashboard, 'profile_name', 'Nirajan')
        return default_profile, {'current_profile': default_profile}


# System status callback
@dashboard.callback(
    Output('system-status-badge', 'children'),
    Output('system-status-badge', 'color'),
    Input('auto-refresh-interval', 'n_intervals')
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
    Output('last-updated', 'children'),
    Input('auto-refresh-interval', 'n_intervals')
)
def update_timestamp(n_intervals):
    """Update last updated timestamp"""
    from datetime import datetime
    return f"Last updated: {datetime.now().strftime('%H:%M:%S')}"


# Register all callbacks
try:
    if 'register_jobs_callbacks' in globals():
        register_jobs_callbacks(dashboard)
        register_analytics_callbacks(dashboard)
        register_scraping_callbacks(dashboard)
        register_processing_callbacks(dashboard)
        register_system_callbacks(dashboard)
        register_settings_callbacks(dashboard)
        
        # Register job tracker callbacks
        try:
            from .callbacks.job_tracker_callbacks import register_job_tracker_callbacks
            register_job_tracker_callbacks(dashboard)
            logger.info("Job tracker callbacks registered")
        except ImportError as e:
            logger.warning(f"Job tracker callbacks not available: {e}")
        
        logger.info("All callbacks registered successfully")
    else:
        logger.info("Using fallback callbacks - imports failed")
except Exception as e:
    logger.error(f"Error registering callbacks: {e}")
    logger.info("Some features may not be available")


def set_dashboard_profile(profile_name):
    """Set the profile name for the dashboard instance"""
    dashboard.profile_name = profile_name
    logger.info(f"Dashboard profile set to: {profile_name}")


if __name__ == '__main__':
    logger.info("Starting JobQst Dashboard...")
    logger.info("Dashboard available at: http://127.0.0.1:8050")
    
    dashboard.run(
        debug=True,
        host='127.0.0.1',
        port=8050
    )

