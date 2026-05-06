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

# Physical/informational thresholds (matches exploratory)
PHYS_LOWER = 33.0
PHYS_UPPER = 67.0
OCC_GROUPS = ["Non-physical", "Mixed", "Physical"]
GROUP_COLORS = {
    "Non-physical": METRIC_COLORS["tasks"],    # Slate blue
    "Mixed":        METRIC_COLORS["workers"],   # Sage teal
    "Physical":     METRIC_COLORS["wages"],     # Warm tan
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


def _run_config(dataset_name: str, agg_level: str = "occupation") -> pd.DataFrame:
    from backend.compute import get_group_data
    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": "nat",
        "agg_level": agg_level,
        "sort_by": "% Tasks Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    assert data is not None, f"No data for {dataset_name}"
    df: pd.DataFrame = data["df"]
    group_col: str = data["group_col"]
    df = df.rename(columns={group_col: "category"})
    return df


def _get_national_totals() -> tuple[float, float]:
    from backend.compute import load_eco_raw
    eco = load_eco_raw()
    occ = eco.drop_duplicates(subset=["title_current"])
    total_emp = float(occ["emp_tot_nat_2024"].sum())
    total_wages = float((occ["emp_tot_nat_2024"] * occ["a_med_nat_2024"]).sum())
    return total_emp, total_wages


def _load_occ_structural() -> pd.DataFrame:
    """Load eco_2025 and compute per-occupation structural data:
    pct_physical, occ_group, job_zone.
    """
    eco = pd.read_csv(DATA_DIR / "final_eco_2025.csv")
    assert "title_current" in eco.columns
    assert "physical" in eco.columns
    assert "job_zone" in eco.columns

    occ = (
        eco.groupby("title_current")
        .agg(
            n_tasks=("physical", "count"),
            n_physical=("physical", "sum"),
            job_zone=("job_zone", "first"),
            emp=("emp_tot_nat_2024", "first"),
            wage=("a_med_nat_2024", "first"),
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
        title=dict(text="Occupation group", font=dict(size=LABEL_FS - 2)),
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

    # Summary stats
    zone_stats = []
    for z in sorted(occ["job_zone"].unique()):
        sub = occ[occ["job_zone"] == z]
        zone_stats.append({
            "job_zone": z,
            "n_occs": len(sub),
            "median_pct": round(float(sub["pct_tasks_affected"].median()), 1),
            "mean_pct": round(float(sub["pct_tasks_affected"].mean()), 1),
            "q25": round(float(sub["pct_tasks_affected"].quantile(0.25)), 1),
            "q75": round(float(sub["pct_tasks_affected"].quantile(0.75)), 1),
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

    fig = go.Figure()

    zones = sorted(occ["job_zone"].unique())
    for z in zones:
        sub = occ[occ["job_zone"] == z]
        n = len(sub)
        med = sub["pct_tasks_affected"].median()
        mean = sub["pct_tasks_affected"].mean()
        label = ZONE_LABELS.get(z, f"Zone {z}")

        fig.add_trace(go.Violin(
            x=sub["pct_tasks_affected"],
            name=f"{label}  (n={n})",
            marker_color=zone_colors[z],
            line_color=zone_colors[z],
            fillcolor=zone_colors[z],
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

    # Add annotation with stats
    annot_lines = []
    for row in zone_stats:
        z = row["job_zone"]
        annot_lines.append(
            f"Zone {z}: median {row['median_pct']:.1f}%, "
            f"mean {row['mean_pct']:.1f}%"
        )
    annot_text = "<br>".join(annot_lines)

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
        borderwidth=1,
        borderpad=6,
    )

    style_paper_figure(
        fig,
        "Task Exposure by Job Zone",
        subtitle=f"Distribution of % tasks exposed by O*NET job zone across {len(occ)} occupations",
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
        title=dict(text="Job zone (O*NET preparation level)", font=dict(size=LABEL_FS - 2)),
        showgrid=False, showline=False,
        tickfont=dict(size=TICK_FS - 1, family=FONT_FAMILY),
    )

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
) -> pd.DataFrame:
    """Compute AI and workforce imp×lv variants per element for one SKA type."""
    df = onet_df.copy()
    df["pct"] = df["title"].map(pct_series)
    df = df.dropna(subset=["pct", "importance", "level"])
    df = df[df["importance"] >= IMPORTANCE_THRESHOLD].copy()
    assert len(df) > 0, f"No {type_name} rows after importance filter"

    df["occ_score"] = df["importance"] * df["level"]
    df["ai_product"] = (df["pct"] / 100.0) * df["occ_score"]

    records = []
    for element_name, grp in df.groupby("element_name"):
        ai_vals = grp["ai_product"].dropna()
        occ_vals = grp["occ_score"].dropna()
        n_ai = len(ai_vals)
        n_occ = len(occ_vals)
        top_n_ai = min(TOP_N_FOR_AVERAGE, n_ai)
        top_n_occ = min(TOP_N_FOR_AVERAGE, n_occ)

        records.append({
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
        })

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

    elem_rows = []
    for (eid, ename), grp in pivoted.groupby(["element_id", "element_name"]):
        ai_vals = grp["ai_product"]
        occ_vals = grp["occ_score"]
        n = len(ai_vals)
        top_n = min(TOP_N_FOR_AVERAGE, n)
        elem_rows.append({
            "element_id": eid,
            "element_name": ename,
            "subcategory": cat_fn(eid),
            "ai_top10": float(ai_vals.nlargest(top_n).mean()),
            "ai_p95": float(ai_vals.quantile(0.95)) if n >= 2 else float(ai_vals.iloc[0]),
            "ai_max": float(ai_vals.max()),
            "eco_max": float(occ_vals.max()),
            "eco_mean": float(occ_vals.mean()),
        })
    elem_df = pd.DataFrame(elem_rows)
    for col in ["ai_top10", "ai_p95", "ai_max", "eco_mean"]:
        elem_df[f"{col}_pct"] = elem_df[col] / elem_df["eco_max"] * 100.0

    cat_rows = []
    for sub, grp in elem_df.groupby("subcategory"):
        cat_rows.append({
            "subcategory": sub,
            "n_elements": len(grp),
            "ai_top10_pct": float(grp["ai_top10_pct"].mean()),
            "ai_p95_pct":   float(grp["ai_p95_pct"].mean()),
            "ai_max_pct":   float(grp["ai_max_pct"].mean()),
            "eco_mean_pct": float(grp["eco_mean_pct"].mean()),
        })
    return (
        pd.DataFrame(cat_rows)
        .sort_values("ai_top10_pct", ascending=False)
        .reset_index(drop=True)
    )


def _build_ska_skills_chart(
    elements_df: pd.DataFrame, results: Path, figures: Path
) -> None:
    """Skills only — element-level. Bar = AI Top-10 mean (rerank by
    top10/eco_max). Red diamond = AI Max, red circle = AI P95. Black
    dot = workforce mean."""
    df = elements_df.copy()
    df["sort_pct"] = df["ai_top10"] / df["eco_max"].replace(0, float("nan")) * 100
    df = df.sort_values("sort_pct", ascending=False).reset_index(drop=True)

    enames = df["element_name"].tolist()
    bar_vals = df["ai_top10"].fillna(0).tolist()
    p95_vals = df["ai_95th"].fillna(0).tolist()
    max_vals = df["ai_max"].fillna(0).tolist()
    emax_vals = df["eco_max"].fillna(0).tolist()
    emean_vals = df["eco_mean"].fillna(0).tolist()

    max_eco = max(emax_vals) if emax_vals else 1.0
    label_x = max_eco * 1.07
    x_range_max = max_eco * 1.20

    pct_labels = [
        f"{a / m * 100:.0f}%" if m > 0 else "-"
        for a, m in zip(bar_vals, emax_vals)
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=enames, x=emax_vals, orientation="h",
        name="Workforce Max",
        marker=dict(color="#e8e8e2", line=dict(width=0)),
        hovertemplate="Workforce max: %{x:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=enames, x=bar_vals, orientation="h",
        name="AI Top-10 Avg",
        marker=dict(color=METRIC_COLORS["tasks"], opacity=0.88, line=dict(width=0)),
        hovertemplate="AI Top-10 avg: %{x:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        y=enames, x=p95_vals, mode="markers",
        name="AI P95",
        marker=dict(color=AI_MARKER_COLOR, symbol="circle", size=11,
                    line=dict(width=2, color="white")),
        hovertemplate="AI P95: %{x:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        y=enames, x=max_vals, mode="markers",
        name="AI Max",
        marker=dict(color=AI_MARKER_COLOR, symbol="diamond", size=12,
                    line=dict(width=2, color="white")),
        hovertemplate="AI Max: %{x:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        y=enames, x=emean_vals, mode="markers",
        name="Workforce Mean",
        marker=dict(color="#1a1a1a", symbol="circle", size=8,
                    line=dict(width=1, color="#1a1a1a")),
        hovertemplate="Workforce mean: %{x:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        y=enames, x=[label_x] * len(enames), mode="text",
        text=pct_labels, textposition="middle right",
        textfont=dict(size=12, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showlegend=False, hoverinfo="skip",
    ))

    fig_height = max(1100, len(enames) * 28 + 280)
    fig.update_layout(
        title=dict(
            text=(
                "AI Capability vs. Workforce Requirements — O*NET Skills"
                f"<br><span style='font-size:{SUBTITLE_FS}px;"
                f"color:{PAPER_PALETTE['muted']}'>"
                "Bar = AI Top-10 average · Red diamond = AI Max · Red circle = AI P95 · Black dot = workforce mean"
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
            yanchor="top", y=-0.03, xanchor="center", x=0.5,
            font=dict(size=LEGEND_FS, color=PAPER_PALETTE["neutral"]),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
        ),
        margin=dict(l=290, r=90, t=120, b=120),
    )
    fig.update_yaxes(
        title=dict(text="O*NET Skill", font=dict(size=LABEL_FS - 2)),
        autorange="reversed",
        tickfont=dict(size=13, color=PAPER_PALETTE["text"], family=FONT_FAMILY),
        showgrid=False, showline=False,
    )
    fig.update_xaxes(
        title=dict(
            text="Importance (1–5) × Level of expertise needed (1–7)",
            font=dict(size=LABEL_FS - 2),
        ),
        range=[0, x_range_max],
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        showticklabels=False,
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
        vertical_spacing=0.04,
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

        fig.add_trace(go.Bar(
            y=sub_labels, x=df["ai_top10_pct"], orientation="h",
            name="AI Top-10 Avg",
            marker=dict(color=METRIC_COLORS["tasks"], opacity=0.88, line=dict(width=0)),
            showlegend=_show("ai_top10"),
            text=[f"{v:.0f}%" for v in df["ai_top10_pct"]],
            textposition="outside",
            textfont=dict(size=12, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
            hovertemplate="AI Top-10 avg (% of max): %{x:.1f}%<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scatter(
            y=sub_labels, x=df["ai_p95_pct"], mode="markers",
            name="AI P95",
            marker=dict(color=AI_MARKER_COLOR, symbol="circle", size=11,
                        line=dict(width=2, color="white")),
            showlegend=_show("ai_p95"),
            hovertemplate="AI P95 (% of max): %{x:.1f}%<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scatter(
            y=sub_labels, x=df["ai_max_pct"], mode="markers",
            name="AI Max",
            marker=dict(color=AI_MARKER_COLOR, symbol="diamond", size=12,
                        line=dict(width=2, color="white")),
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
            range=[0, 130], ticksuffix="%",
            showgrid=True, gridcolor=PAPER_PALETTE["grid"],
            tickfont=dict(size=12, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
            showline=False, zeroline=True, zerolinecolor=PAPER_PALETTE["grid"],
            row=row, col=1,
        )

    # Y axis titles per subplot
    fig.update_yaxes(
        title=dict(text="O*NET Knowledge category", font=dict(size=LABEL_FS - 2)),
        row=1, col=1,
    )
    fig.update_yaxes(
        title=dict(text="O*NET Ability subcategory", font=dict(size=LABEL_FS - 2)),
        row=2, col=1,
    )
    fig.update_xaxes(
        title=dict(
            text="Mean AI capability as % of workforce max (across elements in subcategory)",
            font=dict(size=LABEL_FS - 2),
        ),
        row=2, col=1,
    )

    fig_height = max(900, total * 35 + 320)

    fig.update_layout(
        title=dict(
            text=(
                "AI Capability vs. Workforce Requirements — O*NET Knowledge and Abilities"
                f"<br><span style='font-size:{SUBTITLE_FS}px;"
                f"color:{PAPER_PALETTE['muted']}'>"
                "Mean across the elements in each subcategory · "
                "Bar = AI Top-10 avg · Red diamond = AI Max · Red circle = AI P95 · Black dot = workforce mean"
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
            yanchor="top", y=-0.03, xanchor="center", x=0.5,
            font=dict(size=LEGEND_FS, color=PAPER_PALETTE["neutral"]),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
        ),
        margin=dict(l=300, r=80, t=120, b=120),
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

    # Skills — element level (per-element bars)
    skills_df = _compute_ska_variants(ska_data.skills, pct, "skills")
    print(f"    skills: {len(skills_df)} elements")

    # Knowledge — subcategory rollup (10 categories from O*NET 2.C.1–2.C.10)
    know_path = ROOT / "analysis" / "data" / "knowledge_v30.1.csv"
    knowledge_cat = _compute_subcategory_rollup(know_path, pct, _knowledge_cat)
    n_know_elements = _count_elements(know_path, pct)
    print(f"    knowledge (subcategory): {len(knowledge_cat)} subcategories "
          f"({n_know_elements} elements)")

    # Abilities — subcategory rollup (15 subcategories under 1.A.1–1.A.4)
    abil_path = ROOT / "analysis" / "data" / "abilities_v30.1.csv"
    abilities_cat = _compute_subcategory_rollup(abil_path, pct, _ability_subcat)
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
    gwa_df = _get_wa_data(PRIMARY_DATASET, "gwa")
    assert not gwa_df.empty, "No GWA data returned"

    gwa_df = gwa_df.sort_values("pct_tasks_affected", ascending=True)
    save_csv(gwa_df, results / "gwa_exposure.csv")

    n_gwas = len(gwa_df)
    categories = gwa_df["category"].tolist()
    pct_vals = gwa_df["pct_tasks_affected"].tolist()
    workers_vals = gwa_df["workers_affected"].tolist()
    wages_vals = gwa_df["wages_affected"].tolist()

    annotations = [
        f"{fmt_workers(w)} workers | {fmt_wages(wg)} wages"
        for w, wg in zip(workers_vals, wages_vals)
    ]

    fig = go.Figure()

    # Single bar trace; color encodes workers via heatmap-style colorscale
    # so we can surface a vertical color bar legend on the side.
    fig.add_trace(go.Bar(
        y=categories,
        x=pct_vals,
        orientation="h",
        marker=dict(
            color=workers_vals,
            colorscale=[[0, "#b8cfe0"], [1, "#1a4f73"]],
            showscale=True,
            colorbar=dict(
                title=dict(text="Workers<br>in scope", side="top",
                           font=dict(size=ANNOT_FS, family=FONT_FAMILY)),
                tickfont=dict(size=ANNOT_FS - 1, family=FONT_FAMILY),
                tickvals=[min(workers_vals), max(workers_vals)],
                ticktext=[fmt_workers(min(workers_vals)),
                          fmt_workers(max(workers_vals))],
                len=0.55, thickness=14,
                x=1.005, xanchor="left",
            ),
            line=dict(width=0),
        ),
        text=[f"{v:.1f}%" for v in pct_vals],
        textposition="inside",
        insidetextanchor="end",
        textfont=dict(size=INSIDE_FS - 5, color="white", family=FONT_FAMILY),
        cliponaxis=False,
        showlegend=False,
        hovertemplate="%{y}<br>%{x:.1f}% tasks<extra></extra>",
    ))

    # Workers + wages annotations outside bars
    fig.add_trace(go.Scatter(
        y=categories,
        x=[v + 1.5 for v in pct_vals],
        mode="text",
        text=annotations,
        textposition="middle right",
        textfont=dict(size=ANNOT_FS, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showlegend=False,
        hoverinfo="skip",
    ))

    height = max(PAPER_H + 250, n_gwas * 28 + 280)

    style_paper_figure(
        fig,
        "Task Exposure Across All O*NET General Work Activities",
        subtitle=f"% tasks exposed per GWA across {n_gwas} activities — bar color = workers in scope",
        height=height,
        width=PAPER_W + 100,
        margin=dict(l=20, r=420, t=140, b=80),
    )

    fig.update_xaxes(
        title=dict(text="% Tasks Exposed", font=dict(size=LABEL_FS)),
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        showline=True, linecolor=PAPER_PALETTE["grid"],
        ticksuffix="%",
    )
    fig.update_yaxes(
        title=dict(text="O*NET General Work Activity", font=dict(size=LABEL_FS - 2)),
        showgrid=False, showline=False,
        tickfont=dict(size=TICK_FS - 2, family=FONT_FAMILY),
    )

    save_figure(fig, results / "figures" / "gwa_exposure.png", scale=2)
    _copy_fig(results, figures, "gwa_exposure.png")
    print("  -> gwa_exposure.png")


# ─────────────────────────────────────────────────────────────────────────
# Chart 5: All 22 Major Categories — 3 Side-by-Side Panels
# ─────────────────────────────────────────────────────────────────────────

def build_major_categories(results: Path, figures: Path) -> None:
    df = _run_config(PRIMARY_DATASET, "major")
    assert not df.empty, "No major category data"

    # Sort by pct_tasks_affected descending for consistent ordering
    df = df.sort_values("pct_tasks_affected", ascending=False).reset_index(drop=True)
    save_csv(df, results / "major_categories.csv")

    categories = df["category"].tolist()
    pct_vals = df["pct_tasks_affected"].tolist()
    workers_vals = df["workers_affected"].tolist()
    wages_vals = df["wages_affected"].tolist()

    # Reverse for Plotly (top = first) — we want highest at top
    categories_r = list(reversed(categories))
    pct_r = list(reversed(pct_vals))
    workers_r = list(reversed(workers_vals))
    wages_r = list(reversed(wages_vals))

    n_cats = len(categories)

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=["% Tasks Exposed", "Workers In Scope", "Wages In Scope"],
        horizontal_spacing=0.12,
        shared_yaxes=True,
    )

    # Panel 1: % Tasks Affected
    fig.add_trace(go.Bar(
        y=categories_r, x=pct_r, orientation="h",
        name="% Tasks Affected",
        marker=dict(color=METRIC_COLORS["tasks"], line=dict(width=0)),
        text=[f"{v:.1f}%" for v in pct_r],
        textposition="outside",
        textfont=dict(size=ANNOT_FS, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showlegend=False,
        cliponaxis=False,
    ), row=1, col=1)

    # Panel 2: Workers Affected
    fig.add_trace(go.Bar(
        y=categories_r, x=workers_r, orientation="h",
        name="Workers Affected",
        marker=dict(color=METRIC_COLORS["workers"], line=dict(width=0)),
        text=[fmt_workers(v) for v in workers_r],
        textposition="outside",
        textfont=dict(size=ANNOT_FS, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showlegend=False,
        cliponaxis=False,
    ), row=1, col=2)

    # Panel 3: Wages Affected
    fig.add_trace(go.Bar(
        y=categories_r, x=wages_r, orientation="h",
        name="Wages Affected",
        marker=dict(color=METRIC_COLORS["wages"], line=dict(width=0)),
        text=[fmt_wages(v) for v in wages_r],
        textposition="outside",
        textfont=dict(size=ANNOT_FS, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showlegend=False,
        cliponaxis=False,
    ), row=1, col=3)

    height = max(PAPER_H + 200, n_cats * 32 + 200)

    style_paper_figure(
        fig,
        "AI Exposure by Major Occupational Category",
        height=height,
        width=PAPER_W + 200,
        margin=dict(l=20, r=100, t=90, b=50),
    )

    fig.update_xaxes(showgrid=False, showticklabels=False, showline=False, zeroline=False)
    fig.update_yaxes(showgrid=False, showline=False)

    # Y-axis title only on first panel
    fig.update_yaxes(
        title=dict(text="Major occupational category", font=dict(size=LABEL_FS - 2)),
        tickfont=dict(size=TICK_FS - 2, family=FONT_FAMILY),
        row=1, col=1,
    )

    panel_titles = {"% Tasks Exposed", "Workers In Scope", "Wages In Scope"}
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in panel_titles:
            ann.font = dict(size=LABEL_FS, family=FONT_FAMILY, color=PAPER_PALETTE["text"])

    fig.update_layout(bargap=0.3)

    save_figure(fig, results / "figures" / "major_categories.png", scale=2)
    _copy_fig(results, figures, "major_categories.png")
    print("  -> major_categories.png")


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

    print("\n[1/5] Physical / Informational Divide")
    build_phys_info_divide(results, figures)

    print("\n[2/5] Job Zone Violin")
    build_job_zone_violin(results, figures)

    print("\n[3/5] SKA Levels (AI Max)")
    build_ska_levels(results, figures)

    print("\n[4/5] Work Activities (GWA)")
    build_gwa_chart(results, figures)

    print("\n[5/5] Major Occupational Categories")
    build_major_categories(results, figures)

    print("\n[combined A] Phys/Info + Job Zone — Stacked")
    build_combined_stacked(results, figures)

    print("\n[combined B] Phys × Zone — Faceted")
    build_combined_faceted(results, figures)

    print("\n" + "=" * 60)
    print("Part 2 complete — figures in results/figures/ and figures/")
    print("=" * 60)


if __name__ == "__main__":
    main()
