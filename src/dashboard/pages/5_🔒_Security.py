"""Page 5: Data Security — PII incidents, secret detection, compliance adherence."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from src.data.database import query_df
from src.dashboard.components import apply_custom_css, metric_card, section_header, alert_banner
from src.utils.helpers import TEAM_COLORS, severity_color

st.set_page_config(page_title="Data Security", page_icon="🔒", layout="wide")
apply_custom_css()
st.title("🔒 Data Security")
st.caption("Sensitive data access alerts, PII incident tracking, compliance adherence")

sprints = query_df("SELECT * FROM sprints ORDER BY number")
teams = query_df("SELECT * FROM teams ORDER BY name")
col_f1, col_f2 = st.columns(2)
with col_f1:
    sel_sprint = st.selectbox("Sprint", [s["name"] for s in sprints], index=len(sprints)-1, key="sec_sp")
    sprint_id = next(s["id"] for s in sprints if s["name"] == sel_sprint)
with col_f2:
    sel_team = st.selectbox("Team", ["All Teams"] + [t["name"] for t in teams], key="sec_tm")

team_sql = ""
team_p = ()
if sel_team != "All Teams":
    tid = next(t["id"] for t in teams if t["name"] == sel_team)
    team_sql = " AND si.team_id = ?"
    team_p = (tid,)

st.markdown("---")

# --- KPIs ---
kpi = query_df(f"""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical,
           SUM(CASE WHEN status = 'open' OR status = 'investigating' THEN 1 ELSE 0 END) as open_count,
           SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved,
           SUM(CASE WHEN pii_type IS NOT NULL THEN 1 ELSE 0 END) as pii_incidents
    FROM security_incidents si WHERE si.sprint_id = ?{team_sql}
""", (sprint_id, *team_p))

# Security compliance from compliance_scores
sec_comp = query_df(f"""
    SELECT AVG(score) as v FROM compliance_scores cs
    WHERE cs.sprint_id = ? AND cs.category IN ('security', 'data_privacy')
    {team_sql.replace('si.', 'cs.')}
""", (sprint_id, *team_p))

k = kpi[0] if kpi else {}
sc = sec_comp[0]["v"] if sec_comp and sec_comp[0]["v"] else 0

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    v = k.get("total") or 0
    metric_card("Total Incidents", str(v), "", "negative" if v > 5 else "neutral",
                "#E24B4A" if v > 5 else "#BA7517" if v > 0 else "#639922")
with c2:
    v = k.get("critical") or 0
    metric_card("Critical Severity", str(v), "", "negative" if v > 0 else "positive",
                "#E24B4A" if v > 0 else "#639922")
with c3:
    v = k.get("open_count") or 0
    metric_card("Open / Investigating", str(v), "", "negative" if v > 2 else "neutral", "#D85A30")
with c4:
    v = k.get("pii_incidents") or 0
    metric_card("PII Incidents", str(v), "", "negative" if v > 0 else "positive",
                "#E24B4A" if v > 0 else "#639922")
with c5:
    metric_card("Security Compliance", f"{sc:.1f}%", "Avg security + privacy",
                "positive" if sc >= 85 else "negative",
                "#639922" if sc >= 85 else "#BA7517" if sc >= 70 else "#E24B4A")

st.markdown("---")

# --- Active Critical Alerts ---
critical = query_df(f"""
    SELECT si.*, t.name as team_name FROM security_incidents si
    JOIN teams t ON si.team_id = t.id
    WHERE si.sprint_id = ? AND si.severity = 'critical' AND si.status != 'resolved'
    {team_sql}
    ORDER BY si.detected_at DESC
""", (sprint_id, *team_p))

if critical:
    section_header("Active Critical Incidents")
    for inc in critical:
        alert_banner("critical",
                     f"**{inc['team_name']}** — {inc['description']} "
                     f"({inc['incident_type']}) in `{inc['affected_file']}`")

st.markdown("---")

# --- Incidents by Type & Severity ---
col_l, col_r = st.columns(2)

with col_l:
    section_header("Incidents by Type")
    by_type = query_df(f"""
        SELECT incident_type, COUNT(*) as count
        FROM security_incidents si WHERE si.sprint_id = ?{team_sql}
        GROUP BY incident_type ORDER BY count DESC
    """, (sprint_id, *team_p))
    if by_type:
        df = pd.DataFrame(by_type)
        fig = px.bar(df, x="count", y="incident_type", orientation="h",
                     color="count", color_continuous_scale=["#378ADD", "#D85A30", "#E24B4A"])
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10),
                          showlegend=False, coloraxis_showscale=False,
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(gridcolor="#e8e6e0")
        st.plotly_chart(fig, use_container_width=True)

with col_r:
    section_header("Incidents by Severity")
    by_sev = query_df(f"""
        SELECT severity, COUNT(*) as count
        FROM security_incidents si WHERE si.sprint_id = ?{team_sql}
        GROUP BY severity ORDER BY CASE severity
            WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END
    """, (sprint_id, *team_p))
    if by_sev:
        df = pd.DataFrame(by_sev)
        colors = [severity_color(s) for s in df["severity"]]
        fig = go.Figure(go.Pie(labels=df["severity"], values=df["count"],
                               marker=dict(colors=colors), hole=0.45))
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10),
                          paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- Incident Trend Across Sprints ---
section_header("Security Incident Trend")
trend = query_df("""
    SELECT s.name as sprint, t.name as team, COUNT(*) as count
    FROM security_incidents si
    JOIN teams t ON si.team_id = t.id
    JOIN sprints s ON si.sprint_id = s.id
    GROUP BY s.name, t.name, s.number ORDER BY s.number
""")
if trend:
    df = pd.DataFrame(trend)
    fig = px.bar(df, x="sprint", y="count", color="team",
                 color_discrete_map=TEAM_COLORS, barmode="group",
                 text_auto=True)
    fig.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10),
                      yaxis=dict(title="Incident Count"),
                      legend=dict(orientation="h", y=-0.15),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig.update_yaxes(gridcolor="#e8e6e0")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- Security Compliance by Team ---
section_header("Security & Privacy Compliance by Team")
sec_team = query_df("""
    SELECT t.name as team, cs.category,
           ROUND(AVG(cs.score), 1) as score
    FROM compliance_scores cs
    JOIN teams t ON cs.team_id = t.id
    WHERE cs.sprint_id = ? AND cs.category IN ('security', 'data_privacy')
    GROUP BY t.name, cs.category
""", (sprint_id,))
if sec_team:
    df = pd.DataFrame(sec_team)
    pivot = df.pivot(index="team", columns="category", values="score").fillna(0)
    pivot = pivot.rename(columns={"security": "Security", "data_privacy": "Data Privacy"})
    if "Security" in pivot.columns and "Data Privacy" in pivot.columns:
        pivot["Combined"] = (pivot["Security"] + pivot["Data Privacy"]) / 2
    st.dataframe(
        pivot.style.background_gradient(cmap="RdYlGn", vmin=50, vmax=100),
        use_container_width=True,
    )

st.markdown("---")

# --- Full Incident Log ---
section_header("Incident Log (Current Sprint)")
incidents = query_df(f"""
    SELECT si.incident_type as type, si.severity, si.description,
           t.name as team, si.affected_file as file,
           si.pii_type, si.detected_by, si.status, si.detected_at
    FROM security_incidents si
    JOIN teams t ON si.team_id = t.id
    WHERE si.sprint_id = ?{team_sql}
    ORDER BY si.detected_at DESC
""", (sprint_id, *team_p))
if incidents:
    df = pd.DataFrame(incidents)
    df["severity"] = df["severity"].str.upper()
    df["status"] = df["status"].str.capitalize()
    st.dataframe(df, use_container_width=True, hide_index=True)
