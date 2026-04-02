"""Generate realistic demo data for the Responsible AI Governance dashboard.

Creates a narrative across 4 teams and 6 sprints:
- Platform Engineering: High AI adoption, good compliance, moderate cost
- Data Services: Moderate adoption, best compliance, low cost
- Customer Portal: Aggressive AI adoption, compliance drift, high cost
- ML Ops: Low adoption initially, rapid ramp-up, security incidents
"""

import random
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.database import init_db, get_db

random.seed(42)  # Reproducible data


def uid() -> str:
    return str(uuid.uuid4())[:12]


def seed_all():
    """Main seeding function."""
    init_db()

    with get_db() as conn:
        # Clear existing data
        for table in [
            "alerts", "lifecycle_metrics", "security_incidents",
            "adoption_metrics", "token_usage", "code_quality_metrics",
            "compliance_scores", "policy_violations", "sprints", "teams",
        ]:
            conn.execute(f"DELETE FROM {table}")

        teams = seed_teams(conn)
        sprints = seed_sprints(conn)
        seed_policy_violations(conn, teams, sprints)
        seed_compliance_scores(conn, teams, sprints)
        seed_code_quality(conn, teams, sprints)
        seed_token_usage(conn, teams, sprints)
        seed_adoption_metrics(conn, teams, sprints)
        seed_security_incidents(conn, teams, sprints)
        seed_lifecycle_metrics(conn, teams, sprints)
        seed_alerts(conn, teams, sprints)

    print("✅ Demo data seeded successfully!")
    print(f"   Database: {Path(__file__).parent.parent.parent / 'data' / 'governance.db'}")
    print(f"   Teams: {len(teams)}")
    print(f"   Sprints: {len(sprints)}")


def seed_teams(conn) -> list[dict]:
    teams = [
        {"id": "team-plat", "name": "Platform Engineering", "size": 12, "lead": "Ananya Sharma"},
        {"id": "team-data", "name": "Data Services", "size": 8, "lead": "Ravi Krishnan"},
        {"id": "team-portal", "name": "Customer Portal", "size": 15, "lead": "Priya Desai"},
        {"id": "team-mlops", "name": "ML Ops", "size": 6, "lead": "Vikram Mehta"},
    ]
    for t in teams:
        conn.execute(
            "INSERT INTO teams (id, name, size, lead) VALUES (?, ?, ?, ?)",
            (t["id"], t["name"], t["size"], t["lead"]),
        )
    return teams


def seed_sprints(conn) -> list[dict]:
    sprints = []
    base = datetime(2025, 10, 1)
    for i in range(6):
        s = {
            "id": f"sprint-{i+1}",
            "name": f"Sprint {i+1}",
            "number": i + 1,
            "start_date": (base + timedelta(days=14 * i)).strftime("%Y-%m-%d"),
            "end_date": (base + timedelta(days=14 * i + 13)).strftime("%Y-%m-%d"),
        }
        conn.execute(
            "INSERT INTO sprints (id, name, number, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            (s["id"], s["name"], s["number"], s["start_date"], s["end_date"]),
        )
        sprints.append(s)
    return sprints


# --- Team behavior profiles (per sprint, indexed 0-5) ---
# Each profile defines how a team's metrics evolve across sprints

PROFILES = {
    "team-plat": {
        "desc": "Steady adopter, good governance",
        "adoption_rate": [0.50, 0.58, 0.67, 0.75, 0.83, 0.83],
        "compliance_base": [82, 84, 86, 88, 89, 91],
        "violations_per_sprint": [18, 15, 12, 10, 8, 7],
        "token_multiplier": [0.8, 0.9, 1.0, 1.1, 1.1, 1.05],
        "quality_trend": [72, 74, 76, 79, 81, 83],
        "security_incidents": [2, 1, 1, 0, 1, 0],
        "productivity_gain": [8, 12, 18, 22, 25, 28],
    },
    "team-data": {
        "desc": "Conservative adopter, best compliance",
        "adoption_rate": [0.25, 0.38, 0.50, 0.50, 0.63, 0.63],
        "compliance_base": [90, 91, 92, 93, 94, 95],
        "violations_per_sprint": [6, 5, 4, 3, 3, 2],
        "token_multiplier": [0.4, 0.5, 0.7, 0.7, 0.8, 0.8],
        "quality_trend": [80, 82, 83, 85, 86, 88],
        "security_incidents": [0, 0, 1, 0, 0, 0],
        "productivity_gain": [5, 8, 12, 14, 16, 18],
    },
    "team-portal": {
        "desc": "Aggressive adopter, compliance drift, high cost",
        "adoption_rate": [0.60, 0.73, 0.80, 0.87, 0.93, 0.93],
        "compliance_base": [78, 74, 70, 68, 72, 76],
        "violations_per_sprint": [22, 28, 35, 38, 30, 24],
        "token_multiplier": [1.2, 1.5, 1.8, 2.2, 2.0, 1.7],
        "quality_trend": [68, 65, 62, 60, 64, 68],
        "security_incidents": [3, 4, 5, 6, 4, 3],
        "productivity_gain": [15, 22, 30, 35, 32, 30],
    },
    "team-mlops": {
        "desc": "Late starter, rapid ramp-up, learning curve",
        "adoption_rate": [0.17, 0.33, 0.50, 0.67, 0.83, 0.83],
        "compliance_base": [85, 80, 75, 78, 82, 86],
        "violations_per_sprint": [4, 10, 16, 14, 10, 6],
        "token_multiplier": [0.3, 0.6, 1.0, 1.4, 1.3, 1.1],
        "quality_trend": [78, 74, 70, 73, 77, 80],
        "security_incidents": [0, 1, 3, 2, 1, 0],
        "productivity_gain": [3, 8, 15, 22, 28, 32],
    },
}

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
    "src/services/notification.py", "src/models/order.py", "config/settings.py",
    "src/agents/code_review.py", "src/pipelines/etl.py", "src/ml/inference.py",
]

TOOLS = ["bandit", "gitleaks", "semgrep", "sonarqube", "custom_pii_scanner", "safety"]


def seed_policy_violations(conn, teams, sprints):
    for team in teams:
        profile = PROFILES[team["id"]]
        for si, sprint in enumerate(sprints):
            count = profile["violations_per_sprint"][si]
            # Bias toward certain categories based on team
            for _ in range(count):
                policy = random.choice(POLICY_IDS)
                resolved = random.random() < (0.6 + si * 0.05)
                detected = datetime.strptime(sprint["start_date"], "%Y-%m-%d") + timedelta(
                    days=random.randint(0, 13)
                )
                conn.execute(
                    """INSERT INTO policy_violations
                    (id, team_id, sprint_id, policy_id, policy_name, category, severity,
                     description, file_path, line_number, tool, resolved, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        uid(), team["id"], sprint["id"],
                        policy[0], policy[1], policy[2], policy[3],
                        f"Violation of {policy[1]} detected in AI-generated code",
                        random.choice(SAMPLE_FILES),
                        random.randint(10, 500),
                        random.choice(TOOLS),
                        1 if resolved else 0,
                        detected.isoformat(),
                    ),
                )


def seed_compliance_scores(conn, teams, sprints):
    categories = ["security", "coding_standards", "data_privacy",
                   "dependency_management", "architecture", "testing",
                   "documentation", "performance"]
    for team in teams:
        profile = PROFILES[team["id"]]
        for si, sprint in enumerate(sprints):
            base = profile["compliance_base"][si]
            for cat in categories:
                # Vary score by category
                offsets = {
                    "security": -3, "coding_standards": 2, "data_privacy": -5,
                    "dependency_management": 5, "architecture": 3, "testing": -2,
                    "documentation": 8, "performance": 0,
                }
                score = max(0, min(100, base + offsets.get(cat, 0) + random.randint(-4, 4)))
                total_rules = random.randint(8, 15)
                passed = int(total_rules * score / 100)
                conn.execute(
                    """INSERT INTO compliance_scores
                    (id, team_id, sprint_id, category, score, total_rules, rules_passed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (uid(), team["id"], sprint["id"], cat, score, total_rules, passed),
                )


def seed_code_quality(conn, teams, sprints):
    for team in teams:
        profile = PROFILES[team["id"]]
        for si, sprint in enumerate(sprints):
            quality = profile["quality_trend"][si]
            ai_pct = profile["adoption_rate"][si]
            total_lines = random.randint(3000, 8000) * (1 + ai_pct * 0.5)
            ai_lines = int(total_lines * ai_pct * 0.6)
            human_lines = int(total_lines - ai_lines)
            conn.execute(
                """INSERT INTO code_quality_metrics
                (id, team_id, sprint_id, sonarqube_score, complexity_avg,
                 duplication_pct, test_coverage_pct, docstring_coverage_pct,
                 type_hint_coverage_pct, ai_generated_lines, human_authored_lines,
                 flagged_ai_snippets, bugs_found, code_smells, vulnerabilities)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    uid(), team["id"], sprint["id"],
                    quality + random.uniform(-2, 2),
                    random.uniform(5, 15) - (si * 0.5),
                    random.uniform(3, 12) - (si * 0.3),
                    quality * 0.85 + random.uniform(-3, 3),
                    quality * 0.7 + random.uniform(-5, 5),
                    quality * 0.6 + random.uniform(-5, 5),
                    ai_lines, human_lines,
                    max(0, int(ai_lines / 500 * random.uniform(0.5, 2.0))),
                    random.randint(2, 15),
                    random.randint(5, 40),
                    random.randint(0, 5),
                ),
            )


def seed_token_usage(conn, teams, sprints):
    models = ["claude-sonnet-4", "claude-opus-4", "gpt-4o", "claude-haiku-4"]
    costs = {
        "claude-sonnet-4": (0.003, 0.015),
        "claude-opus-4": (0.015, 0.075),
        "gpt-4o": (0.005, 0.015),
        "claude-haiku-4": (0.001, 0.005),
    }
    for team in teams:
        profile = PROFILES[team["id"]]
        for si, sprint in enumerate(sprints):
            base_date = datetime.strptime(sprint["start_date"], "%Y-%m-%d")
            multiplier = profile["token_multiplier"][si]
            devs_using = int(team["size"] * profile["adoption_rate"][si])
            for day in range(14):
                date = base_date + timedelta(days=day)
                if date.weekday() >= 5:  # Weekend - lower usage
                    day_mult = 0.2
                else:
                    day_mult = 1.0
                for model in models:
                    # Weight models: haiku most used, opus least
                    model_weights = {
                        "claude-sonnet-4": 0.35,
                        "claude-opus-4": 0.10,
                        "gpt-4o": 0.20,
                        "claude-haiku-4": 0.35,
                    }
                    base_tokens = int(
                        devs_using * 5000 * multiplier * day_mult * model_weights[model]
                    )
                    input_tokens = base_tokens + random.randint(-500, 500)
                    output_tokens = int(input_tokens * random.uniform(0.3, 0.7))
                    total = input_tokens + output_tokens
                    in_cost, out_cost = costs[model]
                    cost = (input_tokens / 1000 * in_cost) + (output_tokens / 1000 * out_cost)

                    if input_tokens > 0:
                        conn.execute(
                            """INSERT INTO token_usage
                            (id, team_id, sprint_id, date, model, input_tokens,
                             output_tokens, total_tokens, cost_usd, developer_count)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                uid(), team["id"], sprint["id"],
                                date.strftime("%Y-%m-%d"), model,
                                max(0, input_tokens), max(0, output_tokens),
                                max(0, total), round(max(0, cost), 4), devs_using,
                            ),
                        )


def seed_adoption_metrics(conn, teams, sprints):
    for team in teams:
        profile = PROFILES[team["id"]]
        for si, sprint in enumerate(sprints):
            adoption = profile["adoption_rate"][si]
            ai_devs = int(team["size"] * adoption)
            prod_gain = profile["productivity_gain"][si]
            baseline_velocity = team["size"] * random.randint(4, 7)
            sprint_velocity = int(baseline_velocity * (1 + prod_gain / 100))
            # ROI: (velocity_gain * avg_dev_cost_per_point) - token_cost
            avg_cost_per_point = 250  # USD
            velocity_gain = sprint_velocity - baseline_velocity
            roi = velocity_gain * avg_cost_per_point  # simplified
            conn.execute(
                """INSERT INTO adoption_metrics
                (id, team_id, sprint_id, total_developers, ai_active_developers,
                 adoption_rate_pct, ai_assisted_commits_pct, avg_time_saved_hrs,
                 productivity_gain_pct, sprint_velocity_points,
                 baseline_velocity_points, roi_estimate_usd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    uid(), team["id"], sprint["id"],
                    team["size"], ai_devs,
                    round(adoption * 100, 1),
                    round(adoption * 75 + random.uniform(-5, 5), 1),
                    round(ai_devs * random.uniform(2, 6), 1),
                    round(prod_gain + random.uniform(-2, 2), 1),
                    sprint_velocity, baseline_velocity,
                    round(roi + random.uniform(-200, 200), 2),
                ),
            )


def seed_security_incidents(conn, teams, sprints):
    incident_types = [
        ("pii_exposure", "PII data found in log output"),
        ("hardcoded_secret", "API key committed to repository"),
        ("insecure_dependency", "Critical CVE in dependency"),
        ("sql_injection", "SQL injection pattern in AI-generated code"),
        ("unauthorized_access", "Sensitive endpoint without auth check"),
        ("data_leak", "Customer email addresses in test fixtures"),
        ("weak_crypto", "Deprecated encryption algorithm used"),
    ]
    pii_types = ["email", "phone", "ssn", "credit_card", "address", "name", None]

    for team in teams:
        profile = PROFILES[team["id"]]
        for si, sprint in enumerate(sprints):
            count = profile["security_incidents"][si]
            for _ in range(count):
                inc_type, desc = random.choice(incident_types)
                severity = random.choices(
                    ["critical", "high", "medium"], weights=[0.2, 0.5, 0.3]
                )[0]
                status = random.choices(
                    ["open", "investigating", "resolved", "resolved"],
                    weights=[0.15, 0.15, 0.4, 0.3],
                )[0]
                detected = datetime.strptime(sprint["start_date"], "%Y-%m-%d") + timedelta(
                    days=random.randint(0, 13)
                )
                conn.execute(
                    """INSERT INTO security_incidents
                    (id, team_id, sprint_id, incident_type, severity, description,
                     affected_file, pii_type, detected_by, status, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        uid(), team["id"], sprint["id"],
                        inc_type, severity, desc,
                        random.choice(SAMPLE_FILES),
                        random.choice(pii_types) if "pii" in inc_type or "data" in inc_type else None,
                        random.choice(["gitleaks", "bandit", "semgrep", "custom_scanner", "manual_review"]),
                        status, detected.isoformat(),
                    ),
                )


def seed_lifecycle_metrics(conn, teams, sprints):
    stages = ["requirements", "design", "development", "testing", "deployment", "monitoring"]
    for team in teams:
        profile = PROFILES[team["id"]]
        for si, sprint in enumerate(sprints):
            base_compliance = profile["compliance_base"][si]
            ai_adoption = profile["adoption_rate"][si]
            for stage in stages:
                stage_offsets = {
                    "requirements": {"monitored": 0.7, "compliance": -5, "ai_cov": 0.3, "test_auto": 0},
                    "design": {"monitored": 0.6, "compliance": 0, "ai_cov": 0.2, "test_auto": 0},
                    "development": {"monitored": 0.95, "compliance": 5, "ai_cov": 0.8, "test_auto": 0.3},
                    "testing": {"monitored": 0.9, "compliance": 3, "ai_cov": 0.6, "test_auto": 0.7},
                    "deployment": {"monitored": 0.85, "compliance": 2, "ai_cov": 0.4, "test_auto": 0.5},
                    "monitoring": {"monitored": 0.75, "compliance": -3, "ai_cov": 0.3, "test_auto": 0.4},
                }
                off = stage_offsets[stage]
                is_monitored = 1 if random.random() < (off["monitored"] + si * 0.03) else 0
                compliance = max(0, min(100, base_compliance + off["compliance"] + random.randint(-3, 3)))
                ai_cov = min(100, ai_adoption * 100 * off["ai_cov"] + random.uniform(-5, 5))
                test_auto = min(100, off["test_auto"] * 100 + si * 3 + random.uniform(-5, 5))
                defects = random.randint(1, 10)
                leaked = max(0, int(defects * random.uniform(0.05, 0.25) * (1 - si * 0.03)))
                pipeline = min(100, 80 + si * 2.5 + random.uniform(-5, 5))

                conn.execute(
                    """INSERT INTO lifecycle_metrics
                    (id, team_id, sprint_id, stage, is_monitored, compliance_pct,
                     ai_coverage_pct, test_automation_pct, defects_found,
                     defects_leaked, pipeline_pass_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        uid(), team["id"], sprint["id"], stage,
                        is_monitored, round(compliance, 1),
                        round(max(0, ai_cov), 1), round(max(0, test_auto), 1),
                        defects, leaked, round(pipeline, 1),
                    ),
                )


def seed_alerts(conn, teams, sprints):
    alert_templates = [
        ("token_budget", "warning", "Token budget threshold reached",
         "{team} has consumed {pct}% of sprint token budget"),
        ("compliance_drop", "high", "Compliance score dropped",
         "{team} compliance dropped below {threshold}% in {category}"),
        ("security_incident", "critical", "New security incident",
         "PII exposure detected in {team} codebase"),
        ("quality_gate", "medium", "Quality gate failure",
         "{team} failed SonarQube quality gate in Sprint {sprint}"),
        ("adoption_milestone", "info", "Adoption milestone",
         "{team} reached {pct}% AI adoption rate"),
    ]
    for team in teams:
        for si, sprint in enumerate(sprints):
            # Generate 1-3 alerts per team per sprint
            n_alerts = random.randint(1, 3)
            for _ in range(n_alerts):
                tmpl = random.choice(alert_templates)
                msg = tmpl[3].format(
                    team=team["name"],
                    pct=random.randint(75, 110),
                    threshold=random.randint(60, 80),
                    category=random.choice(["security", "coding_standards", "data_privacy"]),
                    sprint=sprint["number"],
                )
                conn.execute(
                    """INSERT INTO alerts
                    (id, team_id, sprint_id, alert_type, severity, title, message,
                     source, acknowledged, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        uid(), team["id"], sprint["id"],
                        tmpl[0], tmpl[1], tmpl[2], msg,
                        "governance_engine",
                        1 if random.random() < 0.6 else 0,
                        (datetime.strptime(sprint["start_date"], "%Y-%m-%d")
                         + timedelta(days=random.randint(0, 13))).isoformat(),
                    ),
                )


if __name__ == "__main__":
    seed_all()
