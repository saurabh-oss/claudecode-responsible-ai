"""Shared utility functions."""

from pathlib import Path
import yaml


def load_policies() -> dict:
    """Load policy definitions from YAML config."""
    config_path = Path(__file__).parent.parent.parent / "config" / "policies.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def severity_color(severity: str) -> str:
    """Return a color hex for a severity level."""
    return {
        "critical": "#E24B4A",
        "high": "#D85A30",
        "medium": "#BA7517",
        "low": "#378ADD",
        "info": "#888780",
    }.get(severity, "#888780")


def compliance_color(score: float) -> str:
    """Return a color hex for a compliance score."""
    if score >= 90:
        return "#639922"
    elif score >= 75:
        return "#1D9E75"
    elif score >= 60:
        return "#BA7517"
    else:
        return "#E24B4A"


def format_number(n: float, decimals: int = 1) -> str:
    """Format large numbers with K/M suffixes."""
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:.{decimals}f}M"
    elif abs(n) >= 1_000:
        return f"{n/1_000:.{decimals}f}K"
    return f"{n:.{decimals}f}"


def format_currency(n: float) -> str:
    if abs(n) >= 1_000_000:
        return f"${n/1_000_000:.2f}M"
    elif abs(n) >= 1_000:
        return f"${n/1_000:.2f}K"
    return f"${n:.2f}"


TEAM_COLORS = {
    "Platform Engineering": "#534AB7",
    "Data Services": "#1D9E75",
    "Customer Portal": "#D85A30",
    "ML Ops": "#378ADD",
}

CATEGORY_LABELS = {
    "security": "Security",
    "coding_standards": "Coding Standards",
    "data_privacy": "Data Privacy",
    "dependency_management": "Dependencies",
    "architecture": "Architecture",
    "testing": "Testing",
    "documentation": "Documentation",
    "performance": "Performance",
}
