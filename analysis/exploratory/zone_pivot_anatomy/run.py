"""
run.py — Exploratory: Zone Pivot Anatomy

Diagnoses why Zone 3 peaks on pivot cost (359 units) while Zones 4 and 5 are
lower (263 and 235), despite those zones having deeper/more complex SKA profiles.

Five figures:
  1. occ_counts_by_zone_tier   — full occupation counts by zone × risk tier
  2. zone_exposure_profiles    — mean pct_tasks_affected by zone, broken out by tier
  3. ska_mass_and_overlap      — shared SKA mass / pivot cost / drop cost per zone
                                 (magnitude-preserving overlap structure)
  4. sector_composition        — sector breakdown of high-risk occupations per zone
  5. zone34_scatter            — scatter of Zone 3 and Zone 4 occs by exposure × risk score

Run from project root:
    venv/Scripts/python -m analysis.exploratory.zone_pivot_anatomy.run
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.config import (
    ANALYSIS_CONFIGS,
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.data.compute_ska import SKAResult, compute_ska, load_ska_data
from analysis.utils import (
    CATEGORY_PALETTE,
    COLORS,
    FONT_FAMILY,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
RISK_SCORES_FILE = (
    HERE.parent.parent
    / "questions"
    / "job_exposure"
    / "job_risk_scoring"
    / "results"
    / "risk_scores_primary.csv"
)
PIVOT_INPUTS_FILE = (
    HERE.parent.parent
    / "questions"
    / "job_exposure"
    / "job_risk_scoring"
    / "results"
    / "pivot_distance_inputs.csv"
)

PRIMARY_KEY = "all_confirmed"
IMPORTANCE_THRESHOLD = 3.0
TIER_ORDER = ["high", "mod-high", "mod-low", "low"]
TIER_LABELS = {"high": "High", "mod-high": "Mod-High", "mod-low": "Mod-Low", "low": "Low"}
TIER_COLORS = {
    "high": "#c0392b",
    "mod-high": "#e67e22",
    "mod-low": "#f1c40f",
    "low": "#27ae60",
}


# ── Data loading ──────────────────────────────────────────────────────────────

def _load_risk_scores() -> pd.DataFrame:
    """Load risk_scores_primary.csv. Normalise tier strings to lowercase-hyphen."""
    assert RISK_SCORES_FILE.exists(), f"Risk scores not found: {RISK_SCORES_FILE}"
    df = pd.read_csv(RISK_SCORES_FILE)
    assert "title_current" in df.columns, "Missing title_current"
    assert "risk_tier" in df.columns, "Missing risk_tier"
    assert "job_zone" in df.columns, "Missing job_zone"
    assert "pct_tasks_affected" in df.columns, "Missing pct_tasks_affected"
    df = df.dropna(subset=["job_zone"])
    df["job_zone"] = df["job_zone"].astype(int)
    df["risk_tier"] = df["risk_tier"].str.lower().str.replace("_", "-")
    return df


def _load_pivot_inputs() -> pd.DataFrame:
    """Load pivot_distance_inputs.csv (top-10 high/low risk per zone)."""
    assert PIVOT_INPUTS_FILE.exists(), f"Pivot inputs not found: {PIVOT_INPUTS_FILE}"
    df = pd.read_csv(PIVOT_INPUTS_FILE)
    assert "title_current" in df.columns
    assert "group" in df.columns
    assert "job_zone" in df.columns
    df["job_zone"] = df["job_zone"].astype(int)
    return df


# ── SKA profile helpers ───────────────────────────────────────────────────────

def _build_avg_profile(
    occ_list: list[str],
    ska_result: SKAResult,
    types: tuple[str, ...] = ("skills", "knowledge"),
) -> pd.DataFrame:
    """Build average occ_score profile for a list of occupations.

    Returns DataFrame with columns: element_name, type, avg_score.
    Only elements present in at least one of the occupations (importance >= 3
    already filtered in SKAResult) are returned.
    """
    rows = []
    for type_name in types:
        elem_df = ska_result.occ_element_scores.get(type_name, pd.DataFrame())
        if elem_df.empty:
            continue
        subset = elem_df[elem_df["title_current"].isin(occ_list)]
        if subset.empty:
            continue
        agg = (
            subset.groupby("element_name")
            .agg(avg_score=("occ_score", "mean"))
            .reset_index()
        )
        agg["type"] = type_name
        rows.append(agg)
    if not rows:
        return pd.DataFrame(columns=["element_name", "type", "avg_score"])
    return pd.concat(rows, ignore_index=True)


def _compute_overlap_stats(
    high_profile: pd.DataFrame,
    low_profile: pd.DataFrame,
) -> dict[str, float]:
    """Compute magnitude-preserving overlap stats between two SKA profiles.

    shared_mass  = sum of min(high_score, low_score) per element
    pivot_cost   = sum of max(0, low_score - high_score)  [must acquire]
    drop_cost    = sum of max(0, high_score - low_score)  [would leave behind]
    high_mass    = sum of high_score across all elements
    low_mass     = sum of low_score across all elements
    overlap_pct  = shared_mass / low_mass * 100  [% of destination already mastered]
    """
    # Sum across types if the same element_name appears in both skills and knowledge
    high_idx = high_profile.groupby("element_name")["avg_score"].sum()
    low_idx = low_profile.groupby("element_name")["avg_score"].sum()
    all_elems = high_idx.index.union(low_idx.index)

    shared = pivot = drop = 0.0
    for elem in all_elems:
        h = float(high_idx.get(elem, 0.0))
        lo = float(low_idx.get(elem, 0.0))
        shared += min(h, lo)
        pivot += max(0.0, lo - h)
        drop += max(0.0, h - lo)

    high_mass = float(high_idx.sum())
    low_mass = float(low_idx.sum())
    overlap_pct = (shared / low_mass * 100.0) if low_mass > 0 else 0.0

    return {
        "shared_mass": round(shared, 2),
        "pivot_cost": round(pivot, 2),
        "drop_cost": round(drop, 2),
        "high_mass": round(high_mass, 2),
        "low_mass": round(low_mass, 2),
        "overlap_pct": round(overlap_pct, 1),
    }


def _build_zone_overlap_table(
    pivot_inputs: pd.DataFrame,
    ska_result: SKAResult,
) -> pd.DataFrame:
    """Compute overlap stats for all 5 zones."""
    rows = []
    for zone in sorted(pivot_inputs["job_zone"].unique()):
        high_occs = pivot_inputs.loc[
            (pivot_inputs["job_zone"] == zone) & (pivot_inputs["group"] == "high_risk"),
            "title_current",
        ].tolist()
        low_occs = pivot_inputs.loc[
            (pivot_inputs["job_zone"] == zone) & (pivot_inputs["group"] == "low_risk"),
            "title_current",
        ].tolist()
        high_prof = _build_avg_profile(high_occs, ska_result)
        low_prof = _build_avg_profile(low_occs, ska_result)
        stats = _compute_overlap_stats(high_prof, low_prof)
        rows.append({"job_zone": zone, **stats})
    return pd.DataFrame(rows)


# ── Figure 1: Occupation counts by zone × tier ───────────────────────────────

def fig_occ_counts_by_zone_tier(risk_df: pd.DataFrame) -> go.Figure:
    """Stacked bar: n_occs by job zone × risk tier."""
    counts = (
        risk_df.groupby(["job_zone", "risk_tier"])
        .size()
        .reset_index(name="n_occs")
    )

    zones = sorted(risk_df["job_zone"].unique())
    zone_labels = [f"Zone {z}" for z in zones]

    fig = go.Figure()
    for tier in TIER_ORDER:
        tier_label = TIER_LABELS[tier]
        y_vals = [
            int(counts.loc[(counts["job_zone"] == z) & (counts["risk_tier"] == tier), "n_occs"].sum())
            for z in zones
        ]
        fig.add_trace(go.Bar(
            name=tier_label,
            x=zone_labels,
            y=y_vals,
            marker_color=TIER_COLORS[tier],
            text=[str(v) if v > 0 else "" for v in y_vals],
            textposition="inside",
            textfont=dict(color="white", size=11, family=FONT_FAMILY),
        ))

    fig.update_layout(
        barmode="stack",
        xaxis=dict(title="Job Zone", tickfont=dict(family=FONT_FAMILY)),
        yaxis=dict(title="Number of Occupations", tickfont=dict(family=FONT_FAMILY)),
        legend=dict(title="Risk Tier", traceorder="normal", font=dict(family=FONT_FAMILY)),
    )
    style_figure(fig, "Occupation Counts by Job Zone and Risk Tier")
    return fig


# ── Figure 2: Zone exposure profiles by tier ─────────────────────────────────

def fig_zone_exposure_profiles(risk_df: pd.DataFrame) -> go.Figure:
    """Grouped bar: mean pct_tasks_affected by zone, broken out by tier."""
    means = (
        risk_df.groupby(["job_zone", "risk_tier"])["pct_tasks_affected"]
        .mean()
        .reset_index()
    )

    zones = sorted(risk_df["job_zone"].unique())
    zone_labels = [f"Zone {z}" for z in zones]

    fig = go.Figure()
    for tier in TIER_ORDER:
        tier_label = TIER_LABELS[tier]
        y_vals = []
        for z in zones:
            row = means.loc[(means["job_zone"] == z) & (means["risk_tier"] == tier), "pct_tasks_affected"]
            y_vals.append(round(float(row.iloc[0]), 1) if not row.empty else 0.0)
        fig.add_trace(go.Bar(
            name=tier_label,
            x=zone_labels,
            y=y_vals,
            marker_color=TIER_COLORS[tier],
            text=[f"{v:.0f}%" for v in y_vals],
            textposition="outside",
            textfont=dict(size=10, family=FONT_FAMILY),
        ))

    fig.update_layout(
        barmode="group",
        xaxis=dict(title="Job Zone", tickfont=dict(family=FONT_FAMILY)),
        yaxis=dict(
            title="Mean % Tasks Affected",
            range=[0, 100],
            tickfont=dict(family=FONT_FAMILY),
        ),
        legend=dict(title="Risk Tier", font=dict(family=FONT_FAMILY)),
    )
    style_figure(fig, "Mean % Tasks Affected by Job Zone and Risk Tier")
    return fig


# ── Figure 3: SKA mass and overlap structure ──────────────────────────────────

def fig_ska_mass_and_overlap(overlap_df: pd.DataFrame) -> go.Figure:
    """Stacked bar showing shared / pivot / drop components per zone.

    Three stacked layers per zone (in absolute imp×level units):
      - Shared mass (teal): what high-risk already has that matches low-risk
      - Pivot cost (orange): what high-risk must acquire
      - Drop cost (gray): what high-risk has that low-risk doesn't need

    Annotated with overlap % (shared / low_mass × 100).
    """
    zones = sorted(overlap_df["job_zone"].unique())
    zone_labels = [f"Zone {z}" for z in zones]

    shared = overlap_df.set_index("job_zone").loc[zones, "shared_mass"].tolist()
    pivot = overlap_df.set_index("job_zone").loc[zones, "pivot_cost"].tolist()
    drop = overlap_df.set_index("job_zone").loc[zones, "drop_cost"].tolist()
    overlap_pct = overlap_df.set_index("job_zone").loc[zones, "overlap_pct"].tolist()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Shared (already mastered)",
        x=zone_labels,
        y=shared,
        marker_color=COLORS.get("sky", "#0ea5e9"),
        text=[f"{v:.0f}" for v in shared],
        textposition="inside",
        textfont=dict(color="white", size=10, family=FONT_FAMILY),
    ))
    fig.add_trace(go.Bar(
        name="Must acquire (pivot cost)",
        x=zone_labels,
        y=pivot,
        marker_color=COLORS.get("amber", "#f59e0b"),
        text=[f"{v:.0f}" for v in pivot],
        textposition="inside",
        textfont=dict(color="white", size=10, family=FONT_FAMILY),
    ))
    fig.add_trace(go.Bar(
        name="Would leave behind (drop cost)",
        x=zone_labels,
        y=drop,
        marker_color="#94a3b8",
        text=[f"{v:.0f}" for v in drop],
        textposition="inside",
        textfont=dict(color="white", size=10, family=FONT_FAMILY),
    ))

    # Annotate overlap % above bars
    total_heights = [s + p + d for s, p, d in zip(shared, pivot, drop)]
    for i, (zone_label, pct, total) in enumerate(zip(zone_labels, overlap_pct, total_heights)):
        fig.add_annotation(
            x=zone_label,
            y=total + 8,
            text=f"{pct:.0f}% overlap",
            showarrow=False,
            font=dict(size=10, family=FONT_FAMILY, color="#374151"),
        )

    fig.update_layout(
        barmode="stack",
        xaxis=dict(title="Job Zone", tickfont=dict(family=FONT_FAMILY)),
        yaxis=dict(title="SKA Mass (imp × level units)", tickfont=dict(family=FONT_FAMILY)),
        legend=dict(font=dict(family=FONT_FAMILY)),
    )
    style_figure(fig, "SKA Profile Structure: Shared Mass vs. Pivot Cost vs. Drop Cost")
    return fig


# ── Figure 4: Sector composition of high-risk occupations per zone ────────────

def fig_sector_composition(risk_df: pd.DataFrame) -> go.Figure:
    """Stacked bar: sector breakdown of high-risk occupations per zone by employment."""
    high_risk = risk_df[risk_df["risk_tier"] == "high"].copy()
    assert not high_risk.empty, "No high-risk occupations found"
    assert "employment" in high_risk.columns or "emp_nat" in high_risk.columns, \
        "Need employment column (employment or emp_nat)"

    emp_col = "employment" if "employment" in high_risk.columns else "emp_nat"
    high_risk = high_risk.dropna(subset=["major"])

    # Top sectors by total employment across all zones
    sector_emp = high_risk.groupby("major")[emp_col].sum().sort_values(ascending=False)
    top_sectors = sector_emp.head(8).index.tolist()

    # Aggregate: zone × sector employment
    agg = (
        high_risk.groupby(["job_zone", "major"])[emp_col]
        .sum()
        .reset_index()
    )
    # Lump smaller sectors into "Other"
    agg["sector_label"] = agg["major"].apply(
        lambda s: s if s in top_sectors else "Other"
    )
    agg = agg.groupby(["job_zone", "sector_label"])[emp_col].sum().reset_index()

    # Convert to % within each zone
    zone_totals = agg.groupby("job_zone")[emp_col].sum()
    agg["pct_emp"] = agg.apply(
        lambda row: row[emp_col] / zone_totals[row["job_zone"]] * 100, axis=1
    )

    zones = sorted(agg["job_zone"].unique())
    zone_labels = [f"Zone {z}" for z in zones]

    sector_order = top_sectors + (["Other"] if "Other" in agg["sector_label"].values else [])
    colors = CATEGORY_PALETTE + ["#94a3b8"]  # gray for Other

    fig = go.Figure()
    for i, sector in enumerate(sector_order):
        color = colors[i % len(colors)]
        y_vals = []
        for z in zones:
            row = agg.loc[
                (agg["job_zone"] == z) & (agg["sector_label"] == sector), "pct_emp"
            ]
            y_vals.append(round(float(row.iloc[0]), 1) if not row.empty else 0.0)
        fig.add_trace(go.Bar(
            name=sector,
            x=zone_labels,
            y=y_vals,
            marker_color=color,
            text=[f"{v:.0f}%" if v >= 5 else "" for v in y_vals],
            textposition="inside",
            textfont=dict(color="white", size=9, family=FONT_FAMILY),
        ))

    fig.update_layout(
        barmode="stack",
        xaxis=dict(title="Job Zone", tickfont=dict(family=FONT_FAMILY)),
        yaxis=dict(
            title="% of High-Risk Employment in Zone",
            range=[0, 102],
            tickfont=dict(family=FONT_FAMILY),
        ),
        legend=dict(font=dict(size=9, family=FONT_FAMILY), traceorder="normal"),
    )
    style_figure(fig, "Sector Composition of High-Risk Occupations by Job Zone (% Employment)")
    return fig


# ── Figure 5: Zone 3 vs Zone 4 scatter ───────────────────────────────────────

def fig_zone34_scatter(risk_df: pd.DataFrame) -> go.Figure:
    """Side-by-side scatter of Zone 3 and Zone 4 occupations.

    x = pct_tasks_affected, y = risk_score
    color = sector (major)
    size = employment (log-scaled)
    Dashed lines show the High tier threshold crossings.
    """
    assert "major" in risk_df.columns, "Missing major column"
    emp_col = "employment" if "employment" in risk_df.columns else "emp_nat"

    z3 = risk_df[risk_df["job_zone"] == 3].copy()
    z4 = risk_df[risk_df["job_zone"] == 4].copy()

    # Top sectors across zone 3 + 4 combined
    combined = pd.concat([z3, z4])
    top_sectors = (
        combined.groupby("major")[emp_col].sum()
        .sort_values(ascending=False)
        .head(8)
        .index.tolist()
    )
    sector_color = {s: CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)] for i, s in enumerate(top_sectors)}
    sector_color["Other"] = "#94a3b8"

    def get_color(sector: str) -> str:
        return sector_color.get(sector, "#94a3b8")

    def get_size(emp: float) -> float:
        import math
        return max(6.0, min(20.0, 4 + math.log10(max(emp, 1)) * 3))

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["Zone 3", "Zone 4"],
        horizontal_spacing=0.1,
    )

    for col_idx, (zone_df, zone_label) in enumerate([(z3, "Zone 3"), (z4, "Zone 4")], start=1):
        # Plot by sector for legend deduplication
        added_sectors: set[str] = set()
        for _, row in zone_df.iterrows():
            sector = row["major"] if row["major"] in top_sectors else "Other"
            color = get_color(sector)
            size = get_size(float(row.get(emp_col, 100)))
            show_legend = sector not in added_sectors and col_idx == 1
            added_sectors.add(sector)

            fig.add_trace(
                go.Scatter(
                    x=[round(float(row["pct_tasks_affected"]), 1)],
                    y=[int(row["risk_score"])],
                    mode="markers",
                    marker=dict(size=size, color=color, opacity=0.75, line=dict(width=0.5, color="white")),
                    name=sector if show_legend else "",
                    legendgroup=sector,
                    showlegend=show_legend,
                    hovertext=(
                        f"<b>{row['title_current']}</b><br>"
                        f"Sector: {row['major']}<br>"
                        f"pct_tasks_affected: {row['pct_tasks_affected']:.1f}%<br>"
                        f"risk_score: {row['risk_score']}"
                    ),
                    hoverinfo="text",
                ),
                row=1, col=col_idx,
            )

        # High tier threshold line (score = 8)
        fig.add_hline(
            y=7.5, line_dash="dash", line_color="#c0392b", line_width=1, opacity=0.5,
            row=1, col=col_idx,
        )
        # Exposure gate (33%)
        fig.add_vline(
            x=33, line_dash="dot", line_color="#6b7280", line_width=1, opacity=0.5,
            row=1, col=col_idx,
        )

    fig.update_xaxes(title_text="% Tasks Affected", range=[0, 100], tickfont=dict(family=FONT_FAMILY))
    fig.update_yaxes(title_text="Risk Score (0–10)", range=[-0.5, 10.5], tickfont=dict(family=FONT_FAMILY))

    fig.update_layout(
        legend=dict(title="Sector", font=dict(size=9, family=FONT_FAMILY)),
        height=520,
    )
    style_figure(
        fig,
        "Zone 3 vs Zone 4: Exposure × Risk Score by Sector",
        subtitle="Red dashed = High tier threshold (score ≥ 8). Gray dotted = 33% exposure gate.",
        height=520,
    )
    return fig


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    results_dir = ensure_results_dir(HERE)
    figures_dir = results_dir / "figures"

    # Load data
    risk_df = _load_risk_scores()
    pivot_inputs = _load_pivot_inputs()

    pct = get_pct_tasks_affected(ANALYSIS_CONFIGS[PRIMARY_KEY])
    ska_data = load_ska_data()
    ska_result = compute_ska(pct, ska_data)

    # Compute overlap structure per zone
    overlap_df = _build_zone_overlap_table(pivot_inputs, ska_result)
    overlap_df.to_csv(results_dir / "zone_overlap_stats.csv", index=False)

    # Print summary for reference
    print("\n=== Zone Overlap Summary ===")
    print(overlap_df.to_string(index=False))

    # Occupation counts summary
    counts = (
        risk_df.groupby(["job_zone", "risk_tier"])
        .size()
        .reset_index(name="n_occs")
    )
    counts.to_csv(results_dir / "occ_counts_by_zone_tier.csv", index=False)

    # Zone exposure summary
    zone_exposure = (
        risk_df.groupby(["job_zone", "risk_tier"])["pct_tasks_affected"]
        .agg(["mean", "median", "count"])
        .reset_index()
        .rename(columns={"mean": "mean_pct", "median": "median_pct", "count": "n_occs"})
    )
    zone_exposure.to_csv(results_dir / "zone_exposure_by_tier.csv", index=False)

    # Figures
    f1 = fig_occ_counts_by_zone_tier(risk_df)
    save_figure(f1, figures_dir / "occ_counts_by_zone_tier.png")

    f2 = fig_zone_exposure_profiles(risk_df)
    save_figure(f2, figures_dir / "zone_exposure_profiles.png")

    f3 = fig_ska_mass_and_overlap(overlap_df)
    save_figure(f3, figures_dir / "ska_mass_and_overlap.png")

    f4 = fig_sector_composition(risk_df)
    save_figure(f4, figures_dir / "sector_composition_high_risk.png")

    f5 = fig_zone34_scatter(risk_df)
    save_figure(f5, figures_dir / "zone34_scatter.png", width=1100, height=520)

    print(f"\nFigures saved to {figures_dir}")
    print("Done.")


if __name__ == "__main__":
    main()
