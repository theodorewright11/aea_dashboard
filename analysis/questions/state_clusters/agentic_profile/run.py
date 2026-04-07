"""
run.py — State Clusters: Agentic Profile

Cluster U.S. states by the agentic intensity of their AI-exposed workforce —
specifically, the ratio of agentic (API/tool-use) workers to confirmed (all sources)
workers within each major sector.

The rationale: a state's sector composition tells you what industries its workers
are in, but it doesn't tell you what *kind* of AI they're most exposed to. Two
states might both have large healthcare sectors, but one might have a healthcare
workforce concentrated in clinical documentation work (conversational AI) while
the other has more data/systems-intensive roles (agentic AI). The agentic intensity
ratio within sectors captures that distinction.

Feature construction: for each state × major sector:
    agentic_intensity = sum(agentic_pct[occ]/100 × emp[state,occ]) for occs in sector
                      / sum(confirmed_pct[occ]/100 × emp[state,occ]) for occs in sector

This is not the absolute number of agentic workers but the fraction of confirmed
exposure that is agentic — a measure of how "agentic-leaning" each sector is in
each state's particular workforce mix.

Datasets:
  - all_confirmed  (AEI Both + Micro 2026-02-12) — confirmed baseline
  - agentic_confirmed (AEI API 2026-02-12) — confirmed agentic subset

Note: agentic_confirmed uses is_aei=True (AEI API, crosswalked 2010→2019 SOC).
pct_tasks_affected from get_pct_tasks_affected() is returned at title_current level
(post-crosswalk), so the join to eco_raw on title_current is valid.

Outputs:
  results/state_agentic_features.csv   — Per-state agentic intensity by sector
  results/cluster_assignments.csv      — State → cluster (agentic-based)
  results/cluster_profiles.csv         — Per-cluster avg agentic intensity by sector
  results/vs_sector_composition.csv    — Both cluster assignments side-by-side
  results/overall_agentic_share.csv    — Overall agentic intensity per state (single metric)

Figures (committed to figures/):
  agentic_intensity_heatmap.png   — State × sector agentic intensity, sorted by cluster
  cluster_profiles.png            — Avg agentic intensity per sector per cluster
  vs_sector_comp.png              — Sector clusters vs agentic clusters (tile count)
  overall_agentic_bar.png         — States ranked by overall agentic intensity

Run from project root:
    venv/Scripts/python -m analysis.questions.state_clusters.agentic_profile.run
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
    get_pct_tasks_affected,
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

N_CLUSTERS = 5
CONFIRMED_KEY  = "all_confirmed"
AGENTIC_KEY    = "agentic_confirmed"

CLUSTER_COLORS = {
    f"Ag-{i + 1}": CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)]
    for i in range(N_CLUSTERS)
}


# ── Data helpers ─────────────────────────────────────────────────────────────────

def load_sector_clusters() -> pd.DataFrame:
    path = STATE_PROFILES_DIR / "results" / "cluster_assignments.csv"
    assert path.exists(), f"cluster_assignments.csv not found at {path}"
    return pd.read_csv(path)


def build_state_agentic_features() -> tuple[pd.DataFrame, list[str]]:
    """
    Build state × sector agentic-intensity feature matrix.

    Steps:
      1. Get occupation-level pct_tasks_affected for all_confirmed and agentic_confirmed
      2. Load eco_raw → occupation employment by state, and major_occ_category per occ
      3. For each state × sector:
           confirmed_w = sum(pct_conf/100 × emp_state for occs in sector)
           agentic_w   = sum(pct_agnt/100 × emp_state for occs in sector)
           intensity   = agentic_w / confirmed_w  (clipped to [0, 1])
      4. Feature matrix: state × [intensity per sector]
    """
    from backend.compute import load_eco_raw

    print("  Loading pct_tasks_affected for confirmed and agentic configs...")
    pct_confirmed = get_pct_tasks_affected(ANALYSIS_CONFIGS[CONFIRMED_KEY])
    pct_agentic   = get_pct_tasks_affected(ANALYSIS_CONFIGS[AGENTIC_KEY])

    eco = load_eco_raw()
    assert eco is not None, "eco_raw not found"
    assert "title_current" in eco.columns
    assert "major_occ_category" in eco.columns

    # One row per occupation
    task_col = "task_normalized" if "task_normalized" in eco.columns else "task"
    occ_df = eco.groupby("title_current").first().reset_index()

    # Identify state emp columns
    state_geos = sorted([
        col.replace("emp_tot_", "").replace("_2024", "")
        for col in occ_df.columns
        if col.startswith("emp_tot_") and col.endswith("_2024") and col != "emp_tot_nat_2024"
        and col.replace("emp_tot_", "").replace("_2024", "") != "nat"
    ])

    # Map occupation → pct (fill 0 for unmatched)
    occ_df["pct_confirmed"] = occ_df["title_current"].map(pct_confirmed).fillna(0.0)
    occ_df["pct_agentic"]   = occ_df["title_current"].map(pct_agentic).fillna(0.0)

    major_cats = sorted(occ_df["major_occ_category"].dropna().unique().tolist())
    sector_cols = [f"sector_{i}" for i in range(len(major_cats))]
    sector_map  = {cat: col for cat, col in zip(major_cats, sector_cols)}
    col_to_cat  = {col: cat for cat, col in sector_map.items()}

    rows = []
    for geo in state_geos:
        emp_col = f"emp_tot_{geo}_2024"
        if emp_col not in occ_df.columns:
            continue

        emp = pd.to_numeric(occ_df[emp_col], errors="coerce").fillna(0.0)
        conf_w = (occ_df["pct_confirmed"] / 100.0) * emp
        agnt_w = (occ_df["pct_agentic"]   / 100.0) * emp

        row: dict = {"geo": geo}
        for cat in major_cats:
            mask = occ_df["major_occ_category"] == cat
            c_sum = conf_w[mask].sum()
            a_sum = agnt_w[mask].sum()
            intensity = (a_sum / c_sum) if c_sum > 0 else 0.0
            row[sector_map[cat]] = round(float(np.clip(intensity, 0.0, 1.0)), 4)

        # Overall agentic intensity
        total_conf = conf_w.sum()
        total_agnt = agnt_w.sum()
        row["overall_intensity"] = round(float(total_agnt / total_conf) if total_conf > 0 else 0.0, 4)

        rows.append(row)

    feat_df = pd.DataFrame(rows).sort_values("geo").reset_index(drop=True)

    # Return sector columns that have non-trivial variance
    variance = feat_df[sector_cols].var()
    valid_sector_cols = variance[variance > 1e-6].index.tolist()

    # Store mapping for labels
    feat_df.attrs["col_to_cat"] = col_to_cat
    feat_df.attrs["major_cats"] = major_cats
    feat_df.attrs["sector_map"] = sector_map

    return feat_df, valid_sector_cols


# ── Clustering ───────────────────────────────────────────────────────────────────

def run_clustering(
    features: pd.DataFrame,
    sector_cols: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """K-means on sector agentic-intensity columns."""
    X = features[sector_cols].fillna(0.0).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    km = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=20)
    labels = km.fit_predict(X_scaled)

    # Order by descending overall agentic intensity
    order = (
        features.assign(_label=labels)
        .groupby("_label")["overall_intensity"]
        .mean()
        .sort_values(ascending=False)
        .index.tolist()
    )
    rank_map = {old: new for new, old in enumerate(order)}
    mapped = [rank_map[l] for l in labels]

    assignments = features[["geo"]].copy()
    assignments["ag_cluster_id"] = mapped
    assignments["ag_cluster"] = [f"Ag-{x + 1}" for x in mapped]

    profiles = (
        features.assign(_label=mapped)
        .groupby("_label")[sector_cols + ["overall_intensity"]]
        .mean()
        .reset_index()
        .rename(columns={"_label": "ag_cluster_id"})
    )
    profiles["ag_cluster"] = profiles["ag_cluster_id"].apply(lambda x: f"Ag-{x + 1}")
    return assignments, profiles


# ── Figures ──────────────────────────────────────────────────────────────────────

def _build_intensity_heatmap(
    features: pd.DataFrame,
    assignments: pd.DataFrame,
    sector_cols: list[str],
    col_to_cat: dict,
) -> go.Figure:
    """Heatmap: state (rows, sorted by cluster) × sector (cols), agentic intensity."""
    merged = features.merge(assignments[["geo", "ag_cluster", "ag_cluster_id"]], on="geo")
    merged = merged.sort_values(["ag_cluster_id", "geo"])

    z_vals  = merged[sector_cols].values
    y_labels = [f"{row['ag_cluster']} | {row['geo'].upper()}" for _, row in merged.iterrows()]
    x_labels = [col_to_cat.get(c, c)[:35] for c in sector_cols]

    fig = go.Figure(go.Heatmap(
        z=z_vals,
        x=x_labels,
        y=y_labels,
        colorscale=[[0, "#f0f4f8"], [0.5, COLORS["secondary"]], [1.0, "#0d2b45"]],
        text=[[f"{v:.2f}" for v in row] for row in z_vals],
        texttemplate="%{text}",
        textfont=dict(size=7, color="white", family=FONT_FAMILY),
        zmin=0.0, zmax=1.0,
        hovertemplate="<b>%{y}</b><br>%{x}: %{z:.3f} agentic ratio<extra></extra>",
        showscale=True,
        colorbar=dict(title="Agentic<br>Intensity", tickfont=dict(size=9)),
    ))
    style_figure(
        fig,
        "State Agentic Intensity by Sector",
        subtitle=(
            "Ratio of agentic workers to confirmed workers per sector per state | "
            f"{ANALYSIS_CONFIG_LABELS[AGENTIC_KEY]} / {ANALYSIS_CONFIG_LABELS[CONFIRMED_KEY]}"
        ),
        show_legend=False,
        height=max(600, len(y_labels) * 14),
        width=1400,
    )
    fig.update_layout(
        xaxis=dict(side="bottom", tickangle=-40, showgrid=False, tickfont=dict(size=9)),
        yaxis=dict(showgrid=False, tickfont=dict(size=8)),
        margin=dict(l=140, r=80, t=90, b=220),
    )
    return fig


def _build_cluster_profiles_chart(
    profiles: pd.DataFrame,
    sector_cols: list[str],
    col_to_cat: dict,
) -> go.Figure:
    """Grouped bar: avg agentic intensity per sector per cluster."""
    x_labels = [col_to_cat.get(c, c)[:30] for c in sector_cols]
    fig = go.Figure()
    for _, row in profiles.sort_values("ag_cluster_id").iterrows():
        fig.add_trace(go.Bar(
            x=x_labels,
            y=[row[c] for c in sector_cols],
            name=row["ag_cluster"],
            marker_color=CLUSTER_COLORS.get(row["ag_cluster"], COLORS["primary"]),
        ))
    style_figure(
        fig,
        "Agentic-Profile Cluster Profiles",
        subtitle="Average agentic intensity (agentic workers / confirmed workers) by sector",
        y_title="Agentic Intensity Ratio",
        show_legend=True,
        height=500,
        width=1200,
    )
    fig.update_layout(
        barmode="group",
        xaxis=dict(tickangle=-35, showgrid=False, tickfont=dict(size=8)),
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.01),
        margin=dict(t=90, b=180),
    )
    return fig


def _build_overall_bar(features: pd.DataFrame, assignments: pd.DataFrame) -> go.Figure:
    """Horizontal bar: states ranked by overall agentic intensity."""
    merged = features[["geo", "overall_intensity"]].merge(
        assignments[["geo", "ag_cluster"]], on="geo"
    ).sort_values("overall_intensity", ascending=True)

    bar_colors = [
        CLUSTER_COLORS.get(cl, COLORS["primary"]) for cl in merged["ag_cluster"]
    ]
    fig = go.Figure(go.Bar(
        x=merged["overall_intensity"],
        y=merged["geo"],
        orientation="h",
        marker_color=bar_colors,
        text=[f"{v:.3f}" for v in merged["overall_intensity"]],
        textposition="outside",
        textfont=dict(size=9),
    ))
    style_figure(
        fig,
        "States Ranked by Overall Agentic Intensity",
        subtitle="Overall: agentic workers / confirmed workers | Color = agentic cluster",
        x_title="Agentic Intensity Ratio",
        show_legend=False,
        height=1200,
        width=800,
    )
    fig.update_layout(
        xaxis=dict(showgrid=False, showticklabels=True),
        yaxis=dict(showgrid=False, tickfont=dict(size=8)),
        margin=dict(l=30, r=80, t=90, b=40),
    )
    return fig


def _build_vs_sector_comp(
    assignments: pd.DataFrame,
    sector_clusters: pd.DataFrame,
) -> go.Figure:
    merged = assignments.merge(
        sector_clusters[["geo", "cluster_label"]].rename(columns={"cluster_label": "sector_cluster"}),
        on="geo", how="inner",
    )
    cross = pd.crosstab(merged["sector_cluster"], merged["ag_cluster"])
    sector_order = sorted(cross.index.tolist())
    ag_order     = sorted(cross.columns.tolist())
    cross = cross.reindex(index=sector_order, columns=ag_order, fill_value=0)

    fig = go.Figure(go.Heatmap(
        z=cross.values,
        x=ag_order,
        y=sector_order,
        colorscale=[[0, "#f0f4f8"], [0.5, COLORS["primary"]], [1.0, "#0d2b45"]],
        text=[[str(v) for v in row] for row in cross.values],
        texttemplate="%{text}",
        textfont=dict(size=13, color="white", family=FONT_FAMILY),
        showscale=True,
        colorbar=dict(title="# States"),
    ))
    style_figure(
        fig,
        "Sector-Composition Clusters vs. Agentic-Profile Clusters",
        subtitle="Each cell = number of states in that (sector, agentic) cluster pair",
        show_legend=False,
        height=420,
        width=750,
    )
    fig.update_layout(
        xaxis=dict(side="bottom", showgrid=False, title="Agentic-Profile Cluster"),
        yaxis=dict(showgrid=False, title="Sector-Composition Cluster"),
        margin=dict(l=130, r=40, t=90, b=60),
    )
    return fig


# ── Main ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("agentic_profile: building state agentic-intensity features...")
    features, sector_cols = build_state_agentic_features()
    assert not features.empty, "No state features built"
    print(f"  {len(features)} states/territories, {len(sector_cols)} sector features.")

    col_to_cat = features.attrs.get("col_to_cat", {})

    # Save full feature table with readable sector names
    feat_export = features.copy()
    feat_export = feat_export.rename(columns=col_to_cat)
    save_csv(feat_export, results / "state_agentic_features.csv")

    print("agentic_profile: clustering...")
    assignments, profiles = run_clustering(features, sector_cols)
    save_csv(assignments, results / "cluster_assignments.csv")

    profiles_export = profiles.copy().rename(columns=col_to_cat)
    save_csv(profiles_export, results / "cluster_profiles.csv")

    save_csv(
        features[["geo", "overall_intensity"]].merge(assignments, on="geo"),
        results / "overall_agentic_share.csv",
    )

    print("  Agentic cluster distribution:")
    for cl, sub in assignments.groupby("ag_cluster"):
        avg_int = features[features["geo"].isin(sub["geo"])]["overall_intensity"].mean()
        print(f"    {cl}: {len(sub)} states, avg intensity = {avg_int:.3f}")

    sector_clusters = load_sector_clusters()
    comparison = assignments.merge(
        sector_clusters[["geo", "cluster_label"]].rename(columns={"cluster_label": "sector_cluster"}),
        on="geo", how="left",
    )
    save_csv(comparison, results / "vs_sector_composition.csv")

    # Figures
    print("agentic_profile: building figures...")

    fig_heat = _build_intensity_heatmap(features, assignments, sector_cols, col_to_cat)
    save_figure(fig_heat, results / "figures" / "agentic_intensity_heatmap.png")
    shutil.copy(results / "figures" / "agentic_intensity_heatmap.png",
                figs_dir / "agentic_intensity_heatmap.png")
    print("  agentic_intensity_heatmap.png")

    fig_profiles = _build_cluster_profiles_chart(profiles, sector_cols, col_to_cat)
    save_figure(fig_profiles, results / "figures" / "cluster_profiles.png")
    shutil.copy(results / "figures" / "cluster_profiles.png", figs_dir / "cluster_profiles.png")
    print("  cluster_profiles.png")

    fig_bar = _build_overall_bar(features, assignments)
    save_figure(fig_bar, results / "figures" / "overall_agentic_bar.png")
    shutil.copy(results / "figures" / "overall_agentic_bar.png",
                figs_dir / "overall_agentic_bar.png")
    print("  overall_agentic_bar.png")

    fig_vs = _build_vs_sector_comp(assignments, sector_clusters)
    save_figure(fig_vs, results / "figures" / "vs_sector_comp.png")
    shutil.copy(results / "figures" / "vs_sector_comp.png", figs_dir / "vs_sector_comp.png")
    print("  vs_sector_comp.png")

    print("\n-- Agentic intensity summary --")
    print(f"  Overall avg intensity: {features['overall_intensity'].mean():.3f}")
    hi = features.loc[features["overall_intensity"].idxmax()]
    lo = features.loc[features["overall_intensity"].idxmin()]
    print(f"  Highest: {hi['geo'].upper()} ({hi['overall_intensity']:.3f})")
    print(f"  Lowest:  {lo['geo'].upper()} ({lo['overall_intensity']:.3f})")

    report_path = HERE / "agentic_profile_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "agentic_profile_report.pdf")

    print("\nagentic_profile: done.")


if __name__ == "__main__":
    main()
