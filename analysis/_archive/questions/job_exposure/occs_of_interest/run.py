"""
run.py — Job Exposure: Occupations of Interest

How do all job exposure findings land for the 29 named occupations?

Applies all sub-analyses to the curated occupation list. Produces a focused,
presentation-ready summary covering:
  - Exposure pct across all five configs (primary: all_confirmed, ceiling comparison)
  - Risk scores and tier (weighted scoring from job_risk_scoring)
  - SKA gap breakdown (top 5 human-advantage + top 5 AI-advantage per occ)
  - Pct and workers_affected time trends per config
  - Whether each occ is flagged as "hidden at-risk" by audience_framing
  - Three-layer framing: confirmed → ceiling → actual adoption gap

Run from project root (run after job_risk_scoring, worker_resilience, audience_framing):
    venv/Scripts/python -m analysis.questions.job_exposure.occs_of_interest.run
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
    ANALYSIS_CONFIG_SERIES,
    OCCS_OF_INTEREST,
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.data.compute_ska import compute_ska, load_ska_data
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    _format_bar_label,
    format_workers,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
RISK_RESULTS = HERE.parent / "job_risk_scoring" / "results"
RESILIENCE_RESULTS = HERE.parent / "worker_resilience" / "results"
AUDIENCE_RESULTS = HERE.parent / "audience_framing" / "results"

PRIMARY_KEY = "all_confirmed"
CEILING_KEY = "all_ceiling"

GROUP_LABELS = {
    "high_profile": "High-Profile / High-Employment",
    "ai_interesting": "AI-Controversial / Interesting",
    "utah_relevant": "Utah-Relevant",
}

OCC_GROUPS: dict[str, str] = {
    "Registered Nurses": "high_profile",
    "Software Developers": "high_profile",
    "General and Operations Managers": "high_profile",
    "Cashiers": "high_profile",
    "Customer Service Representatives": "high_profile",
    "Retail Salespersons": "high_profile",
    "Heavy and Tractor-Trailer Truck Drivers": "high_profile",
    "Elementary School Teachers, Except Special Education": "high_profile",
    "Waiters and Waitresses": "high_profile",
    "Janitors and Cleaners, Except Maids and Housekeeping Cleaners": "high_profile",
    "Accountants and Auditors": "high_profile",
    "Secretaries and Administrative Assistants, Except Legal, Medical, and Executive": "high_profile",
    "Lawyers": "ai_interesting",
    "Physicians, All Other": "ai_interesting",
    "Financial Analysts": "ai_interesting",
    "Graphic Designers": "ai_interesting",
    "Technical Writers": "ai_interesting",
    "Web Developers": "ai_interesting",
    "Paralegals and Legal Assistants": "ai_interesting",
    "Data Scientists": "ai_interesting",
    "Human Resources Specialists": "ai_interesting",
    "Market Research Analysts and Marketing Specialists": "ai_interesting",
    "Editors": "ai_interesting",
    "Interpreters and Translators": "ai_interesting",
    "Computer Systems Analysts": "utah_relevant",
    "Medical and Health Services Managers": "utah_relevant",
    "Construction Laborers": "utah_relevant",
    "Sales Representatives, Wholesale and Manufacturing, Except Technical and Scientific Products": "utah_relevant",
    "Network and Computer Systems Administrators": "utah_relevant",
}

TIER_COLORS_RISK = {
    "high":     COLORS["negative"],
    "mod_high": COLORS["accent"],
    "mod_low":  COLORS["secondary"],
    "low":      COLORS["muted"],
}


def _find_occ(title: str, available: set[str]) -> str | None:
    title_lower = title.lower()
    for occ in available:
        if occ.lower() == title_lower:
            return occ
    for occ in available:
        if title_lower in occ.lower() or occ.lower() in title_lower:
            return occ
    return None


# ── Figures ───────────────────────────────────────────────────────────────────

def _exposure_ranked_bar(occ_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar: named occs ranked by primary pct, with ceiling shown as lighter overlay."""
    group_colors = {
        "high_profile": COLORS["primary"],
        "ai_interesting": COLORS["accent"],
        "utah_relevant": COLORS["secondary"],
    }
    df = occ_df.sort_values(f"pct_{PRIMARY_KEY}", ascending=True)

    # Primary config bars
    colors = [group_colors.get(g, COLORS["muted"]) for g in df["group"]]
    labels = [f"{v:.1f}%" for v in df[f"pct_{PRIMARY_KEY}"]]

    fig = go.Figure()

    # Ceiling bars (background, lighter)
    fig.add_trace(go.Bar(
        y=df["title_current"],
        x=df[f"pct_{CEILING_KEY}"],
        orientation="h",
        marker=dict(color="rgba(200,200,200,0.3)", line=dict(width=0)),
        name="Ceiling",
        showlegend=True,
    ))

    # Primary bars (foreground)
    fig.add_trace(go.Bar(
        y=df["title_current"],
        x=df[f"pct_{PRIMARY_KEY}"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=labels, textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
        name="Confirmed",
        showlegend=True,
    ))

    chart_h = max(500, len(df) * 28 + 200)
    style_figure(
        fig,
        "AI Task Exposure — Occupations of Interest",
        subtitle=f"% tasks affected | Solid = {ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]} | Faded = Ceiling",
        x_title=None, height=chart_h, show_legend=True,
    )
    fig.update_layout(
        barmode="overlay",
        margin=dict(l=20, r=80, t=80, b=120),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False, zeroline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=9, family=FONT_FAMILY)),
        bargap=0.25,
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5,
                    font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY)),
    )
    return fig


def _risk_tier_chart(occ_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar: named occs by risk score, colored by tier."""
    df = occ_df.sort_values("risk_score", ascending=True)
    colors = [TIER_COLORS_RISK.get(t, COLORS["muted"]) for t in df["risk_tier"]]
    labels = [f"Score: {s}  ({t})" for s, t in zip(df["risk_score"], df["risk_tier"])]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["title_current"], x=df["risk_score"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=labels, textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    chart_h = max(500, len(df) * 28 + 200)
    style_figure(
        fig,
        "Composite Risk Score — Occupations of Interest",
        subtitle=f"Weighted scoring (0–10) | Red = high, Orange = mod-high, Olive = mod-low, Gray = low | {ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]}",
        x_title=None, height=chart_h, show_legend=False,
    )
    fig.update_layout(
        margin=dict(l=20, r=160, t=80, b=100),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False, zeroline=False,
                   range=[0, 12]),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=9, family=FONT_FAMILY)),
        bargap=0.25,
    )
    return fig


def _ska_gap_heatmap(occ_df: pd.DataFrame) -> go.Figure:
    """Heatmap: occ × SKA type as % of occ need."""
    pivot = occ_df[["title_current", "skills_pct", "abilities_pct", "knowledge_pct"]].copy()
    pivot = pivot.set_index("title_current")
    pivot.columns = ["Skills %", "Abilities %", "Knowledge %"]

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[
            [0.0, COLORS["primary"]],
            [0.5, "#f5f5f0"],
            [1.0, COLORS["negative"]],
        ],
        zmid=100,
        text=np.round(pivot.values, 0),
        texttemplate="%{text:.0f}%",
        hovertemplate="<b>%{y}</b><br>%{x}<br>AI at %{z:.0f}% of occ need<extra></extra>",
    ))
    chart_h = max(600, len(pivot) * 24 + 250)
    style_figure(
        fig,
        "AI as % of Occ Need by SKA Type — Occupations of Interest",
        subtitle=f"<100% = human advantage | >100% = AI leads | {ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]}",
        x_title=None, y_title=None, height=chart_h, width=650, show_legend=False,
    )
    fig.update_layout(
        margin=dict(l=20, r=40, t=80, b=100),
        yaxis=dict(autorange="reversed", tickfont=dict(size=9, family=FONT_FAMILY)),
        xaxis=dict(tickfont=dict(size=11, family=FONT_FAMILY)),
    )
    return fig


def _trend_slopes_chart(trend_df: pd.DataFrame, config_key: str) -> go.Figure:
    """Slope chart: pct at first date vs last date for named occs."""
    first_col = f"pct_first_{config_key}"
    last_col = f"pct_last_{config_key}"
    df = trend_df.dropna(subset=[first_col, last_col]).copy()
    df = df.sort_values(last_col, ascending=False)

    fig = go.Figure()
    for _, row in df.iterrows():
        color = COLORS["negative"] if row[last_col] > row[first_col] else COLORS["muted"]
        fig.add_trace(go.Scatter(
            x=[0, 1], y=[row[first_col], row[last_col]],
            mode="lines+markers+text",
            line=dict(color=color, width=1.5),
            marker=dict(size=6, color=color),
            text=["", row["title_current"]],
            textposition="middle right",
            textfont=dict(size=8, family=FONT_FAMILY, color=COLORS["neutral"]),
            showlegend=False,
            name=row["title_current"],
            hovertemplate=f"<b>{row['title_current']}</b><br>"
                          f"First: {row[first_col]:.1f}%<br>"
                          f"Last: {row[last_col]:.1f}%<br>"
                          f"Δ: {row[last_col]-row[first_col]:+.1f}pp<extra></extra>",
        ))
    series = ANALYSIS_CONFIG_SERIES[config_key]
    style_figure(
        fig,
        f"Exposure Trend — {ANALYSIS_CONFIG_LABELS[config_key]}",
        subtitle=f"{series[0]} → {series[-1]} | Red = increasing, Gray = decreasing",
        x_title=None, y_title="% Tasks Affected",
        height=700, width=900, show_legend=False,
    )
    fig.update_layout(
        margin=dict(l=60, r=40, t=80, b=100),
        xaxis=dict(
            tickmode="array", tickvals=[0, 1],
            ticktext=[series[0], series[-1]],
            showgrid=False,
            tickfont=dict(size=10, family=FONT_FAMILY),
        ),
        yaxis=dict(showgrid=True, gridcolor=COLORS["border"]),
    )
    return fig


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    fig_dir = results / "figures"
    print("Occupations of Interest -- generating outputs...\n")

    # ── Structural data ───────────────────────────────────────────────────────
    from backend.compute import get_explorer_occupations

    struct_rows = []
    for occ in get_explorer_occupations():
        struct_rows.append({
            "title_current": occ["title_current"],
            "emp_nat": occ.get("emp") or 0,
            "wage_nat": occ.get("wage") or 0,
            "major": occ.get("major", ""),
            "job_zone": occ.get("job_zone"),
            "outlook": occ.get("dws_star_rating"),
        })
    struct = pd.DataFrame(struct_rows)
    available_occs = set(struct["title_current"].tolist())

    matched = {}
    for name in OCCS_OF_INTEREST:
        m = _find_occ(name, available_occs)
        if m:
            matched[name] = m
        else:
            print(f"  WARNING: '{name}' not matched")

    matched_titles = list(matched.values())
    print(f"Matched {len(matched_titles)}/{len(OCCS_OF_INTEREST)} occupations of interest\n")

    occ_df = struct[struct["title_current"].isin(matched_titles)].copy()
    occ_df["group"] = occ_df["title_current"].apply(
        lambda t: next((g for n, g in OCC_GROUPS.items() if matched.get(n) == t), "unknown")
    )

    # ── Pct for all configs ───────────────────────────────────────────────────
    print("Computing pct for all five configs...")
    for config_key, dataset_name in ANALYSIS_CONFIGS.items():
        print(f"  {config_key}")
        pct = get_pct_tasks_affected(dataset_name)
        occ_df[f"pct_{config_key}"] = occ_df["title_current"].map(pct).fillna(0.0)
        # Workers affected
        occ_df[f"workers_{config_key}"] = occ_df[f"pct_{config_key}"] / 100.0 * occ_df["emp_nat"]

    # Ceiling delta (how much more ceiling shows vs confirmed)
    occ_df["ceiling_delta_pct"] = occ_df[f"pct_{CEILING_KEY}"] - occ_df[f"pct_{PRIMARY_KEY}"]

    # ── Load risk scores ──────────────────────────────────────────────────────
    risk_file = RISK_RESULTS / "risk_scores_primary.csv"
    if risk_file.exists():
        risk_df = pd.read_csv(risk_file)
        risk_cols = ["title_current", "risk_score", "risk_tier", "exposure_gated"] + \
                    [c for c in risk_df.columns if c.startswith("flag")]
        risk_cols = [c for c in risk_cols if c in risk_df.columns]
        occ_df = occ_df.merge(risk_df[risk_cols], on="title_current", how="left")
        print("Loaded risk scores from job_risk_scoring")
    else:
        print("WARNING: risk_scores_primary.csv not found -- run job_risk_scoring first")
        occ_df["risk_score"] = np.nan
        occ_df["risk_tier"] = "unknown"

    # ── SKA gaps ─────────────────────────────────────────────────────────────
    print("\nComputing SKA gaps...")
    ska_data = load_ska_data()
    pct_primary = get_pct_tasks_affected(ANALYSIS_CONFIGS[PRIMARY_KEY])
    ska_result = compute_ska(pct_primary, ska_data)
    ska_gaps = ska_result.occ_gaps

    occ_df = occ_df.merge(
        ska_gaps[["title_current",
                  "skills_gap", "abilities_gap", "knowledge_gap", "overall_gap",
                  "skills_pct", "abilities_pct", "knowledge_pct", "overall_pct"]],
        on="title_current", how="left",
    )

    # ── Pct and workers trends ───────────────────────────────────────────────
    print("\nComputing pct and workers trends...")
    trend_df = occ_df[["title_current", "emp_nat"]].copy()
    for config_key, series in ANALYSIS_CONFIG_SERIES.items():
        if len(series) < 2:
            continue
        pct_first = get_pct_tasks_affected(series[0])
        pct_last = get_pct_tasks_affected(series[-1])
        trend_df[f"pct_first_{config_key}"] = trend_df["title_current"].map(pct_first).fillna(0)
        trend_df[f"pct_last_{config_key}"] = trend_df["title_current"].map(pct_last).fillna(0)
        trend_df[f"pct_delta_{config_key}"] = (
            trend_df[f"pct_last_{config_key}"] - trend_df[f"pct_first_{config_key}"]
        )
        # Workers trend
        trend_df[f"workers_first_{config_key}"] = (
            trend_df[f"pct_first_{config_key}"] / 100.0 * trend_df["emp_nat"]
        )
        trend_df[f"workers_last_{config_key}"] = (
            trend_df[f"pct_last_{config_key}"] / 100.0 * trend_df["emp_nat"]
        )
        trend_df[f"workers_delta_{config_key}"] = (
            trend_df[f"workers_last_{config_key}"] - trend_df[f"workers_first_{config_key}"]
        )
    save_csv(trend_df, results / "trend_summary.csv")

    # ── Hidden at-risk flag ───────────────────────────────────────────────────
    hidden_file = AUDIENCE_RESULTS / "hidden_at_risk_occs.csv"
    if hidden_file.exists():
        hidden_df = pd.read_csv(hidden_file)
        hidden_set = set(hidden_df["title_current"].tolist())
        occ_df["hidden_at_risk"] = occ_df["title_current"].isin(hidden_set)
        print(f"Hidden at-risk flag: {occ_df['hidden_at_risk'].sum()} of {len(occ_df)} named occs flagged")
    else:
        occ_df["hidden_at_risk"] = False
        print("WARNING: hidden_at_risk_occs.csv not found -- run audience_framing first")

    # ── Save full output ──────────────────────────────────────────────────────
    pct_cols = [f"pct_{k}" for k in ANALYSIS_CONFIGS]
    workers_cols = [f"workers_{k}" for k in ANALYSIS_CONFIGS]
    flag_cols = [c for c in occ_df.columns if c.startswith("flag")]
    out_cols = (
        ["title_current", "group", "major", "emp_nat", "wage_nat", "job_zone", "outlook"] +
        pct_cols + workers_cols + ["ceiling_delta_pct"] +
        ["risk_score", "risk_tier"] + flag_cols +
        ["skills_gap", "abilities_gap", "knowledge_gap", "overall_gap",
         "skills_pct", "abilities_pct", "knowledge_pct", "overall_pct",
         "hidden_at_risk"]
    )
    full_out = occ_df[[c for c in out_cols if c in occ_df.columns]].copy()
    save_csv(full_out.sort_values(f"pct_{PRIMARY_KEY}", ascending=False),
             results / "occs_of_interest_full.csv")
    print("\nSaved occs_of_interest_full.csv")

    exposure_out = occ_df[["title_current", "group"] + pct_cols + ["ceiling_delta_pct"]].copy()
    save_csv(exposure_out, results / "exposure_by_config.csv")

    # ── Per-occ SKA element detail ────────────────────────────────────────────
    interest_elem_file = RESILIENCE_RESULTS / "occs_of_interest_gaps.csv"
    if interest_elem_file.exists():
        shutil.copy2(interest_elem_file, results / "ska_element_detail.csv")
        print("Copied SKA element detail from worker_resilience")

    # ── Figures ───────────────────────────────────────────────────────────────
    print("\nGenerating figures...")

    fig = _exposure_ranked_bar(occ_df)
    save_figure(fig, fig_dir / "exposure_ranked_bar.png")
    print("  exposure_ranked_bar.png")

    if "risk_score" in occ_df.columns and occ_df["risk_score"].notna().any():
        fig = _risk_tier_chart(occ_df.dropna(subset=["risk_score"]))
        save_figure(fig, fig_dir / "risk_tier_summary.png")
        print("  risk_tier_summary.png")

    if "skills_gap" in occ_df.columns and occ_df["skills_gap"].notna().any():
        fig = _ska_gap_heatmap(occ_df.dropna(subset=["skills_gap"]))
        save_figure(fig, fig_dir / "ska_gap_heatmap.png")
        print("  ska_gap_heatmap.png")

    # Trend slope charts (primary + ceiling)
    for ck in [PRIMARY_KEY, CEILING_KEY]:
        trend_cols = [c for c in trend_df.columns if ck in c]
        if trend_cols:
            fig = _trend_slopes_chart(trend_df, ck)
            safe_ck = ck.replace("_", "")
            save_figure(fig, fig_dir / f"trend_slopes_{safe_ck}.png")
            print(f"  trend_slopes_{safe_ck}.png")

    # ── Copy key figures ──────────────────────────────────────────────────────
    committed = HERE / "figures"
    committed.mkdir(exist_ok=True)
    for fname in ["exposure_ranked_bar.png", "risk_tier_summary.png",
                  "ska_gap_heatmap.png", "trend_slopes_allconfirmed.png",
                  "trend_slopes_allceiling.png"]:
        src = fig_dir / fname
        if src.exists():
            shutil.copy2(src, committed / fname)

    # ── PDF ───────────────────────────────────────────────────────────────────
    from analysis.utils import generate_pdf
    md_path = HERE / "occs_of_interest_report.md"
    if md_path.exists():
        generate_pdf(md_path, results / "occs_of_interest_report.pdf")

    print("\nDone.")


if __name__ == "__main__":
    main()
