# Responsible AI Governance Platform — PoC

A comprehensive Proof of Concept demonstrating **enterprise-grade AI governance** for AI-assisted software engineering (Claude Code, Cursor, Copilot, and other Gen AI coding tools).

> **Business Objective:** Showcase the need and power of a Responsible AI dashboard to identify risks, enforce guardrails, and measure the impact of AI on engineering outcomes.

---

## Quick Start (Windows / Mac / Linux)

### Prerequisites
- **Python 3.11+** installed and on PATH
- **pip** package manager

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd responsible-ai-governance

# Create virtual environment (recommended)
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize Demo Data

```bash
python scripts/seed_data.py
```

This generates realistic simulated data for 4 teams across 6 sprints — including policy violations, token consumption, code quality scores, adoption metrics, and security incidents.

### 3. Launch the Dashboard

```bash
streamlit run src/dashboard/Home.py
```

The dashboard opens at **http://localhost:8501** in your browser.

### 4. (Optional) Launch the API Server

```bash
uvicorn src.api.main:app --reload --port 8000
```

API docs available at **http://localhost:8000/docs**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  Developer Ecosystem                         │
│   Claude Code · Cursor · Copilot · IDE Plugins · CLI Agents │
└────────────────────────┬────────────────────────────────────┘
                         │ Events, Telemetry
┌────────────────────────▼────────────────────────────────────┐
│              Ingestion & Instrumentation Layer                │
│   Git Hooks · CI/CD Webhooks · Token Metering · SAST Feeds  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Governance Engine                          │
│  ┌──────────┐  ┌──────────────┐  ┌─────────────┐           │
│  │  Policy   │  │  Analytics   │  │    Alert    │           │
│  │  Engine   │  │    Core      │  │   Manager   │           │
│  └──────────┘  └──────────────┘  └─────────────┘           │
│  ┌───────────────────┐  ┌──────────────────────┐           │
│  │ Token & Cost       │  │ Security & PII       │           │
│  │ Tracker            │  │ Scanner              │           │
│  └───────────────────┘  └──────────────────────┘           │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Data & Persistence Layer                         │
│         SQLite · Time-Series Metrics · Event Log             │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│            Observability & Dashboard Layer                    │
│  ┌──────────┐ ┌────────┐ ┌───────┐ ┌────────┐ ┌────────┐  │
│  │Compliance│ │  Code  │ │ Token │ │Adoption│ │Security│  │
│  │ Heatmap  │ │Quality │ │ Cost  │ │  ROI   │ │  PII   │  │
│  └──────────┘ └────────┘ └───────┘ └────────┘ └────────┘  │
│                  ┌──────────────┐                            │
│                  │  Lifecycle   │                            │
│                  │  CI/CD Mon.  │                            │
│                  └──────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

## Dashboard Pillars (6 Modules)

| # | Pillar | Key Metrics |
|---|--------|-------------|
| 1 | **Monitoring & Compliance** | Rule compliance heatmap, role-based policy matrix, % rules adhered per team, violation trends |
| 2 | **Coding Standards** | Static analysis scorecard, SonarQube scores, flagged AI code snippets, dynamic analysis alerts |
| 3 | **AI Token Usage** | Token consumption trends, cost breakdown by team/model, cost per sprint, budget vs actual |
| 4 | **Adoption & Productivity** | Adoption rate gauge, % developers using AI, productivity gain chart, ROI estimate |
| 5 | **Data Security** | Sensitive data access alerts, PII incidents, compliance adherence %, secret detection |
| 6 | **Lifecycle Integration** | CI/CD compliance monitor, test automation coverage, % lifecycle stages monitored, defect leakage |

## Project Structure

```
responsible-ai-governance/
├── src/
│   ├── data/
│   │   ├── __init__.py
│   │   ├── models.py          # SQLAlchemy / Pydantic data models
│   │   ├── database.py        # SQLite database setup
│   │   └── seed.py            # Data generation logic
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── policy_engine.py   # Policy evaluation & scoring
│   │   ├── analytics.py       # Metric computation & trends
│   │   ├── alerts.py          # Threshold-based alerting
│   │   ├── token_tracker.py   # Token/cost accounting
│   │   └── security_scanner.py# PII & secret detection
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py            # FastAPI REST endpoints
│   ├── dashboard/
│   │   ├── Home.py            # Streamlit main app (Home)
│   │   ├── pages/
│   │   │   ├── 1_📋_Compliance.py
│   │   │   ├── 2_📊_Code_Quality.py
│   │   │   ├── 3_💰_Token_Usage.py
│   │   │   ├── 4_🚀_Adoption.py
│   │   │   ├── 5_🔒_Security.py
│   │   │   └── 6_🔄_Lifecycle.py
│   │   └── components.py      # Reusable dashboard widgets
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── config/
│   ├── policies.yaml          # Organizational policy definitions
│   └── settings.py            # Application configuration
├── scripts/
│   └── seed_data.py           # CLI to generate demo data
├── .claude/
│   └── settings.json          # Claude Code governance rules
├── .pre-commit-config.yaml
├── requirements.txt
├── run.py                     # Single-command launcher
└── README.md
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend API | FastAPI | REST endpoints, OpenAPI docs |
| Dashboard | Streamlit + Plotly | Interactive visualizations |
| Database | SQLite | Zero-config persistence |
| Data Generation | Faker + custom generators | Realistic demo scenarios |
| Static Analysis | Bandit, Semgrep, Gitleaks | Security scanning (production) |
| Pre-commit | pre-commit framework | Git hook enforcement |

## Configuration

### Policy Definitions (`config/policies.yaml`)

Policies are defined in YAML and evaluated by the governance engine:

```yaml
policies:
  - id: SEC-001
    name: No Hardcoded Secrets
    category: security
    severity: critical
    applies_to: [developer, tech_lead]
    threshold: 0  # zero tolerance
```

### Claude Code Rules (`.claude/settings.json`)

Organizational guardrails enforced at the IDE level during AI-assisted development.

## License

MIT

## Contributing

This is a PoC/reference architecture. Contributions welcome — especially for additional policy templates, dashboard visualizations, and CI/CD integration patterns.
