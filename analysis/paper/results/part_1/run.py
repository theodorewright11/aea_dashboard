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
    ANALYSIS_DIR,
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

# ── External benchmarks (for convergence_external chart) ─────────────────
# Four external occupation-level AI-exposure measures from prior academic
# work. The convergence_external chart correlates our four internal sources
# against each of these benchmarks at the same four SOC aggregation levels.
EXT_SOURCES: list[tuple[str, str]] = [
    ("gpt_beta",   "Eloundou GPT-4 β"),
    ("human_beta", "Eloundou Human β"),
    ("aioe_mean",  "AIOE mean (10 apps)"),
    ("aioe_rc",    "AIOE Reading Compr."),
]

GPTS_CSV = ANALYSIS_DIR / "data" / "gpts_are_gpts_occ_data.csv"
AIOE_MATRIX_PATH = ANALYSIS_DIR / "data" / "aioe_ability_matrix.csv"
ABILITIES_PATH = ANALYSIS_DIR / "data" / "abilities_v30.1.csv"


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


def _stars(p: float) -> str:
    """Standard significance asterisks for two-tailed correlation p-values."""
    if not np.isfinite(p):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return ""


SIG_FOOTNOTE: str = (
    "Significance: <b>*</b> p &lt; .05  &nbsp; "
    "<b>**</b> p &lt; .01  &nbsp; "
    "<b>***</b> p &lt; .001 (two-tailed Spearman)."
)


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
# Chart 2: Convergence — internal sources + external benchmarks combined
# ─────────────────────────────────────────────────────────────────────────

def _load_eloundou_occ() -> pd.DataFrame:
    """Eloundou et al. (2023) per-occupation ratings, scaled ×100 to match
    our pct_tasks_affected units. Returns title_current, gpt_beta, human_beta."""
    df = pd.read_csv(GPTS_CSV)
    assert "Title" in df.columns, f"Title column missing in {GPTS_CSV}"
    for c in ("dv_rating_beta", "human_rating_beta"):
        assert c in df.columns, f"{c} column missing in {GPTS_CSV}"
    out = pd.DataFrame({
        "title_current": df["Title"].astype(str),
        "gpt_beta":      pd.to_numeric(df["dv_rating_beta"], errors="coerce") * 100.0,
        "human_beta":    pd.to_numeric(df["human_rating_beta"], errors="coerce") * 100.0,
    })
    assert out["gpt_beta"].notna().any(), "Eloundou gpt_beta is all NaN after load"
    return out


def _compute_aioe_occ() -> pd.DataFrame:
    """Per-occupation AIOE scores computed as ratio-of-sums of imp×lv×ability_cap
    over imp≥3 ability rows (per Felten/Raj/Seamans framing). Two variants:
    mean of the 10 AI-application columns, and Reading Comprehension only.
    Values are ×100 to match pct_tasks_affected. Returns title_current,
    aioe_mean, aioe_rc."""
    matrix = pd.read_csv(AIOE_MATRIX_PATH, index_col=0)
    assert matrix.shape == (52, 10), f"AIOE matrix shape {matrix.shape} — expected (52, 10)"
    # AIOE labels this "Visual Color Determination"; O*NET v30.1 uses
    # "Visual Color Discrimination". Same element.
    matrix = matrix.rename(index={
        "Visual Color Determination": "Visual Color Discrimination",
    })
    per_ability = pd.DataFrame({
        "ability_name": matrix.index,
        "aioe_mean":    matrix.mean(axis=1).values,
        "aioe_rc":      matrix["Reading Comprehension"].values,
    })

    abilities = pd.read_csv(ABILITIES_PATH, dtype=str)
    abilities = abilities.rename(columns={
        "O*NET-SOC Code": "soc_code",
        "Title":          "title_current",
        "Element Name":   "ability_name",
        "Scale ID":       "scale_id",
        "Data Value":     "data_value",
    })
    abilities["data_value"] = pd.to_numeric(abilities["data_value"], errors="coerce")
    abilities = abilities[abilities["scale_id"].isin(["IM", "LV"])]
    pivoted = (
        abilities.pivot_table(
            index=["title_current", "ability_name"],
            columns="scale_id", values="data_value", aggfunc="mean",
        )
        .reset_index()
    )
    pivoted.columns.name = None
    pivoted = pivoted.rename(columns={"IM": "importance", "LV": "level"})
    pivoted = pivoted.dropna(subset=["importance", "level"])

    joined = pivoted.merge(per_ability, on="ability_name", how="inner")
    # imp ≥ 3 filter is applied per (occ, ability) row
    filt = joined[joined["importance"] >= 3].copy()
    assert not filt.empty, "AIOE: no rows after imp>=3 filter"
    filt["weight"] = filt["importance"] * filt["level"]

    grouped = filt.groupby("title_current")
    rows: list[dict] = []
    for title, g in grouped:
        w_sum = float(g["weight"].sum())
        if w_sum == 0:
            continue
        rows.append({
            "title_current": title,
            "aioe_mean": float((g["weight"] * g["aioe_mean"]).sum() / w_sum) * 100.0,
            "aioe_rc":   float((g["weight"] * g["aioe_rc"]).sum()   / w_sum) * 100.0,
        })
    out = pd.DataFrame(rows)
    assert not out.empty, "AIOE per-occ scores are empty"
    return out


def _ext_at_level(ext_df: pd.DataFrame, col: str, agg_level: str) -> pd.Series:
    """Roll an external benchmark from occupation level to SOC group level
    using an unweighted mean across matched occupations (each occupation
    contributes equally to its group). Matches the rollup method used in
    the exploratory gpts_are_gpts and aioe_comparison charts 14/18."""
    work = ext_df[["title_current", col]].dropna().copy()
    if agg_level == "occupation":
        return work.set_index("title_current")[col]

    from backend.compute import load_eco_raw
    eco = load_eco_raw()
    level_col = {
        "major": "major_occ_category",
        "minor": "minor_occ_category",
        "broad": "broad_occ",
    }[agg_level]
    occ_to_group = (
        eco[["title_current", level_col]].drop_duplicates()
           .set_index("title_current")[level_col]
    )
    work["group"] = work["title_current"].map(occ_to_group)
    work = work.dropna(subset=["group"])
    return work.groupby("group")[col].mean()


def build_convergence(results: Path, figures: Path) -> None:
    """One combined heatmap per agg level. Y-axis = our 4 internal sources.
    X-axis = our 4 sources (lower triangle filled, diagonal/upper blank) + 4
    external benchmarks = 8 cols. 2x2 grid across SOC levels. Single shared
    color bar; zmin = min observed across all cells."""
    eloundou = _load_eloundou_occ()
    aioe = _compute_aioe_occ()
    ext_df = eloundou.merge(aioe, on="title_current", how="outer")
    print(f"  External benchmarks loaded: {len(ext_df)} occs")

    source_data: dict[str, dict[str, pd.Series]] = {}
    for skey in CORR_ORDER:
        ds = CORR_SOURCES[skey]["dataset"]
        source_data[skey] = {}
        for level in AGG_LEVELS:
            df = _run_config(ds, level)
            source_data[skey][level] = df.set_index("category")["pct_tasks_affected"]
        print(f"  {CORR_SOURCES[skey]['label']}: loaded all levels")

    ext_keys = [k for k, _ in EXT_SOURCES]
    ext_labels = [lbl for _, lbl in EXT_SOURCES]
    our_labels = CORR_LABELS
    n = len(CORR_ORDER)
    n_ext = len(EXT_SOURCES)

    x_labels = list(our_labels) + list(ext_labels)
    n_cols = len(x_labels)

    corr_records: list[dict] = []
    matrices: dict[str, np.ndarray] = {}
    pmatrices: dict[str, np.ndarray] = {}

    for level in AGG_LEVELS:
        mat = np.full((n, n_cols), np.nan)
        pmat = np.full((n, n_cols), np.nan)

        # Internal block (lower triangle): rows 0..n-1 vs cols 0..n-1
        for i in range(n):
            for j in range(i):
                si = source_data[CORR_ORDER[i]][level]
                sj = source_data[CORR_ORDER[j]][level]
                merged = pd.concat([si, sj], axis=1, join="inner").dropna()
                if len(merged) < 3:
                    continue
                rho, pval = stats.spearmanr(merged.iloc[:, 0], merged.iloc[:, 1])
                mat[i, j] = rho
                pmat[i, j] = pval
                corr_records.append({
                    "level": level, "kind": "internal",
                    "source_a": our_labels[i], "source_b": our_labels[j],
                    "rho": round(float(rho), 3),
                    "p_value": round(float(pval), 6),
                    "n": len(merged), "stars": _stars(pval),
                })

        # External block: rows 0..n-1 vs cols n..n+n_ext-1
        for i, skey in enumerate(CORR_ORDER):
            ours = source_data[skey][level]
            for k, ext_key in enumerate(ext_keys):
                theirs = _ext_at_level(ext_df, ext_key, level)
                merged = pd.concat(
                    [ours.rename("x"), theirs.rename("y")],
                    axis=1, join="inner",
                ).dropna()
                if len(merged) < 3:
                    continue
                rho, pval = stats.spearmanr(merged["x"], merged["y"])
                mat[i, n + k] = rho
                pmat[i, n + k] = pval
                corr_records.append({
                    "level": level, "kind": "external",
                    "source_a": our_labels[i], "source_b": ext_labels[k],
                    "rho": round(float(rho), 3),
                    "p_value": round(float(pval), 6),
                    "n": len(merged), "stars": _stars(pval),
                })

        matrices[level] = mat
        pmatrices[level] = pmat

    save_csv(pd.DataFrame(corr_records), results / "spearman_combined.csv")

    # Shared color scale: zmin = min observed across all subplots, zmax = 1.0
    all_vals = np.concatenate([m[~np.isnan(m)] for m in matrices.values()])
    z_min = float(np.floor(all_vals.min() * 20) / 20)  # round down to nearest 0.05
    z_max = 1.0

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[AGG_TITLES[l] for l in AGG_LEVELS],
        horizontal_spacing=0.10,
        vertical_spacing=0.14,
    )

    for idx, level in enumerate(AGG_LEVELS):
        row_pos = idx // 2 + 1
        col_pos = idx % 2 + 1
        mat = matrices[level]
        pmat = pmatrices[level]

        fig.add_trace(
            go.Heatmap(
                z=mat.tolist(),
                x=x_labels,
                y=our_labels,
                colorscale=[[0, HEATMAP_LOW], [1, HEATMAP_HIGH]],
                zmin=z_min, zmax=z_max,
                showscale=(idx == 3),
                hoverinfo="z",
                colorbar=dict(
                    title=dict(text="Spearman ρ",
                               font=dict(size=LABEL_FS, family=FONT_FAMILY)),
                    len=0.45, y=0.22,
                    tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
                ),
            ),
            row=row_pos, col=col_pos,
        )

        for i in range(n):
            for j in range(n_cols):
                val = mat[i, j]
                if np.isnan(val):
                    continue
                norm = (val - z_min) / max(z_max - z_min, 1e-9)
                txt_color = "white" if norm >= 0.55 else PAPER_PALETTE["text_dark"]
                fig.add_annotation(
                    x=x_labels[j], y=our_labels[i],
                    text=f"{val:.2f}{_stars(pmat[i, j])}",
                    showarrow=False,
                    font=dict(size=HEATMAP_TEXT_FS - 2, family=FONT_FAMILY, color=txt_color),
                    xref=f"x{idx + 1}" if idx > 0 else "x",
                    yref=f"y{idx + 1}" if idx > 0 else "y",
                )

        # Vertical divider between internal and external blocks
        x_axis = f"x{idx + 1}" if idx > 0 else "x"
        y_axis = f"y{idx + 1}" if idx > 0 else "y"
        fig.add_shape(
            type="line",
            x0=n - 0.5, x1=n - 0.5,
            y0=-0.5, y1=n - 0.5,
            xref=x_axis, yref=y_axis,
            line=dict(color=PAPER_PALETTE["text"], width=2),
        )

    style_paper_figure(
        fig,
        "Spearman ρ — Internal Source Agreement and External Benchmark Convergence",
        width=PAPER_W + 100,
        height=PAPER_H + 240,
        margin=dict(l=20, r=130, t=90, b=110),
    )

    fig.add_annotation(
        text=SIG_FOOTNOTE,
        xref="paper", yref="paper",
        x=0, y=-0.08, xanchor="left", yanchor="top",
        showarrow=False,
        font=dict(size=ANNOT_FS, family=FONT_FAMILY,
                  color=PAPER_PALETTE["muted"]),
    )

    agg_title_set = set(AGG_TITLES.values())
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in agg_title_set:
            ann.font = dict(
                size=LABEL_FS + 1, family=FONT_FAMILY,
                color=PAPER_PALETTE["text"],
            )

    for i in range(1, 5):
        xkey = f"xaxis{i}" if i > 1 else "xaxis"
        ykey = f"yaxis{i}" if i > 1 else "yaxis"
        fig.layout[xkey].tickfont = dict(size=TICK_FS - 2, family=FONT_FAMILY)
        fig.layout[ykey].tickfont = dict(size=TICK_FS - 1, family=FONT_FAMILY)
        fig.layout[xkey].tickangle = -30

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


def _build_combined_table(trend_df: pd.DataFrame, results: Path, figures: Path) -> None:
    """Two side-by-side trimmed tables (one per config) in a single figure.
    Each table: Date | Unique Tasks Rated (+ Δ) | AI Capability (+ Δ)."""
    highlight = PAPER_PALETTE["row_highlight"]
    white = PAPER_PALETTE["surface"]
    ref_fill = PAPER_PALETTE["row_ref"]

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "table"}, {"type": "table"}]],
        subplot_titles=[ANALYSIS_CONFIG_LABELS[k] for k in TREND_CONFIGS],
        horizontal_spacing=0.04,
    )

    for col_idx, config_key in enumerate(TREND_CONFIGS, start=1):
        sub = trend_df[trend_df["config"] == config_key].sort_values("date").reset_index(drop=True)
        if sub.empty:
            continue

        col_date: list[str] = []
        col_tasks: list[str] = []
        col_dtasks: list[str] = []
        col_autoaug: list[str] = []
        col_dautoaug: list[str] = []
        date_fills: list[str] = []

        for i, (_, r) in enumerate(sub.iterrows()):
            is_start, is_end = i == 0, i == len(sub) - 1
            if is_start:
                col_date.append(f"Start: {fmt_date(r['date'])}")
            elif is_end:
                col_date.append(f"End: {fmt_date(r['date'])}")
            else:
                col_date.append(fmt_date(r["date"]))

            col_tasks.append(f"{int(r['n_tasks']):,}")
            col_autoaug.append(f"{r['avg_auto_aug']:.2f}")

            if is_start:
                col_dtasks.append("—")
                col_dautoaug.append("—")
            else:
                prev = sub.iloc[i - 1]
                dt = int(r["n_tasks"] - prev["n_tasks"])
                col_dtasks.append(f"{'+' if dt >= 0 else ''}{dt:,}")
                da = float(r["avg_auto_aug"] - prev["avg_auto_aug"])
                col_dautoaug.append(f"{'+' if da >= 0 else ''}{da:.2f}")

            date_fills.append(highlight if (is_start or is_end) else white)

        n_rows = len(col_date)
        neutral_fills = [white] * n_rows

        header_color = (PAPER_PALETTE["all_confirmed"]
                        if "confirmed" in config_key
                        else PAPER_PALETTE["all_ceiling"])

        fig.add_trace(go.Table(
            header=dict(
                values=["Date", "Unique<br>Tasks Rated", "Δ", "AI Capability<br>(0–5)", "Δ"],
                font=dict(size=TABLE_HEADER_FS, family=FONT_FAMILY, color="white"),
                fill_color=header_color,
                align="center",
                height=40,
            ),
            cells=dict(
                values=[col_date, col_tasks, col_dtasks, col_autoaug, col_dautoaug],
                font=dict(size=TABLE_CELL_FS, family=FONT_FAMILY),
                fill_color=[date_fills, neutral_fills, neutral_fills,
                            neutral_fills, neutral_fills],
                align="center",
                height=32,
            ),
        ), row=1, col=col_idx)

    max_rows = max(
        len(trend_df[trend_df["config"] == k]) for k in TREND_CONFIGS
    )
    height = max(380, max_rows * 40 + 150)

    style_paper_figure(
        fig,
        "Tasks rated and AI capability over time",
        height=height,
        margin=dict(l=10, r=10, t=80, b=20),
    )

    # Style the per-table title annotations
    label_set = {ANALYSIS_CONFIG_LABELS[k] for k in TREND_CONFIGS}
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in label_set:
            ann.font = dict(size=LABEL_FS, family=FONT_FAMILY,
                            color=PAPER_PALETTE["text"])

    save_figure(fig, results / "figures" / "temporal_tables.png")
    _copy_fig(results, figures, "temporal_tables.png")
    print("  -> temporal_tables.png")


def _build_three_panel_trend(trend_df: pd.DataFrame, results: Path, figures: Path) -> None:
    """Three side-by-side panels (Workers / Wages / % Tasks Affected),
    each plotting all_confirmed and all_ceiling lines."""
    panels = [
        ("workers", "Workers Affected", lambda v: fmt_workers(v),
         lambda subset: subset["workers"]),
        ("wages",   "Wages Affected",   lambda v: fmt_wages(v),
         lambda subset: subset["wages"]),
        ("pct",     "% Tasks Affected", lambda v: f"{v:.1f}%",
         lambda subset: subset["pct_tasks_affected"]),
    ]

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=[p[1] for p in panels],
        horizontal_spacing=0.08,
    )

    for col_idx, (key, title, fmt_fn, getter) in enumerate(panels, start=1):
        for config_key in TREND_CONFIGS:
            subset = trend_df[trend_df["config"] == config_key].sort_values("date")
            label = ANALYSIS_CONFIG_LABELS[config_key]
            color = TREND_COLORS[config_key]
            yvals = getter(subset)

            positions = ["top center"] * len(subset)
            if len(subset) >= 2:
                positions[-1] = "top left"

            fig.add_trace(go.Scatter(
                x=subset["date"],
                y=yvals,
                name=label,
                legendgroup=config_key,
                showlegend=(col_idx == 1),
                mode="lines+markers+text",
                line=dict(color=color, width=3),
                marker=dict(size=8, color=color),
                text=[fmt_fn(v) for v in yvals],
                textposition=positions,
                textfont=dict(size=ANNOT_FS, color=color, family=FONT_FAMILY),
            ), row=1, col=col_idx)

        if key == "pct":
            fig.update_yaxes(ticksuffix="%", row=1, col=col_idx)
        elif key == "wages":
            fig.update_yaxes(tickprefix="$", row=1, col=col_idx)

        fig.update_xaxes(
            tickangle=-30,
            tickfont=dict(size=ANNOT_FS, family=FONT_FAMILY),
            row=1, col=col_idx,
        )
        fig.update_yaxes(
            rangemode="tozero",
            tickfont=dict(size=ANNOT_FS, family=FONT_FAMILY),
            row=1, col=col_idx,
        )

    style_paper_figure(
        fig,
        "AI exposure over time — confirmed vs. ceiling",
        height=PAPER_H - 80,
        width=PAPER_W + 100,
        margin=dict(l=60, r=40, t=90, b=110),
    )

    panel_titles = {p[1] for p in panels}
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in panel_titles:
            ann.font = dict(size=LABEL_FS, family=FONT_FAMILY,
                            color=PAPER_PALETTE["text"])

    save_figure(fig, results / "figures" / "temporal_trend.png")
    _copy_fig(results, figures, "temporal_trend.png")
    print("  -> temporal_trend.png")


def build_temporal(results: Path, figures: Path) -> None:
    trend_df = _build_trend_data()
    save_csv(trend_df, results / "trend_data.csv")
    _build_three_panel_trend(trend_df, results, figures)
    _build_combined_table(trend_df, results, figures)

    # Remove stale single-config tables and temporal_deltas if they exist
    for stale in (
        "temporal_table_all_confirmed.png",
        "temporal_table_all_ceiling.png",
        "temporal_deltas.png",
    ):
        for d in (results / "figures", figures):
            p = d / stale
            if p.exists():
                p.unlink()


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

    print("\n[2/3] Convergence: combined internal + external")
    build_convergence(results, figures)

    print("\n[3/3] Temporal: Growth trends + data tables")
    build_temporal(results, figures)

    print("\n" + "=" * 60)
    print("Part 1 complete — figures in results/figures/ and figures/")
    print("=" * 60)


if __name__ == "__main__":
    main()
