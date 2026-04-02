"""
run.py — Job Exposure: Worker Resilience

What can an individual worker do to make their job more resilient to AI?

For each occupation, ranks Skills, Abilities, and Knowledge elements by the
gap between the occupation's need and AI's current capability. Elements where
gap < 0 (human exceeds AI) are where training effort matters most. Elements
where gap > 0 (AI already exceeds occ need) are where workers should leverage
AI as a tool rather than compete with it.

Uses all three O*NET types (S + A + K), importance >= 3 filter.
Gap = AI capability score − occupation score.

Primary config: all_ceiling. Cross-config comparison shows which gaps are robust.

Run from project root:
    venv/Scripts/python -m analysis.questions.job_exposure.worker_resilience.run
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
    OCCS_OF_INTEREST,
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.data.compute_ska import SKAResult, compute_ska, load_ska_data
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent

# Config used as primary
PRIMARY_KEY = "all_ceiling"

# Number of elements to show in bar charts
TOP_N_ELEMENTS = 15


def _find_occ(title: str, available: set[str]) -> str | None:
    """Fuzzy match an occupation title against available titles (case-insensitive)."""
    title_lower = title.lower()
    for occ in available:
        if occ.lower() == title_lower:
            return occ
    # Partial match
    for occ in available:
        if title_lower in occ.lower() or occ.lower() in title_lower:
            return occ
    return None


# ── Figures ───────────────────────────────────────────────────────────────────

def _element_gap_bar(
    element_df: pd.DataFrame,
    title: str,
    subtitle: str,
    direction: str,       # "human_advantage" | "ai_advantage"
    n: int = TOP_N_ELEMENTS,
) -> go.Figure:
    """Horizontal bar chart of top N elements by gap magnitude."""
    if direction == "human_advantage":
        # Most negative gap = biggest human advantage
        top = element_df.nsmallest(n, "mean_gap").sort_values("mean_gap", ascending=False)
        color = COLORS["primary"]
        label_fn = lambda v: f"{abs(v):.2f}"
    else:
        # Most positive gap = AI leads most
        top = element_df.nlargest(n, "mean_gap").sort_values("mean_gap", ascending=True)
        color = COLORS["negative"]
        label_fn = lambda v: f"+{v:.2f}"

    labels = [f"{label_fn(v)}  ({t})" for v, t in zip(top["mean_gap"], top["type"])]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top["element_name"],
        x=top["mean_gap"].abs(),
        orientation="h",
        marker=dict(color=color, line=dict(width=0)),
        text=labels,
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    chart_h = max(400, n * 38 + 150)
    style_figure(fig, title, subtitle=subtitle, x_title=None,
                 height=chart_h, show_legend=False)
    fig.update_layout(
        margin=dict(l=20, r=100),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False, zeroline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        bargap=0.25,
    )
    return fig


def _occ_heatmap(
    occ_elem_df: pd.DataFrame,
    occs: list[str],
    elements: list[str],
    title: str,
    subtitle: str,
) -> go.Figure:
    """Heatmap: occ × element gap for a selected set of occupations and elements."""
    pivot = occ_elem_df[
        occ_elem_df["title_current"].isin(occs) &
        occ_elem_df["element_name"].isin(elements)
    ].pivot_table(
        index="title_current", columns="element_name", values="gap", aggfunc="mean"
    )
    # Fill missing with 0
    pivot = pivot.reindex(index=occs, columns=elements, fill_value=0)

    z = pivot.values
    fig = go.Figure(go.Heatmap(
        z=z,
        x=elements,
        y=occs,
        colorscale=[
            [0.0, COLORS["primary"]],    # most negative = strong human advantage
            [0.5, "#f5f5f0"],
            [1.0, COLORS["negative"]],   # most positive = AI leads
        ],
        zmid=0,
        text=np.round(z, 2),
        texttemplate="%{text:.1f}",
        hovertemplate="<b>%{y}</b><br>%{x}<br>Gap: %{z:.2f}<extra></extra>",
        showscale=True,
    ))
    chart_h = max(500, len(occs) * 22 + 200)
    chart_w = max(800, len(elements) * 40 + 250)
    style_figure(fig, title, subtitle=subtitle, x_title=None, y_title=None,
                 height=chart_h, width=chart_w, show_legend=False)
    fig.update_layout(
        xaxis=dict(tickangle=-45, tickfont=dict(size=8, family=FONT_FAMILY)),
        yaxis=dict(autorange="reversed", tickfont=dict(size=9, family=FONT_FAMILY)),
    )
    return fig


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    fig_dir = results / "figures"
    print("Worker Resilience -- generating outputs...\n")

    # ── Load SKA data ─────────────────────────────────────────────────────────
    print("Loading SKA base data...")
    ska_data = load_ska_data()

    # ── Primary config ────────────────────────────────────────────────────────
    print(f"Computing pct for primary config ({PRIMARY_KEY})...")
    pct_primary = get_pct_tasks_affected(ANALYSIS_CONFIGS[PRIMARY_KEY])

    print("Computing SKA gaps (primary config)...")
    result_primary: SKAResult = compute_ska(pct_primary, ska_data)

    # ── Per-element summary (mean gap across all matched occs) ─────────────────
    all_elem_rows = []
    for type_name, elem_df in result_primary.occ_element_scores.items():
        agg = (
            elem_df.groupby("element_name")["gap"]
            .agg(["mean", "median", "std", "count"])
            .reset_index()
            .rename(columns={"mean": "mean_gap", "median": "median_gap",
                              "std": "std_gap", "count": "n_occs"})
        )
        agg["type"] = type_name
        all_elem_rows.append(agg)
    element_summary = pd.concat(all_elem_rows, ignore_index=True)
    element_summary = element_summary.sort_values("mean_gap")

    save_csv(element_summary, results / "element_gaps_summary.csv")
    print(f"Saved element_gaps_summary.csv ({len(element_summary)} elements)")

    # Human advantage (gap < 0 = occ need > AI capability)
    human_advantage = element_summary[element_summary["mean_gap"] < 0].nsmallest(
        TOP_N_ELEMENTS, "mean_gap"
    )
    save_csv(human_advantage, results / "human_advantage_elements.csv")

    # AI advantage (gap > 0 = AI already exceeds occ need)
    ai_advantage = element_summary[element_summary["mean_gap"] > 0].nlargest(
        TOP_N_ELEMENTS, "mean_gap"
    )
    save_csv(ai_advantage, results / "ai_advantage_elements.csv")

    # ── Per-occ element detail (all_ceiling) ──────────────────────────────────
    occ_elem_all = pd.concat([
        df.assign(type=t)
        for t, df in result_primary.occ_element_scores.items()
    ], ignore_index=True)
    save_csv(occ_elem_all, results / "occ_element_gaps.csv")
    print("Saved occ_element_gaps.csv")

    # Per-occ summary
    occ_gaps = result_primary.occ_gaps.copy()
    save_csv(occ_gaps, results / "occ_gaps_summary.csv")
    print("Saved occ_gaps_summary.csv")

    # ── Occs of interest ─────────────────────────────────────────────────────
    available_occs = set(occ_gaps["title_current"].tolist())
    matched_occs = []
    for name in OCCS_OF_INTEREST:
        match = _find_occ(name, available_occs)
        if match:
            matched_occs.append(match)
        else:
            print(f"  WARNING: '{name}' not matched in SKA results")

    occ_interest_gaps = occ_gaps[occ_gaps["title_current"].isin(matched_occs)].copy()

    # Per-element detail for occs of interest
    occ_interest_elem = occ_elem_all[occ_elem_all["title_current"].isin(matched_occs)]

    # Top 5 human-advantage and AI-advantage elements per occ of interest
    interest_rows = []
    for occ in matched_occs:
        occ_data = occ_interest_elem[occ_interest_elem["title_current"] == occ]
        top_human = occ_data.nsmallest(5, "gap")[["element_name", "type", "occ_score",
                                                    "ai_score", "gap"]].assign(
            direction="human_advantage", rank=range(1, 6))
        top_ai = occ_data.nlargest(5, "gap")[["element_name", "type", "occ_score",
                                               "ai_score", "gap"]].assign(
            direction="ai_advantage", rank=range(1, 6))
        for df_part in [top_human, top_ai]:
            df_part["title_current"] = occ
            interest_rows.append(df_part)
    if interest_rows:
        interest_detail = pd.concat(interest_rows, ignore_index=True)
        save_csv(interest_detail, results / "occs_of_interest_gaps.csv")
        print(f"Saved occs_of_interest_gaps.csv ({len(matched_occs)} occupations)")

    # ── Cross-config comparison ───────────────────────────────────────────────
    print("\nComputing cross-config SKA gaps...")
    config_gap_rows = []
    for config_key, dataset_name in ANALYSIS_CONFIGS.items():
        pct_cfg = get_pct_tasks_affected(dataset_name)
        result_cfg = compute_ska(pct_cfg, ska_data)
        gaps_cfg = result_cfg.occ_gaps.copy()
        gaps_cfg["config"] = config_key
        config_gap_rows.append(gaps_cfg[["title_current", "config", "overall_gap",
                                          "skills_gap", "abilities_gap", "knowledge_gap"]])
        print(f"  Done: {config_key}")
    config_gaps = pd.concat(config_gap_rows, ignore_index=True)
    save_csv(config_gaps, results / "occ_gaps_all_configs.csv")
    print("Saved occ_gaps_all_configs.csv")

    # ── Figures ───────────────────────────────────────────────────────────────
    print("\nGenerating figures...")

    # Human advantage bar
    fig = _element_gap_bar(
        element_summary, direction="human_advantage",
        title="Where Humans Still Have the Biggest Advantage Over AI",
        subtitle=f"Avg gap = AI capability − occ score (negative = human leads) | {ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]}",
    )
    save_figure(fig, fig_dir / "human_advantage_bar.png")
    print("  human_advantage_bar.png")

    # AI advantage bar
    fig = _element_gap_bar(
        element_summary, direction="ai_advantage",
        title="Where AI Already Exceeds the Typical Occupation's Need",
        subtitle=f"Avg gap = AI capability − occ score (positive = AI leads) | {ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]}",
    )
    save_figure(fig, fig_dir / "ai_advantage_bar.png")
    print("  ai_advantage_bar.png")

    # Heatmap: occs of interest × top elements by gap magnitude
    if matched_occs:
        top_elements = (
            element_summary.assign(abs_gap=element_summary["mean_gap"].abs())
            .nlargest(25, "abs_gap")["element_name"]
            .tolist()
        )
        fig = _occ_heatmap(
            occ_elem_all, occs=matched_occs[:20], elements=top_elements,
            title="SKA Gap Heatmap — Occupations of Interest",
            subtitle="Blue = human advantage | Red = AI leads | Primary config: all_ceiling",
        )
        save_figure(fig, fig_dir / "occ_heatmap.png")
        print("  occ_heatmap.png")

    # ── Copy key figures ──────────────────────────────────────────────────────
    committed = HERE / "figures"
    committed.mkdir(exist_ok=True)
    for fname in ["human_advantage_bar.png", "ai_advantage_bar.png", "occ_heatmap.png"]:
        src = fig_dir / fname
        if src.exists():
            shutil.copy2(src, committed / fname)

    # ── PDF ───────────────────────────────────────────────────────────────────
    from analysis.utils import generate_pdf
    md_path = HERE / "worker_resilience_report.md"
    if md_path.exists():
        generate_pdf(md_path, results / "worker_resilience_report.pdf")

    print("\nDone.")


if __name__ == "__main__":
    main()
