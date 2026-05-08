"""
run.py — State Clusters: Activity Signature

Cluster U.S. states by the General Work Activity (GWA) composition of their
AI-exposed workforce.

The sector-composition clustering (economic_footprint/state_profiles) groups
states by what *industries* their workers are in. This analysis groups them by
what *kinds of work* their AI-exposed workers actually do — e.g., "Communicating
with Persons Outside the Organization", "Analyzing Data", "Performing Physical
Activities". These can come apart: a state heavy in healthcare and one heavy in
finance might look very similar on sector share, but their GWA fingerprints could
differ (clinical activities vs. financial analysis activities).

Approach:
  1. Load eco_raw (eco_2025): one row per (title_current, task_normalized, gwa_title)
  2. Dedup to (title_current, task_normalized) — one row per unique task per occ —
     and take the first gwa_title for that task (avoids double-counting)
  3. Compute freq-based emp fraction per task within each occupation:
         _emp_frac = freq_mean / sum(freq_mean per occ)
  4. For each state geo, compute task-level employment:
         task_emp = _emp_frac × emp_tot_{geo}_2024
  5. Aggregate task_emp by gwa_title per state → GWA employment shares
  6. Build state × GWA feature matrix (shares)
  7. K-means (k=5) clustering
  8. Compare to sector-composition clusters

Note on employment split: eco_raw already contains per-state employment columns
(emp_tot_{geo}_2024), so no API calls are needed. The freq-based split is the
same "Time" method used in the dashboard and other analyses.

Outputs:
  results/state_gwa_features.csv      — Per-state GWA employment shares
  results/cluster_assignments.csv     — State → cluster (activity-based)
  results/cluster_profiles.csv        — Per-cluster avg GWA shares
  results/vs_sector_composition.csv   — Both cluster assignments side-by-side
  results/top_gwas_per_cluster.csv    — Top 5 GWAs per cluster by share delta vs. avg

Figures (committed to figures/):
  gwa_heatmap.png        — State × GWA shares heatmap, sorted by cluster
  cluster_profiles.png   — Top GWAs per cluster (bars showing share vs. national avg)
  vs_sector_comp.png     — Sector clusters vs activity clusters (tile count)

Run from project root:
    venv/Scripts/python -m analysis.questions.state_clusters.activity_signature.run
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from analysis.config import ensure_results_dir
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

N_CLUSTERS = 5
NATIONAL_GEO = "nat"
TOP_GWAS_TO_SHOW = 10  # GWAs to include in heatmap (top by variance)

CLUSTER_COLORS = {
    f"Act-{i + 1}": CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)]
    for i in range(N_CLUSTERS)
}


# ── Data helpers ─────────────────────────────────────────────────────────────────

def load_sector_clusters() -> pd.DataFrame:
    path = STATE_PROFILES_DIR / "results" / "cluster_assignments.csv"
    assert path.exists(), f"cluster_assignments.csv not found at {path}"
    return pd.read_csv(path)


def build_state_gwa_features() -> tuple[pd.DataFrame, list[str]]:
    """
    Build state × GWA employment share matrix.

    For each state:
      - Split occupation employment across tasks using freq fractions
      - Assign each task to its primary GWA (first occurrence after dedup)
      - Sum task employment by GWA → normalize to shares within state

    Returns (feature_df with geo + one col per GWA, list_of_gwa_cols).
    """
    from backend.compute import load_eco_raw

    eco = load_eco_raw()
    assert eco is not None, "eco_raw not found"
    assert "title_current" in eco.columns, "eco_raw missing title_current"
    assert "gwa_title" in eco.columns, "eco_raw missing gwa_title"
    assert "freq_mean" in eco.columns, "eco_raw missing freq_mean"

    # Step 1: Dedup to (title_current, task_normalized) — one row per unique task per occ
    # Take the first gwa_title for each task. This avoids double-counting when a task
    # maps to multiple DWAs under different GWAs.
    task_col = "task_normalized" if "task_normalized" in eco.columns else "task"
    eco_dedup = (
        eco.groupby(["title_current", task_col], sort=False)
        .first()
        .reset_index()
    )

    # Step 2: Compute freq-based emp fraction per task within each occupation
    eco_dedup["freq_mean"] = pd.to_numeric(eco_dedup["freq_mean"], errors="coerce").fillna(0.0)
    eco_dedup["_freq_sum"] = eco_dedup.groupby("title_current")["freq_mean"].transform("sum")
    eco_dedup["_emp_frac"] = (
        eco_dedup["freq_mean"] / eco_dedup["_freq_sum"].replace(0, np.nan)
    ).fillna(0.0)

    # Identify state emp columns (exclude national)
    state_geos = [
        col.replace("emp_tot_", "").replace("_2024", "")
        for col in eco_dedup.columns
        if col.startswith("emp_tot_") and col.endswith("_2024") and col != "emp_tot_nat_2024"
    ]
    state_geos = [g for g in state_geos if g != "nat"]

    # Step 3: For each state, compute GWA employment shares
    all_gwas = sorted(eco_dedup["gwa_title"].dropna().unique().tolist())
    rows = []

    for geo in state_geos:
        emp_col = f"emp_tot_{geo}_2024"
        if emp_col not in eco_dedup.columns:
            continue

        emp_vals = pd.to_numeric(eco_dedup[emp_col], errors="coerce").fillna(0.0)
        task_emp = eco_dedup["_emp_frac"] * emp_vals  # task-level employment

        # Sum by GWA
        gwa_series = pd.Series(task_emp.values, index=eco_dedup["gwa_title"]).groupby(level=0).sum()
        total = gwa_series.sum()
        if total <= 0:
            continue

        gwa_shares = (gwa_series / total * 100).reindex(all_gwas, fill_value=0.0)
        row = {"geo": geo, "total_task_emp": total}
        row.update(gwa_shares.to_dict())
        rows.append(row)

    feat_df = pd.DataFrame(rows).sort_values("geo").reset_index(drop=True)

    # Drop GWA cols with all-zero or near-zero variance
    gwa_cols = [c for c in feat_df.columns if c not in ("geo", "total_task_emp")]
    variance = feat_df[gwa_cols].var()
    gwa_cols = variance[variance > 0.001].index.tolist()

    return feat_df, gwa_cols


# ── Clustering ───────────────────────────────────────────────────────────────────

def run_clustering(
    features: pd.DataFrame,
    gwa_cols: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """K-means on GWA share columns. Returns (assignments_df, profiles_df)."""
    X = features[gwa_cols].fillna(0.0).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    km = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=20)
    labels = km.fit_predict(X_scaled)

    # Label by total task employment (largest cluster = Act-1)
    order = (
        features.assign(_label=labels)
        .groupby("_label")["total_task_emp"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )
    rank_map = {old: new for new, old in enumerate(order)}
    mapped = [rank_map[l] for l in labels]

    assignments = features[["geo"]].copy()
    assignments["act_cluster_id"] = mapped
    assignments["act_cluster"] = [f"Act-{x + 1}" for x in mapped]

    profiles = (
        features.assign(_label=mapped)
        .groupby("_label")[gwa_cols]
        .mean()
        .reset_index()
        .rename(columns={"_label": "act_cluster_id"})
    )
    profiles["act_cluster"] = profiles["act_cluster_id"].apply(lambda x: f"Act-{x + 1}")
    return assignments, profiles


def get_top_gwas_per_cluster(
    profiles: pd.DataFrame,
    features: pd.DataFrame,
    gwa_cols: list[str],
    top_n: int = 5,
) -> pd.DataFrame:
    """For each cluster, identify GWAs with highest share relative to national avg."""
    nat_avg = features[gwa_cols].mean()
    rows = []
    for _, row in profiles.iterrows():
        deltas = {g: row[g] - nat_avg[g] for g in gwa_cols if g in row.index}
        sorted_gwas = sorted(deltas.items(), key=lambda x: x[1], reverse=True)
        for rank, (gwa, delta) in enumerate(sorted_gwas[:top_n], 1):
            rows.append({
                "act_cluster": row["act_cluster"],
                "rank": rank,
                "gwa": gwa,
                "cluster_share": round(row[gwa], 2),
                "national_avg": round(nat_avg[gwa], 2),
                "delta_vs_nat": round(delta, 2),
            })
    return pd.DataFrame(rows)


# ── Figures ──────────────────────────────────────────────────────────────────────

def _build_gwa_heatmap(
    features: pd.DataFrame,
    assignments: pd.DataFrame,
    gwa_cols: list[str],
) -> go.Figure:
    """Heatmap: state (rows, sorted by cluster) × GWA (cols, sorted by variance)."""
    merged = features.merge(assignments[["geo", "act_cluster", "act_cluster_id"]], on="geo")
    merged = merged.sort_values(["act_cluster_id", "geo"])

    # Keep top GWAs by variance for readability
    variance = features[gwa_cols].var().sort_values(ascending=False)
    top_gwas = variance.head(TOP_GWAS_TO_SHOW).index.tolist()

    z_vals = merged[top_gwas].values
    y_labels = [f"{row['act_cluster']} | {row['geo'].upper()}" for _, row in merged.iterrows()]
    x_labels = [g[:40] for g in top_gwas]

    fig = go.Figure(go.Heatmap(
        z=z_vals,
        x=x_labels,
        y=y_labels,
        colorscale=[[0, "#f0f4f8"], [0.5, COLORS["primary"]], [1.0, "#0d2b45"]],
        text=[[f"{v:.1f}%" for v in row] for row in z_vals],
        texttemplate="%{text}",
        textfont=dict(size=7, color="white", family=FONT_FAMILY),
        hovertemplate="<b>%{y}</b><br>%{x}: %{z:.2f}%<extra></extra>",
        showscale=True,
        colorbar=dict(title="% of task<br>employment", tickfont=dict(size=9)),
    ))
    style_figure(
        fig,
        "State Work-Activity Signature — GWA Employment Shares",
        subtitle=f"Top {TOP_GWAS_TO_SHOW} GWAs by variance | States sorted by activity cluster",
        show_legend=False,
        height=max(600, len(y_labels) * 14),
        width=1400,
    )
    fig.update_layout(
        xaxis=dict(side="bottom", tickangle=-40, showgrid=False, tickfont=dict(size=9)),
        yaxis=dict(showgrid=False, tickfont=dict(size=8)),
        margin=dict(l=140, r=80, t=90, b=200),
    )
    return fig


def _build_cluster_profiles_chart(
    profiles: pd.DataFrame,
    features: pd.DataFrame,
    gwa_cols: list[str],
) -> go.Figure:
    """Bar chart: for each cluster, delta vs. national avg for top-5 distinctive GWAs."""
    nat_avg = features[gwa_cols].mean()
    fig = go.Figure()

    for i, (_, row) in enumerate(profiles.sort_values("act_cluster_id").iterrows()):
        deltas = {g: row[g] - nat_avg[g] for g in gwa_cols if g in row.index}
        sorted_gwas = sorted(deltas.items(), key=lambda x: abs(x[1]), reverse=True)[:6]
        gwas, delta_vals = zip(*sorted_gwas)

        fig.add_trace(go.Bar(
            x=list(gwas),
            y=list(delta_vals),
            name=row["act_cluster"],
            marker_color=CLUSTER_COLORS.get(row["act_cluster"], COLORS["primary"]),
            hovertemplate="%{x}: %{y:+.2f}pp vs. national avg<extra></extra>",
        ))

    style_figure(
        fig,
        "Activity-Cluster Distinctive GWAs",
        subtitle="Delta vs. national average GWA share (pp) — top 6 most distinctive per cluster",
        y_title="Δ share vs. national avg (pp)",
        show_legend=True,
        height=500,
        width=1100,
    )
    fig.update_layout(
        barmode="group",
        xaxis=dict(tickangle=-30, showgrid=False, tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.01),
        margin=dict(t=90, b=160),
    )
    return fig


def _build_vs_sector_comp(
    assignments: pd.DataFrame,
    sector_clusters: pd.DataFrame,
) -> go.Figure:
    """Tile heatmap: sector cluster (rows) vs activity cluster (cols), count of states."""
    merged = assignments.merge(
        sector_clusters[["geo", "cluster_label"]].rename(columns={"cluster_label": "sector_cluster"}),
        on="geo",
        how="inner",
    )
    cross = pd.crosstab(merged["sector_cluster"], merged["act_cluster"])
    sector_order = sorted(cross.index.tolist())
    act_order    = sorted(cross.columns.tolist())
    cross = cross.reindex(index=sector_order, columns=act_order, fill_value=0)

    fig = go.Figure(go.Heatmap(
        z=cross.values,
        x=act_order,
        y=sector_order,
        colorscale=[[0, "#f0f4f8"], [0.5, COLORS["primary"]], [1.0, "#0d2b45"]],
        text=[[str(v) for v in row] for row in cross.values],
        texttemplate="%{text}",
        textfont=dict(size=13, color="white", family=FONT_FAMILY),
        hovertemplate="Sector: %{y}<br>Activity: %{x}<br>States: %{z}<extra></extra>",
        showscale=True,
        colorbar=dict(title="# States"),
    ))
    style_figure(
        fig,
        "Sector-Composition Clusters vs. Activity-Signature Clusters",
        subtitle="Each cell = number of states in that (sector, activity) cluster pair",
        show_legend=False,
        height=420,
        width=750,
    )
    fig.update_layout(
        xaxis=dict(side="bottom", showgrid=False, title="Activity-Signature Cluster"),
        yaxis=dict(showgrid=False, title="Sector-Composition Cluster"),
        margin=dict(l=130, r=40, t=90, b=60),
    )
    return fig


# ── Main ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("activity_signature: building state GWA features from eco_raw...")
    features, gwa_cols = build_state_gwa_features()
    assert not features.empty, "No state features built — check eco_raw"
    print(f"  {len(features)} states/territories, {len(gwa_cols)} GWA features.")

    save_csv(features, results / "state_gwa_features.csv")

    print("activity_signature: clustering...")
    assignments, profiles = run_clustering(features, gwa_cols)
    save_csv(assignments, results / "cluster_assignments.csv")
    save_csv(profiles, results / "cluster_profiles.csv")

    top_gwas = get_top_gwas_per_cluster(profiles, features, gwa_cols)
    save_csv(top_gwas, results / "top_gwas_per_cluster.csv")

    print("  Activity cluster distribution:")
    for cl, sub in assignments.groupby("act_cluster"):
        print(f"    {cl}: {len(sub)} states")

    # Compare to sector clusters
    sector_clusters = load_sector_clusters()
    comparison = assignments.merge(
        sector_clusters[["geo", "cluster_label"]].rename(columns={"cluster_label": "sector_cluster"}),
        on="geo",
        how="left",
    )
    save_csv(comparison, results / "vs_sector_composition.csv")

    # Figures
    print("activity_signature: building figures...")

    fig_heat = _build_gwa_heatmap(features, assignments, gwa_cols)
    save_figure(fig_heat, results / "figures" / "gwa_heatmap.png")
    shutil.copy(results / "figures" / "gwa_heatmap.png", figs_dir / "gwa_heatmap.png")
    print("  gwa_heatmap.png")

    fig_profiles = _build_cluster_profiles_chart(profiles, features, gwa_cols)
    save_figure(fig_profiles, results / "figures" / "cluster_profiles.png")
    shutil.copy(results / "figures" / "cluster_profiles.png", figs_dir / "cluster_profiles.png")
    print("  cluster_profiles.png")

    fig_vs = _build_vs_sector_comp(assignments, sector_clusters)
    save_figure(fig_vs, results / "figures" / "vs_sector_comp.png")
    shutil.copy(results / "figures" / "vs_sector_comp.png", figs_dir / "vs_sector_comp.png")
    print("  vs_sector_comp.png")

    # Summary
    print("\n-- Top GWA per cluster --")
    for cl in sorted(top_gwas["act_cluster"].unique()):
        top = top_gwas[top_gwas["act_cluster"] == cl].iloc[0]
        print(f"  {cl}: {top['gwa']} (delta {top['delta_vs_nat']:+.2f}pp vs. nat avg)")

    report_path = HERE / "activity_signature_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "activity_signature_report.pdf")

    print("\nactivity_signature: done.")


if __name__ == "__main__":
    main()
