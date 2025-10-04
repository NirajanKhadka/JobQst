"""
Ranked Jobs Callbacks - Load and display ranked job opportunities
Handles filtering, sorting, and displaying job cards/lists
"""

import sys
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

import dash
from dash import html, Input, Output, State, callback_context, ALL
import dash_bootstrap_components as dbc

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

try:
    from src.core.user_profile_manager import UserProfileManager
    from src.core.duckdb_database import DuckDBJobDatabase
    from src.dashboard.dash_app.layouts.ranked_jobs_layout import create_job_card
except ImportError as e:
    logger.warning(f"Import warning in ranked jobs callbacks: {e}")


def register_ranked_jobs_callbacks(app):
    """Register all ranked jobs related callbacks"""

    @app.callback(
        [
            Output("total-jobs-count", "children"),
            Output("high-match-count", "children"),
            Output("new-jobs-count", "children"),
        ],
        [Input("auto-refresh-interval", "n_intervals")],
        prevent_initial_call=False,
    )
    def update_ranked_jobs_stats(n_intervals):
        """Update ranked jobs statistics"""
        try:
            # Get current profile - MUST be set when dashboard launches
            if not hasattr(app, "profile_name") or app.profile_name is None:
                logger.error("No profile set on app instance")
                return html.Div("Error: No profile configured", className="text-danger")
            
            current_profile = app.profile_name

            # Get database
            db = DuckDBJobDatabase(profile_name=current_profile)

            # Get total jobs
            total_query = "SELECT COUNT(*) as count FROM jobs"
            total_df = db.conn.execute(total_query).df()
            total = total_df["count"].iloc[0] if not total_df.empty else 0

            # Get high match jobs (>70% fit score)
            high_match_query = """
                SELECT COUNT(*) as count FROM jobs 
                WHERE fit_score > 70
            """
            high_match_df = db.conn.execute(high_match_query).df()
            high_match = high_match_df["count"].iloc[0] if not high_match_df.empty else 0

            # Get new jobs (created in last 24 hours)
            new_jobs_query = """
                SELECT COUNT(*) as count FROM jobs 
                WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '1 day'
            """
            try:
                new_jobs_df = db.conn.execute(new_jobs_query).df()
                new_jobs = new_jobs_df["count"].iloc[0] if not new_jobs_df.empty else 0
            except:
                # Fallback if created_at doesn't exist
                new_jobs = 0

            return str(total), str(high_match), str(new_jobs)

        except Exception as e:
            logger.error(f"Error updating ranked jobs stats: {e}")
            return "0", "0", "0"

    @app.callback(
        Output("ranked-jobs-container", "children"),
        [
            Input("refresh-ranked-jobs", "n_clicks"),
            Input("sort-dropdown", "value"),
            Input("view-mode-select", "value"),
            Input("min-score-slider", "value"),
            Input("date-filter-dropdown", "value"),
            Input("location-type-filter", "value"),
            Input("keyword-search-input", "value"),
            Input("auto-refresh-interval", "n_intervals"),
        ],
        prevent_initial_call=False,
    )
    def update_ranked_jobs_list(
        refresh_clicks, sort_by, view_mode, min_score, date_filter, location_types, keyword, n_intervals
    ):
        """Update ranked jobs list with filters and sorting"""
        try:
            # Get current profile - MUST be set when dashboard launches
            if not hasattr(app, "profile_name") or app.profile_name is None:
                logger.error("No profile set on app instance")
                return []
            
            current_profile = app.profile_name
            db = DuckDBJobDatabase(profile_name=current_profile)

            # Build base query with profile filter
            query = """
                SELECT 
                    id, title, company, location, summary, skills,
                    fit_score, date_posted, url, salary_range,
                    is_rcip_city, is_immigration_priority, city_tags,
                    application_status, created_at
                FROM jobs 
                WHERE profile_name = ?
            """
            params = [current_profile]

            # Apply filters
            conditions = []

            # Min score filter
            if min_score and min_score > 0:
                conditions.append(f"fit_score >= {min_score}")

            # Date filter
            if date_filter and date_filter != "all":
                days = int(date_filter)
                conditions.append(f"date_posted >= CURRENT_DATE - INTERVAL '{days} days'")

            # Keyword search
            if keyword and keyword.strip():
                keyword_safe = keyword.replace("'", "''")
                conditions.append(f"""(
                    title ILIKE '%{keyword_safe}%' OR
                    company ILIKE '%{keyword_safe}%' OR
                    skills ILIKE '%{keyword_safe}%'
                )""")

            # Add conditions to query
            if conditions:
                query += " AND " + " AND ".join(conditions)

            # Apply sorting
            sort_map = {
                "match_desc": "fit_score DESC NULLS LAST",
                "rcip_priority": "is_rcip_city DESC, is_immigration_priority DESC, fit_score DESC",
                "date_desc": "date_posted DESC NULLS LAST",
                "company_asc": "company ASC",
            }
            order_by = sort_map.get(sort_by, "fit_score DESC NULLS LAST")
            query += f" ORDER BY {order_by} LIMIT 50"

            # Execute query with parameters
            df = db.conn.execute(query, params).df()

            if df.empty:
                return dbc.Alert(
                    [
                        html.H4("No Jobs Found", className="alert-heading"),
                        html.P("Try adjusting your filters or run a new job search."),
                        dbc.Button(
                            [html.I(className="fas fa-search me-2"), "Start Job Search"],
                            color="primary",
                            href="#",
                        ),
                    ],
                    color="info",
                    className="text-center",
                )

            # Create job cards
            jobs = []
            for _, job in df.iterrows():
                job_dict = {
                    "id": job["id"],
                    "title": job["title"],
                    "company": job["company"],
                    "location": job["location"],
                    "summary": job.get("summary", ""),
                    "skills": job.get("skills", ""),
                    "fit_score": job.get("fit_score", 0),
                    "date_posted": job.get("date_posted", ""),
                    "url": job.get("url", "#"),
                    "salary_range": job.get("salary_range", ""),
                    "is_rcip_city": job.get("is_rcip_city", False),
                    "is_immigration_priority": job.get("is_immigration_priority", False),
                    "city_tags": job.get("city_tags", ""),
                    "application_status": job.get("application_status", "discovered"),
                }
                jobs.append(create_job_card(job_dict, view_mode=view_mode or "cards"))

            return jobs

        except Exception as e:
            logger.error(f"Error loading ranked jobs: {e}")
            import traceback
            error_details = traceback.format_exc()
            return dbc.Alert(
                [
                    html.H4("Error Loading Jobs", className="alert-heading"),
                    html.P(f"Error: {str(e)}"),
                    html.Details([
                        html.Summary("Technical Details"),
                        html.Pre(error_details, className="text-monospace small mt-2")
                    ])
                ],
                color="danger",
            )

    @app.callback(
        [
            Output("min-score-slider", "value"),
            Output("date-filter-dropdown", "value"),
            Output("location-type-filter", "value"),
            Output("keyword-search-input", "value"),
        ],
        [Input("clear-filters-btn", "n_clicks")],
        prevent_initial_call=True,
    )
    def clear_all_filters(n_clicks):
        """Clear all filters"""
        if n_clicks:
            return 0, "all", ["remote", "hybrid", "onsite"], ""
        return dash.no_update

    @app.callback(
        Output("rcip-stats-container", "children"),
        [Input("auto-refresh-interval", "n_intervals")],
        prevent_initial_call=False,
    )
    def update_rcip_stats(n_intervals):
        """Update RCIP statistics"""
        try:
            from src.dashboard.dash_app.components.rcip_components import create_rcip_stats_card

            # Get current profile - MUST be set when dashboard launches
            if not hasattr(app, "profile_name") or app.profile_name is None:
                logger.error("No profile set on app instance")
                return html.Div("Error: No profile configured", className="text-danger")
            
            current_profile = app.profile_name
            db = DuckDBJobDatabase(profile_name=current_profile)

            # Count RCIP cities
            rcip_query = "SELECT COUNT(*) as count FROM jobs WHERE is_rcip_city = TRUE"
            rcip_df = db.conn.execute(rcip_query).df()
            rcip_count = rcip_df["count"].iloc[0] if not rcip_df.empty else 0

            # Count immigration priority
            priority_query = "SELECT COUNT(*) as count FROM jobs WHERE is_immigration_priority = TRUE"
            priority_df = db.conn.execute(priority_query).df()
            priority_count = priority_df["count"].iloc[0] if not priority_df.empty else 0

            return create_rcip_stats_card(rcip_count, priority_count)

        except Exception as e:
            logger.error(f"Error updating RCIP stats: {e}")
            from src.dashboard.dash_app.components.rcip_components import create_rcip_stats_card
            return create_rcip_stats_card(0, 0)

    # New callbacks for Task 5.2: Home tab analytics
    
    @app.callback(
        [
            Output("home-stats-row", "children"),
            Output("total-jobs-badge", "children"),
        ],
        [Input("auto-refresh-interval", "n_intervals")],
        prevent_initial_call=False,
    )
    def update_home_stats(n_intervals):
        """Update professional stats row on home tab"""
        try:
            from src.dashboard.dash_app.utils.data_loader import DataLoader
            from src.dashboard.dash_app.components.professional_stats import create_stats_row
            
            # Get current profile - MUST be set when dashboard launches
            if not hasattr(app, "profile_name") or app.profile_name is None:
                logger.error("No profile set on app instance")
                return html.Div("Error: No profile configured", className="text-danger")
            
            current_profile = app.profile_name
            data_loader = DataLoader()
            
            # Get enhanced stats
            stats = data_loader.get_enhanced_stats(current_profile)
            
            # Prepare stats data for the component
            stats_data = {
                "total_jobs": {
                    "value": stats.get("total_jobs", 0),
                    "trend": None
                },
                "new_today": {
                    "value": stats.get("new_today", 0),
                    "trend": None
                },
                "high_match": {
                    "value": stats.get("high_match", 0),
                    "trend": None
                },
                "rcip_jobs": {
                    "value": stats.get("rcip_jobs", 0),
                    "trend": None
                }
            }
            
            # Create stats row
            stats_row = create_stats_row(stats_data)
            
            # Update badge
            total_jobs = stats.get("total_jobs", 0)
            badge_text = f"{total_jobs} Jobs"
            
            logger.info(f"Home stats updated successfully: {total_jobs} jobs")
            return stats_row, badge_text
            
        except Exception as e:
            logger.error(f"Error updating home stats: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Return fallback content instead of empty div
            from src.dashboard.dash_app.components.professional_stats import create_stats_row
            fallback_stats = {
                "total_jobs": {"value": 0, "trend": None},
                "new_today": {"value": 0, "trend": None},
                "high_match": {"value": 0, "trend": None},
                "rcip_jobs": {"value": 0, "trend": None}
            }
            return create_stats_row(fallback_stats), "0 Jobs"
    
    @app.callback(
        Output("skill-gap-analysis-container", "children"),
        [Input("auto-refresh-interval", "n_intervals")],
        prevent_initial_call=False,
    )
    def update_skill_gap_analysis(n_intervals):
        """Update skill gap analysis on home tab"""
        try:
            from src.dashboard.dash_app.utils.data_loader import DataLoader
            from src.dashboard.dash_app.utils.skill_analyzer import analyze_skill_gaps
            from src.dashboard.dash_app.components.skill_gap_analyzer import create_skill_gap_analysis_card
            
            # Get current profile - MUST be set when dashboard launches
            if not hasattr(app, "profile_name") or app.profile_name is None:
                logger.error("No profile set on app instance")
                return html.Div("Error: No profile configured", className="text-danger")
            
            current_profile = app.profile_name
            data_loader = DataLoader()
            
            # Get skill analysis data
            skill_data = data_loader.get_skill_analysis_data(current_profile)
            
            if not skill_data:
                logger.warning("No skill data available")
                return html.Div()
            
            user_skills = skill_data.get("user_skills", [])
            jobs = skill_data.get("jobs", [])
            
            # Analyze skill gaps
            skill_gaps = analyze_skill_gaps(user_skills, jobs, top_n=5)
            
            # Create card
            logger.info(f"Skill gap analysis updated: {len(skill_gaps)} gaps found")
            return create_skill_gap_analysis_card(skill_gaps)
            
        except Exception as e:
            logger.error(f"Error updating skill gap analysis: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Return empty div on error
            return html.Div()
    
    @app.callback(
        Output("success-predictor-container", "children"),
        [Input("auto-refresh-interval", "n_intervals")],
        prevent_initial_call=False,
    )
    def update_success_predictor(n_intervals):
        """Update success predictor on home tab"""
        try:
            from src.dashboard.dash_app.utils.data_loader import DataLoader
            from src.dashboard.dash_app.utils.success_calculator import predict_success_by_role
            from src.dashboard.dash_app.components.success_predictor import create_success_predictor_card
            
            # Get current profile - MUST be set when dashboard launches
            if not hasattr(app, "profile_name") or app.profile_name is None:
                logger.error("No profile set on app instance")
                return html.Div("Error: No profile configured", className="text-danger")
            
            current_profile = app.profile_name
            data_loader = DataLoader()
            
            # Get success prediction data
            prediction_data = data_loader.get_success_prediction_data(current_profile)
            
            if not prediction_data:
                logger.warning("No prediction data available")
                return html.Div()
            
            user_skills = prediction_data.get("user_skills", [])
            jobs = prediction_data.get("jobs", [])
            
            # Predict success by role
            predictions = predict_success_by_role(user_skills, jobs)
            
            # Create card
            logger.info(f"Success predictor updated: {len(predictions)} predictions")
            return create_success_predictor_card(predictions)
            
        except Exception as e:
            logger.error(f"Error updating success predictor: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Return empty div on error
            return html.Div()
    
    @app.callback(
        Output("recommended-actions-container", "children"),
        [Input("auto-refresh-interval", "n_intervals")],
        prevent_initial_call=False,
    )
    def update_recommended_actions(n_intervals):
        """Update recommended actions based on current data"""
        try:
            from src.dashboard.dash_app.layouts.ranked_jobs_layout import create_recommended_actions_card
            from src.dashboard.dash_app.utils.data_loader import DataLoader
            
            # Get current profile - MUST be set when dashboard launches
            if not hasattr(app, "profile_name") or app.profile_name is None:
                logger.error("No profile set on app instance")
                return html.Div("Error: No profile configured", className="text-danger")
            
            current_profile = app.profile_name
            data_loader = DataLoader()
            
            # Get stats to generate recommendations
            stats = data_loader.get_enhanced_stats(current_profile)
            skill_data = data_loader.get_skill_analysis_data(current_profile)
            
            actions = []
            
            # Generate smart recommendations based on data
            high_match = stats.get("high_match", 0)
            total_jobs = stats.get("total_jobs", 0)
            new_today = stats.get("new_today", 0)
            
            if high_match > 0:
                actions.append({
                    "title": f"Apply to {high_match} High Match Jobs",
                    "description": f"You have {high_match} jobs with 70%+ match score. These are your best opportunities!",
                    "icon": "fas fa-paper-plane",
                    "priority": "high",
                    "action_type": "apply"
                })
            
            if new_today > 0:
                actions.append({
                    "title": f"Review {new_today} New Jobs Today",
                    "description": "Fresh opportunities just posted. Early applications have better success rates.",
                    "icon": "fas fa-clock",
                    "priority": "high",
                    "action_type": "review"
                })
            
            # Check skill gaps
            if skill_data:
                user_skills = skill_data.get("user_skills", [])
                if len(user_skills) < 5:
                    actions.append({
                        "title": "Add More Skills to Your Profile",
                        "description": "Adding more skills will improve job matching accuracy and find better opportunities.",
                        "icon": "fas fa-user-edit",
                        "priority": "medium",
                        "action_type": "profile"
                    })
            
            if total_jobs < 10:
                actions.append({
                    "title": "Run a New Job Search",
                    "description": "Expand your search to find more opportunities. Try different keywords or locations.",
                    "icon": "fas fa-search-plus",
                    "priority": "medium",
                    "action_type": "search"
                })
            
            # Default action if no specific recommendations
            if not actions:
                actions.append({
                    "title": "Keep Your Profile Updated",
                    "description": "Regularly update your skills and preferences for better job matches.",
                    "icon": "fas fa-sync-alt",
                    "priority": "low",
                    "action_type": "profile"
                })
            
            return create_recommended_actions_card(actions)
            
        except Exception as e:
            logger.error(f"Error updating recommended actions: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return html.Div()

    # Top Companies Widget Callback
    @app.callback(
        Output("top-companies-list", "children"),
        [Input("auto-refresh-interval", "n_intervals")],
        prevent_initial_call=False,
    )
    def update_top_companies(n_intervals):
        """Update top hiring companies widget"""
        try:
            if not hasattr(app, "profile_name") or app.profile_name is None:
                return html.Div("No profile set", className="text-muted")
            
            db = DuckDBJobDatabase(profile_name=app.profile_name)
            
            # Get top companies by job count
            query = """
                SELECT company, COUNT(*) as job_count
                FROM jobs
                WHERE company IS NOT NULL AND company != ''
                GROUP BY company
                ORDER BY job_count DESC
                LIMIT 8
            """
            companies_df = db.conn.execute(query).df()
            
            if companies_df.empty:
                return html.P("No company data available", className="text-muted text-center")
            
            # Create list of companies
            company_items = []
            for idx, row in companies_df.iterrows():
                company_items.append(
                    dbc.ListGroupItem(
                        [
                            html.Div(
                                [
                                    html.Span(row["company"], className="fw-bold"),
                                    dbc.Badge(
                                        f"{row['job_count']} jobs",
                                        color="primary",
                                        className="float-end",
                                        pill=True,
                                    ),
                                ],
                                className="d-flex justify-content-between align-items-center",
                            )
                        ],
                        className="border-0 py-2",
                    )
                )
            
            return dbc.ListGroup(company_items, flush=True)
            
        except Exception as e:
            logger.error(f"Error updating top companies: {e}")
            return html.P(f"Error loading companies", className="text-danger")

    # Top Locations Widget Callback
    @app.callback(
        Output("top-locations-list", "children"),
        [Input("auto-refresh-interval", "n_intervals")],
        prevent_initial_call=False,
    )
    def update_top_locations(n_intervals):
        """Update top locations widget"""
        try:
            if not hasattr(app, "profile_name") or app.profile_name is None:
                return html.Div("No profile set", className="text-muted")
            
            db = DuckDBJobDatabase(profile_name=app.profile_name)
            
            # Get top locations by job count
            query = """
                SELECT location, COUNT(*) as job_count
                FROM jobs
                WHERE location IS NOT NULL AND location != ''
                GROUP BY location
                ORDER BY job_count DESC
                LIMIT 8
            """
            locations_df = db.conn.execute(query).df()
            
            if locations_df.empty:
                return html.P("No location data available", className="text-muted text-center")
            
            # Create list of locations
            location_items = []
            for idx, row in locations_df.iterrows():
                location_items.append(
                    dbc.ListGroupItem(
                        [
                            html.Div(
                                [
                                    html.I(className="fas fa-map-marker-alt me-2 text-primary"),
                                    html.Span(row["location"]),
                                    dbc.Badge(
                                        f"{row['job_count']}",
                                        color="info",
                                        className="float-end",
                                        pill=True,
                                    ),
                                ],
                                className="d-flex justify-content-between align-items-center",
                            )
                        ],
                        className="border-0 py-2",
                    )
                )
            
            return dbc.ListGroup(location_items, flush=True)
            
        except Exception as e:
            logger.error(f"Error updating top locations: {e}")
            return html.P(f"Error loading locations", className="text-danger")

    # Recent Jobs Widget Callback
    @app.callback(
        Output("recent-jobs-list", "children"),
        [Input("auto-refresh-interval", "n_intervals")],
        prevent_initial_call=False,
    )
    def update_recent_jobs(n_intervals):
        """Update recent jobs widget"""
        try:
            if not hasattr(app, "profile_name") or app.profile_name is None:
                return html.Div("No profile set", className="text-muted")
            
            db = DuckDBJobDatabase(profile_name=app.profile_name)
            
            # Get most recent jobs
            query = """
                SELECT id, title, company, location, created_at, fit_score
                FROM jobs
                ORDER BY created_at DESC
                LIMIT 10
            """
            recent_df = db.conn.execute(query).df()
            
            if recent_df.empty:
                return html.P("No recent jobs available", className="text-muted text-center")
            
            # Create list of recent jobs
            job_items = []
            for idx, row in recent_df.iterrows():
                # Format score badge color - handle NaN values
                score = row.get("fit_score")
                if pd.isna(score) or score is None:
                    score = 0
                else:
                    score = float(score)
                
                badge_color = "success" if score >= 70 else "warning" if score >= 50 else "secondary"
                
                job_items.append(
                    dbc.ListGroupItem(
                        [
                            html.Div(
                                [
                                    html.Strong(row["title"], className="d-block"),
                                    html.Small(f"{row['company']} • {row['location']}", className="text-muted"),
                                ],
                                className="mb-1",
                            ),
                            html.Div(
                                [
                                    dbc.Badge(f"{int(score)}% match", color=badge_color, className="me-2"),
                                    html.Small(
                                        pd.to_datetime(row["created_at"]).strftime("%b %d, %H:%M")
                                        if pd.notna(row["created_at"])
                                        else "Recently",
                                        className="text-muted",
                                    ),
                                ]
                            ),
                        ],
                        className="border-0 py-2",
                    )
                )
            
            return dbc.ListGroup(job_items, flush=True)
            
        except Exception as e:
            logger.error(f"Error updating recent jobs: {e}")
            return html.P(f"Error loading recent jobs", className="text-danger")

    # Application Pipeline Widget Callback
    @app.callback(
        [
            Output("pipeline-to-apply", "children"),
            Output("pipeline-applied", "children"),
            Output("pipeline-response", "children"),
        ],
        [Input("auto-refresh-interval", "n_intervals")],
        prevent_initial_call=False,
    )
    def update_application_pipeline(n_intervals):
        """Update application pipeline stats"""
        try:
            if not hasattr(app, "profile_name") or app.profile_name is None:
                return "--", "--", "--"
            
            db = DuckDBJobDatabase(profile_name=app.profile_name)
            
            # Count jobs by application status
            query = """
                SELECT 
                    SUM(CASE WHEN status IN ('new', 'ready_to_apply') THEN 1 ELSE 0 END) as to_apply,
                    SUM(CASE WHEN status = 'applied' THEN 1 ELSE 0 END) as applied,
                    SUM(CASE WHEN status IN ('interviewing', 'offer', 'accepted') THEN 1 ELSE 0 END) as response
                FROM jobs
            """
            stats_df = db.conn.execute(query).df()
            
            if stats_df.empty:
                return "0", "0", "0"
            
            row = stats_df.iloc[0]
            to_apply = int(row.get("to_apply", 0) or 0)
            applied = int(row.get("applied", 0) or 0)
            response = int(row.get("response", 0) or 0)
            
            return str(to_apply), str(applied), str(response)
            
        except Exception as e:
            logger.error(f"Error updating application pipeline: {e}")
            return "0", "0", "0"

    logger.info("Ranked jobs callbacks registered successfully")
