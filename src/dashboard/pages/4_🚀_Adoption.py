"""Page 4: Adoption & Productivity — AI adoption rates, productivity gains, ROI."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from src.data.database import query_df
from src.dashboard.components import apply_custom_css, metric_card, section_header
from src.utils.helpers import TEAM_COLORS, format_currency

st.set_page_config(page_title="Adoption & Productivity", page_icon="🚀", layout="wide")
apply_custom_css()
st.title("🚀 Adoption & Productivity")
st.caption("AI adoption rates, productivity gains, sprint velocity impact, and ROI estimation")

sprints = query_df("SELECT * FROM sprints ORDER BY number")
teams = query_df("SELECT * FROM teams ORDER BY name")
col_f1, col_f2 = st.columns(2)
with col_f1:
    sel_sprint = st.selectbox("Sprint", [s["name"] for s in sprints], index=len(sprints)-1, key="ad_sp")
    sprint_id = next(s["id"] for s in sprints if s["name"] == sel_sprint)
with col_f2:
    sel_team = st.selectbox("Team", ["All Teams"] + [t["name"] for t in teams], key="ad_tm")

team_sql = ""
team_p = ()
if sel_team != "All Teams":
    tid = next(t["id"] for t in teams if t["name"] == sel_team)
    team_sql = " AND am.team_id = ?"
    team_p = (tid,)

st.markdown("---")

# --- KPIs ---
kpi = query_df(f"""
    SELECT AVG(adoption_rate_pct) as adopt, AVG(productivity_gain_pct) as prod,
           SUM(avg_time_saved_hrs) as time_saved, SUM(roi_estimate_usd) as roi,
           SUM(ai_active_developers) as ai_devs, SUM(total_developers) as total_devs,
           AVG(ai_assisted_commits_pct) as ai_commits
    FROM adoption_metrics am WHERE am.sprint_id = ?{team_sql}
""", (sprint_id, *team_p))

k = kpi[0] if kpi else {}
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    v = k.get("adopt") or 0
    metric_card("Adoption Rate", f"{v:.0f}%", f"{int(k.get('ai_devs') or 0)}/{int(k.get('total_devs') or 0)} developers",
                "positive" if v > 60 else "neutral", "#1D9E75")
with c2:
    v = k.get("prod") or 0
    metric_card("Productivity Gain", f"{v:.1f}%", "vs pre-AI baseline", "positive" if v > 15 else "neutral", "#534AB7")
with c3:
    v = k.get("time_saved") or 0
    metric_card("Time Saved", f"{v:.0f} hrs", "this sprint", "positive", "#378ADD")
with c4:
    v = k.get("ai_commits") or 0
    metric_card("AI-Assisted Commits", f"{v:.0f}%", "of all commits", "neutral", "#D85A30")
with c5:
    v = k.get("roi") or 0
    metric_card("ROI Estimate", format_currency(v), "velocity gain − token cost",
                "positive" if v > 0 else "negative", "#639922" if v > 0 else "#E24B4A")

st.markdown("---")

# --- Adoption Gauge per Team ---
section_header("AI Adoption by Team")
team_adopt = query_df("""
    SELECT t.name as team, am.adoption_rate_pct as rate,
           am.ai_active_developers as ai_devs, am.total_developers as total
    FROM adoption_metrics am
    JOIN teams t ON am.team_id = t.id
    WHERE am.sprint_id = ?
    ORDER BY am.adoption_rate_pct DESC
""", (sprint_id,))

if team_adopt:
    cols = st.columns(len(team_adopt))
    for col, row in zip(cols, team_adopt):
        with col:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=row["rate"],
                title={"text": row["team"], "font": {"size": 13}},
                number={"suffix": "%", "font": {"size": 28}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1},
                    "bar": {"color": TEAM_COLORS.get(row["team"], "#534AB7")},
                    "steps": [
                        {"range": [0, 40], "color": "#FCEBEB"},
                        {"range": [40, 70], "color": "#FAEEDA"},
                        {"range": [70, 100], "color": "#E1F5EE"},
                    ],
                    "threshold": {"line": {"color": "#E24B4A", "width": 2}, "thickness": 0.8, "value": 50},
                },
            ))
            fig.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=10),
                              paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"{row['ai_devs']}/{row['total']} developers active")

st.markdown("---")

# --- Adoption & Productivity Trend ---
col_l, col_r = st.columns(2)

with col_l:
    section_header("Adoption Rate Trend")
    adopt_trend = query_df("""
        SELECT s.name as sprint, t.name as team, am.adoption_rate_pct as rate
        FROM adoption_metrics am
        JOIN teams t ON am.team_id = t.id
        JOIN sprints s ON am.sprint_id = s.id
        ORDER BY s.number
    """)
    if adopt_trend:
        df = pd.DataFrame(adopt_trend)
        fig = px.line(df, x="sprint", y="rate", color="team",
                      color_discrete_map=TEAM_COLORS, markers=True)
        fig.add_hline(y=50, line_dash="dash", line_color="#BA7517",
                      annotation_text="Target: 50%")
        fig.update_layout(height=350, yaxis=dict(title="Adoption %", range=[0, 100]),
                          margin=dict(l=10, r=10, t=10, b=10),
                          legend=dict(orientation="h", y=-0.15),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_yaxes(gridcolor="#e8e6e0")
        st.plotly_chart(fig, use_container_width=True)

with col_r:
    section_header("Productivity Gain Trend")
    prod_trend = query_df("""
        SELECT s.name as sprint, t.name as team, am.productivity_gain_pct as gain
        FROM adoption_metrics am
        JOIN teams t ON am.team_id = t.id
        JOIN sprints s ON am.sprint_id = s.id
        ORDER BY s.number
    """)
    if prod_trend:
        df = pd.DataFrame(prod_trend)
        fig = px.line(df, x="sprint", y="gain", color="team",
                      color_discrete_map=TEAM_COLORS, markers=True)
        fig.update_layout(height=350, yaxis=dict(title="Productivity Gain %"),
                          margin=dict(l=10, r=10, t=10, b=10),
                          legend=dict(orientation="h", y=-0.15),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_yaxes(gridcolor="#e8e6e0")
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- Velocity Impact ---
section_header("Sprint Velocity: AI-Boosted vs Baseline")
velocity = query_df("""
    SELECT s.name as sprint, t.name as team,
           am.sprint_velocity_points as actual,
           am.baseline_velocity_points as baseline
    FROM adoption_metrics am
    JOIN teams t ON am.team_id = t.id
    JOIN sprints s ON am.sprint_id = s.id
    ORDER BY s.number
""")
if velocity:
    df_v = pd.DataFrame(velocity)
    # Show for most recent sprint
    df_latest = df_v[df_v["sprint"] == sel_sprint]
    if not df_latest.empty:
        fig_v = go.Figure()
        fig_v.add_trace(go.Bar(name="Baseline Velocity", x=df_latest["team"],
                               y=df_latest["baseline"], marker_color="#888780",
                               text=df_latest["baseline"], textposition="auto"))
        fig_v.add_trace(go.Bar(name="AI-Boosted Velocity", x=df_latest["team"],
                               y=df_latest["actual"],
                               marker_color=[TEAM_COLORS.get(t, "#534AB7") for t in df_latest["team"]],
                               text=df_latest["actual"], textposition="auto"))
        fig_v.update_layout(barmode="group", height=350,
                            margin=dict(l=10, r=10, t=10, b=10),
                            yaxis=dict(title="Story Points"),
                            legend=dict(orientation="h", y=-0.15),
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig_v.update_yaxes(gridcolor="#e8e6e0")
        st.plotly_chart(fig_v, use_container_width=True)

st.markdown("---")

# --- ROI Summary Table ---
section_header("ROI Summary by Team")
roi_data = query_df("""
    SELECT t.name as team, am.adoption_rate_pct as adoption,
           am.productivity_gain_pct as productivity_gain,
           am.avg_time_saved_hrs as hours_saved,
           am.roi_estimate_usd as roi_usd
    FROM adoption_metrics am
    JOIN teams t ON am.team_id = t.id
    WHERE am.sprint_id = ?
    ORDER BY am.roi_estimate_usd DESC
""", (sprint_id,))
if roi_data:
    df_roi = pd.DataFrame(roi_data)
    st.dataframe(
        df_roi.style.format({
            "adoption": "{:.0f}%", "productivity_gain": "{:.1f}%",
            "hours_saved": "{:.1f} hrs", "roi_usd": "${:,.0f}"
        }).background_gradient(subset=["roi_usd"], cmap="RdYlGn"),
        use_container_width=True, hide_index=True,
    )
