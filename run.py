#!/usr/bin/env python3
"""Single-command launcher for the Responsible AI Governance Platform.

Usage:
    python run.py              # Seed data + launch dashboard
    python run.py --seed-only  # Only seed data
    python run.py --no-seed    # Launch without re-seeding
    python run.py --api        # Launch API server instead
"""

import sys
import os
import subprocess
from pathlib import Path

# Ensure UTF-8 output on Windows terminals that default to cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def seed_data():
    """Generate demo data."""
    print("🔄 Seeding demo data...")
    from src.data.seed import seed_all
    seed_all()


def launch_dashboard():
    """Launch the Streamlit dashboard."""
    print("\n🚀 Launching Responsible AI Governance Dashboard...")
    print("   Dashboard URL: http://localhost:8501")
    print("   Press Ctrl+C to stop\n")
    app_path = PROJECT_ROOT / "src" / "dashboard" / "Home.py"
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.headless=false",
        "--browser.gatherUsageStats=false",
        "--theme.primaryColor=#534AB7",
        "--theme.backgroundColor=#ffffff",
        "--theme.secondaryBackgroundColor=#f8f7f4",
        "--theme.textColor=#2C2C2A",
    ])


def launch_api():
    """Launch the FastAPI server."""
    print("\n🚀 Launching API server...")
    print("   API URL: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("   Press Ctrl+C to stop\n")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "src.api.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000",
    ])


def main():
    args = sys.argv[1:]

    if "--seed-only" in args:
        seed_data()
        return

    if "--api" in args:
        if "--no-seed" not in args:
            seed_data()
        launch_api()
        return

    # Default: seed + dashboard
    if "--no-seed" not in args:
        seed_data()
    launch_dashboard()


if __name__ == "__main__":
    main()
