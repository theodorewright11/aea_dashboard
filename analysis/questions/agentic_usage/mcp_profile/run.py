"""
run.py -- Agentic Usage: MCP Profile

What is MCP's unique signature? Which occupations and work activities does
MCP uniquely expose, and how does it compare to the AEI API?

Run from project root:
    venv/Scripts/python -m analysis.questions.agentic_usage.mcp_profile.run
"""
from __future__ import annotations

import warnings
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from analysis.config import ensure_results_dir
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    CATEGORY_PALETTE,
    save_figure,
    save_csv,
    style_figure,
    make_horizontal_bar,
    generate_pdf,
)

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent

DATASETS = {
    "mcp_only":      ("MCP Cumul. v4",                "MCP Only"),
    "aei_api":       ("AEI API 2026-02-12",           "Agentic (AEI API)"),
    "conv_baseline": ("AEI Both + Micro 2026-02-12",  "Conv. Baseline"),
}

DATASET_COLORS = {
    "mcp_only":      CATEGORY_PALETTE[3],
    "aei_api":       COLORS["secondary"],
    "conv_baseline": COLORS["muted"],
}


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


def get_wa_data(dataset_name: str, level: str = "iwa") -> pd.DataFrame:
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


def assign_tier(pct: float) -> str:
    if pct < 20:
        return "<20"
    elif pct < 40:
        return "20-40"
    elif pct < 60:
        return "40-60"
    else:
        return ">=60"


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("mcp_profile: loading occupation data...")

    # ── 1. Occupation-level data for all 3 datasets ───────────────────────────
    occ_dfs: dict[str, pd.DataFrame] = {}
    for key, (ds_name, label) in DATASETS.items():
        print(f"  {label}...")
        occ_dfs[key] = get_occ_data(ds_name)

    # Build wide df
    wide = occ_dfs["mcp_only"].rename(columns={"pct_tasks_affected": "pct_mcp_only", "workers_affected": "workers_mcp_only"})
    for key in ["aei_api", "conv_baseline"]:
        tmp = occ_dfs[key].rename(columns={"pct_tasks_affected": f"pct_{key}", "workers_affected": f"workers_{key}"})
        wide = wide.merge(tmp[["category", f"pct_{key}", f"workers_{key}"]], on="category", how="outer")

    # Deltas
    wide["delta_mcp_vs_aei"] = wide["pct_mcp_only"] - wide["pct_aei_api"]
    wide["delta_mcp_vs_conv"] = wide["pct_mcp_only"] - wide["pct_conv_baseline"]

    # ── 2. Top 30 by MCP pct ─────────────────────────────────────────────────
    top30_mcp = wide.nlargest(30, "pct_mcp_only")[["category", "pct_mcp_only", "pct_aei_api", "pct_conv_baseline",
                                                     "delta_mcp_vs_aei", "delta_mcp_vs_conv"]].copy()
    save_csv(top30_mcp, results / "mcp_top_occs.csv")
    print("  mcp_top_occs.csv saved")

    # Save full delta CSV
    delta_occ = wide[["category", "pct_mcp_only", "pct_aei_api", "pct_conv_baseline",
                       "delta_mcp_vs_aei", "delta_mcp_vs_conv"]].copy()
    save_csv(delta_occ.sort_values("delta_mcp_vs_aei", ascending=False), results / "mcp_vs_aei_delta_occ.csv")
    print("  mcp_vs_aei_delta_occ.csv saved")

    # ── 3. Major-category comparison ──────────────────────────────────────────
    print("  Loading major-level data...")
    major_dfs: dict[str, pd.DataFrame] = {}
    for key, (ds_name, label) in DATASETS.items():
        major_dfs[key] = get_major_data(ds_name)

    major_wide = major_dfs["mcp_only"].rename(columns={"pct_tasks_affected": "pct_mcp_only", "workers_affected": "workers_mcp_only"})
    for key in ["aei_api", "conv_baseline"]:
        tmp = major_dfs[key].rename(columns={"pct_tasks_affected": f"pct_{key}", "workers_affected": f"workers_{key}"})
        major_wide = major_wide.merge(tmp[["category", f"pct_{key}", f"workers_{key}"]], on="category", how="outer")

    major_wide["delta_mcp_vs_aei"] = major_wide["pct_mcp_only"] - major_wide["pct_aei_api"]
    major_wide["delta_mcp_vs_conv"] = major_wide["pct_mcp_only"] - major_wide["pct_conv_baseline"]
    save_csv(major_wide, results / "mcp_vs_aei_delta_major.csv")
    print("  mcp_vs_aei_delta_major.csv saved")

    # ── 4. MCP work activities (eco_2025 mcp_group) ───────────────────────────
    print("  Loading MCP work activities...")
    mcp_ds = DATASETS["mcp_only"][0]
    mcp_iwa = get_wa_data(mcp_ds, "iwa")
    mcp_gwa = get_wa_data(mcp_ds, "gwa")

    if not mcp_iwa.empty and "pct_tasks_affected" in mcp_iwa.columns:
        save_csv(mcp_iwa.sort_values("pct_tasks_affected", ascending=False), results / "mcp_iwa_profile.csv")
        print(f"  mcp_iwa_profile.csv: {len(mcp_iwa)} IWAs")

    if not mcp_gwa.empty and "pct_tasks_affected" in mcp_gwa.columns:
        save_csv(mcp_gwa.sort_values("pct_tasks_affected", ascending=False), results / "mcp_gwa_profile.csv")
        print(f"  mcp_gwa_profile.csv: {len(mcp_gwa)} GWAs")

    # ── 5. Tier distribution comparison: MCP vs AEI API ──────────────────────
    tier_rows = []
    for key in ["mcp_only", "aei_api"]:
        col = f"pct_{key}"
        label = DATASETS[key][1]
        sub = wide[[col]].dropna()
        sub["tier"] = sub[col].apply(assign_tier)
        for tier, cnt in sub.groupby("tier").size().items():
            tier_rows.append({"source": label, "tier": tier, "count": int(cnt)})
    tier_df = pd.DataFrame(tier_rows)

    # ── 6. Figures ─────────────────────────────────────────────────────────────
    print("  Building figures...")

    # Fig 1: Top 30 MCP occupations — horizontal bar
    fig1 = make_horizontal_bar(
        top30_mcp.sort_values("pct_mcp_only", ascending=False),
        category_col="category",
        value_col="pct_mcp_only",
        title="Top 30 Occupations by MCP Exposure",
        subtitle="pct_tasks_affected | MCP Cumul. v4 | eco_2025 baseline",
        x_title="% Tasks Affected",
        color=CATEGORY_PALETTE[3],
        value_format="%.1f%%",
        height=850, width=1200,
    )
    save_figure(fig1, results / "figures" / "mcp_top_occupations.png")
    shutil.copy(results / "figures" / "mcp_top_occupations.png", figs_dir / "mcp_top_occupations.png")
    print("  mcp_top_occupations.png")

    # Fig 2: Diverging bar — MCP pct - AEI API pct by major category
    delta_major_plot = major_wide.dropna(subset=["delta_mcp_vs_aei"]).sort_values("delta_mcp_vs_aei", ascending=True)
    pos_color = CATEGORY_PALETTE[3]   # purple = MCP leads
    neg_color = COLORS["secondary"]   # teal = AEI leads
    bar_colors = [pos_color if v >= 0 else neg_color for v in delta_major_plot["delta_mcp_vs_aei"]]

    fig2 = go.Figure(go.Bar(
        x=delta_major_plot["delta_mcp_vs_aei"].tolist(),
        y=delta_major_plot["category"].tolist(),
        orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"{v:+.1f}pp" for v in delta_major_plot["delta_mcp_vs_aei"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(
        fig2,
        "MCP vs. AEI API by Major Category",
        subtitle="pct_tasks_affected delta: MCP Only minus Agentic (AEI API) | purple = MCP leads, teal = AEI leads",
        x_title="Delta (percentage points)",
        height=700, width=1100,
        show_legend=False,
    )
    fig2.update_layout(
        xaxis=dict(showgrid=True, zeroline=True, zerolinecolor=COLORS["grid"], zerolinewidth=2),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        margin=dict(l=300, r=120, t=80, b=60),
    )
    save_figure(fig2, results / "figures" / "mcp_vs_aei_delta_major.png")
    shutil.copy(results / "figures" / "mcp_vs_aei_delta_major.png", figs_dir / "mcp_vs_aei_delta_major.png")
    print("  mcp_vs_aei_delta_major.png")

    # Fig 3: MCP signature IWAs — top 20
    if not mcp_iwa.empty and "pct_tasks_affected" in mcp_iwa.columns:
        top20_iwa = mcp_iwa.nlargest(20, "pct_tasks_affected").sort_values("pct_tasks_affected", ascending=False)
        fig3 = make_horizontal_bar(
            top20_iwa,
            category_col="category",
            value_col="pct_tasks_affected",
            title="MCP Signature: Top 20 IWAs",
            subtitle="Top 20 Intermediate Work Activities by pct_tasks_affected | MCP Cumul. v4 | eco_2025 (mcp_group)",
            x_title="% Tasks Affected",
            color=CATEGORY_PALETTE[3],
            value_format="%.1f%%",
            height=700, width=1200,
        )
        save_figure(fig3, results / "figures" / "mcp_signature_iwas.png")
        shutil.copy(results / "figures" / "mcp_signature_iwas.png", figs_dir / "mcp_signature_iwas.png")
        print("  mcp_signature_iwas.png")

    # Fig 4: MCP vs conv. baseline by major category — grouped bar
    major_plot = major_wide.dropna(subset=["pct_mcp_only", "pct_conv_baseline"]).sort_values("pct_conv_baseline", ascending=True)
    categories = major_plot["category"].tolist()

    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=major_plot["pct_conv_baseline"].tolist(),
        y=categories,
        orientation="h",
        name="Conv. Baseline",
        marker=dict(color=COLORS["muted"], opacity=0.85),
    ))
    fig4.add_trace(go.Bar(
        x=major_plot["pct_mcp_only"].tolist(),
        y=categories,
        orientation="h",
        name="MCP Only",
        marker=dict(color=CATEGORY_PALETTE[3], opacity=0.85),
    ))
    style_figure(
        fig4,
        "MCP Only vs. Conv. Baseline by Major Category",
        subtitle="pct_tasks_affected comparison | Conv. Baseline = All Confirmed (AEI Both + Micro)",
        x_title="% Tasks Affected",
        height=700, width=1200,
    )
    fig4.update_layout(
        barmode="group",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        margin=dict(l=300, r=80, t=80, b=80),
        legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
    )
    save_figure(fig4, results / "figures" / "mcp_vs_conv_major.png")
    shutil.copy(results / "figures" / "mcp_vs_conv_major.png", figs_dir / "mcp_vs_conv_major.png")
    print("  mcp_vs_conv_major.png")

    # ── 7. Print key stats ──────────────────────────────────────────────────────
    print("\n-- Key stats --")
    print("  Top 5 MCP occupations:")
    for _, row in top30_mcp.head(5).iterrows():
        print(f"    {row['category']}: MCP={row['pct_mcp_only']:.1f}%  AEI={row['pct_aei_api']:.1f}%  delta={row['delta_mcp_vs_aei']:+.1f}pp")

    print("\n  MCP-lead categories (MCP >> AEI):")
    mcp_lead = delta_occ.nlargest(5, "delta_mcp_vs_aei")
    for _, row in mcp_lead.iterrows():
        print(f"    {row['category']}: MCP={row['pct_mcp_only']:.1f}%  AEI={row['pct_aei_api']:.1f}%  delta={row['delta_mcp_vs_aei']:+.1f}pp")

    print("\n  AEI-lead categories (AEI >> MCP):")
    aei_lead = delta_occ.nsmallest(5, "delta_mcp_vs_aei")
    for _, row in aei_lead.iterrows():
        print(f"    {row['category']}: MCP={row['pct_mcp_only']:.1f}%  AEI={row['pct_aei_api']:.1f}%  delta={row['delta_mcp_vs_aei']:+.1f}pp")

    if not mcp_iwa.empty and "pct_tasks_affected" in mcp_iwa.columns:
        print("\n  Top 5 MCP IWAs:")
        for _, row in mcp_iwa.nlargest(5, "pct_tasks_affected").iterrows():
            print(f"    {row['category']}: {row['pct_tasks_affected']:.1f}%")

    print("\nmcp_profile: done.")


if __name__ == "__main__":
    main()
