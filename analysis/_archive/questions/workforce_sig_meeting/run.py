"""
workforce_sig_meeting — generates the two custom charts the report needs.

Most charts in `workforce_sig_meeting_report.md` are reused from
`analysis/paper/results/part_1`, `part_2`, and `part_3` (`tech_commodities.png`
only). Two are produced locally here:

  1. `conv_allconfirmed_ceiling.png` — three bars per major:
     Conversational → All Confirmed → Ceiling.
  2. `gap_to_ceiling_wages.png` — top sectors by all_confirmed → all_ceiling
     wage gap. Stacked "confirmed + extension to ceiling" structure on a
     wages-affected x-axis.

Both charts get saved to `results/figures/` (gitignored) and copied to
`figures/` (committed) so the report renders on GitHub.

Run from project root:
    venv/Scripts/python -m analysis.questions.workforce_sig_meeting.run
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from analysis.config import ANALYSIS_CONFIGS, ensure_results_dir
from analysis.utils import FONT_FAMILY, save_csv, save_figure
from analysis.paper.paper_config import (
    PAPER_W,
    TICK_FS, LABEL_FS, ANNOT_FS,
    CONFIG_COLORS, PAPER_PALETTE,
    style_paper_figure, fmt_wages, fmt_workers,
)

HERE = Path(__file__).resolve().parent


def _run_config(dataset_name: str, agg_level: str) -> pd.DataFrame:
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


def _copy_fig(results: Path, figures: Path, name: str) -> None:
    shutil.copy(results / "figures" / name, figures / name)


# ─────────────────────────────────────────────────────────────────────────
# Figure 1: Conversational vs. All Confirmed vs. Ceiling
# ─────────────────────────────────────────────────────────────────────────

def build_conv_allconfirmed_ceiling(results: Path, figures: Path) -> None:
    conv = _run_config(ANALYSIS_CONFIGS["human_conversation"], "major")
    all_conf = _run_config(ANALYSIS_CONFIGS["all_confirmed"], "major")
    all_ceil = _run_config(ANALYSIS_CONFIGS["all_ceiling"], "major")

    keep_cols = ["category", "pct_tasks_affected", "workers_affected", "wages_affected"]
    df = (
        conv[keep_cols].rename(columns={
            "pct_tasks_affected": "pct_conv",
            "workers_affected": "wk_conv",
            "wages_affected": "wg_conv",
        }).merge(
            all_conf[keep_cols].rename(columns={
                "pct_tasks_affected": "pct_allconf",
                "workers_affected": "wk_allconf",
                "wages_affected": "wg_allconf",
            }), on="category"
        ).merge(
            all_ceil[keep_cols].rename(columns={
                "pct_tasks_affected": "pct_ceil",
                "workers_affected": "wk_ceil",
                "wages_affected": "wg_ceil",
            }), on="category"
        )
    )
    df["ceiling_gap"] = df["pct_ceil"] - df["pct_conv"]
    df = df.sort_values("ceiling_gap", ascending=False).head(15).copy()
    save_csv(df, results / "conv_allconfirmed_ceiling.csv")

    df = df.sort_values("ceiling_gap", ascending=True)  # plotly bottom-up
    cats = df["category"].tolist()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=cats, x=df["pct_conv"], orientation="h",
        name="Conversational Confirmed",
        marker=dict(color=CONFIG_COLORS["human_conversation"], line=dict(width=0)),
        text=[f"{v:.0f}%" for v in df["pct_conv"]],
        textposition="inside", insidetextanchor="end",
        textfont=dict(size=12, color="white", family=FONT_FAMILY),
        hovertemplate="%{y}<br>Conversational: %{x:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=cats, x=df["pct_allconf"], orientation="h",
        name="All Confirmed",
        marker=dict(color=CONFIG_COLORS["all_confirmed"], line=dict(width=0)),
        text=[f"{v:.0f}%" for v in df["pct_allconf"]],
        textposition="inside", insidetextanchor="end",
        textfont=dict(size=12, color="white", family=FONT_FAMILY),
        hovertemplate="%{y}<br>All Confirmed: %{x:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=cats, x=df["pct_ceil"], orientation="h",
        name="Ceiling",
        marker=dict(color=CONFIG_COLORS["all_ceiling"], line=dict(width=0)),
        text=[f"{v:.0f}%" for v in df["pct_ceil"]],
        textposition="inside", insidetextanchor="end",
        textfont=dict(size=12, color="white", family=FONT_FAMILY),
        hovertemplate="%{y}<br>Ceiling: %{x:.1f}%<extra></extra>",
    ))

    annotations_x = [
        max(c, ac, ce) + 1
        for c, ac, ce in zip(df["pct_conv"], df["pct_allconf"], df["pct_ceil"])
    ]
    fig.add_trace(go.Scatter(
        y=cats, x=annotations_x, mode="text",
        text=[f"+{h:.0f}pp ceiling gap" for h in df["ceiling_gap"]],
        textposition="middle right",
        textfont=dict(size=ANNOT_FS, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showlegend=False, hoverinfo="skip",
    ))

    fig.update_layout(barmode="group", bargap=0.20, bargroupgap=0.10)
    style_paper_figure(
        fig,
        "Conversational vs. All Confirmed vs. Ceiling by Sector",
        subtitle=(
            "Top 15 sectors by ceiling-minus-conversational gap | "
            "Conversational = AEI Conv + Microsoft | "
            "All Confirmed = AEI Conv + API + Microsoft | "
            "Ceiling = AEI + MCP + Microsoft | "
            "National | freq, auto-aug ON"
        ),
        height=720, width=PAPER_W,
        margin=dict(l=30, r=200, t=110, b=110),
    )
    fig.update_xaxes(
        title=dict(text="% Tasks Affected", font=dict(size=LABEL_FS)),
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        ticksuffix="%", range=[0, max(df["pct_ceil"]) * 1.18],
    )
    fig.update_yaxes(showgrid=False, showline=False, tickfont=dict(size=TICK_FS - 1))

    save_figure(fig, results / "figures" / "conv_allconfirmed_ceiling.png", scale=2)
    _copy_fig(results, figures, "conv_allconfirmed_ceiling.png")
    print("  -> conv_allconfirmed_ceiling.png")


# ─────────────────────────────────────────────────────────────────────────
# Figure 2: Gap to Ceiling — wages variant
# ─────────────────────────────────────────────────────────────────────────

def build_gap_to_ceiling_wages(results: Path, figures: Path) -> None:
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

    df = df.sort_values("wg_gap", ascending=False).head(15).copy()
    save_csv(df, results / "gap_to_ceiling_wages.csv")
    df = df.sort_values("wg_gap", ascending=True)
    cats = df["category"].tolist()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=cats, x=df["wg_conf"], orientation="h",
        name="Confirmed (wages affected)",
        marker=dict(color=CONFIG_COLORS["all_confirmed"], line=dict(width=0)),
        text=[fmt_wages(v) for v in df["wg_conf"]],
        textposition="inside", insidetextanchor="end",
        textfont=dict(size=12, color="white", family=FONT_FAMILY),
        hovertemplate="%{y}<br>Confirmed: $%{x:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=cats, x=df["wg_gap"], orientation="h",
        name="Gap to Ceiling",
        marker=dict(color=CONFIG_COLORS["all_ceiling"], opacity=0.55, line=dict(width=0)),
        text=[f"+{fmt_wages(w)}  (+{p:.0f}pp, +{fmt_workers(v)})"
              for w, p, v in zip(df["wg_gap"], df["pct_gap"], df["wk_gap"])],
        textposition="outside",
        textfont=dict(size=ANNOT_FS, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
        hovertemplate="%{y}<br>Gap: +$%{x:,.0f}<extra></extra>",
    ))

    fig.update_layout(barmode="stack", bargap=0.25)
    style_paper_figure(
        fig,
        "Where Confirmed Use Sits Furthest Below Demonstrated Capability (Wages)",
        subtitle=(
            "Top 15 sectors by all-confirmed → all-ceiling wage gap | "
            "Each row: confirmed wages bar + extension to ceiling | "
            "National | freq, auto-aug ON"
        ),
        height=720, width=PAPER_W,
        margin=dict(l=30, r=320, t=110, b=110),
    )
    max_total = (df["wg_conf"] + df["wg_gap"]).max()
    fig.update_xaxes(
        title=dict(text="Wages Affected (USD/yr)", font=dict(size=LABEL_FS)),
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        range=[0, max_total * 1.30],
        tickformat="$.2s",
    )
    fig.update_yaxes(showgrid=False, showline=False, tickfont=dict(size=TICK_FS - 1))

    save_figure(fig, results / "figures" / "gap_to_ceiling_wages.png", scale=2)
    _copy_fig(results, figures, "gap_to_ceiling_wages.png")
    print("  -> gap_to_ceiling_wages.png")


# ─────────────────────────────────────────────────────────────────────────
# Methodology table — Chief Executives breakdown
# ─────────────────────────────────────────────────────────────────────────

def build_methodology_breakdown(results: Path) -> dict:
    """Pull the real Chief Executives task breakdown that backs the
    methodology table at the top of the report. Returns a dict with the
    per-task rows (full + sample) and the summary numbers.

    The values returned here are what the report quotes; if data ever
    changes, regenerate the report with these numbers."""
    eco_path = HERE.parent.parent.parent / "data" / "final_eco_2025.csv"
    ac_path = HERE.parent.parent.parent / "data" / "final_all_confirmed_usage_2026-02-12.csv"
    eco = pd.read_csv(eco_path)
    ac = pd.read_csv(ac_path)

    ce_eco = eco[eco["title_current"] == "Chief Executives"].drop_duplicates(
        subset=["task_normalized"]
    )
    ce_ac = ac[ac["title_current"] == "Chief Executives"].drop_duplicates(
        subset=["task_normalized"]
    )

    merged = ce_eco[["task", "task_normalized", "freq_mean"]].merge(
        ce_ac[["task_normalized", "auto_aug_mean"]],
        on="task_normalized", how="left",
    )
    merged["ai_affected"] = merged["auto_aug_mean"].notna()
    merged["weight_baseline"] = merged["freq_mean"].fillna(0.0)
    merged["weight_ai"] = (
        merged["freq_mean"].fillna(0.0)
        * merged["auto_aug_mean"].fillna(0.0)
        / 5.0
    )
    save_csv(merged.sort_values(["ai_affected", "freq_mean"], ascending=[False, False]),
             results / "methodology_chief_executives_full.csv",
             float_format="%.4f")

    n_total = int(len(merged))
    n_ai = int(merged["ai_affected"].sum())
    sum_baseline = float(merged["weight_baseline"].sum())
    sum_ai = float(merged["weight_ai"].sum())
    pct = sum_ai / sum_baseline * 100.0
    emp = float(ce_eco["emp_tot_nat_2025"].iloc[0])
    wage = float(ce_eco["a_med_nat_2025"].iloc[0])
    workers = pct / 100.0 * emp
    wages = workers * wage

    summary = {
        "n_total_tasks": n_total,
        "n_ai_tasks": n_ai,
        "sum_baseline_freq": sum_baseline,
        "sum_ai_weighted": sum_ai,
        "pct_tasks_affected": pct,
        "employment": emp,
        "median_wage": wage,
        "workers_affected": workers,
        "wages_affected": wages,
    }
    save_csv(pd.DataFrame([summary]),
             results / "methodology_chief_executives_summary.csv",
             float_format="%.4f")
    print(
        "  -> methodology breakdown: "
        f"{n_total} tasks ({n_ai} AI-affected), "
        f"pct={pct:.2f}%, workers={workers:,.0f}, wages=${wages/1e9:.2f}B"
    )
    return summary


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figures = HERE / "figures"
    figures.mkdir(exist_ok=True)

    print("=" * 64)
    print("workforce_sig_meeting — custom charts + methodology")
    print("=" * 64)

    print("\n[1/3] Conversational vs. All Confirmed vs. Ceiling")
    build_conv_allconfirmed_ceiling(results, figures)

    print("\n[2/3] Gap to Ceiling — wages")
    build_gap_to_ceiling_wages(results, figures)

    print("\n[3/3] Methodology breakdown — Chief Executives")
    build_methodology_breakdown(results)

    print("\nDone — figures in figures/ (committed) and results/figures/ (gitignored)")


if __name__ == "__main__":
    main()
