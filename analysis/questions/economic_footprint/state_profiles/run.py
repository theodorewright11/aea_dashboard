"""
run.py — Economic Footprint: State Profiles

Do states share similar AI exposure profiles? Are there regional clusters?

Approach:
  1. For each state, compute pct_tasks_affected at the major category level
     using the primary config (all_confirmed).
  2. Build a state × major_category matrix.
  3. Run k-means clustering (k=5 default) on this matrix to identify state groups.
  4. Aggregate each cluster: weighted avg pct across all sectors.
  5. Map cluster profiles and show state rankings.

Also produces:
  - State-level aggregate totals (workers, wages, pct)
  - Cluster profiles: what makes each cluster distinctive

Outputs:
  results/state_totals.csv           — Per-state: workers, wages, pct, cluster
  results/state_major_matrix.csv     — State × major category pct matrix
  results/cluster_profiles.csv       — Per-cluster average pct by major
  results/cluster_assignments.csv    — State → cluster assignment

Figures:
  state_rankings_workers.png     — States ranked by workers affected
  state_rankings_pct.png         — States ranked by avg pct tasks affected
  cluster_heatmap.png            — Heatmap: cluster × major, avg pct (cluster profiles)
  state_cluster_map.png          — State × cluster scatter (sorted)

Run from project root:
    venv/Scripts/python -m analysis.questions.economic_footprint.state_profiles.run
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
    format_workers,
    format_wages,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
PRIMARY_KEY = "all_confirmed"
N_CLUSTERS = 5
TOP_STATES_DISPLAY = 30  # states to show in ranking charts


# -- Data helpers ---------------------------------------------------------------

def get_geo_options() -> list[str]:
    """Return all available geo codes from the backend."""
    from backend.compute import get_group_data

    # Query with a placeholder geo and catch what's available
    # Actually read the geo options from config
    from backend.config import GEO_OPTIONS
    return list(GEO_OPTIONS.keys())


def get_state_major_data(geo: str, dataset_name: str) -> pd.DataFrame:
    """Return major-category breakdown for a given state geo code."""
    from backend.compute import get_group_data

    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": geo,
        "agg_level": "major",
        "sort_by": "Workers Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    if data is None:
        return pd.DataFrame()
    df = data["df"].rename(columns={"major_occ_category": "category"})
    df["geo"] = geo
    return df


def get_state_totals(geo: str, dataset_name: str) -> dict:
    """Return aggregate totals for a state."""
    from backend.compute import get_group_data

    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": geo,
        "agg_level": "occupation",
        "sort_by": "Workers Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    if data is None:
        return {}
    df = data["df"]
    if df.empty:
        return {}
    workers = df["workers_affected"].sum()
    wages = df["wages_affected"].sum()
    # pct_tasks_affected mean as summary (ratio-of-totals not recomputable without task data)
    wtd_pct = df["pct_tasks_affected"].mean()
    return {
        "geo": geo,
        "workers_affected": workers,
        "wages_affected": wages,
        "pct_tasks_wtd": wtd_pct,
        "total_emp": workers,  # proxy — workers_affected as indicator of state size
    }


# -- Clustering -----------------------------------------------------------------

def run_clustering(matrix: pd.DataFrame, n_clusters: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Cluster states by their major-category pct profile.
    Returns (assignments_df, cluster_profiles_df).
    """
    X = matrix.values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
    labels = km.fit_predict(X_scaled)

    assignments = pd.DataFrame({
        "geo": matrix.index.tolist(),
        "cluster": labels,
    })
    assignments["cluster_label"] = assignments["cluster"].apply(lambda x: f"Cluster {x + 1}")

    # Cluster profiles: mean pct per cluster per major
    matrix_with_cluster = matrix.copy()
    matrix_with_cluster["cluster"] = labels
    profiles = matrix_with_cluster.groupby("cluster").mean().reset_index()
    profiles["cluster_label"] = profiles["cluster"].apply(lambda x: f"Cluster {x + 1}")

    return assignments, profiles


# -- Figure builders ------------------------------------------------------------

def _build_state_ranking(state_df: pd.DataFrame, metric: str,
                          metric_label: str, title: str) -> go.Figure:
    """Horizontal bar: top states by a given metric, colored by cluster."""
    top = state_df.sort_values(metric, ascending=False).head(TOP_STATES_DISPLAY)
    top = top.sort_values(metric, ascending=True)  # flip for horizontal bar

    cluster_colors = {
        f"Cluster {i + 1}": CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)]
        for i in range(N_CLUSTERS)
    }
    bar_colors = [cluster_colors.get(c, COLORS["primary"]) for c in top["cluster_label"]]

    if metric == "workers_affected":
        text_vals = [f"{v/1e6:.1f}M" for v in top[metric]]
    elif metric == "pct_tasks_wtd":
        text_vals = [f"{v:.1f}%" for v in top[metric]]
    else:
        text_vals = [str(v) for v in top[metric]]

    fig = go.Figure(go.Bar(
        x=top[metric],
        y=top["geo"],
        orientation="h",
        marker_color=bar_colors,
        text=text_vals,
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(fig, title,
                 subtitle=f"Top {TOP_STATES_DISPLAY} states | Color = cluster assignment | {ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]}",
                 x_title=metric_label, show_legend=False, height=900, width=1100)
    fig.update_layout(
        margin=dict(l=20, r=100),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        bargap=0.15,
    )
    return fig


def _build_cluster_heatmap(profiles: pd.DataFrame, major_cols: list[str]) -> go.Figure:
    """Heatmap: cluster (rows) × major category (cols), avg pct."""
    pivot = profiles.set_index("cluster_label")[major_cols].fillna(0)
    # Order major cols by total pct descending
    col_order = pivot.sum(axis=0).sort_values(ascending=False).index.tolist()
    pivot = pivot[col_order]

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=list(pivot.columns),
        y=list(pivot.index),
        colorscale=[[0, "#f0f4f8"], [0.5, COLORS["primary"]], [1.0, "#0d2b45"]],
        text=[[f"{v:.1f}%" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=10, color="white", family=FONT_FAMILY),
        hovertemplate="%{y} | %{x}: %{z:.1f}%<extra></extra>",
        showscale=True,
        colorbar=dict(title="Avg %<br>Tasks<br>Affected", tickfont=dict(size=10)),
    ))
    style_figure(fig, f"State Cluster Profiles — {N_CLUSTERS} Clusters",
                 subtitle="Average % tasks affected per major category for each state cluster",
                 show_legend=False, height=500, width=1400)
    fig.update_layout(
        xaxis=dict(side="bottom", tickangle=-35, showgrid=False, showline=False,
                   tickfont=dict(size=9)),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=11)),
        margin=dict(l=100, r=80, t=90, b=200),
    )
    return fig


def _build_cluster_strip(assignments: pd.DataFrame, state_totals: pd.DataFrame) -> go.Figure:
    """Strip plot: states arranged by cluster and sorted by avg pct within each cluster."""
    merged = assignments.merge(state_totals[["geo", "pct_tasks_wtd", "workers_affected"]], on="geo")
    merged = merged.sort_values(["cluster", "pct_tasks_wtd"])

    cluster_colors = {
        f"Cluster {i + 1}": CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)]
        for i in range(N_CLUSTERS)
    }

    fig = go.Figure()
    for cluster_label, sub in merged.groupby("cluster_label"):
        fig.add_trace(go.Scatter(
            x=sub["geo"],
            y=sub["pct_tasks_wtd"],
            mode="markers+text",
            text=sub["geo"],
            textposition="top center",
            textfont=dict(size=9, family=FONT_FAMILY),
            marker=dict(
                color=cluster_colors.get(cluster_label, COLORS["primary"]),
                size=sub["workers_affected"].clip(1e5, 2e7).apply(
                    lambda v: max(6, min(20, v / 5e5))
                ),
                opacity=0.8,
            ),
            name=cluster_label,
            hovertemplate="<b>%{x}</b><br>Avg pct: %{y:.1f}%<extra></extra>",
        ))

    style_figure(fig, "State Clusters by AI Exposure Profile",
                 subtitle=f"k={N_CLUSTERS} clusters | Dot size ∝ employment | Y = avg % tasks affected",
                 y_title="Avg % Tasks Affected", height=600, width=1400)
    fig.update_layout(
        xaxis=dict(showgrid=False, showticklabels=False, showline=False),
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
    )
    return fig


# -- Main -----------------------------------------------------------------------

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    ds_name = ANALYSIS_CONFIGS[PRIMARY_KEY]
    print("state_profiles: loading geo options...")

    try:
        geo_list = get_geo_options()
    except Exception:
        # Fallback: use known US state abbreviations + nat
        geo_list = [
            "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga",
            "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md",
            "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj",
            "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc",
            "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy",
            "dc",
        ]

    # Remove national from state analysis
    state_geos = [g for g in geo_list if g != "nat"]
    print(f"  Processing {len(state_geos)} state/territory geographies...")

    # -- 1. State totals + major breakdown -------------------------------------
    state_total_rows: list[dict] = []
    major_rows: list[dict] = []

    for geo in state_geos:
        print(f"  {geo}...", end=" ", flush=True)
        totals = get_state_totals(geo, ds_name)
        if not totals or totals.get("workers_affected", 0) == 0:
            print("(skipped -- no data)")
            continue
        state_total_rows.append(totals)

        major_df = get_state_major_data(geo, ds_name)
        if not major_df.empty:
            major_rows.extend(major_df.to_dict("records"))

    print()
    state_totals = pd.DataFrame(state_total_rows)
    major_all = pd.DataFrame(major_rows)
    print(f"  Loaded {len(state_totals)} states/territories.")

    if state_totals.empty:
        print("  No state data returned — aborting.")
        return

    # -- 2. Build state × major matrix -----------------------------------------
    # Cluster on workers_share (% of state's affected workers in each sector)
    # rather than pct_tasks_affected which is occupation-driven and doesn't vary by state.
    if not major_all.empty:
        major_all_norm = major_all.copy()
        state_total_lookup = state_totals.set_index("geo")["workers_affected"].to_dict()
        major_all_norm["state_total"] = major_all_norm["geo"].map(state_total_lookup)
        major_all_norm["workers_share"] = (
            major_all_norm["workers_affected"] / major_all_norm["state_total"].clip(1) * 100
        )
        matrix = major_all_norm.pivot_table(
            index="geo", columns="category", values="workers_share", aggfunc="first"
        ).fillna(0)
        major_cols = matrix.columns.tolist()
        # Save both matrices
        pct_matrix = major_all.pivot_table(
            index="geo", columns="category", values="pct_tasks_affected", aggfunc="first"
        ).fillna(0)
        save_csv(pct_matrix.reset_index(), results / "state_major_matrix.csv")
        save_csv(matrix.reset_index(), results / "state_major_workers_share.csv")
    else:
        matrix = pd.DataFrame(index=state_totals["geo"])
        major_cols = []

    # -- 3. Clustering ---------------------------------------------------------
    if len(matrix) >= N_CLUSTERS and len(major_cols) >= 3:
        print(f"  Running k-means clustering (k={N_CLUSTERS})...")
        assignments, profiles = run_clustering(matrix, N_CLUSTERS)
        save_csv(assignments, results / "cluster_assignments.csv")
        save_csv(profiles, results / "cluster_profiles.csv")

        # Merge cluster labels into state_totals
        state_totals = state_totals.merge(assignments, on="geo", how="left")
        state_totals["cluster_label"] = state_totals["cluster_label"].fillna("Unassigned")
    else:
        print("  Not enough data for clustering.")
        state_totals["cluster"] = 0
        state_totals["cluster_label"] = "All States"
        assignments = state_totals[["geo", "cluster", "cluster_label"]]
        profiles = pd.DataFrame()

    save_cols = ["geo", "workers_affected", "wages_affected", "pct_tasks_wtd", "total_emp"]
    if "cluster" in state_totals.columns:
        save_cols += ["cluster", "cluster_label"]
    save_csv(state_totals[save_cols], results / "state_totals.csv")

    # -- 4. Figures ------------------------------------------------------------

    # 4a. State rankings — workers affected
    fig_workers = _build_state_ranking(
        state_totals, "workers_affected", "Workers Affected",
        "States Ranked by Workers Affected",
    )
    save_figure(fig_workers, results / "figures" / "state_rankings_workers.png")
    shutil.copy(results / "figures" / "state_rankings_workers.png",
                figs_dir / "state_rankings_workers.png")
    print("  state_rankings_workers.png")

    # 4b. State rankings — avg pct tasks affected
    fig_pct = _build_state_ranking(
        state_totals, "pct_tasks_wtd", "Avg % Tasks Affected (employment-weighted)",
        "States Ranked by Average % Tasks Affected",
    )
    save_figure(fig_pct, results / "figures" / "state_rankings_pct.png")
    shutil.copy(results / "figures" / "state_rankings_pct.png", figs_dir / "state_rankings_pct.png")
    print("  state_rankings_pct.png")

    # 4c. Cluster heatmap
    if not profiles.empty and major_cols:
        fig_heat = _build_cluster_heatmap(profiles, major_cols)
        save_figure(fig_heat, results / "figures" / "cluster_heatmap.png")
        shutil.copy(results / "figures" / "cluster_heatmap.png", figs_dir / "cluster_heatmap.png")
        print("  cluster_heatmap.png")

    # 4d. Cluster strip plot
    if "cluster_label" in state_totals.columns:
        fig_strip = _build_cluster_strip(assignments, state_totals)
        save_figure(fig_strip, results / "figures" / "state_cluster_map.png")
        shutil.copy(results / "figures" / "state_cluster_map.png", figs_dir / "state_cluster_map.png")
        print("  state_cluster_map.png")

    # -- 5. Summary ------------------------------------------------------------
    print("\n-- State summary --")
    top5 = state_totals.sort_values("pct_tasks_wtd", ascending=False).head(5)
    print("  Top 5 states by avg % tasks affected:")
    for _, row in top5.iterrows():
        print(f"    {row['geo'].upper()}: {row['pct_tasks_wtd']:.1f}% "
              f"({format_workers(row['workers_affected'])} workers)")

    if "cluster_label" in state_totals.columns:
        print("\n  Cluster sizes:")
        for cl, sub in state_totals.groupby("cluster_label"):
            avg_pct = sub["pct_tasks_wtd"].mean()
            print(f"    {cl}: {len(sub)} states, avg pct = {avg_pct:.1f}%")

    # -- 6. PDF ----------------------------------------------------------------
    report_path = HERE / "state_profiles_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "state_profiles_report.pdf")

    print("\nstate_profiles: done.")


if __name__ == "__main__":
    main()
