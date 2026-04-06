"""
run.py — Economic Footprint: Skills Landscape

What do SKA gaps and technology category profiles look like across the economy?

Two parts:
  1. SKA domain leads — which skill/ability/knowledge elements AI leads vs humans
     at the economy level and broken down by major sector.
  2. Tech category exposure — weight each of ~127 O*NET technology categories
     by (pct_tasks_affected × employment) to get an economy-wide exposure-weighted
     tech profile; break down by major sector.

Primary config: all_confirmed. SKA run for all five configs for robustness.

Outputs:
  results/ska_economy_elements.csv   — Economy-level gap per element × SKA domain
  results/ska_major_gaps.csv         — Average overall_gap per major category × config
  results/tech_categories_economy.csv — Tech categories weighted by exposure × emp
  results/tech_categories_major.csv  — Tech category counts and exposure by major sector
  results/ska_top_ai_leads.csv       — Top elements where AI capability exceeds human
  results/ska_top_human_leads.csv    — Top elements where humans lead AI

Figures (key ones copied to figures/):
  ska_leads_ai.png          — Top 20 elements where AI leads (gap > 0)
  ska_leads_human.png       — Top 20 elements where humans lead (gap < 0)
  ska_major_heatmap.png     — Heatmap: major × SKA domain overall gap
  tech_top_economy.png      — Top 25 tech categories by exposure-weighted presence
  tech_major_heatmap.png    — Heatmap: major × top tech categories (normalized counts)

Run from project root:
    venv/Scripts/python -m analysis.questions.economic_footprint.skills_landscape.run
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
    get_pct_tasks_affected,
)
from analysis.data.compute_ska import SKAData, compute_ska, load_ska_data
from analysis.utils import (
    CATEGORY_PALETTE,
    COLORS,
    FONT_FAMILY,
    generate_pdf,
    make_horizontal_bar,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent.parent.parent.parent / "analysis" / "data"
TECH_SKILLS_FILE = DATA_DIR / "technology_skills_v30.1.csv"
PRIMARY_KEY = "all_confirmed"


# ── Data helpers ───────────────────────────────────────────────────────────────

def _get_structural() -> pd.DataFrame:
    """Return occ-level structural data: title_current, emp, major."""
    from backend.compute import get_explorer_occupations

    rows = [
        {
            "title_current": o["title_current"],
            "emp": o.get("emp") or 0,
            "major": o.get("major", ""),
        }
        for o in get_explorer_occupations()
    ]
    return pd.DataFrame(rows)


def compute_economy_ska(pct: pd.Series, ska_data: SKAData) -> pd.DataFrame:
    """
    Return per-element economy-level stats: ai_capability, eco_baseline, gap.
    result.ai_capability and result.eco_baseline are DataFrames with
    columns: element_name, ai_score/eco_score, type.
    Returns a single DataFrame with: element_name, domain, ai_capability, eco_baseline, gap.
    """
    result = compute_ska(pct, ska_data)
    # Merge ai_capability and eco_baseline on element_name + type
    ai_df = result.ai_capability.rename(columns={"ai_score": "ai_capability", "type": "domain"})
    eco_df = result.eco_baseline.rename(columns={"eco_score": "eco_baseline", "type": "domain"})
    merged = ai_df.merge(eco_df, on=["element_name", "domain"], how="outer")
    merged["gap"] = merged["ai_capability"] - merged["eco_baseline"]
    return merged


def compute_major_ska_gaps(pct: pd.Series, ska_data: SKAData, structural: pd.DataFrame) -> pd.DataFrame:
    """
    Return per-major-category average overall_gap.
    Joins occ_gaps with structural data.
    """
    result = compute_ska(pct, ska_data)
    gaps = result.occ_gaps[["title_current", "overall_gap"]].copy()
    merged = gaps.merge(structural[["title_current", "major"]], on="title_current", how="left")
    major_gaps = (
        merged.groupby("major")["overall_gap"].mean().reset_index()
        .rename(columns={"overall_gap": "avg_overall_gap"})
    )
    return major_gaps


def load_tech_skills(pct: pd.Series, structural: pd.DataFrame) -> pd.DataFrame:
    """
    Load tech_skills CSV and compute exposure-weighted presence per technology category.
    Weight = pct_tasks_affected × emp for each occ that uses the tech category.
    """
    assert TECH_SKILLS_FILE.exists(), f"Tech skills file not found: {TECH_SKILLS_FILE}"
    tech = pd.read_csv(TECH_SKILLS_FILE)
    # Normalize column names
    tech.columns = [c.strip() for c in tech.columns]

    # Join with structural data (emp, major) by Title → title_current
    struct = structural.copy()
    tech = tech.merge(struct.rename(columns={"title_current": "Title"}), on="Title", how="left")

    # Join with pct
    pct_df = pct.reset_index().rename(columns={"index": "Title", 0: "pct", "title_current": "Title"})
    if pct_df.columns.tolist()[0] != "Title":
        pct_df.columns = ["Title", "pct"]
    # Build pct merge df: Title (O*NET title) → pct value
    pct_merge = pct.rename("pct").reset_index()
    pct_merge.columns = ["Title", "pct"]  # pct Series index is title_current = O*NET Title
    tech = tech.merge(pct_merge, on="Title", how="left")
    tech["pct"] = tech["pct"].fillna(0.0)
    tech["emp"] = tech["emp"].fillna(0.0)

    # Exposure weight: pct × emp per occ
    tech["exposure_weight"] = tech["pct"] * tech["emp"]

    return tech


def aggregate_tech_categories(tech: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate by Commodity Title (tech category):
      - total_exposure_weight: sum of pct × emp across all occs using this category
      - n_occs: number of unique occupations using it
      - n_entries: raw row count
    """
    agg = (
        tech.groupby("Commodity Title")
        .agg(
            total_exposure_weight=("exposure_weight", "sum"),
            n_occs=("Title", "nunique"),
            n_entries=("Title", "count"),
        )
        .reset_index()
        .sort_values("total_exposure_weight", ascending=False)
    )
    return agg


def aggregate_tech_by_major(tech: pd.DataFrame, top_categories: list[str]) -> pd.DataFrame:
    """
    For top tech categories: count distinct occupations per (major, category),
    normalized by number of occs in major.
    """
    filtered = tech[tech["Commodity Title"].isin(top_categories)].copy()
    # Count unique occs per major per category
    counts = (
        filtered.groupby(["major", "Commodity Title"])["Title"]
        .nunique()
        .reset_index()
        .rename(columns={"Title": "n_occs_with_tech"})
    )
    # Total occs per major
    major_totals = tech.groupby("major")["Title"].nunique().reset_index().rename(
        columns={"Title": "total_occs"}
    )
    counts = counts.merge(major_totals, on="major")
    counts["pct_occs"] = counts["n_occs_with_tech"] / counts["total_occs"] * 100
    return counts


# ── Figure builders ────────────────────────────────────────────────────────────

def _build_ska_leads_bar(elem_df: pd.DataFrame, direction: str, top_n: int = 20) -> go.Figure:
    """
    Horizontal bar of top elements where AI leads (gap > 0) or humans lead (gap < 0).
    direction: 'ai' or 'human'
    """
    if direction == "ai":
        sub = elem_df[elem_df["gap"] > 0].sort_values("gap", ascending=False).head(top_n)
        sub = sub.sort_values("gap", ascending=True)  # flip for horizontal bar (top at top)
        title = f"Top {top_n} Elements Where AI Capability Exceeds Human Need"
        subtitle = "Gap = AI capability score − occupation score (positive = AI advantage)"
        color = COLORS["accent"]
    else:
        sub = elem_df[elem_df["gap"] < 0].sort_values("gap", ascending=True).head(top_n)
        sub = sub.sort_values("gap", ascending=False)  # most negative at top
        title = f"Top {top_n} Elements Showing Human Advantage Over AI"
        subtitle = "Gap = AI capability score − occupation score (negative = human advantage)"
        color = COLORS["primary"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sub["gap"],
        y=sub["element_name"] + " (" + sub["domain"] + ")",
        orientation="h",
        marker_color=color,
        text=[f"{v:+.1f}" for v in sub["gap"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(fig, title, subtitle=subtitle,
                 x_title="Gap (AI capability − human occupational score)", show_legend=False,
                 height=700, width=1200)
    fig.update_layout(
        margin=dict(l=20, r=100),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        bargap=0.2,
    )
    return fig


def _build_ska_major_heatmap(major_gaps_all: pd.DataFrame) -> go.Figure:
    """Heatmap: major × config, average overall_gap."""
    pivot = major_gaps_all.pivot_table(
        index="major", columns="config_label", values="avg_overall_gap", aggfunc="first"
    )
    primary_label = ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]
    if primary_label in pivot.columns:
        pivot = pivot.sort_values(primary_label, ascending=True)

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=list(pivot.columns),
        y=list(pivot.index),
        colorscale=[[0, COLORS["primary"]], [0.5, "#f7f7f4"], [1.0, COLORS["accent"]]],
        zmid=0,
        text=[[f"{v:+.1f}" if not np.isnan(v) else "" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=10, family=FONT_FAMILY),
        hovertemplate="%{y} | %{x}: %{z:+.2f}<extra></extra>",
        showscale=True,
        colorbar=dict(title="SKA Gap<br>(AI − human)", tickfont=dict(size=10)),
    ))
    style_figure(fig, "Average SKA Gap by Sector and Config",
                 subtitle="Positive = AI capability exceeds typical occupation need | Negative = human advantage",
                 show_legend=False, height=700, width=1100)
    fig.update_layout(
        xaxis=dict(side="bottom", tickangle=-20, showgrid=False, showline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        margin=dict(l=280, r=80, t=90, b=100),
    )
    return fig


def _build_tech_top_bar(tech_agg: pd.DataFrame, top_n: int = 25) -> go.Figure:
    """Horizontal bar of top tech categories by exposure-weighted presence."""
    top = tech_agg.head(top_n).sort_values("total_exposure_weight", ascending=True)
    fig = go.Figure(go.Bar(
        x=top["total_exposure_weight"],
        y=top["Commodity Title"],
        orientation="h",
        marker_color=COLORS["primary"],
        text=[f"{v/1e9:.1f}B" if v >= 1e9 else f"{v/1e6:.0f}M" for v in top["total_exposure_weight"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(fig, f"Top {top_n} Technology Categories by Exposure-Weighted Presence",
                 subtitle="Weight = pct_tasks_affected × employment summed across occupations using each tech category",
                 x_title="Exposure weight (pct × emp, summed)", show_legend=False,
                 height=800, width=1200)
    fig.update_layout(
        margin=dict(l=20, r=120),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        bargap=0.2,
    )
    return fig


def _build_tech_major_heatmap(major_tech: pd.DataFrame, top_categories: list[str]) -> go.Figure:
    """Heatmap: major × tech category, pct of occs in that major using the tech."""
    pivot = major_tech.pivot_table(
        index="major", columns="Commodity Title", values="pct_occs", aggfunc="first"
    ).fillna(0)
    # Order columns by total pct
    col_order = pivot.sum(axis=0).sort_values(ascending=False).index.tolist()
    pivot = pivot[col_order[:20]]  # top 20 categories only for readability
    # Order rows alphabetically
    pivot = pivot.sort_index()

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=list(pivot.columns),
        y=list(pivot.index),
        colorscale=[[0, "#f0f4f8"], [0.5, COLORS["secondary"]], [1.0, "#0a2e25"]],
        text=[[f"{v:.0f}%" if v > 0 else "" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=9, family=FONT_FAMILY),
        hovertemplate="%{y} | %{x}: %{z:.1f}%<extra></extra>",
        showscale=True,
        colorbar=dict(title="% of occs<br>in sector<br>using tech", tickfont=dict(size=10)),
    ))
    style_figure(fig, "Technology Category Penetration by Sector",
                 subtitle="% of occupations in each major sector that use each technology category",
                 show_legend=False, height=700, width=1400)
    fig.update_layout(
        xaxis=dict(side="bottom", tickangle=-35, showgrid=False, showline=False, tickfont=dict(size=9)),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        margin=dict(l=280, r=80, t=90, b=200),
    )
    return fig


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("skills_landscape: loading SKA data...")
    ska_data = load_ska_data()
    structural = _get_structural()

    # ── 1. SKA — economy-level element gaps (primary config) ──────────────────
    print(f"  SKA economy elements ({ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]})...")
    pct_primary = get_pct_tasks_affected(ANALYSIS_CONFIGS[PRIMARY_KEY])
    all_elements = compute_economy_ska(pct_primary, ska_data)

    save_csv(all_elements.sort_values("gap", ascending=False), results / "ska_economy_elements.csv")

    top_ai = all_elements[all_elements["gap"] > 0].sort_values("gap", ascending=False).head(30)
    top_human = all_elements[all_elements["gap"] < 0].sort_values("gap", ascending=True).head(30)
    save_csv(top_ai, results / "ska_top_ai_leads.csv")
    save_csv(top_human, results / "ska_top_human_leads.csv")
    print(f"  Economy elements: {len(all_elements)} total, "
          f"{(all_elements['gap'] > 0).sum()} AI-led, {(all_elements['gap'] < 0).sum()} human-led")

    # ── 2. SKA — major category gaps across all configs ───────────────────────
    print("  SKA major gaps across configs...")
    major_gap_frames = []
    for key, ds_name in ANALYSIS_CONFIGS.items():
        label = ANALYSIS_CONFIG_LABELS[key]
        pct = get_pct_tasks_affected(ds_name)
        major_gaps = compute_major_ska_gaps(pct, ska_data, structural)
        major_gaps["config_key"] = key
        major_gaps["config_label"] = label
        major_gap_frames.append(major_gaps)

    all_major_gaps = pd.concat(major_gap_frames, ignore_index=True)
    save_csv(all_major_gaps, results / "ska_major_gaps.csv")

    # ── 3. Tech skills analysis ───────────────────────────────────────────────
    print("  Tech skills analysis...")
    tech = load_tech_skills(pct_primary, structural)
    tech_agg = aggregate_tech_categories(tech)
    save_csv(tech_agg, results / "tech_categories_economy.csv")

    top_25_cats = tech_agg.head(25)["Commodity Title"].tolist()
    major_tech = aggregate_tech_by_major(tech, top_25_cats)
    save_csv(major_tech, results / "tech_categories_major.csv")
    print(f"  Tech: {len(tech_agg)} categories, top-25 by exposure weight saved.")

    # ── 4. Figures ────────────────────────────────────────────────────────────

    # 4a. SKA AI leads
    fig_ai = _build_ska_leads_bar(all_elements, "ai", top_n=20)
    save_figure(fig_ai, results / "figures" / "ska_leads_ai.png")
    shutil.copy(results / "figures" / "ska_leads_ai.png", figs_dir / "ska_leads_ai.png")
    print("  ska_leads_ai.png")

    # 4b. SKA human leads
    fig_human = _build_ska_leads_bar(all_elements, "human", top_n=20)
    save_figure(fig_human, results / "figures" / "ska_leads_human.png")
    shutil.copy(results / "figures" / "ska_leads_human.png", figs_dir / "ska_leads_human.png")
    print("  ska_leads_human.png")

    # 4c. SKA major × config heatmap
    fig_heat = _build_ska_major_heatmap(all_major_gaps)
    save_figure(fig_heat, results / "figures" / "ska_major_heatmap.png")
    shutil.copy(results / "figures" / "ska_major_heatmap.png", figs_dir / "ska_major_heatmap.png")
    print("  ska_major_heatmap.png")

    # 4d. Top tech categories
    fig_tech = _build_tech_top_bar(tech_agg, top_n=25)
    save_figure(fig_tech, results / "figures" / "tech_top_economy.png")
    shutil.copy(results / "figures" / "tech_top_economy.png", figs_dir / "tech_top_economy.png")
    print("  tech_top_economy.png")

    # 4e. Tech × major heatmap
    fig_tech_heat = _build_tech_major_heatmap(major_tech, top_25_cats)
    save_figure(fig_tech_heat, results / "figures" / "tech_major_heatmap.png")
    shutil.copy(results / "figures" / "tech_major_heatmap.png", figs_dir / "tech_major_heatmap.png")
    print("  tech_major_heatmap.png")

    # ── 5. Generate PDF ───────────────────────────────────────────────────────
    report_path = HERE / "skills_landscape_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "skills_landscape_report.pdf")

    print("\nskills_landscape: done.")


if __name__ == "__main__":
    main()
