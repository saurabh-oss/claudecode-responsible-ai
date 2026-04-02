"""Page 1: Compliance & Monitoring — Detailed heatmaps, policy matrix, violation drill-down."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from src.data.database import query_df
from src.dashboard.components import apply_custom_css, metric_card, section_header, alert_banner
from src.utils.helpers import TEAM_COLORS, CATEGORY_LABELS, compliance_color, severity_color

st.set_page_config(page_title="Compliance & Monitoring", page_icon="📋", layout="wide")
apply_custom_css()

st.title("📋 Compliance & Monitoring")
st.caption("Rule compliance heatmaps, role-based policy matrix, and violation drill-down")

# Filters
sprints = query_df("SELECT * FROM sprints ORDER BY number")
teams = query_df("SELECT * FROM teams ORDER BY name")
col_f1, col_f2 = st.columns(2)
with col_f1:
    selected_sprint = st.selectbox("Sprint", [s["name"] for s in sprints], index=len(sprints) - 1, key="comp_sprint")
    sprint_id = next(s["id"] for s in sprints if s["name"] == selected_sprint)
with col_f2:
    selected_team = st.selectbox("Team", ["All Teams"] + [t["name"] for t in teams], key="comp_team")

team_clause = ""
team_params = ()
if selected_team != "All Teams":
    tid = next(t["id"] for t in teams if t["name"] == selected_team)
    team_clause = " AND cs.team_id = ?"
    team_params = (tid,)

st.markdown("---")

# --- KPI Row ---
kpi_data = query_df(f"""
    SELECT
        AVG(cs.score) as avg_score,
        MIN(cs.score) as min_score,
        MAX(cs.score) as max_score
    FROM compliance_scores cs
    WHERE cs.sprint_id = ?{team_clause}
""", (sprint_id, *team_params))

viol_count = query_df(f"""
    SELECT COUNT(*) as total, SUM(CASE WHEN resolved = 1 THEN 1 ELSE 0 END) as resolved
    FROM policy_violations pv
    WHERE pv.sprint_id = ?{team_clause.replace('cs.', 'pv.')}
""", (sprint_id, *team_params))

c1, c2, c3, c4 = st.columns(4)
with c1:
    v = kpi_data[0]["avg_score"] if kpi_data and kpi_data[0]["avg_score"] else 0
    metric_card("Avg Compliance", f"{v:.1f}%", "", "neutral", compliance_color(v))
with c2:
    v = kpi_data[0]["min_score"] if kpi_data and kpi_data[0]["min_score"] else 0
    metric_card("Lowest Category", f"{v:.1f}%", "", "negative" if v < 70 else "neutral", compliance_color(v))
with c3:
    t = viol_count[0]["total"] if viol_count else 0
    metric_card("Total Violations", str(t), "", "negative" if t > 20 else "neutral")
with c4:
    r = viol_count[0]["resolved"] if viol_count and viol_count[0]["resolved"] else 0
    t = viol_count[0]["total"] if viol_count and viol_count[0]["total"] else 1
    pct = (r / t * 100) if t > 0 else 0
    metric_card("Resolution Rate", f"{pct:.0f}%", f"{r}/{t} resolved", "positive" if pct > 70 else "negative")

st.markdown("---")

# --- Compliance Heatmap (Full) ---
section_header("Compliance Heatmap — Teams × Categories")

heat = query_df("""
    SELECT t.name as team, cs.category, AVG(cs.score) as score
    FROM compliance_scores cs
    JOIN teams t ON cs.team_id = t.id
    WHERE cs.sprint_id = ?
    GROUP BY t.name, cs.category
""", (sprint_id,))

if heat:
    df = pd.DataFrame(heat)
    df["category"] = df["category"].map(CATEGORY_LABELS)
    pivot = df.pivot(index="team", columns="category", values="score").fillna(0)

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0, "#E24B4A"], [0.6, "#BA7517"], [0.75, "#1D9E75"], [1.0, "#639922"]],
        zmin=50, zmax=100,
        text=[[f"{v:.0f}%" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont={"size": 12, "color": "white"},
        colorbar=dict(title="Score %"),
    ))
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), xaxis=dict(side="top"),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- Role-Based Policy Matrix ---
section_header("Role-Based Policy Adherence")

role_data = query_df("""
    SELECT t.name as team,
           ROUND(AVG(CASE WHEN cs.category = 'security' THEN cs.score END), 1) as security,
           ROUND(AVG(CASE WHEN cs.category = 'coding_standards' THEN cs.score END), 1) as coding,
           ROUND(AVG(CASE WHEN cs.category = 'data_privacy' THEN cs.score END), 1) as privacy,
           ROUND(AVG(CASE WHEN cs.category = 'testing' THEN cs.score END), 1) as testing,
           ROUND(AVG(CASE WHEN cs.category = 'architecture' THEN cs.score END), 1) as architecture
    FROM compliance_scores cs
    JOIN teams t ON cs.team_id = t.id
    WHERE cs.sprint_id = ?
    GROUP BY t.name
""", (sprint_id,))

if role_data:
    df_role = pd.DataFrame(role_data)
    st.dataframe(
        df_role.style.background_gradient(subset=["security", "coding", "privacy", "testing", "architecture"],
                                           cmap="RdYlGn", vmin=50, vmax=100),
        use_container_width=True, hide_index=True,
    )

st.markdown("---")

# --- Violation Breakdown ---
col_l, col_r = st.columns(2)

with col_l:
    section_header("Violations by Category")
    viol_cat = query_df(f"""
        SELECT category, COUNT(*) as count
        FROM policy_violations
        WHERE sprint_id = ?{team_clause.replace('cs.', '')}
        GROUP BY category ORDER BY count DESC
    """, (sprint_id, *team_params))
    if viol_cat:
        df_vc = pd.DataFrame(viol_cat)
        df_vc["category"] = df_vc["category"].map(CATEGORY_LABELS)
        fig_vc = px.bar(df_vc, x="count", y="category", orientation="h",
                        color="count", color_continuous_scale=["#1D9E75", "#BA7517", "#E24B4A"])
        fig_vc.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10),
                             showlegend=False, coloraxis_showscale=False,
                             paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig_vc.update_xaxes(gridcolor="#e8e6e0")
        st.plotly_chart(fig_vc, use_container_width=True)

with col_r:
    section_header("Violations by Team")
    viol_team = query_df("""
        SELECT t.name as team, COUNT(*) as count
        FROM policy_violations pv
        JOIN teams t ON pv.team_id = t.id
        WHERE pv.sprint_id = ?
        GROUP BY t.name ORDER BY count DESC
    """, (sprint_id,))
    if viol_team:
        df_vt = pd.DataFrame(viol_team)
        fig_vt = px.pie(df_vt, names="team", values="count",
                        color="team", color_discrete_map=TEAM_COLORS, hole=0.4)
        fig_vt.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10),
                             paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_vt, use_container_width=True)

st.markdown("---")

# --- Compliance Trend ---
section_header("Compliance Score Trend (All Sprints)")
trend = query_df("""
    SELECT s.name as sprint, t.name as team, AVG(cs.score) as score
    FROM compliance_scores cs
    JOIN teams t ON cs.team_id = t.id
    JOIN sprints s ON cs.sprint_id = s.id
    GROUP BY s.name, t.name, s.number ORDER BY s.number
""")
if trend:
    df_tr = pd.DataFrame(trend)
    fig_tr = px.line(df_tr, x="sprint", y="score", color="team",
                     color_discrete_map=TEAM_COLORS, markers=True)
    fig_tr.add_hline(y=75, line_dash="dash", line_color="#BA7517", annotation_text="Minimum Threshold (75%)")
    fig_tr.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10),
                         yaxis=dict(title="Compliance %", range=[50, 100]),
                         legend=dict(orientation="h", y=-0.15),
                         paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig_tr.update_yaxes(gridcolor="#e8e6e0")
    st.plotly_chart(fig_tr, use_container_width=True)

st.markdown("---")

# --- Recent Violations Table ---
section_header("Recent Violations (Detail)")
recent = query_df(f"""
    SELECT pv.policy_id, pv.policy_name, pv.category, pv.severity,
           pv.file_path, pv.tool, pv.resolved, t.name as team, pv.detected_at
    FROM policy_violations pv
    JOIN teams t ON pv.team_id = t.id
    WHERE pv.sprint_id = ?{team_clause.replace('cs.', 'pv.')}
    ORDER BY pv.detected_at DESC LIMIT 25
""", (sprint_id, *team_params))

if recent:
    df_recent = pd.DataFrame(recent)
    df_recent["resolved"] = df_recent["resolved"].map({1: "✅", 0: "❌"})
    df_recent["severity"] = df_recent["severity"].str.upper()
    st.dataframe(df_recent, use_container_width=True, hide_index=True)
