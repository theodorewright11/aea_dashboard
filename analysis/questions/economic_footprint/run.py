"""
run.py — AI Economic Footprint: Total workforce and wage exposure to AI.

Computes the total share of the US economy affected by AI across multiple
data source perspectives, splits by agentic vs conversational AI mode,
and tests robustness across methodology toggles.

Source groups:
  - Current Usage (AEI Cumul. v4 + Microsoft) — floor / what AI IS doing
  - Capability Ceiling (MCP v4) — ceiling / what AI CAN do
  - Combined (all three averaged) — best overall estimate
  - Agentic (AEI API v3 + v4 + MCP v4) — tool-use / autonomous AI
  - Conversational (AEI Cumul. v4 + Microsoft) — chat / copilot AI

Usage from project root:
    venv/Scripts/python -m analysis.questions.economic_footprint.run
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.config import (
    make_config,
    DEFAULT_OCC_CONFIG,
    ensure_results_dir,
)
from analysis.utils import (
    style_figure,
    save_figure,
    save_csv,
    format_workers,
    format_wages,
    format_pct,
    describe_config,
    generate_pdf,
    _format_bar_label,
    COLORS,
    FONT_FAMILY,
    CATEGORY_PALETTE,
)

HERE = Path(__file__).resolve().parent

# ── Source group definitions ─────────────────────────────────────────────────

SOURCE_GROUPS: dict[str, dict[str, Any]] = {
    "Current Usage": {
        "datasets": ["AEI Cumul. v4", "Microsoft"],
        "combine": "Average",
        "color": COLORS["aei"],
        "desc": "AEI Cumul. v4 + Microsoft",
    },
    "Capability Ceiling": {
        "datasets": ["MCP v4"],
        "combine": "Average",
        "color": COLORS["mcp"],
        "desc": "MCP v4",
    },
    "Combined": {
        "datasets": ["AEI Cumul. v4", "MCP v4", "Microsoft"],
        "combine": "Average",
        "color": COLORS["brand"],
        "desc": "AEI Cumul. v4 + MCP v4 + Microsoft",
    },
}

AGENTIC_DATASETS: list[str] = ["AEI API v3", "AEI API v4", "MCP v4"]
CONVERSATIONAL_DATASETS: list[str] = ["AEI Cumul. v4", "Microsoft"]

TOGGLE_VARIANTS: list[dict[str, Any]] = [
    {"label": "Primary (Time, Aug ON)", "method": "freq", "use_auto_aug": True},
    {"label": "Auto-aug OFF", "method": "freq", "use_auto_aug": False},
    {"label": "Value Method", "method": "imp", "use_auto_aug": True},
    {"label": "Max Exposure (Value, Aug OFF)", "method": "imp", "use_auto_aug": False},
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _economy_baseline(geo: str = "nat") -> dict[str, float]:
    """Total employment and wage bill from eco_2025 (the denominator)."""
    from backend.compute import load_eco_raw

    eco = load_eco_raw()
    emp_col = f"emp_tot_{geo}_2024"
    wage_col = f"a_med_{geo}_2024"
    occ = eco.drop_duplicates(subset=["title_current"])
    total_emp = float(occ[emp_col].fillna(0).sum())
    total_wages = float((occ[emp_col].fillna(0) * occ[wage_col].fillna(0)).sum())
    return {"total_emp": total_emp, "total_wages": total_wages}


def _run_group(
    datasets: list[str],
    combine: str = "Average",
    agg_level: str = "major",
    **overrides: Any,
) -> dict[str, Any] | None:
    """Run the compute pipeline for a dataset group.

    Returns dict with 'df' (category-level DataFrame), 'total_workers',
    'total_wages', or None if no data.
    """
    from backend.compute import get_group_data

    cfg = make_config(
        DEFAULT_OCC_CONFIG,
        selected_datasets=datasets,
        combine_method=combine,
        agg_level=agg_level,
        top_n=1000,
        search_query="",
        **overrides,
    )
    result = get_group_data(cfg)
    if result is None:
        return None
    df = result["df"].rename(columns={result["group_col"]: "category"})
    return {
        "df": df,
        "total_workers": float(result["total_emp"]),
        "total_wages": float(result["total_wages"]),
    }


# ── Chart builders ───────────────────────────────────────────────────────────

def _chart_economy_overview(
    source_totals: dict[str, dict],
    agentic_r: dict,
    conv_r: dict,
    eco_base: dict[str, float],
) -> go.Figure:
    """Horizontal bars showing % of economy exposed per source group."""
    rows = []
    # Source range (top section)
    for name in ["Capability Ceiling", "Combined", "Current Usage"]:
        r = source_totals[name]
        pct_w = r["total_workers"] / eco_base["total_emp"] * 100
        pct_g = r["total_wages"] / eco_base["total_wages"] * 100
        rows.append({
            "name": name, "pct_w": pct_w, "pct_g": pct_g,
            "workers": r["total_workers"], "wages": r["total_wages"],
            "color": SOURCE_GROUPS[name]["color"],
        })
    # AI mode split (bottom section)
    for name, r, color in [
        ("Agentic (API + MCP)", agentic_r, COLORS["mcp"]),
        ("Conversational (AEI + MS)", conv_r, COLORS["aei"]),
    ]:
        pct_w = r["total_workers"] / eco_base["total_emp"] * 100
        pct_g = r["total_wages"] / eco_base["total_wages"] * 100
        rows.append({
            "name": name, "pct_w": pct_w, "pct_g": pct_g,
            "workers": r["total_workers"], "wages": r["total_wages"],
            "color": color,
        })

    names = [r["name"] for r in rows]
    pcts = [r["pct_w"] for r in rows]
    clrs = [r["color"] for r in rows]
    labels = [
        f"  {r['pct_w']:.1f}% workers ({format_workers(r['workers'])})  "
        f"|  {r['pct_g']:.1f}% wages ({format_wages(r['wages'])})"
        for r in rows
    ]

    min_pct = min(r["pct_w"] for r in rows[:3])
    max_pct = max(r["pct_w"] for r in rows[:3])

    fig = go.Figure(go.Bar(
        y=names,
        x=pcts,
        orientation="h",
        marker=dict(color=clrs, line=dict(width=0)),
        text=labels,
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text"], family=FONT_FAMILY),
        cliponaxis=False,
    ))

    fig.update_yaxes(autorange="reversed")

    # Separator line between source range and AI mode sections
    fig.add_shape(
        type="line", x0=0, x1=1, y0=2.5, y1=2.5,
        xref="paper", yref="y",
        line=dict(color=COLORS["grid"], width=1, dash="dot"),
    )
    fig.add_annotation(
        text="AI Mode Split", x=0.01, y=2.5, xref="paper", yref="y",
        showarrow=False, yshift=12,
        font=dict(size=10, color=COLORS["muted"], family=FONT_FAMILY),
    )

    style_figure(
        fig,
        f"Between {min_pct:.0f}% and {max_pct:.0f}% of the US Workforce Is AI-Exposed",
        subtitle="Share of total US employment and wages affected | Time, Auto-aug ON, National",
        width=1200, height=420, show_legend=False,
    )
    fig.update_layout(
        margin=dict(l=20, r=350),
        xaxis=dict(
            showgrid=True, gridcolor=COLORS["grid"],
            range=[0, max(pcts) * 1.8], showticklabels=False,
            showline=False, zeroline=False,
        ),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=12)),
        bargap=0.25,
    )
    return fig


def _chart_dumbbell(
    usage_df: pd.DataFrame,
    cap_df: pd.DataFrame,
    combined_df: pd.DataFrame,
    metric: str = "workers_affected",
) -> go.Figure:
    """Dumbbell chart: floor-to-ceiling range per major category."""
    merged = (
        usage_df[["category", metric]]
        .rename(columns={metric: "usage"})
        .merge(
            cap_df[["category", metric]].rename(columns={metric: "capability"}),
            on="category", how="outer",
        )
        .merge(
            combined_df[["category", metric]].rename(columns={metric: "combined"}),
            on="category", how="outer",
        )
        .fillna(0)
    )
    merged["gap"] = merged["capability"] - merged["usage"]
    merged = merged.sort_values("combined", ascending=True)

    cats = merged["category"].tolist()
    fig = go.Figure()

    # Connecting lines (floor → ceiling)
    for _, row in merged.iterrows():
        fig.add_shape(
            type="line",
            x0=row["usage"], x1=row["capability"],
            y0=row["category"], y1=row["category"],
            line=dict(color=COLORS["grid"], width=2.5),
        )

    # Floor dots
    fig.add_trace(go.Scatter(
        x=merged["usage"], y=cats, mode="markers",
        marker=dict(size=10, color=COLORS["aei"], symbol="circle", line=dict(width=1, color="white")),
        name="Current Usage (Floor)",
    ))
    # Ceiling dots
    fig.add_trace(go.Scatter(
        x=merged["capability"], y=cats, mode="markers",
        marker=dict(size=10, color=COLORS["mcp"], symbol="diamond", line=dict(width=1, color="white")),
        name="Capability Ceiling",
    ))
    # Combined dots
    fig.add_trace(go.Scatter(
        x=merged["combined"], y=cats, mode="markers",
        marker=dict(size=7, color=COLORS["accent"], symbol="square"),
        name="Combined Estimate",
    ))

    metric_label = "Workers Affected" if "workers" in metric else "% Tasks Affected"
    style_figure(
        fig,
        f"The Uncertainty Range: AI Exposure by Sector",
        subtitle=f"{metric_label} — floor (usage) to ceiling (capability) per major category | National",
        x_title=metric_label,
        width=1200, height=max(650, len(cats) * 32 + 150),
    )
    fig.update_layout(
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=11)),
        legend=dict(orientation="h", yanchor="top", y=-0.08, xanchor="center", x=0.5),
    )
    return fig


def _chart_treemap(df: pd.DataFrame) -> go.Figure:
    """Treemap sized by wages_affected, colored by pct_tasks_affected."""
    plot_df = df[df["wages_affected"] > 0].copy()

    fig = go.Figure(go.Treemap(
        labels=plot_df["category"],
        parents=[""] * len(plot_df),
        values=plot_df["wages_affected"],
        marker=dict(
            colors=plot_df["pct_tasks_affected"],
            colorscale=[[0, "#e8f0f8"], [0.35, "#7ba3c4"], [0.7, "#3a5f83"], [1, "#1a3050"]],
            colorbar=dict(
                title=dict(text="% Tasks<br>Affected", font=dict(size=11)),
                ticksuffix="%", len=0.6,
            ),
            line=dict(width=2, color="white"),
        ),
        text=[
            f"{format_wages(w)}<br>{p:.1f}% tasks"
            for w, p in zip(plot_df["wages_affected"], plot_df["pct_tasks_affected"])
        ],
        textinfo="label+text",
        textfont=dict(family=FONT_FAMILY, size=13, color="white"),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Wages Affected: %{value:$,.0f}<br>"
            "% Tasks: %{marker.colors:.1f}%<extra></extra>"
        ),
    ))

    total_w = plot_df["wages_affected"].sum()
    style_figure(
        fig,
        f"Where the Money Is: {format_wages(total_w)} in AI-Exposed Wages",
        subtitle="Combined (All Sources) | Box size = wages affected, color intensity = % tasks affected",
        width=1200, height=700, show_legend=False,
    )
    fig.update_layout(margin=dict(l=10, r=10, t=80, b=60))
    return fig


def _chart_butterfly(
    agentic_df: pd.DataFrame,
    conv_df: pd.DataFrame,
) -> go.Figure:
    """Diverging bar chart: agentic left, conversational right."""
    merged = (
        agentic_df[["category", "workers_affected"]]
        .rename(columns={"workers_affected": "agentic"})
        .merge(
            conv_df[["category", "workers_affected"]]
            .rename(columns={"workers_affected": "conversational"}),
            on="category", how="outer",
        )
        .fillna(0)
    )
    merged["total"] = merged["agentic"] + merged["conversational"]
    merged = merged.sort_values("total", ascending=True)

    cats = merged["category"].tolist()
    fig = go.Figure()

    # Agentic (left — negative x)
    fig.add_trace(go.Bar(
        y=cats, x=-merged["agentic"], orientation="h",
        name="Agentic / Tool-use AI",
        marker=dict(color=COLORS["mcp"], line=dict(width=0)),
        text=[format_workers(v) for v in merged["agentic"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["mcp"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    # Conversational (right — positive x)
    fig.add_trace(go.Bar(
        y=cats, x=merged["conversational"], orientation="h",
        name="Conversational / Copilot AI",
        marker=dict(color=COLORS["aei"], line=dict(width=0)),
        text=[format_workers(v) for v in merged["conversational"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["aei"], family=FONT_FAMILY),
        cliponaxis=False,
    ))

    # Find which side dominates more categories
    n_agentic_leads = int((merged["agentic"] > merged["conversational"]).sum())
    n_conv_leads = int((merged["conversational"] > merged["agentic"]).sum())

    max_val = max(merged["agentic"].max(), merged["conversational"].max()) * 1.35
    style_figure(
        fig,
        "Two Modes of AI: Agentic vs Conversational Impact",
        subtitle=(
            f"← Agentic (AEI API v3+v4 + MCP v4)  |  "
            f"Conversational (AEI Cumul. v4 + Microsoft) →  |  Workers Affected"
        ),
        width=1400, height=max(650, len(cats) * 32 + 150),
    )
    fig.update_layout(
        xaxis=dict(
            range=[-max_val, max_val], showgrid=False,
            zeroline=True, zerolinecolor=COLORS["text"], zerolinewidth=1.5,
            showticklabels=False, showline=False,
        ),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=11)),
        bargap=0.2,
        legend=dict(orientation="h", yanchor="top", y=-0.06, xanchor="center", x=0.5),
    )
    return fig


def _chart_heatmap(
    source_dfs: dict[str, pd.DataFrame],
    agentic_df: pd.DataFrame,
    conv_df: pd.DataFrame,
) -> go.Figure:
    """Heatmap: major categories × data sources by % tasks affected."""
    sources = {
        "Current<br>Usage": source_dfs["Current Usage"],
        "Capability<br>Ceiling": source_dfs["Capability Ceiling"],
        "Combined": source_dfs["Combined"],
        "Agentic": agentic_df,
        "Conversa-<br>tional": conv_df,
    }

    # Order categories by combined workers_affected descending
    cats = (
        source_dfs["Combined"]
        .sort_values("workers_affected", ascending=False)["category"]
        .tolist()
    )

    z: list[list[float]] = []
    text: list[list[str]] = []
    for cat in cats:
        row_z: list[float] = []
        row_t: list[str] = []
        for src_df in sources.values():
            match = src_df[src_df["category"] == cat]
            pct = float(match["pct_tasks_affected"].iloc[0]) if not match.empty else 0.0
            row_z.append(pct)
            row_t.append(f"{pct:.1f}%")
        z.append(row_z)
        text.append(row_t)

    fig = go.Figure(go.Heatmap(
        z=z, x=list(sources.keys()), y=cats,
        text=text, texttemplate="%{text}",
        textfont=dict(size=10, family=FONT_FAMILY),
        colorscale=[[0, "#f7f7f4"], [0.3, "#b8cee0"], [0.6, "#5a8fbc"], [1, "#1a3a54"]],
        colorbar=dict(title=dict(text="% Tasks", font=dict(size=11)), ticksuffix="%", len=0.5),
        hovertemplate="<b>%{y}</b><br>%{x}: %{text}<extra></extra>",
    ))

    style_figure(
        fig,
        "Source Agreement: Where Do Data Sources Agree on AI Exposure?",
        subtitle="% Tasks Affected by major category and data source | Darker = higher exposure",
        width=1000, height=max(650, len(cats) * 30 + 120),
        show_legend=False,
    )
    fig.update_layout(
        xaxis=dict(side="top", showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(showgrid=False, autorange="reversed", tickfont=dict(size=11)),
        margin=dict(l=20, r=20, t=100, b=60),
    )
    return fig


def _chart_physical(
    results: dict[str, dict],
    eco_base: dict[str, float],
) -> go.Figure:
    """Side-by-side bars: all vs non-physical vs physical-only."""
    modes = ["All Tasks", "Non-Physical Only", "Physical Only"]
    clrs = [COLORS["primary"], COLORS["secondary"], COLORS["accent"]]
    pcts = [results[m]["total_workers"] / eco_base["total_emp"] * 100 for m in modes]
    workers = [results[m]["total_workers"] for m in modes]

    fig = go.Figure()
    for mode, pct, w, c in zip(modes, pcts, workers, clrs):
        fig.add_trace(go.Bar(
            x=[mode], y=[pct], name=mode,
            marker=dict(color=c, line=dict(width=0)),
            text=[f"{pct:.1f}%\n{format_workers(w)}"],
            textposition="outside",
            textfont=dict(size=13, color=COLORS["text"], family=FONT_FAMILY),
            showlegend=False,
        ))

    style_figure(
        fig,
        f"Non-Physical Work Is {pcts[1] / max(pcts[2], 0.01):.1f}× More AI-Exposed Than Physical",
        subtitle="Combined (All Sources) | % of total employment affected | National",
        y_title="% of Economy Affected",
        width=750, height=500, show_legend=False,
    )
    fig.update_layout(
        xaxis=dict(showgrid=False, tickfont=dict(size=12)),
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"], range=[0, max(pcts) * 1.25]),
        bargap=0.4,
    )
    return fig


def _chart_toggle_sensitivity(
    toggle_results: list[dict],
    eco_base: dict[str, float],
) -> go.Figure:
    """Dot/lollipop plot: how total footprint changes across config toggles."""
    labels = [r["label"] for r in toggle_results]
    pcts = [r["total_workers"] / eco_base["total_emp"] * 100 for r in toggle_results]

    fig = go.Figure()

    # Horizontal reference lines
    for label, pct in zip(labels, pcts):
        fig.add_shape(
            type="line", x0=0, x1=pct, y0=label, y1=label,
            line=dict(color=COLORS["grid"], width=1.5, dash="dot"),
        )

    fig.add_trace(go.Scatter(
        x=pcts, y=labels, mode="markers+text",
        marker=dict(size=16, color=COLORS["primary"], symbol="circle",
                    line=dict(width=2, color="white")),
        text=[f"  {p:.1f}% ({format_workers(r['total_workers'])})" for p, r in zip(pcts, toggle_results)],
        textposition="middle right",
        textfont=dict(size=12, color=COLORS["text"], family=FONT_FAMILY),
        showlegend=False,
    ))

    spread = max(pcts) - min(pcts)
    style_figure(
        fig,
        f"Methodology Sensitivity: {spread:.1f} Percentage Points of Variation",
        subtitle="Combined (All Sources) | % of US employment affected under different settings",
        x_title="% of Economy Affected",
        width=1050, height=380, show_legend=False,
    )
    fig.update_layout(
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   range=[0, max(pcts) * 1.4], showline=False),
        yaxis=dict(showgrid=False, showline=False, autorange="reversed",
                   tickfont=dict(size=12)),
        margin=dict(l=20, r=200),
    )
    return fig


def _chart_autoaug_distribution(occs_df: pd.DataFrame) -> go.Figure:
    """Employment distribution across auto-aug score tiers."""
    bins = [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 5.01]
    labels = ["0–0.5", "0.5–1.0", "1.0–1.5", "1.5–2.0",
              "2.0–2.5", "2.5–3.0", "3.0–3.5", "3.5–5.0"]

    occs_df = occs_df.copy()
    occs_df["auto_tier"] = pd.cut(
        occs_df["auto_avg_all"].fillna(0),
        bins=bins, labels=labels, include_lowest=True,
    )
    tier_emp = occs_df.groupby("auto_tier", observed=False)["emp_nat"].sum().reindex(labels, fill_value=0)

    n = len(labels)
    tier_colors = [f"rgba(58, 95, 131, {0.15 + 0.85 * i / (n - 1):.2f})" for i in range(n)]

    # Compute headline stat
    weighted_avg = float(
        (occs_df["auto_avg_all"].fillna(0) * occs_df["emp_nat"].fillna(0)).sum()
        / occs_df["emp_nat"].fillna(0).sum()
    )

    fig = go.Figure(go.Bar(
        x=labels, y=tier_emp.values,
        marker=dict(color=tier_colors, line=dict(width=0)),
        text=[format_workers(v) for v in tier_emp.values],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["neutral"], family=FONT_FAMILY),
    ))

    style_figure(
        fig,
        f"How Automatable Is American Work? (Avg Score: {weighted_avg:.2f} / 5)",
        subtitle="US employment by average auto-aug score across all AI sources | Higher = more automatable",
        x_title="Average Auto-Aug Score (0–5 scale)",
        y_title="Total Employment",
        width=1100, height=550, show_legend=False,
    )
    fig.update_layout(
        xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        bargap=0.12,
    )
    return fig


def _chart_impact_scatter(df: pd.DataFrame, eco_base: dict[str, float]) -> go.Figure:
    """Scatter: employment vs % tasks affected, bubble = wages affected."""
    plot_df = df.copy()
    # Scale bubble sizes
    max_wages = plot_df["wages_affected"].max()
    plot_df["bubble_size"] = (plot_df["wages_affected"] / max_wages * 50).clip(lower=8)

    fig = go.Figure(go.Scatter(
        x=plot_df["pct_tasks_affected"],
        y=plot_df["workers_affected"],
        mode="markers+text",
        marker=dict(
            size=plot_df["bubble_size"],
            color=plot_df["pct_tasks_affected"],
            colorscale=[[0, "#b8cee0"], [0.5, "#5a8fbc"], [1, "#1a3a54"]],
            line=dict(width=1, color="white"),
            opacity=0.85,
        ),
        text=plot_df["category"],
        textposition="top center",
        textfont=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "% Tasks: %{x:.1f}%<br>"
            "Workers: %{y:,.0f}<br>"
            "<extra></extra>"
        ),
    ))

    style_figure(
        fig,
        "Impact Map: Where AI Exposure Meets Workforce Size",
        subtitle="Combined (All Sources) | Bubble size = wages affected | National",
        x_title="% Tasks Affected",
        y_title="Workers Affected",
        width=1100, height=700,
        show_legend=False,
    )
    fig.update_layout(
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
    )
    return fig


# ── Main pipeline ────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    fig_dir = results / "figures"
    print("AI Economic Footprint — generating outputs...\n")

    # ── 1. Economy baseline ──────────────────────────────────────────────
    print("== Economy baseline ==")
    eco_nat = _economy_baseline("nat")
    eco_ut = _economy_baseline("ut")
    print(f"  National: {format_workers(eco_nat['total_emp'])} workers, "
          f"{format_wages(eco_nat['total_wages'])} wages")
    print(f"  Utah:     {format_workers(eco_ut['total_emp'])} workers, "
          f"{format_wages(eco_ut['total_wages'])} wages")

    # ── 2. Source group results (major level) ────────────────────────────
    print("\n== Source group computations (major level) ==")
    source_results: dict[str, dict] = {}
    source_major_dfs: dict[str, pd.DataFrame] = {}
    for name, cfg in SOURCE_GROUPS.items():
        print(f"  {name}...")
        r = _run_group(cfg["datasets"], cfg["combine"])
        if r is None:
            print(f"    SKIP — no data")
            continue
        source_results[name] = r
        source_major_dfs[name] = r["df"]
        pct = r["total_workers"] / eco_nat["total_emp"] * 100
        print(f"    {format_workers(r['total_workers'])} workers ({pct:.1f}%), "
              f"{format_wages(r['total_wages'])} wages")

    if len(source_results) < 3:
        print("ERROR: Not all source groups produced data. Aborting.")
        return

    # ── 3. Agentic + Conversational (major level) ───────────────────────
    print("\n== Agentic vs Conversational ==")
    agentic_r = _run_group(AGENTIC_DATASETS)
    conv_r = _run_group(CONVERSATIONAL_DATASETS)
    if agentic_r:
        pct = agentic_r["total_workers"] / eco_nat["total_emp"] * 100
        print(f"  Agentic:        {format_workers(agentic_r['total_workers'])} ({pct:.1f}%)")
    if conv_r:
        pct = conv_r["total_workers"] / eco_nat["total_emp"] * 100
        print(f"  Conversational: {format_workers(conv_r['total_workers'])} ({pct:.1f}%)")

    if not agentic_r or not conv_r:
        print("ERROR: Agentic/Conversational groups failed. Aborting.")
        return

    # ── 4. Economy summary CSV ───────────────────────────────────────────
    print("\n== Saving economy summary ==")
    summary_rows: list[dict[str, Any]] = []
    for name, r in source_results.items():
        summary_rows.append({
            "Source": name,
            "Datasets": SOURCE_GROUPS[name]["desc"],
            "Workers Affected": r["total_workers"],
            "% of Employment": r["total_workers"] / eco_nat["total_emp"] * 100,
            "Wages Affected ($)": r["total_wages"],
            "% of Wage Bill": r["total_wages"] / eco_nat["total_wages"] * 100,
        })
    for label, r, desc in [
        ("Agentic", agentic_r, "AEI API v3 + v4 + MCP v4"),
        ("Conversational", conv_r, "AEI Cumul. v4 + Microsoft"),
    ]:
        summary_rows.append({
            "Source": label,
            "Datasets": desc,
            "Workers Affected": r["total_workers"],
            "% of Employment": r["total_workers"] / eco_nat["total_emp"] * 100,
            "Wages Affected ($)": r["total_wages"],
            "% of Wage Bill": r["total_wages"] / eco_nat["total_wages"] * 100,
        })
    summary_df = pd.DataFrame(summary_rows)
    save_csv(summary_df, results / "economy_totals.csv")

    # Major-level CSVs per source
    for name, df in source_major_dfs.items():
        slug = name.lower().replace(" ", "_")
        save_csv(
            df.sort_values("workers_affected", ascending=False),
            results / f"major_{slug}.csv",
        )
    save_csv(
        agentic_r["df"].sort_values("workers_affected", ascending=False),
        results / "major_agentic.csv",
    )
    save_csv(
        conv_r["df"].sort_values("workers_affected", ascending=False),
        results / "major_conversational.csv",
    )

    # ── 5. Charts: Economy overview + dumbbell + treemap + scatter ───────
    print("\n== Generating charts ==")

    print("  Economy overview...")
    fig = _chart_economy_overview(source_results, agentic_r, conv_r, eco_nat)
    save_figure(fig, fig_dir / "economy_overview.png")

    print("  Dumbbell range (workers)...")
    fig = _chart_dumbbell(
        source_major_dfs["Current Usage"],
        source_major_dfs["Capability Ceiling"],
        source_major_dfs["Combined"],
        metric="workers_affected",
    )
    save_figure(fig, fig_dir / "range_workers_major.png")

    print("  Dumbbell range (% tasks)...")
    fig = _chart_dumbbell(
        source_major_dfs["Current Usage"],
        source_major_dfs["Capability Ceiling"],
        source_major_dfs["Combined"],
        metric="pct_tasks_affected",
    )
    save_figure(fig, fig_dir / "range_pct_major.png")

    print("  Treemap (wages)...")
    fig = _chart_treemap(source_major_dfs["Combined"])
    save_figure(fig, fig_dir / "treemap_wages.png")

    print("  Impact scatter...")
    fig = _chart_impact_scatter(source_major_dfs["Combined"], eco_nat)
    save_figure(fig, fig_dir / "impact_scatter.png")

    # ── 6. Chart: Butterfly (agentic vs conversational) ──────────────────
    print("  Butterfly (agentic vs conversational)...")
    fig = _chart_butterfly(agentic_r["df"], conv_r["df"])
    save_figure(fig, fig_dir / "agentic_vs_conversational.png")

    # ── 7. Chart: Heatmap ────────────────────────────────────────────────
    print("  Heatmap (sources × categories)...")
    fig = _chart_heatmap(source_major_dfs, agentic_r["df"], conv_r["df"])
    save_figure(fig, fig_dir / "heatmap_sources.png")

    # ── 8. Physical split ────────────────────────────────────────────────
    print("\n== Physical split ==")
    phys_results: dict[str, dict] = {}
    combined_ds = SOURCE_GROUPS["Combined"]["datasets"]
    for mode_label, phys_mode in [
        ("All Tasks", "all"),
        ("Non-Physical Only", "exclude"),
        ("Physical Only", "only"),
    ]:
        r = _run_group(combined_ds, physical_mode=phys_mode)
        if r:
            phys_results[mode_label] = r
            pct = r["total_workers"] / eco_nat["total_emp"] * 100
            print(f"  {mode_label}: {format_workers(r['total_workers'])} ({pct:.1f}%)")

    if len(phys_results) == 3:
        print("  Chart: physical comparison...")
        fig = _chart_physical(phys_results, eco_nat)
        save_figure(fig, fig_dir / "physical_comparison.png")

        phys_rows = []
        for mode_label, r in phys_results.items():
            phys_rows.append({
                "Physical Mode": mode_label,
                "Workers Affected": r["total_workers"],
                "% of Employment": r["total_workers"] / eco_nat["total_emp"] * 100,
                "Wages Affected ($)": r["total_wages"],
                "% of Wage Bill": r["total_wages"] / eco_nat["total_wages"] * 100,
            })
        save_csv(pd.DataFrame(phys_rows), results / "physical_comparison.csv")

    # ── 9. Toggle sensitivity ────────────────────────────────────────────
    print("\n== Toggle sensitivity ==")
    toggle_results: list[dict[str, Any]] = []
    combined_ds = SOURCE_GROUPS["Combined"]["datasets"]
    for variant in TOGGLE_VARIANTS:
        r = _run_group(
            combined_ds,
            method=variant["method"],
            use_auto_aug=variant["use_auto_aug"],
        )
        if r:
            entry = {
                "label": variant["label"],
                "total_workers": r["total_workers"],
                "total_wages": r["total_wages"],
            }
            toggle_results.append(entry)
            pct = r["total_workers"] / eco_nat["total_emp"] * 100
            print(f"  {variant['label']}: {format_workers(r['total_workers'])} ({pct:.1f}%)")

    if toggle_results:
        print("  Chart: toggle sensitivity...")
        fig = _chart_toggle_sensitivity(toggle_results, eco_nat)
        save_figure(fig, fig_dir / "toggle_sensitivity.png")

        toggle_rows = []
        for t in toggle_results:
            toggle_rows.append({
                "Config": t["label"],
                "Workers Affected": t["total_workers"],
                "% of Employment": t["total_workers"] / eco_nat["total_emp"] * 100,
                "Wages Affected ($)": t["total_wages"],
                "% of Wage Bill": t["total_wages"] / eco_nat["total_wages"] * 100,
            })
        save_csv(pd.DataFrame(toggle_rows), results / "toggle_sensitivity.csv")

    # ── 10. Robustness: stable categories across toggles ─────────────────
    print("\n== Robustness check ==")
    toggle_top10_sets: list[set[str]] = []
    for variant in TOGGLE_VARIANTS:
        r = _run_group(
            combined_ds,
            method=variant["method"],
            use_auto_aug=variant["use_auto_aug"],
        )
        if r:
            top10 = set(
                r["df"]
                .sort_values("workers_affected", ascending=False)
                .head(10)["category"]
                .tolist()
            )
            toggle_top10_sets.append(top10)
    if toggle_top10_sets:
        stable = set.intersection(*toggle_top10_sets)
        print(f"  {len(stable)} of 10 major categories stable across all 4 toggle combos")
        print(f"  Stable: {', '.join(sorted(stable))}")

    # ── 11. National vs Utah ─────────────────────────────────────────────
    print("\n== National vs Utah ==")
    utah_r = _run_group(combined_ds, geo="ut")
    if utah_r:
        pct_nat = source_results["Combined"]["total_workers"] / eco_nat["total_emp"] * 100
        pct_ut = utah_r["total_workers"] / eco_ut["total_emp"] * 100
        print(f"  National: {pct_nat:.1f}% of workers")
        print(f"  Utah:     {pct_ut:.1f}% of workers")

        geo_rows = [
            {
                "Geography": "National",
                "Workers Affected": source_results["Combined"]["total_workers"],
                "% of Employment": pct_nat,
                "Wages Affected ($)": source_results["Combined"]["total_wages"],
                "% of Wage Bill": source_results["Combined"]["total_wages"] / eco_nat["total_wages"] * 100,
            },
            {
                "Geography": "Utah",
                "Workers Affected": utah_r["total_workers"],
                "% of Employment": pct_ut,
                "Wages Affected ($)": utah_r["total_wages"],
                "% of Wage Bill": utah_r["total_wages"] / eco_ut["total_wages"] * 100,
            },
        ]
        save_csv(pd.DataFrame(geo_rows), results / "nat_vs_utah.csv")

    # ── 12. Auto-aug economy-wide distribution ───────────────────────────
    print("\n== Auto-aug economy metrics ==")
    from backend.compute import get_explorer_occupations

    occs_raw = get_explorer_occupations()
    occs_df = pd.DataFrame(occs_raw)

    if not occs_df.empty and "auto_avg_all" in occs_df.columns:
        emp_total = occs_df["emp_nat"].fillna(0).sum()
        weighted_avg = float(
            (occs_df["auto_avg_all"].fillna(0) * occs_df["emp_nat"].fillna(0)).sum()
            / max(emp_total, 1)
        )
        high_auto = occs_df[occs_df["auto_avg_all"].fillna(0) >= 2.0]
        pct_high = float(high_auto["emp_nat"].fillna(0).sum() / max(emp_total, 1) * 100)
        print(f"  Employment-weighted avg auto-aug: {weighted_avg:.2f} / 5")
        print(f"  Workers in occupations with auto-aug >= 2.0: {pct_high:.1f}%")

        print("  Chart: auto-aug distribution...")
        fig = _chart_autoaug_distribution(occs_df)
        save_figure(fig, fig_dir / "autoaug_distribution.png")

        # Pct concentration stats
        if "sum_pct_avg" in occs_df.columns:
            pct_df = occs_df[["title_current", "emp_nat", "sum_pct_avg"]].copy()
            pct_df["sum_pct_avg"] = pct_df["sum_pct_avg"].fillna(0)
            pct_df = pct_df.sort_values("sum_pct_avg", ascending=False)
            top50_emp = float(pct_df.head(50)["emp_nat"].fillna(0).sum())
            top50_pct = top50_emp / max(emp_total, 1) * 100
            print(f"  Top 50 occs by AI conversation share represent {top50_pct:.1f}% of employment")

        # Save auto-aug summary
        auto_rows = [
            {"Metric": "Employment-weighted avg auto-aug (0-5)", "Value": f"{weighted_avg:.2f}"},
            {"Metric": "Workers in occs with auto-aug >= 2.0", "Value": f"{pct_high:.1f}%"},
            {"Metric": "Total occupations", "Value": str(len(occs_df))},
        ]
        if "sum_pct_avg" in occs_df.columns:
            auto_rows.append({
                "Metric": "Top 50 occs by AI conversation share (% of employment)",
                "Value": f"{top50_pct:.1f}%",
            })
        save_csv(pd.DataFrame(auto_rows), results / "autoaug_summary.csv")

    # ── 13. Tasks coverage ───────────────────────────────────────────────
    print("\n== Task coverage ==")
    from backend.compute import get_all_tasks

    all_tasks = get_all_tasks()
    if all_tasks:
        tasks_df = pd.DataFrame(all_tasks)
        total_tasks = len(tasks_df)
        ai_touched = int(
            (tasks_df["avg_auto_aug"].fillna(0) > 0).sum()
            if "avg_auto_aug" in tasks_df.columns
            else 0
        )
        pct_touched = ai_touched / max(total_tasks, 1) * 100
        print(f"  {ai_touched} of {total_tasks} unique tasks rated by AI ({pct_touched:.1f}%)")
        save_csv(
            pd.DataFrame([{
                "Total unique tasks": total_tasks,
                "Tasks with AI rating": ai_touched,
                "% rated": pct_touched,
            }]),
            results / "task_coverage.csv",
        )

    # ── 14. Copy key figures ─────────────────────────────────────────────
    print("\n== Copying key figures ==")
    committed_figs = HERE / "figures"
    committed_figs.mkdir(exist_ok=True)

    key_figures = [
        "economy_overview.png",
        "range_workers_major.png",
        "treemap_wages.png",
        "agentic_vs_conversational.png",
        "heatmap_sources.png",
        "physical_comparison.png",
        "toggle_sensitivity.png",
        "autoaug_distribution.png",
        "impact_scatter.png",
    ]
    for fname in key_figures:
        src = fig_dir / fname
        if src.exists():
            shutil.copy2(src, committed_figs / fname)
            print(f"  Copied {fname}")
        else:
            print(f"  SKIP (not found): {fname}")

    # ── 15. Generate PDF ─────────────────────────────────────────────────
    print("\n== Generating PDF ==")
    md_path = HERE / "economic_footprint.md"
    pdf_path = results / "economic_footprint.pdf"
    if md_path.exists():
        generate_pdf(md_path, pdf_path)
        print(f"  Saved {pdf_path.name}")
    else:
        print(f"  SKIP — {md_path.name} not yet written")

    print("\nDone.")


if __name__ == "__main__":
    main()
