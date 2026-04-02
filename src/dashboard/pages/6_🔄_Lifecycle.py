"""Page 6: Lifecycle Integration — CI/CD monitoring, test coverage, defect leakage."""

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

st.set_page_config(page_title="Lifecycle Integration", page_icon="🔄", layout="wide")
apply_custom_css()
st.title("🔄 Lifecycle Integration")
st.caption("CI/CD compliance monitoring, test automation coverage, defect leakage analysis")

sprints = query_df("SELECT * FROM sprints ORDER BY number")
teams = query_df("SELECT * FROM teams ORDER BY name")
col_f1, col_f2 = st.columns(2)
with col_f1:
    sel_sprint = st.selectbox("Sprint", [s["name"] for s in sprints], index=len(sprints)-1, key="lc_sp")
    sprint_id = next(s["id"] for s in sprints if s["name"] == sel_sprint)
with col_f2:
    sel_team = st.selectbox("Team", ["All Teams"] + [t["name"] for t in teams], key="lc_tm")

team_sql = ""
team_p = ()
if sel_team != "All Teams":
    tid = next(t["id"] for t in teams if t["name"] == sel_team)
    team_sql = " AND lm.team_id = ?"
    team_p = (tid,)

st.markdown("---")

# --- KPIs ---
kpi = query_df(f"""
    SELECT
        ROUND(AVG(CASE WHEN is_monitored = 1 THEN 100.0 ELSE 0 END), 1) as monitored_pct,
        ROUND(AVG(compliance_pct), 1) as avg_compliance,
        ROUND(AVG(test_automation_pct), 1) as avg_test_auto,
        ROUND(AVG(pipeline_pass_rate), 1) as avg_pipeline,
        SUM(defects_found) as total_defects,
        SUM(defects_leaked) as total_leaked
    FROM lifecycle_metrics lm WHERE lm.sprint_id = ?{team_sql}
""", (sprint_id, *team_p))

k = kpi[0] if kpi else {}
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    v = k.get("monitored_pct") or 0
    metric_card("Stages Monitored", f"{v:.0f}%", "of SDLC stages", "positive" if v > 80 else "negative", "#534AB7")
with c2:
    v = k.get("avg_compliance") or 0
    metric_card("Lifecycle Compliance", f"{v:.1f}%", "", "positive" if v > 80 else "negative", "#1D9E75")
with c3:
    v = k.get("avg_test_auto") or 0
    metric_card("Test Automation", f"{v:.1f}%", "", "positive" if v > 60 else "negative", "#378ADD")
with c4:
    v = k.get("avg_pipeline") or 0
    metric_card("Pipeline Pass Rate", f"{v:.1f}%", "", "positive" if v > 90 else "negative",
                "#639922" if v > 90 else "#BA7517")
with c5:
    found = k.get("total_defects") or 0
    leaked = k.get("total_leaked") or 0
    leakage = (leaked / found * 100) if found > 0 else 0
    metric_card("Defect Leakage", f"{leakage:.1f}%", f"{leaked}/{found} defects leaked",
                "negative" if leakage > 15 else "positive",
                "#E24B4A" if leakage > 15 else "#BA7517" if leakage > 5 else "#639922")

st.markdown("---")

# --- SDLC Stage Compliance Radar ---
section_header("SDLC Stage Compliance (Current Sprint)")

stages_data = query_df(f"""
    SELECT stage, ROUND(AVG(compliance_pct), 1) as compliance,
           ROUND(AVG(ai_coverage_pct), 1) as ai_coverage,
           ROUND(AVG(test_automation_pct), 1) as test_auto,
           ROUND(AVG(pipeline_pass_rate), 1) as pipeline_pass
    FROM lifecycle_metrics lm WHERE lm.sprint_id = ?{team_sql}
    GROUP BY stage
    ORDER BY CASE stage
        WHEN 'requirements' THEN 1 WHEN 'design' THEN 2 WHEN 'development' THEN 3
        WHEN 'testing' THEN 4 WHEN 'deployment' THEN 5 WHEN 'monitoring' THEN 6 END
""", (sprint_id, *team_p))

if stages_data:
    df_s = pd.DataFrame(stages_data)
    stage_labels = df_s["stage"].str.capitalize().tolist()

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=df_s["compliance"].tolist() + [df_s["compliance"].iloc[0]],
        theta=stage_labels + [stage_labels[0]],
        fill="toself", name="Compliance",
        line=dict(color="#534AB7"),
        fillcolor="rgba(83,74,183,0.15)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=df_s["ai_coverage"].tolist() + [df_s["ai_coverage"].iloc[0]],
        theta=stage_labels + [stage_labels[0]],
        fill="toself", name="AI Coverage",
        line=dict(color="#1D9E75"),
        fillcolor="rgba(29,158,117,0.1)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=df_s["test_auto"].tolist() + [df_s["test_auto"].iloc[0]],
        theta=stage_labels + [stage_labels[0]],
        fill="toself", name="Test Automation",
        line=dict(color="#378ADD"),
        fillcolor="rgba(55,138,221,0.1)",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=420, margin=dict(l=40, r=40, t=20, b=20),
        legend=dict(orientation="h", y=-0.1),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- Stage-by-Stage Breakdown ---
col_l, col_r = st.columns(2)

with col_l:
    section_header("Compliance by Stage & Team")
    stage_team = query_df("""
        SELECT t.name as team, lm.stage, ROUND(AVG(lm.compliance_pct), 1) as compliance
        FROM lifecycle_metrics lm
        JOIN teams t ON lm.team_id = t.id
        WHERE lm.sprint_id = ?
        GROUP BY t.name, lm.stage
    """, (sprint_id,))
    if stage_team:
        df = pd.DataFrame(stage_team)
        df["stage"] = df["stage"].str.capitalize()
        pivot = df.pivot(index="team", columns="stage", values="compliance").fillna(0)
        # Reorder columns
        order = ["Requirements", "Design", "Development", "Testing", "Deployment", "Monitoring"]
        pivot = pivot[[c for c in order if c in pivot.columns]]

        fig = go.Figure(data=go.Heatmap(
            z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
            colorscale=[[0, "#E24B4A"], [0.6, "#BA7517"], [0.75, "#1D9E75"], [1.0, "#639922"]],
            zmin=50, zmax=100,
            text=[[f"{v:.0f}%" for v in row] for row in pivot.values],
            texttemplate="%{text}", textfont={"size": 11, "color": "white"},
        ))
        fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10),
                          xaxis=dict(side="top"),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

with col_r:
    section_header("Defect Leakage by Team")
    leakage = query_df("""
        SELECT t.name as team, SUM(lm.defects_found) as found,
               SUM(lm.defects_leaked) as leaked
        FROM lifecycle_metrics lm
        JOIN teams t ON lm.team_id = t.id
        WHERE lm.sprint_id = ?
        GROUP BY t.name
    """, (sprint_id,))
    if leakage:
        df = pd.DataFrame(leakage)
        df["contained"] = df["found"] - df["leaked"]
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Contained", x=df["team"], y=df["contained"],
                             marker_color="#1D9E75", text=df["contained"], textposition="auto"))
        fig.add_trace(go.Bar(name="Leaked", x=df["team"], y=df["leaked"],
                             marker_color="#E24B4A", text=df["leaked"], textposition="auto"))
        fig.update_layout(barmode="stack", height=280,
                          margin=dict(l=10, r=10, t=10, b=10),
                          yaxis=dict(title="Defects"),
                          legend=dict(orientation="h", y=-0.2),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_yaxes(gridcolor="#e8e6e0")
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- Pipeline Pass Rate Trend ---
section_header("Pipeline Pass Rate Trend")
pipeline_trend = query_df("""
    SELECT s.name as sprint, t.name as team,
           ROUND(AVG(lm.pipeline_pass_rate), 1) as pass_rate
    FROM lifecycle_metrics lm
    JOIN teams t ON lm.team_id = t.id
    JOIN sprints s ON lm.sprint_id = s.id
    GROUP BY s.name, t.name, s.number ORDER BY s.number
""")
if pipeline_trend:
    df = pd.DataFrame(pipeline_trend)
    fig = px.line(df, x="sprint", y="pass_rate", color="team",
                  color_discrete_map=TEAM_COLORS, markers=True)
    fig.add_hline(y=90, line_dash="dash", line_color="#639922",
                  annotation_text="Target: 90%")
    fig.update_layout(height=350, yaxis=dict(title="Pass Rate %", range=[60, 100]),
                      margin=dict(l=10, r=10, t=10, b=10),
                      legend=dict(orientation="h", y=-0.15),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig.update_yaxes(gridcolor="#e8e6e0")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- Monitoring Coverage Table ---
section_header("SDLC Stage Monitoring Status")
monitoring = query_df(f"""
    SELECT lm.stage, 
           ROUND(AVG(CASE WHEN lm.is_monitored = 1 THEN 100.0 ELSE 0 END), 0) as monitored_pct,
           ROUND(AVG(lm.compliance_pct), 1) as compliance,
           ROUND(AVG(lm.ai_coverage_pct), 1) as ai_coverage,
           ROUND(AVG(lm.test_automation_pct), 1) as test_automation,
           SUM(lm.defects_found) as defects_found,
           SUM(lm.defects_leaked) as defects_leaked,
           ROUND(AVG(lm.pipeline_pass_rate), 1) as pipeline_pass
    FROM lifecycle_metrics lm WHERE lm.sprint_id = ?{team_sql}
    GROUP BY lm.stage
    ORDER BY CASE lm.stage
        WHEN 'requirements' THEN 1 WHEN 'design' THEN 2 WHEN 'development' THEN 3
        WHEN 'testing' THEN 4 WHEN 'deployment' THEN 5 WHEN 'monitoring' THEN 6 END
""", (sprint_id, *team_p))
if monitoring:
    df = pd.DataFrame(monitoring)
    df["stage"] = df["stage"].str.capitalize()
    df["monitored_pct"] = df["monitored_pct"].apply(lambda x: f"{x:.0f}%")
    st.dataframe(df.style.background_gradient(
        subset=["compliance", "ai_coverage", "test_automation", "pipeline_pass"],
        cmap="RdYlGn", vmin=40, vmax=100),
        use_container_width=True, hide_index=True)
