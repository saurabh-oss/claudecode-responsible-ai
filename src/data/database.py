"""Database setup and connection management using SQLite."""

import sqlite3
import json
from pathlib import Path
from contextlib import contextmanager

DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DB_DIR / "governance.db"


def get_db_path() -> Path:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables."""
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS teams (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            size INTEGER NOT NULL,
            lead TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sprints (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            number INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS policy_violations (
            id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL,
            sprint_id TEXT NOT NULL,
            policy_id TEXT NOT NULL,
            policy_name TEXT,
            category TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT,
            file_path TEXT,
            line_number INTEGER,
            tool TEXT,
            resolved INTEGER DEFAULT 0,
            resolved_at TIMESTAMP,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (sprint_id) REFERENCES sprints(id)
        );

        CREATE TABLE IF NOT EXISTS compliance_scores (
            id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL,
            sprint_id TEXT NOT NULL,
            category TEXT NOT NULL,
            score REAL NOT NULL,
            total_rules INTEGER,
            rules_passed INTEGER,
            computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (sprint_id) REFERENCES sprints(id)
        );

        CREATE TABLE IF NOT EXISTS code_quality_metrics (
            id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL,
            sprint_id TEXT NOT NULL,
            sonarqube_score REAL,
            complexity_avg REAL,
            duplication_pct REAL,
            test_coverage_pct REAL,
            docstring_coverage_pct REAL,
            type_hint_coverage_pct REAL,
            ai_generated_lines INTEGER DEFAULT 0,
            human_authored_lines INTEGER DEFAULT 0,
            flagged_ai_snippets INTEGER DEFAULT 0,
            bugs_found INTEGER DEFAULT 0,
            code_smells INTEGER DEFAULT 0,
            vulnerabilities INTEGER DEFAULT 0,
            computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (sprint_id) REFERENCES sprints(id)
        );

        CREATE TABLE IF NOT EXISTS token_usage (
            id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL,
            sprint_id TEXT NOT NULL,
            date DATE NOT NULL,
            model TEXT NOT NULL,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            cost_usd REAL DEFAULT 0.0,
            developer_count INTEGER DEFAULT 1,
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (sprint_id) REFERENCES sprints(id)
        );

        CREATE TABLE IF NOT EXISTS adoption_metrics (
            id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL,
            sprint_id TEXT NOT NULL,
            total_developers INTEGER,
            ai_active_developers INTEGER,
            adoption_rate_pct REAL,
            ai_assisted_commits_pct REAL,
            avg_time_saved_hrs REAL,
            productivity_gain_pct REAL,
            sprint_velocity_points INTEGER,
            baseline_velocity_points INTEGER,
            roi_estimate_usd REAL,
            computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (sprint_id) REFERENCES sprints(id)
        );

        CREATE TABLE IF NOT EXISTS security_incidents (
            id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL,
            sprint_id TEXT NOT NULL,
            incident_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT,
            affected_file TEXT,
            pii_type TEXT,
            detected_by TEXT,
            status TEXT DEFAULT 'open',
            resolved_at TIMESTAMP,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (sprint_id) REFERENCES sprints(id)
        );

        CREATE TABLE IF NOT EXISTS lifecycle_metrics (
            id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL,
            sprint_id TEXT NOT NULL,
            stage TEXT NOT NULL,
            is_monitored INTEGER DEFAULT 0,
            compliance_pct REAL DEFAULT 0.0,
            ai_coverage_pct REAL DEFAULT 0.0,
            test_automation_pct REAL DEFAULT 0.0,
            defects_found INTEGER DEFAULT 0,
            defects_leaked INTEGER DEFAULT 0,
            pipeline_pass_rate REAL DEFAULT 0.0,
            computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams(id),
            FOREIGN KEY (sprint_id) REFERENCES sprints(id)
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            team_id TEXT,
            sprint_id TEXT,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT,
            source TEXT,
            acknowledged INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)


def query_df(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a query and return results as list of dicts."""
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def execute_write(sql: str, params: tuple = ()) -> None:
    """Execute a write (INSERT/UPDATE/DELETE) statement."""
    with get_db() as conn:
        conn.execute(sql, params)
