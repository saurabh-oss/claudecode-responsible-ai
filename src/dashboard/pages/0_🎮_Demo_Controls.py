"""Demo Control Panel — inject live events and adjust metrics on the fly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import uuid
import random
import streamlit as st
from datetime import datetime

from src.data.database import query_df, execute_write, get_db
from src.dashboard.components import apply_custom_css, section_header

st.set_page_config(
    page_title="Demo Controls",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_css()


def uid() -> str:
    return str(uuid.uuid4())[:12]


# ── helpers ────────────────────────────────────────────────────────────────────

def get_teams() -> list[dict]:
    return query_df("SELECT * FROM teams ORDER BY name")


def get_latest_sprint() -> dict:
    rows = query_df("SELECT * FROM sprints ORDER BY number DESC LIMIT 1")
    return rows[0] if rows else {}


def get_sprints() -> list[dict]:
    return query_df("SELECT * FROM sprints ORDER BY number")


POLICY_IDS = [
    ("SEC-001", "No Hardcoded Secrets", "security", "critical"),
    ("SEC-002", "No SQL Injection Patterns", "security", "critical"),
    ("SEC-003", "Input Validation Required", "security", "high"),
    ("SEC-004", "No Shell Injection", "security", "critical"),
    ("CS-001", "SonarQube Quality Gate", "coding_standards", "high"),
    ("CS-002", "Code Complexity Limit", "coding_standards", "medium"),
    ("CS-003", "Docstring Coverage", "coding_standards", "low"),
    ("CS-004", "Type Hint Coverage", "coding_standards", "medium"),
    ("DP-001", "No PII in Logs", "data_privacy", "critical"),
    ("DP-002", "Data Classification Headers", "data_privacy", "high"),
    ("DP-003", "Encryption at Rest", "data_privacy", "critical"),
    ("DM-001", "No Known Vulnerabilities", "dependency_management", "high"),
    ("DM-002", "Approved Packages Only", "dependency_management", "medium"),
    ("AR-001", "API Design Standards", "architecture", "medium"),
    ("AR-002", "No Direct DB Access from UI", "architecture", "high"),
    ("TS-001", "Minimum Test Coverage", "testing", "high"),
    ("TS-002", "AI-Generated Code Tests", "testing", "high"),
    ("DC-001", "README Completeness", "documentation", "low"),
    ("PF-001", "No N+1 Queries", "performance", "medium"),
]

SAMPLE_FILES = [
    "src/auth/login_handler.py", "src/api/endpoints.py", "src/models/user.py",
    "src/services/payment.py", "src/utils/crypto.py", "src/db/queries.py",
    "src/handlers/webhook.py", "src/middleware/auth.py", "tests/test_api.py",
    "src/services/notification.py",
]

INCIDENT_TYPES = [
    ("pii_exposure", "PII data found in log output"),
    ("hardcoded_secret", "API key committed to repository"),
    ("insecure_dependency", "Critical CVE found in dependency"),
    ("sql_injection", "SQL injection pattern in AI-generated code"),
    ("unauthorized_access", "Sensitive endpoint missing auth check"),
    ("data_leak", "Customer email addresses in test fixtures"),
    ("weak_crypto", "Deprecated encryption algorithm used"),
]

CATEGORIES = ["security", "coding_standards", "data_privacy",
               "dependency_management", "architecture", "testing",
               "documentation", "performance"]

# ── page header ────────────────────────────────────────────────────────────────

st.title("🎮 Demo Control Panel")
st.caption("Inject live events and adjust metrics — changes reflect immediately across all dashboard pages.")
st.markdown("---")

teams = get_teams()
sprints = get_sprints()
latest_sprint = get_latest_sprint()

team_by_name = {t["name"]: t for t in teams}
sprint_by_name = {s["name"]: s for s in sprints}
team_names = [t["name"] for t in teams]
sprint_names = [s["name"] for s in sprints]

# ── tabs ───────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "🚨 Scenarios",
    "➕ Inject Event",
    "🎚️ Adjust Metrics",
    "🔔 Manage Alerts",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ONE-CLICK SCENARIOS
# ══════════════════════════════════════════════════════════════════════════════

with tab1:
    section_header("One-Click Demo Scenarios")
    st.markdown("Each scenario injects realistic data and fires alerts — navigate to the relevant page to see the impact.")
    st.markdown("")

    col1, col2 = st.columns(2)

    # ── Compliance Crisis ──────────────────────────────────────────────────────
    with col1:
        with st.container(border=True):
            st.markdown("#### 📉 Compliance Crisis")
            st.caption("Drops compliance scores and injects critical violations for a team.")
            target_cc = st.selectbox("Target team", team_names, key="cc_team")
            if st.button("Trigger Compliance Crisis", type="primary", use_container_width=True):
                team = team_by_name[target_cc]
                sprint = latest_sprint
                with get_db() as conn:
                    # Drop security + data_privacy + testing scores
                    for cat in ["security", "data_privacy", "testing"]:
                        conn.execute(
                            """UPDATE compliance_scores
                               SET score = MAX(20, score - 18),
                                   rules_passed = MAX(0, rules_passed - 3)
                               WHERE team_id = ? AND sprint_id = ? AND category = ?""",
                            (team["id"], sprint["id"], cat),
                        )
                    # Insert 6 critical violations
                    critical_policies = [p for p in POLICY_IDS if p[3] in ("critical", "high")]
                    for policy in random.sample(critical_policies, min(6, len(critical_policies))):
                        conn.execute(
                            """INSERT INTO policy_violations
                               (id, team_id, sprint_id, policy_id, policy_name, category,
                                severity, description, file_path, line_number, tool, resolved, detected_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)""",
                            (uid(), team["id"], sprint["id"],
                             policy[0], policy[1], policy[2], policy[3],
                             f"[DEMO] AI-generated code violates {policy[1]}",
                             random.choice(SAMPLE_FILES), random.randint(10, 400),
                             random.choice(["bandit", "semgrep", "sonarqube"]),
                             datetime.now().isoformat()),
                        )
                    # Fire critical alert
                    conn.execute(
                        """INSERT INTO alerts
                           (id, team_id, sprint_id, alert_type, severity, title, message,
                            source, acknowledged, created_at)
                           VALUES (?, ?, ?, 'compliance_drop', 'critical',
                                   'Compliance Crisis Detected',
                                   ?, 'demo_control', 0, ?)""",
                        (uid(), team["id"], sprint["id"],
                         f"[DEMO] {team['name']} compliance dropped sharply in security & data privacy categories.",
                         datetime.now().isoformat()),
                    )
                st.success(f"✅ Compliance crisis triggered for **{target_cc}**. Check the Compliance page.")

    # ── Security Breach ────────────────────────────────────────────────────────
    with col2:
        with st.container(border=True):
            st.markdown("#### 🔓 Security Breach")
            st.caption("Injects critical security incidents and fires an unacknowledged alert.")
            target_sb = st.selectbox("Target team", team_names, key="sb_team")
            if st.button("Trigger Security Breach", type="primary", use_container_width=True):
                team = team_by_name[target_sb]
                sprint = latest_sprint
                breach_incidents = [
                    ("pii_exposure", "critical", "PII data found in log output", "email"),
                    ("hardcoded_secret", "critical", "API key committed to repository", None),
                    ("sql_injection", "high", "SQL injection pattern in AI-generated code", None),
                ]
                with get_db() as conn:
                    for inc_type, sev, desc, pii in breach_incidents:
                        conn.execute(
                            """INSERT INTO security_incidents
                               (id, team_id, sprint_id, incident_type, severity, description,
                                affected_file, pii_type, detected_by, status, detected_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'demo_scanner', 'open', ?)""",
                            (uid(), team["id"], sprint["id"],
                             inc_type, sev, f"[DEMO] {desc}",
                             random.choice(SAMPLE_FILES), pii,
                             datetime.now().isoformat()),
                        )
                    conn.execute(
                        """INSERT INTO alerts
                           (id, team_id, sprint_id, alert_type, severity, title, message,
                            source, acknowledged, created_at)
                           VALUES (?, ?, ?, 'security_incident', 'critical',
                                   '🚨 Critical Security Breach',
                                   ?, 'demo_control', 0, ?)""",
                        (uid(), team["id"], sprint["id"],
                         f"[DEMO] 3 critical security incidents detected in {team['name']} — immediate action required.",
                         datetime.now().isoformat()),
                    )
                st.success(f"✅ Security breach triggered for **{target_sb}**. Check the Security page.")

    col3, col4 = st.columns(2)

    # ── Token Budget Spike ─────────────────────────────────────────────────────
    with col3:
        with st.container(border=True):
            st.markdown("#### 💸 Token Budget Spike")
            st.caption("Simulates a day of 3× token over-consumption and fires a budget alert.")
            target_tb = st.selectbox("Target team", team_names, key="tb_team")
            if st.button("Trigger Token Spike", type="primary", use_container_width=True):
                team = team_by_name[target_tb]
                sprint = latest_sprint
                models_costs = {
                    "claude-sonnet-4": (0.003, 0.015),
                    "claude-opus-4": (0.015, 0.075),
                    "gpt-4o": (0.005, 0.015),
                    "claude-haiku-4": (0.001, 0.005),
                }
                today = datetime.now().strftime("%Y-%m-%d")
                with get_db() as conn:
                    for model, (in_rate, out_rate) in models_costs.items():
                        input_tokens = team["size"] * 12000
                        output_tokens = int(input_tokens * 0.5)
                        total = input_tokens + output_tokens
                        cost = (input_tokens / 1000 * in_rate) + (output_tokens / 1000 * out_rate)
                        conn.execute(
                            """INSERT INTO token_usage
                               (id, team_id, sprint_id, date, model, input_tokens,
                                output_tokens, total_tokens, cost_usd, developer_count)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (uid(), team["id"], sprint["id"], today, model,
                             input_tokens, output_tokens, total, round(cost, 4), team["size"]),
                        )
                    conn.execute(
                        """INSERT INTO alerts
                           (id, team_id, sprint_id, alert_type, severity, title, message,
                            source, acknowledged, created_at)
                           VALUES (?, ?, ?, 'token_budget', 'high',
                                   'Token Budget Exceeded',
                                   ?, 'demo_control', 0, ?)""",
                        (uid(), team["id"], sprint["id"],
                         f"[DEMO] {team['name']} consumed 3× expected tokens today — sprint budget at risk.",
                         datetime.now().isoformat()),
                    )
                st.success(f"✅ Token spike triggered for **{target_tb}**. Check the Token Usage page.")

    # ── Adoption Milestone ─────────────────────────────────────────────────────
    with col4:
        with st.container(border=True):
            st.markdown("#### 🚀 Adoption Milestone")
            st.caption("Boosts a team's AI adoption and productivity metrics for the current sprint.")
            target_am = st.selectbox("Target team", team_names, key="am_team")
            new_adoption = st.slider("New adoption rate (%)", 60, 100, 90, key="am_adoption")
            new_productivity = st.slider("New productivity gain (%)", 20, 60, 40, key="am_prod")
            if st.button("Apply Adoption Boost", type="primary", use_container_width=True):
                team = team_by_name[target_am]
                sprint = latest_sprint
                ai_devs = int(team["size"] * new_adoption / 100)
                roi = (team["size"] * (new_productivity / 100) * 250 * 14)
                with get_db() as conn:
                    conn.execute(
                        """UPDATE adoption_metrics
                           SET adoption_rate_pct = ?,
                               ai_active_developers = ?,
                               productivity_gain_pct = ?,
                               avg_time_saved_hrs = ?,
                               roi_estimate_usd = ?
                           WHERE team_id = ? AND sprint_id = ?""",
                        (new_adoption, ai_devs, new_productivity,
                         round(ai_devs * 4.5, 1), round(roi, 2),
                         team["id"], sprint["id"]),
                    )
                    conn.execute(
                        """INSERT INTO alerts
                           (id, team_id, sprint_id, alert_type, severity, title, message,
                            source, acknowledged, created_at)
                           VALUES (?, ?, ?, 'adoption_milestone', 'info',
                                   '🎉 Adoption Milestone Reached',
                                   ?, 'demo_control', 0, ?)""",
                        (uid(), team["id"], sprint["id"],
                         f"[DEMO] {team['name']} hit {new_adoption}% AI adoption with {new_productivity}% productivity gain!",
                         datetime.now().isoformat()),
                    )
                st.success(f"✅ Adoption boosted for **{target_am}** to {new_adoption}%. Check the Adoption page.")

    st.markdown("---")

    # ── Reset ──────────────────────────────────────────────────────────────────
    section_header("Reset to Baseline")
    st.warning("This will wipe all current data and re-seed the database with the original demo dataset.")
    if st.button("🔄 Reset All Data to Baseline", type="secondary"):
        with st.spinner("Re-seeding database..."):
            from src.data.seed import seed_all
            seed_all()
        st.success("✅ Database reset to baseline. All demo changes have been cleared.")
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — INJECT EVENT
# ══════════════════════════════════════════════════════════════════════════════

with tab2:
    col_left, col_right = st.columns(2)

    # ── Add Violation ──────────────────────────────────────────────────────────
    with col_left:
        section_header("Inject Policy Violation")
        with st.form("add_violation"):
            v_team = st.selectbox("Team", team_names, key="v_team")
            v_sprint = st.selectbox("Sprint", sprint_names, index=len(sprint_names) - 1, key="v_sprint")
            policy_labels = [f"{p[0]} — {p[1]} ({p[3]})" for p in POLICY_IDS]
            v_policy_idx = st.selectbox("Policy", range(len(policy_labels)),
                                        format_func=lambda i: policy_labels[i])
            v_file = st.selectbox("File", SAMPLE_FILES)
            v_line = st.number_input("Line number", min_value=1, max_value=999, value=42)
            v_desc = st.text_input("Description (optional)",
                                   placeholder="AI-generated code bypasses validation...")
            v_tool = st.selectbox("Detected by", ["bandit", "semgrep", "sonarqube",
                                                   "gitleaks", "custom_pii_scanner", "safety"])
            submitted = st.form_submit_button("➕ Add Violation", use_container_width=True, type="primary")
            if submitted:
                team = team_by_name[v_team]
                sprint = sprint_by_name[v_sprint]
                policy = POLICY_IDS[v_policy_idx]
                execute_write(
                    """INSERT INTO policy_violations
                       (id, team_id, sprint_id, policy_id, policy_name, category,
                        severity, description, file_path, line_number, tool, resolved, detected_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)""",
                    (uid(), team["id"], sprint["id"],
                     policy[0], policy[1], policy[2], policy[3],
                     v_desc or f"[DEMO] Violation of {policy[1]}",
                     v_file, int(v_line), v_tool,
                     datetime.now().isoformat()),
                )
                st.success(f"✅ **{policy[0]}** violation added for {v_team} in {v_sprint}.")

    # ── Add Security Incident ──────────────────────────────────────────────────
    with col_right:
        section_header("Inject Security Incident")
        with st.form("add_incident"):
            i_team = st.selectbox("Team", team_names, key="i_team")
            i_sprint = st.selectbox("Sprint", sprint_names, index=len(sprint_names) - 1, key="i_sprint")
            inc_labels = [f"{t} — {d}" for t, d in INCIDENT_TYPES]
            i_type_idx = st.selectbox("Incident type", range(len(inc_labels)),
                                      format_func=lambda i: inc_labels[i])
            i_severity = st.selectbox("Severity", ["critical", "high", "medium", "low"])
            i_file = st.selectbox("Affected file", SAMPLE_FILES, key="i_file")
            pii_types = ["None", "email", "phone", "ssn", "credit_card", "address", "name"]
            i_pii = st.selectbox("PII type (if applicable)", pii_types)
            i_detector = st.selectbox("Detected by", ["gitleaks", "bandit", "semgrep",
                                                       "custom_scanner", "manual_review"])
            i_submitted = st.form_submit_button("➕ Add Incident", use_container_width=True, type="primary")
            if i_submitted:
                team = team_by_name[i_team]
                sprint = sprint_by_name[i_sprint]
                inc_type, inc_desc = INCIDENT_TYPES[i_type_idx]
                execute_write(
                    """INSERT INTO security_incidents
                       (id, team_id, sprint_id, incident_type, severity, description,
                        affected_file, pii_type, detected_by, status, detected_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)""",
                    (uid(), team["id"], sprint["id"],
                     inc_type, i_severity, f"[DEMO] {inc_desc}",
                     i_file, None if i_pii == "None" else i_pii,
                     i_detector, datetime.now().isoformat()),
                )
                st.success(f"✅ **{inc_type}** incident ({i_severity}) added for {i_team}.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ADJUST METRICS
# ══════════════════════════════════════════════════════════════════════════════

with tab3:
    col_l, col_r = st.columns(2)

    # ── Compliance Score ───────────────────────────────────────────────────────
    with col_l:
        section_header("Adjust Compliance Score")
        with st.form("adjust_compliance"):
            ac_team = st.selectbox("Team", team_names, key="ac_team")
            ac_sprint = st.selectbox("Sprint", sprint_names, index=len(sprint_names) - 1, key="ac_sprint")
            ac_category = st.selectbox("Category", CATEGORIES)
            # Load current score
            team_id = team_by_name[ac_team]["id"]
            sprint_id = sprint_by_name[ac_sprint]["id"]
            current = query_df(
                "SELECT score FROM compliance_scores WHERE team_id=? AND sprint_id=? AND category=?",
                (team_id, sprint_id, ac_category),
            )
            current_score = int(current[0]["score"]) if current else 75
            ac_score = st.slider(f"New score (current: {current_score}%)", 0, 100, current_score)
            ac_submitted = st.form_submit_button("✅ Apply Score", use_container_width=True, type="primary")
            if ac_submitted:
                total = 12
                passed = int(total * ac_score / 100)
                execute_write(
                    """UPDATE compliance_scores
                       SET score = ?, rules_passed = ?
                       WHERE team_id = ? AND sprint_id = ? AND category = ?""",
                    (ac_score, passed, team_id, sprint_id, ac_category),
                )
                st.success(f"✅ {ac_team} — {ac_category} set to **{ac_score}%** in {ac_sprint}.")

    # ── Adoption Metrics ───────────────────────────────────────────────────────
    with col_r:
        section_header("Adjust Adoption Metrics")
        with st.form("adjust_adoption"):
            aa_team = st.selectbox("Team", team_names, key="aa_team")
            aa_sprint = st.selectbox("Sprint", sprint_names, index=len(sprint_names) - 1, key="aa_sprint")
            team_obj = team_by_name[aa_team]
            sprint_obj = sprint_by_name[aa_sprint]
            cur_adopt = query_df(
                "SELECT adoption_rate_pct, productivity_gain_pct FROM adoption_metrics WHERE team_id=? AND sprint_id=?",
                (team_obj["id"], sprint_obj["id"]),
            )
            cur_rate = int(cur_adopt[0]["adoption_rate_pct"]) if cur_adopt else 50
            cur_prod = int(cur_adopt[0]["productivity_gain_pct"]) if cur_adopt else 15
            aa_rate = st.slider(f"Adoption rate % (current: {cur_rate}%)", 0, 100, cur_rate)
            aa_prod = st.slider(f"Productivity gain % (current: {cur_prod}%)", 0, 60, cur_prod)
            aa_submitted = st.form_submit_button("✅ Apply Metrics", use_container_width=True, type="primary")
            if aa_submitted:
                ai_devs = int(team_obj["size"] * aa_rate / 100)
                roi = round(ai_devs * aa_prod / 100 * 250 * 14, 2)
                execute_write(
                    """UPDATE adoption_metrics
                       SET adoption_rate_pct = ?,
                           ai_active_developers = ?,
                           productivity_gain_pct = ?,
                           roi_estimate_usd = ?
                       WHERE team_id = ? AND sprint_id = ?""",
                    (aa_rate, ai_devs, aa_prod, roi, team_obj["id"], sprint_obj["id"]),
                )
                st.success(f"✅ {aa_team} adoption → **{aa_rate}%**, productivity → **{aa_prod}%** in {aa_sprint}.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — MANAGE ALERTS
# ══════════════════════════════════════════════════════════════════════════════

with tab4:
    section_header("Active Alerts")

    open_alerts = query_df("""
        SELECT a.*, t.name as team_name
        FROM alerts a
        LEFT JOIN teams t ON a.team_id = t.id
        WHERE a.acknowledged = 0
        ORDER BY CASE a.severity
            WHEN 'critical' THEN 1 WHEN 'high' THEN 2
            WHEN 'medium' THEN 3 ELSE 4
        END, a.created_at DESC
    """)

    severity_colors = {
        "critical": "#E24B4A", "high": "#D85A30",
        "medium": "#BA7517", "info": "#378ADD", "warning": "#BA7517",
    }

    if not open_alerts:
        st.success("✅ No unacknowledged alerts.")
    else:
        st.markdown(f"**{len(open_alerts)} unacknowledged alert(s)**")
        for alert in open_alerts:
            color = severity_colors.get(alert["severity"], "#888780")
            col_msg, col_btn = st.columns([5, 1])
            with col_msg:
                st.markdown(
                    f'<div style="padding:10px 14px; background:#f8f7f4; border-left:4px solid {color}; '
                    f'border-radius:6px; margin-bottom:6px;">'
                    f'<strong>[{alert["severity"].upper()}]</strong> {alert["team_name"] or "–"} — {alert["message"]}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col_btn:
                if st.button("Acknowledge", key=f"ack_{alert['id']}"):
                    execute_write(
                        "UPDATE alerts SET acknowledged = 1 WHERE id = ?",
                        (alert["id"],),
                    )
                    st.rerun()

    st.markdown("---")
    section_header("Create Custom Alert")
    with st.form("create_alert"):
        ca_team = st.selectbox("Team", team_names, key="ca_team")
        ca_sprint = st.selectbox("Sprint", sprint_names, index=len(sprint_names) - 1, key="ca_sprint")
        ca_type = st.selectbox("Alert type", ["compliance_drop", "security_incident",
                                               "token_budget", "quality_gate", "adoption_milestone"])
        ca_severity = st.selectbox("Severity", ["critical", "high", "medium", "info"])
        ca_title = st.text_input("Title", placeholder="e.g. Compliance threshold breached")
        ca_message = st.text_area("Message", placeholder="Describe what happened...", height=80)
        ca_submitted = st.form_submit_button("📣 Fire Alert", use_container_width=True, type="primary")
        if ca_submitted and ca_title:
            team = team_by_name[ca_team]
            sprint = sprint_by_name[ca_sprint]
            execute_write(
                """INSERT INTO alerts
                   (id, team_id, sprint_id, alert_type, severity, title, message,
                    source, acknowledged, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'demo_control', 0, ?)""",
                (uid(), team["id"], sprint["id"],
                 ca_type, ca_severity, ca_title, ca_message,
                 datetime.now().isoformat()),
            )
            st.success(f"✅ Alert fired: **{ca_title}**")
            st.rerun()

    st.markdown("---")
    col_ack, col_del = st.columns(2)
    with col_ack:
        if st.button("✅ Acknowledge All Alerts", use_container_width=True):
            execute_write("UPDATE alerts SET acknowledged = 1")
            st.success("All alerts acknowledged.")
            st.rerun()
    with col_del:
        if st.button("🗑️ Delete Demo-Injected Alerts", use_container_width=True):
            execute_write("DELETE FROM alerts WHERE source = 'demo_control'")
            st.success("Demo alerts deleted.")
            st.rerun()
