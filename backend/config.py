"""
config.py — Backend configuration (paths, dataset registry, metrics).
Mirrors dashboard/config.py but stripped of Streamlit deps.
"""
from pathlib import Path

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

ECO_BASELINE_FILE = str(DATA_DIR / "final_eco_2025.csv")

CROSSWALK_PATHS = [
    str(DATA_DIR / "2010_to_2019_soc_crosswalk.csv"),
    str(ROOT.parent / "aea_dashboard_dev" / "data" / "2010_to_2019_soc_crosswalk.csv"),
    str(ROOT.parent / "automation_exposure_analysis" / "data" / "2010_to_2019_soc_crosswalk.csv"),
]

DATASETS = {
    "AEI v1":     {"file": str(DATA_DIR / "final_aei_v1.csv"),     "is_aei": True,  "is_mcp": False},
    "AEI v2":     {"file": str(DATA_DIR / "final_aei_v2.csv"),     "is_aei": True,  "is_mcp": False},
    "AEI v3":     {"file": str(DATA_DIR / "final_aei_v3.csv"),     "is_aei": True,  "is_mcp": False},
    "AEI v4":     {"file": str(DATA_DIR / "final_aei_v4.csv"),     "is_aei": True,  "is_mcp": False},
    "AEI API v3": {"file": str(DATA_DIR / "final_aei_api_v3.csv"), "is_aei": True,  "is_mcp": False},
    "AEI API v4": {"file": str(DATA_DIR / "final_aei_api_v4.csv"), "is_aei": True,  "is_mcp": False},
    "MCP v1":     {"file": str(DATA_DIR / "final_mcp_v1.csv"),     "is_aei": False, "is_mcp": True},
    "MCP v2":     {"file": str(DATA_DIR / "final_mcp_v2.csv"),     "is_aei": False, "is_mcp": True},
    "MCP v3":     {"file": str(DATA_DIR / "final_mcp_v3.csv"),     "is_aei": False, "is_mcp": True},
    "MCP v4":     {"file": str(DATA_DIR / "final_mcp_v4.csv"),     "is_aei": False, "is_mcp": True},
    "Microsoft":  {"file": str(DATA_DIR / "final_microsoft.csv"),  "is_aei": False, "is_mcp": False},
    "Eco 2015":   {"file": str(DATA_DIR / "final_eco_2015.csv"),   "is_aei": True,  "is_mcp": False},
}

AGG_LEVEL_COL = {
    "occupation": "title_current",
    "broad":      "broad_occ",
    "minor":      "minor_occ_category",
    "major":      "major_occ_category",
}

AGG_LEVEL_OPTIONS = {
    "Major Category":   "major",
    "Minor Category":   "minor",
    "Broad Occupation": "broad",
    "Occupation":       "occupation",
}

SORT_OPTIONS = ["Workers Affected", "Wages Affected", "% Tasks Affected"]
SORT_COL_MAP = {
    "Workers Affected": "workers_affected",
    "Wages Affected":   "wages_affected",
    "% Tasks Affected": "pct_tasks_affected",
}
