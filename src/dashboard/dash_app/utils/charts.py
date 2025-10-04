"""
Chart generation utilities for the dashboard
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import logging
from src.dashboard.analytics import (
    compute_company_stats,
    compute_location_stats,
    compute_job_metrics,
)

logger = logging.getLogger(__name__)


def create_match_score_distribution(jobs_data):
    """Create histogram of match score distribution"""
    try:
        if not jobs_data:
            return create_empty_chart("No data available")

        df = pd.DataFrame(jobs_data)

        if "match_score" not in df.columns:
            return create_empty_chart("Match score data not available")

        fig = px.histogram(
            df,
            x="match_score",
            nbins=10,
            title="Match Score Distribution",
            labels={"match_score": "Match Score", "count": "Number of Jobs"},
            color_discrete_sequence=["#2E8B57"],
        )

        fig.update_layout(template="plotly_white", height=300, margin=dict(t=40, b=40, l=40, r=40))

        return fig

    except Exception as e:
        logger.error(f"Error creating match score distribution: {e}")
        return create_empty_chart("Error creating chart")


def create_timeline_chart(jobs_data):
    """Create timeline chart showing jobs over time"""
    try:
        if not jobs_data:
            return create_empty_chart("No data available")

        df = pd.DataFrame(jobs_data)

        if "created_at" not in df.columns:
            return create_empty_chart("Date data not available")

        # Convert to datetime and group by date
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["date"] = df["created_at"].dt.date

        timeline_data = df.groupby("date").size().reset_index(name="count")

        fig = px.line(
            timeline_data,
            x="date",
            y="count",
            title="Jobs Timeline",
            labels={"date": "Date", "count": "Number of Jobs"},
            color_discrete_sequence=["#4CAF50"],
        )

        fig.update_traces(mode="lines+markers")
        fig.update_layout(template="plotly_white", height=300, margin=dict(t=40, b=40, l=40, r=40))

        return fig

    except Exception as e:
        logger.error(f"Error creating timeline chart: {e}")
        return create_empty_chart("Error creating chart")


def create_status_pie_chart(jobs_data):
    """Create pie chart showing job status distribution"""
    try:
        if not jobs_data:
            return create_empty_chart("No data available")

        df = pd.DataFrame(jobs_data)

        if "status" not in df.columns:
            return create_empty_chart("Status data not available")

        # Use shared aggregation helper
        job_metrics = compute_job_metrics(df)
        status_counts = job_metrics.status_counts

        colors = {
            "new": "#2196F3",
            "ready_to_apply": "#4CAF50",
            "applied": "#FF9800",
            "needs_review": "#9C27B0",
            "filtered_out": "#757575",
            "interview": "#00BCD4",
            "rejected": "#F44336",
            "offer": "#8BC34A",
        }

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=status_counts.index,
                    values=status_counts.values,
                    marker=dict(
                        colors=[colors.get(status, "#757575") for status in status_counts.index]
                    ),
                )
            ]
        )

        fig.update_layout(
            title="Job Status Distribution",
            template="plotly_white",
            height=300,
            margin=dict(t=40, b=40, l=40, r=40),
        )

        return fig

    except Exception as e:
        logger.error(f"Error creating status pie chart: {e}")
        return create_empty_chart("Error creating chart")


def create_company_bar_chart(jobs_data, top_n=10):
    """Create bar chart showing top companies by job count"""
    try:
        if not jobs_data:
            return create_empty_chart("No data available")

        df = pd.DataFrame(jobs_data)

        if "company" not in df.columns:
            return create_empty_chart("Company data not available")

        # Use shared aggregation helper
        company_stats = compute_company_stats(df, top_n=top_n)
        company_counts = pd.Series(company_stats.counts, index=company_stats.companies)

        fig = px.bar(
            x=company_counts.values,
            y=company_counts.index,
            orientation="h",
            title=f"Top {top_n} Companies by Job Count",
            labels={"x": "Number of Jobs", "y": "Company"},
            color=company_counts.values,
            color_continuous_scale="viridis",
        )

        fig.update_layout(
            template="plotly_white",
            height=400,
            margin=dict(t=40, b=40, l=40, r=40),
            yaxis={"categoryorder": "total ascending"},
        )

        return fig

    except Exception as e:
        logger.error(f"Error creating company bar chart: {e}")
        return create_empty_chart("Error creating chart")


def create_location_chart(jobs_data, top_n=10):
    """Create chart showing job distribution by location"""
    try:
        if not jobs_data:
            return create_empty_chart("No data available")

        df = pd.DataFrame(jobs_data)

        if "location" not in df.columns:
            return create_empty_chart("Location data not available")

        # Use shared aggregation helper
        location_stats = compute_location_stats(df, top_n=top_n)
        location_counts = pd.Series(location_stats.counts, index=location_stats.locations)

        fig = px.bar(
            x=location_counts.index,
            y=location_counts.values,
            title=f"Top {top_n} Locations by Job Count",
            labels={"x": "Location", "y": "Number of Jobs"},
            color=location_counts.values,
            color_continuous_scale="Blues",
        )

        fig.update_layout(
            template="plotly_white",
            height=400,
            margin=dict(t=40, b=40, l=40, r=40),
            xaxis={"tickangle": 45},
        )

        return fig

    except Exception as e:
        logger.error(f"Error creating location chart: {e}")
        return create_empty_chart("Error creating chart")


def create_rcip_cities_chart(jobs_data):
    """Create chart showing RCIP vs Non-RCIP city distribution"""
    try:
        if not jobs_data:
            return create_empty_chart("No data available")

        df = pd.DataFrame(jobs_data)

        if "is_rcip_city" not in df.columns:
            return create_empty_chart("RCIP data not available")

        # Count RCIP vs Non-RCIP cities
        rcip_counts = df["is_rcip_city"].value_counts()
        labels = ["Non-RCIP Cities", "RCIP Cities"]
        values = [rcip_counts.get(0, 0), rcip_counts.get(1, 0)]
        colors = ["#ff7f7f", "#7fbf7f"]  # Red for non-RCIP, Green for RCIP

        fig = px.pie(
            values=values,
            names=labels,
            title="Job Distribution: RCIP vs Non-RCIP Cities",
            color_discrete_sequence=colors,
        )

        fig.update_layout(template="plotly_white", height=400, margin=dict(t=40, b=40, l=40, r=40))

        return fig

    except Exception as e:
        logger.error(f"Error creating RCIP cities chart: {e}")
        return create_empty_chart("Error creating chart")


def create_location_category_chart(jobs_data):
    """Create chart showing job distribution by location category"""
    try:
        if not jobs_data:
            return create_empty_chart("No data available")

        df = pd.DataFrame(jobs_data)

        if "location_category" not in df.columns:
            return create_empty_chart("Location category data not available")

        # Count by location category
        category_counts = df["location_category"].value_counts()

        # Define colors for each category
        color_map = {
            "major_city": "#1f77b4",
            "rcip_city": "#2ca02c",
            "immigration_priority": "#ff7f0e",
            "remote": "#d62728",
            "custom": "#9467bd",
            "unknown": "#8c564b",
        }

        colors = [color_map.get(cat, "#17becf") for cat in category_counts.index]

        fig = px.bar(
            x=category_counts.index,
            y=category_counts.values,
            title="Job Distribution by Location Category",
            labels={"x": "Location Category", "y": "Number of Jobs"},
            color=category_counts.index,
            color_discrete_map=color_map,
        )

        fig.update_layout(
            template="plotly_white",
            height=400,
            margin=dict(t=40, b=40, l=40, r=40),
            xaxis={"tickangle": 45},
        )

        return fig

    except Exception as e:
        logger.error(f"Error creating location category chart: {e}")
        return create_empty_chart("Error creating chart")


def create_salary_distribution(jobs_data):
    """Create salary distribution chart"""
    try:
        if not jobs_data:
            return create_empty_chart("No data available")

        df = pd.DataFrame(jobs_data)

        # Look for salary columns
        salary_cols = [col for col in df.columns if "salary" in col.lower()]
        if not salary_cols:
            return create_empty_chart("Salary data not available")

        # Use the first salary column found
        salary_col = salary_cols[0]
        salary_data = df[salary_col].dropna()

        if len(salary_data) == 0:
            return create_empty_chart("No salary data available")

        fig = px.histogram(
            x=salary_data,
            nbins=15,
            title="Salary Distribution",
            labels={"x": "Salary", "y": "Number of Jobs"},
            color_discrete_sequence=["#FF6B6B"],
        )

        fig.update_layout(template="plotly_white", height=300, margin=dict(t=40, b=40, l=40, r=40))

        return fig

    except Exception as e:
        logger.error(f"Error creating salary distribution: {e}")
        return create_empty_chart("Error creating chart")


def create_application_funnel(jobs_data):
    """Create funnel chart showing application process stages"""
    try:
        if not jobs_data:
            return create_empty_chart("No data available")

        df = pd.DataFrame(jobs_data)

        if "status" not in df.columns:
            return create_empty_chart("Status data not available")

        # Define funnel stages in order
        funnel_stages = ["new", "ready_to_apply", "applied", "interview", "offer"]
        stage_counts = []

        for stage in funnel_stages:
            count = len(df[df["status"] == stage])
            stage_counts.append(count)

        # Only show stages with data
        valid_stages = [
            (stage, count) for stage, count in zip(funnel_stages, stage_counts) if count > 0
        ]

        if not valid_stages:
            return create_empty_chart("No funnel data available")

        stages, counts = zip(*valid_stages)

        fig = go.Figure(go.Funnel(y=list(stages), x=list(counts), textinfo="value+percent initial"))

        fig.update_layout(
            title="Application Funnel",
            template="plotly_white",
            height=400,
            margin=dict(t=40, b=40, l=40, r=40),
        )

        return fig

    except Exception as e:
        logger.error(f"Error creating application funnel: {e}")
        return create_empty_chart("Error creating chart")


def create_skill_demand_chart(jobs_data, top_n=15):
    """Create chart showing most in-demand skills"""
    try:
        if not jobs_data:
            return create_empty_chart("No data available")

        df = pd.DataFrame(jobs_data)

        # Look for skills or requirements column
        skills_cols = [
            col
            for col in df.columns
            if any(keyword in col.lower() for keyword in ["skill", "requirement", "keyword"])
        ]

        if not skills_cols:
            return create_empty_chart("Skills data not available")

        # Extract skills from description or skills column
        all_skills = []
        for col in skills_cols:
            skills_data = df[col].dropna()
            for skills_str in skills_data:
                if isinstance(skills_str, str):
                    # Simple skill extraction (you might want to improve this)
                    skills = [skill.strip() for skill in skills_str.split(",")]
                    all_skills.extend(skills)

        if not all_skills:
            return create_empty_chart("No skills data found")

        skill_counts = pd.Series(all_skills).value_counts().head(top_n)

        fig = px.bar(
            x=skill_counts.values,
            y=skill_counts.index,
            orientation="h",
            title=f"Top {top_n} In-Demand Skills",
            labels={"x": "Frequency", "y": "Skills"},
            color=skill_counts.values,
            color_continuous_scale="Reds",
        )

        fig.update_layout(
            template="plotly_white",
            height=500,
            margin=dict(t=40, b=40, l=40, r=40),
            yaxis={"categoryorder": "total ascending"},
        )

        return fig

    except Exception as e:
        logger.error(f"Error creating skill demand chart: {e}")
        return create_empty_chart("Error creating chart")


def create_empty_chart(message="No data available"):
    """Create an empty chart with a message"""
    fig = go.Figure()

    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        xanchor="center",
        yanchor="middle",
        showarrow=False,
        font=dict(size=16, color="gray"),
    )

    fig.update_layout(
        template="plotly_white",
        height=300,
        margin=dict(t=40, b=40, l=40, r=40),
        xaxis={"visible": False},
        yaxis={"visible": False},
    )

    return fig


def create_kpi_figure(value, title, color="#2E8B57"):
    """Create a KPI figure for display"""
    fig = go.Figure(
        go.Indicator(
            mode="number",
            value=value,
            title={"text": title, "font": {"size": 16}},
            number={"font": {"size": 36, "color": color}},
        )
    )

    fig.update_layout(
        height=120,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig
