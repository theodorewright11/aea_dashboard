"""
run.py -- Agentic Usage: Work Activities

What kinds of work are most affected under agentic AI?
Compares IWA and GWA-level exposure across eco_2025 and eco_2015 sources.

Run from project root:
    venv/Scripts/python -m analysis.questions.agentic_usage.work_activities.run
"""
from __future__ import annotations

import warnings
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from analysis.config import ensure_results_dir
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

# Part A: eco_2025 sources
ECO2025 = {
    "mcp_ceiling":    ("MCP + API 2026-02-18",         "Agentic Ceiling"),
    "mcp_only":       ("MCP Cumul. v4",                "MCP Only"),
    "conv_baseline":  ("AEI Both + Micro 2026-02-12",  "Conv. Baseline"),
}

ECO2025_COLORS = {
    "mcp_ceiling":   COLORS["primary"],
    "mcp_only":      CATEGORY_PALETTE[3],
    "conv_baseline": COLORS["muted"],
}

# Part B: eco_2015 source
ECO2015 = {
    "aei_api": ("AEI API 2026-02-12", "Agentic (AEI API)"),
}


def get_wa_data(dataset_name: str, level: str = "iwa") -> pd.DataFrame:
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


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("work_activities: loading eco_2025 IWA data...")

    # ── Part A: eco_2025 ─────────────────────────────────────────────────────

    # Load IWA for all 3 eco_2025 sources
    iwa_frames: dict[str, pd.DataFrame] = {}
    for key, (ds_name, label) in ECO2025.items():
        print(f"  IWA: {label}...")
        idf = get_wa_data(ds_name, "iwa")
        if not idf.empty and "pct_tasks_affected" in idf.columns:
            iwa_frames[key] = idf.rename(columns={"pct_tasks_affected": f"pct_{key}"})[["category", f"pct_{key}"]]

    # Wide IWA table (eco_2025)
    iwa_wide = pd.DataFrame()
    if iwa_frames:
        iwa_wide = list(iwa_frames.values())[0]
        for df in list(iwa_frames.values())[1:]:
            iwa_wide = iwa_wide.merge(df, on="category", how="outer")
        save_csv(iwa_wide.sort_values("pct_mcp_ceiling", ascending=False), results / "iwa_eco2025.csv")
        print(f"  iwa_eco2025.csv: {len(iwa_wide)} IWAs")

    # Load GWA for all 3 eco_2025 sources
    gwa_frames: dict[str, pd.DataFrame] = {}
    for key, (ds_name, label) in ECO2025.items():
        print(f"  GWA: {label}...")
        gdf = get_wa_data(ds_name, "gwa")
        if not gdf.empty and "pct_tasks_affected" in gdf.columns:
            gwa_frames[key] = gdf.rename(columns={"pct_tasks_affected": f"pct_{key}"})[["category", f"pct_{key}"]]

    gwa_wide = pd.DataFrame()
    if gwa_frames:
        gwa_wide = list(gwa_frames.values())[0]
        for df in list(gwa_frames.values())[1:]:
            gwa_wide = gwa_wide.merge(df, on="category", how="outer")
        save_csv(gwa_wide.sort_values("pct_mcp_ceiling", ascending=False), results / "gwa_eco2025.csv")
        print(f"  gwa_eco2025.csv: {len(gwa_wide)} GWAs")

    # Delta: agentic ceiling - conv_baseline at IWA level
    if not iwa_wide.empty and "pct_mcp_ceiling" in iwa_wide.columns and "pct_conv_baseline" in iwa_wide.columns:
        delta_df = iwa_wide[["category", "pct_mcp_ceiling", "pct_conv_baseline"]].copy()
        delta_df["delta"] = delta_df["pct_mcp_ceiling"] - delta_df["pct_conv_baseline"]
        delta_df = delta_df.dropna(subset=["delta"]).sort_values("delta", ascending=False)
        save_csv(delta_df, results / "iwa_delta.csv")
        print(f"  iwa_delta.csv saved")
    else:
        delta_df = pd.DataFrame()

    # ── Part B: eco_2015 (AEI API) ────────────────────────────────────────────
    print("  Loading eco_2015 IWA data (AEI API)...")
    aei_iwa_df = pd.DataFrame()
    for key, (ds_name, label) in ECO2015.items():
        idf = get_wa_data(ds_name, "iwa")
        if not idf.empty and "pct_tasks_affected" in idf.columns:
            aei_iwa_df = idf.rename(columns={"pct_tasks_affected": "pct_aei_api"})
            aei_iwa_df = aei_iwa_df[["category", "pct_aei_api"]].copy()
            save_csv(aei_iwa_df.sort_values("pct_aei_api", ascending=False), results / "iwa_eco2015_aei_api.csv")
            print(f"  iwa_eco2015_aei_api.csv: {len(aei_iwa_df)} IWAs")

    # ── Figures ───────────────────────────────────────────────────────────────
    print("  Building figures...")

    # Fig 1: Top 20 IWAs by pct (Agentic Ceiling, eco_2025)
    if not iwa_wide.empty and "pct_mcp_ceiling" in iwa_wide.columns:
        top20_ceiling = iwa_wide.nlargest(20, "pct_mcp_ceiling").sort_values("pct_mcp_ceiling", ascending=False)
        fig1 = make_horizontal_bar(
            top20_ceiling,
            category_col="category",
            value_col="pct_mcp_ceiling",
            title="Top 20 IWAs by % Tasks Affected — Agentic Ceiling",
            subtitle="Intermediate Work Activities | Agentic Ceiling (MCP + API 2026-02-18) | eco_2025 baseline",
            x_title="% Tasks Affected",
            color=COLORS["primary"],
            value_format="%.1f%%",
            height=700, width=1200,
        )
        save_figure(fig1, results / "figures" / "top_iwas_agentic_ceiling.png")
        shutil.copy(results / "figures" / "top_iwas_agentic_ceiling.png", figs_dir / "top_iwas_agentic_ceiling.png")
        print("  top_iwas_agentic_ceiling.png")

    # Fig 2: Top 20 IWA delta (ceiling - conv baseline)
    if not delta_df.empty:
        top20_delta = delta_df.head(20).sort_values("delta", ascending=False)
        fig2 = make_horizontal_bar(
            top20_delta,
            category_col="category",
            value_col="delta",
            title="Top 20 IWAs Gaining Most from Agentic AI",
            subtitle="Delta: Agentic Ceiling pct - Conv. Baseline pct | eco_2025 sources | positive = gained exposure under agentic",
            x_title="Delta (percentage points)",
            color=COLORS["primary"],
            value_format="%+.1f%%",
            height=700, width=1200,
        )
        save_figure(fig2, results / "figures" / "iwa_delta_agentic_vs_conv.png")
        shutil.copy(results / "figures" / "iwa_delta_agentic_vs_conv.png", figs_dir / "iwa_delta_agentic_vs_conv.png")
        print("  iwa_delta_agentic_vs_conv.png")

    # Fig 3: GWA comparison — 3 eco_2025 sources side by side
    if not gwa_wide.empty:
        gwa_plot = gwa_wide.copy()
        if "pct_mcp_ceiling" in gwa_plot.columns:
            gwa_plot = gwa_plot.sort_values("pct_mcp_ceiling", ascending=True)
        categories = gwa_plot["category"].tolist()

        fig3 = go.Figure()
        for key, (ds_name, label) in ECO2025.items():
            col = f"pct_{key}"
            if col in gwa_plot.columns:
                fig3.add_trace(go.Bar(
                    x=gwa_plot[col].tolist(),
                    y=categories,
                    orientation="h",
                    name=label,
                    marker=dict(color=ECO2025_COLORS[key], opacity=0.85),
                ))

        style_figure(
            fig3,
            "GWA Comparison — eco_2025 Sources",
            subtitle="pct_tasks_affected at General Work Activity level | Agentic Ceiling, MCP Only, Conv. Baseline",
            x_title="% Tasks Affected",
            height=700, width=1200,
        )
        fig3.update_layout(
            barmode="group",
            xaxis=dict(showgrid=True),
            yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
            margin=dict(l=260, r=80, t=80, b=80),
            legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
        )
        save_figure(fig3, results / "figures" / "gwa_comparison_eco2025.png")
        shutil.copy(results / "figures" / "gwa_comparison_eco2025.png", figs_dir / "gwa_comparison_eco2025.png")
        print("  gwa_comparison_eco2025.png")

    # Fig 4: Top 20 IWAs for AEI API (eco_2015)
    if not aei_iwa_df.empty:
        top20_aei = aei_iwa_df.nlargest(20, "pct_aei_api").sort_values("pct_aei_api", ascending=False)
        fig4 = make_horizontal_bar(
            top20_aei,
            category_col="category",
            value_col="pct_aei_api",
            title="Top 20 IWAs — Agentic (AEI API) [eco_2015 baseline]",
            subtitle="AEI API 2026-02-12 | eco_2015 O*NET baseline | note: not directly comparable to eco_2025 sources",
            x_title="% Tasks Affected",
            color=COLORS["secondary"],
            value_format="%.1f%%",
            height=700, width=1200,
        )
        save_figure(fig4, results / "figures" / "top_iwas_aei_api.png")
        shutil.copy(results / "figures" / "top_iwas_aei_api.png", figs_dir / "top_iwas_aei_api.png")
        print("  top_iwas_aei_api.png")

    # ── Print key stats ────────────────────────────────────────────────────────
    print("\n-- Key stats --")
    if not iwa_wide.empty and "pct_mcp_ceiling" in iwa_wide.columns:
        top5_ceiling = iwa_wide.nlargest(5, "pct_mcp_ceiling")
        print("  Top 5 IWAs (Agentic Ceiling):")
        for _, row in top5_ceiling.iterrows():
            print(f"    {row['category']}: {row['pct_mcp_ceiling']:.1f}%")

    if not delta_df.empty:
        print("\n  Top 5 IWA gainers (ceiling - conv):")
        for _, row in delta_df.head(5).iterrows():
            print(f"    {row['category']}: +{row['delta']:.1f}pp")

    if not aei_iwa_df.empty:
        top5_aei = aei_iwa_df.nlargest(5, "pct_aei_api")
        print("\n  Top 5 IWAs (AEI API eco_2015):")
        for _, row in top5_aei.iterrows():
            print(f"    {row['category']}: {row['pct_aei_api']:.1f}%")

    print("\nwork_activities: done.")


if __name__ == "__main__":
    main()
