"""
Part 3 — Action: What To Do About It

Two figures so far. Audience scaffolding will be reintroduced as more
charts come in.

  1. Tech commodities composite (top-25)
  2. Conv → Confirmed → Ceiling gap by major occ category

Run from project root:
    venv/Scripts/python -m analysis.paper.results.part_3.run
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
    ROOT,
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.utils import FONT_FAMILY, save_csv, save_figure
from analysis.paper.paper_config import (
    PAPER_W,
    ANNOT_FS, LABEL_FS, TICK_FS,
    PAPER_PALETTE,
    style_paper_figure, fmt_wages, fmt_workers,
)

HERE = Path(__file__).resolve().parent
ANALYSIS_DATA_DIR = ROOT / "analysis" / "data"
TECH_SKILLS_FILE = ANALYSIS_DATA_DIR / "technology_skills_v30.1.csv"

PRIMARY_KEY = "all_confirmed"
PRIMARY_DATASET = ANALYSIS_CONFIGS[PRIMARY_KEY]
PRIMARY_LABEL = ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]
CONFIG_SUBTITLE = f"{PRIMARY_LABEL} | National | freq, auto-aug ON"


# ─────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────

def _copy_fig(results: Path, figures: Path, name: str) -> None:
    shutil.copy(results / "figures" / name, figures / name)


def _run_config(dataset_name: str, agg_level: str) -> pd.DataFrame:
    """Run get_group_data for one dataset and return a category dataframe."""
    from backend.compute import get_group_data
    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": "nat",
        "agg_level": agg_level,
        "sort_by": "% Tasks Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    assert data is not None, f"No data for {dataset_name} @ {agg_level}"
    df: pd.DataFrame = data["df"]
    return df.rename(columns={data["group_col"]: "category"})


# ─────────────────────────────────────────────────────────────────────────
# Figure 1: Tech commodities composite (reuse skills_landscape pipeline)
# ─────────────────────────────────────────────────────────────────────────

def _structural_for_tech() -> pd.DataFrame:
    """Per-occ structural data for tech-skills join."""
    from backend.compute import get_explorer_occupations
    rows = [
        {
            "title_current": o["title_current"],
            "emp": o.get("emp") or 0,
            "wage": o.get("wage") or 0,
            "major": o.get("major", ""),
        }
        for o in get_explorer_occupations()
    ]
    return pd.DataFrame(rows)


def build_tech_commodities(results: Path, figures: Path) -> None:
    assert TECH_SKILLS_FILE.exists(), f"Tech skills file not found: {TECH_SKILLS_FILE}"
    pct = get_pct_tasks_affected(PRIMARY_DATASET)
    structural = _structural_for_tech()

    tech = pd.read_csv(TECH_SKILLS_FILE)
    tech.columns = [c.strip() for c in tech.columns]
    tech = tech.merge(
        structural.rename(columns={"title_current": "Title"}),
        on="Title", how="left",
    )
    pct_merge = pct.rename("pct").reset_index()
    pct_merge.columns = ["Title", "pct"]
    tech = tech.merge(pct_merge, on="Title", how="left")
    tech["pct"] = tech["pct"].fillna(0.0)
    tech["emp"] = tech["emp"].fillna(0.0)
    tech["wage"] = tech["wage"].fillna(0.0)
    n_comm = tech.groupby("Title").size().rename("n_comm_in_occ").reset_index()
    tech = tech.merge(n_comm, on="Title", how="left")
    tech["per_row_workers_affected"] = (tech["pct"] / 100.0) * tech["emp"]
    tech["per_row_payroll"] = (tech["emp"] * tech["wage"]) / tech["n_comm_in_occ"].replace(0, np.nan)
    tech["per_row_wages_affected"] = (tech["pct"] / 100.0) * tech["per_row_payroll"]

    agg = (
        tech.groupby("Commodity Title")
        .agg(
            mean_pct_affected=("pct", "mean"),
            workers_affected=("per_row_workers_affected", "sum"),
            wages_affected=("per_row_wages_affected", "sum"),
            n_entries=("Title", "size"),
            n_occs=("Title", "nunique"),
        )
        .reset_index()
    )
    pct_min, pct_max = agg["mean_pct_affected"].min(), agg["mean_pct_affected"].max()
    wrk_min, wrk_max = agg["workers_affected"].min(), agg["workers_affected"].max()
    agg["norm_pct"] = (agg["mean_pct_affected"] - pct_min) / max(pct_max - pct_min, 1e-9)
    agg["norm_workers"] = (agg["workers_affected"] - wrk_min) / max(wrk_max - wrk_min, 1e-9)
    agg["composite"] = np.sqrt(agg["norm_pct"] * agg["norm_workers"])
    top = agg.sort_values("composite", ascending=False).head(25).copy()
    save_csv(top, results / "tech_commodities_top25.csv")

    top = top.sort_values("composite", ascending=True)  # smallest at bottom for plotly
    labels = [
        f"{fmt_workers(wk)} workers | {fmt_wages(wa)} wages | "
        f"{p:.1f}% avg | {o} occs | {int(ne):,} entries"
        for wk, wa, p, o, ne in zip(
            top["workers_affected"], top["wages_affected"],
            top["mean_pct_affected"], top["n_occs"], top["n_entries"],
        )
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top["composite"],
        y=top["Commodity Title"],
        orientation="h",
        marker=dict(
            color=top["mean_pct_affected"].values,
            colorscale=[[0, "#c4d9d2"], [1, "#0a2e25"]],
            showscale=True,
            colorbar=dict(
                title=dict(text="Avg %<br>tasks", side="top",
                           font=dict(size=ANNOT_FS)),
                ticksuffix="%",
                tickfont=dict(size=ANNOT_FS),
                len=0.55, thickness=14,
                x=1.005, xanchor="left",
            ),
        ),
        text=labels,
        textposition="outside",
        textfont=dict(size=ANNOT_FS, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
        showlegend=False,
    ))

    style_paper_figure(
        fig,
        "Top 25 Tech Commodities — Where AI Has the Deepest and Broadest Reach",
        subtitle=(
            "Composite = √(min-max %tasks × min-max workers) | "
            "Color = avg % tasks affected | "
            f"{CONFIG_SUBTITLE}"
        ),
        height=900, width=PAPER_W + 100,
        margin=dict(l=20, r=440, t=110, b=80),
    )
    fig.update_xaxes(
        title=dict(text="Depth × Breadth Composite (0–1)", font=dict(size=LABEL_FS)),
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        showticklabels=True, range=[0, 1.05],
    )
    fig.update_yaxes(showgrid=False, showline=False, tickfont=dict(size=11))
    fig.update_layout(bargap=0.25)

    save_figure(fig, results / "figures" / "tech_commodities.png", scale=2)
    _copy_fig(results, figures, "tech_commodities.png")
    print("  -> tech_commodities.png")


# ─────────────────────────────────────────────────────────────────────────
# Figure 2: Conv → Confirmed → Ceiling gap by major occ category
# ─────────────────────────────────────────────────────────────────────────

def build_conv_confirmed_ceiling_gap(results: Path, figures: Path) -> None:
    """All 22 majors stacked into 3 segments: Conv base + Conv→Confirmed gap
    (the focal segment, color-coded by workers added) + Confirmed→Ceiling
    extension. Sorted by Conv→Confirmed % tasks gap."""
    conv = _run_config(ANALYSIS_CONFIGS["human_conversation"], "major")
    confirmed = _run_config(ANALYSIS_CONFIGS["all_confirmed"], "major")
    ceiling = _run_config(ANALYSIS_CONFIGS["all_ceiling"], "major")

    keep = ["category", "pct_tasks_affected", "workers_affected", "wages_affected"]
    df = (
        conv[keep].rename(columns={
            "pct_tasks_affected": "pct_conv",
            "workers_affected": "wk_conv",
            "wages_affected": "wg_conv",
        })
        .merge(confirmed[keep].rename(columns={
            "pct_tasks_affected": "pct_conf",
            "workers_affected": "wk_conf",
            "wages_affected": "wg_conf",
        }), on="category")
        .merge(ceiling[keep].rename(columns={
            "pct_tasks_affected": "pct_ceil",
            "workers_affected": "wk_ceil",
            "wages_affected": "wg_ceil",
        }), on="category")
    )

    df["pct_gap_cv_cf"] = df["pct_conf"] - df["pct_conv"]
    df["wk_gap_cv_cf"] = df["wk_conf"] - df["wk_conv"]
    df["wg_gap_cv_cf"] = df["wg_conf"] - df["wg_conv"]
    df["pct_gap_cf_ce"] = df["pct_ceil"] - df["pct_conf"]
    df["wk_gap_cf_ce"] = df["wk_ceil"] - df["wk_conf"]
    df["wg_gap_cf_ce"] = df["wg_ceil"] - df["wg_conf"]

    save_csv(df.sort_values("pct_gap_cv_cf", ascending=False),
             results / "conv_confirmed_ceiling_gap.csv", float_format="%.3f")

    df = df.sort_values("pct_gap_cv_cf", ascending=True)  # plotly bottom-up
    cats = df["category"].tolist()

    fig = go.Figure()

    # Segment 1: Conversational base (muted sage-grey)
    fig.add_trace(go.Bar(
        y=cats, x=df["pct_conv"], orientation="h",
        name="Conversational confirmed",
        marker=dict(color="#a8b8b3", line=dict(width=0)),
        text=[f"{v:.0f}%" for v in df["pct_conv"]],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(size=12, color="white", family=FONT_FAMILY),
        hovertemplate="<b>%{y}</b><br>Conversational: %{x:.1f}%<extra></extra>",
    ))

    # Segment 2: Conv → Confirmed gap (focal segment, color = workers added)
    wk_min = float(df["wk_gap_cv_cf"].min())
    wk_max_v = float(df["wk_gap_cv_cf"].max())
    fig.add_trace(go.Bar(
        y=cats, x=df["pct_gap_cv_cf"], orientation="h",
        name="Conv-Confirmed gap",
        marker=dict(
            color=df["wk_gap_cv_cf"].values,
            colorscale=[[0, "#c4d9d2"], [1, "#0a2e25"]],
            showscale=False,
            line=dict(width=0),
        ),
        text=[f"+{v:.0f}pp" for v in df["pct_gap_cv_cf"]],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(size=12, color="white", family=FONT_FAMILY),
        hovertemplate="<b>%{y}</b><br>Conv-Conf gap: +%{x:.1f}pp<extra></extra>",
    ))

    # Segment 3: Confirmed → Ceiling extension (warm sand, more transparent)
    fig.add_trace(go.Bar(
        y=cats, x=df["pct_gap_cf_ce"], orientation="h",
        name="Confirmed-Ceiling gap",
        marker=dict(color="#e8d9b8", opacity=0.8, line=dict(width=0)),
        text=[f"+{v:.0f}pp" for v in df["pct_gap_cf_ce"]],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(size=12, color=PAPER_PALETTE["text_dark"], family=FONT_FAMILY),
        hovertemplate="<b>%{y}</b><br>Conf→Ceil gap: +%{x:.1f}pp<extra></extra>",
    ))

    # Right-side per-row two-line annotations (as fig-level annotations,
    # not a scatter trace — kaleido rendering is more stable that way).
    for cat, pct_ceil, p1, w1, g1, p2, w2, g2 in zip(
        cats, df["pct_ceil"],
        df["pct_gap_cv_cf"], df["wk_gap_cv_cf"], df["wg_gap_cv_cf"],
        df["pct_gap_cf_ce"], df["wk_gap_cf_ce"], df["wg_gap_cf_ce"],
    ):
        fig.add_annotation(
            x=pct_ceil + 1.5, y=cat,
            xref="x", yref="y",
            text=(
                f"Conv-Conf  +{p1:.1f}pp | {fmt_workers(w1)} wk | {fmt_wages(g1)}<br>"
                f"Conf-Ceil  +{p2:.1f}pp | {fmt_workers(w2)} wk | {fmt_wages(g2)}"
            ),
            showarrow=False,
            xanchor="left", yanchor="middle",
            font=dict(size=11, color=PAPER_PALETTE["text"], family=FONT_FAMILY),
        )

    fig.update_layout(barmode="stack", bargap=0.22)
    style_paper_figure(
        fig,
        "Conversational > Confirmed > Ceiling Reach by Major Sector",
        subtitle=(
            f"All 22 major occ categories | "
            f"Sorted by Conv-Confirmed % tasks gap (largest at top) | "
            f"Middle-segment color = workers added in that gap "
            f"({fmt_workers(wk_min)} to {fmt_workers(wk_max_v)}) | "
            f"National | freq, auto-aug ON"
        ),
        height=920, width=PAPER_W + 250,
        margin=dict(l=30, r=560, t=110, b=120),
    )
    x_top = max(df["pct_ceil"]) * 1.04
    fig.update_xaxes(
        title=dict(text="% Tasks Affected", font=dict(size=LABEL_FS)),
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        ticksuffix="%", range=[0, x_top],
    )
    fig.update_yaxes(
        showgrid=False, showline=False,
        tickfont=dict(size=TICK_FS - 2),
    )
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom", y=-0.13, xanchor="left", x=0,
            font=dict(size=11),
            bgcolor="rgba(255,255,255,0.9)",
        ),
    )

    save_figure(fig, results / "figures" / "conv_confirmed_ceiling_gap.png", scale=2)
    _copy_fig(results, figures, "conv_confirmed_ceiling_gap.png")
    print("  -> conv_confirmed_ceiling_gap.png")


# ─────────────────────────────────────────────────────────────────────────
# Figure 3: AI intensity vs. median-rank anchor (chart 15 from
# exploratory/pct_norm_vs_eco v3) — major occ categories ranked by
# Σ pct (rated, bias-corrected) / Σ (freq × emp) over FULL eco_2025.
# Bars colored by pct_tasks_affected (darker = higher).
# Imports at function level so part_3 can still run if exploratory/ is
# absent (folder is gitignored).
# ─────────────────────────────────────────────────────────────────────────

def build_intensity_anchor_fulleco(results: Path, figures: Path) -> None:
    try:
        from analysis.exploratory.pct_norm_vs_eco.run import (
            BIAS_VARIANTS, compute_bias_ratios,
        )
        from analysis.exploratory.pct_norm_vs_eco.run_v3 import (
            compute_v3_intensity,
            compute_major_full_eco_denominator,
            compute_major_pct_tasks_affected,
        )
    except ImportError as exc:
        print(f"  -> SKIPPED: exploratory/pct_norm_vs_eco not available ({exc})")
        return

    base = compute_v3_intensity(
        "all_confirmed", compute_bias_ratios(BIAS_VARIANTS["equal"])
    ).copy()
    full_den = compute_major_full_eco_denominator()
    base["den_full"] = base["category"].map(full_den).fillna(0.0)
    base["ratio_full"] = np.where(
        base["den_full"] > 0, base["num"] / base["den_full"], 0.0
    )
    total_full = base["ratio_full"].sum()
    base["ratio_full_pct"] = (
        base["ratio_full"] / total_full * 100.0 if total_full > 0 else 0.0
    )
    pct_aff = compute_major_pct_tasks_affected()
    base["pct_tasks_affected"] = base["category"].map(pct_aff).fillna(0.0)

    # Anchor major: 12th of 22 sorted ascending on chart 12's rated-denom
    # ratio_pct (matching v3's anchor selection so charts 12-15 are comparable).
    # Apply that anchor to chart 15's full-eco ratio_full_pct.
    base_sorted = base.sort_values("ratio_pct", ascending=True).reset_index(drop=True)
    anchor_major = base_sorted.iloc[11]["category"]
    anchor_val = base.loc[base["category"] == anchor_major, "ratio_full_pct"].iloc[0]
    assert anchor_val > 0, f"Anchor value for {anchor_major} must be > 0"
    base["lift"] = base["ratio_full_pct"] / anchor_val
    median_lift = float(base["lift"].median())

    out = base[["category", "ratio_full_pct", "lift", "pct_tasks_affected"]].copy()
    out["anchor_value"] = anchor_val
    out["median_lift"] = median_lift
    save_csv(
        out.sort_values("lift", ascending=False),
        results / "intensity_anchor_fulleco.csv",
        float_format="%.4f",
    )

    plot_df = base.sort_values("lift", ascending=True).reset_index(drop=True)
    cvals = plot_df["pct_tasks_affected"].to_numpy(dtype=float)
    cmin, cmax = cvals.min(), cvals.max()
    if cmax > cmin:
        ts = (cvals - cmin) / (cmax - cmin)
    else:
        ts = np.full_like(cvals, 0.5)

    def _interp(t: float) -> str:
        light = (196, 217, 210)  # #c4d9d2
        dark = (10, 46, 37)      # #0a2e25
        rgb = tuple(int(light[i] + max(0.0, min(1.0, t)) * (dark[i] - light[i])) for i in range(3))
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    bar_colors = [_interp(t) for t in ts]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=plot_df["category"], x=plot_df["lift"], orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"{v:.2f}x" for v in plot_df["lift"]],
        textposition="outside",
        textfont=dict(size=12, color=PAPER_PALETTE["text"], family=FONT_FAMILY),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>lift: %{x:.2f}x<extra></extra>",
        showlegend=False,
    ))

    # Median reference line
    fig.add_vline(
        x=median_lift, line_dash="dash",
        line_color=PAPER_PALETTE["negative"], line_width=1.5,
    )
    fig.add_annotation(
        x=median_lift, y=1.005,
        xref="x", yref="paper",
        text=f"median = {median_lift:.2f}x",
        showarrow=False, xanchor="left", yanchor="bottom",
        font=dict(size=ANNOT_FS, color=PAPER_PALETTE["negative"], family=FONT_FAMILY),
    )

    style_paper_figure(
        fig,
        "AI Intensity vs. Median-Rank Anchor — All Confirmed (full eco_2025 denominator)",
        subtitle=(
            f"All Confirmed (AEI Both + Micro 2026-02-12) - equal 3-source consensus bias correction | "
            f"Sigma pct (rated) / Sigma (freq x emp) over FULL eco_2025, renormalized | "
            f"Anchor: {anchor_major} = 1.00x | "
            f"Bar shading: darker = higher pct_tasks_affected"
        ),
        height=820, width=PAPER_W,
        margin=dict(l=30, r=140, t=110, b=110),
    )
    x_top = max(plot_df["lift"]) * 1.18
    fig.update_xaxes(
        title=dict(
            text="AI usage relative to anchor major (x) - Sigma pct (rated) / Sigma (freq x emp) over FULL eco_2025, renormalized",
            font=dict(size=LABEL_FS),
        ),
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        range=[0, x_top],
    )
    fig.update_yaxes(
        showgrid=False, showline=False,
        tickfont=dict(size=TICK_FS - 2),
    )

    save_figure(fig, results / "figures" / "intensity_anchor_fulleco.png", scale=2)
    _copy_fig(results, figures, "intensity_anchor_fulleco.png")
    print("  -> intensity_anchor_fulleco.png")


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figures = HERE / "figures"
    figures.mkdir(exist_ok=True)

    print("=" * 64)
    print("Part 3: Action — What To Do About It")
    print("=" * 64)

    print("\n[1/3] Tech commodities composite")
    build_tech_commodities(results, figures)

    print("\n[2/3] Conv -> Confirmed -> Ceiling gap by major")
    build_conv_confirmed_ceiling_gap(results, figures)

    print("\n[3/3] AI intensity vs. median-rank anchor (full eco_2025)")
    build_intensity_anchor_fulleco(results, figures)

    print("\n" + "=" * 64)
    print("Part 3 complete — figures in results/figures/ and figures/")
    print("=" * 64)


if __name__ == "__main__":
    main()
