"""
run.py — Potential Growth: Automation Opportunity

Where does AI capability already exceed human occupational need (SKA pct > 100%)
AND the adoption gap is large — signaling where automation could happen right now?

Two input dimensions per occupation:
  1. SKA overall_pct  — AI capability as a % of the occupation's skill+knowledge
                        requirement (ratio of sums per occ). >100% means AI exceeds
                        the occupation's need; <100% means humans still lead.
  2. Adoption gap     — pct_tasks_affected(ceiling) − pct_tasks_affected(confirmed).

Quadrant framing:
  - Split on SKA pct at the natural threshold of 100% (AI leads ↔ humans lead),
    not the median — this aligns with the "AI surpasses human requirement"
    semantic of the new percentage framing.
  - Split on adoption gap at the median.

  Q1: AI leads (>100%)  + Big gap   = Automation opportunity (AI can do it, nobody's deployed it)
  Q2: AI leads (>100%)  + Small gap = Already adopted
  Q3: Humans lead (<100%) + Big gap = Tool gap (humans have edge, but AI exists and isn't used)
  Q4: Humans lead (<100%) + Small gap = Low priority

When Q1 occupations also carry a high risk tier (from job_risk_scoring), that's a
signal for job transformation — not just upside opportunity.

SKA formula: compute_ska(all_confirmed pct) → per-occupation overall_pct.
Risk tiers: loaded from job_risk_scoring/results/risk_scores_primary.csv if available;
falls back to recomputing from exposure flags if not.

Figures (key ones copied to figures/):
  opportunity_scatter.png          — Scatter: SKA gap × adoption gap, colored by risk tier
  opportunity_quadrant_summary.png — Quadrant employment distribution by major category
  q1_top_occupations.png           — Top Q1 occupations by workers × adoption gap
  transformation_signal.png        — Q1 ∩ high-risk tier
  sector_opportunity.png           — Major category: mean SKA gap vs mean adoption gap

Run from project root:
    venv/Scripts/python -m analysis.questions.potential_growth.automation_opportunity.run
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
from analysis.data.compute_ska import compute_ska, load_ska_data
from analysis.utils import (
    CATEGORY_PALETTE,
    COLORS,
    FONT_FAMILY,
    format_workers,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
RISK_SCORES_CSV = (
    HERE.parent.parent.parent  # analysis/
    / "questions" / "job_exposure" / "job_risk_scoring" / "results"
    / "risk_scores_primary.csv"
)

PRIMARY_KEY = "all_confirmed"
CEILING_KEY = "all_ceiling"

QUADRANT_COLORS = {
    "Q1: Automation opportunity": COLORS["accent"],
    "Q2: Already adopted":        COLORS["secondary"],
    "Q3: Tool gap":               COLORS["primary"],
    "Q4: Low priority":           COLORS["muted"],
}

RISK_TIER_COLORS = {
    "high":     COLORS["negative"],
    "mod_high": COLORS["accent"],
    "mod_low":  COLORS["secondary"],
    "low":      COLORS["primary"],
    "unknown":  COLORS["muted"],
}


# ── Data helpers ──────────────────────────────────────────────────────────────

def _get_occ_data(dataset_name: str) -> pd.DataFrame:
    """Get occupation-level metrics for one dataset."""
    from backend.compute import get_group_data

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
        return pd.DataFrame()
    df = data["df"]
    gc = data.get("group_col", "title_current")
    df = df.rename(columns={gc: "title_current"})
    return df[["title_current", "pct_tasks_affected", "workers_affected", "wages_affected"]].copy()


def _get_emp_lookup() -> pd.DataFrame:
    from backend.compute import get_explorer_occupations

    rows = []
    for occ in get_explorer_occupations():
        rows.append({
            "title_current": occ["title_current"],
            "emp_nat": occ.get("emp") or 0,
            "median_wage": occ.get("wage") or 0,
            "major": occ.get("major", ""),
            "job_zone": occ.get("job_zone"),
        })
    return pd.DataFrame(rows)


def _load_risk_tiers() -> pd.DataFrame:
    """Load risk tier per occupation from job_risk_scoring results if available."""
    if RISK_SCORES_CSV.exists():
        df = pd.read_csv(RISK_SCORES_CSV, usecols=["title_current", "risk_tier", "risk_score"])
        return df
    return pd.DataFrame(columns=["title_current", "risk_tier", "risk_score"])


SKA_THRESHOLD = 100.0  # AI leads vs humans lead — natural threshold on overall_pct


def _assign_quadrant(ska_pct: float, adoption_gap: float,
                     gap_median: float) -> str:
    """Quadrant assignment.

    Note: SKA axis splits at 100% (the natural "AI matches occupation need"
    line), NOT at the median. The adoption gap axis still splits at the median.
    """
    ai_leads = ska_pct > SKA_THRESHOLD
    big_gap = adoption_gap > gap_median
    if ai_leads and big_gap:
        return "Q1: Automation opportunity"
    if ai_leads and not big_gap:
        return "Q2: Already adopted"
    if not ai_leads and big_gap:
        return "Q3: Tool gap"
    return "Q4: Low priority"


# ── Figure builders ────────────────────────────────────────────────────────────

def _opportunity_scatter(df: pd.DataFrame) -> go.Figure:
    """2D scatter: SKA gap (x) vs adoption gap (y), colored by risk tier."""
    fig = go.Figure()

    risk_tiers = df["risk_tier"].unique().tolist()
    # 4-tier risk taxonomy from the new job_risk_scoring
    for tier in ["high", "mod_high", "mod_low", "low", "unknown"]:
        if tier not in risk_tiers:
            continue
        sub = df[df["risk_tier"] == tier]
        max_emp = df["emp_nat"].max() if df["emp_nat"].max() > 0 else 1
        sizes = (sub["emp_nat"] / max_emp * 20 + 4).clip(upper=22).tolist()
        fig.add_trace(go.Scatter(
            x=sub["ska_overall_pct"],
            y=sub["adoption_gap"],
            mode="markers",
            name=f"{tier.replace('_', '-').title()} risk",
            marker=dict(
                color=RISK_TIER_COLORS.get(tier, COLORS["muted"]),
                size=sizes,
                opacity=0.65,
                line=dict(width=0.5, color=COLORS["bg"]),
            ),
            text=sub["title_current"],
            hovertemplate=(
                "<b>%{text}</b><br>SKA pct: %{x:.0f}%<br>"
                "Adoption gap: %{y:.1f}pp<extra></extra>"
            ),
        ))

    # Crosshair lines: SKA at 100%, adoption gap at median
    fig.add_vline(x=SKA_THRESHOLD, line_dash="dot",
                  line_color=COLORS["muted"], line_width=1)
    fig.add_hline(y=df["adoption_gap"].median(), line_dash="dot",
                  line_color=COLORS["muted"], line_width=1)

    # Quadrant labels
    x_range = df["ska_overall_pct"].quantile([0.05, 0.95])
    y_range = df["adoption_gap"].quantile([0.05, 0.95])
    gap_med = df["adoption_gap"].median()

    fig.add_annotation(x=x_range[0.95] * 0.7, y=y_range[0.95] * 0.85,
                       text="<b>Q1: Automation<br>Opportunity</b>",
                       showarrow=False,
                       font=dict(size=9, color=COLORS["accent"], family=FONT_FAMILY))
    fig.add_annotation(x=x_range[0.95] * 0.7, y=y_range[0.05] * 1.3,
                       text="Q2: Already Adopted",
                       showarrow=False,
                       font=dict(size=9, color=COLORS["secondary"], family=FONT_FAMILY))
    fig.add_annotation(x=x_range[0.05] * 0.5, y=y_range[0.95] * 0.85,
                       text="Q3: Tool Gap",
                       showarrow=False,
                       font=dict(size=9, color=COLORS["primary"], family=FONT_FAMILY))
    fig.add_annotation(x=x_range[0.05] * 0.5, y=y_range[0.05] * 1.3,
                       text="Q4: Low Priority",
                       showarrow=False,
                       font=dict(size=9, color=COLORS["muted"], family=FONT_FAMILY))

    style_figure(
        fig,
        "Automation Opportunity Landscape",
        subtitle=(
            "x = AI capability as % of occ need (>100% = AI leads) | "
            "y = adoption gap (ceiling − confirmed %) | color = risk tier | size = employment"
        ),
        x_title="SKA Overall % (AI as % of occ need; 100% = AI matches)",
        y_title="Adoption Gap (pp)",
        height=720, width=1100,
        show_legend=True,
    )
    fig.update_layout(
        margin=dict(l=70, r=40, t=80, b=120),
        legend=dict(
            orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        ),
    )
    return fig


def _quadrant_summary_bar(df: pd.DataFrame) -> go.Figure:
    """Stacked bar: employment in each quadrant by major category."""
    by_major_q = (
        df.groupby(["major", "quadrant"])["emp_nat"]
        .sum()
        .reset_index()
    )
    major_totals = df.groupby("major")["emp_nat"].sum().reset_index(name="total")
    by_major_q = by_major_q.merge(major_totals, on="major")
    by_major_q["pct_emp"] = by_major_q["emp_nat"] / by_major_q["total"] * 100

    # Sort by Q1 share
    q1_share = (
        by_major_q[by_major_q["quadrant"] == "Q1: Automation opportunity"]
        .set_index("major")["pct_emp"]
    )
    majors = sorted(df["major"].dropna().unique(), key=lambda m: q1_share.get(m, 0))

    quadrant_order = [
        "Q1: Automation opportunity",
        "Q2: Already adopted",
        "Q3: Tool gap",
        "Q4: Low priority",
    ]
    fig = go.Figure()
    for q in quadrant_order:
        sub = by_major_q[by_major_q["quadrant"] == q].set_index("major")
        vals = [sub.loc[m, "pct_emp"] if m in sub.index else 0 for m in majors]
        fig.add_trace(go.Bar(
            y=majors, x=vals, orientation="h",
            name=q,
            marker=dict(color=QUADRANT_COLORS.get(q, COLORS["muted"]), line=dict(width=0)),
        ))

    chart_h = max(550, len(majors) * 28 + 250)
    style_figure(
        fig,
        "Automation Opportunity Quadrants by Sector",
        subtitle="% of sector employment in each quadrant | SKA × adoption gap",
        x_title=None,
        height=chart_h,
        show_legend=True,
    )
    fig.update_layout(
        barmode="stack", bargap=0.2,
        margin=dict(l=20, r=40, t=80, b=120),
        xaxis=dict(showgrid=False, showticklabels=True, ticksuffix="%",
                   tickfont=dict(size=9, color=COLORS["muted"])),
        yaxis=dict(showgrid=False, tickfont=dict(size=9, family=FONT_FAMILY)),
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5,
                    font=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY)),
    )
    return fig


def _q1_bar(q1_df: pd.DataFrame, title: str, subtitle: str, top_n: int = 25) -> go.Figure:
    """Top Q1 occupations by opportunity score (workers × adoption_gap)."""
    df = q1_df.sort_values("opportunity_score", ascending=False).head(top_n)
    df = df.sort_values("opportunity_score", ascending=True)

    labels = [f"{row['adoption_gap']:.1f}pp | SKA: {row['ska_overall_pct']:.0f}%"
              for _, row in df.iterrows()]

    fig = go.Figure(go.Bar(
        y=df["title_current"],
        x=df["opportunity_score"],
        orientation="h",
        marker=dict(color=COLORS["accent"], line=dict(width=0)),
        text=labels,
        textposition="outside",
        textfont=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Score: %{x:,.0f}<extra></extra>",
    ))
    chart_h = max(500, len(df) * 30 + 200)
    style_figure(
        fig, title, subtitle=subtitle,
        x_title=None, height=chart_h, show_legend=False,
    )
    fig.update_layout(
        margin=dict(l=20, r=180, t=80, b=80),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False, zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        bargap=0.25,
    )
    return fig


def _sector_opportunity_scatter(major_df: pd.DataFrame) -> go.Figure:
    """Sector-level: mean SKA pct vs mean adoption gap, sized by total workers."""
    df = major_df.dropna(subset=["mean_ska_pct", "mean_adoption_gap"])
    max_emp = df["total_workers"].max() if df["total_workers"].max() > 0 else 1

    fig = go.Figure(go.Scatter(
        x=df["mean_ska_pct"],
        y=df["mean_adoption_gap"],
        mode="markers+text",
        marker=dict(
            color=COLORS["primary"],
            size=(df["total_workers"] / max_emp * 40 + 10).clip(upper=45).tolist(),
            opacity=0.75,
            line=dict(width=1, color=COLORS["bg"]),
        ),
        text=df["major"],
        textposition="top center",
        textfont=dict(size=8, color=COLORS["neutral"], family=FONT_FAMILY),
        hovertemplate=(
            "<b>%{text}</b><br>Mean SKA pct: %{x:.0f}%<br>"
            "Mean adoption gap: %{y:.1f}pp<extra></extra>"
        ),
    ))

    fig.add_vline(x=SKA_THRESHOLD, line_dash="solid",
                  line_color=COLORS["border"], line_width=1)
    fig.add_hline(y=df["mean_adoption_gap"].median(), line_dash="dot",
                  line_color=COLORS["muted"], line_width=1)

    style_figure(
        fig,
        "Sector Opportunity Landscape",
        subtitle=("x = mean SKA pct per sector (>100% = AI leads) | "
                  "y = mean adoption gap | size = total workers"),
        x_title="Mean SKA Overall % (100% = AI matches occ need)",
        y_title="Mean Adoption Gap (pp)",
        height=650, width=1000,
        show_legend=False,
    )
    fig.update_layout(margin=dict(l=60, r=40, t=80, b=80))
    return fig


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    fig_dir = results / "figures"
    committed_figs = HERE / "figures"
    committed_figs.mkdir(exist_ok=True)

    primary_ds = ANALYSIS_CONFIGS[PRIMARY_KEY]
    ceiling_ds = ANALYSIS_CONFIGS[CEILING_KEY]

    print("Automation Opportunity — generating outputs...\n")

    # ── 1. Get pct data and compute SKA ───────────────────────────────────────

    print("== Computing SKA (all_confirmed) ==")
    ska_data = load_ska_data()
    pct_confirmed = get_pct_tasks_affected(primary_ds)
    ska_result = compute_ska(pct_confirmed, ska_data)
    occ_gaps = ska_result.occ_gaps.copy()
    # occ_gaps columns: title_current, skills_gap/pct, abilities_gap/pct,
    # knowledge_gap/pct, overall_gap, overall_pct
    print(f"  SKA computed for {len(occ_gaps)} occupations")

    # ── 2. Get adoption gap per occupation ────────────────────────────────────

    print("== Computing adoption gap ==")
    confirmed_occ = _get_occ_data(primary_ds)
    ceiling_occ = _get_occ_data(ceiling_ds)

    if confirmed_occ.empty or ceiling_occ.empty:
        print("  ERROR: could not load occupation data")
        return

    merged_occ = confirmed_occ.merge(
        ceiling_occ, on="title_current", how="outer", suffixes=("_confirmed", "_ceiling")
    )
    for col in ["pct_tasks_affected", "workers_affected", "wages_affected"]:
        merged_occ[f"{col}_confirmed"] = merged_occ.get(f"{col}_confirmed", pd.Series(0.0)).fillna(0.0)
        merged_occ[f"{col}_ceiling"] = merged_occ.get(f"{col}_ceiling", pd.Series(0.0)).fillna(0.0)
    merged_occ["adoption_gap"] = (
        merged_occ["pct_tasks_affected_ceiling"] - merged_occ["pct_tasks_affected_confirmed"]
    )

    # ── 3. Merge all dimensions ───────────────────────────────────────────────

    print("== Merging SKA + adoption gap + risk tiers ==")
    emp_lookup = _get_emp_lookup()
    risk_df = _load_risk_tiers()
    if risk_df.empty:
        print("  WARNING: risk scores not found — risk tier will be 'unknown'")

    df = merged_occ.merge(
        occ_gaps[["title_current", "overall_pct"]].rename(columns={"overall_pct": "ska_overall_pct"}),
        on="title_current", how="left",
    )
    df = df.merge(emp_lookup, on="title_current", how="left")
    if not risk_df.empty:
        df = df.merge(risk_df, on="title_current", how="left")
    else:
        df["risk_tier"] = "unknown"
        df["risk_score"] = np.nan

    df["risk_tier"] = df["risk_tier"].fillna("unknown")
    df["emp_nat"] = df["emp_nat"].fillna(0.0)
    df = df.dropna(subset=["ska_overall_pct", "adoption_gap"])
    print(f"  Combined dataset: {len(df)} occupations")

    # ── 4. Assign quadrants ───────────────────────────────────────────────────

    gap_median = df["adoption_gap"].median()
    print(f"  SKA threshold: {SKA_THRESHOLD}% (natural) | Adoption gap median: {gap_median:.1f}pp")

    df["quadrant"] = df.apply(
        lambda r: _assign_quadrant(r["ska_overall_pct"], r["adoption_gap"], gap_median),
        axis=1,
    )

    # Opportunity score: for Q1 occupations, workers × adoption_gap
    df["opportunity_score"] = df["workers_affected_confirmed"] * df["adoption_gap"]

    # Save full table
    save_csv(
        df.sort_values("opportunity_score", ascending=False),
        results / "opportunity_scores.csv",
    )

    # Q1 occupations
    q1 = df[df["quadrant"] == "Q1: Automation opportunity"].copy()
    save_csv(
        q1.sort_values("opportunity_score", ascending=False),
        results / "q1_occupations.csv",
    )
    print(f"  Q1 (automation opportunity): {len(q1)} occupations, "
          f"{format_workers(q1['emp_nat'].sum())} workers")

    # Q1 ∩ high risk = transformation signal
    q1_high = q1[q1["risk_tier"] == "high"].copy()
    save_csv(
        q1_high.sort_values("opportunity_score", ascending=False),
        results / "q1_transformation_signal.csv",
    )
    print(f"  Q1 + high risk (transformation signal): {len(q1_high)} occupations")

    # Q3 occupations (tool gap: humans lead, big adoption gap)
    q3 = df[df["quadrant"] == "Q3: Tool gap"].copy()
    save_csv(q3.sort_values("opportunity_score", ascending=False), results / "q3_tool_gap.csv")

    # Quadrant summary by major
    quad_summary = (
        df.groupby(["major", "quadrant"])
        .agg(n_occs=("title_current", "count"), emp=("emp_nat", "sum"))
        .reset_index()
    )
    save_csv(quad_summary, results / "quadrant_summary.csv")

    # Sector-level means
    sector_df = (
        df.groupby("major")
        .agg(
            mean_ska_pct=("ska_overall_pct", "mean"),
            mean_adoption_gap=("adoption_gap", "mean"),
            total_workers=("emp_nat", "sum"),
            n_occs=("title_current", "count"),
        )
        .reset_index()
    )
    save_csv(sector_df, results / "sector_opportunity.csv")

    # ── 5. Figures ────────────────────────────────────────────────────────────

    print("\n== Building figures ==")

    # Opportunity scatter
    fig = _opportunity_scatter(df)
    save_figure(fig, fig_dir / "opportunity_scatter.png")

    # Quadrant distribution by major
    fig = _quadrant_summary_bar(df)
    save_figure(fig, fig_dir / "opportunity_quadrant_summary.png")

    # Top Q1 occupations
    if not q1.empty:
        fig = _q1_bar(
            q1, "Top Automation Opportunity Occupations (Q1)",
            subtitle=(
                "AI leads on SKA (>100%) + large adoption gap | "
                "Score = workers × adoption gap | "
                f"Adoption gap median: {gap_median:.1f}pp"
            ),
        )
        save_figure(fig, fig_dir / "q1_top_occupations.png")

    # Transformation signal (Q1 + high risk)
    if not q1_high.empty:
        fig = _q1_bar(
            q1_high,
            "Transformation Signal: Q1 + High Risk Occupations",
            subtitle=(
                "AI already leads AND adoption gap is large AND high job transformation risk — "
                "these are where AI adoption may mean structural job change"
            ),
            top_n=20,
        )
        save_figure(fig, fig_dir / "transformation_signal.png")
    else:
        print("  No Q1 + high-risk occupations found")

    # Sector opportunity landscape
    if not sector_df.empty:
        fig = _sector_opportunity_scatter(sector_df)
        save_figure(fig, fig_dir / "sector_opportunity.png")

    # ── 6. Copy key figures ───────────────────────────────────────────────────

    print("\n== Copying key figures ==")
    key_figs = [
        "opportunity_scatter.png",
        "opportunity_quadrant_summary.png",
        "q1_top_occupations.png",
        "transformation_signal.png",
        "sector_opportunity.png",
    ]
    for fname in key_figs:
        src = fig_dir / fname
        if src.exists():
            shutil.copy2(src, committed_figs / fname)
            print(f"  Copied {fname}")
        else:
            print(f"  SKIP: {fname}")

    # ── 7. Generate PDF ───────────────────────────────────────────────────────

    print("\n== Generating PDF ==")
    md_path = HERE / "automation_opportunity_report.md"
    pdf_path = results / "automation_opportunity_report.pdf"
    if md_path.exists():
        generate_pdf(md_path, pdf_path)
        print(f"  Saved {pdf_path.name}")
    else:
        print(f"  SKIP — report not yet written")

    print("\nDone.")


if __name__ == "__main__":
    main()
