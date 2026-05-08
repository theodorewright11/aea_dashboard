"""
run.py — Job Exposure: Current State of Exposure

What is the current state of AI task exposure across all occupations?

Computes pct_tasks_affected for all 923 occupations across the five canonical
analysis configs. Assigns tiers, rolls up by major category, computes time
trends (including workers_affected trend), and surfaces minor/broad-level
deviations from the major-category ranking.

Primary config: all_confirmed. Ceiling (all_ceiling) shown as comparison layer.
Method: freq (time-weighted), auto-aug ON, national.

Tiers (applied to primary config):
  High:          >= 60%
  Moderate:      40–60%
  Restructuring: 20–40%
  Low:           < 20%

Run from project root:
    venv/Scripts/python -m analysis.questions.job_exposure.exposure_state.run
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
    ANALYSIS_CONFIG_SERIES,
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    _format_bar_label,
    format_workers,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent

# ── Primary config ────────────────────────────────────────────────────────────
PRIMARY_KEY = "all_confirmed"
CEILING_KEY = "all_ceiling"

# ── Tier thresholds ────────────────────────────────────────────────────────────

HIGH_EXP = 60.0
MOD_EXP = 40.0
REST_EXP = 20.0

TIER_ORDER = ["high", "moderate", "restructuring", "low"]
TIER_LABELS = {
    "high": "High (>=60%)",
    "moderate": "Moderate (40–60%)",
    "restructuring": "Restructuring (20–40%)",
    "low": "Low (<20%)",
}
TIER_COLORS = {
    "high": COLORS["negative"],
    "moderate": COLORS["accent"],
    "restructuring": COLORS["primary"],
    "low": COLORS["muted"],
}


def _assign_tier(pct: float) -> str:
    if pct >= HIGH_EXP:
        return "high"
    if pct >= MOD_EXP:
        return "moderate"
    if pct >= REST_EXP:
        return "restructuring"
    return "low"


# ── Employment lookup ──────────────────────────────────────────────────────────

def _get_emp_lookup() -> pd.DataFrame:
    """Return DataFrame: title_current, emp_nat, wage_nat, major, minor, broad, job_zone, outlook."""
    from backend.compute import get_explorer_occupations

    rows = []
    for occ in get_explorer_occupations():
        rows.append({
            "title_current": occ["title_current"],
            "emp_nat": occ.get("emp") or 0,
            "wage_nat": occ.get("wage") or 0,
            "major": occ.get("major", ""),
            "minor": occ.get("minor", ""),
            "broad": occ.get("broad", ""),
            "job_zone": occ.get("job_zone"),
            "outlook": occ.get("dws_star_rating"),
        })
    return pd.DataFrame(rows)


# ── Tier summary helpers ───────────────────────────────────────────────────────

def _tier_summary(df: pd.DataFrame, config_key: str) -> pd.DataFrame:
    """Count occupations and employment per tier for one config."""
    tier_col = f"tier_{config_key}"
    rows = []
    for tier in TIER_ORDER:
        mask = df[tier_col] == tier
        rows.append({
            "config": config_key,
            "config_label": ANALYSIS_CONFIG_LABELS[config_key],
            "tier": tier,
            "tier_label": TIER_LABELS[tier],
            "n_occs": int(mask.sum()),
            "emp": df.loc[mask, "emp_nat"].sum(),
        })
    return pd.DataFrame(rows)


# ── Figures ────────────────────────────────────────────────────────────────────

def _scatter_exposure_vs_emp(df: pd.DataFrame, config_key: str) -> go.Figure:
    """Scatter: pct (x) vs employment (y), colored by tier."""
    pct_col = f"pct_{config_key}"
    tier_col = f"tier_{config_key}"
    fig = go.Figure()
    for tier in TIER_ORDER:
        sub = df[df[tier_col] == tier]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub[pct_col],
            y=sub["emp_nat"],
            mode="markers",
            name=TIER_LABELS[tier],
            marker=dict(color=TIER_COLORS[tier], size=6, opacity=0.6,
                        line=dict(width=0.5, color=COLORS["bg"])),
            text=sub["title_current"],
            hovertemplate="<b>%{text}</b><br>% Tasks: %{x:.1f}%<br>Emp: %{y:,.0f}<extra></extra>",
        ))
    for thresh, label in [(HIGH_EXP, "60%"), (MOD_EXP, "40%"), (REST_EXP, "20%")]:
        fig.add_vline(x=thresh, line_dash="dot", line_color=COLORS["border"], line_width=1,
                      annotation_text=label, annotation_position="top",
                      annotation_font=dict(size=9, color=COLORS["muted"], family=FONT_FAMILY))
    style_figure(
        fig,
        f"Exposure vs Employment — {ANALYSIS_CONFIG_LABELS[config_key]}",
        subtitle="Each point = one occupation | Colored by exposure tier",
        x_title="% Tasks Affected", y_title="Total Employment",
        height=700, width=1100, show_legend=True,
    )
    fig.update_yaxes(type="log")
    fig.update_layout(
        margin=dict(l=60, r=40, t=80, b=120),
        legend=dict(
            orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        ),
    )
    return fig


def _stacked_tier_by_major(df: pd.DataFrame, config_key: str) -> go.Figure:
    """Stacked horizontal bar: % of major's occs in each tier."""
    tier_col = f"tier_{config_key}"
    by_major_tier = (
        df.groupby(["major", tier_col])
        .size()
        .reset_index(name="n")
    )
    major_totals = df.groupby("major").size().reset_index(name="total")
    by_major_tier = by_major_tier.merge(major_totals, on="major")
    by_major_tier["pct_of_major"] = by_major_tier["n"] / by_major_tier["total"] * 100

    # Sort majors by high-exposure share descending
    high_share = (
        by_major_tier[by_major_tier[tier_col] == "high"]
        .set_index("major")["pct_of_major"]
    )
    all_majors = df["major"].dropna().unique().tolist()
    major_order = sorted(all_majors, key=lambda m: high_share.get(m, 0))

    fig = go.Figure()
    for tier in reversed(TIER_ORDER):
        sub = by_major_tier[by_major_tier[tier_col] == tier].set_index("major")
        vals = [sub.loc[m, "pct_of_major"] if m in sub.index else 0 for m in major_order]
        fig.add_trace(go.Bar(
            y=major_order, x=vals, orientation="h",
            name=TIER_LABELS[tier],
            marker=dict(color=TIER_COLORS[tier], line=dict(width=0)),
        ))
    chart_h = max(600, len(major_order) * 28 + 250)
    style_figure(
        fig,
        f"Exposure Tier Makeup by Major Category — {ANALYSIS_CONFIG_LABELS[config_key]}",
        subtitle="% of occupations in each tier within major category",
        x_title=None, height=chart_h, show_legend=True,
    )
    fig.update_layout(
        barmode="stack", bargap=0.2,
        margin=dict(l=20, r=40, t=80, b=120),
        xaxis=dict(showgrid=False, showticklabels=True, ticksuffix="%",
                   tickfont=dict(size=9, color=COLORS["muted"])),
        yaxis=dict(showgrid=False, tickfont=dict(size=9, family=FONT_FAMILY)),
        legend=dict(orientation="h", yanchor="top", y=-0.10, xanchor="center", x=0.5,
                    font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY)),
    )
    return fig


def _config_comparison_scatter(df: pd.DataFrame) -> go.Figure:
    """Scatter: all_confirmed pct (x) vs all_ceiling pct (y)."""
    fig = go.Figure()
    tier_col = f"tier_{PRIMARY_KEY}"
    for tier in TIER_ORDER:
        sub = df[df[tier_col] == tier]
        fig.add_trace(go.Scatter(
            x=sub[f"pct_{PRIMARY_KEY}"],
            y=sub[f"pct_{CEILING_KEY}"],
            mode="markers",
            name=TIER_LABELS[tier],
            marker=dict(color=TIER_COLORS[tier], size=6, opacity=0.55,
                        line=dict(width=0.5, color=COLORS["bg"])),
            text=sub["title_current"],
            hovertemplate=(
                "<b>%{text}</b><br>"
                f"Confirmed: %{{x:.1f}}%<br>"
                f"Ceiling: %{{y:.1f}}%<extra></extra>"
            ),
        ))
    max_val = max(df[f"pct_{PRIMARY_KEY}"].max(), df[f"pct_{CEILING_KEY}"].max())
    fig.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val], mode="lines",
        line=dict(dash="dash", color=COLORS["border"], width=1),
        showlegend=False, hoverinfo="skip",
    ))
    style_figure(
        fig,
        "Ceiling Exceeds Confirmed Usage Across Nearly All Occupations",
        subtitle="Each dot = one occupation | Above diagonal: ceiling > confirmed usage",
        x_title="All Confirmed % Tasks Affected",
        y_title="All Sources (Ceiling) % Tasks Affected",
        height=700, width=850, show_legend=True,
    )
    fig.update_layout(
        margin=dict(l=60, r=40, t=80, b=120),
        legend=dict(
            orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        ),
    )
    return fig


def _top_climbers_chart(trend_df: pd.DataFrame, config_key: str, n: int = 20,
                        metric: str = "pct") -> go.Figure:
    """Horizontal bar: top N occupations by growth for a config."""
    col = f"{metric}_delta_{config_key}"
    label_prefix = "% Tasks" if metric == "pct" else "Workers"
    top = (
        trend_df.dropna(subset=[col])
        .nlargest(n, col)
        .sort_values(col, ascending=True)
    )

    if metric == "pct":
        labels = [f"+{v:.1f}pp" for v in top[col]]
    else:
        labels = [f"+{format_workers(v)}" for v in top[col]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top["title_current"], x=top[col], orientation="h",
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=labels, textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    chart_h = max(400, n * 38 + 200)
    style_figure(
        fig,
        f"Top {n} Fastest-Growing Occupations ({label_prefix}) — {ANALYSIS_CONFIG_LABELS[config_key]}",
        subtitle="Change from earliest to most recent date",
        x_title=None, height=chart_h, show_legend=False,
    )
    fig.update_layout(
        margin=dict(l=20, r=80, t=80, b=100),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False, zeroline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        bargap=0.25,
    )
    return fig


def _outlier_subgroups_chart(outliers: pd.DataFrame, level: str, config_key: str,
                             n: int = 20) -> go.Figure:
    """Horizontal bar: minor/broad groups that deviate from their major category ranking."""
    top = outliers.nlargest(n, "rank_deviation").sort_values("rank_deviation", ascending=True)
    labels = [f"{v:.0f} ranks higher than major avg" for v in top["rank_deviation"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top[level], x=top["rank_deviation"], orientation="h",
        marker=dict(color=COLORS["accent"], line=dict(width=0)),
        text=labels, textposition="outside",
        textfont=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    chart_h = max(400, n * 38 + 200)
    style_figure(
        fig,
        f"Surprising {level.title()} Groups — Higher Exposure Than Their Major Category",
        subtitle=f"Rank deviation: how many positions above the major category avg | {ANALYSIS_CONFIG_LABELS[config_key]}",
        x_title=None, height=chart_h, show_legend=False,
    )
    fig.update_layout(
        margin=dict(l=20, r=120, t=80, b=100),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False, zeroline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=9, family=FONT_FAMILY)),
        bargap=0.25,
    )
    return fig


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    fig_dir = results / "figures"
    print("Exposure State -- generating outputs...\n")

    # ── Employment lookup ─────────────────────────────────────────────────────
    print("Loading employment data...")
    emp = _get_emp_lookup()
    print(f"  {len(emp)} occupations\n")

    # ── Pct for all five configs ───────────────────────────────────────────────
    print("Computing pct_tasks_affected for all five configs...")
    pct_all: dict[str, pd.Series] = {}
    for config_key, dataset_name in ANALYSIS_CONFIGS.items():
        print(f"  {config_key}: {dataset_name}")
        pct_all[config_key] = get_pct_tasks_affected(dataset_name)

    # ── Build master occupation DataFrame ─────────────────────────────────────
    df = emp.copy()
    for config_key, pct in pct_all.items():
        df[f"pct_{config_key}"] = df["title_current"].map(pct).fillna(0.0)
        df[f"tier_{config_key}"] = df[f"pct_{config_key}"].apply(_assign_tier)
        # Workers affected = (pct/100) * emp
        df[f"workers_{config_key}"] = df[f"pct_{config_key}"] / 100.0 * df["emp_nat"]

    save_csv(df.rename(columns={"emp_nat": "employment", "wage_nat": "median_wage"}),
             results / "all_occupations_exposure.csv")
    print("\nSaved all_occupations_exposure.csv")

    # ── Tier summary per config ───────────────────────────────────────────────
    tier_rows = []
    for config_key in ANALYSIS_CONFIGS:
        tier_rows.append(_tier_summary(df, config_key))
    tier_by_config = pd.concat(tier_rows, ignore_index=True)
    save_csv(tier_by_config, results / "tier_by_config.csv")
    print("Saved tier_by_config.csv")

    # Print summary for primary config
    print(f"\n-- Tier distribution ({PRIMARY_KEY}) --")
    primary = tier_by_config[tier_by_config["config"] == PRIMARY_KEY]
    for _, row in primary.iterrows():
        print(f"  {row['tier_label']}: {row['n_occs']} occs, {format_workers(row['emp'])} workers")

    # Also print ceiling for comparison
    print(f"\n-- Tier distribution ({CEILING_KEY}) --")
    ceiling = tier_by_config[tier_by_config["config"] == CEILING_KEY]
    for _, row in ceiling.iterrows():
        print(f"  {row['tier_label']}: {row['n_occs']} occs, {format_workers(row['emp'])} workers")

    # ── Major-category rollup (primary config) ────────────────────────────────
    primary_tier_col = f"tier_{PRIMARY_KEY}"
    major_tier = (
        df.groupby(["major", primary_tier_col])
        .agg(n_occs=("title_current", "count"), emp=("emp_nat", "sum"))
        .reset_index()
    )
    major_totals = df.groupby("major").agg(
        total_occs=("title_current", "count"),
        total_emp=("emp_nat", "sum"),
    ).reset_index()
    major_tier = major_tier.merge(major_totals, on="major")
    major_tier["pct_of_major_occs"] = major_tier["n_occs"] / major_tier["total_occs"] * 100
    major_tier["pct_of_major_emp"] = major_tier["emp"] / major_tier["total_emp"] * 100
    major_tier = major_tier.rename(columns={primary_tier_col: "tier"})
    save_csv(major_tier, results / "major_tier_rollup.csv")
    print("Saved major_tier_rollup.csv")

    # ── Minor/Broad-level deviation analysis ─────────────────────────────────
    print("\nComputing minor/broad-level deviations from major ranking...")
    pct_col = f"pct_{PRIMARY_KEY}"

    # Major-level average pct
    major_avg = df.groupby("major")[pct_col].mean().rename("major_avg_pct")
    major_rank = major_avg.rank(ascending=False).rename("major_rank")

    for level in ["minor", "broad"]:
        level_avg = df.groupby(level)[pct_col].mean().rename(f"{level}_avg_pct")
        level_rank = level_avg.rank(ascending=False).rename(f"{level}_rank")
        level_df = pd.DataFrame(level_avg).join(level_rank)

        # Map each subgroup back to its major
        level_to_major = df.drop_duplicates(subset=[level]).set_index(level)["major"]
        level_df["major"] = level_df.index.map(level_to_major)
        level_df["major_avg_pct"] = level_df["major"].map(major_avg)
        level_df["major_rank"] = level_df["major"].map(major_rank)

        # Deviation: how many rank positions above/below the major avg
        # Positive = subgroup ranks higher (more exposed) than its major
        level_df["rank_deviation"] = level_df["major_rank"] - level_df[f"{level}_rank"]
        level_df["pct_deviation"] = level_df[f"{level}_avg_pct"] - level_df["major_avg_pct"]
        level_df = level_df.reset_index()

        save_csv(level_df, results / f"{level}_deviations.csv")
        print(f"  Saved {level}_deviations.csv")

        # Show top outliers (subgroups much higher than their major)
        outliers = level_df[level_df["pct_deviation"] > 10].nlargest(20, "pct_deviation")
        if not outliers.empty:
            print(f"  Top {level} outliers (>10pp above major avg):")
            for _, row in outliers.head(5).iterrows():
                print(f"    {row[level]}: {row[f'{level}_avg_pct']:.1f}% "
                      f"(major '{row['major']}' avg: {row['major_avg_pct']:.1f}%)")

    # ── Time trends ───────────────────────────────────────────────────────────
    print("\nComputing pct and workers_affected time trends...")
    trend_df = df[["title_current", "emp_nat", "wage_nat", "major", "minor", "broad"]].copy()
    for config_key, series in ANALYSIS_CONFIG_SERIES.items():
        if len(series) < 2:
            continue
        first_dataset, last_dataset = series[0], series[-1]
        print(f"  {config_key}: {first_dataset} -> {last_dataset}")
        pct_first = get_pct_tasks_affected(first_dataset)
        pct_last = get_pct_tasks_affected(last_dataset)
        trend_df[f"pct_first_{config_key}"] = trend_df["title_current"].map(pct_first).fillna(0)
        trend_df[f"pct_last_{config_key}"] = trend_df["title_current"].map(pct_last).fillna(0)
        trend_df[f"pct_delta_{config_key}"] = (
            trend_df[f"pct_last_{config_key}"] - trend_df[f"pct_first_{config_key}"]
        )
        # Workers affected trend
        trend_df[f"workers_first_{config_key}"] = (
            trend_df[f"pct_first_{config_key}"] / 100.0 * trend_df["emp_nat"]
        )
        trend_df[f"workers_last_{config_key}"] = (
            trend_df[f"pct_last_{config_key}"] / 100.0 * trend_df["emp_nat"]
        )
        trend_df[f"workers_delta_{config_key}"] = (
            trend_df[f"workers_last_{config_key}"] - trend_df[f"workers_first_{config_key}"]
        )

    save_csv(trend_df, results / "pct_trend_by_config.csv")
    print("Saved pct_trend_by_config.csv")

    # Print trend summary for primary config
    delta_col = f"pct_delta_{PRIMARY_KEY}"
    if delta_col in trend_df.columns:
        positive = trend_df[trend_df[delta_col] > 0]
        print(f"\n  {PRIMARY_KEY}: {len(positive)}/{len(trend_df)} occs with positive growth")
        print(f"  Median gain: {trend_df[delta_col].median():.1f}pp")

        workers_delta_col = f"workers_delta_{PRIMARY_KEY}"
        total_workers_gain = trend_df[workers_delta_col].sum()
        print(f"  Total workers affected growth: {format_workers(total_workers_gain)}")

    # ── Figures ───────────────────────────────────────────────────────────────
    print("\nGenerating figures...")

    # Scatter: primary config pct vs employment
    fig = _scatter_exposure_vs_emp(df, PRIMARY_KEY)
    save_figure(fig, fig_dir / "scatter_exposure_vs_emp_confirmed.png")
    print("  scatter_exposure_vs_emp_confirmed.png")

    # Scatter: ceiling pct vs employment (comparison)
    fig = _scatter_exposure_vs_emp(df, CEILING_KEY)
    save_figure(fig, fig_dir / "scatter_exposure_vs_emp_ceiling.png")
    print("  scatter_exposure_vs_emp_ceiling.png")

    # Stacked bar: tier by major (primary config)
    fig = _stacked_tier_by_major(df, PRIMARY_KEY)
    save_figure(fig, fig_dir / "tier_stacked_by_major.png")
    print("  tier_stacked_by_major.png")

    # Config comparison: confirmed vs ceiling
    fig = _config_comparison_scatter(df)
    save_figure(fig, fig_dir / "config_comparison.png")
    print("  config_comparison.png")

    # Top climbers: pct trend for primary config
    fig = _top_climbers_chart(trend_df, PRIMARY_KEY, metric="pct")
    save_figure(fig, fig_dir / "top_climbers_confirmed_pct.png")
    print("  top_climbers_confirmed_pct.png")

    # Top climbers: workers affected trend for primary config
    fig = _top_climbers_chart(trend_df, PRIMARY_KEY, metric="workers")
    save_figure(fig, fig_dir / "top_climbers_confirmed_workers.png")
    print("  top_climbers_confirmed_workers.png")

    # Top climbers: pct for ceiling (comparison)
    fig = _top_climbers_chart(trend_df, CEILING_KEY, metric="pct")
    save_figure(fig, fig_dir / "top_climbers_ceiling_pct.png")
    print("  top_climbers_ceiling_pct.png")

    # Minor/broad outlier charts
    for level in ["minor", "broad"]:
        deviations_file = results / f"{level}_deviations.csv"
        if deviations_file.exists():
            dev_df = pd.read_csv(deviations_file)
            outliers = dev_df[dev_df["pct_deviation"] > 5].copy()
            if len(outliers) >= 3:
                fig = _outlier_subgroups_chart(outliers, level, PRIMARY_KEY)
                save_figure(fig, fig_dir / f"{level}_outliers.png")
                print(f"  {level}_outliers.png")

    # ── Copy key figures to committed figures/ dir ────────────────────────────
    committed = HERE / "figures"
    committed.mkdir(exist_ok=True)
    key_figs = [
        "scatter_exposure_vs_emp_confirmed.png",
        "scatter_exposure_vs_emp_ceiling.png",
        "tier_stacked_by_major.png",
        "config_comparison.png",
        "top_climbers_confirmed_pct.png",
        "top_climbers_confirmed_workers.png",
        "top_climbers_ceiling_pct.png",
        "minor_outliers.png",
        "broad_outliers.png",
    ]
    for fname in key_figs:
        src = fig_dir / fname
        if src.exists():
            shutil.copy2(src, committed / fname)
            print(f"  Copied {fname} to figures/")

    # ── PDF ────────────────────────────────────────────────────────────────────
    from analysis.utils import generate_pdf
    md_path = HERE / "exposure_state_report.md"
    if md_path.exists():
        generate_pdf(md_path, results / "exposure_state_report.pdf")
        print(f"\nSaved PDF: {results / 'exposure_state_report.pdf'}")
    else:
        print(f"\nNo report markdown found at {md_path} -- skipping PDF")

    print("\nDone.")


if __name__ == "__main__":
    main()
