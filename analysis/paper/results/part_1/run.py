"""
Part 1 — Scale, Convergence, Growth

Three chart groups for the first section of the Results chapter:
1. Overview: Five-config aggregate economic footprint (grouped horizontal bars)
2. Convergence: Spearman rank correlation across four independent sources (2x2 heatmaps)
3. Temporal: Task penetration growth over time (line chart + delta tables)

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
from analysis.utils import FONT_FAMILY, save_figure, save_csv
from analysis.paper.paper_config import (
    PAPER_W, PAPER_H,
    TITLE_FS, SUBTITLE_FS, INSIDE_FS, OUTSIDE_FS, TICK_FS, LABEL_FS,
    LEGEND_FS, ANNOT_FS, HEATMAP_TEXT_FS, TABLE_HEADER_FS, TABLE_CELL_FS,
    METRIC_COLORS, HEATMAP_LOW, HEATMAP_HIGH,
    TREND_COLORS, PAPER_PALETTE,
    style_paper_figure, fmt_wages, fmt_workers, fmt_date,
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

# ── Correlation sources ──────────────────────────────────────────────────
CORR_SOURCES: dict[str, dict[str, str]] = {
    "claude":     {"dataset": "AEI Conv 2026-02-12",  "label": "Claude Browser"},
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

TREND_CONFIGS: list[str] = ["all_confirmed", "all_ceiling"]


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────

def _get_national_totals() -> tuple[float, float]:
    from backend.compute import load_eco_raw
    eco = load_eco_raw()
    occ = eco.drop_duplicates(subset=["title_current"])
    total_emp = float(occ["emp_tot_nat_2024"].sum())
    total_wages = float((occ["emp_tot_nat_2024"] * occ["a_med_nat_2024"]).sum())
    return total_emp, total_wages


def _get_eco_task_count() -> int:
    from backend.compute import load_eco_raw
    eco = load_eco_raw()
    return int(eco["task_normalized"].nunique())


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


def _count_tasks(dataset_name: str) -> int:
    from backend.config import DATASETS
    meta = DATASETS.get(dataset_name)
    if meta is None:
        return 0
    fpath = Path(meta["file"])
    if not fpath.exists():
        return 0
    df = pd.read_csv(fpath, usecols=["task_normalized"])
    return int(df["task_normalized"].nunique())


def _avg_auto_aug(dataset_name: str) -> float:
    """Average auto_aug_mean across unique tasks that have a value."""
    from backend.config import DATASETS
    meta = DATASETS.get(dataset_name)
    if meta is None:
        return 0.0
    fpath = Path(meta["file"])
    if not fpath.exists():
        return 0.0
    df = pd.read_csv(fpath, usecols=["task_normalized", "auto_aug_mean"])
    task_avg = df.groupby("task_normalized")["auto_aug_mean"].mean()
    return float(task_avg.mean())


def _copy_fig(results: Path, figures: Path, name: str) -> None:
    shutil.copy(results / "figures" / name, figures / name)


# ─────────────────────────────────────────────────────────────────────────
# Chart 1: Overview
# ─────────────────────────────────────────────────────────────────────────

def build_overview(results: Path, figures: Path) -> None:
    total_emp, total_wages = _get_national_totals()

    rows: list[dict] = []
    for key in CONFIG_ORDER:
        ds = ANALYSIS_CONFIGS[key]
        label = ANALYSIS_CONFIG_LABELS[key]
        df = _run_config(ds, "occupation")

        workers = float(df["workers_affected"].sum())
        wages = float(df["wages_affected"].sum())
        pct_tasks = float(df["pct_tasks_affected"].mean())
        pct_workers = workers / total_emp * 100
        pct_wages = wages / total_wages * 100

        rows.append({
            "config": key, "label": label,
            "pct_tasks": round(pct_tasks, 1),
            "pct_workers": round(pct_workers, 1),
            "pct_wages": round(pct_wages, 1),
            "workers": workers, "wages": wages,
        })
        print(f"  {label}: {pct_tasks:.1f}% tasks, "
              f"{fmt_workers(workers)} ({pct_workers:.1f}%), "
              f"{fmt_wages(wages)} ({pct_wages:.1f}%)")

    save_csv(pd.DataFrame(rows), results / "overview_totals.csv")

    fig = go.Figure()
    plot_rows = list(reversed(rows))
    labels = [r["label"] for r in plot_rows]

    metrics = [
        ("pct_tasks",   "% Tasks Affected",
         METRIC_COLORS["tasks"],
         lambda r: f"{r['pct_tasks']:.1f}%"),
        ("pct_workers", "Workers in AI-Exposed Occupations (% of economy employment)",
         METRIC_COLORS["workers"],
         lambda r: f"{fmt_workers(r['workers'])}  ({r['pct_workers']:.1f}%)"),
        ("pct_wages",   "Wages in AI-Exposed Occupations (% of economy wages)",
         METRIC_COLORS["wages"],
         lambda r: f"{fmt_wages(r['wages'])}  ({r['pct_wages']:.1f}%)"),
    ]

    for pct_key, name, color, fmt_fn in metrics:
        fig.add_trace(go.Bar(
            y=labels,
            x=[r[pct_key] for r in plot_rows],
            name=name,
            orientation="h",
            marker=dict(color=color, line=dict(width=0)),
            text=[fmt_fn(r) for r in plot_rows],
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(size=INSIDE_FS, color="white", family=FONT_FAMILY),
        ))

    fig.update_layout(
        barmode="group",
        bargap=0.25,
        bargroupgap=0.06,
        xaxis=dict(
            title="% of National Total",
            range=[0, 60],
            ticksuffix="%",
        ),
        yaxis=dict(tickfont=dict(size=LABEL_FS, family=FONT_FAMILY)),
    )

    style_paper_figure(
        fig,
        "Aggregate AI Economic Footprint",
        height=PAPER_H + 40,
        margin=dict(l=20, r=60, t=70, b=90),
    )

    save_figure(fig, results / "figures" / "overview.png")
    _copy_fig(results, figures, "overview.png")
    print("  -> overview.png")


# ─────────────────────────────────────────────────────────────────────────
# Chart 2: Convergence
# ─────────────────────────────────────────────────────────────────────────

def build_convergence(results: Path, figures: Path) -> None:
    n = len(CORR_ORDER)

    source_data: dict[str, dict[str, pd.Series]] = {}
    for skey in CORR_ORDER:
        ds = CORR_SOURCES[skey]["dataset"]
        lbl = CORR_SOURCES[skey]["label"]
        source_data[skey] = {}
        for level in AGG_LEVELS:
            df = _run_config(ds, level)
            source_data[skey][level] = df.set_index("category")["pct_tasks_affected"]
        print(f"  {lbl}: loaded all levels")

    corr_records: list[dict] = []
    matrices: dict[str, np.ndarray] = {}

    for level in AGG_LEVELS:
        mat = np.full((n, n), np.nan)
        for i in range(n):
            for j in range(i):
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

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[AGG_TITLES[l] for l in AGG_LEVELS],
        horizontal_spacing=0.08,
        vertical_spacing=0.10,
    )

    for idx, level in enumerate(AGG_LEVELS):
        row = idx // 2 + 1
        col = idx % 2 + 1
        mat = matrices[level]

        fig.add_trace(
            go.Heatmap(
                z=mat.tolist(),
                x=CORR_LABELS,
                y=CORR_LABELS,
                colorscale=[[0, HEATMAP_LOW], [1, HEATMAP_HIGH]],
                zmin=0.4, zmax=1.0,
                showscale=(idx == 3),
                hoverinfo="z",
                colorbar=dict(
                    title=dict(
                        text="Spearman ρ",
                        font=dict(size=LABEL_FS, family=FONT_FAMILY),
                    ),
                    len=0.45, y=0.22,
                    tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
                ),
            ),
            row=row, col=col,
        )

        # Add cell annotations with conditional text color
        for i in range(n):
            for j in range(n):
                val = mat[i, j]
                if np.isnan(val):
                    continue
                txt_color = "white" if val >= 0.70 else PAPER_PALETTE["text_dark"]
                fig.add_annotation(
                    x=CORR_LABELS[j], y=CORR_LABELS[i],
                    text=f"{val:.2f}",
                    showarrow=False,
                    font=dict(size=HEATMAP_TEXT_FS, family=FONT_FAMILY, color=txt_color),
                    xref=f"x{idx + 1}" if idx > 0 else "x",
                    yref=f"y{idx + 1}" if idx > 0 else "y",
                )

    style_paper_figure(
        fig,
        "Spearman ρ on % Tasks Affected",
        width=PAPER_W,
        height=PAPER_H + 120,
        margin=dict(l=20, r=130, t=90, b=40),
    )

    # Style subplot titles — bigger font
    agg_title_set = set(AGG_TITLES.values())
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in agg_title_set:
            ann.font = dict(
                size=LABEL_FS + 1, family=FONT_FAMILY,
                color=PAPER_PALETTE["text"],
            )

    # Bump axis tick fonts for all subplots
    for i in range(1, 5):
        xkey = f"xaxis{i}" if i > 1 else "xaxis"
        ykey = f"yaxis{i}" if i > 1 else "yaxis"
        fig.layout[xkey].tickfont = dict(size=TICK_FS - 1, family=FONT_FAMILY)
        fig.layout[ykey].tickfont = dict(size=TICK_FS - 1, family=FONT_FAMILY)

    save_figure(fig, results / "figures" / "convergence.png")
    _copy_fig(results, figures, "convergence.png")
    print("  -> convergence.png")


# ─────────────────────────────────────────────────────────────────────────
# Chart 3: Temporal
# ─────────────────────────────────────────────────────────────────────────

def _build_trend_data() -> pd.DataFrame:
    total_emp, total_wages = _get_national_totals()
    eco_tasks = _get_eco_task_count()

    trend_rows: list[dict] = []
    for config_key in TREND_CONFIGS:
        series = ANALYSIS_CONFIG_SERIES[config_key]
        label = ANALYSIS_CONFIG_LABELS[config_key]
        for ds_name in series:
            date_str = ds_name.rsplit(" ", 1)[-1]
            df = _run_config(ds_name, "occupation")

            workers = float(df["workers_affected"].sum())
            wages = float(df["wages_affected"].sum())
            pct_emp = workers / total_emp * 100
            pct_tasks = float(df["pct_tasks_affected"].mean())  # unweighted
            n_tasks = _count_tasks(ds_name)
            auto_aug = _avg_auto_aug(ds_name)

            trend_rows.append({
                "config": config_key,
                "label": label,
                "date": date_str,
                "dataset": ds_name,
                "pct_of_employment": round(pct_emp, 1),
                "pct_tasks_affected": round(pct_tasks, 1),
                "workers": workers,
                "wages": wages,
                "n_tasks": n_tasks,
                "avg_auto_aug": round(auto_aug, 2),
                "eco_tasks": eco_tasks,
                "total_emp": total_emp,
                "total_wages": total_wages,
            })
            print(f"  {label} {date_str}: {pct_tasks:.1f}% tasks aff, "
                  f"{fmt_workers(workers)}, {n_tasks} tasks, "
                  f"auto-aug {auto_aug:.2f}")

    return pd.DataFrame(trend_rows)


def _build_one_table(
    trend_df: pd.DataFrame,
    config_key: str,
    results: Path,
    figures: Path,
) -> None:
    label = ANALYSIS_CONFIG_LABELS[config_key]
    sub = trend_df[trend_df["config"] == config_key].sort_values("date").reset_index(drop=True)
    if sub.empty:
        return

    eco_tasks = int(sub.iloc[0]["eco_tasks"])
    total_emp = sub.iloc[0]["total_emp"]
    total_wages = sub.iloc[0]["total_wages"]

    # Column arrays
    col_date: list[str] = []
    col_tasks: list[str] = []
    col_dtasks: list[str] = []
    col_workers: list[str] = []
    col_dworkers: list[str] = []
    col_wages: list[str] = []
    col_dwages: list[str] = []
    col_autoaug: list[str] = []
    col_pct: list[str] = []
    col_dpct: list[str] = []

    # Fill color arrays
    highlight = PAPER_PALETTE["row_highlight"]
    pos_fill = PAPER_PALETTE["cell_pos"]
    white = PAPER_PALETTE["surface"]
    ref_fill = PAPER_PALETTE["row_ref"]

    date_fills: list[str] = []
    delta_fills: list[str] = []

    for i, (_, r) in enumerate(sub.iterrows()):
        is_start = (i == 0)
        is_end = (i == len(sub) - 1)

        # Date
        if is_start:
            col_date.append(f"Start: {fmt_date(r['date'])}")
        elif is_end:
            col_date.append(f"End: {fmt_date(r['date'])}")
        else:
            col_date.append(fmt_date(r["date"]))

        col_tasks.append(f"{int(r['n_tasks']):,}")
        col_workers.append(fmt_workers(r["workers"]))
        col_wages.append(fmt_wages(r["wages"]))
        col_autoaug.append(f"{r['avg_auto_aug']:.2f}")
        col_pct.append(f"{r['pct_tasks_affected']:.1f}%")

        if is_start:
            col_dtasks.append("—")
            col_dworkers.append("—")
            col_dwages.append("—")
            col_dpct.append("—")
            date_fills.append(highlight)
            delta_fills.append(highlight)
        else:
            prev = sub.iloc[i - 1]

            # Delta tasks: absolute + %
            dt = int(r["n_tasks"] - prev["n_tasks"])
            dt_pct = dt / prev["n_tasks"] * 100 if prev["n_tasks"] else 0
            col_dtasks.append(
                f"{'+' if dt >= 0 else ''}{dt:,} "
                f"({'+' if dt_pct >= 0 else ''}{dt_pct:.1f}%)"
            )

            # Delta workers: absolute + %
            dw = r["workers"] - prev["workers"]
            dw_pct = dw / prev["workers"] * 100 if prev["workers"] else 0
            col_dworkers.append(
                f"{'+' if dw >= 0 else ''}{fmt_workers(dw)} "
                f"({'+' if dw_pct >= 0 else ''}{dw_pct:.1f}%)"
            )

            # Delta wages: absolute + %
            dwg = r["wages"] - prev["wages"]
            dwg_pct = dwg / prev["wages"] * 100 if prev["wages"] else 0
            col_dwages.append(
                f"{'+' if dwg >= 0 else ''}{fmt_wages(dwg)} "
                f"({'+' if dwg_pct >= 0 else ''}{dwg_pct:.1f}%)"
            )

            # Delta % tasks affected
            dp = r["pct_tasks_affected"] - prev["pct_tasks_affected"]
            col_dpct.append(f"+{dp:.1f}%" if dp >= 0 else f"{dp:.1f}%")

            if is_end:
                date_fills.append(highlight)
                delta_fills.append(highlight)
            else:
                date_fills.append(white)
                delta_fills.append(pos_fill if dw > 0 else white)

    # Reference row: economy totals
    col_date.append("Economy Total")
    col_tasks.append(f"{eco_tasks:,}")
    col_dtasks.append("—")
    col_workers.append(fmt_workers(total_emp))
    col_dworkers.append("—")
    col_wages.append(fmt_wages(total_wages))
    col_dwages.append("—")
    col_autoaug.append("—")
    col_pct.append("—")
    col_dpct.append("—")
    date_fills.append(ref_fill)
    delta_fills.append(ref_fill)

    n_rows = len(col_date)
    neutral_fills = [white] * (n_rows - 1) + [ref_fill]

    header_color = (PAPER_PALETTE["all_confirmed"]
                    if "confirmed" in config_key
                    else PAPER_PALETTE["all_ceiling"])

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=["Date", "Unique Tasks<br>Rated", "Δ Unique<br>Tasks Rated",
                    "% Tasks<br>Affected", "Δ % Tasks<br>Affected",
                    "Workers", "Δ Workers",
                    "Wages", "Δ Wages",
                    "AI Capability<br>(0–5)"],
            font=dict(size=TABLE_HEADER_FS, family=FONT_FAMILY, color="white"),
            fill_color=header_color,
            align="center",
            height=40,
        ),
        cells=dict(
            values=[col_date, col_tasks, col_dtasks,
                    col_pct, col_dpct,
                    col_workers, col_dworkers,
                    col_wages, col_dwages,
                    col_autoaug],
            font=dict(size=TABLE_CELL_FS, family=FONT_FAMILY),
            fill_color=[date_fills, neutral_fills, delta_fills,
                        neutral_fills, delta_fills,
                        neutral_fills, delta_fills,
                        neutral_fills, delta_fills,
                        neutral_fills],
            align="center",
            height=32,
        ),
    )])

    tbl_height = max(350, n_rows * 40 + 150)
    style_paper_figure(
        fig,
        label,
        height=tbl_height,
        margin=dict(l=10, r=10, t=60, b=20),
    )

    fname = f"temporal_table_{config_key}.png"
    save_figure(fig, results / "figures" / fname)
    _copy_fig(results, figures, fname)
    print(f"  -> {fname}")


def build_temporal(results: Path, figures: Path) -> None:
    trend_df = _build_trend_data()
    save_csv(trend_df, results / "trend_data.csv")

    # ── Line chart ───────────────────────────────────────────────────
    fig = go.Figure()

    for config_key in TREND_CONFIGS:
        subset = trend_df[trend_df["config"] == config_key].sort_values("date")
        label = ANALYSIS_CONFIG_LABELS[config_key]
        color = TREND_COLORS[config_key]

        # Offset last ceiling label to avoid overlap
        positions = ["top center"] * len(subset)
        if config_key == "all_ceiling" and len(subset) >= 2:
            positions[-2] = "top left"
            positions[-1] = "top right"

        fig.add_trace(go.Scatter(
            x=subset["date"],
            y=subset["pct_of_employment"],
            name=label,
            mode="lines+markers+text",
            line=dict(color=color, width=3),
            marker=dict(size=10, color=color),
            text=[f"{v:.1f}%" for v in subset["pct_of_employment"]],
            textposition=positions,
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
        "% of Employment with AI-Exposed Tasks Over Time",
        margin=dict(l=60, r=40, t=70, b=80),
    )

    save_figure(fig, results / "figures" / "temporal_trend.png")
    _copy_fig(results, figures, "temporal_trend.png")
    print("  -> temporal_trend.png")

    # ── Data tables ──────────────────────────────────────────────────
    for config_key in TREND_CONFIGS:
        _build_one_table(trend_df, config_key, results, figures)


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

    print("\n[3/3] Temporal: Growth trends + data tables")
    build_temporal(results, figures)

    print("\n" + "=" * 60)
    print("Part 1 complete — figures in results/figures/ and figures/")
    print("=" * 60)


if __name__ == "__main__":
    main()
