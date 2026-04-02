"""Reusable dashboard components and styling."""

import streamlit as st


def apply_custom_css():
    """Apply custom CSS for the dashboard."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');

    .stApp {
        font-family: 'DM Sans', sans-serif;
    }

    .metric-card {
        background: linear-gradient(135deg, #f8f7f4 0%, #ffffff 100%);
        border: 1px solid #e8e6e0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 8px;
    }
    .metric-card .metric-label {
        font-size: 13px;
        color: #888780;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .metric-card .metric-value {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 2px;
    }
    .metric-card .metric-delta {
        font-size: 13px;
        font-weight: 500;
    }
    .delta-positive { color: #639922; }
    .delta-negative { color: #E24B4A; }
    .delta-neutral { color: #888780; }

    .severity-critical { color: #E24B4A; font-weight: 700; }
    .severity-high { color: #D85A30; font-weight: 600; }
    .severity-medium { color: #BA7517; font-weight: 500; }
    .severity-low { color: #378ADD; }
    .severity-info { color: #888780; }

    .section-header {
        font-size: 18px;
        font-weight: 600;
        color: #2C2C2A;
        margin-top: 24px;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 2px solid #534AB7;
    }

    .alert-banner {
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 8px;
        font-size: 14px;
    }
    .alert-critical { background: #FCEBEB; border-left: 4px solid #E24B4A; }
    .alert-high { background: #FAECE7; border-left: 4px solid #D85A30; }
    .alert-warning { background: #FAEEDA; border-left: 4px solid #BA7517; }
    .alert-info { background: #E6F1FB; border-left: 4px solid #378ADD; }

    div[data-testid="stMetric"] {
        background: #f8f7f4;
        border: 1px solid #e8e6e0;
        border-radius: 12px;
        padding: 16px;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
    }

    /* Clickable pillar card icons */
    .pillar-icon-link {
        display: inline-block;
        text-decoration: none;
        font-size: 32px;
        margin-bottom: 8px;
        transition: transform 0.15s;
    }
    .pillar-icon-link:hover {
        transform: scale(1.2);
    }
    </style>
    """, unsafe_allow_html=True)


def metric_card(label: str, value: str, delta: str = "", delta_type: str = "neutral", color: str = "#2C2C2A"):
    """Render a styled metric card."""
    delta_class = f"delta-{delta_type}"
    delta_html = f'<div class="metric-delta {delta_class}">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color: {color};">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str):
    """Render a styled section header."""
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def alert_banner(severity: str, message: str):
    """Render a styled alert banner."""
    css_class = {
        "critical": "alert-critical",
        "high": "alert-high",
        "warning": "alert-warning",
        "medium": "alert-warning",
        "info": "alert-info",
        "low": "alert-info",
    }.get(severity, "alert-info")
    icon = {"critical": "🔴", "high": "🟠", "warning": "🟡", "medium": "🟡", "info": "🔵", "low": "🔵"}.get(severity, "ℹ️")
    st.markdown(f'<div class="alert-banner {css_class}">{icon} {message}</div>', unsafe_allow_html=True)
