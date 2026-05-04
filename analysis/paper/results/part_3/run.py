"""
Part 3 — Action: What To Do About It

Eight figures, audience-organized:

  Framing:
    0. Property biplot (PCA on 12 task properties at occ level)

  For Organizations:
    1. Tech commodities composite (top-25)
    2. Conversational vs. agentic footprint (sectors)
    3. Gap to ceiling (top sectors by confirmed→ceiling worker gap)

  For Policy:
    4. Risk × recovery (a) — 8-flag risk score × SKA overall_gap
    5. Risk × recovery (b) — pct_tasks_affected × mean(nt + de)
    6. Phys/Mixed/Non-physical × friction sub-bands

  For Individuals:
    7. Tacit knowledge × duration scatter + employment-quartile bar

Run from project root:
    venv/Scripts/python -m analysis.paper.results.part_3.run
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.config import (
    ANALYSIS_CONFIGS,
    ANALYSIS_CONFIG_LABELS,
    ROOT,
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.utils import CATEGORY_PALETTE, FONT_FAMILY, save_csv, save_figure
from analysis.paper.paper_config import (
    PAPER_W, PAPER_H,
    TITLE_FS, SUBTITLE_FS, INSIDE_FS, OUTSIDE_FS, TICK_FS, LABEL_FS,
    LEGEND_FS, ANNOT_FS,
    METRIC_COLORS, CONFIG_COLORS, PAPER_PALETTE,
    style_paper_figure, fmt_wages, fmt_workers,
)

HERE = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
ANALYSIS_DATA_DIR = ROOT / "analysis" / "data"
PROPS_CSV = DATA_DIR / "final_eco_2025_with_task_properties.csv"
TECH_SKILLS_FILE = ANALYSIS_DATA_DIR / "technology_skills_v30.1.csv"

PRIMARY_KEY = "all_confirmed"
PRIMARY_DATASET = ANALYSIS_CONFIGS[PRIMARY_KEY]
PRIMARY_LABEL = ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]
CONFIG_SUBTITLE = f"{PRIMARY_LABEL} | National | freq, auto-aug ON"

PROP_KEYS = ["m", "d", "s", "r", "h", "e", "t", "tf", "df", "de", "nt", "ac"]
SUITABILITY_KEYS = ["s", "d", "m", "h"]
FRICTION_KEYS = ["r", "df", "tf"]
OFFSET_KEYS = ["nt", "de"]


# ─────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────

def _copy_fig(results: Path, figures: Path, name: str) -> None:
    shutil.copy(results / "figures" / name, figures / name)


def _load_eco_props() -> pd.DataFrame:
    """Per-task properties + occupation context. One row per (task, occ)."""
    keep = [
        "task_normalized", "title_current", "soc_code_2019_full",
        "major_occ_category", "minor_occ_category", "broad_occ",
        "physical", "freq_mean", "job_zone",
        "emp_tot_nat_2024", "a_med_nat_2024",
    ] + PROP_KEYS
    df = pd.read_csv(PROPS_CSV, usecols=keep)
    for k in PROP_KEYS:
        assert df[k].between(1, 5).all(), f"{k} out of [1,5] range"
    return df


def _occ_property_means(eco: pd.DataFrame) -> pd.DataFrame:
    """One row per occupation with mean of each property + structural cols.
    Mean is unweighted across that occupation's tasks (consistent with how
    the property biplot, nt+de, e/t, and friction charts each interpret
    the occupation as a "property bundle")."""
    grouped = eco.groupby("title_current")
    occ = grouped[PROP_KEYS].mean().reset_index()
    structural = grouped.agg(
        major_occ_category=("major_occ_category", "first"),
        emp=("emp_tot_nat_2024", "first"),
        wage=("a_med_nat_2024", "first"),
        n_tasks=("task_normalized", "size"),
        n_physical=("physical", "sum"),
    ).reset_index()
    occ = occ.merge(structural, on="title_current", how="left")
    occ["pct_physical"] = occ["n_physical"] / occ["n_tasks"] * 100.0
    return occ


def _major_color_map(majors: list[str]) -> dict[str, str]:
    """Stable color mapping for major categories."""
    uniq = sorted({m for m in majors if isinstance(m, str) and m})
    return {m: CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)] for i, m in enumerate(uniq)}


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
# Figure 0: Property biplot (PCA framing)
# ─────────────────────────────────────────────────────────────────────────

def build_property_biplot(results: Path, figures: Path) -> None:
    eco = _load_eco_props()
    occ = _occ_property_means(eco)

    X = occ[PROP_KEYS].to_numpy(dtype=float)
    mu = X.mean(axis=0)
    sigma = X.std(axis=0, ddof=1)
    sigma[sigma == 0] = 1.0
    Xs = (X - mu) / sigma  # z-scored

    # SVD-based PCA
    U, S, Vt = np.linalg.svd(Xs, full_matrices=False)
    var = (S ** 2) / (Xs.shape[0] - 1)
    var_ratio = var / var.sum()
    scores = U * S  # (n_occ, n_props)
    loadings = Vt.T  # (n_props, n_props)

    pc1 = scores[:, 0]
    pc2 = scores[:, 1]
    # Sign convention: PC1 oriented so that "physical" properties (low s, high physical)
    # land on negative side. We orient PC1 by correlation with mean s (suitability).
    s_mean = occ["s"].to_numpy()
    if np.corrcoef(pc1, s_mean)[0, 1] < 0:
        pc1 = -pc1
        loadings[:, 0] = -loadings[:, 0]
    # PC2: orient so that frictions sit on the positive side
    fric_mean = occ[FRICTION_KEYS].mean(axis=1).to_numpy()
    if np.corrcoef(pc2, fric_mean)[0, 1] < 0:
        pc2 = -pc2
        loadings[:, 1] = -loadings[:, 1]

    occ["pc1"] = pc1
    occ["pc2"] = pc2

    # Save loadings + variance
    loadings_df = pd.DataFrame(loadings[:, :3], index=PROP_KEYS, columns=["PC1", "PC2", "PC3"])
    loadings_df["explained_var_ratio"] = np.nan
    loadings_df.loc[loadings_df.index[0], "explained_var_ratio"] = var_ratio[0]
    loadings_df.loc[loadings_df.index[1], "explained_var_ratio"] = var_ratio[1]
    save_csv(loadings_df.reset_index().rename(columns={"index": "property"}),
             results / "property_biplot_loadings.csv", float_format="%.4f")
    save_csv(occ[["title_current", "major_occ_category", "pc1", "pc2"]],
             results / "property_biplot_scores.csv", float_format="%.4f")

    color_map = _major_color_map(occ["major_occ_category"].dropna().tolist())

    fig = go.Figure()
    for major, sub in occ.groupby("major_occ_category", sort=False):
        if not isinstance(major, str) or not major:
            continue
        fig.add_trace(go.Scatter(
            x=sub["pc1"], y=sub["pc2"],
            mode="markers",
            name=major,
            marker=dict(
                size=8,
                color=color_map.get(major, PAPER_PALETTE["neutral"]),
                opacity=0.65,
                line=dict(width=0.5, color="#ffffff"),
            ),
            text=sub["title_current"],
            hovertemplate="<b>%{text}</b><br>" + major +
                          "<br>PC1=%{x:.2f} PC2=%{y:.2f}<extra></extra>",
            showlegend=True,
            legendgroup=major,
        ))

    # Loading arrows — scale so longest arrow ≈ 85% of the visible data range
    loading_norms = np.sqrt(loadings[:, 0] ** 2 + loadings[:, 1] ** 2)
    max_loading = float(loading_norms.max())
    plot_extent = float(np.max(np.abs([occ["pc1"], occ["pc2"]])))
    arrow_scale = 0.85 * plot_extent / max(max_loading, 1e-9)
    for i, prop in enumerate(PROP_KEYS):
        lx = loadings[i, 0] * arrow_scale
        ly = loadings[i, 1] * arrow_scale
        fig.add_annotation(
            ax=0, ay=0, axref="x", ayref="y",
            x=lx, y=ly,
            xref="x", yref="y",
            showarrow=True, arrowhead=3, arrowsize=1.4, arrowwidth=2.0,
            arrowcolor=PAPER_PALETTE["text_dark"],
        )
        # Push label out a bit beyond the arrow tip, in the same direction
        norm_xy = max(np.sqrt(lx * lx + ly * ly), 1e-9)
        ext = 0.12 * plot_extent / norm_xy
        fig.add_annotation(
            x=lx * (1 + ext), y=ly * (1 + ext),
            xref="x", yref="y",
            text=f"<b>{prop}</b>",
            showarrow=False,
            font=dict(size=15, color=PAPER_PALETTE["text_dark"], family=FONT_FAMILY),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=PAPER_PALETTE["grid"], borderwidth=1, borderpad=3,
        )

    var_pc1 = var_ratio[0] * 100.0
    var_pc2 = var_ratio[1] * 100.0
    style_paper_figure(
        fig,
        "12 Task Properties Collapse to ~2 Dimensions",
        subtitle=(
            f"PC1 = phys/info ({var_pc1:.0f}% variance) | "
            f"PC2 = friction load ({var_pc2:.0f}% variance) | "
            f"Each point = one occupation, mean across its tasks | "
            f"{CONFIG_SUBTITLE}"
        ),
        height=820, width=PAPER_W,
        margin=dict(l=70, r=240, t=110, b=100),
    )
    fig.update_xaxes(
        title=dict(text=f"PC1  (phys/info — {var_pc1:.0f}%)", font=dict(size=LABEL_FS)),
        zeroline=True, zerolinecolor=PAPER_PALETTE["grid"], zerolinewidth=1,
        gridcolor=PAPER_PALETTE["grid"], showline=False,
    )
    fig.update_yaxes(
        title=dict(text=f"PC2  (frictions — {var_pc2:.0f}%)", font=dict(size=LABEL_FS)),
        zeroline=True, zerolinecolor=PAPER_PALETTE["grid"], zerolinewidth=1,
        gridcolor=PAPER_PALETTE["grid"], showline=False,
    )
    fig.update_layout(
        legend=dict(
            orientation="v",
            yanchor="top", y=1.0, xanchor="left", x=1.02,
            font=dict(size=10),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=PAPER_PALETTE["grid"], borderwidth=1,
        ),
    )

    save_figure(fig, results / "figures" / "property_biplot.png", scale=2)
    _copy_fig(results, figures, "property_biplot.png")
    print("  -> property_biplot.png")


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
# Figure 2: Conversational vs. agentic footprint (sectors)
# ─────────────────────────────────────────────────────────────────────────

def build_conv_vs_agentic(results: Path, figures: Path) -> None:
    conv = _run_config(ANALYSIS_CONFIGS["human_conversation"], "major")
    agentic_ceiling = _run_config(ANALYSIS_CONFIGS["agentic_ceiling"], "major")
    agentic_confirmed = _run_config(ANALYSIS_CONFIGS["agentic_confirmed"], "major")

    keep_cols = ["category", "pct_tasks_affected", "workers_affected", "wages_affected"]
    df = (
        conv[keep_cols].rename(columns={
            "pct_tasks_affected": "pct_conv",
            "workers_affected": "wk_conv",
            "wages_affected": "wg_conv",
        }).merge(
            agentic_confirmed[keep_cols].rename(columns={
                "pct_tasks_affected": "pct_agconf",
                "workers_affected": "wk_agconf",
                "wages_affected": "wg_agconf",
            }), on="category"
        ).merge(
            agentic_ceiling[keep_cols].rename(columns={
                "pct_tasks_affected": "pct_agceil",
                "workers_affected": "wk_agceil",
                "wages_affected": "wg_agceil",
            }), on="category"
        )
    )
    df["agentic_headroom"] = df["pct_agceil"] - df["pct_conv"]
    df = df.sort_values("agentic_headroom", ascending=False).head(15).copy()
    save_csv(df, results / "conv_vs_agentic.csv")

    df = df.sort_values("agentic_headroom", ascending=True)  # plotly bottom-up
    cats = df["category"].tolist()

    fig = go.Figure()

    # Conversational
    fig.add_trace(go.Bar(
        y=cats, x=df["pct_conv"], orientation="h",
        name="Conversational Confirmed",
        marker=dict(color=CONFIG_COLORS["human_conversation"], line=dict(width=0)),
        text=[f"{v:.0f}%" for v in df["pct_conv"]],
        textposition="inside", insidetextanchor="end",
        textfont=dict(size=12, color="white", family=FONT_FAMILY),
        hovertemplate="%{y}<br>Conversational: %{x:.1f}%<extra></extra>",
    ))
    # Agentic Confirmed
    fig.add_trace(go.Bar(
        y=cats, x=df["pct_agconf"], orientation="h",
        name="Agentic Confirmed",
        marker=dict(color=CONFIG_COLORS["agentic_confirmed"], line=dict(width=0)),
        text=[f"{v:.0f}%" for v in df["pct_agconf"]],
        textposition="inside", insidetextanchor="end",
        textfont=dict(size=12, color="white", family=FONT_FAMILY),
        hovertemplate="%{y}<br>Agentic Confirmed: %{x:.1f}%<extra></extra>",
    ))
    # Agentic Ceiling
    fig.add_trace(go.Bar(
        y=cats, x=df["pct_agceil"], orientation="h",
        name="Agentic Ceiling",
        marker=dict(color=CONFIG_COLORS["agentic_ceiling"], line=dict(width=0)),
        text=[f"{v:.0f}%" for v in df["pct_agceil"]],
        textposition="inside", insidetextanchor="end",
        textfont=dict(size=12, color="white", family=FONT_FAMILY),
        hovertemplate="%{y}<br>Agentic Ceiling: %{x:.1f}%<extra></extra>",
    ))

    # Headroom annotations on the right
    annotations_x = [max(c, ag1, ag2) + 1 for c, ag1, ag2 in
                     zip(df["pct_conv"], df["pct_agconf"], df["pct_agceil"])]
    fig.add_trace(go.Scatter(
        y=cats, x=annotations_x, mode="text",
        text=[f"+{h:.0f}pp ceiling gap" for h in df["agentic_headroom"]],
        textposition="middle right",
        textfont=dict(size=ANNOT_FS, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showlegend=False, hoverinfo="skip",
    ))

    fig.update_layout(barmode="group", bargap=0.20, bargroupgap=0.10)
    style_paper_figure(
        fig,
        "Conversational vs. Agentic AI Footprint by Sector",
        subtitle=(
            "Top 15 sectors by ceiling-minus-conversational gap | "
            "Conversational = AEI Conv + Microsoft | "
            "Agentic Confirmed = AEI API | Agentic Ceiling = MCP + AEI API | "
            "National | freq, auto-aug ON"
        ),
        height=720, width=PAPER_W,
        margin=dict(l=30, r=200, t=110, b=110),
    )
    fig.update_xaxes(
        title=dict(text="% Tasks Affected", font=dict(size=LABEL_FS)),
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        ticksuffix="%", range=[0, max(df["pct_agceil"]) * 1.18],
    )
    fig.update_yaxes(showgrid=False, showline=False, tickfont=dict(size=TICK_FS - 1))

    save_figure(fig, results / "figures" / "conv_vs_agentic.png", scale=2)
    _copy_fig(results, figures, "conv_vs_agentic.png")
    print("  -> conv_vs_agentic.png")


# ─────────────────────────────────────────────────────────────────────────
# Figure 3: Gap to Ceiling (sector-level)
# ─────────────────────────────────────────────────────────────────────────

def build_gap_to_ceiling(results: Path, figures: Path) -> None:
    confirmed = _run_config(ANALYSIS_CONFIGS["all_confirmed"], "major")
    ceiling = _run_config(ANALYSIS_CONFIGS["all_ceiling"], "major")

    df = (
        confirmed[["category", "pct_tasks_affected", "workers_affected", "wages_affected"]]
        .rename(columns={
            "pct_tasks_affected": "pct_conf",
            "workers_affected": "wk_conf",
            "wages_affected": "wg_conf",
        })
        .merge(
            ceiling[["category", "pct_tasks_affected", "workers_affected", "wages_affected"]]
            .rename(columns={
                "pct_tasks_affected": "pct_ceil",
                "workers_affected": "wk_ceil",
                "wages_affected": "wg_ceil",
            }),
            on="category",
        )
    )
    df["wk_gap"] = df["wk_ceil"] - df["wk_conf"]
    df["wg_gap"] = df["wg_ceil"] - df["wg_conf"]
    df["pct_gap"] = df["pct_ceil"] - df["pct_conf"]

    df = df.sort_values("wk_gap", ascending=False).head(15).copy()
    save_csv(df, results / "gap_to_ceiling.csv")
    df = df.sort_values("wk_gap", ascending=True)
    cats = df["category"].tolist()

    fig = go.Figure()

    # Confirmed (base)
    fig.add_trace(go.Bar(
        y=cats, x=df["wk_conf"], orientation="h",
        name="Confirmed (workers affected)",
        marker=dict(color=CONFIG_COLORS["all_confirmed"], line=dict(width=0)),
        text=[fmt_workers(v) for v in df["wk_conf"]],
        textposition="inside", insidetextanchor="end",
        textfont=dict(size=12, color="white", family=FONT_FAMILY),
        hovertemplate="%{y}<br>Confirmed: %{x:,.0f}<extra></extra>",
    ))
    # Gap stacked on top
    fig.add_trace(go.Bar(
        y=cats, x=df["wk_gap"], orientation="h",
        name="Gap to Ceiling",
        marker=dict(color=CONFIG_COLORS["all_ceiling"], opacity=0.55, line=dict(width=0)),
        text=[f"+{fmt_workers(v)}  (+{p:.0f}pp, +{fmt_wages(w)})"
              for v, p, w in zip(df["wk_gap"], df["pct_gap"], df["wg_gap"])],
        textposition="outside",
        textfont=dict(size=ANNOT_FS, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
        hovertemplate="%{y}<br>Gap: +%{x:,.0f}<extra></extra>",
    ))

    fig.update_layout(barmode="stack", bargap=0.25)
    style_paper_figure(
        fig,
        "Where Confirmed Use Sits Furthest Below Demonstrated Capability",
        subtitle=(
            "Top 15 sectors by all-confirmed → all-ceiling worker gap | "
            "Each row: confirmed bar + extension to ceiling | "
            "National | freq, auto-aug ON"
        ),
        height=720, width=PAPER_W,
        margin=dict(l=30, r=320, t=110, b=110),
    )
    max_total = (df["wk_conf"] + df["wk_gap"]).max()
    fig.update_xaxes(
        title=dict(text="Workers Affected", font=dict(size=LABEL_FS)),
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        range=[0, max_total * 1.30],
        tickformat=".2s",
    )
    fig.update_yaxes(showgrid=False, showline=False, tickfont=dict(size=TICK_FS - 1))

    save_figure(fig, results / "figures" / "gap_to_ceiling.png", scale=2)
    _copy_fig(results, figures, "gap_to_ceiling.png")
    print("  -> gap_to_ceiling.png")


# ─────────────────────────────────────────────────────────────────────────
# Figure 4: Risk × Recovery (a) — 8-flag risk × SKA gap
# ─────────────────────────────────────────────────────────────────────────

RISK_SCORES_CSV = (
    ROOT / "analysis" / "questions" / "job_exposure" / "job_risk_scoring"
    / "results" / "risk_scores_primary.csv"
)
SKA_GAPS_CSV = (
    ROOT / "analysis" / "questions" / "job_exposure" / "worker_resilience"
    / "results" / "occ_gaps_summary.csv"
)


def build_risk_x_ska(results: Path, figures: Path) -> None:
    assert RISK_SCORES_CSV.exists(), f"Risk scores CSV not found: {RISK_SCORES_CSV}"
    assert SKA_GAPS_CSV.exists(), f"SKA gaps CSV not found: {SKA_GAPS_CSV}"

    risk = pd.read_csv(RISK_SCORES_CSV)
    ska = pd.read_csv(SKA_GAPS_CSV)
    df = risk.merge(ska[["title_current", "overall_gap"]], on="title_current", how="inner")
    df = df.dropna(subset=["risk_score", "overall_gap", "employment", "major"])
    df["employment"] = df["employment"].fillna(0)

    save_csv(df[["title_current", "major", "employment", "risk_score", "risk_tier",
                 "pct_tasks_affected", "overall_gap"]],
             results / "risk_x_ska.csv", float_format="%.3f")

    color_map = _major_color_map(df["major"].tolist())
    sizeref = 2.0 * df["employment"].max() / (60 ** 2)

    fig = go.Figure()
    for major, sub in df.groupby("major", sort=False):
        fig.add_trace(go.Scatter(
            x=sub["risk_score"],
            y=sub["overall_gap"],
            mode="markers",
            name=major,
            marker=dict(
                size=sub["employment"],
                sizemode="area",
                sizeref=sizeref,
                sizemin=4,
                color=color_map.get(major, PAPER_PALETTE["neutral"]),
                opacity=0.65,
                line=dict(width=0.5, color="#ffffff"),
            ),
            text=sub["title_current"],
            customdata=np.stack([sub["employment"], sub["pct_tasks_affected"]], axis=-1),
            hovertemplate=(
                "<b>%{text}</b><br>" + major +
                "<br>Risk score: %{x}<br>SKA overall_gap: %{y:.1f}"
                "<br>Employment: %{customdata[0]:,.0f}"
                "<br>%% tasks affected: %{customdata[1]:.1f}%<extra></extra>"
            ),
            showlegend=True, legendgroup=major,
        ))

    # Annotate top displacement candidates (high risk, AI-leads SKA)
    annot_top = df[(df["risk_score"] >= 8) & (df["overall_gap"] > 0)].nlargest(5, "employment")
    for _, r in annot_top.iterrows():
        fig.add_annotation(
            x=r["risk_score"], y=r["overall_gap"],
            text=str(r["title_current"])[:35],
            showarrow=True, arrowhead=2, ax=20, ay=-25,
            font=dict(size=10, color=PAPER_PALETTE["text"], family=FONT_FAMILY),
            bgcolor="rgba(255,255,255,0.9)", bordercolor=PAPER_PALETTE["grid"], borderpad=2,
        )
    # Annotate most-resilient large occupations (low risk, big human advantage)
    annot_safe = df[(df["risk_score"] <= 3) & (df["overall_gap"] < df["overall_gap"].quantile(0.10))].nlargest(5, "employment")
    for _, r in annot_safe.iterrows():
        fig.add_annotation(
            x=r["risk_score"], y=r["overall_gap"],
            text=str(r["title_current"])[:35],
            showarrow=True, arrowhead=2, ax=-20, ay=20,
            font=dict(size=10, color=PAPER_PALETTE["text"], family=FONT_FAMILY),
            bgcolor="rgba(255,255,255,0.9)", bordercolor=PAPER_PALETTE["grid"], borderpad=2,
        )

    style_paper_figure(
        fig,
        "Risk × Recovery (Option A) — 8-Flag Risk Score vs. SKA Overall Gap",
        subtitle=(
            "x = composite risk score (0–10) | y = SKA overall_gap "
            "(negative = human advantage on skills/abilities/knowledge) | "
            "Bubble size = employment | " + CONFIG_SUBTITLE
        ),
        height=820, width=PAPER_W,
        margin=dict(l=70, r=240, t=110, b=110),
    )
    fig.add_hline(y=0, line_dash="dash", line_color=PAPER_PALETTE["grid"], line_width=1)
    fig.add_vline(x=5, line_dash="dot", line_color=PAPER_PALETTE["grid"], line_width=1)
    fig.update_xaxes(
        title=dict(text="Risk score (8 flags, weighted, 0–10)", font=dict(size=LABEL_FS)),
        gridcolor=PAPER_PALETTE["grid"], dtick=1, range=[-0.5, 10.5],
    )
    fig.update_yaxes(
        title=dict(text="SKA overall_gap  (–) human advantage  ↑  AI advantage (+)",
                   font=dict(size=LABEL_FS)),
        gridcolor=PAPER_PALETTE["grid"],
    )
    fig.update_layout(
        legend=dict(
            orientation="v",
            yanchor="top", y=1.0, xanchor="left", x=1.02,
            font=dict(size=10),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=PAPER_PALETTE["grid"], borderwidth=1,
        ),
    )
    save_figure(fig, results / "figures" / "risk_x_ska.png", scale=2)
    _copy_fig(results, figures, "risk_x_ska.png")
    print("  -> risk_x_ska.png")


# ─────────────────────────────────────────────────────────────────────────
# Figure 5: Risk × Recovery (b) — pct × (nt + de)
# ─────────────────────────────────────────────────────────────────────────

def build_pct_x_nt_de(results: Path, figures: Path) -> None:
    eco = _load_eco_props()
    occ = _occ_property_means(eco)
    pct = get_pct_tasks_affected(PRIMARY_DATASET)
    occ["pct"] = occ["title_current"].map(pct)
    occ = occ.dropna(subset=["pct", "nt", "de", "major_occ_category"])
    occ["nt_plus_de"] = occ["nt"] + occ["de"]
    occ["emp"] = occ["emp"].fillna(0)

    save_csv(
        occ[["title_current", "major_occ_category", "emp", "pct", "nt", "de", "nt_plus_de"]],
        results / "pct_x_nt_de.csv", float_format="%.3f",
    )

    pct_med = occ["pct"].median()
    nt_de_med = occ["nt_plus_de"].median()
    color_map = _major_color_map(occ["major_occ_category"].tolist())
    sizeref = 2.0 * occ["emp"].max() / (60 ** 2)

    fig = go.Figure()
    for major, sub in occ.groupby("major_occ_category", sort=False):
        fig.add_trace(go.Scatter(
            x=sub["pct"], y=sub["nt_plus_de"], mode="markers",
            name=major,
            marker=dict(
                size=sub["emp"], sizemode="area", sizeref=sizeref, sizemin=4,
                color=color_map.get(major, PAPER_PALETTE["neutral"]),
                opacity=0.65, line=dict(width=0.5, color="#ffffff"),
            ),
            text=sub["title_current"],
            hovertemplate=(
                "<b>%{text}</b><br>" + major +
                "<br>pct: %{x:.1f}%<br>nt+de: %{y:.2f}<extra></extra>"
            ),
            showlegend=True, legendgroup=major,
        ))

    # Quadrant labels
    pct_max = occ["pct"].max()
    nt_de_max = occ["nt_plus_de"].max()
    nt_de_min = occ["nt_plus_de"].min()
    fig.add_annotation(
        x=pct_max * 0.97, y=nt_de_min + (nt_de_max - nt_de_min) * 0.06,
        text="<b>Displacement risk</b><br>(high exposure, low offset)",
        showarrow=False, xanchor="right", yanchor="bottom",
        font=dict(size=12, color=PAPER_PALETTE["negative"], family=FONT_FAMILY),
        bgcolor="rgba(255,255,255,0.9)", bordercolor=PAPER_PALETTE["grid"],
        borderpad=4, borderwidth=1,
    )
    fig.add_annotation(
        x=pct_max * 0.97, y=nt_de_max * 0.98,
        text="<b>Exposure with offset</b><br>(high exposure, high new tasks + deployment efficiency)",
        showarrow=False, xanchor="right", yanchor="top",
        font=dict(size=12, color=PAPER_PALETTE["positive"], family=FONT_FAMILY),
        bgcolor="rgba(255,255,255,0.9)", bordercolor=PAPER_PALETTE["grid"],
        borderpad=4, borderwidth=1,
    )

    # Major-category centroids — labeled
    centroids = (
        occ.groupby("major_occ_category")
        .agg(pct=("pct", "mean"), nt_plus_de=("nt_plus_de", "mean"), emp=("emp", "sum"))
        .reset_index()
    )
    for _, r in centroids.iterrows():
        fig.add_annotation(
            x=r["pct"], y=r["nt_plus_de"],
            text=f"<b>{str(r['major_occ_category'])[:24]}</b>",
            showarrow=False,
            font=dict(size=10, color=PAPER_PALETTE["text_dark"], family=FONT_FAMILY),
            bgcolor="rgba(255,255,255,0.85)", borderpad=1,
        )

    style_paper_figure(
        fig,
        "Risk × Recovery (Option B) — Exposure vs. Offset Properties",
        subtitle=(
            f"x = % tasks affected | y = mean(nt + de) per occupation "
            f"(new-task creation + deployment efficiency) | "
            f"Bubble size = employment | major-category labels at centroids | "
            f"{CONFIG_SUBTITLE}"
        ),
        height=820, width=PAPER_W,
        margin=dict(l=70, r=240, t=110, b=110),
    )
    fig.add_hline(y=nt_de_med, line_dash="dash", line_color=PAPER_PALETTE["grid"], line_width=1)
    fig.add_vline(x=pct_med, line_dash="dot", line_color=PAPER_PALETTE["grid"], line_width=1)
    fig.update_xaxes(
        title=dict(text="% Tasks Affected (occupation level)", font=dict(size=LABEL_FS)),
        gridcolor=PAPER_PALETTE["grid"], ticksuffix="%",
    )
    fig.update_yaxes(
        title=dict(text="nt + de  (offset score, higher = more recovery)", font=dict(size=LABEL_FS)),
        gridcolor=PAPER_PALETTE["grid"],
    )
    fig.update_layout(
        legend=dict(
            orientation="v",
            yanchor="top", y=1.0, xanchor="left", x=1.02,
            font=dict(size=10),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=PAPER_PALETTE["grid"], borderwidth=1,
        ),
    )

    save_figure(fig, results / "figures" / "pct_x_nt_de.png", scale=2)
    _copy_fig(results, figures, "pct_x_nt_de.png")
    print("  -> pct_x_nt_de.png")


# ─────────────────────────────────────────────────────────────────────────
# Figure 6: Phys/Mixed/Non-physical × friction sub-bands
# ─────────────────────────────────────────────────────────────────────────

PHYS_LOWER = 33.0
PHYS_UPPER = 67.0


def build_phys_info_frictions(results: Path, figures: Path) -> None:
    eco = _load_eco_props()
    occ = _occ_property_means(eco)
    pct = get_pct_tasks_affected(PRIMARY_DATASET)
    occ["pct"] = occ["title_current"].map(pct)
    occ = occ.dropna(subset=["pct"])
    occ["friction_load"] = occ[FRICTION_KEYS].mean(axis=1)
    occ["bucket"] = "Mixed"
    occ.loc[occ["pct_physical"] < PHYS_LOWER, "bucket"] = "Non-physical"
    occ.loc[occ["pct_physical"] > PHYS_UPPER, "bucket"] = "Physical"

    # Per-bucket friction tertiles (low/mid/high relative to that bucket)
    occ["friction_band"] = "mid"
    parts = []
    for b in ["Non-physical", "Mixed", "Physical"]:
        sub = occ[occ["bucket"] == b].copy()
        if len(sub) < 6:
            sub["friction_band"] = "mid"
            parts.append(sub)
            continue
        q1, q2 = sub["friction_load"].quantile([1/3, 2/3]).tolist()
        sub.loc[sub["friction_load"] <= q1, "friction_band"] = "low"
        sub.loc[(sub["friction_load"] > q1) & (sub["friction_load"] <= q2), "friction_band"] = "mid"
        sub.loc[sub["friction_load"] > q2, "friction_band"] = "high"
        parts.append(sub)
    occ = pd.concat(parts, ignore_index=True)

    summary_rows = []
    for b in ["Non-physical", "Mixed", "Physical"]:
        for fb in ["low", "mid", "high"]:
            sub = occ[(occ["bucket"] == b) & (occ["friction_band"] == fb)]
            if sub.empty:
                continue
            summary_rows.append({
                "bucket": b, "friction_band": fb, "n_occs": len(sub),
                "median_pct": round(float(sub["pct"].median()), 2),
                "mean_pct": round(float(sub["pct"].mean()), 2),
                "median_friction": round(float(sub["friction_load"].median()), 2),
            })
    save_csv(pd.DataFrame(summary_rows), results / "phys_info_frictions.csv")

    # Box plot — bucket × friction_band on y; groupings horizontally
    band_colors = {
        "low":  "#bdd7c4",   # light sage
        "mid":  "#6a9e8f",   # paper sage teal
        "high": "#2d5e54",   # deep sage
    }
    band_labels = {"low": "Low friction", "mid": "Mid friction", "high": "High friction"}

    fig = go.Figure()
    bucket_order = ["Non-physical", "Mixed", "Physical"]
    band_order = ["low", "mid", "high"]

    # Build x-positions: 3 buckets × 3 bands = 9 boxes, grouped
    x_positions = []
    for b in bucket_order:
        for fb in band_order:
            x_positions.append(f"{b}<br>{band_labels[fb]}")

    for i, b in enumerate(bucket_order):
        for j, fb in enumerate(band_order):
            sub = occ[(occ["bucket"] == b) & (occ["friction_band"] == fb)]
            if sub.empty:
                continue
            x_label = f"{b}<br>{band_labels[fb]}"
            fig.add_trace(go.Box(
                y=sub["pct"],
                x=[x_label] * len(sub),
                name=band_labels[fb],
                marker_color=band_colors[fb],
                line_color=band_colors[fb],
                fillcolor=band_colors[fb],
                opacity=0.75, boxmean=True,
                showlegend=(i == 0),
                legendgroup=fb,
                width=0.55,
            ))

    style_paper_figure(
        fig,
        "Frictions Discriminate Within Non-Physical Work",
        subtitle=(
            "Each bucket split into low/mid/high friction tertiles "
            "(mean of r, df, tf within bucket) | "
            f"% tasks affected per occupation | {CONFIG_SUBTITLE}"
        ),
        height=680, width=PAPER_W,
        margin=dict(l=70, r=80, t=110, b=130),
    )
    fig.update_xaxes(
        categoryorder="array", categoryarray=x_positions,
        showgrid=False, showline=True, linecolor=PAPER_PALETTE["grid"],
        tickfont=dict(size=11),
    )
    fig.update_yaxes(
        title=dict(text="% Tasks Affected", font=dict(size=LABEL_FS)),
        range=[0, 100], dtick=20,
        gridcolor=PAPER_PALETTE["grid"], showline=False,
        ticksuffix="%",
    )
    fig.update_layout(boxmode="group")

    save_figure(fig, results / "figures" / "phys_info_frictions.png", scale=2)
    _copy_fig(results, figures, "phys_info_frictions.png")
    print("  -> phys_info_frictions.png")


# ─────────────────────────────────────────────────────────────────────────
# Figure 7: Tacit knowledge × duration + AI-safe overlay
# ─────────────────────────────────────────────────────────────────────────

def build_tacit_duration_safe(results: Path, figures: Path) -> None:
    eco = _load_eco_props()
    occ = _occ_property_means(eco)
    pct = get_pct_tasks_affected(PRIMARY_DATASET)
    ska = pd.read_csv(SKA_GAPS_CSV)
    occ = occ.merge(ska[["title_current", "overall_gap", "overall_pct"]],
                    on="title_current", how="left")
    occ["pct"] = occ["title_current"].map(pct)
    occ = occ.dropna(subset=["e", "t", "overall_gap", "emp"])
    occ["emp"] = occ["emp"].fillna(0)

    # AI-safe definition: high friction + low suitability
    fric = occ[FRICTION_KEYS].mean(axis=1)
    suit = occ[SUITABILITY_KEYS].mean(axis=1)
    occ["friction_load"] = fric
    occ["suitability"] = suit
    fric_thresh = fric.quantile(0.75)
    suit_thresh = suit.quantile(0.25)
    occ["ai_safe"] = (fric >= fric_thresh) & (suit <= suit_thresh)

    # Employment quartiles
    occ_with_emp = occ[occ["emp"] > 0].copy()
    occ_with_emp["emp_quartile"] = pd.qcut(
        occ_with_emp["emp"], q=4, labels=["Q1 (smallest)", "Q2", "Q3", "Q4 (largest)"],
    )
    quartile_means = (
        occ_with_emp.groupby("emp_quartile", observed=True)["e"]
        .agg(["mean", "median", "size"])
        .reset_index()
        .rename(columns={"mean": "mean_e", "median": "median_e", "size": "n_occs"})
    )
    save_csv(quartile_means, results / "tacit_by_employment.csv", float_format="%.3f")
    save_csv(
        occ[["title_current", "major_occ_category", "emp", "e", "t",
             "friction_load", "suitability", "overall_gap", "ai_safe", "pct"]],
        results / "tacit_duration_scatter.csv", float_format="%.3f",
    )

    # ── Two-panel layout: scatter (left, wide) + bar (right) ────────────
    fig = make_subplots(
        rows=1, cols=2, column_widths=[0.68, 0.32],
        subplot_titles=[
            "Tacit Knowledge × Duration (per occupation)",
            "Mean Tacit Knowledge by Employment Quartile",
        ],
        horizontal_spacing=0.16,
    )

    sizeref = 2.0 * occ["emp"].max() / (50 ** 2)

    # Left scatter — color by overall_gap (continuous)
    abs_max = float(np.nanpercentile(np.abs(occ["overall_gap"]), 95))
    fig.add_trace(go.Scatter(
        x=occ["t"], y=occ["e"], mode="markers",
        marker=dict(
            size=occ["emp"], sizemode="area", sizeref=sizeref, sizemin=4,
            color=occ["overall_gap"],
            colorscale=[
                [0, METRIC_COLORS["workers"]],   # green/teal — human advantage
                [0.5, "#f0e6d3"],                # neutral
                [1, METRIC_COLORS["wages"]],     # tan/orange — AI advantage
            ],
            cmin=-abs_max, cmax=abs_max,
            opacity=0.72, line=dict(width=0.5, color="#ffffff"),
            colorbar=dict(
                title=dict(text="SKA gap<br>(−) human / AI (+)",
                           side="top", font=dict(size=ANNOT_FS)),
                tickfont=dict(size=ANNOT_FS),
                len=0.45, thickness=10,
                x=0.555, xanchor="left", y=0.45,
            ),
        ),
        text=occ["title_current"], showlegend=False,
        customdata=np.stack([occ["emp"], occ["overall_gap"], occ["pct"].fillna(0)], axis=-1),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "t (duration)=%{x:.2f} | e (tacit)=%{y:.2f}"
            "<br>employment=%{customdata[0]:,.0f}"
            "<br>SKA gap=%{customdata[1]:.1f}"
            "<br>%% tasks affected=%{customdata[2]:.1f}%<extra></extra>"
        ),
    ), row=1, col=1)

    # Annotate top-5 AI-safe occs
    safe_top = occ[occ["ai_safe"]].nlargest(5, "emp")
    for _, r in safe_top.iterrows():
        fig.add_annotation(
            x=r["t"], y=r["e"], xref="x1", yref="y1",
            text=f"<b>{str(r['title_current'])[:32]}</b>",
            showarrow=True, arrowhead=2, ax=20, ay=-22,
            font=dict(size=10, color=METRIC_COLORS["workers"], family=FONT_FAMILY),
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor=METRIC_COLORS["workers"], borderwidth=1, borderpad=2,
        )

    # Right bar — mean(e) by employment quartile
    quartile_colors = ["#bdd7c4", "#8fbeae", "#6a9e8f", "#3e7869"]
    fig.add_trace(go.Bar(
        x=quartile_means["emp_quartile"].astype(str),
        y=quartile_means["mean_e"],
        marker=dict(color=quartile_colors[:len(quartile_means)], line=dict(width=0)),
        text=[f"{v:.2f}" for v in quartile_means["mean_e"]],
        textposition="outside",
        textfont=dict(size=12, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showlegend=False,
        cliponaxis=False,
        hovertemplate="%{x}<br>mean e: %{y:.2f}<extra></extra>",
    ), row=1, col=2)

    fig.update_xaxes(
        title=dict(text="t  (mean per-instance task duration)", font=dict(size=LABEL_FS)),
        gridcolor=PAPER_PALETTE["grid"], row=1, col=1,
    )
    fig.update_yaxes(
        title=dict(text="e  (mean tacit-knowledge requirement)", font=dict(size=LABEL_FS)),
        gridcolor=PAPER_PALETTE["grid"], row=1, col=1,
    )
    fig.update_xaxes(
        title=dict(text="Employment Quartile", font=dict(size=LABEL_FS)),
        showgrid=False, row=1, col=2, tickfont=dict(size=11),
    )
    fig.update_yaxes(
        title=dict(text="Mean e", font=dict(size=LABEL_FS)),
        gridcolor=PAPER_PALETTE["grid"], row=1, col=2,
        range=[0, max(quartile_means["mean_e"]) * 1.20],
    )

    style_paper_figure(
        fig,
        "Where Humans Still Lead — Tacit Knowledge and Long-Duration Tasks",
        subtitle=(
            "Left: occupations on (mean t, mean e); color = SKA gap, size = employment; "
            "AI-safe occs (high friction + low suitability) annotated. "
            "Right: mean(e) by employment quartile. | "
            + CONFIG_SUBTITLE
        ),
        height=780, width=PAPER_W,
        margin=dict(l=70, r=80, t=170, b=110),
    )

    # Style subplot titles + push them down so they don't collide with main title
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text and (
            ann.text.startswith("Tacit Knowledge ×")
            or ann.text.startswith("Mean Tacit Knowledge by")
        ):
            ann.font = dict(size=LABEL_FS, family=FONT_FAMILY,
                            color=PAPER_PALETTE["text"])
            ann.y = 1.02
            ann.yanchor = "bottom"

    save_figure(fig, results / "figures" / "tacit_duration_safe.png", scale=2)
    _copy_fig(results, figures, "tacit_duration_safe.png")
    print("  -> tacit_duration_safe.png")


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

    print("\n[0/8] Property biplot (PCA framing)")
    build_property_biplot(results, figures)

    print("\n[1/8] Tech commodities composite")
    build_tech_commodities(results, figures)

    print("\n[2/8] Conversational vs. agentic")
    build_conv_vs_agentic(results, figures)

    print("\n[3/8] Gap to ceiling")
    build_gap_to_ceiling(results, figures)

    print("\n[4/8] Risk × Recovery (a) — 8-flag risk × SKA gap")
    build_risk_x_ska(results, figures)

    print("\n[5/8] Risk × Recovery (b) — pct × (nt + de)")
    build_pct_x_nt_de(results, figures)

    print("\n[6/8] Phys/info with frictions inside")
    build_phys_info_frictions(results, figures)

    print("\n[7/8] Tacit knowledge × duration + employment quartile")
    build_tacit_duration_safe(results, figures)

    print("\n" + "=" * 64)
    print("Part 3 complete — figures in results/figures/ and figures/")
    print("=" * 64)


if __name__ == "__main__":
    main()
