"""
config.py — Backend configuration (paths, dataset registry, metrics).
"""
from pathlib import Path

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

ECO_BASELINE_FILE = str(DATA_DIR / "final_eco_2025.csv")
ECO_2015_FILE     = str(DATA_DIR / "final_eco_2015.csv")

CROSSWALK_PATHS = [
    str(DATA_DIR / "2010_to_2019_soc_crosswalk.csv"),
    str(ROOT.parent / "aea_dashboard_dev" / "data" / "2010_to_2019_soc_crosswalk.csv"),
    str(ROOT.parent / "automation_exposure_analysis" / "data" / "2010_to_2019_soc_crosswalk.csv"),
]

# All datasets
DATASETS = {
    # AEI Conversation snapshots (2010 SOC, needs crosswalk)
    "AEI Conv. v1":   {"file": str(DATA_DIR / "final_aei_v1.csv"),     "is_aei": True,  "is_mcp": False},
    "AEI Conv. v2":   {"file": str(DATA_DIR / "final_aei_v2.csv"),     "is_aei": True,  "is_mcp": False},
    "AEI Conv. v3":   {"file": str(DATA_DIR / "final_aei_v3.csv"),     "is_aei": True,  "is_mcp": False},
    "AEI Conv. v4":   {"file": str(DATA_DIR / "final_aei_v4.csv"),     "is_aei": True,  "is_mcp": False},
    "AEI Conv. v5":   {"file": str(DATA_DIR / "final_aei_v5.csv"),     "is_aei": True,  "is_mcp": False},
    # AEI API snapshots (2010 SOC, needs crosswalk)
    "AEI API v3":     {"file": str(DATA_DIR / "final_aei_api_v3.csv"), "is_aei": True,  "is_mcp": False},
    "AEI API v4":     {"file": str(DATA_DIR / "final_aei_api_v4.csv"), "is_aei": True,  "is_mcp": False},
    "AEI API v5":     {"file": str(DATA_DIR / "final_aei_api_v5.csv"), "is_aei": True,  "is_mcp": False},
    # MCP Cumulative (2019 SOC)
    "MCP Cumul. v1":  {"file": str(DATA_DIR / "final_mcp_v1.csv"),     "is_aei": False, "is_mcp": True},
    "MCP Cumul. v2":  {"file": str(DATA_DIR / "final_mcp_v2.csv"),     "is_aei": False, "is_mcp": True},
    "MCP Cumul. v3":  {"file": str(DATA_DIR / "final_mcp_v3.csv"),     "is_aei": False, "is_mcp": True},
    "MCP Cumul. v4":  {"file": str(DATA_DIR / "final_mcp_v4.csv"),     "is_aei": False, "is_mcp": True},
    # Microsoft (2019 SOC)
    "Microsoft":      {"file": str(DATA_DIR / "final_microsoft.csv"),  "is_aei": False, "is_mcp": False},
    # AEI Cumulative — conversation-only (no API), v1/v2 only have conv data naturally
    "AEI Cumul. Conv. v1": {"file": str(DATA_DIR / "final_aei_cumulative_v1.csv"),          "is_aei": True, "is_mcp": False},
    "AEI Cumul. Conv. v2": {"file": str(DATA_DIR / "final_aei_cumulative_v2.csv"),          "is_aei": True, "is_mcp": False},
    "AEI Cumul. Conv. v3": {"file": str(DATA_DIR / "final_aei_cumulative_aei_only_v3.csv"), "is_aei": True, "is_mcp": False},
    "AEI Cumul. Conv. v4": {"file": str(DATA_DIR / "final_aei_cumulative_aei_only_v4.csv"), "is_aei": True, "is_mcp": False},
    "AEI Cumul. Conv. v5": {"file": str(DATA_DIR / "final_aei_cumulative_aei_only_v5.csv"), "is_aei": True, "is_mcp": False},
    # AEI Cumulative — API-only
    "AEI API Cumul. v4":   {"file": str(DATA_DIR / "final_aei_cumulative_api_only_v4.csv"), "is_aei": True, "is_mcp": False},
    "AEI API Cumul. v5":   {"file": str(DATA_DIR / "final_aei_cumulative_api_only_v5.csv"), "is_aei": True, "is_mcp": False},
    # AEI Cumulative — both conversation + API
    "AEI Cumul. (Both) v3": {"file": str(DATA_DIR / "final_aei_cumulative_v3.csv"), "is_aei": True, "is_mcp": False},
    "AEI Cumul. (Both) v4": {"file": str(DATA_DIR / "final_aei_cumulative_v4.csv"), "is_aei": True, "is_mcp": False},
    "AEI Cumul. (Both) v5": {"file": str(DATA_DIR / "final_aei_cumulative_v5.csv"), "is_aei": True, "is_mcp": False},
}

# Eco 2015 is used internally as the baseline for AEI work-activity analysis (not user-selectable)
ECO_2015_META = {"file": ECO_2015_FILE, "is_aei": True, "is_mcp": False}

# Dataset family classification (for selection enforcement)
AEI_CONV_SNAPSHOT_DATASETS    = {"AEI Conv. v1", "AEI Conv. v2", "AEI Conv. v3", "AEI Conv. v4", "AEI Conv. v5"}
AEI_API_SNAPSHOT_DATASETS     = {"AEI API v3", "AEI API v4", "AEI API v5"}
AEI_CONV_CUMULATIVE_DATASETS  = {"AEI Cumul. Conv. v1", "AEI Cumul. Conv. v2", "AEI Cumul. Conv. v3", "AEI Cumul. Conv. v4", "AEI Cumul. Conv. v5"}
AEI_API_CUMULATIVE_DATASETS   = {"AEI API Cumul. v4", "AEI API Cumul. v5"}
AEI_BOTH_CUMULATIVE_DATASETS  = {"AEI Cumul. (Both) v3", "AEI Cumul. (Both) v4", "AEI Cumul. (Both) v5"}
MCP_DATASETS                  = {"MCP Cumul. v1", "MCP Cumul. v2", "MCP Cumul. v3", "MCP Cumul. v4"}

# Dataset series for time-trend analysis
DATASET_SERIES = {
    "AEI Conv.":         ["AEI Conv. v1", "AEI Conv. v2", "AEI Conv. v3", "AEI Conv. v4", "AEI Conv. v5"],
    "AEI API":           ["AEI API v3", "AEI API v4", "AEI API v5"],
    "AEI Cumul. Conv.":  ["AEI Cumul. Conv. v1", "AEI Cumul. Conv. v2", "AEI Cumul. Conv. v3", "AEI Cumul. Conv. v4", "AEI Cumul. Conv. v5"],
    "AEI API Cumul.":    ["AEI API Cumul. v4", "AEI API Cumul. v5"],
    "AEI Cumul. (Both)": ["AEI Cumul. (Both) v3", "AEI Cumul. (Both) v4", "AEI Cumul. (Both) v5"],
    "MCP Cumul.":        ["MCP Cumul. v1", "MCP Cumul. v2", "MCP Cumul. v3", "MCP Cumul. v4"],
    "Microsoft":         ["Microsoft"],
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

# All supported geography codes (national + 50 states + DC + territories)
GEO_OPTIONS = {
    "nat": "National",
    "al": "Alabama", "ak": "Alaska", "az": "Arizona", "ar": "Arkansas",
    "ca": "California", "co": "Colorado", "ct": "Connecticut", "de": "Delaware",
    "dc": "District of Columbia", "fl": "Florida", "ga": "Georgia", "hi": "Hawaii",
    "id": "Idaho", "il": "Illinois", "in": "Indiana", "ia": "Iowa",
    "ks": "Kansas", "ky": "Kentucky", "la": "Louisiana", "me": "Maine",
    "md": "Maryland", "ma": "Massachusetts", "mi": "Michigan", "mn": "Minnesota",
    "ms": "Mississippi", "mo": "Missouri", "mt": "Montana", "ne": "Nebraska",
    "nv": "Nevada", "nh": "New Hampshire", "nj": "New Jersey", "nm": "New Mexico",
    "ny": "New York", "nc": "North Carolina", "nd": "North Dakota", "oh": "Ohio",
    "ok": "Oklahoma", "or": "Oregon", "pa": "Pennsylvania", "ri": "Rhode Island",
    "sc": "South Carolina", "sd": "South Dakota", "tn": "Tennessee", "tx": "Texas",
    "ut": "Utah", "vt": "Vermont", "va": "Virginia", "wa": "Washington",
    "wv": "West Virginia", "wi": "Wisconsin", "wy": "Wyoming",
    "gu": "Guam", "pr": "Puerto Rico", "vi": "U.S. Virgin Islands",
}
