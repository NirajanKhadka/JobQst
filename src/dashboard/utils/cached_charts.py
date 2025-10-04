"""Cached chart helpers backed by shared aggregation utilities."""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.dashboard.analytics import (
    compute_company_stats,
    compute_job_metrics,
    compute_location_stats,
    dataframe_fingerprint,
    ensure_dataframe,
)

try:
    from src.dashboard.services.cache_service import cached_operation
except ImportError:  # pragma: no cover - fallback for limited environments

    def cached_operation(cache_key_func=None, ttl=300):
        def decorator(func):
            return func

        return decorator


logger = logging.getLogger(__name__)


def create_empty_chart(message: str = "No data available") -> go.Figure:
    """Return a Plotly figure with an informative placeholder message."""
    figure = go.Figure()
    figure.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        font={"size": 16, "color": "gray"},
        showarrow=False,
    )
    figure.update_layout(
        xaxis={"visible": False},
        yaxis={"visible": False},
        template="plotly_white",
        height=400,
    )
    return figure


def _resolve_fingerprint(jobs_data: Any, override: Optional[str]) -> str:
    if override:
        return override
    dataframe = ensure_dataframe(jobs_data)
    return dataframe_fingerprint(dataframe)


def company_cache_key(
    jobs_data: Any,
    profile_name: str = "default",
    top_n: int = 15,
    data_hash: Optional[str] = None,
    **_: Any,
) -> str:
    fingerprint = _resolve_fingerprint(jobs_data, data_hash)
    return hashlib.md5(
        f"company|profile={profile_name}|top={top_n}|data={fingerprint}".encode()
    ).hexdigest()


def location_cache_key(
    jobs_data: Any,
    profile_name: str = "default",
    top_n: int = 10,
    data_hash: Optional[str] = None,
    **_: Any,
) -> str:
    fingerprint = _resolve_fingerprint(jobs_data, data_hash)
    return hashlib.md5(
        f"location|profile={profile_name}|top={top_n}|data={fingerprint}".encode()
    ).hexdigest()


@cached_operation(cache_key_func=company_cache_key, ttl=300)
def create_cached_company_chart(
    jobs_data: List[Dict[str, Any]],
    profile_name: str = "default",
    top_n: int = 15,
    data_hash: Optional[str] = None,
) -> go.Figure:
    """Generate a cached bar chart showing top companies by job count."""
    try:
        dataframe = ensure_dataframe(jobs_data)
        stats = compute_company_stats(dataframe, top_n=top_n)
        if not stats.companies:
            return create_empty_chart("Company data not available")

        fig = px.bar(
            x=stats.counts,
            y=stats.companies,
            orientation="h",
            title=f"Top {top_n} Companies by Job Count",
            labels={"x": "Number of Jobs", "y": "Company"},
            color=stats.counts,
            color_continuous_scale="viridis",
        )
        fig.update_layout(
            template="plotly_white",
            height=400,
            margin=dict(t=40, b=40, l=40, r=40),
            yaxis={"categoryorder": "total ascending"},
        )
        return fig
    except Exception as error:  # pragma: no cover - defensive logging
        logger.error("Error creating company chart: %s", error)
        return create_empty_chart("Error creating chart")


@cached_operation(cache_key_func=location_cache_key, ttl=300)
def create_cached_location_chart(
    jobs_data: List[Dict[str, Any]],
    profile_name: str = "default",
    top_n: int = 10,
    data_hash: Optional[str] = None,
) -> go.Figure:
    """Generate a cached bar chart showing job distribution by location."""
    try:
        dataframe = ensure_dataframe(jobs_data)
        stats = compute_location_stats(dataframe, top_n=top_n)
        if not stats.locations:
            return create_empty_chart("Location data not available")

        fig = px.bar(
            x=stats.locations,
            y=stats.counts,
            title=f"Top {top_n} Locations by Job Count",
            labels={"x": "Location", "y": "Number of Jobs"},
            color=stats.counts,
            color_continuous_scale="Blues",
        )
        fig.update_layout(
            template="plotly_white",
            height=400,
            margin=dict(t=40, b=40, l=40, r=40),
            xaxis={"tickangle": 45},
        )
        return fig
    except Exception as error:  # pragma: no cover - defensive logging
        logger.error("Error creating location chart: %s", error)
        return create_empty_chart("Error creating chart")


def create_score_distribution_chart(
    score_data: Any,
    profile_name: str = "default",
) -> go.Figure:
    """Render a pie chart representing match score distribution."""
    try:
        if isinstance(score_data, dict):
            ranges = score_data.get("ranges", [])
            counts = score_data.get("counts", [])
        else:
            metrics = compute_job_metrics(score_data)
            ranges = metrics.score_distribution.ranges
            counts = metrics.score_distribution.counts

        if not ranges or not counts:
            return create_empty_chart("No score data available")

        fig = px.pie(
            values=counts,
            names=ranges,
            title="Match Score Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        fig.update_layout(
            template="plotly_white",
            height=400,
            margin=dict(t=40, b=40, l=40, r=40),
        )
        return fig
    except Exception as error:  # pragma: no cover - defensive logging
        logger.error("Error creating score distribution chart: %s", error)
        return create_empty_chart("Error creating chart")


def create_status_overview_chart(
    status_data: Dict[str, int],
    profile_name: str = "default",
) -> go.Figure:
    """Render a bar chart summarising job status counts."""
    try:
        if not status_data:
            return create_empty_chart("No status data available")

        statuses = list(status_data.keys())
        counts = list(status_data.values())
        color_map = {
            "new": "#3498db",
            "ready_to_apply": "#2ecc71",
            "applied": "#f39c12",
            "needs_review": "#e74c3c",
            "rejected": "#95a5a6",
            "interview": "#9b59b6",
        }
        colors = [color_map.get(status, "#34495e") for status in statuses]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=statuses,
                    y=counts,
                    marker_color=colors,
                    text=counts,
                    textposition="auto",
                )
            ]
        )
        fig.update_layout(
            title="Job Status Overview",
            xaxis_title="Status",
            yaxis_title="Number of Jobs",
            template="plotly_white",
            height=400,
            margin=dict(t=40, b=40, l=40, r=40),
        )
        return fig
    except Exception as error:  # pragma: no cover - defensive logging
        logger.error("Error creating status overview chart: %s", error)
        return create_empty_chart("Error creating chart")


def generate_data_hash(jobs_data: List[Dict[str, Any]]) -> str:
    """Return a lightweight hash signature for job collections."""
    if not jobs_data:
        return "empty"

    size_component = len(jobs_data)
    first_id = jobs_data[0].get("id", "<missing>")
    last_id = jobs_data[-1].get("id", "<missing>")
    signature = f"{size_component}:{first_id}:{last_id}"
    return hashlib.md5(signature.encode()).hexdigest()
