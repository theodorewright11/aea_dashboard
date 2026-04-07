"""
run.py -- Agentic Usage: Sector Footprint

Which industry sectors are most exposed under agentic AI?
How does the agentic ceiling compare to the conv. baseline by sector?

Run from project root:
    venv/Scripts/python -m analysis.questions.agentic_usage.sector_footprint.run
"""
from __future__ import annotations

import warnings
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from analysis.config import ensure_results_dir, ANALYSIS_CONFIGS
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    CATEGORY_PALETTE,
    save_figure,
    save_csv,
    style_figure,
    make_horizontal_bar,
    generate_pdf,
)

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent

# Four datasets for this analysis
DATASETS = {
    "agentic_confirmed": ("AEI API 2026-02-12",           "Agentic Confirmed"),
    "mcp_only":          ("MCP Cumul. v4",                "MCP Only"),
    "agentic_ceiling":   ("MCP + API 2026-02-18",         "Agentic Ceiling"),
    "conv_baseline":     ("AEI Both + Micro 2026-02-12",  "Conv. Baseline"),
}

DATASET_COLORS = {
    "agentic_confirmed": COLORS["secondary"],
    "mcp_only":          CATEGORY_PALETTE[3],
    "agentic_ceiling":   COLORS["primary"],
    "conv_baseline":     COLORS["muted"],
}


def get_level_data(dataset_name: str, agg_level: str) -> pd.DataFrame:
    from backend.compute import get_group_data
    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": "nat",
        "agg_level": agg_level,
        "sort_by": "Workers Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    assert data is not None, f"No data for {dataset_name} at {agg_level}"
    group_col = data["group_col"]
    df = data["df"].rename(columns={group_col: "category"})
    return df[["category", "pct_tasks_affected", "workers_affected", "wages_affected"]].copy()


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("sector_footprint: loading major-level data for all datasets...")

    # ── 1. Major-category breakdown for all 4 datasets ───────────────────────
    major_dfs: dict[str, pd.DataFrame] = {}
    for key, (ds_name, label) in DATASETS.items():
        print(f"  {label}...")
        df = get_level_data(ds_name, "major")
        df = df.rename(columns={
            "pct_tasks_affected": f"pct_{key}",
            "workers_affected": f"workers_{key}",
            "wages_affected": f"wages_{key}",
        })
        major_dfs[key] = df

    # Merge all into one wide df
    major_wide = major_dfs["conv_baseline"].copy()
    for key in ["agentic_confirmed", "mcp_only", "agentic_ceiling"]:
        cols_to_merge = ["category", f"pct_{key}", f"workers_{key}", f"wages_{key}"]
        major_wide = major_wide.merge(major_dfs[key][cols_to_merge], on="category", how="outer")

    # ── 2. Delta: agentic_ceiling - conv_baseline ─────────────────────────────
    major_wide["delta_pct"] = major_wide["pct_agentic_ceiling"] - major_wide["pct_conv_baseline"]

    save_csv(major_wide.sort_values("pct_agentic_ceiling", ascending=False), results / "major_all_datasets.csv")
    print("  major_all_datasets.csv saved")

    # Save delta CSV
    delta_df = major_wide[["category", "pct_conv_baseline", "pct_agentic_ceiling", "delta_pct"]].copy()
    delta_df = delta_df.sort_values("delta_pct", ascending=False)
    save_csv(delta_df, results / "major_delta.csv")
    print("  major_delta.csv saved")

    # ── 3. Minor-category for agentic ceiling ────────────────────────────────
    print("  Loading minor-level data for Agentic Ceiling...")
    minor_ceiling = get_level_data(DATASETS["agentic_ceiling"][0], "minor")
    save_csv(minor_ceiling.sort_values("workers_affected", ascending=False), results / "minor_agentic_ceiling.csv")
    print("  minor_agentic_ceiling.csv saved")

    # ── 4. Figures ──────────────────────────────────────────────────────────
    print("  Building figures...")

    # Sort by agentic ceiling workers for all bar charts
    ceiling_sorted = major_wide.sort_values("workers_agentic_ceiling", ascending=True)

    # Fig 1: Top major categories by workers_affected (agentic ceiling) — horizontal bar
    fig_workers = make_horizontal_bar(
        ceiling_sorted.sort_values("workers_agentic_ceiling", ascending=False),
        category_col="category",
        value_col="workers_agentic_ceiling",
        title="Workers Affected by Major Category — Agentic Ceiling",
        subtitle="Total workers in occupations with >=1 affected task | Agentic Ceiling (MCP + API 2026-02-18)",
        x_title="Workers Affected",
        color=COLORS["primary"],
        height=700, width=1100,
    )
    save_figure(fig_workers, results / "figures" / "major_workers_agentic_ceiling.png")
    shutil.copy(results / "figures" / "major_workers_agentic_ceiling.png", figs_dir / "major_workers_agentic_ceiling.png")
    print("  major_workers_agentic_ceiling.png")

    # Fig 2: pct_tasks_affected by major category (agentic ceiling)
    pct_sorted = major_wide.sort_values("pct_agentic_ceiling", ascending=False).head(20)
    fig_pct = make_horizontal_bar(
        pct_sorted.sort_values("pct_agentic_ceiling", ascending=True),
        category_col="category",
        value_col="pct_agentic_ceiling",
        title="% Tasks Affected by Major Category — Agentic Ceiling",
        subtitle="pct_tasks_affected (ratio-of-totals) | Agentic Ceiling (MCP + API 2026-02-18)",
        x_title="% Tasks Affected",
        color=COLORS["primary"],
        value_format="%.1f%%",
        height=700, width=1100,
    )
    save_figure(fig_pct, results / "figures" / "major_pct_agentic_ceiling.png")
    shutil.copy(results / "figures" / "major_pct_agentic_ceiling.png", figs_dir / "major_pct_agentic_ceiling.png")
    print("  major_pct_agentic_ceiling.png")

    # Fig 3: Diverging bar — delta (agentic ceiling pct - conv baseline pct)
    delta_plot = delta_df.sort_values("delta_pct", ascending=True)
    pos_color = COLORS["primary"]
    neg_color = COLORS["muted"]
    bar_colors = [pos_color if v >= 0 else neg_color for v in delta_plot["delta_pct"]]

    fig_delta = go.Figure(go.Bar(
        x=delta_plot["delta_pct"].tolist(),
        y=delta_plot["category"].tolist(),
        orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"{v:+.1f}pp" for v in delta_plot["delta_pct"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(
        fig_delta,
        "Agentic AI Gain vs. Conv. Baseline by Sector",
        subtitle="pct_tasks_affected delta: Agentic Ceiling minus Conv. Baseline | positive = more tasks exposed under agentic AI",
        x_title="Delta (percentage points)",
        height=700, width=1100,
    )
    fig_delta.update_layout(
        xaxis=dict(showgrid=True, zeroline=True, zerolinecolor=COLORS["grid"], zerolinewidth=2),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        margin=dict(l=280, r=100, t=80, b=60),
        showlegend=False,
    )
    save_figure(fig_delta, results / "figures" / "agentic_vs_conv_delta.png")
    shutil.copy(results / "figures" / "agentic_vs_conv_delta.png", figs_dir / "agentic_vs_conv_delta.png")
    print("  agentic_vs_conv_delta.png")

    # Fig 4: Heatmap — major category x dataset (pct_tasks_affected)
    pct_cols = ["pct_conv_baseline", "pct_agentic_confirmed", "pct_mcp_only", "pct_agentic_ceiling"]
    col_labels = ["Conv. Baseline", "Agentic Confirmed", "MCP Only", "Agentic Ceiling"]

    # Sort rows by mean pct
    heatmap_df = major_wide.copy()
    heatmap_df["mean_pct"] = heatmap_df[pct_cols].mean(axis=1)
    heatmap_df = heatmap_df.sort_values("mean_pct", ascending=True)

    z_vals = heatmap_df[pct_cols].values
    y_cats = heatmap_df["category"].tolist()

    fig_heat = go.Figure(go.Heatmap(
        z=z_vals,
        x=col_labels,
        y=y_cats,
        colorscale=[[0, "#f0f4f8"], [0.5, COLORS["primary"]], [1.0, "#0d2b45"]],
        text=[[f"{v:.0f}%" for v in row_vals] for row_vals in z_vals],
        texttemplate="%{text}",
        textfont=dict(size=9, color="white", family=FONT_FAMILY),
        showscale=True,
        colorbar=dict(title="% Tasks Affected", tickfont=dict(size=10)),
        hovertemplate="%{y} | %{x}: %{z:.1f}%<extra></extra>",
    ))
    style_figure(
        fig_heat,
        "Sector Exposure by Dataset",
        subtitle="pct_tasks_affected per major category across 4 datasets",
        show_legend=False,
        height=700, width=1000,
    )
    fig_heat.update_layout(
        xaxis=dict(side="bottom", showgrid=False, showline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        margin=dict(l=300, r=80, t=80, b=80),
    )
    save_figure(fig_heat, results / "figures" / "sector_heatmap.png")
    shutil.copy(results / "figures" / "sector_heatmap.png", figs_dir / "sector_heatmap.png")
    print("  sector_heatmap.png")

    # ── 5. Print key stats ──────────────────────────────────────────────────
    print("\n-- Key stats --")
    top5_workers = major_wide.nlargest(5, "workers_agentic_ceiling")[["category", "workers_agentic_ceiling", "pct_agentic_ceiling"]]
    print("  Top 5 by workers (agentic ceiling):")
    for _, row in top5_workers.iterrows():
        print(f"    {row['category']}: {row['workers_agentic_ceiling']/1e6:.1f}M workers, {row['pct_agentic_ceiling']:.1f}%")

    print("\n  Top 5 delta (agentic gains over conv baseline):")
    for _, row in delta_df.head(5).iterrows():
        print(f"    {row['category']}: +{row['delta_pct']:.1f}pp")

    print("\n  Bottom 5 delta (agentic gains):")
    for _, row in delta_df.tail(5).iterrows():
        print(f"    {row['category']}: {row['delta_pct']:.1f}pp")

    print("\nsector_footprint: done.")


if __name__ == "__main__":
    main()
