"""
Enhanced Analytics Callbacks
Standards-compliant callback registration for analytics dashboard
"""

import logging
from typing import List, Dict, Any, Optional
from dash import Input, Output, no_update
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.dashboard.analytics import (
    compute_company_stats,
    compute_location_stats,
    compute_job_metrics,
)

logger = logging.getLogger(__name__)


def register_enhanced_analytics_callbacks(app) -> None:
    """Register all analytics-related callbacks"""

    @app.callback(
        [
            Output("total-jobs-kpi", "children"),
            Output("success-rate-kpi", "children"),
            Output("avg-match-kpi", "children"),
            Output("companies-kpi", "children"),
        ],
        Input("jobs-data-store", "data"),
    )
    def update_kpi_metrics(jobs_data: Optional[List[Dict[str, Any]]]):
        """Update KPI metrics cards"""
        try:
            if not jobs_data:
                return "0", "0%", "0%", "0"

            df = pd.DataFrame(jobs_data)

            # Calculate metrics
            total_jobs = len(df)

            # Success rate (applied/total)
            applied_count = len(df[df.get("application_status", "") == "applied"])
            success_rate = (applied_count / total_jobs * 100) if total_jobs > 0 else 0

            # Average match score
            avg_match_score = df.get("match_score", pd.Series([0])).mean()

            # Unique companies
            companies_count = df.get("company", pd.Series([])).nunique()

            return (
                f"{total_jobs:,}",
                f"{success_rate:.1f}%",
                f"{avg_match_score:.0f}%",
                f"{companies_count:,}",
            )

        except Exception as e:
            logger.error(f"Error updating KPI metrics: {e}")
            return "Error", "Error", "Error", "Error"

    @app.callback(Output("applications-timeline-chart", "figure"), Input("jobs-data-store", "data"))
    def update_applications_timeline(jobs_data: Optional[List[Dict[str, Any]]]):
        """Update applications timeline chart"""
        try:
            if not jobs_data:
                return px.line(title="No data available")

            df = pd.DataFrame(jobs_data)

            if "created_at" in df.columns:
                df["created_at"] = pd.to_datetime(df["created_at"])
                daily_counts = df.groupby(df["created_at"].dt.date).size()

                fig = px.line(
                    x=daily_counts.index,
                    y=daily_counts.values,
                    title="Job Applications Over Time",
                    labels={"x": "Date", "y": "Number of Jobs"},
                )
                fig.update_layout(height=350)
                return fig

            return px.line(title="No date information available")

        except Exception as e:
            logger.error(f"Error creating timeline chart: {e}")
            return px.line(title="Error loading chart")

    @app.callback(Output("top-companies-chart", "figure"), Input("jobs-data-store", "data"))
    def update_top_companies_chart(jobs_data: Optional[List[Dict[str, Any]]]):
        """Update top companies chart"""
        try:
            if not jobs_data:
                return px.bar(title="No data available")

            df = pd.DataFrame(jobs_data)

            if "company" in df.columns:
                # Use shared aggregation helper
                company_stats = compute_company_stats(df, top_n=10)
                company_counts = pd.Series(company_stats.counts, index=company_stats.companies)

                fig = px.bar(
                    x=company_counts.values,
                    y=company_counts.index,
                    orientation="h",
                    title="Top 10 Companies",
                    labels={"x": "Number of Jobs", "y": "Company"},
                )
                fig.update_layout(height=350)
                return fig

            return px.bar(title="No company information available")

        except Exception as e:
            logger.error(f"Error creating companies chart: {e}")
            return px.bar(title="Error loading chart")

    @app.callback(Output("skills-demand-chart", "figure"), Input("jobs-data-store", "data"))
    def update_skills_demand_chart(jobs_data: Optional[List[Dict[str, Any]]]):
        """Update skills demand chart"""
        try:
            if not jobs_data:
                return px.bar(title="No data available")

            # This would analyze job descriptions for skills
            # For now, return a placeholder
            skills = ["Python", "JavaScript", "SQL", "React", "AWS"]
            demand = [45, 38, 42, 28, 35]

            fig = px.bar(
                x=skills,
                y=demand,
                title="Skills in Demand",
                labels={"x": "Skills", "y": "Frequency"},
            )
            fig.update_layout(height=350)
            return fig

        except Exception as e:
            logger.error(f"Error creating skills chart: {e}")
            return px.bar(title="Error loading chart")

    @app.callback(Output("location-distribution-chart", "figure"), Input("jobs-data-store", "data"))
    def update_location_distribution_chart(jobs_data: Optional[List[Dict[str, Any]]]):
        """Update location distribution chart"""
        try:
            if not jobs_data:
                return px.pie(title="No data available")

            df = pd.DataFrame(jobs_data)

            if "location" in df.columns:
                # Use shared aggregation helper
                location_stats = compute_location_stats(df, top_n=8)
                location_counts = pd.Series(location_stats.counts, index=location_stats.locations)

                fig = px.pie(
                    values=location_counts.values,
                    names=location_counts.index,
                    title="Job Locations",
                )
                fig.update_layout(height=350)
                return fig

            return px.pie(title="No location information available")

        except Exception as e:
            logger.error(f"Error creating location chart: {e}")
            return px.pie(title="Error loading chart")

    logger.info("Enhanced analytics callbacks registered successfully")
