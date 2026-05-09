"""
Web Dashboard for the Job Application Copilot
Simple Streamlit-based dashboard for monitoring applications
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from storage.database import JobDatabase
from services.analytics import AnalyticsEngine
from models.config import AppConfig


def create_dashboard():
    """Create the web dashboard"""
    # Initialize components
    config = AppConfig()
    database = JobDatabase(str(config.storage.data_dir / config.storage.database_file))
    analytics = AnalyticsEngine(config, database)

    # Set up page
    st.set_page_config(page_title="Job Application Copilot Dashboard", layout="wide")

    # Title
    st.title("🤖 Job Application Copilot Dashboard")

    # Get statistics
    stats = analytics.get_application_statistics()

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Applications", stats.get("total_applications", 0))

    with col2:
        st.metric("Applied", stats.get("applied", 0))

    with col3:
        st.metric("Success Rate", f"{stats.get('success_rate', 0)}%")

    with col4:
        st.metric("Today's Applications", stats.get("today_count", 0))

    # Charts
    st.subheader("📊 Application Trends")

    # Daily trend chart
    trend_data = analytics.get_daily_trend()
    if trend_data:
        trend_df = pd.DataFrame(
            {"Date": list(trend_data.keys()), "Applications": list(trend_data.values())}
        )
        fig = px.line(trend_df, x="Date", y="Applications", title="Daily Applications")
        st.plotly_chart(fig, use_container_width=True)

    # Match score distribution
    st.subheader("🎯 Match Score Distribution")
    distribution_data = analytics.get_match_score_distribution()
    if distribution_data:
        dist_df = pd.DataFrame(
            {
                "Score Range": list(distribution_data.keys()),
                "Count": list(distribution_data.values()),
            }
        )
        fig = px.bar(
            dist_df, x="Score Range", y="Count", title="Match Score Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Recent applications table
    st.subheader("📋 Recent Applications")

    # Get all applications
    all_applications = database.get_all_applications()

    if all_applications:
        # Convert to DataFrame
        app_data = []
        for app in all_applications[:50]:  # Limit to 50 most recent
            app_data.append(
                {
                    "Job Title": app.job_metadata.title,
                    "Company": app.job_metadata.company,
                    "Status": app.status.value,
                    "Match Score": (
                        f"{app.score.match_score:.2f}" if app.score else "N/A"
                    ),
                    "Applied At": (
                        app.applied_at.strftime("%Y-%m-%d %H:%M")
                        if app.applied_at
                        else "N/A"
                    ),
                    "Reason": app.skipped_reason or app.failed_reason or "N/A",
                }
            )

        df = pd.DataFrame(app_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No applications found in database")


if __name__ == "__main__":
    create_dashboard()
