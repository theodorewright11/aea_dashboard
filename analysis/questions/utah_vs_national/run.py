"""
run.py — Utah vs National: Where do state-level results diverge?

Re-runs the three existing analyses (Economic Footprint, AI Transformative
Potential, Job Elimination Risk) with geo="ut" and compares against the
national results. Only surfaces notable divergences.

Key insight: % tasks affected is geography-independent (computed from O*NET
task scores and AI auto-aug scores, which don't vary by geography). Only
workers_affected and wages_affected change, because they depend on BLS
employment counts and wage levels that differ between national and Utah.

This means divergences show up as:
  - Ranking shifts (different occupational mix in Utah)
  - Different absolute magnitudes (Utah is ~1.5% of the US workforce)
  - Different sector-level shares (Utah's industry concentration differs)

Usage from project root:
    venv/Scripts/python -m analysis.questions.utah_vs_national.run
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from analysis.config import (
    make_config,
    DEFAULT_OCC_CONFIG,
    run_occ_query,
    ensure_results_dir,
)
from analysis.utils import (
    style_figure,
    save_figure,
    save_csv,
    make_horizontal_bar,
    format_workers,
    format_wages,
    format_pct,
    _format_bar_label,
    COLORS,
    FONT_FAMILY,
    CATEGORY_PALETTE,
)

HERE = Path(__file__).resolve().parent

# ── Shared constants ────────────────────────────────────────────────────────

# Threshold for "notable" rank shift (absolute positions)
RANK_SHIFT_THRESHOLD = 3

# Threshold for "notable" share difference (percentage points)
SHARE_DIFF_THRESHOLD = 2.0

# Dataset configs (same as the original analyses)
COMBINED_DATASETS = ["AEI Cumul. (Both) v4", "MCP Cumul. v4", "Microsoft"]
USAGE_DATASETS = ["AEI Cumul. (Both) v4", "Microsoft"]
CAPABILITY_DATASETS = ["AEI Cumul. (Both) v4", "MCP Cumul. v4", "Microsoft"]
MCP_DATASETS = ["MCP Cumul. v4"]
AEI_DATASETS = ["AEI Cumul. (Both) v4"]
AGENTIC_DATASETS = ["AEI API Cumul. v4", "MCP Cumul. v4"]
CONVERSATIONAL_DATASETS = ["AEI Cumul. Conv. v4", "Microsoft"]

# Tier thresholds (from job_elimination_risk)
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
    "high_risk": COLORS["negative"],
    "moderate_risk": COLORS["accent"],
    "restructuring": COLORS["primary"],
    "low_exposure": COLORS["muted"],
}


# ── Helpers ─────────────────────────────────────────────────────────────────

def _run_query(
    datasets: list[str],
    geo: str,
    agg_level: str = "major",
    combine_method: str = "Average",
    method: str = "freq",
    use_auto_aug: bool = True,
    sort_by: str = "Workers Affected",
    top_n: int = 1000,
    physical_mode: str = "all",
) -> pd.DataFrame | None:
    """Run the compute pipeline and return full DataFrame with 'category' col."""
    cfg = make_config(
        DEFAULT_OCC_CONFIG,
        selected_datasets=datasets,
        combine_method=combine_method,
        method=method,
        use_auto_aug=use_auto_aug,
        physical_mode=physical_mode,
        geo=geo,
        agg_level=agg_level,
        sort_by=sort_by,
        top_n=top_n,
        search_query="",
    )
    result = run_occ_query(cfg)
    if result is None:
        return None
    df, _ = result
    return df


def _run_group_totals(
    datasets: list[str],
    geo: str,
    combine_method: str = "Average",
    **overrides: Any,
) -> dict[str, Any] | None:
    """Run pipeline and return totals dict like economic_footprint."""
    from backend.compute import get_group_data

    cfg = make_config(
        DEFAULT_OCC_CONFIG,
        selected_datasets=datasets,
        combine_method=combine_method,
        geo=geo,
        agg_level="major",
        top_n=1000,
        search_query="",
        **overrides,
    )
    result = get_group_data(cfg)
    if result is None:
        return None
    df = result["df"].rename(columns={result["group_col"]: "category"})
    return {
        "df": df,
        "total_workers": float(result["total_emp"]),
        "total_wages": float(result["total_wages"]),
    }


def _economy_baseline(geo: str) -> dict[str, float]:
    """Total employment and wage bill from eco_2025."""
    from backend.compute import load_eco_raw

    eco = load_eco_raw()
    emp_col = f"emp_tot_{geo}_2024"
    wage_col = f"a_med_{geo}_2024"
    occ = eco.drop_duplicates(subset=["title_current"])
    total_emp = float(occ[emp_col].fillna(0).sum())
    total_wages = float((occ[emp_col].fillna(0) * occ[wage_col].fillna(0)).sum())
    return {"total_emp": total_emp, "total_wages": total_wages}


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


def _compare_rankings(
    nat_df: pd.DataFrame,
    ut_df: pd.DataFrame,
    metric: str,
    label: str,
) -> pd.DataFrame:
    """Compare national vs Utah rankings for a metric, return divergences."""
    nat = nat_df[["category", metric]].copy()
    nat["rank_nat"] = nat[metric].rank(ascending=False, method="min").astype(int)
    nat = nat.rename(columns={metric: f"{metric}_nat"})

    ut = ut_df[["category", metric]].copy()
    ut["rank_ut"] = ut[metric].rank(ascending=False, method="min").astype(int)
    ut = ut.rename(columns={metric: f"{metric}_ut"})

    merged = nat.merge(ut, on="category", how="outer")
    merged["rank_shift"] = merged["rank_nat"] - merged["rank_ut"]  # positive = higher in Utah
    merged["abs_rank_shift"] = merged["rank_shift"].abs()

    return merged.sort_values("abs_rank_shift", ascending=False)


def _compute_share_comparison(
    nat_df: pd.DataFrame,
    ut_df: pd.DataFrame,
    metric: str,
) -> pd.DataFrame:
    """Compare each category's share of total (nat vs ut)."""
    nat_total = nat_df[metric].sum()
    ut_total = ut_df[metric].sum()

    nat = nat_df[["category", metric]].copy()
    nat["share_nat"] = nat[metric] / nat_total * 100

    ut = ut_df[["category", metric]].copy()
    ut["share_ut"] = ut[metric] / ut_total * 100

    merged = nat.merge(ut, on="category", how="outer", suffixes=("_nat", "_ut"))
    merged["share_nat"] = merged["share_nat"].fillna(0)
    merged["share_ut"] = merged["share_ut"].fillna(0)
    merged["share_diff_pp"] = merged["share_ut"] - merged["share_nat"]
    merged["abs_share_diff"] = merged["share_diff_pp"].abs()

    return merged.sort_values("abs_share_diff", ascending=False)


# ── Chart builders ──────────────────────────────────────────────────────────

def _chart_share_divergence(
    share_df: pd.DataFrame,
    metric_label: str,
    title: str,
    subtitle: str,
    top_n: int = 22,
) -> go.Figure:
    """Diverging horizontal bar chart showing share difference (pp) Utah vs Nat."""
    plot_df = share_df.head(top_n).copy()
    plot_df = plot_df.sort_values("share_diff_pp", ascending=True)

    colors = [
        COLORS["utah"] if v > 0 else COLORS["national"]
        for v in plot_df["share_diff_pp"]
    ]

    labels = [
        f"{'+'if v > 0 else ''}{v:.1f}pp  (UT {s_ut:.1f}% vs Nat {s_nat:.1f}%)"
        for v, s_ut, s_nat in zip(
            plot_df["share_diff_pp"], plot_df["share_ut"], plot_df["share_nat"]
        )
    ]

    fig = go.Figure(go.Bar(
        y=plot_df["category"],
        x=plot_df["share_diff_pp"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=labels,
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))

    max_abs = max(abs(plot_df["share_diff_pp"].min()), abs(plot_df["share_diff_pp"].max()))
    chart_h = max(550, top_n * 30 + 160)
    style_figure(
        fig, title, subtitle=subtitle,
        width=1200, height=chart_h, show_legend=False,
    )
    fig.update_layout(
        margin=dict(l=20, r=320),
        xaxis=dict(
            showgrid=True, gridcolor=COLORS["grid"],
            zeroline=True, zerolinecolor=COLORS["text"], zerolinewidth=1,
            showticklabels=False, showline=False,
            range=[-max_abs * 2.5, max_abs * 2.5],
        ),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=11)),
        bargap=0.22,
    )
    return fig


def _chart_rank_bump(
    nat_df: pd.DataFrame,
    ut_df: pd.DataFrame,
    metric: str,
    metric_label: str,
    title: str,
    subtitle: str,
    top_n: int = 15,
) -> go.Figure:
    """Slope/bump chart showing rank changes between National and Utah."""
    nat = nat_df.sort_values(metric, ascending=False).head(top_n).copy()
    nat["rank_nat"] = range(1, len(nat) + 1)

    # Get all categories that appear in national top N
    cats = nat["category"].tolist()

    ut = ut_df.copy()
    ut["rank_ut_full"] = ut[metric].rank(ascending=False, method="min").astype(int)

    merged = nat[["category", "rank_nat"]].merge(
        ut[["category", "rank_ut_full"]], on="category", how="left",
    )
    merged["rank_ut_full"] = merged["rank_ut_full"].fillna(top_n + 5).astype(int)

    fig = go.Figure()

    for _, row in merged.iterrows():
        shift = row["rank_nat"] - row["rank_ut_full"]
        if abs(shift) >= RANK_SHIFT_THRESHOLD:
            color = COLORS["utah"] if shift < 0 else COLORS["national"]
            width = 2.5
            opacity = 0.9
        else:
            color = COLORS["muted"]
            width = 1.2
            opacity = 0.4

        fig.add_trace(go.Scatter(
            x=["National", "Utah"],
            y=[row["rank_nat"], row["rank_ut_full"]],
            mode="lines+markers+text",
            line=dict(color=color, width=width),
            marker=dict(size=8, color=color),
            opacity=opacity,
            text=[f"#{row['rank_nat']}  {row['category']}", f"#{row['rank_ut_full']}"],
            textposition=["middle left", "middle right"],
            textfont=dict(size=9, color=color, family=FONT_FAMILY),
            showlegend=False,
            hovertemplate=(
                f"<b>{row['category']}</b><br>"
                f"National rank: #{row['rank_nat']}<br>"
                f"Utah rank: #{row['rank_ut_full']}<br>"
                f"<extra></extra>"
            ),
        ))

    style_figure(
        fig, title, subtitle=subtitle,
        width=900, height=max(500, top_n * 35 + 150),
        show_legend=False,
    )
    fig.update_layout(
        xaxis=dict(
            showgrid=False, showline=False,
            tickfont=dict(size=13, color=COLORS["text"]),
        ),
        yaxis=dict(
            autorange="reversed", showgrid=False, showline=False,
            tickfont=dict(size=10), title=None,
            dtick=1,
        ),
        margin=dict(l=280, r=120, t=80, b=60),
    )
    return fig


def _chart_tier_employment_comparison(
    nat_tier_emp: dict[str, float],
    ut_tier_emp: dict[str, float],
    nat_total: float,
    ut_total: float,
) -> go.Figure:
    """Grouped bars: share of workforce in each risk tier, nat vs ut."""
    tiers = TIER_ORDER
    nat_pcts = [nat_tier_emp.get(t, 0) / nat_total * 100 for t in tiers]
    ut_pcts = [ut_tier_emp.get(t, 0) / ut_total * 100 for t in tiers]
    tier_names = [TIER_LABELS[t] for t in tiers]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=tier_names, y=nat_pcts, name="National",
        marker=dict(color=COLORS["national"], line=dict(width=0)),
        text=[f"{p:.1f}%" for p in nat_pcts],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["national"], family=FONT_FAMILY),
    ))
    fig.add_trace(go.Bar(
        x=tier_names, y=ut_pcts, name="Utah",
        marker=dict(color=COLORS["utah"], line=dict(width=0)),
        text=[f"{p:.1f}%" for p in ut_pcts],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["utah"], family=FONT_FAMILY),
    ))

    style_figure(
        fig,
        "Risk Tier Distribution: National vs Utah",
        subtitle="Share of total workforce in each risk tier | Value method | Auto-aug ON",
        y_title="% of Workforce",
        width=1000, height=550, show_legend=True,
    )
    fig.update_layout(
        barmode="group", bargap=0.3, bargroupgap=0.08,
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   range=[0, max(max(nat_pcts), max(ut_pcts)) * 1.2]),
    )
    return fig


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    fig_dir = results / "figures"
    print("Utah vs National — generating outputs...\n")

    # ── Economy baselines ────────────────────────────────────────────────
    print("== Economy baselines ==")
    eco_nat = _economy_baseline("nat")
    eco_ut = _economy_baseline("ut")
    ut_share = eco_ut["total_emp"] / eco_nat["total_emp"] * 100
    print(f"  National: {format_workers(eco_nat['total_emp'])} workers")
    print(f"  Utah:     {format_workers(eco_ut['total_emp'])} workers ({ut_share:.1f}% of national)")

    # ══════════════════════════════════════════════════════════════════════
    # 1. ECONOMIC FOOTPRINT — Sector-level divergences
    # ══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("== 1. ECONOMIC FOOTPRINT — Sector share divergences ==")
    print("=" * 70)

    # Headline totals
    nat_combined = _run_group_totals(COMBINED_DATASETS, "nat")
    ut_combined = _run_group_totals(COMBINED_DATASETS, "ut")

    if nat_combined and ut_combined:
        nat_pct = nat_combined["total_workers"] / eco_nat["total_emp"] * 100
        ut_pct = ut_combined["total_workers"] / eco_ut["total_emp"] * 100
        print(f"  National: {nat_pct:.1f}% of workforce AI-exposed")
        print(f"  Utah:     {ut_pct:.1f}% of workforce AI-exposed")
        print(f"  Difference: {ut_pct - nat_pct:+.1f}pp")

        # Major-level share comparison
        share_workers = _compute_share_comparison(
            nat_combined["df"], ut_combined["df"], "workers_affected",
        )
        share_wages = _compute_share_comparison(
            nat_combined["df"], ut_combined["df"], "wages_affected",
        )
        save_csv(share_workers, results / "footprint_share_workers_major.csv")
        save_csv(share_wages, results / "footprint_share_wages_major.csv")

        notable_w = share_workers[share_workers["abs_share_diff"] >= SHARE_DIFF_THRESHOLD]
        print(f"\n  Notable share divergences (>={SHARE_DIFF_THRESHOLD}pp) in workers:")
        for _, row in notable_w.iterrows():
            direction = "higher in Utah" if row["share_diff_pp"] > 0 else "lower in Utah"
            print(f"    {row['category']}: {row['share_diff_pp']:+.1f}pp ({direction})")

        # Chart: share divergence
        fig = _chart_share_divergence(
            share_workers, "Workers Affected",
            "Where Utah's AI Exposure Mix Differs From National",
            "Share of AI-exposed workers by major category | Utah minus National (pp) | Combined sources",
        )
        save_figure(fig, fig_dir / "footprint_share_divergence_workers.png")

        fig = _chart_share_divergence(
            share_wages, "Wages Affected",
            "Utah's AI-Exposed Wage Distribution vs National",
            "Share of AI-exposed wages by major category | Utah minus National (pp) | Combined sources",
        )
        save_figure(fig, fig_dir / "footprint_share_divergence_wages.png")

        # Ranking comparison at major level
        rank_workers = _compare_rankings(
            nat_combined["df"], ut_combined["df"], "workers_affected", "Workers",
        )
        save_csv(rank_workers, results / "footprint_rank_comparison_major.csv")

    # Agentic vs Conversational — Utah split
    print("\n  Agentic vs Conversational (Utah)...")
    ut_agentic = _run_group_totals(AGENTIC_DATASETS, "ut")
    ut_conv = _run_group_totals(CONVERSATIONAL_DATASETS, "ut")
    nat_agentic = _run_group_totals(AGENTIC_DATASETS, "nat")
    nat_conv = _run_group_totals(CONVERSATIONAL_DATASETS, "nat")

    if ut_agentic and ut_conv and nat_agentic and nat_conv:
        nat_ag_pct = nat_agentic["total_workers"] / eco_nat["total_emp"] * 100
        nat_cv_pct = nat_conv["total_workers"] / eco_nat["total_emp"] * 100
        ut_ag_pct = ut_agentic["total_workers"] / eco_ut["total_emp"] * 100
        ut_cv_pct = ut_conv["total_workers"] / eco_ut["total_emp"] * 100

        print(f"  National — Agentic: {nat_ag_pct:.1f}%, Conversational: {nat_cv_pct:.1f}%")
        print(f"  Utah     — Agentic: {ut_ag_pct:.1f}%, Conversational: {ut_cv_pct:.1f}%")

        mode_rows = [
            {"Geography": "National", "Mode": "Agentic", "% of Workforce": nat_ag_pct,
             "Workers Affected": nat_agentic["total_workers"]},
            {"Geography": "National", "Mode": "Conversational", "% of Workforce": nat_cv_pct,
             "Workers Affected": nat_conv["total_workers"]},
            {"Geography": "Utah", "Mode": "Agentic", "% of Workforce": ut_ag_pct,
             "Workers Affected": ut_agentic["total_workers"]},
            {"Geography": "Utah", "Mode": "Conversational", "% of Workforce": ut_cv_pct,
             "Workers Affected": ut_conv["total_workers"]},
        ]
        save_csv(pd.DataFrame(mode_rows), results / "footprint_ai_mode_comparison.csv")

    # Minor-level comparison for deeper divergences
    print("\n  Minor category comparison...")
    nat_minor = _run_query(COMBINED_DATASETS, "nat", agg_level="minor")
    ut_minor = _run_query(COMBINED_DATASETS, "ut", agg_level="minor")

    if nat_minor is not None and ut_minor is not None:
        share_minor = _compute_share_comparison(nat_minor, ut_minor, "workers_affected")
        save_csv(share_minor.head(50), results / "footprint_share_workers_minor.csv")

        notable_minor = share_minor[share_minor["abs_share_diff"] >= 1.0]
        if not notable_minor.empty:
            print(f"  Notable minor-level divergences (>=1pp): {len(notable_minor)}")
            for _, row in notable_minor.head(10).iterrows():
                print(f"    {row['category']}: {row['share_diff_pp']:+.1f}pp")

    # ══════════════════════════════════════════════════════════════════════
    # 2. AI TRANSFORMATIVE POTENTIAL — Gap ranking divergences
    # ══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("== 2. AI TRANSFORMATIVE POTENTIAL — Gap ranking divergences ==")
    print("=" * 70)

    for agg_level, agg_label in [("major", "Major Category"), ("occupation", "Occupation")]:
        print(f"\n  {agg_label} level...")

        # Ceiling (MCP v4) for each geo
        nat_ceil = _run_query(
            MCP_DATASETS, "nat", agg_level=agg_level,
            sort_by="Workers Affected",
        )
        ut_ceil = _run_query(
            MCP_DATASETS, "ut", agg_level=agg_level,
            sort_by="Workers Affected",
        )
        # Current usage (AEI) for each geo
        nat_curr = _run_query(
            AEI_DATASETS, "nat", agg_level=agg_level,
            sort_by="Workers Affected",
        )
        ut_curr = _run_query(
            AEI_DATASETS, "ut", agg_level=agg_level,
            sort_by="Workers Affected",
        )

        if nat_ceil is None or ut_ceil is None or nat_curr is None or ut_curr is None:
            print(f"    SKIP — missing data")
            continue

        # Compute gap for each geo
        def _gap(ceil_df: pd.DataFrame, curr_df: pd.DataFrame) -> pd.DataFrame:
            merged = ceil_df.merge(
                curr_df, on="category", how="outer", suffixes=("_mcp", "_aei"),
            )
            for m in ["pct_tasks_affected", "workers_affected", "wages_affected"]:
                merged[f"{m}_mcp"] = merged[f"{m}_mcp"].fillna(0)
                merged[f"{m}_aei"] = merged[f"{m}_aei"].fillna(0)
                merged[f"{m}_gap"] = merged[f"{m}_mcp"] - merged[f"{m}_aei"]
            return merged

        nat_gap = _gap(nat_ceil, nat_curr)
        ut_gap = _gap(ut_ceil, ut_curr)

        # Compare gap rankings by workers
        nat_gap_ranked = nat_gap[["category", "workers_affected_gap"]].copy()
        nat_gap_ranked = nat_gap_ranked.rename(columns={"workers_affected_gap": "gap_nat"})
        nat_gap_ranked["rank_nat"] = nat_gap_ranked["gap_nat"].rank(ascending=False, method="min").astype(int)

        ut_gap_ranked = ut_gap[["category", "workers_affected_gap"]].copy()
        ut_gap_ranked = ut_gap_ranked.rename(columns={"workers_affected_gap": "gap_ut"})
        ut_gap_ranked["rank_ut"] = ut_gap_ranked["gap_ut"].rank(ascending=False, method="min").astype(int)

        gap_comp = nat_gap_ranked.merge(ut_gap_ranked, on="category", how="outer")
        gap_comp["rank_shift"] = gap_comp["rank_nat"] - gap_comp["rank_ut"]
        gap_comp["abs_rank_shift"] = gap_comp["rank_shift"].abs()
        gap_comp = gap_comp.sort_values("abs_rank_shift", ascending=False)

        save_csv(gap_comp, results / f"transformative_gap_rank_{agg_level}.csv")

        notable_shifts = gap_comp[gap_comp["abs_rank_shift"] >= RANK_SHIFT_THRESHOLD]
        print(f"    Notable rank shifts (>={RANK_SHIFT_THRESHOLD}): {len(notable_shifts)} of {len(gap_comp)}")
        for _, row in notable_shifts.head(8).iterrows():
            direction = "higher in UT" if row["rank_shift"] > 0 else "lower in UT"
            print(f"      {row['category']}: nat #{row['rank_nat']:.0f} -> ut #{row['rank_ut']:.0f} ({direction})")

        # Share of gap comparison
        gap_share = _compute_share_comparison(
            nat_gap.rename(columns={"workers_affected_gap": "workers_affected"}),
            ut_gap.rename(columns={"workers_affected_gap": "workers_affected"}),
            "workers_affected",
        )
        save_csv(gap_share, results / f"transformative_gap_share_{agg_level}.csv")

        # Chart: gap share divergence at major level
        if agg_level == "major":
            fig = _chart_share_divergence(
                gap_share, "Workers Gap",
                "AI Potential Gap: Utah's Sector Profile vs National",
                "Share of unrealized AI potential (workers gap) by major category | MCP v4 vs AEI Cumul. Both v4",
            )
            save_figure(fig, fig_dir / "transformative_gap_share_major.png")

            # Bump chart for major categories
            fig = _chart_rank_bump(
                nat_gap.rename(columns={"workers_affected_gap": "workers_gap_ranked"}),
                ut_gap.rename(columns={"workers_affected_gap": "workers_gap_ranked"}),
                "workers_gap_ranked", "Workers Gap",
                "Gap Ranking Shifts: National vs Utah",
                "Top categories by unrealized AI potential (workers gap) | MCP v4 vs AEI Both v4",
            )
            save_figure(fig, fig_dir / "transformative_rank_bump_major.png")

    # ══════════════════════════════════════════════════════════════════════
    # 3. JOB ELIMINATION RISK — Utah tier employment
    # ══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("== 3. JOB ELIMINATION RISK — Utah-specific tier analysis ==")
    print("=" * 70)

    # Get employment lookup for both geos
    from backend.compute import get_explorer_occupations
    occ_list = get_explorer_occupations()
    emp_lookup = pd.DataFrame([{
        "title_current": o["title_current"],
        "emp_nat": o.get("emp_nat", 0) or 0,
        "emp_ut": o.get("emp_ut", 0) or 0,
        "wage_nat": o.get("wage_nat", 0) or 0,
        "wage_ut": o.get("wage_ut", 0) or 0,
        "major": o.get("major", ""),
    } for o in occ_list])

    # Run usage-confirmed pipeline at occupation level (both geos)
    nat_usage = _run_query(
        USAGE_DATASETS, "nat", agg_level="occupation",
        method="imp", sort_by="% Tasks Affected",
    )
    ut_usage = _run_query(
        USAGE_DATASETS, "ut", agg_level="occupation",
        method="imp", sort_by="% Tasks Affected",
    )

    if nat_usage is not None and ut_usage is not None:
        # Tier assignment (same tiers — % tasks is geo-independent)
        nat_tiered = nat_usage.merge(
            emp_lookup, left_on="category", right_on="title_current", how="left",
        )
        nat_tiered["tier"] = nat_tiered["pct_tasks_affected"].apply(_assign_tier)

        ut_tiered = ut_usage.merge(
            emp_lookup, left_on="category", right_on="title_current", how="left",
        )
        ut_tiered["tier"] = ut_tiered["pct_tasks_affected"].apply(_assign_tier)

        # Tier employment comparison
        nat_tier_emp = nat_tiered.groupby("tier")["emp_nat"].sum().to_dict()
        ut_tier_emp = ut_tiered.groupby("tier")["emp_ut"].sum().to_dict()
        nat_total_emp = emp_lookup["emp_nat"].sum()
        ut_total_emp = emp_lookup["emp_ut"].sum()

        tier_comp_rows = []
        for t in TIER_ORDER:
            nat_e = nat_tier_emp.get(t, 0)
            ut_e = ut_tier_emp.get(t, 0)
            nat_p = nat_e / nat_total_emp * 100
            ut_p = ut_e / ut_total_emp * 100
            tier_comp_rows.append({
                "Tier": TIER_LABELS[t],
                "National Workers": nat_e,
                "National %": nat_p,
                "Utah Workers": ut_e,
                "Utah %": ut_p,
                "Difference (pp)": ut_p - nat_p,
            })
            print(f"  {TIER_LABELS[t]}: National {nat_p:.1f}%, Utah {ut_p:.1f}% ({ut_p - nat_p:+.1f}pp)")

        tier_comp_df = pd.DataFrame(tier_comp_rows)
        save_csv(tier_comp_df, results / "risk_tier_comparison.csv")

        # Chart: tier comparison
        fig = _chart_tier_employment_comparison(
            nat_tier_emp, ut_tier_emp, nat_total_emp, ut_total_emp,
        )
        save_figure(fig, fig_dir / "risk_tier_comparison.png")

        # Utah's largest at-risk occupations (moderate + high risk)
        ut_at_risk = ut_tiered[
            ut_tiered["tier"].isin(["high_risk", "moderate_risk"])
        ].sort_values("emp_ut", ascending=False).head(20)

        if not ut_at_risk.empty:
            ut_risk_out = ut_at_risk[[
                "category", "pct_tasks_affected", "emp_ut", "wage_ut",
                "workers_affected", "tier", "major",
            ]].rename(columns={
                "category": "occupation",
                "emp_ut": "utah_employment",
                "wage_ut": "utah_median_wage",
                "major": "major_category",
            })
            ut_risk_out["tier_label"] = ut_risk_out["tier"].map(TIER_LABELS)
            save_csv(ut_risk_out, results / "utah_largest_at_risk.csv")
            print(f"\n  Utah's largest at-risk occupations saved ({len(ut_risk_out)} rows)")

            # Compare Utah's top at-risk vs national's top at-risk
            nat_at_risk = nat_tiered[
                nat_tiered["tier"].isin(["high_risk", "moderate_risk"])
            ].sort_values("emp_nat", ascending=False).head(20)

            # Which occupations are in Utah's top 20 but NOT national's top 20?
            ut_top_set = set(ut_at_risk["category"].tolist())
            nat_top_set = set(nat_at_risk["category"].tolist())
            ut_unique = ut_top_set - nat_top_set
            nat_unique = nat_top_set - ut_top_set

            if ut_unique:
                print(f"\n  Occupations in Utah's top 20 at-risk but NOT national's:")
                for occ in sorted(ut_unique):
                    row = ut_at_risk[ut_at_risk["category"] == occ].iloc[0]
                    print(f"    {occ}: {row['emp_ut']:,.0f} Utah workers, {row['pct_tasks_affected']:.1f}% tasks")

            if nat_unique:
                print(f"\n  Occupations in National's top 20 at-risk but NOT Utah's:")
                for occ in sorted(nat_unique):
                    row = nat_at_risk[nat_at_risk["category"] == occ].iloc[0]
                    print(f"    {occ}: {row['emp_nat']:,.0f} nat workers, {row['pct_tasks_affected']:.1f}% tasks")

            # Chart: Utah's top at-risk occupations
            plot_df = ut_at_risk.sort_values("emp_ut", ascending=True).head(15)
            labels = [
                f"{_format_bar_label(e)}  ({p:.0f}%)"
                for e, p in zip(plot_df["emp_ut"], plot_df["pct_tasks_affected"])
            ]
            tier_colors_list = [TIER_COLORS.get(t, COLORS["muted"]) for t in plot_df["tier"]]

            fig = go.Figure(go.Bar(
                y=plot_df["category"],
                x=plot_df["emp_ut"],
                orientation="h",
                marker=dict(color=tier_colors_list, line=dict(width=0)),
                text=labels,
                textposition="outside",
                textfont=dict(size=11, color=COLORS["neutral"], family=FONT_FAMILY),
                cliponaxis=False,
            ))
            style_figure(
                fig,
                "Utah's Largest At-Risk Occupations",
                subtitle="Moderate + High risk occupations by Utah employment | Value | Auto-aug ON",
                height=max(450, len(plot_df) * 38 + 150),
                show_legend=False,
            )
            fig.update_layout(
                margin=dict(l=20, r=100),
                xaxis=dict(showgrid=False, showticklabels=False, showline=False, zeroline=False),
                yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=11)),
                bargap=0.25,
            )
            save_figure(fig, fig_dir / "utah_largest_at_risk.png")

        # Risk by major category — share comparison
        print("\n  Risk concentration by major category...")
        for geo_label, tiered_df, emp_col in [
            ("nat", nat_tiered, "emp_nat"), ("ut", ut_tiered, "emp_ut"),
        ]:
            tier_major = (
                tiered_df.groupby(["major", "tier"])
                .agg(total_emp=(emp_col, "sum"))
                .reset_index()
            )
            major_total = tiered_df.groupby("major")[emp_col].sum().reset_index()
            major_total.columns = ["major", "major_total"]
            tier_major = tier_major.merge(major_total, on="major", how="left")
            tier_major["pct_of_major"] = tier_major["total_emp"] / tier_major["major_total"] * 100
            save_csv(tier_major, results / f"risk_by_major_{geo_label}.csv")

        # Compute the difference in moderate+high share per major
        nat_risk_share = (
            nat_tiered[nat_tiered["tier"].isin(["high_risk", "moderate_risk"])]
            .groupby("major")["emp_nat"].sum()
        )
        nat_major_total = nat_tiered.groupby("major")["emp_nat"].sum()
        nat_risk_pct = (nat_risk_share / nat_major_total * 100).fillna(0)

        ut_risk_share = (
            ut_tiered[ut_tiered["tier"].isin(["high_risk", "moderate_risk"])]
            .groupby("major")["emp_ut"].sum()
        )
        ut_major_total = ut_tiered.groupby("major")["emp_ut"].sum()
        ut_risk_pct = (ut_risk_share / ut_major_total * 100).fillna(0)

        risk_major_comp = pd.DataFrame({
            "category": nat_risk_pct.index,
            "nat_moderate_high_pct": nat_risk_pct.values,
        }).merge(
            pd.DataFrame({
                "category": ut_risk_pct.index,
                "ut_moderate_high_pct": ut_risk_pct.values,
            }),
            on="category", how="outer",
        ).fillna(0)
        risk_major_comp["diff_pp"] = risk_major_comp["ut_moderate_high_pct"] - risk_major_comp["nat_moderate_high_pct"]
        risk_major_comp["abs_diff"] = risk_major_comp["diff_pp"].abs()
        risk_major_comp = risk_major_comp.sort_values("abs_diff", ascending=False)
        save_csv(risk_major_comp, results / "risk_major_moderate_high_comparison.csv")

        notable_risk = risk_major_comp[risk_major_comp["abs_diff"] >= 2.0]
        if not notable_risk.empty:
            print(f"\n  Notable differences in moderate+high risk share by major (>=2pp):")
            for _, row in notable_risk.iterrows():
                direction = "more at-risk in Utah" if row["diff_pp"] > 0 else "less at-risk in Utah"
                print(f"    {row['category']}: {row['diff_pp']:+.1f}pp ({direction})")

    # ── Capability ceiling — Utah tier shift ─────────────────────────────
    print("\n  Capability ceiling tier comparison...")
    nat_cap = _run_query(
        CAPABILITY_DATASETS, "nat", agg_level="occupation",
        method="imp", combine_method="Max", sort_by="% Tasks Affected",
    )
    ut_cap = _run_query(
        CAPABILITY_DATASETS, "ut", agg_level="occupation",
        method="imp", combine_method="Max", sort_by="% Tasks Affected",
    )

    if nat_cap is not None and ut_cap is not None:
        nat_cap_tiered = nat_cap.merge(
            emp_lookup, left_on="category", right_on="title_current", how="left",
        )
        nat_cap_tiered["tier"] = nat_cap_tiered["pct_tasks_affected"].apply(_assign_tier)

        ut_cap_tiered = ut_cap.merge(
            emp_lookup, left_on="category", right_on="title_current", how="left",
        )
        ut_cap_tiered["tier"] = ut_cap_tiered["pct_tasks_affected"].apply(_assign_tier)

        nat_cap_tier_emp = nat_cap_tiered.groupby("tier")["emp_nat"].sum().to_dict()
        ut_cap_tier_emp = ut_cap_tiered.groupby("tier")["emp_ut"].sum().to_dict()

        cap_tier_rows = []
        for t in TIER_ORDER:
            nat_e = nat_cap_tier_emp.get(t, 0)
            ut_e = ut_cap_tier_emp.get(t, 0)
            nat_p = nat_e / nat_total_emp * 100
            ut_p = ut_e / ut_total_emp * 100
            cap_tier_rows.append({
                "Tier": TIER_LABELS[t],
                "National Workers": nat_e,
                "National %": nat_p,
                "Utah Workers": ut_e,
                "Utah %": ut_p,
                "Difference (pp)": ut_p - nat_p,
            })
        save_csv(pd.DataFrame(cap_tier_rows), results / "risk_tier_comparison_ceiling.csv")
        print("  Saved ceiling tier comparison")

    # ══════════════════════════════════════════════════════════════════════
    # Summary CSV
    # ══════════════════════════════════════════════════════════════════════
    print("\n== Summary ==")
    summary_rows = []
    if nat_combined and ut_combined:
        summary_rows.append({
            "Analysis": "Economic Footprint",
            "Metric": "% of workforce AI-exposed",
            "National": f"{nat_combined['total_workers'] / eco_nat['total_emp'] * 100:.1f}%",
            "Utah": f"{ut_combined['total_workers'] / eco_ut['total_emp'] * 100:.1f}%",
            "Difference": f"{ut_combined['total_workers'] / eco_ut['total_emp'] * 100 - nat_combined['total_workers'] / eco_nat['total_emp'] * 100:+.1f}pp",
        })

    if nat_usage is not None and ut_usage is not None:
        for t in TIER_ORDER:
            nat_e = nat_tier_emp.get(t, 0)
            ut_e = ut_tier_emp.get(t, 0)
            nat_p = nat_e / nat_total_emp * 100
            ut_p = ut_e / ut_total_emp * 100
            summary_rows.append({
                "Analysis": "Job Risk",
                "Metric": TIER_LABELS[t],
                "National": f"{nat_p:.1f}%",
                "Utah": f"{ut_p:.1f}%",
                "Difference": f"{ut_p - nat_p:+.1f}pp",
            })

    if summary_rows:
        save_csv(pd.DataFrame(summary_rows), results / "summary.csv")

    # ── Copy key figures ─────────────────────────────────────────────────
    print("\n== Copying key figures ==")
    committed_figs = HERE / "figures"
    committed_figs.mkdir(exist_ok=True)

    key_figures = [
        "footprint_share_divergence_workers.png",
        "risk_tier_comparison.png",
        "utah_largest_at_risk.png",
        "transformative_gap_share_major.png",
    ]
    for fname in key_figures:
        src = fig_dir / fname
        if src.exists():
            shutil.copy2(src, committed_figs / fname)
            print(f"  Copied {fname}")
        else:
            print(f"  SKIP (not found): {fname}")

    # ── Generate PDF ─────────────────────────────────────────────────────
    print("\n== Generating PDF ==")
    from analysis.utils import generate_pdf
    md_path = HERE / "utah_vs_national.md"
    pdf_path = results / "utah_vs_national.pdf"
    if md_path.exists():
        generate_pdf(md_path, pdf_path)
        print(f"  Saved {pdf_path.name}")
    else:
        print(f"  SKIP — {md_path.name} not yet written")

    print("\nDone.")


if __name__ == "__main__":
    main()
