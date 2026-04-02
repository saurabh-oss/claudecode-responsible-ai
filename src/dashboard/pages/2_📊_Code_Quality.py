"""Page 2: Coding Standards — SAST scorecard, AI code analysis, quality trends."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from src.data.database import query_df
from src.dashboard.components import apply_custom_css, metric_card, section_header
from src.utils.helpers import TEAM_COLORS

st.set_page_config(page_title="Code Quality", page_icon="📊", layout="wide")
apply_custom_css()
st.title("📊 Coding Standards & Quality")
st.caption("Static analysis scorecard, AI-generated code analysis, quality trends")

sprints = query_df("SELECT * FROM sprints ORDER BY number")
teams = query_df("SELECT * FROM teams ORDER BY name")
col_f1, col_f2 = st.columns(2)
with col_f1:
    sel_sprint = st.selectbox("Sprint", [s["name"] for s in sprints], index=len(sprints)-1, key="cq_sp")
    sprint_id = next(s["id"] for s in sprints if s["name"] == sel_sprint)
with col_f2:
    sel_team = st.selectbox("Team", ["All Teams"] + [t["name"] for t in teams], key="cq_tm")

team_sql = ""
team_p = ()
if sel_team != "All Teams":
    tid = next(t["id"] for t in teams if t["name"] == sel_team)
    team_sql = " AND cq.team_id = ?"
    team_p = (tid,)

st.markdown("---")

# KPIs
kpi = query_df(f"""
    SELECT AVG(sonarqube_score) as sq, AVG(test_coverage_pct) as cov,
           AVG(complexity_avg) as comp, SUM(flagged_ai_snippets) as flagged,
           SUM(ai_generated_lines) as ai_lines, SUM(human_authored_lines) as human_lines,
           SUM(bugs_found) as bugs, SUM(vulnerabilities) as vulns
    FROM code_quality_metrics cq WHERE cq.sprint_id = ?{team_sql}
""", (sprint_id, *team_p))

k = kpi[0] if kpi else {}
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    v = k.get("sq") or 0
    metric_card("SonarQube Score", f"{v:.1f}", "", "neutral",
                "#639922" if v >= 80 else "#BA7517" if v >= 60 else "#E24B4A")
with c2:
    v = k.get("cov") or 0
    metric_card("Test Coverage", f"{v:.1f}%", "", "positive" if v >= 70 else "negative")
with c3:
    v = k.get("comp") or 0
    metric_card("Avg Complexity", f"{v:.1f}", "Target < 10", "positive" if v < 10 else "negative")
with c4:
    v = k.get("flagged") or 0
    metric_card("Flagged AI Snippets", str(int(v)), "", "negative" if v > 10 else "neutral", "#D85A30")
with c5:
    v = k.get("vulns") or 0
    metric_card("Vulnerabilities", str(int(v)), "", "negative" if v > 0 else "positive",
                "#E24B4A" if v > 3 else "#BA7517" if v > 0 else "#639922")

st.markdown("---")

# --- AI vs Human Code Composition ---
col_l, col_r = st.columns(2)

with col_l:
    section_header("AI-Generated vs Human-Authored Code")
    comp_data = query_df("""
        SELECT t.name as team, SUM(cq.ai_generated_lines) as ai,
               SUM(cq.human_authored_lines) as human
        FROM code_quality_metrics cq
        JOIN teams t ON cq.team_id = t.id
        WHERE cq.sprint_id = ?
        GROUP BY t.name
    """, (sprint_id,))
    if comp_data:
        df = pd.DataFrame(comp_data)
        fig = go.Figure()
        fig.add_trace(go.Bar(name="AI-Generated", x=df["team"], y=df["ai"],
                             marker_color="#534AB7", text=df["ai"].apply(lambda x: f"{x:,.0f}"),
                             textposition="auto"))
        fig.add_trace(go.Bar(name="Human-Authored", x=df["team"], y=df["human"],
                             marker_color="#1D9E75", text=df["human"].apply(lambda x: f"{x:,.0f}"),
                             textposition="auto"))
        fig.update_layout(barmode="group", height=350, margin=dict(l=10, r=10, t=10, b=10),
                          legend=dict(orientation="h", y=-0.15),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_yaxes(gridcolor="#e8e6e0", title="Lines of Code")
        st.plotly_chart(fig, use_container_width=True)

with col_r:
    section_header("Quality Score by Team (Current Sprint)")
    team_scores = query_df("""
        SELECT t.name as team, cq.sonarqube_score as score,
               cq.test_coverage_pct as coverage, cq.complexity_avg as complexity
        FROM code_quality_metrics cq
        JOIN teams t ON cq.team_id = t.id
        WHERE cq.sprint_id = ?
        ORDER BY cq.sonarqube_score DESC
    """, (sprint_id,))
    if team_scores:
        df_ts = pd.DataFrame(team_scores)
        fig_ts = go.Figure()
        fig_ts.add_trace(go.Bar(
            x=df_ts["team"], y=df_ts["score"],
            marker_color=[TEAM_COLORS.get(t, "#888780") for t in df_ts["team"]],
            text=df_ts["score"].apply(lambda x: f"{x:.1f}"),
            textposition="auto",
        ))
        fig_ts.add_hline(y=80, line_dash="dash", line_color="#639922",
                         annotation_text="Quality Gate (80)")
        fig_ts.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10),
                             yaxis=dict(title="SonarQube Score", range=[0, 100]),
                             paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig_ts.update_yaxes(gridcolor="#e8e6e0")
        st.plotly_chart(fig_ts, use_container_width=True)

st.markdown("---")

# --- Quality Trend Over Sprints ---
section_header("Quality Score Trend Across Sprints")
trend = query_df("""
    SELECT s.name as sprint, t.name as team, cq.sonarqube_score as score
    FROM code_quality_metrics cq
    JOIN teams t ON cq.team_id = t.id
    JOIN sprints s ON cq.sprint_id = s.id
    ORDER BY s.number
""")
if trend:
    df_t = pd.DataFrame(trend)
    fig = px.line(df_t, x="sprint", y="score", color="team",
                  color_discrete_map=TEAM_COLORS, markers=True)
    fig.add_hline(y=80, line_dash="dash", line_color="#639922", annotation_text="Quality Gate")
    fig.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10),
                      yaxis=dict(title="SonarQube Score", range=[40, 100]),
                      legend=dict(orientation="h", y=-0.15),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig.update_yaxes(gridcolor="#e8e6e0")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- Static Analysis Breakdown ---
section_header("Static Analysis Findings")
findings = query_df("""
    SELECT t.name as team, SUM(bugs_found) as bugs,
           SUM(code_smells) as smells, SUM(vulnerabilities) as vulns,
           SUM(flagged_ai_snippets) as ai_flagged
    FROM code_quality_metrics cq
    JOIN teams t ON cq.team_id = t.id
    WHERE cq.sprint_id = ?
    GROUP BY t.name
""", (sprint_id,))
if findings:
    df_f = pd.DataFrame(findings)
    st.dataframe(
        df_f.style.background_gradient(subset=["bugs", "smells", "vulns", "ai_flagged"],
                                        cmap="YlOrRd", vmin=0),
        use_container_width=True, hide_index=True,
    )
