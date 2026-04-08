"""
run.py — Work Activity Exposure: Activity Robustness

Which work activities are AI-resistant, and which are in the next wave?

Robustness tiers (applied to the primary all_confirmed config):
  Fragile:   >= 66% pct_tasks_affected (majority of work is AI-exposed)
  Moderate:  33–66%
  Robust:    < 33%  (activity consistently below the threshold)

Confirmed-to-ceiling gap identifies the "next wave": activities where at
least one AI source already shows high exposure even though the confirmed
average is still below 33%.

Run from project root:
    venv/Scripts/python -m analysis.questions.work_activity_exposure.activity_robustness.run
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

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
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
PRIMARY_KEY = "all_confirmed"
CEILING_KEY = "all_ceiling"

ROBUST_THRESHOLD = 33.0
FRAGILE_THRESHOLD = 66.0

TIER_COLORS = {
    "robust":   COLORS["positive"],
    "moderate": COLORS["primary"],
    "fragile":  COLORS["negative"],
}
TIER_LABELS = {
    "robust":   "Robust (<33%)",
    "moderate": "Moderate (33–66%)",
    "fragile":  "Fragile (≥66%)",
}


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
    if pct >= FRAGILE_THRESHOLD:
        return "fragile"
    if pct >= ROBUST_THRESHOLD:
        return "moderate"
    return "robust"


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("activity_robustness: loading IWA and GWA data...")

    # ── 1. Load primary and ceiling ───────────────────────────────────────────
    prim_iwa = get_wa_data(ANALYSIS_CONFIGS[PRIMARY_KEY], "iwa")
    ceil_iwa = get_wa_data(ANALYSIS_CONFIGS[CEILING_KEY], "iwa")
    prim_gwa = get_wa_data(ANALYSIS_CONFIGS[PRIMARY_KEY], "gwa")

    assert not prim_iwa.empty, "No IWA data for primary config"
    assert not ceil_iwa.empty, "No IWA data for ceiling config"

    prim_iwa["tier"] = prim_iwa["pct_tasks_affected"].apply(assign_tier)
    ceil_iwa = ceil_iwa.rename(columns={
        "pct_tasks_affected": "ceiling_pct",
        "workers_affected": "ceiling_workers",
        "wages_affected": "ceiling_wages",
    })

    # ── 2. Build comparison table ─────────────────────────────────────────────
    comp = prim_iwa.merge(
        ceil_iwa[["category", "ceiling_pct"]], on="category", how="left"
    )
    comp["gap_pp"] = (comp["ceiling_pct"] - comp["pct_tasks_affected"]).round(2)
    comp = comp.sort_values("pct_tasks_affected", ascending=False).reset_index(drop=True)
    comp["rank"] = comp.index + 1

    save_csv(comp, results / "iwa_robustness.csv")

    # ── 3. Cross-config tier stability ────────────────────────────────────────
    # How many configs classify each IWA as robust?
    stability_rows: list[dict] = []
    for key, dataset_name in ANALYSIS_CONFIGS.items():
        iwa = get_wa_data(dataset_name, "iwa")
        if iwa.empty:
            continue
        iwa["tier"] = iwa["pct_tasks_affected"].apply(assign_tier)
        iwa["config_key"] = key
        stability_rows.append(iwa[["category", "tier", "config_key", "pct_tasks_affected"]])

    stability_all = pd.concat(stability_rows, ignore_index=True)

    # Count how many configs classify each IWA as robust
    robust_counts = (
        stability_all[stability_all["tier"] == "robust"]
        .groupby("category")
        .size()
        .reset_index(name="n_robust_configs")
    )
    total_configs = len(ANALYSIS_CONFIGS)
    robust_counts["n_robust_configs_of"] = total_configs

    # Stable robust = robust in all 5 configs
    stable_robust = robust_counts[robust_counts["n_robust_configs"] == total_configs]["category"].tolist()

    # Stable fragile = fragile in all 5 configs
    fragile_counts = (
        stability_all[stability_all["tier"] == "fragile"]
        .groupby("category")
        .size()
        .reset_index(name="n_fragile_configs")
    )
    stable_fragile = fragile_counts[fragile_counts["n_fragile_configs"] == total_configs]["category"].tolist()

    # Full stability summary (one row per IWA)
    pivot = stability_all.pivot_table(
        index="category",
        columns="config_key",
        values="pct_tasks_affected",
        aggfunc="first",
    ).reset_index()
    pivot = pivot.merge(robust_counts, on="category", how="left")
    pivot["n_robust_configs"] = pivot["n_robust_configs"].fillna(0).astype(int)
    pivot = pivot.merge(
        prim_iwa[["category", "tier"]].rename(columns={"tier": "primary_tier"}),
        on="category", how="left"
    )
    pivot = pivot.sort_values(f"all_confirmed", ascending=True, na_position="last")
    save_csv(pivot, results / "iwa_tier_stability.csv")

    # ── 4. GWA-level robustness ───────────────────────────────────────────────
    prim_gwa["tier"] = prim_gwa["pct_tasks_affected"].apply(assign_tier)
    gwa_robust = prim_gwa.sort_values("pct_tasks_affected")
    save_csv(gwa_robust, results / "gwa_robustness.csv")

    # ── 5. Next wave: low confirmed but large ceiling gap ─────────────────────
    next_wave = comp[
        (comp["pct_tasks_affected"] < ROBUST_THRESHOLD) &
        (comp["ceiling_pct"] >= ROBUST_THRESHOLD)
    ].copy().sort_values("gap_pp", ascending=False)
    save_csv(next_wave, results / "next_wave_iwas.csv")

    print(f"  robust in all 5 configs: {len(stable_robust)}")
    print(f"  fragile in all 5 configs: {len(stable_fragile)}")
    print(f"  next wave (low confirmed, ceiling >= 33%): {len(next_wave)}")

    # ── 6. Figures ────────────────────────────────────────────────────────────

    # 6a. IWA robustness tiers (all IWAs, colored by tier)
    fig_tiers = _make_robustness_tier_chart(comp)
    _save(fig_tiers, results / "figures" / "iwa_robustness_tiers.png", figs_dir / "iwa_robustness_tiers.png")

    # 6b. Next wave: largest confirmed-to-ceiling gaps
    if not next_wave.empty:
        fig_next = _make_next_wave_chart(next_wave.head(20))
        _save(fig_next, results / "figures" / "next_wave_gaps.png", figs_dir / "next_wave_gaps.png")

    # 6c. GWA robustness overview
    fig_gwa = _make_gwa_robustness(gwa_robust)
    _save(fig_gwa, results / "figures" / "gwa_robustness.png", figs_dir / "gwa_robustness.png")

    # 6d. Cross-config tier stability scatter
    fig_stability = _make_stability_chart(stability_all)
    _save(fig_stability, results / "figures" / "cross_config_stability.png", figs_dir / "cross_config_stability.png")

    print("  saved all figures")

    # ── 7. PDF ────────────────────────────────────────────────────────────────
    report_md = HERE / "activity_robustness_report.md"
    if report_md.exists():
        generate_pdf(report_md, results / "activity_robustness_report.pdf")

    print("activity_robustness: done.")


# ── Chart helpers ─────────────────────────────────────────────────────────────

def _save(fig: go.Figure, results_path: Path, figures_path: Path) -> None:
    save_figure(fig, results_path)
    shutil.copy(str(results_path), str(figures_path))


def _make_robustness_tier_chart(comp: pd.DataFrame) -> go.Figure:
    """Horizontal bar of all IWAs, colored by tier, sorted by pct."""
    df = comp.sort_values("pct_tasks_affected", ascending=True)
    bar_colors = [TIER_COLORS[t] for t in df["tier"]]

    fig = go.Figure(go.Bar(
        x=df["pct_tasks_affected"],
        y=df["category"],
        orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"{v:.1f}%" for v in df["pct_tasks_affected"]],
        textposition="outside",
        textfont=dict(size=8, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))

    # Threshold lines
    fig.add_vline(x=ROBUST_THRESHOLD, line=dict(color=COLORS["muted"], dash="dot", width=1.5))
    fig.add_vline(x=FRAGILE_THRESHOLD, line=dict(color=COLORS["accent"], dash="dot", width=1.5))

    # Legend traces (invisible bars just for legend)
    for tier, color in TIER_COLORS.items():
        fig.add_trace(go.Bar(
            x=[None], y=[None], orientation="h",
            name=TIER_LABELS[tier],
            marker=dict(color=color),
        ))

    style_figure(
        fig,
        "Work Activity Robustness — All IWAs",
        subtitle="All Confirmed Usage | Robust <33% | Moderate 33–66% | Fragile ≥66%",
        x_title="% Tasks Affected",
        height=max(600, len(df) * 14),
        width=1100,
    )
    fig.update_layout(
        barmode="overlay",
        margin=dict(l=20, r=80, t=80, b=80),
        xaxis=dict(showgrid=True, range=[0, max(df["pct_tasks_affected"]) * 1.2]),
        yaxis=dict(showgrid=False, tickfont=dict(size=9)),
        bargap=0.2,
    )
    return fig


def _make_next_wave_chart(next_wave: pd.DataFrame) -> go.Figure:
    """Bar chart showing IWAs with largest confirmed-to-ceiling gaps."""
    df = next_wave.sort_values("gap_pp", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["pct_tasks_affected"],
        y=df["category"],
        orientation="h",
        name="Confirmed %",
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
    ))
    fig.add_trace(go.Bar(
        x=df["gap_pp"],
        y=df["category"],
        orientation="h",
        name="Gap to Ceiling",
        marker=dict(color=COLORS["accent"], line=dict(width=0)),
    ))

    style_figure(
        fig,
        "Next Wave — Low Confirmed but Growing Ceiling Exposure",
        subtitle="IWAs currently <33% confirmed but ceiling ≥33% | ordered by ceiling gap",
        x_title="% Tasks Affected",
        height=max(400, len(df) * 20),
        width=1100,
    )
    fig.update_layout(
        barmode="stack",
        margin=dict(l=20, r=80, t=80, b=140),
        yaxis=dict(showgrid=False, tickfont=dict(size=9)),
        bargap=0.25,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.12,
            xanchor="center",
            x=0.5,
        ),
    )
    return fig


def _make_gwa_robustness(gwa_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar of GWAs colored by tier."""
    df = gwa_df.sort_values("pct_tasks_affected", ascending=True)
    bar_colors = [TIER_COLORS[t] for t in df["tier"]]

    fig = go.Figure(go.Bar(
        x=df["pct_tasks_affected"],
        y=df["category"],
        orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"{v:.1f}%" for v in df["pct_tasks_affected"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    fig.add_vline(x=ROBUST_THRESHOLD, line=dict(color=COLORS["muted"], dash="dot", width=1.5))

    style_figure(
        fig,
        "GWA Robustness — Broad Activity Categories",
        subtitle="All Confirmed Usage | Robust <33% | Moderate 33–66% | Fragile ≥66%",
        x_title="% Tasks Affected",
        show_legend=False,
        height=600,
        width=1000,
    )
    fig.update_layout(
        margin=dict(l=20, r=80, t=80, b=60),
        xaxis=dict(showgrid=True, range=[0, max(df["pct_tasks_affected"]) * 1.2]),
        yaxis=dict(showgrid=False, tickfont=dict(size=10)),
        bargap=0.3,
    )
    return fig


def _make_stability_chart(stability_all: pd.DataFrame) -> go.Figure:
    """Dot plot showing the spread of pct across configs, filtered to IWAs with meaningful disagreement."""
    # Compute per-IWA spread across configs
    spread = (
        stability_all.groupby("category")["pct_tasks_affected"]
        .agg(["min", "max"])
        .reset_index()
    )
    spread["range_pp"] = spread["max"] - spread["min"]

    # Keep only IWAs where configs disagree by more than 3pp (meaningful uncertainty)
    SPREAD_THRESHOLD = 3.0
    contested = spread[spread["range_pp"] > SPREAD_THRESHOLD]["category"].tolist()
    stability_filtered = stability_all[stability_all["category"].isin(contested)].copy()

    # Order by median pct descending
    order = (
        stability_filtered.groupby("category")["pct_tasks_affected"]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )

    fig = go.Figure()
    for i, key in enumerate(ANALYSIS_CONFIGS.keys()):
        sub = stability_filtered[stability_filtered["config_key"] == key]
        fig.add_trace(go.Scatter(
            x=sub["pct_tasks_affected"],
            y=sub["category"],
            mode="markers",
            name=ANALYSIS_CONFIG_LABELS[key],
            marker=dict(
                color=CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)],
                size=6,
                opacity=0.75,
            ),
        ))

    style_figure(
        fig,
        "Cross-Config Stability — Where Configs Disagree",
        subtitle=f"IWAs with >3pp spread across 5 configs ({len(contested)} of 332) | each dot = one config | spread = uncertainty",
        x_title="% Tasks Affected",
        height=max(600, len(order) * 13),
        width=1200,
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.05,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
        ),
        yaxis=dict(
            categoryorder="array",
            categoryarray=list(reversed(order)),
            tickfont=dict(size=8),
        ),
        margin=dict(l=20, r=40, t=80, b=120),
    )
    return fig


if __name__ == "__main__":
    main()
