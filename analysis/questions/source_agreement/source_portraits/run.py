"""
run.py -- Source Agreement: Source Portraits

What does each data source uniquely contribute? Which occupations and work
activities does each source rate distinctively high compared to others?

Run from project root:
    venv/Scripts/python -m analysis.questions.source_agreement.source_portraits.run
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


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("source_portraits: loading occupation data...")

    # ── 1. Load all 4 sources at occupation level ─────────────────────────────
    source_dfs: dict[str, pd.DataFrame] = {}
    for key, (ds_name, label) in SOURCES.items():
        print(f"  loading {label}...")
        df = get_occ_data(ds_name)
        source_dfs[key] = df

    # Build wide df
    wide = source_dfs["human_conv"].rename(columns={"pct_tasks_affected": "pct_human_conv"})
    for key in ["aei_api", "microsoft", "mcp"]:
        df2 = source_dfs[key].rename(columns={"pct_tasks_affected": f"pct_{key}"})
        wide = wide.merge(df2, on="category", how="outer")

    pct_cols = [f"pct_{k}" for k in SOURCES.keys()]
    wide_clean = wide.dropna(subset=pct_cols).copy()

    # ── 2. Distinctiveness: z-score for each source vs. mean of other 3 ───────
    for key in SOURCES.keys():
        this_col = f"pct_{key}"
        other_cols = [f"pct_{k}" for k in SOURCES.keys() if k != key]
        other_mean = wide_clean[other_cols].mean(axis=1)
        other_std = wide_clean[other_cols].std(axis=1)
        wide_clean[f"z_{key}"] = (wide_clean[this_col] - other_mean) / other_std.replace(0, np.nan)

    # Save full CSV
    save_csv(wide_clean.sort_values("pct_human_conv", ascending=False), results / "occ_all_sources.csv")
    print("  occ_all_sources.csv saved")

    # ── 3. Source summary stats ────────────────────────────────────────────────
    summary_rows = []
    for key, (ds_name, label) in SOURCES.items():
        col = f"pct_{key}"
        vals = wide_clean[col].dropna()
        summary_rows.append({
            "source": label,
            "median_pct": round(float(vals.median()), 2),
            "mean_pct": round(float(vals.mean()), 2),
            "max_pct": round(float(vals.max()), 2),
            "pct_high_tier": round(float((vals >= 60).mean() * 100), 2),
            "pct_low_tier": round(float((vals < 20).mean() * 100), 2),
        })
    summary_df = pd.DataFrame(summary_rows)
    save_csv(summary_df, results / "source_summary.csv")
    print("  source_summary.csv saved")

    # ── 4. WA GWA portraits for eco_2025 sources ──────────────────────────────
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
        eco_cols = [f"pct_{k}" for k in ECO2025_SOURCES]
        gwa_wide["mean_pct"] = gwa_wide[eco_cols].mean(axis=1)
        save_csv(gwa_wide, results / "wa_gwa_portraits.csv")
        print(f"  wa_gwa_portraits.csv: {len(gwa_wide)} GWAs")

    # ── 5. Figures ─────────────────────────────────────────────────────────────
    print("  Building figures...")

    def _build_distinctive_fig(key: str, top15: pd.DataFrame) -> go.Figure:
        """Horizontal bar of distinctiveness: this source's pct vs other sources mean."""
        label = SOURCES[key][1]
        color = SOURCE_COLORS[key]
        this_col = f"pct_{key}"
        other_cols = [f"pct_{k}" for k in SOURCES.keys() if k != key]

        plot_df = top15.sort_values(this_col, ascending=True).copy()
        plot_df["others_mean"] = plot_df[other_cols].mean(axis=1)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=plot_df[this_col].tolist(),
            y=plot_df["category"].tolist(),
            orientation="h",
            name=label,
            marker=dict(color=color, opacity=0.85, line=dict(width=0)),
            text=[f"{v:.0f}%" for v in plot_df[this_col]],
            textposition="outside",
            textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
            cliponaxis=False,
        ))
        fig.add_trace(go.Scatter(
            x=plot_df["others_mean"].tolist(),
            y=plot_df["category"].tolist(),
            mode="markers",
            name="Other sources mean",
            marker=dict(color=COLORS["muted"], size=10, symbol="diamond", opacity=0.8),
        ))
        style_figure(
            fig,
            f"Distinctively {label} Occupations (Top 15)",
            subtitle=f"Occupations rated highest by {label} relative to other 3 sources | bar = this source | diamond = others avg",
            x_title="% Tasks Affected",
            height=650, width=1100,
        )
        fig.update_layout(
            xaxis=dict(showgrid=True, range=[0, 115]),
            yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
            margin=dict(l=280, r=80, t=80, b=60),
            legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
        )
        return fig

    # Fig 1-4: Distinctive occupations per source
    for key in SOURCES.keys():
        z_col = f"z_{key}"
        top15 = wide_clean.nlargest(15, z_col)
        fig = _build_distinctive_fig(key, top15)
        fname = f"distinctive_{key}.png"
        save_figure(fig, results / "figures" / fname)
        shutil.copy(results / "figures" / fname, figs_dir / fname)
        print(f"  {fname}")

    # Fig 5: Source summary stats (median and mean per source)
    source_labels = summary_df["source"].tolist()
    fig_summary = go.Figure()
    fig_summary.add_trace(go.Bar(
        name="Median",
        x=source_labels,
        y=summary_df["median_pct"].tolist(),
        marker_color=COLORS["primary"],
        text=[f"{v:.1f}%" for v in summary_df["median_pct"]],
        textposition="outside",
        textfont=dict(size=11, family=FONT_FAMILY),
    ))
    fig_summary.add_trace(go.Bar(
        name="Mean",
        x=source_labels,
        y=summary_df["mean_pct"].tolist(),
        marker_color=COLORS["secondary"],
        text=[f"{v:.1f}%" for v in summary_df["mean_pct"]],
        textposition="outside",
        textfont=dict(size=11, family=FONT_FAMILY),
    ))
    style_figure(
        fig_summary,
        "Source Summary Statistics",
        subtitle="Median and mean pct_tasks_affected per source | occupation level",
        y_title="% Tasks Affected",
        height=500, width=850,
    )
    fig_summary.update_layout(
        barmode="group",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True),
        bargap=0.2,
    )
    save_figure(fig_summary, results / "figures" / "source_summary_stats.png")
    shutil.copy(results / "figures" / "source_summary_stats.png", figs_dir / "source_summary_stats.png")
    print("  source_summary_stats.png")

    # Fig 6: GWA portraits — top 10 GWAs per eco_2025 source (grouped bar)
    if not gwa_wide.empty:
        eco_cols = [f"pct_{k}" for k in ECO2025_SOURCES]
        top10_gwa = gwa_wide.nlargest(15, "mean_pct").sort_values("mean_pct", ascending=True)

        fig_gwa = go.Figure()
        for key in ECO2025_SOURCES:
            col = f"pct_{key}"
            fig_gwa.add_trace(go.Bar(
                x=top10_gwa[col].tolist(),
                y=top10_gwa["category"].tolist(),
                orientation="h",
                name=SOURCES[key][1],
                marker=dict(color=SOURCE_COLORS[key], opacity=0.85),
            ))
        style_figure(
            fig_gwa,
            "Top GWAs by Source — eco_2025 Sources",
            subtitle="Top 15 GWAs by mean pct_tasks_affected | Human Conv., Microsoft, MCP | eco_2025 baseline",
            x_title="% Tasks Affected",
            height=650, width=1100,
        )
        fig_gwa.update_layout(
            barmode="group",
            xaxis=dict(showgrid=True),
            yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
            margin=dict(l=280, r=80, t=80, b=80),
            legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
        )
        save_figure(fig_gwa, results / "figures" / "wa_gwa_portraits.png")
        shutil.copy(results / "figures" / "wa_gwa_portraits.png", figs_dir / "wa_gwa_portraits.png")
        print("  wa_gwa_portraits.png")

    # ── 6. Print key stats ─────────────────────────────────────────────────────
    print("\n-- Key stats --")
    print("  Summary stats:")
    for _, row in summary_df.iterrows():
        print(f"    {row['source']}: median={row['median_pct']:.1f}%  mean={row['mean_pct']:.1f}%  "
              f"high_tier={row['pct_high_tier']:.1f}%  low_tier={row['pct_low_tier']:.1f}%")

    print("\n  Top 5 distinctive per source:")
    for key in SOURCES.keys():
        z_col = f"z_{key}"
        top5 = wide_clean.nlargest(5, z_col)
        label = SOURCES[key][1]
        print(f"    {label}:")
        for _, row in top5.iterrows():
            print(f"      {row['category']}: z={row[z_col]:.2f}, pct={row[f'pct_{key}']:.1f}%")

    print("\nsource_portraits: done.")


if __name__ == "__main__":
    main()
