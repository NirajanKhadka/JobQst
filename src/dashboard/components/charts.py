# import streamlit as st
# import plotly.express as px
# import pandas as pd

# def render_charts(df: pd.DataFrame):
#     st.subheader("📈 Analytics")
#     if df.empty:
#         st.info("No job data available for charts")
#         return
#     tab1, tab2, tab3, tab4 = st.tabs(["Job Status", "Experience Levels", "Match Scores", "Timeline"])
#     with tab1:
#         if 'status' in df.columns:
#             status_counts = df['status'].value_counts()
#             fig = px.pie(values=status_counts.values, names=status_counts.index, title="Job Status Distribution")
#             st.plotly_chart(fig, use_container_width=True)
#     with tab2:
#         if 'experience_level' in df.columns:
#             exp_counts = df['experience_level'].value_counts()
#             fig = px.bar(x=exp_counts.index, y=exp_counts.values, title="Jobs by Experience Level")
#             st.plotly_chart(fig, use_container_width=True)
#     with tab3:
#         if 'match_score' in df.columns:
#             fig = px.histogram(df, x='match_score', nbins=20, title="Match Score Distribution")
#             st.plotly_chart(fig, use_container_width=True)
#     with tab4:
#         if 'created_at' in df.columns:
#             timeline_data = df.groupby(df['created_at'].dt.date).size().reset_index()
#             timeline_data.columns = ['date', 'count']
#             fig = px.line(timeline_data, x='date', y='count', title="Jobs Created Over Time", markers=True)
#             st.plotly_chart(fig, use_container_width=True)
