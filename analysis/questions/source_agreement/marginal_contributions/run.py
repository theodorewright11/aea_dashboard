"""
run.py -- Source Agreement: Marginal Contributions

How much does each new data layer add to the overall AI exposure picture?
What occupations and work activities cross exposure thresholds when agentic
tool-use (API) or MCP data is added?

Run from project root:
    venv/Scripts/python -m analysis.questions.source_agreement.marginal_contributions.run
"""
from __future__ import annotations

import warnings
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from analysis.config import ensure_results_dir, ANALYSIS_CONFIGS
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    CATEGORY_PALETTE,
    save_figure,
    save_csv,
    style_figure,
    generate_pdf,
)

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent

# Three configs for marginal contribution analysis
CONFIGS = {
    "human_conv":    ANALYSIS_CONFIGS["human_conversation"],  # AEI Conv + Micro 2026-02-12
    "all_confirmed": ANALYSIS_CONFIGS["all_confirmed"],       # AEI Both + Micro 2026-02-12
    "all_ceiling":   ANALYSIS_CONFIGS["all_ceiling"],         # All 2026-02-18
}

CONFIG_LABELS = {
    "human_conv":    "Human Conv.",
    "all_confirmed": "All Confirmed",
    "all_ceiling":   "All Ceiling",
}

CONFIG_COLORS = {
    "human_conv":    COLORS["aei"],
    "all_confirmed": COLORS["muted"],
    "all_ceiling":   COLORS["primary"],
}

TIER_LABELS = ["Low", "Restructuring", "Moderate", "High"]


def assign_tier(pct: float) -> str:
    if pct < 20:
        return "Low"
    elif pct < 40:
        return "Restructuring"
    elif pct < 60:
        return "Moderate"
    else:
        return "High"


def get_occ_data(dataset_name: str) -> pd.DataFrame:
    from backend.compute import get_group_data
    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": "nat",
        "agg_level": "occupation",
        "sort_by": "Workers Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    assert data is not None, f"No data for {dataset_name}"
    group_col = data["group_col"]
    df = data["df"].rename(columns={group_col: "category"})
    return df[["category", "pct_tasks_affected", "workers_affected"]].copy()


def get_major_data(dataset_name: str) -> pd.DataFrame:
    from backend.compute import get_group_data
    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": "nat",
        "agg_level": "major",
        "sort_by": "Workers Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    assert data is not None, f"No data for {dataset_name}"
    group_col = data["group_col"]
    df = data["df"].rename(columns={group_col: "category"})
    return df[["category", "pct_tasks_affected", "workers_affected"]].copy()


def get_iwa_data(dataset_name: str) -> pd.DataFrame:
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
    rows = group.get("iwa", [])
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def build_tier_shift_matrix(from_df: pd.DataFrame, to_df: pd.DataFrame) -> pd.DataFrame:
    """Build a 4x4 transition matrix (from_tier -> to_tier) for occupations."""
    merged = from_df.merge(to_df, on="category", suffixes=("_from", "_to"))
    merged = merged.dropna(subset=["pct_tasks_affected_from", "pct_tasks_affected_to"])
    merged["tier_from"] = merged["pct_tasks_affected_from"].apply(assign_tier)
    merged["tier_to"] = merged["pct_tasks_affected_to"].apply(assign_tier)

    matrix = pd.DataFrame(0, index=TIER_LABELS, columns=TIER_LABELS)
    for _, row in merged.iterrows():
        matrix.loc[row["tier_from"], row["tier_to"]] += 1
    return matrix


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("marginal_contributions: loading occupation data...")

    # ── 1. Load occupation-level data for all 3 configs ───────────────────────
    occ_dfs: dict[str, pd.DataFrame] = {}
    major_dfs: dict[str, pd.DataFrame] = {}
    for key, ds_name in CONFIGS.items():
        print(f"  {CONFIG_LABELS[key]}...")
        occ_dfs[key] = get_occ_data(ds_name)
        major_dfs[key] = get_major_data(ds_name)

    # ── 2. Tier assignments ────────────────────────────────────────────────────
    for key in CONFIGS.keys():
        occ_dfs[key]["tier"] = occ_dfs[key]["pct_tasks_affected"].apply(assign_tier)

    # Build wide occupation df with all configs
    wide = occ_dfs["human_conv"].rename(columns={
        "pct_tasks_affected": "pct_human_conv",
        "tier": "tier_human_conv",
        "workers_affected": "workers_human_conv",
    })
    for key in ["all_confirmed", "all_ceiling"]:
        tmp = occ_dfs[key].rename(columns={
            "pct_tasks_affected": f"pct_{key}",
            "tier": f"tier_{key}",
            "workers_affected": f"workers_{key}",
        })
        wide = wide.merge(tmp, on="category", how="outer")

    save_csv(wide.sort_values("pct_human_conv", ascending=False), results / "occ_tier_by_config.csv")
    print("  occ_tier_by_config.csv saved")

    # ── 3. Tier shift matrices ─────────────────────────────────────────────────
    # API effect: human_conv -> all_confirmed
    matrix_api = build_tier_shift_matrix(occ_dfs["human_conv"], occ_dfs["all_confirmed"])
    save_csv(matrix_api.reset_index().rename(columns={"index": "tier_from"}), results / "tier_shift_api.csv")
    print("  tier_shift_api.csv saved")

    # MCP effect: all_confirmed -> all_ceiling
    matrix_mcp = build_tier_shift_matrix(occ_dfs["all_confirmed"], occ_dfs["all_ceiling"])
    save_csv(matrix_mcp.reset_index().rename(columns={"index": "tier_from"}), results / "tier_shift_mcp.csv")
    print("  tier_shift_mcp.csv saved")

    # ── 4. New entrants to High tier (>=60%) at each step ─────────────────────
    # API effect: occupations that enter High tier when going from human_conv to all_confirmed
    wide_clean = wide.dropna(subset=["pct_human_conv", "pct_all_confirmed", "pct_all_ceiling"])

    new_high_api = wide_clean[
        (wide_clean["tier_human_conv"] != "High") &
        (wide_clean["tier_all_confirmed"] == "High")
    ][["category", "pct_human_conv", "pct_all_confirmed"]].copy()
    new_high_api = new_high_api.sort_values("pct_all_confirmed", ascending=False)
    save_csv(new_high_api, results / "new_entrants_high_api.csv")
    print(f"  new_entrants_high_api.csv: {len(new_high_api)} occupations")

    # MCP effect: occupations entering High when going from all_confirmed to all_ceiling
    new_high_mcp = wide_clean[
        (wide_clean["tier_all_confirmed"] != "High") &
        (wide_clean["tier_all_ceiling"] == "High")
    ][["category", "pct_all_confirmed", "pct_all_ceiling"]].copy()
    new_high_mcp = new_high_mcp.sort_values("pct_all_ceiling", ascending=False)
    save_csv(new_high_mcp, results / "new_entrants_high_mcp.csv")
    print(f"  new_entrants_high_mcp.csv: {len(new_high_mcp)} occupations")

    # ── 5. Major-category delta at each layer ──────────────────────────────────
    major_wide = major_dfs["human_conv"].rename(columns={"pct_tasks_affected": "pct_human_conv", "workers_affected": "workers_human_conv"})
    for key in ["all_confirmed", "all_ceiling"]:
        tmp = major_dfs[key].rename(columns={"pct_tasks_affected": f"pct_{key}", "workers_affected": f"workers_{key}"})
        major_wide = major_wide.merge(tmp[["category", f"pct_{key}", f"workers_{key}"]], on="category", how="outer")

    major_wide["delta_api"] = major_wide["pct_all_confirmed"] - major_wide["pct_human_conv"]
    major_wide["delta_mcp"] = major_wide["pct_all_ceiling"] - major_wide["pct_all_confirmed"]
    save_csv(major_wide, results / "major_delta_by_config.csv")
    print("  major_delta_by_config.csv saved")

    # ── 6. IWA data for all 3 configs ─────────────────────────────────────────
    print("  Loading IWA data...")
    iwa_dfs: dict[str, pd.DataFrame] = {}
    for key, ds_name in CONFIGS.items():
        idf = get_iwa_data(ds_name)
        if not idf.empty and "pct_tasks_affected" in idf.columns:
            iwa_dfs[key] = idf.rename(columns={"pct_tasks_affected": f"pct_{key}"})[["category", f"pct_{key}"]]

    iwa_wide = pd.DataFrame()
    if iwa_dfs:
        iwa_wide = list(iwa_dfs.values())[0]
        for df in list(iwa_dfs.values())[1:]:
            iwa_wide = iwa_wide.merge(df, on="category", how="outer")

        # Threshold crossings
        threshold_rows = []
        for threshold in [33, 50]:
            for step, (from_key, to_key) in [("API addition", ("human_conv", "all_confirmed")),
                                              ("MCP addition", ("all_confirmed", "all_ceiling"))]:
                from_col = f"pct_{from_key}"
                to_col = f"pct_{to_key}"
                if from_col in iwa_wide.columns and to_col in iwa_wide.columns:
                    sub = iwa_wide.dropna(subset=[from_col, to_col])
                    crossings = sub[(sub[from_col] < threshold) & (sub[to_col] >= threshold)]
                    threshold_rows.append({
                        "step": step,
                        "threshold": threshold,
                        "n_crossings": len(crossings),
                    })

        threshold_df = pd.DataFrame(threshold_rows)
        save_csv(iwa_wide, results / "wa_iwa_layer_comparison.csv")
        print(f"  wa_iwa_layer_comparison.csv: {len(iwa_wide)} IWAs")
    else:
        threshold_df = pd.DataFrame(columns=["step", "threshold", "n_crossings"])

    # ── 7. Figures ──────────────────────────────────────────────────────────────
    print("  Building figures...")

    # Fig 1: Tier shift API — heatmap
    def _build_tier_heatmap(matrix_df: pd.DataFrame, title: str, subtitle: str) -> go.Figure:
        z_vals = matrix_df.values
        text_vals = [[str(int(v)) for v in row_vals] for row_vals in z_vals]
        fig = go.Figure(go.Heatmap(
            z=z_vals,
            x=TIER_LABELS,
            y=TIER_LABELS,
            colorscale=[[0, "#f7f7f4"], [0.5, COLORS["primary"]], [1.0, "#0d2b45"]],
            text=text_vals,
            texttemplate="%{text}",
            textfont=dict(size=14, color="white", family=FONT_FAMILY),
            showscale=True,
            colorbar=dict(title="N Occupations", tickfont=dict(size=10)),
            hovertemplate="From %{y} -> To %{x}: %{z} occupations<extra></extra>",
        ))
        style_figure(
            fig, title,
            subtitle=subtitle,
            show_legend=False,
            height=500, width=750,
        )
        fig.update_layout(
            xaxis=dict(title="Tier After", showgrid=False, showline=False, side="bottom"),
            yaxis=dict(title="Tier Before", showgrid=False, showline=False, autorange="reversed"),
            margin=dict(l=100, r=60, t=100, b=100),
        )
        return fig

    fig_api_heat = _build_tier_heatmap(
        matrix_api, "Tier Transitions: API Addition",
        "How occupations move across exposure tiers when AEI API data is added | Human Conv. -> All Confirmed",
    )
    save_figure(fig_api_heat, results / "figures" / "tier_shift_api.png")
    shutil.copy(results / "figures" / "tier_shift_api.png", figs_dir / "tier_shift_api.png")
    print("  tier_shift_api.png")

    fig_mcp_heat = _build_tier_heatmap(
        matrix_mcp, "Tier Transitions: MCP Addition",
        "How occupations move across exposure tiers when MCP data is added | All Confirmed -> All Ceiling",
    )
    save_figure(fig_mcp_heat, results / "figures" / "tier_shift_mcp.png")
    shutil.copy(results / "figures" / "tier_shift_mcp.png", figs_dir / "tier_shift_mcp.png")
    print("  tier_shift_mcp.png")

    # Fig 2: Major delta API — diverging horizontal bar
    def _build_delta_bar(df: pd.DataFrame, delta_col: str, title: str, subtitle: str) -> go.Figure:
        plot_df = df.dropna(subset=[delta_col]).sort_values(delta_col, ascending=True)
        pos_color = COLORS["primary"]
        neg_color = COLORS["muted"]
        bar_colors = [pos_color if v >= 0 else neg_color for v in plot_df[delta_col]]

        fig = go.Figure(go.Bar(
            x=plot_df[delta_col].tolist(),
            y=plot_df["category"].tolist(),
            orientation="h",
            marker=dict(color=bar_colors, line=dict(width=0)),
            text=[f"{v:+.1f}pp" for v in plot_df[delta_col]],
            textposition="outside",
            textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
            cliponaxis=False,
        ))
        style_figure(
            fig, title,
            subtitle=subtitle,
            x_title="Delta (percentage points)",
            height=700, width=1100,
            show_legend=False,
        )
        fig.update_layout(
            xaxis=dict(showgrid=True, zeroline=True, zerolinecolor=COLORS["grid"], zerolinewidth=2),
            yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
            margin=dict(l=300, r=100, t=80, b=60),
        )
        return fig

    fig_major_api = _build_delta_bar(
        major_wide, "delta_api",
        "Major Category Gain from API Addition",
        "pct_tasks_affected change: All Confirmed - Human Conv. | positive = API data adds exposure",
    )
    save_figure(fig_major_api, results / "figures" / "major_delta_api.png")
    shutil.copy(results / "figures" / "major_delta_api.png", figs_dir / "major_delta_api.png")
    print("  major_delta_api.png")

    fig_major_mcp = _build_delta_bar(
        major_wide, "delta_mcp",
        "Major Category Gain from MCP Addition",
        "pct_tasks_affected change: All Ceiling - All Confirmed | positive = MCP data adds exposure",
    )
    save_figure(fig_major_mcp, results / "figures" / "major_delta_mcp.png")
    shutil.copy(results / "figures" / "major_delta_mcp.png", figs_dir / "major_delta_mcp.png")
    print("  major_delta_mcp.png")

    # Fig 3: WA threshold crossings — grouped bar
    if not threshold_df.empty:
        steps = threshold_df["step"].unique().tolist()
        thresholds = [33, 50]

        fig_thresh = go.Figure()
        thresh_colors = {33: COLORS["secondary"], 50: COLORS["primary"]}
        for thresh in thresholds:
            counts = []
            for step in steps:
                row = threshold_df[(threshold_df["step"] == step) & (threshold_df["threshold"] == thresh)]
                counts.append(int(row["n_crossings"].values[0]) if len(row) > 0 else 0)
            fig_thresh.add_trace(go.Bar(
                name=f">{thresh}% threshold",
                x=steps,
                y=counts,
                marker_color=thresh_colors[thresh],
                text=counts,
                textposition="outside",
                textfont=dict(size=12, family=FONT_FAMILY),
            ))

        style_figure(
            fig_thresh,
            "IWA Threshold Crossings by Layer Addition",
            subtitle="Number of Intermediate Work Activities crossing 33% and 50% exposure when each data layer is added",
            y_title="Number of IWAs",
            height=500, width=800,
        )
        fig_thresh.update_layout(
            barmode="group",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True),
            bargap=0.2,
        )
        save_figure(fig_thresh, results / "figures" / "wa_threshold_crossings.png")
        shutil.copy(results / "figures" / "wa_threshold_crossings.png", figs_dir / "wa_threshold_crossings.png")
        print("  wa_threshold_crossings.png")

    # ── 8. Print key stats ──────────────────────────────────────────────────────
    print("\n-- Key stats --")
    print(f"  New entrants to High tier from API: {len(new_high_api)}")
    print(f"  New entrants to High tier from MCP: {len(new_high_mcp)}")

    print("\n  API tier shift matrix (from -> to):")
    print(matrix_api.to_string())
    print("\n  MCP tier shift matrix (from -> to):")
    print(matrix_mcp.to_string())

    print("\n  Top 5 major API delta:")
    for _, row in major_wide.dropna(subset=["delta_api"]).nlargest(5, "delta_api").iterrows():
        print(f"    {row['category']}: +{row['delta_api']:.1f}pp")

    print("\n  Top 5 major MCP delta:")
    for _, row in major_wide.dropna(subset=["delta_mcp"]).nlargest(5, "delta_mcp").iterrows():
        print(f"    {row['category']}: +{row['delta_mcp']:.1f}pp")

    if not threshold_df.empty:
        print("\n  IWA threshold crossings:")
        for _, row in threshold_df.iterrows():
            print(f"    {row['step']}, >{row['threshold']}%: {row['n_crossings']} IWAs")

    print("\nmarginal_contributions: done.")


if __name__ == "__main__":
    main()
