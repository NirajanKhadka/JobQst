"""
Keyword Cloud Component
Interactive tag cloud for skill-based job filtering
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from typing import List, Dict, Any
from collections import Counter


def extract_keywords_from_jobs(jobs_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Extract and count keywords from job descriptions and titles.

    Args:
        jobs_data: List of job dictionaries

    Returns:
        dict: Keywords with their frequency counts
    """
    all_keywords = []

    # Common tech keywords to prioritize
    tech_keywords = {
        "python",
        "javascript",
        "java",
        "react",
        "node.js",
        "sql",
        "aws",
        "docker",
        "kubernetes",
        "git",
        "django",
        "flask",
        "fastapi",
        "postgresql",
        "mongodb",
        "redis",
        "html",
        "css",
        "typescript",
        "vue.js",
        "angular",
        "express",
        "spring",
        "hibernate",
        "mysql",
        "linux",
        "bash",
        "jenkins",
        "ci/cd",
        "terraform",
        "ansible",
        "machine learning",
        "data science",
        "pandas",
        "numpy",
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "api",
        "rest",
        "graphql",
        "microservices",
        "agile",
        "scrum",
        "devops",
        "cloud",
        "azure",
        "gcp",
        "serverless",
    }

    for job in jobs_data:
        # Extract from existing keywords field if available
        if "keywords" in job and job["keywords"]:
            if isinstance(job["keywords"], list):
                all_keywords.extend(job["keywords"])
            elif isinstance(job["keywords"], str):
                keywords_list = [kw.strip() for kw in job["keywords"].split(",")]
                all_keywords.extend(keywords_list)

        # Extract from job title and description
        text_fields = [
            job.get("title", ""),
            job.get("description", ""),
            job.get("requirements", ""),
        ]

        for text in text_fields:
            if text:
                # Convert to lowercase for matching
                text_lower = text.lower()

                # Find tech keywords in text
                for keyword in tech_keywords:
                    if keyword.lower() in text_lower:
                        all_keywords.append(keyword.title())

    # Count keywords and return top ones
    keyword_counts = Counter(all_keywords)

    # Filter out very common or very rare keywords
    min_count = max(1, len(jobs_data) // 20)  # At least 5% of jobs
    max_count = len(jobs_data) // 2  # No more than 50% of jobs

    filtered_keywords = {
        keyword: count
        for keyword, count in keyword_counts.items()
        if min_count <= count <= max_count and len(keyword) > 2
    }

    sorted_keywords = sorted(filtered_keywords.items(), key=lambda x: x[1], reverse=True)
    return dict(sorted_keywords)


def create_keyword_cloud_panel(jobs_data: List[Dict[str, Any]] = None) -> dbc.Card:
    """
    Create interactive keyword cloud panel for job filtering.

    Args:
        jobs_data: List of job dictionaries to extract keywords from

    Returns:
        dbc.Card: Keyword cloud panel component
    """
    if not jobs_data:
        jobs_data = []

    keywords_with_counts = extract_keywords_from_jobs(jobs_data)

    # Create keyword badges with different sizes based on frequency
    keyword_badges = []
    if keywords_with_counts:
        max_count = max(keywords_with_counts.values())

        # Top 30 keywords
        top_keywords = list(keywords_with_counts.items())[:30]
        for keyword, count in top_keywords:
            # Calculate relative size (0.8 to 1.4 multiplier)
            size_multiplier = 0.8 + (count / max_count) * 0.6

            # Color based on frequency
            if count >= max_count * 0.7:
                color = "primary"
            elif count >= max_count * 0.4:
                color = "info"
            else:
                color = "secondary"

            badge = dbc.Badge(
                [keyword, html.Small(f" ({count})", className="ms-1 opacity-75")],
                color=color,
                className="me-2 mb-2 keyword-cloud-badge",
                style={
                    "fontSize": f"{size_multiplier:.1f}rem",
                    "padding": (
                        f"{0.3 * size_multiplier:.1f}rem " f"{0.6 * size_multiplier:.1f}rem"
                    ),
                    "cursor": "pointer",
                    "transition": "all 0.2s ease",
                },
                id={"type": "keyword-filter-badge", "keyword": keyword},
            )
            keyword_badges.append(badge)

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.Div(
                        [
                            html.H6(
                                [html.I(className="fas fa-tags me-2"), "Skills & Keywords"],
                                className="mb-0 d-inline-block",
                            ),
                            dbc.Badge(
                                f"{len(keywords_with_counts)} skills found",
                                color="light",
                                className="ms-2",
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-times me-1"), "Clear Filters"],
                                color="outline-secondary",
                                size="sm",
                                className="float-end",
                                id="clear-keyword-filters-btn",
                            ),
                        ]
                    )
                ]
            ),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.P(
                                "Click on skills to filter jobs. "
                                "Larger badges appear in more jobs.",
                                className="text-muted small mb-3",
                            ),
                            html.Div(
                                (
                                    keyword_badges
                                    if keyword_badges
                                    else [
                                        html.P(
                                            "No keywords found. Load some jobs to "
                                            "see skill tags.",
                                            className="text-muted text-center py-3",
                                        )
                                    ]
                                ),
                                className="keyword-cloud-container",
                                style={"maxHeight": "200px", "overflowY": "auto"},
                            ),
                            # Hidden storage for selected keywords
                            dcc.Store(id="selected-keywords-store", data=[]),
                        ]
                    )
                ]
            ),
        ],
        className="mb-4",
    )


def create_selected_keywords_display() -> html.Div:
    """Create display for currently selected keyword filters."""
    return html.Div(
        [
            html.Div(id="selected-keywords-display"),
            html.Hr(className="my-2", style={"display": "none"}, id="keywords-divider"),
        ]
    )


def create_keyword_filter_results_summary() -> dbc.Alert:
    """Create summary of filtered results."""
    return dbc.Alert(
        [
            html.Div(id="keyword-filter-summary"),
        ],
        color="info",
        className="mb-3",
        style={"display": "none"},
        id="keyword-filter-alert",
    )


# CSS styles for keyword cloud
KEYWORD_CLOUD_CSS = """
.keyword-cloud-badge:hover {
    transform: scale(1.1) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
}

.keyword-cloud-badge.selected {
    background: linear-gradient(45deg, #28a745, #20c997) !important;
    border-color: #28a745 !important;
    transform: scale(1.05);
}

.keyword-cloud-container {
    line-height: 1.8;
}

.selected-keyword-badge {
    animation: pulse 1s ease-in-out;
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

/* Responsive keyword cloud */
@media (max-width: 768px) {
    .keyword-cloud-badge {
        font-size: 0.8rem !important;
        padding: 0.2rem 0.4rem !important;
    }
}
"""


def get_jobs_matching_keywords(
    jobs_data: List[Dict[str, Any]], selected_keywords: List[str]
) -> List[Dict[str, Any]]:
    """
    Filter jobs that match the selected keywords.

    Args:
        jobs_data: List of job dictionaries
        selected_keywords: List of selected keyword strings

    Returns:
        list: Filtered jobs that match at least one keyword
    """
    if not selected_keywords:
        return jobs_data

    matching_jobs = []
    selected_keywords_lower = [kw.lower() for kw in selected_keywords]

    for job in jobs_data:
        # Check in multiple fields
        text_fields = [
            job.get("title", ""),
            job.get("description", ""),
            job.get("requirements", ""),
            " ".join(job.get("keywords", []) if isinstance(job.get("keywords"), list) else []),
        ]

        job_text = " ".join(text_fields).lower()

        # Check if any selected keyword is in the job text
        if any(keyword in job_text for keyword in selected_keywords_lower):
            # Add match score based on number of matching keywords
            matches = sum(1 for keyword in selected_keywords_lower if keyword in job_text)
            job_copy = job.copy()
            job_copy["keyword_matches"] = matches
            matching_jobs.append(job_copy)

    # Sort by number of keyword matches (descending)
    matching_jobs.sort(key=lambda x: x.get("keyword_matches", 0), reverse=True)

    return matching_jobs
