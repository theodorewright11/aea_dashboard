"""
run.py — Potential Growth: Audience Framing

How do the potential growth findings land for different audiences?

Loads key result CSVs from the three other sub-questions and produces
audience-specific charts and narratives for:
  - Policy (investment priorities, GDP-scale framing)
  - Workforce / educators (tool-literacy training targets — directional, not prescriptive)
  - Researchers (config sensitivity / robustness)
  - Laypeople (plain-language sector overview)

Must run AFTER adoption_gap, wage_potential, and automation_opportunity.

Figures (key ones copied to figures/):
  policy_investment_priorities.png   — Sectors: combined wage gap + workers gap
  workforce_training_targets.png     — Q1 + Q3 occupations by emp × median wage
  researcher_config_sensitivity.png  — Gap magnitude across all 5 configs (major level)
  layperson_opportunity.png          — Plain sector overview: confirmed vs ceiling

Run from project root:
    venv/Scripts/python -m analysis.questions.potential_growth.audience_framing.run
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
    format_wages,
    format_workers,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
QUESTIONS = HERE.parent  # potential_growth/

# Result CSV paths from sibling sub-questions
ADOPTION_GAP_DIR = QUESTIONS / "adoption_gap" / "results"
WAGE_POTENTIAL_DIR = QUESTIONS / "wage_potential" / "results"
AUTO_OPP_DIR = QUESTIONS / "automation_opportunity" / "results"


# ── Data loading ──────────────────────────────────────────────────────────────

def _load_csv(path: Path, required_cols: list[str] | None = None) -> pd.DataFrame:
    """Load a CSV; return empty DataFrame with a warning if missing."""
    if not path.exists():
        print(f"  WARNING: {path.name} not found — run sibling sub-questions first")
        return pd.DataFrame()
    df = pd.read_csv(path)
    if required_cols:
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            print(f"  WARNING: {path.name} missing columns: {missing}")
    return df


def _get_occ_data(dataset_name: str, agg_level: str = "major") -> pd.DataFrame:
    """Lightweight occ data fetch for audience-framing charts."""
    from backend.compute import get_group_data

    agg_col_map = {
        "major": "major_occ_category",
        "occupation": "title_current",
    }
    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": "nat",
        "agg_level": agg_level,
        "sort_by": "Workers Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    if data is None:
        return pd.DataFrame()
    df = data["df"]
    raw_col = agg_col_map.get(agg_level, "title_current")
    gc = data.get("group_col", raw_col)
    rename_col = gc if gc in df.columns else raw_col
    if rename_col not in df.columns:
        return pd.DataFrame()
    df = df.rename(columns={rename_col: "category"})
    return df[["category", "pct_tasks_affected", "workers_affected", "wages_affected"]].copy()


# ── Figure builders ────────────────────────────────────────────────────────────

def _policy_priorities(wage_gap_major: pd.DataFrame, adoption_gap_major: pd.DataFrame
                       ) -> go.Figure:
    """Horizontal grouped bar: wage gap and workers gap per major sector."""
    if wage_gap_major.empty or adoption_gap_major.empty:
        return go.Figure()

    needed_w = ["category", "wages_affected_gap"]
    needed_a = ["category", "workers_affected_gap"]
    if not all(c in wage_gap_major.columns for c in needed_w):
        return go.Figure()
    if not all(c in adoption_gap_major.columns for c in needed_a):
        return go.Figure()

    # Merge on category
    df = wage_gap_major[["category", "wages_affected_gap"]].merge(
        adoption_gap_major[["category", "workers_affected_gap"]],
        on="category", how="inner",
    )

    # Normalize both metrics to 0-1 for combined ranking
    df["wages_norm"] = df["wages_affected_gap"] / df["wages_affected_gap"].max()
    df["workers_norm"] = df["workers_affected_gap"] / df["workers_affected_gap"].max()
    df["combined_score"] = (df["wages_norm"] + df["workers_norm"]) / 2
    df = df.sort_values("combined_score", ascending=True)

    save_csv(df.sort_values("combined_score", ascending=False),
             HERE / "results" / "policy_priorities.csv")

    def _fmt_wages(v: float) -> str:
        if v >= 1e12:
            return f"${v / 1e12:.2f}T"
        if v >= 1e9:
            return f"${v / 1e9:.1f}B"
        return f"${v / 1e6:.0f}M"

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["category"],
        x=df["wages_norm"],
        orientation="h",
        name="Wage Gap (normalized)",
        marker=dict(color=COLORS["accent"], line=dict(width=0), opacity=0.85),
        text=[_fmt_wages(v) for v in df["wages_affected_gap"]],
        textposition="outside",
        textfont=dict(size=9, color=COLORS["accent"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    fig.add_trace(go.Bar(
        y=df["category"],
        x=df["workers_norm"],
        orientation="h",
        name="Workers Gap (normalized)",
        marker=dict(color=COLORS["primary"], line=dict(width=0), opacity=0.7),
        text=[format_workers(v) for v in df["workers_affected_gap"]],
        textposition="inside",
        textfont=dict(size=9, color=COLORS["bg"], family=FONT_FAMILY),
    ))

    chart_h = max(550, len(df) * 30 + 200)
    style_figure(
        fig,
        "Policy Investment Priorities — Where the Economic Gap Lives",
        subtitle=(
            "Normalized wage gap + workers gap | "
            "Sectors ranked by combined opportunity score | "
            "Labels show raw values"
        ),
        x_title=None,
        height=chart_h,
        show_legend=True,
    )
    fig.update_layout(
        barmode="group",
        margin=dict(l=20, r=120, t=80, b=120),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False, zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        bargap=0.15, bargroupgap=0.05,
        legend=dict(
            orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        ),
    )
    return fig


def _workforce_targets(opp_scores: pd.DataFrame) -> go.Figure:
    """
    Top Q1 + Q3 occupations for workforce framing: where training matters.
    Q1 = AI already leads AND gap is large → AI tool adoption leverage.
    Q3 = humans still lead but gap exists → tool familiarity is most valuable.
    Sorted by emp × median_wage as a proxy for aggregate economic relevance.
    """
    if opp_scores.empty:
        return go.Figure()
    needed = ["title_current", "quadrant", "emp_nat", "median_wage", "adoption_gap", "ska_overall_pct"]
    if not all(c in opp_scores.columns for c in needed):
        return go.Figure()

    targets = opp_scores[opp_scores["quadrant"].isin([
        "Q1: Automation opportunity", "Q3: Tool gap"
    ])].copy()
    if targets.empty:
        return go.Figure()

    targets["relevance_score"] = targets["emp_nat"] * targets["median_wage"]
    targets = targets.sort_values("relevance_score", ascending=False).head(30)

    save_csv(targets, HERE / "results" / "workforce_targets.csv")

    targets = targets.sort_values("relevance_score", ascending=True)

    colors = [
        COLORS["accent"] if q == "Q1: Automation opportunity" else COLORS["primary"]
        for q in targets["quadrant"]
    ]

    labels = [
        f"{row['adoption_gap']:.1f}pp gap | {row['quadrant'].split(':')[0]}"
        for _, row in targets.iterrows()
    ]

    fig = go.Figure(go.Bar(
        y=targets["title_current"],
        x=targets["relevance_score"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=labels,
        textposition="outside",
        textfont=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Relevance score: %{x:,.0f}<extra></extra>",
    ))

    chart_h = max(600, len(targets) * 28 + 200)
    style_figure(
        fig,
        "Workforce Training Targets — AI Tool Adoption Leverage",
        subtitle=(
            "Q1 (orange): AI already leads, deployment gap remains | "
            "Q3 (blue): humans still have edge, AI tools exist | "
            "Score = employment × median wage"
        ),
        x_title=None,
        height=chart_h,
        show_legend=False,
    )
    fig.update_layout(
        margin=dict(l=20, r=200, t=80, b=80),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False, zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=9, family=FONT_FAMILY)),
        bargap=0.2,
    )
    return fig


def _researcher_sensitivity(robustness_csv: pd.DataFrame) -> go.Figure:
    """
    Config sensitivity: shows pct_tasks_affected at major level across all 5 configs.
    Identifies which sectors are stable vs. sensitive to the measurement approach.
    """
    if robustness_csv.empty:
        return go.Figure()
    needed = ["category", "config_label", "pct_tasks_affected"]
    if not all(c in robustness_csv.columns for c in needed):
        return go.Figure()

    # Compute confirmed vs ceiling for each major sector
    confirmed_label = ANALYSIS_CONFIG_LABELS["all_confirmed"]
    ceiling_label = ANALYSIS_CONFIG_LABELS["all_ceiling"]

    pivot = robustness_csv.pivot_table(
        index="category", columns="config_label",
        values="pct_tasks_affected", aggfunc="mean"
    )
    if confirmed_label not in pivot.columns or ceiling_label not in pivot.columns:
        return go.Figure()

    # Range = ceiling - confirmed per sector
    pivot["range"] = pivot[ceiling_label] - pivot[confirmed_label]
    pivot = pivot.sort_values("range", ascending=True)

    col_order = [ANALYSIS_CONFIG_LABELS[k] for k in
                 ["all_confirmed", "human_conversation", "agentic_confirmed",
                  "agentic_ceiling", "all_ceiling"]
                 if ANALYSIS_CONFIG_LABELS[k] in pivot.columns]

    save_csv(pivot.reset_index(), HERE / "results" / "researcher_sensitivity.csv")

    fig = go.Figure()
    palette = CATEGORY_PALETTE[:len(col_order)]
    for i, col in enumerate(col_order):
        if col not in pivot.columns:
            continue
        fig.add_trace(go.Bar(
            y=pivot.index.tolist(),
            x=pivot[col].tolist(),
            orientation="h",
            name=col,
            marker=dict(color=palette[i], line=dict(width=0)),
        ))

    chart_h = max(600, len(pivot) * 32 + 200)
    style_figure(
        fig,
        "Config Sensitivity — Pct Tasks Affected by Sector and Dataset",
        subtitle=(
            "Same sectors, different measurement approaches | "
            "Gap between All Confirmed and All Ceiling = robustness range"
        ),
        x_title="% Tasks Affected",
        height=chart_h,
        show_legend=True,
    )
    fig.update_layout(
        barmode="group",
        bargap=0.15, bargroupgap=0.04,
        margin=dict(l=20, r=40, t=80, b=120),
        xaxis=dict(ticksuffix="%", gridcolor=COLORS["grid"],
                   tickfont=dict(size=9, color=COLORS["muted"])),
        yaxis=dict(showgrid=False, tickfont=dict(size=9, family=FONT_FAMILY)),
        legend=dict(
            orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5,
            font=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
        ),
    )
    return fig


def _layperson_overview(confirmed_major: pd.DataFrame, ceiling_major: pd.DataFrame
                        ) -> go.Figure:
    """
    Simple, plain-language sector view: confirmed vs ceiling workers affected.
    No jargon. Just: 'here's what AI is doing now, here's what it could do.'
    """
    if confirmed_major.empty or ceiling_major.empty:
        return go.Figure()

    df = confirmed_major.merge(
        ceiling_major, on="category", how="outer", suffixes=("_confirmed", "_ceiling")
    )
    df["workers_confirmed"] = df.get("workers_affected_confirmed", pd.Series(0.0)).fillna(0.0)
    df["workers_ceiling"] = df.get("workers_affected_ceiling", pd.Series(0.0)).fillna(0.0)
    df["workers_gap"] = df["workers_ceiling"] - df["workers_confirmed"]
    df = df.sort_values("workers_gap", ascending=True)

    def _fmt(v: float) -> str:
        if v >= 1e6:
            return f"{v / 1e6:.1f}M"
        if v >= 1e3:
            return f"{v / 1e3:.0f}K"
        return str(int(v))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["category"],
        x=df["workers_confirmed"],
        orientation="h",
        name="Workers using AI now",
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=[_fmt(v) for v in df["workers_confirmed"]],
        textposition="inside",
        textfont=dict(size=9, color=COLORS["bg"], family=FONT_FAMILY),
    ))
    fig.add_trace(go.Bar(
        y=df["category"],
        x=df["workers_gap"],
        orientation="h",
        name="Additional workers who could be (capability gap)",
        marker=dict(color=COLORS["accent"], line=dict(width=0), opacity=0.8),
        text=[_fmt(v) for v in df["workers_gap"]],
        textposition="inside",
        textfont=dict(size=9, color=COLORS["bg"], family=FONT_FAMILY),
    ))

    chart_h = max(600, len(df) * 30 + 200)
    style_figure(
        fig,
        "AI in the Workforce: Where We Are vs Where We Could Be",
        subtitle=(
            "Blue = workers in jobs where AI tools are already being actively used | "
            "Orange = additional workers in jobs where the tools exist but aren't deployed yet"
        ),
        x_title="Workers",
        height=chart_h,
        show_legend=True,
    )
    fig.update_layout(
        barmode="stack",
        margin=dict(l=20, r=40, t=80, b=120),
        xaxis=dict(gridcolor=COLORS["grid"], tickfont=dict(size=9)),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        legend=dict(
            orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        ),
    )
    return fig


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    fig_dir = results / "figures"
    committed_figs = HERE / "figures"
    committed_figs.mkdir(exist_ok=True)

    print("Audience Framing — generating outputs...\n")

    # ── Load sibling results ──────────────────────────────────────────────────

    wage_gap_major = _load_csv(
        WAGE_POTENTIAL_DIR / "wage_gap_major.csv",
        required_cols=["category", "wages_affected_gap"],
    )
    adoption_gap_major = _load_csv(
        ADOPTION_GAP_DIR / "occ_gap_major.csv",
        required_cols=["category", "workers_affected_gap"],
    )
    robustness_csv = _load_csv(
        ADOPTION_GAP_DIR / "config_robustness.csv",
        required_cols=["category", "config_label", "pct_tasks_affected"],
    )
    opp_scores = _load_csv(
        AUTO_OPP_DIR / "opportunity_scores.csv",
        required_cols=["title_current", "quadrant", "emp_nat", "median_wage"],
    )

    # Fresh confirmed/ceiling data for layperson chart
    primary_ds = ANALYSIS_CONFIGS["all_confirmed"]
    ceiling_ds = ANALYSIS_CONFIGS["all_ceiling"]
    confirmed_major = _get_occ_data(primary_ds, "major")
    ceiling_major = _get_occ_data(ceiling_ds, "major")

    # ── Policy figure ─────────────────────────────────────────────────────────

    print("== Policy investment priorities ==")
    fig = _policy_priorities(wage_gap_major, adoption_gap_major)
    if fig.data:
        save_figure(fig, fig_dir / "policy_investment_priorities.png")
    else:
        print("  SKIP — missing input data")

    # ── Workforce figure ──────────────────────────────────────────────────────

    print("== Workforce training targets ==")
    fig = _workforce_targets(opp_scores)
    if fig.data:
        save_figure(fig, fig_dir / "workforce_training_targets.png")
    else:
        print("  SKIP — missing input data")

    # ── Researcher sensitivity figure ─────────────────────────────────────────

    print("== Researcher config sensitivity ==")
    fig = _researcher_sensitivity(robustness_csv)
    if fig.data:
        save_figure(fig, fig_dir / "researcher_config_sensitivity.png")
    else:
        print("  SKIP — missing input data")

    # ── Layperson overview ────────────────────────────────────────────────────

    print("== Layperson overview ==")
    fig = _layperson_overview(confirmed_major, ceiling_major)
    if fig.data:
        save_figure(fig, fig_dir / "layperson_opportunity.png")
    else:
        print("  SKIP — missing input data")

    # ── Copy key figures ──────────────────────────────────────────────────────

    print("\n== Copying key figures ==")
    key_figs = [
        "policy_investment_priorities.png",
        "workforce_training_targets.png",
        "researcher_config_sensitivity.png",
        "layperson_opportunity.png",
    ]
    for fname in key_figs:
        src = fig_dir / fname
        if src.exists():
            shutil.copy2(src, committed_figs / fname)
            print(f"  Copied {fname}")
        else:
            print(f"  SKIP: {fname}")

    # ── Generate PDF ──────────────────────────────────────────────────────────

    print("\n== Generating PDF ==")
    md_path = HERE / "audience_framing_report.md"
    pdf_path = results / "audience_framing_report.pdf"
    if md_path.exists():
        generate_pdf(md_path, pdf_path)
        print(f"  Saved {pdf_path.name}")
    else:
        print(f"  SKIP — report not yet written")

    print("\nDone.")


if __name__ == "__main__":
    main()
