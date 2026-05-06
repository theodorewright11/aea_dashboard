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
    ANNOT_FS, LABEL_FS, TICK_FS, INSIDE_FS,
    METRIC_COLORS, PAPER_PALETTE,
    style_paper_figure, fmt_wages, fmt_workers,
)

HERE = Path(__file__).resolve().parent
ANALYSIS_DATA_DIR = ROOT / "analysis" / "data"
TECH_SKILLS_FILE = ANALYSIS_DATA_DIR / "technology_skills_v30.1.csv"

PRIMARY_KEY = "all_confirmed"
PRIMARY_DATASET = ANALYSIS_CONFIGS[PRIMARY_KEY]
PRIMARY_LABEL = ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]

# Tasks blue + workers green blend, light → dark (used by tech_commodities)
BLEND_LIGHT = "#cdd9d4"
BLEND_DARK = "#2a4f56"
TASKS_LIGHT = "#cfe0ec"
TASKS_DARK = "#2c4f6b"


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
        f"{p:.1f}% avg | {fmt_workers(wk)} workers | {fmt_wages(wa)} wages | "
        f"{o} occs | {int(ne):,} entries"
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
            colorscale=[[0, BLEND_LIGHT], [1, BLEND_DARK]],
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
        subtitle="Composite = √(% tasks × workers), each min-max scaled to 0–1",
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
    """Top 10 majors by Conv→Confirmed % tasks gap, stacked into 3 segments:
    Conv base (tasks-blue) + Conv→Confirmed gap (workers-shaded) + Confirmed→
    Ceiling extension. Bar text shows +pp; right-side labels show
    workers + wages deltas only."""
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

    top10 = df.sort_values("pct_gap_cv_cf", ascending=False).head(10)
    df = top10.sort_values("pct_gap_cv_cf", ascending=True)  # plotly bottom-up
    cats = df["category"].tolist()

    fig = go.Figure()

    # Segment 1: Conversational base — tasks blue
    fig.add_trace(go.Bar(
        y=cats, x=df["pct_conv"], orientation="h",
        name="Conversational confirmed",
        marker=dict(color=METRIC_COLORS["tasks"], line=dict(width=0)),
        text=[f"{v:.0f}%" for v in df["pct_conv"]],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(size=ANNOT_FS, color="white", family=FONT_FAMILY),
        hovertemplate="<b>%{y}</b><br>Conversational: %{x:.1f}%<extra></extra>",
    ))

    # Segment 2: Conv → Confirmed gap (focal — workers-added gradient)
    fig.add_trace(go.Bar(
        y=cats, x=df["pct_gap_cv_cf"], orientation="h",
        name="Conv → Confirmed (agentic)",
        marker=dict(
            color=df["wk_gap_cv_cf"].values,
            colorscale=[[0, BLEND_LIGHT], [1, BLEND_DARK]],
            showscale=False,
            line=dict(width=0),
        ),
        text=[f"+{v:.0f}pp" for v in df["pct_gap_cv_cf"]],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(size=ANNOT_FS, color="white", family=FONT_FAMILY),
        hovertemplate="<b>%{y}</b><br>Conv → Conf gap: +%{x:.1f}pp<extra></extra>",
    ))

    # Segment 3: Confirmed → Ceiling extension
    fig.add_trace(go.Bar(
        y=cats, x=df["pct_gap_cf_ce"], orientation="h",
        name="Confirmed → Ceiling",
        marker=dict(color="#e8d9b8", opacity=0.85, line=dict(width=0)),
        text=[f"+{v:.0f}pp" for v in df["pct_gap_cf_ce"]],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(size=ANNOT_FS, color=PAPER_PALETTE["text_dark"], family=FONT_FAMILY),
        hovertemplate="<b>%{y}</b><br>Conf → Ceil gap: +%{x:.1f}pp<extra></extra>",
    ))

    # Right-side annotations: split into two stacked annotations per row to
    # avoid <br> rendering quirks in this plotly+kaleido combination.
    n_rows = len(cats)
    for idx, (cat, pct_ceil, w1, g1, w2, g2) in enumerate(zip(
        cats, df["pct_ceil"],
        df["wk_gap_cv_cf"], df["wg_gap_cv_cf"],
        df["wk_gap_cf_ce"], df["wg_gap_cf_ce"],
    )):
        # Each row occupies one categorical y position; offset by ±0.18 in
        # the categorical axis to stack two text lines per row.
        fig.add_annotation(
            x=pct_ceil + 1.5,
            y=idx + 0.20,
            xref="x", yref="y",
            text=f"Agentic: {fmt_workers(w1)} workers · {fmt_wages(g1)}",
            showarrow=False,
            xanchor="left", yanchor="middle",
            font=dict(size=ANNOT_FS, color=PAPER_PALETTE["text"], family=FONT_FAMILY),
        )
        fig.add_annotation(
            x=pct_ceil + 1.5,
            y=idx - 0.20,
            xref="x", yref="y",
            text=f"Ceiling: {fmt_workers(w2)} workers · {fmt_wages(g2)}",
            showarrow=False,
            xanchor="left", yanchor="middle",
            font=dict(size=ANNOT_FS, color=PAPER_PALETTE["text"], family=FONT_FAMILY),
        )

    fig.update_layout(barmode="stack", bargap=0.25)
    style_paper_figure(
        fig,
        "Conversational → Confirmed → Ceiling Reach by Major Sector (Top 10)",
        subtitle="Sorted by Conv → Confirmed gap. Middle-segment color shades by workers added.",
        height=600, width=PAPER_W + 250,
        margin=dict(l=30, r=560, t=110, b=120),
    )
    x_top = max(df["pct_ceil"]) * 1.04
    fig.update_xaxes(
        title=dict(text="% Tasks Affected", font=dict(size=LABEL_FS)),
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        ticksuffix="%", range=[0, x_top],
        tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
    )
    fig.update_yaxes(
        showgrid=False, showline=False,
        tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
    )
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom", y=-0.18, xanchor="left", x=0,
            font=dict(size=ANNOT_FS, family=FONT_FAMILY),
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
        light = (207, 224, 236)  # #cfe0ec — tasks light
        dark = (44, 79, 107)     # #2c4f6b — tasks dark
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
        "AI Usage Intensity by Sector",
        subtitle=(
            f"Anchor: {anchor_major} = 1.00× — bars are usage per unit of economic activity, "
            "shaded by % tasks affected"
        ),
        height=820, width=PAPER_W,
        margin=dict(l=30, r=140, t=110, b=110),
    )
    x_top = max(plot_df["lift"]) * 1.18
    fig.update_xaxes(
        title=dict(text="Usage relative to anchor (×)", font=dict(size=LABEL_FS)),
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        range=[0, x_top],
        tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
    )
    fig.update_yaxes(
        showgrid=False, showline=False,
        tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
    )

    save_figure(fig, results / "figures" / "intensity_anchor_fulleco.png", scale=2)
    _copy_fig(results, figures, "intensity_anchor_fulleco.png")
    print("  -> intensity_anchor_fulleco.png")


# ─────────────────────────────────────────────────────────────────────────
# Figure 4: Risk Score Audit — Section 5f (SKA-gated focused 43)
# Pulls audit's flag-frame + focused-set builders, renders in paper style.
# Skips gracefully if exploratory/risk_score_audit isn't available.
# ─────────────────────────────────────────────────────────────────────────

def build_risk_score_5f(results: Path, figures: Path) -> None:
    try:
        from analysis.exploratory.risk_score_audit.run import (
            _load_flag_df, _build_focused_set,
        )
    except ImportError as exc:
        print(f"  -> SKIPPED: exploratory/risk_score_audit not available ({exc})")
        return

    flags_df = _load_flag_df()
    sub = _build_focused_set(flags_df)
    s5f = sub[sub["ska_gated"] == 1].copy()
    s5f["abs_emp"] = s5f["emp_proj_pct"].abs()
    s5f = s5f.sort_values("abs_emp", ascending=True).reset_index(drop=True)

    save_csv(
        s5f.sort_values("abs_emp", ascending=False)[
            ["title_current", "major_short", "job_zone", "emp_proj_pct",
             "pct", "ska_pct", "pct_delta", "workers_affected", "wages_affected"]
        ],
        results / "risk_score_5f.csv",
        float_format="%.3f",
    )

    pct_min_f = float(s5f["pct"].min())
    pct_max_f = float(s5f["pct"].max())

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=s5f["title_current"], x=s5f["abs_emp"], orientation="h",
        marker=dict(
            color=s5f["pct"].values,
            colorscale=[[0, TASKS_LIGHT], [1, TASKS_DARK]],
            cmin=pct_min_f, cmax=pct_max_f,
            line=dict(width=0),
        ),
        text=[
            f"{r['emp_proj_pct']:+.1f}% emp proj  |  {r['major_short']}  |  "
            f"pct {r['pct']:.0f}%  |  zone {int(r['job_zone'])}"
            for _, r in s5f.iterrows()
        ],
        textposition="outside",
        textfont=dict(size=ANNOT_FS - 1, color=PAPER_PALETTE["neutral"],
                      family=FONT_FAMILY),
        cliponaxis=False, showlegend=False,
        hovertemplate="<b>%{y}</b><br>emp proj: -%{x:.1f}%<extra></extra>",
    ))

    n = len(s5f)
    height = max(900, n * 25 + 220)

    style_paper_figure(
        fig,
        f"Occupations Most At Risk Of Displacement (n={n})",
        subtitle=(
            "% tasks affected > 50, growth above median, BLS projects employment decline, "
            "and AI capability exceeds median SKA need. "
            "Bar shading: darker = higher % tasks affected."
        ),
        height=height, width=PAPER_W + 200,
        margin=dict(l=380, r=440, t=110, b=110),
    )
    fig.update_xaxes(
        title=dict(text="BLS projected employment decline 2024–2034 (%)",
                   font=dict(size=LABEL_FS)),
        showgrid=True, gridcolor=PAPER_PALETTE["grid"], ticksuffix="%",
        tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
    )
    fig.update_yaxes(
        showgrid=False, showline=False,
        tickfont=dict(size=TICK_FS - 4, family=FONT_FAMILY),
    )
    fig.update_layout(bargap=0.25)

    save_figure(fig, results / "figures" / "risk_score_5f.png", scale=2)
    _copy_fig(results, figures, "risk_score_5f.png")
    print("  -> risk_score_5f.png")


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

    print("\n[1/4] Conv -> Confirmed -> Ceiling gap by major (top 10)")
    build_conv_confirmed_ceiling_gap(results, figures)

    print("\n[2/4] Tech commodities composite")
    build_tech_commodities(results, figures)

    print("\n[3/4] Risk score 5f — SKA-gated focused 43")
    build_risk_score_5f(results, figures)

    print("\n[4/4] AI intensity vs. median-rank anchor (full eco_2025)")
    build_intensity_anchor_fulleco(results, figures)

    print("\n" + "=" * 64)
    print("Part 3 complete — figures in results/figures/ and figures/")
    print("=" * 64)


if __name__ == "__main__":
    main()
