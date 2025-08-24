"""
Settings callbacks for JobLens Dashboard
Handle configuration and settings management
"""
import logging
from dash import Input, Output, State

logger = logging.getLogger(__name__)

def register_settings_callbacks(app):
    """Register all settings-related callbacks"""
    
    @app.callback(
        Output('settings-content', 'children'),
        Input('settings-tabs', 'active_tab')
    )
    def render_settings_content(active_tab):
        """Render settings content based on active tab"""
        try:
            from ..layouts.settings_layout import (
                create_processing_settings,
                create_dashboard_settings,
                create_profile_settings,
                create_workflow_settings
            )
            
            if active_tab == "processing-settings":
                return create_processing_settings()
            elif active_tab == "dashboard-settings":
                return create_dashboard_settings()
            elif active_tab == "profile-settings":
                return create_profile_settings()
            elif active_tab == "workflow-settings":
                return create_workflow_settings()
            else:
                return create_processing_settings()
                
        except Exception as e:
            logger.error(f"Error rendering settings content: {e}")
            return f"Error loading settings: {e}"
    
    @app.callback(
        [Output('profile-name', 'value'),
         Output('preferred-locations', 'value'),
         Output('skills-keywords', 'value'),
         Output('salary-range', 'value')],
        Input('profile-selector', 'value')
    )
    def load_profile_settings(selected_profile):
        """Load profile-specific settings"""
        try:
            # In a real implementation, load from profile configuration
            profile_data = {
                'name': selected_profile or 'Nirajan',
                'locations': 'Toronto, Vancouver, Remote',
                'skills': 'Python, Data Science, Machine Learning, AI',
                'salary_range': [80000, 150000]
            }
            
            return (
                profile_data['name'],
                profile_data['locations'],
                profile_data['skills'],
                profile_data['salary_range']
            )
            
        except Exception as e:
            logger.error(f"Error loading profile settings: {e}")
            return "Error", "Error", "Error", [50000, 100000]
    
    @app.callback(
        Output('settings-save-status', 'children'),
        [Input('default-processing-method', 'value'),
         Input('default-batch-size', 'value'),
         Input('min-match-score', 'value'),
         Input('processing-features', 'value'),
         Input('max-concurrent-jobs', 'value'),
         Input('default-view', 'value'),
         Input('jobs-per-page', 'value'),
         Input('dashboard-features', 'value'),
         Input('refresh-interval', 'value'),
         Input('cache-ttl', 'value'),
         Input('performance-options', 'value'),
         Input('automation-level', 'value'),
         Input('auto-apply-threshold', 'value'),
         Input('daily-limit', 'value'),
         Input('workflow-features', 'value')],
        prevent_initial_call=True
    )
    def save_settings(*args):
        """Save all settings (auto-save on change)"""
        try:
            # In a real implementation, save to configuration files
            settings = {
                'processing': {
                    'method': args[0],
                    'batch_size': args[1],
                    'min_match_score': args[2],
                    'features': args[3],
                    'max_concurrent': args[4]
                },
                'dashboard': {
                    'default_view': args[5],
                    'jobs_per_page': args[6],
                    'features': args[7],
                    'refresh_interval': args[8],
                    'cache_ttl': args[9],
                    'performance': args[10]
                },
                'workflow': {
                    'automation_level': args[11],
                    'auto_apply_threshold': args[12],
                    'daily_limit': args[13],
                    'features': args[14]
                }
            }
            
            logger.info(f"Settings auto-saved: {settings}")
            return "Settings saved automatically"
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return f"Error saving settings: {e}"