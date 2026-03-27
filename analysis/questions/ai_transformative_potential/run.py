"""
run.py — Where is AI most transformative? Potential vs. current adoption.

Compares a "ceiling on capability" (AEI Cumul. (Both) v4 + MCP Cumul. v4 +
Microsoft, combined with Max) against "current usage" (AEI Cumul. (Both) v4
alone) to find occupations/sectors with the largest unrealized AI potential.

Also runs a sensitivity test on the current-usage side: does adding Microsoft
(on Average or Max) significantly change the numbers?

Produces three ranked views at each of 3 aggregation levels (major, minor,
occupation) under 4 config variants (Time/Value x auto-aug ON/OFF):
  1. Ceiling (all sources, Max) -> capability ceiling
  2. AEI Cumul. (Both) v4 alone -> current adoption
  3. Gap (Ceiling - Current) -> unrealized potential

Usage from project root:
    venv/Scripts/python -m analysis.questions.ai_transformative_potential.run
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

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
    describe_config,
    format_workers,
    format_wages,
    format_pct,
    COLORS,
    FONT_FAMILY,
    CATEGORY_PALETTE,
)

HERE = Path(__file__).resolve().parent

# ── Constants ────────────────────────────────────────────────────────────────

METRICS = ["pct_tasks_affected", "workers_affected", "wages_affected"]
METRIC_LABELS = {
    "pct_tasks_affected": "% Tasks Affected",
    "workers_affected": "Workers Affected",
    "wages_affected": "Wages Affected",
}
METRIC_FORMATTERS = {
    "pct_tasks_affected": format_pct,
    "workers_affected": format_workers,
    "wages_affected": format_wages,
}

AGG_LEVELS = ["major", "minor", "occupation"]
AGG_LABELS = {"major": "Major Category", "minor": "Minor Category", "occupation": "Occupation"}

TOP_N = 20
TOP_N_FULL = 30  # for CSVs (more rows than charts)

CONFIG_VARIANTS = [
    {"label": "Time, Auto-aug ON",  "method": "freq", "use_auto_aug": True},
    {"label": "Time, Auto-aug OFF", "method": "freq", "use_auto_aug": False},
    {"label": "Value, Auto-aug ON",  "method": "imp",  "use_auto_aug": True},
    {"label": "Value, Auto-aug OFF", "method": "imp",  "use_auto_aug": False},
]

# The two sides we're comparing
CEILING_DATASETS = ["AEI Cumul. (Both) v4", "MCP Cumul. v4", "Microsoft"]
CEILING_COMBINE = "Max"
CURRENT_DATASETS = ["AEI Cumul. (Both) v4"]

# Microsoft sensitivity test for current usage
CURRENT_PLUS_MS_DATASETS = ["AEI Cumul. (Both) v4", "Microsoft"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _base_config(
    agg_level: str, method: str, use_auto_aug: bool,
    combine_method: str = "Average",
) -> dict[str, Any]:
    """Build a base config with no datasets yet (caller sets selected_datasets)."""
    return make_config(
        DEFAULT_OCC_CONFIG,
        combine_method=combine_method,
        method=method,
        use_auto_aug=use_auto_aug,
        physical_mode="all",
        geo="nat",
        agg_level=agg_level,
        sort_by="Workers Affected",
        top_n=300,  # get all rows; we'll slice later
        search_query="",
    )


def _run_single(
    datasets: list[str], agg_level: str, method: str, use_auto_aug: bool,
    combine_method: str = "Average",
) -> pd.DataFrame | None:
    """Run the pipeline for one dataset selection + config, return full df."""
    cfg = _base_config(agg_level, method, use_auto_aug, combine_method=combine_method)
    cfg["selected_datasets"] = datasets
    result = run_occ_query(cfg)
    if result is None:
        return None
    df, _ = result
    return df


def _compute_gap(ceiling_df: pd.DataFrame, current_df: pd.DataFrame) -> pd.DataFrame:
    """Compute gap = ceiling - current for each category, preserving both sides."""
    merged = ceiling_df.merge(
        current_df,
        on="category",
        how="outer",
        suffixes=("_mcp", "_aei"),
    )
    for m in METRICS:
        merged[f"{m}_mcp"] = merged[f"{m}_mcp"].fillna(0)
        merged[f"{m}_aei"] = merged[f"{m}_aei"].fillna(0)
        merged[f"{m}_gap"] = merged[f"{m}_mcp"] - merged[f"{m}_aei"]
    return merged


def _fmt(val: float) -> str:
    """Abbreviated label for bar values."""
    abs_val = abs(val)
    if abs_val >= 1_000_000_000:
        return f"${val / 1e9:.1f}B"
    if abs_val >= 1_000_000:
        return f"{val / 1e6:.1f}M" if abs_val < 10_000_000 else f"{val / 1e6:.0f}M"
    if abs_val >= 1_000:
        return f"{val / 1e3:.0f}K"
    if abs_val >= 1:
        return f"{val:.0f}"
    return f"{val:.1f}"


def _make_gap_bar_chart(
    gap_df: pd.DataFrame,
    metric: str,
    agg_level: str,
    variant_label: str,
    top_n: int = TOP_N,
) -> go.Figure:
    """Grouped horizontal bar chart: ceiling vs current side by side."""
    col_mcp = f"{metric}_mcp"
    col_aei = f"{metric}_aei"
    col_gap = f"{metric}_gap"

    plot_df = gap_df.sort_values(col_gap, ascending=False).head(top_n).copy()
    plot_df = plot_df.sort_values(col_gap, ascending=True)  # reverse for horiz bars

    aei_labels = [_fmt(v) for v in plot_df[col_aei]]
    mcp_labels = [_fmt(v) for v in plot_df[col_mcp]]

    fig = go.Figure()

    # Current bars
    fig.add_trace(go.Bar(
        y=plot_df["category"],
        x=plot_df[col_aei],
        orientation="h",
        name="Current Usage (AEI Cumul. Both v4)",
        marker=dict(color=COLORS["aei"], line=dict(width=0)),
        text=aei_labels,
        textposition="outside",
        textfont=dict(size=10, color=COLORS["aei"], family=FONT_FAMILY),
        cliponaxis=False,
        opacity=0.85,
    ))

    # Ceiling bars
    fig.add_trace(go.Bar(
        y=plot_df["category"],
        x=plot_df[col_mcp],
        orientation="h",
        name="Capability Ceiling (All Sources, Max)",
        marker=dict(color=COLORS["mcp"], line=dict(width=0)),
        text=mcp_labels,
        textposition="outside",
        textfont=dict(size=10, color=COLORS["mcp"], family=FONT_FAMILY),
        cliponaxis=False,
        opacity=0.85,
    ))

    metric_label = METRIC_LABELS[metric]
    chart_height = max(550, top_n * 38 + 160)
    style_figure(
        fig,
        f"Largest Unrealized AI Potential — {AGG_LABELS[agg_level]}",
        subtitle=f"Top {top_n} by {metric_label} gap | {variant_label}",
        x_title=None,
        height=chart_height,
    )
    fig.update_layout(
        barmode="group",
        bargap=0.2,
        bargroupgap=0.06,
        margin=dict(l=20, r=100),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False, zeroline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=11)),
        legend=dict(
            orientation="h", yanchor="top", y=-0.06, xanchor="center", x=0.5,
            font=dict(size=11, color=COLORS["neutral"]),
        ),
    )

    return fig


def _make_single_ranking_chart(
    df: pd.DataFrame,
    metric: str,
    agg_level: str,
    source_label: str,
    variant_label: str,
    color: str,
    top_n: int = TOP_N,
) -> go.Figure:
    """Simple horizontal bar chart for a single-source ranking."""
    plot_df = df.sort_values(metric, ascending=False).head(top_n)
    return make_horizontal_bar(
        plot_df,
        "category",
        metric,
        title=f"{source_label} — {AGG_LABELS[agg_level]}",
        subtitle=f"Top {top_n} by {METRIC_LABELS[metric]} | {variant_label}",
        x_title=METRIC_LABELS[metric],
        color=color,
        height=max(500, top_n * 30 + 150),
    )


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    print("AI Transformative Potential - generating outputs...\n")

    # Storage for all results (for cross-variant analysis)
    # Structure: all_results[variant_label][agg_level] = {"ceiling": df, "current": df, "gap": df}
    all_results: dict[str, dict[str, dict[str, pd.DataFrame]]] = {}

    for variant in CONFIG_VARIANTS:
        vlabel = variant["label"]
        method = variant["method"]
        use_auto_aug = variant["use_auto_aug"]
        print(f"== {vlabel} ==")
        all_results[vlabel] = {}

        # Filesystem-safe label
        vslug = vlabel.lower().replace(", ", "_").replace(" ", "_").replace("-", "")

        for agg in AGG_LEVELS:
            print(f"  {AGG_LABELS[agg]}...")

            ceiling_df = _run_single(
                CEILING_DATASETS, agg, method, use_auto_aug,
                combine_method=CEILING_COMBINE,
            )
            current_df = _run_single(CURRENT_DATASETS, agg, method, use_auto_aug)

            if ceiling_df is None or current_df is None:
                print(f"    SKIP — no data for {agg}")
                continue

            gap_df = _compute_gap(ceiling_df, current_df)
            all_results[vlabel][agg] = {
                "ceiling": ceiling_df, "current": current_df, "gap": gap_df,
            }

            # ── CSVs ──────────────────────────────────────────────────────
            ceil_sorted = ceiling_df.sort_values("workers_affected", ascending=False).head(TOP_N_FULL)
            save_csv(ceil_sorted, results / f"ceiling_{agg}_{vslug}.csv")

            cur_sorted = current_df.sort_values("workers_affected", ascending=False).head(TOP_N_FULL)
            save_csv(cur_sorted, results / f"current_{agg}_{vslug}.csv")

            gap_sorted = gap_df.sort_values("workers_affected_gap", ascending=False).head(TOP_N_FULL)
            save_csv(gap_sorted, results / f"gap_{agg}_{vslug}.csv")

            # ── Figures ───────────────────────────────────────────────────
            fig_dir = results / "figures"

            if vlabel == "Time, Auto-aug ON":
                # Full chart set for primary config
                for metric in METRICS:
                    # Gap chart
                    fig = _make_gap_bar_chart(gap_df, metric, agg, vlabel)
                    save_figure(fig, fig_dir / f"gap_{metric}_{agg}.png")

                    # Ceiling alone
                    fig = _make_single_ranking_chart(
                        ceiling_df, metric, agg,
                        "Capability Ceiling (All Sources, Max)",
                        vlabel, COLORS["mcp"],
                    )
                    save_figure(fig, fig_dir / f"ceiling_{metric}_{agg}.png")

                    # Current alone
                    fig = _make_single_ranking_chart(
                        current_df, metric, agg,
                        "Current Usage (AEI Cumul. Both v4)",
                        vlabel, COLORS["aei"],
                    )
                    save_figure(fig, fig_dir / f"current_{metric}_{agg}.png")
            else:
                # Gap chart only for secondary configs (workers metric)
                fig = _make_gap_bar_chart(
                    gap_df, "workers_affected", agg, vlabel,
                )
                save_figure(fig, fig_dir / f"gap_workers_{agg}_{vslug}.png")

    # -- Microsoft sensitivity test on current usage ----------------------------
    print("\n== Microsoft sensitivity test (current usage) ==")
    ms_sensitivity_rows: list[dict[str, Any]] = []

    for combine in ["Average", "Max"]:
        for agg in AGG_LEVELS:
            base_df = _run_single(CURRENT_DATASETS, agg, "freq", True)
            plus_ms_df = _run_single(
                CURRENT_PLUS_MS_DATASETS, agg, "freq", True,
                combine_method=combine,
            )
            if base_df is None or plus_ms_df is None:
                continue

            merged = base_df.merge(
                plus_ms_df, on="category", how="outer", suffixes=("_base", "_ms"),
            )
            for _, row in merged.iterrows():
                for m in METRICS:
                    base_val = row.get(f"{m}_base", 0) or 0
                    ms_val = row.get(f"{m}_ms", 0) or 0
                    diff = ms_val - base_val
                    pct_change = (diff / base_val * 100) if base_val != 0 else float("nan")
                    ms_sensitivity_rows.append({
                        "combine_method": combine,
                        "agg_level": agg,
                        "category": row["category"],
                        "metric": METRIC_LABELS[m],
                        "aei_only": base_val,
                        "aei_plus_microsoft": ms_val,
                        "difference": diff,
                        "pct_change": pct_change,
                    })

            # Save per-level CSV
            cslug = combine.lower()
            save_csv(
                merged.sort_values("workers_affected_base", ascending=False).head(TOP_N_FULL),
                results / f"ms_sensitivity_{cslug}_{agg}.csv",
            )

    if ms_sensitivity_rows:
        ms_df = pd.DataFrame(ms_sensitivity_rows)
        save_csv(ms_df, results / "ms_sensitivity_full.csv", float_format="%.4f")
        print("  Saved ms_sensitivity_full.csv")

        # Print summary for the report
        for combine in ["Average", "Max"]:
            sub = ms_df[
                (ms_df["combine_method"] == combine)
                & (ms_df["agg_level"] == "major")
                & (ms_df["metric"] == "Workers Affected")
            ].copy()
            if not sub.empty:
                mean_pct = sub["pct_change"].abs().mean()
                max_pct = sub["pct_change"].abs().max()
                print(f"  {combine}: mean abs % change = {mean_pct:.1f}%, max = {max_pct:.1f}%")

    # -- Cross-variant stability analysis ------------------------------------
    print("\n== Stability & toggle comparison analysis ==")

    stability_rows: list[dict[str, Any]] = []
    toggle_rows: list[dict[str, Any]] = []

    for agg in AGG_LEVELS:
        # Collect top-10 gap lists per variant
        gap_top10: dict[str, list[str]] = {}
        gap_data: dict[str, pd.DataFrame] = {}

        for variant in CONFIG_VARIANTS:
            vlabel = variant["label"]
            if agg not in all_results.get(vlabel, {}):
                continue
            gdf = all_results[vlabel][agg]["gap"]
            top10 = (
                gdf.sort_values("workers_affected_gap", ascending=False)
                .head(10)["category"]
                .tolist()
            )
            gap_top10[vlabel] = top10
            gap_data[vlabel] = gdf

        if not gap_top10:
            continue

        # Stability: categories appearing in top-10 across ALL variants
        all_top10_sets = [set(v) for v in gap_top10.values()]
        stable_cats = set.intersection(*all_top10_sets) if all_top10_sets else set()

        stability_rows.append({
            "agg_level": agg,
            "stable_top10_count": len(stable_cats),
            "stable_categories": "; ".join(sorted(stable_cats)),
            "total_variants": len(gap_top10),
        })

        # Toggle comparison: auto-aug ON vs OFF (Time method)
        on_label = "Time, Auto-aug ON"
        off_label = "Time, Auto-aug OFF"
        if on_label in gap_data and off_label in gap_data:
            on_df = gap_data[on_label].set_index("category")
            off_df = gap_data[off_label].set_index("category")
            common = on_df.index.intersection(off_df.index)
            for cat in common:
                for m in METRICS:
                    gap_col = f"{m}_gap"
                    if gap_col in on_df.columns and gap_col in off_df.columns:
                        toggle_rows.append({
                            "agg_level": agg,
                            "category": cat,
                            "metric": METRIC_LABELS[m],
                            "toggle": "Auto-aug",
                            "gap_ON": on_df.loc[cat, gap_col],
                            "gap_OFF": off_df.loc[cat, gap_col],
                            "difference": off_df.loc[cat, gap_col] - on_df.loc[cat, gap_col],
                        })

        # Toggle comparison: Time vs Value (auto-aug ON)
        time_label = "Time, Auto-aug ON"
        value_label = "Value, Auto-aug ON"
        if time_label in gap_data and value_label in gap_data:
            time_df = gap_data[time_label].set_index("category")
            value_df = gap_data[value_label].set_index("category")
            common = time_df.index.intersection(value_df.index)
            for cat in common:
                for m in METRICS:
                    gap_col = f"{m}_gap"
                    if gap_col in time_df.columns and gap_col in value_df.columns:
                        toggle_rows.append({
                            "agg_level": agg,
                            "category": cat,
                            "metric": METRIC_LABELS[m],
                            "toggle": "Method",
                            "gap_ON": time_df.loc[cat, gap_col],
                            "gap_OFF": value_df.loc[cat, gap_col],
                            "difference": value_df.loc[cat, gap_col] - time_df.loc[cat, gap_col],
                        })

    if stability_rows:
        stability_df = pd.DataFrame(stability_rows)
        save_csv(stability_df, results / "stability_summary.csv")
        print("  Saved stability_summary.csv")

    if toggle_rows:
        toggle_df = pd.DataFrame(toggle_rows)
        save_csv(toggle_df, results / "toggle_comparison.csv", float_format="%.4f")
        print("  Saved toggle_comparison.csv")

        # Summary: biggest movers per toggle
        for toggle_name in ["Auto-aug", "Method"]:
            sub = toggle_df[toggle_df["toggle"] == toggle_name].copy()
            if sub.empty:
                continue
            sub["abs_diff"] = sub["difference"].abs()
            for agg in AGG_LEVELS:
                agg_sub = sub[sub["agg_level"] == agg]
                if agg_sub.empty:
                    continue
                top_movers = (
                    agg_sub.sort_values("abs_diff", ascending=False)
                    .head(20)
                )
                slug = toggle_name.lower().replace("-", "")
                save_csv(
                    top_movers.drop(columns=["abs_diff"]),
                    results / f"toggle_movers_{slug}_{agg}.csv",
                )

    # -- Composite summary chart -----------------------------------------------
    if "Time, Auto-aug ON" in all_results and "major" in all_results["Time, Auto-aug ON"]:
        print("\n== Composite summary chart ==")
        gap_df = all_results["Time, Auto-aug ON"]["major"]["gap"]

        plot_df = gap_df.sort_values("workers_affected_gap", ascending=False).head(TOP_N)
        plot_df = plot_df.sort_values("workers_affected_gap", ascending=True)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            y=plot_df["category"],
            x=plot_df["pct_tasks_affected_gap"],
            orientation="h",
            name="% Tasks Gap",
            marker_color=COLORS["accent"],
        ))

        style_figure(
            fig,
            "Unrealized AI Potential by Major Category",
            subtitle="Gap = Ceiling (All Sources, Max) minus Current (AEI Cumul. Both v4) | Time, Auto-aug ON, National",
            x_title="% Tasks Affected Gap (pp)",
            height=max(500, TOP_N * 30 + 150),
            show_legend=True,
        )
        save_figure(fig, results / "figures" / "summary_gap_major.png")

    # -- Copy key figures to committed figures/ dir ----------------------------
    print("\n== Copying key figures for README ==")
    committed_figs = HERE / "figures"
    committed_figs.mkdir(exist_ok=True)

    import shutil
    key_figures = [
        "gap_workers_affected_major.png",
        "gap_workers_affected_occupation.png",
        "ceiling_workers_affected_major.png",
        "current_workers_affected_major.png",
        "summary_gap_major.png",
        "gap_workers_major_time_autoaug_off.png",
    ]
    fig_src = results / "figures"
    for fname in key_figures:
        src = fig_src / fname
        if src.exists():
            shutil.copy2(src, committed_figs / fname)
            print(f"  Copied {fname}")
        else:
            print(f"  SKIP (not found): {fname}")

    # -- Generate PDF ----------------------------------------------------------
    print("\n== Generating PDF ==")
    from analysis.utils import generate_pdf
    md_path = HERE / "ai_transformative_potential.md"
    pdf_path = results / "ai_transformative_potential.pdf"
    if md_path.exists():
        generate_pdf(md_path, pdf_path)
        print(f"  Saved {pdf_path.name}")
    else:
        print(f"  SKIP - {md_path.name} not found")

    print("\nDone.")


if __name__ == "__main__":
    main()
