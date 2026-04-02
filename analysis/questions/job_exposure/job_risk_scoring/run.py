"""
run.py — Job Exposure: Job Risk Scoring

Which jobs are most at risk of replacement (not just transformation)?

Computes seven binary risk flags per occupation and combines them into a
composite risk score (0–7). Primary config: all_ceiling. Cross-config
comparison shows which assignments are robust vs. source-dependent.

Risk flags (1 = at risk):
  1. pct_tasks_affected > median
  2. overall_ska_gap > median  (AI capability exceeds typical job need)
  3. pct_delta > 0 AND pct_delta > median(pct_delta)  [trend, first→last date]
  4. ska_delta > 0 AND ska_delta > median(ska_delta)   [SKA gap trend]
  5. job_zone ∈ {1, 2, 3}
  6. outlook ∈ {2, 3}  (note: 1 = good outlook/low wages — NOT at risk)
  7. n_software > median

Risk tiers: 5–7 = High, 3–4 = Moderate, 1–2 = Low.

Run from project root:
    venv/Scripts/python -m analysis.questions.job_exposure.job_risk_scoring.run
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
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.data.compute_ska import SKAData, compute_ska, load_ska_data
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "analysis" / "data"
TECH_SKILLS_FILE = DATA_DIR / "tech_skills_simple.csv"

RISK_AT_RISK_ZONE = {1, 2, 3}      # job_zone values flagged as at risk
RISK_AT_RISK_OUTLOOK = {2, 3}      # DWS outlook values flagged as at risk
PIVOT_N = 10                        # top/bottom N occs used for pivot distance

TIER_LABELS = {"high": "High Risk (5–7)", "moderate": "Moderate Risk (3–4)", "low": "Low Risk (1–2)"}
TIER_ORDER = ["high", "moderate", "low"]
TIER_COLORS = {"high": COLORS["negative"], "moderate": COLORS["accent"], "low": COLORS["muted"]}


def _assign_risk_tier(score: int) -> str:
    if score >= 5:
        return "high"
    if score >= 3:
        return "moderate"
    return "low"


# ── Employment + structural lookup ────────────────────────────────────────────

def _get_structural_data() -> pd.DataFrame:
    """Return DataFrame with title_current, emp_nat, wage_nat, major, job_zone, outlook."""
    from backend.compute import get_explorer_occupations

    rows = []
    for occ in get_explorer_occupations():
        rows.append({
            "title_current": occ["title_current"],
            "emp_nat": occ.get("emp") or 0,
            "wage_nat": occ.get("wage") or 0,
            "major": occ.get("major", ""),
            "job_zone": occ.get("job_zone"),
            "outlook": occ.get("dws_star_rating"),
        })
    return pd.DataFrame(rows)


# ── Trend helpers ─────────────────────────────────────────────────────────────

def _compute_pct_trend(config_key: str) -> pd.Series:
    """Return pct_delta (last - first) per occ for a config's time series."""
    series = ANALYSIS_CONFIG_SERIES[config_key]
    if len(series) < 2:
        return pd.Series(dtype=float)
    pct_first = get_pct_tasks_affected(series[0])
    pct_last = get_pct_tasks_affected(series[-1])
    combined = pd.DataFrame({"first": pct_first, "last": pct_last})
    combined["delta"] = combined["last"].fillna(0) - combined["first"].fillna(0)
    return combined["delta"]


def _compute_ska_trend(config_key: str, ska_data: SKAData) -> pd.Series:
    """Return ska_delta (overall_gap last - first) per occ for a config's series."""
    series = ANALYSIS_CONFIG_SERIES[config_key]
    if len(series) < 2:
        return pd.Series(dtype=float)
    pct_first = get_pct_tasks_affected(series[0])
    pct_last = get_pct_tasks_affected(series[-1])
    result_first = compute_ska(pct_first, ska_data)
    result_last = compute_ska(pct_last, ska_data)
    gaps_first = result_first.occ_gaps.set_index("title_current")["overall_gap"]
    gaps_last = result_last.occ_gaps.set_index("title_current")["overall_gap"]
    delta = (gaps_last - gaps_first).rename("ska_delta")
    return delta


# ── Flag computation ──────────────────────────────────────────────────────────

def _compute_flags(
    df: pd.DataFrame,
    pct: pd.Series,
    ska_gap: pd.Series,
    pct_delta: pd.Series,
    ska_delta: pd.Series,
) -> pd.DataFrame:
    """
    Compute all 7 binary flags for each occupation.

    Parameters
    ----------
    df        : structural data (title_current, emp_nat, job_zone, outlook, n_software)
    pct       : pct_tasks_affected Series (title_current index)
    ska_gap   : overall_gap Series (title_current index)
    pct_delta : pct delta from first to last date (title_current index)
    ska_delta : ska_gap delta from first to last date (title_current index)
    """
    out = df.copy()
    out["pct"] = out["title_current"].map(pct).fillna(0.0)
    out["ska_gap"] = out["title_current"].map(ska_gap).fillna(np.nan)
    out["pct_delta"] = out["title_current"].map(pct_delta).fillna(np.nan)
    out["ska_delta"] = out["title_current"].map(ska_delta).fillna(np.nan)

    pct_median = out["pct"].median()
    ska_median = out["ska_gap"].median()
    pct_delta_median = out["pct_delta"].median()
    ska_delta_median = out["ska_delta"].median()
    n_software_median = out["n_software"].median()

    out["flag1_pct"] = (out["pct"] > pct_median).astype(int)
    out["flag2_ska"] = (out["ska_gap"] > ska_median).astype(int)
    out["flag3_pct_trend"] = (
        (out["pct_delta"] > 0) & (out["pct_delta"] > pct_delta_median)
    ).astype(int)
    out["flag4_ska_trend"] = (
        (out["ska_delta"] > 0) & (out["ska_delta"] > ska_delta_median)
    ).astype(int)
    out["flag5_job_zone"] = out["job_zone"].apply(
        lambda z: 1 if pd.notna(z) and int(z) in RISK_AT_RISK_ZONE else 0
    )
    out["flag6_outlook"] = out["outlook"].apply(
        lambda o: 1 if pd.notna(o) and int(o) in RISK_AT_RISK_OUTLOOK else 0
    )
    out["flag7_n_software"] = (out["n_software"] > n_software_median).astype(int)

    flag_cols = [f"flag{i}_{n}" for i, n in
                 enumerate(["pct", "ska", "pct_trend", "ska_trend", "job_zone", "outlook", "n_software"], 1)]
    out["risk_score"] = out[flag_cols].sum(axis=1)
    out["risk_tier"] = out["risk_score"].apply(_assign_risk_tier)

    return out


# ── Figures ───────────────────────────────────────────────────────────────────

def _risk_distribution_bar(df: pd.DataFrame, config_label: str) -> go.Figure:
    """Bar chart: number of occupations in each risk tier."""
    counts = df["risk_tier"].value_counts()
    emp_by_tier = df.groupby("risk_tier")["emp_nat"].sum()
    fig = go.Figure()
    for tier in TIER_ORDER:
        n = counts.get(tier, 0)
        e = emp_by_tier.get(tier, 0)
        fig.add_trace(go.Bar(
            x=[TIER_LABELS[tier]], y=[n],
            marker=dict(color=TIER_COLORS[tier], line=dict(width=0)),
            text=[f"{n} occs<br>{e/1e6:.1f}M workers"],
            textposition="outside",
            textfont=dict(size=11, color=COLORS["neutral"], family=FONT_FAMILY),
            name=TIER_LABELS[tier],
            showlegend=False,
        ))
    style_figure(
        fig,
        "Most Occupations Are in the Low-Risk Tier",
        subtitle=f"{config_label} | 7-factor composite risk score",
        x_title=None, y_title="Number of Occupations",
        height=500, width=700, show_legend=False,
    )
    fig.update_layout(
        yaxis=dict(showgrid=True, gridcolor=COLORS["border"]),
        xaxis=dict(showgrid=False),
        bargap=0.35,
    )
    return fig


def _risk_vs_pct_scatter(df: pd.DataFrame, config_label: str) -> go.Figure:
    """Scatter: risk_score (x) vs pct_tasks_affected (y)."""
    fig = go.Figure()
    for tier in TIER_ORDER:
        sub = df[df["risk_tier"] == tier]
        fig.add_trace(go.Scatter(
            x=sub["risk_score"] + (np.random.default_rng(42).uniform(-0.2, 0.2, len(sub))),
            y=sub["pct"],
            mode="markers",
            name=TIER_LABELS[tier],
            marker=dict(color=TIER_COLORS[tier], size=6, opacity=0.6,
                        line=dict(width=0.5, color=COLORS["bg"])),
            text=sub["title_current"],
            hovertemplate="<b>%{text}</b><br>Risk Score: %{x:.0f}<br>% Tasks: %{y:.1f}%<extra></extra>",
        ))
    style_figure(
        fig,
        "Risk Score vs Task Exposure",
        subtitle=f"{config_label} | Jitter added to x-axis for visibility",
        x_title="Composite Risk Score (0–7)", y_title="% Tasks Affected",
        height=600, width=900, show_legend=True,
    )
    fig.update_layout(
        xaxis=dict(tickmode="linear", tick0=0, dtick=1),
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5,
                    font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY)),
    )
    return fig


def _cross_config_heatmap(risk_all: pd.DataFrame) -> go.Figure:
    """
    Heatmap: for each occ, show risk tier across all five configs.
    Only show top 40 highest-risk occs (by primary config score).
    """
    tier_to_num = {"high": 3, "moderate": 2, "low": 1}
    tier_to_color = {3: COLORS["negative"], 2: COLORS["accent"], 1: COLORS["muted"]}

    top40 = (
        risk_all[risk_all["config"] == "all_ceiling"]
        .nlargest(40, "risk_score")["title_current"]
        .tolist()
    )
    pivot = risk_all[risk_all["title_current"].isin(top40)].pivot(
        index="title_current", columns="config", values="risk_tier"
    )
    pivot = pivot.loc[top40]
    pivot_num = pivot.map(lambda t: tier_to_num.get(t, 0))

    config_order = list(ANALYSIS_CONFIGS.keys())
    pivot = pivot[config_order]
    pivot_num = pivot_num[config_order]

    z = pivot_num.values
    text = pivot.values

    fig = go.Figure(go.Heatmap(
        z=z,
        x=[ANALYSIS_CONFIG_LABELS[k] for k in config_order],
        y=top40,
        text=text,
        texttemplate="%{text}",
        colorscale=[[0, COLORS["muted"]], [0.5, COLORS["accent"]], [1.0, COLORS["negative"]]],
        showscale=False,
        hovertemplate="<b>%{y}</b><br>Config: %{x}<br>Tier: %{text}<extra></extra>",
    ))
    chart_h = max(700, len(top40) * 20 + 200)
    style_figure(
        fig,
        "Risk Tier Robustness Across Dataset Configs",
        subtitle="Top 40 highest-risk occupations (all_ceiling) | How tier assignment varies by config",
        x_title=None, y_title=None, height=chart_h, width=900, show_legend=False,
    )
    fig.update_layout(
        yaxis=dict(autorange="reversed", tickfont=dict(size=9, family=FONT_FAMILY)),
        xaxis=dict(tickfont=dict(size=10, family=FONT_FAMILY)),
    )
    return fig


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    fig_dir = results / "figures"
    print("Job Risk Scoring -- generating outputs...\n")

    # ── Structural data ───────────────────────────────────────────────────────
    print("Loading structural data...")
    struct = _get_structural_data()
    print(f"  {len(struct)} occupations")

    # ── n_software ────────────────────────────────────────────────────────────
    if not TECH_SKILLS_FILE.exists():
        raise FileNotFoundError(
            f"tech_skills_simple.csv not found at {TECH_SKILLS_FILE}. "
            "Run: venv/Scripts/python -m analysis.data.compute_tech_skills"
        )
    tech = pd.read_csv(TECH_SKILLS_FILE)
    struct = struct.merge(
        tech[["title", "n_software"]].rename(columns={"title": "title_current"}),
        on="title_current", how="left",
    )
    struct["n_software"] = struct["n_software"].fillna(0).astype(int)
    print(f"  n_software joined: {struct['n_software'].gt(0).sum()} occs matched\n")

    # ── Load SKA data once ────────────────────────────────────────────────────
    print("Loading SKA base data...")
    ska_data = load_ska_data()

    # ── Primary config: all_ceiling ───────────────────────────────────────────
    primary_key = "all_ceiling"
    primary_dataset = ANALYSIS_CONFIGS[primary_key]
    print(f"\n== Primary config: {primary_key} ({primary_dataset}) ==")

    print("  Computing pct_tasks_affected...")
    pct_primary = get_pct_tasks_affected(primary_dataset)

    print("  Computing SKA gaps...")
    ska_primary = compute_ska(pct_primary, ska_data)
    ska_gap_primary = ska_primary.occ_gaps.set_index("title_current")["overall_gap"]

    print("  Computing pct trend (first -> last date)...")
    pct_delta_primary = _compute_pct_trend(primary_key)

    print("  Computing SKA trend (first -> last date)...")
    ska_delta_primary = _compute_ska_trend(primary_key, ska_data)

    print("  Computing risk flags...")
    primary_df = _compute_flags(struct, pct_primary, ska_gap_primary,
                                pct_delta_primary, ska_delta_primary)

    # Print tier summary
    tier_emp = primary_df.groupby("risk_tier")["emp_nat"].sum()
    for tier in TIER_ORDER:
        n = (primary_df["risk_tier"] == tier).sum()
        e = tier_emp.get(tier, 0)
        print(f"  {TIER_LABELS[tier]}: {n} occs, {e/1e6:.1f}M workers")

    # Flag frequency
    flag_cols = [c for c in primary_df.columns if c.startswith("flag")]
    flag_freq = primary_df[flag_cols].sum().reset_index()
    flag_freq.columns = ["flag", "n_triggered"]
    flag_freq["pct_of_occs"] = flag_freq["n_triggered"] / len(primary_df) * 100
    save_csv(flag_freq, results / "flags_breakdown.csv")

    # Save primary results
    out_cols = ["title_current", "emp_nat", "wage_nat", "major", "job_zone", "outlook",
                "n_software", "pct", "ska_gap", "pct_delta", "ska_delta"] + flag_cols + \
               ["risk_score", "risk_tier"]
    primary_out = primary_df[out_cols].rename(columns={
        "emp_nat": "employment", "wage_nat": "median_wage", "pct": "pct_tasks_affected"
    })
    save_csv(primary_out.sort_values("risk_score", ascending=False),
             results / "risk_scores_primary.csv")
    print("\nSaved risk_scores_primary.csv")

    # Tier summary
    tier_summary = primary_df.groupby("risk_tier").agg(
        n_occs=("title_current", "count"),
        total_emp=("emp_nat", "sum"),
        total_wages=("wage_nat", "mean"),  # median wage isn't directly addable
        avg_pct=("pct", "mean"),
        avg_risk_score=("risk_score", "mean"),
    ).reset_index()
    save_csv(tier_summary, results / "risk_tier_summary.csv")

    # ── Cross-config comparison ───────────────────────────────────────────────
    print("\n== Cross-config risk scores ==")
    all_config_rows = []
    for config_key, dataset_name in ANALYSIS_CONFIGS.items():
        print(f"  {config_key}: {dataset_name}")
        pct_cfg = get_pct_tasks_affected(dataset_name)
        ska_cfg = compute_ska(pct_cfg, ska_data)
        ska_gap_cfg = ska_cfg.occ_gaps.set_index("title_current")["overall_gap"]
        pct_delta_cfg = _compute_pct_trend(config_key)
        ska_delta_cfg = _compute_ska_trend(config_key, ska_data)
        flags_cfg = _compute_flags(struct, pct_cfg, ska_gap_cfg, pct_delta_cfg, ska_delta_cfg)
        flags_cfg["config"] = config_key
        all_config_rows.append(
            flags_cfg[["title_current", "config", "pct", "ska_gap",
                        "risk_score", "risk_tier"]].copy()
        )

    risk_all = pd.concat(all_config_rows, ignore_index=True)
    save_csv(risk_all, results / "risk_scores_all_configs.csv")
    print("Saved risk_scores_all_configs.csv")

    # ── Save pivot-distance inputs (top/bottom 10 per zone) ───────────────────
    zone_pivot_rows = []
    for zone in [1, 2, 3, 4, 5]:
        zone_df = primary_df[primary_df["job_zone"].apply(
            lambda z: pd.notna(z) and int(z) == zone
        )].copy()
        if zone_df.empty:
            continue
        top_n = min(PIVOT_N, len(zone_df))
        high_risk = zone_df.nlargest(top_n, "risk_score")[
            ["title_current", "risk_score", "pct"]
        ].assign(group="high_risk", job_zone=zone)
        low_risk = zone_df.nsmallest(top_n, "risk_score")[
            ["title_current", "risk_score", "pct"]
        ].assign(group="low_risk", job_zone=zone)
        zone_pivot_rows.extend([high_risk, low_risk])
    if zone_pivot_rows:
        pivot_inputs = pd.concat(zone_pivot_rows, ignore_index=True)
        save_csv(pivot_inputs, results / "pivot_distance_inputs.csv")
        print("Saved pivot_distance_inputs.csv (for pivot_distance sub-question)")

    # ── Figures ───────────────────────────────────────────────────────────────
    print("\nGenerating figures...")

    fig = _risk_distribution_bar(primary_df, ANALYSIS_CONFIG_LABELS[primary_key])
    save_figure(fig, fig_dir / "risk_tier_distribution.png")
    print("  risk_tier_distribution.png")

    fig = _risk_vs_pct_scatter(primary_df, ANALYSIS_CONFIG_LABELS[primary_key])
    save_figure(fig, fig_dir / "risk_vs_pct_scatter.png")
    print("  risk_vs_pct_scatter.png")

    fig = _cross_config_heatmap(risk_all)
    save_figure(fig, fig_dir / "cross_config_robustness.png")
    print("  cross_config_robustness.png")

    # ── Copy key figures ──────────────────────────────────────────────────────
    committed = HERE / "figures"
    committed.mkdir(exist_ok=True)
    for fname in ["risk_tier_distribution.png", "risk_vs_pct_scatter.png",
                  "cross_config_robustness.png"]:
        src = fig_dir / fname
        if src.exists():
            shutil.copy2(src, committed / fname)

    # ── PDF ────────────────────────────────────────────────────────────────────
    from analysis.utils import generate_pdf
    md_path = HERE / "job_risk_scoring_report.md"
    if md_path.exists():
        generate_pdf(md_path, results / "job_risk_scoring_report.pdf")

    print("\nDone.")


if __name__ == "__main__":
    main()
