"""
run.py — Exploratory: Physical vs. Informational Divide

Classifies occupations by the proportion of their O*NET tasks that are physical
(using the `physical` flag in the task data):
  < 33% physical tasks → Non-physical occupation
  33–67% physical tasks → Mixed occupation
  > 67% physical tasks → Physical occupation

For each of the six (occ_group × task_type) combinations, shows the distribution
of tasks across GWA, IWA, and DWA categories — purely structural task counts, no
AI scoring. Also compares average auto-aug score across the three occupation groups.

Four figures:
  1. gwa_task_distribution  — 3×2 panel: top-15 GWAs by task count
  2. iwa_task_distribution  — 3×2 panel: top-12 IWAs by task count
  3. dwa_task_distribution  — 3×2 panel: top-10 DWAs by task count
  4. auto_aug_by_occ_group  — 3-bar horizontal: mean auto-aug per occ group

Run from project root:
    venv/Scripts/python -m analysis.exploratory.physical_informational_divide.run
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.config import ensure_results_dir
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

# ── Constants ──────────────────────────────────────────────────────────────────

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent.parent.parent / "data"
PRIMARY_DATASET = "final_all_confirmed_usage_2026-02-12.csv"

PHYS_LOWER = 33.0   # below this → Non-physical occupation
PHYS_UPPER = 67.0   # above this → Physical occupation

OCC_GROUPS = ["Non-physical", "Mixed", "Physical"]
TASK_TYPES = ["Physical tasks", "Non-physical tasks"]

GROUP_COLORS = {
    "Non-physical": COLORS["primary"],    # slate blue
    "Mixed":        COLORS["secondary"],  # teal green
    "Physical":     COLORS["accent"],     # orange-brown
}

TOP_GWA = 15
TOP_IWA = 12
TOP_DWA = 10
LABEL_MAX_CHARS = 52


# ── Data loading ───────────────────────────────────────────────────────────────

def load_and_classify() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load all_confirmed task data; classify occupations by % physical tasks.

    Returns
    -------
    df       : task-level DataFrame with occ_group and task_type columns added
    occ_stats: occupation-level DataFrame with pct_physical, occ_group, auto_aug
    """
    path = DATA_DIR / PRIMARY_DATASET
    assert path.exists(), f"Dataset not found: {path}"

    df = pd.read_csv(path)

    assert "title_current" in df.columns, "Missing title_current"
    assert "physical" in df.columns, "Missing physical flag"
    assert "iwa_title" in df.columns, "Missing iwa_title"
    assert "gwa_title" in df.columns, "Missing gwa_title"
    assert "dwa_title" in df.columns, "Missing dwa_title"
    assert "auto_aug_mean" in df.columns, "Missing auto_aug_mean"
    assert not df.empty, "Dataset is empty"

    # Occupation-level stats
    occ_stats = (
        df.groupby("title_current")
        .agg(
            n_tasks=("physical", "count"),
            n_physical=("physical", "sum"),
            auto_aug=("auto_aug_mean", "first"),   # occupation-level score, same for all rows
            major_cat=("major_occ_category", "first"),
        )
        .reset_index()
    )
    occ_stats["pct_physical"] = occ_stats["n_physical"] / occ_stats["n_tasks"] * 100

    occ_stats["occ_group"] = "Mixed"
    occ_stats.loc[occ_stats["pct_physical"] < PHYS_LOWER, "occ_group"] = "Non-physical"
    occ_stats.loc[occ_stats["pct_physical"] > PHYS_UPPER, "occ_group"] = "Physical"

    # Join classification to task-level rows
    df = df.merge(occ_stats[["title_current", "occ_group"]], on="title_current", how="left")
    df["task_type"] = df["physical"].map({True: "Physical tasks", False: "Non-physical tasks"})

    return df, occ_stats


# ── Figure helpers ─────────────────────────────────────────────────────────────

def _truncate(s: str, max_chars: int = LABEL_MAX_CHARS) -> str:
    return s if len(s) <= max_chars else s[:max_chars - 1] + "…"


def fig_task_distribution(
    df: pd.DataFrame,
    level_col: str,
    top_n: int,
    title: str,
    subtitle: str,
) -> go.Figure:
    """3×2 subplot: top-N work activity categories by task count for each
    (occ_group × task_type) combination.

    Rows: Non-physical / Mixed / Physical occupations
    Cols: Physical tasks / Non-physical tasks
    """
    subplot_titles = [f"{g} — {t}" for g in OCC_GROUPS for t in TASK_TYPES]

    fig = make_subplots(
        rows=3,
        cols=2,
        subplot_titles=subplot_titles,
        horizontal_spacing=0.08,
        vertical_spacing=0.09,
    )

    for ri, grp in enumerate(OCC_GROUPS, start=1):
        color = GROUP_COLORS[grp]
        for ci, task_type in enumerate(TASK_TYPES, start=1):
            subset = df[(df["occ_group"] == grp) & (df["task_type"] == task_type)]
            counts = (
                subset.groupby(level_col)
                .size()
                .reset_index(name="n_tasks")
                # ascending=True → smallest at bottom, largest at top in Plotly horizontal bar
                .sort_values("n_tasks", ascending=True)
                .tail(top_n)
            )
            counts[level_col] = counts[level_col].apply(_truncate)

            fig.add_trace(
                go.Bar(
                    x=counts["n_tasks"],
                    y=counts[level_col],
                    orientation="h",
                    marker=dict(color=color, line=dict(width=0)),
                    text=counts["n_tasks"].astype(str),
                    textposition="outside",
                    textfont=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
                    showlegend=False,
                    cliponaxis=False,
                ),
                row=ri,
                col=ci,
            )

    # Height: ~28px per bar per row, 3 rows, plus margins
    height = top_n * 28 * 3 + 220

    fig.update_layout(
        height=height,
        width=1400,
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(family=FONT_FAMILY, size=10, color=COLORS["text"]),
        title=dict(
            text=(
                f"{title}<br>"
                f"<span style='font-size:12px;color:{COLORS['neutral']}'>{subtitle}</span>"
            ),
            font=dict(size=16, family=FONT_FAMILY, color=COLORS["text"]),
            x=0.01,
            xanchor="left",
        ),
        margin=dict(l=20, r=90, t=100, b=60),
    )

    for ri in range(1, 4):
        for ci in range(1, 3):
            fig.update_xaxes(
                showgrid=False,
                showticklabels=False,
                showline=False,
                zeroline=False,
                row=ri,
                col=ci,
            )
            fig.update_yaxes(
                tickfont=dict(size=9, family=FONT_FAMILY, color=COLORS["neutral"]),
                showline=False,
                showgrid=False,
                row=ri,
                col=ci,
            )

    fig.add_annotation(
        text="Source: AEA Dashboard — Utah OAIP | O*NET 2025 task structure | All Confirmed config",
        xref="paper",
        yref="paper",
        x=1.0,
        y=-0.03,
        showarrow=False,
        font=dict(size=9, color=COLORS["muted"], family=FONT_FAMILY),
        xanchor="right",
    )

    return fig


def fig_auto_aug(occ_stats: pd.DataFrame) -> go.Figure:
    """3-bar horizontal chart: mean auto-aug score by occupation group."""
    summary = (
        occ_stats.groupby("occ_group")["auto_aug"]
        .agg(mean_auto_aug="mean")
        .reset_index()
        # ascending=True → largest at top in horizontal bar
        .sort_values("mean_auto_aug", ascending=True)
    )

    colors = [GROUP_COLORS[grp] for grp in summary["occ_group"]]

    fig = go.Figure(
        go.Bar(
            x=summary["mean_auto_aug"],
            y=summary["occ_group"],
            orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=[f"{v:.2f}" for v in summary["mean_auto_aug"]],
            textposition="outside",
            textfont=dict(size=13, color=COLORS["neutral"], family=FONT_FAMILY),
            cliponaxis=False,
        )
    )

    fig.update_layout(
        xaxis=dict(
            range=[0, 5.5],
            showgrid=False,
            showticklabels=False,
            showline=False,
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            tickfont=dict(size=13, family=FONT_FAMILY),
        ),
        bargap=0.4,
    )

    style_figure(
        fig,
        "Average Auto-Augmentability Score by Occupation Group",
        subtitle=(
            "Mean auto-aug score (0–5 scale) | All Confirmed config | "
            "Thresholds: <33% physical tasks = Non-physical, >67% = Physical"
        ),
        show_legend=False,
        height=380,
    )

    return fig


# ── Summary printing ───────────────────────────────────────────────────────────

def print_summary(occ_stats: pd.DataFrame, df: pd.DataFrame) -> None:
    print("\n=== Occupation Classification Summary ===")
    group_counts = occ_stats.groupby("occ_group").agg(
        n_occs=("title_current", "count"),
        mean_pct_physical=("pct_physical", "mean"),
        mean_auto_aug=("auto_aug", "mean"),
    )
    print(group_counts.to_string())

    print("\n=== Task Counts by (occ_group, task_type) ===")
    task_counts = df.groupby(["occ_group", "task_type"]).size().reset_index(name="n_tasks")
    print(task_counts.to_string(index=False))

    print("\n=== Auto-aug by occ group ===")
    aug = occ_stats.groupby("occ_group")["auto_aug"].agg(["mean", "median"]).round(3)
    print(aug.to_string())

    print("\n=== Top 5 GWAs per (occ_group, task_type) ===")
    for grp in OCC_GROUPS:
        for tt in TASK_TYPES:
            sub = df[(df["occ_group"] == grp) & (df["task_type"] == tt)]
            top = sub.groupby("gwa_title").size().nlargest(5)
            print(f"\n  {grp} / {tt}:")
            for name, cnt in top.items():
                print(f"    {cnt:4d}  {name}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    results_dir = ensure_results_dir(HERE)
    figures_dir = results_dir / "figures"

    # Load and classify
    df, occ_stats = load_and_classify()
    print_summary(occ_stats, df)

    # Save CSVs
    save_csv(
        occ_stats[["title_current", "pct_physical", "occ_group", "auto_aug", "major_cat"]],
        results_dir / "occ_classification.csv",
    )

    auto_aug_summary = (
        occ_stats.groupby("occ_group")["auto_aug"]
        .agg(mean="mean", median="median", n_occs="count")
        .reset_index()
        .round(3)
    )
    save_csv(auto_aug_summary, results_dir / "auto_aug_summary.csv")

    for level_col, label in [("gwa_title", "gwa"), ("iwa_title", "iwa"), ("dwa_title", "dwa")]:
        counts = (
            df.groupby(["occ_group", "task_type", level_col])
            .size()
            .reset_index(name="n_tasks")
        )
        save_csv(counts, results_dir / f"{label}_counts.csv")

    # Figure 1: GWA distribution
    f1 = fig_task_distribution(
        df,
        level_col="gwa_title",
        top_n=TOP_GWA,
        title="Task Distribution by GWA: Physical vs. Non-Physical Occupations",
        subtitle=(
            f"Top {TOP_GWA} General Work Activities by task count | "
            "Rows = occupation group | Cols = physical vs. non-physical tasks"
        ),
    )
    save_figure(f1, figures_dir / "gwa_task_distribution.png", width=1400, height=f1.layout.height)

    # Figure 2: IWA distribution
    f2 = fig_task_distribution(
        df,
        level_col="iwa_title",
        top_n=TOP_IWA,
        title="Task Distribution by IWA: Physical vs. Non-Physical Occupations",
        subtitle=(
            f"Top {TOP_IWA} Intermediate Work Activities by task count | "
            "Rows = occupation group | Cols = physical vs. non-physical tasks"
        ),
    )
    save_figure(f2, figures_dir / "iwa_task_distribution.png", width=1400, height=f2.layout.height)

    # Figure 3: DWA distribution
    f3 = fig_task_distribution(
        df,
        level_col="dwa_title",
        top_n=TOP_DWA,
        title="Task Distribution by DWA: Physical vs. Non-Physical Occupations",
        subtitle=(
            f"Top {TOP_DWA} Detailed Work Activities by task count | "
            "Rows = occupation group | Cols = physical vs. non-physical tasks"
        ),
    )
    save_figure(f3, figures_dir / "dwa_task_distribution.png", width=1400, height=f3.layout.height)

    # Figure 4: Auto-aug by occ group
    f4 = fig_auto_aug(occ_stats)
    save_figure(f4, figures_dir / "auto_aug_by_occ_group.png", width=900, height=380)

    # Generate PDF from report
    report_path = HERE / "physical_informational_divide_report.md"
    if report_path.exists():
        generate_pdf(report_path, results_dir / "physical_informational_divide_report.pdf")

    print("Done.")


if __name__ == "__main__":
    main()
