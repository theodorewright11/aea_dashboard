"""
run.py — Field Benchmarks: Utah Benchmarks

Focuses on the pct_tasks_affected dimension for Utah workers specifically,
complementing wage_impact/ which covers the dollar magnitude.

Seampoint Utah (2026, preliminary):
  ~20% of work hours AI can take over (governance-constrained)
  ~51% of work hours AI can augment

Our Utah metric (geo="ut"):
  pct_agg = sum(workers_affected) / total_ut_emp * 100
  This is the employment-weighted average task exposure rate for Utah workers.

Also shows which Utah occupations are most exposed, providing ground-level
context for the state-level comparison.

Figures (key ones copied to figures/):
  utah_pct_comparison.png  — Our 5 configs pct_agg vs Seampoint 20%/51%
  utah_top_occs.png        — Top 20 Utah occupations by pct_tasks_affected (all_confirmed)

Run from project root:
    venv/Scripts/python -m analysis.questions.field_benchmarks.utah_benchmarks.run
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from analysis.config import (
    ANALYSIS_CONFIGS,
    ANALYSIS_CONFIG_LABELS,
    ensure_results_dir,
)
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
PRIMARY_KEY = "all_confirmed"

# ── Seampoint Utah constants ─────────────────────────────────────────────────
SEAMPOINT_TAKEOVER = 20.0   # % of work hours — AI can perform with cheap verification
SEAMPOINT_AUGMENT  = 51.0   # % of work hours — AI extends human judgment


def _get_utah_occ_data(dataset_name: str) -> pd.DataFrame:
    """Get occupation-level data for Utah."""
    from backend.compute import get_group_data

    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": "ut",
        "agg_level": "occupation",
        "sort_by": "Workers Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    if data is None:
        return pd.DataFrame()
    df = data["df"]
    gc = data.get("group_col", "title_current")
    return df.rename(columns={gc: "title_current"})[
        ["title_current", "pct_tasks_affected", "workers_affected", "wages_affected"]
    ].copy()


def _compute_utah_pct(occ_df: pd.DataFrame) -> float:
    """pct_agg = sum(workers_affected) / total_utah_emp * 100."""
    total_ut_emp = occ_df.apply(
        lambda r: r["workers_affected"] / (r["pct_tasks_affected"] / 100)
        if r["pct_tasks_affected"] > 0 else 0.0,
        axis=1,
    ).max()  # All rows share the same denominator at state level
    # Better: derive total_utah_emp from sum of employment
    # workers_affected = emp * pct_tasks_affected/100, so emp = workers_affected / (pct/100)
    # Derive total emp from rows with pct > 0
    valid = occ_df[occ_df["pct_tasks_affected"] > 0].copy()
    if valid.empty:
        return np.nan
    emp_per_occ = valid["workers_affected"] / (valid["pct_tasks_affected"] / 100)
    total_ut_emp = emp_per_occ.sum()
    workers = occ_df["workers_affected"].sum()
    return (workers / total_ut_emp * 100) if total_ut_emp > 0 else np.nan


def _build_pct_comparison(agg_rows: list[dict]) -> go.Figure:
    """Bar chart: our 5 configs Utah pct_agg vs Seampoint benchmarks."""
    config_order = ["all_confirmed", "all_ceiling", "human_conversation",
                    "agentic_confirmed", "agentic_ceiling"]
    color_map = {
        "all_confirmed":      COLORS["primary"],
        "all_ceiling":        COLORS["secondary"],
        "human_conversation": COLORS["accent"],
        "agentic_confirmed":  COLORS["muted"],
        "agentic_ceiling":    COLORS["neutral"],
    }

    by_key = {r["config_key"]: r for r in agg_rows}
    labels, vals, cols = [], [], []
    for k in config_order:
        if k in by_key:
            labels.append(ANALYSIS_CONFIG_LABELS[k])
            vals.append(round(by_key[k]["pct_agg"], 1))
            cols.append(color_map[k])

    # Add Seampoint benchmarks
    labels += ["Seampoint: AI Can Take Over", "Seampoint: AI Can Augment"]
    vals   += [SEAMPOINT_TAKEOVER, SEAMPOINT_AUGMENT]
    cols   += [COLORS["accent"], COLORS["accent"]]

    fig = go.Figure(go.Bar(
        x=labels, y=vals,
        marker=dict(color=cols, line=dict(width=0)),
        text=[f"{v:.1f}%" for v in vals],
        textposition="outside",
        textfont=dict(size=12, color=COLORS["neutral"], family=FONT_FAMILY),
    ))
    style_figure(
        fig,
        "Utah Task Exposure Rate — AEA Dashboard vs. Seampoint",
        subtitle=(
            "AEA Dashboard: emp-weighted mean pct_tasks_affected, Utah workers | "
            "Seampoint (2026 preliminary): % of Utah work hours, governance-constrained"
        ),
        y_title="% of Work Tasks / Hours Affected",
        height=500, width=1000,
        show_legend=False,
    )
    fig.update_layout(
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix="%", range=[0, max(vals) * 1.30]),
        xaxis=dict(showgrid=False, tickfont=dict(size=11, family=FONT_FAMILY)),
        margin=dict(l=60, r=40, t=80, b=100),
    )
    return fig


def _build_top_occs(occ_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar: top 20 Utah occupations by pct_tasks_affected (all_confirmed)."""
    top = (
        occ_df[occ_df["workers_affected"] > 0]
        .sort_values("pct_tasks_affected", ascending=False)
        .head(20)
    )
    labels = top["title_current"].tolist()[::-1]
    vals   = top["pct_tasks_affected"].tolist()[::-1]
    workers_k = (top["workers_affected"] / 1000).tolist()[::-1]

    fig = go.Figure(go.Bar(
        y=labels, x=vals,
        orientation="h",
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=[f"{v:.1f}% ({w:.1f}K workers)" for v, w in zip(vals, workers_k)],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(
        fig,
        "Top 20 Utah Occupations by AI Task Exposure (All Confirmed)",
        subtitle="pct_tasks_affected for Utah workers | All Confirmed config | Freq | Auto-aug ON",
        x_title="% of Tasks Affected by AI",
        height=620, width=1100,
        show_legend=False,
    )
    fig.update_layout(
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix="%", range=[0, max(vals) * 1.30]),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        margin=dict(l=20, r=200, t=80, b=60),
    )
    return fig


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("utah_benchmarks: loading Utah occupation data...")

    agg_rows: list[dict] = []
    primary_occ_df = pd.DataFrame()

    for key, ds_name in ANALYSIS_CONFIGS.items():
        label = ANALYSIS_CONFIG_LABELS[key]
        print(f"  {label}...")
        occ_df = _get_utah_occ_data(ds_name)
        if occ_df.empty:
            print(f"    WARNING: no data for {ds_name} geo=ut")
            continue
        pct_agg = _compute_utah_pct(occ_df)
        workers = occ_df["workers_affected"].sum()
        wages   = occ_df["wages_affected"].sum()
        agg_rows.append({
            "config_key":       key,
            "config_label":     label,
            "workers_affected": workers,
            "wages_affected":   wages,
            "pct_agg":          round(pct_agg, 2),
        })
        if key == PRIMARY_KEY:
            primary_occ_df = occ_df

    assert agg_rows, "No Utah data loaded"
    agg_df = pd.DataFrame(agg_rows)

    # Print summary
    print("\n-- Utah pct_tasks_affected --")
    for _, r in agg_df.iterrows():
        print(f"  {r['config_label']:<30}: {r['pct_agg']:.1f}%  "
              f"  ({r['workers_affected']/1e3:,.0f}K workers, ${r['wages_affected']/1e9:.1f}B wages)")
    print(f"\n  Seampoint Utah takeover: {SEAMPOINT_TAKEOVER:.1f}%")
    print(f"  Seampoint Utah augment:  {SEAMPOINT_AUGMENT:.1f}%")

    # Save CSVs
    save_csv(agg_df, results / "utah_pct_agg.csv")
    if not primary_occ_df.empty:
        save_csv(
            primary_occ_df.sort_values("pct_tasks_affected", ascending=False),
            results / "utah_top_occs_confirmed.csv",
        )
    print("\n  CSVs saved.")

    # Figures
    print("  Building figures...")
    fig = _build_pct_comparison(agg_rows)
    save_figure(fig, results / "figures" / "utah_pct_comparison.png")
    shutil.copy(results / "figures" / "utah_pct_comparison.png",
                figs_dir / "utah_pct_comparison.png")
    print("    utah_pct_comparison.png")

    if not primary_occ_df.empty:
        fig = _build_top_occs(primary_occ_df)
        save_figure(fig, results / "figures" / "utah_top_occs.png")
        shutil.copy(results / "figures" / "utah_top_occs.png",
                    figs_dir / "utah_top_occs.png")
        print("    utah_top_occs.png")

    # PDF
    md_path = HERE / "utah_benchmarks_report.md"
    if md_path.exists():
        generate_pdf(md_path, results / "utah_benchmarks_report.pdf")

    print("\nutah_benchmarks: done.")


if __name__ == "__main__":
    main()
