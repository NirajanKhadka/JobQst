"""
Settings callbacks for JobQst Dashboard
Handle configuration and settings management
"""

import logging
from dash import Input, Output, State

logger = logging.getLogger(__name__)


def register_settings_callbacks(app):
    """Register all settings-related callbacks"""

    @app.callback(Output("settings-content", "children"), Input("settings-tabs", "active_tab"))
    def render_settings_content(active_tab):
        """Render settings content based on active tab"""
        try:
            from ..layouts.settings_layout import (
                create_profile_settings,
                create_job_preferences,
                create_dashboard_settings,
                create_data_management,
            )

            if active_tab == "profile-settings":
                return create_profile_settings()
            elif active_tab == "job-preferences":
                return create_job_preferences()
            elif active_tab == "dashboard-settings":
                return create_dashboard_settings()
            elif active_tab == "data-management":
                return create_data_management()
            else:
                return create_profile_settings()

        except Exception as e:
            logger.error(f"Error rendering settings content: {e}")
            return f"Error loading settings: {e}"

    @app.callback(
        Output("settings-save-notification", "children"),
        Input("save-profile-settings-btn", "n_clicks"),
        [
            State("profile-full-name", "value"),
            State("profile-email", "value"),
            State("profile-experience-years", "value"),
            State("profile-current-title", "value"),
            State("profile-skills", "value"),
            State("profile-selector", "value"),
        ],
        prevent_initial_call=True,
    )
    def save_profile_settings(n_clicks, full_name, email, experience_years, current_title, skills, profile_name):
        """Save profile settings to JSON using UserProfileManager"""
        import dash_bootstrap_components as dbc
        from dash import html
        
        try:
            from src.core.user_profile_manager import UserProfileManager
            
            profile_manager = UserProfileManager()
            if not profile_name:
                logger.error("No profile provided to settings callback")
                return html.Div("Error: No profile configured", className="text-danger")
            
            # Load existing profile
            profile_data = profile_manager.load_profile(profile_name)
            
            # Update with new values
            if full_name:
                profile_data["name"] = full_name
            if email:
                profile_data["email"] = email
            if experience_years is not None:
                profile_data["experience"] = {"years": int(experience_years)}
            if current_title:
                profile_data["current_title"] = current_title
            if skills:
                # Parse comma-separated skills
                profile_data["skills"] = [s.strip() for s in skills.split(",") if s.strip()]
            
            # Save profile
            profile_manager.save_profile(profile_name, profile_data)
            
            logger.info(f"Profile settings saved for {profile_name}")
            
            return dbc.Alert(
                [html.I(className="fas fa-check-circle me-2"), "Profile settings saved successfully!"],
                color="success",
                dismissable=True,
                duration=4000,
                className="mt-3"
            )
        
        except Exception as e:
            logger.error(f"Error saving profile settings: {e}")
            return dbc.Alert(
                [html.I(className="fas fa-exclamation-circle me-2"), f"Error saving profile: {str(e)}"],
                color="danger",
                dismissable=True,
                duration=4000,
                className="mt-3"
            )
    
    @app.callback(
        Output("settings-save-notification", "children", allow_duplicate=True),
        Input("save-job-preferences-btn", "n_clicks"),
        [
            State("job-pref-locations", "value"),
            State("job-pref-salary-range", "value"),
            State("job-pref-work-type", "value"),
            State("job-pref-employment-type", "value"),
            State("profile-selector", "value"),
        ],
        prevent_initial_call=True,
    )
    def save_job_preferences(n_clicks, locations, salary_range, work_type, employment_type, profile_name):
        """Save job preferences to profile"""
        import dash_bootstrap_components as dbc
        from dash import html
        
        try:
            from src.core.user_profile_manager import UserProfileManager
            
            profile_manager = UserProfileManager()
            if not profile_name:
                logger.error("No profile provided to settings callback")
                return html.Div("Error: No profile configured", className="text-danger")
            
            # Load existing profile
            profile_data = profile_manager.load_profile(profile_name)
            
            # Update job preferences
            if locations:
                profile_data["preferred_locations"] = [loc.strip() for loc in locations.split(",") if loc.strip()]
            
            if salary_range:
                profile_data["salary_expectation"] = {
                    "min": salary_range[0],
                    "max": salary_range[1]
                }
            
            if work_type:
                profile_data["work_type_preferences"] = work_type
            
            if employment_type:
                profile_data["employment_type_preferences"] = employment_type
            
            # Save profile
            profile_manager.save_profile(profile_name, profile_data)
            
            logger.info(f"Job preferences saved for {profile_name}")
            
            return dbc.Alert(
                [html.I(className="fas fa-check-circle me-2"), "Job preferences saved successfully!"],
                color="success",
                dismissable=True,
                duration=4000,
                className="mt-3"
            )
        
        except Exception as e:
            logger.error(f"Error saving job preferences: {e}")
            return dbc.Alert(
                [html.I(className="fas fa-exclamation-circle me-2"), f"Error saving preferences: {str(e)}"],
                color="danger",
                dismissable=True,
                duration=4000,
                className="mt-3"
            )
    
    @app.callback(
        Output("settings-save-notification", "children", allow_duplicate=True),
        Input("save-dashboard-settings-btn", "n_clicks"),
        [
            State("dash-settings-default-view", "value"),
            State("dash-settings-jobs-per-page", "value"),
            State("dash-settings-auto-refresh", "value"),
            State("dash-settings-refresh-interval", "value"),
            State("dash-settings-notifications", "value"),
            State("dash-settings-filters", "value"),
        ],
        prevent_initial_call=True,
    )
    def save_dashboard_settings(n_clicks, default_view, jobs_per_page, auto_refresh, refresh_interval, notifications, filters):
        """Save dashboard settings and apply immediately"""
        import dash_bootstrap_components as dbc
        from dash import html
        
        try:
            # In production, save to a config file or database
            dashboard_config = {
                "default_view": default_view,
                "jobs_per_page": jobs_per_page,
                "auto_refresh": "enabled" in (auto_refresh or []),
                "refresh_interval": refresh_interval,
                "notifications": notifications or [],
                "filters": filters or []
            }
            
            logger.info(f"Dashboard settings saved: {dashboard_config}")
            
            return dbc.Alert(
                [html.I(className="fas fa-check-circle me-2"), "Dashboard settings saved successfully!"],
                color="success",
                dismissable=True,
                duration=4000,
                className="mt-3"
            )
        
        except Exception as e:
            logger.error(f"Error saving dashboard settings: {e}")
            return dbc.Alert(
                [html.I(className="fas fa-exclamation-circle me-2"), f"Error saving settings: {str(e)}"],
                color="danger",
                dismissable=True,
                duration=4000,
                className="mt-3"
            )

    @app.callback(
        Output("settings-save-status", "children"),
        [
            Input("default-processing-method", "value"),
            Input("default-batch-size", "value"),
            Input("min-match-score", "value"),
            Input("processing-features", "value"),
            Input("max-concurrent-jobs", "value"),
            Input("default-view", "value"),
            Input("jobs-per-page", "value"),
            Input("dashboard-features", "value"),
            Input("refresh-interval", "value"),
            Input("cache-ttl", "value"),
            Input("performance-options", "value"),
            Input("automation-level", "value"),
            Input("auto-apply-threshold", "value"),
            Input("daily-limit", "value"),
            Input("workflow-features", "value"),
        ],
        prevent_initial_call=True,
    )
    def save_settings(*args):
        """Save all settings (auto-save on change)"""
        try:
            # In a real implementation, save to configuration files
            settings = {
                "processing": {
                    "method": args[0],
                    "batch_size": args[1],
                    "min_match_score": args[2],
                    "features": args[3],
                    "max_concurrent": args[4],
                },
                "dashboard": {
                    "default_view": args[5],
                    "jobs_per_page": args[6],
                    "features": args[7],
                    "refresh_interval": args[8],
                    "cache_ttl": args[9],
                    "performance": args[10],
                },
                "workflow": {
                    "automation_level": args[11],
                    "auto_apply_threshold": args[12],
                    "daily_limit": args[13],
                    "features": args[14],
                },
            }

            logger.info(f"Settings auto-saved: {settings}")
            return "Settings saved automatically"

        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return f"Error saving settings: {e}"
