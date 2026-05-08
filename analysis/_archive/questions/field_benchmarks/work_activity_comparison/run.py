"""
run.py — Field Benchmarks: Work Activity Comparison

Compares our GWA/IWA-level work activity exposure findings against what external
platform-specific studies report about which types of work AI is actually doing.

The external sources don't report GWA exposure rates directly — they report usage
distributions or task categories. This script:
  1. Shows our GWA-level rankings (which work activities AI covers most).
  2. Extracts the dominant GWA-aligned finding from each external source.
  3. Produces a side-by-side showing where the literatures converge.

External GWA-aligned findings:

  AEI (Humlum & Vestergaard 2024), "Which Economic Tasks are Performed with AI":
    - Augmentative use (AI + human) = 57%; Automative = 43%
    - Technical problem-solving ~37% of task-attempts → GWA: "Analyzing Data or Information"
    - Writing tasks ~22% → GWA: "Communicating and Interacting" / "Documenting/Recording"
    - Analysis & synthesis ~18% → GWA: "Making Decisions and Reasoning"
    - AI augments more than it automates — tasks with human judgment still dominate

  Microsoft Copilot (2025), "Working With AI":
    - Getting Information = dominant user goal GWA (~35% of sessions)
    - ~40% of conversations: disjoint user-goal IWA vs. AI-action IWA (AI doing something
      different from what user thinks they're asking about)
    - Copilot activity: Processing Information, Documenting, Communicating

  ChatGPT (Weidinger et al., 2025):
    - Writing = 40% of work sessions → GWA: "Documenting or Recording Information"
    - Practical Guidance = 24% → GWA: "Providing Information, Explanation"
    - Seeking Information = 13.5% → GWA: "Getting Information"

Figures (key ones copied to figures/):
  our_gwa_rankings.png         — Our top 15 GWAs by workers_affected (all_confirmed)
  augment_vs_automate.png      — AEI's 57%/43% split with our confirmed/ceiling GWA context
  platform_gwa_alignment.png   — Which GWAs appear top-ranked across all platforms

Run from project root:
    venv/Scripts/python -m analysis.questions.field_benchmarks.work_activity_comparison.run
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
PRIMARY_KEY = "all_confirmed"

# ── External GWA-level constants ──────────────────────────────────────────────

# AEI (Humlum & Vestergaard, 2024)
AEI_AUGMENT_PCT   = 57.0   # % of AI task-attempts that are augmentative
AEI_AUTOMATE_PCT  = 43.0   # % that are fully automative

# GWA mappings from external sources (% of use / coverage or prominence ranking)
# ChatGPT work-session categories mapped to GWA labels
CHATGPT_GWA_MAP = {
    "Documenting / Recording Information (Writing)":    40.0,
    "Providing Information / Explanation (Guidance)":   24.0,
    "Getting Information (Seeking)":                    13.5,
    "Processing Information (Coding / Technical)":      11.0,
    "Analyzing Data / Reasoning (Analysis)":             8.0,
    "Other work-related GWAs":                           3.5,
}

# Copilot user goal GWA distribution (from Microsoft 2025 analysis)
COPILOT_GWA_MAP = {
    "Getting Information":                              35.0,
    "Processing Information":                           22.0,
    "Documenting / Recording Information":              18.0,
    "Communicating and Interacting":                    14.0,
    "Analyzing Data or Information":                     7.0,
    "Other GWAs":                                        4.0,
}


def _get_gwa_data(dataset_name: str) -> pd.DataFrame:
    """Get GWA-level work activity data for one dataset."""
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
    df = pd.DataFrame(rows)
    return df[["category", "pct_tasks_affected", "workers_affected", "wages_affected"]].copy()


def _build_our_gwa_rankings(gwa_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar: our top 15 GWAs by workers_affected."""
    top = gwa_df.sort_values("workers_affected", ascending=False).head(15)
    labels = top["category"].tolist()[::-1]
    workers_m = (top["workers_affected"] / 1e6).tolist()[::-1]
    pcts = top["pct_tasks_affected"].tolist()[::-1]

    fig = go.Figure(go.Bar(
        y=labels, x=workers_m,
        orientation="h",
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=[f"{w:.1f}M ({p:.0f}%)" for w, p in zip(workers_m, pcts)],
        textposition="outside",
        textfont=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(
        fig,
        "Top 15 Work Activities by Workers Affected — AEA Dashboard (All Confirmed)",
        subtitle="GWA level | All Confirmed config | National | Freq | Auto-aug ON | Numbers: workers (M) + % tasks affected",
        x_title="Workers Affected (millions)",
        height=640, width=1150,
        show_legend=False,
    )
    fig.update_layout(
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix="M", range=[0, max(workers_m) * 1.35]),
        yaxis=dict(showgrid=False, tickfont=dict(size=9, family=FONT_FAMILY)),
        margin=dict(l=20, r=200, t=80, b=60),
    )
    return fig


def _build_augment_vs_automate() -> go.Figure:
    """Donut/bar showing AEI's augment vs. automate split in context of our usage."""
    fig = go.Figure()

    # AEI split
    fig.add_trace(go.Bar(
        name="AEI: Nature of AI Task Use",
        x=["Augmentative\n(AI + Human)", "Automative\n(AI Replaces)"],
        y=[AEI_AUGMENT_PCT, AEI_AUTOMATE_PCT],
        marker=dict(color=[COLORS["primary"], COLORS["secondary"]], line=dict(width=0)),
        text=[f"{AEI_AUGMENT_PCT:.0f}%", f"{AEI_AUTOMATE_PCT:.0f}%"],
        textposition="outside",
        textfont=dict(size=13, color=COLORS["neutral"], family=FONT_FAMILY),
    ))

    style_figure(
        fig,
        "How AI Is Being Used: Augmentative vs. Automative (AEI, 2024)",
        subtitle=(
            "AEI (Humlum & Vestergaard 2024): of confirmed AI task-attempts, "
            "57% involve AI working alongside humans; 43% are fully AI-handled"
        ),
        y_title="% of Confirmed AI Task-Attempts",
        height=400, width=700,
        show_legend=False,
    )
    fig.update_layout(
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix="%", range=[0, 75]),
        xaxis=dict(showgrid=False, tickfont=dict(size=12, family=FONT_FAMILY)),
        margin=dict(l=60, r=40, t=80, b=60),
    )
    return fig


def _build_platform_gwa_alignment() -> go.Figure:
    """
    Grouped bar showing GWA prominence across ChatGPT and Copilot.
    Uses each source's reported % of sessions for that GWA type.
    """
    # Shared GWA categories that appear across both sources
    shared_gwas = [
        "Getting Information",
        "Documenting / Recording Information",
        "Processing Information",
        "Providing Information / Explanation",
        "Analyzing Data / Reasoning",
    ]

    chatgpt_vals = [
        CHATGPT_GWA_MAP.get("Getting Information (Seeking)", 0),
        CHATGPT_GWA_MAP.get("Documenting / Recording Information (Writing)", 0),
        CHATGPT_GWA_MAP.get("Processing Information (Coding / Technical)", 0),
        CHATGPT_GWA_MAP.get("Providing Information / Explanation (Guidance)", 0),
        CHATGPT_GWA_MAP.get("Analyzing Data / Reasoning (Analysis)", 0),
    ]
    copilot_vals = [
        COPILOT_GWA_MAP.get("Getting Information", 0),
        COPILOT_GWA_MAP.get("Documenting / Recording Information", 0),
        COPILOT_GWA_MAP.get("Processing Information", 0),
        0,  # Copilot doesn't break out "Providing Guidance" separately
        COPILOT_GWA_MAP.get("Analyzing Data or Information", 0),
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="ChatGPT (Weidinger et al. 2025)",
        x=shared_gwas, y=chatgpt_vals,
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=[f"{v:.1f}%" if v > 0 else "" for v in chatgpt_vals],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
    ))
    fig.add_trace(go.Bar(
        name="Copilot Enterprise (Microsoft 2025)",
        x=shared_gwas, y=copilot_vals,
        marker=dict(
            color=COLORS["accent"],
            pattern=dict(shape="/", size=6, fgcolor="white"),
            line=dict(width=0.5, color=COLORS["border"]),
        ),
        text=[f"{v:.1f}%" if v > 0 else "" for v in copilot_vals],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
    ))

    all_vals = chatgpt_vals + copilot_vals
    style_figure(
        fig,
        "Most Common Work Activity Types: ChatGPT vs. Copilot",
        subtitle=(
            "ChatGPT: % of work-related sessions by GWA type (Weidinger et al. 2025) | "
            "Copilot: % of enterprise sessions by user goal GWA (Microsoft 2025)"
        ),
        y_title="% of AI Work Sessions",
        height=480, width=1050,
        show_legend=True,
    )
    fig.update_layout(
        barmode="group",
        bargap=0.25,
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix="%", range=[0, max(all_vals) * 1.30]),
        xaxis=dict(showgrid=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        legend=dict(
            orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        ),
        margin=dict(l=60, r=40, t=80, b=120),
    )
    return fig


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("work_activity_comparison: loading GWA data...")

    gwa_df = _get_gwa_data(ANALYSIS_CONFIGS[PRIMARY_KEY])
    if gwa_df.empty:
        print("  WARNING: no GWA data for primary config")
    else:
        print(f"  {len(gwa_df)} GWAs loaded")
        print("\n-- Top 5 GWAs by workers_affected (all_confirmed) --")
        for _, r in gwa_df.sort_values("workers_affected", ascending=False).head(5).iterrows():
            print(f"  {r['category']:<50}: {r['workers_affected']/1e6:.1f}M workers, {r['pct_tasks_affected']:.1f}%")

    # Save CSVs
    if not gwa_df.empty:
        save_csv(gwa_df.sort_values("workers_affected", ascending=False),
                 results / "our_gwa_confirmed.csv")
    save_csv(pd.DataFrame([
        {"source": "ChatGPT (2025)", "gwa_category": k, "pct_of_sessions": v}
        for k, v in CHATGPT_GWA_MAP.items()
    ]), results / "chatgpt_gwa_distribution.csv")
    save_csv(pd.DataFrame([
        {"source": "Copilot (2025)", "gwa_category": k, "pct_of_sessions": v}
        for k, v in COPILOT_GWA_MAP.items()
    ]), results / "copilot_gwa_distribution.csv")
    save_csv(pd.DataFrame([
        {"source": "AEI (2024)", "category": "Augmentative", "pct": AEI_AUGMENT_PCT},
        {"source": "AEI (2024)", "category": "Automative",   "pct": AEI_AUTOMATE_PCT},
    ]), results / "aei_augment_automate.csv")
    print("\n  CSVs saved.")

    # Figures
    print("  Building figures...")
    if not gwa_df.empty:
        fig = _build_our_gwa_rankings(gwa_df)
        save_figure(fig, results / "figures" / "our_gwa_rankings.png")
        shutil.copy(results / "figures" / "our_gwa_rankings.png",
                    figs_dir / "our_gwa_rankings.png")
        print("    our_gwa_rankings.png")

    fig = _build_augment_vs_automate()
    save_figure(fig, results / "figures" / "augment_vs_automate.png")
    shutil.copy(results / "figures" / "augment_vs_automate.png",
                figs_dir / "augment_vs_automate.png")
    print("    augment_vs_automate.png")

    fig = _build_platform_gwa_alignment()
    save_figure(fig, results / "figures" / "platform_gwa_alignment.png")
    shutil.copy(results / "figures" / "platform_gwa_alignment.png",
                figs_dir / "platform_gwa_alignment.png")
    print("    platform_gwa_alignment.png")

    # PDF
    md_path = HERE / "work_activity_comparison_report.md"
    if md_path.exists():
        generate_pdf(md_path, results / "work_activity_comparison_report.pdf")

    print("\nwork_activity_comparison: done.")


if __name__ == "__main__":
    main()
