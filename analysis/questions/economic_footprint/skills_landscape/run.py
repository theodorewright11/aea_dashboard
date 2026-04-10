"""
run.py — Economic Footprint: Skills Landscape

What do SKA gaps and technology category profiles look like across the economy?

Two parts:
  1. SKA domain leads — for each O*NET element, AI capability as a percentage
     of the typical occupation's requirement (mean occ_score baseline) AND of
     the top-practitioner requirement (95th pct occ_score baseline). Both views
     are charted to give the policymaker mean-vs-elite framings.
  2. Tech category exposure — three views over the technology_skills_v30.1.csv
     file (one row per (occupation, specific_software) entry):
       (a) Average % tasks affected per commodity (mean of pct across rows)
       (b) Exposed workers per commodity (sum of (pct/100) × emp), labelled
           with the share of all commodity users that this represents
       (c) Exposed wages per commodity (sum of (pct/100) × emp × wage / n_commodities),
           with the n_commodities-in-occ divisor preventing wage double-counting
           when one occupation lists many commodities. Workers don't need this
           divisor (each worker really does interact with multiple software
           categories).

Primary config: all_confirmed. SKA run for all five configs for the major
heatmap.

Outputs:
  results/ska_economy_elements.csv         — Per-element AI cap, eco mean & p95
  results/ska_major_gaps.csv               — overall_pct per major × config
  results/tech_pct_affected_economy.csv    — Chart 1 source
  results/tech_workers_affected_economy.csv — Chart 2 source
  results/tech_wages_affected_economy.csv  — Chart 3 source
  results/tech_categories_major.csv        — Heatmap source (sector penetration)
  results/ska_top_ai_leads.csv             — Top elements where AI ≥ 100% of occ need
  results/ska_top_human_leads.csv          — Top elements where AI < 100% of occ need

Figures (key ones copied to figures/):
  ska_leads_ai_eco_mean.png    — Top 20 elements where AI leads (vs eco_mean baseline)
  ska_leads_human_eco_mean.png — Top 20 elements where humans lead (vs eco_mean)
  ska_leads_ai_eco_p95.png     — Same vs the 95th-pct top-practitioner baseline
  ska_leads_human_eco_p95.png  — Same vs the 95th-pct top-practitioner baseline
  ska_major_heatmap.png        — Heatmap: major × config overall_pct (ratio of sums)
  tech_pct_affected.png        — Chart 1: avg pct affected per commodity
  tech_workers_affected.png    — Chart 2: exposed workers per commodity
  tech_wages_affected.png      — Chart 3: exposed wages per commodity (no double-count)
  tech_major_heatmap.png       — Sector × top-25 commodities (sorted by Chart 2)

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
    """Return occ-level structural data: title_current, emp, wage, major."""
    from backend.compute import get_explorer_occupations

    rows = [
        {
            "title_current": o["title_current"],
            "emp": o.get("emp") or 0,
            "wage": o.get("wage") or 0,
            "major": o.get("major", ""),
        }
        for o in get_explorer_occupations()
    ]
    return pd.DataFrame(rows)


def compute_economy_ska(pct: pd.Series, ska_data: SKAData) -> pd.DataFrame:
    """
    Return per-element economy-level stats with both percentage framings.

    Columns:
      element_name, domain, ai_capability,
      eco_mean, eco_p95,
      ai_pct_eco_mean   = ai_capability / eco_mean × 100
      ai_pct_eco_p95    = ai_capability / eco_p95 × 100
      gap_eco_mean      = ai_capability − eco_mean   (raw imp×level units, kept for ref)
    """
    result = compute_ska(pct, ska_data)
    ai_df = result.ai_capability.rename(
        columns={"ai_score": "ai_capability", "type": "domain"}
    )
    eco_mean_df = result.eco_baseline.rename(
        columns={"eco_score": "eco_mean", "type": "domain"}
    )
    eco_p95_df = result.eco_baseline_p95.rename(
        columns={"eco_score_p95": "eco_p95", "type": "domain"}
    )
    merged = ai_df.merge(eco_mean_df, on=["element_name", "domain"], how="outer")
    merged = merged.merge(eco_p95_df, on=["element_name", "domain"], how="outer")
    merged["ai_pct_eco_mean"] = merged["ai_capability"] / merged["eco_mean"] * 100.0
    merged["ai_pct_eco_p95"] = merged["ai_capability"] / merged["eco_p95"] * 100.0
    merged["gap_eco_mean"] = merged["ai_capability"] - merged["eco_mean"]
    return merged


def compute_major_ska_gaps(pct: pd.Series, ska_data: SKAData, structural: pd.DataFrame) -> pd.DataFrame:
    """
    Return per-major-category average overall_pct (ratio-of-sums per occ, then mean over occs).
    """
    result = compute_ska(pct, ska_data)
    gaps = result.occ_gaps[["title_current", "overall_pct"]].copy()
    merged = gaps.merge(structural[["title_current", "major"]], on="title_current", how="left")
    major_gaps = (
        merged.groupby("major")["overall_pct"].mean().reset_index()
        .rename(columns={"overall_pct": "avg_overall_pct"})
    )
    return major_gaps


def load_tech_skills(pct: pd.Series, structural: pd.DataFrame) -> pd.DataFrame:
    """
    Load technology_skills_v30.1.csv and join per-row with the occupation's
    pct_tasks_affected, employment, wage, and n_commodities count.

    Each row in the source file is one (occupation, specific software entry).
    A single commodity category (e.g. "Office suite software") can have many
    rows for the same occupation if the occ uses multiple softwares in that
    category — these are kept distinct (real instances, not duplicates).

    Adds:
      - pct        — pct_tasks_affected for the row's occupation (0-100)
      - emp        — national employment for the occupation
      - wage       — median annual wage for the occupation
      - major      — major SOC category
      - n_comm_in_occ — number of (occupation, commodity-row) entries the occ
                       has across all commodities, used as the wage divisor
                       to prevent wage double-counting in Chart 3
    """
    assert TECH_SKILLS_FILE.exists(), f"Tech skills file not found: {TECH_SKILLS_FILE}"
    tech = pd.read_csv(TECH_SKILLS_FILE)
    tech.columns = [c.strip() for c in tech.columns]

    struct = structural.copy()
    tech = tech.merge(
        struct.rename(columns={"title_current": "Title"}), on="Title", how="left"
    )

    pct_merge = pct.rename("pct").reset_index()
    pct_merge.columns = ["Title", "pct"]
    tech = tech.merge(pct_merge, on="Title", how="left")
    tech["pct"] = tech["pct"].fillna(0.0)
    tech["emp"] = tech["emp"].fillna(0.0)
    tech["wage"] = tech["wage"].fillna(0.0)

    # n commodities per occupation (count of all rows in tech file for that occ)
    n_comm = tech.groupby("Title").size().rename("n_comm_in_occ").reset_index()
    tech = tech.merge(n_comm, on="Title", how="left")

    return tech


def chart1_pct_affected(tech: pd.DataFrame) -> pd.DataFrame:
    """Chart 1 source: per commodity, mean pct_tasks_affected across rows.

    Each (occ, software) row contributes its occ-level pct. A commodity that
    appears 50 times in 30 occs gets the mean of those 50 pct values.
    """
    agg = (
        tech.groupby("Commodity Title")
        .agg(
            mean_pct_affected=("pct", "mean"),
            n_entries=("Title", "size"),
            n_occs=("Title", "nunique"),
        )
        .reset_index()
        .sort_values("mean_pct_affected", ascending=False)
    )
    return agg


def chart2_workers_affected(tech: pd.DataFrame) -> pd.DataFrame:
    """Chart 2 source: per commodity, sum((pct/100) × emp) across rows.

    No wage-style divisor — workers genuinely interact with multiple commodities
    so the per-row count is the right unit. Also computes total commodity workers
    (sum of emp across rows) and the share affected.
    """
    df = tech.copy()
    df["per_row_workers_affected"] = (df["pct"] / 100.0) * df["emp"]
    agg = (
        df.groupby("Commodity Title")
        .agg(
            workers_affected=("per_row_workers_affected", "sum"),
            total_commodity_workers=("emp", "sum"),
            n_entries=("Title", "size"),
            n_occs=("Title", "nunique"),
        )
        .reset_index()
    )
    agg["pct_of_commodity_workers"] = np.where(
        agg["total_commodity_workers"] > 0,
        agg["workers_affected"] / agg["total_commodity_workers"] * 100.0,
        0.0,
    )
    return agg.sort_values("workers_affected", ascending=False)


def chart3_wages_affected(tech: pd.DataFrame) -> pd.DataFrame:
    """Chart 3 source: per commodity, sum((pct/100) × emp × wage / n_comm_in_occ).

    Divides wage contribution by the number of commodity rows the occupation
    has, so an occupation that lists 80 commodities doesn't multiply its
    payroll by 80. The denominator (total_commodity_wages) uses the same
    divisor for consistency.
    """
    df = tech.copy()
    df["per_row_payroll"] = (df["emp"] * df["wage"]) / df["n_comm_in_occ"].replace(0, np.nan)
    df["per_row_wages_affected"] = (df["pct"] / 100.0) * df["per_row_payroll"]
    agg = (
        df.groupby("Commodity Title")
        .agg(
            wages_affected=("per_row_wages_affected", "sum"),
            total_commodity_wages=("per_row_payroll", "sum"),
            n_entries=("Title", "size"),
            n_occs=("Title", "nunique"),
        )
        .reset_index()
    )
    agg["pct_of_commodity_wages"] = np.where(
        agg["total_commodity_wages"] > 0,
        agg["wages_affected"] / agg["total_commodity_wages"] * 100.0,
        0.0,
    )
    return agg.sort_values("wages_affected", ascending=False)


def aggregate_tech_by_major(tech: pd.DataFrame, top_categories: list[str]) -> pd.DataFrame:
    """
    For top tech categories: count distinct occupations per (major, category),
    normalized by number of occs in major.
    """
    filtered = tech[tech["Commodity Title"].isin(top_categories)].copy()
    counts = (
        filtered.groupby(["major", "Commodity Title"])["Title"]
        .nunique()
        .reset_index()
        .rename(columns={"Title": "n_occs_with_tech"})
    )
    major_totals = tech.groupby("major")["Title"].nunique().reset_index().rename(
        columns={"Title": "total_occs"}
    )
    counts = counts.merge(major_totals, on="major")
    counts["pct_occs"] = counts["n_occs_with_tech"] / counts["total_occs"] * 100
    return counts


# ── Figure builders ────────────────────────────────────────────────────────────

def _build_ska_leads_bar(
    elem_df: pd.DataFrame,
    direction: str,
    baseline: str = "eco_mean",
    top_n: int = 20,
) -> go.Figure:
    """
    Horizontal bar of top elements where AI leads or humans lead, on the
    percentage framing. Reads as "AI is at X% of [the typical / the top
    practitioner's] requirement for this element."

    direction: 'ai' (top elements above 100%) or 'human' (top below 100%)
    baseline:  'eco_mean' (typical occupation) or 'eco_p95' (top practitioners)
    """
    col = f"ai_pct_{baseline}"
    baseline_label = "typical occupation requirement" if baseline == "eco_mean" \
                     else "top-practitioner requirement (95th pct)"

    if direction == "ai":
        if baseline == "eco_p95":
            # Against top practitioners, AI doesn't yet exceed 100% on any element.
            # Show top-N elements where AI comes *closest* to that bar.
            sub = elem_df.sort_values(col, ascending=False).head(top_n)
            sub = sub.sort_values(col, ascending=True)
            title = f"Top {len(sub)} Elements Where AI Comes Closest to Top-Practitioner Need"
        else:
            sub = elem_df[elem_df[col] >= 100].sort_values(col, ascending=False).head(top_n)
            sub = sub.sort_values(col, ascending=True)
            title = f"Top {len(sub)} Elements Where AI ≥ 100% of {baseline_label}"
        color = COLORS["accent"]
    else:
        sub = elem_df[elem_df[col] < 100].sort_values(col, ascending=True).head(top_n)
        sub = sub.sort_values(col, ascending=False)  # bottom→top, smallest at bottom
        title = f"Top {len(sub)} Elements Where Humans Lead AI"
        color = COLORS["primary"]

    if sub.empty:
        return go.Figure()

    subtitle = (
        f"AI capability as % of {baseline_label} | "
        f"100% = AI matches; >100% = AI leads; <100% = human advantage"
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sub[col],
        y=sub["element_name"] + " (" + sub["domain"] + ")",
        orientation="h",
        marker_color=color,
        text=[f"{v:.0f}%" for v in sub[col]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    fig.add_vline(x=100, line_dash="dot", line_color=COLORS["neutral"], line_width=1)
    style_figure(fig, title, subtitle=subtitle,
                 x_title=f"AI capability as % of {baseline_label}", show_legend=False,
                 height=700, width=1200)
    fig.update_layout(
        margin=dict(l=20, r=100),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        bargap=0.2,
    )
    return fig


def _build_ska_major_heatmap(major_gaps_all: pd.DataFrame) -> go.Figure:
    """Heatmap: major × config, average overall_pct (ratio of sums per occ, mean over occs)."""
    pivot = major_gaps_all.pivot_table(
        index="major", columns="config_label", values="avg_overall_pct", aggfunc="first"
    )
    primary_label = ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]
    if primary_label in pivot.columns:
        pivot = pivot.sort_values(primary_label, ascending=True)

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=list(pivot.columns),
        y=list(pivot.index),
        colorscale=[[0, COLORS["primary"]], [0.5, "#f7f7f4"], [1.0, COLORS["accent"]]],
        zmid=100,
        text=[[f"{v:.0f}%" if not np.isnan(v) else "" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=10, family=FONT_FAMILY),
        hovertemplate="%{y} | %{x}: %{z:.1f}%<extra></extra>",
        showscale=True,
        colorbar=dict(title="AI as %<br>of occ need", tickfont=dict(size=10)),
    ))
    style_figure(fig, "Average AI-as-%-of-Occupation-Need by Sector and Config",
                 subtitle=("Per-occ overall_pct = sum(ai_capability) / sum(occ_score) × 100, "
                           "averaged within sector | 100% = AI matches; >100% = AI leads"),
                 show_legend=False, height=700, width=1100)
    fig.update_layout(
        xaxis=dict(side="bottom", tickangle=-20, showgrid=False, showline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        margin=dict(l=280, r=80, t=90, b=100),
    )
    return fig


def _format_workers(v: float) -> str:
    if v >= 1e6:
        return f"{v/1e6:.1f}M"
    if v >= 1e3:
        return f"{v/1e3:.0f}K"
    return f"{v:.0f}"


def _format_dollars(v: float) -> str:
    if v >= 1e9:
        return f"${v/1e9:.1f}B"
    if v >= 1e6:
        return f"${v/1e6:.0f}M"
    if v >= 1e3:
        return f"${v/1e3:.0f}K"
    return f"${v:.0f}"


def _build_tech_pct_affected(chart1: pd.DataFrame, top_n: int = 25) -> go.Figure:
    """Chart 1: top commodities by mean pct_tasks_affected across rows."""
    top = chart1.head(top_n).sort_values("mean_pct_affected", ascending=True)
    labels = [
        f"{p:.1f}%  ({n} entries / {o} occs)"
        for p, n, o in zip(top["mean_pct_affected"], top["n_entries"], top["n_occs"])
    ]
    fig = go.Figure(go.Bar(
        x=top["mean_pct_affected"],
        y=top["Commodity Title"],
        orientation="h",
        marker_color=COLORS["accent"],
        text=labels,
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(
        fig,
        f"Top {top_n} Tech Commodities by % Usage Automatable",
        subtitle=("Mean of pct_tasks_affected across all (occupation, software) rows for each "
                  "commodity. Reads as: 'X% of the usage of this software is AI-affected.'"),
        x_title="Mean % of usage automatable",
        show_legend=False, height=850, width=1200,
    )
    fig.update_layout(
        margin=dict(l=20, r=180),
        xaxis=dict(showgrid=True, gridcolor=COLORS["border"], ticksuffix="%"),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        bargap=0.2,
    )
    return fig


def _build_tech_workers_affected(chart2: pd.DataFrame, top_n: int = 25) -> go.Figure:
    """Chart 2: top commodities by exposed workers (sum((pct/100) × emp))."""
    top = chart2.head(top_n).sort_values("workers_affected", ascending=True)
    labels = [
        f"{_format_workers(w)} workers  ({p:.0f}% of users)"
        for w, p in zip(top["workers_affected"], top["pct_of_commodity_workers"])
    ]
    fig = go.Figure(go.Bar(
        x=top["workers_affected"],
        y=top["Commodity Title"],
        orientation="h",
        marker_color=COLORS["primary"],
        text=labels,
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(
        fig,
        f"Top {top_n} Tech Commodities by Workers in AI-Affected Use",
        subtitle=("Exposed workers = sum((pct_tasks_affected / 100) × employment) across "
                  "the (occ, software) rows that mention each commodity. Label shows the share "
                  "of all commodity users that this represents."),
        x_title="Workers in AI-affected use",
        show_legend=False, height=850, width=1200,
    )
    fig.update_layout(
        margin=dict(l=20, r=200),
        xaxis=dict(showgrid=True, gridcolor=COLORS["border"], showticklabels=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        bargap=0.2,
    )
    return fig


def _build_tech_wages_affected(chart3: pd.DataFrame, top_n: int = 25) -> go.Figure:
    """Chart 3: top commodities by exposed wages (with n-commodities-in-occ divisor)."""
    top = chart3.head(top_n).sort_values("wages_affected", ascending=True)
    labels = [
        f"{_format_dollars(w)} wages  ({p:.0f}% of commodity wages)"
        for w, p in zip(top["wages_affected"], top["pct_of_commodity_wages"])
    ]
    fig = go.Figure(go.Bar(
        x=top["wages_affected"],
        y=top["Commodity Title"],
        orientation="h",
        marker_color=COLORS["secondary"],
        text=labels,
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(
        fig,
        f"Top {top_n} Tech Commodities by Wages in AI-Affected Use",
        subtitle=("Exposed wages = sum((pct/100) × emp × wage / n_commodities_in_occ) across "
                  "the (occ, software) rows. The n_commodities divisor prevents wage "
                  "double-counting when one occ lists many commodities."),
        x_title="Wages in AI-affected use",
        show_legend=False, height=850, width=1200,
    )
    fig.update_layout(
        margin=dict(l=20, r=240),
        xaxis=dict(showgrid=True, gridcolor=COLORS["border"], showticklabels=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        bargap=0.2,
    )
    return fig


def _build_tech_major_heatmap(
    major_tech: pd.DataFrame,
    top_categories_in_order: list[str],
) -> go.Figure:
    """Heatmap: major × tech category. Columns are ordered by `top_categories_in_order`
    (the Chart 2 / exposed-workers ranking) so the most exposed commodities are on
    the left."""
    pivot = major_tech.pivot_table(
        index="major", columns="Commodity Title", values="pct_occs", aggfunc="first"
    ).fillna(0)
    # Use the exposed-workers ranking; keep only commodities present in pivot
    ordered_cols = [c for c in top_categories_in_order if c in pivot.columns][:20]
    pivot = pivot[ordered_cols]
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
    style_figure(
        fig,
        "Technology Category Penetration by Sector",
        subtitle=("% of occupations in each major sector that list each technology category. "
                  "Columns ordered by exposed workers (Chart 2 ranking) so most "
                  "AI-affected commodities sit on the left."),
        show_legend=False, height=700, width=1400,
    )
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

    save_csv(
        all_elements.sort_values("ai_pct_eco_mean", ascending=False),
        results / "ska_economy_elements.csv",
    )

    top_ai = all_elements[all_elements["ai_pct_eco_mean"] >= 100].sort_values(
        "ai_pct_eco_mean", ascending=False
    ).head(30)
    top_human = all_elements[all_elements["ai_pct_eco_mean"] < 100].sort_values(
        "ai_pct_eco_mean", ascending=True
    ).head(30)
    save_csv(top_ai, results / "ska_top_ai_leads.csv")
    save_csv(top_human, results / "ska_top_human_leads.csv")
    print(
        f"  Economy elements: {len(all_elements)} total, "
        f"{(all_elements['ai_pct_eco_mean'] >= 100).sum()} AI-led (vs eco_mean), "
        f"{(all_elements['ai_pct_eco_mean'] < 100).sum()} human-led"
    )

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

    # ── 3. Tech skills analysis (3 charts + heatmap) ─────────────────────────
    print("  Tech skills analysis...")
    tech = load_tech_skills(pct_primary, structural)

    chart1 = chart1_pct_affected(tech)
    chart2 = chart2_workers_affected(tech)
    chart3 = chart3_wages_affected(tech)
    save_csv(chart1, results / "tech_pct_affected_economy.csv")
    save_csv(chart2, results / "tech_workers_affected_economy.csv")
    save_csv(chart3, results / "tech_wages_affected_economy.csv")

    # Heatmap columns are ordered by Chart 2 (exposed workers) ranking
    top_25_by_workers = chart2.head(25)["Commodity Title"].tolist()
    major_tech = aggregate_tech_by_major(tech, top_25_by_workers)
    save_csv(major_tech, results / "tech_categories_major.csv")
    print(
        f"  Tech: {len(chart1)} commodities; chart 1 (pct), 2 (workers), 3 (wages) saved."
    )

    # ── 4. Figures ────────────────────────────────────────────────────────────
    fig_dir = results / "figures"

    def _save_committed(fig, name: str) -> None:
        path = fig_dir / name
        save_figure(fig, path)
        shutil.copy(path, figs_dir / name)
        print(f"  {name}")

    # 4a–4d. SKA AI / human leads × eco_mean / eco_p95 baselines
    _save_committed(_build_ska_leads_bar(all_elements, "ai", "eco_mean"),
                    "ska_leads_ai_eco_mean.png")
    _save_committed(_build_ska_leads_bar(all_elements, "human", "eco_mean"),
                    "ska_leads_human_eco_mean.png")
    _save_committed(_build_ska_leads_bar(all_elements, "ai", "eco_p95"),
                    "ska_leads_ai_eco_p95.png")
    _save_committed(_build_ska_leads_bar(all_elements, "human", "eco_p95"),
                    "ska_leads_human_eco_p95.png")

    # 4e. SKA major × config heatmap
    _save_committed(_build_ska_major_heatmap(all_major_gaps), "ska_major_heatmap.png")

    # 4f–4h. Three tech commodity charts
    _save_committed(_build_tech_pct_affected(chart1, top_n=25), "tech_pct_affected.png")
    _save_committed(_build_tech_workers_affected(chart2, top_n=25), "tech_workers_affected.png")
    _save_committed(_build_tech_wages_affected(chart3, top_n=25), "tech_wages_affected.png")

    # 4i. Tech × major heatmap (sorted by Chart 2 ranking)
    _save_committed(
        _build_tech_major_heatmap(major_tech, top_25_by_workers),
        "tech_major_heatmap.png",
    )

    # ── 5. Generate PDF ───────────────────────────────────────────────────────
    report_path = HERE / "skills_landscape_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "skills_landscape_report.pdf")

    print("\nskills_landscape: done.")


if __name__ == "__main__":
    main()
