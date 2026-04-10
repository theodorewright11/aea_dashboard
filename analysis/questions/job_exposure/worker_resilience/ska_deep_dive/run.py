"""
run.py — SKA Deep Dive: Skills, Abilities, and Knowledge Analysis

Comprehensive sub-report within Worker Resilience. Covers:
1. SKA element trends over time (all_confirmed series, Sept 2024 → Feb 2026)
2. Cross-config comparison of element rankings (all five canonical configs)
3. SKA profile by occupation major category (average gap and S/A/K breakdown)
4. Top SKA elements within each major category vs. overall
5. Most AI-subsumed occupations (where AI coverage is closest to / above 100%)

Run from project root:
    venv/Scripts/python -m analysis.questions.job_exposure.worker_resilience.ska_deep_dive.run
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from analysis.config import (
    ANALYSIS_CONFIGS,
    ANALYSIS_CONFIG_LABELS,
    ANALYSIS_CONFIG_SERIES,
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.data.compute_ska import SKAResult, compute_ska, load_ska_data
from analysis.utils import (
    CATEGORY_PALETTE,
    COLORS,
    FONT_FAMILY,
    save_csv,
    save_figure,
    style_figure,
)
from backend.compute import load_eco_raw

HERE = Path(__file__).resolve().parent
PRIMARY_KEY = "all_confirmed"
TOP_N_ELEMENTS = 15
TOP_N_OCCS = 25
TOP_N_CATS = 20  # category chart rows


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_date(dataset_name: str) -> str:
    """Extract YYYY-MM-DD from a dataset name string."""
    m = re.search(r"\d{4}-\d{2}-\d{2}", dataset_name)
    return m.group() if m else dataset_name


def _compute_element_summary(result: SKAResult) -> pd.DataFrame:
    """
    Compute ai_pct_eco_mean per element from a SKAResult.
    ai_pct_eco_mean = ai_capability / mean(occ_score) × 100
    Below 100 = human advantage; above 100 = AI leads.
    """
    ai_cap = result.ai_capability.rename(columns={"ai_score": "ai_capability"})
    eco_base = result.eco_baseline.rename(columns={"eco_score": "eco_baseline"})
    df = ai_cap.merge(eco_base, on=["element_name", "type"])
    df["ai_pct_eco_mean"] = df["ai_capability"] / df["eco_baseline"] * 100.0
    return df[["element_name", "type", "ai_capability", "eco_baseline", "ai_pct_eco_mean"]]


def _occ_elem_concat(result: SKAResult) -> pd.DataFrame:
    """Concatenate per-occ element scores from all domains, add ai_pct_occ."""
    parts = []
    for t, df in result.occ_element_scores.items():
        parts.append(df.assign(type=t))
    combined = pd.concat(parts, ignore_index=True)
    combined["ai_pct_occ"] = np.where(
        combined["occ_score"] > 0,
        combined["ai_score"] / combined["occ_score"] * 100.0,
        np.nan,
    )
    return combined


def _trend_line_chart(
    trend_df: pd.DataFrame,
    domain: Optional[str],
    title: str,
    subtitle: str,
    n: int = TOP_N_ELEMENTS,
) -> go.Figure:
    """
    Line chart: top N elements by gain across dates, one line per element.
    trend_df cols: element_name, type, date, ai_pct_eco_mean, dataset.
    """
    df = trend_df.copy()
    if domain:
        df = df[df["type"] == domain]

    dates = sorted(df["date"].unique())
    if len(dates) < 2:
        return go.Figure()

    # Compute gain = last_date - first_date
    first = df[df["date"] == dates[0]].set_index("element_name")["ai_pct_eco_mean"]
    last = df[df["date"] == dates[-1]].set_index("element_name")["ai_pct_eco_mean"]
    gains = (last - first).dropna().sort_values(ascending=False)
    top_elements = gains.head(n).index.tolist()

    fig = go.Figure()
    palette = CATEGORY_PALETTE if len(top_elements) <= len(CATEGORY_PALETTE) else None

    for i, elem in enumerate(top_elements):
        elem_df = df[df["element_name"] == elem].sort_values("date")
        color = palette[i % len(palette)] if palette else None
        gain_val = gains.get(elem, 0)
        fig.add_trace(go.Scatter(
            x=elem_df["date"],
            y=elem_df["ai_pct_eco_mean"],
            mode="lines+markers",
            name=f"{elem} (+{gain_val:.0f}pp)",
            line=dict(color=color, width=2),
            marker=dict(size=6),
            hovertemplate=(
                f"<b>{elem}</b><br>"
                "Date: %{x}<br>"
                "AI at %{y:.0f}% of occ need<extra></extra>"
            ),
        ))

    fig.add_hline(y=100, line_dash="dot", line_color=COLORS["neutral"], line_width=1,
                  annotation_text="100% = AI matches occ need",
                  annotation_position="bottom right",
                  annotation_font=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY))

    style_figure(fig, title, subtitle=subtitle,
                 x_title="Date", y_title="AI capability as % of occ requirement",
                 height=500, show_legend=True)
    fig.update_layout(
        legend=dict(font=dict(size=9, family=FONT_FAMILY), orientation="v",
                    x=1.01, y=1, xanchor="left"),
        margin=dict(l=20, r=220, t=80, b=60),
        xaxis=dict(type="category"),
        yaxis=dict(showgrid=True, gridcolor=COLORS["border"]),
    )
    return fig


def _gain_bar_chart(
    gains_df: pd.DataFrame,
    title: str,
    subtitle: str,
    n: int = TOP_N_ELEMENTS,
) -> go.Figure:
    """Horizontal bar: top N elements by gain (first→last date)."""
    top = gains_df.nlargest(n, "gain").sort_values("gain", ascending=True)
    if top.empty:
        return go.Figure()

    colors = [COLORS["negative"] if row["gain"] > 0 else COLORS["primary"]
              for _, row in top.iterrows()]
    labels = [f"+{v:.0f}pp  ({t})" for v, t in zip(top["gain"], top["type"])]

    fig = go.Figure(go.Bar(
        x=top["gain"],
        y=top["element_name"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=labels,
        textposition="outside",
        textfont=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    chart_h = max(400, len(top) * 36 + 180)
    style_figure(fig, title, subtitle=subtitle,
                 x_title="Change in AI capability (pp, first → last date)",
                 height=chart_h, show_legend=False)
    fig.update_layout(
        margin=dict(l=20, r=140, t=80, b=60),
        xaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=True,
                   zerolinecolor=COLORS["border"]),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        bargap=0.3,
    )
    return fig


def _cross_config_bar(
    config_elem_df: pd.DataFrame,
    direction: str,
    domain: Optional[str],
    title: str,
    subtitle: str,
    n: int = 10,
) -> go.Figure:
    """
    Grouped horizontal bar: top N elements (by all_confirmed) across all 5 configs.
    direction: "human_advantage" (lowest ai_pct_eco_mean) or "ai_advantage" (highest).
    """
    primary_df = config_elem_df[config_elem_df["config"] == PRIMARY_KEY].copy()
    if domain:
        primary_df = primary_df[primary_df["type"] == domain]
        config_elem_df = config_elem_df[config_elem_df["type"] == domain]

    if direction == "human_advantage":
        top_elements = primary_df.nsmallest(n, "ai_pct_eco_mean")["element_name"].tolist()
        sort_ascending = True
    else:
        top_elements = primary_df.nlargest(n, "ai_pct_eco_mean")["element_name"].tolist()
        sort_ascending = False

    df = config_elem_df[config_elem_df["element_name"].isin(top_elements)].copy()
    configs = list(ANALYSIS_CONFIG_LABELS.keys())
    config_labels = [ANALYSIS_CONFIG_LABELS[k] for k in configs]

    fig = go.Figure()
    for cfg_key, cfg_label, color in zip(
        configs, config_labels,
        [COLORS["primary"], COLORS["secondary"], COLORS["negative"],
         COLORS["accent"], COLORS["muted"]][:len(configs)]
    ):
        cfg_df = df[df["config"] == cfg_key].set_index("element_name")
        y_vals = []
        x_vals = []
        for elem in top_elements:
            y_vals.append(elem)
            val = cfg_df.loc[elem, "ai_pct_eco_mean"] if elem in cfg_df.index else np.nan
            x_vals.append(val)

        fig.add_trace(go.Bar(
            name=cfg_label,
            x=x_vals,
            y=y_vals,
            orientation="h",
            marker=dict(color=color, line=dict(width=0)),
            hovertemplate=f"<b>%{{y}}</b><br>{cfg_label}: %{{x:.0f}}%<extra></extra>",
        ))

    fig.add_vline(x=100, line_dash="dot", line_color=COLORS["neutral"], line_width=1)
    chart_h = max(400, len(top_elements) * 42 + 200)
    style_figure(fig, title, subtitle=subtitle,
                 x_title="AI capability as % of occ requirement",
                 height=chart_h, show_legend=True)
    fig.update_layout(
        barmode="group",
        legend=dict(font=dict(size=10, family=FONT_FAMILY), orientation="h",
                    x=0, y=-0.15),
        margin=dict(l=20, r=40, t=80, b=120),
        xaxis=dict(showgrid=True, gridcolor=COLORS["border"]),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        bargap=0.2, bargroupgap=0.05,
    )
    return fig


def _category_bar(
    cat_summary: pd.DataFrame,
    metric: str,
    title: str,
    subtitle: str,
) -> go.Figure:
    """Horizontal bar: average SKA metric by major occupation category."""
    df = cat_summary.sort_values(metric, ascending=True)
    labels = [f"{v:.0f}%  (n={n})" for v, n in zip(df[metric], df["n_occs"])]

    fig = go.Figure(go.Bar(
        x=df[metric],
        y=df["major_occ_category"],
        orientation="h",
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=labels,
        textposition="outside",
        textfont=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    fig.add_vline(x=100, line_dash="dot", line_color=COLORS["neutral"], line_width=1)
    chart_h = max(400, len(df) * 36 + 180)
    style_figure(fig, title, subtitle=subtitle,
                 x_title="AI capability as % of occupation requirement (avg across occs in category)",
                 height=chart_h, show_legend=False)
    fig.update_layout(
        margin=dict(l=20, r=140, t=80, b=60),
        xaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        bargap=0.25,
    )
    return fig


def _category_ska_breakdown(
    cat_summary: pd.DataFrame,
    title: str,
    subtitle: str,
) -> go.Figure:
    """Grouped horizontal bar: skills_pct, abilities_pct, knowledge_pct by category."""
    df = cat_summary.sort_values("overall_pct", ascending=True)

    domain_colors = {
        "Skills": COLORS["primary"],
        "Abilities": COLORS["secondary"],
        "Knowledge": COLORS["negative"],
    }
    fig = go.Figure()
    for domain, col in [("Skills", "skills_pct"), ("Abilities", "abilities_pct"),
                        ("Knowledge", "knowledge_pct")]:
        fig.add_trace(go.Bar(
            name=domain,
            x=df[col],
            y=df["major_occ_category"],
            orientation="h",
            marker=dict(color=domain_colors[domain], line=dict(width=0)),
            hovertemplate=f"<b>%{{y}}</b><br>{domain}: %{{x:.0f}}%<extra></extra>",
        ))

    fig.add_vline(x=100, line_dash="dot", line_color=COLORS["neutral"], line_width=1)
    chart_h = max(500, len(df) * 42 + 200)
    style_figure(fig, title, subtitle=subtitle,
                 x_title="AI capability as % of occupation requirement",
                 height=chart_h, show_legend=True)
    fig.update_layout(
        barmode="group",
        legend=dict(font=dict(size=10, family=FONT_FAMILY), orientation="h",
                    x=0, y=-0.10),
        margin=dict(l=20, r=40, t=80, b=100),
        xaxis=dict(showgrid=True, gridcolor=COLORS["border"]),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        bargap=0.2, bargroupgap=0.05,
    )
    return fig


def _category_element_heatmap(
    cat_elem_df: pd.DataFrame,
    element_list: list[str],
    title: str,
    subtitle: str,
) -> go.Figure:
    """
    Heatmap: major_occ_category (y) × element_name (x) → mean_ai_pct.
    Shows where AI leads (warm) vs. humans lead (cool) across sectors.
    """
    pivot = cat_elem_df[cat_elem_df["element_name"].isin(element_list)].pivot_table(
        index="major_occ_category",
        columns="element_name",
        values="mean_ai_pct",
        aggfunc="mean",
    )
    pivot = pivot.reindex(columns=element_list)
    # Sort rows by overall mean (most AI-covered at top)
    pivot = pivot.loc[pivot.mean(axis=1).sort_values(ascending=True).index]

    z = pivot.values
    fig = go.Figure(go.Heatmap(
        z=z,
        x=element_list,
        y=pivot.index.tolist(),
        colorscale=[
            [0.0, COLORS["primary"]],
            [0.5, "#f5f5f0"],
            [1.0, COLORS["negative"]],
        ],
        zmid=100,
        text=np.round(z, 0),
        texttemplate="%{text:.0f}%",
        hovertemplate="<b>%{y}</b><br>%{x}<br>AI at %{z:.0f}% of occ need<extra></extra>",
        showscale=True,
        colorbar=dict(title="AI as %<br>of occ need",
                      tickfont=dict(size=9, family=FONT_FAMILY)),
    ))
    chart_h = max(500, len(pivot) * 26 + 250)
    chart_w = max(900, len(element_list) * 48 + 250)
    style_figure(fig, title, subtitle=subtitle, x_title=None, y_title=None,
                 height=chart_h, width=chart_w, show_legend=False)
    fig.update_layout(
        margin=dict(l=20, r=100, t=80, b=120),
        xaxis=dict(tickangle=-45, tickfont=dict(size=8, family=FONT_FAMILY)),
        yaxis=dict(autorange="reversed", tickfont=dict(size=9, family=FONT_FAMILY)),
    )
    return fig


def _most_subsumed_bar(
    occ_gaps: pd.DataFrame,
    title: str,
    subtitle: str,
    n: int = TOP_N_OCCS,
) -> go.Figure:
    """Horizontal bar: top N occupations by overall_pct, colored by major category."""
    top = occ_gaps.nlargest(n, "overall_pct").sort_values("overall_pct", ascending=True)
    if top.empty:
        return go.Figure()

    # Assign colors by major category
    cats = top["major_occ_category"].fillna("Unknown").unique()
    cat_color_map = {cat: CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)]
                     for i, cat in enumerate(sorted(cats))}
    bar_colors = [cat_color_map.get(c, COLORS["neutral"])
                  for c in top["major_occ_category"].fillna("Unknown")]

    labels = [f"{v:.0f}%  ({c})" for v, c in
              zip(top["overall_pct"], top["major_occ_category"].fillna("Unknown"))]

    fig = go.Figure(go.Bar(
        x=top["overall_pct"],
        y=top["title_current"],
        orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=labels,
        textposition="outside",
        textfont=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>AI at %{x:.0f}% of overall SKA need<extra></extra>",
    ))
    fig.add_vline(x=100, line_dash="dot", line_color=COLORS["neutral"], line_width=1)
    chart_h = max(500, n * 26 + 200)
    style_figure(fig, title, subtitle=subtitle,
                 x_title="AI capability as % of overall SKA requirement",
                 height=chart_h, show_legend=False)
    fig.update_layout(
        margin=dict(l=20, r=240, t=80, b=60),
        xaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=9, family=FONT_FAMILY)),
        bargap=0.25,
    )
    return fig


def _subsumed_ska_breakdown(
    occ_gaps: pd.DataFrame,
    title: str,
    subtitle: str,
    n: int = 20,
) -> go.Figure:
    """Grouped horizontal bar: skills/abilities/knowledge breakdown for top N subsumed occs."""
    top = occ_gaps.nlargest(n, "overall_pct").sort_values("overall_pct", ascending=True)
    domain_colors = {
        "Skills": COLORS["primary"],
        "Abilities": COLORS["secondary"],
        "Knowledge": COLORS["negative"],
    }
    fig = go.Figure()
    for domain, col in [("Skills", "skills_pct"), ("Abilities", "abilities_pct"),
                        ("Knowledge", "knowledge_pct")]:
        fig.add_trace(go.Bar(
            name=domain,
            x=top[col],
            y=top["title_current"],
            orientation="h",
            marker=dict(color=domain_colors[domain], line=dict(width=0)),
            hovertemplate=f"<b>%{{y}}</b><br>{domain}: %{{x:.0f}}%<extra></extra>",
        ))
    fig.add_vline(x=100, line_dash="dot", line_color=COLORS["neutral"], line_width=1)
    chart_h = max(500, n * 36 + 200)
    style_figure(fig, title, subtitle=subtitle,
                 x_title="AI capability as % of occupation requirement",
                 height=chart_h, show_legend=True)
    fig.update_layout(
        barmode="group",
        legend=dict(font=dict(size=10, family=FONT_FAMILY), orientation="h",
                    x=0, y=-0.10),
        margin=dict(l=20, r=40, t=80, b=100),
        xaxis=dict(showgrid=True, gridcolor=COLORS["border"]),
        yaxis=dict(showgrid=False, tickfont=dict(size=9, family=FONT_FAMILY)),
        bargap=0.2, bargroupgap=0.05,
    )
    return fig


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    fig_dir = results / "figures"
    print("SKA Deep Dive -- generating outputs...\n")

    # ── Load base data ────────────────────────────────────────────────────────
    print("Loading base data...")
    ska_data = load_ska_data()

    eco = load_eco_raw()
    assert eco is not None, "load_eco_raw() returned None"
    occ_to_major: pd.Series = (
        eco[["title_current", "major_occ_category"]]
        .drop_duplicates("title_current")
        .set_index("title_current")["major_occ_category"]
    )

    # ── Primary config SKA ────────────────────────────────────────────────────
    print(f"\nComputing primary SKA ({PRIMARY_KEY})...")
    pct_primary = get_pct_tasks_affected(ANALYSIS_CONFIGS[PRIMARY_KEY])
    result_primary: SKAResult = compute_ska(pct_primary, ska_data)
    elem_summary_primary = _compute_element_summary(result_primary)

    occ_gaps = result_primary.occ_gaps.copy()
    occ_gaps["major_occ_category"] = occ_gaps["title_current"].map(occ_to_major)

    occ_elem_all = _occ_elem_concat(result_primary)
    occ_elem_all["major_occ_category"] = occ_elem_all["title_current"].map(occ_to_major)

    save_csv(occ_gaps, results / "occ_gaps_with_category.csv")
    save_csv(elem_summary_primary, results / "element_summary_primary.csv")

    # ── Section 1: Element trends over time ───────────────────────────────────
    print("\n=== Section 1: Element trends over time ===")
    series = ANALYSIS_CONFIG_SERIES[PRIMARY_KEY]
    trend_rows = []
    for dataset in series:
        date_label = _extract_date(dataset)
        print(f"  Computing SKA for {date_label}...")
        pct = get_pct_tasks_affected(dataset)
        result = compute_ska(pct, ska_data)
        elem_df = _compute_element_summary(result)
        elem_df["date"] = date_label
        elem_df["dataset"] = dataset
        trend_rows.append(elem_df)
    trend_elem_df = pd.concat(trend_rows, ignore_index=True)
    save_csv(trend_elem_df, results / "element_trends.csv")

    dates = sorted(trend_elem_df["date"].unique())
    first_date, last_date = dates[0], dates[-1]
    first_vals = (
        trend_elem_df[trend_elem_df["date"] == first_date]
        .set_index(["element_name", "type"])["ai_pct_eco_mean"]
    )
    last_vals = (
        trend_elem_df[trend_elem_df["date"] == last_date]
        .set_index(["element_name", "type"])["ai_pct_eco_mean"]
    )
    gains = (last_vals - first_vals).reset_index().rename(
        columns={"ai_pct_eco_mean": "gain"}
    )
    save_csv(gains.sort_values("gain", ascending=False), results / "element_trend_gains.csv")
    print(f"  Total elements tracked: {len(gains)}")
    print(f"  Top gaining element: {gains.nlargest(1, 'gain').iloc[0]['element_name']} "
          f"(+{gains['gain'].max():.1f}pp)")

    # ── Section 2: Cross-config element comparison ────────────────────────────
    print("\n=== Section 2: Cross-config comparison ===")
    config_elem_rows = []
    config_occ_rows = []
    for config_key, dataset in ANALYSIS_CONFIGS.items():
        print(f"  {config_key}...")
        pct = get_pct_tasks_affected(dataset)
        result = compute_ska(pct, ska_data)
        elem_df = _compute_element_summary(result)
        elem_df["config"] = config_key
        elem_df["config_label"] = ANALYSIS_CONFIG_LABELS[config_key]
        config_elem_rows.append(elem_df)

        occ_cfg = result.occ_gaps.copy()
        occ_cfg["config"] = config_key
        occ_cfg["config_label"] = ANALYSIS_CONFIG_LABELS[config_key]
        occ_cfg["major_occ_category"] = occ_cfg["title_current"].map(occ_to_major)
        config_occ_rows.append(occ_cfg)

    config_elem_df = pd.concat(config_elem_rows, ignore_index=True)
    config_occ_df = pd.concat(config_occ_rows, ignore_index=True)
    save_csv(config_elem_df, results / "cross_config_elements.csv")
    save_csv(config_occ_df, results / "cross_config_occ_gaps.csv")

    # Cross-config median overall_pct per config
    config_medians = (
        config_occ_df.groupby("config_label")["overall_pct"]
        .median()
        .reset_index()
        .sort_values("overall_pct", ascending=False)
    )
    print("  Config medians (overall_pct):")
    for _, row in config_medians.iterrows():
        print(f"    {row['config_label']}: {row['overall_pct']:.1f}%")

    # ── Section 3 & 4: Category analysis ─────────────────────────────────────
    print("\n=== Section 3-4: Category analysis ===")
    cat_summary = (
        occ_gaps.groupby("major_occ_category")
        .agg(
            n_occs=("title_current", "count"),
            overall_pct=("overall_pct", "mean"),
            skills_pct=("skills_pct", "mean"),
            abilities_pct=("abilities_pct", "mean"),
            knowledge_pct=("knowledge_pct", "mean"),
        )
        .reset_index()
        .sort_values("overall_pct", ascending=False)
    )
    save_csv(cat_summary, results / "category_summary.csv")

    print("  Category summary (top 5 by overall_pct):")
    for _, row in cat_summary.head(5).iterrows():
        print(f"    {row['major_occ_category']}: {row['overall_pct']:.1f}%")

    # Element-level by category: mean ai_pct_occ per (major_category, element)
    cat_elem = (
        occ_elem_all.groupby(["major_occ_category", "element_name", "type"])["ai_pct_occ"]
        .mean()
        .reset_index()
        .rename(columns={"ai_pct_occ": "mean_ai_pct"})
    )
    save_csv(cat_elem, results / "category_element_means.csv")

    # Per-category top 5 human-advantage and AI-advantage elements
    cat_top_rows = []
    for cat, cat_df in cat_elem.groupby("major_occ_category"):
        top_human = (
            cat_df.nsmallest(5, "mean_ai_pct")
            .assign(direction="human_advantage", category=cat)
        )
        top_ai = (
            cat_df.nlargest(5, "mean_ai_pct")
            .assign(direction="ai_advantage", category=cat)
        )
        cat_top_rows.extend([top_human, top_ai])
    cat_top_df = pd.concat(cat_top_rows, ignore_index=True)
    save_csv(cat_top_df, results / "category_top_elements.csv")

    # Find elements with highest cross-category variance (differ most between sectors)
    elem_cat_pivot = cat_elem.pivot_table(
        index="element_name", columns="major_occ_category", values="mean_ai_pct"
    )
    elem_variance = elem_cat_pivot.std(axis=1).sort_values(ascending=False)
    high_variance_elements = elem_variance.head(20).index.tolist()
    save_csv(elem_variance.reset_index().rename(columns={0: "std_across_cats"}),
             results / "element_cross_category_variance.csv")

    # ── Section 5: Most subsumed occupations ──────────────────────────────────
    print("\n=== Section 5: Most subsumed occupations ===")
    top_subsumed = occ_gaps.nlargest(TOP_N_OCCS, "overall_pct").copy()
    save_csv(top_subsumed, results / "most_subsumed_occupations.csv")
    print(f"  Top subsumed: {top_subsumed.iloc[0]['title_current']} "
          f"({top_subsumed.iloc[0]['overall_pct']:.1f}%)")
    print(f"  #25: {top_subsumed.iloc[-1]['title_current']} "
          f"({top_subsumed.iloc[-1]['overall_pct']:.1f}%)")

    # ── Figures ───────────────────────────────────────────────────────────────
    print("\n=== Generating figures ===")
    primary_label = ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]

    # -- Trend: gain bar (all domains)
    fig = _gain_bar_chart(
        gains,
        title="SKA Elements With the Biggest Gains in AI Coverage",
        subtitle=f"Change in AI capability as % of occ need, {first_date} → {last_date} | {primary_label}",
    )
    save_figure(fig, fig_dir / "element_gains_all.png")
    print("  element_gains_all.png")

    # -- Trend: gain bar per domain
    for domain in ["skills", "abilities", "knowledge"]:
        fig = _gain_bar_chart(
            gains[gains["type"] == domain],
            title=f"{domain.title()} — Biggest AI Coverage Gains Over Time",
            subtitle=f"{first_date} → {last_date} | {primary_label}",
        )
        if fig.data:
            save_figure(fig, fig_dir / f"element_gains_{domain}.png")
            print(f"  element_gains_{domain}.png")

    # -- Trend: line charts per domain
    for domain in ["skills", "abilities", "knowledge"]:
        fig = _trend_line_chart(
            trend_elem_df,
            domain=domain,
            title=f"{domain.title()} — AI Coverage Over Time (Top Growing Elements)",
            subtitle=f"AI capability as % of occ need | {primary_label} series",
        )
        if fig.data:
            save_figure(fig, fig_dir / f"element_trends_{domain}.png")
            print(f"  element_trends_{domain}.png")

    # -- Cross-config: human advantage comparison
    fig = _cross_config_bar(
        config_elem_df, direction="human_advantage", domain=None,
        title="Top Human-Advantage Elements Across All Configs",
        subtitle="AI capability as % of occ need | elements ranked by all_confirmed | lower = bigger human advantage",
    )
    if fig.data:
        save_figure(fig, fig_dir / "cross_config_human_advantage.png")
        print("  cross_config_human_advantage.png")

    # -- Cross-config: AI advantage comparison
    fig = _cross_config_bar(
        config_elem_df, direction="ai_advantage", domain=None,
        title="Top AI-Advantage Elements Across All Configs",
        subtitle="AI capability as % of occ need | elements ranked by all_confirmed | higher = bigger AI lead",
    )
    if fig.data:
        save_figure(fig, fig_dir / "cross_config_ai_advantage.png")
        print("  cross_config_ai_advantage.png")

    # -- Cross-config: per-domain human advantage
    for domain in ["skills", "abilities", "knowledge"]:
        fig = _cross_config_bar(
            config_elem_df, direction="human_advantage", domain=domain,
            title=f"{domain.title()} — Human Advantage Across Configs",
            subtitle="AI capability as % of occ need | lower = bigger human advantage",
        )
        if fig.data:
            save_figure(fig, fig_dir / f"cross_config_human_{domain}.png")
            print(f"  cross_config_human_{domain}.png")

    # -- Category: overall_pct bar
    fig = _category_bar(
        cat_summary, metric="overall_pct",
        title="Average AI Coverage of SKA Requirements by Occupation Category",
        subtitle=f"Mean overall_pct across all occupations in each category | {primary_label}",
    )
    if fig.data:
        save_figure(fig, fig_dir / "category_overall_pct.png")
        print("  category_overall_pct.png")

    # -- Category: S/A/K breakdown
    fig = _category_ska_breakdown(
        cat_summary,
        title="Skills, Abilities, and Knowledge — AI Coverage by Occupation Category",
        subtitle=f"Mean ai_pct per domain across occupations in each category | {primary_label}",
    )
    if fig.data:
        save_figure(fig, fig_dir / "category_ska_breakdown.png")
        print("  category_ska_breakdown.png")

    # -- Category element heatmap (high-variance elements)
    fig = _category_element_heatmap(
        cat_elem, element_list=high_variance_elements,
        title="Which SKA Elements Vary Most Across Occupation Categories",
        subtitle=(
            "Mean AI coverage (%) of occupations in each sector | "
            "Blue <100% (human advantage) | Red >100% (AI leads) | "
            f"Elements selected by cross-category variance | {primary_label}"
        ),
    )
    if fig.data:
        save_figure(fig, fig_dir / "category_element_heatmap.png")
        print("  category_element_heatmap.png")

    # -- Most subsumed occupations
    fig = _most_subsumed_bar(
        occ_gaps,
        title=f"Most AI-Subsumed Occupations — Top {TOP_N_OCCS} by Overall SKA Coverage",
        subtitle=f"AI capability as % of occupation's overall SKA requirement | {primary_label}",
    )
    if fig.data:
        save_figure(fig, fig_dir / "most_subsumed_occupations.png")
        print("  most_subsumed_occupations.png")

    # -- Most subsumed: S/A/K breakdown
    fig = _subsumed_ska_breakdown(
        occ_gaps,
        title="S/A/K Breakdown for Most AI-Subsumed Occupations",
        subtitle=f"AI capability as % of occupation requirement by domain | {primary_label}",
    )
    if fig.data:
        save_figure(fig, fig_dir / "most_subsumed_ska_breakdown.png")
        print("  most_subsumed_ska_breakdown.png")

    # ── Copy key figures ──────────────────────────────────────────────────────
    committed = HERE / "figures"
    committed.mkdir(exist_ok=True)
    key_figs = [
        "element_gains_all.png",
        "element_gains_skills.png",
        "element_gains_abilities.png",
        "element_gains_knowledge.png",
        "element_trends_skills.png",
        "element_trends_abilities.png",
        "element_trends_knowledge.png",
        "cross_config_human_advantage.png",
        "cross_config_ai_advantage.png",
        "cross_config_human_skills.png",
        "cross_config_human_abilities.png",
        "cross_config_human_knowledge.png",
        "category_overall_pct.png",
        "category_ska_breakdown.png",
        "category_element_heatmap.png",
        "most_subsumed_occupations.png",
        "most_subsumed_ska_breakdown.png",
    ]
    for fname in key_figs:
        src = fig_dir / fname
        if src.exists():
            shutil.copy2(src, committed / fname)

    # ── PDF ───────────────────────────────────────────────────────────────────
    from analysis.utils import generate_pdf
    md_path = HERE / "ska_deep_dive_report.md"
    if md_path.exists():
        generate_pdf(md_path, results / "ska_deep_dive_report.pdf")

    print("\nDone.")


if __name__ == "__main__":
    main()
