"""Appendix figures.

Two charts produced fresh by this run.py (no copying from elsewhere):

1. phys_zone_faceted — three panels (Physical | Mixed | Non-physical) of
   job zone violins, with per-row (job zone) and per-column (phys group)
   median + n labels in addition to per-cell annotations.

2. ska_full — element-level SKA chart for skills, abilities, knowledge,
   with the full ladder of workforce references (mean, P95, top-10). The
   Part 2 chart trims this down for readability in the main text; the
   appendix preserves the full version with abilities included at the
   element level.

Run from project root:
    venv/Scripts/python -m analysis.exploratory.paperinfra_appendix.run
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
from analysis.data.compute_ska import load_ska_data
from analysis.utils import FONT_FAMILY, save_figure, save_csv
from analysis.paper.paper_config import (
    PAPER_W, PAPER_H,
    TITLE_FS, SUBTITLE_FS, LABEL_FS, TICK_FS, ANNOT_FS, LEGEND_FS,
    INSIDE_FS,
    METRIC_COLORS, PAPER_PALETTE,
    fmt_workers, fmt_wages,
    style_paper_figure,
)

# Match paper part_1 ordering (top → bottom in chart = first → last here)
OVERVIEW_CONFIG_ORDER: list[str] = [
    "all_confirmed",
    "human_conversation",
    "agentic_confirmed",
    "agentic_ceiling",
    "all_ceiling",
]

HERE = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

PRIMARY_KEY = "all_confirmed"
PRIMARY_DATASET = ANALYSIS_CONFIGS[PRIMARY_KEY]

PHYS_LOWER = 33.0
PHYS_UPPER = 67.0

# Order panels Physical → Mixed → Non-physical
OCC_GROUPS = ["Physical", "Mixed", "Non-physical"]
GROUP_COLORS = {
    "Non-physical": METRIC_COLORS["tasks"],
    "Mixed":        METRIC_COLORS["workers"],
    "Physical":     METRIC_COLORS["wages"],
}

ZONE_LABELS = {
    1: "Zone 1 — Little/No Prep",
    2: "Zone 2 — Some Prep",
    3: "Zone 3 — Medium Prep",
    4: "Zone 4 — Considerable Prep",
    5: "Zone 5 — Extensive Prep",
}
ZONE_COLORS = {
    1: "#b8cfe0", 2: "#8cafc5", 3: "#6090aa",
    4: "#3a6f8f", 5: "#1a4f73",
}

IMPORTANCE_THRESHOLD = 3.0
TOP_N_FOR_AVERAGE = 10


def _copy_fig(results: Path, figures: Path, name: str) -> None:
    shutil.copy(results / "figures" / name, figures / name)


def _load_occ_structural() -> pd.DataFrame:
    """Per-occ pct_physical, computed over UNIQUE (occ, task) pairs.
    See ANALYSIS_ARCHITECTURE.md Common Pitfalls — eco_2025 expands tasks
    across GWA/IWA/DWA non-proportionally between physical and non-physical
    tasks, so dedup is required before counting."""
    eco = pd.read_csv(DATA_DIR / "final_eco_2025.csv")
    eco_unique = eco.drop_duplicates(["title_current", "task_normalized"])
    occ = (
        eco_unique.groupby("title_current")
        .agg(
            n_tasks=("physical", "count"),
            n_physical=("physical", "sum"),
            job_zone=("job_zone", "first"),
        )
        .reset_index()
    )
    occ["pct_physical"] = occ["n_physical"] / occ["n_tasks"] * 100
    occ["occ_group"] = "Mixed"
    occ.loc[occ["pct_physical"] < PHYS_LOWER, "occ_group"] = "Non-physical"
    occ.loc[occ["pct_physical"] > PHYS_UPPER, "occ_group"] = "Physical"
    return occ


def _occ_with_pct() -> pd.DataFrame:
    occ = _load_occ_structural()
    pct = get_pct_tasks_affected(PRIMARY_DATASET)
    occ["pct_tasks_affected"] = occ["title_current"].map(pct)
    occ = occ.dropna(subset=["pct_tasks_affected", "job_zone"])
    occ["job_zone"] = occ["job_zone"].astype(int)
    return occ


# ──────────────────────────────────────────────────────────────────────────
# Chart 1: phys_zone_faceted (modified)
# ──────────────────────────────────────────────────────────────────────────

def build_phys_zone_faceted(results: Path, figures: Path) -> None:
    occ = _occ_with_pct()
    zones = sorted(occ["job_zone"].unique())

    rows_csv = []
    for grp in OCC_GROUPS:
        for z in zones:
            sub = occ[(occ["occ_group"] == grp) & (occ["job_zone"] == z)]
            rows_csv.append({
                "occ_group": grp,
                "job_zone": z,
                "n_occs": len(sub),
                "median_pct": (round(float(sub["pct_tasks_affected"].median()), 1)
                               if len(sub) else None),
                "mean_pct": (round(float(sub["pct_tasks_affected"].mean()), 1)
                             if len(sub) else None),
            })
    save_csv(pd.DataFrame(rows_csv), results / "phys_zone_crosstab.csv")

    # Panel titles include column-level (group) n + median across all zones
    panel_titles: list[str] = []
    for grp in OCC_GROUPS:
        sub = occ[occ["occ_group"] == grp]
        med = sub["pct_tasks_affected"].median()
        panel_titles.append(
            f"{grp}<br><sub>n={len(sub)} · median {med:.0f}%</sub>"
        )

    fig = make_subplots(
        rows=1, cols=3,
        shared_yaxes=True,
        horizontal_spacing=0.05,
        subplot_titles=panel_titles,
    )

    y_labels = [f"Zone {z}" for z in zones]

    for col_idx, grp in enumerate(OCC_GROUPS, start=1):
        grp_df = occ[occ["occ_group"] == grp]
        for z in zones:
            sub = grp_df[grp_df["job_zone"] == z]
            label = f"Zone {z}"
            if len(sub) == 0:
                fig.add_trace(go.Scatter(
                    x=[None], y=[label],
                    mode="markers",
                    marker=dict(opacity=0),
                    showlegend=False, hoverinfo="skip",
                ), row=1, col=col_idx)
                continue
            fig.add_trace(go.Violin(
                x=sub["pct_tasks_affected"],
                y=[label] * len(sub),
                marker_color=ZONE_COLORS[z],
                line_color=ZONE_COLORS[z],
                fillcolor=ZONE_COLORS[z],
                opacity=0.7,
                box_visible=True,
                meanline_visible=True,
                orientation="h",
                side="positive",
                width=0.9,
                points=False,
                showlegend=False,
                name=f"{grp} — {label}",
                hovertemplate=f"{grp}, {label}<br>%{{x:.1f}}%<extra></extra>",
            ), row=1, col=col_idx)

        # Per-cell n + median annotation, parked at far left of each panel
        # (avoids overlapping the density tails which sit on the right).
        for z in zones:
            sub = grp_df[grp_df["job_zone"] == z]
            if len(sub) == 0:
                txt = "n=0"
            else:
                med = sub["pct_tasks_affected"].median()
                txt = f"n={len(sub)} · med {med:.0f}%"
            fig.add_annotation(
                x=2, y=f"Zone {z}",
                xref=f"x{'' if col_idx == 1 else col_idx}",
                yref=f"y{'' if col_idx == 1 else col_idx}",
                text=txt,
                showarrow=False,
                xanchor="left", yanchor="middle",
                font=dict(size=ANNOT_FS - 2,
                          color=PAPER_PALETTE["neutral"],
                          family=FONT_FAMILY),
                bgcolor="rgba(255,255,255,0.85)",
            )

    y_order = [f"Zone {z}" for z in reversed(zones)]
    for col_idx in range(1, 4):
        fig.update_yaxes(
            categoryorder="array",
            categoryarray=y_order,
            showgrid=False, showline=False,
            tickfont=dict(size=TICK_FS - 1, family=FONT_FAMILY),
            row=1, col=col_idx,
        )
        fig.update_xaxes(
            range=[0, 100], dtick=20,
            showgrid=True, gridcolor=PAPER_PALETTE["grid"],
            showline=True, linecolor=PAPER_PALETTE["grid"],
            row=1, col=col_idx,
        )
        if col_idx == 2:
            fig.update_xaxes(
                title=dict(text="% Tasks Affected", font=dict(size=LABEL_FS)),
                row=1, col=col_idx,
            )

    # Per-row (zone) summary label, anchored beside the y-axis on the left.
    # Pooled across all three panels.
    for z in zones:
        sub = occ[occ["job_zone"] == z]
        med = sub["pct_tasks_affected"].median()
        fig.add_annotation(
            x=-0.025, y=f"Zone {z}",
            xref="paper",
            yref="y",
            text=f"<b>n={len(sub)}</b><br>med {med:.0f}%",
            showarrow=False,
            xanchor="right", yanchor="middle", align="right",
            font=dict(size=ANNOT_FS - 1,
                      color=PAPER_PALETTE["neutral"],
                      family=FONT_FAMILY),
        )

    style_paper_figure(
        fig,
        "AI Exposure by Physical Mix × Preparation Level",
        subtitle=f"Job zone violins within each occupation group ({len(occ)} occupations)",
        height=720,
        width=PAPER_W + 80,
        margin=dict(l=160, r=60, t=140, b=80),
    )

    # Style the panel titles (kept smaller because they wrap)
    panel_title_set = set(panel_titles)
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in panel_title_set:
            ann.font = dict(size=LABEL_FS - 1, family=FONT_FAMILY,
                            color=PAPER_PALETTE["text"])

    save_figure(fig, results / "figures" / "phys_zone_faceted.png", scale=2)
    _copy_fig(results, figures, "phys_zone_faceted.png")
    print("  -> phys_zone_faceted.png")


# ──────────────────────────────────────────────────────────────────────────
# Chart 2: ska_full — original element-level SKA with full workforce ladder
# ──────────────────────────────────────────────────────────────────────────

def _compute_ska_variants(
    onet_df: pd.DataFrame,
    pct_series: pd.Series,
    type_name: str,
) -> pd.DataFrame:
    df = onet_df.copy()
    df["pct"] = df["title"].map(pct_series)
    df = df.dropna(subset=["pct", "importance", "level"])
    df = df[df["importance"] >= IMPORTANCE_THRESHOLD].copy()
    assert len(df) > 0, f"No {type_name} rows after importance filter"

    df["occ_score"] = df["importance"] * df["level"]
    df["ai_product"] = (df["pct"] / 100.0) * df["occ_score"]

    records: list[dict] = []
    for element_name, grp in df.groupby("element_name"):
        ai_vals = grp["ai_product"].dropna()
        occ_vals = grp["occ_score"].dropna()
        n_ai = len(ai_vals)
        n_occ = len(occ_vals)
        top_n_ai = min(TOP_N_FOR_AVERAGE, n_ai)
        top_n_occ = min(TOP_N_FOR_AVERAGE, n_occ)
        records.append({
            "element_name": element_name,
            "type": type_name,
            "n_occs": n_ai,
            "ai_95th":  float(ai_vals.quantile(0.95)) if n_ai >= 2 else (
                        float(ai_vals.iloc[0]) if n_ai == 1 else float("nan")),
            "ai_max":   float(ai_vals.max()) if n_ai >= 1 else float("nan"),
            "ai_top10": float(ai_vals.nlargest(top_n_ai).mean()) if n_ai >= 1 else float("nan"),
            "eco_max":  float(occ_vals.max()) if n_occ >= 1 else float("nan"),
            "eco_p95":  float(occ_vals.quantile(0.95)) if n_occ >= 2 else (
                        float(occ_vals.iloc[0]) if n_occ == 1 else float("nan")),
            "eco_top10": float(occ_vals.nlargest(top_n_occ).mean()) if n_occ >= 1 else float("nan"),
            "eco_mean": float(occ_vals.mean()) if n_occ >= 1 else float("nan"),
        })
    return pd.DataFrame(records)


def build_ska_full(results: Path, figures: Path) -> None:
    pct = get_pct_tasks_affected(PRIMARY_DATASET)
    ska_data = load_ska_data()

    elements_by_type: dict[str, pd.DataFrame] = {}
    for type_name, onet_df in [
        ("skills", ska_data.skills),
        ("knowledge", ska_data.knowledge),
        ("abilities", ska_data.abilities),
    ]:
        df = _compute_ska_variants(onet_df, pct, type_name)
        elements_by_type[type_name] = df
        print(f"    {type_name}: {len(df)} elements")

    save_csv(
        pd.concat(elements_by_type.values(), ignore_index=True),
        results / "ska_full.csv", float_format="%.4f",
    )

    TYPES = ["skills", "knowledge", "abilities"]
    TYPE_LABELS = {"skills": "Skills", "knowledge": "Knowledge", "abilities": "Abilities"}
    counts = {t: len(elements_by_type[t]) for t in TYPES}
    total_elems = sum(counts.values())
    row_heights = [counts[t] / total_elems for t in TYPES]
    fig_height = max(1800, total_elems * 22 + 380)

    fig = make_subplots(
        rows=3, cols=1,
        row_heights=row_heights,
        vertical_spacing=0.05,
        subplot_titles=[f"{TYPE_LABELS[t]}  ({counts[t]} elements)" for t in TYPES],
    )

    legend_shown: set[str] = set()

    def _show(key: str) -> bool:
        if key not in legend_shown:
            legend_shown.add(key)
            return True
        return False

    ai_marker_color = METRIC_COLORS["workers"]

    for row, type_name in enumerate(TYPES, start=1):
        df = elements_by_type[type_name].copy()
        df["sort_pct"] = df["ai_max"] / df["eco_max"].replace(0, float("nan")) * 100
        df = df.sort_values("sort_pct", ascending=False)

        enames = df["element_name"].tolist()
        ai_vals = df["ai_max"].fillna(0).tolist()
        ai_p95_vals = df["ai_95th"].fillna(0).tolist()
        ai_top10_vals = df["ai_top10"].fillna(0).tolist()
        emax_vals = df["eco_max"].fillna(0).tolist()
        ep95_vals = df["eco_p95"].fillna(0).tolist()
        etop10_vals = df["eco_top10"].fillna(0).tolist()
        emean_vals = df["eco_mean"].fillna(0).tolist()

        max_eco = max(emax_vals) if emax_vals else 1.0
        label_x = max_eco * 1.07
        x_range_max = max_eco * 1.20

        pct_labels = [
            f"{a / m * 100:.0f}%" if m > 0 else "-"
            for a, m in zip(ai_vals, emax_vals)
        ]

        fig.add_trace(go.Bar(
            y=enames, x=emax_vals, orientation="h",
            name="Workforce Max",
            marker=dict(color="#e8e8e2", line=dict(width=0)),
            showlegend=_show("emax"),
            hovertemplate="Max (workforce): %{x:.1f}<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Bar(
            y=enames, x=ai_vals, orientation="h",
            name="AI Maximum",
            marker=dict(color=METRIC_COLORS["tasks"], opacity=0.88, line=dict(width=0)),
            showlegend=_show("ai_max"),
            hovertemplate="AI Maximum: %{x:.1f}<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scatter(
            y=enames, x=ai_p95_vals, mode="markers",
            name="AI P95",
            marker=dict(color=ai_marker_color, symbol="circle", size=8,
                        line=dict(width=1.5, color=ai_marker_color)),
            showlegend=_show("ai_p95"),
            hovertemplate="AI P95: %{x:.1f}<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scatter(
            y=enames, x=ai_top10_vals, mode="markers",
            name="AI Top-10 Avg",
            marker=dict(color=ai_marker_color, symbol="diamond", size=8,
                        line=dict(width=1.5, color=ai_marker_color)),
            showlegend=_show("ai_top10"),
            hovertemplate="AI Top-10 avg: %{x:.1f}<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scatter(
            y=enames, x=ep95_vals, mode="markers",
            name="Workforce P95",
            marker=dict(color="#1a1a1a", symbol="line-ew", size=14,
                        line=dict(width=3, color="#1a1a1a")),
            showlegend=_show("ep95"),
            hovertemplate="Workforce P95: %{x:.1f}<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scatter(
            y=enames, x=etop10_vals, mode="markers",
            name="Workforce Top-10 Avg",
            marker=dict(color="#1a1a1a", symbol="diamond", size=7,
                        line=dict(width=1, color="#1a1a1a")),
            showlegend=_show("etop10"),
            hovertemplate="Workforce Top-10 avg: %{x:.1f}<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scatter(
            y=enames, x=emean_vals, mode="markers",
            name="Workforce Mean",
            marker=dict(color="#1a1a1a", symbol="circle", size=7,
                        line=dict(width=1, color="#1a1a1a")),
            showlegend=_show("emean"),
            hovertemplate="Workforce mean: %{x:.1f}<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scatter(
            y=enames, x=[label_x] * len(enames), mode="text",
            text=pct_labels, textposition="middle right",
            textfont=dict(size=10, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
            showlegend=False, hoverinfo="skip",
        ), row=row, col=1)

        fig.update_yaxes(
            autorange="reversed", row=row, col=1,
            tickfont=dict(size=11, color=PAPER_PALETTE["text"], family=FONT_FAMILY),
            showgrid=False, showline=False,
        )
        fig.update_xaxes(
            range=[0, x_range_max],
            showgrid=True, gridcolor=PAPER_PALETTE["grid"],
            showticklabels=True,
            tickfont=dict(size=10, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
            showline=False, zeroline=True, zerolinecolor=PAPER_PALETTE["grid"],
            row=row, col=1,
        )

    fig.update_layout(
        title=dict(
            text=(
                "AI Capability vs. Workforce Requirements — Full SKA element view"
                f"<br><span style='font-size:{SUBTITLE_FS}px;"
                f"color:{PAPER_PALETTE['muted']}'>"
                "Bar = AI Maximum, faint background = workforce max | "
                "Teal markers = AI P95 + Top-10 | Black markers = workforce P95 + Top-10 + Mean"
                "</span>"
            ),
            font=dict(size=TITLE_FS, color=PAPER_PALETTE["text"], family=FONT_FAMILY),
            x=0.01, xanchor="left",
        ),
        height=fig_height,
        width=PAPER_W,
        font=dict(family=FONT_FAMILY, size=11, color=PAPER_PALETTE["text"]),
        plot_bgcolor=PAPER_PALETTE["surface"],
        paper_bgcolor=PAPER_PALETTE["surface"],
        barmode="overlay",
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.03, xanchor="center", x=0.5,
            font=dict(size=LEGEND_FS, color=PAPER_PALETTE["neutral"]),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
        ),
        margin=dict(l=270, r=80, t=120, b=100),
    )

    type_label_set = {f"{TYPE_LABELS[t]}  ({counts[t]} elements)" for t in TYPES}
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in type_label_set:
            ann.font = dict(size=LABEL_FS, family=FONT_FAMILY, color=PAPER_PALETTE["text"])

    save_figure(fig, results / "figures" / "ska_full.png", scale=2)
    _copy_fig(results, figures, "ska_full.png")
    print("  -> ska_full.png")


# ──────────────────────────────────────────────────────────────────────────
# Chart 3: nonphys_gwa_diff_phys_excluded
# Within non-physical occupations, what kinds of work separate the more-
# from the less-exposed — restricted to non-physical tasks on both sides
# so the GWA composition signal can't be a phys-residual proxy.
# ──────────────────────────────────────────────────────────────────────────

PHYS_NONPHYS_THRESHOLD = 33.0
TOP_DIFF_N = 12
COLOR_HIGH_EXP = METRIC_COLORS["tasks"]
COLOR_LOW_EXP = METRIC_COLORS["workers"]


def _split_top_bottom_nonphys(pct_series: pd.Series) -> tuple[list[str], list[str]]:
    q1 = pct_series.quantile(0.25)
    q3 = pct_series.quantile(0.75)
    top = sorted(pct_series[pct_series >= q3].index.tolist())
    bot = sorted(pct_series[pct_series <= q1].index.tolist())
    return top, bot


def build_nonphys_gwa_diff_phys_excluded(
    results: Path, figures: Path,
) -> None:
    eco = pd.read_csv(DATA_DIR / "final_eco_2025.csv")
    occ = _load_occ_structural()

    # Non-physical occupation set (pct_physical < 33%)
    nonphys_titles = set(
        occ.loc[occ["pct_physical"] < PHYS_NONPHYS_THRESHOLD, "title_current"]
    )

    # Quartile split on All Confirmed pct_tasks_affected, restricted to non-phys
    pct = get_pct_tasks_affected(PRIMARY_DATASET)
    pct_nonphys = pct.loc[pct.index.isin(nonphys_titles)].dropna()
    top_occs, bot_occs = _split_top_bottom_nonphys(pct_nonphys)
    n_top, n_bot = len(top_occs), len(bot_occs)

    # Drop physical tasks, recompute per-occ GWA shares
    eco_nonphys = eco[eco["physical"] != 1]
    sub = eco_nonphys.drop_duplicates(
        ["title_current", "task_normalized", "gwa_title"]
    )
    counts = (sub.groupby(["title_current", "gwa_title"]).size()
              .rename("n").reset_index())
    totals = counts.groupby("title_current")["n"].sum().rename("total")
    counts = counts.join(totals, on="title_current")
    counts["share"] = counts["n"] / counts["total"]
    wide = counts.pivot(index="title_current", columns="gwa_title",
                        values="share").fillna(0.0)

    top_mean = wide.loc[wide.index.isin(top_occs)].mean(axis=0)
    bot_mean = wide.loc[wide.index.isin(bot_occs)].mean(axis=0)
    diff = pd.DataFrame({
        "top_mean": top_mean,
        "bot_mean": bot_mean,
        "diff": top_mean - bot_mean,
    }).sort_values("diff", ascending=False)
    diff = diff[diff.index.astype(str).str.strip() != ""].dropna()

    save_csv(
        diff.reset_index().rename(columns={"index": "gwa_title"}),
        results / "nonphys_gwa_diff_phys_excluded.csv",
        float_format="%.4f",
    )

    pos = diff.head(TOP_DIFF_N).iloc[::-1]   # largest positive at top
    neg = diff.tail(TOP_DIFF_N)               # largest negative at bottom

    fig = make_subplots(
        rows=1, cols=2,
        horizontal_spacing=0.40,
        subplot_titles=(
            "<b>Over-represented in HIGH-exposure non-phys occs</b>",
            "<b>Over-represented in LOW-exposure non-phys occs</b>",
        ),
    )

    def _add_panel(side_df: pd.DataFrame, col_idx: int) -> None:
        labels = side_df.index.tolist()
        fig.add_trace(go.Bar(
            y=labels, x=side_df["top_mean"] * 100,
            orientation="h",
            name=f"Top quartile share (n={n_top})",
            marker=dict(color=COLOR_HIGH_EXP, line=dict(width=0)),
            text=[f"{v*100:.1f}%" for v in side_df["top_mean"]],
            textposition="outside",
            textfont=dict(size=ANNOT_FS, family=FONT_FAMILY),
            cliponaxis=False,
            showlegend=(col_idx == 1),
            hovertemplate="<b>%{y}</b><br>top share: %{x:.2f}%<extra></extra>",
        ), row=1, col=col_idx)
        fig.add_trace(go.Bar(
            y=labels, x=side_df["bot_mean"] * 100,
            orientation="h",
            name=f"Bottom quartile share (n={n_bot})",
            marker=dict(color=COLOR_LOW_EXP, line=dict(width=0)),
            text=[f"{v*100:.1f}%" for v in side_df["bot_mean"]],
            textposition="outside",
            textfont=dict(size=ANNOT_FS, family=FONT_FAMILY),
            cliponaxis=False,
            showlegend=(col_idx == 1),
            hovertemplate="<b>%{y}</b><br>bot share: %{x:.2f}%<extra></extra>",
        ), row=1, col=col_idx)

    _add_panel(pos, 1)
    _add_panel(neg, 2)

    # Panel-specific x-axis ranges so labels never clip
    pos_max = max(pos["top_mean"].max(), pos["bot_mean"].max()) * 100
    neg_max = max(neg["top_mean"].max(), neg["bot_mean"].max()) * 100
    fig.update_xaxes(
        title="Mean task-share within group (%) — non-physical tasks only",
        range=[0, pos_max * 1.18], row=1, col=1,
    )
    fig.update_xaxes(
        title="Mean task-share within group (%) — non-physical tasks only",
        range=[0, neg_max * 1.18], row=1, col=2,
    )
    fig.update_yaxes(
        tickfont=dict(size=TICK_FS - 1, family=FONT_FAMILY),
        automargin=True,
    )

    fig.update_layout(barmode="group", bargap=0.30, bargroupgap=0.10)

    style_paper_figure(
        fig,
        "Within non-physical occupations: GWA composition (physical tasks excluded)",
        subtitle=(
            "Per occupation, share of unique tasks in each GWA, computed over only the non-physical tasks of each occ. "
            f"Quartiles by All Confirmed % tasks affected, restricted to occs with pct_physical &lt; 33% (n top = {n_top}, bot = {n_bot})."
            f"<br>Top {TOP_DIFF_N} GWAs by absolute share gap on each side. "
            "Robustness test: if the same GWAs appear here as in the raw chart, the structural signal is not just a pct_physical residual."
        ),
        width=PAPER_W + 300,   # wider canvas so labels + leader text don't clip
        height=900,            # taller so x-axis title clears bottom margin
        margin=dict(l=20, r=40, t=160, b=170),
    )

    # Centered horizontal legend below the panels (default sits flush left)
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="top", y=-0.12,
        xanchor="center", x=0.5,
        font=dict(size=LEGEND_FS, family=FONT_FAMILY),
        bgcolor="rgba(0,0,0,0)",
    ))

    # Style panel subtitle annotations to match the paper aesthetic
    panel_titles = {
        "<b>Over-represented in HIGH-exposure non-phys occs</b>",
        "<b>Over-represented in LOW-exposure non-phys occs</b>",
    }
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in panel_titles:
            ann.font = dict(size=LABEL_FS, family=FONT_FAMILY,
                            color=PAPER_PALETTE["text"])

    save_figure(
        fig, results / "figures" / "nonphys_gwa_diff_phys_excluded.png",
        scale=2,
    )
    _copy_fig(results, figures, "nonphys_gwa_diff_phys_excluded.png")
    print("  -> nonphys_gwa_diff_phys_excluded.png")


# ──────────────────────────────────────────────────────────────────────────
# Chart 4: major_de_nt_plane
# Each major plotted on the demand-elasticity × new-task-creation plane.
# Dot size ~ workers affected; color ~ % tasks affected (All Confirmed).
# Labels positioned with collision-avoidance to stay readable.
# ──────────────────────────────────────────────────────────────────────────

def _major_pct_and_workers() -> pd.DataFrame:
    """Major-level pct_tasks_affected and workers_affected from All Confirmed."""
    from backend.compute import get_group_data
    rows = []
    for sort_by, val_col in [("% Tasks Affected", "pct_tasks_affected"),
                             ("Workers Affected", "workers_affected")]:
        data = get_group_data({
            "selected_datasets": [PRIMARY_DATASET],
            "combine_method": "Average", "method": "freq", "use_auto_aug": True,
            "physical_mode": "all", "geo": "nat", "agg_level": "major",
            "sort_by": sort_by, "top_n": 9999,
            "search_query": "", "context_size": 3,
        })
        df = data["df"].rename(columns={data["group_col"]: "major"})
        rows.append(df.set_index("major")[val_col])
    return pd.concat(rows, axis=1)


def build_major_de_nt_plane(results: Path, figures: Path) -> None:
    """Per-major mean of de and nt computed over the major's UNIQUE tasks
    (deduped on (major, task_normalized)). Color = % tasks affected; size =
    workers affected. Quadrant lines at medians."""
    eco = pd.read_csv(DATA_DIR / "final_eco_2025_with_task_properties.csv")
    sub = eco.drop_duplicates(["major_occ_category", "task_normalized"])
    means = sub.groupby("major_occ_category")[["de", "nt"]].mean()

    extras = _major_pct_and_workers()
    means = means.join(extras, how="left").dropna()
    means["short"] = means.index.str.replace(" Occupations", "", regex=False)

    save_csv(
        means.reset_index(), results / "major_de_nt_plane.csv",
        float_format="%.3f",
    )

    de_med = float(means["de"].median())
    nt_med = float(means["nt"].median())
    pct_min, pct_max = float(means["pct_tasks_affected"].min()), float(means["pct_tasks_affected"].max())

    # Hand-tuned label offsets per major. Each entry is (dx, dy) in axis units;
    # positive dx pushes label right, positive dy pushes label up. Designed so
    # the upper-right growth-quadrant cluster fans out radially with leader
    # lines. Anything not listed gets a neutral upward placement.
    # All offsets in axis units. Upper-right cluster is densely packed so
    # those labels get pushed quite far out with leader lines back to dots.
    # Per-major label offsets in axis units. Aggressive for the dense
    # upper-right cluster so leader lines fan out without overlapping.
    OFFSETS: dict[str, tuple[float, float]] = {
        # Right side of plot (E)
        "Community and Social Service":                      (0.07,  0.07),   # NE
        "Educational Instruction and Library":               (0.20, -0.05),   # E
        "Healthcare Practitioners and Technical":            (0.25, -0.16),   # ESE
        "Arts, Design, Entertainment, Sports, and Media":    (0.07, -0.25),   # SSE
        "Business and Financial Operations":                 (-0.10, -0.23),  # SSW
        # Left side of cluster (W)
        "Computer and Mathematical":                         (-0.40, -0.05),  # W
        "Life, Physical, and Social Science":                (-0.45, 0.04),   # W
        "Architecture and Engineering":                      (-0.30, 0.18),   # NW
        "Management":                                        (-0.05, 0.22),   # N
        # Middle band
        "Legal":                                             (-0.13, 0.08),
        "Protective Service":                                (0.07,  0.08),
        # Right-middle cluster
        "Sales and Related":                                 (0.17,  0.07),
        "Healthcare Support":                                (-0.08, -0.10),
        # Lower band
        "Office and Administrative Support":                 (0.25, -0.02),
        "Food Preparation and Serving Related":              (-0.07, -0.13),
        "Building and Grounds Cleaning and Maintenance":     (-0.22, -0.06),
        "Personal Care and Service":                         (0.13,  0.07),
        "Farming, Fishing, and Forestry":                    (0.00,  0.10),
        "Transportation and Material Moving":                (0.00, -0.12),
        "Installation, Maintenance, and Repair":             (0.16,  0.05),
        "Production":                                        (0.00, -0.12),
        "Construction and Extraction":                       (0.00,  0.10),
    }
    means["dx"] = means.index.map(lambda m: OFFSETS.get(m, (0.0, 0.05))[0])
    means["dy"] = means.index.map(lambda m: OFFSETS.get(m, (0.0, 0.05))[1])

    fig = go.Figure()

    # Build manual size scaling so the smallest dot is visible and the
    # largest is bounded; sqrt scaling on workers_affected.
    sizes = np.sqrt(means["workers_affected"].values) * 0.0018 + 18
    # Markers only — labels are added separately as annotations with leaders
    fig.add_trace(go.Scatter(
        x=means["de"], y=means["nt"], mode="markers",
        marker=dict(
            size=sizes,
            color=means["pct_tasks_affected"],
            colorscale=[[0, COLOR_LOW_EXP], [1, COLOR_HIGH_EXP]],
            cmin=pct_min, cmax=pct_max,
            colorbar=dict(
                title=dict(text="% tasks<br>affected",
                           font=dict(size=ANNOT_FS, family=FONT_FAMILY)),
                tickfont=dict(size=ANNOT_FS - 1, family=FONT_FAMILY),
                len=0.65, thickness=14,
                x=1.02, xanchor="left",
            ),
            line=dict(width=0.8, color="#2a2a2a"),
            opacity=0.92,
        ),
        text=means["short"],
        hovertemplate=(
            "<b>%{text}</b><br>de: %{x:.2f}<br>nt: %{y:.2f}<br>"
            "% tasks affected: %{marker.color:.1f}%<extra></extra>"
        ),
        cliponaxis=False, showlegend=False,
    ))

    # Per-major leader-line annotations. In plotly, when showarrow=True the
    # text is rendered at (x, y) and the arrow tail sits at (ax, ay). So the
    # OFFSET position goes in (x, y) and the dot position in (ax, ay).
    for major, row in means.iterrows():
        dx = float(row["dx"])
        dy = float(row["dy"])
        # Anchor the text on the side closer to the dot so the leader doesn't
        # cut through the label.
        if dx > 0.02:
            xa = "left"
        elif dx < -0.02:
            xa = "right"
        else:
            xa = "center"
        ya = "bottom" if dy > 0 else "top"
        show_arrow = abs(dx) > 0.02 or abs(dy) > 0.05
        fig.add_annotation(
            # text + arrowhead position (where the label is drawn)
            x=row["de"] + dx, y=row["nt"] + dy,
            # arrow tail position (the dot itself)
            ax=row["de"], ay=row["nt"],
            xref="x", yref="y", axref="x", ayref="y",
            text=row["short"],
            showarrow=show_arrow,
            arrowhead=0, arrowwidth=0.7, arrowcolor=PAPER_PALETTE["muted"],
            standoff=2, startstandoff=8,   # gap on both ends so leader is clean
            xanchor=xa, yanchor=ya,
            font=dict(size=ANNOT_FS + 1, family=FONT_FAMILY,
                      color=PAPER_PALETTE["text"]),
        )

    # Quadrant lines at medians
    fig.add_vline(x=de_med, line=dict(color=PAPER_PALETTE["muted"],
                                      width=1, dash="dash"))
    fig.add_hline(y=nt_med, line=dict(color=PAPER_PALETTE["muted"],
                                      width=1, dash="dash"))

    # Quadrant text annotations parked at corners with proper anchoring.
    # Padding chosen wide enough that leader-line labels in the upper-right
    # cluster have somewhere to go without leaving the plot.
    x_lo = float(means["de"].min()) - 0.20
    x_hi = float(means["de"].max()) + 0.30
    y_lo = float(means["nt"].min()) - 0.20
    y_hi = float(means["nt"].max()) + 0.30

    quadrant_annotations = [
        (x_hi, y_hi, "right", "top",
         "<b>HIGH de · HIGH nt</b><br>growth quadrant",
         PAPER_PALETTE["positive"]),
        (x_lo, y_lo, "left", "bottom",
         "<b>LOW de · LOW nt</b><br>least dynamic",
         PAPER_PALETTE["negative"]),
        (x_hi, y_lo, "right", "bottom",
         "HIGH de · LOW nt<br>cheaper, fewer new roles",
         PAPER_PALETTE["neutral"]),
        (x_lo, y_hi, "left", "top",
         "LOW de · HIGH nt<br>not cheaper, but new roles",
         PAPER_PALETTE["neutral"]),
    ]
    for x, y, xa, ya, text, color in quadrant_annotations:
        fig.add_annotation(
            x=x, y=y, text=text, showarrow=False,
            xanchor=xa, yanchor=ya,
            font=dict(size=ANNOT_FS + 1, family=FONT_FAMILY, color=color),
        )

    fig.update_xaxes(
        title="Mean demand elasticity (de) — task-level mean of LLM rating, 1-5",
        range=[x_lo, x_hi],
    )
    fig.update_yaxes(
        title="Mean new task creation (nt) — task-level mean of LLM rating, 1-5",
        range=[y_lo, y_hi],
    )

    style_paper_figure(
        fig,
        "Demand elasticity × new task creation by major occupational category",
        subtitle=(
            f"Per-major mean of LLM-rated task properties across the major's unique tasks (deduped on (major, task)). "
            f"Dot size ∝ √(workers affected, All Confirmed); color = major's % tasks affected. "
            f"<br>Dashed lines at the per-axis medians (de={de_med:.2f}, nt={nt_med:.2f}). "
            f"de = how much demand expands if the task gets cheaper; nt = whether automation generates new human roles. (Both 1-5.)"
        ),
        width=PAPER_W + 300,
        height=860,
        margin=dict(l=90, r=160, t=160, b=110),
    )

    save_figure(
        fig, results / "figures" / "major_de_nt_plane.png", scale=2,
    )
    _copy_fig(results, figures, "major_de_nt_plane.png")
    print("  -> major_de_nt_plane.png")


def build_convergence_full(results: Path, figures: Path) -> None:
    """Full square correlation matrix: every internal measure (4 AI sources +
    5 ANALYSIS_CONFIGS) and every external benchmark (8 academic indices)
    on both x and y axes, lower-triangular cells only. Two panels stacked
    vertically: Major SOC level (n ≈ 22) and Occupation level (n ≈ 900).

    A blank gap row + gap column separate the internal section from the
    external section on both axes. Cell rendering, gray-out, and the
    contamination legend follow the conventions of the main paper charts.
    """
    from scipy import stats
    from analysis.paper.results.part_1.run import (
        CORR_SOURCES, CORR_ORDER, CORR_LABELS,
        CONFIG_ORDER,
        EXT_SOURCES,
        ELOUNDOU_LABELS,
        CONTAMINATED_SOURCE_ROWS, CONTAMINATED_CONFIG_ROWS,
        SIG_NOTE,
        _run_config,
        _load_eloundou_occ, _compute_aioe_occ,
        _load_schaal_occ, _load_tomlinson_occ,
        _ext_at_level, _stars,
    )
    from analysis.paper.paper_config import (
        HEATMAP_TEXT_FS, HEATMAP_LOW, HEATMAP_HIGH,
    )

    from analysis.config import ANALYSIS_CONFIG_LABELS

    LEVELS = [("major", "Major level"), ("occupation", "Occ level")]

    # ── Internal measures ────────────────────────────────────────────
    internal_keys = list(CORR_ORDER) + list(CONFIG_ORDER)
    internal_labels = (list(CORR_LABELS)
                       + [ANALYSIS_CONFIG_LABELS[k] for k in CONFIG_ORDER])
    n_int = len(internal_keys)

    internal_data: dict[str, dict[str, pd.Series]] = {}
    for skey in CORR_ORDER:
        ds = CORR_SOURCES[skey]["dataset"]
        internal_data[skey] = {}
        for lvl, _ in LEVELS:
            df = _run_config(ds, lvl)
            internal_data[skey][lvl] = df.set_index("category")["pct_tasks_affected"]
        print(f"  {CORR_SOURCES[skey]['label']}: loaded {[l for l, _ in LEVELS]}")
    for ckey in CONFIG_ORDER:
        ds = ANALYSIS_CONFIGS[ckey]
        internal_data[ckey] = {}
        for lvl, _ in LEVELS:
            df = _run_config(ds, lvl)
            internal_data[ckey][lvl] = df.set_index("category")["pct_tasks_affected"]
        print(f"  {ANALYSIS_CONFIG_LABELS[ckey]}: loaded {[l for l, _ in LEVELS]}")

    # ── External measures ────────────────────────────────────────────
    eloundou = _load_eloundou_occ()
    aioe = _compute_aioe_occ()
    schaal = _load_schaal_occ()
    tomlinson = _load_tomlinson_occ()
    ext_df = (eloundou.merge(aioe,      on="title_current", how="outer")
                       .merge(schaal,    on="title_current", how="outer")
                       .merge(tomlinson, on="title_current", how="outer"))

    ext_keys = [k for k, _ in EXT_SOURCES]
    ext_labels = [lbl for _, lbl in EXT_SOURCES]
    n_ext = len(ext_keys)

    external_data: dict[str, dict[str, pd.Series]] = {}
    for ekey in ext_keys:
        external_data[ekey] = {}
        for lvl, _ in LEVELS:
            external_data[ekey][lvl] = _ext_at_level(ext_df, ekey, lvl)
    print(f"  External benchmarks: loaded {n_ext} columns × {len(LEVELS)} levels")

    # ── Layout: gap inserted between internal and external on each axis
    all_keys = internal_keys + ext_keys
    all_labels = internal_labels + ext_labels
    all_data = {**internal_data, **external_data}
    n_meas = n_int + n_ext           # 17

    GAP_LABEL = " "
    layout_labels = list(internal_labels) + [GAP_LABEL] + list(ext_labels)
    n_layout = len(layout_labels)    # 18
    EXT_OFFSET = n_int + 1

    def m2l(m_idx: int) -> int:
        """measure index → layout index (skipping the gap row/col at n_int)"""
        return m_idx if m_idx < n_int else m_idx + 1

    contaminated_internals = CONTAMINATED_SOURCE_ROWS | CONTAMINATED_CONFIG_ROWS

    # ── Compute lower-tri correlations ───────────────────────────────
    matrices: dict[str, np.ndarray] = {}
    pmatrices: dict[str, np.ndarray] = {}
    records: list[dict] = []

    for level, _ in LEVELS:
        mat = np.full((n_layout, n_layout), np.nan)
        pmat = np.full((n_layout, n_layout), np.nan)
        for i in range(n_meas):
            for j in range(i):
                key_i, key_j = all_keys[i], all_keys[j]
                si = all_data[key_i][level]
                sj = all_data[key_j][level]
                merged = pd.concat([si, sj], axis=1, join="inner").dropna()
                if len(merged) < 3:
                    continue
                rho, pval = stats.spearmanr(merged.iloc[:, 0], merged.iloc[:, 1])
                li, lj = m2l(i), m2l(j)
                mat[li, lj] = rho
                pmat[li, lj] = pval
                records.append({
                    "level": level,
                    "measure_a": all_labels[i],
                    "measure_b": all_labels[j],
                    "rho": round(float(rho), 3),
                    "p_value": round(float(pval), 6),
                    "n": len(merged),
                    "stars": _stars(pval),
                })
        matrices[level] = mat
        pmatrices[level] = pmat
        print(f"  {level}: {int(np.isfinite(mat).sum())} cells filled")

    save_csv(pd.DataFrame(records), results / "spearman_combined_full.csv")

    # ── Render: 2 panels stacked vertically ──────────────────────────
    all_vals = np.concatenate([m[~np.isnan(m)] for m in matrices.values()])
    z_min = float(np.floor(all_vals.min() * 20) / 20)
    z_max = 1.0

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=[title for _, title in LEVELS],
        vertical_spacing=0.10,
    )

    cell_fs = HEATMAP_TEXT_FS - 4   # 14pt — denser than the main charts
    contam_color = "rgba(200, 200, 200, 0.92)"
    contam_text  = "#777777"

    for idx, (level, _) in enumerate(LEVELS):
        row_pos = idx + 1
        mat = matrices[level]
        pmat = pmatrices[level]

        fig.add_trace(
            go.Heatmap(
                z=mat.tolist(),
                x=layout_labels,
                y=layout_labels,
                colorscale=[[0, HEATMAP_LOW], [1, HEATMAP_HIGH]],
                zmin=z_min, zmax=z_max,
                showscale=(idx == 0),
                hoverinfo="z",
                colorbar=dict(
                    title=dict(text="Spearman ρ",
                               font=dict(size=LABEL_FS, family=FONT_FAMILY)),
                    len=0.40, y=0.78,
                    tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
                ),
            ),
            row=row_pos, col=1,
        )

        x_axis = f"x{idx + 1}" if idx > 0 else "x"
        y_axis = f"y{idx + 1}" if idx > 0 else "y"

        # Cell annotations + contamination overlays
        for li in range(n_layout):
            for lj in range(n_layout):
                val = mat[li, lj]
                if np.isnan(val):
                    continue
                row_label = layout_labels[li]
                col_label = layout_labels[lj]
                # Eloundou × Copilot-containing on either axis is contaminated
                contam_pair = (
                    (row_label in ELOUNDOU_LABELS and col_label in contaminated_internals)
                    or (col_label in ELOUNDOU_LABELS and row_label in contaminated_internals)
                )
                if contam_pair:
                    fig.add_shape(
                        type="rect",
                        x0=lj - 0.5, x1=lj + 0.5,
                        y0=li - 0.5, y1=li + 0.5,
                        xref=x_axis, yref=y_axis,
                        fillcolor=contam_color,
                        line=dict(width=0),
                        layer="above",
                    )
                    txt_color = contam_text
                else:
                    norm = (val - z_min) / max(z_max - z_min, 1e-9)
                    txt_color = "white" if norm >= 0.55 else PAPER_PALETTE["text_dark"]
                fig.add_annotation(
                    x=col_label, y=row_label,
                    text=f"{val:.2f}",
                    showarrow=False,
                    font=dict(size=cell_fs, family=FONT_FAMILY, color=txt_color),
                    xref=x_axis, yref=y_axis,
                )

        # X-axis group headers (above each column block)
        internal_x_mid = (n_int - 1) / 2.0
        external_x_mid = EXT_OFFSET + (n_ext - 1) / 2.0
        for header_text, header_x in [("Internal", internal_x_mid),
                                       ("External", external_x_mid)]:
            fig.add_annotation(
                x=header_x, y=n_layout - 0.5,
                text=f"<b>{header_text}</b>",
                showarrow=False,
                xanchor="center", yanchor="bottom",
                yshift=14,
                font=dict(size=LABEL_FS + 1, family=FONT_FAMILY,
                          color=PAPER_PALETTE["text"]),
                xref=x_axis, yref=y_axis,
            )

        # Y-axis group headers (left of each row block, rotated). Plotly
        # heatmaps put the first y label at the bottom by default, so the
        # internal section is at the bottom and the external section at top.
        internal_y_mid = (n_int - 1) / 2.0
        external_y_mid = EXT_OFFSET + (n_ext - 1) / 2.0
        for header_text, header_y in [("Internal", internal_y_mid),
                                       ("External", external_y_mid)]:
            fig.add_annotation(
                x=0, y=header_y,
                text=f"<b>{header_text}</b>",
                showarrow=False,
                xanchor="right", yanchor="middle",
                xshift=-160,
                textangle=-90,
                font=dict(size=LABEL_FS + 1, family=FONT_FAMILY,
                          color=PAPER_PALETTE["text"]),
                xref=x_axis, yref=y_axis,
            )

        # Vertical + horizontal dividers between internal and external blocks
        fig.add_shape(
            type="line",
            x0=n_int, x1=n_int,
            y0=-0.5, y1=n_layout - 0.5,
            xref=x_axis, yref=y_axis,
            line=dict(color=PAPER_PALETTE["text"], width=2),
        )
        fig.add_shape(
            type="line",
            x0=-0.5, x1=n_layout - 0.5,
            y0=n_int, y1=n_int,
            xref=x_axis, yref=y_axis,
            line=dict(color=PAPER_PALETTE["text"], width=2),
        )

    # ── Figure-level styling ─────────────────────────────────────────
    fig_width = PAPER_W + 600          # ~2000 px wide
    fig_height = 1700                  # tall enough for 2 stacked dense panels

    style_paper_figure(
        fig,
        title=("Internal and External Benchmark Comparison — "
               "Full Matrix"),
        subtitle=("Spearman ρ across all internal sources, data "
                  f"configurations, and academic benchmarks. {SIG_NOTE}"),
        width=fig_width,
        height=fig_height,
        margin=dict(l=260, r=160, t=140, b=200),
    )

    # Bump subplot titles
    panel_title_set = {title for _, title in LEVELS}
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in panel_title_set:
            ann.font = dict(size=LABEL_FS + 3, family=FONT_FAMILY,
                            color=PAPER_PALETTE["text"])
            ann.yshift = 32

    # Tick fonts
    for i in range(1, 3):
        xkey = f"xaxis{i}" if i > 1 else "xaxis"
        ykey = f"yaxis{i}" if i > 1 else "yaxis"
        fig.layout[xkey].tickfont = dict(size=TICK_FS - 2, family=FONT_FAMILY)
        fig.layout[ykey].tickfont = dict(size=TICK_FS - 2, family=FONT_FAMILY)
        fig.layout[xkey].tickangle = -30

    # Contamination legend (bottom-left, paper coords, real swatch)
    sx0, sx1 = 0.085, 0.130
    sy0, sy1 = -0.090, -0.060
    fig.add_shape(
        type="rect",
        xref="paper", yref="paper",
        x0=sx0, x1=sx1, y0=sy0, y1=sy1,
        fillcolor=contam_color,
        line=dict(color=contam_text, width=1),
        layer="above",
    )
    fig.add_annotation(
        xref="paper", yref="paper",
        x=sx1 + 0.010, y=(sy0 + sy1) / 2,
        xanchor="left", yanchor="middle",
        text=("<b>Eloundou-contaminated cell</b> — Eloundou's task labels "
              "were used to filter Copilot tasks, so correlations between "
              "a Copilot-containing measure and an Eloundou benchmark "
              "double-count that signal. Values shown for transparency."),
        showarrow=False,
        font=dict(size=ANNOT_FS + 1, family=FONT_FAMILY,
                  color=PAPER_PALETTE["text"]),
    )

    save_figure(fig, results / "figures" / "convergence_full.png")
    _copy_fig(results, figures, "convergence_full.png")
    print("  -> convergence_full.png")


def _run_overview_config(dataset_name: str, use_auto_aug: bool) -> pd.DataFrame:
    from backend.compute import get_group_data
    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": use_auto_aug,
        "physical_mode": "all",
        "geo": "nat",
        "agg_level": "occupation",
        "sort_by": "% Tasks Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    assert data is not None, f"No data for {dataset_name}"
    df: pd.DataFrame = data["df"]
    group_col: str = data["group_col"]
    return df.rename(columns={group_col: "category"})


def _national_totals_emp_wages() -> tuple[float, float]:
    from backend.compute import load_eco_raw
    eco = load_eco_raw()
    occ = eco.drop_duplicates(subset=["title_current"])
    total_emp = float(occ["emp_tot_nat_2024"].sum())
    total_wages = float((occ["emp_tot_nat_2024"] * occ["a_med_nat_2024"]).sum())
    return total_emp, total_wages


def _compute_paper_overview_rows(total_emp: float, total_wages: float) -> list[dict]:
    """Reproduce the paper part_1 build_overview values (auto_aug=True, method=freq)
    so variant charts can show delta-vs-paper."""
    rows: list[dict] = []
    for key in OVERVIEW_CONFIG_ORDER:
        ds = ANALYSIS_CONFIGS[key]
        df = _run_overview_config(ds, use_auto_aug=True)
        workers = float(df["workers_affected"].sum())
        wages = float(df["wages_affected"].sum())
        pct_tasks = float(df["pct_tasks_affected"].mean())
        rows.append({
            "config": key,
            "pct_tasks": round(pct_tasks, 1),
            "pct_workers": round(workers / total_emp * 100, 1),
            "pct_wages": round(wages / total_wages * 100, 1),
        })
    return rows


def _render_overview_with_deltas(
    rows: list[dict],
    paper_rows: list[dict],
    title: str,
    subtitle: str,
    out_name: str,
    results: Path,
    figures: Path,
    x_range_max: float = 75.0,
) -> None:
    """Render the overview chart with delta-vs-paper annotated inside each bar
    AND a thin vertical marker on each bar at the paper chart's value (so the
    reader can see where the original landed without flipping back)."""
    paper_lookup = {p["config"]: p for p in paper_rows}

    fig = go.Figure()
    plot_rows = list(reversed(rows))
    labels = [r["label"] for r in plot_rows]

    metrics = [
        ("pct_tasks",   "Tasks Exposed",
         METRIC_COLORS["tasks"], "pct_tasks",
         lambda r, d: f"{r['pct_tasks']:.1f}%  Δ{d:+.1f}pp"),
        ("pct_workers", "Workers Exposed (% of National Employment)",
         METRIC_COLORS["workers"], "pct_workers",
         lambda r, d: f"{fmt_workers(r['workers'])} ({r['pct_workers']:.1f}%)  Δ{d:+.1f}pp"),
        ("pct_wages",   "Wages Exposed (% of National Wages)",
         METRIC_COLORS["wages"], "pct_wages",
         lambda r, d: f"{fmt_wages(r['wages'])} ({r['pct_wages']:.1f}%)  Δ{d:+.1f}pp"),
    ]

    for pct_key, name, color, paper_key, fmt_fn in reversed(metrics):
        texts = []
        for r in plot_rows:
            paper_val = paper_lookup[r["config"]][paper_key]
            delta = r[pct_key] - paper_val
            texts.append(fmt_fn(r, delta))
        fig.add_trace(go.Bar(
            y=labels,
            x=[r[pct_key] for r in plot_rows],
            name=name,
            orientation="h",
            marker=dict(color=color, line=dict(width=0)),
            text=texts,
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(size=INSIDE_FS - 4, color="white", family=FONT_FAMILY),
        ))

    # Vertical "where the paper chart landed" markers, one per bar in each cluster.
    # Grouped-bar y offsets: with 3 traces and bargap=0.30, each cluster spans
    # 0.70 in y units, with bargroupgap=0.06 between sub-bars. We compute the
    # exact center and height of each sub-bar so the tick fully covers it.
    n_per_cluster = 3
    bargap = 0.30
    bargroupgap = 0.06
    cluster_span = 1.0 - bargap                       # 0.70
    bar_pitch = cluster_span / n_per_cluster          # spacing between sub-bar centers (≈ 0.233)
    bar_height = bar_pitch * (1.0 - bargroupgap)      # actual sub-bar height (≈ 0.219)
    half_span = cluster_span / 2.0                    # 0.35
    # Plotly grouped bars order: trace 0 at the BOTTOM of the cluster.
    # Our metrics were added in reverse so wages=trace0, workers=trace1, tasks=trace2.
    sub_centers = {
        "pct_wages":   -half_span + 0.5 * bar_pitch,
        "pct_workers": -half_span + 1.5 * bar_pitch,
        "pct_tasks":   -half_span + 2.5 * bar_pitch,
    }
    shapes = []
    for y_idx, r in enumerate(plot_rows):
        paper_r = paper_lookup[r["config"]]
        for paper_key in ("pct_tasks", "pct_workers", "pct_wages"):
            xv = paper_r[paper_key]
            yc = y_idx + sub_centers[paper_key]
            shapes.append(dict(
                type="line",
                xref="x", yref="y",
                x0=xv, x1=xv,
                y0=yc - bar_height / 2.0,
                y1=yc + bar_height / 2.0,
                line=dict(color="rgba(20,20,20,0.95)", width=2),
                layer="above",
            ))

    # Legend-only entry explaining the black tick. Scatter with a vertical-line
    # marker so the legend swatch reads as a tick, not a horizontal line.
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode="markers",
        marker=dict(
            symbol="line-ns",
            color="rgba(20,20,20,0.95)",
            size=14,
            line=dict(color="rgba(20,20,20,0.95)", width=2),
        ),
        name="Paper-chart value (Δ baseline)",
        showlegend=True,
        hoverinfo="skip",
    ))

    fig.update_layout(
        barmode="group",
        bargap=0.30,
        bargroupgap=0.06,
        legend=dict(traceorder="reversed"),
        xaxis=dict(
            title=dict(text="% of National Total", font=dict(size=LABEL_FS)),
            range=[0, x_range_max],
            ticksuffix="%",
        ),
        yaxis=dict(
            title=dict(text="Data Configuration", font=dict(size=LABEL_FS)),
            tickfont=dict(size=LABEL_FS, family=FONT_FAMILY),
        ),
        shapes=shapes,
    )

    style_paper_figure(
        fig, title, subtitle=subtitle,
        height=PAPER_H + 140,
        margin=dict(l=20, r=60, t=140, b=110),
    )

    save_figure(fig, results / "figures" / out_name)
    _copy_fig(results, figures, out_name)
    print(f"  -> {out_name}")


def build_overview_no_autoaug(results: Path, figures: Path) -> None:
    """Variant of paper part_1 build_overview with auto_aug weighting off.
    Every affected task contributes its full freq weight regardless of its
    0–5 automatability rating. Same five configs, same layout. Each bar
    carries the delta-vs-paper-chart in percentage points (and a small
    black tick on the bar at the paper chart's value)."""
    total_emp, total_wages = _national_totals_emp_wages()
    paper_rows = _compute_paper_overview_rows(total_emp, total_wages)

    rows: list[dict] = []
    for key in OVERVIEW_CONFIG_ORDER:
        ds = ANALYSIS_CONFIGS[key]
        label = ANALYSIS_CONFIG_LABELS[key]
        df = _run_overview_config(ds, use_auto_aug=False)

        workers = float(df["workers_affected"].sum())
        wages = float(df["wages_affected"].sum())
        pct_tasks = float(df["pct_tasks_affected"].mean())
        pct_workers = workers / total_emp * 100
        pct_wages = wages / total_wages * 100

        rows.append({
            "config": key, "label": label,
            "pct_tasks": round(pct_tasks, 1),
            "pct_workers": round(pct_workers, 1),
            "pct_wages": round(pct_wages, 1),
            "workers": workers, "wages": wages,
        })
        print(f"  {label}: {pct_tasks:.1f}% tasks, "
              f"{fmt_workers(workers)} ({pct_workers:.1f}%), "
              f"{fmt_wages(wages)} ({pct_wages:.1f}%)")

    save_csv(pd.DataFrame(rows), results / "overview_no_autoaug_totals.csv")

    _render_overview_with_deltas(
        rows, paper_rows,
        title="AI Economic Exposure Across Data Configurations — No Auto-Aug Weighting",
        subtitle=(
            "Each affected task contributes its full freq weight regardless of its 0–5 automatability score."
            "<br>Δ inside each bar = delta vs. the paper chart in percentage points."
        ),
        out_name="overview_no_autoaug.png",
        results=results, figures=figures,
        x_range_max=75.0,
    )


def _load_deepdive_csv(name: str) -> pd.DataFrame | None:
    """Pull a CSV from the deepdive folder if it exists; None if not."""
    src = (ROOT / "analysis" / "exploratory" / "deepdive_within_nonphys_signal"
           / "results" / name)
    if not src.exists():
        return None
    return pd.read_csv(src)


def _df_to_md_table(df: pd.DataFrame, fmt: str = "{:+.2f}",
                    int_cols: tuple[str, ...] = ()) -> str:
    """Render a small DataFrame as a GitHub-flavored markdown table with the
    first column rendered as-is (label) and remaining columns formatted via
    `fmt`. int_cols are rendered as integers."""
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows = [header, sep]
    for _, row in df.iterrows():
        cells = [str(row[cols[0]])]
        for c in cols[1:]:
            val = row[c]
            if c in int_cols:
                cells.append(f"{int(val)}" if pd.notna(val) else "—")
            elif pd.isna(val):
                cells.append("—")
            else:
                cells.append(fmt.format(val))
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)


def _build_appendix_tables_section() -> str:
    """Build the markdown section that holds the two within-non-phys
    discrimination tables + the property correlation table. Each one is read
    fresh from the deepdive folder's CSVs; if any is missing, that subsection
    falls back to a single 'Not generated' line."""
    fric = _load_deepdive_csv("nonphys_friction_weighted_variants_matrix.csv")
    cap = _load_deepdive_csv("nonphys_capability_weighted_variants_matrix.csv")
    cor = _load_deepdive_csv("property_phys_exposure_correlations.csv")

    parts: list[str] = []
    parts.append("---\n\n## Within-non-phys discrimination — friction × weight\n")
    parts.append(
        "Cohen's d on the same top vs bottom exposure quartile of the 409 "
        "non-physical occupations (n=103 each), with each friction-property "
        "composite computed as a per-occ weighted mean across the occ's "
        "unique tasks. Negative d = top quartile lower on the property "
        "(predicted friction direction).\n"
    )
    if fric is not None:
        parts.append(_df_to_md_table(fric, fmt="{:+.2f}") + "\n")
        parts.append(
            "Reading: every three-property combination of r/tf/df hits "
            "|d| ≈ 1.5; single props top out at 1.35. Choice of weight "
            "barely matters (× freq drags d down ~0.15; × imp and × rel are "
            "within rounding error of raw; × value is consistently the "
            "weakest). The combination is what carries the signal, not the "
            "algebraic form, and not the per-task weight.\n"
        )
    else:
        parts.append("_Friction matrix not generated yet — run "
                     "`analysis.exploratory.deepdive_within_nonphys_signal.run`._\n")

    parts.append("---\n\n## Within-non-phys discrimination — capability × weight\n")
    parts.append(
        "Same shape as the friction table but on the three capability "
        "enablers (m / d / s). Predicted direction: top quartile HIGHER on "
        "capability (positive d). Composites include each prop alone, the "
        "sum / mean of all three, the slim two-prop products (d·s, d·m, "
        "m·s), and the audit_task_properties Composite B (d·m·s).\n"
    )
    if cap is not None:
        parts.append(_df_to_md_table(cap, fmt="{:+.2f}") + "\n")
        parts.append(
            "Reading: `s` alone is the strongest single discriminator "
            "(|d| = 0.66 raw → 0.76 × value). `d` is second (0.48 → 0.62). "
            "`m` is essentially noise within non-phys (|d| < 0.20). "
            "Adding `m` to anything *hurts* (d·m < d alone; m·s < s alone). "
            "Composite B (d·m·s) is worse than `s` alone. The audit_task_"
            "properties result that `s` carries most of the capability "
            "signal holds inside non-phys too, and the lift from layering "
            "`d` on top of `s` is small. Notably, capability d-values top "
            "out at 0.76 — meaningfully smaller than the 1.51 the friction "
            "composites reach. **Inside non-phys, friction discriminates "
            "exposure better than capability does.**\n"
        )
    else:
        parts.append("_Capability matrix not generated yet — run "
                     "`analysis.exploratory.deepdive_within_nonphys_signal.run`._\n")

    parts.append("---\n\n## Property × pct_physical × pct_tasks_affected — Spearman ρ\n")
    parts.append(
        "How much each LLM-rated property tracks (a) pct_physical and "
        "(b) pct_tasks_affected, both economy-wide (n=923) and inside the "
        "non-physical cut (n=409). The economy-wide columns show capability "
        "and forward-looking props are heavily entangled with the phys/"
        "non-phys split; the within-non-phys columns show how much *direct* "
        "discriminative signal each prop carries after that cut.\n"
    )
    if cor is not None:
        # Reduce to a friendlier 5-column table
        view = cor[[
            "property",
            "rho_vs_phys_all_eco", "rho_vs_pct_all_eco",
            "rho_vs_phys_within_nonphys", "rho_vs_pct_within_nonphys",
        ]].copy()
        view.columns = [
            "property",
            "ρ vs phys (all eco, n=923)",
            "ρ vs pct (all eco, n=923)",
            "ρ vs phys (non-phys, n=409)",
            "ρ vs pct (non-phys, n=409)",
        ]
        parts.append(_df_to_md_table(view, fmt="{:+.2f}") + "\n")
        parts.append(
            "Reading, in order:\n"
            "1. **Economy-wide, capability props are strongly negative against "
            "pct_physical** (s = −0.67, d = −0.59, m = +0.12 is the outlier). "
            "Every forward-looking prop (de, nt, ac) sits at −0.59 to −0.62. "
            "These props are partially proxying the cognitive/physical cut.\n"
            "2. **Economy-wide vs pct_tasks_affected mirrors that:** s = +0.67, "
            "d = +0.58, de = +0.52. The same props that anti-correlate with "
            "pct_physical positively correlate with exposure.\n"
            "3. **Inside non-phys, capability ρ-vs-phys collapses to |ρ| ≤ 0.13.** "
            "There's not much pct_physical residual to leak through, which is "
            "consistent with the chart-0 diagnostic finding that pct_physical "
            "leaves ~89% of within-non-phys variance unexplained.\n"
            "4. **Inside non-phys, friction wins for direct discrimination:** "
            "r = −0.44, df = −0.34, tf = −0.27 against pct. The strongest "
            "capability prop is s at +0.25. So once you cut to non-phys, "
            "the discriminative work shifts from capability to friction.\n"
        )
    else:
        parts.append("_Correlation table not generated yet — run "
                     "`analysis.exploratory.deepdive_within_nonphys_signal.run`._\n")

    return "\n".join(parts)


def write_markdown() -> None:
    md_path = HERE / "appendix_charts.md"
    extra = _build_appendix_tables_section()
    md_path.write_text(
        "# Appendix figures\n"
        "\n"
        "Auxiliary charts not in the main results. Generated by `run.py`.\n"
        "\n"
        "---\n"
        "\n"
        "## phys_zone_faceted\n"
        "\n"
        "![phys_zone_faceted](figures/phys_zone_faceted.png)\n"
        "\n"
        "---\n"
        "\n"
        "## ska_full\n"
        "\n"
        "![ska_full](figures/ska_full.png)\n"
        "\n"
        "---\n"
        "\n"
        "## nonphys_gwa_diff_phys_excluded\n"
        "\n"
        "Within the 409 non-physical occupations, the General Work Activity "
        "composition that separates the high-exposure quartile from the "
        "low-exposure quartile, computed over only the non-physical tasks of "
        "each occupation. The chart functions as a robustness test on the "
        "raw composition diff: if the same GWAs appear here as in the raw "
        "chart, the structural signal is not a pct_physical residual proxy.\n"
        "\n"
        "![nonphys_gwa_diff_phys_excluded](figures/nonphys_gwa_diff_phys_excluded.png)\n"
        "\n"
        "---\n"
        "\n"
        "## major_de_nt_plane\n"
        "\n"
        "Each of the 22 SOC major occupational categories plotted on the "
        "demand-elasticity × new-task-creation plane (LLM-rated task "
        "properties, 1–5 scale, averaged per major over unique tasks). Dot "
        "size scales with workers affected; color encodes the major's "
        "All-Confirmed % tasks affected. Dashed lines at the per-axis "
        "medians split the plane into four readable quadrants.\n"
        "\n"
        "![major_de_nt_plane](figures/major_de_nt_plane.png)\n"
        "\n"
        "---\n"
        "\n"
        "## convergence_full\n"
        "\n"
        "Combined version of the two main convergence charts (Part 1 — "
        "`convergence` and `convergence_configs`): the four internal AI "
        "sources and five `ANALYSIS_CONFIGS` data configurations are stacked "
        "on a single y-axis (9 rows). The x-axis carries those same nine "
        "measures as a lower-triangular internal block, then the gap "
        "column, then the eight external academic benchmarks. Cell "
        "rendering, group headers, and the Eloundou-contamination gray-out "
        "match the main paper charts exactly.\n"
        "\n"
        "![convergence_full](figures/convergence_full.png)\n"
        "\n"
        "---\n"
        "\n"
        "## overview_no_autoaug\n"
        "\n"
        "Paper part_1 `overview` recomputed with `use_auto_aug=False`. Each "
        "affected task contributes its full freq weight regardless of its "
        "0–5 automatability score. Inside-bar text carries `Δ±X.Xpp` vs. the "
        "paper chart; black tick marks the paper-chart value's position on "
        "each bar.\n"
        "\n"
        "![overview_no_autoaug](figures/overview_no_autoaug.png)\n"
        "\n"
        + extra,
        encoding="utf-8",
    )
    print(f"  -> {md_path.relative_to(ROOT)}")


def main() -> None:
    results = ensure_results_dir(HERE)
    figures = HERE / "figures"
    figures.mkdir(exist_ok=True)

    print("=" * 60)
    print("Appendix figures")
    print("=" * 60)

    print("\n[1/6] phys_zone_faceted (modified)")
    build_phys_zone_faceted(results, figures)

    print("\n[2/6] ska_full (full element-level SKA)")
    build_ska_full(results, figures)

    print("\n[3/6] nonphys_gwa_diff_phys_excluded (within-non-phys structural)")
    build_nonphys_gwa_diff_phys_excluded(results, figures)

    print("\n[4/6] major_de_nt_plane (forward-looking quadrant)")
    build_major_de_nt_plane(results, figures)

    print("\n[5/6] convergence_full (sources + configs vs. external benchmarks)")
    build_convergence_full(results, figures)

    print("\n[6/6] overview_no_autoaug (paper part_1 overview, no auto_aug)")
    build_overview_no_autoaug(results, figures)

    print("\nWriting appendix_charts.md")
    write_markdown()

    print("\nDone — figures in results/figures/ and figures/")


if __name__ == "__main__":
    main()
