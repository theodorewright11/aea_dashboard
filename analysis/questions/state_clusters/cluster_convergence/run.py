"""
run.py — State Clusters: Cluster Convergence

Do the four independent state clusterings (risk profile, activity signature,
agentic profile, adoption gap) agree with each other and with the baseline
sector-composition clustering from state_profiles?

This is the synthesis sub-question. It doesn't cluster states again — it loads
the five cluster assignment tables and measures agreement between them.

Approach:
  1. Load cluster assignments from all five sub-questions:
       - sector_composition (from economic_footprint/state_profiles)
       - risk_profile
       - activity_signature
       - agentic_profile
       - adoption_gap
  2. For each pair of clusterings, compute the Adjusted Rand Index (ARI).
     ARI = 1.0 means perfect agreement; ARI = 0.0 means random; ARI < 0 means
     systematic disagreement.
  3. Build a state-level stability score: for each state, across all pairs of
     clusterings, what fraction of the time does it end up in the same cluster
     as itself? (Using co-clustering: if state X is in cluster A under clustering
     1 and cluster B under clustering 2, it gets credit for any other state that
     is in cluster A AND cluster B.)
     Simpler version: for each state, count how many of the 5 clusterings agree
     on its cluster assignment with a plurality vote.
  4. Identify stable states (always group the same way) and unstable ones (flip).
  5. Show how sector-composition clusters map to risk/activity/agentic/gap clusters.

Outputs:
  results/all_assignments.csv   — State → cluster label in each of the 5 schemes
  results/ari_matrix.csv        — Pairwise ARI between all clustering pairs
  results/state_stability.csv   — Per-state: which cluster each scheme assigns + stability score
  results/co_cluster_counts.csv — For each state pair: how many times do they cluster together

Figures (committed to figures/):
  ari_heatmap.png         — Pairwise ARI heatmap
  stability_bar.png       — States ranked by stability score (how consistently they cluster)
  sector_to_risk.png      — Sector-comp → risk-profile flow (tile map)
  sector_to_activity.png  — Sector-comp → activity-signature flow
  sector_to_agentic.png   — Sector-comp → agentic-profile flow
  sector_to_gap.png       — Sector-comp → adoption-gap flow

Run from project root (after running all other state_clusters sub-questions):
    venv/Scripts/python -m analysis.questions.state_clusters.cluster_convergence.run
"""
from __future__ import annotations

import shutil
from pathlib import Path
from itertools import combinations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.metrics import adjusted_rand_score

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
STATE_CLUSTERS_DIR = QUESTIONS_DIR
ECONOMIC_FOOTPRINT_DIR = QUESTIONS_DIR.parent / "economic_footprint"

# Where each sub-question's cluster_assignments.csv lives
CLUSTERING_SOURCES = {
    "sector_composition": ECONOMIC_FOOTPRINT_DIR / "state_profiles" / "results" / "cluster_assignments.csv",
    "risk_profile":       STATE_CLUSTERS_DIR / "risk_profile"       / "results" / "cluster_assignments.csv",
    "activity_signature": STATE_CLUSTERS_DIR / "activity_signature" / "results" / "cluster_assignments.csv",
    "agentic_profile":    STATE_CLUSTERS_DIR / "agentic_profile"    / "results" / "cluster_assignments.csv",
    "adoption_gap":       STATE_CLUSTERS_DIR / "adoption_gap"       / "results" / "cluster_assignments.csv",
}

# The column in each file that holds the cluster label
CLUSTER_COL = {
    "sector_composition": "cluster_label",
    "risk_profile":       "risk_cluster",
    "activity_signature": "act_cluster",
    "agentic_profile":    "ag_cluster",
    "adoption_gap":       "gap_cluster",
}

SCHEME_LABELS = {
    "sector_composition": "Sector Composition",
    "risk_profile":       "Risk Profile",
    "activity_signature": "Activity Signature",
    "agentic_profile":    "Agentic Profile",
    "adoption_gap":       "Adoption Gap",
}


# ── Data loading ─────────────────────────────────────────────────────────────────

def load_all_assignments() -> pd.DataFrame:
    """
    Load cluster assignments from all five sources. Returns a wide DataFrame:
        geo | sector_composition | risk_profile | activity_signature | agentic_profile | adoption_gap
    Only states present in ALL five schemes are included.
    """
    frames = {}
    for scheme, path in CLUSTERING_SOURCES.items():
        assert path.exists(), (
            f"cluster_assignments.csv not found for '{scheme}' at {path}. "
            f"Run {scheme} sub-question first."
        )
        df = pd.read_csv(path)
        col = CLUSTER_COL[scheme]
        assert col in df.columns, f"Expected column '{col}' in {path}, got: {df.columns.tolist()}"
        frames[scheme] = df[["geo", col]].rename(columns={col: scheme})

    merged = frames["sector_composition"]
    for scheme in ["risk_profile", "activity_signature", "agentic_profile", "adoption_gap"]:
        merged = merged.merge(frames[scheme], on="geo", how="inner")

    return merged.sort_values("geo").reset_index(drop=True)


# ── ARI matrix ───────────────────────────────────────────────────────────────────

def compute_ari_matrix(assignments: pd.DataFrame, schemes: list[str]) -> pd.DataFrame:
    """Compute pairwise Adjusted Rand Index between all clustering pairs."""
    n = len(schemes)
    ari = np.zeros((n, n))
    for i, j in combinations(range(n), 2):
        score = adjusted_rand_score(
            assignments[schemes[i]].values,
            assignments[schemes[j]].values,
        )
        ari[i, j] = score
        ari[j, i] = score
    np.fill_diagonal(ari, 1.0)
    return pd.DataFrame(ari, index=schemes, columns=schemes)


# ── State stability ──────────────────────────────────────────────────────────────

def compute_stability(assignments: pd.DataFrame, schemes: list[str]) -> pd.DataFrame:
    """
    For each state, count how many scheme-pairs agree on its relative grouping.

    A simpler proxy: for each state, look at which other states it shares a
    cluster with across all schemes. Its stability score = (fraction of states
    that always co-cluster with it across all schemes).

    Even simpler for reporting: count the number of scheme pairs (out of 10 total
    for 5 schemes) where two states that co-cluster under one scheme also co-cluster
    under the other scheme. A state's stability = the mean over all other states
    of the fraction of pairs where they agree on co-clustering.

    Implemented as: for each state, for each other state, compute co-cluster
    agreement fraction (0–1), then average. States that cluster very consistently
    with the same set of neighbors score high.
    """
    n_states = len(assignments)
    geos = assignments["geo"].values
    scheme_labels = assignments[schemes].values  # n_states × n_schemes

    # Co-cluster matrix: for each (state_i, state_j), fraction of schemes
    # where they are in the same cluster
    co_cluster = np.zeros((n_states, n_states))
    for s in range(len(schemes)):
        labels_s = scheme_labels[:, s]
        for i in range(n_states):
            for j in range(n_states):
                if labels_s[i] == labels_s[j]:
                    co_cluster[i, j] += 1
    co_cluster /= len(schemes)

    # Stability score per state: mean co-cluster fraction with all other states
    # relative to what would be expected under independence (rough measure)
    stability = co_cluster.mean(axis=1)

    result = pd.DataFrame({
        "geo": geos,
        "stability_score": stability.round(3),
    })
    for scheme in schemes:
        result[scheme] = assignments[scheme].values

    return result.sort_values("stability_score", ascending=False).reset_index(drop=True)


# ── Figures ──────────────────────────────────────────────────────────────────────

def _build_ari_heatmap(ari_df: pd.DataFrame, schemes: list[str]) -> go.Figure:
    """Heatmap of pairwise Adjusted Rand Index."""
    labels = [SCHEME_LABELS.get(s, s) for s in schemes]
    z = ari_df.loc[schemes, schemes].values

    fig = go.Figure(go.Heatmap(
        z=z,
        x=labels,
        y=labels,
        colorscale=[[0, "#f0f4f8"], [0.5, COLORS["primary"]], [1.0, "#0d2b45"]],
        zmin=0.0, zmax=1.0,
        text=[[f"{v:.3f}" for v in row] for row in z],
        texttemplate="%{text}",
        textfont=dict(size=12, color="white", family=FONT_FAMILY),
        hovertemplate="%{y} vs %{x}: ARI = %{z:.3f}<extra></extra>",
        showscale=True,
        colorbar=dict(title="Adjusted<br>Rand Index", tickfont=dict(size=10)),
    ))
    style_figure(
        fig,
        "Clustering Agreement: Adjusted Rand Index",
        subtitle=(
            "ARI = 1.0 → perfect agreement | ARI = 0.0 → random | "
            "All five state clustering schemes compared pairwise"
        ),
        show_legend=False,
        height=500,
        width=680,
    )
    fig.update_layout(
        xaxis=dict(side="bottom", showgrid=False, tickangle=-30, tickfont=dict(size=11)),
        yaxis=dict(showgrid=False, tickfont=dict(size=11)),
        margin=dict(l=160, r=80, t=90, b=100),
    )
    return fig


def _build_stability_bar(stability: pd.DataFrame) -> go.Figure:
    """Horizontal bar: states ranked by stability score."""
    df = stability.sort_values("stability_score", ascending=True)

    # Color by score: green = stable, red = unstable
    colors = [
        COLORS["success"] if v >= 0.6 else (COLORS["warning"] if v >= 0.4 else "#d62728")
        for v in df["stability_score"]
    ]
    fig = go.Figure(go.Bar(
        x=df["stability_score"],
        y=df["geo"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:.3f}" for v in df["stability_score"]],
        textposition="outside",
        textfont=dict(size=9),
    ))
    style_figure(
        fig,
        "State Clustering Stability",
        subtitle=(
            "Average fraction of scheme-pairs where each state co-clusters with the same neighbors | "
            "Green ≥ 0.6 (stable), Orange 0.4–0.6, Red < 0.4 (unstable)"
        ),
        x_title="Stability Score",
        show_legend=False,
        height=1200,
        width=800,
    )
    fig.update_layout(
        xaxis=dict(showgrid=False, range=[0, 1.05]),
        yaxis=dict(showgrid=False, tickfont=dict(size=8)),
        margin=dict(l=30, r=80, t=90, b=40),
    )
    return fig


def _build_cross_scheme_tile(
    assignments: pd.DataFrame,
    scheme_a: str,
    scheme_b: str,
    label_a: str,
    label_b: str,
) -> go.Figure:
    """Tile heatmap: cluster_a (rows) × cluster_b (cols), count of states."""
    cross = pd.crosstab(assignments[scheme_a], assignments[scheme_b])
    row_order = sorted(cross.index.tolist())
    col_order = sorted(cross.columns.tolist())
    cross = cross.reindex(index=row_order, columns=col_order, fill_value=0)

    fig = go.Figure(go.Heatmap(
        z=cross.values,
        x=col_order,
        y=row_order,
        colorscale=[[0, "#f0f4f8"], [0.5, COLORS["primary"]], [1.0, "#0d2b45"]],
        text=[[str(v) for v in row] for row in cross.values],
        texttemplate="%{text}",
        textfont=dict(size=13, color="white", family=FONT_FAMILY),
        showscale=True,
        colorbar=dict(title="# States"),
    ))
    style_figure(
        fig,
        f"{label_a} vs. {label_b}",
        subtitle="Each cell = number of states in that cluster pair",
        show_legend=False,
        height=420,
        width=750,
    )
    fig.update_layout(
        xaxis=dict(side="bottom", showgrid=False, title=label_b),
        yaxis=dict(showgrid=False, title=label_a),
        margin=dict(l=140, r=40, t=90, b=60),
    )
    return fig


# ── Main ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("cluster_convergence: loading all cluster assignments...")
    assignments = load_all_assignments()
    schemes = list(CLUSTERING_SOURCES.keys())
    print(f"  {len(assignments)} states with complete assignments across all 5 schemes.")
    save_csv(assignments, results / "all_assignments.csv")

    # ARI matrix
    print("cluster_convergence: computing ARI matrix...")
    ari_df = compute_ari_matrix(assignments, schemes)
    save_csv(ari_df.reset_index().rename(columns={"index": "scheme"}), results / "ari_matrix.csv")

    print("\n-- Pairwise ARI --")
    for i, j in combinations(range(len(schemes)), 2):
        s1, s2 = schemes[i], schemes[j]
        print(f"  {SCHEME_LABELS[s1]} vs {SCHEME_LABELS[s2]}: ARI = {ari_df.loc[s1, s2]:.3f}")

    # State stability
    print("\ncluster_convergence: computing state stability...")
    stability = compute_stability(assignments, schemes)
    save_csv(stability, results / "state_stability.csv")

    top_stable   = stability.head(5)["geo"].tolist()
    top_unstable = stability.tail(5)["geo"].tolist()
    print(f"  Most stable states: {top_stable}")
    print(f"  Least stable states: {top_unstable}")

    # Figures
    print("\ncluster_convergence: building figures...")

    fig_ari = _build_ari_heatmap(ari_df, schemes)
    save_figure(fig_ari, results / "figures" / "ari_heatmap.png")
    shutil.copy(results / "figures" / "ari_heatmap.png", figs_dir / "ari_heatmap.png")
    print("  ari_heatmap.png")

    fig_stab = _build_stability_bar(stability)
    save_figure(fig_stab, results / "figures" / "stability_bar.png")
    shutil.copy(results / "figures" / "stability_bar.png", figs_dir / "stability_bar.png")
    print("  stability_bar.png")

    for other_scheme in ["risk_profile", "activity_signature", "agentic_profile", "adoption_gap"]:
        fig = _build_cross_scheme_tile(
            assignments,
            "sector_composition",
            other_scheme,
            SCHEME_LABELS["sector_composition"],
            SCHEME_LABELS[other_scheme],
        )
        fname = f"sector_to_{other_scheme}.png"
        save_figure(fig, results / "figures" / fname)
        shutil.copy(results / "figures" / fname, figs_dir / fname)
        print(f"  {fname}")

    # Mean ARI vs sector composition
    print("\n-- Mean ARI vs. sector composition --")
    for s in schemes[1:]:
        print(f"  {SCHEME_LABELS[s]}: {ari_df.loc['sector_composition', s]:.3f}")

    report_path = HERE / "cluster_convergence_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "cluster_convergence_report.pdf")

    print("\ncluster_convergence: done.")


if __name__ == "__main__":
    main()
