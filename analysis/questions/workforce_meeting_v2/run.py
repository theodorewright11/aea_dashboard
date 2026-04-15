"""
run.py — Workforce Meeting v2 Presentation Charts

V2 changes from v1:
- Charts only (no narrative text in report)
- 11 charts (headline, pivot cost, and auto-aug dropped)
- Larger fonts throughout: titles 26px, y-axis labels 15px, inside bar text 20px
- Primary values as large white text inside bars (like "54%" in v1 chart 01)
- Secondary info in smaller text outside bars to the right
- No config subtitles ("All Confirmed | UTAH | ...") on any chart
- X-axis scale visible on all charts with axis title on every chart
- "%" not "pp" for all percentage deltas
- Chart 07: overlaid bars showing conversational vs agentic AI reach by sector
- SKA charts: explicit "= avg job need in this skill" reference line framing

Charts (renumbered for v2):
  01_sector_scope          — Top 7 sectors by workers with AI-exposed tasks
  02_gwa_scope             — Most AI-exposed types of work (GWA, % tasks)
  03_sector_trend          — Fastest-growing sectors (Δ workers)
  04_gwa_trend             — Fastest-growing work types (Δ % tasks)
  05_sector_adoption_gap   — Where AI could still expand: sector untapped %
  06_gwa_adoption_gap      — Where AI could still expand: work activity gap
  07_human_vs_agentic      — Conversational vs. agentic AI reach by sector
  08_ska_human_skills      — Skills where humans still outperform AI
  09_ska_human_knowledge   — Knowledge domains where humans still outperform AI
  10_ska_ai_skills         — Skills where AI has surpassed average job requirements
  11_ska_ai_knowledge      — Knowledge domains where AI has surpassed average job requirements

Run from project root:
    venv/Scripts/python -m analysis.questions.workforce_meeting_v2.run
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from analysis.config import (
    ANALYSIS_CONFIGS,
    ANALYSIS_CONFIG_SERIES,
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    format_workers,
    format_wages,
    generate_pdf,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent

# ── Constants ──────────────────────────────────────────────────────────────────

GEO: str = "ut"
TOP_N: int = 7

PRIMARY_DS: str = ANALYSIS_CONFIGS["all_confirmed"]
CEILING_DS: str = ANALYSIS_CONFIGS["all_ceiling"]
CONV_DS: str = ANALYSIS_CONFIGS["human_conversation"]
AGENTIC_DS: str = ANALYSIS_CONFIGS["agentic_confirmed"]

TREND_FIRST: str = ANALYSIS_CONFIG_SERIES["all_confirmed"][0]
TREND_LAST: str = ANALYSIS_CONFIG_SERIES["all_confirmed"][-1]

CHART_W: int = 1400
CHART_H: int = 787
BAR_COLOR: str = COLORS["primary"]

# Font sizes — larger than v1 for readability
TITLE_FS: int = 26
YAXIS_FS: int = 15
TICK_FS: int = 13
INSIDE_FS: int = 20   # large white text inside bar
OUTSIDE_FS: int = 16  # secondary text outside bar (bumped for readability)
LEGEND_FS: int = 14


# ── Formatting helpers ─────────────────────────────────────────────────────────

def _fmt_date(date_str: str) -> str:
    """Parse 'YYYY-MM-DD' → 'Month YYYY' (e.g. 'March 2025')."""
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %Y")


def _sign_workers(v: float) -> str:
    """Format worker count with explicit +/- sign."""
    sign = "+" if v >= 0 else ""
    return f"{sign}{format_workers(v)}"


def _sign_wages(v: float) -> str:
    """Format wage amount with explicit +/- sign."""
    sign = "+" if v >= 0 else ""
    return f"{sign}{format_wages(v)}"


# ── Data helpers ───────────────────────────────────────────────────────────────

def _get_utah_major(dataset_name: str) -> pd.DataFrame:
    """Major-category breakdown for a single dataset, Utah geo."""
    from backend.compute import get_group_data

    data = get_group_data({
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": GEO,
        "agg_level": "major",
        "sort_by": "Workers Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    })
    assert data is not None, f"No data for {dataset_name}"
    return data["df"].rename(columns={"major_occ_category": "category"})


def _get_utah_gwa(dataset_name: str) -> pd.DataFrame:
    """GWA-level breakdown for a single pre-combined dataset, Utah geo."""
    from backend.compute import compute_work_activities

    result = compute_work_activities({
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": GEO,
        "sort_by": "workers_affected",
        "top_n": 9999,
    })
    group = result.get("mcp_group") or result.get("aei_group")
    assert group is not None, f"No WA data for {dataset_name}"
    rows = group.get("gwa", [])
    assert rows, f"Empty GWA rows for {dataset_name}"
    return pd.DataFrame(rows)


def _get_ska_elements() -> dict[str, pd.DataFrame]:
    """Compute element-level AI coverage % from all_confirmed (national).

    Returns dict["skills"|"knowledge"] → DataFrame[element_name, ai_pct_mean].
    ai_pct_mean = mean of (ai_score / occ_score × 100) across occupations where
    importance >= 3 — i.e., AI as % of each occupation's own requirement, then
    averaged. This is the eco_mean comparison (avg job requirement in this skill).
    """
    from analysis.data.compute_ska import load_ska_data, compute_ska

    pct = get_pct_tasks_affected(PRIMARY_DS, method="freq", use_auto_aug=True)
    ska_data = load_ska_data()
    result = compute_ska(pct, ska_data)

    out: dict[str, pd.DataFrame] = {}
    for domain in ("skills", "knowledge"):
        occ_elem = result.occ_element_scores.get(domain)
        if occ_elem is None or occ_elem.empty:
            out[domain] = pd.DataFrame(columns=["element_name", "ai_pct_mean"])
            continue
        occ_elem = occ_elem.copy()
        safe_occ = occ_elem["occ_score"].replace(0, np.nan)
        occ_elem["ai_pct_occ"] = occ_elem["ai_score"] / safe_occ * 100.0
        elem_agg = (
            occ_elem.groupby("element_name")["ai_pct_occ"]
            .mean()
            .reset_index()
            .rename(columns={"ai_pct_occ": "ai_pct_mean"})
        )
        out[domain] = elem_agg
    return out


# ── Utah total employment / wages (denominators for headline %) ────────────────

def _get_utah_totals() -> tuple[float, float]:
    """Return (total_workers, total_wages) for all Utah occupations.

    Sums emp_tot_ut_2024 across unique occupations in the eco baseline.
    Total wages = sum of emp * a_med (annual median wage) across unique occs.
    """
    from backend.compute import load_eco_raw

    eco = load_eco_raw()
    assert eco is not None, "Could not load eco baseline"

    emp_col = "emp_tot_ut_2024"
    wage_col = "a_med_ut_2024"

    # One row per (occupation × task) — deduplicate to one row per occupation
    occ = eco[["title_current", emp_col, wage_col]].drop_duplicates("title_current")

    total_workers = float(occ[emp_col].fillna(0).sum())
    total_wages = float((occ[emp_col].fillna(0) * occ[wage_col].fillna(0)).sum())
    return total_workers, total_wages


# ── Chart styling helpers ──────────────────────────────────────────────────────

def _apply_base_style(
    fig: go.Figure,
    title: str,
    *,
    subtitle: str | None = None,
    height: int = CHART_H,
    width: int = CHART_W,
    show_legend: bool = False,
) -> go.Figure:
    """Apply v2 base styling: large title, optional subtitle, tight margins."""
    style_figure(
        fig, title,
        subtitle=subtitle,
        show_legend=show_legend,
        height=height,
        width=width,
        source_text="",
    )
    fig.update_layout(
        title=dict(font=dict(size=TITLE_FS, color=COLORS["text"], family=FONT_FAMILY)),
        margin=dict(l=20, r=280, t=90, b=80),
    )
    return fig


def _annotated_bar(
    df: pd.DataFrame,
    category_col: str,
    value_col: str,
    inside_text: list[str],
    outside_text: list[str],
    title: str,
    *,
    subtitle: str | None = None,
    color: str = BAR_COLOR,
    top_n: int = TOP_N,
    xaxis_tickformat: str = "~s",
    xaxis_ticksuffix: str = "",
    xaxis_title: str = "",
    x_range_pad: float = 1.6,
) -> go.Figure:
    """Horizontal bar with large white inside text and secondary outside text.

    inside_text: short primary label (e.g. "146K workers") — rendered as big
                 white text centered inside the bar.
    outside_text: secondary context (e.g. "51% tasks affected · $9.4B wages
                  affected") — larger text to the right of the bar end.
    xaxis_title: label shown below x-axis ticks describing the unit.
    """
    plot_df = df.head(top_n).copy()
    ins = inside_text[:top_n]
    out_ = outside_text[:top_n]
    max_val = float(plot_df[value_col].max()) if len(plot_df) > 0 else 1.0

    fig = go.Figure()

    # Main bar — large white text inside
    fig.add_trace(go.Bar(
        x=plot_df[value_col],
        y=plot_df[category_col],
        orientation="h",
        marker=dict(color=color, line=dict(width=0)),
        text=ins,
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=INSIDE_FS, color="white", family=FONT_FAMILY),
        cliponaxis=False,
    ))

    # Secondary text to the right of each bar — offset by 4% of max for gap
    fig.add_trace(go.Scatter(
        x=plot_df[value_col] + max_val * 0.04,
        y=plot_df[category_col],
        mode="text",
        text=out_,
        textposition="middle right",
        textfont=dict(size=OUTSIDE_FS, color=COLORS["neutral"], family=FONT_FAMILY),
        showlegend=False,
        hoverinfo="skip",
    ))

    fig.update_yaxes(
        autorange="reversed",
        showgrid=False,
        showline=False,
        tickfont=dict(size=YAXIS_FS, color=COLORS["text"], family=FONT_FAMILY),
    )

    _apply_base_style(fig, title, subtitle=subtitle)

    xaxis_cfg: dict = dict(
        showgrid=True,
        gridcolor=COLORS["grid"],
        showticklabels=True,
        tickformat=xaxis_tickformat,
        ticksuffix=xaxis_ticksuffix,
        showline=False,
        zeroline=False,
        range=[0, max_val * x_range_pad],
        tickfont=dict(size=TICK_FS, color=COLORS["neutral"], family=FONT_FAMILY),
    )
    if xaxis_title:
        xaxis_cfg["title"] = dict(
            text=xaxis_title,
            font=dict(size=TICK_FS, color=COLORS["neutral"], family=FONT_FAMILY),
        )

    fig.update_layout(
        xaxis=xaxis_cfg,
        yaxis=dict(
            showgrid=False,
            showline=False,
            tickfont=dict(size=YAXIS_FS, color=COLORS["text"], family=FONT_FAMILY),
        ),
        bargap=0.25,
    )

    return fig


# ── Chart 00: Headline numbers ────────────────────────────────────────────────

def _chart_00_headline(
    major_df: pd.DataFrame,
    total_workers: float,
    total_wages: float,
) -> go.Figure:
    """Three big metric tiles: % tasks affected, workers affected, wages affected.

    Workers and wages are shown with their absolute value and as a % of total
    Utah employment / total Utah wage generation.
    """
    # Aggregate across all sectors from confirmed dataset
    workers_aff = float(major_df["workers_affected"].sum())
    wages_aff   = float(major_df["wages_affected"].sum())

    # pct_tasks_affected is ratio-of-totals — pull from any single-sector agg
    # by recomputing: workers_affected / total_workers (approx scope)
    # Better: use weighted avg from the df itself (workers-weighted pct_tasks)
    pct_tasks = float(
        (major_df["pct_tasks_affected"] * major_df["workers_affected"]).sum()
        / major_df["workers_affected"].sum()
    )

    pct_workers = workers_aff / total_workers * 100.0 if total_workers else 0.0
    pct_wages   = wages_aff   / total_wages   * 100.0 if total_wages   else 0.0

    # ── Layout: three equal columns, one metric each ──────────────────────────
    METRIC_FS  = 72   # giant number
    LABEL_FS   = 20   # description below number
    SUBVAL_FS  = 22   # secondary value (% of total)

    # x positions for the three columns (paper coords 0–1)
    xs = [1/6, 3/6, 5/6]
    labels = ["of tasks in at-risk\noccupations involve AI", "workers in jobs with\nAI-exposed tasks", "wages in jobs with\nAI-exposed tasks"]
    big_vals = [
        f"{pct_tasks:.0f}%",
        format_workers(workers_aff),
        format_wages(wages_aff),
    ]
    sub_vals = [
        "",
        f"{pct_workers:.0f}% of total Utah employment",
        f"{pct_wages:.0f}% of total Utah wage generation",
    ]

    fig = go.Figure()

    # Invisible scatter to force a plot area (needed for paper-coord annotations)
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="markers", marker=dict(opacity=0), showlegend=False, hoverinfo="skip"))

    for i, (x, big, sub, lbl) in enumerate(zip(xs, big_vals, sub_vals, labels)):
        # Big number
        fig.add_annotation(
            x=x, y=0.72, xref="paper", yref="paper",
            text=f"<b>{big}</b>",
            showarrow=False,
            font=dict(size=METRIC_FS, color=COLORS["primary"], family=FONT_FAMILY),
            xanchor="center", yanchor="middle",
        )
        # Description label below number
        fig.add_annotation(
            x=x, y=0.42, xref="paper", yref="paper",
            text=lbl,
            showarrow=False,
            font=dict(size=LABEL_FS, color=COLORS["text"], family=FONT_FAMILY),
            xanchor="center", yanchor="top",
            align="center",
        )
        # Secondary % of total (workers and wages only)
        if sub:
            fig.add_annotation(
                x=x, y=0.12, xref="paper", yref="paper",
                text=sub,
                showarrow=False,
                font=dict(size=SUBVAL_FS, color=COLORS["neutral"], family=FONT_FAMILY),
                xanchor="center", yanchor="top",
                align="center",
            )

        # Vertical divider between columns (skip after last)
        if i < 2:
            fig.add_shape(
                type="line",
                x0=xs[i] + 1/6 * 0.5, x1=xs[i] + 1/6 * 0.5,
                y0=0.08, y1=0.95,
                xref="paper", yref="paper",
                line=dict(color=COLORS["grid"], width=1.5),
            )

    _apply_base_style(fig, "AI Exposure in Utah — At a Glance")

    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="white",
        margin=dict(l=40, r=40, t=110, b=40),
    )

    return fig


# ── Chart 01: Sector scope ─────────────────────────────────────────────────────

def _chart_01_sector_scope(major_df: pd.DataFrame) -> go.Figure:
    """Top 7 sectors by workers with AI-exposed tasks."""
    df = major_df.sort_values("workers_affected", ascending=False).head(TOP_N).copy()
    ins = [f"{format_workers(r['workers_affected'])} workers" for _, r in df.iterrows()]
    out = [
        f"{r['pct_tasks_affected']:.0f}% tasks  ·  {format_wages(r['wages_affected'])} wages"
        for _, r in df.iterrows()
    ]
    return _annotated_bar(
        df, "category", "workers_affected",
        ins, out,
        "Top Sectors by Workers Affected Based on AI-Exposed Tasks",
        xaxis_tickformat="~s",
        xaxis_title="Workers Affected",
        x_range_pad=1.8,
    )


# ── Chart 02: GWA scope ────────────────────────────────────────────────────────

def _chart_02_gwa_scope(gwa_df: pd.DataFrame) -> go.Figure:
    """Top 7 work activity types by % tasks affected."""
    df = gwa_df.sort_values("pct_tasks_affected", ascending=False).head(TOP_N).copy()
    ins = [f"{r['pct_tasks_affected']:.0f}% tasks" for _, r in df.iterrows()]
    out = [
        f"{format_workers(r['workers_affected'])} workers  ·  {format_wages(r['wages_affected'])} wages"
        for _, r in df.iterrows()
    ]
    return _annotated_bar(
        df, "category", "pct_tasks_affected",
        ins, out,
        "Top Work Activities by Tasks Affected Based on AI-Exposed Tasks",
        xaxis_tickformat=".0f",
        xaxis_ticksuffix="%",
        xaxis_title="% of Tasks Affected",
        x_range_pad=1.7,
    )


# ── Chart 03: Sector trend ─────────────────────────────────────────────────────

def _chart_03_sector_trend(
    first_df: pd.DataFrame, last_df: pd.DataFrame
) -> go.Figure:
    """Top 7 sectors by growth in workers affected (Δ first → last date)."""
    merged = last_df[["category", "workers_affected", "pct_tasks_affected", "wages_affected"]].merge(
        first_df[["category", "workers_affected", "pct_tasks_affected", "wages_affected"]],
        on="category", suffixes=("_last", "_first"),
    )
    merged["delta_workers"] = merged["workers_affected_last"] - merged["workers_affected_first"]
    merged["delta_pct"] = merged["pct_tasks_affected_last"] - merged["pct_tasks_affected_first"]
    merged["delta_wages"] = merged["wages_affected_last"] - merged["wages_affected_first"]

    df = merged[merged["delta_workers"] > 0].sort_values(
        "delta_workers", ascending=False
    ).head(TOP_N).copy()

    first_date = _fmt_date(TREND_FIRST.split()[-1])
    last_date = _fmt_date(TREND_LAST.split()[-1])

    ins = [f"+{format_workers(r['delta_workers'])} workers" for _, r in df.iterrows()]
    out = [
        f"{r['delta_pct']:+.1f}% tasks  ·  {_sign_wages(r['delta_wages'])} wages"
        for _, r in df.iterrows()
    ]
    return _annotated_bar(
        df, "category", "delta_workers",
        ins, out,
        f"Top Sectors by Growth in Workers Affected ({first_date} → {last_date})",
        xaxis_tickformat="~s",
        xaxis_title="Change in Workers Affected",
        x_range_pad=1.8,
    )


# ── Chart 04: GWA trend ────────────────────────────────────────────────────────

def _chart_04_gwa_trend(
    first_df: pd.DataFrame, last_df: pd.DataFrame
) -> go.Figure:
    """Top 7 work activity types by growth in % tasks affected (Δ first → last)."""
    merged = last_df[["category", "pct_tasks_affected", "workers_affected", "wages_affected"]].merge(
        first_df[["category", "pct_tasks_affected", "workers_affected", "wages_affected"]],
        on="category", suffixes=("_last", "_first"),
    )
    merged["delta_pct"] = merged["pct_tasks_affected_last"] - merged["pct_tasks_affected_first"]
    merged["delta_workers"] = merged["workers_affected_last"] - merged["workers_affected_first"]
    merged["delta_wages"] = merged["wages_affected_last"] - merged["wages_affected_first"]

    df = merged[merged["delta_pct"] > 0].sort_values(
        "delta_pct", ascending=False
    ).head(TOP_N).copy()

    first_date = _fmt_date(TREND_FIRST.split()[-1])
    last_date = _fmt_date(TREND_LAST.split()[-1])

    ins = [f"{r['delta_pct']:+.1f}% tasks" for _, r in df.iterrows()]
    out = [
        f"{_sign_workers(r['delta_workers'])} workers  ·  {_sign_wages(r['delta_wages'])} wages"
        for _, r in df.iterrows()
    ]
    return _annotated_bar(
        df, "category", "delta_pct",
        ins, out,
        f"Top Work Activities by Growth in Tasks Affected ({first_date} → {last_date})",
        xaxis_tickformat=".1f",
        xaxis_ticksuffix="%",
        xaxis_title="Change in % Tasks Affected",
        x_range_pad=1.7,
    )


# ── Chart 05: Sector adoption gap ─────────────────────────────────────────────

def _chart_05_sector_gap(
    confirmed_df: pd.DataFrame, ceiling_df: pd.DataFrame
) -> go.Figure:
    """Top 7 sectors by confirmed→ceiling gap, sorted by % tasks gap."""
    merged = ceiling_df[["category", "workers_affected", "pct_tasks_affected", "wages_affected"]].merge(
        confirmed_df[["category", "workers_affected", "pct_tasks_affected", "wages_affected"]],
        on="category", suffixes=("_ceil", "_conf"),
    )
    merged["gap_workers"] = merged["workers_affected_ceil"] - merged["workers_affected_conf"]
    merged["gap_pct"] = merged["pct_tasks_affected_ceil"] - merged["pct_tasks_affected_conf"]
    merged["gap_wages"] = merged["wages_affected_ceil"] - merged["wages_affected_conf"]

    # Sort by % tasks gap (untapped coverage), not raw worker count
    df = merged[merged["gap_pct"] > 0].sort_values(
        "gap_pct", ascending=False
    ).head(TOP_N).copy()

    ins = [f"+{r['gap_pct']:.0f}% tasks" for _, r in df.iterrows()]
    out = [
        f"+{format_workers(r['gap_workers'])} workers  ·  {_sign_wages(r['gap_wages'])} wages"
        for _, r in df.iterrows()
    ]
    return _annotated_bar(
        df, "category", "gap_pct",
        ins, out,
        "Top Sectors by Untapped AI Capability",
        subtitle="Potential not captured by usage data — capabilities present in custom agentic tools (usage of these unknown)",
        xaxis_tickformat=".1f",
        xaxis_ticksuffix="%",
        xaxis_title="Untapped Task Coverage (%)",
        x_range_pad=1.9,
    )


# ── Chart 06: GWA adoption gap ─────────────────────────────────────────────────

def _chart_06_gwa_gap(
    confirmed_df: pd.DataFrame, ceiling_df: pd.DataFrame
) -> go.Figure:
    """Top 7 GWAs by confirmed→ceiling gap in % tasks (Utah)."""
    merged = ceiling_df[["category", "pct_tasks_affected", "workers_affected", "wages_affected"]].merge(
        confirmed_df[["category", "pct_tasks_affected", "workers_affected", "wages_affected"]],
        on="category", suffixes=("_ceil", "_conf"),
    )
    merged["gap_pct"] = merged["pct_tasks_affected_ceil"] - merged["pct_tasks_affected_conf"]
    merged["gap_workers"] = merged["workers_affected_ceil"] - merged["workers_affected_conf"]
    merged["gap_wages"] = merged["wages_affected_ceil"] - merged["wages_affected_conf"]

    df = merged[merged["gap_pct"] > 0].sort_values(
        "gap_pct", ascending=False
    ).head(TOP_N).copy()

    ins = [f"+{r['gap_pct']:.0f}% tasks" for _, r in df.iterrows()]
    out = [
        f"+{format_workers(r['gap_workers'])} workers  ·  {_sign_wages(r['gap_wages'])} wages"
        for _, r in df.iterrows()
    ]
    return _annotated_bar(
        df, "category", "gap_pct",
        ins, out,
        "Top Work Activities by Untapped AI Capability",
        subtitle="Potential not captured by usage data — capabilities present in custom agentic tools (usage of these unknown)",
        xaxis_tickformat=".1f",
        xaxis_ticksuffix="%",
        xaxis_title="Gap in % Tasks Affected",
        x_range_pad=1.8,
    )


# ── Chart 07: Conversational vs Agentic overlay ────────────────────────────────

def _chart_07_human_vs_agentic(
    conv_df: pd.DataFrame, agentic_df: pd.DataFrame
) -> go.Figure:
    """Overlaid bars: conversational (light) vs agentic (dark) workers by sector.

    Sorted by conversational workers descending. Tells the story of where AI
    is active conversationally vs where it is deployed as an autonomous agent.
    """
    merged = conv_df[["category", "workers_affected"]].merge(
        agentic_df[["category", "workers_affected"]],
        on="category", suffixes=("_conv", "_agt"),
    )
    df = merged.sort_values("workers_affected_conv", ascending=False).head(TOP_N).copy()

    max_val = float(df["workers_affected_conv"].max())

    fig = go.Figure()

    # Conversational bar (background) — lighter color, text outside
    fig.add_trace(go.Bar(
        x=df["workers_affected_conv"],
        y=df["category"],
        orientation="h",
        name="Chat AI (Browser)",
        marker=dict(color="#a8c4d8", line=dict(width=0)),
        text=[f"{format_workers(v)} workers" for v in df["workers_affected_conv"]],
        textposition="outside",
        textfont=dict(
            size=OUTSIDE_FS, color=COLORS["neutral"], family=FONT_FAMILY
        ),
        cliponaxis=False,
    ))

    # Agentic bar (foreground) — full color, white text inside
    fig.add_trace(go.Bar(
        x=df["workers_affected_agt"],
        y=df["category"],
        orientation="h",
        name="Agentic AI (API)",
        marker=dict(color=BAR_COLOR, line=dict(width=0)),
        text=[f"{format_workers(v)} workers" for v in df["workers_affected_agt"]],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=INSIDE_FS, color="white", family=FONT_FAMILY),
        cliponaxis=False,
    ))

    fig.update_layout(barmode="overlay")

    fig.update_yaxes(
        autorange="reversed",
        showgrid=False,
        showline=False,
        tickfont=dict(size=YAXIS_FS, color=COLORS["text"], family=FONT_FAMILY),
    )

    _apply_base_style(fig, "Conversational vs. Agentic AI Reach by Sector")

    # Override to show legend for this chart
    fig.update_layout(
        showlegend=True,
        legend=dict(
            visible=True,
            orientation="h",
            yanchor="bottom",
            y=-0.17,
            xanchor="center",
            x=0.5,
            font=dict(size=LEGEND_FS, color=COLORS["neutral"], family=FONT_FAMILY),
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor=COLORS["grid"],
            showticklabels=True,
            tickformat="~s",
            showline=False,
            zeroline=False,
            range=[0, max_val * 1.55],
            tickfont=dict(size=TICK_FS, color=COLORS["neutral"], family=FONT_FAMILY),
            title=dict(
                text="Workers Reached",
                font=dict(size=TICK_FS, color=COLORS["neutral"], family=FONT_FAMILY),
            ),
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            tickfont=dict(size=YAXIS_FS, color=COLORS["text"], family=FONT_FAMILY),
        ),
        bargap=0.25,
    )

    return fig


# ── Charts 08–11: SKA elements ─────────────────────────────────────────────────

def _chart_ska(
    elements_df: pd.DataFrame,
    direction: str,
    domain: str,
) -> go.Figure:
    """SKA element chart comparing AI vs average job requirement.

    direction="human": lowest ai_pct_mean (humans lead — AI below avg job need)
    direction="ai": highest ai_pct_mean (AI leads — AI above avg job need)

    The x-axis represents AI capability as % of the average occupation's
    requirement for this skill/knowledge element (importance >= 3 filter).
    100% = AI matches the average job's need in this area.
    """
    domain_label = "Skills" if domain == "skills" else "Knowledge"

    if direction == "human":
        df = elements_df.sort_values("ai_pct_mean", ascending=True).head(TOP_N).copy()
        title = f"{domain_label} Where the Average Workforce Need Still Outperforms AI"
        color = COLORS["secondary"]
    else:
        df = elements_df.sort_values("ai_pct_mean", ascending=False).head(TOP_N).copy()
        title = f"{domain_label} Where AI Has Surpassed the Average Workforce Need"
        color = COLORS["accent"]

    max_val = float(df["ai_pct_mean"].max())
    x_max = max(max_val * 1.3, 135.0)  # ensure parity line is always visible

    ins = [f"{v:.0f}%" for v in df["ai_pct_mean"]]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["ai_pct_mean"],
        y=df["element_name"],
        orientation="h",
        marker=dict(color=color, line=dict(width=0)),
        text=ins,
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=INSIDE_FS, color="white", family=FONT_FAMILY),
        cliponaxis=False,
    ))

    fig.update_yaxes(
        autorange="reversed",
        showgrid=False,
        showline=False,
        tickfont=dict(size=YAXIS_FS, color=COLORS["text"], family=FONT_FAMILY),
    )

    # Parity reference line — no inline annotation (avoids overlap with bars)
    fig.add_vline(
        x=100,
        line_dash="dash",
        line_color=COLORS["muted"],
        line_width=2,
    )
    # Annotation placed above the chart area via paper y-coords — never overlaps bars
    fig.add_annotation(
        x=100,
        y=1.04,
        xref="x",
        yref="paper",
        text="100% = avg job need in this skill",
        showarrow=False,
        font=dict(size=17, color=COLORS["muted"], family=FONT_FAMILY),
        xanchor="left",
        yanchor="bottom",
    )

    _apply_base_style(fig, title)

    # Extra top margin so above-chart annotation is not clipped
    fig.update_layout(margin=dict(l=20, r=280, t=110, b=80))

    fig.update_layout(
        xaxis=dict(
            showgrid=True,
            gridcolor=COLORS["grid"],
            showticklabels=True,
            tickformat=".0f",
            ticksuffix="%",
            showline=False,
            zeroline=False,
            range=[0, x_max],
            tickfont=dict(size=TICK_FS, color=COLORS["neutral"], family=FONT_FAMILY),
            title=dict(
                text="AI Capability as % of Average Job Requirement",
                font=dict(size=TICK_FS, color=COLORS["neutral"], family=FONT_FAMILY),
            ),
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            tickfont=dict(size=YAXIS_FS, color=COLORS["text"], family=FONT_FAMILY),
        ),
        bargap=0.25,
    )

    return fig


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("workforce_meeting_v2: loading data...")

    print("  Utah major (confirmed)...")
    major_confirmed = _get_utah_major(PRIMARY_DS)

    print("  Utah major (ceiling)...")
    major_ceiling = _get_utah_major(CEILING_DS)

    print(f"  Utah major (trend first: {TREND_FIRST})...")
    major_first = _get_utah_major(TREND_FIRST)

    print("  Utah major (conversational)...")
    major_conv = _get_utah_major(CONV_DS)

    print("  Utah major (agentic)...")
    major_agentic = _get_utah_major(AGENTIC_DS)

    print("  Utah GWA (confirmed)...")
    gwa_confirmed = _get_utah_gwa(PRIMARY_DS)

    print("  Utah GWA (ceiling)...")
    gwa_ceiling = _get_utah_gwa(CEILING_DS)

    print(f"  Utah GWA (trend first: {TREND_FIRST})...")
    gwa_first = _get_utah_gwa(TREND_FIRST)

    print("  Utah totals (employment + wages)...")
    utah_total_workers, utah_total_wages = _get_utah_totals()

    print("  SKA elements...")
    ska_elements = _get_ska_elements()

    # ── Generate charts ────────────────────────────────────────────────────────
    charts: dict[str, go.Figure] = {}
    print("\n  Generating charts...")

    charts["00_headline"] = _chart_00_headline(
        major_confirmed, utah_total_workers, utah_total_wages
    )
    print("    00_headline")

    charts["01_sector_scope"] = _chart_01_sector_scope(major_confirmed)
    print("    01_sector_scope")

    charts["02_gwa_scope"] = _chart_02_gwa_scope(gwa_confirmed)
    print("    02_gwa_scope")

    charts["03_sector_trend"] = _chart_03_sector_trend(major_first, major_confirmed)
    print("    03_sector_trend")

    charts["04_gwa_trend"] = _chart_04_gwa_trend(gwa_first, gwa_confirmed)
    print("    04_gwa_trend")

    charts["05_sector_adoption_gap"] = _chart_05_sector_gap(
        major_confirmed, major_ceiling
    )
    print("    05_sector_adoption_gap")

    charts["06_gwa_adoption_gap"] = _chart_06_gwa_gap(gwa_confirmed, gwa_ceiling)
    print("    06_gwa_adoption_gap")

    charts["07_human_vs_agentic"] = _chart_07_human_vs_agentic(
        major_conv, major_agentic
    )
    print("    07_human_vs_agentic")

    for domain in ("skills", "knowledge"):
        elem_df = ska_elements.get(domain)
        if elem_df is not None and not elem_df.empty:
            idx_h = 8 if domain == "skills" else 9
            idx_a = 10 if domain == "skills" else 11
            charts[f"{idx_h:02d}_ska_human_{domain}"] = _chart_ska(
                elem_df, "human", domain
            )
            print(f"    {idx_h:02d}_ska_human_{domain}")
            charts[f"{idx_a:02d}_ska_ai_{domain}"] = _chart_ska(
                elem_df, "ai", domain
            )
            print(f"    {idx_a:02d}_ska_ai_{domain}")

    # ── Save figures ───────────────────────────────────────────────────────────
    print("\n  Saving figures...")
    for name, fig in sorted(charts.items()):
        png_name = f"{name}.png"
        save_figure(fig, results / "figures" / png_name)
        shutil.copy(results / "figures" / png_name, figs_dir / png_name)
        print(f"    {png_name}")

    # ── Generate PDF from report ───────────────────────────────────────────────
    report_path = HERE / "workforce_meeting_v2_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "workforce_meeting_v2_report.pdf")

    print(f"\nworkforce_meeting_v2: done. {len(charts)} charts generated.")


if __name__ == "__main__":
    main()
