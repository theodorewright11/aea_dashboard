"""
run.py — Field Benchmarks: Sector Breakdown

Compares which economic sectors show the highest AI exposure across multiple sources.
Each source has its own sector terminology; this script crosswalks to BLS major
occupational groups and shows where there is agreement vs. divergence.

External sector findings (hardcoded from published sources):

  AEI / Humlum & Vestergaard (2024), "Which Economic Tasks are Performed with AI":
    Computer & Math tasks account for 37.2% of all Claude conversation task-attempts.
    ~57% of AI task attempts are augmentative (AI + human), ~43% are automative.
    Top-3 task categories: Technical problem solving, Writing, Analysis & Synthesis.

  Microsoft Copilot enterprise analysis (2025), "Working With AI":
    Highest task applicability: Sales (~52%), Computer & Mathematical (~50%),
    Office & Administrative Support (~49%).
    Most common user goal GWA: Getting Information (~35% of Copilot sessions).
    ~40% of conversations show disjoint user goal / AI action IWA categories.

  ChatGPT usage study (Weidinger et al., 2025), "How People Use ChatGPT":
    Writing = 40% of work-related sessions.
    Practical Guidance = 24%.
    Seeking Information = 13.5%.
    Most use is conversational (Asking ~49%, Doing ~40%).

Our metric (all_confirmed, agg_level="major"):
    workers_affected and pct_tasks_affected by BLS major occupational group.

Figures (key ones copied to figures/):
  our_sector_rankings.png    — Our top 10 major sectors (workers_affected)
  cross_source_sectors.png   — Common high-exposure sectors across all sources

Run from project root:
    venv/Scripts/python -m analysis.questions.field_benchmarks.sector_breakdown.run
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

# ── External sector constants ─────────────────────────────────────────────────

# Microsoft Copilot enterprise analysis (2025)
# Task applicability rates by BLS major category (proxied from their top-sector analysis)
COPILOT_SECTOR_APPLICABILITY = {
    "Sales and Related Occupations":           52.0,
    "Computer and Mathematical Occupations":   50.0,
    "Office and Administrative Support":       49.0,
    "Business and Financial Operations":       44.0,
    "Management Occupations":                  41.0,
}
# Source note for display
COPILOT_NOTE = "Copilot enterprise (2025): task applicability rate by sector"

# AEI (Humlum & Vestergaard, 2024) top AI-use task categories
# These map to BLS groups: Computer/Math, Office/Admin, Management, Business/Finance
AEI_TOP_TASK_CATEGORIES = {
    "Computer & Mathematical (Technical problem solving)": 37.2,
    "Writing tasks (cross-sector)":                       22.0,
    "Analysis & Synthesis (cross-sector)":                18.0,
    "Information Retrieval (cross-sector)":               10.0,
}
AEI_NOTE = "AEI (Humlum & Vestergaard 2024): % of Claude conversation task-attempts"

# ChatGPT work-use categories (Weidinger et al., 2025)
CHATGPT_WORK_CATEGORIES = {
    "Writing":             40.0,
    "Practical Guidance":  24.0,
    "Seeking Information": 13.5,
    "Coding/Technical":    11.0,
    "Analysis":             8.0,
    "Other work use":       3.5,
}
CHATGPT_NOTE = "ChatGPT work-related sessions (Weidinger et al. 2025): % of work-related use"


def _get_sector_data(dataset_name: str) -> pd.DataFrame:
    """Get major-category sector data for one dataset."""
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
    df = data["df"]
    gc = data.get("group_col", "major")
    return df.rename(columns={gc: "sector"})[
        ["sector", "workers_affected", "wages_affected", "pct_tasks_affected"]
    ].copy()


def _build_our_sector_rankings(sector_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar: our top 10 sectors by workers_affected (all_confirmed)."""
    top = sector_df.sort_values("workers_affected", ascending=False).head(10)
    labels = top["sector"].tolist()[::-1]
    workers_m = (top["workers_affected"] / 1e6).tolist()[::-1]
    pcts = top["pct_tasks_affected"].tolist()[::-1]

    # Use palette colors for bars
    palette = CATEGORY_PALETTE
    bar_colors = [palette[i % len(palette)] for i in range(len(labels))][::-1]

    fig = go.Figure(go.Bar(
        y=labels, x=workers_m,
        orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"{w:.1f}M workers ({p:.1f}% exposure)" for w, p in zip(workers_m, pcts)],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(
        fig,
        "Top 10 Sectors by Workers Affected — AEA Dashboard (All Confirmed)",
        subtitle="National | All Confirmed config | Freq | Auto-aug ON | Numbers above bars show % task exposure",
        x_title="Workers Affected (millions)",
        height=560, width=1100,
        show_legend=False,
    )
    fig.update_layout(
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix="M", range=[0, max(workers_m) * 1.35]),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        margin=dict(l=20, r=200, t=80, b=60),
    )
    return fig


def _build_cross_source_sectors(sector_df: pd.DataFrame) -> go.Figure:
    """
    Grouped bar showing our pct_tasks_affected alongside Copilot's applicability rates
    for the sectors that appear in both (Computer/Math, Office/Admin, Sales, Business/Finance, Management).
    """
    # Sectors present in Copilot data — map Copilot labels to our sector names (partial match)
    sector_map = {
        "Sales and Related Occupations":           "Sales and Related Occupations",
        "Computer and Mathematical Occupations":   "Computer and Mathematical Occupations",
        "Office and Administrative Support":       "Office and Administrative Support Occupations",
        "Business and Financial Operations":       "Business and Financial Operations Occupations",
        "Management Occupations":                  "Management Occupations",
    }
    rows = []
    df_indexed = sector_df.set_index("sector")
    for copilot_key, our_key in sector_map.items():
        # Try exact match first, then partial
        matched = None
        if our_key in df_indexed.index:
            matched = our_key
        else:
            for idx in df_indexed.index:
                if copilot_key.split(" and ")[0].lower() in idx.lower():
                    matched = idx
                    break
        our_pct = df_indexed.loc[matched, "pct_tasks_affected"] if matched else np.nan
        copilot_pct = COPILOT_SECTOR_APPLICABILITY[copilot_key]
        rows.append({
            "sector_short": copilot_key.replace(" Occupations", "").replace(" and Administrative Support", "/Admin"),
            "our_pct": our_pct,
            "copilot_pct": copilot_pct,
        })

    df_plot = pd.DataFrame(rows).sort_values("our_pct", ascending=True)
    labels = df_plot["sector_short"].tolist()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="AEA Dashboard (All Confirmed)",
        y=labels,
        x=df_plot["our_pct"].tolist(),
        orientation="h",
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=[f"{v:.1f}%" if not np.isnan(v) else "N/A" for v in df_plot["our_pct"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    fig.add_trace(go.Bar(
        name="Copilot Enterprise (2025)",
        y=labels,
        x=df_plot["copilot_pct"].tolist(),
        orientation="h",
        marker=dict(
            color=COLORS["accent"],
            pattern=dict(shape="/", size=6, fgcolor="white"),
            line=dict(width=0.5, color=COLORS["border"]),
        ),
        text=[f"{v:.1f}%" for v in df_plot["copilot_pct"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    all_vals = df_plot["our_pct"].dropna().tolist() + df_plot["copilot_pct"].tolist()
    style_figure(
        fig,
        "Sector AI Exposure: AEA Dashboard vs. Copilot Enterprise Analysis",
        subtitle=(
            "AEA Dashboard: % of tasks touched by AI (confirmed usage) | "
            "Copilot: task applicability rate from enterprise deployment data"
        ),
        x_title="AI Task Exposure / Applicability (%)",
        height=480, width=1100,
        show_legend=True,
    )
    fig.update_layout(
        barmode="group",
        bargap=0.3,
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix="%", range=[0, max(all_vals) * 1.30]),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        legend=dict(
            orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        ),
        margin=dict(l=20, r=180, t=80, b=120),
    )
    return fig


def _build_external_task_breakdown() -> go.Figure:
    """
    Two-panel overview of how external sources slice tasks:
    AEI task categories (left) and ChatGPT work-use categories (right).
    Rendered as separate subplots so labels don't crowd each other.
    """
    from plotly.subplots import make_subplots

    aei_labels = list(AEI_TOP_TASK_CATEGORIES.keys())
    aei_vals   = list(AEI_TOP_TASK_CATEGORIES.values())
    cgpt_labels = list(CHATGPT_WORK_CATEGORIES.keys())
    cgpt_vals   = list(CHATGPT_WORK_CATEGORIES.values())

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[
            "AEI (Humlum & Vestergaard 2024)<br><sup>% of Claude conversation task-attempts</sup>",
            "ChatGPT (Weidinger et al. 2025)<br><sup>% of work-related sessions by use type</sup>",
        ],
        horizontal_spacing=0.12,
    )

    fig.add_trace(go.Bar(
        x=aei_labels,
        y=aei_vals,
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=[f"{v:.1f}%" for v in aei_vals],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
        showlegend=False,
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=cgpt_labels,
        y=cgpt_vals,
        marker=dict(
            color=COLORS["secondary"],
            line=dict(width=0),
        ),
        text=[f"{v:.1f}%" for v in cgpt_vals],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
        showlegend=False,
    ), row=1, col=2)

    max_aei  = max(aei_vals)
    max_cgpt = max(cgpt_vals)

    fig.update_layout(
        height=520, width=1150,
        title=dict(
            text="How External Studies Slice AI Task Use: AEI & ChatGPT",
            font=dict(size=16, family=FONT_FAMILY, color=COLORS["neutral"]),
            x=0.5, xanchor="center",
        ),
        margin=dict(l=60, r=60, t=120, b=140),
        plot_bgcolor=COLORS.get("bg", "white"),
        paper_bgcolor=COLORS.get("bg", "white"),
    )
    fig.update_xaxes(
        tickfont=dict(size=10, family=FONT_FAMILY),
        tickangle=-30,
        showgrid=False,
        row=1, col=1,
    )
    fig.update_xaxes(
        tickfont=dict(size=10, family=FONT_FAMILY),
        tickangle=-30,
        showgrid=False,
        row=1, col=2,
    )
    fig.update_yaxes(
        ticksuffix="%",
        showgrid=True,
        gridcolor=COLORS["grid"],
        range=[0, max_aei * 1.30],
        tickfont=dict(size=10, family=FONT_FAMILY),
        row=1, col=1,
    )
    fig.update_yaxes(
        ticksuffix="%",
        showgrid=True,
        gridcolor=COLORS["grid"],
        range=[0, max_cgpt * 1.30],
        tickfont=dict(size=10, family=FONT_FAMILY),
        row=1, col=2,
    )
    return fig


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("sector_breakdown: loading sector data (all_confirmed)...")
    primary_df = _get_sector_data(ANALYSIS_CONFIGS[PRIMARY_KEY])
    assert not primary_df.empty, "No sector data loaded"

    # Also get ceiling for comparison
    ceiling_df = _get_sector_data(ANALYSIS_CONFIGS["all_ceiling"])

    print(f"  {len(primary_df)} major sectors loaded")
    print("\n-- Top 5 sectors (all_confirmed, workers_affected) --")
    for _, r in primary_df.sort_values("workers_affected", ascending=False).head(5).iterrows():
        print(f"  {r['sector']:<45}: {r['workers_affected']/1e6:.1f}M workers, {r['pct_tasks_affected']:.1f}%")

    # Save CSVs
    save_csv(primary_df.sort_values("workers_affected", ascending=False),
             results / "sector_confirmed.csv")
    if not ceiling_df.empty:
        save_csv(ceiling_df.sort_values("workers_affected", ascending=False),
                 results / "sector_ceiling.csv")
    save_csv(pd.DataFrame([
        {"source": "Copilot Enterprise (2025)", "sector": k, "applicability_pct": v}
        for k, v in COPILOT_SECTOR_APPLICABILITY.items()
    ]), results / "copilot_sector_data.csv")
    save_csv(pd.DataFrame([
        {"source": "AEI (2024)", "task_category": k, "share_pct": v}
        for k, v in AEI_TOP_TASK_CATEGORIES.items()
    ]), results / "aei_task_categories.csv")
    save_csv(pd.DataFrame([
        {"source": "ChatGPT usage (2025)", "use_type": k, "share_pct": v}
        for k, v in CHATGPT_WORK_CATEGORIES.items()
    ]), results / "chatgpt_work_categories.csv")
    print("\n  CSVs saved.")

    # Figures
    print("  Building figures...")
    fig = _build_our_sector_rankings(primary_df)
    save_figure(fig, results / "figures" / "our_sector_rankings.png")
    shutil.copy(results / "figures" / "our_sector_rankings.png",
                figs_dir / "our_sector_rankings.png")
    print("    our_sector_rankings.png")

    fig = _build_cross_source_sectors(primary_df)
    save_figure(fig, results / "figures" / "cross_source_sectors.png")
    shutil.copy(results / "figures" / "cross_source_sectors.png",
                figs_dir / "cross_source_sectors.png")
    print("    cross_source_sectors.png")

    fig = _build_external_task_breakdown()
    save_figure(fig, results / "figures" / "external_task_breakdown.png")
    shutil.copy(results / "figures" / "external_task_breakdown.png",
                figs_dir / "external_task_breakdown.png")
    print("    external_task_breakdown.png")

    # PDF
    md_path = HERE / "sector_breakdown_report.md"
    if md_path.exists():
        generate_pdf(md_path, results / "sector_breakdown_report.pdf")

    print("\nsector_breakdown: done.")


if __name__ == "__main__":
    main()
