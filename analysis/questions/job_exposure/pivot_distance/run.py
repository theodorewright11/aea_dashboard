"""
run.py — Job Exposure: Pivot Distance

How costly is it for a worker in a high-risk occupation to reskill into a
low-risk occupation in the same job zone?

Method
------
For each job zone (1–5):
  1. Select top 10 highest-risk occupations (by risk_score from job_risk_scoring)
  2. Select bottom 10 lowest-risk occupations (by risk_score)
  3. Build average Skills + Knowledge profile for each group
     (mean importance × level per element, importance >= 3)
  4. Pivot cost per element = max(0, low_risk_avg_score − high_risk_avg_score)
     (the skill "distance" the high-risk worker needs to close)
  5. Total pivot cost = sum of element pivot costs for that zone

Uses Skills + Knowledge only (abilities excluded — less trainable).
Primary config: all_confirmed. Ceiling comparison included.

Actionable additions:
  - Per-zone: which specific elements are the biggest cost drivers
  - Cross-reference with worker_resilience tips: elements where AI can help
    close the gap vs ones that need genuine human learning

Run from project root:
    venv/Scripts/python -m analysis.questions.job_exposure.pivot_distance.run
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
    COLORS,
    FONT_FAMILY,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
RISK_SCORING_RESULTS = HERE.parent / "job_risk_scoring" / "results"
PIVOT_INPUTS_FILE = RISK_SCORING_RESULTS / "pivot_distance_inputs.csv"

PRIMARY_KEY = "all_confirmed"
CEILING_KEY = "all_ceiling"
PIVOT_N = 10
IMPORTANCE_THRESHOLD = 3.0


def _get_structural_data() -> pd.DataFrame:
    """Return DataFrame: title_current, job_zone, outlook, emp_nat, major."""
    from backend.compute import get_explorer_occupations

    rows = []
    for occ in get_explorer_occupations():
        rows.append({
            "title_current": occ["title_current"],
            "emp_nat": occ.get("emp") or 0,
            "major": occ.get("major", ""),
            "job_zone": occ.get("job_zone"),
        })
    return pd.DataFrame(rows)


def _build_occ_ska_profile(
    occ_list: list[str],
    ska_data: SKAData,
    pct: pd.Series,
    types: tuple[str, ...] = ("skills", "knowledge"),
) -> pd.DataFrame:
    """Build average profile (element_name → mean_occ_score) for a list of occupations."""
    result = compute_ska(pct, ska_data)
    rows = []
    for type_name in types:
        elem_df = result.occ_element_scores.get(type_name, pd.DataFrame())
        if elem_df.empty:
            continue
        subset = elem_df[elem_df["title_current"].isin(occ_list)]
        agg = (
            subset.groupby("element_name").agg(
                avg_score=("occ_score", "mean"),
                ai_score=("ai_score", "mean"),
            ).reset_index()
        )
        agg["type"] = type_name
        rows.append(agg)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(
        columns=["element_name", "avg_score", "ai_score", "type"]
    )


def _compute_pivot_cost(
    high_profile: pd.DataFrame,
    low_profile: pd.DataFrame,
) -> tuple[pd.DataFrame, float]:
    """Compute per-element pivot cost and total pivot cost."""
    high_dedup = high_profile.drop_duplicates(subset="element_name")
    low_dedup = low_profile.drop_duplicates(subset="element_name")
    high_idx = high_dedup.set_index("element_name")["avg_score"]
    low_idx = low_dedup.set_index("element_name")["avg_score"]
    type_idx = low_dedup.set_index("element_name")["type"]

    # AI score from low-risk profile (to see if AI can help)
    ai_idx = low_dedup.set_index("element_name").get("ai_score", pd.Series(dtype=float))

    all_elements = low_idx.index.union(high_idx.index)

    rows = []
    for elem in all_elements:
        low_score = float(low_idx.get(elem, 0.0))
        high_score = float(high_idx.get(elem, 0.0))
        cost = max(0.0, low_score - high_score)
        elem_type = type_idx.get(elem, "unknown")
        if isinstance(elem_type, pd.Series):
            elem_type = elem_type.iloc[0]
        ai_score = float(ai_idx.get(elem, 0.0)) if not ai_idx.empty else 0.0
        # Can AI help close this gap?
        ai_can_help = ai_score > high_score if cost > 0 else False
        rows.append({
            "element_name": elem,
            "type": elem_type,
            "high_risk_avg_score": round(high_score, 3),
            "low_risk_avg_score": round(low_score, 3),
            "ai_score": round(ai_score, 3),
            "pivot_cost": round(cost, 3),
            "ai_can_help": ai_can_help,
        })
    element_costs = pd.DataFrame(rows).sort_values("pivot_cost", ascending=False)
    total = element_costs["pivot_cost"].sum()
    return element_costs, total


# ── Figures ───────────────────────────────────────────────────────────────────

def _pivot_cost_by_zone_bar(zone_summary: pd.DataFrame) -> go.Figure:
    """Bar: total pivot cost per job zone."""
    zone_summary = zone_summary.sort_values("job_zone")
    labels = [f"{c:.1f}" for c in zone_summary["total_pivot_cost"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=zone_summary["job_zone"].astype(str).tolist(),
        y=zone_summary["total_pivot_cost"],
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=labels, textposition="outside",
        textfont=dict(size=12, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(
        fig,
        "Reskilling Cost by Job Zone",
        subtitle=(
            "Total skill+knowledge gap to close: top-10 high-risk → bottom-10 low-risk "
            f"per zone | {ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]}"
        ),
        x_title="Job Zone", y_title="Total Pivot Cost (sum of element gaps)",
        height=550, width=750, show_legend=False,
    )
    fig.update_layout(
        margin=dict(l=60, r=40, t=80, b=100),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=COLORS["border"]),
        bargap=0.35,
    )
    return fig


def _element_cost_heatmap(
    element_costs_by_zone: list[tuple[int, pd.DataFrame]],
    top_n: int = 20,
) -> go.Figure:
    """Heatmap: element × job_zone pivot cost."""
    all_costs = pd.concat([df.assign(zone=z) for z, df in element_costs_by_zone])
    top_elements = (
        all_costs.groupby("element_name")["pivot_cost"]
        .mean()
        .nlargest(top_n)
        .index.tolist()
    )

    pivot = pd.DataFrame(index=top_elements)
    for zone, df in element_costs_by_zone:
        zone_costs = df.set_index("element_name")["pivot_cost"]
        pivot[f"Zone {zone}"] = zone_costs.reindex(top_elements, fill_value=0)

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0, "#f5f5f0"], [1.0, COLORS["negative"]]],
        text=np.round(pivot.values, 2),
        texttemplate="%{text:.1f}",
        hovertemplate="<b>%{y}</b><br>%{x}<br>Cost: %{z:.2f}<extra></extra>",
    ))
    chart_h = max(500, top_n * 22 + 250)
    style_figure(
        fig,
        "Which Skills Drive Reskilling Cost Across Job Zones?",
        subtitle="Top 20 elements by average pivot cost | Higher = more to learn",
        x_title=None, y_title=None, height=chart_h, width=750, show_legend=False,
    )
    fig.update_layout(
        margin=dict(l=20, r=40, t=80, b=100),
        yaxis=dict(autorange="reversed", tickfont=dict(size=9, family=FONT_FAMILY)),
        xaxis=dict(tickfont=dict(size=10, family=FONT_FAMILY)),
    )
    return fig


def _ai_assisted_reskilling_bar(element_costs_all: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Bar chart: elements with highest pivot cost where AI can help close the gap."""
    ai_helped = element_costs_all[element_costs_all["ai_can_help"]].copy()
    if ai_helped.empty:
        return go.Figure()

    agg = (
        ai_helped.groupby("element_name")
        .agg(avg_cost=("pivot_cost", "mean"), n_zones=("job_zone", "nunique"))
        .reset_index()
        .nlargest(top_n, "avg_cost")
        .sort_values("avg_cost", ascending=True)
    )

    labels = [f"{v:.1f} (in {n} zones)" for v, n in zip(agg["avg_cost"], agg["n_zones"])]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=agg["element_name"], x=agg["avg_cost"], orientation="h",
        marker=dict(color=COLORS["secondary"], line=dict(width=0)),
        text=labels, textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    chart_h = max(400, len(agg) * 38 + 200)
    style_figure(
        fig,
        "Reskilling Gaps Where AI Can Help",
        subtitle="Elements with high pivot cost where AI capability exceeds the high-risk worker's current level",
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
    print("Pivot Distance -- generating outputs...\n")

    # ── Load risk scores ──────────────────────────────────────────────────────
    if not PIVOT_INPUTS_FILE.exists():
        raise FileNotFoundError(
            f"pivot_distance_inputs.csv not found at {PIVOT_INPUTS_FILE}. "
            "Run job_risk_scoring first:\n"
            "  venv/Scripts/python -m analysis.questions.job_exposure.job_risk_scoring.run"
        )
    pivot_inputs = pd.read_csv(PIVOT_INPUTS_FILE)
    print(f"Loaded pivot_distance_inputs.csv ({len(pivot_inputs)} rows)\n")

    struct = _get_structural_data()

    # ── SKA data + pct ───────────────────────────────────────────────────────
    print("Loading SKA data...")
    ska_data = load_ska_data()

    print(f"Computing pct for {PRIMARY_KEY}...")
    pct_primary = get_pct_tasks_affected(ANALYSIS_CONFIGS[PRIMARY_KEY])

    print(f"Computing pct for ceiling ({CEILING_KEY})...")
    pct_ceiling = get_pct_tasks_affected(ANALYSIS_CONFIGS[CEILING_KEY])

    # ── Per-zone pivot cost ───────────────────────────────────────────────────
    print("\nComputing pivot cost per job zone...")
    zone_summary_rows = []
    element_costs_by_zone: list[tuple[int, pd.DataFrame]] = []
    high_risk_profiles = []
    low_risk_profiles = []
    all_element_costs = []

    for zone in [1, 2, 3, 4, 5]:
        zone_data = pivot_inputs[pivot_inputs["job_zone"] == zone]
        if zone_data.empty:
            print(f"  Zone {zone}: no data -- skipping")
            continue

        high_risk_occs = zone_data[zone_data["group"] == "high_risk"]["title_current"].tolist()
        low_risk_occs = zone_data[zone_data["group"] == "low_risk"]["title_current"].tolist()

        if not high_risk_occs or not low_risk_occs:
            print(f"  Zone {zone}: missing high or low risk occs -- skipping")
            continue

        print(f"  Zone {zone}: {len(high_risk_occs)} high-risk, {len(low_risk_occs)} low-risk occs")

        high_profile = _build_occ_ska_profile(high_risk_occs, ska_data, pct_primary)
        low_profile = _build_occ_ska_profile(low_risk_occs, ska_data, pct_primary)

        element_costs, total_cost = _compute_pivot_cost(high_profile, low_profile)
        element_costs["job_zone"] = zone
        element_costs_by_zone.append((zone, element_costs))
        all_element_costs.append(element_costs)

        # Count elements where AI can help
        n_ai_helped = element_costs["ai_can_help"].sum()
        ai_cost_share = (
            element_costs[element_costs["ai_can_help"]]["pivot_cost"].sum() / total_cost * 100
            if total_cost > 0 else 0
        )

        zone_summary_rows.append({
            "job_zone": zone,
            "n_high_risk": len(high_risk_occs),
            "n_low_risk": len(low_risk_occs),
            "total_pivot_cost": round(total_cost, 2),
            "n_elements_with_cost": len(element_costs[element_costs["pivot_cost"] > 0]),
            "n_elements_ai_can_help": int(n_ai_helped),
            "pct_cost_ai_can_help": round(ai_cost_share, 1),
            "example_high_risk": ", ".join(high_risk_occs[:3]),
            "example_low_risk": ", ".join(low_risk_occs[:3]),
        })

        # Ceiling comparison
        high_profile_ceil = _build_occ_ska_profile(high_risk_occs, ska_data, pct_ceiling)
        low_profile_ceil = _build_occ_ska_profile(low_risk_occs, ska_data, pct_ceiling)
        _, ceiling_cost = _compute_pivot_cost(high_profile_ceil, low_profile_ceil)
        zone_summary_rows[-1]["ceiling_pivot_cost"] = round(ceiling_cost, 2)
        zone_summary_rows[-1]["cost_delta_ceiling"] = round(ceiling_cost - total_cost, 2)

        high_profile["job_zone"] = zone
        high_profile["group"] = "high_risk"
        low_profile["job_zone"] = zone
        low_profile["group"] = "low_risk"
        high_risk_profiles.append(high_profile)
        low_risk_profiles.append(low_profile)

        print(f"    Total pivot cost: {total_cost:.2f} (ceiling: {ceiling_cost:.2f})")

    zone_summary = pd.DataFrame(zone_summary_rows)
    save_csv(zone_summary, results / "pivot_cost_by_zone.csv")
    print("\nSaved pivot_cost_by_zone.csv")

    if element_costs_by_zone:
        all_elem_costs = pd.concat([df.assign(job_zone=z) for z, df in element_costs_by_zone])
        save_csv(all_elem_costs, results / "element_costs_by_zone.csv")
        print("Saved element_costs_by_zone.csv")

    if high_risk_profiles:
        save_csv(pd.concat(high_risk_profiles), results / "high_risk_profiles.csv")
        save_csv(pd.concat(low_risk_profiles), results / "low_risk_profiles.csv")
        print("Saved high/low risk profiles")

    # ── Figures ───────────────────────────────────────────────────────────────
    print("\nGenerating figures...")

    if not zone_summary.empty:
        fig = _pivot_cost_by_zone_bar(zone_summary)
        save_figure(fig, fig_dir / "pivot_cost_by_zone.png")
        print("  pivot_cost_by_zone.png")

    if element_costs_by_zone:
        fig = _element_cost_heatmap(element_costs_by_zone)
        save_figure(fig, fig_dir / "element_cost_heatmap.png")
        print("  element_cost_heatmap.png")

    if all_element_costs:
        combined_elem = pd.concat(all_element_costs)
        fig = _ai_assisted_reskilling_bar(combined_elem)
        if fig.data:
            save_figure(fig, fig_dir / "ai_assisted_reskilling.png")
            print("  ai_assisted_reskilling.png")

    # ── Copy key figures ──────────────────────────────────────────────────────
    committed = HERE / "figures"
    committed.mkdir(exist_ok=True)
    for fname in ["pivot_cost_by_zone.png", "element_cost_heatmap.png",
                  "ai_assisted_reskilling.png"]:
        src = fig_dir / fname
        if src.exists():
            shutil.copy2(src, committed / fname)

    # ── PDF ───────────────────────────────────────────────────────────────────
    from analysis.utils import generate_pdf
    md_path = HERE / "pivot_distance_report.md"
    if md_path.exists():
        generate_pdf(md_path, results / "pivot_distance_report.pdf")

    print("\nDone.")


if __name__ == "__main__":
    main()
