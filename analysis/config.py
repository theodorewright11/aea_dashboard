"""
config.py — Shared configuration for analysis scripts.

Provides path setup, dataset presets, and default configs so question
scripts don't have to repeat boilerplate.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# ── Path setup ────────────────────────────────────────────────────────────────
# Project root (aea_dashboard/)
ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
DATA_DIR = ROOT / "data"
ANALYSIS_DIR = ROOT / "analysis"
QUESTIONS_DIR = ANALYSIS_DIR / "questions"
REPORT_DIR = ANALYSIS_DIR / "report"

# Add backend to sys.path so `from backend.compute import ...` works,
# and also add backend dir itself so compute.py's `from config import ...` resolves.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ── Dataset presets ───────────────────────────────────────────────────────────

# Standard occupation-level analysis: all snapshot sources
ALL_DATASETS: list[str] = [
    "AEI v1", "AEI v2", "AEI v3", "AEI v4",
    "AEI API v3", "AEI API v4",
    "MCP v4",
    "Microsoft",
]

# AEI family only (for WA analysis — uses O*NET 2015 baseline)
AEI_DATASETS: list[str] = [
    "AEI v1", "AEI v2", "AEI v3", "AEI v4",
    "AEI API v3", "AEI API v4",
]

# MCP + Microsoft (for WA analysis — uses O*NET 2025 baseline)
MCP_MS_DATASETS: list[str] = ["MCP v4", "Microsoft"]

# WA analysis presets (same as above, explicit aliases for clarity)
WA_AEI_DATASETS: list[str] = AEI_DATASETS
WA_MCP_MS_DATASETS: list[str] = MCP_MS_DATASETS


# ── Default configs ───────────────────────────────────────────────────────────

DEFAULT_OCC_CONFIG: dict[str, Any] = {
    "selected_datasets": ALL_DATASETS,
    "combine_method": "Average",
    "method": "freq",
    "use_auto_aug": True,
    "physical_mode": "all",
    "geo": "nat",
    "agg_level": "major",
    "sort_by": "Workers Affected",
    "top_n": 30,
    "search_query": "",
    "context_size": 3,
}

DEFAULT_WA_AEI_CONFIG: dict[str, Any] = {
    "selected_datasets": WA_AEI_DATASETS,
    "combine_method": "Average",
    "method": "freq",
    "use_auto_aug": True,
    "physical_mode": "all",
    "geo": "nat",
    "agg_level": "dwa",
    "sort_by": "Workers Affected",
    "top_n": 30,
    "search_query": "",
    "context_size": 3,
}

DEFAULT_WA_MCP_MS_CONFIG: dict[str, Any] = {
    "selected_datasets": WA_MCP_MS_DATASETS,
    "combine_method": "Average",
    "method": "freq",
    "use_auto_aug": True,
    "physical_mode": "all",
    "geo": "nat",
    "agg_level": "dwa",
    "sort_by": "Workers Affected",
    "top_n": 30,
    "search_query": "",
    "context_size": 3,
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_config(base: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    """Create a config dict from a base with overrides.

    Example:
        cfg = make_config(DEFAULT_OCC_CONFIG, geo="ut", agg_level="occupation", top_n=20)
    """
    cfg = base.copy()
    cfg.update(overrides)
    return cfg


def run_occ_query(config: dict[str, Any]) -> tuple[Any, str] | None:
    """Run get_group_data and return (DataFrame with 'category' column, group_col).

    Handles the column rename from the internal agg column name to 'category'
    so question scripts don't need to know the internal column names.

    Returns None if no data is available.
    """
    from backend.compute import get_group_data
    import pandas as pd

    data = get_group_data(config)
    if data is None:
        return None
    df: pd.DataFrame = data["df"]
    group_col: str = data["group_col"]
    df = df.rename(columns={group_col: "category"})
    return df, group_col


def ensure_results_dir(question_dir: Path) -> Path:
    """Create and return the results/ directory for a question folder."""
    results = question_dir / "results"
    results.mkdir(parents=True, exist_ok=True)
    (results / "figures").mkdir(exist_ok=True)
    return results


def question_dir(name: str) -> Path:
    """Return the path to a question folder by name."""
    return QUESTIONS_DIR / name
