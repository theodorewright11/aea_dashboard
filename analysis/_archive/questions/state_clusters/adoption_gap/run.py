"""
run.py — State Clusters: Adoption Gap

Cluster U.S. states by the shape of their AI adoption gap — specifically, the
relative gap between the confirmed-usage ceiling and current confirmed usage,
broken down by major sector.

"Adoption gap" here means: if AI already reaches this many workers (confirmed),
how many MORE could it reach if all demonstrated capability were adopted
(ceiling)? Some sectors have large relative gaps (MCP-dominated tool use not
yet reflected in confirmed usage); others are nearly closed. States differ in
how their adoption gap is distributed across sectors — and those differences
cluster in identifiable ways.

Feature construction: for each state × major sector:
    gap_ratio = (ceiling_workers - confirmed_workers) / confirmed_workers

    where:
        ceiling_workers   = sum(pct_ceiling[occ]/100   × emp[state,occ]) for occs in sector
        confirmed_workers = sum(pct_confirmed[occ]/100 × emp[state,occ]) for occs in sector

    Clipped at 0 (no negative gaps). Sectors with <100 confirmed workers in a
    state are excluded from ratio computation for that state.

Datasets:
  - all_confirmed  (AEI Both + Micro 2026-02-12) — current confirmed baseline
  - all_ceiling    (All 2026-02-18)               — full capability ceiling

Outputs:
  results/state_gap_features.csv      — Per-state gap ratio by sector
  results/cluster_assignments.csv     — State → cluster (gap-based)
  results/cluster_profiles.csv        — Per-cluster avg gap ratio by sector
  results/vs_sector_composition.csv   — Both cluster assignments side-by-side
  results/overall_gap.csv             — Overall gap ratio + absolute workers per state

Figures (committed to figures/):
  gap_heatmap.png        — State × sector gap ratios, sorted by cluster
  cluster_profiles.png   — Avg gap ratio per sector per cluster
  vs_sector_comp.png     — Sector clusters vs gap clusters (tile count)
  overall_gap_bar.png    — States ranked by overall gap ratio

Run from project root:
    venv/Scripts/python -m analysis.questions.state_clusters.adoption_gap.run
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
CONFIRMED_KEY = "all_confirmed"
CEILING_KEY   = "all_ceiling"
MIN_CONFIRMED_WORKERS = 100.0  # minimum confirmed workers in sector to include ratio

CLUSTER_COLORS = {
    f"Gap-{i + 1}": CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)]
    for i in range(N_CLUSTERS)
}


# ── Data helpers ─────────────────────────────────────────────────────────────────

def load_sector_clusters() -> pd.DataFrame:
    path = STATE_PROFILES_DIR / "results" / "cluster_assignments.csv"
    assert path.exists(), f"cluster_assignments.csv not found at {path}"
    return pd.read_csv(path)


def build_state_gap_features() -> tuple[pd.DataFrame, list[str]]:
    """
    Build state × sector adoption-gap feature matrix.

    Returns (feature_df, list_of_sector_feature_cols).
    """
    from backend.compute import load_eco_raw

    print("  Loading pct_tasks_affected for confirmed and ceiling configs...")
    pct_confirmed = get_pct_tasks_affected(ANALYSIS_CONFIGS[CONFIRMED_KEY])
    pct_ceiling   = get_pct_tasks_affected(ANALYSIS_CONFIGS[CEILING_KEY])

    eco = load_eco_raw()
    assert eco is not None, "eco_raw not found"
    assert "title_current" in eco.columns
    assert "major_occ_category" in eco.columns

    occ_df = eco.groupby("title_current").first().reset_index()

    state_geos = sorted([
        col.replace("emp_tot_", "").replace("_2024", "")
        for col in occ_df.columns
        if col.startswith("emp_tot_") and col.endswith("_2024")
        and col.replace("emp_tot_", "").replace("_2024", "") not in ("nat", "")
    ])

    occ_df["pct_confirmed"] = occ_df["title_current"].map(pct_confirmed).fillna(0.0)
    occ_df["pct_ceiling"]   = occ_df["title_current"].map(pct_ceiling).fillna(0.0)

    major_cats  = sorted(occ_df["major_occ_category"].dropna().unique().tolist())
    sector_cols = [f"sector_{i}" for i in range(len(major_cats))]
    sector_map  = {cat: col for cat, col in zip(major_cats, sector_cols)}
    col_to_cat  = {col: cat for cat, col in sector_map.items()}

    rows = []
    for geo in state_geos:
        emp_col = f"emp_tot_{geo}_2024"
        if emp_col not in occ_df.columns:
            continue

        emp = pd.to_numeric(occ_df[emp_col], errors="coerce").fillna(0.0)
        conf_w    = (occ_df["pct_confirmed"] / 100.0) * emp
        ceiling_w = (occ_df["pct_ceiling"]   / 100.0) * emp

        total_conf    = conf_w.sum()
        total_ceiling = ceiling_w.sum()
        if total_conf <= 0:
            continue

        row: dict = {
            "geo": geo,
            "total_confirmed_workers": round(total_conf, 0),
            "total_ceiling_workers":   round(total_ceiling, 0),
            "overall_gap_ratio": round(
                float(np.clip((total_ceiling - total_conf) / total_conf, 0.0, None)), 4
            ),
        }

        for cat in major_cats:
            mask  = occ_df["major_occ_category"] == cat
            c_sum = conf_w[mask].sum()
            k_sum = ceiling_w[mask].sum()
            if c_sum >= MIN_CONFIRMED_WORKERS:
                ratio = float(np.clip((k_sum - c_sum) / c_sum, 0.0, None))
            else:
                ratio = 0.0
            row[sector_map[cat]] = round(ratio, 4)

        rows.append(row)

    feat_df = pd.DataFrame(rows).sort_values("geo").reset_index(drop=True)

    variance = feat_df[sector_cols].var()
    valid_sector_cols = variance[variance > 1e-6].index.tolist()

    feat_df.attrs["col_to_cat"] = col_to_cat
    feat_df.attrs["major_cats"] = major_cats
    feat_df.attrs["sector_map"] = sector_map

    return feat_df, valid_sector_cols


# ── Clustering ───────────────────────────────────────────────────────────────────

def run_clustering(
    features: pd.DataFrame,
    sector_cols: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    X = features[sector_cols].fillna(0.0).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    km = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=20)
    labels = km.fit_predict(X_scaled)

    # Order by descending overall gap ratio
    order = (
        features.assign(_label=labels)
        .groupby("_label")["overall_gap_ratio"]
        .mean()
        .sort_values(ascending=False)
        .index.tolist()
    )
    rank_map = {old: new for new, old in enumerate(order)}
    mapped = [rank_map[l] for l in labels]

    assignments = features[["geo"]].copy()
    assignments["gap_cluster_id"] = mapped
    assignments["gap_cluster"] = [f"Gap-{x + 1}" for x in mapped]

    profiles = (
        features.assign(_label=mapped)
        .groupby("_label")[sector_cols + ["overall_gap_ratio"]]
        .mean()
        .reset_index()
        .rename(columns={"_label": "gap_cluster_id"})
    )
    profiles["gap_cluster"] = profiles["gap_cluster_id"].apply(lambda x: f"Gap-{x + 1}")
    return assignments, profiles


# ── Figures ──────────────────────────────────────────────────────────────────────

def _build_gap_heatmap(
    features: pd.DataFrame,
    assignments: pd.DataFrame,
    sector_cols: list[str],
    col_to_cat: dict,
) -> go.Figure:
    merged = features.merge(assignments[["geo", "gap_cluster", "gap_cluster_id"]], on="geo")
    merged = merged.sort_values(["gap_cluster_id", "geo"])

    z_vals   = merged[sector_cols].values
    y_labels = [f"{row['gap_cluster']} | {row['geo'].upper()}" for _, row in merged.iterrows()]
    x_labels = [col_to_cat.get(c, c)[:35] for c in sector_cols]

    fig = go.Figure(go.Heatmap(
        z=z_vals,
        x=x_labels,
        y=y_labels,
        colorscale=[[0, "#f0f4f8"], [0.4, COLORS["accent"]], [1.0, "#d62728"]],
        text=[[f"{v:.2f}" for v in row] for row in z_vals],
        texttemplate="%{text}",
        textfont=dict(size=7, color="black", family=FONT_FAMILY),
        hovertemplate="<b>%{y}</b><br>%{x}: %{z:.3f} gap ratio<extra></extra>",
        showscale=True,
        colorbar=dict(title="Gap Ratio<br>(ceiling/confirmed − 1)", tickfont=dict(size=9)),
    ))
    style_figure(
        fig,
        "State Adoption Gap by Sector",
        subtitle=(
            "Gap ratio = (ceiling workers − confirmed workers) / confirmed workers per sector | "
            f"{ANALYSIS_CONFIG_LABELS[CEILING_KEY]} vs {ANALYSIS_CONFIG_LABELS[CONFIRMED_KEY]}"
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
    x_labels = [col_to_cat.get(c, c)[:30] for c in sector_cols]
    fig = go.Figure()
    for _, row in profiles.sort_values("gap_cluster_id").iterrows():
        fig.add_trace(go.Bar(
            x=x_labels,
            y=[row[c] for c in sector_cols],
            name=row["gap_cluster"],
            marker_color=CLUSTER_COLORS.get(row["gap_cluster"], COLORS["primary"]),
        ))
    style_figure(
        fig,
        "Adoption-Gap Cluster Profiles",
        subtitle="Average gap ratio by sector per cluster (ceiling / confirmed − 1)",
        y_title="Gap Ratio",
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


def _build_overall_gap_bar(features: pd.DataFrame, assignments: pd.DataFrame) -> go.Figure:
    merged = features[["geo", "overall_gap_ratio"]].merge(
        assignments[["geo", "gap_cluster"]], on="geo"
    ).sort_values("overall_gap_ratio", ascending=True)

    bar_colors = [
        CLUSTER_COLORS.get(cl, COLORS["primary"]) for cl in merged["gap_cluster"]
    ]
    fig = go.Figure(go.Bar(
        x=merged["overall_gap_ratio"],
        y=merged["geo"],
        orientation="h",
        marker_color=bar_colors,
        text=[f"{v:.3f}" for v in merged["overall_gap_ratio"]],
        textposition="outside",
        textfont=dict(size=9),
    ))
    style_figure(
        fig,
        "States Ranked by Overall Adoption Gap Ratio",
        subtitle="(Ceiling workers − confirmed workers) / confirmed workers | Color = gap cluster",
        x_title="Adoption Gap Ratio",
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
    cross = pd.crosstab(merged["sector_cluster"], merged["gap_cluster"])
    sector_order = sorted(cross.index.tolist())
    gap_order    = sorted(cross.columns.tolist())
    cross = cross.reindex(index=sector_order, columns=gap_order, fill_value=0)

    fig = go.Figure(go.Heatmap(
        z=cross.values,
        x=gap_order,
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
        "Sector-Composition Clusters vs. Adoption-Gap Clusters",
        subtitle="Each cell = number of states in that (sector, gap) cluster pair",
        show_legend=False,
        height=420,
        width=750,
    )
    fig.update_layout(
        xaxis=dict(side="bottom", showgrid=False, title="Adoption-Gap Cluster"),
        yaxis=dict(showgrid=False, title="Sector-Composition Cluster"),
        margin=dict(l=130, r=40, t=90, b=60),
    )
    return fig


# ── Main ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("adoption_gap: building state gap features...")
    features, sector_cols = build_state_gap_features()
    assert not features.empty, "No state features built"
    print(f"  {len(features)} states/territories, {len(sector_cols)} sector features.")

    col_to_cat = features.attrs.get("col_to_cat", {})

    feat_export = features.copy().rename(columns=col_to_cat)
    save_csv(feat_export, results / "state_gap_features.csv")

    print("adoption_gap: clustering...")
    assignments, profiles = run_clustering(features, sector_cols)
    save_csv(assignments, results / "cluster_assignments.csv")

    profiles_export = profiles.copy().rename(columns=col_to_cat)
    save_csv(profiles_export, results / "cluster_profiles.csv")

    overall_cols = ["geo", "total_confirmed_workers", "total_ceiling_workers", "overall_gap_ratio"]
    save_csv(
        features[overall_cols].merge(assignments[["geo", "gap_cluster"]], on="geo"),
        results / "overall_gap.csv",
    )

    print("  Gap cluster distribution:")
    for cl, sub in assignments.groupby("gap_cluster"):
        avg_gap = features[features["geo"].isin(sub["geo"])]["overall_gap_ratio"].mean()
        print(f"    {cl}: {len(sub)} states, avg gap ratio = {avg_gap:.3f}")

    sector_clusters = load_sector_clusters()
    comparison = assignments.merge(
        sector_clusters[["geo", "cluster_label"]].rename(columns={"cluster_label": "sector_cluster"}),
        on="geo", how="left",
    )
    save_csv(comparison, results / "vs_sector_composition.csv")

    # Figures
    print("adoption_gap: building figures...")

    fig_heat = _build_gap_heatmap(features, assignments, sector_cols, col_to_cat)
    save_figure(fig_heat, results / "figures" / "gap_heatmap.png")
    shutil.copy(results / "figures" / "gap_heatmap.png", figs_dir / "gap_heatmap.png")
    print("  gap_heatmap.png")

    fig_profiles = _build_cluster_profiles_chart(profiles, sector_cols, col_to_cat)
    save_figure(fig_profiles, results / "figures" / "cluster_profiles.png")
    shutil.copy(results / "figures" / "cluster_profiles.png", figs_dir / "cluster_profiles.png")
    print("  cluster_profiles.png")

    fig_bar = _build_overall_gap_bar(features, assignments)
    save_figure(fig_bar, results / "figures" / "overall_gap_bar.png")
    shutil.copy(results / "figures" / "overall_gap_bar.png", figs_dir / "overall_gap_bar.png")
    print("  overall_gap_bar.png")

    fig_vs = _build_vs_sector_comp(assignments, sector_clusters)
    save_figure(fig_vs, results / "figures" / "vs_sector_comp.png")
    shutil.copy(results / "figures" / "vs_sector_comp.png", figs_dir / "vs_sector_comp.png")
    print("  vs_sector_comp.png")

    print("\n-- Adoption gap summary --")
    print(f"  Overall avg gap ratio: {features['overall_gap_ratio'].mean():.3f}")
    hi = features.loc[features["overall_gap_ratio"].idxmax()]
    lo = features.loc[features["overall_gap_ratio"].idxmin()]
    print(f"  Highest gap: {hi['geo'].upper()} ({hi['overall_gap_ratio']:.3f})")
    print(f"  Lowest gap:  {lo['geo'].upper()} ({lo['overall_gap_ratio']:.3f})")

    report_path = HERE / "adoption_gap_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "adoption_gap_report.pdf")

    print("\nadoption_gap: done.")


if __name__ == "__main__":
    main()
