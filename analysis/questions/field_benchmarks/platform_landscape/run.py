"""
run.py — Field Benchmarks: Platform Landscape

A synthesis sub-folder that maps all the external sources + the AEA Dashboard
into a single methodological comparison. Doesn't compute new backend metrics —
instead, it loads our headline numbers for all five configs and produces the
cross-platform summary table, a methodology map, and a headline comparison chart.

This is the capstone view for the field_benchmarks/ bucket: after seeing how
we compare on automation share, wage impact, sector mix, and work activities,
this script zooms out and shows what all these sources are actually measuring
and where the AEA Dashboard sits within that landscape.

Sources compared:
  AEA Dashboard (this project):         Confirmed real-world AI task usage, cross-walked to BLS
  AEI (Humlum & Vestergaard 2024):      Occupational task coverage from Claude API conversation logs
  ChatGPT (Weidinger et al. 2025):      Session-level use categorization from ChatGPT logs
  Microsoft Copilot (2025):             Enterprise deployment task applicability
  Project Iceberg (Chopra et al. 2025): Skill-based technical substitutability index
  Seampoint Utah (2026, prelim.):       Governance-constrained deployment readiness for Utah

Figures (key ones copied to figures/):
  methodology_map.png      — Scatter: x=data source type, y=coverage scope, bubble=worker count
  headline_comparison.png  — All six sources' headline % numbers on one chart
  source_summary_table.png — Rendered table of methodology comparison

Run from project root:
    venv/Scripts/python -m analysis.questions.field_benchmarks.platform_landscape.run
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
    COLORS,
    FONT_FAMILY,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent

# ── All external constants ────────────────────────────────────────────────────

# Project Iceberg (Chopra et al., 2025)
ICEBERG_SURFACE  = 2.2
ICEBERG_FULL     = 11.7
ICEBERG_WORKERS  = None   # skill-value based, no direct worker count

# Seampoint Utah (2026, preliminary)
SEAMPOINT_TAKEOVER   = 20.0
SEAMPOINT_AUGMENT    = 51.0
SEAMPOINT_UT_WORKERS = 1_600_000
SEAMPOINT_UT_WAGES_B = 104.0

# AEI (Humlum & Vestergaard 2024)
AEI_HIGH_COVERAGE_PCT  = 36.0   # % occupations with ≥25% task coverage
AEI_AUGMENT_SHARE      = 57.0   # % of task-attempts that are augmentative
AEI_AUTOMATE_SHARE     = 43.0

# ChatGPT (Weidinger et al. 2025)
CHATGPT_WORK_SHARE     = 27.0   # % of all ChatGPT sessions that are work-related

# Microsoft Copilot (2025)
COPILOT_TOP_SECTOR_AVG = 50.0   # approx. average applicability rate for top 3 sectors


def _get_our_headline_numbers() -> dict:
    """Fetch headline confirmed/ceiling numbers for the platform landscape table."""
    from backend.compute import get_group_data, get_explorer_occupations

    def _pull(ds_name: str) -> dict:
        config = {
            "selected_datasets": [ds_name],
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
        return {
            "workers_affected": df["workers_affected"].sum(),
            "wages_affected":   df["wages_affected"].sum(),
        }

    all_occs = get_explorer_occupations()
    total_emp = sum(o.get("emp") or 0 for o in all_occs)

    out: dict[str, dict] = {}
    for key, ds_name in ANALYSIS_CONFIGS.items():
        nums = _pull(ds_name)
        if nums:
            nums["pct_agg"] = nums["workers_affected"] / total_emp * 100
            out[key] = nums
    return out


def _build_headline_comparison(our_nums: dict) -> go.Figure:
    """
    All headline % numbers from all sources on one horizontal bar chart.
    Color-coded by source / measurement type.
    """
    entries = []

    # Our configs
    config_order = ["agentic_confirmed", "all_confirmed", "all_ceiling"]
    color_map = {
        "agentic_confirmed": COLORS["muted"],
        "all_confirmed":     COLORS["primary"],
        "all_ceiling":       COLORS["secondary"],
    }
    for k in config_order:
        if k in our_nums:
            entries.append({
                "label":   f"AEA: {ANALYSIS_CONFIG_LABELS[k]}",
                "value":   round(our_nums[k]["pct_agg"], 1),
                "color":   color_map[k],
                "source":  "AEA Dashboard",
            })

    # External sources
    entries += [
        {"label": "AEI: Occupations ≥25% Confirmed Coverage", "value": AEI_HIGH_COVERAGE_PCT,
         "color": COLORS["neutral"], "source": "AEI (2024)"},
        {"label": "ChatGPT: Work-Related Sessions", "value": CHATGPT_WORK_SHARE,
         "color": COLORS["neutral"], "source": "ChatGPT (2025)"},
        {"label": "Copilot: Top-Sector Task Applicability", "value": COPILOT_TOP_SECTOR_AVG,
         "color": COLORS["neutral"], "source": "Copilot (2025)"},
        {"label": "Seampoint UT: AI Can Take Over", "value": SEAMPOINT_TAKEOVER,
         "color": COLORS["accent"], "source": "Seampoint (2026)"},
        {"label": "Seampoint UT: AI Can Augment", "value": SEAMPOINT_AUGMENT,
         "color": COLORS["accent"], "source": "Seampoint (2026)"},
        {"label": "Iceberg: Full Index (All Sectors)", "value": ICEBERG_FULL,
         "color": "#888", "source": "Iceberg (2025)"},
        {"label": "Iceberg: Surface Index (Tech Only)", "value": ICEBERG_SURFACE,
         "color": "#aaa", "source": "Iceberg (2025)"},
    ]

    df_plot = pd.DataFrame(entries).sort_values("value", ascending=True)

    fig = go.Figure(go.Bar(
        y=df_plot["label"].tolist(),
        x=df_plot["value"].tolist(),
        orientation="h",
        marker=dict(color=df_plot["color"].tolist(), line=dict(width=0)),
        text=[f"{v:.1f}%" for v in df_plot["value"].tolist()],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(
        fig,
        "Headline AI Exposure Numbers Across All Sources",
        subtitle=(
            "Each source measures something different — see methodology_map for full framing | "
            "AEA primary config (All Confirmed) shown in blue"
        ),
        x_title="Headline Exposure / Coverage Rate (%)",
        height=580, width=1200,
        show_legend=False,
    )
    fig.update_layout(
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix="%", range=[0, max(df_plot["value"]) * 1.25]),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        margin=dict(l=20, r=120, t=80, b=60),
    )
    return fig


def _build_methodology_map(our_nums: dict) -> go.Figure:
    """
    Scatter plot: x = data type (ordinal: usage log → deployment → capability),
    y = headline % number, size = approximate worker count (where available).
    """
    # Encode source type as x position
    # 0 = Confirmed real-world usage logs
    # 1 = Enterprise deployment / applicability
    # 2 = Governance-constrained readiness
    # 3 = Technical capability ceiling

    aea_confirmed  = our_nums.get("all_confirmed",     {})
    aea_ceiling    = our_nums.get("all_ceiling",        {})
    aea_agentic    = our_nums.get("agentic_confirmed",  {})

    entries = [
        # (label, x, y, size_M, color, symbol)
        ("AEA: Agentic Confirmed",
         0, aea_agentic.get("pct_agg", 20),
         aea_agentic.get("workers_affected", 31e6) / 1e6,
         COLORS["muted"], "circle"),
        ("AEA: All Confirmed (Primary)",
         0, aea_confirmed.get("pct_agg", 40),
         aea_confirmed.get("workers_affected", 61e6) / 1e6,
         COLORS["primary"], "circle"),
        ("AEA: Ceiling",
         3, aea_ceiling.get("pct_agg", 50),
         aea_ceiling.get("workers_affected", 77e6) / 1e6,
         COLORS["secondary"], "circle"),
        ("AEI: Occ ≥25% Coverage",
         0, AEI_HIGH_COVERAGE_PCT, 45,
         COLORS["neutral"], "diamond"),
        ("ChatGPT: Work Sessions",
         0, CHATGPT_WORK_SHARE, 30,
         COLORS["neutral"], "diamond"),
        ("Copilot: Top-Sector Applicability",
         1, COPILOT_TOP_SECTOR_AVG, 25,
         COLORS["neutral"], "square"),
        ("Seampoint: AI Can Take Over",
         2, SEAMPOINT_TAKEOVER, 1.6 * 0.20,
         COLORS["accent"], "square"),
        ("Seampoint: AI Can Augment",
         2, SEAMPOINT_AUGMENT, 1.6 * 0.51,
         COLORS["accent"], "square"),
        ("Iceberg: Full Index",
         3, ICEBERG_FULL, 20,
         "#888", "diamond"),
        ("Iceberg: Surface Index",
         3, ICEBERG_SURFACE, 5,
         "#aaa", "diamond"),
    ]

    fig = go.Figure()
    for lbl, x, y, sz, col, sym in entries:
        if y is None or np.isnan(y):
            continue
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode="markers+text",
            marker=dict(
                color=col, size=max(12, min(50, sz * 0.5)),
                symbol=sym, opacity=0.85,
                line=dict(width=1.5, color=COLORS["bg"]),
            ),
            text=[f"<b>{lbl}</b><br>{y:.1f}%"],
            textposition="top center",
            textfont=dict(size=8, color=col, family=FONT_FAMILY),
            name=lbl,
            showlegend=False,
        ))

    style_figure(
        fig,
        "Where Each Source Sits in the Measurement Landscape",
        subtitle=(
            "X axis: measurement approach (usage logs → deployment data → governance readiness → technical ceiling) | "
            "Y axis: headline exposure rate | Bubble size ∝ worker coverage"
        ),
        x_title="Data Source Type",
        y_title="Headline Exposure / Coverage Rate (%)",
        height=560, width=1150,
        show_legend=False,
    )
    fig.update_layout(
        xaxis=dict(
            tickvals=[0, 1, 2, 3],
            ticktext=["Confirmed Usage Logs", "Enterprise Deployment", "Governance-Constrained", "Technical Capability"],
            showgrid=True, gridcolor=COLORS["grid"],
            tickfont=dict(size=10, family=FONT_FAMILY),
        ),
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix="%", range=[0, 65]),
        margin=dict(l=60, r=40, t=80, b=80),
    )
    return fig


def _build_summary_table(our_nums: dict) -> go.Figure:
    """Rendered table with methodology comparison across all sources."""
    rows = [
        {
            "Source": "AEA Dashboard",
            "Pub. Year": "2026",
            "Geography": "National (US)",
            "Method": "Confirmed AI task logs → BLS occupation crosswalk",
            "Unit": "Employment-weighted task exposure %",
            "Headline %": f"{our_nums.get('all_confirmed', {}).get('pct_agg', 40):.1f}% confirmed / "
                          f"{our_nums.get('all_ceiling', {}).get('pct_agg', 50):.1f}% ceiling",
        },
        {
            "Source": "AEI (Humlum & Vestergaard)",
            "Pub. Year": "2024",
            "Geography": "National (US/global)",
            "Method": "Claude API conversation logs → O*NET task matching",
            "Unit": "% of occupations with ≥25% task coverage",
            "Headline %": f"{AEI_HIGH_COVERAGE_PCT:.0f}% of occupations",
        },
        {
            "Source": "ChatGPT (Weidinger et al.)",
            "Pub. Year": "2025",
            "Geography": "Global (ChatGPT users)",
            "Method": "Sampled ChatGPT session logs → use-type classification",
            "Unit": "% of sessions that are work-related",
            "Headline %": f"{CHATGPT_WORK_SHARE:.0f}% work-related sessions",
        },
        {
            "Source": "Microsoft Copilot",
            "Pub. Year": "2025",
            "Geography": "Enterprise (US/global)",
            "Method": "Copilot enterprise deployment logs → task applicability",
            "Unit": "Task applicability rate by sector",
            "Headline %": f"~{COPILOT_TOP_SECTOR_AVG:.0f}% top-sector avg. applicability",
        },
        {
            "Source": "Project Iceberg (MIT/ORNL)",
            "Pub. Year": "2025",
            "Geography": "National (US)",
            "Method": "O*NET skill taxonomy → AI tool capability overlap",
            "Unit": "% of skill wage value AI tools can technically perform",
            "Headline %": f"{ICEBERG_SURFACE:.1f}% (tech) / {ICEBERG_FULL:.1f}% (all sectors)",
        },
        {
            "Source": "Seampoint LLC (Utah)",
            "Pub. Year": "2026 (prelim.)",
            "Geography": "Utah",
            "Method": "Expert governance assessment of deployment readiness",
            "Unit": "% of work hours AI can take over / augment",
            "Headline %": f"{SEAMPOINT_TAKEOVER:.0f}% takeover / {SEAMPOINT_AUGMENT:.0f}% augment",
        },
    ]
    df_table = pd.DataFrame(rows)

    col_widths = [180, 90, 170, 340, 240, 250]
    header_font_size = 11
    cell_font_size = 10

    fig = go.Figure(go.Table(
        columnwidth=col_widths,
        header=dict(
            values=list(df_table.columns),
            fill_color=COLORS["primary"],
            font=dict(color="white", size=header_font_size, family=FONT_FAMILY),
            align="left",
            height=32,
        ),
        cells=dict(
            values=[df_table[c].tolist() for c in df_table.columns],
            fill_color=[[COLORS["bg"] if i % 2 == 0 else "#f5f5f5"
                         for i in range(len(df_table))]
                        for _ in df_table.columns],
            font=dict(color=COLORS["neutral"], size=cell_font_size, family=FONT_FAMILY),
            align="left",
            height=52,
        ),
    ))
    fig.update_layout(
        title=dict(
            text="AI-and-Work Research Source Comparison",
            font=dict(size=16, color=COLORS["neutral"], family=FONT_FAMILY),
            x=0.02,
        ),
        height=420,
        width=1400,
        margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor=COLORS["bg"],
    )
    return fig


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("platform_landscape: loading our headline numbers for all 5 configs...")
    our_nums = _get_our_headline_numbers()

    print("\n-- AEA Dashboard headline numbers --")
    for key, nums in our_nums.items():
        print(f"  {ANALYSIS_CONFIG_LABELS[key]:<30}: "
              f"{nums['workers_affected']/1e6:.1f}M workers, "
              f"${nums['wages_affected']/1e12:.2f}T wages, "
              f"{nums['pct_agg']:.1f}%")

    # Build comparison table CSV
    table_rows = []
    for key, nums in our_nums.items():
        table_rows.append({
            "source": "AEA Dashboard",
            "config": ANALYSIS_CONFIG_LABELS[key],
            "workers_affected_M": round(nums["workers_affected"] / 1e6, 1),
            "wages_affected_T":   round(nums["wages_affected"] / 1e12, 2),
            "pct_agg":            round(nums["pct_agg"], 1),
        })
    external_rows = [
        {"source": "AEI (2024)",         "config": "occupations ≥25% coverage", "workers_affected_M": None, "wages_affected_T": None, "pct_agg": AEI_HIGH_COVERAGE_PCT},
        {"source": "ChatGPT (2025)",     "config": "work-related sessions",      "workers_affected_M": None, "wages_affected_T": None, "pct_agg": CHATGPT_WORK_SHARE},
        {"source": "Copilot (2025)",     "config": "top-sector applicability",   "workers_affected_M": None, "wages_affected_T": None, "pct_agg": COPILOT_TOP_SECTOR_AVG},
        {"source": "Seampoint (2026)",   "config": "takeover (Utah)",            "workers_affected_M": round(SEAMPOINT_UT_WORKERS * SEAMPOINT_TAKEOVER / 100 / 1e6, 2), "wages_affected_T": None, "pct_agg": SEAMPOINT_TAKEOVER},
        {"source": "Seampoint (2026)",   "config": "augment (Utah)",             "workers_affected_M": round(SEAMPOINT_UT_WORKERS * SEAMPOINT_AUGMENT / 100 / 1e6, 2), "wages_affected_T": None, "pct_agg": SEAMPOINT_AUGMENT},
        {"source": "Iceberg (2025)",     "config": "full index",                 "workers_affected_M": None, "wages_affected_T": None, "pct_agg": ICEBERG_FULL},
        {"source": "Iceberg (2025)",     "config": "surface index",              "workers_affected_M": None, "wages_affected_T": None, "pct_agg": ICEBERG_SURFACE},
    ]
    save_csv(pd.DataFrame(table_rows + external_rows), results / "platform_comparison_table.csv")
    print("\n  CSV saved.")

    # Figures
    print("  Building figures...")
    fig = _build_headline_comparison(our_nums)
    save_figure(fig, results / "figures" / "headline_comparison.png")
    shutil.copy(results / "figures" / "headline_comparison.png",
                figs_dir / "headline_comparison.png")
    print("    headline_comparison.png")

    fig = _build_methodology_map(our_nums)
    save_figure(fig, results / "figures" / "methodology_map.png")
    shutil.copy(results / "figures" / "methodology_map.png",
                figs_dir / "methodology_map.png")
    print("    methodology_map.png")

    fig = _build_summary_table(our_nums)
    save_figure(fig, results / "figures" / "source_summary_table.png")
    shutil.copy(results / "figures" / "source_summary_table.png",
                figs_dir / "source_summary_table.png")
    print("    source_summary_table.png")

    # PDF
    md_path = HERE / "platform_landscape_report.md"
    if md_path.exists():
        generate_pdf(md_path, results / "platform_landscape_report.pdf")

    print("\nplatform_landscape: done.")


if __name__ == "__main__":
    main()
