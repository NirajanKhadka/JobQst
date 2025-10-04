"""
LinkedIn-Style Job Browser Layout
Professional job table with advanced filters, keywords, and AI summaries
"""

import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
import pandas as pd
from typing import Dict

# Import new components
from src.dashboard.dash_app.components.advanced_search import (
    create_enhanced_search_bar,
    create_sort_dropdown,
    create_advanced_filters_panel
)
from src.dashboard.dash_app.components.enhanced_job_card import create_enhanced_job_card
from src.dashboard.dash_app.components.duplicate_detector import create_duplicate_warning_alert


def create_job_browser_layout():
    """Create professional job browser with LinkedIn-style interface"""
    return html.Div([
        # Auto-refresh interval
        dcc.Interval(id='browser-stats-interval', interval=5000, n_intervals=0),
        
        # Professional Header with Actions
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H2([
                            html.I(className="fas fa-search me-3 text-primary"),
                            "Job Browser"
                        ], className="mb-1 fw-bold"),
                        html.P("Professional job search with AI-powered insights", 
                               className="text-muted mb-0")
                    ], width=8),
                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-sync-alt me-2"),
                                "Refresh"
                            ], id="browser-refresh-btn", color="primary", outline=True, size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-download me-2"),
                                "Export"
                            ], id="browser-export-btn", color="success", outline=True, size="sm"),
                        ], className="float-end")
                    ], width=4)
                ])
            ])
        ], className="mb-4 shadow-sm border-0"),

        # Quick Stats Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-briefcase fa-2x text-primary mb-2"),
                            html.H3("--", id="browser-total-jobs", className="mb-0"),
                            html.P("Total Jobs", className="text-muted small mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm border-0")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-star fa-2x text-success mb-2"),
                            html.H3("--", id="browser-high-match", className="mb-0"),
                            html.P("High Matches", className="text-muted small mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm border-0")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-maple-leaf fa-2x text-success mb-2"),
                            html.H3("--", id="browser-rcip-jobs", className="mb-0"),
                            html.P("RCIP Cities", className="text-muted small mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm border-0")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-home fa-2x text-info mb-2"),
                            html.H3("--", id="browser-remote-jobs", className="mb-0"),
                            html.P("Remote Jobs", className="text-muted small mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm border-0")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-clock fa-2x text-secondary mb-2"),
                            html.H3("--", id="browser-recent-jobs", className="mb-0"),
                            html.P("Recent Jobs", className="text-muted small mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm border-0")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-percent fa-2x text-warning mb-2"),
                            html.H3("--", id="browser-avg-match", className="mb-0"),
                            html.P("Avg Match", className="text-muted small mb-0")
                        ], className="text-center")
                    ])
                ], className="shadow-sm border-0")
            ], md=2),
        ], className="mb-4"),

        # Enhanced Search Bar and Sort
        dbc.Row([
            dbc.Col([
                create_enhanced_search_bar()
            ], md=8),
            dbc.Col([
                create_sort_dropdown()
            ], md=4)
        ], className="mb-3"),
        
        # Duplicate Warning Alert
        html.Div(id="browser-duplicate-alert-container", className="mb-3"),
        
        # Search and Filters
        dbc.Row([
            # Left: Advanced Filters Panel
            dbc.Col([
                create_advanced_filters_panel()
            ], md=3),

            # Right: Job Listings with Enhanced Cards
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                html.Span([
                                    html.I(className="fas fa-list me-2"),
                                    html.Span("Job Listings", className="fw-semibold")
                                ])
                            ], width=6),
                            dbc.Col([
                                html.Span(id="browser-results-count", className="text-muted small")
                            ], width=6, className="text-end")
                        ])
                    ]),
                    dbc.CardBody([
                        # Loading State
                        dcc.Loading(
                            id="browser-loading",
                            type="default",
                            children=[
                                # Enhanced Job Cards Container
                                html.Div(
                                    id="job-browser-container",
                                    className="job-browser-scroll",
                                    style={
                                        "maxHeight": "calc(100vh - 350px)",
                                        "overflowY": "auto"
                                    }
                                )
                            ]
                        )
                    ])
                ], className="shadow-sm border-0")
            ], md=9)
        ]),

        # Job Details Modal
        create_job_details_modal(),

        # Hidden stores
        dcc.Store(id="browser-selected-job", storage_type="memory"),
        dcc.Store(id="browser-current-job-id", storage_type="memory"),
    ])


def create_job_details_modal():
    """Create detailed job view modal with AI insights"""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="browser-job-modal-title")),
        dbc.ModalBody([
            # Company and Location
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.I(className="fas fa-building me-2 text-primary"),
                        html.Strong(id="browser-job-modal-company")
                    ])
                ], md=6),
                dbc.Col([
                    html.Div([
                        html.I(className="fas fa-map-marker-alt me-2 text-success"),
                        html.Span(id="browser-job-modal-location")
                    ])
                ], md=6)
            ], className="mb-3"),

            # AI Summary Section (NEW!)
            dbc.Alert([
                html.H5([
                    html.I(className="fas fa-brain me-2"),
                    "AI Summary - What They're Looking For"
                ], className="alert-heading"),
                html.P(id="browser-job-modal-summary", className="mb-0")
            ], color="info", className="mb-3"),

            # Top Keywords Section (NEW!)
            html.Div([
                html.H6([
                    html.I(className="fas fa-tags me-2"),
                    "Top Keywords in Job Description"
                ], className="mb-2"),
                html.Div(id="browser-job-modal-keywords", className="mb-3")
            ]),

            # Skill Match Analysis (NEW!)
            html.Div([
                html.H6([
                    html.I(className="fas fa-chart-pie me-2"),
                    "Your Skill Match"
                ], className="mb-2"),
                html.Div(id="browser-job-modal-skill-gap")
            ], className="mb-3"),

            # Salary and Details
            dbc.Row([
                dbc.Col([
                    html.Label("💰 Salary Range", className="fw-semibold"),
                    html.P(id="job-modal-salary")
                ], md=4),
                dbc.Col([
                    html.Label("📅 Posted", className="fw-semibold"),
                    html.P(id="browser-job-modal-posted")
                ], md=4),
                dbc.Col([
                    html.Label("⭐ Match Score", className="fw-semibold"),
                    html.P(id="browser-job-modal-match-badge")
                ], md=4)
            ], className="mb-3"),

            # Full Description
            html.Hr(),
            html.H6("📋 Full Job Description"),
            html.Div(id="browser-job-modal-description", 
                    style={"maxHeight": "300px", "overflowY": "auto"},
                    className="p-3 bg-light rounded"),
            
            # Similar Jobs Section (NEW!)
            html.Hr(),
            html.Div([
                html.H6([
                    html.I(className="fas fa-link me-2"),
                    "Similar Jobs You Might Like"
                ], className="mb-3"),
                html.Div(id="browser-job-modal-similar-jobs", className="mb-2")
            ])
        ]),
        dbc.ModalFooter([
            html.Div(id="browser-job-action-feedback", className="me-auto"),
            dbc.ButtonGroup([
                dbc.Button([
                    html.I(className="fas fa-check me-2"),
                    "Add to Tracker"
                ], id="browser-add-to-tracker-btn", color="success", outline=True,
                   title="Add this job to your application tracker"),
                dbc.Button([
                    html.I(className="fas fa-paper-plane me-2"),
                    "Mark as Applied"
                ], id="job-modal-apply-btn", color="primary", outline=True),
                html.A(
                    dbc.Button([
                        html.I(className="fas fa-external-link-alt me-2"),
                        "Open Posting"
                    ], color="info", outline=True),
                    id="job-modal-open-link",
                    href="#",
                    target="_blank",
                    style={"textDecoration": "none"}
                ),
                dbc.Button("Close", id="browser-job-modal-close", color="secondary")
            ])
        ])
    ], id="browser-job-details-modal", size="xl", is_open=False)


def create_job_card_enhanced(job: dict) -> dbc.Card:
    """Create enhanced job card with keywords and AI summary"""
    
    # Extract top keywords (if available)
    keywords = job.get("top_keywords", [])[:5]  # Top 5 keywords
    
    # Get AI summary (if available)
    ai_summary = job.get("ai_summary", "")
    
    # Calculate match score display
    fit_score = job.get("fit_score", 0)
    if pd.isna(fit_score) or fit_score is None:
        match_badge = dbc.Badge("Not Rated", color="secondary", className="me-2")
        match_color = "secondary"
    else:
        match_badge = dbc.Badge(f"{fit_score:.0f}% Match", 
                               color="success" if fit_score > 70 else "warning" if fit_score > 50 else "danger",
                               className="me-2")
        match_color = "success" if fit_score > 70 else "warning" if fit_score > 50 else "danger"
    
    return dbc.Card([
        dbc.CardBody([
            # Header Row
            dbc.Row([
                dbc.Col([
                    html.H5(job.get("title", "No Title"), className="mb-1"),
                    html.Div([
                        html.I(className="fas fa-building me-2 text-primary"),
                        html.Strong(job.get("company", "Unknown")),
                        html.Span(" • ", className="mx-2 text-muted"),
                        html.I(className="fas fa-map-marker-alt me-2 text-success"),
                        job.get("location", "Unknown")
                    ], className="text-muted mb-2")
                ], width=9),
                dbc.Col([
                    html.Div([
                        match_badge,
                        dbc.Progress(
                            value=fit_score if not pd.isna(fit_score) else 0,
                            color=match_color,
                            style={"height": "8px"},
                            className="mt-1"
                        )
                    ], className="text-end")
                ], width=3)
            ]),

            # AI Summary Section (Highlighted)
            (dbc.Alert([
                html.Strong("💡 TL;DR: "),
                html.Span(ai_summary[:200] + "..." if len(ai_summary) > 200 else ai_summary)
            ], color="light", className="mb-2 py-2") if ai_summary else html.Div()),

            # Top Keywords
            (html.Div([
                html.Small("🔑 Top Keywords: ", className="text-muted fw-semibold"),
                *[dbc.Badge(kw, color="primary", pill=True, className="me-1") 
                  for kw in keywords]
            ], className="mb-2") if keywords else html.Div()),

            # Tags Row
            html.Div([
                *([dbc.Badge("🍁 RCIP City", color="success", className="me-1")] 
                  if job.get("is_rcip_city") else []),
                *([dbc.Badge("🌟 Immigration Priority", color="info", className="me-1")] 
                  if job.get("is_immigration_priority") else []),
                *([dbc.Badge("🏠 Remote", color="warning", className="me-1")] 
                  if "remote" in str(job.get("location", "")).lower() else []),
                *([dbc.Badge(f"💰 {job.get('salary_range')}", color="dark", className="me-1")] 
                  if job.get("salary_range") else []),
            ], className="mb-2"),

            # Action Buttons
            dbc.ButtonGroup([
                dbc.Button([
                    html.I(className="fas fa-eye me-1"),
                    "View Details"
                ], size="sm", color="primary", outline=True,
                   id={"type": "view-job-browser", "index": job.get("id")}),
                dbc.Button([
                    html.I(className="fas fa-bookmark me-1"),
                    "Save"
                ], size="sm", color="warning", outline=True,
                   id={"type": "save-job-browser", "index": job.get("id")}),
                dbc.Button([
                    html.I(className="fas fa-external-link-alt me-1"),
                    "Apply"
                ], size="sm", color="success",
                   href=job.get("url", "#"), target="_blank")
            ], size="sm", className="w-100")
        ])
    ], className="mb-3 shadow-sm hover-shadow job-card-enhanced")
