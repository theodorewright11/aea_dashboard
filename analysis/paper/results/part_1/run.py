"""
Part 1 — Scale, Convergence, Growth

Three chart groups for the first section of the Results chapter:
1. Overview: Five-config aggregate economic footprint (grouped horizontal bars)
2. Convergence: Spearman rank correlation across four independent sources (2x2 heatmaps)
3. Temporal: Task penetration growth over time (line chart + delta table)

Run from project root:
    venv/Scripts/python -m analysis.paper.results.part_1.run
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.config import (
    ANALYSIS_CONFIGS,
    ANALYSIS_CONFIG_LABELS,
    ANALYSIS_CONFIG_SERIES,
    ROOT,
    ensure_results_dir,
)
from analysis.utils import (
    save_figure,
    save_csv,
    FONT_FAMILY,
    format_workers,
    format_wages,
)
from analysis.paper.paper_config import (
    PAPER_W, PAPER_H,
    TITLE_FS, SUBTITLE_FS, INSIDE_FS, OUTSIDE_FS, TICK_FS, LABEL_FS,
    LEGEND_FS, ANNOT_FS, HEATMAP_TEXT_FS,
    CONFIG_COLORS, METRIC_COLORS, HEATMAP_LOW, HEATMAP_HIGH,
    TREND_COLORS, PAPER_PALETTE, SOURCE_LINE,
    style_paper_figure,
)

HERE = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

# ── Config display order ─────────────────────────────────────────────────
CONFIG_ORDER: list[str] = [
    "all_confirmed",
    "all_ceiling",
    "human_conversation",
    "agentic_confirmed",
    "agentic_ceiling",
]

# ── Correlation sources (four independent AI measurement instruments) ────
# Using pure cumulative datasets — no cross-source contamination
CORR_SOURCES: dict[str, dict[str, str]] = {
    "claude":     {"dataset": "AEI Conv 2026-02-12",  "label": "Claude"},
    "claude_api": {"dataset": "AEI API 2026-02-12",   "label": "Claude API"},
    "copilot":    {"dataset": "Microsoft",             "label": "Copilot"},
    "mcp":        {"dataset": "MCP Cumul. v4",         "label": "MCP"},
}
CORR_ORDER: list[str] = ["claude", "claude_api", "copilot", "mcp"]
CORR_LABELS: list[str] = [CORR_SOURCES[k]["label"] for k in CORR_ORDER]

AGG_LEVELS: list[str] = ["major", "minor", "broad", "occupation"]
AGG_TITLES: dict[str, str] = {
    "major": "Major level",
    "minor": "Minor level",
    "broad": "Broad level",
    "occupation": "Occ level",
}

# ── Trend configs ────────────────────────────────────────────────────────
TREND_CONFIGS: list[str] = ["all_confirmed", "all_ceiling"]


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────

def _get_national_totals() -> tuple[float, float]:
    """Return (total_employment, total_wage_bill) from eco_2025."""
    from backend.compute import load_eco_raw

    eco = load_eco_raw()
    occ = eco.drop_duplicates(subset=["title_current"])
    emp_col = "emp_tot_nat_2024"
    wage_col = "a_med_nat_2024"
    total_emp = float(occ[emp_col].sum())
    total_wages = float((occ[emp_col] * occ[wage_col]).sum())
    return total_emp, total_wages


def _run_config(dataset_name: str, agg_level: str = "occupation") -> pd.DataFrame:
    """Run the compute pipeline for one dataset at the given agg level."""
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


def _count_tasks(dataset_name: str) -> int:
    """Count unique tasks in a dataset's raw CSV."""
    from backend.config import DATASETS

    meta = DATASETS.get(dataset_name)
    if meta is None:
        return 0
    fpath = Path(meta["file"])
    if not fpath.exists():
        return 0
    df = pd.read_csv(fpath, usecols=["task_normalized"])
    return int(df["task_normalized"].nunique())


def _copy_fig(results: Path, figures: Path, name: str) -> None:
    """Copy a figure from results/figures/ to the committed figures/ dir."""
    src = results / "figures" / name
    dst = figures / name
    shutil.copy(src, dst)


# ─────────────────────────────────────────────────────────────────────────
# Chart 1: Overview — Five-Config Aggregate Footprint
# ─────────────────────────────────────────────────────────────────────────

def build_overview(results: Path, figures: Path) -> None:
    """Grouped horizontal bars: three metrics × five configs."""
    total_emp, total_wages = _get_national_totals()

    rows: list[dict] = []
    for key in CONFIG_ORDER:
        ds = ANALYSIS_CONFIGS[key]
        label = ANALYSIS_CONFIG_LABELS[key]
        df = _run_config(ds, "occupation")

        workers = float(df["workers_affected"].sum())
        wages = float(df["wages_affected"].sum())
        pct_workers = workers / total_emp * 100
        pct_wages = wages / total_wages * 100

        rows.append({
            "config": key,
            "label": label,
            "pct_workers": round(pct_workers, 1),
            "pct_wages": round(pct_wages, 1),
            "workers": workers,
            "wages": wages,
        })
        print(f"  {label}: {format_workers(workers)} ({pct_workers:.1f}%), "
              f"{format_wages(wages)} ({pct_wages:.1f}%)")

    save_csv(pd.DataFrame(rows), results / "overview_totals.csv")

    # ── Build grouped horizontal bar chart ───────────────────────────
    fig = go.Figure()

    # Reversed so first config is at top
    plot_rows = list(reversed(rows))
    labels = [r["label"] for r in plot_rows]

    # Workers bar
    fig.add_trace(go.Bar(
        y=labels,
        x=[r["pct_workers"] for r in plot_rows],
        name="Workers Affected (% of employment)",
        orientation="h",
        marker=dict(color=METRIC_COLORS["workers"], line=dict(width=0)),
        text=[f"{format_workers(r['workers'])}  ({r['pct_workers']:.1f}%)" for r in plot_rows],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=INSIDE_FS, color="white", family=FONT_FAMILY),
    ))

    # Wages bar
    fig.add_trace(go.Bar(
        y=labels,
        x=[r["pct_wages"] for r in plot_rows],
        name="Wages Affected (% of wage bill)",
        orientation="h",
        marker=dict(color=METRIC_COLORS["wages"], line=dict(width=0)),
        text=[f"{format_wages(r['wages'])}  ({r['pct_wages']:.1f}%)" for r in plot_rows],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=INSIDE_FS, color="white", family=FONT_FAMILY),
    ))

    fig.update_layout(
        barmode="group",
        bargap=0.30,
        bargroupgap=0.05,
        xaxis=dict(
            title="% of National Total",
            range=[0, 60],
            ticksuffix="%",
            tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
        ),
        yaxis=dict(
            tickfont=dict(size=LABEL_FS, family=FONT_FAMILY),
        ),
    )

    style_paper_figure(
        fig,
        "Aggregate AI Economic Footprint — Five Configurations",
        subtitle="National | Freq | Auto-aug ON",
        margin=dict(l=20, r=60, t=90, b=90),
    )

    save_figure(fig, results / "figures" / "overview.png")
    _copy_fig(results, figures, "overview.png")
    print("  -> overview.png")


# ─────────────────────────────────────────────────────────────────────────
# Chart 2: Convergence — Spearman Rank Correlation Heatmaps
# ─────────────────────────────────────────────────────────────────────────

def build_convergence(results: Path, figures: Path) -> None:
    """2x2 heatmap grid: lower-triangle Spearman rho at four agg levels."""
    n = len(CORR_ORDER)

    # Gather pct_tasks_affected per source per agg_level
    source_data: dict[str, dict[str, pd.Series]] = {}
    for skey in CORR_ORDER:
        ds = CORR_SOURCES[skey]["dataset"]
        lbl = CORR_SOURCES[skey]["label"]
        source_data[skey] = {}
        for level in AGG_LEVELS:
            df = _run_config(ds, level)
            source_data[skey][level] = df.set_index("category")["pct_tasks_affected"]
        print(f"  {lbl}: loaded all levels")

    # Compute pairwise Spearman for each level
    corr_records: list[dict] = []
    matrices: dict[str, np.ndarray] = {}

    for level in AGG_LEVELS:
        mat = np.full((n, n), np.nan)
        for i in range(n):
            for j in range(i):  # lower triangle only
                si = source_data[CORR_ORDER[i]][level]
                sj = source_data[CORR_ORDER[j]][level]
                merged = pd.concat([si, sj], axis=1, join="inner").dropna()
                if len(merged) < 3:
                    continue
                rho, pval = stats.spearmanr(merged.iloc[:, 0], merged.iloc[:, 1])
                mat[i, j] = rho
                corr_records.append({
                    "level": level,
                    "source_a": CORR_LABELS[i],
                    "source_b": CORR_LABELS[j],
                    "rho": round(float(rho), 3),
                    "p_value": round(float(pval), 6),
                    "n": len(merged),
                })
        matrices[level] = mat

    save_csv(pd.DataFrame(corr_records), results / "spearman_by_level.csv")

    # ── Build 2×2 heatmap grid ───────────────────────────────────────
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[AGG_TITLES[l] for l in AGG_LEVELS],
        horizontal_spacing=0.14,
        vertical_spacing=0.14,
    )

    for idx, level in enumerate(AGG_LEVELS):
        row = idx // 2 + 1
        col = idx % 2 + 1
        mat = matrices[level]

        # Build text annotations — show values in lower triangle only
        text_mat: list[list[str]] = []
        for i in range(n):
            row_text: list[str] = []
            for j in range(n):
                if np.isnan(mat[i, j]):
                    row_text.append("")
                else:
                    row_text.append(f"{mat[i, j]:.2f}")
            text_mat.append(row_text)

        fig.add_trace(
            go.Heatmap(
                z=mat.tolist(),
                x=CORR_LABELS,
                y=CORR_LABELS,
                text=text_mat,
                texttemplate="%{text}",
                textfont=dict(size=HEATMAP_TEXT_FS, family=FONT_FAMILY),
                colorscale=[[0, HEATMAP_LOW], [1, HEATMAP_HIGH]],
                zmin=0.4,
                zmax=1.0,
                showscale=(idx == 3),
                colorbar=dict(
                    title=dict(text="Spearman ρ", font=dict(size=LABEL_FS)),
                    len=0.45,
                    y=0.22,
                    tickfont=dict(size=TICK_FS),
                ),
            ),
            row=row, col=col,
        )

    style_paper_figure(
        fig,
        "Source Agreement Degrades at Finer Granularity",
        subtitle="Spearman ρ on pct_tasks_affected | Four independent sources",
        width=PAPER_W,
        height=PAPER_H + 80,
        margin=dict(l=20, r=120, t=100, b=60),
    )

    # Style subplot titles
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in AGG_TITLES.values():
            ann.font = dict(
                size=LABEL_FS + 2, family=FONT_FAMILY,
                color=PAPER_PALETTE["text"],
            )

    save_figure(fig, results / "figures" / "convergence.png")
    _copy_fig(results, figures, "convergence.png")
    print("  -> convergence.png")


# ─────────────────────────────────────────────────────────────────────────
# Chart 3: Temporal — Growth Trends
# ─────────────────────────────────────────────────────────────────────────

def build_temporal(results: Path, figures: Path) -> None:
    """Line chart of % tasks affected over time + delta table."""
    total_emp, total_wages = _get_national_totals()

    trend_rows: list[dict] = []
    for config_key in TREND_CONFIGS:
        series = ANALYSIS_CONFIG_SERIES[config_key]
        label = ANALYSIS_CONFIG_LABELS[config_key]
        for ds_name in series:
            date_str = ds_name.rsplit(" ", 1)[-1]
            df = _run_config(ds_name, "occupation")

            workers = float(df["workers_affected"].sum())
            wages = float(df["wages_affected"].sum())
            pct = workers / total_emp * 100
            n_tasks = _count_tasks(ds_name)

            trend_rows.append({
                "config": config_key,
                "label": label,
                "date": date_str,
                "dataset": ds_name,
                "pct_of_employment": round(pct, 1),
                "workers_affected": round(workers),
                "wages_affected": round(wages),
                "n_tasks": n_tasks,
            })
            print(f"  {label} {date_str}: {pct:.1f}%, {format_workers(workers)}, "
                  f"{n_tasks} tasks")

    trend_df = pd.DataFrame(trend_rows)

    # Compute deltas between consecutive dates within each config
    for config_key in TREND_CONFIGS:
        mask = trend_df["config"] == config_key
        subset = trend_df.loc[mask].sort_values("date")
        idx = subset.index
        trend_df.loc[idx, "delta_pct"] = subset["pct_of_employment"].diff()
        trend_df.loc[idx, "delta_workers"] = subset["workers_affected"].diff()
        trend_df.loc[idx, "delta_wages"] = subset["wages_affected"].diff()
        trend_df.loc[idx, "delta_tasks"] = subset["n_tasks"].diff()

    save_csv(trend_df, results / "trend_data.csv")

    # ── Line chart: % of employment over time ────────────────────────
    fig = go.Figure()

    for config_key in TREND_CONFIGS:
        subset = trend_df[trend_df["config"] == config_key].sort_values("date")
        label = ANALYSIS_CONFIG_LABELS[config_key]
        color = TREND_COLORS[config_key]

        fig.add_trace(go.Scatter(
            x=subset["date"],
            y=subset["pct_of_employment"],
            name=label,
            mode="lines+markers+text",
            line=dict(color=color, width=3),
            marker=dict(size=10, color=color),
            text=[f"{v:.1f}%" for v in subset["pct_of_employment"]],
            textposition="top center",
            textfont=dict(size=OUTSIDE_FS, color=color, family=FONT_FAMILY),
        ))

    fig.update_layout(
        yaxis=dict(
            title="% of Employment with AI-Exposed Tasks",
            ticksuffix="%",
            range=[0, 60],
        ),
        xaxis=dict(title=""),
    )

    style_paper_figure(
        fig,
        "AI Task Exposure Is Growing — Confirmed Usage Tracks Toward Ceiling",
        subtitle="National | Freq | Auto-aug ON",
        margin=dict(l=60, r=40, t=90, b=90),
    )

    save_figure(fig, results / "figures" / "temporal_trend.png")
    _copy_fig(results, figures, "temporal_trend.png")
    print("  -> temporal_trend.png")

    # ── Delta table as PNG ───────────────────────────────────────────
    delta_rows = trend_df[trend_df["delta_pct"].notna()].copy()
    delta_rows = delta_rows.sort_values(["config", "date"])

    table_data: list[dict] = []
    for _, r in delta_rows.iterrows():
        dt = int(r["delta_tasks"])
        dw = r["delta_workers"]
        dwg = r["delta_wages"]
        dp = r["delta_pct"]
        table_data.append({
            "Config": r["label"],
            "Date": r["date"],
            "New Tasks": f"+{dt:,}" if dt > 0 else f"{dt:,}",
            "Delta Workers": ("+" if dw > 0 else "") + format_workers(dw),
            "Delta Wages": ("+" if dwg > 0 else "") + format_wages(dwg),
            "Delta % Emp": f"+{dp:.1f}pp" if dp > 0 else f"{dp:.1f}pp",
        })

    delta_table = pd.DataFrame(table_data)
    save_csv(delta_table, results / "trend_deltas.csv")

    # Render table as Plotly figure
    fig_table = go.Figure(data=[go.Table(
        header=dict(
            values=list(delta_table.columns),
            font=dict(size=LABEL_FS, family=FONT_FAMILY, color="white"),
            fill_color=PAPER_PALETTE["all_confirmed"],
            align="center",
            height=36,
        ),
        cells=dict(
            values=[delta_table[col] for col in delta_table.columns],
            font=dict(size=TICK_FS + 1, family=FONT_FAMILY),
            fill_color=PAPER_PALETTE["surface"],
            align="center",
            height=32,
        ),
    )])

    tbl_height = max(350, len(delta_table) * 36 + 160)
    style_paper_figure(
        fig_table,
        "Growth Per Dataset Update",
        subtitle="Change from previous date | National | Freq | Auto-aug ON",
        height=tbl_height,
        margin=dict(l=20, r=20, t=80, b=40),
    )

    save_figure(fig_table, results / "figures" / "temporal_deltas.png")
    _copy_fig(results, figures, "temporal_deltas.png")
    print("  -> temporal_deltas.png")


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figures = HERE / "figures"
    figures.mkdir(exist_ok=True)

    print("=" * 60)
    print("Part 1: Scale, Convergence, Growth")
    print("=" * 60)

    print("\n[1/3] Overview: Five-config aggregate footprint")
    build_overview(results, figures)

    print("\n[2/3] Convergence: Source correlation heatmaps")
    build_convergence(results, figures)

    print("\n[3/3] Temporal: Growth trends")
    build_temporal(results, figures)

    print("\n" + "=" * 60)
    print("Part 1 complete — figures in results/figures/ and figures/")
    print("=" * 60)


if __name__ == "__main__":
    main()
