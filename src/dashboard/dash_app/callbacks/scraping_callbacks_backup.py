"""
Enhanced Scraping callbacks for JobQst Dashboard
Integrates with the improved scraping handler architecture
"""
import logging
import threading
import asyncio
from datetime import datetime
from dash import Input, Output, State, no_update, callback_context
import dash_bootstrap_components as dbc
from dash import html

# Import our improved scraping integration
try:
    from src.cli.handlers.dashboard_integration import (
        create_integrated_scraping_handler,
        DashboardAPI
    )
    from src.core.user_profile_manager import load_profile
    INTEGRATION_AVAILABLE = True
except ImportError:
    INTEGRATION_AVAILABLE = False
    logging.warning("Dashboard integration not available - using fallback")

logger = logging.getLogger(__name__)

# Global state for real-time updates
_active_scrapers = {}
_scraping_logs = []
_performance_metrics = {}


def register_scraping_callbacks(app):
    """Register enhanced scraping callbacks with improved architecture integration"""
    
    @app.callback(
        [Output('scraping-logs', 'value'),
         Output('jobs-found-count', 'children'),
         Output('last-scrape-status', 'children'),
         Output('active-scrapers', 'children'),
         Output('performance-metrics', 'children')],
        [Input('start-ultra-fast-pipeline-btn', 'n_clicks'),
         Input('start-simple-scrape-btn', 'n_clicks'), 
         Input('start-multi-worker-btn', 'n_clicks'),
         Input('refresh-scrape-status-btn', 'n_clicks'),
         Input('interval-component', 'n_intervals')],
        [State('profile-store', 'data'),
         State('scrape-keywords', 'value'),
         State('scrape-sites', 'value'),
         State('max-jobs-input', 'value')],
        prevent_initial_call=True
    )
    def handle_enhanced_scraping_actions(ultra_fast_clicks, simple_clicks, 
                                       multi_worker_clicks, refresh_clicks,
                                       n_intervals, profile_data, keywords,
                                       sites, max_jobs):
        """Handle enhanced scraping with improved architecture"""
        
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update, no_update
        
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Get profile
        profile_name = profile_data.get('selected_profile', 'Nirajan') if profile_data else 'Nirajan'
        
        try:
            if INTEGRATION_AVAILABLE:
                return handle_integrated_scraping(
                    trigger_id, profile_name, keywords, sites, max_jobs or 20
                )
            else:
                return handle_fallback_scraping(
                    trigger_id, profile_name, keywords, sites, max_jobs or 20
                )
                
        except Exception as e:
            logger.error(f"Scraping callback error: {e}")
            error_msg = f"Error: {str(e)}"
            return (error_msg, "Error", 
                   dbc.Alert("Scraping failed", color="danger"),
                   "No active scrapers", "Error in metrics")

    @app.callback(
        Output('pipeline-performance-chart', 'figure'),
        [Input('interval-component', 'n_intervals')],
        prevent_initial_call=True
    )
    def update_performance_chart(n_intervals):
        """Update real-time performance chart"""
        # This would create a real-time performance visualization
        # using the performance metrics from the integrated scraping
        
        if not _performance_metrics:
            return {
                'data': [],
                'layout': {
                    'title': 'No Performance Data',
                    'xaxis': {'title': 'Time'},
                    'yaxis': {'title': 'Jobs/Second'}
                }
            }
        
        # Create performance chart data
        return {
            'data': [{
                'x': ['Last Run'],
                'y': [_performance_metrics.get('jobs_per_second', 0)],
                'type': 'bar',
                'name': 'Performance'
            }],
            'layout': {
                'title': 'Scraping Performance',
                'xaxis': {'title': 'Run'},
                'yaxis': {'title': 'Jobs/Second'}
            }
        }


def handle_integrated_scraping(trigger_id: str, profile_name: str, 
                             keywords: list, sites: list, max_jobs: int):
    """Handle scraping using integrated improved architecture"""
    
    global _active_scrapers, _scraping_logs, _performance_metrics
    
    # Load profile
    profile = load_profile(profile_name)
    if not profile:
        return ("Profile not found", "0", 
               dbc.Alert("Profile not found", color="danger"),
               "No profile", "No metrics")
    
    # Add profile name to profile dict
    profile["profile_name"] = profile_name
    
    if trigger_id in ['start-ultra-fast-pipeline-btn', 'start-simple-scrape-btn', 
                     'start-multi-worker-btn']:
        
        # Determine scraping mode
        mode_map = {
            'start-ultra-fast-pipeline-btn': 'simple',  # Ultra-fast uses simple mode with optimizations
            'start-simple-scrape-btn': 'simple',
            'start-multi-worker-btn': 'multi_worker'
        }
        mode = mode_map.get(trigger_id, 'simple')
        
        # Start scraping in background thread
        thread = threading.Thread(
            target=run_integrated_scraping,
            args=(profile, mode, max_jobs, sites or ['indeed', 'linkedin'])
        )
        thread.daemon = True
        thread.start()
        
        # Update logs
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] Started {mode} scraping with {max_jobs} jobs target"
        _scraping_logs.append(log_entry)
        
        # Keep only last 50 log entries
        _scraping_logs = _scraping_logs[-50:]
        
        return (
            "\n".join(_scraping_logs),
            f"Target: {max_jobs}",
            dbc.Alert(f"Started {mode} scraping", color="info"),
            f"Active: {mode} mode",
            get_performance_display()
        )
    
    elif trigger_id in ['refresh-scrape-status-btn', 'interval-component']:
        # Return current status
        return (
            "\n".join(_scraping_logs[-10:]) if _scraping_logs else "No recent activity",
            f"Found: {_performance_metrics.get('total_jobs', 0)}",
            get_status_display(),
            get_active_scrapers_display(),
            get_performance_display()
        )
    
    return no_update, no_update, no_update, no_update, no_update


def run_integrated_scraping(profile: dict, mode: str, max_jobs: int, sites: list):
    """Run scraping using the integrated improved architecture"""
    
    global _active_scrapers, _scraping_logs, _performance_metrics
    
    try:
        # Create integrated orchestrator
        orchestrator = create_integrated_scraping_handler(profile)
        
        # Register dashboard callback for real-time updates
        def dashboard_callback(event):
            timestamp = datetime.now().strftime("%H:%M:%S")
            event_type = event.get("type", "unknown")
            
            if event_type == "scraping_started":
                log_msg = f"[{timestamp}] 🚀 Starting {event['data']['mode']} pipeline"
                _scraping_logs.append(log_msg)
                _active_scrapers[event['data']['operation_id']] = {
                    'mode': event['data']['mode'],
                    'status': 'running',
                    'start_time': timestamp
                }
                
            elif event_type == "pipeline_progress":
                stage = event['data']['stage']
                log_msg = f"[{timestamp}] 📊 Pipeline stage: {stage}"
                _scraping_logs.append(log_msg)
                
            elif event_type == "scraping_completed":
                metrics = event['data'].get('metrics', {})
                success = event['data']['success']
                
                if success and metrics:
                    _performance_metrics.update(metrics)
                    jobs_per_sec = metrics.get('jobs_per_second', 0)
                    duration = metrics.get('duration', 0)
                    log_msg = f"[{timestamp}] ✅ Completed! {jobs_per_sec:.1f} jobs/sec in {duration:.1f}s"
                else:
                    log_msg = f"[{timestamp}] ❌ Scraping failed"
                
                _scraping_logs.append(log_msg)
                
                # Remove from active scrapers
                op_id = event['data']['operation_id']
                if op_id in _active_scrapers:
                    del _active_scrapers[op_id]
                    
            elif event_type == "scraping_error":
                error = event['data']['error']
                log_msg = f"[{timestamp}] ❌ Error: {error}"
                _scraping_logs.append(log_msg)
        
        orchestrator.register_dashboard_listener(dashboard_callback)
        
        # Run scraping with dashboard integration
        success = orchestrator.run_scraping_with_dashboard(
            mode=mode, 
            jobs=max_jobs, 
            sites=sites
        )
        
        # Final status update
        timestamp = datetime.now().strftime("%H:%M:%S")
        if success:
            _scraping_logs.append(f"[{timestamp}] 🎉 Scraping session completed successfully!")
        else:
            _scraping_logs.append(f"[{timestamp}] ⚠️ Scraping session completed with issues")
            
    except Exception as e:
        timestamp = datetime.now().strftime("%H:%M:%S")
        _scraping_logs.append(f"[{timestamp}] ❌ Scraping error: {str(e)}")
        logger.error(f"Integrated scraping error: {e}")


def handle_fallback_scraping(trigger_id: str, profile_name: str, 
                           keywords: list, sites: list, max_jobs: int):
    """Fallback scraping handler when integration is not available"""
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if trigger_id.startswith('start-'):
        return (
            f"[{timestamp}] Using fallback scraping mode...",
            f"Target: {max_jobs}",
            dbc.Alert("Using fallback mode - integration unavailable", color="warning"),
            "Fallback mode active",
            "Metrics unavailable"
        )
    
    return (
        "Integration not available",
        "0",
        dbc.Alert("Dashboard integration unavailable", color="warning"),
        "No integration",
        "No metrics"
    )


def get_status_display():
    """Get status display component"""
    if _active_scrapers:
        return dbc.Alert("Scraping in progress", color="info")
    elif _performance_metrics:
        return dbc.Alert("Last scraping completed", color="success")
    else:
        return dbc.Alert("Ready to scrape", color="light")


def get_active_scrapers_display():
    """Get active scrapers display"""
    if not _active_scrapers:
        return "No active scrapers"
    
    active_list = []
    for op_id, info in _active_scrapers.items():
        active_list.append(f"{info['mode']} ({info['status']})")
    
    return f"Active: {', '.join(active_list)}"


def get_performance_display():
    """Get performance metrics display"""
    if not _performance_metrics:
        return "No performance data"
    
    jobs_per_sec = _performance_metrics.get('jobs_per_second', 0)
    duration = _performance_metrics.get('duration', 0)
    mode = _performance_metrics.get('mode', 'unknown')
    
    return html.Div([
        html.P(f"Last run: {mode} mode"),
        html.P(f"Speed: {jobs_per_sec:.1f} jobs/sec"),
        html.P(f"Duration: {duration:.1f}s")
    ])

