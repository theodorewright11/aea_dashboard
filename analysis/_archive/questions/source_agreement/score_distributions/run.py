"""
run.py -- Source Agreement: Score Distributions

How do the four sources distribute their pct_tasks_affected scores across
all occupations? Where do they cluster, where do they spread?

Run from project root:
    venv/Scripts/python -m analysis.questions.source_agreement.score_distributions.run
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
    generate_pdf,
)

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent

SOURCES = {
    "human_conv": ("AEI Conv + Micro 2026-02-12", "Human Conv."),
    "aei_api":    ("AEI API 2026-02-12",           "Agentic (AEI API)"),
    "microsoft":  ("Microsoft",                    "Microsoft"),
    "mcp":        ("MCP Cumul. v4",                "MCP"),
}

SOURCE_COLORS = {
    "human_conv": COLORS["aei"],
    "aei_api":    COLORS["secondary"],
    "microsoft":  COLORS["microsoft"],
    "mcp":        CATEGORY_PALETTE[3],
}

ECO2025_SOURCES = ["human_conv", "microsoft", "mcp"]


def get_occ_data(dataset_name: str) -> pd.DataFrame:
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
    assert data is not None, f"No data for {dataset_name}"
    group_col = data["group_col"]
    df = data["df"].rename(columns={group_col: "category"})
    return df[["category", "pct_tasks_affected"]].copy()


def get_wa_data(dataset_name: str, level: str = "gwa") -> pd.DataFrame:
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


def assign_tier(pct: float) -> str:
    if pct < 20:
        return "<20"
    elif pct < 40:
        return "20-40"
    elif pct < 60:
        return "40-60"
    else:
        return ">=60"


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("score_distributions: loading occupation data...")

    # ── 1. Load occupation-level pct for all 4 sources ───────────────────────
    source_dfs: dict[str, pd.DataFrame] = {}
    for key, (ds_name, label) in SOURCES.items():
        print(f"  loading {label}...")
        df = get_occ_data(ds_name)
        source_dfs[key] = df

    # ── 2. Build wide merge on occupation name ────────────────────────────────
    wide = source_dfs["human_conv"].rename(columns={"pct_tasks_affected": "pct_human_conv"})
    for key in ["aei_api", "microsoft", "mcp"]:
        df2 = source_dfs[key].rename(columns={"pct_tasks_affected": f"pct_{key}"})
        wide = wide.merge(df2, on="category", how="outer")

    pct_cols = [f"pct_{k}" for k in SOURCES.keys()]
    wide["mean_pct"] = wide[pct_cols].mean(axis=1)
    wide["std_pct"] = wide[pct_cols].std(axis=1)

    save_csv(wide.sort_values("std_pct", ascending=False), results / "occ_cross_source.csv")
    print(f"  occ_cross_source.csv: {len(wide)} occupations")

    # ── 3. Top 20 highest / lowest variance ──────────────────────────────────
    wide_clean = wide.dropna(subset=pct_cols)
    top_var = wide_clean.nlargest(20, "std_pct")
    low_var = wide_clean.nsmallest(20, "std_pct")

    # ── 4. Tier counts ────────────────────────────────────────────────────────
    tier_rows = []
    for key, (ds_name, label) in SOURCES.items():
        col = f"pct_{key}"
        sub = wide[[col]].dropna()
        sub["tier"] = sub[col].apply(assign_tier)
        for tier, cnt in sub.groupby("tier").size().items():
            tier_rows.append({"source": label, "tier": tier, "count": int(cnt)})

    tier_df = pd.DataFrame(tier_rows)
    save_csv(tier_df, results / "tier_counts.csv")
    print("  tier_counts.csv saved")

    # ── 5. WA GWA distribution for eco_2025 sources ──────────────────────────
    print("  Loading GWA data for eco_2025 sources...")
    gwa_frames = []
    for key in ECO2025_SOURCES:
        ds_name = SOURCES[key][0]
        gdf = get_wa_data(ds_name, "gwa")
        if not gdf.empty and "pct_tasks_affected" in gdf.columns:
            gdf = gdf.rename(columns={"pct_tasks_affected": f"pct_{key}"})[["category", f"pct_{key}"]]
            gwa_frames.append(gdf)

    gwa_wide = pd.DataFrame()
    if gwa_frames:
        gwa_wide = gwa_frames[0]
        for df in gwa_frames[1:]:
            gwa_wide = gwa_wide.merge(df, on="category", how="outer")
        eco_pct_cols = [f"pct_{k}" for k in ECO2025_SOURCES]
        gwa_wide["mean_pct"] = gwa_wide[eco_pct_cols].mean(axis=1)
        gwa_wide["std_pct"] = gwa_wide[eco_pct_cols].std(axis=1)
        save_csv(gwa_wide, results / "wa_gwa_cross_source.csv")
        print(f"  wa_gwa_cross_source.csv: {len(gwa_wide)} GWAs")

    # ── 6. Figures ─────────────────────────────────────────────────────────────
    print("  Building figures...")

    # Fig 1: Distribution of pct_tasks_affected by source (overlaid histogram)
    fig_dist = go.Figure()
    for key, (ds_name, label) in SOURCES.items():
        col = f"pct_{key}"
        vals = wide[col].dropna().tolist()
        fig_dist.add_trace(go.Histogram(
            x=vals,
            name=label,
            marker_color=SOURCE_COLORS[key],
            opacity=0.6,
            xbins=dict(start=0, end=100, size=5),
            autobinx=False,
        ))
    style_figure(
        fig_dist,
        "Score Distribution by Source",
        subtitle="Distribution of pct_tasks_affected across 923 occupations | 5-point bins",
        x_title="% Tasks Affected",
        y_title="Number of Occupations",
        height=550, width=1000,
    )
    fig_dist.update_layout(barmode="overlay", xaxis=dict(showgrid=True))
    save_figure(fig_dist, results / "figures" / "pct_distribution_by_source.png")
    shutil.copy(results / "figures" / "pct_distribution_by_source.png", figs_dir / "pct_distribution_by_source.png")
    print("  pct_distribution_by_source.png")

    # Fig 2: Top 20 highest-variance occupations — dot plot
    def _build_dot_plot(var_df: pd.DataFrame, title: str, subtitle: str) -> go.Figure:
        var_df = var_df.sort_values("std_pct", ascending=True)
        fig = go.Figure()
        for key, (ds_name, label) in SOURCES.items():
            col = f"pct_{key}"
            fig.add_trace(go.Scatter(
                x=var_df[col].tolist(),
                y=var_df["category"].tolist(),
                mode="markers",
                name=label,
                marker=dict(color=SOURCE_COLORS[key], size=9, opacity=0.8),
            ))
        style_figure(
            fig, title,
            subtitle=subtitle,
            x_title="% Tasks Affected",
            height=700, width=1100,
        )
        fig.update_layout(
            xaxis=dict(showgrid=True, range=[0, 105]),
            yaxis=dict(showgrid=False, tickfont=dict(size=10)),
            margin=dict(l=280, r=60, t=80, b=60),
        )
        return fig

    fig_high_var = _build_dot_plot(
        top_var,
        "Top 20 Highest-Variance Occupations",
        "Occupations with most source disagreement | each dot = one source's pct_tasks_affected",
    )
    save_figure(fig_high_var, results / "figures" / "cross_source_variance_high.png")
    shutil.copy(results / "figures" / "cross_source_variance_high.png", figs_dir / "cross_source_variance_high.png")
    print("  cross_source_variance_high.png")

    fig_low_var = _build_dot_plot(
        low_var,
        "Top 20 Lowest-Variance Occupations",
        "Occupations with most source consensus | each dot = one source's pct_tasks_affected",
    )
    save_figure(fig_low_var, results / "figures" / "cross_source_variance_low.png")
    shutil.copy(results / "figures" / "cross_source_variance_low.png", figs_dir / "cross_source_variance_low.png")
    print("  cross_source_variance_low.png")

    # Fig 3: Tier distribution — grouped bar
    tier_order = ["<20", "20-40", "40-60", ">=60"]
    tier_colors_map = {
        "<20":   COLORS["muted"],
        "20-40": COLORS["secondary"],
        "40-60": COLORS["primary"],
        ">=60":  COLORS["positive"],
    }
    source_labels = [SOURCES[k][1] for k in SOURCES.keys()]

    fig_tiers = go.Figure()
    for tier in tier_order:
        counts = []
        for key in SOURCES.keys():
            label = SOURCES[key][1]
            row = tier_df[(tier_df["source"] == label) & (tier_df["tier"] == tier)]
            counts.append(int(row["count"].values[0]) if len(row) > 0 else 0)
        fig_tiers.add_trace(go.Bar(
            name=tier,
            x=source_labels,
            y=counts,
            marker_color=tier_colors_map[tier],
            text=counts,
            textposition="outside",
            textfont=dict(size=11, family=FONT_FAMILY),
        ))
    style_figure(
        fig_tiers,
        "Tier Distribution by Source",
        subtitle="Number of occupations per exposure tier | <20 / 20-40 / 40-60 / >=60%",
        y_title="Number of Occupations",
        height=550, width=900,
    )
    fig_tiers.update_layout(
        barmode="group",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True),
        bargap=0.2,
    )
    save_figure(fig_tiers, results / "figures" / "tier_distribution.png")
    shutil.copy(results / "figures" / "tier_distribution.png", figs_dir / "tier_distribution.png")
    print("  tier_distribution.png")

    # Fig 4: GWA distribution — overlaid histogram for eco_2025 sources
    if not gwa_wide.empty:
        fig_gwa = go.Figure()
        eco_pct_cols = [f"pct_{k}" for k in ECO2025_SOURCES]
        for key in ECO2025_SOURCES:
            col = f"pct_{key}"
            vals = gwa_wide[col].dropna().tolist()
            fig_gwa.add_trace(go.Histogram(
                x=vals,
                name=SOURCES[key][1],
                marker_color=SOURCE_COLORS[key],
                opacity=0.65,
                xbins=dict(start=0, end=100, size=5),
                autobinx=False,
            ))
        style_figure(
            fig_gwa,
            "GWA Score Distribution — eco_2025 Sources",
            subtitle="Distribution of pct_tasks_affected across General Work Activities | Human Conv., Microsoft, MCP",
            x_title="% Tasks Affected",
            y_title="Number of GWAs",
            height=500, width=950,
        )
        fig_gwa.update_layout(barmode="overlay", xaxis=dict(showgrid=True))
        save_figure(fig_gwa, results / "figures" / "wa_gwa_distribution.png")
        shutil.copy(results / "figures" / "wa_gwa_distribution.png", figs_dir / "wa_gwa_distribution.png")
        print("  wa_gwa_distribution.png")

    # ── 7. Print key stats ────────────────────────────────────────────────────
    print("\n-- Key stats --")
    for key, (ds_name, label) in SOURCES.items():
        col = f"pct_{key}"
        sub = wide[col].dropna()
        print(f"  {label}: mean={sub.mean():.1f}  median={sub.median():.1f}  std={sub.std():.1f}  "
              f">=60: {(sub >= 60).sum()}  <20: {(sub < 20).sum()}")

    print(f"\n  Top 5 highest-variance occs:")
    for _, row in top_var.head(5).iterrows():
        print(f"    {row['category']}: std={row['std_pct']:.1f}")

    print(f"\n  Top 5 lowest-variance occs:")
    for _, row in low_var.head(5).iterrows():
        print(f"    {row['category']}: std={row['std_pct']:.2f}")

    print("\nscore_distributions: done.")


if __name__ == "__main__":
    main()
