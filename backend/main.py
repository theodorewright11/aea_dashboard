"""
main.py — FastAPI backend for the Automation Exposure Dashboard website.

Endpoints:
  GET  /api/health   — liveness check
  GET  /api/config   — dataset list, availability, controls metadata
  POST /api/compute  — run compute pipeline for one group, return chart data
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import math

from config import DATASETS, AGG_LEVEL_OPTIONS, SORT_OPTIONS, AGG_LEVEL_COL
from compute import get_group_data, crosswalk_available, dataset_exists

app = FastAPI(title="AEA Dashboard API", version="1.0.0")

# Allow the Next.js frontend to call the API (update origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Request / Response models ──────────────────────────────────────────────────

class ComputeRequest(BaseModel):
    selected_datasets: list[str]
    combine_method:    str = "Average"   # "Average" | "Max"
    method:            str = "freq"      # "freq" | "imp"
    use_auto_aug:      bool = False
    use_adj_mean:      bool = False
    physical_mode:     str = "all"       # "all" | "exclude" | "only"
    geo:               str = "nat"       # "nat" | "ut"
    agg_level:         str = "major"     # "major" | "minor" | "broad" | "occupation"
    sort_by:           str = "Workers Affected"
    top_n:             int = 10


class ChartRow(BaseModel):
    category:           str
    pct_tasks_affected: float
    workers_affected:   float
    wages_affected:     float


class ComputeResponse(BaseModel):
    rows:      list[ChartRow]
    group_col: str


class ConfigResponse(BaseModel):
    datasets:             list[str]
    dataset_availability: dict[str, bool]
    agg_levels:           dict[str, str]   # display label → internal key
    sort_options:         list[str]
    crosswalk_available:  bool


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/config", response_model=ConfigResponse)
def config():
    return ConfigResponse(
        datasets=list(DATASETS.keys()),
        dataset_availability={name: dataset_exists(name) for name in DATASETS},
        agg_levels=AGG_LEVEL_OPTIONS,
        sort_options=SORT_OPTIONS,
        crosswalk_available=crosswalk_available(),
    )


@app.post("/api/compute", response_model=ComputeResponse)
def compute(req: ComputeRequest):
    settings = {
        "selected_datasets": req.selected_datasets,
        "combine_method":    req.combine_method,
        "method":            req.method,
        "use_auto_aug":      req.use_auto_aug,
        "use_adj_mean":      req.use_adj_mean,
        "physical_mode":     req.physical_mode,
        "geo":               req.geo,
        "agg_level":         req.agg_level,
        "sort_by":           req.sort_by,
        "top_n":             req.top_n,
    }

    df = get_group_data(settings)
    group_col = AGG_LEVEL_COL[req.agg_level]

    if df is None or df.empty:
        return ComputeResponse(rows=[], group_col=group_col)

    def _safe(v) -> float:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return 0.0
        return float(v)

    rows = [
        ChartRow(
            category=str(row[group_col]),
            pct_tasks_affected=_safe(row.get("pct_tasks_affected", 0)),
            workers_affected=_safe(row.get("workers_affected", 0)),
            wages_affected=_safe(row.get("wages_affected", 0)),
        )
        for _, row in df.iterrows()
    ]

    return ComputeResponse(rows=rows, group_col=group_col)
