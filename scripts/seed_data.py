#!/usr/bin/env python3
"""CLI script to seed demo data."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.data.seed import seed_all

if __name__ == "__main__":
    print("🔄 Seeding Responsible AI Governance demo data...")
    seed_all()
