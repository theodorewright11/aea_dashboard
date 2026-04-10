"""
run.py — Workforce Meeting Presentation Charts

14 presentation-quality charts for a Utah workforce meeting with business and
education leaders. All charts use Utah employment figures where applicable.

Config: all_confirmed (AEI Both + Micro 2026-02-12) | freq | auto-aug ON | Utah
Trend: first → last date of all_confirmed series (no Sep/Dec 2024)
Adoption gap: all_confirmed vs all_ceiling (both Utah)
AI modes gap: human_conversation vs agentic_confirmed (both Utah)
SKA: national scope (occupation-level metric, geo-invariant)
Auto-aug: national scope (task-level metric, geo-invariant)

Charts (numbered by suggested slide order):
  01_utah_headline         — Utah workers with AI-exposed tasks (stacked bar)
  02_sector_scope          — Top 7 sectors by workers affected (+ %tasks, wages)
  03_gwa_scope             — Top 7 GWAs by % tasks affected (+ workers, wages)
  04_sector_trend          — Top 7 sector growers: Δworkers Mar 2025 → Feb 2026
  05_gwa_trend             — Top 7 GWA growers: Δ% tasks Mar 2025 → Feb 2026
  06_sector_adoption_gap   — Top 7 sectors: confirmed→ceiling worker gap
  07_gwa_adoption_gap      — Top 7 GWAs: confirmed→ceiling %tasks gap
  08_ai_modes_gap          — Top 7 sectors: conversational→agentic worker drop
  09_autoaug_by_sector     — Top 7 sectors by avg auto-aug (tasks with AI score)
  10_pivot_cost            — Reskilling cost by job zone (all 5 zones)
  11_ska_human_skills      — Top 7 skills where humans still lead AI
  12_ska_human_knowledge   — Top 7 knowledge domains where humans still lead AI
  13_ska_ai_skills         — Top 7 skills where AI has overtaken humans
  14_ska_ai_knowledge      — Top 7 knowledge domains where AI has overtaken humans

Run from project root:
    venv/Scripts/python -m analysis.questions.workforce_meeting.run
"""
from __future__ import annotations

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
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    format_workers,
    format_wages,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent

# ── Constants ──────────────────────────────────────────────────────────────────
UTAH_TOTAL_EMP: int = 1_709_790
GEO: str = "ut"
TOP_N: int = 7

PRIMARY_DS: str = ANALYSIS_CONFIGS["all_confirmed"]
CEILING_DS: str = ANALYSIS_CONFIGS["all_ceiling"]
CONV_DS: str = ANALYSIS_CONFIGS["human_conversation"]
AGENTIC_DS: str = ANALYSIS_CONFIGS["agentic_confirmed"]

# Trend window (dynamic from config — no Sep/Dec 2024 in this series)
TREND_FIRST: str = ANALYSIS_CONFIG_SERIES["all_confirmed"][0]
TREND_LAST: str = ANALYSIS_CONFIG_SERIES["all_confirmed"][-1]

# Presentation styling
CHART_W: int = 1400
CHART_H: int = 787
SUBTITLE_BASE: str = "All Confirmed | UTAH | Freq | Auto-aug ON"
BAR_COLOR: str = COLORS["primary"]


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


def _get_autoaug_by_major() -> pd.DataFrame:
    """Avg auto-aug score (tasks with AI score only) per major sector.

    Task-level metric — geo-invariant. Uses all_confirmed dataset.
    """
    from backend.config import DATASETS
    from backend.compute import load_eco_raw

    meta = DATASETS.get(PRIMARY_DS)
    assert meta is not None, f"Unknown dataset: {PRIMARY_DS}"

    eco_raw = load_eco_raw()
    assert eco_raw is not None, "Eco baseline not found"

    eco_tasks = (
        eco_raw[["major_occ_category", "task_normalized"]]
        .drop_duplicates()
        .copy()
    )

    df = pd.read_csv(
        meta["file"],
        usecols=["task_normalized", "major_occ_category", "auto_aug_mean"],
    )
    df["auto_aug_mean"] = pd.to_numeric(df["auto_aug_mean"], errors="coerce")

    ai_tasks = (
        df.groupby(["major_occ_category", "task_normalized"])
        .agg(auto_aug_mean=("auto_aug_mean", "mean"))
        .reset_index()
    )

    merged = eco_tasks.merge(
        ai_tasks, on=["major_occ_category", "task_normalized"], how="left"
    )

    rows: list[dict] = []
    for major, grp in merged.groupby("major_occ_category"):
        with_vals = grp[grp["auto_aug_mean"].notna()]
        avg = float(with_vals["auto_aug_mean"].mean()) if len(with_vals) > 0 else 0.0
        rows.append({"category": major, "avg_autoaug": avg})
    return pd.DataFrame(rows)


def _get_ska_elements() -> dict[str, pd.DataFrame]:
    """Compute element-level AI coverage % from all_confirmed (national).

    Returns dict["skills"|"knowledge"] → DataFrame[element_name, ai_pct_mean].
    ai_pct_mean = mean of (ai_score / occ_score × 100) across occupations.
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


def _get_pivot_costs() -> pd.DataFrame:
    """Load pivot cost by zone from existing results."""
    csv_path = (
        HERE.parent / "job_exposure" / "pivot_distance"
        / "results" / "pivot_cost_by_zone.csv"
    )
    if not csv_path.exists():
        print(f"  WARNING: pivot cost CSV not found at {csv_path}")
        return pd.DataFrame()
    return pd.read_csv(csv_path)


# ── Chart helper ───────────────────────────────────────────────────────────────

def _annotated_bar(
    df: pd.DataFrame,
    category_col: str,
    value_col: str,
    text_col: str,
    title: str,
    *,
    subtitle: str = SUBTITLE_BASE,
    color: str = BAR_COLOR,
    top_n: int = TOP_N,
    x_range_pad: float = 1.4,
) -> go.Figure:
    """Horizontal bar chart with custom compound text labels.

    Same visual style as make_horizontal_bar. DataFrame must be pre-sorted
    ascending=False (largest first).
    """
    plot_df = df.head(top_n)

    fig = go.Figure(go.Bar(
        x=plot_df[value_col],
        y=plot_df[category_col],
        orientation="h",
        marker=dict(color=color, line=dict(width=0)),
        text=plot_df[text_col],
        textposition="outside",
        textfont=dict(size=12, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))

    fig.update_yaxes(autorange="reversed")

    style_figure(
        fig, title,
        subtitle=subtitle,
        show_legend=False,
        height=CHART_H, width=CHART_W,
    )

    max_val = plot_df[value_col].max() if len(plot_df) > 0 else 1
    fig.update_layout(
        margin=dict(l=20, r=160, t=90, b=80),
        xaxis=dict(
            showgrid=False, showticklabels=False, showline=False, zeroline=False,
            range=[0, max_val * x_range_pad] if max_val > 0 else None,
        ),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=12)),
        bargap=0.25,
    )

    return fig


def _fmt_delta(val: float, fmt_fn) -> str:  # type: ignore[type-arg]
    """Format a delta value with explicit +/- sign."""
    sign = "+" if val >= 0 else ""
    return f"{sign}{fmt_fn(val)}"


def _fmt_delta_pct(val: float) -> str:
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.1f} pp"


# ── Chart 01: Headline ────────────────────────────────────────────────────────

def _chart_01_headline(major_df: pd.DataFrame) -> go.Figure:
    """Stacked bar: Utah workers with AI-exposed tasks vs rest."""
    workers = float(major_df["workers_affected"].sum())
    pct = workers / UTAH_TOTAL_EMP * 100
    rest = UTAH_TOTAL_EMP - workers

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=[""],
        x=[workers],
        orientation="h",
        name=f"AI-exposed tasks: {format_workers(workers)}",
        marker=dict(color=BAR_COLOR, line=dict(width=0)),
    ))
    fig.add_trace(go.Bar(
        y=[""],
        x=[rest],
        orientation="h",
        name=f"No AI task overlap: {format_workers(rest)}",
        marker=dict(color="#d5e3ef", line=dict(width=0)),
    ))

    fig.update_layout(
        barmode="stack",
        title=dict(
            text=(
                f"AI Task Exposure Across the Utah Workforce"
                f"<br><span style='font-size:13px;color:{COLORS['neutral']}'>"
                f"{SUBTITLE_BASE}</span>"
            ),
            font=dict(size=20, family=FONT_FAMILY, color=COLORS["text"]),
            x=0.01, xanchor="left",
        ),
        font=dict(family=FONT_FAMILY, size=14, color=COLORS["text"]),
        plot_bgcolor=COLORS["bg"],
        paper_bgcolor=COLORS["bg"],
        width=CHART_W, height=400,
        margin=dict(l=40, r=40, t=100, b=100),
        xaxis=dict(
            showticklabels=False, showgrid=False, showline=False, zeroline=False,
            range=[0, UTAH_TOTAL_EMP * 1.01],
        ),
        yaxis=dict(showticklabels=False, showgrid=False, showline=False),
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.15,
            xanchor="center", x=0.5,
            font=dict(size=13, family=FONT_FAMILY, color=COLORS["neutral"]),
        ),
    )

    # Big percentage inside the blue bar (use paper coords for reliable placement)
    bar_mid_paper = (workers / UTAH_TOTAL_EMP) * 0.48  # approx center of blue bar
    fig.add_annotation(
        text=f"<b>{pct:.0f}%</b>",
        x=bar_mid_paper, y=0.45,
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=48, color="white", family=FONT_FAMILY),
    )

    fig.add_annotation(
        text="Source: AEA Dashboard — Utah OAIP",
        xref="paper", yref="paper",
        x=1.0, y=-0.22,
        showarrow=False,
        font=dict(size=10, color=COLORS["muted"], family=FONT_FAMILY),
        xanchor="right",
    )

    return fig


# ── Chart 02: Sector scope ───────────────────────────────────────────────────

def _chart_02_sector_scope(
    major_df: pd.DataFrame,
    total_workers: float,
    total_wages: float,
    total_utah_wages: Optional[float],
) -> go.Figure:
    """Top 7 sectors by workers affected (Utah), with %tasks + wages."""
    df = major_df.sort_values("workers_affected", ascending=False).head(TOP_N).copy()

    df["label"] = df.apply(
        lambda r: (
            f"{format_workers(r['workers_affected'])} workers  "
            f"({r['pct_tasks_affected']:.0f}% tasks, "
            f"{format_wages(r['wages_affected'])})"
        ),
        axis=1,
    )

    pct_emp = total_workers / UTAH_TOTAL_EMP * 100
    total_line = (
        f"Total Utah AI exposure: {format_workers(total_workers)} workers "
        f"({pct_emp:.0f}% of workforce), {format_wages(total_wages)} wages"
    )
    if total_utah_wages and total_utah_wages > 0:
        wages_pct = total_wages / total_utah_wages * 100
        total_line += f" ({wages_pct:.0f}% of payroll)"

    subtitle = f"{SUBTITLE_BASE}<br><b>{total_line}</b>"

    return _annotated_bar(
        df, "category", "workers_affected", "label",
        "Top Utah Sectors by Workers Affected",
        subtitle=subtitle,
    )


# ── Chart 03: GWA scope ──────────────────────────────────────────────────────

def _chart_03_gwa_scope(gwa_df: pd.DataFrame) -> go.Figure:
    """Top 7 GWAs by % tasks affected (Utah), with workers + wages."""
    df = gwa_df.sort_values("pct_tasks_affected", ascending=False).head(TOP_N).copy()

    df["label"] = df.apply(
        lambda r: (
            f"{r['pct_tasks_affected']:.1f}%  "
            f"({format_workers(r['workers_affected'])}, "
            f"{format_wages(r['wages_affected'])})"
        ),
        axis=1,
    )

    return _annotated_bar(
        df, "category", "pct_tasks_affected", "label",
        "Top Utah Work Activities by % Tasks Affected",
        subtitle=SUBTITLE_BASE,
    )


# ── Chart 04: Sector trend ───────────────────────────────────────────────────

def _chart_04_sector_trend(
    first_df: pd.DataFrame, last_df: pd.DataFrame
) -> go.Figure:
    """Top 7 sector growers: delta workers from first to last date."""
    merged = last_df[["category", "workers_affected", "pct_tasks_affected", "wages_affected"]].merge(
        first_df[["category", "workers_affected", "pct_tasks_affected", "wages_affected"]],
        on="category", suffixes=("_last", "_first"),
    )
    merged["delta_workers"] = merged["workers_affected_last"] - merged["workers_affected_first"]
    merged["delta_pct"] = merged["pct_tasks_affected_last"] - merged["pct_tasks_affected_first"]
    merged["delta_wages"] = merged["wages_affected_last"] - merged["wages_affected_first"]

    positive = merged[merged["delta_workers"] > 0]
    df = positive.sort_values("delta_workers", ascending=False).head(TOP_N).copy()

    df["label"] = df.apply(
        lambda r: (
            f"{_fmt_delta(r['delta_workers'], format_workers)} workers  "
            f"({_fmt_delta_pct(r['delta_pct'])}, "
            f"{_fmt_delta(r['delta_wages'], format_wages)})"
        ),
        axis=1,
    )

    first_date = TREND_FIRST.split()[-1]
    last_date = TREND_LAST.split()[-1]

    return _annotated_bar(
        df, "category", "delta_workers", "label",
        "Fastest-Growing Utah Sectors — Workers Affected",
        subtitle=f"{SUBTITLE_BASE}  |  Δ from {first_date} to {last_date}",
    )


# ── Chart 05: GWA trend ──────────────────────────────────────────────────────

def _chart_05_gwa_trend(
    first_df: pd.DataFrame, last_df: pd.DataFrame
) -> go.Figure:
    """Top 7 GWA growers: delta % tasks from first to last date."""
    merged = last_df[["category", "pct_tasks_affected", "workers_affected", "wages_affected"]].merge(
        first_df[["category", "pct_tasks_affected", "workers_affected", "wages_affected"]],
        on="category", suffixes=("_last", "_first"),
    )
    merged["delta_pct"] = merged["pct_tasks_affected_last"] - merged["pct_tasks_affected_first"]
    merged["delta_workers"] = merged["workers_affected_last"] - merged["workers_affected_first"]
    merged["delta_wages"] = merged["wages_affected_last"] - merged["wages_affected_first"]

    positive = merged[merged["delta_pct"] > 0]
    df = positive.sort_values("delta_pct", ascending=False).head(TOP_N).copy()

    df["label"] = df.apply(
        lambda r: (
            f"{_fmt_delta_pct(r['delta_pct'])}  "
            f"({_fmt_delta(r['delta_workers'], format_workers)}, "
            f"{_fmt_delta(r['delta_wages'], format_wages)})"
        ),
        axis=1,
    )

    first_date = TREND_FIRST.split()[-1]
    last_date = TREND_LAST.split()[-1]

    return _annotated_bar(
        df, "category", "delta_pct", "label",
        "Fastest-Growing Utah Work Activities — % Tasks Affected",
        subtitle=f"{SUBTITLE_BASE}  |  Δ from {first_date} to {last_date}",
    )


# ── Chart 06: Sector adoption gap ────────────────────────────────────────────

def _chart_06_sector_gap(
    confirmed_df: pd.DataFrame, ceiling_df: pd.DataFrame
) -> go.Figure:
    """Top 7 sectors by confirmed→ceiling gap in workers."""
    merged = ceiling_df[["category", "workers_affected", "pct_tasks_affected"]].merge(
        confirmed_df[["category", "workers_affected", "pct_tasks_affected"]],
        on="category", suffixes=("_ceil", "_conf"),
    )
    merged["gap_workers"] = merged["workers_affected_ceil"] - merged["workers_affected_conf"]
    merged["gap_pct"] = merged["pct_tasks_affected_ceil"] - merged["pct_tasks_affected_conf"]

    df = merged[merged["gap_workers"] > 0].sort_values(
        "gap_workers", ascending=False
    ).head(TOP_N).copy()

    df["label"] = df.apply(
        lambda r: (
            f"+{format_workers(r['gap_workers'])} workers  "
            f"(+{r['gap_pct']:.1f} pp tasks)"
        ),
        axis=1,
    )

    return _annotated_bar(
        df, "category", "gap_workers", "label",
        "Where AI Could Expand Next: Confirmed → Ceiling Gap",
        subtitle=f"{SUBTITLE_BASE}  |  Gap: All Confirmed vs All Sources (Ceiling)",
    )


# ── Chart 07: GWA adoption gap ───────────────────────────────────────────────

def _chart_07_gwa_gap(
    confirmed_df: pd.DataFrame, ceiling_df: pd.DataFrame
) -> go.Figure:
    """Top 7 GWAs by confirmed→ceiling gap in % tasks."""
    merged = ceiling_df[["category", "pct_tasks_affected", "workers_affected"]].merge(
        confirmed_df[["category", "pct_tasks_affected", "workers_affected"]],
        on="category", suffixes=("_ceil", "_conf"),
    )
    merged["gap_pct"] = merged["pct_tasks_affected_ceil"] - merged["pct_tasks_affected_conf"]
    merged["gap_workers"] = merged["workers_affected_ceil"] - merged["workers_affected_conf"]

    df = merged[merged["gap_pct"] > 0].sort_values(
        "gap_pct", ascending=False
    ).head(TOP_N).copy()

    df["label"] = df.apply(
        lambda r: (
            f"+{r['gap_pct']:.1f} pp  "
            f"(+{format_workers(r['gap_workers'])} workers)"
        ),
        axis=1,
    )

    return _annotated_bar(
        df, "category", "gap_pct", "label",
        "Where AI Could Expand Next: Confirmed → Ceiling Gap by Activity",
        subtitle=f"{SUBTITLE_BASE}  |  Gap: All Confirmed vs All Sources (Ceiling)",
    )


# ── Chart 08: AI modes gap ───────────────────────────────────────────────────

def _chart_08_modes_gap(
    conv_df: pd.DataFrame, agentic_df: pd.DataFrame
) -> go.Figure:
    """Top 7 sectors by drop from conversational to agentic (workers)."""
    merged = conv_df[["category", "workers_affected", "pct_tasks_affected"]].merge(
        agentic_df[["category", "workers_affected", "pct_tasks_affected"]],
        on="category", suffixes=("_conv", "_agt"),
    )
    merged["drop_workers"] = merged["workers_affected_conv"] - merged["workers_affected_agt"]
    merged["drop_pct"] = merged["pct_tasks_affected_conv"] - merged["pct_tasks_affected_agt"]

    df = merged[merged["drop_workers"] > 0].sort_values(
        "drop_workers", ascending=False
    ).head(TOP_N).copy()

    df["label"] = df.apply(
        lambda r: (
            f"−{format_workers(r['drop_workers'])} workers  "
            f"(−{r['drop_pct']:.1f} pp tasks)"
        ),
        axis=1,
    )

    return _annotated_bar(
        df, "category", "drop_workers", "label",
        "Agentic Deployment Gap: Conversational vs Agentic by Sector",
        subtitle="Human Conversation vs Agentic Confirmed | UTAH | Freq | Auto-aug ON",
    )


# ── Chart 09: Auto-aug by sector ─────────────────────────────────────────────

def _chart_09_autoaug(autoaug_df: pd.DataFrame) -> go.Figure:
    """Top 7 sectors by avg auto-aug score (tasks with AI score)."""
    df = autoaug_df.sort_values("avg_autoaug", ascending=False).head(TOP_N).copy()
    df["label"] = df["avg_autoaug"].apply(lambda v: f"{v:.2f} / 5.0")

    return _annotated_bar(
        df, "category", "avg_autoaug", "label",
        "AI Augmentation Potential by Sector",
        subtitle="Avg auto-aug score (tasks with AI score) | All Confirmed | National",
        x_range_pad=1.25,
    )


# ── Chart 10: Pivot cost ─────────────────────────────────────────────────────

def _chart_10_pivot_cost(pivot_df: pd.DataFrame) -> go.Figure:
    """Bar chart: reskilling cost by job zone."""
    zone_col = next(
        (c for c in pivot_df.columns if "zone" in c.lower()), pivot_df.columns[0]
    )
    cost_col = next(
        (c for c in pivot_df.columns if "cost" in c.lower()), pivot_df.columns[1]
    )

    df = pivot_df.sort_values(zone_col).copy()
    df["zone_label"] = df[zone_col].apply(lambda z: f"Zone {int(z)}")

    fig = go.Figure(go.Bar(
        x=df["zone_label"],
        y=df[cost_col],
        marker=dict(color=BAR_COLOR, line=dict(width=0)),
        text=df[cost_col].apply(lambda v: f"{v:.0f}"),
        textposition="outside",
        textfont=dict(size=14, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))

    max_cost = df[cost_col].max()
    style_figure(
        fig, "Reskilling Cost by Job Zone",
        subtitle=(
            "Skill + knowledge gap: high-risk → low-risk occupations  |  "
            "All Confirmed | National"
        ),
        y_title="Total Reskilling Cost (L1 Distance)",
        height=CHART_H, width=CHART_W,
        show_legend=False,
    )

    fig.update_layout(
        yaxis=dict(range=[0, max_cost * 1.2], showgrid=True, gridcolor=COLORS["grid"]),
        xaxis=dict(tickfont=dict(size=14)),
        bargap=0.35,
    )

    return fig


# ── Charts 11–14: SKA elements ───────────────────────────────────────────────

def _chart_ska(
    elements_df: pd.DataFrame,
    direction: str,
    domain: str,
) -> go.Figure:
    """SKA element chart: top 7 by AI coverage.

    direction="human": lowest ai_pct_mean (humans lead)
    direction="ai": highest ai_pct_mean (AI leads / exceeds)
    """
    if direction == "human":
        df = elements_df.sort_values("ai_pct_mean", ascending=True).head(TOP_N).copy()
        title = f"Durable {domain.title()}: Where Humans Still Lead AI"
        color = COLORS["secondary"]
    else:
        df = elements_df.sort_values("ai_pct_mean", ascending=False).head(TOP_N).copy()
        title = f"AI-Dominated {domain.title()}: Where AI Has Overtaken Humans"
        color = COLORS["accent"]

    df["label"] = df["ai_pct_mean"].apply(lambda v: f"{v:.0f}%")

    fig = go.Figure(go.Bar(
        x=df["ai_pct_mean"],
        y=df["element_name"],
        orientation="h",
        marker=dict(color=color, line=dict(width=0)),
        text=df["label"],
        textposition="outside",
        textfont=dict(size=12, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))

    fig.update_yaxes(autorange="reversed")

    # Reference line at 100% parity
    fig.add_vline(
        x=100, line_dash="dash", line_color=COLORS["muted"], line_width=1.5,
        annotation_text="100% = parity",
        annotation_position="top right",
        annotation_font=dict(size=10, color=COLORS["muted"]),
    )

    max_val = df["ai_pct_mean"].max()
    x_max = max(max_val * 1.3, 120)

    style_figure(
        fig, title,
        subtitle="AI capability as % of avg occupation requirement | All Confirmed | National",
        show_legend=False,
        height=CHART_H, width=CHART_W,
    )

    fig.update_layout(
        margin=dict(l=20, r=100, t=90, b=80),
        xaxis=dict(
            showgrid=False, showticklabels=False, showline=False, zeroline=False,
            range=[0, x_max],
        ),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=12)),
        bargap=0.25,
    )

    return fig


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("workforce_meeting: loading data...")

    # ── Data loading ─────────────────────────────────────────────────────────
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

    print("  Auto-aug by major...")
    autoaug_df = _get_autoaug_by_major()

    print("  Pivot cost data...")
    pivot_df = _get_pivot_costs()

    print("  SKA elements...")
    ska_elements = _get_ska_elements()

    # ── Aggregate totals ─────────────────────────────────────────────────────
    total_workers = float(major_confirmed["workers_affected"].sum())
    total_wages = float(major_confirmed["wages_affected"].sum())

    # Try to compute total Utah wages payroll from raw emp × wage
    total_utah_wages: Optional[float] = None
    if "emp" in major_confirmed.columns and "median_annual_wage" in major_confirmed.columns:
        total_utah_wages = float(
            (major_confirmed["emp"] * major_confirmed["median_annual_wage"]).sum()
        )
    elif "emp" in major_confirmed.columns:
        # Try 'wage' column name
        wage_col = next(
            (c for c in major_confirmed.columns if "wage" in c.lower() and "affected" not in c.lower()),
            None,
        )
        if wage_col:
            total_utah_wages = float(
                (major_confirmed["emp"] * major_confirmed[wage_col]).sum()
            )

    print(f"\n  Total UT workers affected: {format_workers(total_workers)} "
          f"({total_workers / UTAH_TOTAL_EMP * 100:.1f}% of workforce)")
    print(f"  Total UT wages affected:   {format_wages(total_wages)}")
    if total_utah_wages:
        print(f"  Total UT payroll:          {format_wages(total_utah_wages)}")

    # ── Generate charts ──────────────────────────────────────────────────────
    charts: dict[str, go.Figure] = {}
    print("\n  Generating charts...")

    charts["01_utah_headline"] = _chart_01_headline(major_confirmed)
    print("    01_utah_headline")

    charts["02_sector_scope"] = _chart_02_sector_scope(
        major_confirmed, total_workers, total_wages, total_utah_wages
    )
    print("    02_sector_scope")

    charts["03_gwa_scope"] = _chart_03_gwa_scope(gwa_confirmed)
    print("    03_gwa_scope")

    # Trend: major_confirmed IS the last date (same dataset)
    charts["04_sector_trend"] = _chart_04_sector_trend(major_first, major_confirmed)
    print("    04_sector_trend")

    charts["05_gwa_trend"] = _chart_05_gwa_trend(gwa_first, gwa_confirmed)
    print("    05_gwa_trend")

    charts["06_sector_adoption_gap"] = _chart_06_sector_gap(
        major_confirmed, major_ceiling
    )
    print("    06_sector_adoption_gap")

    charts["07_gwa_adoption_gap"] = _chart_07_gwa_gap(gwa_confirmed, gwa_ceiling)
    print("    07_gwa_adoption_gap")

    charts["08_ai_modes_gap"] = _chart_08_modes_gap(major_conv, major_agentic)
    print("    08_ai_modes_gap")

    charts["09_autoaug_by_sector"] = _chart_09_autoaug(autoaug_df)
    print("    09_autoaug_by_sector")

    if not pivot_df.empty:
        charts["10_pivot_cost"] = _chart_10_pivot_cost(pivot_df)
        print("    10_pivot_cost")
    else:
        print("    SKIPPED: 10_pivot_cost (no data)")

    for domain in ("skills", "knowledge"):
        elem_df = ska_elements.get(domain)
        if elem_df is not None and not elem_df.empty:
            idx_h = 11 if domain == "skills" else 12
            idx_a = 13 if domain == "skills" else 14
            charts[f"{idx_h:02d}_ska_human_{domain}"] = _chart_ska(
                elem_df, "human", domain
            )
            print(f"    {idx_h:02d}_ska_human_{domain}")
            charts[f"{idx_a:02d}_ska_ai_{domain}"] = _chart_ska(
                elem_df, "ai", domain
            )
            print(f"    {idx_a:02d}_ska_ai_{domain}")

    # ── Save all figures ─────────────────────────────────────────────────────
    print("\n  Saving figures...")
    for name, fig in sorted(charts.items()):
        png_name = f"{name}.png"
        save_figure(fig, results / "figures" / png_name)
        shutil.copy(results / "figures" / png_name, figs_dir / png_name)

    # ── Save summary CSV ─────────────────────────────────────────────────────
    summary_rows = []
    for name, fig in sorted(charts.items()):
        raw_title = fig.layout.title.text if fig.layout.title and fig.layout.title.text else name
        clean_title = raw_title.split("<br>")[0]
        summary_rows.append({"chart": name, "title": clean_title})
    save_csv(pd.DataFrame(summary_rows), results / "chart_index.csv")

    # ── Generate PDF ─────────────────────────────────────────────────────────
    report_path = HERE / "workforce_meeting_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "workforce_meeting_report.pdf")

    print(f"\nworkforce_meeting: done. {len(charts)} charts generated.")


if __name__ == "__main__":
    main()
