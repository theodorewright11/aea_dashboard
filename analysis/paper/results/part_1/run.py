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
    METRIC_COLORS, METRIC_COLORS_LIGHT, HEATMAP_LOW, HEATMAP_HIGH,
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
    ("gpt_beta",      "Eloundou GPT-4 β"),
    ("human_beta",    "Eloundou Human β"),
    ("aioe_mean",     "AIOE Overall"),
    ("aioe_rc",       "AIOE Reading Compr."),
    ("schaal_overall", "Schaal Overall"),
    ("schaal_da",     "Schaal DA"),
    ("schaal_ag",     "Schaal AG"),
    ("tomlinson_copilot", "Tomlinson (Copilot)"),
]

# Cells to gray out as contaminated by the Copilot task-filter pipeline
# (Eloundou labels were used to filter which Copilot tasks were included,
# so any correlation between a Copilot-containing measure and an Eloundou
# benchmark double-counts that signal). Keys are (row_label, col_label)
# pairs matching the labels rendered on each chart.
ELOUNDOU_LABELS: set[str] = {"Eloundou GPT-4 β", "Eloundou Human β"}
CONTAMINATED_SOURCE_ROWS: set[str] = {"Copilot"}
CONTAMINATED_CONFIG_ROWS: set[str] = {
    "All Confirmed", "All Sources (Ceiling)", "Conversational Confirmed",
}

GPTS_CSV = ANALYSIS_DIR / "data" / "gpts_are_gpts_occ_data.csv"
AIOE_MATRIX_PATH = ANALYSIS_DIR / "data" / "aioe_ability_matrix.csv"
ABILITIES_PATH = ANALYSIS_DIR / "data" / "abilities_v30.1.csv"
SCHAAL_INDICES_CSV = ANALYSIS_DIR / "data" / "Comparison of Indices.csv"
TOMLINSON_CSV = ANALYSIS_DIR / "data" / "ai_applicability_scores.csv"


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


SIG_NOTE: str = "All correlations significant at p < .001 (two-tailed Spearman)."


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

    # Bar order within each config: tasks → workers → wages (top to bottom
    # within each grouped cluster). Plotly grouped bars stack first-trace
    # at the bottom of the cluster, so add them in reverse.
    metrics = [
        ("pct_tasks",   "% Tasks Exposed",
         METRIC_COLORS["tasks"],
         lambda r: f"{r['pct_tasks']:.1f}% tasks"),
        ("pct_workers", "Workers Exposed (% of National Employment)",
         METRIC_COLORS["workers"],
         lambda r: f"{fmt_workers(r['workers'])} ({r['pct_workers']:.1f}%) workers"),
        ("pct_wages",   "Wages Exposed (% of National Wages)",
         METRIC_COLORS["wages"],
         lambda r: f"{fmt_wages(r['wages'])} ({r['pct_wages']:.1f}%) wages"),
    ]

    for pct_key, name, color, fmt_fn in reversed(metrics):
        fig.add_trace(go.Bar(
            y=labels,
            x=[r[pct_key] for r in plot_rows],
            name=name,
            orientation="h",
            marker=dict(color=color, line=dict(width=0)),
            text=[fmt_fn(r) for r in plot_rows],
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(size=INSIDE_FS - 2, color="white", family=FONT_FAMILY),
        ))

    # Reorder legend to read tasks → workers → wages even though traces
    # were added in reverse for the cluster ordering.
    fig.update_layout(
        barmode="group",
        bargap=0.30,
        bargroupgap=0.06,
        legend=dict(traceorder="reversed"),
        xaxis=dict(
            title=dict(text="% of National Total", font=dict(size=LABEL_FS)),
            range=[0, 65],
            ticksuffix="%",
        ),
        yaxis=dict(
            title=dict(text="Data Configuration", font=dict(size=LABEL_FS)),
            tickfont=dict(size=LABEL_FS, family=FONT_FAMILY),
        ),
    )

    style_paper_figure(
        fig,
        "AI Economic Exposure Across Data Configurations",
        subtitle=(
            "Share of national tasks, employment, and wages exposed per "
            "AI data configuration."
        ),
        height=PAPER_H + 140,
        margin=dict(l=20, r=60, t=140, b=110),
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


def _load_schaal_occ() -> pd.DataFrame:
    """Schaal 2025 occupation-level scores from `Comparison of Indices.csv`.
    Title joins exactly to title_current. Returns title_current,
    schaal_overall (auto_w), schaal_da (da_w), schaal_ag (ag_w)."""
    df = pd.read_csv(SCHAAL_INDICES_CSV)
    assert "title" in df.columns, f"title column missing in {SCHAAL_INDICES_CSV}"
    for c in ("auto_w", "da_w", "ag_w"):
        assert c in df.columns, f"{c} column missing in {SCHAAL_INDICES_CSV}"
    out = pd.DataFrame({
        "title_current":   df["title"].astype(str),
        "schaal_overall":  pd.to_numeric(df["auto_w"], errors="coerce"),
        "schaal_da":       pd.to_numeric(df["da_w"],   errors="coerce"),
        "schaal_ag":       pd.to_numeric(df["ag_w"],   errors="coerce"),
    })
    assert out["schaal_overall"].notna().any(), "Schaal auto_w is all NaN after load"
    assert out["schaal_da"].notna().any(),      "Schaal da_w is all NaN after load"
    assert out["schaal_ag"].notna().any(),      "Schaal ag_w is all NaN after load"
    return out


def _load_tomlinson_occ() -> pd.DataFrame:
    """Tomlinson, Jaffe, Wang, Counts & Suri (2025) AI applicability score per
    SOC, derived from ~100k Bing Copilot conversations × O*NET IWA weights
    × LLM completion + scope. Title joins exactly to title_current. Returns
    title_current, tomlinson_copilot."""
    df = pd.read_csv(TOMLINSON_CSV)
    assert "title" in df.columns, f"title column missing in {TOMLINSON_CSV}"
    assert "ai_applicability_score" in df.columns, \
        f"ai_applicability_score column missing in {TOMLINSON_CSV}"
    out = pd.DataFrame({
        "title_current":      df["title"].astype(str),
        "tomlinson_copilot":  pd.to_numeric(df["ai_applicability_score"], errors="coerce"),
    }).dropna(subset=["tomlinson_copilot"])
    assert not out.empty, "Tomlinson scores are all NaN after load"
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


def _build_convergence_chart(
    rows_keys: list[str],
    rows_labels: list[str],
    rows_data: dict[str, dict[str, pd.Series]],
    title: str,
    subtitle: str,
    out_name: str,
    csv_name: str,
    results: Path,
    figures: Path,
    y_axis_title: str,
    contaminated_rows: set[str] | None = None,
) -> None:
    """Build one combined heatmap (lower-tri internal + external block).

    `rows_keys` and `rows_labels` define the y-axis. `rows_data` is a
    nested dict {key → {level → pd.Series}} of pct_tasks_affected at
    each SOC level. `contaminated_rows` is the set of row labels whose
    correlations against ELOUNDOU_LABELS columns should be visually
    grayed out (the Eloundou-filter contamination on Copilot-containing
    measures).
    """
    contaminated_rows = contaminated_rows or set()
    eloundou = _load_eloundou_occ()
    aioe = _compute_aioe_occ()
    schaal = _load_schaal_occ()
    tomlinson = _load_tomlinson_occ()
    ext_df = (
        eloundou.merge(aioe,      on="title_current", how="outer")
                .merge(schaal,    on="title_current", how="outer")
                .merge(tomlinson, on="title_current", how="outer")
    )

    ext_keys = [k for k, _ in EXT_SOURCES]
    ext_labels = [lbl for _, lbl in EXT_SOURCES]
    n = len(rows_keys)
    n_ext = len(EXT_SOURCES)

    # Insert one blank column between the internal block and the external
    # block to visually separate the two groups. The gap column sits at
    # position `n` (index n in the matrix, label "" so no x-tick renders).
    GAP_LABEL = " "
    x_labels = list(rows_labels) + [GAP_LABEL] + list(ext_labels)
    n_cols = len(x_labels)
    EXT_OFFSET = n + 1   # column index where external block starts

    corr_records: list[dict] = []
    matrices: dict[str, np.ndarray] = {}
    pmatrices: dict[str, np.ndarray] = {}

    for level in AGG_LEVELS:
        mat = np.full((n, n_cols), np.nan)
        pmat = np.full((n, n_cols), np.nan)

        # Internal block (lower triangle)
        for i in range(n):
            for j in range(i):
                si = rows_data[rows_keys[i]][level]
                sj = rows_data[rows_keys[j]][level]
                merged = pd.concat([si, sj], axis=1, join="inner").dropna()
                if len(merged) < 3:
                    continue
                rho, pval = stats.spearmanr(merged.iloc[:, 0], merged.iloc[:, 1])
                mat[i, j] = rho
                pmat[i, j] = pval
                corr_records.append({
                    "level": level, "kind": "internal",
                    "source_a": rows_labels[i], "source_b": rows_labels[j],
                    "rho": round(float(rho), 3),
                    "p_value": round(float(pval), 6),
                    "n": len(merged), "stars": _stars(pval),
                })

        # External block (offset by 1 to skip the gap column)
        for i, skey in enumerate(rows_keys):
            ours = rows_data[skey][level]
            for k, ext_key in enumerate(ext_keys):
                theirs = _ext_at_level(ext_df, ext_key, level)
                merged = pd.concat(
                    [ours.rename("x"), theirs.rename("y")],
                    axis=1, join="inner",
                ).dropna()
                if len(merged) < 3:
                    continue
                rho, pval = stats.spearmanr(merged["x"], merged["y"])
                mat[i, EXT_OFFSET + k] = rho
                pmat[i, EXT_OFFSET + k] = pval
                corr_records.append({
                    "level": level, "kind": "external",
                    "source_a": rows_labels[i], "source_b": ext_labels[k],
                    "rho": round(float(rho), 3),
                    "p_value": round(float(pval), 6),
                    "n": len(merged), "stars": _stars(pval),
                })

        matrices[level] = mat
        pmatrices[level] = pmat

    save_csv(pd.DataFrame(corr_records), results / csv_name)

    all_vals = np.concatenate([m[~np.isnan(m)] for m in matrices.values()])
    z_min = float(np.floor(all_vals.min() * 20) / 20)
    z_max = 1.0

    # Tight 2x2 grid — panels pushed close together so the heatmap content
    # itself takes up more of the figure area. Vertical spacing still has
    # to leave room for the "Internal" / "External" group headers above
    # each panel + the subplot title above those.
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[AGG_TITLES[l] for l in AGG_LEVELS],
        horizontal_spacing=0.09,
        vertical_spacing=0.20,
    )

    # Cell number font — bumped past HEATMAP_TEXT_FS for readability
    cell_fs = HEATMAP_TEXT_FS + 2     # 20pt regardless of column count

    contam_color = "rgba(200, 200, 200, 0.92)"
    contam_text  = "#777777"

    for idx, level in enumerate(AGG_LEVELS):
        row_pos = idx // 2 + 1
        col_pos = idx % 2 + 1
        mat = matrices[level]
        pmat = pmatrices[level]

        fig.add_trace(
            go.Heatmap(
                z=mat.tolist(),
                x=x_labels,
                y=rows_labels,
                colorscale=[[0, HEATMAP_LOW], [1, HEATMAP_HIGH]],
                zmin=z_min, zmax=z_max,
                showscale=(idx == 3),
                hoverinfo="z",
                colorbar=dict(
                    title=dict(text="Spearman ρ",
                               font=dict(size=LABEL_FS + 2, family=FONT_FAMILY)),
                    len=0.45, y=0.22,
                    tickfont=dict(size=TICK_FS + 1, family=FONT_FAMILY),
                ),
            ),
            row=row_pos, col=col_pos,
        )

        x_axis = f"x{idx + 1}" if idx > 0 else "x"
        y_axis = f"y{idx + 1}" if idx > 0 else "y"

        for i in range(n):
            for j in range(n_cols):
                val = mat[i, j]
                if np.isnan(val):
                    continue

                # Contamination check: row label is in contaminated set AND
                # this column is one of the Eloundou columns. Apply gray
                # overlay first (so annotation sits on top), then render
                # the value in muted text.
                row_label = rows_labels[i]
                col_label = x_labels[j]
                is_contam = (row_label in contaminated_rows
                             and col_label in ELOUNDOU_LABELS)

                if is_contam:
                    fig.add_shape(
                        type="rect",
                        x0=j - 0.5, x1=j + 0.5,
                        y0=i - 0.5, y1=i + 0.5,
                        xref=x_axis, yref=y_axis,
                        fillcolor=contam_color,
                        line=dict(width=0),
                        layer="above",
                    )
                    txt_color = contam_text
                else:
                    norm = (val - z_min) / max(z_max - z_min, 1e-9)
                    txt_color = "white" if norm >= 0.55 else PAPER_PALETTE["text_dark"]

                fig.add_annotation(
                    x=x_labels[j], y=rows_labels[i],
                    text=f"{val:.2f}",
                    showarrow=False,
                    font=dict(size=cell_fs, family=FONT_FAMILY, color=txt_color),
                    xref=x_axis, yref=y_axis,
                )

        # Group header annotations centered above each block. Positioned
        # in axis coordinates (x = block midpoint), with a pixel yshift
        # so they sit just above the top edge of the heatmap regardless
        # of zoom level.
        internal_mid = (n - 1) / 2.0
        external_mid = EXT_OFFSET + (n_ext - 1) / 2.0
        for header_text, header_x in [("Internal", internal_mid),
                                       ("External", external_mid)]:
            fig.add_annotation(
                x=header_x, y=n - 0.5,
                text=f"<b>{header_text}</b>",
                showarrow=False,
                xanchor="center", yanchor="bottom",
                yshift=12,
                font=dict(size=LABEL_FS + 4, family=FONT_FAMILY,
                          color=PAPER_PALETTE["text"]),
                xref=x_axis, yref=y_axis,
            )

        # Vertical divider between internal and external blocks
        fig.add_shape(
            type="line",
            x0=n - 0.5 + 0.5, x1=n - 0.5 + 0.5,  # midpoint of the gap col
            y0=-0.5, y1=n - 0.5,
            xref=x_axis, yref=y_axis,
            line=dict(color=PAPER_PALETTE["text"], width=2),
        )

    # Width unchanged from the previous version — just shrink margins
    # so the panels themselves are larger inside the same canvas.
    fig_width = PAPER_W + max(0, (n_cols - 8) * 80)
    fig_height = PAPER_H + 540

    full_subtitle = f"{subtitle}. {SIG_NOTE}"
    style_paper_figure(
        fig,
        title,
        subtitle=full_subtitle,
        width=fig_width,
        height=fig_height,
        margin=dict(l=20, r=120, t=170, b=220),
    )

    # Bump subplot titles up + embiggen so they sit clear of the
    # "Internal" / "External" group headers placed below them.
    agg_title_set = set(AGG_TITLES.values())
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in agg_title_set:
            ann.font = dict(
                size=LABEL_FS + 6, family=FONT_FAMILY,
                color=PAPER_PALETTE["text"],
            )
            ann.yshift = 32

    # Contamination legend — shown only when something is grayed out.
    # Placed in the bottom margin, below the angled x-tick labels. The
    # swatch is rendered as a real paper-coordinate rectangle because
    # Plotly's PNG export ignores HTML background-color in spans.
    if contaminated_rows:
        # Swatch position (paper coords). Pushed well below the heatmap
        # so it sits clear of the angled tick labels.
        sx0, sx1 = 0.085, 0.130
        sy0, sy1 = -0.150, -0.110
        fig.add_shape(
            type="rect",
            xref="paper", yref="paper",
            x0=sx0, x1=sx1, y0=sy0, y1=sy1,
            fillcolor=contam_color,
            line=dict(color=contam_text, width=1),
            layer="above",
        )
        fig.add_annotation(
            xref="paper", yref="paper",
            x=sx1 + 0.010, y=(sy0 + sy1) / 2,
            xanchor="left", yanchor="middle",
            text=("<b>Eloundou-contaminated cell</b> — Eloundou's task labels "
                  "were used to filter Copilot tasks, so correlations between "
                  "a Copilot-containing measure and an Eloundou benchmark "
                  "double-count that signal. Values shown for transparency."),
            showarrow=False,
            font=dict(size=ANNOT_FS + 3, family=FONT_FAMILY,
                      color=PAPER_PALETTE["text"]),
        )

    # y-axis title only on the left column (panels 1 and 3) so it doesn't
    # collide with the colorbar on the right-column panels.
    left_col_axes = {1, 3}
    for i in range(1, 5):
        xkey = f"xaxis{i}" if i > 1 else "xaxis"
        ykey = f"yaxis{i}" if i > 1 else "yaxis"
        fig.layout[xkey].tickfont = dict(size=TICK_FS + 1, family=FONT_FAMILY)
        fig.layout[ykey].tickfont = dict(size=TICK_FS + 1, family=FONT_FAMILY)
        fig.layout[xkey].tickangle = -30
        if y_axis_title and i in left_col_axes:
            fig.layout[ykey].title = dict(
                text=y_axis_title,
                font=dict(size=LABEL_FS + 1, family=FONT_FAMILY),
            )

    save_figure(fig, results / "figures" / out_name)
    _copy_fig(results, figures, out_name)
    print(f"  -> {out_name}")


def build_convergence(results: Path, figures: Path) -> None:
    """Source-level external benchmark comparison: 4 internal sources
    on the y-axis, 4 sources (lower-tri) + 4 external benchmarks on x."""
    source_data: dict[str, dict[str, pd.Series]] = {}
    for skey in CORR_ORDER:
        ds = CORR_SOURCES[skey]["dataset"]
        source_data[skey] = {}
        for level in AGG_LEVELS:
            df = _run_config(ds, level)
            source_data[skey][level] = df.set_index("category")["pct_tasks_affected"]
        print(f"  {CORR_SOURCES[skey]['label']}: loaded all levels")

    _build_convergence_chart(
        rows_keys=CORR_ORDER,
        rows_labels=CORR_LABELS,
        rows_data=source_data,
        title="Internal and External Benchmark Comparison — by AI Source",
        subtitle="Spearman ρ across our internal sources and academic benchmarks",
        out_name="convergence.png",
        csv_name="spearman_combined.csv",
        results=results, figures=figures,
        y_axis_title="Internal Source",
        contaminated_rows=CONTAMINATED_SOURCE_ROWS,
    )


def build_convergence_configs(results: Path, figures: Path) -> None:
    """Configuration-level external benchmark comparison: 6 ANALYSIS_CONFIGS
    on the y-axis, 6 configs (lower-tri) + 4 external benchmarks on x."""
    config_data: dict[str, dict[str, pd.Series]] = {}
    for ckey in CONFIG_ORDER:
        ds = ANALYSIS_CONFIGS[ckey]
        config_data[ckey] = {}
        for level in AGG_LEVELS:
            df = _run_config(ds, level)
            config_data[ckey][level] = df.set_index("category")["pct_tasks_affected"]
        print(f"  {ANALYSIS_CONFIG_LABELS[ckey]}: loaded all levels")

    _build_convergence_chart(
        rows_keys=CONFIG_ORDER,
        rows_labels=[ANALYSIS_CONFIG_LABELS[k] for k in CONFIG_ORDER],
        rows_data=config_data,
        title="Internal and External Benchmark Comparison — by Data Configuration",
        subtitle="Spearman ρ across our data configurations and academic benchmarks",
        out_name="convergence_configs.png",
        csv_name="spearman_combined_configs.csv",
        results=results, figures=figures,
        y_axis_title="Data Configuration",
        contaminated_rows=CONTAMINATED_CONFIG_ROWS,
    )


# ─────────────────────────────────────────────────────────────────────────
# Chart 3: Temporal
# ─────────────────────────────────────────────────────────────────────────

# Earlier dates added to the table (cream rows). AI Capability is barred
# because the all_confirmed / all_ceiling combined series doesn't have
# enough source coverage on these dates to compute a stable score, but the
# combined "tasks rated" count is still meaningful — we draw it from the
# date-matched all_confirmed / all_ceiling files (`AEI Both + Micro` /
# `All` respectively), which mirror the line-chart series.
HISTORICAL_DATES: list[str] = ["2024-09-30", "2024-12-23"]
# Per-config dataset names for the historical task counts.
HISTORICAL_DATASETS: dict[str, dict[str, str]] = {
    "all_confirmed": {
        "2024-09-30": "AEI Both + Micro 2024-09-30",
        "2024-12-23": "AEI Both + Micro 2024-12-23",
    },
    "all_ceiling": {
        "2024-09-30": "All 2024-09-30",
        "2024-12-23": "All 2024-12-23",
    },
}


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


def _build_historical_rows(config_key: str) -> list[dict]:
    """Cream-row task counts for the dates that pre-date the line chart.

    The All Confirmed and All Ceiling tables each pull their historical
    rows from the same combined-source dataset family that the line chart
    uses (AEI Both + Micro for confirmed, All for ceiling). Sep 2024 only
    has Microsoft contributing, so the count there is Microsoft's rated
    set; Dec 2024 has Microsoft + AEI Conv v1, and the AEI Both + Micro /
    All files contain the union."""
    rows: list[dict] = []
    for date_str in HISTORICAL_DATES:
        ds_name = HISTORICAL_DATASETS[config_key][date_str]
        n_tasks = _count_tasks(ds_name)
        rows.append({"date": date_str, "n_tasks": n_tasks})
        print(f"  historical {date_str} ({config_key}, {ds_name}): {n_tasks} tasks rated")
    return rows


def _build_combined_table(trend_df: pd.DataFrame, results: Path, figures: Path) -> None:
    """Two side-by-side per-config tables in one figure.

    Each table includes Sep 2024 and Dec 2024 historical rows pulled from
    that table's own dataset family (AEI Both + Micro for confirmed, All
    for ceiling). AI Capability cell is barred for those rows because the
    confirmed/ceiling AI-capability metric isn't well-defined that early
    in the series (only one or two sources contributing)."""
    highlight = PAPER_PALETTE["row_highlight"]
    white = PAPER_PALETTE["surface"]
    historical_fill = "#f5f0e8"  # subtle cream to mark historical rows
    total_eco_tasks = _get_eco_task_count()

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

        historical_rows = _build_historical_rows(config_key)

        col_date: list[str] = []
        col_tasks: list[str] = []
        col_dtasks: list[str] = []
        col_autoaug: list[str] = []
        col_dautoaug: list[str] = []
        date_fills: list[str] = []

        # Historical (cream) rows first — combined-dataset task counts.
        prev_n_tasks: int | None = None
        for hr in historical_rows:
            col_date.append(fmt_date(hr["date"]))
            col_tasks.append(f"{int(hr['n_tasks']):,}")
            if prev_n_tasks is None:
                col_dtasks.append("—")
            else:
                dt = int(hr["n_tasks"]) - prev_n_tasks
                col_dtasks.append(f"{'+' if dt >= 0 else ''}{dt:,}")
            col_autoaug.append("—")
            col_dautoaug.append("—")
            date_fills.append(historical_fill)
            prev_n_tasks = int(hr["n_tasks"])

        # Series rows (the line-chart range)
        for i, (_, r) in enumerate(sub.iterrows()):
            is_start_combined = (i == 0)
            is_end = (i == len(sub) - 1)

            if is_start_combined:
                col_date.append(f"Series start: {fmt_date(r['date'])}")
            elif is_end:
                col_date.append(f"End: {fmt_date(r['date'])}")
            else:
                col_date.append(fmt_date(r["date"]))

            col_tasks.append(f"{int(r['n_tasks']):,}")
            col_autoaug.append(f"{r['avg_auto_aug']:.2f}")

            curr_n_tasks = int(r["n_tasks"])
            if prev_n_tasks is None:
                col_dtasks.append("—")
            else:
                dt = curr_n_tasks - prev_n_tasks
                col_dtasks.append(f"{'+' if dt >= 0 else ''}{dt:,}")
            prev_n_tasks = curr_n_tasks

            if is_start_combined:
                col_dautoaug.append("—")
            else:
                prev = sub.iloc[i - 1]
                da = float(r["avg_auto_aug"] - prev["avg_auto_aug"])
                col_dautoaug.append(f"{'+' if da >= 0 else ''}{da:.2f}")

            date_fills.append(highlight if (is_start_combined or is_end) else white)

        n_rows = len(col_date)
        n_hist = len(HISTORICAL_DATES)
        cell_fills = [historical_fill] * n_hist + [white] * (n_rows - n_hist)

        header_color = (PAPER_PALETTE["all_confirmed"]
                        if "confirmed" in config_key
                        else PAPER_PALETTE["all_ceiling"])

        fig.add_trace(go.Table(
            columnwidth=[120, 180, 60, 110, 60],
            header=dict(
                values=[
                    "Date",
                    f"Unique Tasks Rated<br>(of {total_eco_tasks:,} total in O*NET)",
                    "Δ",
                    "AI Capability<br>(0–5)",
                    "Δ",
                ],
                font=dict(size=TABLE_HEADER_FS, family=FONT_FAMILY, color="white"),
                fill_color=header_color,
                align="center",
                height=48,
            ),
            cells=dict(
                values=[col_date, col_tasks, col_dtasks, col_autoaug, col_dautoaug],
                font=dict(size=TABLE_CELL_FS, family=FONT_FAMILY),
                fill_color=[date_fills, cell_fills, cell_fills, cell_fills, cell_fills],
                align="center",
                height=32,
            ),
        ), row=1, col=col_idx)

    max_rows = max(
        len(trend_df[trend_df["config"] == k]) for k in TREND_CONFIGS
    ) + len(HISTORICAL_DATES)
    # Header (40) + per-row (38) + title/subtitle/margin (180) — give the
    # ceiling table enough room for all 9 rows + start/end highlights.
    height = max(520, max_rows * 38 + 240)

    style_paper_figure(
        fig,
        "Tasks Rated And AI Capability Over Time",
        subtitle="Cream rows don't have reliable AI capability scores.",
        height=height + 50,
        margin=dict(l=10, r=10, t=170, b=20),
    )

    label_set = {ANALYSIS_CONFIG_LABELS[k] for k in TREND_CONFIGS}
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in label_set:
            ann.font = dict(size=LABEL_FS, family=FONT_FAMILY,
                            color=PAPER_PALETTE["text"])

    save_figure(fig, results / "figures" / "temporal_tables.png")
    _copy_fig(results, figures, "temporal_tables.png")
    print("  -> temporal_tables.png")


def _build_three_panel_trend(trend_df: pd.DataFrame, results: Path, figures: Path) -> None:
    """Three side-by-side panels (Tasks / Workers / Wages), each plotting
    All Confirmed and All Sources (Ceiling) lines. Per-panel metric color:
    tasks=blue, workers=gold, wages=green. All Confirmed = solid line in
    primary color; All Sources (Ceiling) = dashed line in lighter shade.

    Per-point value labels are rendered as annotations with an explicit
    pixel `yshift` so they sit a fixed distance above/below the marker
    regardless of how the line curves — text mode + textposition only
    offsets ~6px which isn't enough to clear a curving line. Confirmed
    labels go below their line; ceiling labels go above theirs.

    The legend is rendered from two neutral-gray dummy traces (one solid,
    one dashed) so it conveys *line style* rather than implying any one
    panel's color is "the" color of confirmed vs. ceiling."""
    panels = [
        ("pct",     "% Tasks Exposed", "% Tasks Exposed",     "tasks",
         lambda v: f"{v:.1f}%",
         lambda subset: subset["pct_tasks_affected"]),
        ("workers", "Workers Exposed", "Workers Exposed",     "workers",
         lambda v: fmt_workers(v),
         lambda subset: subset["workers"]),
        ("wages",   "Wages Exposed",   "Wages Exposed (USD)", "wages",
         lambda v: fmt_wages(v),
         lambda subset: subset["wages"]),
    ]

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=[p[1] for p in panels],
        horizontal_spacing=0.10,
    )

    # Neutral-gray dummy traces JUST for the legend (one solid, one dashed).
    # Use a real date string from the data with y=None so plotly's x-axis
    # type detection still picks date (passing x=[None] forces numeric).
    legend_color = PAPER_PALETTE["text"]
    legend_anchor_x = trend_df["date"].iloc[0]
    fig.add_trace(go.Scatter(
        x=[legend_anchor_x], y=[None], mode="lines",
        name=ANALYSIS_CONFIG_LABELS["all_confirmed"],
        line=dict(color=legend_color, width=3, dash="solid"),
        showlegend=True, hoverinfo="skip",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=[legend_anchor_x], y=[None], mode="lines",
        name=ANALYSIS_CONFIG_LABELS["all_ceiling"],
        line=dict(color=legend_color, width=3, dash="dash"),
        showlegend=True, hoverinfo="skip",
    ), row=1, col=1)

    # Pixel offset for value labels above/below each marker. This is a
    # fixed pixel shift so labels stay clear of the line as it curves
    # between markers, regardless of zoom or aspect ratio.
    LABEL_YSHIFT_PX = 18

    # Horizons (days from final observed date) for the linear extrapolation
    # band on each panel. 2-year ceiling chosen because longer horizons are
    # statistically indefensible given 4–6 observed snapshots.
    EXTRAP_HORIZONS_DAYS: list[tuple[str, int]] = [
        ("6mo", 183),
        ("1yr", 365),
        ("2yr", 730),
    ]

    def _linear_fit_project(dates: list[str], yvals: list[float],
                            horizon_days: list[int]) -> tuple[list[pd.Timestamp], list[float]]:
        """OLS y = a + b·t on observed (date, value) points; project values at each
        horizon past the final observed date. Returns (future_dates, future_values).

        Linear is the simplest defensible "if recent rate continues" frame for a
        2-year window. Pretends nothing past linear; saturation is out of scope."""
        if len(dates) < 2:
            return [], []
        ts = [pd.Timestamp(d) for d in dates]
        t0 = ts[0]
        x = np.array([(t - t0).days for t in ts], dtype=float)
        y = np.array(yvals, dtype=float)
        b, a = np.polyfit(x, y, deg=1)
        last_x = x[-1]
        future_xs = [last_x + h for h in horizon_days]
        future_ts = [t0 + pd.Timedelta(days=int(fx)) for fx in future_xs]
        future_ys = [float(a + b * fx) for fx in future_xs]
        return future_ts, future_ys

    def _spaced_label_indices(dates: list[str], min_days: int = 25) -> set[int]:
        """Pick which date indices get a value label drawn.

        Walks backwards from the last point and keeps a label only if it
        is at least `min_days` from the next kept label. This prevents
        labels at very close dates (e.g. Feb 12 / Feb 18 on the ceiling
        series) from stacking on top of each other horizontally.
        """
        if not dates:
            return set()
        parsed = [pd.Timestamp(d) for d in dates]
        keep = [len(dates) - 1]
        for i in range(len(dates) - 2, -1, -1):
            if (parsed[keep[-1]] - parsed[i]).days >= min_days:
                keep.append(i)
        return set(keep)

    for col_idx, (key, _panel_title, y_axis_title, metric_key, fmt_fn, getter) in enumerate(
        panels, start=1
    ):
        x_ref = "x" if col_idx == 1 else f"x{col_idx}"
        y_ref = "y" if col_idx == 1 else f"y{col_idx}"

        panel_vals: list[float] = []
        for config_key in TREND_CONFIGS:
            subset = trend_df[trend_df["config"] == config_key].sort_values("date").reset_index(drop=True)
            label = ANALYSIS_CONFIG_LABELS[config_key]
            if config_key == "all_confirmed":
                color = METRIC_COLORS[metric_key]
                dash = "solid"
                yshift = -LABEL_YSHIFT_PX  # below marker
            else:
                color = METRIC_COLORS_LIGHT[metric_key]
                dash = "dash"
                yshift = LABEL_YSHIFT_PX   # above marker

            xvals = list(subset["date"])
            yvals = list(getter(subset))
            panel_vals.extend(float(v) for v in yvals)

            # The line + markers (showlegend=False — legend uses the dummy
            # neutral traces, since each panel's color is different).
            fig.add_trace(go.Scatter(
                x=xvals, y=yvals,
                name=label,
                legendgroup=config_key,
                showlegend=False,
                mode="lines+markers",
                line=dict(color=color, width=3, dash=dash),
                marker=dict(size=8, color=color),
                hovertemplate=f"<b>{label}</b><br>%{{x}}<br>%{{y}}<extra></extra>",
                cliponaxis=False,
            ), row=1, col=col_idx)

            # Linear "if-recent-rate-continued" projection extending past
            # the final observed point at 6mo / 1yr / 2yr horizons.
            horizon_days = [d for _, d in EXTRAP_HORIZONS_DAYS]
            future_ts, future_ys = _linear_fit_project(xvals, yvals, horizon_days)
            if future_ts:
                proj_x = [pd.Timestamp(xvals[-1])] + future_ts
                proj_y = [yvals[-1]] + future_ys
                fig.add_trace(go.Scatter(
                    x=proj_x, y=proj_y,
                    mode="lines+markers",
                    line=dict(color=color, width=2, dash="dot"),
                    marker=dict(size=7, color=color, symbol="x"),
                    showlegend=False,
                    hovertemplate=f"<b>{label} (linear proj.)</b><br>%{{x}}<br>%{{y}}<extra></extra>",
                    cliponaxis=False,
                    opacity=0.7,
                ), row=1, col=col_idx)
                panel_vals.extend(future_ys)
                for (hz_label, _), t, v in zip(EXTRAP_HORIZONS_DAYS, future_ts, future_ys):
                    fig.add_annotation(
                        x=t, y=v,
                        xref=x_ref, yref=y_ref,
                        text=f"{hz_label}: {fmt_fn(v)}",
                        showarrow=False,
                        yshift=yshift,
                        font=dict(size=ANNOT_FS - 2, color=color, family=FONT_FAMILY),
                    )

            # Per-point value labels as annotations with explicit pixel
            # yshift — ensures the line never overlaps the text. Skip
            # labels for dates within 25 days of the next kept label so
            # close-clustered dates (e.g. Feb 12 / Feb 18) don't stack.
            kept = _spaced_label_indices(xvals)
            for i, (x_i, y_i) in enumerate(zip(xvals, yvals)):
                if i not in kept:
                    continue
                fig.add_annotation(
                    x=x_i, y=y_i,
                    xref=x_ref, yref=y_ref,
                    text=fmt_fn(y_i),
                    showarrow=False,
                    yshift=yshift,
                    font=dict(size=ANNOT_FS - 1, color=color, family=FONT_FAMILY),
                )

        # Tight y-range — leave enough room above and below the data band
        # for the pixel-shifted annotations to render without clipping.
        if panel_vals:
            v_lo, v_hi = min(panel_vals), max(panel_vals)
            spread = v_hi - v_lo
            pad_lo = spread * 0.22
            pad_hi = spread * 0.22
            y_min = max(0.0, v_lo - pad_lo)
            y_max = v_hi + pad_hi
        else:
            y_min, y_max = 0.0, 1.0

        if key == "pct":
            fig.update_yaxes(ticksuffix="%", range=[y_min, y_max], row=1, col=col_idx)
        elif key == "wages":
            fig.update_yaxes(tickprefix="$", range=[y_min, y_max], row=1, col=col_idx)
        else:
            fig.update_yaxes(range=[y_min, y_max], row=1, col=col_idx)

        fig.update_yaxes(
            title=dict(text=y_axis_title, font=dict(size=LABEL_FS - 2)),
            tickfont=dict(size=ANNOT_FS, family=FONT_FAMILY),
            row=1, col=col_idx,
        )
        fig.update_xaxes(
            title=dict(text="Snapshot Date", font=dict(size=LABEL_FS - 2)),
            tickangle=-30,
            tickfont=dict(size=ANNOT_FS, family=FONT_FAMILY),
            row=1, col=col_idx,
        )

    style_paper_figure(
        fig,
        "All Confirmed vs All Sources (Ceiling) Over Time",
        subtitle=(
            "Tasks, workers, and wages exposed over the dataset window "
            "(March 2025 – February 2026). Dotted segments extend each line "
            "with a linear OLS fit through observed points, marking 6mo / 1yr / 2yr "
            "horizons if the recent rate continued."
        ),
        height=PAPER_H + 90,
        width=PAPER_W + 100,
        margin=dict(l=80, r=60, t=170, b=160),
    )

    # Bottom-aligned legend driven by the neutral dummy traces.
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom", y=-0.32, xanchor="center", x=0.5,
            font=dict(size=LEGEND_FS, family=FONT_FAMILY),
            bgcolor="rgba(255,255,255,0.9)",
        ),
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

    print("\n[1/4] External benchmark comparison: by AI Source")
    build_convergence(results, figures)

    print("\n[2/4] External benchmark comparison: by Data Configuration")
    build_convergence_configs(results, figures)

    print("\n[3/4] Overview: Six-config aggregate footprint")
    build_overview(results, figures)

    print("\n[4/4] Temporal: Growth trends + data tables")
    build_temporal(results, figures)

    print("\n" + "=" * 60)
    print("Part 1 complete — figures in results/figures/ and figures/")
    print("=" * 60)


if __name__ == "__main__":
    main()
