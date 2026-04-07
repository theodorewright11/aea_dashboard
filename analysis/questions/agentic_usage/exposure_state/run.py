"""
run.py — Agentic Usage: Exposure State

What is the current state of agentic AI exposure — headline numbers, distribution,
and how far above conversational usage does it reach?

Datasets:
  - AEI API 2026-02-12       → Agentic Confirmed (is_aei=True, aei_group)
  - MCP Cumul. v4            → MCP Only (is_aei=False, mcp_group)
  - MCP + API 2026-02-18     → Agentic Ceiling (is_aei=False, mcp_group)
  - AEI Both + Micro 2026-02-12 → Conv. Baseline (is_aei=False, mcp_group)

Produces:
  results/aggregate_totals.csv
  results/tier_counts.csv
  results/occ_all_agentic.csv
  results/figures/aggregate_totals.png
  results/figures/tier_distribution.png
  results/figures/agentic_vs_conversational_scatter.png
  results/figures/floor_ceiling_range.png

Run from project root:
    venv/Scripts/python -m analysis.questions.agentic_usage.exposure_state.run
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from analysis.config import ensure_results_dir
from analysis.utils import (
    CATEGORY_PALETTE,
    COLORS,
    FONT_FAMILY,
    format_workers,
    format_wages,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent

# Dataset definitions
DATASETS = {
    "agentic_confirmed": "AEI API 2026-02-12",
    "mcp_only":          "MCP Cumul. v4",
    "agentic_ceiling":   "MCP + API 2026-02-18",
    "conv_baseline":     "AEI Both + Micro 2026-02-12",
}
LABELS = {
    "agentic_confirmed": "Agentic Confirmed",
    "mcp_only":          "MCP Only",
    "agentic_ceiling":   "Agentic Ceiling",
    "conv_baseline":     "Conv. Baseline",
}
DATASET_COLORS = {
    "agentic_confirmed": COLORS["secondary"],
    "mcp_only":          COLORS["mcp"],
    "agentic_ceiling":   COLORS["primary"],
    "conv_baseline":     COLORS["muted"],
}

TIERS = [
    ("<20%",       0,  20,  "Low"),
    ("20-40%",    20,  40,  "Restructuring"),
    ("40-60%",    40,  60,  "Moderate"),
    (">=60%",     60, 999,  "High"),
]


# ── Data helpers ───────────────────────────────────────────────────────────────

def get_occ_data(dataset_name: str) -> pd.DataFrame:
    """Return occupation-level breakdown for a single dataset."""
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
    df = data["df"].rename(columns={"title_current": "category"})
    return df


def get_major_data(dataset_name: str) -> pd.DataFrame:
    """Return major-category breakdown for a single dataset."""
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
    assert data is not None, f"No major data for {dataset_name}"
    df = data["df"].rename(columns={"major_occ_category": "category"})
    return df


def compute_tiers(occ_df: pd.DataFrame) -> list[dict]:
    """Count occupations and workers in each exposure tier."""
    rows = []
    for label, lo, hi, tier_name in TIERS:
        mask = (occ_df["pct_tasks_affected"] >= lo) & (occ_df["pct_tasks_affected"] < hi)
        subset = occ_df[mask]
        rows.append({
            "tier_label": label,
            "tier_name": tier_name,
            "n_occs": len(subset),
            "workers": subset["workers_affected"].sum(),
        })
    return rows


# ── Figure builders ────────────────────────────────────────────────────────────

def _build_aggregate_bars(totals_df: pd.DataFrame) -> go.Figure:
    """Grouped bars: workers (M) and pct_of_employment for all 4 configs."""
    labels = totals_df["label"].tolist()
    workers_m = [w / 1e6 for w in totals_df["workers_affected"]]
    pct_emp = totals_df["pct_of_employment"].tolist()
    bar_colors = [DATASET_COLORS[k] for k in totals_df["key"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Workers Affected (M)",
        x=labels,
        y=workers_m,
        marker_color=bar_colors,
        text=[f"{w:.1f}M" for w in workers_m],
        textposition="outside",
        textfont=dict(size=12, color=COLORS["neutral"], family=FONT_FAMILY),
        yaxis="y1",
        opacity=0.9,
    ))
    fig.add_trace(go.Bar(
        name="% of Employment",
        x=labels,
        y=pct_emp,
        marker_color=bar_colors,
        text=[f"{p:.1f}%" for p in pct_emp],
        textposition="outside",
        textfont=dict(size=12, color=COLORS["neutral"], family=FONT_FAMILY),
        yaxis="y2",
        opacity=0.5,
        marker_pattern_shape="x",
    ))
    fig.update_layout(
        barmode="group",
        yaxis=dict(title="Workers Affected (millions)", showgrid=True, gridcolor=COLORS["grid"]),
        yaxis2=dict(title="% of Total Employment", overlaying="y", side="right", showgrid=False),
        bargap=0.25,
    )
    style_figure(
        fig,
        "Agentic AI Exposure — Aggregate Totals",
        subtitle="Occupation-level workers summed | National | freq | auto-aug ON",
        height=580, width=1100,
    )
    return fig


def _build_tier_distribution(tier_data: dict[str, list[dict]]) -> go.Figure:
    """Grouped bars: occupation counts in each tier per config."""
    tier_labels = [t[0] for t in TIERS]
    tier_colors = [COLORS["muted"], COLORS["mcp"], COLORS["primary"], COLORS["accent"]]

    fig = go.Figure()
    for i, tier_lbl in enumerate(tier_labels):
        n_occs_vals = []
        config_labels = []
        for key, label in LABELS.items():
            tiers_for_config = tier_data[key]
            row = next((r for r in tiers_for_config if r["tier_label"] == tier_lbl), None)
            n_occs_vals.append(row["n_occs"] if row else 0)
            config_labels.append(label)
        fig.add_trace(go.Bar(
            name=tier_lbl,
            x=config_labels,
            y=n_occs_vals,
            marker_color=tier_colors[i],
            text=[str(n) for n in n_occs_vals],
            textposition="outside",
            textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        ))

    fig.update_layout(barmode="group", bargap=0.2)
    style_figure(
        fig,
        "Occupation Tier Distribution by Agentic Config",
        subtitle="# occupations in each exposure tier (<20%, 20–40%, 40–60%, ≥60% tasks affected)",
        y_title="Number of Occupations",
        height=580, width=1100,
    )
    return fig


def _build_floor_ceiling_dumbbell(confirmed_major: pd.DataFrame, ceiling_major: pd.DataFrame) -> go.Figure:
    """Dumbbell: AEI API confirmed vs MCP+API ceiling per major category."""
    merged = confirmed_major[["category", "pct_tasks_affected"]].merge(
        ceiling_major[["category", "pct_tasks_affected"]].rename(columns={"pct_tasks_affected": "ceiling_pct"}),
        on="category",
        how="inner",
    ).sort_values("pct_tasks_affected", ascending=True)

    fig = go.Figure()
    for _, row in merged.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["pct_tasks_affected"], row["ceiling_pct"]],
            y=[row["category"], row["category"]],
            mode="lines",
            line=dict(color=COLORS["grid"], width=2),
            showlegend=False,
        ))
    fig.add_trace(go.Scatter(
        x=merged["pct_tasks_affected"],
        y=merged["category"],
        mode="markers",
        name="Agentic Confirmed (AEI API)",
        marker=dict(color=COLORS["secondary"], size=10, symbol="circle"),
    ))
    fig.add_trace(go.Scatter(
        x=merged["ceiling_pct"],
        y=merged["category"],
        mode="markers",
        name="Agentic Ceiling (MCP+API)",
        marker=dict(color=COLORS["primary"], size=10, symbol="diamond"),
    ))
    style_figure(
        fig,
        "Agentic Exposure Range by Sector — Confirmed vs Ceiling",
        subtitle="Confirmed = AEI API 2026-02-12 | Ceiling = MCP + API 2026-02-18 | % tasks affected",
        x_title="% Tasks Affected",
        height=700, width=1200,
    )
    fig.update_layout(
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=11)),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
    )
    return fig


def _build_agentic_vs_conv_scatter(agentic_major: pd.DataFrame, conv_major: pd.DataFrame) -> go.Figure:
    """Scatter: x=conv_baseline pct, y=agentic_ceiling pct per major category."""
    merged = conv_major[["category", "pct_tasks_affected"]].rename(
        columns={"pct_tasks_affected": "conv_pct"}
    ).merge(
        agentic_major[["category", "pct_tasks_affected"]].rename(
            columns={"pct_tasks_affected": "agentic_pct"}
        ),
        on="category",
        how="inner",
    )

    fig = go.Figure()
    colors_palette = CATEGORY_PALETTE
    for i, (_, row) in enumerate(merged.iterrows()):
        fig.add_trace(go.Scatter(
            x=[row["conv_pct"]],
            y=[row["agentic_pct"]],
            mode="markers+text",
            text=[row["category"]],
            textposition="top center",
            textfont=dict(size=9, color=COLORS["neutral"]),
            marker=dict(color=colors_palette[i % len(colors_palette)], size=12),
            name=row["category"],
            showlegend=False,
        ))

    # Diagonal reference
    max_val = max(merged["conv_pct"].max(), merged["agentic_pct"].max()) + 5
    fig.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val],
        mode="lines",
        line=dict(color=COLORS["muted"], dash="dot", width=1),
        showlegend=False,
    ))

    style_figure(
        fig,
        "Agentic Ceiling vs Conv. Baseline — Major Category Scatter",
        subtitle="X = Conv. Baseline (AEI Both + Micro) | Y = Agentic Ceiling (MCP + API) | % tasks affected",
        x_title="Conv. Baseline % Tasks Affected",
        y_title="Agentic Ceiling % Tasks Affected",
        show_legend=False,
        height=700, width=950,
    )
    return fig


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("exposure_state: loading data...")

    from backend.compute import get_explorer_occupations
    all_occs = get_explorer_occupations()
    total_emp = sum(o.get("emp") or 0 for o in all_occs)
    print(f"  Total national employment: {total_emp:,.0f}")

    # ── 1. Load occupation-level and major-category data ──────────────────────
    occ_data: dict[str, pd.DataFrame] = {}
    major_data: dict[str, pd.DataFrame] = {}
    totals_rows: list[dict] = []

    for key, ds_name in DATASETS.items():
        label = LABELS[key]
        print(f"  {label}...")
        occ_df = get_occ_data(ds_name)
        occ_df["config_key"] = key
        occ_df["config_label"] = label
        occ_data[key] = occ_df

        maj_df = get_major_data(ds_name)
        maj_df["config_key"] = key
        maj_df["config_label"] = label
        major_data[key] = maj_df

        workers = occ_df["workers_affected"].sum()
        wages = occ_df["wages_affected"].sum()
        pct_emp = (workers / total_emp * 100) if total_emp > 0 else np.nan
        totals_rows.append({
            "key": key,
            "label": label,
            "workers_affected": workers,
            "wages_affected": wages,
            "pct_of_employment": pct_emp,
        })

    totals_df = pd.DataFrame(totals_rows)

    # ── 2. Tier distributions ─────────────────────────────────────────────────
    tier_data: dict[str, list[dict]] = {}
    tier_rows: list[dict] = []
    for key in DATASETS:
        occ_df = occ_data[key]
        tiers = compute_tiers(occ_df)
        tier_data[key] = tiers
        for t in tiers:
            tier_rows.append({
                "config_key": key,
                "config_label": LABELS[key],
                **t,
            })
    tier_df = pd.DataFrame(tier_rows)

    # ── 3. CSVs ───────────────────────────────────────────────────────────────
    save_csv(totals_df.drop(columns=["key"]), results / "aggregate_totals.csv")
    save_csv(tier_df, results / "tier_counts.csv")

    # All occ data combined
    all_occ_combined = pd.concat([
        occ_data[k][["category", "config_key", "config_label", "pct_tasks_affected",
                     "workers_affected", "wages_affected"]]
        for k in DATASETS
    ], ignore_index=True)
    save_csv(all_occ_combined, results / "occ_all_agentic.csv")
    print("  CSVs saved.")

    # ── 4. Figures ─────────────────────────────────────────────────────────────

    # 4a. Aggregate totals
    fig_agg = _build_aggregate_bars(totals_df)
    save_figure(fig_agg, results / "figures" / "aggregate_totals.png")
    shutil.copy(results / "figures" / "aggregate_totals.png", figs_dir / "aggregate_totals.png")
    print("  aggregate_totals.png")

    # 4b. Tier distribution
    fig_tiers = _build_tier_distribution(tier_data)
    save_figure(fig_tiers, results / "figures" / "tier_distribution.png")
    shutil.copy(results / "figures" / "tier_distribution.png", figs_dir / "tier_distribution.png")
    print("  tier_distribution.png")

    # 4c. Floor-ceiling dumbbell (AEI API vs MCP+API at major level)
    fig_db = _build_floor_ceiling_dumbbell(
        major_data["agentic_confirmed"], major_data["agentic_ceiling"]
    )
    save_figure(fig_db, results / "figures" / "floor_ceiling_range.png")
    shutil.copy(results / "figures" / "floor_ceiling_range.png", figs_dir / "floor_ceiling_range.png")
    print("  floor_ceiling_range.png")

    # 4d. Agentic ceiling vs conv scatter (major category)
    fig_scatter = _build_agentic_vs_conv_scatter(
        major_data["agentic_ceiling"], major_data["conv_baseline"]
    )
    save_figure(fig_scatter, results / "figures" / "agentic_vs_conversational_scatter.png")
    shutil.copy(
        results / "figures" / "agentic_vs_conversational_scatter.png",
        figs_dir / "agentic_vs_conversational_scatter.png",
    )
    print("  agentic_vs_conversational_scatter.png")

    # ── 5. Summary ─────────────────────────────────────────────────────────────
    print("\n-- Aggregate Totals --")
    for _, row in totals_df.iterrows():
        print(f"  {row['label']:30s}: {format_workers(row['workers_affected'])} workers, "
              f"{format_wages(row['wages_affected'])} wages, "
              f"{row['pct_of_employment']:.1f}% of employment")

    print("\n-- Tier Distributions --")
    for key in DATASETS:
        print(f"  {LABELS[key]}:")
        for t in tier_data[key]:
            print(f"    {t['tier_label']:8s}: {t['n_occs']:4d} occs, {format_workers(t['workers'])} workers")

    # ── 6. PDF ────────────────────────────────────────────────────────────────
    report_md = HERE / "exposure_state_report.md"
    if report_md.exists():
        generate_pdf(report_md, results / "exposure_state_report.pdf")

    print("\nexposure_state: done.")


if __name__ == "__main__":
    main()
