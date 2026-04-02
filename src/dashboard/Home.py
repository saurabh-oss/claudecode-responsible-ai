"""Responsible AI Governance Platform — Main Dashboard."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from src.data.database import query_df, get_db_path, init_db
from src.dashboard.components import apply_custom_css, metric_card, section_header, alert_banner
from src.utils.helpers import TEAM_COLORS, compliance_color, format_number, format_currency

# --- Page Config ---
st.set_page_config(
    page_title="Responsible AI Governance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_css()

# --- Check DB ---
if not get_db_path().exists():
    st.error("⚠️ Database not found. Please run `python scripts/seed_data.py` first.")
    st.stop()

# --- Sidebar ---
# Sprint filter
sprints = query_df("SELECT * FROM sprints ORDER BY number")
sprint_names = [s["name"] for s in sprints]
selected_sprint = st.sidebar.selectbox("Sprint", sprint_names, index=len(sprint_names) - 1)
sprint_id = next(s["id"] for s in sprints if s["name"] == selected_sprint)

# Team filter
teams = query_df("SELECT * FROM teams ORDER BY name")
team_names = ["All Teams"] + [t["name"] for t in teams]
selected_team = st.sidebar.selectbox("Team", team_names)

st.sidebar.markdown("---")
st.sidebar.caption("PoC v1.0 • Open Source Stack")

# --- Helper to apply team filter ---
def team_filter_sql(prefix: str = "") -> tuple[str, tuple]:
    if selected_team == "All Teams":
        return "", ()
    team_id = next(t["id"] for t in teams if t["name"] == selected_team)
    col = f"{prefix}team_id" if prefix else "team_id"
    return f" AND {col} = ?", (team_id,)


# === MAIN CONTENT ===
st.title("🛡️ Responsible AI Governance Platform")
st.caption("Enterprise-grade observability for AI-assisted software engineering")

# --- Executive Summary Row ---
tf_sql, tf_params = team_filter_sql()

# KPI: Overall compliance
comp_data = query_df(
    f"SELECT AVG(score) as avg_score FROM compliance_scores WHERE sprint_id = ?{tf_sql}",
    (sprint_id, *tf_params),
)
avg_compliance = comp_data[0]["avg_score"] if comp_data and comp_data[0]["avg_score"] else 0

# KPI: Total violations
viol_data = query_df(
    f"SELECT COUNT(*) as cnt FROM policy_violations WHERE sprint_id = ?{tf_sql}",
    (sprint_id, *tf_params),
)
total_violations = viol_data[0]["cnt"] if viol_data else 0

# KPI: Token cost
cost_data = query_df(
    f"SELECT SUM(cost_usd) as total_cost FROM token_usage WHERE sprint_id = ?{tf_sql}",
    (sprint_id, *tf_params),
)
total_cost = cost_data[0]["total_cost"] if cost_data and cost_data[0]["total_cost"] else 0

# KPI: Adoption rate
adopt_data = query_df(
    f"SELECT AVG(adoption_rate_pct) as avg_adopt FROM adoption_metrics WHERE sprint_id = ?{tf_sql}",
    (sprint_id, *tf_params),
)
avg_adoption = adopt_data[0]["avg_adopt"] if adopt_data and adopt_data[0]["avg_adopt"] else 0

# KPI: Security incidents
sec_data = query_df(
    f"SELECT COUNT(*) as cnt FROM security_incidents WHERE sprint_id = ?{tf_sql}",
    (sprint_id, *tf_params),
)
total_incidents = sec_data[0]["cnt"] if sec_data else 0

# Previous sprint for deltas
prev_sprint_num = next((s["number"] for s in sprints if s["id"] == sprint_id), 1) - 1
prev_sprint_id = next((s["id"] for s in sprints if s["number"] == prev_sprint_num), None)

prev_compliance = 0
prev_violations = 0
prev_cost = 0
if prev_sprint_id:
    pc = query_df(
        f"SELECT AVG(score) as v FROM compliance_scores WHERE sprint_id = ?{tf_sql}",
        (prev_sprint_id, *tf_params),
    )
    prev_compliance = pc[0]["v"] if pc and pc[0]["v"] else 0
    pv = query_df(
        f"SELECT COUNT(*) as v FROM policy_violations WHERE sprint_id = ?{tf_sql}",
        (prev_sprint_id, *tf_params),
    )
    prev_violations = pv[0]["v"] if pv else 0
    pcost = query_df(
        f"SELECT SUM(cost_usd) as v FROM token_usage WHERE sprint_id = ?{tf_sql}",
        (prev_sprint_id, *tf_params),
    )
    prev_cost = pcost[0]["v"] if pcost and pcost[0]["v"] else 0

# Display KPIs
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    delta_c = avg_compliance - prev_compliance
    delta_str = f"{'↑' if delta_c >= 0 else '↓'} {abs(delta_c):.1f}% vs prev sprint"
    metric_card(
        "Overall Compliance",
        f"{avg_compliance:.1f}%",
        delta_str,
        "positive" if delta_c >= 0 else "negative",
        compliance_color(avg_compliance),
    )
with col2:
    delta_v = total_violations - prev_violations
    metric_card(
        "Policy Violations",
        str(total_violations),
        f"{'↑' if delta_v > 0 else '↓'} {abs(delta_v)} vs prev sprint",
        "negative" if delta_v > 0 else "positive",
        "#E24B4A" if total_violations > 20 else "#BA7517" if total_violations > 10 else "#639922",
    )
with col3:
    delta_cost = total_cost - prev_cost
    metric_card(
        "Token Cost (Sprint)",
        format_currency(total_cost),
        f"{'↑' if delta_cost > 0 else '↓'} {format_currency(abs(delta_cost))} vs prev",
        "negative" if delta_cost > 0 else "positive",
        "#534AB7",
    )
with col4:
    metric_card(
        "AI Adoption Rate",
        f"{avg_adoption:.0f}%",
        "",
        "neutral",
        "#1D9E75",
    )
with col5:
    metric_card(
        "Security Incidents",
        str(total_incidents),
        "",
        "negative" if total_incidents > 3 else "neutral",
        "#E24B4A" if total_incidents > 3 else "#BA7517" if total_incidents > 0 else "#639922",
    )

st.markdown("---")

# --- Compliance Heatmap ---
section_header("Compliance Heatmap — Teams × Policy Categories")

heatmap_data = query_df("""
    SELECT t.name as team, cs.category, AVG(cs.score) as score
    FROM compliance_scores cs
    JOIN teams t ON cs.team_id = t.id
    WHERE cs.sprint_id = ?
    GROUP BY t.name, cs.category
    ORDER BY t.name, cs.category
""", (sprint_id,))

if heatmap_data:
    df_heat = pd.DataFrame(heatmap_data)
    pivot = df_heat.pivot(index="team", columns="category", values="score").fillna(0)

    # Rename columns for display
    col_labels = {
        "security": "Security", "coding_standards": "Coding Std",
        "data_privacy": "Data Privacy", "dependency_management": "Dependencies",
        "architecture": "Architecture", "testing": "Testing",
        "documentation": "Docs", "performance": "Performance",
    }
    pivot = pivot.rename(columns=col_labels)

    fig_heat = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[
            [0, "#E24B4A"], [0.6, "#BA7517"],
            [0.75, "#1D9E75"], [1.0, "#639922"],
        ],
        zmin=50, zmax=100,
        text=[[f"{v:.0f}%" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont={"size": 13, "color": "white"},
        hovertemplate="Team: %{y}<br>Category: %{x}<br>Score: %{z:.1f}%<extra></extra>",
        colorbar=dict(title="Score %", ticksuffix="%"),
    ))
    fig_heat.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(side="top"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("---")

# --- Trend Charts Row ---
col_left, col_right = st.columns(2)

with col_left:
    section_header("Compliance Trend Across Sprints")
    trend_data = query_df("""
        SELECT s.name as sprint, t.name as team, AVG(cs.score) as score
        FROM compliance_scores cs
        JOIN teams t ON cs.team_id = t.id
        JOIN sprints s ON cs.sprint_id = s.id
        GROUP BY s.name, t.name, s.number
        ORDER BY s.number
    """)
    if trend_data:
        df_trend = pd.DataFrame(trend_data)
        fig_trend = px.line(
            df_trend, x="sprint", y="score", color="team",
            color_discrete_map=TEAM_COLORS,
            markers=True,
        )
        fig_trend.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(title="Compliance %", range=[50, 100]),
            xaxis=dict(title=""),
            legend=dict(orientation="h", y=-0.15),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig_trend.update_yaxes(gridcolor="#e8e6e0")
        st.plotly_chart(fig_trend, use_container_width=True)

with col_right:
    section_header("Violations by Severity (Current Sprint)")
    viol_sev = query_df("""
        SELECT severity, COUNT(*) as count
        FROM policy_violations
        WHERE sprint_id = ?
        GROUP BY severity
        ORDER BY CASE severity
            WHEN 'critical' THEN 1 WHEN 'high' THEN 2
            WHEN 'medium' THEN 3 WHEN 'low' THEN 4 ELSE 5
        END
    """, (sprint_id,))
    if viol_sev:
        df_sev = pd.DataFrame(viol_sev)
        colors = {"critical": "#E24B4A", "high": "#D85A30", "medium": "#BA7517", "low": "#378ADD", "info": "#888780"}
        fig_sev = go.Figure(data=[go.Bar(
            x=df_sev["severity"],
            y=df_sev["count"],
            marker_color=[colors.get(s, "#888780") for s in df_sev["severity"]],
            text=df_sev["count"],
            textposition="auto",
        )])
        fig_sev.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(title="Count"),
            xaxis=dict(title=""),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig_sev.update_yaxes(gridcolor="#e8e6e0")
        st.plotly_chart(fig_sev, use_container_width=True)

st.markdown("---")

# --- Active Alerts ---
section_header("Active Alerts")
alerts = query_df("""
    SELECT a.*, t.name as team_name
    FROM alerts a
    JOIN teams t ON a.team_id = t.id
    WHERE a.sprint_id = ? AND a.acknowledged = 0
    ORDER BY CASE a.severity
        WHEN 'critical' THEN 1 WHEN 'high' THEN 2
        WHEN 'medium' THEN 3 ELSE 4
    END
    LIMIT 8
""", (sprint_id,))

if alerts:
    for alert in alerts:
        alert_banner(alert["severity"], f"**{alert['team_name']}** — {alert['message']}")
else:
    st.success("✅ No active alerts for this sprint")

st.markdown("---")

# --- Quick Navigation ---
section_header("Explore Dashboard Pillars")
nav_cols = st.columns(6)
pages = [
    ("📋", "Compliance", "Detailed compliance heatmaps and policy matrix", "/Compliance"),
    ("📊", "Code Quality", "SAST scores, AI code analysis, quality trends", "/Code_Quality"),
    ("💰", "Token Usage", "Cost breakdown, consumption trends, budgets", "/Token_Usage"),
    ("🚀", "Adoption", "AI adoption rates, productivity, ROI", "/Adoption"),
    ("🔒", "Security", "PII incidents, secret detection, compliance", "/Security"),
    ("🔄", "Lifecycle", "CI/CD monitoring, test coverage, defect leakage", "/Lifecycle"),
]
for col, (icon, title, desc, url) in zip(nav_cols, pages):
    with col:
        st.markdown(f"""
        <div style="text-align:center; padding:16px; background:#f8f7f4;
             border:1px solid #e8e6e0; border-radius:12px; min-height:140px;">
            <a href="{url}" target="_self" class="pillar-icon-link">{icon}</a>
            <div style="font-weight:600; margin-bottom:4px;">{title}</div>
            <div style="font-size:12px; color:#888780;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
