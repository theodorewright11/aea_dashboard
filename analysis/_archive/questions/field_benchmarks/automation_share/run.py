"""
run.py — Field Benchmarks: Automation Share

How does our confirmed task-exposure rate compare to Project Iceberg (MIT/ORNL)
and Seampoint's governance-constrained estimate?

External benchmarks (hardcoded — from published sources):
  Project Iceberg (Chopra et al., 2025):
    Surface Index  = 2.2%   % of wage value of skills that tech-sector AI tools can perform
    Full Index     = 11.7%  same metric extended to admin/finance/professional services
  Seampoint LLC (2026, Utah):
    AI Can Take Over = ~20%  share of work hours where AI can perform tasks with cheap verification
    AI Can Make Better = ~51%  share of hours where AI extends human judgment (not replaces)

Our metric:
  pct_tasks_affected (emp-weighted mean) = sum(workers_affected) / total_emp * 100
  This equals the employment-weighted average of pct_tasks_affected across all occupations,
  meaning "what fraction of the average worker's tasks are touched by AI."

Key framing: these three measure DIFFERENT things.
  Iceberg measures technical capability of skills (what AI tools CAN do with skill taxonomy).
  Seampoint measures governance-constrained deployment readiness (what orgs CAN deploy today).
  Ours measures confirmed real-world AI usage cross-walked to BLS tasks (what IS being done).

Figures (key ones copied to figures/):
  rate_comparison.png         — Our 5 configs vs external benchmarks (apples-to-apples where possible)
  layer_chart.png             — Stacked dot/range showing confirmed → ceiling → Iceberg gap

Run from project root:
    venv/Scripts/python -m analysis.questions.field_benchmarks.automation_share.run
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from analysis.config import (
    ANALYSIS_CONFIGS,
    ANALYSIS_CONFIG_LABELS,
    ensure_results_dir,
    make_config,
)
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
PRIMARY_KEY = "all_confirmed"
CEILING_KEY = "all_ceiling"

# ── External benchmark constants ─────────────────────────────────────────────
# Source: Chopra et al. (2025), "The Iceberg Index: Measuring Skills-centered
#   Exposure in the AI Economy," Project Iceberg (MIT / Oak Ridge National Lab).
ICEBERG_SURFACE = 2.2    # % of wage value — tech sector skill overlap
ICEBERG_FULL    = 11.7   # % of wage value — full economy (admin/finance/professional)

# Source: Seampoint LLC (2026), "Utah's AI Workforce Reality," preliminary draft.
#   ~20% of Utah work hours can be shifted directly to AI (governance-constrained).
#   ~51% of Utah work hours AI can make better (augmentation, not replacement).
SEAMPOINT_TAKEOVER = 20.0
SEAMPOINT_AUGMENT  = 51.0


# ── Data helpers ─────────────────────────────────────────────────────────────

def _get_occ_data(dataset_name: str, geo: str = "nat") -> pd.DataFrame:
    """Occupation-level pct_tasks_affected and workers/wages for one dataset."""
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
        return pd.DataFrame()
    df = data["df"]
    gc = data.get("group_col", "title_current")
    return df.rename(columns={gc: "title_current"})[
        ["title_current", "pct_tasks_affected", "workers_affected", "wages_affected"]
    ].copy()


def _compute_agg(occ_df: pd.DataFrame, config_key: str) -> dict:
    """
    Compute aggregate pct from occ-level data.
    pct_agg = sum(workers_affected) / total_workers * 100
    This is the employment-weighted mean pct_tasks_affected.
    """
    from backend.compute import get_explorer_occupations

    all_occs = get_explorer_occupations()
    total_emp = sum(o.get("emp") or 0 for o in all_occs)

    workers = occ_df["workers_affected"].sum()
    wages   = occ_df["wages_affected"].sum()
    pct_agg = (workers / total_emp * 100) if total_emp > 0 else np.nan

    return {
        "config_key":       config_key,
        "config_label":     ANALYSIS_CONFIG_LABELS[config_key],
        "workers_affected": workers,
        "wages_affected":   wages,
        "pct_agg":          pct_agg,
        "total_emp":        total_emp,
    }


# ── Figure builders ───────────────────────────────────────────────────────────

def _build_rate_comparison(agg_df: pd.DataFrame) -> go.Figure:
    """
    Grouped horizontal bar comparing our 5 configs to external benchmarks.
    Two groups: (1) our confirmed/ceiling pct, (2) external benchmarks.
    """
    fig = go.Figure()

    # Our configs — order: confirmed first
    config_order = ["all_confirmed", "all_ceiling", "human_conversation",
                    "agentic_confirmed", "agentic_ceiling"]
    ours = agg_df.set_index("config_key")

    our_labels = []
    our_vals   = []
    our_colors = []
    color_map  = {
        "all_confirmed":      COLORS["primary"],
        "all_ceiling":        COLORS["secondary"],
        "human_conversation": COLORS["accent"],
        "agentic_confirmed":  COLORS["muted"],
        "agentic_ceiling":    COLORS["neutral"],
    }
    for k in config_order:
        if k in ours.index:
            our_labels.append(ANALYSIS_CONFIG_LABELS[k])
            our_vals.append(round(ours.loc[k, "pct_agg"], 1))
            our_colors.append(color_map.get(k, COLORS["primary"]))

    fig.add_trace(go.Bar(
        name="AEA Dashboard (this analysis)",
        y=our_labels,
        x=our_vals,
        orientation="h",
        marker=dict(color=our_colors, line=dict(width=0)),
        text=[f"{v:.1f}%" for v in our_vals],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))

    # External benchmarks as reference lines / separate bar group
    ext_labels = [
        "Seampoint (augment: AI makes better)",
        "Seampoint (takeover: AI replaces)",
        "Iceberg Full Index (all sectors)",
        "Iceberg Surface Index (tech only)",
    ]
    ext_vals = [SEAMPOINT_AUGMENT, SEAMPOINT_TAKEOVER, ICEBERG_FULL, ICEBERG_SURFACE]
    ext_colors = [COLORS["accent"], COLORS["accent"], "#888", "#aaa"]

    fig.add_trace(go.Bar(
        name="External benchmarks",
        y=ext_labels,
        x=ext_vals,
        orientation="h",
        marker=dict(
            color=ext_colors,
            pattern=dict(shape="/", size=6, fgcolor="white"),
            line=dict(width=0.5, color=COLORS["border"]),
        ),
        text=[f"{v:.1f}%" for v in ext_vals],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))

    chart_h = max(500, (len(our_labels) + len(ext_labels)) * 38 + 200)
    style_figure(
        fig,
        "AI Exposure Rate: Confirmed Usage vs. External Benchmarks",
        subtitle=(
            "AEA Dashboard: emp-weighted mean pct_tasks_affected (% of tasks touched by AI per avg worker) | "
            "Iceberg: % of skill wage value AI tools can technically perform | "
            "Seampoint: % of work hours (governance-constrained deployment)"
        ),
        x_title="Rate (%)",
        height=chart_h,
        width=1200,
        show_legend=True,
    )
    fig.update_layout(
        barmode="group",
        bargap=0.25,
        margin=dict(l=20, r=140, t=90, b=80),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix="%", range=[0, 65]),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        legend=dict(
            orientation="h", yanchor="top", y=-0.10, xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        ),
    )
    return fig


def _build_layer_chart(agg_df: pd.DataFrame) -> go.Figure:
    """
    Dot plot showing the measurement spectrum from confirmed to theoretical ceiling.
    Shows: agentic_confirmed → all_confirmed → all_ceiling → Seampoint takeover →
           Iceberg Full → Seampoint augment
    """
    confirmed_pct = agg_df.loc[agg_df["config_key"] == "all_confirmed", "pct_agg"].iloc[0]
    ceiling_pct   = agg_df.loc[agg_df["config_key"] == "all_ceiling",   "pct_agg"].iloc[0]
    agentic_pct   = agg_df.loc[agg_df["config_key"] == "agentic_confirmed", "pct_agg"].iloc[0]

    labels = [
        "Agentic confirmed<br>(AEA: tool-use only)",
        "All confirmed<br>(AEA: primary config)",
        "All ceiling<br>(AEA: incl. MCP potential)",
        "Iceberg Full Index<br>(technical capability, skill value)",
        "Seampoint<br>(governance-constrained<br>deployment, takeover)",
        "Seampoint<br>(AI makes people better)",
    ]
    values  = [agentic_pct, confirmed_pct, ceiling_pct,
               ICEBERG_FULL, SEAMPOINT_TAKEOVER, SEAMPOINT_AUGMENT]
    colors  = [
        COLORS["muted"], COLORS["primary"], COLORS["secondary"],
        "#888", COLORS["accent"], COLORS["accent"],
    ]
    symbols = ["circle", "circle", "circle", "diamond", "diamond", "diamond"]
    sizes   = [14, 18, 14, 14, 14, 14]

    fig = go.Figure()
    for i, (lbl, val, col, sym, sz) in enumerate(
            zip(labels, values, colors, symbols, sizes)):
        fig.add_trace(go.Scatter(
            x=[val], y=[i],
            mode="markers+text",
            marker=dict(color=col, size=sz, symbol=sym,
                        line=dict(width=1.5, color=COLORS["bg"])),
            text=[f"<b>{val:.1f}%</b>"],
            textposition="top center",
            textfont=dict(size=10, color=col, family=FONT_FAMILY),
            name=lbl.replace("<br>", " "),
            showlegend=False,
        ))

    # Vertical separator between AEA and external
    fig.add_vline(x=(ceiling_pct + ICEBERG_FULL) / 2,
                  line_dash="dot", line_color=COLORS["muted"], line_width=1)

    style_figure(
        fig,
        "Measuring AI Exposure: Three Lenses, One Workforce",
        subtitle=(
            "AEA Dashboard (circles) measures confirmed and ceiling real-world usage | "
            "External sources (diamonds) measure technical capability or governance-constrained readiness"
        ),
        x_title="Exposure Rate (%)",
        height=500, width=1100,
        show_legend=False,
    )
    fig.update_layout(
        yaxis=dict(
            tickvals=list(range(len(labels))),
            ticktext=[l.replace("<br>", " ") for l in labels],
            showgrid=False,
            tickfont=dict(size=10, family=FONT_FAMILY),
        ),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix="%", range=[0, 60]),
        margin=dict(l=20, r=60, t=80, b=80),
    )
    return fig


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("automation_share: loading occupation data for all 5 configs...")

    rows: list[dict] = []
    # Only need total_emp once
    from backend.compute import get_explorer_occupations
    all_occs = get_explorer_occupations()
    total_emp = sum(o.get("emp") or 0 for o in all_occs)
    print(f"  Total national employment: {total_emp:,.0f}")

    for key, ds_name in ANALYSIS_CONFIGS.items():
        print(f"  {ANALYSIS_CONFIG_LABELS[key]}...")
        occ_df = _get_occ_data(ds_name)
        if occ_df.empty:
            print(f"    WARNING: no data for {ds_name}")
            continue
        workers = occ_df["workers_affected"].sum()
        wages   = occ_df["wages_affected"].sum()
        pct_agg = (workers / total_emp * 100) if total_emp > 0 else np.nan
        rows.append({
            "config_key":       key,
            "config_label":     ANALYSIS_CONFIG_LABELS[key],
            "workers_affected": workers,
            "wages_affected":   wages,
            "pct_agg":          round(pct_agg, 2),
            "total_emp":        total_emp,
        })

    assert rows, "No data loaded — check dataset names in ANALYSIS_CONFIGS"
    agg_df = pd.DataFrame(rows)

    # Add external benchmarks to summary CSV
    ext_rows = [
        {"source": "Iceberg Surface Index (tech sector)",       "pct": ICEBERG_SURFACE,   "metric_basis": "% skill wage value"},
        {"source": "Iceberg Full Index (all sectors)",          "pct": ICEBERG_FULL,      "metric_basis": "% skill wage value"},
        {"source": "Seampoint Utah (AI can take over)",         "pct": SEAMPOINT_TAKEOVER,"metric_basis": "% work hours"},
        {"source": "Seampoint Utah (AI can make better)",       "pct": SEAMPOINT_AUGMENT, "metric_basis": "% work hours"},
    ]
    ext_df = pd.DataFrame(ext_rows)

    # Print summary
    print("\n-- Automation share comparison --")
    for _, r in agg_df.iterrows():
        print(f"  {r['config_label']:<30}: {r['pct_agg']:.1f}%")
    print(f"\n  External benchmarks:")
    print(f"    Iceberg Surface:  {ICEBERG_SURFACE}%")
    print(f"    Iceberg Full:     {ICEBERG_FULL}%")
    print(f"    Seampoint takeover: {SEAMPOINT_TAKEOVER}%")
    print(f"    Seampoint augment:  {SEAMPOINT_AUGMENT}%")

    # Save CSVs
    save_csv(agg_df, results / "automation_share_ours.csv")
    save_csv(ext_df, results / "external_benchmarks.csv")
    print("\n  CSVs saved.")

    # Figures
    print("  Building figures...")
    fig = _build_rate_comparison(agg_df)
    save_figure(fig, results / "figures" / "rate_comparison.png")
    shutil.copy(results / "figures" / "rate_comparison.png", figs_dir / "rate_comparison.png")
    print("    rate_comparison.png")

    fig = _build_layer_chart(agg_df)
    save_figure(fig, results / "figures" / "layer_chart.png")
    shutil.copy(results / "figures" / "layer_chart.png", figs_dir / "layer_chart.png")
    print("    layer_chart.png")

    # PDF
    md_path = HERE / "automation_share_report.md"
    if md_path.exists():
        generate_pdf(md_path, results / "automation_share_report.pdf")

    print("\nautomation_share: done.")


if __name__ == "__main__":
    main()
