"""
run.py — Economic Footprint: Sector Footprint

Which sectors lead on workers, wages, and % tasks affected?

Runs the full compute pipeline across all five ANALYSIS_CONFIGS and produces:
  - Aggregate national totals (workers, wages, pct) per config
  - Major category breakdown (top-N by each metric, primary config)
  - Minor/broad breakdowns (primary config only — too granular for cross-config)
  - Floor (all_confirmed) vs ceiling (all_ceiling) uncertainty ranges per major category
  - Cross-config heatmap at major category level

Figures (key ones copied to figures/):
  aggregate_totals.png        — Workers/wages/pct aggregate across 5 configs
  major_workers.png           — Top major categories by workers affected (primary)
  major_wages.png             — Top major categories by wages affected (primary)
  major_pct.png               — Top major categories by % tasks affected (primary)
  floor_ceiling_range.png     — Dumbbell chart: confirmed vs ceiling per major
  config_heatmap.png          — Heatmap: major × config, % tasks affected

Run from project root:
    venv/Scripts/python -m analysis.questions.economic_footprint.sector_footprint.run
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
    make_config,
)
from analysis.utils import (
    CATEGORY_PALETTE,
    COLORS,
    FONT_FAMILY,
    format_wages,
    format_workers,
    generate_pdf,
    make_horizontal_bar,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
PRIMARY_KEY = "all_confirmed"
CEILING_KEY = "all_ceiling"
TOP_N = 23  # show all major categories


# ── Data helpers ───────────────────────────────────────────────────────────────

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
    assert data is not None, f"No data for {dataset_name}"
    df = data["df"].rename(columns={"major_occ_category": "category"})
    df["dataset"] = dataset_name
    return df


def get_minor_data(dataset_name: str) -> pd.DataFrame:
    """Return minor-category breakdown for a single dataset."""
    from backend.compute import get_group_data

    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": "nat",
        "agg_level": "minor",
        "sort_by": "Workers Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    assert data is not None, f"No minor data for {dataset_name}"
    df = data["df"].rename(columns={"minor_occ_category": "category"})
    df["dataset"] = dataset_name
    return df


def get_occ_data(dataset_name: str) -> pd.DataFrame:
    """Return occupation-level breakdown for aggregate total computation."""
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
    assert data is not None, f"No occ data for {dataset_name}"
    df = data["df"].rename(columns={"title_current": "category"})
    df["dataset"] = dataset_name
    return df


def compute_aggregate_total(occ_df: pd.DataFrame, config_key: str, config_label: str,
                             total_emp: float) -> dict:
    """Compute aggregate national totals from occ-level data.

    Args:
        total_emp: total national employment (from get_explorer_occupations), used to
                   compute pct_of_employment.
    """
    workers = occ_df["workers_affected"].sum()
    wages = occ_df["wages_affected"].sum()
    pct_workers = (workers / total_emp * 100) if total_emp > 0 else np.nan

    # Simple average pct (already ratio-of-totals at occ level, mean is reasonable summary)
    pct_tasks_mean = occ_df["pct_tasks_affected"].mean()

    return {
        "config_key": config_key,
        "config_label": config_label,
        "workers_affected": workers,
        "wages_affected": wages,
        "pct_of_employment": pct_workers,
        "pct_tasks_affected_mean": pct_tasks_mean,
    }


# ── Figure builders ────────────────────────────────────────────────────────────

def _build_aggregate_bar(totals_df: pd.DataFrame) -> go.Figure:
    """Bar: workers affected (M) across 5 configs, annotated with % of employment."""
    configs = totals_df["config_label"].tolist()
    workers_m = [w / 1e6 for w in totals_df["workers_affected"]]
    pct = totals_df["pct_of_employment"].tolist()
    max_workers = max(workers_m)

    palette = CATEGORY_PALETTE
    bar_colors = [palette[i % len(palette)] for i in range(len(configs))]

    # Single bar per config showing workers; % of employment shown as inside label
    bar_labels = [f"{w:.1f}M<br>({p:.1f}%)" for w, p in zip(workers_m, pct)]

    fig = go.Figure(go.Bar(
        x=configs,
        y=workers_m,
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=bar_labels,
        textposition="outside",
        textfont=dict(size=13, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))

    fig.update_layout(
        yaxis=dict(
            title="Workers Affected (millions)",
            showgrid=True,
            gridcolor=COLORS["grid"],
            range=[0, max_workers * 1.35],
        ),
        xaxis=dict(tickfont=dict(size=12, family=FONT_FAMILY)),
        bargap=0.35,
        showlegend=False,
        margin=dict(l=80, r=60, t=110, b=80),
    )
    style_figure(
        fig,
        "Aggregate AI Economic Footprint — Five Configs",
        subtitle="Workers Affected (M) | Labels show % of total national employment | National | Freq | Auto-aug ON",
        height=580, width=1200,
    )
    return fig


def _build_floor_ceiling_dumbbell(confirmed_df: pd.DataFrame, ceiling_df: pd.DataFrame,
                                   metric: str = "pct_tasks_affected") -> go.Figure:
    """Dumbbell chart: confirmed (floor) vs ceiling per major category."""
    merged = confirmed_df[["category", metric]].merge(
        ceiling_df[["category", metric]].rename(columns={metric: f"{metric}_ceiling"}),
        on="category",
    ).sort_values(metric, ascending=True)

    fig = go.Figure()

    # Lines connecting floor to ceiling
    for _, row in merged.iterrows():
        fig.add_trace(go.Scatter(
            x=[row[metric], row[f"{metric}_ceiling"]],
            y=[row["category"], row["category"]],
            mode="lines",
            line=dict(color=COLORS["grid"], width=2),
            showlegend=False,
        ))

    # Floor dots
    fig.add_trace(go.Scatter(
        x=merged[metric],
        y=merged["category"],
        mode="markers",
        name="Confirmed (floor)",
        marker=dict(color=COLORS["primary"], size=10, symbol="circle"),
    ))
    # Ceiling dots
    fig.add_trace(go.Scatter(
        x=merged[f"{metric}_ceiling"],
        y=merged["category"],
        mode="markers",
        name="Ceiling (all sources)",
        marker=dict(color=COLORS["accent"], size=10, symbol="diamond"),
    ))

    x_title = "% Tasks Affected" if "pct" in metric else "Workers Affected"
    style_figure(fig, "AI Exposure Range by Sector — Confirmed vs Ceiling",
                 subtitle="Dots show floor (all_confirmed) and ceiling (all_ceiling) per major category",
                 x_title=x_title, height=700, width=1200)
    fig.update_layout(
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=11)),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
    )
    return fig


def _build_config_heatmap(all_major: pd.DataFrame) -> go.Figure:
    """Heatmap: major category (rows) × config (cols), showing % tasks affected."""
    pivot = all_major.pivot_table(
        index="category", columns="config_label", values="pct_tasks_affected", aggfunc="first"
    )
    # Order rows by primary config descending
    primary_label = ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]
    if primary_label in pivot.columns:
        pivot = pivot.sort_values(primary_label, ascending=True)

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=list(pivot.columns),
        y=list(pivot.index),
        colorscale=[[0, "#f0f4f8"], [0.5, COLORS["primary"]], [1.0, "#0d2b45"]],
        text=[[f"{v:.1f}%" if not np.isnan(v) else "" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=10, color="white", family=FONT_FAMILY),
        hovertemplate="%{y} | %{x}: %{z:.1f}%<extra></extra>",
        showscale=True,
        colorbar=dict(title="% Tasks<br>Affected", tickfont=dict(size=10)),
    ))
    style_figure(fig, "% Tasks Affected by Sector and Config",
                 subtitle="All five ANALYSIS_CONFIGS | National | Freq | Auto-aug ON",
                 show_legend=False, height=700, width=1100)
    fig.update_layout(
        xaxis=dict(side="bottom", tickangle=-20, showgrid=False, showline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        margin=dict(l=280, r=80, t=90, b=100),
    )
    return fig


def _build_treemap_wages(major_df: pd.DataFrame) -> go.Figure:
    """Treemap: sector block sizes = wages affected; color = % tasks affected."""
    df = major_df.copy()
    df = df[df["wages_affected"] > 0]

    labels = df["category"].tolist()
    values = df["wages_affected"].tolist()
    pct = df["pct_tasks_affected"].tolist()

    # Custom text: sector + wages + pct
    custom_text = [
        f"<b>{lab}</b><br>${w / 1e9:.1f}B<br>{p:.1f}% tasks"
        for lab, w, p in zip(labels, values, pct)
    ]

    fig = go.Figure(go.Treemap(
        labels=labels,
        values=values,
        parents=[""] * len(labels),
        text=custom_text,
        textinfo="text",
        hovertemplate="<b>%{label}</b><br>Wages: $%{value:.2s}<br>%{customdata:.1f}% tasks affected<extra></extra>",
        customdata=pct,
        marker=dict(
            colors=pct,
            colorscale=[[0, "#f0f4f8"], [0.5, COLORS["primary"]], [1.0, "#0d2b45"]],
            showscale=True,
            colorbar=dict(
                title="% Tasks<br>Affected",
                tickfont=dict(size=10, family=FONT_FAMILY),
                len=0.8,
            ),
        ),
        textfont=dict(size=12, family=FONT_FAMILY),
    ))

    style_figure(
        fig, "Wages Affected by Sector",
        subtitle="Block size = wages affected | Color = % tasks affected | All Confirmed | National",
        show_legend=False, height=700, width=1200,
    )
    fig.update_layout(margin=dict(l=10, r=10, t=90, b=60))
    return fig


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("sector_footprint: loading data...")

    # ── 0. Get total employment from explorer for pct_of_employment calc ─────
    from backend.compute import get_explorer_occupations
    all_occs = get_explorer_occupations()
    total_emp = sum(o.get("emp") or 0 for o in all_occs)
    print(f"  Total national employment: {total_emp:,.0f}")

    # ── 1. Load all configs ───────────────────────────────────────────────────
    major_frames: list[pd.DataFrame] = []
    totals_rows: list[dict] = []

    for key, ds_name in ANALYSIS_CONFIGS.items():
        label = ANALYSIS_CONFIG_LABELS[key]
        print(f"  {label}...")
        major_df = get_major_data(ds_name)
        major_df["config_key"] = key
        major_df["config_label"] = label
        major_frames.append(major_df)

        occ_df = get_occ_data(ds_name)
        totals_rows.append(compute_aggregate_total(occ_df, key, label, total_emp))

    all_major = pd.concat(major_frames, ignore_index=True)
    totals_df = pd.DataFrame(totals_rows)

    # Config ordering: primary first, then ceiling, then others
    config_order = [
        ANALYSIS_CONFIG_LABELS[k] for k in
        ["all_confirmed", "all_ceiling", "human_conversation", "agentic_confirmed", "agentic_ceiling"]
    ]
    totals_df["_order"] = totals_df["config_label"].map({l: i for i, l in enumerate(config_order)})
    totals_df = totals_df.sort_values("_order").drop(columns=["_order"])

    # ── 2. Primary config datasets for detailed charts ────────────────────────
    primary_label = ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]
    ceiling_label = ANALYSIS_CONFIG_LABELS[CEILING_KEY]
    primary_major = all_major[all_major["config_key"] == PRIMARY_KEY].copy()
    ceiling_major = all_major[all_major["config_key"] == CEILING_KEY].copy()

    # ── 3. Minor breakdown (primary only) ────────────────────────────────────
    print("  Loading minor breakdown...")
    minor_primary = get_minor_data(ANALYSIS_CONFIGS[PRIMARY_KEY])
    minor_primary["config_key"] = PRIMARY_KEY
    minor_primary["config_label"] = primary_label

    # ── 4. Save CSVs ──────────────────────────────────────────────────────────
    save_csv(totals_df.drop(columns=["config_key"]), results / "aggregate_totals.csv")
    save_csv(
        all_major[["config_label", "category", "workers_affected", "wages_affected", "pct_tasks_affected"]],
        results / "major_all_configs.csv",
    )
    save_csv(
        primary_major[["category", "workers_affected", "wages_affected", "pct_tasks_affected"]]
        .sort_values("workers_affected", ascending=False),
        results / "major_primary.csv",
    )
    save_csv(
        minor_primary[["category", "workers_affected", "wages_affected", "pct_tasks_affected"]]
        .sort_values("workers_affected", ascending=False),
        results / "minor_primary.csv",
    )
    print("  CSVs saved.")

    # ── 5. Figures ────────────────────────────────────────────────────────────

    # 5a. Aggregate totals grouped bar
    fig_agg = _build_aggregate_bar(totals_df)
    save_figure(fig_agg, results / "figures" / "aggregate_totals.png")
    shutil.copy(results / "figures" / "aggregate_totals.png", figs_dir / "aggregate_totals.png")
    print("  aggregate_totals.png")

    # 5b. Major categories — workers
    pm_sorted_workers = primary_major.sort_values("workers_affected", ascending=False)
    fig_w = make_horizontal_bar(
        pm_sorted_workers, "category", "workers_affected",
        "Top Sectors by Workers Affected",
        subtitle=f"{primary_label} | National | Freq | Auto-aug ON",
        x_title="Workers Affected",
        color=COLORS["primary"],
        height=700, width=1200,
    )
    save_figure(fig_w, results / "figures" / "major_workers.png")
    shutil.copy(results / "figures" / "major_workers.png", figs_dir / "major_workers.png")
    print("  major_workers.png")

    # 5c. Major categories — wages
    pm_sorted_wages = primary_major.sort_values("wages_affected", ascending=False)
    fig_wages = make_horizontal_bar(
        pm_sorted_wages, "category", "wages_affected",
        "Top Sectors by Wages Affected",
        subtitle=f"{primary_label} | National | Freq | Auto-aug ON",
        x_title="Wages Affected ($)",
        color=COLORS["secondary"],
        height=700, width=1200,
    )
    save_figure(fig_wages, results / "figures" / "major_wages.png")
    shutil.copy(results / "figures" / "major_wages.png", figs_dir / "major_wages.png")
    print("  major_wages.png")

    # 5d. Major categories — % tasks affected
    pm_sorted_pct = primary_major.sort_values("pct_tasks_affected", ascending=False)
    fig_pct = make_horizontal_bar(
        pm_sorted_pct, "category", "pct_tasks_affected",
        "Top Sectors by % Tasks Affected",
        subtitle=f"{primary_label} | National | Freq | Auto-aug ON",
        x_title="% Tasks Affected",
        color=COLORS["accent"],
        value_format="%.1f%%",
        height=700, width=1200,
    )
    save_figure(fig_pct, results / "figures" / "major_pct.png")
    shutil.copy(results / "figures" / "major_pct.png", figs_dir / "major_pct.png")
    print("  major_pct.png")

    # 5e. Floor vs ceiling dumbbell
    fig_db = _build_floor_ceiling_dumbbell(primary_major, ceiling_major, "pct_tasks_affected")
    save_figure(fig_db, results / "figures" / "floor_ceiling_range.png")
    shutil.copy(results / "figures" / "floor_ceiling_range.png", figs_dir / "floor_ceiling_range.png")
    print("  floor_ceiling_range.png")

    # 5f. Config heatmap
    fig_heat = _build_config_heatmap(all_major)
    save_figure(fig_heat, results / "figures" / "config_heatmap.png")
    shutil.copy(results / "figures" / "config_heatmap.png", figs_dir / "config_heatmap.png")
    print("  config_heatmap.png")

    # 5g. Treemap: wages by sector
    fig_treemap = _build_treemap_wages(primary_major)
    save_figure(fig_treemap, results / "figures" / "treemap_wages.png")
    shutil.copy(results / "figures" / "treemap_wages.png", figs_dir / "treemap_wages.png")
    print("  treemap_wages.png")

    # ── 6. Print summary ──────────────────────────────────────────────────────
    primary_totals = totals_df[totals_df["config_key"] == PRIMARY_KEY].iloc[0]
    ceiling_totals = totals_df[totals_df["config_key"] == CEILING_KEY].iloc[0]

    print("\n-- Aggregate totals --")
    print(f"  Primary (all_confirmed): {format_workers(primary_totals['workers_affected'])} workers, "
          f"{format_wages(primary_totals['wages_affected'])} wages, "
          f"{primary_totals['pct_of_employment']:.1f}% of employment")
    print(f"  Ceiling  (all_ceiling) : {format_workers(ceiling_totals['workers_affected'])} workers, "
          f"{format_wages(ceiling_totals['wages_affected'])} wages, "
          f"{ceiling_totals['pct_of_employment']:.1f}% of employment")
    print(f"  Gap: +{format_workers(ceiling_totals['workers_affected'] - primary_totals['workers_affected'])} workers")

    top3 = primary_major.sort_values("workers_affected", ascending=False).head(3)
    print("  Top 3 by workers (primary):")
    for _, r in top3.iterrows():
        print(f"    {r['category']}: {format_workers(r['workers_affected'])}, "
              f"{r['pct_tasks_affected']:.1f}% tasks")

    # ── 7. Generate PDF report ────────────────────────────────────────────────
    report_path = HERE / "sector_footprint_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "sector_footprint_report.pdf")

    print("\nsector_footprint: done.")


if __name__ == "__main__":
    main()
