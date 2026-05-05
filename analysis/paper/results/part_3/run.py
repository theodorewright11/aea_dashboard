"""
Part 3 — Action: What To Do About It

Currently a single figure. Audience scaffolding and additional charts are
on hold pending a content revamp.

  1. Tech commodities composite (top-25)

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
    ANNOT_FS, LABEL_FS,
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
# Main
# ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figures = HERE / "figures"
    figures.mkdir(exist_ok=True)

    print("=" * 64)
    print("Part 3: Action — What To Do About It")
    print("=" * 64)

    print("\n[1/1] Tech commodities composite")
    build_tech_commodities(results, figures)

    print("\n" + "=" * 64)
    print("Part 3 complete — figures in results/figures/ and figures/")
    print("=" * 64)


if __name__ == "__main__":
    main()
