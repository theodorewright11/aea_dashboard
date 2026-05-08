"""
run.py — Time Trends: Work Activity Tipping Points

Identifies IWAs (Intermediate Work Activities) that crossed meaningful
exposure thresholds during the Sep 2024 → Feb 2026 window, using the
all_confirmed series. A "tipping point" is when an activity crossed one
of three thresholds: 10% (early signal), 33% (meaningful presence), 66%
(majority of associated work exposed).

Key outputs:
  - IWA pct_tasks_affected at each date in all_confirmed series
  - Threshold crossing events (which IWA, which threshold, when it crossed)
  - "Active expansion" IWAs: currently 10–33%, growing (about to tip)
  - Growth rate ranking: fastest-growing IWAs
  - GWA-level rollup of threshold crossings

Note: uses eco_2025 baseline (all all_confirmed series datasets are
pre-combined, is_aei=False → mcp_group → eco_2025).

Run from project root:
    venv/Scripts/python -m analysis.questions.time_trends.wa_tipping_points.run
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from analysis.config import (
    ANALYSIS_CONFIG_SERIES,
    ensure_results_dir,
)
from analysis.utils import (
    CATEGORY_PALETTE,
    COLORS,
    FONT_FAMILY,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
PRIMARY_KEY = "all_confirmed"
THRESHOLDS = [10.0, 33.0, 66.0]


def get_iwa_data(dataset_name: str) -> pd.DataFrame:
    """Return IWA-level pct_tasks_affected, workers_affected, wages_affected."""
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
    rows = group.get("iwa", [])
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    assert "category" in df.columns, "Expected 'category' column in IWA data"
    assert "pct_tasks_affected" in df.columns, "Expected 'pct_tasks_affected' column"
    return df


def get_gwa_data(dataset_name: str) -> pd.DataFrame:
    """Return GWA-level pct_tasks_affected."""
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
    rows = group.get("gwa", [])
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    series = ANALYSIS_CONFIG_SERIES[PRIMARY_KEY]
    dates = [ds.rsplit(" ", 1)[-1] for ds in series]
    first_date = dates[0]
    last_date = dates[-1]

    # ── 1. Load IWA pct at each date ─────────────────────────────────────────
    print("wa_tipping_points: loading IWA series...")
    all_iwa_rows: list[dict] = []
    for ds_name, d in zip(series, dates):
        print(f"  {ds_name}...")
        df = get_iwa_data(ds_name)
        if df.empty:
            print(f"    WARNING: no IWA data for {ds_name}")
            continue
        for _, row in df.iterrows():
            all_iwa_rows.append({
                "date": d,
                "iwa": row["category"],
                "pct_tasks_affected": float(row["pct_tasks_affected"]),
                "workers_affected": float(row.get("workers_affected", 0)),
                "wages_affected": float(row.get("wages_affected", 0)),
            })
    iwa_df = pd.DataFrame(all_iwa_rows)
    assert not iwa_df.empty, "IWA time series is empty"
    save_csv(iwa_df, results / "iwa_series.csv")
    print(f"  {iwa_df['iwa'].nunique()} IWAs tracked across {len(dates)} dates")

    # ── 2. Wide pivot (iwa × date) ────────────────────────────────────────────
    wide = iwa_df.pivot_table(
        index="iwa", columns="date", values="pct_tasks_affected"
    ).reset_index()
    date_cols = [c for c in wide.columns if c != "iwa"]
    wide[date_cols] = wide[date_cols].ffill(axis=1).fillna(0.0)

    # ── 3. Threshold crossing detection ──────────────────────────────────────
    print("wa_tipping_points: detecting threshold crossings...")
    crossing_rows: list[dict] = []
    for _, row in wide.iterrows():
        iwa = row["iwa"]
        for thresh in THRESHOLDS:
            above = False
            crossed_date = None
            for d in date_cols:
                val = float(row[d])
                if not above and val >= thresh:
                    crossed_date = d
                    above = True
                    break
            crossing_rows.append({
                "iwa": iwa,
                "threshold": thresh,
                "crossed_date": crossed_date,  # None if never crossed
                "pct_last": float(row[date_cols[-1]]),
                "pct_first": float(row[date_cols[0]]),
            })
    crossing_df = pd.DataFrame(crossing_rows)
    save_csv(crossing_df, results / "threshold_crossings.csv")

    # Crossings that happened DURING the window (not already above at start)
    during_window = crossing_df[
        (crossing_df["crossed_date"].notna()) &
        (crossing_df["crossed_date"] != first_date)
    ].copy()

    print(f"\n  Threshold crossings during the window:")
    for thresh in THRESHOLDS:
        sub = during_window[during_window["threshold"] == thresh]
        print(f"    {thresh:.0f}%: {len(sub)} IWAs crossed for the first time")

    # Save crossings-during-window
    save_csv(during_window, results / "new_threshold_crossings.csv")

    # ── 4. IWA growth metrics ────────────────────────────────────────────────
    iwa_growth: list[dict] = []
    for _, row in wide.iterrows():
        iwa = row["iwa"]
        first_val = float(row[date_cols[0]])
        last_val = float(row[date_cols[-1]])
        total_gain = last_val - first_val
        # Midpoint
        mid_idx = len(date_cols) // 2
        early_gain = float(row[date_cols[mid_idx]]) - first_val
        late_gain = last_val - float(row[date_cols[mid_idx]])

        # Current zone
        if last_val >= 66.0:
            zone = "high (>=66%)"
        elif last_val >= 33.0:
            zone = "moderate (33-66%)"
        elif last_val >= 10.0:
            zone = "emerging (10-33%)"
        else:
            zone = "low (<10%)"

        iwa_growth.append({
            "iwa": iwa,
            "pct_first": round(first_val, 2),
            "pct_last": round(last_val, 2),
            "total_gain_pp": round(total_gain, 2),
            "early_gain_pp": round(early_gain, 2),
            "late_gain_pp": round(late_gain, 2),
            "current_zone": zone,
        })
    iwa_growth_df = pd.DataFrame(iwa_growth).sort_values("total_gain_pp", ascending=False)
    save_csv(iwa_growth_df, results / "iwa_growth.csv")

    # ── 5. Active expansion zone: currently 10–33%, growing ──────────────────
    approaching = iwa_growth_df[
        (iwa_growth_df["pct_last"] >= 10.0) &
        (iwa_growth_df["pct_last"] < 33.0) &
        (iwa_growth_df["total_gain_pp"] > 3.0)
    ].sort_values("total_gain_pp", ascending=False)
    save_csv(approaching, results / "iwa_approaching_33pct.csv")
    print(f"\n  IWAs in active expansion zone (10-33%, growing): {len(approaching)}")

    # IWAs that crossed 33% during the window (were below 33% at start)
    crossed_33 = during_window[during_window["threshold"] == 33.0].sort_values(
        "pct_last", ascending=False
    )
    save_csv(crossed_33, results / "iwa_crossed_33pct.csv")

    # ── 6. Figures ────────────────────────────────────────────────────────────

    pal = list(CATEGORY_PALETTE) if hasattr(CATEGORY_PALETTE, "__iter__") else [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
        "#bcbd22", "#17becf"
    ]

    # 6a. Top 20 fastest-growing IWAs (bar chart)
    top20 = iwa_growth_df.head(20).sort_values("total_gain_pp", ascending=True)
    colors_bar = []
    for _, r in top20.iterrows():
        if r["pct_last"] >= 66:
            colors_bar.append(COLORS.get("negative", "#d62728"))
        elif r["pct_last"] >= 33:
            colors_bar.append(COLORS.get("accent", "#ff7f0e"))
        else:
            colors_bar.append(COLORS.get("primary", "#1f77b4"))

    short_labels = [
        (s[:45] + "...") if len(s) > 45 else s for s in top20["iwa"].tolist()
    ]
    fig_top20 = go.Figure(go.Bar(
        x=top20["total_gain_pp"],
        y=short_labels,
        orientation="h",
        marker_color=colors_bar,
        text=[f"+{v:.1f}pp -> {l:.1f}%"
              for v, l in zip(top20["total_gain_pp"], top20["pct_last"])],
        textposition="outside",
        textfont=dict(size=9, color="#333", family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(fig_top20,
                 "Top 20 Fastest-Growing IWAs",
                 subtitle=f"All Confirmed series | {first_date} to {last_date} | "
                          "Color: orange=now>=33%, red=now>=66%",
                 x_title="Total gain (percentage points)",
                 show_legend=False,
                 height=700, width=1050)
    fig_top20.update_layout(
        margin=dict(l=20, r=160),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        yaxis=dict(showgrid=False),
        bargap=0.25,
    )
    save_figure(fig_top20, results / "figures" / "top20_iwa_growth.png")
    shutil.copy(results / "figures" / "top20_iwa_growth.png",
                figs_dir / "top20_iwa_growth.png")
    print("  top20_iwa_growth.png")

    # 6b. IWAs that crossed 33% — when they crossed (bubble on timeline)
    crossed_33_all = crossing_df[
        (crossing_df["threshold"] == 33.0) & (crossing_df["crossed_date"].notna())
    ].copy()
    crossed_33_all_sorted = crossed_33_all.sort_values("pct_last", ascending=False)

    crossing_counts = crossed_33_all_sorted.groupby("crossed_date").size().reset_index(name="count")
    # Bar per date showing how many crossed 33%
    fig_cross = go.Figure(go.Bar(
        x=crossing_counts["crossed_date"],
        y=crossing_counts["count"],
        marker_color=COLORS.get("accent", "#ff7f0e"),
        text=crossing_counts["count"].astype(str),
        textposition="outside",
        textfont=dict(size=11, color="#333", family=FONT_FAMILY),
    ))
    style_figure(fig_cross,
                 "IWAs Crossing 33% Threshold — When They First Crossed",
                 subtitle="All Confirmed series | Count of IWAs crossing 33% for first time at each date",
                 x_title="Dataset date",
                 y_title="Count of IWAs",
                 show_legend=False,
                 height=430, width=850)
    fig_cross.update_layout(margin=dict(l=60, r=20), bargap=0.4)
    save_figure(fig_cross, results / "figures" / "iwa_33pct_crossing_dates.png")
    shutil.copy(results / "figures" / "iwa_33pct_crossing_dates.png",
                figs_dir / "iwa_33pct_crossing_dates.png")
    print("  iwa_33pct_crossing_dates.png")

    # 6c. Active expansion zone: IWAs approaching 33%
    if not approaching.empty:
        top_approach = approaching.head(20).sort_values("total_gain_pp", ascending=True)
        short_labels_ap = [
            (s[:45] + "...") if len(s) > 45 else s for s in top_approach["iwa"].tolist()
        ]
        fig_approach = go.Figure(go.Bar(
            x=top_approach["pct_last"],
            y=short_labels_ap,
            orientation="h",
            marker_color=COLORS.get("primary", "#1f77b4"),
            text=[f"{v:.1f}% (+{g:.1f}pp)"
                  for v, g in zip(top_approach["pct_last"], top_approach["total_gain_pp"])],
            textposition="outside",
            textfont=dict(size=9, color="#333", family=FONT_FAMILY),
            cliponaxis=False,
        ))
        # Add vertical reference line at 33%
        fig_approach.add_vline(
            x=33.0, line_width=2, line_dash="dash",
            line_color=COLORS.get("accent", "#ff7f0e"),
            annotation_text="33% threshold",
            annotation_position="top right",
        )
        style_figure(fig_approach,
                     "Active Expansion Zone: IWAs Approaching 33% Threshold",
                     subtitle=f"Currently 10-33% and growing | As of {last_date} | Dashed line = 33% gate",
                     x_title="Current % Tasks Affected",
                     show_legend=False,
                     height=700, width=1000)
        fig_approach.update_layout(
            margin=dict(l=20, r=160),
            xaxis=dict(range=[0, 40], showgrid=True, gridcolor=COLORS["grid"]),
            yaxis=dict(showgrid=False),
            bargap=0.25,
        )
        save_figure(fig_approach, results / "figures" / "iwa_approaching_33pct.png")
        shutil.copy(results / "figures" / "iwa_approaching_33pct.png",
                    figs_dir / "iwa_approaching_33pct.png")
        print("  iwa_approaching_33pct.png")

    # 6d. Zone distribution over time (stacked bar of IWA counts by zone)
    zone_data: list[dict] = []
    for ds_name, d in zip(series, dates):
        sub_iwa = iwa_df[iwa_df["date"] == d]
        if sub_iwa.empty:
            continue
        zone_data.append({
            "date": d,
            "high": (sub_iwa["pct_tasks_affected"] >= 66).sum(),
            "moderate": ((sub_iwa["pct_tasks_affected"] >= 33) & (sub_iwa["pct_tasks_affected"] < 66)).sum(),
            "emerging": ((sub_iwa["pct_tasks_affected"] >= 10) & (sub_iwa["pct_tasks_affected"] < 33)).sum(),
            "low": (sub_iwa["pct_tasks_affected"] < 10).sum(),
        })
    zone_df = pd.DataFrame(zone_data)
    save_csv(zone_df, results / "iwa_zone_over_time.csv")

    fig_zone = go.Figure()
    zone_colors = {
        "high":     "#d62728",
        "moderate": "#ff7f0e",
        "emerging": "#1f77b4",
        "low":      "#aec7e8",
    }
    for zone in ["low", "emerging", "moderate", "high"]:
        if zone in zone_df.columns:
            fig_zone.add_trace(go.Bar(
                name=zone.title(),
                x=zone_df["date"],
                y=zone_df[zone],
                marker_color=zone_colors[zone],
            ))
    style_figure(fig_zone,
                 "IWA Exposure Zone Distribution Over Time",
                 subtitle="All Confirmed series | Count of IWAs in each pct threshold zone",
                 x_title="Dataset date",
                 y_title="Count of IWAs",
                 show_legend=True,
                 height=480, width=950)
    fig_zone.update_layout(barmode="stack", margin=dict(l=60, r=20))
    save_figure(fig_zone, results / "figures" / "iwa_zone_over_time.png")
    shutil.copy(results / "figures" / "iwa_zone_over_time.png",
                figs_dir / "iwa_zone_over_time.png")
    print("  iwa_zone_over_time.png")

    # ── 7. Summary ────────────────────────────────────────────────────────────
    print("\n  IWA zone counts at last date:")
    last_sub = iwa_df[iwa_df["date"] == last_date]
    for label, lo, hi in [
        (">=66%", 66, 200),
        ("33-66%", 33, 66),
        ("10-33%", 10, 33),
        ("<10%", 0, 10),
    ]:
        n = ((last_sub["pct_tasks_affected"] >= lo) &
             (last_sub["pct_tasks_affected"] < hi)).sum()
        print(f"    {label}: {n} IWAs")

    # ── 8. PDF ─────────────────────────────────────────────────────────────────
    report_path = HERE / "wa_tipping_points_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "wa_tipping_points_report.pdf")

    print("\nwa_tipping_points: done.")


if __name__ == "__main__":
    main()
