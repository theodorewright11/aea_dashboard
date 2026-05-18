"""
Part 2 — Characterization: Where AI Exposure Falls

Five chart groups characterizing the structural distribution of AI exposure:
1. Physical/Informational Divide: box plots of % tasks affected by occ group
2. Job Zone: violin plots of % tasks affected by job zone (1–5)
3. SKA Levels: AI max bar + workforce markers for every SKA element (3 subplots)
4. Work Activities: all GWAs ranked by % tasks affected, colored by workers
5. Major Categories: all 22 majors, three side-by-side panels (pct/workers/wages)

Run from project root:
    venv/Scripts/python -m analysis.paper.results.part_2.run
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.config import (
    ANALYSIS_CONFIGS,
    ANALYSIS_CONFIG_LABELS,
    ANALYSIS_CONFIG_SERIES,
    ROOT,
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.data.compute_ska import load_ska_data
from analysis.utils import FONT_FAMILY, save_figure, save_csv
from analysis.paper.paper_config import (
    PAPER_W, PAPER_H,
    TITLE_FS, SUBTITLE_FS, INSIDE_FS, OUTSIDE_FS, TICK_FS, LABEL_FS,
    LEGEND_FS, ANNOT_FS,
    METRIC_COLORS, PAPER_PALETTE,
    style_paper_figure, fmt_wages, fmt_workers,
)

HERE = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

PRIMARY_KEY = "all_confirmed"
PRIMARY_DATASET = ANALYSIS_CONFIGS[PRIMARY_KEY]
PRIMARY_LABEL = ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]

# Physical/informational thresholds (matches exploratory).
# Display order is Physical → Mixed → Non-physical, top to bottom.
PHYS_LOWER = 33.0
PHYS_UPPER = 67.0
OCC_GROUPS = ["Physical", "Mixed", "Non-physical"]
GROUP_COLORS = {
    "Non-physical": METRIC_COLORS["tasks"],     # Slate blue
    "Mixed":        METRIC_COLORS["wages"],     # Sage green
    "Physical":     METRIC_COLORS["workers"],   # Gold / yellow
}

# Job zone labels
ZONE_LABELS = {
    1: "Zone 1 — Little/No Prep",
    2: "Zone 2 — Some Prep",
    3: "Zone 3 — Medium Prep",
    4: "Zone 4 — Considerable Prep",
    5: "Zone 5 — Extensive Prep",
}

# SKA constants
IMPORTANCE_THRESHOLD = 3.0
TOP_N_FOR_AVERAGE = 10
SKA_LABEL_MAX = 45


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────

def _copy_fig(results: Path, figures: Path, name: str) -> None:
    shutil.copy(results / "figures" / name, figures / name)


def _run_config(
    dataset_name: str,
    agg_level: str = "occupation",
    physical_mode: str = "all",
) -> pd.DataFrame:
    """Run the dashboard pipeline. `physical_mode='exclude'` strips physical
    tasks from both numerator and denominator (used by variant B charts)."""
    from backend.compute import get_group_data
    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": physical_mode,
        "geo": "nat",
        "agg_level": agg_level,
        "sort_by": "% Tasks Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    assert data is not None, f"No data for {dataset_name} ({physical_mode}, {agg_level})"
    df: pd.DataFrame = data["df"]
    group_col: str = data["group_col"]
    df = df.rename(columns={group_col: "category"})
    return df


# ─────────────────────────────────────────────────────────────────────────
# Structural variants: Variant A (eco-only non-phys task share, ratio of
# totals) and Variant B (dashboard pipeline restricted to non-phys tasks).
# Both serve the major-cat trio at the top of Part 2 and the GWA quintet.
# ─────────────────────────────────────────────────────────────────────────

LEVEL_COL: dict[str, str] = {
    "major":      "major_occ_category",
    "minor":      "minor_occ_category",
    "broad":      "broad_occ",
    "occupation": "title_current",
}


def _coerce_phys_bool(val) -> bool:
    """Mirror backend.compute._phys_bool. eco rows store physical as
    1/0/True/False/'True'/'False' depending on import path."""
    if isinstance(val, bool):
        return val
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return False
    if isinstance(val, (int, np.integer)):
        return bool(val)
    if isinstance(val, str):
        return val.strip().lower() in {"true", "1", "yes", "y"}
    return bool(val)


def compute_variant_a(agg_level: str = "major") -> pd.DataFrame:
    """Variant A — naive non-physical task share by group, freq-weighted.

    For each task-occ pair: w_all = freq_mean, w_nonphys = freq_mean if
    non-physical else 0. Per group (occupation / broad / minor / major):
    pct_A = Σ w_nonphys / Σ w_all × 100  (ratio of totals).

    Returns DataFrame with columns: category, pct_tasks_affected.
    """
    cols = [
        "title_current", "task_normalized",
        "broad_occ", "minor_occ_category", "major_occ_category",
        "physical", "freq_mean",
    ]
    df = pd.read_csv(DATA_DIR / "final_eco_2025.csv", usecols=cols)
    df = df.groupby(["title_current", "task_normalized"], sort=False, as_index=False).first()
    df["physical_bool"] = df["physical"].apply(_coerce_phys_bool)
    df["freq_mean"] = df["freq_mean"].fillna(0.0).astype(float)
    df["w_all"]      = df["freq_mean"]
    df["w_nonphys"]  = np.where(df["physical_bool"], 0.0, df["freq_mean"])

    gc = LEVEL_COL[agg_level]
    agg = df.groupby(gc, sort=False, as_index=False).agg(
        num=("w_nonphys", "sum"),
        den=("w_all", "sum"),
    )
    agg["pct_tasks_affected"] = (
        agg["num"] / agg["den"].replace(0, np.nan) * 100.0
    ).fillna(0.0)
    return agg.rename(columns={gc: "category"})[["category", "pct_tasks_affected"]]


def compute_variant_a_gwa() -> pd.DataFrame:
    """Variant A at GWA level: pct_A per GWA = Σ freq_mean[non-phys] /
    Σ freq_mean[all] within the GWA's task pool. eco_2025 expands tasks by
    work-activity so we group on (task_normalized, gwa_title) rather than
    deduping by task alone."""
    cols = ["task_normalized", "gwa_title", "physical", "freq_mean"]
    df = pd.read_csv(DATA_DIR / "final_eco_2025.csv", usecols=cols)
    df = df.dropna(subset=["gwa_title"])
    df = df.groupby(["task_normalized", "gwa_title"], sort=False, as_index=False).first()
    df["physical_bool"] = df["physical"].apply(_coerce_phys_bool)
    df["freq_mean"] = df["freq_mean"].fillna(0.0).astype(float)
    df["w_all"]     = df["freq_mean"]
    df["w_nonphys"] = np.where(df["physical_bool"], 0.0, df["freq_mean"])
    agg = df.groupby("gwa_title", sort=False, as_index=False).agg(
        num=("w_nonphys", "sum"),
        den=("w_all", "sum"),
    )
    agg["pct_tasks_affected"] = (
        agg["num"] / agg["den"].replace(0, np.nan) * 100.0
    ).fillna(0.0)
    return agg.rename(columns={"gwa_title": "category"})[["category", "pct_tasks_affected"]]


# ─────────────────────────────────────────────────────────────────────────
# Trend helpers — linear OLS projection (mirrors Part 1's extrapolation)
# ─────────────────────────────────────────────────────────────────────────

def _linear_project(dates: list[pd.Timestamp], yvals: list[float],
                    horizon_days: int) -> tuple[float, float, float]:
    """OLS y = a + b·t. Returns (slope_b_per_day, projected_y, r_squared).

    Linear is the simplest defensible "if recent rate continues" model
    given 4-snapshot input series; longer horizons need richer models."""
    if len(dates) < 2:
        return 0.0, float(yvals[-1] if yvals else 0.0), 0.0
    t0 = dates[0]
    x = np.array([(t - t0).days for t in dates], dtype=float)
    y = np.array(yvals, dtype=float)
    b, a = np.polyfit(x, y, deg=1)
    last_x = x[-1]
    projected = float(a + b * (last_x + horizon_days))
    # r²
    y_pred = a + b * x
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return float(b), projected, r2


def _get_national_totals() -> tuple[float, float]:
    from backend.compute import load_eco_raw
    eco = load_eco_raw()
    occ = eco.drop_duplicates(subset=["title_current"])
    total_emp = float(occ["emp_tot_nat_2025"].sum())
    total_wages = float((occ["emp_tot_nat_2025"] * occ["a_med_nat_2025"]).sum())
    return total_emp, total_wages


def _load_occ_structural() -> pd.DataFrame:
    """Load eco_2025 and compute per-occupation structural data:
    pct_physical, occ_group, job_zone.

    pct_physical is computed over UNIQUE (occ, task) pairs — eco_2025 expands
    each task across its GWA/IWA/DWA classifications, and that expansion is
    not proportional between physical and non-physical tasks. Counting raw
    rows weights tasks by their WA-expansion factor and produces the wrong
    per-occ physical share. This matches the dashboard backend pipeline.
    """
    eco = pd.read_csv(DATA_DIR / "final_eco_2025.csv")
    assert "title_current" in eco.columns
    assert "physical" in eco.columns
    assert "job_zone" in eco.columns
    assert "task_normalized" in eco.columns

    # Dedup on (occ, task) before counting. job_zone, emp, wage are occ-level
    # constants so the dedup leaves them untouched.
    eco_unique = eco.drop_duplicates(["title_current", "task_normalized"])

    occ = (
        eco_unique.groupby("title_current")
        .agg(
            n_tasks=("physical", "count"),
            n_physical=("physical", "sum"),
            job_zone=("job_zone", "first"),
            emp=("emp_tot_nat_2025", "first"),
            wage=("a_med_nat_2025", "first"),
        )
        .reset_index()
    )
    occ["pct_physical"] = occ["n_physical"] / occ["n_tasks"] * 100

    occ["occ_group"] = "Mixed"
    occ.loc[occ["pct_physical"] < PHYS_LOWER, "occ_group"] = "Non-physical"
    occ.loc[occ["pct_physical"] > PHYS_UPPER, "occ_group"] = "Physical"

    return occ


def _get_wa_data(dataset_name: str, level: str = "gwa") -> pd.DataFrame:
    """Get work activity exposure for one pre-combined dataset."""
    from backend.compute import compute_work_activities
    settings = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": "nat",
        "sort_by": "workers_affected",
        "top_n": 9999,
    }
    result = compute_work_activities(settings)
    group = result.get("mcp_group") or result.get("aei_group")
    if group is None:
        return pd.DataFrame()
    rows = group.get(level, [])
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────
# Chart 1: Physical / Informational Divide
# ─────────────────────────────────────────────────────────────────────────

def build_phys_info_divide(results: Path, figures: Path) -> None:
    occ = _load_occ_structural()
    pct = get_pct_tasks_affected(PRIMARY_DATASET)

    occ["pct_tasks_affected"] = occ["title_current"].map(pct)
    occ = occ.dropna(subset=["pct_tasks_affected"])

    # Summary stats for CSV
    summary_rows = []
    for grp in OCC_GROUPS:
        sub = occ[occ["occ_group"] == grp]
        summary_rows.append({
            "occ_group": grp,
            "n_occs": len(sub),
            "median_pct": round(float(sub["pct_tasks_affected"].median()), 1),
            "mean_pct": round(float(sub["pct_tasks_affected"].mean()), 1),
            "q25": round(float(sub["pct_tasks_affected"].quantile(0.25)), 1),
            "q75": round(float(sub["pct_tasks_affected"].quantile(0.75)), 1),
        })
    save_csv(pd.DataFrame(summary_rows), results / "phys_info_summary.csv")

    # Box plot
    fig = go.Figure()

    for grp in OCC_GROUPS:
        subset = occ[occ["occ_group"] == grp]
        fig.add_trace(go.Box(
            x=subset["pct_tasks_affected"],
            name=f"{grp}  (n={len(subset)})",
            marker_color=GROUP_COLORS[grp],
            line_color=GROUP_COLORS[grp],
            fillcolor=GROUP_COLORS[grp],
            opacity=0.7,
            boxmean=True,
            orientation="h",
        ))

    fig.update_layout(
        yaxis=dict(
            categoryorder="array",
            categoryarray=[
                f"{g}  (n={int(occ[occ['occ_group'] == g].shape[0])})"
                for g in reversed(OCC_GROUPS)
            ],
        ),
    )

    style_paper_figure(
        fig,
        "Task Exposure by Physical, Mixed, or Non-Physical Occupations",
        subtitle=(
            f"Distribution of % tasks exposed across {len(occ)} occupations "
            "(Physical = >67% tasks physical · Mixed = 33–67% · Non-physical = <33%)"
        ),
        height=460,
        width=PAPER_W,
        margin=dict(l=80, r=60, t=100, b=80),
    )

    fig.update_layout(showlegend=False)

    fig.update_xaxes(
        title=dict(text="% Tasks Exposed", font=dict(size=LABEL_FS)),
        range=[0, 100], dtick=10,
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        showline=True, linecolor=PAPER_PALETTE["grid"],
    )
    fig.update_yaxes(
        title=dict(text="Occupation Group", font=dict(size=LABEL_FS - 2)),
        showgrid=False, showline=False,
        tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
    )

    save_figure(fig, results / "figures" / "phys_info_divide.png")
    _copy_fig(results, figures, "phys_info_divide.png")
    print("  -> phys_info_divide.png")


# ─────────────────────────────────────────────────────────────────────────
# Chart 2: Job Zone Violin
# ─────────────────────────────────────────────────────────────────────────

def build_job_zone_violin(results: Path, figures: Path) -> None:
    occ = _load_occ_structural()
    pct = get_pct_tasks_affected(PRIMARY_DATASET)

    occ["pct_tasks_affected"] = occ["title_current"].map(pct)
    occ = occ.dropna(subset=["pct_tasks_affected", "job_zone"])
    occ["job_zone"] = occ["job_zone"].astype(int)

    # Summary stats — including phys-mix breakdown per zone
    zone_stats = []
    for z in sorted(occ["job_zone"].unique()):
        sub = occ[occ["job_zone"] == z]
        n_total = len(sub)
        n_phys = int((sub["occ_group"] == "Physical").sum())
        n_mix  = int((sub["occ_group"] == "Mixed").sum())
        n_non  = int((sub["occ_group"] == "Non-physical").sum())
        zone_stats.append({
            "job_zone": z,
            "n_occs": n_total,
            "median_pct": round(float(sub["pct_tasks_affected"].median()), 1),
            "mean_pct": round(float(sub["pct_tasks_affected"].mean()), 1),
            "q25": round(float(sub["pct_tasks_affected"].quantile(0.25)), 1),
            "q75": round(float(sub["pct_tasks_affected"].quantile(0.75)), 1),
            "n_physical":     n_phys,
            "n_mixed":        n_mix,
            "n_non_physical": n_non,
            "pct_physical":     round(n_phys / n_total * 100, 1) if n_total else 0.0,
            "pct_mixed":        round(n_mix / n_total * 100, 1) if n_total else 0.0,
            "pct_non_physical": round(n_non / n_total * 100, 1) if n_total else 0.0,
        })
    stats_df = pd.DataFrame(zone_stats)
    save_csv(stats_df, results / "job_zone_summary.csv")

    # Color gradient: Zone 1 lightest, Zone 5 darkest
    zone_colors = {
        1: "#b8cfe0",  # Light slate
        2: "#8cafc5",
        3: "#6090aa",
        4: "#3a6f8f",
        5: "#1a4f73",  # Deep slate
    }

    zones = sorted(occ["job_zone"].unique())
    zone_labels_full = [
        f"{ZONE_LABELS.get(z, f'Zone {z}')}  (n={int(occ[occ['job_zone'] == z].shape[0])})"
        for z in zones
    ]

    # Two-panel layout: violins on the left, phys-mix stacked bar on the right.
    # Shared y-axis ordering so each zone row aligns. The phys-mix panel is
    # narrow (~15% width) so it reads as an overlay, not a competing chart.
    fig = make_subplots(
        rows=1, cols=2,
        shared_yaxes=True,
        column_widths=[0.85, 0.15],
        horizontal_spacing=0.02,
        subplot_titles=["", "Phys Mix"],
    )

    for z in zones:
        sub = occ[occ["job_zone"] == z]
        label = ZONE_LABELS.get(z, f"Zone {z}")
        fig.add_trace(go.Violin(
            x=sub["pct_tasks_affected"],
            y=[f"{label}  (n={len(sub)})"] * len(sub),
            name=f"{label}  (n={len(sub)})",
            marker_color=zone_colors[z],
            line_color=zone_colors[z],
            fillcolor=zone_colors[z],
            opacity=0.7,
            box_visible=True,
            meanline_visible=True,
            orientation="h",
            side="positive",
            width=0.8,
            showlegend=False,
            hovertemplate=f"{label}<br>%{{x:.1f}}%<extra></extra>",
        ), row=1, col=1)

    # Phys-mix stacked bar: one row per zone, three segments (Phys / Mixed /
    # Non-physical) using the same palette as the major trio. Legend shown
    # below the chart.
    y_labels = []
    for r in zone_stats:
        z = r["job_zone"]
        zone_label = ZONE_LABELS.get(z, f"Zone {z}")
        y_labels.append(f"{zone_label}  (n={int(r['n_occs'])})")
    pct_phys_arr = [r["pct_physical"]     for r in zone_stats]
    pct_mix_arr  = [r["pct_mixed"]        for r in zone_stats]
    pct_non_arr  = [r["pct_non_physical"] for r in zone_stats]

    fig.add_trace(go.Bar(
        x=pct_phys_arr, y=y_labels, orientation="h",
        marker=dict(color=GROUP_COLORS["Physical"], line=dict(width=0)),
        name="% Physical occs",
        showlegend=True,
        hovertemplate="Physical: %{x:.0f}%<extra></extra>",
    ), row=1, col=2)
    fig.add_trace(go.Bar(
        x=pct_mix_arr, y=y_labels, orientation="h",
        marker=dict(color=GROUP_COLORS["Mixed"], line=dict(width=0)),
        name="% Mixed occs",
        showlegend=True,
        hovertemplate="Mixed: %{x:.0f}%<extra></extra>",
    ), row=1, col=2)
    fig.add_trace(go.Bar(
        x=pct_non_arr, y=y_labels, orientation="h",
        marker=dict(color=GROUP_COLORS["Non-physical"], line=dict(width=0)),
        name="% Non-physical occs",
        showlegend=True,
        hovertemplate="Non-physical: %{x:.0f}%<extra></extra>",
    ), row=1, col=2)

    annot_text = "<br>".join(
        f"Zone {r['job_zone']}: median {r['median_pct']:.1f}%, mean {r['mean_pct']:.1f}%"
        for r in zone_stats
    )
    fig.add_annotation(
        text=annot_text,
        xref="x", yref="paper",
        x=99, y=0.98,
        showarrow=False,
        font=dict(size=ANNOT_FS, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        align="right",
        xanchor="right", yanchor="top",
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor=PAPER_PALETTE["grid"],
        borderwidth=1, borderpad=6,
    )

    style_paper_figure(
        fig,
        "Task Exposure by Job Zone (with Physical Mix Overlay)",
        subtitle=(
            f"Distribution of % tasks exposed by O*NET job zone across {len(occ)} occupations. "
            "Right panel: share of each zone's occupations that are Physical / Mixed / Non-Physical."
        ),
        height=700,
        width=PAPER_W + 80,
        margin=dict(l=80, r=60, t=110, b=170),
    )

    # Order zones from top to bottom (highest zone at top).
    cat_array = list(reversed(zone_labels_full))
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=cat_array,
        showgrid=False, showline=False,
        tickfont=dict(size=TICK_FS - 1, family=FONT_FAMILY),
        title=dict(text="Job Zone (O*NET Preparation Level)", font=dict(size=LABEL_FS - 2)),
        row=1, col=1,
    )
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=cat_array,
        showgrid=False, showline=False,
        showticklabels=False,
        row=1, col=2,
    )

    fig.update_xaxes(
        title=dict(text="% Tasks Exposed", font=dict(size=LABEL_FS)),
        range=[0, 100], dtick=10,
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        showline=True, linecolor=PAPER_PALETTE["grid"],
        row=1, col=1,
    )
    fig.update_xaxes(
        range=[0, 100], dtick=25,
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        showline=True, linecolor=PAPER_PALETTE["grid"],
        ticksuffix="%",
        tickfont=dict(size=TICK_FS - 3, family=FONT_FAMILY),
        title=dict(text="% of zone", font=dict(size=LABEL_FS - 4)),
        row=1, col=2,
    )

    fig.update_layout(
        barmode="stack",
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.18, xanchor="center", x=0.5,
            font=dict(size=LEGEND_FS - 1, family=FONT_FAMILY),
            bgcolor="rgba(255,255,255,0.9)",
        ),
    )

    # Force the right-panel subplot title down so it doesn't collide with
    # the main figure title.
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text == "Phys Mix":
            ann.font = dict(size=LABEL_FS - 2, family=FONT_FAMILY,
                            color=PAPER_PALETTE["text"])

    save_figure(fig, results / "figures" / "job_zone_violin.png")
    _copy_fig(results, figures, "job_zone_violin.png")
    print("  -> job_zone_violin.png")


# ─────────────────────────────────────────────────────────────────────────
# Combined Phys/Info × Job Zone — Option A (stacked) and Option B (faceted)
# ─────────────────────────────────────────────────────────────────────────

ZONE_COLORS = {
    1: "#b8cfe0",
    2: "#8cafc5",
    3: "#6090aa",
    4: "#3a6f8f",
    5: "#1a4f73",
}


def _occ_with_pct() -> pd.DataFrame:
    occ = _load_occ_structural()
    pct = get_pct_tasks_affected(PRIMARY_DATASET)
    occ["pct_tasks_affected"] = occ["title_current"].map(pct)
    occ = occ.dropna(subset=["pct_tasks_affected", "job_zone"])
    occ["job_zone"] = occ["job_zone"].astype(int)
    return occ


def build_combined_stacked(results: Path, figures: Path) -> None:
    """Option A — phys/info boxes (top) + job zone violins (bottom), shared x-axis."""
    occ = _occ_with_pct()
    zones = sorted(occ["job_zone"].unique())
    n_phys = len(OCC_GROUPS)
    n_zones = len(zones)

    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[n_phys / (n_phys + n_zones), n_zones / (n_phys + n_zones)],
        shared_xaxes=True,
        vertical_spacing=0.07,
        subplot_titles=[
            "Physical / Informational Divide",
            "Job Zone (Preparation Level)",
        ],
    )

    # Top: phys/info boxes
    for grp in OCC_GROUPS:
        sub = occ[occ["occ_group"] == grp]
        fig.add_trace(go.Box(
            x=sub["pct_tasks_affected"],
            name=f"{grp}  (n={len(sub)})",
            marker_color=GROUP_COLORS[grp],
            line_color=GROUP_COLORS[grp],
            fillcolor=GROUP_COLORS[grp],
            opacity=0.7,
            boxmean=True,
            orientation="h",
            showlegend=False,
        ), row=1, col=1)

    # Bottom: zone violins
    for z in zones:
        sub = occ[occ["job_zone"] == z]
        label = ZONE_LABELS.get(z, f"Zone {z}")
        fig.add_trace(go.Violin(
            x=sub["pct_tasks_affected"],
            name=f"{label}  (n={len(sub)})",
            marker_color=ZONE_COLORS[z],
            line_color=ZONE_COLORS[z],
            fillcolor=ZONE_COLORS[z],
            opacity=0.7,
            box_visible=True,
            meanline_visible=True,
            orientation="h",
            side="positive",
            width=0.85,
            showlegend=False,
        ), row=2, col=1)

    # Y-axis ordering per row
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=[
            f"{g}  (n={int(occ[occ['occ_group'] == g].shape[0])})"
            for g in reversed(OCC_GROUPS)
        ],
        showgrid=False, showline=False,
        tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
        row=1, col=1,
    )
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=[
            f"{ZONE_LABELS.get(z, f'Zone {z}')}  (n={int(occ[occ['job_zone'] == z].shape[0])})"
            for z in reversed(zones)
        ],
        showgrid=False, showline=False,
        tickfont=dict(size=TICK_FS - 1, family=FONT_FAMILY),
        row=2, col=1,
    )

    fig.update_xaxes(
        range=[0, 100], dtick=10,
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        showline=True, linecolor=PAPER_PALETTE["grid"],
        row=1, col=1,
    )
    fig.update_xaxes(
        range=[0, 100], dtick=10,
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        showline=True, linecolor=PAPER_PALETTE["grid"],
        title=dict(text="% Tasks Affected", font=dict(size=LABEL_FS)),
        row=2, col=1,
    )

    style_paper_figure(
        fig,
        "Where AI Exposure Falls — by Physical Mix and Preparation Level",
        subtitle=f"Distribution of % tasks affected across {len(occ)} occupations",
        height=820,
        width=PAPER_W,
        margin=dict(l=20, r=60, t=90, b=70),
    )

    # Style subplot titles
    panel_titles = {
        "Physical / Informational Divide",
        "Job Zone (Preparation Level)",
    }
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in panel_titles:
            ann.font = dict(size=LABEL_FS, family=FONT_FAMILY, color=PAPER_PALETTE["text"])

    save_figure(fig, results / "figures" / "phys_zone_stacked.png", scale=2)
    _copy_fig(results, figures, "phys_zone_stacked.png")
    print("  -> phys_zone_stacked.png")


def build_combined_faceted(results: Path, figures: Path) -> None:
    """Option B — 3 panels (Non-physical / Mixed / Physical), each containing 5
    job zone violins. Cross-tab view.
    """
    occ = _occ_with_pct()
    zones = sorted(occ["job_zone"].unique())

    # Cross-tab summary CSV
    rows_csv = []
    for grp in OCC_GROUPS:
        for z in zones:
            sub = occ[(occ["occ_group"] == grp) & (occ["job_zone"] == z)]
            rows_csv.append({
                "occ_group": grp,
                "job_zone": z,
                "n_occs": len(sub),
                "median_pct": round(float(sub["pct_tasks_affected"].median()), 1) if len(sub) else None,
                "mean_pct": round(float(sub["pct_tasks_affected"].mean()), 1) if len(sub) else None,
            })
    save_csv(pd.DataFrame(rows_csv), results / "phys_zone_crosstab.csv")

    panel_titles = [
        f"{g}  (n={int(occ[occ['occ_group'] == g].shape[0])})"
        for g in OCC_GROUPS
    ]

    fig = make_subplots(
        rows=1, cols=3,
        shared_yaxes=True,
        horizontal_spacing=0.04,
        subplot_titles=panel_titles,
    )

    y_labels = [f"Zone {z}" for z in zones]

    for col_idx, grp in enumerate(OCC_GROUPS, start=1):
        grp_df = occ[occ["occ_group"] == grp]
        for z in zones:
            sub = grp_df[grp_df["job_zone"] == z]
            label = f"Zone {z}"
            if len(sub) == 0:
                # Add an invisible placeholder so the axis row still renders
                fig.add_trace(go.Scatter(
                    x=[None], y=[label],
                    mode="markers",
                    marker=dict(opacity=0),
                    showlegend=False,
                    hoverinfo="skip",
                ), row=1, col=col_idx)
                continue
            fig.add_trace(go.Violin(
                x=sub["pct_tasks_affected"],
                y=[label] * len(sub),
                marker_color=ZONE_COLORS[z],
                line_color=ZONE_COLORS[z],
                fillcolor=ZONE_COLORS[z],
                opacity=0.7,
                box_visible=True,
                meanline_visible=True,
                orientation="h",
                side="positive",
                width=0.9,
                points=False,
                showlegend=False,
                name=f"{grp} — {label}",
                hovertemplate=(
                    f"{grp}, {label}<br>"
                    "%{x:.1f}%<extra></extra>"
                ),
            ), row=1, col=col_idx)

        # Cell-level n + median annotations to the right of each violin
        for z in zones:
            sub = grp_df[grp_df["job_zone"] == z]
            if len(sub) == 0:
                txt = "n=0"
            else:
                med = sub["pct_tasks_affected"].median()
                txt = f"n={len(sub)}, med {med:.0f}%"
            fig.add_annotation(
                x=99, y=f"Zone {z}",
                xref=f"x{'' if col_idx == 1 else col_idx}",
                yref=f"y{'' if col_idx == 1 else col_idx}",
                text=txt,
                showarrow=False,
                xanchor="right", yanchor="middle",
                font=dict(size=ANNOT_FS - 1, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
            )

    y_order = [f"Zone {z}" for z in reversed(zones)]
    for col_idx in range(1, 4):
        fig.update_yaxes(
            categoryorder="array",
            categoryarray=y_order,
            showgrid=False, showline=False,
            tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
            row=1, col=col_idx,
        )
        x_kwargs = dict(
            range=[0, 100], dtick=20,
            showgrid=True, gridcolor=PAPER_PALETTE["grid"],
            showline=True, linecolor=PAPER_PALETTE["grid"],
            row=1, col=col_idx,
        )
        if col_idx == 2:
            fig.update_xaxes(
                title=dict(text="% Tasks Affected", font=dict(size=LABEL_FS)),
                **x_kwargs,
            )
        else:
            fig.update_xaxes(**x_kwargs)

    style_paper_figure(
        fig,
        "AI Exposure by Physical Mix × Preparation Level",
        subtitle=f"Job zone violins within each occupation group ({len(occ)} occupations)",
        height=640,
        width=PAPER_W,
        margin=dict(l=20, r=60, t=90, b=70),
    )

    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in panel_titles:
            ann.font = dict(size=LABEL_FS, family=FONT_FAMILY, color=PAPER_PALETTE["text"])

    save_figure(fig, results / "figures" / "phys_zone_faceted.png", scale=2)
    _copy_fig(results, figures, "phys_zone_faceted.png")
    print("  -> phys_zone_faceted.png")


# ─────────────────────────────────────────────────────────────────────────
# Chart 3: SKA Levels
# ─────────────────────────────────────────────────────────────────────────

def _compute_ska_variants(
    onet_df: pd.DataFrame,
    pct_series: pd.Series,
    type_name: str,
    phys_map: Optional[pd.Series] = None,
) -> pd.DataFrame:
    """Compute AI and workforce imp×lv variants per element for one SKA
    type. `phys_map` is an optional title_current → pct_physical Series;
    when present, each element record carries `phys_score` (unweighted
    mean of pct_physical across occs with imp ≥ 3 for that element) and
    `phys_tier` (Physical / Mixed / Non-physical bucket)."""
    df = onet_df.copy()
    df["pct"] = df["title"].map(pct_series)
    df = df.dropna(subset=["pct", "importance", "level"])
    df = df[df["importance"] >= IMPORTANCE_THRESHOLD].copy()
    assert len(df) > 0, f"No {type_name} rows after importance filter"

    df["occ_score"] = df["importance"] * df["level"]
    df["ai_product"] = (df["pct"] / 100.0) * df["occ_score"]
    if phys_map is not None:
        df["pct_physical_occ"] = df["title"].map(phys_map)

    records = []
    for element_name, grp in df.groupby("element_name"):
        ai_vals = grp["ai_product"].dropna()
        occ_vals = grp["occ_score"].dropna()
        n_ai = len(ai_vals)
        n_occ = len(occ_vals)
        top_n_ai = min(TOP_N_FOR_AVERAGE, n_ai)
        top_n_occ = min(TOP_N_FOR_AVERAGE, n_occ)

        rec = {
            "element_name": element_name,
            "type": type_name,
            "n_occs": n_ai,
            "ai_95th": float(ai_vals.quantile(0.95)) if n_ai >= 2 else (float(ai_vals.iloc[0]) if n_ai == 1 else float("nan")),
            "ai_max": float(ai_vals.max()) if n_ai >= 1 else float("nan"),
            "ai_top10": float(ai_vals.nlargest(top_n_ai).mean()) if n_ai >= 1 else float("nan"),
            "eco_max": float(occ_vals.max()) if n_occ >= 1 else float("nan"),
            "eco_p95": float(occ_vals.quantile(0.95)) if n_occ >= 2 else (float(occ_vals.iloc[0]) if n_occ == 1 else float("nan")),
            "eco_top10": float(occ_vals.nlargest(top_n_occ).mean()) if n_occ >= 1 else float("nan"),
            "eco_mean": float(occ_vals.mean()) if n_occ >= 1 else float("nan"),
        }
        if phys_map is not None:
            phys_vals = grp["pct_physical_occ"].dropna()
            phys_score = float(phys_vals.mean()) if len(phys_vals) else float("nan")
            rec["phys_score"] = phys_score
            rec["phys_tier"] = _phys_tier(phys_score) if pd.notna(phys_score) else "Non-physical"
        records.append(rec)

    return pd.DataFrame(records)


# O*NET subcategory maps (mirror ska_category_breakdown)
ABILITY_SUBCATEGORY: dict[str, str] = {
    "1.A.1.a": "Verbal", "1.A.1.b": "Idea Generation", "1.A.1.c": "Quantitative",
    "1.A.1.d": "Memory", "1.A.1.e": "Perceptual", "1.A.1.f": "Spatial",
    "1.A.1.g": "Attentiveness",
    "1.A.2.a": "Fine Manipulative", "1.A.2.b": "Control Movement", "1.A.2.c": "Reaction",
    "1.A.3.a": "Strength", "1.A.3.b": "Endurance",
    "1.A.3.c": "Flexibility, Balance, Coordination",
    "1.A.4.a": "Visual", "1.A.4.b": "Auditory and Speech",
}

KNOWLEDGE_CATEGORY: dict[str, str] = {
    "2.C.1": "Business and Management",
    "2.C.2": "Manufacturing and Production",
    "2.C.3": "Engineering and Technology",
    "2.C.4": "Mathematics and Science",
    "2.C.5": "Health Services",
    "2.C.6": "Education and Training",
    "2.C.7": "Arts and Humanities",
    "2.C.8": "Law and Public Safety",
    "2.C.9": "Communications",
    "2.C.10": "Transportation",
}

# Muted red for AI markers — visible on blue without being aggressive
AI_MARKER_COLOR = "#a04444"

# SKA AI Top-10 bar color per phys-mix tier. Uses the same Physical / Mixed
# / Non-physical palette as the major trio so the structural cut tracks
# visually across Part 2.
SKA_BAR_COLOR_BY_TIER: dict[str, str] = {
    "Non-physical": METRIC_COLORS["tasks"],     # Slate blue — same as default tasks
    "Mixed":        METRIC_COLORS["wages"],     # Sage green
    "Physical":     METRIC_COLORS["workers"],   # Gold / yellow
}


def _major_phys_mix_shares(occ_struct: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Per-major % of occupations in each phys/mixed/non-phys bucket.

    `occ_struct` is the output of `_load_occ_structural()`. We join it to
    eco_2025's title_current → major mapping and tally occ_group shares
    per major. The result is consumed by panel 6 of the major trio."""
    from backend.compute import load_eco_raw
    eco = load_eco_raw()
    occ_to_major = (
        eco[["title_current", "major_occ_category"]]
        .drop_duplicates()
        .set_index("title_current")["major_occ_category"]
    )
    df = occ_struct[["title_current", "occ_group"]].copy()
    df["major"] = df["title_current"].map(occ_to_major)
    df = df.dropna(subset=["major"])

    out: dict[str, dict[str, float]] = {}
    for major, grp in df.groupby("major"):
        total = len(grp)
        if total == 0:
            continue
        counts = grp["occ_group"].value_counts()
        out[str(major)] = {
            "pct_physical":     float(counts.get("Physical", 0)     / total * 100.0),
            "pct_mixed":        float(counts.get("Mixed", 0)        / total * 100.0),
            "pct_non_physical": float(counts.get("Non-physical", 0) / total * 100.0),
            "n_occs":           total,
        }
    return out


def _gwa_phys_task_shares() -> dict[str, dict[str, float]]:
    """Per-GWA % of tasks that are physical vs non-physical.

    Dedupes to (task_normalized, gwa_title) before tallying, since eco_2025
    expands tasks across the work-activity hierarchy. Two-segment readout
    (no "mixed" — task physical flag is binary)."""
    cols = ["task_normalized", "gwa_title", "physical"]
    df = pd.read_csv(DATA_DIR / "final_eco_2025.csv", usecols=cols)
    df = df.dropna(subset=["gwa_title"])
    df = df.groupby(["task_normalized", "gwa_title"], sort=False, as_index=False).first()
    df["physical_bool"] = df["physical"].apply(_coerce_phys_bool)

    out: dict[str, dict[str, float]] = {}
    for gwa, grp in df.groupby("gwa_title"):
        total = len(grp)
        if total == 0:
            continue
        n_phys = int(grp["physical_bool"].sum())
        out[str(gwa)] = {
            "pct_physical":     float(n_phys / total * 100.0),
            "pct_non_physical": float((total - n_phys) / total * 100.0),
            "n_tasks":          total,
        }
    return out


def _load_occ_phys_map() -> pd.Series:
    """title_current → pct_physical (occ-level), used to color SKA element
    rows by the average physicality of their user base. Counts UNIQUE
    (occ, task) pairs (eco_2025 expands tasks across GWA/IWA/DWA, and that
    expansion is not proportional between physical and non-physical tasks),
    so dedup is required before the n_physical / n_tasks division. Matches
    `_load_occ_structural` and the dashboard backend pipeline."""
    eco = pd.read_csv(DATA_DIR / "final_eco_2025.csv",
                       usecols=["title_current", "task_normalized", "physical"])
    eco_unique = eco.drop_duplicates(["title_current", "task_normalized"])
    eco_unique["physical_bool"] = eco_unique["physical"].apply(_coerce_phys_bool)
    grouped = eco_unique.groupby("title_current")["physical_bool"].agg(["sum", "count"])
    pct_phys = (grouped["sum"] / grouped["count"] * 100.0).fillna(0.0)
    return pct_phys


def _phys_tier(pct_physical: float) -> str:
    if pct_physical > PHYS_UPPER:
        return "Physical"
    if pct_physical < PHYS_LOWER:
        return "Non-physical"
    return "Mixed"


def _ability_subcat(eid: str) -> str:
    parts = eid.split(".")
    sub_key = ".".join(parts[:4]) if len(parts) >= 4 else ".".join(parts[:3])
    return ABILITY_SUBCATEGORY.get(sub_key, "Other")


def _knowledge_cat(eid: str) -> str:
    parts = eid.split(".")
    cat_key_3 = ".".join(parts[:3]) if len(parts) >= 3 else ""
    if cat_key_3 in KNOWLEDGE_CATEGORY:
        return KNOWLEDGE_CATEGORY[cat_key_3]
    cat_key_2 = ".".join(parts[:2]) if len(parts) >= 2 else ""
    return KNOWLEDGE_CATEGORY.get(cat_key_2, "Other")


def _compute_subcategory_rollup(
    onet_path: Path,
    pct_series: pd.Series,
    cat_fn,
    phys_map: Optional[pd.Series] = None,
) -> pd.DataFrame:
    """Per-subcategory rollup of element-level AI capability metrics.

    For each element: imp×lv per (occ, element) row at imp ≥ 3,
    then ai_top10 = mean of top-10 ai_product across occs, ai_max =
    max ai_product, eco_max = max occ_score, eco_mean = mean occ_score.
    Element-level value rolled to subcategory by mean of (metric / eco_max × 100).
    """
    df = pd.read_csv(onet_path, dtype=str)
    df = df.rename(columns={
        "O*NET-SOC Code": "soc_code", "Title": "title",
        "Element ID": "element_id", "Element Name": "element_name",
        "Scale ID": "scale_id", "Data Value": "data_value",
    })
    df["data_value"] = pd.to_numeric(df["data_value"], errors="coerce")
    df = df[df["scale_id"].isin(["IM", "LV"])]

    pivoted = (
        df.pivot_table(
            index=["soc_code", "title", "element_id", "element_name"],
            columns="scale_id", values="data_value", aggfunc="mean",
        )
        .reset_index()
    )
    pivoted.columns.name = None
    pivoted = pivoted.rename(columns={"IM": "importance", "LV": "level"}).dropna(
        subset=["importance", "level"]
    )

    pivoted["pct"] = pivoted["title"].map(pct_series)
    pivoted = pivoted.dropna(subset=["pct"])
    pivoted = pivoted[pivoted["importance"] >= IMPORTANCE_THRESHOLD].copy()

    pivoted["occ_score"] = pivoted["importance"] * pivoted["level"]
    pivoted["ai_product"] = (pivoted["pct"] / 100.0) * pivoted["occ_score"]
    if phys_map is not None:
        pivoted["pct_physical_occ"] = pivoted["title"].map(phys_map)

    elem_rows = []
    for (eid, ename), grp in pivoted.groupby(["element_id", "element_name"]):
        ai_vals = grp["ai_product"]
        occ_vals = grp["occ_score"]
        n = len(ai_vals)
        top_n = min(TOP_N_FOR_AVERAGE, n)
        rec = {
            "element_id": eid,
            "element_name": ename,
            "subcategory": cat_fn(eid),
            "ai_top10": float(ai_vals.nlargest(top_n).mean()),
            "ai_p95": float(ai_vals.quantile(0.95)) if n >= 2 else float(ai_vals.iloc[0]),
            "ai_max": float(ai_vals.max()),
            "eco_max": float(occ_vals.max()),
            "eco_mean": float(occ_vals.mean()),
        }
        if phys_map is not None:
            phys_vals = grp["pct_physical_occ"].dropna()
            rec["phys_score"] = float(phys_vals.mean()) if len(phys_vals) else float("nan")
        elem_rows.append(rec)
    elem_df = pd.DataFrame(elem_rows)
    for col in ["ai_top10", "ai_p95", "ai_max", "eco_mean"]:
        elem_df[f"{col}_pct"] = elem_df[col] / elem_df["eco_max"] * 100.0

    cat_rows = []
    for sub, grp in elem_df.groupby("subcategory"):
        row = {
            "subcategory": sub,
            "n_elements": len(grp),
            "ai_top10_pct": float(grp["ai_top10_pct"].mean()),
            "ai_p95_pct":   float(grp["ai_p95_pct"].mean()),
            "ai_max_pct":   float(grp["ai_max_pct"].mean()),
            "eco_mean_pct": float(grp["eco_mean_pct"].mean()),
        }
        if "phys_score" in grp.columns:
            phys_vals = grp["phys_score"].dropna()
            phys_score_cat = float(phys_vals.mean()) if len(phys_vals) else float("nan")
            row["phys_score"] = phys_score_cat
            row["phys_tier"]  = _phys_tier(phys_score_cat) if pd.notna(phys_score_cat) else "Non-physical"
        cat_rows.append(row)
    return (
        pd.DataFrame(cat_rows)
        .sort_values("ai_top10_pct", ascending=False)
        .reset_index(drop=True)
    )


def _build_ska_skills_chart(
    elements_df: pd.DataFrame, results: Path, figures: Path
) -> None:
    """Skills only — element-level. All values normalized to % of workforce
    max (eco_max), so the workforce-max bar is always 100% and the AI
    Top-10 bar is the AI capability as % of that ceiling. Markers and the
    workforce mean dot are also % of eco_max — same scaling as the K&A
    chart."""
    df = elements_df.copy()
    df["ai_top10_pct"] = df["ai_top10"] / df["eco_max"].replace(0, float("nan")) * 100
    df["ai_p95_pct"]   = df["ai_95th"]  / df["eco_max"].replace(0, float("nan")) * 100
    df["ai_max_pct"]   = df["ai_max"]   / df["eco_max"].replace(0, float("nan")) * 100
    df["eco_mean_pct"] = df["eco_mean"] / df["eco_max"].replace(0, float("nan")) * 100
    df = df.sort_values("ai_top10_pct", ascending=False).reset_index(drop=True)

    enames = df["element_name"].tolist()
    bar_vals = df["ai_top10_pct"].fillna(0).tolist()
    p95_vals = df["ai_p95_pct"].fillna(0).tolist()
    max_vals = df["ai_max_pct"].fillna(0).tolist()
    emean_vals = df["eco_mean_pct"].fillna(0).tolist()

    # Per-element phys tier color. Falls back to the default tasks color
    # if the phys_tier column is absent (older calls without phys_map).
    if "phys_tier" in df.columns:
        bar_colors = [SKA_BAR_COLOR_BY_TIER.get(t, METRIC_COLORS["tasks"])
                      for t in df["phys_tier"].fillna("Non-physical")]
    else:
        bar_colors = [METRIC_COLORS["tasks"]] * len(enames)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=enames, x=[100] * len(enames), orientation="h",
        name="Workforce Max",
        marker=dict(color="#e8e8e2", line=dict(width=0)),
        hovertemplate="Workforce max: 100%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=enames, x=bar_vals, orientation="h",
        name="AI Top-10 Avg",
        marker=dict(color=bar_colors, opacity=0.88, line=dict(width=0)),
        text=[f"{v:.0f}%" for v in bar_vals],
        textposition="outside",
        textfont=dict(size=12, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        hovertemplate="AI Top-10 avg (% of workforce max): %{x:.1f}%<extra></extra>",
    ))

    # Phys-tier legend entries — invisible bars carrying just the colored
    # marker so the legend can document the three-bucket coloring.
    for tier, tier_color in SKA_BAR_COLOR_BY_TIER.items():
        fig.add_trace(go.Bar(
            y=[None], x=[None], orientation="h",
            name=f"Bar color: {tier} occ mix",
            marker=dict(color=tier_color, opacity=0.88, line=dict(width=0)),
            showlegend=True, hoverinfo="skip",
        ))
    fig.add_trace(go.Scatter(
        y=enames, x=p95_vals, mode="markers",
        name="AI P95",
        marker=dict(color=AI_MARKER_COLOR, symbol="circle", size=11),
        hovertemplate="AI P95 (% of workforce max): %{x:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        y=enames, x=max_vals, mode="markers",
        name="AI Max",
        marker=dict(color=AI_MARKER_COLOR, symbol="diamond", size=12),
        hovertemplate="AI Max (% of workforce max): %{x:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        y=enames, x=emean_vals, mode="markers",
        name="Workforce Mean",
        marker=dict(color="#1a1a1a", symbol="circle", size=8,
                    line=dict(width=1, color="#1a1a1a")),
        hovertemplate="Workforce mean (% of workforce max): %{x:.1f}%<extra></extra>",
    ))

    fig_height = max(1100, len(enames) * 28 + 320)
    fig.update_layout(
        title=dict(
            text=(
                "AI Capability as % of Workforce Max — O*NET Skills"
                f"<br><span style='font-size:{SUBTITLE_FS}px;"
                f"color:{PAPER_PALETTE['muted']}'>"
                "Gray bar = workforce maximum (the highest occupational need "
                "for the element, set to 100%). Blue bar = AI Top-10 average "
                "as a share of that workforce maximum."
                "</span>"
            ),
            font=dict(size=TITLE_FS, color=PAPER_PALETTE["text"], family=FONT_FAMILY),
            x=0.01, xanchor="left",
        ),
        height=fig_height,
        width=PAPER_W,
        font=dict(family=FONT_FAMILY, size=13, color=PAPER_PALETTE["text"]),
        plot_bgcolor=PAPER_PALETTE["surface"],
        paper_bgcolor=PAPER_PALETTE["surface"],
        barmode="overlay",
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.10, xanchor="center", x=0.5,
            font=dict(size=LEGEND_FS, color=PAPER_PALETTE["neutral"]),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
        ),
        margin=dict(l=290, r=140, t=120, b=160),
    )
    fig.update_yaxes(
        title=dict(text="O*NET Skill", font=dict(size=LABEL_FS - 2)),
        autorange="reversed",
        tickfont=dict(size=13, color=PAPER_PALETTE["text"], family=FONT_FAMILY),
        showgrid=False, showline=False,
    )
    fig.update_xaxes(
        title=dict(
            text=(
                "AI Capability as % of Workforce Max "
                "(AI Top-10 Average ÷ Occupation Max for the Element)"
            ),
            font=dict(size=LABEL_FS - 2),
        ),
        range=[0, 100], ticksuffix="%",
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        showticklabels=True,
        tickfont=dict(size=12, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showline=False, zeroline=True, zerolinecolor=PAPER_PALETTE["grid"],
    )

    save_figure(fig, results / "figures" / "ska_skills.png", scale=2)
    _copy_fig(results, figures, "ska_skills.png")
    print("  -> ska_skills.png")


def _build_ska_subcategory_chart(
    knowledge_df: pd.DataFrame,
    abilities_df: pd.DataFrame,
    n_know_elements: int,
    n_abil_elements: int,
    results: Path, figures: Path,
) -> None:
    """Knowledge + Abilities at subcategory level. Each cell is a mean
    across the elements in that subcategory. Bar = AI Top-10 mean (% of
    workforce max). Red diamond = AI Max %, red circle = AI P95 %. Black
    dot = workforce mean %."""
    n_know = len(knowledge_df)
    n_abil = len(abilities_df)
    total = n_know + n_abil
    row_heights = [n_know / total, n_abil / total]

    fig = make_subplots(
        rows=2, cols=1,
        row_heights=row_heights,
        vertical_spacing=0.10,
        subplot_titles=[
            f"Knowledge  ({n_know} subcategories | {n_know_elements} elements)",
            f"Abilities  ({n_abil} subcategories | {n_abil_elements} elements)",
        ],
    )

    legend_shown: set[str] = set()

    def _show(key: str) -> bool:
        if key not in legend_shown:
            legend_shown.add(key)
            return True
        return False

    for row, df in enumerate([knowledge_df, abilities_df], start=1):
        sub_labels = [
            f"{r.subcategory}  (n={int(r.n_elements)})"
            for r in df.itertuples()
        ]
        fig.add_trace(go.Bar(
            y=sub_labels, x=[100] * len(sub_labels), orientation="h",
            name="Workforce Max",
            marker=dict(color="#e8e8e2", line=dict(width=0)),
            showlegend=_show("emax"),
            hovertemplate="Workforce max: 100%<extra></extra>",
        ), row=row, col=1)

        if "phys_tier" in df.columns:
            bar_colors = [SKA_BAR_COLOR_BY_TIER.get(t, METRIC_COLORS["tasks"])
                          for t in df["phys_tier"].fillna("Non-physical")]
        else:
            bar_colors = [METRIC_COLORS["tasks"]] * len(sub_labels)

        fig.add_trace(go.Bar(
            y=sub_labels, x=df["ai_top10_pct"], orientation="h",
            name="AI Top-10 Avg",
            marker=dict(color=bar_colors, opacity=0.88, line=dict(width=0)),
            showlegend=_show("ai_top10"),
            text=[f"{v:.0f}%" for v in df["ai_top10_pct"]],
            textposition="outside",
            textfont=dict(size=12, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
            hovertemplate="AI Top-10 avg (% of max): %{x:.1f}%<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scatter(
            y=sub_labels, x=df["ai_p95_pct"], mode="markers",
            name="AI P95",
            marker=dict(color=AI_MARKER_COLOR, symbol="circle", size=11),
            showlegend=_show("ai_p95"),
            hovertemplate="AI P95 (% of max): %{x:.1f}%<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scatter(
            y=sub_labels, x=df["ai_max_pct"], mode="markers",
            name="AI Max",
            marker=dict(color=AI_MARKER_COLOR, symbol="diamond", size=12),
            showlegend=_show("ai_max"),
            hovertemplate="AI Max (% of max): %{x:.1f}%<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scatter(
            y=sub_labels, x=df["eco_mean_pct"], mode="markers",
            name="Workforce Mean",
            marker=dict(color="#1a1a1a", symbol="circle", size=8,
                        line=dict(width=1, color="#1a1a1a")),
            showlegend=_show("emean"),
            hovertemplate="Workforce mean (% of max): %{x:.1f}%<extra></extra>",
        ), row=row, col=1)

        fig.update_yaxes(
            autorange="reversed", row=row, col=1,
            tickfont=dict(size=13, color=PAPER_PALETTE["text"], family=FONT_FAMILY),
            showgrid=False, showline=False,
        )
        fig.update_xaxes(
            range=[0, 100], ticksuffix="%",
            showgrid=True, gridcolor=PAPER_PALETTE["grid"],
            tickfont=dict(size=12, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
            showline=False, zeroline=True, zerolinecolor=PAPER_PALETTE["grid"],
            row=row, col=1,
        )

    # Phys-tier legend entries — invisible bars carrying just the colored
    # marker so the legend documents the three-bucket coloring.
    for tier, tier_color in SKA_BAR_COLOR_BY_TIER.items():
        fig.add_trace(go.Bar(
            y=[None], x=[None], orientation="h",
            name=f"Bar color: {tier} occ mix",
            marker=dict(color=tier_color, opacity=0.88, line=dict(width=0)),
            showlegend=True, hoverinfo="skip",
        ), row=1, col=1)

    # Y axis titles per subplot
    fig.update_yaxes(
        title=dict(text="O*NET Knowledge Subcategory", font=dict(size=LABEL_FS - 2)),
        row=1, col=1,
    )
    fig.update_yaxes(
        title=dict(text="O*NET Ability Subcategory", font=dict(size=LABEL_FS - 2)),
        row=2, col=1,
    )
    fig.update_xaxes(
        title=dict(
            text=(
                "AI Capability as % of Workforce Max — "
                "Average across the subcategory of (AI Top-10 ÷ Occupation Max per Element)"
            ),
            font=dict(size=LABEL_FS - 2),
        ),
        row=2, col=1,
    )

    fig_height = max(900, total * 35 + 380)

    fig.update_layout(
        title=dict(
            text=(
                "AI Capability as % of Workforce Max — O*NET Knowledge and Abilities"
                f"<br><span style='font-size:{SUBTITLE_FS}px;"
                f"color:{PAPER_PALETTE['muted']}'>"
                "Gray bar = workforce maximum (highest occupational need per element, "
                "set to 100%). Blue bar = AI Top-10 average as a share of that maximum, "
                "averaged across the subcategory."
                "</span>"
            ),
            font=dict(size=TITLE_FS, color=PAPER_PALETTE["text"], family=FONT_FAMILY),
            x=0.01, xanchor="left",
        ),
        height=fig_height,
        width=PAPER_W,
        font=dict(family=FONT_FAMILY, size=13, color=PAPER_PALETTE["text"]),
        plot_bgcolor=PAPER_PALETTE["surface"],
        paper_bgcolor=PAPER_PALETTE["surface"],
        barmode="overlay",
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.10, xanchor="center", x=0.5,
            font=dict(size=LEGEND_FS, color=PAPER_PALETTE["neutral"]),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
        ),
        margin=dict(l=300, r=80, t=120, b=180),
    )

    panel_starts = ("Knowledge  ", "Abilities  ")
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and any(ann.text.startswith(s) for s in panel_starts):
            ann.font = dict(size=LABEL_FS, family=FONT_FAMILY,
                            color=PAPER_PALETTE["text"])

    save_figure(fig, results / "figures" / "ska_knowledge_abilities.png", scale=2)
    _copy_fig(results, figures, "ska_knowledge_abilities.png")
    print("  -> ska_knowledge_abilities.png")


def build_ska_levels(results: Path, figures: Path) -> None:
    pct = get_pct_tasks_affected(PRIMARY_DATASET)
    ska_data = load_ska_data()
    phys_map = _load_occ_phys_map()

    # Skills — element level (per-element bars)
    skills_df = _compute_ska_variants(ska_data.skills, pct, "skills", phys_map=phys_map)
    print(f"    skills: {len(skills_df)} elements")

    # Knowledge — subcategory rollup (10 categories from O*NET 2.C.1–2.C.10)
    know_path = ROOT / "analysis" / "data" / "knowledge_v30.1.csv"
    knowledge_cat = _compute_subcategory_rollup(know_path, pct, _knowledge_cat, phys_map=phys_map)
    n_know_elements = _count_elements(know_path, pct)
    print(f"    knowledge (subcategory): {len(knowledge_cat)} subcategories "
          f"({n_know_elements} elements)")

    # Abilities — subcategory rollup (15 subcategories under 1.A.1–1.A.4)
    abil_path = ROOT / "analysis" / "data" / "abilities_v30.1.csv"
    abilities_cat = _compute_subcategory_rollup(abil_path, pct, _ability_subcat, phys_map=phys_map)
    n_abil_elements = _count_elements(abil_path, pct)
    print(f"    abilities (subcategory): {len(abilities_cat)} subcategories "
          f"({n_abil_elements} elements)")

    save_csv(skills_df, results / "ska_skills.csv", float_format="%.4f")
    save_csv(knowledge_cat, results / "ska_knowledge_by_subcategory.csv",
             float_format="%.2f")
    save_csv(abilities_cat, results / "ska_abilities_by_subcategory.csv",
             float_format="%.2f")

    _build_ska_skills_chart(skills_df, results, figures)
    _build_ska_subcategory_chart(
        knowledge_cat, abilities_cat,
        n_know_elements, n_abil_elements,
        results, figures,
    )

    # Tidy-up: remove the old combined chart if it lingers from earlier runs
    for stale in ("ska_levels.png",):
        for d in (results / "figures", figures):
            p = d / stale
            if p.exists():
                p.unlink()


def _count_elements(onet_path: Path, pct_series: pd.Series) -> int:
    """Number of unique elements after the pct/imp filter — for label use."""
    df = pd.read_csv(onet_path, dtype=str)
    df = df.rename(columns={
        "O*NET-SOC Code": "soc_code", "Title": "title",
        "Element ID": "element_id", "Scale ID": "scale_id",
        "Data Value": "data_value",
    })
    df["data_value"] = pd.to_numeric(df["data_value"], errors="coerce")
    df = df[df["scale_id"].isin(["IM", "LV"])]
    pivoted = (
        df.pivot_table(
            index=["soc_code", "title", "element_id"],
            columns="scale_id", values="data_value", aggfunc="mean",
        )
        .reset_index()
    )
    pivoted.columns.name = None
    pivoted = pivoted.rename(columns={"IM": "importance", "LV": "level"}).dropna(
        subset=["importance", "level"]
    )
    pivoted["pct"] = pivoted["title"].map(pct_series)
    pivoted = pivoted.dropna(subset=["pct"])
    pivoted = pivoted[pivoted["importance"] >= IMPORTANCE_THRESHOLD]
    return int(pivoted["element_id"].nunique())


# ─────────────────────────────────────────────────────────────────────────
# Chart 4: All GWAs by % Tasks Affected
# ─────────────────────────────────────────────────────────────────────────

def build_gwa_chart(results: Path, figures: Path) -> None:
    """Five-panel GWA quintet matching the major trio: variant A % |
    variant B % | all_confirmed % | workers | wages. All ~41 GWAs visible,
    shared y-axis ordered by all_confirmed % tasks descending."""
    base = _get_wa_data(PRIMARY_DATASET, "gwa")
    variant_a = compute_variant_a_gwa()
    variant_b_df = _get_wa_data_with_phys(PRIMARY_DATASET, "gwa", physical_mode="exclude")
    assert not base.empty,      "all_confirmed GWA data is empty"
    assert not variant_a.empty, "variant_a GWA data is empty"
    assert not variant_b_df.empty, "variant_b GWA data is empty"

    base = base.sort_values("pct_tasks_affected", ascending=False).reset_index(drop=True)
    a_map = variant_a.set_index("category")["pct_tasks_affected"]
    b_map = variant_b_df.set_index("category")["pct_tasks_affected"]
    base["pct_a"] = base["category"].map(a_map)
    base["pct_b"] = base["category"].map(b_map)
    save_csv(base, results / "gwa_exposure.csv")

    n_gwas = len(base)

    # Per-GWA phys task shares for panel 6.
    gwa_phys = _gwa_phys_task_shares()

    # Reverse for plotly: top of chart = highest-pct GWA.
    categories_r = list(reversed(base["category"].tolist()))
    pct_a_r     = list(reversed(base["pct_a"].fillna(0.0).tolist()))
    pct_b_r     = list(reversed(base["pct_b"].fillna(0.0).tolist()))
    pct_r       = list(reversed(base["pct_tasks_affected"].tolist()))
    workers_r   = list(reversed(base["workers_affected"].tolist()))
    wages_r     = list(reversed(base["wages_affected"].tolist()))
    pct_phys_r  = [gwa_phys.get(c, {}).get("pct_physical",     0.0) for c in categories_r]
    pct_non_r   = [gwa_phys.get(c, {}).get("pct_non_physical", 0.0) for c in categories_r]

    fig = make_subplots(
        rows=1, cols=6,
        shared_yaxes=True,
        horizontal_spacing=0.03,
        subplot_titles=[
            "Variant A: Non-Phys Task Share",
            "Variant B: % in Non-Phys Work",
            "% Tasks Exposed (All Confirmed)",
            "Workers Exposed (All Confirmed)",
            "Wages Exposed (All Confirmed)",
            "Phys Mix (Tasks)",
        ],
        column_widths=[1.0, 1.0, 1.0, 1.0, 1.0, 0.55],
    )

    VARIANT_A_COLOR = "#7a9ab8"
    VARIANT_B_COLOR = "#3a6f8f"

    fig.add_trace(go.Bar(
        y=categories_r, x=pct_a_r, orientation="h",
        marker=dict(color=VARIANT_A_COLOR, line=dict(width=0)),
        text=[f"{v:.0f}%" for v in pct_a_r],
        textposition="inside", insidetextanchor="end",
        textfont=dict(size=INSIDE_FS - 2, color="white", family=FONT_FAMILY),
        cliponaxis=False, showlegend=False,
        hovertemplate="Variant A: %{x:.1f}%<extra></extra>",
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        y=categories_r, x=pct_b_r, orientation="h",
        marker=dict(color=VARIANT_B_COLOR, line=dict(width=0)),
        text=[f"{v:.0f}%" for v in pct_b_r],
        textposition="inside", insidetextanchor="end",
        textfont=dict(size=INSIDE_FS - 2, color="white", family=FONT_FAMILY),
        cliponaxis=False, showlegend=False,
        hovertemplate="Variant B: %{x:.1f}%<extra></extra>",
    ), row=1, col=2)

    fig.add_trace(go.Bar(
        y=categories_r, x=pct_r, orientation="h",
        marker=dict(color=METRIC_COLORS["tasks"], line=dict(width=0)),
        text=[f"{v:.0f}%" for v in pct_r],
        textposition="inside", insidetextanchor="end",
        textfont=dict(size=INSIDE_FS - 2, color="white", family=FONT_FAMILY),
        cliponaxis=False, showlegend=False,
        hovertemplate="All Confirmed: %{x:.1f}%<extra></extra>",
    ), row=1, col=3)

    fig.add_trace(go.Bar(
        y=categories_r, x=workers_r, orientation="h",
        marker=dict(color=METRIC_COLORS["workers"], line=dict(width=0)),
        text=[fmt_workers(v) for v in workers_r],
        textposition="inside", insidetextanchor="end",
        textfont=dict(size=INSIDE_FS - 2, color="white", family=FONT_FAMILY),
        cliponaxis=False, showlegend=False,
    ), row=1, col=4)

    fig.add_trace(go.Bar(
        y=categories_r, x=wages_r, orientation="h",
        marker=dict(color=METRIC_COLORS["wages"], line=dict(width=0)),
        text=[fmt_wages(v) for v in wages_r],
        textposition="inside", insidetextanchor="end",
        textfont=dict(size=INSIDE_FS - 2, color="white", family=FONT_FAMILY),
        cliponaxis=False, showlegend=False,
    ), row=1, col=5)

    # Panel 6 — per-GWA task phys-mix stacked bar (2-segment, since the
    # task physical flag is binary at the task level). Uses `base` to stack
    # manually so the other panels' single-trace bars don't get squeezed.
    fig.add_trace(go.Bar(
        y=categories_r, x=pct_phys_r, base=0, orientation="h",
        marker=dict(color=GROUP_COLORS["Physical"], line=dict(width=0)),
        name="% Physical tasks", showlegend=True,
        hovertemplate="Physical: %{x:.0f}%<extra></extra>",
    ), row=1, col=6)
    fig.add_trace(go.Bar(
        y=categories_r, x=pct_non_r, base=pct_phys_r, orientation="h",
        marker=dict(color=GROUP_COLORS["Non-physical"], line=dict(width=0)),
        name="% Non-physical tasks", showlegend=True,
        hovertemplate="Non-physical: %{x:.0f}%<extra></extra>",
    ), row=1, col=6)

    # Dummy invisible trace carrying just a dashed-line glyph for the legend,
    # so readers know what the 33/67 reference lines mean.
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode="lines",
        line=dict(color="#1a1a1a", width=1.4, dash="dash"),
        name="33% / 67% phys-mix bucket cuts",
        showlegend=True, hoverinfo="skip",
    ), row=1, col=6)

    height = max(PAPER_H + 600, n_gwas * 38 + 320)

    style_paper_figure(
        fig,
        "Task Exposure Across All O*NET General Work Activities — Variants A, B, and All Confirmed",
        subtitle=(
            f"All {n_gwas} GWAs ranked by All Confirmed % tasks exposed. "
            "Variant A = naive non-physical task share within the GWA's task pool. "
            "Variant B = AI exposure restricted to non-physical tasks. "
            "Right panel: share of each GWA's tasks classified as Physical vs Non-Physical."
        ),
        height=height,
        width=PAPER_W + 1000,
        margin=dict(l=40, r=80, t=170, b=140),
    )

    import math

    def _nice_ticks(max_val: float, n_ticks: int = 4) -> list[float]:
        if max_val <= 0:
            return [0.0]
        raw_step = max_val / (n_ticks - 1)
        magnitude = 10 ** math.floor(math.log10(raw_step))
        step = math.ceil(raw_step / magnitude) * magnitude
        ticks = [step * i for i in range(n_ticks + 1)]
        return [t for t in ticks if t <= max_val * 1.05]

    def _strip_zero_decimal(s: str) -> str:
        for unit in ("M", "B", "K", "T"):
            s = s.replace(f".0{unit}", unit)
        return s

    workers_max = float(base["workers_affected"].max())
    wages_max   = float(base["wages_affected"].max())
    worker_ticks = _nice_ticks(workers_max)
    wage_ticks   = _nice_ticks(wages_max)

    fig.update_xaxes(
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        showline=True, linecolor=PAPER_PALETTE["grid"],
        zeroline=True, zerolinecolor=PAPER_PALETTE["grid"],
        tickfont=dict(size=TICK_FS - 2, family=FONT_FAMILY),
    )
    fig.update_xaxes(ticksuffix="%", title=dict(text="% (Variant A)",         font=dict(size=LABEL_FS - 4)), row=1, col=1)
    fig.update_xaxes(ticksuffix="%", title=dict(text="% (Variant B)",         font=dict(size=LABEL_FS - 4)), row=1, col=2)
    fig.update_xaxes(ticksuffix="%", title=dict(text="% Tasks Exposed",       font=dict(size=LABEL_FS - 4)), row=1, col=3)
    fig.update_xaxes(
        tickvals=worker_ticks,
        ticktext=[_strip_zero_decimal(fmt_workers(v)) for v in worker_ticks],
        title=dict(text="Workers Exposed", font=dict(size=LABEL_FS - 4)),
        row=1, col=4,
    )
    fig.update_xaxes(
        tickvals=wage_ticks,
        ticktext=[_strip_zero_decimal(fmt_wages(v)) for v in wage_ticks],
        title=dict(text="Wages Exposed", font=dict(size=LABEL_FS - 4)),
        row=1, col=5,
    )
    fig.update_xaxes(
        range=[0, 100], dtick=25,
        ticksuffix="%", tickfont=dict(size=TICK_FS - 4, family=FONT_FAMILY),
        title=dict(text="% of GWA's tasks", font=dict(size=LABEL_FS - 4)),
        row=1, col=6,
    )

    # 33% and 67% reference lines on the phys-mix panel — same thresholds
    # used to bucket occupations as Non-physical / Mixed / Physical, so a
    # GWA whose phys segment crosses 67 reads as predominantly physical,
    # and one whose phys segment stays under 33 reads as predominantly
    # non-physical. Dark gray with strong opacity so the line reads
    # consistently against colored bars and the white row gaps between
    # bars; "above" layer so the line is never hidden by the bars.
    fig.add_vline(
        x=33, layer="above",
        line=dict(color="#1a1a1a", width=1.4, dash="dash"),
        row=1, col=6, opacity=0.85,
    )
    fig.add_vline(
        x=67, layer="above",
        line=dict(color="#1a1a1a", width=1.4, dash="dash"),
        row=1, col=6, opacity=0.85,
    )

    fig.update_yaxes(showgrid=False, showline=False)
    fig.update_yaxes(
        title=dict(text="O*NET General Work Activity", font=dict(size=LABEL_FS - 2)),
        tickfont=dict(size=TICK_FS - 2, family=FONT_FAMILY),
        row=1, col=1,
    )

    panel_titles = {
        "Variant A: Non-Phys Task Share",
        "Variant B: % in Non-Phys Work",
        "% Tasks Exposed (All Confirmed)",
        "Workers Exposed (All Confirmed)",
        "Wages Exposed (All Confirmed)",
        "Phys Mix (Tasks)",
    }
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in panel_titles:
            ann.font = dict(size=LABEL_FS - 2, family=FONT_FAMILY,
                            color=PAPER_PALETTE["text"])

    fig.update_layout(
        bargap=0.3,
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.04, xanchor="center", x=0.5,
            font=dict(size=LEGEND_FS - 2, family=FONT_FAMILY),
            bgcolor="rgba(255,255,255,0.9)",
        ),
    )

    save_figure(fig, results / "figures" / "gwa_exposure.png", scale=2)
    _copy_fig(results, figures, "gwa_exposure.png")
    print("  -> gwa_exposure.png")


def _get_wa_data_with_phys(dataset_name: str, level: str, physical_mode: str) -> pd.DataFrame:
    """Variant of _get_wa_data that lets the caller override physical_mode
    (variant B uses 'exclude')."""
    from backend.compute import compute_work_activities
    settings = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": physical_mode,
        "geo": "nat",
        "sort_by": "workers_affected",
        "top_n": 9999,
    }
    result = compute_work_activities(settings)
    group = result.get("mcp_group") or result.get("aei_group")
    if group is None:
        return pd.DataFrame()
    rows = group.get(level, [])
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────
# Chart 5: All 22 Major Categories — 3 Side-by-Side Panels
# ─────────────────────────────────────────────────────────────────────────

def build_major_categories(results: Path, figures: Path) -> None:
    """Five-panel major trio: variant A % | variant B % | all_confirmed %
    | all_confirmed workers | all_confirmed wages.

    Variant A — naive non-phys task share (eco only, no AI). Variant B —
    pipeline pct restricted to non-physical tasks on both sides. The
    all_confirmed reading occupies the right three panels just like the
    old major_categories.png. A trailing annotation reports n_occs by
    physical bucket (Phys / Mixed / Non-physical), since the box plot
    that used to carry that distribution has been removed from Part 2."""
    base = _run_config(PRIMARY_DATASET, "major")
    variant_a = compute_variant_a("major")
    variant_b = _run_config(PRIMARY_DATASET, "major", physical_mode="exclude")
    assert not base.empty,      "all_confirmed major data is empty"
    assert not variant_a.empty, "variant_a major data is empty"
    assert not variant_b.empty, "variant_b major data is empty"

    base = base.sort_values("pct_tasks_affected", ascending=False).reset_index(drop=True)
    a_map = variant_a.set_index("category")["pct_tasks_affected"]
    b_map = variant_b.set_index("category")["pct_tasks_affected"]
    base["pct_a"] = base["category"].map(a_map)
    base["pct_b"] = base["category"].map(b_map)
    save_csv(base, results / "major_categories.csv")

    categories = base["category"].tolist()
    n_cats = len(categories)

    # Reverse for plotly: top of chart = highest-pct major.
    categories_r = list(reversed(categories))
    pct_a_r     = list(reversed(base["pct_a"].fillna(0.0).tolist()))
    pct_b_r     = list(reversed(base["pct_b"].fillna(0.0).tolist()))
    pct_r       = list(reversed(base["pct_tasks_affected"].tolist()))
    workers_r   = list(reversed(base["workers_affected"].tolist()))
    wages_r     = list(reversed(base["wages_affected"].tolist()))

    # n_occs by phys bucket — global totals, used in the chart subtitle and
    # for the per-major stacked bar in panel 6. Same cuts (<33 / 33-67 / >67
    # % physical) the variant pipeline uses.
    occ_struct = _load_occ_structural()
    bucket_counts = occ_struct.groupby("occ_group").size().to_dict()
    n_phys = int(bucket_counts.get("Physical", 0))
    n_mix  = int(bucket_counts.get("Mixed", 0))
    n_non  = int(bucket_counts.get("Non-physical", 0))

    # Per-major occupation phys-mix shares for the 6th panel.
    major_phys_mix = _major_phys_mix_shares(occ_struct)
    pct_phys_r = [major_phys_mix.get(c, {}).get("pct_physical",     0.0) for c in categories_r]
    pct_mix_r  = [major_phys_mix.get(c, {}).get("pct_mixed",        0.0) for c in categories_r]
    pct_non_r  = [major_phys_mix.get(c, {}).get("pct_non_physical", 0.0) for c in categories_r]

    fig = make_subplots(
        rows=1, cols=6,
        subplot_titles=[
            "Variant A: Non-Phys Task Share",
            "Variant B: % Tasks Exposed in Non-Phys Work",
            "% Tasks Exposed (All Confirmed)",
            "Workers Exposed (All Confirmed)",
            "Wages Exposed (All Confirmed)",
            "Phys Mix (Occs)",
        ],
        horizontal_spacing=0.04,
        shared_yaxes=True,
        column_widths=[1.0, 1.0, 1.0, 1.0, 1.0, 0.55],
    )

    # Use the workers/wages metric palette for the all_confirmed reading,
    # and a desaturated neutral tone for variants A and B (structural
    # framing — they're scaffolding for the all_confirmed columns).
    VARIANT_A_COLOR = "#7a9ab8"
    VARIANT_B_COLOR = "#3a6f8f"

    fig.add_trace(go.Bar(
        y=categories_r, x=pct_a_r, orientation="h",
        marker=dict(color=VARIANT_A_COLOR, line=dict(width=0)),
        text=[f"{v:.1f}%" for v in pct_a_r],
        textposition="outside",
        textfont=dict(size=ANNOT_FS - 2, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showlegend=False, cliponaxis=False,
        hovertemplate="Variant A: %{x:.1f}%<extra></extra>",
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        y=categories_r, x=pct_b_r, orientation="h",
        marker=dict(color=VARIANT_B_COLOR, line=dict(width=0)),
        text=[f"{v:.1f}%" for v in pct_b_r],
        textposition="outside",
        textfont=dict(size=ANNOT_FS - 2, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showlegend=False, cliponaxis=False,
        hovertemplate="Variant B: %{x:.1f}%<extra></extra>",
    ), row=1, col=2)

    fig.add_trace(go.Bar(
        y=categories_r, x=pct_r, orientation="h",
        marker=dict(color=METRIC_COLORS["tasks"], line=dict(width=0)),
        text=[f"{v:.1f}%" for v in pct_r],
        textposition="outside",
        textfont=dict(size=ANNOT_FS - 2, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showlegend=False, cliponaxis=False,
        hovertemplate="All Confirmed: %{x:.1f}%<extra></extra>",
    ), row=1, col=3)

    fig.add_trace(go.Bar(
        y=categories_r, x=workers_r, orientation="h",
        marker=dict(color=METRIC_COLORS["workers"], line=dict(width=0)),
        text=[fmt_workers(v) for v in workers_r],
        textposition="outside",
        textfont=dict(size=ANNOT_FS - 2, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showlegend=False, cliponaxis=False,
    ), row=1, col=4)

    fig.add_trace(go.Bar(
        y=categories_r, x=wages_r, orientation="h",
        marker=dict(color=METRIC_COLORS["wages"], line=dict(width=0)),
        text=[fmt_wages(v) for v in wages_r],
        textposition="outside",
        textfont=dict(size=ANNOT_FS - 2, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showlegend=False, cliponaxis=False,
    ), row=1, col=5)

    # Panel 6 — per-major occupation phys-mix stacked bar. Uses `base` for
    # manual stacking instead of barmode="stack" so the other panels'
    # single-trace bars don't get squeezed.
    base_mix = pct_phys_r
    base_non = [p + m for p, m in zip(pct_phys_r, pct_mix_r)]
    fig.add_trace(go.Bar(
        y=categories_r, x=pct_phys_r, base=0, orientation="h",
        marker=dict(color=GROUP_COLORS["Physical"], line=dict(width=0)),
        name="% Physical occs", showlegend=True,
        hovertemplate="Physical: %{x:.0f}%<extra></extra>",
    ), row=1, col=6)
    fig.add_trace(go.Bar(
        y=categories_r, x=pct_mix_r, base=base_mix, orientation="h",
        marker=dict(color=GROUP_COLORS["Mixed"], line=dict(width=0)),
        name="% Mixed occs", showlegend=True,
        hovertemplate="Mixed: %{x:.0f}%<extra></extra>",
    ), row=1, col=6)
    fig.add_trace(go.Bar(
        y=categories_r, x=pct_non_r, base=base_non, orientation="h",
        marker=dict(color=GROUP_COLORS["Non-physical"], line=dict(width=0)),
        name="% Non-physical occs", showlegend=True,
        hovertemplate="Non-physical: %{x:.0f}%<extra></extra>",
    ), row=1, col=6)

    height = max(PAPER_H + 200, n_cats * 36 + 220)

    style_paper_figure(
        fig,
        "AI Exposure by Major Occupational Category — Variants A, B, and All Confirmed",
        subtitle=(
            f"All {n_cats} major SOC categories ranked by All Confirmed % tasks exposed. "
            "Variant A = naive non-physical task share (no AI signal). "
            "Variant B = % tasks exposed restricted to non-physical work. "
            "Right panel: share of each major's occupations classified Physical / Mixed / Non-Physical. "
            f"Economy-wide totals: {n_phys} Physical · {n_mix} Mixed · {n_non} Non-physical occupations."
        ),
        height=height + 60,
        width=PAPER_W + 900,
        margin=dict(l=20, r=80, t=160, b=160),
    )

    fig.update_xaxes(
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        showticklabels=True, showline=True, linecolor=PAPER_PALETTE["grid"],
        zeroline=True, zerolinecolor=PAPER_PALETTE["grid"],
        tickfont=dict(size=TICK_FS - 2, family=FONT_FAMILY),
    )

    def _nice_ticks(max_val: float, n_ticks: int = 5) -> list[float]:
        import math
        if max_val <= 0:
            return [0.0]
        raw_step = max_val / (n_ticks - 1)
        magnitude = 10 ** math.floor(math.log10(raw_step))
        step = math.ceil(raw_step / magnitude) * magnitude
        ticks = [step * i for i in range(n_ticks + 1)]
        return [t for t in ticks if t <= max_val * 1.05]

    workers_max = float(base["workers_affected"].max())
    wages_max   = float(base["wages_affected"].max())
    worker_ticks = _nice_ticks(workers_max)
    wage_ticks   = _nice_ticks(wages_max)

    def _strip_zero_decimal(s: str) -> str:
        for unit in ("M", "B", "K", "T"):
            s = s.replace(f".0{unit}", unit)
        return s

    fig.update_xaxes(ticksuffix="%", title=dict(text="% (Variant A)", font=dict(size=LABEL_FS - 4)), row=1, col=1)
    fig.update_xaxes(ticksuffix="%", title=dict(text="% (Variant B)", font=dict(size=LABEL_FS - 4)), row=1, col=2)
    fig.update_xaxes(ticksuffix="%", title=dict(text="% Tasks Exposed", font=dict(size=LABEL_FS - 4)), row=1, col=3)
    fig.update_xaxes(
        tickvals=worker_ticks,
        ticktext=[_strip_zero_decimal(fmt_workers(v)) for v in worker_ticks],
        title=dict(text="Workers Exposed", font=dict(size=LABEL_FS - 4)),
        row=1, col=4,
    )
    fig.update_xaxes(
        tickvals=wage_ticks,
        ticktext=[_strip_zero_decimal(fmt_wages(v)) for v in wage_ticks],
        title=dict(text="Wages Exposed", font=dict(size=LABEL_FS - 4)),
        row=1, col=5,
    )
    fig.update_xaxes(
        range=[0, 100], dtick=25,
        ticksuffix="%", tickfont=dict(size=TICK_FS - 4, family=FONT_FAMILY),
        title=dict(text="% of major's occs", font=dict(size=LABEL_FS - 4)),
        row=1, col=6,
    )

    fig.update_yaxes(showgrid=False, showline=False)
    fig.update_yaxes(
        title=dict(text="Major Occupational Category", font=dict(size=LABEL_FS - 2)),
        tickfont=dict(size=TICK_FS - 2, family=FONT_FAMILY),
        row=1, col=1,
    )

    panel_titles = {
        "Variant A: Non-Phys Task Share",
        "Variant B: % Tasks Exposed in Non-Phys Work",
        "% Tasks Exposed (All Confirmed)",
        "Workers Exposed (All Confirmed)",
        "Wages Exposed (All Confirmed)",
        "Phys Mix (Occs)",
    }
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in panel_titles:
            ann.font = dict(size=LABEL_FS - 2, family=FONT_FAMILY,
                            color=PAPER_PALETTE["text"])

    fig.update_layout(
        bargap=0.3,
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.06, xanchor="center", x=0.5,
            font=dict(size=LEGEND_FS - 2, family=FONT_FAMILY),
            bgcolor="rgba(255,255,255,0.9)",
        ),
    )

    save_figure(fig, results / "figures" / "major_categories.png", scale=2)
    _copy_fig(results, figures, "major_categories.png")
    print("  -> major_categories.png")


# ─────────────────────────────────────────────────────────────────────────
# Chart: Major-cat 2-year linear trend projection (per-panel top 10 movers)
# ─────────────────────────────────────────────────────────────────────────

PROJECTION_DAYS = 730  # 2 years


def _major_trend_series() -> pd.DataFrame:
    """Stack the all_confirmed series at major level into long form.

    Columns: date, category, pct_tasks_affected, workers_affected, wages_affected.
    Uses ANALYSIS_CONFIG_SERIES['all_confirmed'] (which excludes the 2024
    dates per the trend-series invariant)."""
    series = ANALYSIS_CONFIG_SERIES["all_confirmed"]
    rows = []
    for ds in series:
        date_str = ds.rsplit(" ", 1)[-1]
        df = _run_config(ds, "major")
        for _, r in df.iterrows():
            rows.append({
                "date": pd.Timestamp(date_str),
                "category": r["category"],
                "pct_tasks_affected": float(r["pct_tasks_affected"]),
                "workers_affected":   float(r["workers_affected"]),
                "wages_affected":     float(r["wages_affected"]),
            })
        print(f"  loaded {ds}: {len(df)} majors")
    return pd.DataFrame(rows)


def build_major_categories_trend(results: Path, figures: Path) -> None:
    """Per-panel top-10 movers chart: bars show current (final-snapshot)
    value with a lighter projected-delta segment extending the bar to its
    2-year linear projection. Ranked within each panel by the absolute
    delta from the first to the final observed snapshot."""
    trend = _major_trend_series()
    save_csv(trend, results / "major_trend_data.csv")

    metrics = [
        ("pct_tasks_affected", "% Tasks Exposed", "tasks",  lambda v: f"{v:.1f}%"),
        ("workers_affected",   "Workers Exposed", "workers", fmt_workers),
        ("wages_affected",     "Wages Exposed",   "wages",   fmt_wages),
    ]

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=[m[1] for m in metrics],
        horizontal_spacing=0.28,
    )

    summary_rows = []

    for col_idx, (metric, panel_title, metric_key, fmt_fn) in enumerate(metrics, start=1):
        per_major: list[dict] = []
        for cat, sub in trend.groupby("category"):
            sub = sub.sort_values("date")
            dates = list(sub["date"])
            yvals = list(sub[metric])
            if len(dates) < 2 or yvals[-1] == 0 and yvals[0] == 0:
                continue
            slope_per_day, projected, r2 = _linear_project(dates, yvals, PROJECTION_DAYS)
            per_major.append({
                "category":  cat,
                "current":   yvals[-1],
                "first":     yvals[0],
                "jump":      yvals[-1] - yvals[0],
                "projected": projected,
                "delta_proj": projected - yvals[-1],
                "r2":        r2,
            })
            summary_rows.append({
                "metric": metric, "category": cat,
                "first": yvals[0], "current": yvals[-1],
                "jump_observed": yvals[-1] - yvals[0],
                "projected_2yr": projected,
                "delta_projected_2yr": projected - yvals[-1],
                "r2": r2,
            })

        per_df = pd.DataFrame(per_major)
        per_df = per_df.iloc[per_df["jump"].abs().argsort()[::-1]].head(10)
        # Sort ascending for plotly (largest at top)
        per_df = per_df.sort_values("jump", ascending=True)

        cats   = per_df["category"].tolist()
        curr   = per_df["current"].tolist()
        proj_d = per_df["delta_proj"].tolist()
        jumps  = per_df["jump"].tolist()
        proj_v = per_df["projected"].tolist()
        r2s    = per_df["r2"].tolist()

        # Two stacked traces: current value (solid) + projected delta (faint).
        # Negative projected deltas plot as negative offsets so the bar shrinks
        # toward 0; honest visual encoding either way.
        fig.add_trace(go.Bar(
            y=cats, x=curr, orientation="h",
            marker=dict(color=METRIC_COLORS[metric_key], line=dict(width=0)),
            name="Current (Feb 2026)",
            showlegend=(col_idx == 1),
            hovertemplate="Current: %{x}<extra></extra>",
        ), row=1, col=col_idx)

        fig.add_trace(go.Bar(
            y=cats, x=proj_d, orientation="h",
            marker=dict(
                color=METRIC_COLORS[metric_key],
                opacity=0.35,
                line=dict(width=0),
                pattern=dict(shape="/", solidity=0.25, fgcolor="white"),
            ),
            name="2-yr linear projection",
            showlegend=(col_idx == 1),
            hovertemplate="Projected delta: %{x}<extra></extra>",
        ), row=1, col=col_idx)

        # Right-side annotations: "→ 2yr {value} ({+delta})". Short form;
        # observed delta is implicit in the bar length itself.
        x_ref = "x" if col_idx == 1 else f"x{col_idx}"
        y_ref = "y" if col_idx == 1 else f"y{col_idx}"
        max_x = float(max(c + max(0.0, d) for c, d in zip(curr, proj_d)) or 1.0)
        for cat, c_v, j_v, p_v in zip(cats, curr, jumps, proj_v):
            proj_sign = "+" if p_v - c_v >= 0 else ""
            text = f"  2yr {fmt_fn(p_v)} ({proj_sign}{fmt_fn(p_v - c_v)})"
            fig.add_annotation(
                x=c_v + max(0.0, p_v - c_v), y=cat,
                xref=x_ref, yref=y_ref,
                text=text,
                showarrow=False,
                xanchor="left", yanchor="middle",
                font=dict(size=ANNOT_FS - 2, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
            )

        fig.update_xaxes(
            range=[0, max_x * 1.40],
            showgrid=True, gridcolor=PAPER_PALETTE["grid"],
            showline=True, linecolor=PAPER_PALETTE["grid"],
            zeroline=True, zerolinecolor=PAPER_PALETTE["grid"],
            tickfont=dict(size=TICK_FS - 2, family=FONT_FAMILY),
            title=dict(text=panel_title, font=dict(size=LABEL_FS - 2)),
            row=1, col=col_idx,
        )
        if metric == "pct_tasks_affected":
            fig.update_xaxes(ticksuffix="%", row=1, col=col_idx)

        fig.update_yaxes(
            showgrid=False, showline=False,
            tickfont=dict(size=TICK_FS - 2, family=FONT_FAMILY),
            row=1, col=col_idx,
        )

    save_csv(pd.DataFrame(summary_rows), results / "major_trend_projections.csv")

    style_paper_figure(
        fig,
        "Major Occupational Category — 2-Year Linear Trend Projection",
        subtitle=(
            "Per-metric top 10 movers ranked by absolute observed change from "
            "first to final snapshot. Solid bar = current Feb 2026 value. Faint "
            "hatched segment = projected 2-year linear OLS extension. Right-side "
            "text shows the projected 2-year value with the projected delta. "
            "Linear extrapolation assumes the recent rate continues."
        ),
        height=940,
        width=PAPER_W + 1400,
        margin=dict(l=20, r=80, t=180, b=130),
    )

    fig.update_layout(
        barmode="stack",
        legend=dict(
            orientation="h",
            yanchor="bottom", y=-0.20, xanchor="center", x=0.5,
            font=dict(size=LEGEND_FS, family=FONT_FAMILY),
            bgcolor="rgba(255,255,255,0.9)",
        ),
    )

    panel_titles = {m[1] for m in metrics}
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in panel_titles:
            ann.font = dict(size=LABEL_FS - 2, family=FONT_FAMILY,
                            color=PAPER_PALETTE["text"])

    save_figure(fig, results / "figures" / "major_categories_trend.png", scale=2)
    _copy_fig(results, figures, "major_categories_trend.png")
    print("  -> major_categories_trend.png")


# ─────────────────────────────────────────────────────────────────────────
# Chart: Job zone violin restricted to non-physical occupations
# ─────────────────────────────────────────────────────────────────────────

def build_job_zone_violin_nonphys(results: Path, figures: Path) -> None:
    """Same chart as build_job_zone_violin but restricted to occupations
    with pct_physical < PHYS_LOWER. Useful for testing whether the zone
    pattern survives stripping the phys/non-phys structural cut."""
    occ = _load_occ_structural()
    pct = get_pct_tasks_affected(PRIMARY_DATASET)
    occ["pct_tasks_affected"] = occ["title_current"].map(pct)
    occ = occ.dropna(subset=["pct_tasks_affected", "job_zone"])
    occ = occ[occ["occ_group"] == "Non-physical"].copy()
    occ["job_zone"] = occ["job_zone"].astype(int)

    if occ.empty:
        print("  -> job_zone_violin_nonphys.png SKIPPED (no non-physical occs)")
        return

    zone_stats = []
    for z in sorted(occ["job_zone"].unique()):
        sub = occ[occ["job_zone"] == z]
        zone_stats.append({
            "job_zone": z,
            "n_occs": len(sub),
            "median_pct": round(float(sub["pct_tasks_affected"].median()), 1),
            "mean_pct":   round(float(sub["pct_tasks_affected"].mean()), 1),
            "q25": round(float(sub["pct_tasks_affected"].quantile(0.25)), 1),
            "q75": round(float(sub["pct_tasks_affected"].quantile(0.75)), 1),
        })
    save_csv(pd.DataFrame(zone_stats), results / "job_zone_nonphys_summary.csv")

    fig = go.Figure()
    zones = sorted(occ["job_zone"].unique())
    for z in zones:
        sub = occ[occ["job_zone"] == z]
        label = ZONE_LABELS.get(z, f"Zone {z}")
        fig.add_trace(go.Violin(
            x=sub["pct_tasks_affected"],
            name=f"{label}  (n={len(sub)})",
            marker_color=ZONE_COLORS[z],
            line_color=ZONE_COLORS[z],
            fillcolor=ZONE_COLORS[z],
            opacity=0.7,
            box_visible=True,
            meanline_visible=True,
            orientation="h",
            side="positive",
            width=0.8,
        ))

    fig.update_layout(
        yaxis=dict(
            categoryorder="array",
            categoryarray=[
                f"{ZONE_LABELS.get(z, f'Zone {z}')}  (n={int(occ[occ['job_zone'] == z].shape[0])})"
                for z in reversed(zones)
            ],
        ),
    )

    annot_text = "<br>".join(
        f"Zone {r['job_zone']}: median {r['median_pct']:.1f}%, mean {r['mean_pct']:.1f}%"
        for r in zone_stats
    )
    fig.add_annotation(
        text=annot_text,
        xref="paper", yref="paper",
        x=0.98, y=0.98,
        showarrow=False,
        font=dict(size=ANNOT_FS, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        align="right",
        xanchor="right", yanchor="top",
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor=PAPER_PALETTE["grid"],
        borderwidth=1, borderpad=6,
    )

    style_paper_figure(
        fig,
        "Task Exposure by Job Zone — Non-Physical Occupations Only",
        subtitle=(
            f"Distribution of % tasks exposed by O*NET job zone across {len(occ)} "
            "non-physical occupations (pct_physical < 33%)."
        ),
        height=600,
        width=PAPER_W,
        margin=dict(l=80, r=60, t=100, b=80),
    )
    fig.update_layout(showlegend=False)
    fig.update_xaxes(
        title=dict(text="% Tasks Exposed", font=dict(size=LABEL_FS)),
        range=[0, 100], dtick=10,
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        showline=True, linecolor=PAPER_PALETTE["grid"],
    )
    fig.update_yaxes(
        title=dict(text="Job Zone (O*NET Preparation Level)", font=dict(size=LABEL_FS - 2)),
        showgrid=False, showline=False,
        tickfont=dict(size=TICK_FS - 1, family=FONT_FAMILY),
    )

    save_figure(fig, results / "figures" / "job_zone_violin_nonphys.png")
    _copy_fig(results, figures, "job_zone_violin_nonphys.png")
    print("  -> job_zone_violin_nonphys.png")


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figures = HERE / "figures"
    figures.mkdir(exist_ok=True)

    print("=" * 60)
    print("Part 2: Characterization — Where AI Exposure Falls")
    print("=" * 60)

    print("\n[1/6] Major Occupational Categories (Variant A | B | All Confirmed)")
    build_major_categories(results, figures)

    print("\n[2/6] Major Categories — 2-Year Trend Projection")
    build_major_categories_trend(results, figures)

    print("\n[3/6] Job Zone Violin (with phys-mix overlay)")
    build_job_zone_violin(results, figures)

    print("\n[4/6] Job Zone Violin — Non-Physical Occupations Only")
    build_job_zone_violin_nonphys(results, figures)

    print("\n[5/6] Work Activities (GWA Quintet)")
    build_gwa_chart(results, figures)

    print("\n[6/6] SKA Levels (with phys-mix coloring)")
    build_ska_levels(results, figures)

    # Clear stale figures from the previous Part 2 order (box plot +
    # phys/zone combined charts). The committed appendix folder still
    # carries phys_zone_faceted, so we are not losing the cross-tab view.
    for stale in ("phys_info_divide.png", "phys_zone_stacked.png", "phys_zone_faceted.png"):
        for d in (results / "figures", figures):
            p = d / stale
            if p.exists():
                p.unlink()

    print("\n" + "=" * 60)
    print("Part 2 complete — figures in results/figures/ and figures/")
    print("=" * 60)


if __name__ == "__main__":
    main()
