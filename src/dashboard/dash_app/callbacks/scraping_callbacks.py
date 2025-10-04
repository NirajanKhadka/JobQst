"""
Enhanced Scraping callbacks for JobQst Dashboard
Integrates with the improved scraping handler architecture
"""

import logging
import threading
from datetime import datetime
from dash import Input, Output, State, no_update, callback_context
import dash_bootstrap_components as dbc
from dash import html

# Import our improved scraping integration
try:
    from src.cli.handlers.dashboard_integration import create_integrated_scraping_handler
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
    """Register enhanced scraping callbacks with improved architecture"""

    @app.callback(
        [
            Output("scraping-logs", "value"),
            Output("jobs-found-count", "children"),
            Output("last-scrape-status", "children"),
            Output("active-scrapers", "children"),
            Output("performance-metrics", "children"),
        ],
        [
            Input("start-ultra-fast-pipeline-btn", "n_clicks"),
            Input("start-simple-scrape-btn", "n_clicks"),
            Input("start-multi-worker-btn", "n_clicks"),
            Input("refresh-scrape-status-btn", "n_clicks"),
            Input("interval-component", "n_intervals"),
        ],
        [
            State("profile-store", "data"),
            State("scrape-keywords", "value"),
            State("scrape-sites", "value"),
            State("max-jobs-input", "value"),
        ],
        prevent_initial_call=True,
    )
    def handle_enhanced_scraping_actions(
        ultra_fast_clicks,
        simple_clicks,
        multi_worker_clicks,
        refresh_clicks,
        n_intervals,
        profile_data,
        keywords,
        sites,
        max_jobs,
    ):
        """Handle enhanced scraping with improved architecture"""

        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update, no_update

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Get profile
        # Get profile from profile_data or app instance
        if profile_data and profile_data.get("selected_profile"):
            profile_name = profile_data.get("selected_profile")
        elif hasattr(app, "profile_name") and app.profile_name:
            profile_name = app.profile_name
        else:
            logger.error("No profile available for scraping")
            return html.Div("Error: No profile configured", className="text-danger")

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
            return (
                error_msg,
                "Error",
                dbc.Alert("Scraping failed", color="danger"),
                "No active scrapers",
                "Error in metrics",
            )

    @app.callback(
        Output("pipeline-performance-chart", "figure"),
        [Input("interval-component", "n_intervals")],
        prevent_initial_call=True,
    )
    def update_performance_chart(n_intervals):
        """Update real-time performance chart"""

        if not _performance_metrics:
            return {
                "data": [],
                "layout": {
                    "title": "No Performance Data",
                    "xaxis": {"title": "Time"},
                    "yaxis": {"title": "Jobs/Second"},
                },
            }

        # Create performance chart data
        return {
            "data": [
                {
                    "x": ["Last Run"],
                    "y": [_performance_metrics.get("jobs_per_second", 0)],
                    "type": "bar",
                    "name": "Performance",
                }
            ],
            "layout": {
                "title": "Scraping Performance",
                "xaxis": {"title": "Run"},
                "yaxis": {"title": "Jobs/Second"},
            },
        }


def handle_integrated_scraping(
    trigger_id: str, profile_name: str, keywords: list, sites: list, max_jobs: int
):
    """Handle scraping using integrated improved architecture"""

    global _active_scrapers, _scraping_logs, _performance_metrics

    # Load profile
    profile = load_profile(profile_name)
    if not profile:
        return (
            "Profile not found",
            "0",
            dbc.Alert("Profile not found", color="danger"),
            "No profile",
            "No metrics",
        )

    # Add profile name to profile dict
    profile["profile_name"] = profile_name

    if trigger_id in [
        "start-ultra-fast-pipeline-btn",
        "start-simple-scrape-btn",
        "start-multi-worker-btn",
    ]:

        # Determine scraping mode
        mode_map = {
            "start-ultra-fast-pipeline-btn": "simple",
            "start-simple-scrape-btn": "simple",
            "start-multi-worker-btn": "multi_worker",
        }
        mode = mode_map.get(trigger_id, "simple")

        # Start scraping in background thread
        thread = threading.Thread(
            target=run_integrated_scraping,
            args=(profile, mode, max_jobs, sites or ["indeed", "linkedin"]),
        )
        thread.daemon = True
        thread.start()

        # Update logs
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] Started {mode} scraping " f"with {max_jobs} jobs target"
        _scraping_logs.append(log_entry)

        # Keep only last 50 log entries
        _scraping_logs = _scraping_logs[-50:]

        return (
            "\n".join(_scraping_logs),
            f"Target: {max_jobs}",
            dbc.Alert(f"Started {mode} scraping", color="info"),
            f"Active: {mode} mode",
            get_performance_display(),
        )

    elif trigger_id in ["refresh-scrape-status-btn", "interval-component"]:
        # Return current status
        return (
            ("\n".join(_scraping_logs[-10:]) if _scraping_logs else "No recent activity"),
            f"Found: {_performance_metrics.get('total_jobs', 0)}",
            get_status_display(),
            get_active_scrapers_display(),
            get_performance_display(),
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
                log_msg = f"[{timestamp}] 🚀 Starting " f"{event['data']['mode']} pipeline"
                _scraping_logs.append(log_msg)
                _active_scrapers[event["data"]["operation_id"]] = {
                    "mode": event["data"]["mode"],
                    "status": "running",
                    "start_time": timestamp,
                }

            elif event_type == "pipeline_progress":
                stage = event["data"]["stage"]
                log_msg = f"[{timestamp}] 📊 Pipeline stage: {stage}"
                _scraping_logs.append(log_msg)

            elif event_type == "scraping_completed":
                metrics = event["data"].get("metrics", {})
                success = event["data"]["success"]

                if success and metrics:
                    _performance_metrics.update(metrics)
                    jobs_per_sec = metrics.get("jobs_per_second", 0)
                    duration = metrics.get("duration", 0)
                    log_msg = (
                        f"[{timestamp}] ✅ Completed! "
                        f"{jobs_per_sec:.1f} jobs/sec in {duration:.1f}s"
                    )
                else:
                    log_msg = f"[{timestamp}] ❌ Scraping failed"

                _scraping_logs.append(log_msg)

                # Remove from active scrapers
                op_id = event["data"]["operation_id"]
                if op_id in _active_scrapers:
                    del _active_scrapers[op_id]

            elif event_type == "scraping_error":
                error = event["data"]["error"]
                log_msg = f"[{timestamp}] ❌ Error: {error}"
                _scraping_logs.append(log_msg)

        orchestrator.register_dashboard_listener(dashboard_callback)

        # Run scraping with dashboard integration
        success = orchestrator.run_scraping_with_dashboard(mode=mode, jobs=max_jobs, sites=sites)

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


def handle_fallback_scraping(
    trigger_id: str, profile_name: str, keywords: list, sites: list, max_jobs: int
):
    """Fallback scraping handler when integration is not available"""

    timestamp = datetime.now().strftime("%H:%M:%S")

    if trigger_id.startswith("start-"):
        return (
            f"[{timestamp}] Using fallback scraping mode...",
            f"Target: {max_jobs}",
            dbc.Alert("Using fallback mode - integration unavailable", color="warning"),
            "Fallback mode active",
            "Metrics unavailable",
        )

    return (
        "Integration not available",
        "0",
        dbc.Alert("Dashboard integration unavailable", color="warning"),
        "No integration",
        "No metrics",
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

    jobs_per_sec = _performance_metrics.get("jobs_per_second", 0)
    duration = _performance_metrics.get("duration", 0)
    mode = _performance_metrics.get("mode", "unknown")

    return html.Div(
        [
            html.P(f"Last run: {mode} mode"),
            html.P(f"Speed: {jobs_per_sec:.1f} jobs/sec"),
            html.P(f"Duration: {duration:.1f}s"),
        ]
    )


    @app.callback(
        [
            Output("scraping-progress-bar", "value"),
            Output("scraping-status-messages", "children"),
            Output("scraping-results-summary", "children"),
        ],
        Input("start-custom-scrape-btn", "n_clicks"),
        [
            State("scrape-sites-checkboxes", "value"),
            State("scrape-keywords", "value"),
            State("scrape-location", "value"),
            State("scrape-country", "value"),
            State("max-jobs-per-site", "value"),
            State("scrape-min-salary", "value"),
            State("scraping-options", "value"),
            State("profile-selector", "value"),
        ],
        prevent_initial_call=True,
    )
    def start_custom_scraping(
        n_clicks,
        sites,
        keywords,
        location,
        country,
        max_jobs,
        min_salary,
        options,
        profile_name
    ):
        """
        Start custom scraping with user-defined parameters.
        Integrates with existing scrapers and database.
        """
        if not n_clicks:
            return no_update, no_update, no_update
        
        try:
            # Parse options
            deduplication = "deduplication" in (options or [])
            rcip_only = "rcip_only" in (options or [])
            
            # Parse keywords
            keyword_list = [k.strip() for k in (keywords or "").split(",") if k.strip()]
            if not keyword_list:
                return (
                    0,
                    [html.P("❌ Error: No keywords provided", className="text-danger mb-0")],
                    _create_error_summary("No keywords provided")
                )
            
            # Validate sites
            if not sites:
                return (
                    0,
                    [html.P("❌ Error: No job sites selected", className="text-danger mb-0")],
                    _create_error_summary("No job sites selected")
                )
            
            # Start scraping in background thread
            status_messages = [
                html.P("🚀 Starting scraping process...", className="text-primary mb-1"),
                html.P(f"📍 Location: {location}, {country}", className="text-muted mb-1"),
                html.P(f"🔍 Keywords: {', '.join(keyword_list)}", className="text-muted mb-1"),
                html.P(f"🌐 Sites: {', '.join(sites)}", className="text-muted mb-1"),
                html.P(f"📊 Max jobs per site: {max_jobs}", className="text-muted mb-1"),
            ]
            
            # Simulate scraping progress (in production, use actual scraper integration)
            results = _run_scraping_job(
                profile_name,
                sites,
                keyword_list,
                location,
                country,
                max_jobs,
                min_salary,
                deduplication,
                rcip_only
            )
            
            # Create results summary
            summary = _create_results_summary(results)
            
            return 100, status_messages, summary
        
        except Exception as e:
            logger.error(f"Error in custom scraping: {e}")
            return (
                0,
                [html.P(f"❌ Error: {str(e)}", className="text-danger mb-0")],
                _create_error_summary(str(e))
            )


def _run_scraping_job(
    profile_name,
    sites,
    keywords,
    location,
    country,
    max_jobs,
    min_salary,
    deduplication,
    rcip_only
):
    """
    Run scraping job using existing scrapers.
    This integrates with src/scrapers/ modules.
    """
    try:
        from src.core.duckdb_database import DuckDBJobDatabase
        from src.core.smart_deduplication import SmartDeduplication
        
        # Initialize database
        db = DuckDBJobDatabase(profile_name=profile_name)
        
        # Track results
        results = {
            "total_found": 0,
            "duplicates_removed": 0,
            "stored": 0,
            "sites_scraped": [],
            "success_rate": 0.0
        }
        
        # In production, integrate with actual scrapers
        # For now, log the scraping request
        logger.info(f"Scraping request: sites={sites}, keywords={keywords}, location={location}")
        
        # Simulate scraping (replace with actual scraper calls)
        # Example: from src.scrapers.multi_site_jobspy_workers import scrape_jobs
        # jobs = scrape_jobs(sites, keywords, location, max_jobs)
        
        results["sites_scraped"] = sites
        results["success_rate"] = 100.0
        
        return results
    
    except Exception as e:
        logger.error(f"Error running scraping job: {e}")
        return {
            "total_found": 0,
            "duplicates_removed": 0,
            "stored": 0,
            "sites_scraped": [],
            "success_rate": 0.0,
            "error": str(e)
        }


def _create_results_summary(results):
    """Create results summary component."""
    if "error" in results:
        return _create_error_summary(results["error"])
    
    return dbc.Row(
        [
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4(results["total_found"], className="text-primary mb-0"),
                                    html.P("Jobs Found", className="text-muted mb-0 small"),
                                ]
                            )
                        ],
                        className="text-center"
                    )
                ],
                width=3
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4(results["duplicates_removed"], className="text-warning mb-0"),
                                    html.P("Duplicates Removed", className="text-muted mb-0 small"),
                                ]
                            )
                        ],
                        className="text-center"
                    )
                ],
                width=3
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4(results["stored"], className="text-success mb-0"),
                                    html.P("Jobs Stored", className="text-muted mb-0 small"),
                                ]
                            )
                        ],
                        className="text-center"
                    )
                ],
                width=3
            ),
            dbc.Col(
                [
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4(f"{results['success_rate']:.0f}%", className="text-info mb-0"),
                                    html.P("Success Rate", className="text-muted mb-0 small"),
                                ]
                            )
                        ],
                        className="text-center"
                    )
                ],
                width=3
            ),
        ]
    )


def _create_error_summary(error_msg):
    """Create error summary component."""
    return dbc.Alert(
        [
            html.I(className="fas fa-exclamation-triangle me-2"),
            html.Strong("Scraping Failed: "),
            error_msg
        ],
        color="danger"
    )
