"""
run.py -- Agentic Usage: Trends

How has agentic AI exposure grown over time?
Tracks the agentic ceiling, AEI API, MCP cumulative, and conv. baseline series.

Run from project root:
    venv/Scripts/python -m analysis.questions.agentic_usage.trends.run
"""
from __future__ import annotations

import warnings
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from analysis.config import ensure_results_dir, ANALYSIS_CONFIG_SERIES
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    CATEGORY_PALETTE,
    save_figure,
    save_csv,
    style_figure,
    generate_pdf,
)

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent

# Time series to compute
AEI_API_SERIES = ["AEI API 2025-08-11", "AEI API 2025-11-13", "AEI API 2026-02-12"]
MCP_SERIES = ["MCP Cumul. v1", "MCP Cumul. v2", "MCP Cumul. v3", "MCP Cumul. v4"]
AGENTIC_CEILING_SERIES = ANALYSIS_CONFIG_SERIES["agentic_ceiling"]
ALL_CONFIRMED_SERIES = ANALYSIS_CONFIG_SERIES["all_confirmed"]


def get_aggregate_totals(dataset_name: str) -> dict:
    """Get aggregate workers_affected and pct_of_employment for a single dataset."""
    from backend.compute import get_group_data
    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": "nat",
        "agg_level": "occupation",
        "sort_by": "Workers Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    if data is None:
        return {"dataset": dataset_name, "workers_affected": None, "pct_of_employment": None}
    df = data["df"]
    group_col = data["group_col"]
    # Sum workers and total employment from occupation level
    workers = df["workers_affected"].sum() if "workers_affected" in df.columns else None
    # pct_of_employment: workers_affected / total_employment (from dashboard)
    # We'll sum workers and total from df
    total = df["total_workers"].sum() if "total_workers" in df.columns else None
    pct = (workers / total * 100) if (workers and total and total > 0) else None
    return {
        "dataset": dataset_name,
        "workers_affected": workers,
        "total_workers": total,
        "pct_of_employment": pct,
    }


def get_major_data(dataset_name: str) -> pd.DataFrame:
    from backend.compute import get_group_data
    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": "nat",
        "agg_level": "major",
        "sort_by": "Workers Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    if data is None:
        return pd.DataFrame()
    group_col = data["group_col"]
    df = data["df"].rename(columns={group_col: "category"})
    return df[["category", "pct_tasks_affected", "workers_affected"]].copy()


def build_trend_df(series: list[str], series_name: str) -> pd.DataFrame:
    rows = []
    for ds in series:
        try:
            row = get_aggregate_totals(ds)
            row["series"] = series_name
            rows.append(row)
        except Exception as e:
            print(f"    WARNING: could not load {ds}: {e}")
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("trends: loading time series data...")

    # ── 1. Aggregate totals for each series ───────────────────────────────────
    print("  Agentic Ceiling series...")
    ceiling_df = build_trend_df(AGENTIC_CEILING_SERIES, "Agentic Ceiling")
    save_csv(ceiling_df, results / "agentic_ceiling_trend.csv")
    print(f"  agentic_ceiling_trend.csv: {len(ceiling_df)} points")

    print("  All Confirmed series...")
    all_conf_df = build_trend_df(ALL_CONFIRMED_SERIES, "Conv. Baseline")
    save_csv(all_conf_df, results / "all_confirmed_trend.csv")
    print(f"  all_confirmed_trend.csv: {len(all_conf_df)} points")

    print("  AEI API series...")
    aei_df = build_trend_df(AEI_API_SERIES, "Agentic (AEI API)")
    save_csv(aei_df, results / "aei_api_trend.csv")
    print(f"  aei_api_trend.csv: {len(aei_df)} points")

    print("  MCP Cumul. series...")
    mcp_df = build_trend_df(MCP_SERIES, "MCP Only")
    save_csv(mcp_df, results / "mcp_trend.csv")
    print(f"  mcp_trend.csv: {len(mcp_df)} points")

    # ── 2. Major-category growth: first vs. last of agentic ceiling series ────
    print("  Major-category first/last for agentic ceiling series...")
    try:
        first_ds = AGENTIC_CEILING_SERIES[0]
        last_ds = AGENTIC_CEILING_SERIES[-1]
        major_first = get_major_data(first_ds).rename(columns={"pct_tasks_affected": "pct_first", "workers_affected": "workers_first"})
        major_last = get_major_data(last_ds).rename(columns={"pct_tasks_affected": "pct_last", "workers_affected": "workers_last"})
        major_growth = major_first.merge(major_last[["category", "pct_last", "workers_last"]], on="category", how="outer")
        major_growth["pct_growth"] = major_growth["pct_last"] - major_growth["pct_first"]
        # % growth relative to first value
        major_growth["pct_growth_rel"] = (
            (major_growth["pct_last"] - major_growth["pct_first"]) / major_growth["pct_first"] * 100
        ).where(major_growth["pct_first"] > 0)
        major_growth["first_date"] = first_ds
        major_growth["last_date"] = last_ds
        save_csv(major_growth.sort_values("pct_growth", ascending=False), results / "major_growth_agentic.csv")
        print(f"  major_growth_agentic.csv saved: {len(major_growth)} categories")
    except Exception as e:
        print(f"  WARNING: could not compute major growth: {e}")
        major_growth = pd.DataFrame()

    # ── 3. Figures ─────────────────────────────────────────────────────────────
    print("  Building figures...")

    def workers_in_millions(df: pd.DataFrame, col: str = "workers_affected") -> list[float]:
        return [v / 1e6 if v is not None else None for v in df[col].tolist()]

    # Fig 1: Agentic Ceiling + Conv. Baseline trend — workers_affected over time
    fig1 = go.Figure()
    if not ceiling_df.empty and "workers_affected" in ceiling_df.columns:
        fig1.add_trace(go.Scatter(
            x=ceiling_df["dataset"].tolist(),
            y=workers_in_millions(ceiling_df),
            mode="lines+markers",
            name="Agentic Ceiling",
            line=dict(color=COLORS["primary"], width=3),
            marker=dict(size=7),
        ))
    if not all_conf_df.empty and "workers_affected" in all_conf_df.columns:
        fig1.add_trace(go.Scatter(
            x=all_conf_df["dataset"].tolist(),
            y=workers_in_millions(all_conf_df),
            mode="lines+markers",
            name="Conv. Baseline",
            line=dict(color=COLORS["muted"], width=3, dash="dot"),
            marker=dict(size=7),
        ))
    style_figure(
        fig1,
        "Agentic Ceiling and Conv. Baseline: Workers Affected Over Time",
        subtitle="Total workers in AI-exposed occupations | each point = one dataset version",
        y_title="Workers Affected (millions)",
        height=550, width=1100,
    )
    fig1.update_layout(
        xaxis=dict(showgrid=False, tickangle=-35, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True),
        margin=dict(b=140),
        legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
    )
    save_figure(fig1, results / "figures" / "agentic_ceiling_trend.png")
    shutil.copy(results / "figures" / "agentic_ceiling_trend.png", figs_dir / "agentic_ceiling_trend.png")
    print("  agentic_ceiling_trend.png")

    # Fig 2: AEI API series + MCP series — workers_affected
    fig2 = go.Figure()
    if not aei_df.empty and "workers_affected" in aei_df.columns:
        fig2.add_trace(go.Scatter(
            x=aei_df["dataset"].tolist(),
            y=workers_in_millions(aei_df),
            mode="lines+markers",
            name="Agentic (AEI API)",
            line=dict(color=COLORS["secondary"], width=3),
            marker=dict(size=9),
        ))
    if not mcp_df.empty and "workers_affected" in mcp_df.columns:
        fig2.add_trace(go.Scatter(
            x=mcp_df["dataset"].tolist(),
            y=workers_in_millions(mcp_df),
            mode="lines+markers",
            name="MCP Only",
            line=dict(color=CATEGORY_PALETTE[3], width=3),
            marker=dict(size=9),
        ))
    style_figure(
        fig2,
        "AEI API and MCP Growth Trends",
        subtitle="Workers affected over time | AEI API (3 points) and MCP Cumulative (v1-v4)",
        y_title="Workers Affected (millions)",
        height=550, width=1000,
    )
    fig2.update_layout(
        xaxis=dict(showgrid=False, tickangle=-30, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True),
        margin=dict(b=120),
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
    )
    save_figure(fig2, results / "figures" / "aei_api_mcp_trend.png")
    shutil.copy(results / "figures" / "aei_api_mcp_trend.png", figs_dir / "aei_api_mcp_trend.png")
    print("  aei_api_mcp_trend.png")

    # Fig 3: Sector growth by major category (agentic ceiling first vs. last)
    if not major_growth.empty and "pct_growth" in major_growth.columns:
        growth_plot = major_growth.dropna(subset=["pct_growth"]).sort_values("pct_growth", ascending=True)
        pos_color = COLORS["primary"]
        neg_color = COLORS["muted"]
        bar_colors = [pos_color if v >= 0 else neg_color for v in growth_plot["pct_growth"]]

        fig3 = go.Figure(go.Bar(
            x=growth_plot["pct_growth"].tolist(),
            y=growth_plot["category"].tolist(),
            orientation="h",
            marker=dict(color=bar_colors, line=dict(width=0)),
            text=[f"{v:+.1f}pp" for v in growth_plot["pct_growth"]],
            textposition="outside",
            textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
            cliponaxis=False,
        ))
        style_figure(
            fig3,
            "Sector Exposure Growth (Agentic Ceiling)",
            subtitle=f"pct_tasks_affected delta: {AGENTIC_CEILING_SERIES[-1]} minus {AGENTIC_CEILING_SERIES[0]} | by major category",
            x_title="Delta (percentage points)",
            height=700, width=1100,
            show_legend=False,
        )
        fig3.update_layout(
            xaxis=dict(showgrid=True, zeroline=True, zerolinecolor=COLORS["grid"], zerolinewidth=2),
            yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
            margin=dict(l=300, r=100, t=80, b=60),
        )
        save_figure(fig3, results / "figures" / "growth_rate_by_sector.png")
        shutil.copy(results / "figures" / "growth_rate_by_sector.png", figs_dir / "growth_rate_by_sector.png")
        print("  growth_rate_by_sector.png")

    # ── 4. Print key stats ──────────────────────────────────────────────────────
    print("\n-- Key stats --")
    if not ceiling_df.empty and "workers_affected" in ceiling_df.columns:
        print("  Agentic Ceiling trend (workers_affected):")
        for _, row in ceiling_df.iterrows():
            w = row["workers_affected"]
            pct = row.get("pct_of_employment")
            w_str = f"{w/1e6:.1f}M" if w is not None else "N/A"
            pct_str = f"{pct:.1f}%" if pct is not None else "N/A"
            print(f"    {row['dataset']}: {w_str} workers, {pct_str}")

    if not aei_df.empty and "workers_affected" in aei_df.columns:
        print("\n  AEI API trend:")
        for _, row in aei_df.iterrows():
            w = row["workers_affected"]
            w_str = f"{w/1e6:.1f}M" if w is not None else "N/A"
            print(f"    {row['dataset']}: {w_str}")

    if not mcp_df.empty and "workers_affected" in mcp_df.columns:
        print("\n  MCP trend:")
        for _, row in mcp_df.iterrows():
            w = row["workers_affected"]
            w_str = f"{w/1e6:.1f}M" if w is not None else "N/A"
            print(f"    {row['dataset']}: {w_str}")

    if not major_growth.empty:
        print("\n  Top 5 fastest-growing sectors (agentic ceiling):")
        for _, row in major_growth.dropna(subset=["pct_growth"]).nlargest(5, "pct_growth").iterrows():
            print(f"    {row['category']}: +{row['pct_growth']:.1f}pp")

    print("\ntrends: done.")


if __name__ == "__main__":
    main()
