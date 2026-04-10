"""
run.py — Economic Footprint: Trends

How are workers/wages/% tasks affected changing over time?

Produces time-series data for all five ANALYSIS_CONFIG_SERIES:
  - Aggregate national totals (workers, wages, pct) at each series date
  - Major category-level pct_tasks_affected over time (all_confirmed series)
  - Top 10 fastest-growing major categories (by absolute pct gain, all_confirmed)
  - Cross-config aggregate trend comparison (one line per config)

Figures:
  aggregate_trend.png        — Line chart: workers affected over time, all configs
  aggregate_trend_pct.png    — Line chart: % tasks affected over time, all configs
  major_trends_confirmed.png — Line chart: top 10 major cats by growth (all_confirmed)
  major_growth_bar.png       — Bar: largest absolute pct gain by major (all_confirmed)

Run from project root:
    venv/Scripts/python -m analysis.questions.economic_footprint.trends.run
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
)
from analysis.utils import (
    CATEGORY_PALETTE,
    COLORS,
    FONT_FAMILY,
    format_workers,
    generate_pdf,
    make_line_chart,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
PRIMARY_KEY = "all_confirmed"


# -- Data helpers ---------------------------------------------------------------

def get_major_data(dataset_name: str) -> pd.DataFrame:
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
    if data is None:
        return pd.DataFrame()
    return data["df"].rename(columns={"major_occ_category": "category"})


def _get_total_employment() -> float:
    """Return total national employment from eco_2025 (fixed across dates)."""
    from backend.compute import get_explorer_occupations

    return sum(o.get("emp") or 0 for o in get_explorer_occupations())


def get_occ_totals(dataset_name: str, total_emp: float) -> dict:
    """Return aggregate national totals for a single dataset.

    Parameters
    ----------
    dataset_name : dataset key, e.g. "AEI Both + Micro 2026-02-12"
    total_emp    : total national employment (constant across dates)
    """
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
    if data is None:
        return {}
    df = data["df"]
    workers = df["workers_affected"].sum()
    wages = df["wages_affected"].sum()
    pct_emp = workers / total_emp * 100 if total_emp > 0 else 0
    # Employment-weighted avg pct_tasks_affected = total_workers / total_emp * 100
    wtd_pct = workers / total_emp * 100 if total_emp > 0 else 0
    return {
        "workers_affected": workers,
        "wages_affected": wages,
        "pct_of_employment": pct_emp,
        "pct_tasks_wtd": wtd_pct,
    }


def _parse_date(dataset_name: str) -> str:
    """Extract date string from dataset name (last space-delimited token)."""
    return dataset_name.rsplit(" ", 1)[-1]


# -- Main -----------------------------------------------------------------------

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    # -- 1. Aggregate trend — all configs --------------------------------------
    print("trends: loading total employment...")
    total_emp = _get_total_employment()
    print(f"  total employment: {total_emp/1e6:.1f}M")

    print("trends: aggregate series...")
    agg_rows: list[dict] = []
    for config_key, series in ANALYSIS_CONFIG_SERIES.items():
        label = ANALYSIS_CONFIG_LABELS[config_key]
        for ds_name in series:
            print(f"  {label} {_parse_date(ds_name)}...")
            totals = get_occ_totals(ds_name, total_emp)
            if not totals:
                continue
            agg_rows.append({
                "config_key": config_key,
                "config_label": label,
                "dataset": ds_name,
                "date": _parse_date(ds_name),
                **totals,
            })

    agg_df = pd.DataFrame(agg_rows)
    save_csv(agg_df, results / "aggregate_trend.csv")

    # -- 2. Major category trend — primary config only -------------------------
    print("\ntrends: major category series (all_confirmed)...")
    major_trend_rows: list[dict] = []
    primary_series = ANALYSIS_CONFIG_SERIES[PRIMARY_KEY]
    for ds_name in primary_series:
        major_df = get_major_data(ds_name)
        if major_df.empty:
            continue
        date = _parse_date(ds_name)
        for _, row in major_df.iterrows():
            major_trend_rows.append({
                "date": date,
                "dataset": ds_name,
                "category": row["category"],
                "workers_affected": row["workers_affected"],
                "wages_affected": row["wages_affected"],
                "pct_tasks_affected": row["pct_tasks_affected"],
            })

    major_trend = pd.DataFrame(major_trend_rows)
    save_csv(major_trend, results / "major_trend_confirmed.csv")

    # Compute growth (first -> last date)
    if not major_trend.empty:
        dates = sorted(major_trend["date"].unique())
        first_date, last_date = dates[0], dates[-1]
        first = major_trend[major_trend["date"] == first_date][["category", "pct_tasks_affected"]].rename(
            columns={"pct_tasks_affected": "pct_first"}
        )
        last = major_trend[major_trend["date"] == last_date][["category", "pct_tasks_affected"]].rename(
            columns={"pct_tasks_affected": "pct_last"}
        )
        growth = first.merge(last, on="category")
        growth["pct_gain"] = growth["pct_last"] - growth["pct_first"]
        growth["pct_gain_pct"] = (growth["pct_gain"] / growth["pct_first"].clip(0.1)) * 100
        growth = growth.sort_values("pct_gain", ascending=False)
        save_csv(growth, results / "major_growth.csv")
    else:
        growth = pd.DataFrame()

    # -- 3. Figures ------------------------------------------------------------

    # 3a. Aggregate trend — % of employment
    # Note: pct_tasks_wtd = workers_affected / total_emp * 100, so workers and
    # pct charts are proportional and look identical. Keep only the pct chart
    # (more interpretable) and drop the redundant workers chart.
    if not agg_df.empty:
        agg_pct = agg_df.pivot_table(
            index="date", columns="config_label", values="pct_tasks_wtd"
        ).reset_index()
        agg_pct_long = agg_pct.melt(id_vars="date", var_name="config_label", value_name="pct_tasks_wtd")
        agg_pct_long = agg_pct_long.dropna()

        fig_agg_pct = make_line_chart(
            agg_pct_long, "date", "pct_tasks_wtd", "config_label",
            "% of Employment Reached Over Time — All Configs",
            subtitle="National | Workers affected / total employment | Freq method | Auto-aug ON",
            y_title="% of Employment Reached",
            x_title="Dataset date",
        )
        save_figure(fig_agg_pct, results / "figures" / "aggregate_trend_pct.png")
        shutil.copy(results / "figures" / "aggregate_trend_pct.png", figs_dir / "aggregate_trend_pct.png")
        print("  aggregate_trend_pct.png")

    # 3c. Major category trend — top 10 by growth
    if not major_trend.empty and not growth.empty:
        top10_cats = growth.head(10)["category"].tolist()
        top10_trend = major_trend[major_trend["category"].isin(top10_cats)].copy()
        top10_trend = top10_trend.sort_values("date")

        fig_major = make_line_chart(
            top10_trend, "date", "pct_tasks_affected", "category",
            "Top 10 Fastest-Growing Sectors by % Tasks Affected",
            subtitle=f"All Confirmed config | Ranked by absolute pct gain {first_date}->{last_date}",
            y_title="% Tasks Affected",
            x_title="Dataset date",
        )
        save_figure(fig_major, results / "figures" / "major_trends_confirmed.png")
        shutil.copy(results / "figures" / "major_trends_confirmed.png",
                    figs_dir / "major_trends_confirmed.png")
        print("  major_trends_confirmed.png")

        # 3d. Growth bar chart
        growth_plot = growth.sort_values("pct_gain", ascending=True)
        fig_growth = go.Figure(go.Bar(
            x=growth_plot["pct_gain"],
            y=growth_plot["category"],
            orientation="h",
            marker_color=[
                COLORS["positive"] if v >= 0 else COLORS["negative"]
                for v in growth_plot["pct_gain"]
            ],
            text=[f"{v:+.1f}pp" for v in growth_plot["pct_gain"]],
            textposition="outside",
            textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
            cliponaxis=False,
        ))
        style_figure(fig_growth, "% Tasks Affected Growth by Sector",
                     subtitle=f"All Confirmed config | Absolute percentage-point gain {first_date}->{last_date}",
                     x_title="Gain (pp)", show_legend=False, height=700, width=1100)
        fig_growth.update_layout(
            margin=dict(l=20, r=100),
            xaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
            yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
            bargap=0.25,
        )
        save_figure(fig_growth, results / "figures" / "major_growth_bar.png")
        shutil.copy(results / "figures" / "major_growth_bar.png", figs_dir / "major_growth_bar.png")
        print("  major_growth_bar.png")

    # -- 4. Summary ------------------------------------------------------------
    if not agg_df.empty:
        primary_series_df = agg_df[agg_df["config_key"] == PRIMARY_KEY].sort_values("date")
        if len(primary_series_df) >= 2:
            w_first = primary_series_df.iloc[0]["workers_affected"]
            w_last = primary_series_df.iloc[-1]["workers_affected"]
            print(f"\n-- All confirmed: {format_workers(w_first)} -> {format_workers(w_last)} workers")
            print(f"   ({(w_last - w_first)/1e6:+.1f}M gain)")

    if not growth.empty:
        print("  Top 3 growing major categories (pp gain):")
        for _, row in growth.head(3).iterrows():
            print(f"    {row['category']}: {row['pct_gain']:+.1f}pp")

    # -- 5. PDF ----------------------------------------------------------------
    report_path = HERE / "trends_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "trends_report.pdf")

    print("\ntrends: done.")


if __name__ == "__main__":
    main()
