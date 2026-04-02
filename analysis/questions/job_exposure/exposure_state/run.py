"""
run.py — Job Exposure: Current State of Exposure

What is the current state of AI task exposure across all occupations?

Computes pct_tasks_affected for all 923 occupations across the five canonical
analysis configs. Assigns tiers, rolls up by major category, and computes time
trends to show which occupations are climbing fastest.

Method: freq (time-weighted), auto-aug ON, national.

Tiers (applied to all_ceiling as primary):
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
    """Return DataFrame: title_current, emp_nat, wage_nat, major, job_zone, outlook."""
    from backend.compute import get_explorer_occupations

    rows = []
    for occ in get_explorer_occupations():
        rows.append({
            "title_current": occ["title_current"],
            "emp_nat": occ.get("emp") or 0,
            "wage_nat": occ.get("wage") or 0,
            "major": occ.get("major", ""),
            "job_zone": occ.get("job_zone"),
            "outlook": occ.get("dws_star_rating"),
        })
    return pd.DataFrame(rows)


# ── Tier summary helpers ───────────────────────────────────────────────────────

def _tier_summary(df: pd.DataFrame, config_key: str) -> pd.DataFrame:
    """Count occupations and employment per tier for one config."""
    pct_col = f"pct_{config_key}"
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
        height=650, width=1100, show_legend=True,
    )
    fig.update_yaxes(type="log")
    fig.update_layout(legend=dict(
        orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5,
        font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
    ))
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
    chart_h = max(600, len(major_order) * 28 + 200)
    style_figure(
        fig,
        f"Exposure Tier Makeup by Major Category — {ANALYSIS_CONFIG_LABELS[config_key]}",
        subtitle="% of occupations in each tier within major category",
        x_title=None, height=chart_h, show_legend=True,
    )
    fig.update_layout(
        barmode="stack", bargap=0.2,
        xaxis=dict(showgrid=False, showticklabels=True, ticksuffix="%",
                   tickfont=dict(size=9, color=COLORS["muted"])),
        yaxis=dict(showgrid=False, tickfont=dict(size=9, family=FONT_FAMILY)),
        legend=dict(orientation="h", yanchor="top", y=-0.08, xanchor="center", x=0.5,
                    font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY)),
        margin=dict(l=20, r=40),
    )
    return fig


def _config_comparison_scatter(df: pd.DataFrame) -> go.Figure:
    """Scatter: human_conversation pct (x) vs all_ceiling pct (y)."""
    fig = go.Figure()
    tier_col = "tier_all_ceiling"
    for tier in TIER_ORDER:
        sub = df[df[tier_col] == tier]
        fig.add_trace(go.Scatter(
            x=sub["pct_human_conversation"],
            y=sub["pct_all_ceiling"],
            mode="markers",
            name=TIER_LABELS[tier],
            marker=dict(color=TIER_COLORS[tier], size=6, opacity=0.55,
                        line=dict(width=0.5, color=COLORS["bg"])),
            text=sub["title_current"],
            hovertemplate="<b>%{text}</b><br>Human Conv: %{x:.1f}%<br>Ceiling: %{y:.1f}%<extra></extra>",
        ))
    max_val = max(df["pct_human_conversation"].max(), df["pct_all_ceiling"].max())
    fig.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val], mode="lines",
        line=dict(dash="dash", color=COLORS["border"], width=1),
        showlegend=False, hoverinfo="skip",
    ))
    style_figure(
        fig,
        "Ceiling Far Exceeds Current Conversational Usage",
        subtitle="Each dot = one occupation | Above diagonal: ceiling exceeds human conversation usage",
        x_title="Human Conversation % Tasks Affected",
        y_title="All Sources (Ceiling) % Tasks Affected",
        height=650, width=800, show_legend=True,
    )
    fig.update_layout(legend=dict(
        orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5,
        font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
    ))
    return fig


def _top_climbers_chart(trend_df: pd.DataFrame, config_key: str, n: int = 20) -> go.Figure:
    """Horizontal bar: top N occupations by pct growth for a config."""
    col = f"pct_delta_{config_key}"
    top = (
        trend_df.dropna(subset=[col])
        .nlargest(n, col)
        .sort_values(col, ascending=True)
    )
    labels = [f"+{v:.1f}pp" for v in top[col]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top["title_current"], x=top[col], orientation="h",
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=labels, textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    chart_h = max(400, n * 38 + 150)
    style_figure(
        fig,
        f"Top {n} Fastest-Growing Occupations — {ANALYSIS_CONFIG_LABELS[config_key]}",
        subtitle="Change in % tasks affected from earliest to most recent date",
        x_title=None, height=chart_h, show_legend=False,
    )
    fig.update_layout(
        margin=dict(l=20, r=80),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False, zeroline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10, family=FONT_FAMILY)),
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

    # Print summary
    print("\n-- Tier distribution (all_ceiling) --")
    primary = tier_by_config[tier_by_config["config"] == "all_ceiling"]
    for _, row in primary.iterrows():
        print(f"  {row['tier_label']}: {row['n_occs']} occs, {format_workers(row['emp'])} workers")

    # ── Major-category rollup (primary config) ────────────────────────────────
    primary_tier_col = "tier_all_ceiling"
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

    # ── Time trends ───────────────────────────────────────────────────────────
    print("\nComputing pct time trends...")
    trend_df = df[["title_current", "emp_nat", "major"]].copy()
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

    save_csv(trend_df, results / "pct_trend_by_config.csv")
    print("Saved pct_trend_by_config.csv")

    # ── Figures ───────────────────────────────────────────────────────────────
    print("\nGenerating figures...")

    # Scatter: all_ceiling pct vs employment
    fig = _scatter_exposure_vs_emp(df, "all_ceiling")
    save_figure(fig, fig_dir / "scatter_exposure_vs_emp_ceiling.png")
    print("  scatter_exposure_vs_emp_ceiling.png")

    # Scatter: human_conversation pct vs employment
    fig = _scatter_exposure_vs_emp(df, "human_conversation")
    save_figure(fig, fig_dir / "scatter_exposure_vs_emp_human.png")
    print("  scatter_exposure_vs_emp_human.png")

    # Stacked bar: tier by major (primary config)
    fig = _stacked_tier_by_major(df, "all_ceiling")
    save_figure(fig, fig_dir / "tier_stacked_by_major.png")
    print("  tier_stacked_by_major.png")

    # Config comparison: human_conversation vs all_ceiling
    fig = _config_comparison_scatter(df)
    save_figure(fig, fig_dir / "config_comparison.png")
    print("  config_comparison.png")

    # Top climbers trend chart for primary config
    fig = _top_climbers_chart(trend_df, "all_ceiling")
    save_figure(fig, fig_dir / "top_climbers_ceiling.png")
    print("  top_climbers_ceiling.png")

    # Top climbers for human conversation (different story — conversational AI adoption)
    fig = _top_climbers_chart(trend_df, "human_conversation")
    save_figure(fig, fig_dir / "top_climbers_human_conv.png")
    print("  top_climbers_human_conv.png")

    # ── Copy key figures to committed figures/ dir ────────────────────────────
    committed = HERE / "figures"
    committed.mkdir(exist_ok=True)
    key_figs = [
        "scatter_exposure_vs_emp_ceiling.png",
        "tier_stacked_by_major.png",
        "config_comparison.png",
        "top_climbers_ceiling.png",
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
