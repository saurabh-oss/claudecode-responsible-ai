"""Page 3: AI Token Usage — Consumption trends, cost breakdown, budget tracking."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from src.data.database import query_df
from src.dashboard.components import apply_custom_css, metric_card, section_header
from src.utils.helpers import TEAM_COLORS, format_number, format_currency

st.set_page_config(page_title="Token Usage & Cost", page_icon="💰", layout="wide")
apply_custom_css()
st.title("💰 AI Token Usage & Cost")
st.caption("Token consumption trends, cost breakdown by team and model, budget tracking")

sprints = query_df("SELECT * FROM sprints ORDER BY number")
teams = query_df("SELECT * FROM teams ORDER BY name")
col_f1, col_f2 = st.columns(2)
with col_f1:
    sel_sprint = st.selectbox("Sprint", [s["name"] for s in sprints], index=len(sprints)-1, key="tk_sp")
    sprint_id = next(s["id"] for s in sprints if s["name"] == sel_sprint)
with col_f2:
    sel_team = st.selectbox("Team", ["All Teams"] + [t["name"] for t in teams], key="tk_tm")

team_sql = ""
team_p = ()
if sel_team != "All Teams":
    tid = next(t["id"] for t in teams if t["name"] == sel_team)
    team_sql = " AND tu.team_id = ?"
    team_p = (tid,)

st.markdown("---")

# --- KPIs ---
kpi = query_df(f"""
    SELECT SUM(total_tokens) as total_tokens, SUM(cost_usd) as total_cost,
           SUM(input_tokens) as input_t, SUM(output_tokens) as output_t,
           COUNT(DISTINCT date) as active_days
    FROM token_usage tu WHERE tu.sprint_id = ?{team_sql}
""", (sprint_id, *team_p))

# Previous sprint for delta
sprint_num = next(s["number"] for s in sprints if s["id"] == sprint_id)
prev_id = next((s["id"] for s in sprints if s["number"] == sprint_num - 1), None)
prev_cost = 0
if prev_id:
    pc = query_df(f"SELECT SUM(cost_usd) as v FROM token_usage tu WHERE tu.sprint_id = ?{team_sql}",
                  (prev_id, *team_p))
    prev_cost = pc[0]["v"] if pc and pc[0]["v"] else 0

k = kpi[0] if kpi else {}
total_tokens = k.get("total_tokens") or 0
total_cost = k.get("total_cost") or 0
cost_delta = total_cost - prev_cost

# Budget: 150K tokens/dev/sprint × team sizes
if sel_team == "All Teams":
    budget_tokens = sum(t["size"] for t in teams) * 150000 * 1.2
else:
    tsize = next(t["size"] for t in teams if t["name"] == sel_team)
    budget_tokens = tsize * 150000 * 1.2

budget_pct = (total_tokens / budget_tokens * 100) if budget_tokens > 0 else 0

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    metric_card("Total Tokens", format_number(total_tokens, 0), "", "neutral", "#534AB7")
with c2:
    metric_card("Total Cost", format_currency(total_cost),
                f"{'↑' if cost_delta > 0 else '↓'} {format_currency(abs(cost_delta))} vs prev",
                "negative" if cost_delta > 0 else "positive", "#D85A30")
with c3:
    avg_daily = total_cost / max(1, k.get("active_days") or 1)
    metric_card("Avg Daily Cost", format_currency(avg_daily), "", "neutral", "#1D9E75")
with c4:
    metric_card("Budget Utilization", f"{budget_pct:.0f}%", f"of {format_number(budget_tokens, 0)} budget",
                "negative" if budget_pct > 100 else "positive" if budget_pct < 80 else "neutral",
                "#E24B4A" if budget_pct > 100 else "#BA7517" if budget_pct > 80 else "#639922")
with c5:
    io_ratio = (k.get("input_t") or 0) / max(1, (k.get("output_t") or 1))
    metric_card("Input/Output Ratio", f"{io_ratio:.1f}x", "", "neutral", "#378ADD")

st.markdown("---")

# --- Daily Consumption Trend ---
section_header("Daily Token Consumption (Current Sprint)")
daily = query_df(f"""
    SELECT date, SUM(total_tokens) as tokens, SUM(cost_usd) as cost
    FROM token_usage tu WHERE tu.sprint_id = ?{team_sql}
    GROUP BY date ORDER BY date
""", (sprint_id, *team_p))

if daily:
    df_d = pd.DataFrame(daily)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_d["date"], y=df_d["tokens"], name="Tokens",
                         marker_color="#534AB7", opacity=0.7, yaxis="y"))
    fig.add_trace(go.Scatter(x=df_d["date"], y=df_d["cost"], name="Cost ($)",
                             line=dict(color="#D85A30", width=3), yaxis="y2", mode="lines+markers"))
    fig.update_layout(
        height=350, margin=dict(l=10, r=50, t=10, b=10),
        yaxis=dict(title="Tokens", gridcolor="#e8e6e0"),
        yaxis2=dict(title="Cost (USD)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=-0.15),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- Cost by Model & Cost by Team ---
col_l, col_r = st.columns(2)

with col_l:
    section_header("Cost Breakdown by Model")
    model_data = query_df(f"""
        SELECT model, SUM(cost_usd) as cost, SUM(total_tokens) as tokens
        FROM token_usage tu WHERE tu.sprint_id = ?{team_sql}
        GROUP BY model ORDER BY cost DESC
    """, (sprint_id, *team_p))
    if model_data:
        df_m = pd.DataFrame(model_data)
        model_colors = {
            "claude-sonnet-4": "#534AB7", "claude-opus-4": "#D4537E",
            "gpt-4o": "#1D9E75", "claude-haiku-4": "#378ADD",
        }
        fig_m = px.pie(df_m, names="model", values="cost",
                       color="model", color_discrete_map=model_colors, hole=0.45)
        fig_m.update_traces(textinfo="label+percent", textposition="outside")
        fig_m.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=40),
                            paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig_m, use_container_width=True)

with col_r:
    section_header("Cost by Team (Current Sprint)")
    team_cost = query_df("""
        SELECT t.name as team, SUM(tu.cost_usd) as cost, SUM(tu.total_tokens) as tokens
        FROM token_usage tu
        JOIN teams t ON tu.team_id = t.id
        WHERE tu.sprint_id = ?
        GROUP BY t.name ORDER BY cost DESC
    """, (sprint_id,))
    if team_cost:
        df_tc = pd.DataFrame(team_cost)
        fig_tc = go.Figure(go.Bar(
            x=df_tc["team"], y=df_tc["cost"],
            marker_color=[TEAM_COLORS.get(t, "#888") for t in df_tc["team"]],
            text=df_tc["cost"].apply(lambda x: f"${x:,.2f}"),
            textposition="auto",
        ))
        fig_tc.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10),
                             yaxis=dict(title="Cost (USD)"),
                             paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig_tc.update_yaxes(gridcolor="#e8e6e0")
        st.plotly_chart(fig_tc, use_container_width=True)

st.markdown("---")

# --- Sprint-over-Sprint Cost Trend ---
section_header("Cost Trend Across Sprints")
sprint_trend = query_df("""
    SELECT s.name as sprint, t.name as team, SUM(tu.cost_usd) as cost
    FROM token_usage tu
    JOIN teams t ON tu.team_id = t.id
    JOIN sprints s ON tu.sprint_id = s.id
    GROUP BY s.name, t.name, s.number ORDER BY s.number
""")
if sprint_trend:
    df_st = pd.DataFrame(sprint_trend)
    fig_st = px.bar(df_st, x="sprint", y="cost", color="team",
                    color_discrete_map=TEAM_COLORS, barmode="stack",
                    text_auto=".2s")
    fig_st.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10),
                         yaxis=dict(title="Cost (USD)"),
                         legend=dict(orientation="h", y=-0.15),
                         paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig_st.update_yaxes(gridcolor="#e8e6e0")
    st.plotly_chart(fig_st, use_container_width=True)

st.markdown("---")

# --- Cost per Developer ---
section_header("Cost per Developer (Current Sprint)")
dev_cost = query_df("""
    SELECT t.name as team, t.size,
           SUM(tu.cost_usd) as total_cost,
           ROUND(SUM(tu.cost_usd) / t.size, 2) as cost_per_dev,
           ROUND(SUM(tu.total_tokens) / t.size, 0) as tokens_per_dev
    FROM token_usage tu
    JOIN teams t ON tu.team_id = t.id
    WHERE tu.sprint_id = ?
    GROUP BY t.name, t.size
    ORDER BY cost_per_dev DESC
""", (sprint_id,))
if dev_cost:
    df_dc = pd.DataFrame(dev_cost)
    st.dataframe(df_dc.style.format({
        "total_cost": "${:,.2f}", "cost_per_dev": "${:,.2f}", "tokens_per_dev": "{:,.0f}"
    }).background_gradient(subset=["cost_per_dev"], cmap="YlOrRd"),
        use_container_width=True, hide_index=True)
