"""
run.py — State Clusters: Risk Profile

Cluster U.S. states by the risk-tier composition of their AI-exposed workforce.

Every occupation has a pre-computed risk tier (high / moderate / low) from the
job_risk_scoring analysis. This script asks: when you weight each occupation's
tier by how many workers that state has in that occupation, which states have
unusually high concentrations of high-risk workers — and do those states cluster
together?

Approach:
  1. Load risk_scores_primary.csv → title_current → risk_tier (and pct_tasks_affected)
  2. Load eco_raw (eco_2025) → extract per-state occupation employment from
     emp_tot_{geo}_2024 columns
  3. For each state: compute employment-weighted pct of workers in high/moderate/low
     risk tiers among the AI-exposed population (workers_affected = pct/100 × emp)
  4. Feature matrix: state × [pct_high, pct_moderate, pct_low]
  5. K-means (k=5) clustering
  6. Compare assignments to sector-composition clusters from state_profiles

Outputs:
  results/state_risk_features.csv    — Per-state risk tier distribution
  results/cluster_assignments.csv    — State → cluster (risk-based)
  results/cluster_profiles.csv       — Per-cluster avg risk distribution
  results/vs_sector_composition.csv  — Both cluster assignments side-by-side

Figures (committed to figures/):
  risk_tier_bars.png     — States sorted by pct_high, stacked bars by tier, colored by cluster
  cluster_profiles.png   — Avg risk tier distribution per cluster (grouped bar)
  vs_sector_comp.png     — How sector clusters map to risk clusters (sankey / tile)

Run from project root:
    venv/Scripts/python -m analysis.questions.state_clusters.risk_profile.run
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from analysis.config import (
    ANALYSIS_CONFIGS,
    ANALYSIS_CONFIG_LABELS,
    ensure_results_dir,
)
from analysis.utils import (
    CATEGORY_PALETTE,
    COLORS,
    FONT_FAMILY,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
QUESTIONS_DIR = HERE.parent
STATE_PROFILES_DIR = QUESTIONS_DIR.parent / "economic_footprint" / "state_profiles"
JOB_RISK_DIR = QUESTIONS_DIR.parent / "job_exposure" / "job_risk_scoring"

N_CLUSTERS = 5
PRIMARY_KEY = "all_confirmed"

TIER_COLORS = {
    "high":     "#d62728",
    "moderate": "#ff7f0e",
    "low":      "#2ca02c",
}
CLUSTER_COLORS = {
    f"Cluster {i + 1}": CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)]
    for i in range(N_CLUSTERS)
}


# ── Data helpers ────────────────────────────────────────────────────────────────

def load_risk_scores() -> pd.DataFrame:
    """Load pre-computed risk scores (title_current, risk_tier, pct_tasks_affected)."""
    path = JOB_RISK_DIR / "results" / "risk_scores_primary.csv"
    assert path.exists(), f"risk_scores_primary.csv not found at {path}"
    df = pd.read_csv(path)
    assert "title_current" in df.columns, "risk_scores missing title_current"
    assert "risk_tier" in df.columns, "risk_scores missing risk_tier"
    assert "pct_tasks_affected" in df.columns, "risk_scores missing pct_tasks_affected"
    return df[["title_current", "risk_tier", "pct_tasks_affected"]].copy()


def load_sector_clusters() -> pd.DataFrame:
    """Load sector-composition cluster assignments from state_profiles."""
    path = STATE_PROFILES_DIR / "results" / "cluster_assignments.csv"
    assert path.exists(), f"cluster_assignments.csv not found at {path}. Run state_profiles first."
    return pd.read_csv(path)


def build_state_risk_features() -> pd.DataFrame:
    """
    Build state × risk-tier feature matrix using eco_raw employment.

    For each state geo, occupation employment comes from emp_tot_{geo}_2024
    in eco_raw. Workers affected = (pct_tasks_affected / 100) × employment.
    We split those workers across risk tiers and normalize to shares.
    """
    from backend.compute import load_eco_raw

    eco = load_eco_raw()
    assert eco is not None, "eco_raw not found"
    assert "title_current" in eco.columns, "eco_raw missing title_current"

    risk_scores = load_risk_scores()

    # Dedup eco to one row per occupation (take first — emp columns are repeated per task)
    occ_df = eco.groupby("title_current").first().reset_index()

    # Identify state emp columns
    state_geos = [
        col.replace("emp_tot_", "").replace("_2024", "")
        for col in occ_df.columns
        if col.startswith("emp_tot_") and col.endswith("_2024") and col != "emp_tot_nat_2024"
    ]
    # Remove national
    state_geos = [g for g in state_geos if g != "nat"]

    # Join risk tier to occ employment
    occ_risk = occ_df[["title_current"]].merge(risk_scores, on="title_current", how="left")
    occ_risk["risk_tier"] = occ_risk["risk_tier"].fillna("low")  # unscored → low

    rows = []
    for geo in state_geos:
        emp_col = f"emp_tot_{geo}_2024"
        if emp_col not in occ_df.columns:
            continue

        occ_emp = occ_df[["title_current", emp_col]].copy()
        occ_emp = occ_emp.rename(columns={emp_col: "emp"})
        occ_emp["emp"] = pd.to_numeric(occ_emp["emp"], errors="coerce").fillna(0.0)

        merged = occ_risk.merge(occ_emp, on="title_current", how="left")
        merged["emp"] = merged["emp"].fillna(0.0)

        # Workers affected = pct/100 × emp
        merged["workers_affected"] = (merged["pct_tasks_affected"] / 100.0) * merged["emp"]

        total_wa = merged["workers_affected"].sum()
        if total_wa <= 0:
            continue

        tier_workers = merged.groupby("risk_tier")["workers_affected"].sum()
        pct_high     = tier_workers.get("high",     0.0) / total_wa * 100
        pct_moderate = tier_workers.get("moderate", 0.0) / total_wa * 100
        pct_low      = tier_workers.get("low",      0.0) / total_wa * 100

        rows.append({
            "geo": geo,
            "total_workers_affected": total_wa,
            "pct_high":     round(pct_high,     2),
            "pct_moderate": round(pct_moderate, 2),
            "pct_low":      round(pct_low,      2),
        })

    return pd.DataFrame(rows).sort_values("geo").reset_index(drop=True)


# ── Clustering ──────────────────────────────────────────────────────────────────

def run_clustering(
    features: pd.DataFrame,
    feature_cols: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """K-means on feature_cols. Returns (assignments_df, profiles_df)."""
    X = features[feature_cols].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    km = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=20)
    labels = km.fit_predict(X_scaled)

    assignments = features[["geo"]].copy()
    assignments["risk_cluster_id"] = labels
    # Label clusters by descending pct_high so Cluster 1 = highest risk
    order = (
        features.assign(_label=labels)
        .groupby("_label")["pct_high"]
        .mean()
        .sort_values(ascending=False)
        .index.tolist()
    )
    rank_map = {old: new for new, old in enumerate(order)}
    assignments["risk_cluster_id"] = assignments["risk_cluster_id"].map(rank_map)
    assignments["risk_cluster"] = assignments["risk_cluster_id"].apply(
        lambda x: f"Risk-{x + 1}"
    )

    profiles = (
        features.assign(_label=assignments["risk_cluster_id"].values)
        .groupby("_label")[feature_cols]
        .mean()
        .reset_index()
        .rename(columns={"_label": "risk_cluster_id"})
    )
    profiles["risk_cluster"] = profiles["risk_cluster_id"].apply(
        lambda x: f"Risk-{x + 1}"
    )
    return assignments, profiles


# ── Figures ─────────────────────────────────────────────────────────────────────

def _build_tier_bars(
    features: pd.DataFrame,
    assignments: pd.DataFrame,
) -> go.Figure:
    """Stacked horizontal bar: states sorted by pct_high, colored bar outlines by cluster."""
    merged = features.merge(assignments[["geo", "risk_cluster"]], on="geo")
    merged = merged.sort_values("pct_high", ascending=True)
    merged["geo_label"] = merged["geo"].str.upper()

    fig = go.Figure()
    for tier, col, color in [
        ("High Risk",     "pct_high",     TIER_COLORS["high"]),
        ("Moderate Risk", "pct_moderate", TIER_COLORS["moderate"]),
        ("Low Risk",      "pct_low",      TIER_COLORS["low"]),
    ]:
        fig.add_trace(go.Bar(
            x=merged[col],
            y=merged["geo_label"],
            orientation="h",
            name=tier,
            marker_color=color,
            opacity=0.85,
            hovertemplate=f"<b>%{{y}}</b> | {tier}: %{{x:.1f}}%<extra></extra>",
        ))

    style_figure(
        fig,
        "State Risk-Tier Composition of AI-Exposed Workforce",
        subtitle=(
            f"Sorted by % high-risk workers | k-means clusters on [pct_high, pct_moderate, pct_low] | "
            f"{ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]}"
        ),
        x_title="% of AI-exposed workers",
        show_legend=True,
        height=1200,
        width=900,
    )
    fig.update_layout(
        barmode="stack",
        xaxis=dict(showgrid=False, showticklabels=True, range=[0, 100]),
        yaxis=dict(showgrid=False, tickfont=dict(size=8)),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
        margin=dict(l=30, r=20, t=100, b=40),
    )
    return fig


def _build_cluster_profiles(profiles: pd.DataFrame) -> go.Figure:
    """Grouped bar: avg pct_high / moderate / low per risk cluster."""
    clusters = profiles.sort_values("risk_cluster_id")["risk_cluster"].tolist()
    fig = go.Figure()
    for tier, col, color in [
        ("High Risk",     "pct_high",     TIER_COLORS["high"]),
        ("Moderate Risk", "pct_moderate", TIER_COLORS["moderate"]),
        ("Low Risk",      "pct_low",      TIER_COLORS["low"]),
    ]:
        vals = profiles.sort_values("risk_cluster_id")[col].tolist()
        fig.add_trace(go.Bar(
            x=clusters,
            y=vals,
            name=tier,
            marker_color=color,
            text=[f"{v:.1f}%" for v in vals],
            textposition="outside",
            textfont=dict(size=10),
        ))

    style_figure(
        fig,
        "Risk-Profile Cluster Profiles",
        subtitle="Average % of AI-exposed workers in each risk tier per cluster",
        y_title="% of AI-exposed workers",
        show_legend=True,
        height=500,
        width=800,
    )
    fig.update_layout(
        barmode="group",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.01),
        margin=dict(t=90, b=40),
    )
    return fig


def _build_vs_sector_comp(
    assignments: pd.DataFrame,
    sector_clusters: pd.DataFrame,
) -> go.Figure:
    """Tile/heatmap: sector-comp cluster (rows) vs risk cluster (cols), count of states."""
    merged = assignments.merge(
        sector_clusters[["geo", "cluster_label"]].rename(columns={"cluster_label": "sector_cluster"}),
        on="geo",
        how="inner",
    )
    cross = pd.crosstab(merged["sector_cluster"], merged["risk_cluster"])
    sector_order = sorted(cross.index.tolist())
    risk_order   = sorted(cross.columns.tolist())
    cross = cross.loc[sector_order, risk_order]

    fig = go.Figure(go.Heatmap(
        z=cross.values,
        x=risk_order,
        y=sector_order,
        colorscale=[[0, "#f0f4f8"], [0.5, COLORS["primary"]], [1.0, "#0d2b45"]],
        text=[[str(v) for v in row] for row in cross.values],
        texttemplate="%{text}",
        textfont=dict(size=13, color="white", family=FONT_FAMILY),
        hovertemplate="Sector: %{y}<br>Risk: %{x}<br>States: %{z}<extra></extra>",
        showscale=True,
        colorbar=dict(title="# States", tickfont=dict(size=10)),
    ))
    style_figure(
        fig,
        "Sector-Composition Clusters vs. Risk-Profile Clusters",
        subtitle="Each cell = number of states in that (sector, risk) cluster pair",
        show_legend=False,
        height=420,
        width=750,
    )
    fig.update_layout(
        xaxis=dict(side="bottom", showgrid=False, title="Risk-Profile Cluster"),
        yaxis=dict(showgrid=False, title="Sector-Composition Cluster"),
        margin=dict(l=130, r=40, t=90, b=60),
    )
    return fig


# ── Main ────────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("risk_profile: building state risk-tier features from eco_raw...")
    features = build_state_risk_features()
    assert not features.empty, "No state features built — check eco_raw and risk_scores_primary.csv"
    print(f"  {len(features)} states/territories with data.")

    feature_cols = ["pct_high", "pct_moderate", "pct_low"]
    save_csv(features, results / "state_risk_features.csv")

    print("risk_profile: clustering...")
    assignments, profiles = run_clustering(features, feature_cols)
    save_csv(assignments, results / "cluster_assignments.csv")
    save_csv(profiles, results / "cluster_profiles.csv")

    print("  Risk cluster distribution:")
    for cl, sub in assignments.groupby("risk_cluster"):
        avg_high = features[features["geo"].isin(sub["geo"])]["pct_high"].mean()
        print(f"    {cl}: {len(sub)} states, avg pct_high = {avg_high:.1f}%")

    # Compare to sector clusters
    print("risk_profile: loading sector-composition clusters...")
    sector_clusters = load_sector_clusters()
    comparison = assignments.merge(
        sector_clusters[["geo", "cluster_label"]].rename(columns={"cluster_label": "sector_cluster"}),
        on="geo",
        how="left",
    )
    save_csv(comparison, results / "vs_sector_composition.csv")

    # Figures
    print("risk_profile: building figures...")

    fig_bars = _build_tier_bars(features, assignments)
    save_figure(fig_bars, results / "figures" / "risk_tier_bars.png")
    shutil.copy(results / "figures" / "risk_tier_bars.png", figs_dir / "risk_tier_bars.png")
    print("  risk_tier_bars.png")

    fig_profiles = _build_cluster_profiles(profiles)
    save_figure(fig_profiles, results / "figures" / "cluster_profiles.png")
    shutil.copy(results / "figures" / "cluster_profiles.png", figs_dir / "cluster_profiles.png")
    print("  cluster_profiles.png")

    fig_vs = _build_vs_sector_comp(assignments, sector_clusters)
    save_figure(fig_vs, results / "figures" / "vs_sector_comp.png")
    shutil.copy(results / "figures" / "vs_sector_comp.png", figs_dir / "vs_sector_comp.png")
    print("  vs_sector_comp.png")

    # Summary stats
    print("\n-- Risk profile summary --")
    print(f"  Avg pct_high across all states: {features['pct_high'].mean():.1f}%")
    print(f"  Max pct_high: {features['pct_high'].max():.1f}% ({features.loc[features['pct_high'].idxmax(), 'geo'].upper()})")
    print(f"  Min pct_high: {features['pct_high'].min():.1f}% ({features.loc[features['pct_high'].idxmin(), 'geo'].upper()})")

    # PDF
    report_path = HERE / "risk_profile_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "risk_profile_report.pdf")

    print("\nrisk_profile: done.")


if __name__ == "__main__":
    main()
