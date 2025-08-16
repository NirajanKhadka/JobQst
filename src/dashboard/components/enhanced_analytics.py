"""
Improved Analytics Component for AutoJobAgent Dashboard

This module provides comprehensive analytics including:
- AI analysis metrics and insights
- Keyword frequency analysis
- Market intelligence
- Skills demand analysis
- Application success predictors
"""

from typing import Dict, List, Any, Optional
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import numpy as np


def render_Improved_analytics(df: pd.DataFrame) -> None:
    """
    Render comprehensive analytics dashboard with AI insights.
    
    Args:
        df: DataFrame containing job data with AI analysis
    """
    st.subheader("📈 Improved Analytics & AI Insights")
    
    if df.empty:
        st.info("No job data available for analysis")
        return
    
    # Create tabs for different analytics sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "🤖 AI Analysis", 
        "🔍 Keyword Analysis", 
        "🏢 Market Intelligence", 
        "📊 Skills Demand"
    ])
    
    with tab1:
        _render_ai_analysis_tab(df)
    
    with tab2:
        _render_keyword_analysis_tab(df)
    
    with tab3:
        _render_market_intelligence_tab(df)
    
    with tab4:
        _render_skills_demand_tab(df)


def _render_ai_analysis_tab(df: pd.DataFrame) -> None:
    """
    Render AI analysis insights tab.
    
    Args:
        df: Job DataFrame with AI analysis
    """
    st.markdown("### 🤖 AI Analysis Insights")
    
    # AI Score Distribution
    if "compatibility_score" in df.columns:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_score = df["compatibility_score"].mean()
            st.metric("Average AI Score", f"{avg_score:.1%}")
        
        with col2:
            high_match_count = len(df[df["compatibility_score"] >= 0.8])
            st.metric("High Matches (≥80%)", high_match_count)
        
        with col3:
            good_match_count = len(df[df["compatibility_score"] >= 0.6])
            st.metric("Good Matches (≥60%)", good_match_count)
        
        # AI Score distribution chart
        fig = px.histogram(
            df, 
            x="compatibility_score",
            nbins=20,
            title="AI Compatibility Score Distribution",
            labels={"compatibility_score": "AI Score", "count": "Number of Jobs"}
        )
        fig.add_vline(x=0.6, line_dash="dash", line_color="orange", annotation_text="Good Match Threshold")
        fig.add_vline(x=0.8, line_dash="dash", line_color="green", annotation_text="High Match Threshold")
        st.plotly_chart(fig, use_container_width=True)
        
        # Top matches by AI score
        st.markdown("### 🎯 Top AI Matches")
        top_matches = df.nlargest(10, "compatibility_score")[["title", "company", "compatibility_score"]]
        
        for idx, row in top_matches.iterrows():
            score = row["compatibility_score"]
            color = "🟢" if score >= 0.8 else "🟡" if score >= 0.6 else "🔴"
            st.markdown(f"{color} **{row['title']}** at {row['company']} - Score: {score:.1%}")
    
    # AI Analysis Details
    if "llm_analysis" in df.columns:
        st.markdown("### 📋 AI Analysis Breakdown")
        
        # Extract analysis data
        experience_matches = []
        location_matches = []
        cultural_fits = []
        growth_potentials = []
        
        for _, row in df.iterrows():
            if "llm_analysis" in row and row["llm_analysis"]:
                analysis = row["llm_analysis"]
                if "experience_match" in analysis:
                    experience_matches.append(analysis["experience_match"])
                if "location_match" in analysis:
                    location_matches.append(analysis["location_match"])
                if "cultural_fit" in analysis:
                    cultural_fits.append(analysis["cultural_fit"])
                if "growth_potential" in analysis:
                    growth_potentials.append(analysis["growth_potential"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            if experience_matches:
                exp_counts = Counter(experience_matches)
                fig = px.pie(
                    values=list(exp_counts.values()),
                    names=list(exp_counts.keys()),
                    title="Experience Match Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            if location_matches:
                loc_counts = Counter(location_matches)
                fig = px.pie(
                    values=list(loc_counts.values()),
                    names=list(loc_counts.keys()),
                    title="Location Match Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if cultural_fits:
                avg_cultural = np.mean(cultural_fits)
                st.metric("Average Cultural Fit", f"{avg_cultural:.1%}")
                
                fig = px.histogram(
                    x=cultural_fits,
                    title="Cultural Fit Distribution",
                    labels={"x": "Cultural Fit Score", "count": "Number of Jobs"}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            if growth_potentials:
                avg_growth = np.mean(growth_potentials)
                st.metric("Average Growth Potential", f"{avg_growth:.1%}")
                
                fig = px.histogram(
                    x=growth_potentials,
                    title="Growth Potential Distribution",
                    labels={"x": "Growth Potential Score", "count": "Number of Jobs"}
                )
                st.plotly_chart(fig, use_container_width=True)


def _render_keyword_analysis_tab(df: pd.DataFrame) -> None:
    """
    Render keyword analysis tab.
    
    Args:
        df: Job DataFrame
    """
    st.markdown("### 🔍 Keyword Frequency Analysis")
    
    # Extract keywords from all job descriptions
    all_keywords = _extract_keywords_from_jobs(df)
    
    if all_keywords:
        # Top keywords chart
        top_keywords = all_keywords[:20]
        keywords, frequencies = zip(*top_keywords)
        
        fig = px.bar(
            x=frequencies,
            y=keywords,
            orientation='h',
            title="Top 20 Most Frequent Keywords",
            labels={'x': 'Frequency', 'y': 'Keywords'}
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Keyword categories
        categorized = _categorize_keywords([kw for kw, _ in all_keywords])
        
        st.markdown("### 🏷️ Keywords by Category")
        
        cols = st.columns(3)
        col_idx = 0
        
        for category, keywords in categorized.items():
            if keywords:
                with cols[col_idx]:
                    category_name = category.replace("_", " ").title()
                    st.markdown(f"**{category_name}**")
                    for keyword in keywords[:8]:
                        st.markdown(f"• {keyword}")
                    if len(keywords) > 8:
                        st.markdown(f"*... and {len(keywords) - 8} more*")
                
                col_idx = (col_idx + 1) % 3


def _render_market_intelligence_tab(df: pd.DataFrame) -> None:
    """
    Render market intelligence tab.
    
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
    
    # Salary analysis
    if "salary_range" in df.columns:
        st.markdown("### 💰 Salary Range Analysis")
        
        # Extract salary ranges
        salary_ranges = []
        for salary in df["salary_range"]:
            if pd.notna(salary) and isinstance(salary, str):
                if "$" in salary:
                    salary_ranges.append(salary)
        
        if salary_ranges:
            salary_counts = Counter(salary_ranges)
            top_salaries = salary_counts.most_common(10)
            
            if top_salaries:
                ranges, counts = zip(*top_salaries)
                
                fig = px.bar(
                    x=counts,
                    y=ranges,
                    orientation='h',
                    title="Most Common Salary Ranges",
                    labels={'x': 'Number of Jobs', 'y': 'Salary Range'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)


def _render_skills_demand_tab(df: pd.DataFrame) -> None:
    """
    Render skills demand analysis tab.
    
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
        
        # Emerging skills
        emerging_skills = [skill for skill, count in skill_counts.items() if 2 <= count <= 5]
        
        if emerging_skills:
            st.markdown("**🌱 Emerging Skills (Moderate Demand):**")
            for skill in emerging_skills[:10]:
                st.markdown(f"• {skill} ({skill_counts[skill]} jobs)")


def _extract_keywords_from_jobs(df: pd.DataFrame) -> List[tuple]:
    """
    Extract keywords from all job descriptions and titles.
    
    Args:
        df: DataFrame containing job data
        
    Returns:
        List of (keyword, frequency) tuples
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
    
    return keywords


def _extract_keywords_from_text(text: str, min_length: int = 3, max_keywords: int = 100) -> List[tuple]:
    """
    Extract keywords from text based on frequency and relevance.
    
    Args:
        text: Text to analyze
        min_length: Minimum word length
        max_keywords: Maximum number of keywords to return
        
    Returns:
        List of (keyword, frequency) tuples
    """
    if not text:
        return []
    
    import re
    
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
    return sorted_words


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