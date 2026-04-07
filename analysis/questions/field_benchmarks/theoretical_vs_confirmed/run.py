"""
run.py — Field Benchmarks: Theoretical vs. Confirmed

Positions the AEA Dashboard's confirmed-usage numbers within the full methodological
spectrum of AI-and-work research: from narrow confirmed real-world usage at the bottom,
up through deployment-constrained estimates, to technical capability ceilings at the top.

Three layers in the measurement hierarchy:
  Layer 1 — Confirmed real-world usage (what AI is actually doing):
    AEA Dashboard all_confirmed:  ~40% emp-weighted task exposure nationally
    AEA Dashboard agentic_confirmed: ~20% (tool-use only)
    ChatGPT usage studies:        ~27% of sessions work-related (Weidinger et al. 2025)
    AEI occupational analysis:    ~36% of occupations have >=25% task coverage confirmed
    Copilot enterprise data:      Sales, Computer/Math, Office/Admin top sectors

  Layer 2 — Deployment-constrained readiness (what orgs could deploy today):
    Seampoint Utah takeover:      20% of work hours (governance-constrained)
    Seampoint Utah augment:       51% of work hours

  Layer 3 — Technical capability ceiling (what AI tools can technically perform):
    Project Iceberg Full Index:   11.7% of skill wage value (all sectors)
    Project Iceberg Surface:      2.2% (tech sector only)
    AEA Dashboard all_ceiling:    ~50% (upper bound including MCP)

Key insight: confirmed usage (our primary config, ~40%) is already higher than
Iceberg's capability estimate (11.7%) — because we measure task-level real usage,
not skill-value substitutability. These frameworks measure different things and
should be read as complementary lenses, not competing claims.

Figures (key ones copied to figures/):
  measurement_spectrum.png — Horizontal dot plot of all sources on one axis
  layer_breakdown.png      — Categorized comparison by measurement type

Run from project root:
    venv/Scripts/python -m analysis.questions.field_benchmarks.theoretical_vs_confirmed.run
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

# ── External benchmark constants ─────────────────────────────────────────────

# Project Iceberg (Chopra et al., 2025)
ICEBERG_SURFACE = 2.2    # % of skill wage value — tech sector
ICEBERG_FULL    = 11.7   # % of skill wage value — full economy

# Seampoint LLC (2026, Utah, preliminary)
SEAMPOINT_TAKEOVER = 20.0   # % of work hours AI can take over
SEAMPOINT_AUGMENT  = 51.0   # % of work hours AI can augment

# ChatGPT usage (Weidinger et al., 2025 — "How People Use ChatGPT")
# ~27% of sessions had at least one work-related message category
CHATGPT_WORK_SHARE = 27.0

# AEI occupational analysis (Humlum & Vestergaard, 2024)
# ~36% of occupations have >=25% confirmed task coverage
AEI_HIGH_COVERAGE_OCCS = 36.0

# Copilot enterprise analysis (Microsoft, 2025)
# Copilot highest-applicability sectors: top 3 cover ~60–65% of high-exposure work
# Using a proxy: Copilot's top-sector task applicability rate ~55% (consistent with
# Sales + Computer/Math + Office/Admin having 50%+ task coverage per their analysis)
COPILOT_TOP_SECTOR_AVG = 55.0


def _get_our_pct(dataset_name: str) -> float:
    """Get national emp-weighted pct_tasks_affected for one dataset."""
    from backend.compute import get_group_data, get_explorer_occupations

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
        return np.nan
    df = data["df"]
    all_occs = get_explorer_occupations()
    total_emp = sum(o.get("emp") or 0 for o in all_occs)
    workers = df["workers_affected"].sum()
    return (workers / total_emp * 100) if total_emp > 0 else np.nan


def _build_measurement_spectrum(our_pcts: dict[str, float]) -> go.Figure:
    """
    Horizontal dot plot showing all sources on one axis,
    color-coded by measurement type.
    """
    # Define all data points
    # (label, value, measurement_type, symbol, color)
    entries = [
        # Real-world confirmed usage
        ("AEA Dashboard: Agentic Confirmed", our_pcts.get("agentic_confirmed", np.nan),
         "Confirmed Usage", "circle", COLORS["muted"]),
        ("ChatGPT: Work-Related Sessions", CHATGPT_WORK_SHARE,
         "Confirmed Usage", "circle", COLORS["muted"]),
        ("AEI: Occupations >=25% Task Coverage", AEI_HIGH_COVERAGE_OCCS,
         "Confirmed Usage", "circle", COLORS["muted"]),
        ("AEA Dashboard: All Confirmed (Primary)", our_pcts.get("all_confirmed", np.nan),
         "Confirmed Usage", "circle", COLORS["primary"]),
        # Deployment-constrained
        ("Seampoint: AI Can Take Over (Utah)", SEAMPOINT_TAKEOVER,
         "Deployment-Constrained", "square", COLORS["accent"]),
        ("Seampoint: AI Can Augment (Utah)", SEAMPOINT_AUGMENT,
         "Deployment-Constrained", "square", COLORS["accent"]),
        # Technical capability
        ("Project Iceberg: Surface Index (Tech)", ICEBERG_SURFACE,
         "Technical Capability", "diamond", "#888"),
        ("Project Iceberg: Full Index (All Sectors)", ICEBERG_FULL,
         "Technical Capability", "diamond", "#888"),
        # Ceiling
        ("AEA Dashboard: Ceiling (incl. MCP)", our_pcts.get("all_ceiling", np.nan),
         "Ceiling Estimate", "circle", COLORS["secondary"]),
    ]

    fig = go.Figure()
    type_colors = {
        "Confirmed Usage":        COLORS["primary"],
        "Deployment-Constrained": COLORS["accent"],
        "Technical Capability":   "#888",
        "Ceiling Estimate":       COLORS["secondary"],
    }

    for i, (lbl, val, mtype, sym, col) in enumerate(entries):
        if np.isnan(val):
            continue
        fig.add_trace(go.Scatter(
            x=[val], y=[i],
            mode="markers+text",
            marker=dict(color=col, size=16, symbol=sym,
                        line=dict(width=1.5, color=COLORS["bg"])),
            text=[f"<b>{val:.1f}%</b>"],
            textposition="top center",
            textfont=dict(size=9, color=col, family=FONT_FAMILY),
            name=mtype,
            showlegend=False,
        ))

    y_labels = [e[0] for e in entries]
    type_labels = [e[2] for e in entries]

    # Shaded bands for each measurement type
    type_y_ranges = {}
    for i, (_, _, mtype, _, _) in enumerate(entries):
        if mtype not in type_y_ranges:
            type_y_ranges[mtype] = [i, i]
        else:
            type_y_ranges[mtype][1] = i

    shading_map = {
        "Confirmed Usage":        "rgba(59,130,246,0.05)",
        "Deployment-Constrained": "rgba(245,158,11,0.05)",
        "Technical Capability":   "rgba(150,150,150,0.05)",
        "Ceiling Estimate":       "rgba(139,92,246,0.05)",
    }
    for mtype, (y0, y1) in type_y_ranges.items():
        fig.add_hrect(
            y0=y0 - 0.4, y1=y1 + 0.4,
            fillcolor=shading_map.get(mtype, "rgba(0,0,0,0.02)"),
            line_width=0,
            annotation_text=mtype,
            annotation_position="right",
            annotation_font=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
        )

    style_figure(
        fig,
        "Measuring AI's Role in Work: A Methodological Spectrum",
        subtitle=(
            "Circles = AEA Dashboard configs | Squares = deployment-constrained estimates | "
            "Diamonds = technical capability assessments | Each source measures something different"
        ),
        x_title="Exposure / Coverage Rate (%)",
        height=560, width=1200,
        show_legend=False,
    )
    fig.update_layout(
        yaxis=dict(
            tickvals=list(range(len(entries))),
            ticktext=y_labels,
            showgrid=False,
            tickfont=dict(size=9, family=FONT_FAMILY),
        ),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix="%", range=[0, 65]),
        margin=dict(l=20, r=220, t=90, b=60),
    )
    return fig


def _build_layer_breakdown(our_pcts: dict[str, float]) -> go.Figure:
    """
    Bar chart grouped by measurement framework / layer.
    Each layer is one group, bars show the range within that layer.
    """
    fig = go.Figure()

    # Layer 1: Confirmed usage
    layer1_labels = ["AEA: Agentic\nConfirmed", "ChatGPT: Work\nSessions", "AEI: Occs >=25%\nCoverage", "AEA: All\nConfirmed"]
    layer1_vals   = [
        our_pcts.get("agentic_confirmed", 0),
        CHATGPT_WORK_SHARE,
        AEI_HIGH_COVERAGE_OCCS,
        our_pcts.get("all_confirmed", 0),
    ]
    layer1_cols   = [COLORS["muted"], COLORS["muted"], COLORS["muted"], COLORS["primary"]]
    fig.add_trace(go.Bar(
        name="Layer 1: Confirmed Real-World Usage",
        x=layer1_labels,
        y=layer1_vals,
        marker=dict(color=layer1_cols, line=dict(width=0)),
        text=[f"{v:.1f}%" for v in layer1_vals],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["neutral"], family=FONT_FAMILY),
    ))

    # Layer 2: Deployment-constrained
    layer2_labels = ["Seampoint:\nTakeover", "Seampoint:\nAugment"]
    layer2_vals   = [SEAMPOINT_TAKEOVER, SEAMPOINT_AUGMENT]
    fig.add_trace(go.Bar(
        name="Layer 2: Deployment-Constrained (Seampoint, Utah)",
        x=layer2_labels,
        y=layer2_vals,
        marker=dict(
            color=COLORS["accent"],
            pattern=dict(shape="/", size=6, fgcolor="white"),
            line=dict(width=0.5, color=COLORS["border"]),
        ),
        text=[f"{v:.1f}%" for v in layer2_vals],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["neutral"], family=FONT_FAMILY),
    ))

    # Layer 3: Technical capability + ceiling
    layer3_labels = ["Iceberg:\nSurface", "Iceberg:\nFull", "AEA:\nCeiling"]
    layer3_vals   = [ICEBERG_SURFACE, ICEBERG_FULL, our_pcts.get("all_ceiling", 0)]
    layer3_cols   = ["#aaa", "#888", COLORS["secondary"]]
    fig.add_trace(go.Bar(
        name="Layer 3: Technical Capability / Ceiling",
        x=layer3_labels,
        y=layer3_vals,
        marker=dict(color=layer3_cols, line=dict(width=0)),
        text=[f"{v:.1f}%" for v in layer3_vals],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["neutral"], family=FONT_FAMILY),
    ))

    all_vals = layer1_vals + layer2_vals + layer3_vals
    style_figure(
        fig,
        "Three Lenses on AI's Role in Work",
        subtitle=(
            "Layer 1: what AI is actually doing | "
            "Layer 2: what orgs could deploy today | "
            "Layer 3: what AI is technically capable of"
        ),
        y_title="Coverage / Exposure Rate (%)",
        height=520, width=1100,
        show_legend=True,
    )
    fig.update_layout(
        barmode="group",
        bargap=0.3,
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix="%", range=[0, max(all_vals) * 1.25]),
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

    print("theoretical_vs_confirmed: loading our pct_agg for all 5 configs...")

    our_pcts: dict[str, float] = {}
    for key, ds_name in ANALYSIS_CONFIGS.items():
        print(f"  {ANALYSIS_CONFIG_LABELS[key]}...")
        pct = _get_our_pct(ds_name)
        our_pcts[key] = round(pct, 2)
        print(f"    pct_agg = {pct:.1f}%")

    # Build summary table
    summary_rows = []
    for key, pct in our_pcts.items():
        summary_rows.append({
            "source": f"AEA Dashboard — {ANALYSIS_CONFIG_LABELS[key]}",
            "measurement_layer": "Confirmed Usage" if "confirmed" in key or "conversation" in key else "Ceiling",
            "metric": "emp-weighted mean pct_tasks_affected",
            "value_pct": pct,
        })
    # External rows
    external_rows = [
        {"source": "ChatGPT: work-related sessions (Weidinger et al. 2025)",
         "measurement_layer": "Confirmed Usage", "metric": "% sessions with work-related use",
         "value_pct": CHATGPT_WORK_SHARE},
        {"source": "AEI: occupations >=25% task coverage (Humlum & Vestergaard 2024)",
         "measurement_layer": "Confirmed Usage", "metric": "% of occupations",
         "value_pct": AEI_HIGH_COVERAGE_OCCS},
        {"source": "Seampoint Utah: AI can take over (2026 prelim.)",
         "measurement_layer": "Deployment-Constrained", "metric": "% of work hours",
         "value_pct": SEAMPOINT_TAKEOVER},
        {"source": "Seampoint Utah: AI can augment (2026 prelim.)",
         "measurement_layer": "Deployment-Constrained", "metric": "% of work hours",
         "value_pct": SEAMPOINT_AUGMENT},
        {"source": "Project Iceberg: Surface Index (Chopra et al. 2025)",
         "measurement_layer": "Technical Capability", "metric": "% of skill wage value",
         "value_pct": ICEBERG_SURFACE},
        {"source": "Project Iceberg: Full Index (Chopra et al. 2025)",
         "measurement_layer": "Technical Capability", "metric": "% of skill wage value",
         "value_pct": ICEBERG_FULL},
    ]
    all_rows = summary_rows + external_rows

    print("\n-- Measurement spectrum summary --")
    for r in all_rows:
        print(f"  [{r['measurement_layer']:<25}] {r['source']:<60}: {r['value_pct']:.1f}%")

    save_csv(pd.DataFrame(all_rows), results / "measurement_spectrum.csv")
    print("\n  CSV saved.")

    # Figures
    print("  Building figures...")
    fig = _build_measurement_spectrum(our_pcts)
    save_figure(fig, results / "figures" / "measurement_spectrum.png")
    shutil.copy(results / "figures" / "measurement_spectrum.png",
                figs_dir / "measurement_spectrum.png")
    print("    measurement_spectrum.png")

    fig = _build_layer_breakdown(our_pcts)
    save_figure(fig, results / "figures" / "layer_breakdown.png")
    shutil.copy(results / "figures" / "layer_breakdown.png",
                figs_dir / "layer_breakdown.png")
    print("    layer_breakdown.png")

    # PDF
    md_path = HERE / "theoretical_vs_confirmed_report.md"
    if md_path.exists():
        generate_pdf(md_path, results / "theoretical_vs_confirmed_report.pdf")

    print("\ntheoretical_vs_confirmed: done.")


if __name__ == "__main__":
    main()
