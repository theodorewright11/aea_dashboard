"""
run.py — Job Exposure: Audience Framing

How do job exposure findings frame for different audiences?

Two sub-analyses:

1. Hidden at-risk jobs
   Which occupations share a skill+knowledge profile with high-exposure jobs
   but currently have low exposure themselves? These are the next wave of
   disruption: AI can already reach their skill set but hasn't yet penetrated
   their actual task load via confirmed usage.

2. Dominant skill domains in high-exposure / low-outlook occupations
   Which skills and knowledge domains are most concentrated in jobs that are
   both highly exposed AND have below-average labor market outlook (DWS 2 or 3)?
   These are the areas with the greatest urgency for workforce development.

Uses Skills + Knowledge (importance >= 3). Abilities excluded.
Primary config: all_ceiling.

Run from project root:
    venv/Scripts/python -m analysis.questions.job_exposure.audience_framing.run
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.metrics.pairwise import cosine_similarity  # type: ignore[import]

from analysis.config import (
    ANALYSIS_CONFIGS,
    ANALYSIS_CONFIG_LABELS,
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.data.compute_ska import compute_ska, load_ska_data
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent

PRIMARY_KEY = "all_ceiling"
AT_RISK_OUTLOOK = {2, 3}   # DWS rating: below average (1 = good outcome / low wages)
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


# ── Sub-analysis 1: Hidden at-risk jobs ───────────────────────────────────────

def _compute_skill_profile_matrix(
    result,
    types: tuple[str, ...] = ("skills", "knowledge"),
) -> pd.DataFrame:
    """
    Build occ × element matrix (occ_score values) for cosine similarity.
    Only elements that appear in at least 10% of occupations are included.
    Missing combinations filled with 0.
    """
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

    # Drop very sparse elements (present in <10% of occs)
    min_occs = len(matrix) * 0.10
    matrix = matrix.loc[:, (matrix > 0).sum() >= min_occs]

    return matrix


def _compute_cosine_similarity_to_profile(
    matrix: pd.DataFrame,
    profile: pd.Series,
) -> pd.Series:
    """Cosine similarity of each occupation's vector to a reference profile vector."""
    if matrix.empty or profile.empty:
        return pd.Series(dtype=float)

    # Align columns
    all_cols = matrix.columns.union(profile.index)
    mat = matrix.reindex(columns=all_cols, fill_value=0.0)
    ref = profile.reindex(all_cols, fill_value=0.0).values.reshape(1, -1)

    sims = cosine_similarity(mat.values, ref).flatten()
    return pd.Series(sims, index=mat.index, name="skill_similarity")


# ── Figures ───────────────────────────────────────────────────────────────────

def _hidden_at_risk_scatter(
    df: pd.DataFrame,
    exposure_median: float,
    similarity_median: float,
) -> go.Figure:
    """
    Scatter: pct (x) vs skill_similarity (y).
    Quadrant of interest: low pct + high similarity = hidden at-risk.
    """
    fig = go.Figure()

    # Color by quadrant
    def quadrant(row: pd.Series) -> str:
        hi_sim = row["skill_similarity"] >= similarity_median
        hi_exp = row["pct"] >= exposure_median
        if hi_sim and not hi_exp:
            return "Hidden at-risk"
        if hi_sim and hi_exp:
            return "High exposure (expected)"
        if not hi_sim and hi_exp:
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
            x=sub["pct"], y=sub["skill_similarity"],
            mode="markers", name=quad,
            marker=dict(color=color, size=6, opacity=0.6,
                        line=dict(width=0.5, color=COLORS["bg"])),
            text=sub["title_current"],
            hovertemplate="<b>%{text}</b><br>Exposure: %{x:.1f}%<br>Similarity: %{y:.3f}<extra></extra>",
        ))

    fig.add_vline(x=exposure_median, line_dash="dot", line_color=COLORS["border"], line_width=1,
                  annotation_text="Median exposure", annotation_position="top right",
                  annotation_font=dict(size=9, color=COLORS["muted"], family=FONT_FAMILY))
    fig.add_hline(y=similarity_median, line_dash="dot", line_color=COLORS["border"], line_width=1,
                  annotation_text="Median similarity", annotation_position="right",
                  annotation_font=dict(size=9, color=COLORS["muted"], family=FONT_FAMILY))

    style_figure(
        fig,
        "Hidden At-Risk Jobs: Similar to High-Exposure Profiles but Not Yet Exposed",
        subtitle="Top-left quadrant = similar skill profile to high-exposure jobs but low current exposure",
        x_title="% Tasks Affected (all_ceiling)",
        y_title="Cosine Similarity to High-Exposure Profile",
        height=700, width=950, show_legend=True,
    )
    fig.update_layout(legend=dict(
        orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5,
        font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
    ))
    return fig


def _dominant_elements_bar(element_agg: pd.DataFrame, n: int = TOP_N_ELEMENTS) -> go.Figure:
    """Horizontal bar: top N elements by avg importance×level in high-exp/low-outlook occs."""
    top = element_agg.nlargest(n, "avg_score").sort_values("avg_score", ascending=True)
    labels = [f"{v:.2f}  ({t})" for v, t in zip(top["avg_score"], top["type"])]
    colors = [COLORS["negative"] if t == "knowledge" else COLORS["primary"]
               for t in top["type"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top["element_name"], x=top["avg_score"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=labels, textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    chart_h = max(400, n * 38 + 150)
    style_figure(
        fig,
        "Dominant Skill & Knowledge Domains in High-Exposure / Low-Outlook Occupations",
        subtitle="Avg importance × level (importance ≥ 3) | Blue = skill | Red = knowledge",
        x_title=None, height=chart_h, show_legend=False,
    )
    fig.update_layout(
        margin=dict(l=20, r=100),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False, zeroline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        bargap=0.25,
    )
    return fig


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    fig_dir = results / "figures"
    print("Audience Framing -- generating outputs...\n")

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

    # ── Build occ pct table ───────────────────────────────────────────────────
    occ_pct = pd.DataFrame({
        "title_current": pct_primary.index,
        "pct": pct_primary.values,
    })
    occ_pct = occ_pct.merge(struct, on="title_current", how="left")
    exposure_median = occ_pct["pct"].median()

    # ════════════════════════════════════════════════════════════════════════
    # Sub-analysis 1: Hidden at-risk jobs
    # ════════════════════════════════════════════════════════════════════════
    print("\n== Sub-analysis 1: Hidden at-risk jobs ==")

    # Build skill+knowledge profile matrix
    print("Building skill profile matrix (skills + knowledge)...")
    profile_matrix = _compute_skill_profile_matrix(result_primary)
    print(f"  Matrix shape: {profile_matrix.shape}")

    if profile_matrix.empty:
        print("  WARNING: profile matrix empty -- skipping sub-analysis 1")
    else:
        # Average profile of high-exposure occupations
        high_exp_occs = occ_pct[occ_pct["pct"] >= exposure_median]["title_current"].tolist()
        high_exp_matrix = profile_matrix.reindex(
            [o for o in high_exp_occs if o in profile_matrix.index]
        )
        high_exp_profile = high_exp_matrix.mean()
        print(f"  High-exposure occs for profile: {len(high_exp_matrix)}")

        # Cosine similarity for all occs
        similarity = _compute_cosine_similarity_to_profile(profile_matrix, high_exp_profile)
        similarity_median = similarity.median()
        print(f"  Similarity range: {similarity.min():.3f} – {similarity.max():.3f}")
        print(f"  Similarity median: {similarity_median:.3f}")

        # Build output table
        sim_df = occ_pct.copy()
        sim_df["skill_similarity"] = sim_df["title_current"].map(similarity)
        sim_df = sim_df.dropna(subset=["skill_similarity"])

        save_csv(sim_df[["title_current", "pct", "skill_similarity", "major",
                          "job_zone", "outlook", "emp_nat"]].sort_values(
            "skill_similarity", ascending=False
        ), results / "skill_profile_similarity.csv")
        print("Saved skill_profile_similarity.csv")

        # Hidden at-risk: low exposure but high similarity
        hidden = sim_df[
            (sim_df["pct"] < exposure_median) &
            (sim_df["skill_similarity"] >= similarity_median)
        ].sort_values("skill_similarity", ascending=False)
        save_csv(hidden, results / "hidden_at_risk_occs.csv")
        print(f"Saved hidden_at_risk_occs.csv ({len(hidden)} occupations)")

        # Figure
        fig = _hidden_at_risk_scatter(sim_df, exposure_median, similarity_median)
        save_figure(fig, fig_dir / "hidden_at_risk_scatter.png")
        print("  hidden_at_risk_scatter.png")

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
        # Aggregate skill+knowledge scores for target occs
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

    # ── Copy key figures ──────────────────────────────────────────────────────
    committed = HERE / "figures"
    committed.mkdir(exist_ok=True)
    for fname in ["hidden_at_risk_scatter.png", "dominant_elements_bar.png"]:
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
