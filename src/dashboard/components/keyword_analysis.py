"""
Keyword Analysis Component for AutoJobAgent Dashboard

This module provides comprehensive keyword analysis functionality including:
- Most repeated keywords across jobs
- Skills demand analysis
- Market trend visualization
- Keyword frequency insights
"""

from typing import Dict, List, Any, Optional
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re
import numpy as np


def render_keyword_analysis(df: pd.DataFrame) -> None:
    """
    Render comprehensive keyword analysis dashboard.
    
    Args:
        df: DataFrame containing job data
    """
    st.subheader("🔍 Keyword Analysis & Market Intelligence")
    
    if df.empty:
        st.info("No job data available for keyword analysis")
        return
    
    # Extract keywords from all job descriptions
    all_keywords = extract_keywords_from_jobs(df)
    
    # Display keyword insights
    _display_keyword_insights(all_keywords, df)
    
    # Display market intelligence
    _display_market_intelligence(df)
    
    # Display skills analysis
    _display_skills_analysis(df)


def extract_keywords_from_jobs(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Extract keywords from all job descriptions and titles.
    
    Args:
        df: DataFrame containing job data
        
    Returns:
        Dictionary containing keyword analysis results
    """
    all_text = ""
    
    # Combine all job text
    for _, row in df.iterrows():
        if "title" in row and pd.notna(row["title"]):
            all_text += " " + str(row["title"])
        if "description" in row and pd.notna(row["description"]):
            all_text += " " + str(row["description"])
        if "summary" in row and pd.notna(row["summary"]):
            all_text += " " + str(row["summary"])
    
    # Extract keywords
    keywords = _extract_keywords_from_text(all_text)
    
    # Categorize keywords
    categorized_keywords = _categorize_keywords(keywords)
    
    return {
        "all_keywords": keywords,
        "categorized": categorized_keywords,
        "total_jobs": len(df),
        "text_length": len(all_text)
    }


def _extract_keywords_from_text(text: str, min_length: int = 3, max_keywords: int = 100) -> List[str]:
    """
    Extract keywords from text based on frequency and relevance.
    
    Args:
        text: Text to analyze
        min_length: Minimum word length
        max_keywords: Maximum number of keywords to return
        
    Returns:
        List of keywords sorted by frequency
    """
    if not text:
        return []
    
    # Clean text
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Remove common stop words
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by",
        "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might", "can", "this", "that", "these", "those",
        "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", "my", "your",
        "his", "her", "its", "our", "their", "job", "jobs", "position", "role", "work", "experience",
        "skills", "requirements", "responsibilities", "duties", "qualifications", "preferred",
        "required", "must", "should", "will", "ability", "knowledge", "understanding", "familiarity"
    }
    
    # Split into words and filter
    words = re.findall(r'\b\w+\b', text)
    words = [word for word in words if len(word) >= min_length and word not in stop_words]
    
    # Count frequency
    word_freq = Counter(words)
    
    # Sort by frequency and return top keywords
    sorted_words = word_freq.most_common(max_keywords)
    return [word for word, freq in sorted_words]


def _categorize_keywords(keywords: List[str]) -> Dict[str, List[str]]:
    """
    Categorize keywords into different types.
    
    Args:
        keywords: List of keywords
        
    Returns:
        Dictionary of categorized keywords
    """
    categories = {
        "programming_languages": [],
        "databases": [],
        "cloud_platforms": [],
        "tools_frameworks": [],
        "methodologies": [],
        "soft_skills": [],
        "industries": [],
        "job_titles": [],
        "other_technical": []
    }
    
    # Define keyword categories
    programming_languages = {
        "python", "java", "javascript", "typescript", "c++", "c#", "php", "ruby", "go", "rust",
        "swift", "kotlin", "scala", "r", "matlab", "sql", "html", "css", "scala", "perl"
    }
    
    databases = {
        "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "oracle", "sqlite",
        "dynamodb", "cassandra", "mariadb", "sql server", "nosql", "database"
    }
    
    cloud_platforms = {
        "aws", "azure", "gcp", "google cloud", "amazon web services", "microsoft azure",
        "kubernetes", "docker", "terraform", "jenkins", "gitlab", "github", "ci/cd"
    }
    
    tools_frameworks = {
        "react", "angular", "vue", "node.js", "django", "flask", "spring", "express",
        "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "matplotlib", "seaborn",
        "jupyter", "git", "linux", "bash", "powershell", "excel", "power bi", "tableau",
        "jira", "confluence", "slack", "maven", "gradle", "npm", "yarn"
    }
    
    methodologies = {
        "agile", "scrum", "kanban", "waterfall", "devops", "lean", "six sigma", "tdd", "bdd"
    }
    
    soft_skills = {
        "communication", "leadership", "teamwork", "problem solving", "analytical", "creative",
        "collaboration", "organization", "time management", "attention to detail", "multitasking"
    }
    
    industries = {
        "finance", "healthcare", "technology", "retail", "manufacturing", "consulting",
        "education", "government", "non-profit", "media", "telecommunications", "energy",
        "transportation", "real estate", "insurance", "banking", "e-commerce", "logistics"
    }
    
    job_titles = {
        "analyst", "developer", "engineer", "manager", "specialist", "coordinator",
        "consultant", "architect", "administrator", "scientist", "researcher", "designer"
    }
    
    # Categorize keywords
    for keyword in keywords:
        keyword_lower = keyword.lower()
        
        if keyword_lower in programming_languages:
            categories["programming_languages"].append(keyword)
        elif keyword_lower in databases:
            categories["databases"].append(keyword)
        elif keyword_lower in cloud_platforms:
            categories["cloud_platforms"].append(keyword)
        elif keyword_lower in tools_frameworks:
            categories["tools_frameworks"].append(keyword)
        elif keyword_lower in methodologies:
            categories["methodologies"].append(keyword)
        elif keyword_lower in soft_skills:
            categories["soft_skills"].append(keyword)
        elif keyword_lower in industries:
            categories["industries"].append(keyword)
        elif keyword_lower in job_titles:
            categories["job_titles"].append(keyword)
        else:
            categories["other_technical"].append(keyword)
    
    return categories


def _display_keyword_insights(keyword_data: Dict[str, Any], df: pd.DataFrame) -> None:
    """
    Display keyword insights and visualizations.
    
    Args:
        keyword_data: Keyword analysis data
        df: Original job DataFrame
    """
    st.markdown("### 📊 Keyword Frequency Analysis")
    
    # Top keywords
    top_keywords = keyword_data["all_keywords"][:20]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Keyword frequency bar chart
        if top_keywords:
            keywords, frequencies = zip(*[(kw, freq) for kw, freq in top_keywords])
            
            fig = px.bar(
                x=frequencies,
                y=keywords,
                orientation='h',
                title="Top 20 Most Frequent Keywords",
                labels={'x': 'Frequency', 'y': 'Keywords'}
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Keyword categories pie chart
        categorized = keyword_data["categorized"]
        category_counts = {k: len(v) for k, v in categorized.items() if v}
        
        if category_counts:
            fig = px.pie(
                values=list(category_counts.values()),
                names=list(category_counts.keys()),
                title="Keywords by Category"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Display categorized keywords
    st.markdown("### 🏷️ Keywords by Category")
    
    categorized = keyword_data["categorized"]
    
    cols = st.columns(3)
    col_idx = 0
    
    for category, keywords in categorized.items():
        if keywords:
            with cols[col_idx]:
                category_name = category.replace("_", " ").title()
                st.markdown(f"**{category_name}**")
                for keyword in keywords[:8]:  # Show top 8 per category
                    st.markdown(f"• {keyword}")
                if len(keywords) > 8:
                    st.markdown(f"*... and {len(keywords) - 8} more*")
            
            col_idx = (col_idx + 1) % 3


def _display_market_intelligence(df: pd.DataFrame) -> None:
    """
    Display market intelligence insights.
    
    Args:
        df: Job DataFrame
    """
    st.markdown("### 🏢 Market Intelligence")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Company distribution
        if "company" in df.columns:
            company_counts = df["company"].value_counts().head(10)
            
            fig = px.bar(
                x=company_counts.values,
                y=company_counts.index,
                orientation='h',
                title="Top 10 Companies by Job Postings",
                labels={'x': 'Number of Jobs', 'y': 'Company'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Location distribution
        if "location" in df.columns:
            location_counts = df["location"].value_counts().head(10)
            
            fig = px.bar(
                x=location_counts.values,
                y=location_counts.index,
                orientation='h',
                title="Top 10 Locations by Job Postings",
                labels={'x': 'Number of Jobs', 'y': 'Location'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Experience level analysis
    if "experience_level" in df.columns:
        st.markdown("### 👨‍💼 Experience Level Distribution")
        
        exp_counts = df["experience_level"].value_counts()
        
        fig = px.pie(
            values=exp_counts.values,
            names=exp_counts.index,
            title="Jobs by Experience Level"
        )
        st.plotly_chart(fig, use_container_width=True)


def _display_skills_analysis(df: pd.DataFrame) -> None:
    """
    Display skills analysis and demand insights.
    
    Args:
        df: Job DataFrame
    """
    st.markdown("### 🛠️ Skills Demand Analysis")
    
    # Extract skills from job descriptions
    all_skills = []
    
    for _, row in df.iterrows():
        if "description" in row and pd.notna(row["description"]):
            from src.core.text_utils import extract_keywords
            skills = extract_keywords(str(row["description"]), max_keywords=15)
            all_skills.extend(skills)
    
    if all_skills:
        # Count skill frequency
        skill_counts = Counter(all_skills)
        top_skills = skill_counts.most_common(15)
        
        # Create skills demand chart
        skills, frequencies = zip(*top_skills)
        
        fig = px.bar(
            x=frequencies,
            y=skills,
            orientation='h',
            title="Most Demanded Skills",
            labels={'x': 'Demand (Number of Jobs)', 'y': 'Skills'}
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Skills insights
        st.markdown("### 💡 Skills Insights")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Skills Found", len(skill_counts))
        
        with col2:
            avg_demand = np.mean(list(skill_counts.values()))
            st.metric("Average Skill Demand", f"{avg_demand:.1f}")
        
        with col3:
            max_demand = max(skill_counts.values()) if skill_counts else 0
            st.metric("Highest Demand", max_demand)
        
        # Emerging skills (skills with moderate demand)
        emerging_skills = [skill for skill, count in skill_counts.items() if 2 <= count <= 5]
        
        if emerging_skills:
            st.markdown("**🌱 Emerging Skills (Moderate Demand):**")
            for skill in emerging_skills[:10]:
                st.markdown(f"• {skill} ({skill_counts[skill]} jobs)")


def generate_keyword_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a comprehensive keyword analysis report.
    
    Args:
        df: Job DataFrame
        
    Returns:
        Dictionary containing the analysis report
    """
    keyword_data = extract_keywords_from_jobs(df)
    
    report = {
        "summary": {
            "total_jobs_analyzed": len(df),
            "total_keywords_found": len(keyword_data["all_keywords"]),
            "unique_keywords": len(set(keyword_data["all_keywords"]))
        },
        "top_keywords": keyword_data["all_keywords"][:20],
        "categorized_keywords": keyword_data["categorized"],
        "market_insights": {
            "top_companies": df["company"].value_counts().head(10).to_dict() if "company" in df.columns else {},
            "top_locations": df["location"].value_counts().head(10).to_dict() if "location" in df.columns else {},
            "experience_distribution": df["experience_level"].value_counts().to_dict() if "experience_level" in df.columns else {}
        }
    }
    
    return report 