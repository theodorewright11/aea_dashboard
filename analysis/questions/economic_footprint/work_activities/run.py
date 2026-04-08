"""
run.py — Economic Footprint: Work Activities

What does the GWA/IWA/DWA-level footprint look like through the economic
footprint lens?

Covers:
  - GWA/IWA aggregate footprint (workers, wages, pct) across all 5 configs
  - Agentic vs conversational split at GWA level
  - WA-level trends over time (all_confirmed series, GWA level)
  - Top GWAs/IWAs by each metric (primary config)

Note: For deeper WA exposure analysis see analysis/questions/work_activity_exposure/.
This sub-question covers the economic footprint angles only — not full WA exposure
profiling.

Outputs:
  results/gwa_all_configs.csv      — GWA × 5 configs (pct, workers, wages)
  results/iwa_primary.csv          — IWA breakdown for primary config
  results/gwa_mode_comparison.csv  — GWA × mode (conv vs agentic)
  results/gwa_trend.csv            — GWA trends over all_confirmed series

Figures:
  gwa_workers.png           — Top GWAs by workers affected (primary config)
  gwa_pct.png               — Top GWAs by % tasks affected (primary config)
  gwa_config_heatmap.png    — Heatmap: GWA × config, pct_tasks_affected
  gwa_mode_butterfly.png    — Butterfly: agentic vs conversational by GWA
  gwa_trend.png             — Top 5 GWAs by pct trend over time (all_confirmed)

Run from project root:
    venv/Scripts/python -m analysis.questions.economic_footprint.work_activities.run
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
)
from analysis.utils import (
    CATEGORY_PALETTE,
    COLORS,
    FONT_FAMILY,
    format_workers,
    generate_pdf,
    make_horizontal_bar,
    make_line_chart,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
PRIMARY_KEY = "all_confirmed"
CONV_KEY = "human_conversation"
AGENTIC_KEY = "agentic_confirmed"


# -- Data helpers ---------------------------------------------------------------

def get_wa_data(dataset_name: str, level: str = "gwa") -> pd.DataFrame:
    """Get work activity exposure for a single pre-combined dataset."""
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
    # All ANALYSIS_CONFIGS are is_aei=False → mcp_group
    group = result.get("mcp_group") or result.get("aei_group")
    if group is None:
        return pd.DataFrame()
    rows = group.get(level, [])
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["dataset"] = dataset_name
    return df


def _parse_date(dataset_name: str) -> str:
    return dataset_name.rsplit(" ", 1)[-1]


# -- Figure builders ------------------------------------------------------------

def _build_gwa_config_heatmap(all_gwa: pd.DataFrame) -> go.Figure:
    """Heatmap: GWA (rows) × config (cols), pct_tasks_affected."""
    pivot = all_gwa.pivot_table(
        index="category", columns="config_label", values="pct_tasks_affected", aggfunc="first"
    )
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
    style_figure(fig, "GWA % Tasks Affected — All Five Configs",
                 subtitle="National | Freq method | Auto-aug ON",
                 show_legend=False, height=600, width=1100)
    fig.update_layout(
        xaxis=dict(side="bottom", tickangle=-20, showgrid=False, showline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        margin=dict(l=350, r=80, t=90, b=100),
    )
    return fig


def _build_gwa_butterfly(conv_df: pd.DataFrame, agentic_df: pd.DataFrame) -> go.Figure:
    """Butterfly: conversational (left) vs agentic (right) workers by GWA."""
    merged = conv_df[["category", "workers_affected"]].merge(
        agentic_df[["category", "workers_affected"]].rename(
            columns={"workers_affected": "workers_agentic"}
        ),
        on="category",
    ).sort_values("workers_affected", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[-v / 1e6 for v in merged["workers_affected"]],
        y=merged["category"],
        orientation="h",
        name="Conversational",
        marker_color=COLORS["primary"],
        text=[f"{v/1e6:.1f}M" for v in merged["workers_affected"]],
        textposition="outside",
        textfont=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    fig.add_trace(go.Bar(
        x=[v / 1e6 for v in merged["workers_agentic"]],
        y=merged["category"],
        orientation="h",
        name="Agentic",
        marker_color=COLORS["secondary"],
        text=[f"{v/1e6:.1f}M" for v in merged["workers_agentic"]],
        textposition="outside",
        textfont=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(fig, "Agentic vs Conversational Reach by Work Activity (GWA)",
                 subtitle="Left = conversational | Right = agentic | Workers affected (M)",
                 x_title="Workers Affected (millions)", height=700, width=1200)
    fig.update_layout(
        barmode="relative",
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=9)),
        margin=dict(l=20, r=100),
        bargap=0.15,
    )
    return fig


# -- Main -----------------------------------------------------------------------

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("work_activities: loading GWA data across all configs...")

    # -- 1. GWA data — all configs ----------------------------------------------
    gwa_frames: list[pd.DataFrame] = []
    for key, ds_name in ANALYSIS_CONFIGS.items():
        label = ANALYSIS_CONFIG_LABELS[key]
        print(f"  {label} (GWA)...")
        gwa = get_wa_data(ds_name, "gwa")
        if gwa.empty:
            print(f"    [no data for {ds_name}]")
            continue
        gwa["config_key"] = key
        gwa["config_label"] = label
        gwa_frames.append(gwa)

    if not gwa_frames:
        print("  No GWA data returned — aborting.")
        return

    all_gwa = pd.concat(gwa_frames, ignore_index=True)
    primary_label = ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]
    primary_gwa = all_gwa[all_gwa["config_key"] == PRIMARY_KEY].copy()

    # -- 2. IWA data — primary config only -------------------------------------
    print(f"  {primary_label} (IWA)...")
    iwa_primary = get_wa_data(ANALYSIS_CONFIGS[PRIMARY_KEY], "iwa")

    # -- 3. Mode data — conv vs agentic -----------------------------------------
    print(f"  {ANALYSIS_CONFIG_LABELS[CONV_KEY]} (GWA)...")
    conv_gwa = get_wa_data(ANALYSIS_CONFIGS[CONV_KEY], "gwa")
    print(f"  {ANALYSIS_CONFIG_LABELS[AGENTIC_KEY]} (GWA)...")
    agentic_gwa = get_wa_data(ANALYSIS_CONFIGS[AGENTIC_KEY], "gwa")

    # -- 4. Trend data — all_confirmed series ----------------------------------
    print("  GWA trends (all_confirmed series)...")
    trend_rows: list[dict] = []
    for ds_name in ANALYSIS_CONFIG_SERIES[PRIMARY_KEY]:
        gwa_t = get_wa_data(ds_name, "gwa")
        if gwa_t.empty:
            continue
        date = _parse_date(ds_name)
        for _, row in gwa_t.iterrows():
            trend_rows.append({
                "date": date,
                "category": row["category"],
                "pct_tasks_affected": row.get("pct_tasks_affected", np.nan),
                "workers_affected": row.get("workers_affected", 0),
                "wages_affected": row.get("wages_affected", 0),
            })
    gwa_trend = pd.DataFrame(trend_rows)

    # -- 5. Save CSVs ----------------------------------------------------------
    save_csv(
        all_gwa[["config_label", "category", "workers_affected", "wages_affected", "pct_tasks_affected"]],
        results / "gwa_all_configs.csv",
    )
    if not iwa_primary.empty:
        save_csv(
            iwa_primary[["category", "workers_affected", "wages_affected", "pct_tasks_affected"]]
            .sort_values("workers_affected", ascending=False),
            results / "iwa_primary.csv",
        )
    if not conv_gwa.empty and not agentic_gwa.empty:
        mode_df = pd.concat([
            conv_gwa.assign(mode="conversational", config_label=ANALYSIS_CONFIG_LABELS[CONV_KEY]),
            agentic_gwa.assign(mode="agentic", config_label=ANALYSIS_CONFIG_LABELS[AGENTIC_KEY]),
        ], ignore_index=True)
        save_csv(
            mode_df[["mode", "config_label", "category", "workers_affected", "wages_affected", "pct_tasks_affected"]],
            results / "gwa_mode_comparison.csv",
        )
    if not gwa_trend.empty:
        save_csv(gwa_trend, results / "gwa_trend.csv")
    print("  CSVs saved.")

    # -- 6. Figures -------------------------------------------------------------

    # 6a. GWA by workers affected
    if not primary_gwa.empty:
        pm_sorted_w = primary_gwa.sort_values("workers_affected", ascending=False)
        fig_w = make_horizontal_bar(
            pm_sorted_w, "category", "workers_affected",
            "General Work Activities by Workers Affected",
            subtitle=f"{primary_label} | National | Freq | Auto-aug ON",
            x_title="Workers Affected",
            color=COLORS["primary"],
            height=700, width=1200,
        )
        save_figure(fig_w, results / "figures" / "gwa_workers.png")
        shutil.copy(results / "figures" / "gwa_workers.png", figs_dir / "gwa_workers.png")
        print("  gwa_workers.png")

        # 6b. GWA by % tasks affected
        pm_sorted_pct = primary_gwa.sort_values("pct_tasks_affected", ascending=False)
        fig_pct = make_horizontal_bar(
            pm_sorted_pct, "category", "pct_tasks_affected",
            "General Work Activities by % Tasks Affected",
            subtitle=f"{primary_label} | National | Freq | Auto-aug ON",
            x_title="% Tasks Affected",
            color=COLORS["accent"],
            value_format="%.1f%%",
            height=700, width=1200,
        )
        save_figure(fig_pct, results / "figures" / "gwa_pct.png")
        shutil.copy(results / "figures" / "gwa_pct.png", figs_dir / "gwa_pct.png")
        print("  gwa_pct.png")

    # 6c. GWA × config heatmap
    fig_heat = _build_gwa_config_heatmap(all_gwa)
    save_figure(fig_heat, results / "figures" / "gwa_config_heatmap.png")
    shutil.copy(results / "figures" / "gwa_config_heatmap.png", figs_dir / "gwa_config_heatmap.png")
    print("  gwa_config_heatmap.png")

    # 6d. Mode butterfly
    if not conv_gwa.empty and not agentic_gwa.empty:
        fig_butterfly = _build_gwa_butterfly(conv_gwa, agentic_gwa)
        save_figure(fig_butterfly, results / "figures" / "gwa_mode_butterfly.png")
        shutil.copy(results / "figures" / "gwa_mode_butterfly.png", figs_dir / "gwa_mode_butterfly.png")
        print("  gwa_mode_butterfly.png")

    # 6e. GWA trend — top 5 by growth
    if not gwa_trend.empty:
        dates = sorted(gwa_trend["date"].unique())
        if len(dates) >= 2:
            first_date, last_date = dates[0], dates[-1]
            growth = (
                gwa_trend[gwa_trend["date"].isin([first_date, last_date])]
                .pivot_table(index="category", columns="date", values="pct_tasks_affected")
            )
            growth.columns = ["pct_first", "pct_last"] if growth.shape[1] == 2 else growth.columns
            if "pct_last" in growth.columns and "pct_first" in growth.columns:
                growth["gain"] = growth["pct_last"] - growth["pct_first"]
                top5_gwa = growth.sort_values("gain", ascending=False).head(5).index.tolist()
                top5_trend = gwa_trend[gwa_trend["category"].isin(top5_gwa)]
                fig_trend = make_line_chart(
                    top5_trend, "date", "pct_tasks_affected", "category",
                    "Top 5 GWAs by % Tasks Affected Growth",
                    subtitle=f"All Confirmed series | Ranked by absolute pct gain {first_date}→{last_date}",
                    y_title="% Tasks Affected",
                    x_title="Dataset date",
                )
                save_figure(fig_trend, results / "figures" / "gwa_trend.png")
                shutil.copy(results / "figures" / "gwa_trend.png", figs_dir / "gwa_trend.png")
                print("  gwa_trend.png")

    # -- 7. Summary ------------------------------------------------------------
    if not primary_gwa.empty:
        print("\n-- GWA summary (primary config) --")
        top3 = primary_gwa.sort_values("workers_affected", ascending=False).head(3)
        for _, row in top3.iterrows():
            print(f"  {row['category']}: {format_workers(row['workers_affected'])} workers, "
                  f"{row['pct_tasks_affected']:.1f}% tasks")

    # -- 8. PDF ----------------------------------------------------------------
    report_path = HERE / "work_activities_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "work_activities_report.pdf")

    print("\nwork_activities: done.")


if __name__ == "__main__":
    main()
