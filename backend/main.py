"""
main.py — FastAPI backend for the Automation Exposure Dashboard.

Endpoints:
  GET  /api/health                  — liveness check
  GET  /api/config                  — dataset list, availability, controls metadata
  POST /api/compute                 — occupation-level chart data (overview)
  POST /api/work-activities         — DWA/IWA/GWA activity-level chart data
  POST /api/trends                  — time-series data per dataset series
  POST /api/trends/work-activities  — work-activity time-series trends
  GET  /api/explorer                — occupation list for job explorer
  GET  /api/explorer/tasks          — task details for one occupation
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import math
from typing import Optional

from config import (
    DATASETS, DATASET_SERIES, AGG_LEVEL_OPTIONS, SORT_OPTIONS, AGG_LEVEL_COL,
    AEI_SNAPSHOT_DATASETS, AEI_CUMULATIVE_DATASETS, MCP_DATASETS,
)
from compute import (
    get_group_data,
    compute_work_activities,
    compute_trends,
    compute_wa_trends,
    get_explorer_occupations,
    get_occupation_tasks,
    get_explorer_groups,
    get_wa_explorer_data,
    get_wa_tasks_for_activity,
    get_all_tasks,
    get_all_eco_task_rows,
    crosswalk_available,
    dataset_exists,
    eco2015_available,
    _safe_num,
)

app = FastAPI(title="AEA Dashboard API", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _safe(v) -> float:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return 0.0
    return float(v)


def _safe_int(v) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


# ── Shared settings model ──────────────────────────────────────────────────────

class GroupSettingsModel(BaseModel):
    selected_datasets: list[str]
    combine_method:    str  = "Average"
    method:            str  = "freq"
    use_auto_aug:      bool = False
    use_adj_mean:      bool = False
    physical_mode:     str  = "all"
    geo:               str  = "nat"
    agg_level:         str  = "major"
    sort_by:           str  = "Workers Affected"
    top_n:             int  = 10
    search_query:      str  = ""
    context_size:      int  = 5


# ── /api/config ────────────────────────────────────────────────────────────────

class ConfigResponse(BaseModel):
    datasets:               list[str]
    dataset_availability:   dict[str, bool]
    dataset_series:         dict[str, list[str]]
    agg_levels:             dict[str, str]
    sort_options:           list[str]
    crosswalk_available:    bool
    eco2015_available:      bool
    aei_snapshot_datasets:  list[str]
    aei_cumulative_datasets: list[str]
    mcp_datasets:           list[str]


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/config", response_model=ConfigResponse)
def config():
    return ConfigResponse(
        datasets=list(DATASETS.keys()),
        dataset_availability={name: dataset_exists(name) for name in DATASETS},
        dataset_series=DATASET_SERIES,
        agg_levels=AGG_LEVEL_OPTIONS,
        sort_options=SORT_OPTIONS,
        crosswalk_available=crosswalk_available(),
        eco2015_available=eco2015_available(),
        aei_snapshot_datasets=sorted(AEI_SNAPSHOT_DATASETS),
        aei_cumulative_datasets=sorted(AEI_CUMULATIVE_DATASETS),
        mcp_datasets=sorted(MCP_DATASETS),
    )


# ── /api/compute (overview) ────────────────────────────────────────────────────

class ChartRow(BaseModel):
    category:           str
    pct_tasks_affected: float
    workers_affected:   float
    wages_affected:     float
    rank_workers:       int = 0
    rank_wages:         int = 0
    rank_pct:           int = 0


class ComputeResponse(BaseModel):
    rows:             list[ChartRow]
    group_col:        str
    total_categories: int   = 0
    total_emp:        float = 0.0
    total_wages:      float = 0.0
    matched_category: Optional[str] = None


@app.post("/api/compute", response_model=ComputeResponse)
def compute(req: GroupSettingsModel):
    settings = req.model_dump()
    result   = get_group_data(settings)
    group_col = AGG_LEVEL_COL[req.agg_level]

    if result is None:
        return ComputeResponse(rows=[], group_col=group_col)

    df = result["df"]

    if df is None or df.empty:
        return ComputeResponse(
            rows=[],
            group_col=group_col,
            total_categories=result.get("total_categories", 0),
            total_emp=result.get("total_emp", 0.0),
            total_wages=result.get("total_wages", 0.0),
            matched_category=result.get("matched_category"),
        )

    rows = [
        ChartRow(
            category=str(row[group_col]),
            pct_tasks_affected=_safe(row.get("pct_tasks_affected", 0)),
            workers_affected=_safe(row.get("workers_affected", 0)),
            wages_affected=_safe(row.get("wages_affected", 0)),
            rank_workers=_safe_int(row.get("rank_workers", 0)),
            rank_wages=_safe_int(row.get("rank_wages", 0)),
            rank_pct=_safe_int(row.get("rank_pct", 0)),
        )
        for _, row in df.iterrows()
    ]
    return ComputeResponse(
        rows=rows,
        group_col=group_col,
        total_categories=result.get("total_categories", 0),
        total_emp=_safe(result.get("total_emp", 0.0)),
        total_wages=_safe(result.get("total_wages", 0.0)),
        matched_category=result.get("matched_category"),
    )


# ── /api/work-activities ───────────────────────────────────────────────────────

class ActivityRow(BaseModel):
    category:           str
    pct_tasks_affected: float
    workers_affected:   float
    wages_affected:     float


class ActivityGroup(BaseModel):
    datasets:     list[str]
    gwa:          list[ActivityRow] = []
    iwa:          list[ActivityRow] = []
    dwa:          list[ActivityRow] = []


class WorkActivitiesResponse(BaseModel):
    aei_group: Optional[ActivityGroup] = None
    mcp_group: Optional[ActivityGroup] = None


@app.post("/api/work-activities", response_model=WorkActivitiesResponse)
def work_activities(req: GroupSettingsModel):
    settings = req.model_dump()
    result = compute_work_activities(settings)

    def _parse_group(g: Optional[dict]) -> Optional[ActivityGroup]:
        if g is None:
            return None
        def _rows(key: str) -> list[ActivityRow]:
            return [
                ActivityRow(
                    category=str(r["category"]),
                    pct_tasks_affected=_safe(r.get("pct_tasks_affected", 0)),
                    workers_affected=_safe(r.get("workers_affected", 0)),
                    wages_affected=_safe(r.get("wages_affected", 0)),
                )
                for r in g.get(key, [])
            ]
        return ActivityGroup(
            datasets=g.get("datasets", []),
            gwa=_rows("gwa"),
            iwa=_rows("iwa"),
            dwa=_rows("dwa"),
        )

    return WorkActivitiesResponse(
        aei_group=_parse_group(result.get("aei_group")),
        mcp_group=_parse_group(result.get("mcp_group")),
    )


# ── /api/trends ────────────────────────────────────────────────────────────────

class TrendRow(BaseModel):
    category:           str
    pct_tasks_affected: float
    workers_affected:   float
    wages_affected:     float


class TrendDataPoint(BaseModel):
    dataset:  str
    date:     str
    rows:     list[TrendRow]


class TrendSeries(BaseModel):
    name:            str
    data_points:     list[TrendDataPoint]
    top_categories:  list[str]
    group_col:       str


class TrendsResponse(BaseModel):
    series: list[TrendSeries]


class TrendsRequest(BaseModel):
    series:        list[str] = ["AEI", "MCP"]
    method:        str       = "freq"
    use_auto_aug:  bool      = False
    use_adj_mean:  bool      = False
    physical_mode: str       = "all"
    geo:           str       = "nat"
    agg_level:     str       = "major"
    top_n:         int       = 10
    sort_by:       str       = "Workers Affected"


@app.post("/api/trends", response_model=TrendsResponse)
def trends(req: TrendsRequest):
    settings = req.model_dump()
    result = compute_trends(settings)

    series_out = []
    for s in result.get("series", []):
        dps = []
        for dp in s.get("data_points", []):
            rows = [
                TrendRow(
                    category=str(r["category"]),
                    pct_tasks_affected=_safe(r.get("pct_tasks_affected", 0)),
                    workers_affected=_safe(r.get("workers_affected", 0)),
                    wages_affected=_safe(r.get("wages_affected", 0)),
                )
                for r in dp.get("rows", [])
            ]
            dps.append(TrendDataPoint(
                dataset=dp["dataset"],
                date=dp["date"],
                rows=rows,
            ))
        series_out.append(TrendSeries(
            name=s["name"],
            data_points=dps,
            top_categories=s.get("top_categories", []),
            group_col=s.get("group_col", "major_occ_category"),
        ))

    return TrendsResponse(series=series_out)


# ── /api/trends/work-activities ────────────────────────────────────────────────

class WATrendsRequest(BaseModel):
    series:         list[str] = ["AEI", "MCP"]
    method:         str       = "freq"
    use_auto_aug:   bool      = False
    use_adj_mean:   bool      = False
    physical_mode:  str       = "all"
    geo:            str       = "nat"
    top_n:          int       = 10
    sort_by:        str       = "Workers Affected"
    activity_level: str       = "gwa"   # gwa | iwa | dwa


@app.post("/api/trends/work-activities", response_model=TrendsResponse)
def trends_work_activities(req: WATrendsRequest):
    settings = req.model_dump()
    result = compute_wa_trends(settings)

    series_out = []
    for s in result.get("series", []):
        dps = []
        for dp in s.get("data_points", []):
            rows = [
                TrendRow(
                    category=str(r["category"]),
                    pct_tasks_affected=_safe(r.get("pct_tasks_affected", 0)),
                    workers_affected=_safe(r.get("workers_affected", 0)),
                    wages_affected=_safe(r.get("wages_affected", 0)),
                )
                for r in dp.get("rows", [])
            ]
            dps.append(TrendDataPoint(
                dataset=dp["dataset"],
                date=dp["date"],
                rows=rows,
            ))
        series_out.append(TrendSeries(
            name=s["name"],
            data_points=dps,
            top_categories=s.get("top_categories", []),
            group_col=s.get("group_col", "gwa"),
        ))

    return TrendsResponse(series=series_out)


# ── /api/explorer ──────────────────────────────────────────────────────────────

class OccupationSummary(BaseModel):
    title_current:      str
    major:              Optional[str]   = None
    minor:              Optional[str]   = None
    broad:              Optional[str]   = None
    emp_nat:            Optional[float] = None
    emp_ut:             Optional[float] = None
    wage_nat:           Optional[float] = None
    wage_ut:            Optional[float] = None
    n_tasks:            int             = 0
    n_physical_tasks:   int             = 0
    pct_physical:       Optional[float] = None
    # 4 auto-aug variants
    auto_avg_with_vals: Optional[float] = None
    auto_max_with_vals: Optional[float] = None
    auto_avg_all:       Optional[float] = None
    auto_max_all:       Optional[float] = None
    # 4 pct variants + sum
    pct_avg_with_vals:  Optional[float] = None
    pct_max_with_vals:  Optional[float] = None
    pct_avg_all:        Optional[float] = None
    pct_max_all:        Optional[float] = None
    sum_pct_avg:        Optional[float] = None
    sum_pct_max:        Optional[float] = None


class ExplorerResponse(BaseModel):
    occupations: list[OccupationSummary]


@app.get("/api/explorer", response_model=ExplorerResponse)
def explorer():
    occs = get_explorer_occupations()
    return ExplorerResponse(occupations=[OccupationSummary(**o) for o in occs])


# ── /api/explorer/tasks ────────────────────────────────────────────────────────

class SourceStats(BaseModel):
    auto_aug: Optional[float] = None
    pct_norm: Optional[float] = None


class McpEntry(BaseModel):
    title:  str
    rating: Optional[float] = None
    url:    Optional[str]   = None


class TaskDetail(BaseModel):
    task:              str
    task_normalized:   str
    dwa_title:         Optional[str]   = None
    iwa_title:         Optional[str]   = None
    gwa_title:         Optional[str]   = None
    freq_mean:         Optional[float] = None
    importance:        Optional[float] = None
    relevance:         Optional[float] = None
    physical:          Optional[bool]  = None
    sources:           dict            = {}   # source_name -> {auto_aug, pct_norm}
    avg_auto_aug:      Optional[float] = None
    max_auto_aug:      Optional[float] = None
    avg_pct_norm:      Optional[float] = None
    max_pct_norm:      Optional[float] = None
    top_mcps:          list[McpEntry]   = []


class OccupationTasksResponse(BaseModel):
    title: str
    tasks: list[TaskDetail]


@app.get("/api/explorer/tasks", response_model=OccupationTasksResponse)
def explorer_tasks(title: str = Query(..., description="Occupation title (title_current)")):
    result = get_occupation_tasks(title)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Occupation '{title}' not found")
    return OccupationTasksResponse(
        title=result["title"],
        tasks=[TaskDetail(**t) for t in result["tasks"]],
    )


# ── /api/explorer/groups ───────────────────────────────────────────────────────

class ExplorerGroupRow(BaseModel):
    name:               str
    parent:             Optional[str]   = None
    grandparent:        Optional[str]   = None
    emp_nat:            Optional[float] = None
    emp_ut:             Optional[float] = None
    wage_nat:           Optional[float] = None
    wage_ut:            Optional[float] = None
    n_occs:             int             = 0
    n_tasks:            int             = 0
    n_physical_tasks:   int             = 0
    pct_physical:       Optional[float] = None
    auto_avg_with_vals: Optional[float] = None
    auto_max_with_vals: Optional[float] = None
    auto_avg_all:       Optional[float] = None
    auto_max_all:       Optional[float] = None
    pct_avg_with_vals:  Optional[float] = None
    pct_max_with_vals:  Optional[float] = None
    pct_avg_all:        Optional[float] = None
    pct_max_all:        Optional[float] = None
    sum_pct_avg:        Optional[float] = None
    sum_pct_max:        Optional[float] = None


class ExplorerGroupsResponse(BaseModel):
    major: list[ExplorerGroupRow]
    minor: list[ExplorerGroupRow]
    broad: list[ExplorerGroupRow]


@app.get("/api/explorer/groups", response_model=ExplorerGroupsResponse)
def explorer_groups():
    data = get_explorer_groups()
    def _parse(rows: list) -> list[ExplorerGroupRow]:
        return [ExplorerGroupRow(**r) for r in rows]
    return ExplorerGroupsResponse(
        major=_parse(data.get("major", [])),
        minor=_parse(data.get("minor", [])),
        broad=_parse(data.get("broad", [])),
    )


# ── /api/explorer/wa ───────────────────────────────────────────────────────────

class WAExplorerRow(BaseModel):
    level:              str
    name:               str
    parent:             Optional[str]   = None
    gwa:                Optional[str]   = None
    emp_nat:            Optional[float] = None
    emp_ut:             Optional[float] = None
    wage_nat:           Optional[float] = None
    wage_ut:            Optional[float] = None
    n_occs:             int             = 0
    n_tasks:            int             = 0
    n_physical_tasks:   int             = 0
    pct_physical:       Optional[float] = None
    auto_avg_with_vals: Optional[float] = None
    auto_max_with_vals: Optional[float] = None
    auto_avg_all:       Optional[float] = None
    auto_max_all:       Optional[float] = None
    pct_avg_with_vals:  Optional[float] = None
    pct_max_with_vals:  Optional[float] = None
    pct_avg_all:        Optional[float] = None
    pct_max_all:        Optional[float] = None
    sum_pct_avg:        Optional[float] = None
    sum_pct_max:        Optional[float] = None


class WAExplorerResponse(BaseModel):
    rows: list[WAExplorerRow]


@app.get("/api/explorer/wa", response_model=WAExplorerResponse)
def wa_explorer():
    rows = get_wa_explorer_data()
    return WAExplorerResponse(rows=[WAExplorerRow(**r) for r in rows])


# ── /api/explorer/wa/tasks ─────────────────────────────────────────────────────

class WATaskDetail(BaseModel):
    task:               str
    task_normalized:    str
    dwa_title:          Optional[str]   = None
    iwa_title:          Optional[str]   = None
    gwa_title:          Optional[str]   = None
    physical:           Optional[bool]  = None
    emp_nat:            Optional[float] = None
    emp_ut:             Optional[float] = None
    wage_nat:           Optional[float] = None
    freq_mean:          Optional[float] = None
    importance:         Optional[float] = None
    relevance:          Optional[float] = None
    title_current:      Optional[str]   = None
    broad_occ:          Optional[str]   = None
    minor_occ_category: Optional[str]   = None
    major_occ_category: Optional[str]   = None
    sources:            dict            = {}
    avg_auto_aug:       Optional[float] = None
    max_auto_aug:       Optional[float] = None
    avg_pct_norm:       Optional[float] = None
    max_pct_norm:       Optional[float] = None
    top_mcps:           list[McpEntry]  = []


class WATasksResponse(BaseModel):
    level: str
    name:  str
    tasks: list[WATaskDetail]


@app.get("/api/explorer/wa/tasks", response_model=WATasksResponse)
def wa_explorer_tasks(
    level: str = Query(..., description="Activity level: gwa, iwa, or dwa"),
    name:  str = Query(..., description="Activity name"),
):
    if level not in ("gwa", "iwa", "dwa"):
        raise HTTPException(status_code=400, detail="level must be gwa, iwa, or dwa")
    tasks = get_wa_tasks_for_activity(level, name)
    return WATasksResponse(
        level=level,
        name=name,
        tasks=[WATaskDetail(**t) for t in tasks],
    )


# ── /api/explorer/all-tasks ────────────────────────────────────────────────────

class AllTaskRow(BaseModel):
    task:              str
    task_normalized:   str
    dwa_title:         Optional[str]   = None
    iwa_title:         Optional[str]   = None
    gwa_title:         Optional[str]   = None
    physical:          Optional[bool]  = None
    n_occs:            int             = 0
    emp_nat:           Optional[float] = None
    emp_ut:            Optional[float] = None
    wage_nat:          Optional[float] = None
    sources:           dict            = {}
    avg_auto_aug:      Optional[float] = None
    max_auto_aug:      Optional[float] = None
    avg_pct_norm:      Optional[float] = None
    max_pct_norm:      Optional[float] = None


class AllTasksResponse(BaseModel):
    tasks: list[AllTaskRow]


@app.get("/api/explorer/all-tasks", response_model=AllTasksResponse)
def explorer_all_tasks():
    tasks = get_all_tasks()
    return AllTasksResponse(tasks=[AllTaskRow(**t) for t in tasks])


# ── /api/explorer/all-eco-tasks ───────────────────────────────────────────────

class EcoTaskRow(BaseModel):
    task:               str
    task_normalized:    str
    title_current:      str
    broad_occ:          Optional[str]   = None
    minor_occ_category: Optional[str]   = None
    major_occ_category: Optional[str]   = None
    dwa_title:          Optional[str]   = None
    iwa_title:          Optional[str]   = None
    gwa_title:          Optional[str]   = None
    physical:           Optional[bool]  = None
    emp_nat:            Optional[float] = None
    emp_ut:             Optional[float] = None
    wage_nat:           Optional[float] = None
    wage_ut:            Optional[float] = None
    n_tasks_per_occ:    int             = 1
    freq_mean:          Optional[float] = None
    importance:         Optional[float] = None
    relevance:          Optional[float] = None
    sources:            dict            = {}
    avg_auto_aug:       Optional[float] = None
    max_auto_aug:       Optional[float] = None
    avg_pct_norm:       Optional[float] = None
    max_pct_norm:       Optional[float] = None
    top_mcps:           list[McpEntry]  = []


class EcoTasksResponse(BaseModel):
    tasks: list[EcoTaskRow]


@app.get("/api/explorer/all-eco-tasks", response_model=EcoTasksResponse)
def explorer_all_eco_tasks():
    rows = get_all_eco_task_rows()
    return EcoTasksResponse(tasks=[EcoTaskRow(**r) for r in rows])
