import pandas as pd
import streamlit as st
from src.core.job_database import get_job_db


def load_job_data(profile_name: str) -> pd.DataFrame:
    try:
        db = get_job_db(profile_name)
        jobs = db.get_jobs(limit=1000)
        if not jobs:
            return pd.DataFrame()
        df = pd.DataFrame(jobs)
        if not df.empty:
            df["created_at"] = pd.to_datetime(df["created_at"])
            df["experience_level"] = df["experience_level"].fillna("Unknown")
            df["match_score"] = df["match_score"].fillna(0)
        return df
    except Exception as e:
        st.error(f"Error loading job data: {e}")
        return pd.DataFrame()
