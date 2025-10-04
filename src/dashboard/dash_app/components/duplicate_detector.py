"""
Duplicate Detector Component
Visual indicators for duplicate jobs using existing smart_deduplication.py logic
"""

import dash_bootstrap_components as dbc
from dash import html
from typing import Dict, Optional


def create_duplicate_indicator_badge(
    is_duplicate: bool,
    duplicate_of: Optional[str] = None,
    similarity_score: Optional[float] = None
) -> Optional[dbc.Badge]:
    """
    Create duplicate indicator badge.
    
    Args:
        is_duplicate: Whether job is a duplicate
        duplicate_of: ID of original job
        similarity_score: Similarity score (0-1)
    
    Returns:
        dbc.Badge or None if not a duplicate
    """
    if not is_duplicate:
        return None
    
    badge_text = "Duplicate"
    if similarity_score:
        badge_text = f"Duplicate ({similarity_score*100:.0f}% similar)"
    
    return dbc.Badge(
        [html.I(className="fas fa-copy me-1"), badge_text],
        color="danger",
        className="me-1"
    )


def create_duplicate_job_card_styling(
    is_duplicate: bool,
    duplicate_group: Optional[str] = None
) -> Dict[str, str]:
    """
    Create styling for duplicate job cards (border-left color coding).
    
    Args:
        is_duplicate: Whether job is a duplicate
        duplicate_group: Duplicate group identifier
    
    Returns:
        Dict of CSS styles
    """
    if not is_duplicate:
        return {}
    
    # Color code by duplicate group (cycle through colors)
    colors = ["#dc3545", "#fd7e14", "#ffc107", "#20c997", "#17a2b8"]
    
    if duplicate_group:
        # Use hash of group ID to pick color
        color_index = hash(duplicate_group) % len(colors)
        border_color = colors[color_index]
    else:
        border_color = "#dc3545"  # Default red
    
    return {
        "borderLeft": f"5px solid {border_color}",
        "backgroundColor": "#fff5f5"  # Light red background
    }


def create_view_original_link(
    duplicate_of: Optional[str] = None,
    original_title: Optional[str] = None
) -> Optional[html.Div]:
    """
    Create "View Original" link for duplicate jobs.
    
    Args:
        duplicate_of: ID of original job
        original_title: Title of original job
    
    Returns:
        html.Div with link or None
    """
    if not duplicate_of:
        return None
    
    link_text = "View Original Job"
    if original_title:
        link_text = f"View Original: {original_title[:50]}..."
    
    return html.Div([
        html.I(className="fas fa-link me-2 text-primary"),
        html.A(
            link_text,
            href=f"#job-{duplicate_of}",
            className="text-primary",
            id={"type": "view-original-job", "index": duplicate_of}
        )
    ], className="small text-muted mt-2")


def create_duplicate_warning_alert(
    duplicate_count: int,
    show_duplicates: bool = False
) -> Optional[dbc.Alert]:
    """
    Create warning alert for duplicate jobs.
    
    Args:
        duplicate_count: Number of duplicates found
        show_duplicates: Whether duplicates are currently shown
    
    Returns:
        dbc.Alert or None if no duplicates
    """
    if duplicate_count == 0:
        return None
    
    if show_duplicates:
        message = f"Showing {duplicate_count} duplicate job(s). These may be reposted or from multiple sources."
        button_text = "Hide Duplicates"
        button_id = "hide-duplicates-btn"
    else:
        message = f"{duplicate_count} duplicate job(s) hidden. Click to show them."
        button_text = "Show Duplicates"
        button_id = "show-duplicates-btn"
    
    return dbc.Alert([
        html.Div([
            html.I(className="fas fa-exclamation-triangle me-2"),
            html.Strong(message)
        ], className="mb-2"),
        dbc.Button(
            [html.I(className="fas fa-eye me-2"), button_text],
            id=button_id,
            color="warning",
            size="sm",
            outline=True
        )
    ], color="warning", className="mb-3")


def enhance_job_with_duplicate_info(job: Dict, all_jobs: list) -> Dict:
    """
    Enhance job dictionary with duplicate detection information.
    Uses existing smart_deduplication.py logic.
    
    Args:
        job: Job dictionary
        all_jobs: List of all jobs for comparison
    
    Returns:
        Enhanced job dictionary with duplicate info
    """
    try:
        from src.core.smart_deduplication import SmartDeduplicator
        
        deduplicator = SmartDeduplicator()
        
        # Check if this job is a duplicate
        is_duplicate = False
        duplicate_of = None
        similarity_score = None
        duplicate_group = None
        
        # Compare with other jobs
        for other_job in all_jobs:
            if other_job.get("id") == job.get("id"):
                continue
            
            # Use smart deduplication logic
            similarity = deduplicator.calculate_similarity(job, other_job)
            
            if similarity > 0.85:  # High similarity threshold
                is_duplicate = True
                duplicate_of = other_job.get("id")
                similarity_score = similarity
                duplicate_group = f"group_{min(job.get('id', ''), other_job.get('id', ''))}"
                break
        
        # Add duplicate info to job
        job["is_duplicate"] = is_duplicate
        job["duplicate_of"] = duplicate_of
        job["similarity_score"] = similarity_score
        job["duplicate_group"] = duplicate_group
        
        return job
        
    except Exception as e:
        # If deduplication fails, return job as-is
        print(f"Error in duplicate detection: {e}")
        job["is_duplicate"] = False
        return job


def create_duplicate_summary_card(
    total_jobs: int,
    unique_jobs: int,
    duplicate_jobs: int
) -> dbc.Card:
    """
    Create summary card showing duplicate statistics.
    
    Args:
        total_jobs: Total number of jobs
        unique_jobs: Number of unique jobs
        duplicate_jobs: Number of duplicate jobs
    
    Returns:
        dbc.Card with duplicate statistics
    """
    duplicate_percentage = (duplicate_jobs / total_jobs * 100) if total_jobs > 0 else 0
    
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-chart-pie me-2"),
            "Duplicate Detection Summary"
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H3(str(total_jobs), className="mb-0 text-primary"),
                        html.Small("Total Jobs", className="text-muted")
                    ], className="text-center")
                ], width=4),
                dbc.Col([
                    html.Div([
                        html.H3(str(unique_jobs), className="mb-0 text-success"),
                        html.Small("Unique Jobs", className="text-muted")
                    ], className="text-center")
                ], width=4),
                dbc.Col([
                    html.Div([
                        html.H3(str(duplicate_jobs), className="mb-0 text-danger"),
                        html.Small("Duplicates", className="text-muted")
                    ], className="text-center")
                ], width=4)
            ], className="mb-3"),
            
            dbc.Progress(
                value=duplicate_percentage,
                label=f"{duplicate_percentage:.1f}% duplicates",
                color="danger" if duplicate_percentage > 20 else "warning" if duplicate_percentage > 10 else "success",
                className="mb-2"
            ),
            
            html.Small(
                "Duplicates are automatically detected using smart matching algorithms.",
                className="text-muted"
            )
        ])
    ], className="professional-card mb-3")
