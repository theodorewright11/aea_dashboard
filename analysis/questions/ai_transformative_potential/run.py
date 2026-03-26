"""
run.py — Where is AI most transformative? Potential vs. current adoption.

Compares AEI Cumul. v4 (where AI IS being used) against MCP v4 (where AI
CAN be used) to find occupations/sectors with the largest unrealized
AI potential.

Produces three ranked views at each of 3 aggregation levels (major, minor,
occupation) under 4 config variants (Time/Value x auto-aug ON/OFF):
  1. MCP v4 alone  -> capability ceiling
  2. AEI Cumul. v4 alone -> current adoption
  3. Gap (MCP - AEI) -> unrealized potential

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

# The two datasets we're comparing
MCP_DATASETS = ["MCP v4"]
AEI_DATASETS = ["AEI Cumul. v4"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _base_config(agg_level: str, method: str, use_auto_aug: bool) -> dict[str, Any]:
    """Build a base config with no datasets yet (caller sets selected_datasets)."""
    return make_config(
        DEFAULT_OCC_CONFIG,
        combine_method="Average",
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
) -> pd.DataFrame | None:
    """Run the pipeline for one dataset selection + config, return full df."""
    cfg = _base_config(agg_level, method, use_auto_aug)
    cfg["selected_datasets"] = datasets
    result = run_occ_query(cfg)
    if result is None:
        return None
    df, _ = result
    return df


def _compute_gap(mcp_df: pd.DataFrame, aei_df: pd.DataFrame) -> pd.DataFrame:
    """Compute gap = MCP - AEI for each category, preserving both sides."""
    merged = mcp_df.merge(
        aei_df,
        on="category",
        how="outer",
        suffixes=("_mcp", "_aei"),
    )
    for m in METRICS:
        merged[f"{m}_mcp"] = merged[f"{m}_mcp"].fillna(0)
        merged[f"{m}_aei"] = merged[f"{m}_aei"].fillna(0)
        merged[f"{m}_gap"] = merged[f"{m}_mcp"] - merged[f"{m}_aei"]
    return merged


def _make_gap_bar_chart(
    gap_df: pd.DataFrame,
    metric: str,
    agg_level: str,
    variant_label: str,
    top_n: int = TOP_N,
) -> go.Figure:
    """Grouped horizontal bar chart: MCP vs AEI with gap annotation."""
    col_mcp = f"{metric}_mcp"
    col_aei = f"{metric}_aei"
    col_gap = f"{metric}_gap"

    plot_df = gap_df.sort_values(col_gap, ascending=False).head(top_n).copy()
    plot_df = plot_df.sort_values(col_gap, ascending=True)  # reverse for horiz bars

    fig = go.Figure()

    # AEI bars (current)
    fig.add_trace(go.Bar(
        y=plot_df["category"],
        x=plot_df[col_aei],
        orientation="h",
        name="AEI Cumul. v4 (Current)",
        marker_color=COLORS["aei"],
        opacity=0.7,
    ))

    # MCP bars (capability)
    fig.add_trace(go.Bar(
        y=plot_df["category"],
        x=plot_df[col_mcp],
        orientation="h",
        name="MCP v4 (Capability)",
        marker_color=COLORS["mcp"],
        opacity=0.7,
    ))

    metric_label = METRIC_LABELS[metric]
    style_figure(
        fig,
        f"Largest Unrealized AI Potential — {AGG_LABELS[agg_level]}",
        subtitle=f"Top {top_n} by {metric_label} gap | {variant_label}",
        x_title=metric_label,
        height=max(500, top_n * 30 + 150),
    )
    fig.update_layout(barmode="group")

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
    # Structure: all_results[variant_label][agg_level] = {"mcp": df, "aei": df, "gap": df}
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

            mcp_df = _run_single(MCP_DATASETS, agg, method, use_auto_aug)
            aei_df = _run_single(AEI_DATASETS, agg, method, use_auto_aug)

            if mcp_df is None or aei_df is None:
                print(f"    SKIP — no data for {agg}")
                continue

            gap_df = _compute_gap(mcp_df, aei_df)
            all_results[vlabel][agg] = {"mcp": mcp_df, "aei": aei_df, "gap": gap_df}

            # ── CSVs ──────────────────────────────────────────────────────
            mcp_sorted = mcp_df.sort_values("workers_affected", ascending=False).head(TOP_N_FULL)
            save_csv(mcp_sorted, results / f"mcp_v4_{agg}_{vslug}.csv")

            aei_sorted = aei_df.sort_values("workers_affected", ascending=False).head(TOP_N_FULL)
            save_csv(aei_sorted, results / f"aei_cumul_v4_{agg}_{vslug}.csv")

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

                    # MCP alone
                    fig = _make_single_ranking_chart(
                        mcp_df, metric, agg, "MCP v4 (AI Capability Ceiling)",
                        vlabel, COLORS["mcp"],
                    )
                    save_figure(fig, fig_dir / f"mcp_{metric}_{agg}.png")

                    # AEI alone
                    fig = _make_single_ranking_chart(
                        aei_df, metric, agg, "AEI Cumul. v4 (Current AI Usage)",
                        vlabel, COLORS["aei"],
                    )
                    save_figure(fig, fig_dir / f"aei_{metric}_{agg}.png")
            else:
                # Gap chart only for secondary configs (workers metric)
                fig = _make_gap_bar_chart(
                    gap_df, "workers_affected", agg, vlabel,
                )
                save_figure(fig, fig_dir / f"gap_workers_{agg}_{vslug}.png")

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
            subtitle="Gap = MCP v4 minus AEI Cumul. v4 | Time, Auto-aug ON, National",
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
        "mcp_workers_affected_major.png",
        "aei_workers_affected_major.png",
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
