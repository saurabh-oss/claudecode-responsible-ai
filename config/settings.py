"""Application configuration and constants."""

import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "governance.db"
CONFIG_DIR = PROJECT_ROOT / "config"

# Database
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Dashboard
DASHBOARD_TITLE = "Responsible AI Governance Platform"
DASHBOARD_ICON = "🛡️"

# Demo Configuration
NUM_TEAMS = 4
NUM_SPRINTS = 6
SPRINT_DURATION_DAYS = 14
TEAM_NAMES = ["Platform Engineering", "Data Services", "Customer Portal", "ML Ops"]
TEAM_SIZES = [12, 8, 15, 6]

# AI Models tracked
AI_MODELS = {
    "claude-sonnet-4": {"input_cost_per_1k": 0.003, "output_cost_per_1k": 0.015},
    "claude-opus-4": {"input_cost_per_1k": 0.015, "output_cost_per_1k": 0.075},
    "gpt-4o": {"input_cost_per_1k": 0.005, "output_cost_per_1k": 0.015},
    "claude-haiku-4": {"input_cost_per_1k": 0.001, "output_cost_per_1k": 0.005},
}

# Severity levels
SEVERITIES = ["critical", "high", "medium", "low", "info"]

# Policy categories
POLICY_CATEGORIES = [
    "security",
    "coding_standards",
    "data_privacy",
    "dependency_management",
    "architecture",
    "documentation",
    "testing",
    "performance",
]

# Color palette for dashboard (Plotly-compatible)
COLORS = {
    "primary": "#534AB7",
    "secondary": "#1D9E75",
    "accent": "#D85A30",
    "warning": "#BA7517",
    "danger": "#E24B4A",
    "success": "#639922",
    "info": "#378ADD",
    "muted": "#888780",
    "bg": "#F8F7F4",
    "text": "#2C2C2A",
}

TEAM_COLORS = ["#534AB7", "#1D9E75", "#D85A30", "#378ADD"]

# Compliance thresholds
COMPLIANCE_THRESHOLDS = {
    "excellent": 90,
    "good": 75,
    "needs_improvement": 60,
    "critical": 0,
}
