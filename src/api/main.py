"""FastAPI REST API for the Responsible AI Governance Platform."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from src.data.database import query_df, get_db, init_db

app = FastAPI(
    title="Responsible AI Governance API",
    description="REST API for querying governance metrics, violations, and compliance data.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


# === Health ===
@app.get("/health")
def health():
    return {"status": "healthy", "service": "responsible-ai-governance", "timestamp": datetime.utcnow().isoformat()}


# === Teams ===
@app.get("/api/teams")
def get_teams():
    return query_df("SELECT * FROM teams ORDER BY name")


# === Sprints ===
@app.get("/api/sprints")
def get_sprints():
    return query_df("SELECT * FROM sprints ORDER BY number")


# === Compliance ===
@app.get("/api/compliance/scores")
def get_compliance_scores(
    sprint_id: Optional[str] = Query(None),
    team_id: Optional[str] = Query(None),
):
    sql = "SELECT cs.*, t.name as team_name FROM compliance_scores cs JOIN teams t ON cs.team_id = t.id WHERE 1=1"
    params = []
    if sprint_id:
        sql += " AND cs.sprint_id = ?"
        params.append(sprint_id)
    if team_id:
        sql += " AND cs.team_id = ?"
        params.append(team_id)
    sql += " ORDER BY cs.computed_at DESC"
    return query_df(sql, tuple(params))


@app.get("/api/compliance/heatmap")
def get_compliance_heatmap(sprint_id: str):
    return query_df("""
        SELECT t.name as team, cs.category, ROUND(AVG(cs.score), 1) as score
        FROM compliance_scores cs
        JOIN teams t ON cs.team_id = t.id
        WHERE cs.sprint_id = ?
        GROUP BY t.name, cs.category
    """, (sprint_id,))


# === Violations ===
@app.get("/api/violations")
def get_violations(
    sprint_id: Optional[str] = Query(None),
    team_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    sql = """SELECT pv.*, t.name as team_name FROM policy_violations pv
             JOIN teams t ON pv.team_id = t.id WHERE 1=1"""
    params = []
    if sprint_id:
        sql += " AND pv.sprint_id = ?"
        params.append(sprint_id)
    if team_id:
        sql += " AND pv.team_id = ?"
        params.append(team_id)
    if severity:
        sql += " AND pv.severity = ?"
        params.append(severity)
    sql += " ORDER BY pv.detected_at DESC LIMIT ?"
    params.append(limit)
    return query_df(sql, tuple(params))


# === Token Usage ===
@app.get("/api/tokens/usage")
def get_token_usage(sprint_id: Optional[str] = Query(None), team_id: Optional[str] = Query(None)):
    sql = """SELECT tu.*, t.name as team_name FROM token_usage tu
             JOIN teams t ON tu.team_id = t.id WHERE 1=1"""
    params = []
    if sprint_id:
        sql += " AND tu.sprint_id = ?"
        params.append(sprint_id)
    if team_id:
        sql += " AND tu.team_id = ?"
        params.append(team_id)
    sql += " ORDER BY tu.date DESC"
    return query_df(sql, tuple(params))


@app.get("/api/tokens/summary")
def get_token_summary(sprint_id: str):
    return query_df("""
        SELECT t.name as team, tu.model,
               SUM(tu.total_tokens) as total_tokens,
               ROUND(SUM(tu.cost_usd), 2) as total_cost
        FROM token_usage tu
        JOIN teams t ON tu.team_id = t.id
        WHERE tu.sprint_id = ?
        GROUP BY t.name, tu.model
        ORDER BY total_cost DESC
    """, (sprint_id,))


# === Adoption ===
@app.get("/api/adoption")
def get_adoption(sprint_id: Optional[str] = Query(None)):
    sql = """SELECT am.*, t.name as team_name FROM adoption_metrics am
             JOIN teams t ON am.team_id = t.id WHERE 1=1"""
    params = []
    if sprint_id:
        sql += " AND am.sprint_id = ?"
        params.append(sprint_id)
    sql += " ORDER BY am.computed_at DESC"
    return query_df(sql, tuple(params))


# === Security ===
@app.get("/api/security/incidents")
def get_security_incidents(
    sprint_id: Optional[str] = Query(None),
    team_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
):
    sql = """SELECT si.*, t.name as team_name FROM security_incidents si
             JOIN teams t ON si.team_id = t.id WHERE 1=1"""
    params = []
    if sprint_id:
        sql += " AND si.sprint_id = ?"
        params.append(sprint_id)
    if team_id:
        sql += " AND si.team_id = ?"
        params.append(team_id)
    if severity:
        sql += " AND si.severity = ?"
        params.append(severity)
    sql += " ORDER BY si.detected_at DESC"
    return query_df(sql, tuple(params))


# === Code Quality ===
@app.get("/api/quality")
def get_code_quality(sprint_id: Optional[str] = Query(None)):
    sql = """SELECT cq.*, t.name as team_name FROM code_quality_metrics cq
             JOIN teams t ON cq.team_id = t.id WHERE 1=1"""
    params = []
    if sprint_id:
        sql += " AND cq.sprint_id = ?"
        params.append(sprint_id)
    sql += " ORDER BY cq.computed_at DESC"
    return query_df(sql, tuple(params))


# === Lifecycle ===
@app.get("/api/lifecycle")
def get_lifecycle(sprint_id: Optional[str] = Query(None)):
    sql = """SELECT lm.*, t.name as team_name FROM lifecycle_metrics lm
             JOIN teams t ON lm.team_id = t.id WHERE 1=1"""
    params = []
    if sprint_id:
        sql += " AND lm.sprint_id = ?"
        params.append(sprint_id)
    sql += " ORDER BY lm.computed_at DESC"
    return query_df(sql, tuple(params))


# === Alerts ===
@app.get("/api/alerts")
def get_alerts(sprint_id: Optional[str] = Query(None), acknowledged: Optional[bool] = Query(None)):
    sql = """SELECT a.*, t.name as team_name FROM alerts a
             JOIN teams t ON a.team_id = t.id WHERE 1=1"""
    params = []
    if sprint_id:
        sql += " AND a.sprint_id = ?"
        params.append(sprint_id)
    if acknowledged is not None:
        sql += " AND a.acknowledged = ?"
        params.append(1 if acknowledged else 0)
    sql += " ORDER BY a.created_at DESC"
    return query_df(sql, tuple(params))


# === Log Violation (Ingest) ===
class ViolationInput(BaseModel):
    team_id: str
    sprint_id: str
    policy_id: str
    policy_name: str
    category: str
    severity: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    tool: Optional[str] = None


@app.post("/api/violations/log")
def log_violation(v: ViolationInput):
    import uuid
    vid = str(uuid.uuid4())[:12]
    with get_db() as conn:
        conn.execute("""
            INSERT INTO policy_violations
            (id, team_id, sprint_id, policy_id, policy_name, category, severity,
             description, file_path, line_number, tool)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (vid, v.team_id, v.sprint_id, v.policy_id, v.policy_name,
              v.category, v.severity, v.description, v.file_path, v.line_number, v.tool))
    return {"violation_id": vid, "status": "logged"}
