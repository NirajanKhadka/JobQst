"""
Job Browser Callbacks - LinkedIn-style job browsing with AI intelligence

Handles:
- Loading and filtering jobs from database
- Enriching jobs with AI summaries, keywords, skill gaps
- Displaying similar jobs
- Saving and applying actions
"""

from typing import Dict, List, Optional, Tuple
from dash import Input, Output, State, callback, ctx, html, dcc, ALL
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import pandas as pd

from src.core.duckdb_database import DuckDBJobDatabase
from src.core.user_profile_manager import ModernUserProfileManager
from src.dashboard.dash_app.utils.job_intelligence import (
    enhance_job_with_intelligence,
    find_similar_jobs,
    JobIntelligenceExtractor
)
from src.dashboard.dash_app.components.duplicate_detector import (
    enhance_job_with_duplicate_info,
    create_duplicate_warning_alert
)
from src.dashboard.dash_app.components.enhanced_job_card import create_enhanced_job_card


def register_job_browser_callbacks(app, profile_name: str):
    """
    Register all job browser callbacks
    
    Args:
        app: Dash app instance
        profile_name: Current user profile name
    """
    
    @app.callback(
        [
            Output("browser-total-jobs", "children"),
            Output("browser-high-match", "children"),
            Output("browser-rcip-jobs", "children"),
            Output("browser-remote-jobs", "children"),
            Output("browser-recent-jobs", "children"),
            Output("browser-avg-match", "children")
        ],
        Input("browser-stats-interval", "n_intervals")
    )
    def update_browser_stats(n_intervals):
        """Load job statistics for top stat cards"""
        try:
            db = DuckDBJobDatabase(profile_name=profile_name)
            
            # Total jobs
            total_jobs = db.get_job_count(profile_name)
            
            # High match jobs (>80%)
            high_match_result = db.conn.execute(
                "SELECT COUNT(*) as cnt FROM jobs WHERE fit_score >= 80"
            ).fetchone()
            high_match = high_match_result[0] if high_match_result else 0
            
            # RCIP city jobs
            rcip_result = db.conn.execute(
                "SELECT COUNT(*) as cnt FROM jobs WHERE is_rcip_city = TRUE"
            ).fetchone()
            rcip_jobs = rcip_result[0] if rcip_result else 0
            
            # Remote jobs
            remote_result = db.conn.execute(
                """SELECT COUNT(*) as cnt FROM jobs 
                   WHERE LOWER(location_type) IN ('remote', 'hybrid')
                   OR LOWER(location) LIKE '%remote%'"""
            ).fetchone()
            remote_jobs = remote_result[0] if remote_result else 0
            
            # Recent jobs (last 7 days)
            seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            recent_result = db.conn.execute(
                f"SELECT COUNT(*) as cnt FROM jobs WHERE date_posted >= '{seven_days_ago}'"
            ).fetchone()
            recent_jobs = recent_result[0] if recent_result else 0
            
            # Average match score
            avg_match_result = db.conn.execute(
                "SELECT AVG(fit_score) as avg FROM jobs WHERE fit_score IS NOT NULL"
            ).fetchone()
            avg_match = avg_match_result[0] if avg_match_result and avg_match_result[0] else 0
            
            return (
                str(total_jobs),
                f"{high_match} jobs",
                f"{rcip_jobs} jobs",
                f"{remote_jobs} jobs",
                f"{recent_jobs} this week",
                f"{avg_match:.1f}%"
            )
            
        except Exception as e:
            print(f"Error loading browser stats: {e}")
            return "0", "0 jobs", "0 jobs", "0 jobs", "0 this week", "0%"
    
    
    @app.callback(
        [
            Output("job-browser-container", "children"),
            Output("browser-results-count", "children"),
            Output("browser-duplicate-alert-container", "children")
        ],
        [
            Input("enhanced-search-input", "value"),
            Input("enhanced-sort-dropdown", "value"),
            Input("match-score-range-slider", "value"),
            Input("salary-range-slider", "value"),
            Input("location-type-checkboxes", "value"),
            Input("rcip-filter-checkbox", "value"),
            Input("date-posted-dropdown", "value"),
            Input("clear-advanced-filters-btn", "n_clicks"),
            Input("browser-refresh-btn", "n_clicks")
        ]
    )
    def update_jobs_list(
        search_text: str,
        sort_by: str,
        match_range: List[int],
        salary_range: List[int],
        location_types: List[str],
        rcip_only: List[str],
        date_filter: str,
        clear_clicks: int,
        refresh_clicks: int
    ):
        """Load and filter jobs with enhanced cards and duplicate detection"""
        try:
            # Check if clear button was clicked
            if ctx.triggered_id == "clear-advanced-filters-btn":
                search_text = ""
                sort_by = "match_desc"
                match_range = [0, 100]
                salary_range = [40000, 150000]
                location_types = []
                rcip_only = []
                date_filter = "all"
            
            db = DuckDBJobDatabase(profile_name)
            
            # Build query with filters
            query = "SELECT * FROM jobs WHERE 1=1"
            
            # Search filter
            if search_text:
                search_term = search_text.lower()
                query += f" AND (LOWER(title) LIKE '%{search_term}%' OR LOWER(company) LIKE '%{search_term}%' OR LOWER(job_description) LIKE '%{search_term}%')"
            
            # Match score filter
            if match_range:
                query += f" AND (fit_score >= {match_range[0]} AND fit_score <= {match_range[1]})"
            
            # Salary filter (already in actual dollars from slider)
            if salary_range:
                min_salary = salary_range[0]
                max_salary = salary_range[1]
                query += f" AND ((min_amount >= {min_salary} AND min_amount <= {max_salary}) OR (max_amount >= {min_salary} AND max_amount <= {max_salary}))"
            
            # Location type filter
            if location_types:
                location_conditions = []
                if "remote" in location_types:
                    location_conditions.append("(LOWER(location_type) = 'remote' OR LOWER(location) LIKE '%remote%')")
                if "hybrid" in location_types:
                    location_conditions.append("LOWER(location_type) = 'hybrid'")
                if "onsite" in location_types:
                    location_conditions.append("LOWER(location_type) = 'onsite'")
                if location_conditions:
                    query += f" AND ({' OR '.join(location_conditions)})"
            
            # RCIP filter
            if rcip_only and "rcip_only" in rcip_only:
                query += " AND is_rcip_city = TRUE"
            
            # Date posted filter
            if date_filter and date_filter != "all":
                days_map = {"24h": 1, "7d": 7, "30d": 30}
                days = days_map.get(date_filter, 365)
                cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                query += f" AND date_posted >= '{cutoff_date}'"
            
            # Sort order
            sort_map = {
                "match_desc": "fit_score DESC, date_posted DESC",
                "date_desc": "date_posted DESC",
                "salary_desc": "max_amount DESC NULLS LAST",
                "company_asc": "company ASC",
                "rcip_priority": "is_rcip_city DESC, fit_score DESC"
            }
            order_by = sort_map.get(sort_by, "fit_score DESC, date_posted DESC")
            query += f" ORDER BY {order_by} LIMIT 50"
            
            jobs = db.conn.execute(query).fetchall()
            # Convert to list of dicts
            if jobs:
                columns = [desc[0] for desc in db.conn.description]
                jobs = [dict(zip(columns, row)) for row in jobs]
            else:
                jobs = []
            
            if not jobs:
                return (
                    html.Div(
                        dbc.Alert(
                            [
                                html.I(className="fas fa-search me-2"),
                                "No jobs match your filters. Try adjusting them."
                            ],
                            color="info",
                            className="text-center"
                        ),
                        className="p-5"
                    ),
                    "0 jobs found",
                    html.Div()
                )
            
            # Load user profile for skill matching
            try:
                profile_mgr = ModernUserProfileManager()
                profile = profile_mgr.get_profile(profile_name)
            except:
                profile = None
            
            # Create enhanced job cards with duplicate detection
            job_cards = []
            duplicate_count = 0
            
            for job in jobs:
                # Add duplicate detection info
                job_with_dup = enhance_job_with_duplicate_info(job, jobs)
                if job_with_dup.get("is_duplicate"):
                    duplicate_count += 1
                
                # Create enhanced card (default to 'card' view mode)
                card = create_enhanced_job_card(job_with_dup, view_mode="card")
                job_cards.append(card)
            
            # Results count
            results_text = f"{len(jobs)} jobs found"
            if duplicate_count > 0:
                results_text += f" ({duplicate_count} duplicates detected)"
            
            # Duplicate warning alert
            duplicate_alert = create_duplicate_warning_alert(duplicate_count) if duplicate_count > 0 else html.Div()
            
            return (
                html.Div(job_cards, className="vstack gap-3"),
                results_text,
                duplicate_alert
            )
            
        except Exception as e:
            print(f"Error loading jobs: {e}")
            return (
                html.Div(
                    dbc.Alert(
                        f"Error loading jobs: {str(e)}",
                        color="danger"
                    ),
                    className="p-3"
                ),
                "Error",
                html.Div()
            )
    
    
    @app.callback(
        [
            Output("browser-job-details-modal", "is_open"),
            Output("browser-job-modal-title", "children"),
            Output("browser-job-modal-company", "children"),
            Output("browser-job-modal-location", "children"),
            Output("browser-job-modal-posted", "children"),
            Output("browser-job-modal-match-badge", "children"),
            Output("browser-job-modal-keywords", "children"),
            Output("browser-job-modal-summary", "children"),
            Output("browser-job-modal-skill-gap", "children"),
            Output("browser-job-modal-description", "children"),
            Output("browser-job-modal-similar-jobs", "children"),
            Output("browser-current-job-id", "data")
        ],
        [
            Input({"type": "job-card", "index": ALL}, "n_clicks"),
            Input("browser-job-modal-close", "n_clicks")
        ],
        State("browser-job-details-modal", "is_open"),
        prevent_initial_call=True
    )
    def toggle_job_modal(card_clicks, close_clicks, is_open):
        """Open/close job details modal and populate with job data"""
        
        if ctx.triggered_id == "browser-job-modal-close":
            return False, "", "", "", "", "", "", "", "", "", "", None
        
        # Check if a job card was clicked
        if isinstance(ctx.triggered_id, dict) and ctx.triggered_id.get("type") == "job-card":
            job_id = ctx.triggered_id.get("index")
            
            try:
                db = DuckDBJobDatabase(profile_name=profile_name)
                result = db.conn.execute(f"SELECT * FROM jobs WHERE id = ?", [job_id]).fetchall()
                if result:
                    columns = [desc[0] for desc in db.conn.description]
                    jobs = [dict(zip(columns, row)) for row in result]
                else:
                    jobs = []
                
                if not jobs:
                    return False, "", "", "", "", "", "", "", "", "", ""
                
                job = jobs[0]
                
                # Load profile for skill matching
                try:
                    profile_mgr = ModernUserProfileManager()
                    profile = profile_mgr.get_profile(profile_name)
                except:
                    profile = None
                
                # Enhance job with intelligence
                enhanced_job = enhance_job_with_intelligence(job, profile)
                
                # Find similar jobs
                all_jobs_result = db.conn.execute("SELECT * FROM jobs ORDER BY fit_score DESC LIMIT 100").fetchall()
                if all_jobs_result:
                    columns = [desc[0] for desc in db.conn.description]
                    all_jobs_result = [dict(zip(columns, row)) for row in all_jobs_result]
                else:
                    all_jobs_result = []
                enhanced_all = []
                for j in all_jobs_result:
                    try:
                        enhanced_all.append(enhance_job_with_intelligence(j, profile))
                    except Exception as e:
                        print(f"Error enhancing job: {e}")
                        enhanced_all.append(j)
                
                similar_jobs = find_similar_jobs(enhanced_job, enhanced_all, top_n=3)
                
                # Build modal content
                title = enhanced_job.get("title", enhanced_job.get("job_title", "Unknown Title"))
                company = enhanced_job.get("company", enhanced_job.get("company_name", "Unknown Company"))
                location = f"{enhanced_job.get('location', 'Unknown')} • {enhanced_job.get('location_type', 'On-site')}"
                
                date_posted = enhanced_job.get("date_posted")
                posted_text = f"Posted {date_posted}" if date_posted else "Posted recently"
                
                # Match badge
                fit_score = enhanced_job.get("fit_score")
                if pd.notna(fit_score):
                    badge_color = "success" if fit_score >= 80 else "warning" if fit_score >= 60 else "secondary"
                    match_badge = dbc.Badge(f"{fit_score:.0f}% Match", color=badge_color, className="fs-6")
                else:
                    match_badge = dbc.Badge("Not Rated", color="secondary", className="fs-6")
                
                # Top keywords
                keywords = enhanced_job.get("top_keywords", [])[:8]
                keyword_badges = [
                    dbc.Badge(kw, color="primary", className="me-1 mb-1", pill=True)
                    for kw in keywords
                ]
                
                # AI Summary
                summary = enhanced_job.get("ai_summary", "No summary available.")
                
                # Skill Gap Analysis
                skill_gap = enhanced_job.get("skill_gap_analysis", {})
                matched = skill_gap.get("matched_skills", [])
                missing = skill_gap.get("missing_skills", [])
                match_pct = skill_gap.get("match_percentage", 0)
                
                skill_gap_content = html.Div([
                    html.P(f"You match {match_pct:.0f}% of the required skills", className="fw-bold"),
                    html.Div([
                        html.H6("✅ Your Matching Skills:", className="text-success"),
                        html.Div([
                            dbc.Badge(skill, color="success", className="me-1 mb-1", pill=True)
                            for skill in matched[:10]
                        ]) if matched else html.P("No matched skills identified", className="text-muted")
                    ], className="mb-3"),
                    html.Div([
                        html.H6("📚 Skills to Improve:", className="text-warning"),
                        html.Div([
                            dbc.Badge(skill, color="warning", className="me-1 mb-1", pill=True)
                            for skill in missing[:10]
                        ]) if missing else html.P("Great! You have all the key skills.", className="text-muted")
                    ])
                ])
                
                # Description
                description = enhanced_job.get("description", enhanced_job.get("job_description", "No description available."))
                
                # Similar jobs
                similar_cards = []
                for sim_job in similar_jobs:
                    sim_fit = sim_job.get("fit_score")
                    sim_badge_color = "success" if pd.notna(sim_fit) and sim_fit >= 80 else "secondary"
                    
                    sim_title = sim_job.get("title", sim_job.get("job_title", "Unknown"))
                    sim_company = sim_job.get("company", sim_job.get("company_name", ""))
                    
                    sim_card = dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.H6(sim_title, className="mb-1"),
                                html.Small(sim_company, className="text-muted")
                            ], className="d-flex justify-content-between align-items-start"),
                            html.Div([
                                dbc.Badge(f"{sim_fit:.0f}% Match" if pd.notna(sim_fit) else "Not Rated",
                                         color=sim_badge_color, className="me-2"),
                                html.Small(sim_job.get("location", ""), className="text-muted")
                            ], className="mt-2")
                        ])
                    ], className="mb-2 shadow-sm", style={"cursor": "pointer"})
                    similar_cards.append(sim_card)
                
                similar_content = html.Div(similar_cards) if similar_cards else html.P(
                    "No similar jobs found.", className="text-muted"
                )
                
                return (
                    True,  # Open modal
                    title,
                    company,
                    location,
                    posted_text,
                    match_badge,
                    keyword_badges,
                    summary,
                    skill_gap_content,
                    description,
                    similar_content,
                    job_id  # Store current job ID
                )
                
            except Exception as e:
                print(f"Error loading job details: {e}")
                return False, "", "", "", "", "", "", "", "", "", "", None
        
        return False, "", "", "", "", "", "", "", "", "", "", None
    
    
    @app.callback(
        [
            Output("browser-job-action-feedback", "children"),
            Output("browser-add-to-tracker-btn", "disabled")
        ],
        [
            Input("browser-add-to-tracker-btn", "n_clicks")
        ],
        [
            State("browser-current-job-id", "data"),
            State("browser-job-details-modal", "is_open")
        ],
        prevent_initial_call=True
    )
    def add_job_to_tracker(add_clicks, job_id, modal_open):
        """Add job to application tracker"""
        
        if not add_clicks or not modal_open or not job_id:
            return "", False
        
        try:
            db = DuckDBJobDatabase(profile_name)
            
            # Update job status to 'interested' to add to tracker
            update_query = """
                UPDATE jobs 
                SET application_status = 'interested',
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            db.conn.execute(update_query, [job_id])
            db.conn.commit()
            
            success_msg = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                "Job added to tracker! Check the Job Tracker tab."
            ], color="success", dismissable=True, duration=3000)
            
            return success_msg, True
            
        except Exception as e:
            print(f"Error adding job to tracker: {e}")
            error_msg = dbc.Alert([
                html.I(className="fas fa-exclamation-circle me-2"),
                f"Error: {str(e)}"
            ], color="danger", dismissable=True, duration=4000)
            
            return error_msg, False
    
    
    @app.callback(
        Output("job-modal-open-link", "href"),
        Input("browser-current-job-id", "data"),
        prevent_initial_call=True
    )
    def update_job_link(job_id):
        """Update the job posting link when a job is selected"""
        if not job_id:
            return "#"
        
        try:
            db = DuckDBJobDatabase(profile_name=profile_name)
            result = db.conn.execute("SELECT url FROM jobs WHERE id = ?", [job_id]).fetchone()
            
            if result and result[0]:
                return result[0]
            
            return "#"
        except Exception as e:
            print(f"Error getting job URL: {e}")
            return "#"


def create_enhanced_job_card(job: Dict) -> dbc.Card:
    """
    Create an enhanced job card with AI intelligence
    
    Args:
        job: Enhanced job dictionary with AI features
        
    Returns:
        Dash Bootstrap Card component
    """
    # Extract key fields (handle both field name variations)
    title = job.get("title", job.get("job_title", "Unknown Title"))
    company = job.get("company", job.get("company_name", "Unknown Company"))
    location = job.get("location", "Unknown Location")
    location_type = job.get("location_type", "On-site")
    date_posted = job.get("date_posted", "")
    
    # Match score badge
    fit_score = job.get("fit_score")
    if pd.notna(fit_score):
        badge_color = "success" if fit_score >= 80 else "warning" if fit_score >= 60 else "secondary"
        match_badge = dbc.Badge(f"{fit_score:.0f}% Match", color=badge_color, className="me-2")
    else:
        match_badge = dbc.Badge("Not Rated", color="secondary", className="me-2")
    
    # RCIP badge
    rcip_badge = dbc.Badge("🍁 RCIP", color="success", className="me-2") if job.get("is_rcip_city") else None
    
    # Top keywords - extract from keywords field or job_description
    keywords = job.get("top_keywords", [])
    if not keywords:
        # Try to get from keywords field
        keywords_str = job.get("keywords", "")
        if keywords_str:
            keywords = [k.strip() for k in str(keywords_str).split(",") if k.strip()][:8]
    else:
        keywords = keywords[:8]
    
    keyword_badges = [
        dbc.Badge(kw, color="primary", className="me-1 mb-1", pill=True, 
                 style={"fontSize": "0.75rem"})
        for kw in keywords
    ] if keywords else [html.Small("No keywords available", className="text-muted")]
    
    # AI Summary (first 100 chars)
    summary = job.get("ai_summary", "")
    summary_preview = summary[:100] + "..." if len(summary) > 100 else summary
    
    card = dbc.Card([
        dbc.CardBody([
            # Header
            html.Div([
                html.Div([
                    html.H5(title, className="mb-1"),
                    html.P([
                        html.Strong(company),
                        html.Span(f" • {location} • {location_type}", className="text-muted")
                    ], className="mb-0 small")
                ]),
                html.Div([
                    match_badge,
                    rcip_badge
                ], className="text-end")
            ], className="d-flex justify-content-between align-items-start mb-2"),
            
            # Keywords Section (Prominent)
            html.Div([
                html.Div([
                    html.I(className="fas fa-tags me-2 text-primary"),
                    html.Strong("Top Keywords:", className="text-muted small")
                ], className="mb-1"),
                html.Div(keyword_badges, className="mb-2")
            ], className="mb-2 p-2 bg-light rounded") if keywords else html.Div(),
            
            # AI Summary Preview
            html.P(summary_preview, className="text-muted small mb-2"),
            
            # Footer
            html.Div([
                html.Small(f"Posted {date_posted}" if date_posted else "Posted recently",
                          className="text-muted"),
                html.Div([
                    dbc.Button([
                        html.I(className="fas fa-eye me-1"),
                        "View Details"
                    ], color="primary", size="sm", id={"type": "job-card", "index": job.get("id")})
                ])
            ], className="d-flex justify-content-between align-items-center")
        ])
    ], className="shadow-sm hover-shadow", style={"cursor": "pointer"})
    
    return card
