"""
run.py -- Job Elimination Risk: Which occupations are most at risk?

Identifies occupations where AI can do most of the work AND is already being
used for it.  Uses AEI Cumul. v4 + Microsoft (actual usage data) as the
primary "usage-confirmed" signal, with MCP v4 as a capability-only comparison.

Primary method: Value (importance-weighted) with auto-aug ON.
Sensitivity check: Time (frequency) method.

Tier thresholds (% tasks affected):
  High risk:          >= 60%
  Moderate risk:      40-60%
  Restructuring:      20-40%
  Low exposure:       < 20%

Usage from project root:
    venv/Scripts/python -m analysis.questions.job_elimination_risk.run
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from analysis.config import (
    DEFAULT_OCC_CONFIG,
    make_config,
    run_occ_query,
    ensure_results_dir,
)
from analysis.utils import (
    style_figure,
    save_figure,
    save_csv,
    make_horizontal_bar,
    describe_config,
    format_workers,
    format_wages,
    format_pct,
    COLORS,
    CATEGORY_PALETTE,
)

HERE = Path(__file__).resolve().parent

# -- Thresholds ---------------------------------------------------------------

HIGH_RISK = 60.0
MODERATE_RISK = 40.0
RESTRUCTURING = 20.0

TIER_LABELS = {
    "high_risk": "High Risk (>=60%)",
    "moderate_risk": "Moderate Risk (40-60%)",
    "restructuring": "Restructuring (20-40%)",
    "low_exposure": "Low Exposure (<20%)",
}
TIER_ORDER = ["high_risk", "moderate_risk", "restructuring", "low_exposure"]
TIER_COLORS = {
    "high_risk": "#DC2626",       # Red
    "moderate_risk": "#F59E0B",   # Amber
    "restructuring": "#3B82F6",   # Blue
    "low_exposure": "#6B7280",    # Gray
}

# -- Dataset configs -----------------------------------------------------------

USAGE_DATASETS = ["AEI Cumul. v4", "Microsoft"]
CAPABILITY_DATASETS = ["MCP v4"]

TOP_N_CSV = 50       # rows in CSVs
TOP_N_CHART = 30     # bars in charts


# -- Helpers -------------------------------------------------------------------

def _assign_tier(pct: float) -> str:
    """Assign a risk tier based on pct_tasks_affected."""
    if pct >= HIGH_RISK:
        return "high_risk"
    elif pct >= MODERATE_RISK:
        return "moderate_risk"
    elif pct >= RESTRUCTURING:
        return "restructuring"
    else:
        return "low_exposure"


def _get_employment_lookup() -> pd.DataFrame:
    """Get occupation-level employment and hierarchy from the explorer cache.

    Returns DataFrame with columns: title_current, emp_nat, wage_nat, major.
    """
    from backend.compute import get_explorer_occupations

    occ_list = get_explorer_occupations()
    rows = []
    for occ in occ_list:
        rows.append({
            "title_current": occ["title_current"],
            "emp_nat": occ.get("emp_nat", 0) or 0,
            "wage_nat": occ.get("wage_nat", 0) or 0,
            "major": occ.get("major", ""),
        })
    return pd.DataFrame(rows)


def _run_occ_level(
    datasets: list[str],
    method: str,
    use_auto_aug: bool,
) -> pd.DataFrame | None:
    """Run the compute pipeline at occupation level, return all occupations."""
    cfg = make_config(
        DEFAULT_OCC_CONFIG,
        selected_datasets=datasets,
        combine_method="Average",
        method=method,
        use_auto_aug=use_auto_aug,
        physical_mode="all",
        geo="nat",
        agg_level="occupation",
        sort_by="% Tasks Affected",
        top_n=1000,  # get all occupations
        search_query="",
    )
    result = run_occ_query(cfg)
    if result is None:
        return None
    df, _ = result
    return df


def _build_tiered_df(
    compute_df: pd.DataFrame,
    emp_df: pd.DataFrame,
) -> pd.DataFrame:
    """Merge compute results with employment data and assign risk tiers."""
    merged = compute_df.merge(
        emp_df,
        left_on="category",
        right_on="title_current",
        how="left",
    )
    merged["emp_nat"] = merged["emp_nat"].fillna(0)
    merged["wage_nat"] = merged["wage_nat"].fillna(0)
    merged["major"] = merged["major"].fillna("")

    merged["tier"] = merged["pct_tasks_affected"].apply(_assign_tier)
    merged["tier_label"] = merged["tier"].map(TIER_LABELS)

    # Sort by pct descending within each tier, then by employment
    merged = merged.sort_values(
        ["pct_tasks_affected", "emp_nat"],
        ascending=[False, False],
    ).reset_index(drop=True)

    return merged


def _make_scatter(
    df: pd.DataFrame,
    title: str,
    subtitle: str,
) -> go.Figure:
    """Scatter plot: pct_tasks_affected (X) vs employment (Y), colored by tier."""
    fig = go.Figure()

    for tier in TIER_ORDER:
        tier_df = df[df["tier"] == tier]
        if tier_df.empty:
            continue
        fig.add_trace(go.Scatter(
            x=tier_df["pct_tasks_affected"],
            y=tier_df["emp_nat"],
            mode="markers",
            name=TIER_LABELS[tier],
            marker=dict(
                color=TIER_COLORS[tier],
                size=8,
                opacity=0.7,
                line=dict(width=0.5, color="white"),
            ),
            text=tier_df["category"],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "% Tasks Affected: %{x:.1f}%<br>"
                "Employment: %{y:,.0f}<br>"
                "<extra></extra>"
            ),
        ))

    # Add threshold lines
    for thresh, label in [
        (HIGH_RISK, "60% — High Risk"),
        (MODERATE_RISK, "40% — Moderate"),
        (RESTRUCTURING, "20% — Restructuring"),
    ]:
        fig.add_vline(
            x=thresh, line_dash="dash", line_color="#9CA3AF", line_width=1,
            annotation_text=label, annotation_position="top",
            annotation_font_size=10, annotation_font_color="#9CA3AF",
        )

    style_figure(
        fig,
        title,
        subtitle=subtitle,
        x_title="% Tasks Affected (usage-confirmed, auto-aug weighted)",
        y_title="Total Employment (National)",
        height=700,
        width=1200,
        show_legend=True,
    )
    fig.update_yaxes(type="log", dtick=1)
    fig.update_layout(
        legend=dict(
            orientation="h", yanchor="top", y=-0.15,
            xanchor="center", x=0.5,
        ),
    )

    return fig


def _make_tier_summary_bar(
    tier_summary: pd.DataFrame,
    value_col: str,
    title: str,
    subtitle: str,
    x_title: str,
) -> go.Figure:
    """Stacked horizontal bar: major categories broken out by risk tier."""
    fig = go.Figure()

    for tier in reversed(TIER_ORDER):
        tier_data = tier_summary[tier_summary["tier"] == tier]
        if tier_data.empty:
            continue
        fig.add_trace(go.Bar(
            y=tier_data["major"],
            x=tier_data[value_col],
            orientation="h",
            name=TIER_LABELS[tier],
            marker_color=TIER_COLORS[tier],
        ))

    style_figure(
        fig, title,
        subtitle=subtitle,
        x_title=x_title,
        height=max(600, len(tier_summary["major"].unique()) * 30 + 200),
        width=1200,
        show_legend=True,
    )
    fig.update_layout(barmode="stack")

    return fig


# -- Main ---------------------------------------------------------------------

def main() -> None:
    results = ensure_results_dir(HERE)
    fig_dir = results / "figures"
    print("Job Elimination Risk — generating outputs...\n")

    # ── Employment lookup ─────────────────────────────────────────────────
    print("Loading employment data...")
    emp_df = _get_employment_lookup()
    total_national_emp = emp_df["emp_nat"].sum()
    print(f"  {len(emp_df)} occupations, {total_national_emp:,.0f} total employment\n")

    # ══════════════════════════════════════════════════════════════════════
    # 1. PRIMARY ANALYSIS: Usage-confirmed, Value method, auto-aug ON
    # ══════════════════════════════════════════════════════════════════════
    print("== Primary: Usage-confirmed (AEI Cumul. v4 + Microsoft), Value, Auto-aug ON ==")

    usage_df = _run_occ_level(USAGE_DATASETS, method="imp", use_auto_aug=True)
    if usage_df is None:
        print("  ERROR: No data returned for usage-confirmed config")
        return

    tiered = _build_tiered_df(usage_df, emp_df)
    print(f"  {len(tiered)} occupations tiered")

    # Tier counts
    tier_counts = tiered["tier"].value_counts()
    tier_emp = tiered.groupby("tier")["emp_nat"].sum()
    for t in TIER_ORDER:
        n = tier_counts.get(t, 0)
        e = tier_emp.get(t, 0)
        print(f"    {TIER_LABELS[t]}: {n} occupations, {format_workers(e)} workers")

    # ── CSV: Full tiered list ─────────────────────────────────────────────
    tiered_out = tiered[[
        "category", "pct_tasks_affected", "workers_affected", "wages_affected",
        "emp_nat", "wage_nat", "major", "tier", "tier_label",
    ]].copy()
    tiered_out = tiered_out.rename(columns={
        "category": "occupation",
        "emp_nat": "total_employment",
        "wage_nat": "median_wage",
        "major": "major_category",
    })
    save_csv(tiered_out, results / "all_occupations_tiered.csv")
    print("  Saved all_occupations_tiered.csv")

    # ── CSV: High-risk tier ranked by employment ──────────────────────────
    high_risk = tiered[tiered["tier"] == "high_risk"].copy()
    high_risk = high_risk.sort_values("emp_nat", ascending=False).reset_index(drop=True)
    high_risk_out = high_risk[[
        "category", "pct_tasks_affected", "workers_affected", "wages_affected",
        "emp_nat", "wage_nat", "major",
    ]].rename(columns={
        "category": "occupation",
        "emp_nat": "total_employment",
        "wage_nat": "median_wage",
        "major": "major_category",
    })
    high_risk_out.insert(0, "risk_rank", range(1, len(high_risk_out) + 1))
    save_csv(high_risk_out, results / "high_risk_by_employment.csv")
    print(f"  Saved high_risk_by_employment.csv ({len(high_risk_out)} occupations)")

    # ── Figure: Scatter plot ──────────────────────────────────────────────
    fig = _make_scatter(
        tiered,
        "Job Elimination Risk: AI Task Exposure vs Employment",
        "Usage-confirmed (AEI Cumul. v4 + Microsoft) | Value method | Auto-aug ON | National",
    )
    save_figure(fig, fig_dir / "scatter_risk_vs_employment.png")
    print("  Saved scatter_risk_vs_employment.png")

    # ── Figure: High-risk tier bar chart (by employment) ──────────────────
    if not high_risk.empty:
        hr_plot = high_risk.head(TOP_N_CHART).copy()
        hr_plot = hr_plot.sort_values("emp_nat", ascending=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=hr_plot["category"],
            x=hr_plot["emp_nat"],
            orientation="h",
            marker_color=TIER_COLORS["high_risk"],
            text=[f"{p:.0f}% tasks" for p in hr_plot["pct_tasks_affected"]],
            textposition="auto",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Employment: %{x:,.0f}<br>"
                "%{text}<br>"
                "<extra></extra>"
            ),
        ))
        style_figure(
            fig,
            f"Largest High-Risk Occupations (>={int(HIGH_RISK)}% Tasks Affected)",
            subtitle=(
                f"Top {min(TOP_N_CHART, len(hr_plot))} by employment | "
                "Usage-confirmed | Value | Auto-aug ON"
            ),
            x_title="Total Employment (National)",
            height=max(500, min(TOP_N_CHART, len(hr_plot)) * 28 + 150),
            show_legend=False,
        )
        save_figure(fig, fig_dir / "high_risk_by_employment.png")
        print("  Saved high_risk_by_employment.png")

    # ── Figure: High-risk tier bar chart (by pct tasks affected) ──────────
    if not high_risk.empty:
        hr_pct_plot = high_risk.sort_values(
            "pct_tasks_affected", ascending=False,
        ).head(TOP_N_CHART).copy()
        hr_pct_plot = hr_pct_plot.sort_values("pct_tasks_affected", ascending=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=hr_pct_plot["category"],
            x=hr_pct_plot["pct_tasks_affected"],
            orientation="h",
            marker_color=TIER_COLORS["high_risk"],
            text=[format_workers(e) for e in hr_pct_plot["emp_nat"]],
            textposition="auto",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "% Tasks Affected: %{x:.1f}%<br>"
                "Employment: %{text}<br>"
                "<extra></extra>"
            ),
        ))
        style_figure(
            fig,
            f"Most Exposed High-Risk Occupations (>={int(HIGH_RISK)}% Tasks Affected)",
            subtitle=(
                f"Top {min(TOP_N_CHART, len(hr_pct_plot))} by % tasks affected | "
                "Usage-confirmed | Value | Auto-aug ON"
            ),
            x_title="% Tasks Affected",
            height=max(500, min(TOP_N_CHART, len(hr_pct_plot)) * 28 + 150),
            show_legend=False,
        )
        save_figure(fig, fig_dir / "high_risk_by_pct.png")
        print("  Saved high_risk_by_pct.png")

    # ── Major category rollup ─────────────────────────────────────────────
    print("\n== Major category rollup ==")
    tier_by_major = (
        tiered.groupby(["major", "tier"])
        .agg(
            n_occupations=("category", "count"),
            total_emp=("emp_nat", "sum"),
            total_workers_affected=("workers_affected", "sum"),
        )
        .reset_index()
    )

    # Compute % of each major's occupations in each tier
    major_totals = tiered.groupby("major").agg(
        total_occs=("category", "count"),
        total_major_emp=("emp_nat", "sum"),
    ).reset_index()
    tier_by_major = tier_by_major.merge(major_totals, on="major", how="left")
    tier_by_major["pct_of_major_occs"] = (
        tier_by_major["n_occupations"] / tier_by_major["total_occs"] * 100
    )
    tier_by_major["pct_of_major_emp"] = (
        tier_by_major["total_emp"] / tier_by_major["total_major_emp"] * 100
    )
    tier_by_major["tier_label"] = tier_by_major["tier"].map(TIER_LABELS)

    save_csv(tier_by_major, results / "major_category_tier_rollup.csv")
    print("  Saved major_category_tier_rollup.csv")

    # Sort majors by high-risk share for the chart
    major_hr_share = tier_by_major[tier_by_major["tier"] == "high_risk"].set_index("major")["pct_of_major_occs"]
    major_order = major_hr_share.sort_values(ascending=True).index.tolist()
    # Add majors with 0 high-risk at the top
    all_majors = tiered["major"].unique().tolist()
    for m in all_majors:
        if m not in major_order:
            major_order.insert(0, m)

    # Stacked bar: % of occupations in each tier by major category
    fig = go.Figure()
    for tier in reversed(TIER_ORDER):
        t_data = tier_by_major[tier_by_major["tier"] == tier].set_index("major")
        vals = [t_data.loc[m, "pct_of_major_occs"] if m in t_data.index else 0 for m in major_order]
        fig.add_trace(go.Bar(
            y=major_order,
            x=vals,
            orientation="h",
            name=TIER_LABELS[tier],
            marker_color=TIER_COLORS[tier],
        ))
    style_figure(
        fig,
        "Risk Tier Distribution by Major Category",
        subtitle="% of occupations in each risk tier | Usage-confirmed | Value | Auto-aug ON",
        x_title="% of Occupations",
        height=max(600, len(major_order) * 32 + 200),
        show_legend=True,
    )
    fig.update_layout(barmode="stack")
    save_figure(fig, fig_dir / "tier_distribution_by_major.png")
    print("  Saved tier_distribution_by_major.png")

    # Stacked bar: employment in each tier by major
    fig = go.Figure()
    for tier in reversed(TIER_ORDER):
        t_data = tier_by_major[tier_by_major["tier"] == tier].set_index("major")
        vals = [t_data.loc[m, "total_emp"] if m in t_data.index else 0 for m in major_order]
        fig.add_trace(go.Bar(
            y=major_order,
            x=vals,
            orientation="h",
            name=TIER_LABELS[tier],
            marker_color=TIER_COLORS[tier],
        ))
    style_figure(
        fig,
        "Employment by Risk Tier and Major Category",
        subtitle="Total workers in each risk tier | Usage-confirmed | Value | Auto-aug ON",
        x_title="Employment",
        height=max(600, len(major_order) * 32 + 200),
        show_legend=True,
    )
    fig.update_layout(barmode="stack")
    save_figure(fig, fig_dir / "employment_by_tier_major.png")
    print("  Saved employment_by_tier_major.png")

    # ══════════════════════════════════════════════════════════════════════
    # 2. CAPABILITY COMPARISON: MCP v4 alone
    # ══════════════════════════════════════════════════════════════════════
    print("\n== Capability comparison: MCP v4, Value, Auto-aug ON ==")

    cap_df = _run_occ_level(CAPABILITY_DATASETS, method="imp", use_auto_aug=True)
    if cap_df is None:
        print("  ERROR: No data for MCP v4")
    else:
        cap_tiered = _build_tiered_df(cap_df, emp_df)

        # Compare tier shifts
        usage_tiers = tiered[["category", "tier", "pct_tasks_affected"]].rename(
            columns={"tier": "usage_tier", "pct_tasks_affected": "usage_pct"}
        )
        cap_tiers = cap_tiered[["category", "tier", "pct_tasks_affected"]].rename(
            columns={"tier": "capability_tier", "pct_tasks_affected": "capability_pct"}
        )
        comparison = usage_tiers.merge(cap_tiers, on="category", how="outer")
        comparison["usage_tier"] = comparison["usage_tier"].fillna("low_exposure")
        comparison["capability_tier"] = comparison["capability_tier"].fillna("low_exposure")
        comparison["usage_pct"] = comparison["usage_pct"].fillna(0)
        comparison["capability_pct"] = comparison["capability_pct"].fillna(0)
        comparison["pct_gap"] = comparison["capability_pct"] - comparison["usage_pct"]
        comparison["tier_shifted"] = comparison["usage_tier"] != comparison["capability_tier"]

        save_csv(comparison, results / "usage_vs_capability_comparison.csv")
        print(f"  Saved usage_vs_capability_comparison.csv")

        # Tier shift summary
        shift_counts = comparison.groupby(["usage_tier", "capability_tier"]).size().reset_index(name="count")
        save_csv(shift_counts, results / "tier_shift_matrix.csv")
        print("  Saved tier_shift_matrix.csv")

        # How many occupations are high-risk under capability but not usage?
        cap_only_high = comparison[
            (comparison["capability_tier"] == "high_risk") &
            (comparison["usage_tier"] != "high_risk")
        ]
        usage_high_count = (comparison["usage_tier"] == "high_risk").sum()
        cap_high_count = (comparison["capability_tier"] == "high_risk").sum()
        print(f"  Usage-confirmed high-risk: {usage_high_count} occupations")
        print(f"  Capability high-risk: {cap_high_count} occupations")
        print(f"  High-risk in capability only (not yet usage-confirmed): {len(cap_only_high)}")

        # CSV of capability-only high-risk (these are "emerging risk")
        if not cap_only_high.empty:
            emerging = cap_only_high.merge(
                emp_df, left_on="category", right_on="title_current", how="left",
            )
            emerging = emerging.sort_values("emp_nat", ascending=False)
            emerging_out = emerging[[
                "category", "capability_pct", "usage_pct", "pct_gap",
                "usage_tier", "emp_nat", "major",
            ]].rename(columns={
                "category": "occupation",
                "capability_pct": "mcp_pct_tasks",
                "usage_pct": "usage_pct_tasks",
                "pct_gap": "capability_usage_gap",
                "emp_nat": "total_employment",
                "major": "major_category",
            })
            save_csv(emerging_out, results / "emerging_risk_capability_only.csv")
            print(f"  Saved emerging_risk_capability_only.csv ({len(emerging_out)} occupations)")

        # Scatter comparing usage vs capability pct
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=comparison["usage_pct"],
            y=comparison["capability_pct"],
            mode="markers",
            marker=dict(
                color=[TIER_COLORS.get(t, "#6B7280") for t in comparison["usage_tier"]],
                size=6,
                opacity=0.6,
            ),
            text=comparison["category"],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Usage: %{x:.1f}%<br>"
                "Capability: %{y:.1f}%<br>"
                "<extra></extra>"
            ),
        ))
        # Diagonal line (usage = capability)
        max_val = max(comparison["usage_pct"].max(), comparison["capability_pct"].max())
        fig.add_trace(go.Scatter(
            x=[0, max_val], y=[0, max_val],
            mode="lines", line=dict(dash="dash", color="#D1D5DB", width=1),
            showlegend=False, hoverinfo="skip",
        ))
        style_figure(
            fig,
            "Usage-Confirmed vs Capability-Only Exposure",
            subtitle="Each dot = one occupation | Above diagonal = capability exceeds current usage",
            x_title="% Tasks Affected (AEI Cumul. v4 + Microsoft)",
            y_title="% Tasks Affected (MCP v4)",
            height=700, width=800,
            show_legend=False,
        )
        save_figure(fig, fig_dir / "usage_vs_capability_scatter.png")
        print("  Saved usage_vs_capability_scatter.png")

    # ══════════════════════════════════════════════════════════════════════
    # 3. SENSITIVITY CHECK: Time (freq) method
    # ══════════════════════════════════════════════════════════════════════
    print("\n== Sensitivity check: Time (freq) method ==")

    freq_df = _run_occ_level(USAGE_DATASETS, method="freq", use_auto_aug=True)
    if freq_df is None:
        print("  ERROR: No data for freq method")
    else:
        freq_tiered = _build_tiered_df(freq_df, emp_df)

        # Compare tiers between Value and Time
        val_tiers = tiered[["category", "tier", "pct_tasks_affected"]].rename(
            columns={"tier": "value_tier", "pct_tasks_affected": "value_pct"}
        )
        freq_tiers = freq_tiered[["category", "tier", "pct_tasks_affected"]].rename(
            columns={"tier": "freq_tier", "pct_tasks_affected": "freq_pct"}
        )
        method_comp = val_tiers.merge(freq_tiers, on="category", how="outer")
        method_comp["value_tier"] = method_comp["value_tier"].fillna("low_exposure")
        method_comp["freq_tier"] = method_comp["freq_tier"].fillna("low_exposure")
        method_comp["value_pct"] = method_comp["value_pct"].fillna(0)
        method_comp["freq_pct"] = method_comp["freq_pct"].fillna(0)
        method_comp["pct_diff"] = method_comp["value_pct"] - method_comp["freq_pct"]
        method_comp["tier_changed"] = method_comp["value_tier"] != method_comp["freq_tier"]

        save_csv(method_comp, results / "method_sensitivity_value_vs_freq.csv")
        print("  Saved method_sensitivity_value_vs_freq.csv")

        # Summary stats
        n_changed = method_comp["tier_changed"].sum()
        n_total = len(method_comp)
        val_high = (method_comp["value_tier"] == "high_risk").sum()
        freq_high = (method_comp["freq_tier"] == "high_risk").sum()
        print(f"  Value method high-risk: {val_high}")
        print(f"  Freq method high-risk: {freq_high}")
        print(f"  Tier changed: {n_changed}/{n_total} ({n_changed/n_total*100:.1f}%)")

        # Biggest movers (largest absolute pct difference)
        movers = method_comp[method_comp["tier_changed"]].copy()
        movers["abs_diff"] = movers["pct_diff"].abs()
        movers = movers.sort_values("abs_diff", ascending=False).head(30)
        movers = movers.merge(
            emp_df[["title_current", "emp_nat", "major"]],
            left_on="category", right_on="title_current", how="left",
        )
        movers_out = movers[[
            "category", "value_tier", "freq_tier", "value_pct", "freq_pct",
            "pct_diff", "emp_nat", "major",
        ]].rename(columns={
            "category": "occupation",
            "emp_nat": "total_employment",
            "major": "major_category",
        })
        save_csv(movers_out, results / "method_sensitivity_tier_movers.csv")
        print(f"  Saved method_sensitivity_tier_movers.csv ({len(movers_out)} movers)")

        # Stability: occupations that are high-risk under BOTH methods
        both_high = method_comp[
            (method_comp["value_tier"] == "high_risk") &
            (method_comp["freq_tier"] == "high_risk")
        ]
        both_high_with_emp = both_high.merge(
            emp_df[["title_current", "emp_nat", "major"]],
            left_on="category", right_on="title_current", how="left",
        ).sort_values("emp_nat", ascending=False)
        stable_out = both_high_with_emp[[
            "category", "value_pct", "freq_pct", "emp_nat", "major",
        ]].rename(columns={
            "category": "occupation",
            "emp_nat": "total_employment",
            "major": "major_category",
        })
        save_csv(stable_out, results / "stable_high_risk_both_methods.csv")
        print(f"  Saved stable_high_risk_both_methods.csv ({len(stable_out)} occupations)")

    print("\nDone.")


if __name__ == "__main__":
    main()
