"""
run.py — Source Agreement: Ranking Agreement

Where do the four sources agree and disagree on which occupations are most AI-exposed?

Computes Spearman rank correlations and confidence tiers across all four sources at
major, minor, broad, and occupation levels. Also analyzes WA (GWA/IWA) for the three
eco_2025 sources.

Run from project root:
    venv/Scripts/python -m analysis.questions.source_agreement.ranking_agreement.run
"""
from __future__ import annotations

import shutil
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

from analysis.config import ensure_results_dir
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent

# Four sources — exact dataset names and display labels
SOURCES = {
    "human_conv": ("AEI Conv + Micro 2026-02-12", "Human Conv."),
    "aei_api":    ("AEI API 2026-02-12",           "Agentic (AEI API)"),
    "microsoft":  ("Microsoft",                    "Microsoft"),
    "mcp":        ("MCP Cumul. v4",                "MCP"),
}

# Colors per source
SOURCE_COLORS = {
    "human_conv": COLORS["aei"],
    "aei_api":    COLORS["secondary"],
    "microsoft":  COLORS["microsoft"],
    "mcp":        COLORS["mcp"],
}

# eco_2025 sources (for WA analysis — same baseline, directly comparable)
ECO2025_SOURCES = ["human_conv", "microsoft", "mcp"]

# Confidence-tier top-N thresholds by level
TOP_N = {"major": 10, "minor": 20, "broad": 20, "occ": 30}


# ── Data helpers ────────────────────────────────────────────────────────────────

def get_occ_data(dataset_name: str, agg_level: str) -> pd.DataFrame:
    """Return data at the requested aggregation level for a single dataset."""
    from backend.compute import get_group_data

    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": "nat",
        "agg_level": agg_level,
        "sort_by": "Workers Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    assert data is not None, f"No data for {dataset_name} at {agg_level}"
    group_col = data["group_col"]
    df = data["df"].rename(columns={group_col: "category"})
    return df[["category", "pct_tasks_affected", "workers_affected", "wages_affected"]].copy()


def get_wa_data(dataset_name: str, level: str = "gwa") -> pd.DataFrame:
    """Return WA data for a single dataset. level: 'gwa' or 'iwa'."""
    from backend.compute import compute_work_activities
    settings = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": "nat",
        "sort_by": "workers_affected",
        "top_n": 9999,
    }
    result = compute_work_activities(settings)
    group = result.get("mcp_group") or result.get("aei_group")
    if group is None:
        return pd.DataFrame()
    rows = group.get(level, [])
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ── Compute helpers ──────────────────────────────────────────────────────────────

def build_wide_df(level: str) -> pd.DataFrame:
    """Merge all four sources side by side for a given agg level."""
    frames = []
    for key, (ds_name, label) in SOURCES.items():
        df = get_occ_data(ds_name, level)
        df = df.rename(columns={"pct_tasks_affected": f"pct_{key}"})
        frames.append(df[["category", f"pct_{key}"]])
    wide = frames[0]
    for df in frames[1:]:
        wide = wide.merge(df, on="category", how="outer")
    return wide


def compute_spearman_pairs(wide: pd.DataFrame, source_keys: list[str]) -> list[dict]:
    """Compute all pairwise Spearman correlations from wide df."""
    rows = []
    for a, b in combinations(source_keys, 2):
        col_a, col_b = f"pct_{a}", f"pct_{b}"
        merged = wide[[col_a, col_b]].dropna()
        if len(merged) < 3:
            continue
        rho, pval = stats.spearmanr(merged[col_a], merged[col_b])
        rows.append({
            "source_a": a,
            "source_b": b,
            "label_a": SOURCES[a][1],
            "label_b": SOURCES[b][1],
            "pair": f"{SOURCES[a][1]} vs {SOURCES[b][1]}",
            "rho": round(float(rho), 3),
            "pval": round(float(pval), 4),
            "n": len(merged),
        })
    return rows


def compute_confidence_tiers(wide: pd.DataFrame, source_keys: list[str], top_n: int) -> pd.DataFrame:
    """Assign confidence tiers based on how many sources place each category in their top-N."""
    result = wide.copy()
    for key in source_keys:
        col = f"pct_{key}"
        if col in result.columns:
            result[f"rank_{key}"] = result[col].rank(ascending=False, method="min")
            result[f"intop_{key}"] = (result[f"rank_{key}"] <= top_n).astype(int)

    intop_cols = [f"intop_{k}" for k in source_keys if f"intop_{k}" in result.columns]
    result["confidence_count"] = result[intop_cols].sum(axis=1)

    def tier_label(n: int) -> str:
        if n == 4:
            return "High (4/4)"
        if n == 3:
            return "Moderate (3/4)"
        if n == 2:
            return "Low (2/4)"
        if n == 1:
            return "Single-source (1/4)"
        return "None (0/4)"

    result["confidence_tier"] = result["confidence_count"].apply(tier_label)
    return result


# ── Figure builders ──────────────────────────────────────────────────────────────

def _build_correlation_heatmap_panel(spearman_rows: list[dict], levels: list[str]) -> go.Figure:
    """4-panel heatmap: one correlation matrix per aggregation level."""
    labels = [SOURCES[k][1] for k in SOURCES]
    source_keys = list(SOURCES.keys())
    n = len(source_keys)

    from plotly.subplots import make_subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[f"{lv.title()} level" for lv in levels],
        horizontal_spacing=0.12,
        vertical_spacing=0.15,
    )

    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]

    for idx, level in enumerate(levels):
        level_rows = [r for r in spearman_rows if r["level"] == level]
        # Build correlation matrix
        matrix = np.ones((n, n))
        for r in level_rows:
            i = source_keys.index(r["source_a"])
            j = source_keys.index(r["source_b"])
            matrix[i][j] = r["rho"]
            matrix[j][i] = r["rho"]

        row, col = positions[idx]
        heatmap = go.Heatmap(
            z=matrix,
            x=labels,
            y=labels,
            colorscale=[[0, "#f0e6d3"], [0.5, COLORS["primary"]], [1.0, "#0d2b45"]],
            zmin=0.4, zmax=1.0,
            text=[[f"{v:.2f}" for v in row_vals] for row_vals in matrix],
            texttemplate="%{text}",
            textfont=dict(size=11, color="white", family=FONT_FAMILY),
            showscale=(idx == 3),
            colorbar=dict(title="Spearman ρ", len=0.45, y=0.2) if idx == 3 else None,
            name=level,
        )
        fig.add_trace(heatmap, row=row, col=col)

    style_figure(
        fig,
        "Spearman Rank Correlation Between Sources",
        subtitle="All four sources | pct_tasks_affected | Each panel = aggregation level",
        show_legend=False,
        height=900,
        width=1100,
    )
    fig.update_layout(margin=dict(l=60, r=60, t=100, b=80))
    return fig


def _build_confidence_tiers_bar(tier_summary: pd.DataFrame) -> go.Figure:
    """Stacked bar: % of categories at each confidence tier, per agg level."""
    tier_order = ["High (4/4)", "Moderate (3/4)", "Low (2/4)", "Single-source (1/4)", "None (0/4)"]
    tier_colors_map = {
        "High (4/4)":           COLORS["positive"],
        "Moderate (3/4)":       COLORS["primary"],
        "Low (2/4)":            COLORS["secondary"],
        "Single-source (1/4)":  COLORS["accent"],
        "None (0/4)":           COLORS["muted"],
    }

    levels = tier_summary["level"].unique().tolist()
    fig = go.Figure()

    for tier in tier_order:
        vals = []
        for lv in levels:
            sub = tier_summary[(tier_summary["level"] == lv) & (tier_summary["confidence_tier"] == tier)]
            vals.append(float(sub["pct_of_level"].values[0]) if len(sub) > 0 else 0.0)
        fig.add_trace(go.Bar(
            name=tier,
            x=levels,
            y=vals,
            marker_color=tier_colors_map.get(tier, COLORS["muted"]),
            text=[f"{v:.0f}%" if v >= 3 else "" for v in vals],
            textposition="inside",
            textfont=dict(size=11, color="white", family=FONT_FAMILY),
        ))

    style_figure(
        fig,
        "Confidence Tiers by Aggregation Level",
        subtitle="High = 4/4 sources agree on top placement | degrades at finer levels",
        y_title="% of categories",
        height=550,
        width=900,
    )
    fig.update_layout(
        barmode="stack",
        xaxis=dict(
            categoryorder="array",
            categoryarray=["major", "minor", "broad", "occ"],
            showgrid=False,
        ),
        yaxis=dict(showgrid=True, range=[0, 105]),
        bargap=0.3,
    )
    return fig


def _build_major_rank_comparison(major_wide: pd.DataFrame) -> go.Figure:
    """Grouped bar: all major categories, one bar per source, pct_tasks_affected side by side."""
    source_keys = list(SOURCES.keys())
    categories = major_wide["category"].tolist()

    fig = go.Figure()
    for key in source_keys:
        col = f"pct_{key}"
        fig.add_trace(go.Bar(
            name=SOURCES[key][1],
            x=categories,
            y=major_wide[col].fillna(0).tolist(),
            marker_color=SOURCE_COLORS[key],
            opacity=0.85,
        ))

    style_figure(
        fig,
        "Major Category Rankings — All Four Sources",
        subtitle="% tasks affected per source | categories ordered by Human Conv. rank",
        y_title="% Tasks Affected",
        height=600,
        width=1300,
    )
    fig.update_layout(
        barmode="group",
        xaxis=dict(tickangle=-45, showgrid=False, tickfont=dict(size=9)),
        yaxis=dict(showgrid=True),
        bargap=0.15,
        bargroupgap=0.05,
        margin=dict(b=180),
    )
    return fig


def _build_major_rank_heatmap(major_wide: pd.DataFrame) -> go.Figure:
    """Heatmap: rank of each major category across 4 sources."""
    source_keys = list(SOURCES.keys())
    rank_df = major_wide.set_index("category")[[f"pct_{k}" for k in source_keys]].copy()

    # Rank: 1 = highest pct (most exposed)
    for k in source_keys:
        rank_df[f"rank_{k}"] = rank_df[f"pct_{k}"].rank(ascending=False, method="min")

    rank_matrix = rank_df[[f"rank_{k}" for k in source_keys]].values
    # Sort rows by mean rank
    mean_rank = rank_matrix.mean(axis=1)
    order = np.argsort(mean_rank)
    sorted_cats = rank_df.index[order].tolist()
    sorted_matrix = rank_matrix[order]

    col_labels = [SOURCES[k][1] for k in source_keys]

    fig = go.Figure(go.Heatmap(
        z=sorted_matrix,
        x=col_labels,
        y=sorted_cats,
        colorscale=[[0, "#0d2b45"], [0.5, COLORS["primary"]], [1.0, "#f0f4f8"]],
        text=[[f"{int(v)}" for v in row_vals] for row_vals in sorted_matrix],
        texttemplate="%{text}",
        textfont=dict(size=10, color="white", family=FONT_FAMILY),
        showscale=True,
        colorbar=dict(title="Rank (1=top)", tickfont=dict(size=10)),
        hovertemplate="%{y} | %{x}: rank %{z}<extra></extra>",
    ))

    style_figure(
        fig,
        "Major Category Rank by Source",
        subtitle="Rank 1 = most AI-exposed major group | dark = top rank | sorted by mean rank across sources",
        show_legend=False,
        height=700,
        width=900,
    )
    fig.update_layout(
        xaxis=dict(side="bottom", showgrid=False, showline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        margin=dict(l=280, r=80, t=90, b=80),
    )
    return fig


def _build_wa_gwa_comparison(gwa_wide: pd.DataFrame) -> go.Figure:
    """Grouped bar: GWA level, three eco_2025 sources only."""
    eco_keys = ECO2025_SOURCES
    gwa_wide = gwa_wide.sort_values(f"pct_{eco_keys[0]}", ascending=False)
    categories = gwa_wide["category"].tolist()

    fig = go.Figure()
    for key in eco_keys:
        col = f"pct_{key}"
        fig.add_trace(go.Bar(
            name=SOURCES[key][1],
            x=categories,
            y=gwa_wide[col].fillna(0).tolist(),
            marker_color=SOURCE_COLORS[key],
            opacity=0.85,
        ))

    style_figure(
        fig,
        "GWA Rankings — Three eco_2025 Sources",
        subtitle="% tasks affected at General Work Activity level | Human Conv., Microsoft, MCP only (same O*NET baseline)",
        y_title="% Tasks Affected",
        height=600,
        width=1200,
    )
    fig.update_layout(
        barmode="group",
        xaxis=dict(tickangle=-45, showgrid=False, tickfont=dict(size=9)),
        yaxis=dict(showgrid=True),
        bargap=0.2,
        margin=dict(b=200),
    )
    return fig


def _save(fig: go.Figure, results_path: Path, figures_path: Path) -> None:
    save_figure(fig, results_path)
    shutil.copy(str(results_path), str(figures_path))


# ── Main ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("ranking_agreement: loading data...")

    # ── 1. Load occupation/category data at all 4 aggregation levels ──────────
    levels = ["major", "minor", "broad", "occupation"]
    source_keys = list(SOURCES.keys())

    # Wide dataframes per level
    wide: dict[str, pd.DataFrame] = {}
    for lv in levels:
        print(f"  {lv}...")
        wide[lv] = build_wide_df(lv)

    # ── 2. Compute Spearman correlations per level ────────────────────────────
    spearman_rows: list[dict] = []
    for lv in levels:
        pairs = compute_spearman_pairs(wide[lv], source_keys)
        for r in pairs:
            r["level"] = lv
        spearman_rows.extend(pairs)

    spearman_df = pd.DataFrame(spearman_rows)
    level_display = {"major": "Major", "minor": "Minor", "broad": "Broad", "occupation": "Occupation"}
    spearman_df["level_label"] = spearman_df["level"].map(level_display)
    save_csv(spearman_df[["level", "level_label", "pair", "source_a", "source_b", "rho", "pval", "n"]], results / "spearman_by_level.csv")
    print("  spearman_by_level.csv saved")

    # Print summary
    for lv in levels:
        sub = spearman_df[spearman_df["level"] == lv]
        print(f"  {lv}: mean rho={sub['rho'].mean():.3f}, min={sub['rho'].min():.3f}, max={sub['rho'].max():.3f}")

    # ── 3. Confidence tiers per level ─────────────────────────────────────────
    tier_summary_rows: list[dict] = []
    for lv in levels:
        lv_key = "occ" if lv == "occupation" else lv
        tn = TOP_N.get(lv_key, 20)
        conf_df = compute_confidence_tiers(wide[lv], source_keys, tn)
        tier_counts = conf_df.groupby("confidence_tier").size().reset_index(name="n")
        tier_counts["level"] = lv_key
        tier_counts["pct_of_level"] = tier_counts["n"] / len(conf_df) * 100
        tier_summary_rows.append(tier_counts)

        # Save per-level confidence CSV
        out_name = f"confidence_{lv_key}.csv"
        save_csv(conf_df, results / out_name)

    tier_summary = pd.concat(tier_summary_rows, ignore_index=True)
    save_csv(tier_summary, results / "tier_summary.csv")
    print("  confidence CSVs saved")

    # ── 4. WA data — GWA and IWA for eco_2025 sources ────────────────────────
    print("  Loading WA data for eco_2025 sources...")
    gwa_frames: list[pd.DataFrame] = []
    iwa_frames: list[pd.DataFrame] = []

    for key in ECO2025_SOURCES:
        ds_name = SOURCES[key][0]
        gdf = get_wa_data(ds_name, "gwa")
        idf = get_wa_data(ds_name, "iwa")
        if not gdf.empty:
            gdf = gdf.rename(columns={"pct_tasks_affected": f"pct_{key}"})[["category", f"pct_{key}"]]
            gwa_frames.append(gdf)
        if not idf.empty:
            idf = idf.rename(columns={"pct_tasks_affected": f"pct_{key}"})[["category", f"pct_{key}"]]
            iwa_frames.append(idf)

    gwa_wide: pd.DataFrame = pd.DataFrame()
    iwa_wide: pd.DataFrame = pd.DataFrame()

    if gwa_frames:
        gwa_wide = gwa_frames[0]
        for df in gwa_frames[1:]:
            gwa_wide = gwa_wide.merge(df, on="category", how="outer")
        save_csv(gwa_wide, results / "wa_gwa_comparison.csv")
        print(f"  GWA wide: {len(gwa_wide)} rows")

    if iwa_frames:
        iwa_wide = iwa_frames[0]
        for df in iwa_frames[1:]:
            iwa_wide = iwa_wide.merge(df, on="category", how="outer")
        save_csv(iwa_wide, results / "wa_iwa_comparison.csv")
        print(f"  IWA wide: {len(iwa_wide)} rows")

    # WA Spearman correlations (eco_2025 sources)
    if not gwa_wide.empty:
        wa_spearman = compute_spearman_pairs(gwa_wide, ECO2025_SOURCES)
        for r in wa_spearman:
            r["level"] = "gwa"
        wa_spearman_df = pd.DataFrame(wa_spearman)
        save_csv(wa_spearman_df, results / "wa_gwa_spearman.csv")

    # ── 5. Major rank data ────────────────────────────────────────────────────
    major_wide = wide["major"].sort_values("pct_human_conv", ascending=False)

    # ── 6. Figures ─────────────────────────────────────────────────────────────
    print("  Building figures...")

    # Remap level names for the figure
    spearman_fig_rows = []
    for r in spearman_rows:
        r2 = r.copy()
        r2["level"] = "occ" if r["level"] == "occupation" else r["level"]
        spearman_fig_rows.append(r2)

    # 6a. Correlation matrix by level
    fig_corr = _build_correlation_heatmap_panel(spearman_fig_rows, ["major", "minor", "broad", "occ"])
    _save(fig_corr, results / "figures" / "correlation_matrix_by_level.png", figs_dir / "correlation_matrix_by_level.png")
    print("  correlation_matrix_by_level.png")

    # 6b. Confidence tiers bar
    # Normalize level names
    tier_summary["level"] = tier_summary["level"].replace({"occupation": "occ"})
    fig_tiers = _build_confidence_tiers_bar(tier_summary)
    _save(fig_tiers, results / "figures" / "confidence_tiers.png", figs_dir / "confidence_tiers.png")
    print("  confidence_tiers.png")

    # 6c. Major rank comparison (grouped bar)
    fig_major_bar = _build_major_rank_comparison(major_wide)
    _save(fig_major_bar, results / "figures" / "major_rank_comparison.png", figs_dir / "major_rank_comparison.png")
    print("  major_rank_comparison.png")

    # 6d. Major rank heatmap
    fig_major_heat = _build_major_rank_heatmap(major_wide)
    _save(fig_major_heat, results / "figures" / "major_rank_heatmap.png", figs_dir / "major_rank_heatmap.png")
    print("  major_rank_heatmap.png")

    # 6e. WA GWA comparison
    if not gwa_wide.empty:
        fig_wa = _build_wa_gwa_comparison(gwa_wide)
        _save(fig_wa, results / "figures" / "wa_gwa_rank_comparison.png", figs_dir / "wa_gwa_rank_comparison.png")
        print("  wa_gwa_rank_comparison.png")

    # ── 7. Print key stats for report ─────────────────────────────────────────
    print("\n-- Key stats --")
    # High confidence categories at major level
    major_conf = compute_confidence_tiers(wide["major"], source_keys, TOP_N["major"])
    high_conf = major_conf[major_conf["confidence_count"] == 4]["category"].tolist()
    low_conf = major_conf[major_conf["confidence_count"] <= 1]["category"].tolist()
    print(f"  Major high-confidence (4/4): {high_conf}")
    print(f"  Major single/no-source: {low_conf}")

    # Mean rho by level
    for lv in ["major", "minor", "broad", "occupation"]:
        sub = spearman_df[spearman_df["level"] == lv]
        print(f"  {lv} mean rho: {sub['rho'].mean():.3f}")

    # ── 8. PDF ────────────────────────────────────────────────────────────────
    report_md = HERE / "ranking_agreement_report.md"
    if report_md.exists():
        generate_pdf(report_md, results / "ranking_agreement_report.pdf")

    print("\nranking_agreement: done.")


if __name__ == "__main__":
    main()
