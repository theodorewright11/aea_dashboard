"""
run.py — Job Exposure: Audience Framing (Policy Urgency)

How do job exposure findings frame for different audiences?
Where is policy intervention most urgent?

Three sub-analyses:

1. Hidden at-risk jobs (projection method)
   Uses projection onto the AI capabilities vector AND projection onto the
   average skill profile of the top-25% highest-exposure jobs. Projection
   captures both direction and magnitude (unlike cosine similarity which
   only captures direction). Occupations with high projection but low current
   exposure are the "next wave."

2. Dominant skill domains in high-exposure / low-outlook occupations
   Which skills AND knowledge domains are most concentrated in jobs that are
   both highly exposed AND have below-average labor market outlook?

3. Trend analysis
   Tracks which hidden-at-risk occupations are seeing rising exposure.

Uses Skills + Knowledge + (newly added) Skills for broader coverage.
Primary config: all_confirmed. Ceiling comparison included.

Run from project root:
    venv/Scripts/python -m analysis.questions.job_exposure.audience_framing.run
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
from analysis.data.compute_ska import compute_ska, load_ska_data
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    format_workers,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent

PRIMARY_KEY = "all_confirmed"
CEILING_KEY = "all_ceiling"
AT_RISK_OUTLOOK = {2, 3}
TOP_N_ELEMENTS = 20


def _get_structural_data() -> pd.DataFrame:
    from backend.compute import get_explorer_occupations

    rows = []
    for occ in get_explorer_occupations():
        rows.append({
            "title_current": occ["title_current"],
            "emp_nat": occ.get("emp") or 0,
            "major": occ.get("major", ""),
            "job_zone": occ.get("job_zone"),
            "outlook": occ.get("dws_star_rating"),
        })
    return pd.DataFrame(rows)


# ── Projection-based analysis ─────────────────────────────────────────────────

def _compute_skill_profile_matrix(
    result,
    types: tuple[str, ...] = ("skills", "knowledge"),
) -> pd.DataFrame:
    """Build occ × element matrix (occ_score values) for projection."""
    rows = []
    for type_name in types:
        elem_df = result.occ_element_scores.get(type_name, pd.DataFrame())
        if elem_df.empty:
            continue
        rows.append(elem_df[["title_current", "element_name", "occ_score"]].copy())

    if not rows:
        return pd.DataFrame()

    combined = pd.concat(rows, ignore_index=True)
    matrix = combined.pivot_table(
        index="title_current", columns="element_name",
        values="occ_score", aggfunc="mean", fill_value=0.0,
    )

    # Drop very sparse elements
    min_occs = len(matrix) * 0.10
    matrix = matrix.loc[:, (matrix > 0).sum() >= min_occs]
    return matrix


def _compute_projection(
    matrix: pd.DataFrame,
    target_vector: pd.Series,
) -> pd.Series:
    """
    Compute scalar projection of each occ's vector onto a target vector.
    Projection = (occ · target) / ||target||
    This captures both direction AND magnitude.
    """
    if matrix.empty or target_vector.empty:
        return pd.Series(dtype=float)

    all_cols = matrix.columns.union(target_vector.index)
    mat = matrix.reindex(columns=all_cols, fill_value=0.0)
    target = target_vector.reindex(all_cols, fill_value=0.0)

    target_norm = np.linalg.norm(target.values)
    if target_norm == 0:
        return pd.Series(0.0, index=mat.index)

    projections = mat.values @ target.values / target_norm
    return pd.Series(projections, index=mat.index, name="projection")


# ── Figures ───────────────────────────────────────────────────────────────────

def _hidden_at_risk_scatter(
    df: pd.DataFrame,
    exposure_median: float,
    projection_median: float,
    projection_col: str = "ai_projection",
    projection_label: str = "AI Capability Projection",
) -> go.Figure:
    """Scatter: pct (x) vs projection (y). Top-left = hidden at-risk."""
    fig = go.Figure()

    def quadrant(row: pd.Series) -> str:
        hi_proj = row[projection_col] >= projection_median
        hi_exp = row["pct"] >= exposure_median
        if hi_proj and not hi_exp:
            return "Hidden at-risk"
        if hi_proj and hi_exp:
            return "High exposure (expected)"
        if not hi_proj and hi_exp:
            return "High exposure (different profile)"
        return "Low exposure (safe)"

    df = df.copy()
    df["quadrant"] = df.apply(quadrant, axis=1)

    quad_colors = {
        "Hidden at-risk": COLORS["accent"],
        "High exposure (expected)": COLORS["negative"],
        "High exposure (different profile)": COLORS["muted"],
        "Low exposure (safe)": COLORS["primary"],
    }

    for quad, color in quad_colors.items():
        sub = df[df["quadrant"] == quad]
        fig.add_trace(go.Scatter(
            x=sub["pct"], y=sub[projection_col],
            mode="markers", name=quad,
            marker=dict(color=color, size=6, opacity=0.6,
                        line=dict(width=0.5, color=COLORS["bg"])),
            text=sub["title_current"],
            hovertemplate=f"<b>%{{text}}</b><br>Exposure: %{{x:.1f}}%<br>{projection_label}: %{{y:.2f}}<extra></extra>",
        ))

    fig.add_vline(x=exposure_median, line_dash="dot", line_color=COLORS["border"], line_width=1,
                  annotation_text="Median exposure", annotation_position="top right",
                  annotation_font=dict(size=9, color=COLORS["muted"], family=FONT_FAMILY))
    fig.add_hline(y=projection_median, line_dash="dot", line_color=COLORS["border"], line_width=1,
                  annotation_text="Median projection", annotation_position="right",
                  annotation_font=dict(size=9, color=COLORS["muted"], family=FONT_FAMILY))

    style_figure(
        fig,
        f"Hidden At-Risk Jobs — {projection_label}",
        subtitle="Top-left quadrant = high projection onto AI/exposure profile but low current exposure",
        x_title=f"% Tasks Affected ({ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]})",
        y_title=projection_label,
        height=700, width=950, show_legend=True,
    )
    fig.update_layout(
        margin=dict(l=60, r=40, t=80, b=120),
        legend=dict(
            orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        ),
    )
    return fig


def _dominant_elements_bar(element_agg: pd.DataFrame, n: int = TOP_N_ELEMENTS) -> go.Figure:
    """Horizontal bar: top N elements in high-exp/low-outlook occs."""
    top = element_agg.nlargest(n, "avg_score").sort_values("avg_score", ascending=True)
    labels = [f"{v:.2f}  ({t})" for v, t in zip(top["avg_score"], top["type"])]
    colors = [
        COLORS["negative"] if t == "knowledge" else COLORS["primary"]
        for t in top["type"]
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top["element_name"], x=top["avg_score"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=labels, textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    chart_h = max(400, n * 38 + 200)
    style_figure(
        fig,
        "Dominant Domains in High-Exposure / Low-Outlook Occupations",
        subtitle="Avg importance × level (importance ≥ 3) | Blue = skill | Red = knowledge",
        x_title=None, height=chart_h, show_legend=False,
    )
    fig.update_layout(
        margin=dict(l=20, r=120, t=80, b=100),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False, zeroline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        bargap=0.25,
    )
    return fig


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    fig_dir = results / "figures"
    print("Audience Framing / Policy Urgency -- generating outputs...\n")

    # ── Structural data ───────────────────────────────────────────────────────
    print("Loading structural data...")
    struct = _get_structural_data()

    # ── SKA ───────────────────────────────────────────────────────────────────
    print("Loading SKA data...")
    ska_data = load_ska_data()

    print(f"Computing pct for {PRIMARY_KEY}...")
    pct_primary = get_pct_tasks_affected(ANALYSIS_CONFIGS[PRIMARY_KEY])

    print("Computing SKA gaps...")
    result_primary = compute_ska(pct_primary, ska_data)

    # Ceiling for comparison
    print(f"Computing pct for ceiling ({CEILING_KEY})...")
    pct_ceiling = get_pct_tasks_affected(ANALYSIS_CONFIGS[CEILING_KEY])
    result_ceiling = compute_ska(pct_ceiling, ska_data)

    # ── Build occ pct table ───────────────────────────────────────────────────
    occ_pct = pd.DataFrame({
        "title_current": pct_primary.index,
        "pct": pct_primary.values,
    })
    occ_pct["pct_ceiling"] = occ_pct["title_current"].map(pct_ceiling).fillna(0)
    occ_pct = occ_pct.merge(struct, on="title_current", how="left")
    exposure_median = occ_pct["pct"].median()

    # ════════════════════════════════════════════════════════════════════════
    # Sub-analysis 1: Hidden at-risk jobs (projection method)
    # ════════════════════════════════════════════════════════════════════════
    print("\n== Sub-analysis 1: Hidden at-risk jobs (projection) ==")

    # Build skill+knowledge profile matrix (now includes skills too)
    print("Building skill profile matrix (skills + knowledge)...")
    profile_matrix = _compute_skill_profile_matrix(result_primary, types=("skills", "knowledge"))
    print(f"  Matrix shape: {profile_matrix.shape}")

    if profile_matrix.empty:
        print("  WARNING: profile matrix empty -- skipping sub-analysis 1")
    else:
        # --- Projection 1: onto AI capabilities vector ---
        # AI capability = 95th percentile of ai_product per element (from SKA)
        ai_cap = result_primary.ai_capability.copy()
        # Deduplicate: if same element appears in multiple types, take the max
        ai_cap_vec = ai_cap.groupby("element_name")["ai_score"].max()
        ai_projection = _compute_projection(profile_matrix, ai_cap_vec)
        ai_proj_median = ai_projection.median()
        print(f"  AI projection range: {ai_projection.min():.2f} – {ai_projection.max():.2f}")
        print(f"  AI projection median: {ai_proj_median:.2f}")

        # --- Projection 2: onto top-25% exposed jobs' avg profile ---
        pct_75 = occ_pct["pct"].quantile(0.75)
        top_exposed_occs = occ_pct[occ_pct["pct"] >= pct_75]["title_current"].tolist()
        top_exposed_matrix = profile_matrix.reindex(
            [o for o in top_exposed_occs if o in profile_matrix.index]
        )
        top_exposed_profile = top_exposed_matrix.mean()
        exp_projection = _compute_projection(profile_matrix, top_exposed_profile)
        exp_proj_median = exp_projection.median()
        print(f"  Exposure projection range: {exp_projection.min():.2f} – {exp_projection.max():.2f}")

        # Build output table
        sim_df = occ_pct.copy()
        sim_df["ai_projection"] = sim_df["title_current"].map(ai_projection)
        sim_df["exposure_projection"] = sim_df["title_current"].map(exp_projection)
        sim_df = sim_df.dropna(subset=["ai_projection"])

        save_csv(sim_df[["title_current", "pct", "pct_ceiling", "ai_projection",
                          "exposure_projection", "major", "job_zone", "outlook",
                          "emp_nat"]].sort_values("ai_projection", ascending=False),
                 results / "projection_similarity.csv")
        print("Saved projection_similarity.csv")

        # Hidden at-risk: low exposure but high projection
        hidden_ai = sim_df[
            (sim_df["pct"] < exposure_median) &
            (sim_df["ai_projection"] >= ai_proj_median)
        ].sort_values("ai_projection", ascending=False)
        save_csv(hidden_ai, results / "hidden_at_risk_occs.csv")
        print(f"Saved hidden_at_risk_occs.csv ({len(hidden_ai)} occupations)")

        hidden_exp = sim_df[
            (sim_df["pct"] < exposure_median) &
            (sim_df["exposure_projection"] >= exp_proj_median)
        ].sort_values("exposure_projection", ascending=False)
        save_csv(hidden_exp, results / "hidden_at_risk_exp_projection.csv")
        print(f"Saved hidden_at_risk_exp_projection.csv ({len(hidden_exp)} occupations)")

        # Figures: both projection methods
        fig = _hidden_at_risk_scatter(
            sim_df, exposure_median, ai_proj_median,
            projection_col="ai_projection",
            projection_label="Projection onto AI Capabilities",
        )
        save_figure(fig, fig_dir / "hidden_at_risk_ai_projection.png")
        print("  hidden_at_risk_ai_projection.png")

        fig = _hidden_at_risk_scatter(
            sim_df, exposure_median, exp_proj_median,
            projection_col="exposure_projection",
            projection_label="Projection onto Top-25% Exposed Profile",
        )
        save_figure(fig, fig_dir / "hidden_at_risk_exp_projection.png")
        print("  hidden_at_risk_exp_projection.png")

    # ════════════════════════════════════════════════════════════════════════
    # Sub-analysis 2: Dominant elements in high-exposure / low-outlook
    # ════════════════════════════════════════════════════════════════════════
    print("\n== Sub-analysis 2: Dominant elements in high-exposure / low-outlook ==")

    target_occs = occ_pct[
        (occ_pct["pct"] >= exposure_median) &
        (occ_pct["outlook"].apply(lambda o: pd.notna(o) and int(o) in AT_RISK_OUTLOOK))
    ]["title_current"].tolist()
    print(f"  Target occupations (high exposure + outlook 2-3): {len(target_occs)}")

    if not target_occs:
        print("  WARNING: no occupations match criteria -- skipping sub-analysis 2")
    else:
        # Include skills alongside knowledge (both matter for policy)
        agg_rows = []
        for type_name in ("skills", "knowledge"):
            elem_df = result_primary.occ_element_scores.get(type_name, pd.DataFrame())
            if elem_df.empty:
                continue
            subset = elem_df[elem_df["title_current"].isin(target_occs)]
            agg = (
                subset.groupby("element_name")["occ_score"]
                .mean()
                .reset_index()
                .rename(columns={"occ_score": "avg_score"})
            )
            agg["type"] = type_name
            agg_rows.append(agg)

        if agg_rows:
            element_agg = pd.concat(agg_rows, ignore_index=True)
            save_csv(element_agg.sort_values("avg_score", ascending=False),
                     results / "dominant_elements_high_exp_low_outlook.csv")
            print(f"Saved dominant_elements_high_exp_low_outlook.csv ({len(element_agg)} elements)")

            fig = _dominant_elements_bar(element_agg)
            save_figure(fig, fig_dir / "dominant_elements_bar.png")
            print("  dominant_elements_bar.png")

    # ════════════════════════════════════════════════════════════════════════
    # Sub-analysis 3: Trend analysis for hidden at-risk occupations
    # ════════════════════════════════════════════════════════════════════════
    print("\n== Sub-analysis 3: Trend analysis ==")

    if not profile_matrix.empty and "hidden_ai" in dir() and not hidden_ai.empty:
        # Track exposure growth for hidden at-risk occupations
        hidden_titles = hidden_ai["title_current"].tolist()
        trend_rows = []
        for config_key, series in ANALYSIS_CONFIG_SERIES.items():
            if len(series) < 2:
                continue
            pct_first = get_pct_tasks_affected(series[0])
            pct_last = get_pct_tasks_affected(series[-1])
            for title in hidden_titles:
                first = pct_first.get(title, 0)
                last = pct_last.get(title, 0)
                trend_rows.append({
                    "title_current": title,
                    "config": config_key,
                    "pct_first": first,
                    "pct_last": last,
                    "pct_delta": last - first,
                })
        if trend_rows:
            hidden_trends = pd.DataFrame(trend_rows)
            save_csv(hidden_trends, results / "hidden_at_risk_trends.csv")
            print(f"Saved hidden_at_risk_trends.csv")

            # How many hidden at-risk are seeing rising exposure?
            rising = hidden_trends[
                (hidden_trends["config"] == PRIMARY_KEY) &
                (hidden_trends["pct_delta"] > 0)
            ]
            print(f"  {len(rising)}/{len(hidden_titles)} hidden at-risk occs "
                  f"with rising exposure ({PRIMARY_KEY})")

    # ── Copy key figures ──────────────────────────────────────────────────────
    committed = HERE / "figures"
    committed.mkdir(exist_ok=True)
    for fname in ["hidden_at_risk_ai_projection.png",
                  "hidden_at_risk_exp_projection.png",
                  "dominant_elements_bar.png"]:
        src = fig_dir / fname
        if src.exists():
            shutil.copy2(src, committed / fname)

    # ── PDF ───────────────────────────────────────────────────────────────────
    from analysis.utils import generate_pdf
    md_path = HERE / "audience_framing_report.md"
    if md_path.exists():
        generate_pdf(md_path, results / "audience_framing_report.pdf")

    print("\nDone.")


if __name__ == "__main__":
    main()
