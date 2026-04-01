"""
run.py — Dataset Source Comparison: How do AEI, MCP, and Microsoft differ?

Three-way comparison of each AI scoring source run solo:
  - AEI Cumul. (Both) v4
  - MCP Cumul. v4
  - Microsoft

Plus pairwise analysis: where do the sources agree and disagree?

Lenses:
  1. Economic footprint (total workers/wages/pct per source)
  2. Multi-level ranking analysis (major, minor, broad, occupation)
     with Spearman correlation, top-N overlap, biggest disagreements
  3. Cross-source confidence flags (high/moderate/low agreement)
  4. Exposure tier comparison (how tier assignments shift between sources)
  5. Raw score exploration (auto-aug and pct distributions)
  6. Sensitivity: Time vs Value method, physical toggle

Primary config: Time method, auto-aug ON, national, all physical.
Focus metric: % Tasks Affected (workers/wages in supplementary CSVs).

Usage from project root:
    venv/Scripts/python -m analysis.questions.dataset_source_comparison.run
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

from analysis.config import (
    make_config,
    DEFAULT_OCC_CONFIG,
    run_occ_query,
    ensure_results_dir,
)
from analysis.utils import (
    style_figure,
    save_figure,
    save_csv,
    format_workers,
    format_wages,
    format_pct,
    describe_config,
    generate_pdf,
    _format_bar_label,
    COLORS,
    FONT_FAMILY,
    CATEGORY_PALETTE,
)

HERE = Path(__file__).resolve().parent

# ── Source definitions ───────────────────────────────────────────────────────

SOURCES: dict[str, dict[str, Any]] = {
    "AEI": {
        "datasets": ["AEI Cumul. (Both) v4"],
        "combine": "Average",
        "color": COLORS["aei"],          # slate blue
        "short": "AEI",
    },
    "MCP": {
        "datasets": ["MCP Cumul. v4"],
        "combine": "Average",
        "color": COLORS["mcp"],          # teal green
        "short": "MCP",
    },
    "Microsoft": {
        "datasets": ["Microsoft"],
        "combine": "Average",
        "color": COLORS["microsoft"],    # orange-brown
        "short": "MS",
    },
}

# Combined reference (for context)
COMBINED = {
    "datasets": ["AEI Cumul. (Both) v4", "MCP Cumul. v4", "Microsoft"],
    "combine": "Average",
    "color": COLORS["brand"],
    "short": "Combined",
}

# Exposure tier thresholds (same as job_exposure)
HIGH_EXPOSURE = 60.0
MODERATE_EXPOSURE = 40.0
RESTRUCTURING = 20.0

TIER_LABELS = {
    "high_exposure": "High Exposure (>=60%)",
    "moderate_exposure": "Moderate (40-60%)",
    "restructuring": "Restructuring (20-40%)",
    "low_exposure": "Low Exposure (<20%)",
}
TIER_ORDER = ["high_exposure", "moderate_exposure", "restructuring", "low_exposure"]
TIER_COLORS = {
    "high_exposure": COLORS["negative"],
    "moderate_exposure": COLORS["accent"],
    "restructuring": COLORS["primary"],
    "low_exposure": COLORS["muted"],
}

# Aggregation levels for multi-level analysis
AGG_LEVELS = ["major", "minor", "broad", "occupation"]
AGG_LABELS = {
    "major": "Major Category",
    "minor": "Minor Category",
    "broad": "Broad Occupation",
    "occupation": "Occupation",
}

# Top-N for confidence analysis at each level
CONFIDENCE_TOP_N = {
    "major": 10,
    "minor": 20,
    "broad": 20,
    "occupation": 30,
}

SOURCE_NAMES = ["AEI", "MCP", "Microsoft"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _economy_baseline(geo: str = "nat") -> dict[str, float]:
    """Total employment and wage bill from eco_2025."""
    from backend.compute import load_eco_raw

    eco = load_eco_raw()
    emp_col = f"emp_tot_{geo}_2024"
    wage_col = f"a_med_{geo}_2024"
    occ = eco.drop_duplicates(subset=["title_current"])
    total_emp = float(occ[emp_col].fillna(0).sum())
    total_wages = float((occ[emp_col].fillna(0) * occ[wage_col].fillna(0)).sum())
    return {"total_emp": total_emp, "total_wages": total_wages}


def _run_source(
    datasets: list[str],
    combine: str = "Average",
    agg_level: str = "major",
    top_n: int = 1000,
    **overrides: Any,
) -> dict[str, Any] | None:
    """Run compute pipeline for a source config. Returns df + totals."""
    from backend.compute import get_group_data

    cfg = make_config(
        DEFAULT_OCC_CONFIG,
        selected_datasets=datasets,
        combine_method=combine,
        agg_level=agg_level,
        top_n=top_n,
        search_query="",
        **overrides,
    )
    result = get_group_data(cfg)
    if result is None:
        return None
    df = result["df"].rename(columns={result["group_col"]: "category"})
    return {
        "df": df,
        "total_workers": float(result["total_emp"]),
        "total_wages": float(result["total_wages"]),
        "config": cfg,
    }


def _assign_tier(pct: float) -> str:
    """Assign exposure tier from pct_tasks_affected."""
    if pct >= HIGH_EXPOSURE:
        return "high_exposure"
    elif pct >= MODERATE_EXPOSURE:
        return "moderate_exposure"
    elif pct >= RESTRUCTURING:
        return "restructuring"
    return "low_exposure"


def _merge_sources(
    results: dict[str, dict],
    agg_level: str,
    metric: str = "pct_tasks_affected",
) -> pd.DataFrame:
    """Merge results from all three sources on category column."""
    dfs = []
    for name, r in results.items():
        if r is None:
            continue
        df = r["df"][["category", metric]].copy()
        df = df.rename(columns={metric: name})
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    merged = dfs[0]
    for df in dfs[1:]:
        merged = merged.merge(df, on="category", how="outer")
    return merged


# ── Confidence flags ─────────────────────────────────────────────────────

def _assign_confidence(
    row: pd.Series,
    top_n: int,
    source_ranks: dict[str, pd.Series],
) -> str:
    """Assign a confidence label based on cross-source agreement.

    High: category is in the top_n of all 3 sources
    Moderate: category is in the top_n of exactly 2 sources
    Low: category is in the top_n of only 1 source
    Not ranked: category is not in any source's top_n
    """
    cat = row["category"]
    in_top = sum(
        1 for s in SOURCE_NAMES
        if s in source_ranks and cat in source_ranks[s]
    )
    if in_top == 3:
        return "High"
    elif in_top == 2:
        return "Moderate"
    elif in_top == 1:
        return "Low"
    return "Not ranked"


def _build_confidence_table(
    results: dict[str, dict | None],
    agg_level: str,
    metric: str = "pct_tasks_affected",
    top_n: int = 20,
) -> pd.DataFrame:
    """Build a side-by-side rank table with confidence flags.

    Returns a DataFrame with columns:
      category, AEI_score, AEI_rank, MCP_score, MCP_rank,
      Microsoft_score, Microsoft_rank, confidence, agreement_note
    """
    # Get top-N sets per source for confidence flagging
    source_top_sets: dict[str, set[str]] = {}
    source_dfs: dict[str, pd.DataFrame] = {}
    for sname in SOURCE_NAMES:
        r = results.get(sname)
        if r is None:
            continue
        df = r["df"].copy()
        df[f"rank"] = df[metric].rank(ascending=False, method="min").astype(int)
        source_dfs[sname] = df
        top_cats = set(df.nlargest(top_n, metric)["category"].tolist())
        source_top_sets[sname] = top_cats

    # Union of all categories that appear in any source's top-N
    all_top_cats = set()
    for cats in source_top_sets.values():
        all_top_cats.update(cats)

    if not all_top_cats:
        return pd.DataFrame()

    rows = []
    for cat in sorted(all_top_cats):
        row: dict[str, Any] = {"category": cat}

        scores = {}
        ranks = {}
        for sname in SOURCE_NAMES:
            if sname not in source_dfs:
                row[f"{sname}_score"] = np.nan
                row[f"{sname}_rank"] = np.nan
                continue
            df = source_dfs[sname]
            match = df[df["category"] == cat]
            if match.empty:
                row[f"{sname}_score"] = np.nan
                row[f"{sname}_rank"] = np.nan
            else:
                score = float(match[metric].iloc[0])
                rank = int(match["rank"].iloc[0])
                row[f"{sname}_score"] = score
                row[f"{sname}_rank"] = rank
                scores[sname] = score
                ranks[sname] = rank

        # Confidence flag
        in_top = sum(1 for s in SOURCE_NAMES if cat in source_top_sets.get(s, set()))
        if in_top == 3:
            row["confidence"] = "High"
        elif in_top == 2:
            row["confidence"] = "Moderate"
        else:
            row["confidence"] = "Low"

        # Which source(s) drive the finding
        sources_in = [s for s in SOURCE_NAMES if cat in source_top_sets.get(s, set())]
        sources_out = [s for s in SOURCE_NAMES if cat not in source_top_sets.get(s, set())]
        if in_top == 3:
            row["agreement_note"] = "All sources agree"
        elif in_top == 2:
            row["agreement_note"] = f"Driven by {', '.join(sources_in)}; not in {', '.join(sources_out)} top-{top_n}"
        else:
            row["agreement_note"] = f"Only in {', '.join(sources_in)} top-{top_n}"

        # Directional agreement: are sources that have scores all pointing same direction (high)?
        if len(scores) >= 2:
            vals = list(scores.values())
            mean_score = np.mean(vals)
            spread = max(vals) - min(vals)
            row["mean_score"] = mean_score
            row["score_spread"] = spread
        else:
            row["mean_score"] = list(scores.values())[0] if scores else np.nan
            row["score_spread"] = 0.0

        rows.append(row)

    result_df = pd.DataFrame(rows)
    result_df = result_df.sort_values("mean_score", ascending=False)
    return result_df


def _chart_confidence_summary(
    conf_tables: dict[str, pd.DataFrame],
    top_n_map: dict[str, int],
    subtitle: str,
) -> go.Figure:
    """Stacked bar chart: confidence distribution across aggregation levels."""
    levels = [l for l in AGG_LEVELS if l in conf_tables]
    conf_levels = ["High", "Moderate", "Low"]
    conf_colors = {
        "High": COLORS["secondary"],    # teal — strong agreement
        "Moderate": COLORS["primary"],   # slate — partial agreement
        "Low": COLORS["accent"],         # orange — single-source
    }

    fig = go.Figure()
    for conf in conf_levels:
        counts = []
        for level in levels:
            ct = conf_tables[level]
            counts.append(int((ct["confidence"] == conf).sum()))
        fig.add_trace(go.Bar(
            x=[AGG_LABELS[l] for l in levels],
            y=counts,
            name=conf,
            marker=dict(color=conf_colors[conf]),
            text=[str(c) for c in counts],
            textposition="inside",
            textfont=dict(size=12, color="white", family=FONT_FAMILY),
        ))

    style_figure(fig, "Cross-Source Agreement: How Many Findings Hold Across All Three?",
                 subtitle=subtitle + " | Categories in union of each source's top-N",
                 height=450, width=900)
    fig.update_layout(
        barmode="stack", bargap=0.3,
        yaxis=dict(title=dict(text="Number of Categories")),
        legend=dict(
            orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
            font=dict(size=12),
        ),
    )
    return fig


def _chart_rank_heatmap(
    conf_table: pd.DataFrame,
    agg_level: str,
    top_n: int,
    subtitle: str,
) -> go.Figure:
    """Heatmap of ranks across sources for top categories.

    Rows = categories (sorted by mean score), columns = sources.
    Color intensity = rank (lower rank = darker = better).
    """
    # Take only categories where at least 2 sources have data
    df = conf_table.copy()
    rank_cols = [f"{s}_rank" for s in SOURCE_NAMES]
    df["n_ranked"] = df[rank_cols].notna().sum(axis=1)
    df = df[df["n_ranked"] >= 2].head(min(top_n, 30))

    if df.empty:
        return go.Figure()

    categories = df["category"].tolist()
    z_vals = []
    text_vals = []
    for _, row in df.iterrows():
        row_z = []
        row_t = []
        for s in SOURCE_NAMES:
            rank = row[f"{s}_rank"]
            if pd.isna(rank):
                row_z.append(np.nan)
                row_t.append("—")
            else:
                row_z.append(int(rank))
                row_t.append(f"#{int(rank)}")
        z_vals.append(row_z)
        text_vals.append(row_t)

    # Reverse so top category is at top
    categories = categories[::-1]
    z_vals = z_vals[::-1]
    text_vals = text_vals[::-1]

    fig = go.Figure(go.Heatmap(
        z=z_vals,
        x=SOURCE_NAMES,
        y=categories,
        text=text_vals,
        texttemplate="%{text}",
        textfont=dict(size=11, family=FONT_FAMILY),
        colorscale=[
            [0.0, COLORS["secondary"]],  # low rank (1) = teal = good
            [0.5, "#d4e6f1"],
            [1.0, COLORS["bg_page"]],    # high rank = faded
        ],
        showscale=True,
        colorbar=dict(title="Rank", tickfont=dict(size=10)),
        zmin=1,
        zmax=max(r for row in z_vals for r in row if not (isinstance(r, float) and np.isnan(r))) if z_vals else 100,
    ))

    style_figure(
        fig,
        f"Rank Agreement: {AGG_LABELS[agg_level]}",
        subtitle=subtitle + f" | Top {len(categories)} by mean % Tasks Affected",
        height=max(500, len(categories) * 22 + 150),
        width=700,
    )
    fig.update_layout(
        margin=dict(l=20, r=20),
        yaxis=dict(tickfont=dict(size=10), showgrid=False),
        xaxis=dict(tickfont=dict(size=12), showgrid=False, side="top"),
    )
    return fig


def _chart_score_comparison_dots(
    conf_table: pd.DataFrame,
    agg_level: str,
    top_n: int,
    subtitle: str,
) -> go.Figure:
    """Dot plot showing each source's % Tasks Affected for top categories.

    Each row is a category, with 3 dots (one per source) so you can see
    where they agree and where they diverge.
    """
    df = conf_table.head(min(top_n, 25)).copy()
    if df.empty:
        return go.Figure()

    categories = df["category"].tolist()[::-1]  # reversed for horizontal

    fig = go.Figure()
    for sname in SOURCE_NAMES:
        col = f"{sname}_score"
        vals = []
        for cat in categories:
            row = df[df["category"] == cat]
            if row.empty or pd.isna(row[col].iloc[0]):
                vals.append(None)
            else:
                vals.append(float(row[col].iloc[0]))

        fig.add_trace(go.Scatter(
            x=vals,
            y=categories,
            mode="markers",
            name=sname,
            marker=dict(
                size=10,
                color=SOURCES[sname]["color"],
                symbol="circle",
                line=dict(width=1, color="white"),
            ),
            hovertemplate="%{y}<br>" + sname + ": %{x:.1f}%<extra></extra>",
        ))

    style_figure(
        fig,
        f"Source Scores Side by Side: {AGG_LABELS[agg_level]}",
        subtitle=subtitle + f" | Top {min(top_n, 25)} by mean % Tasks Affected",
        x_title="% Tasks Affected",
        height=max(500, len(categories) * 25 + 150),
        width=900,
    )
    fig.update_layout(
        margin=dict(l=20, r=40),
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"], showline=False, tickfont=dict(size=10)),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"], showline=True),
        legend=dict(
            orientation="h", yanchor="top", y=-0.08, xanchor="center", x=0.5,
            font=dict(size=12),
        ),
    )
    return fig


# ── Chart builders ───────────────────────────────────────────────────────────

def _chart_footprint_comparison(
    source_totals: dict[str, dict],
    eco_base: dict[str, float],
    subtitle: str,
) -> go.Figure:
    """Horizontal bars: % of economy per source (workers and wages)."""
    names = []
    pct_workers = []
    pct_wages = []
    colors = []

    for sname in ["AEI", "MCP", "Microsoft"]:
        r = source_totals[sname]
        names.append(sname)
        pct_workers.append(r["total_workers"] / eco_base["total_emp"] * 100)
        pct_wages.append(r["total_wages"] / eco_base["total_wages"] * 100)
        colors.append(SOURCES[sname]["color"])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=names, x=pct_workers, orientation="h",
        name="Workers",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"  {p:.1f}% ({format_workers(source_totals[n]['total_workers'])})"
              for n, p in zip(names, pct_workers)],
        textposition="outside",
        textfont=dict(size=12, color=COLORS["text"], family=FONT_FAMILY),
        cliponaxis=False,
    ))

    fig.update_yaxes(autorange="reversed")
    style_figure(fig, "AI Exposure by Data Source: Share of US Economy",
                 subtitle=subtitle, height=350, width=900)
    fig.update_layout(
        margin=dict(l=20, r=120),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False, zeroline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=13)),
        bargap=0.3, showlegend=False,
    )
    return fig


def _chart_major_comparison(
    results: dict[str, dict],
    metric: str,
    metric_label: str,
    subtitle: str,
    top_n: int = 15,
) -> go.Figure:
    """Grouped horizontal bars: top N major categories across all three sources."""
    # Get combined ranking for ordering
    combined_cats = set()
    for sname, r in results.items():
        if r is not None:
            top = r["df"].nlargest(top_n, metric)["category"].tolist()
            combined_cats.update(top)

    # Merge and sort by average
    merged = _merge_sources(results, "major", metric)
    source_cols = [s for s in results if s in merged.columns]
    merged["avg"] = merged[source_cols].mean(axis=1)
    merged = merged.nlargest(top_n, "avg")
    categories = merged["category"].tolist()[::-1]  # reversed for horizontal bar

    fig = go.Figure()
    for sname in ["Microsoft", "MCP", "AEI"]:  # reversed so AEI is top in legend
        if sname not in merged.columns:
            continue
        vals = []
        for cat in categories:
            row = merged[merged["category"] == cat]
            vals.append(float(row[sname].iloc[0]) if len(row) and pd.notna(row[sname].iloc[0]) else 0)
        fig.add_trace(go.Bar(
            y=categories, x=vals, orientation="h",
            name=sname,
            marker=dict(color=SOURCES[sname]["color"], line=dict(width=0)),
            text=[_format_bar_label(v) if metric != "pct_tasks_affected" else f"{v:.1f}%" for v in vals],
            textposition="outside",
            textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
            cliponaxis=False,
        ))

    style_figure(fig, f"{metric_label} by Major Category: Source Comparison",
                 subtitle=subtitle, height=max(500, top_n * 35), width=1000)
    fig.update_layout(
        barmode="group",
        margin=dict(l=20, r=100),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False, zeroline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=11)),
        bargap=0.25, bargroupgap=0.08,
        legend=dict(
            orientation="h", yanchor="top", y=-0.08, xanchor="center", x=0.5,
            font=dict(size=12),
        ),
    )
    return fig


def _chart_rank_scatter(
    merged: pd.DataFrame,
    x_source: str,
    y_source: str,
    metric_label: str,
    subtitle: str,
) -> go.Figure:
    """Scatter plot of one source's values vs another's, with diagonal reference."""
    valid = merged.dropna(subset=[x_source, y_source])

    fig = go.Figure()

    # Diagonal reference line
    max_val = max(valid[x_source].max(), valid[y_source].max()) * 1.05
    fig.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val],
        mode="lines",
        line=dict(color=COLORS["grid"], dash="dash", width=1),
        showlegend=False,
    ))

    # Points
    fig.add_trace(go.Scatter(
        x=valid[x_source], y=valid[y_source],
        mode="markers",
        marker=dict(size=6, color=COLORS["primary"], opacity=0.6),
        text=valid["category"],
        hovertemplate="%{text}<br>" + x_source + ": %{x:.1f}%<br>" + y_source + ": %{y:.1f}%<extra></extra>",
        showlegend=False,
    ))

    # Highlight biggest divergers (top 5 by absolute difference)
    valid = valid.copy()
    valid["_diff"] = (valid[y_source] - valid[x_source]).abs()
    top_divergers = valid.nlargest(5, "_diff")
    fig.add_trace(go.Scatter(
        x=top_divergers[x_source], y=top_divergers[y_source],
        mode="markers+text",
        marker=dict(size=9, color=COLORS["accent"], symbol="diamond"),
        text=top_divergers["category"].apply(lambda s: s[:30]),
        textposition="top center",
        textfont=dict(size=9, color=COLORS["accent"], family=FONT_FAMILY),
        showlegend=False,
    ))

    # Correlation annotation
    rho, pval = stats.spearmanr(valid[x_source], valid[y_source])
    fig.add_annotation(
        text=f"Spearman ρ = {rho:.3f}",
        xref="paper", yref="paper", x=0.05, y=0.95,
        showarrow=False, font=dict(size=12, color=COLORS["text"], family=FONT_FAMILY),
        bgcolor=COLORS["bg"], borderpad=4,
    )

    style_figure(fig, f"{metric_label}: {x_source} vs {y_source}",
                 subtitle=subtitle,
                 x_title=f"{x_source} — {metric_label}",
                 y_title=f"{y_source} — {metric_label}",
                 height=650, width=700)
    return fig


def _chart_tier_comparison(
    tier_counts: pd.DataFrame,
    subtitle: str,
) -> go.Figure:
    """Grouped bar chart showing tier distribution across sources."""
    fig = go.Figure()

    for sname in ["AEI", "MCP", "Microsoft"]:
        if sname not in tier_counts.columns:
            continue
        fig.add_trace(go.Bar(
            x=[TIER_LABELS[t] for t in TIER_ORDER],
            y=[tier_counts.loc[t, sname] if t in tier_counts.index else 0 for t in TIER_ORDER],
            name=sname,
            marker=dict(color=SOURCES[sname]["color"]),
            text=[str(int(tier_counts.loc[t, sname])) if t in tier_counts.index else "0" for t in TIER_ORDER],
            textposition="outside",
            textfont=dict(size=11, family=FONT_FAMILY),
        ))

    style_figure(fig, "Exposure Tier Distribution by Source",
                 subtitle=subtitle, height=500, width=900)
    fig.update_layout(
        barmode="group", bargap=0.2, bargroupgap=0.05,
        xaxis=dict(tickfont=dict(size=10)),
        yaxis=dict(title=dict(text="Number of Occupations")),
        legend=dict(
            orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
            font=dict(size=12),
        ),
    )
    return fig


def _chart_tier_shift_heatmap(
    shift_matrix: pd.DataFrame,
    source_a: str,
    source_b: str,
    subtitle: str,
) -> go.Figure:
    """Heatmap showing how occupations move between tiers across two sources."""
    tier_labels = [TIER_LABELS[t] for t in TIER_ORDER]
    z_vals = []
    text_vals = []
    for row_tier in TIER_ORDER:
        row_z = []
        row_t = []
        for col_tier in TIER_ORDER:
            val = shift_matrix.loc[row_tier, col_tier] if row_tier in shift_matrix.index and col_tier in shift_matrix.columns else 0
            row_z.append(val)
            row_t.append(str(int(val)) if val > 0 else "")
        z_vals.append(row_z)
        text_vals.append(row_t)

    fig = go.Figure(go.Heatmap(
        z=z_vals, x=tier_labels, y=tier_labels,
        text=text_vals, texttemplate="%{text}",
        colorscale=[[0, COLORS["bg"]], [0.5, "#d4e6f1"], [1, COLORS["primary"]]],
        showscale=False,
    ))

    style_figure(fig, f"Tier Shift: {source_a} → {source_b}",
                 subtitle=subtitle,
                 x_title=f"{source_b} tier",
                 y_title=f"{source_a} tier",
                 height=500, width=600)
    fig.update_yaxes(autorange="reversed")
    return fig


def _chart_divergence_bars(
    top_div: pd.DataFrame,
    source_a: str,
    source_b: str,
    subtitle: str,
    top_n: int = 20,
) -> go.Figure:
    """Paired horizontal bars showing the biggest pct_tasks_affected disagreements."""
    plot_df = top_div.head(top_n).copy()
    categories = plot_df["category"].tolist()[::-1]

    fig = go.Figure()
    for sname, col_name in [(source_a, source_a), (source_b, source_b)]:
        vals = [float(plot_df[plot_df["category"] == c][col_name].iloc[0]) for c in categories]
        fig.add_trace(go.Bar(
            y=categories, x=vals, orientation="h",
            name=sname,
            marker=dict(color=SOURCES[sname]["color"]),
            text=[f"{v:.1f}%" for v in vals],
            textposition="outside",
            textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
            cliponaxis=False,
        ))

    style_figure(fig, f"Biggest Disagreements: {source_a} vs {source_b}",
                 subtitle=subtitle + " | Sorted by absolute difference",
                 height=max(500, top_n * 30), width=1000)
    fig.update_layout(
        barmode="group", bargap=0.2, bargroupgap=0.05,
        margin=dict(l=20, r=80),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False, zeroline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        legend=dict(
            orientation="h", yanchor="top", y=-0.08, xanchor="center", x=0.5,
            font=dict(size=12),
        ),
    )
    return fig


def _chart_physical_split(
    phys_data: dict[str, dict[str, dict]],
    eco_bases: dict[str, dict[str, float]],
    subtitle: str,
) -> go.Figure:
    """Grouped bars: % economy by source across physical modes."""
    modes = ["all", "exclude", "only"]
    mode_labels = ["All Tasks", "Non-Physical Only", "Physical Only"]

    fig = go.Figure()
    for sname in ["AEI", "MCP", "Microsoft"]:
        pcts = []
        for mode in modes:
            r = phys_data[sname].get(mode)
            base = eco_bases[mode]
            if r is not None and base["total_emp"] > 0:
                pcts.append(r["total_workers"] / base["total_emp"] * 100)
            else:
                pcts.append(0)
        fig.add_trace(go.Bar(
            x=mode_labels, y=pcts,
            name=sname,
            marker=dict(color=SOURCES[sname]["color"]),
            text=[f"{p:.1f}%" for p in pcts],
            textposition="outside",
            textfont=dict(size=11, family=FONT_FAMILY),
        ))

    style_figure(fig, "AI Exposure by Physical Task Filter",
                 subtitle=subtitle, height=500, width=800)
    fig.update_layout(
        barmode="group", bargap=0.3, bargroupgap=0.05,
        yaxis=dict(title=dict(text="% of Workers Affected")),
        legend=dict(
            orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
            font=dict(size=12),
        ),
    )
    return fig


def _chart_sensitivity_dots(
    sens_data: dict[str, dict[str, float]],
    subtitle: str,
) -> go.Figure:
    """Dot plot showing % economy across toggle variants per source."""
    variants = list(next(iter(sens_data.values())).keys())

    fig = go.Figure()
    for sname in ["AEI", "MCP", "Microsoft"]:
        vals = [sens_data[sname][v] for v in variants]
        fig.add_trace(go.Scatter(
            x=vals, y=variants,
            mode="markers+text",
            name=sname,
            marker=dict(size=12, color=SOURCES[sname]["color"], symbol="circle"),
            text=[f"{v:.1f}%" for v in vals],
            textposition="middle right",
            textfont=dict(size=10, color=SOURCES[sname]["color"], family=FONT_FAMILY),
        ))

    style_figure(fig, "Sensitivity: % Workers Affected Across Toggles",
                 subtitle=subtitle,
                 x_title="% of US Workers Affected",
                 height=400, width=900)
    fig.update_layout(
        margin=dict(l=200, r=80),
        yaxis=dict(tickfont=dict(size=11)),
        legend=dict(
            orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5,
            font=dict(size=12),
        ),
    )
    return fig


# ── Main pipeline ────────────────────────────────────────────────────────────

def main() -> None:
    results_dir = ensure_results_dir(HERE)
    figures_dir = HERE / "figures"
    figures_dir.mkdir(exist_ok=True)

    PRIMARY_SUBTITLE = "Time method | Auto-aug ON | National | All tasks"

    print("=" * 60)
    print("Dataset Source Comparison")
    print("=" * 60)

    # ── 1. Economy baseline ──────────────────────────────────────────────────
    print("\n[1/10] Loading economy baseline...")
    eco_base = _economy_baseline("nat")
    print(f"  Total employment: {format_workers(eco_base['total_emp'])}")
    print(f"  Total wage bill:  {format_wages(eco_base['total_wages'])}")

    # ── 2. Run all sources at all aggregation levels ─────────────────────────
    print("\n[2/10] Running all sources at all aggregation levels...")
    # Structure: source_results[agg_level][source_name] = result dict
    source_results: dict[str, dict[str, dict | None]] = {}

    for agg in AGG_LEVELS:
        source_results[agg] = {}
        for sname, sdef in SOURCES.items():
            r = _run_source(sdef["datasets"], sdef["combine"], agg)
            source_results[agg][sname] = r
        n_valid = sum(1 for r in source_results[agg].values() if r is not None)
        print(f"  {AGG_LABELS[agg]}: {n_valid}/3 sources returned data")

    # Convenience aliases for backward compat
    source_results_major = source_results["major"]
    source_results_occ = source_results["occupation"]

    # ── 3. Economy footprint ─────────────────────────────────────────────────
    print("\n[3/10] Economy footprint...")
    for sname in SOURCE_NAMES:
        r = source_results_major[sname]
        if r:
            pct_w = r["total_workers"] / eco_base["total_emp"] * 100
            print(f"  {sname}: {pct_w:.1f}% workers ({format_workers(r['total_workers'])}), "
                  f"wages={format_wages(r['total_wages'])}")

    fig_footprint = _chart_footprint_comparison(source_results_major, eco_base, PRIMARY_SUBTITLE)
    save_figure(fig_footprint, results_dir / "figures" / "footprint_comparison.png")

    rows = []
    for sname in SOURCE_NAMES:
        r = source_results_major[sname]
        if r:
            rows.append({
                "Source": sname,
                "Datasets": ", ".join(SOURCES[sname]["datasets"]),
                "Workers Affected": r["total_workers"],
                "% Workers": r["total_workers"] / eco_base["total_emp"] * 100,
                "Wages Affected": r["total_wages"],
                "% Wages": r["total_wages"] / eco_base["total_wages"] * 100,
            })
    save_csv(pd.DataFrame(rows), results_dir / "economy_totals.csv")

    # ── 4. Multi-level grouped bar charts ────────────────────────────────────
    print("\n[4/10] Multi-level category comparison charts...")
    for agg in AGG_LEVELS:
        if agg == "occupation":
            continue  # too many categories for grouped bars
        sr = source_results[agg]
        for metric, label in [
            ("pct_tasks_affected", "% Tasks Affected"),
            ("workers_affected", "Workers Affected"),
        ]:
            top_n = min(15, CONFIDENCE_TOP_N.get(agg, 15))
            fig = _chart_major_comparison(sr, metric, label,
                                          f"{PRIMARY_SUBTITLE} | {AGG_LABELS[agg]}",
                                          top_n=top_n)
            save_figure(fig, results_dir / "figures" / f"{agg}_{metric}.png")

        # CSVs per source at each level
        for sname, r in sr.items():
            if r is not None:
                save_csv(r["df"], results_dir / f"{agg}_{sname.lower()}.csv")

    # ── 5. Pairwise scatter + rank correlation (all levels) ──────────────────
    print("\n[5/10] Pairwise ranking analysis (all levels)...")
    pairs = [("AEI", "MCP"), ("AEI", "Microsoft"), ("MCP", "Microsoft")]
    all_corr_rows: list[dict[str, Any]] = []

    for agg in AGG_LEVELS:
        sr = source_results[agg]
        merged_pct = _merge_sources(sr, agg, "pct_tasks_affected")

        for sa, sb in pairs:
            valid = merged_pct.dropna(subset=[sa, sb])
            if len(valid) < 3:
                continue

            rho, pval = stats.spearmanr(valid[sa], valid[sb])
            all_corr_rows.append({
                "Level": AGG_LABELS[agg],
                "Pair": f"{sa} vs {sb}",
                "Spearman_rho": rho,
                "p_value": pval,
                "n_categories": len(valid),
            })

            # Scatter chart (for major, minor, broad — not occupation since we already have it)
            fig = _chart_rank_scatter(merged_pct, sa, sb, "% Tasks Affected",
                                      f"{PRIMARY_SUBTITLE} | {AGG_LABELS[agg]}")
            save_figure(fig, results_dir / "figures" / f"scatter_{sa.lower()}_vs_{sb.lower()}_{agg}.png")

            # Top-N overlap
            top_n = CONFIDENCE_TOP_N.get(agg, 20)
            top_a = set(sr[sa]["df"].nlargest(top_n, "pct_tasks_affected")["category"].tolist()) if sr[sa] else set()
            top_b = set(sr[sb]["df"].nlargest(top_n, "pct_tasks_affected")["category"].tolist()) if sr[sb] else set()
            overlap = top_a & top_b
            print(f"  {AGG_LABELS[agg]} - {sa} vs {sb}: rho={rho:.3f}, top-{top_n} overlap={len(overlap)}/{top_n}")

            # Biggest disagreements
            valid = valid.copy()
            valid["abs_diff"] = (valid[sa] - valid[sb]).abs()
            valid["diff"] = valid[sa] - valid[sb]
            top_div = valid.nlargest(20, "abs_diff")
            save_csv(top_div[["category", sa, sb, "diff", "abs_diff"]],
                     results_dir / f"divergence_{sa.lower()}_vs_{sb.lower()}_{agg}.csv")

            # Divergence bar chart for major and minor
            if agg in ("major", "minor"):
                fig = _chart_divergence_bars(top_div, sa, sb,
                                             f"{PRIMARY_SUBTITLE} | {AGG_LABELS[agg]}",
                                             top_n=min(20, len(top_div)))
                save_figure(fig, results_dir / "figures" / f"divergence_{sa.lower()}_vs_{sb.lower()}_{agg}.png")

    save_csv(pd.DataFrame(all_corr_rows), results_dir / "rank_correlations.csv")

    # ── 6. Cross-source confidence analysis (all levels) ─────────────────────
    print("\n[6/10] Cross-source confidence analysis...")
    conf_tables: dict[str, pd.DataFrame] = {}

    for agg in AGG_LEVELS:
        sr = source_results[agg]
        top_n = CONFIDENCE_TOP_N.get(agg, 20)
        ct = _build_confidence_table(sr, agg, "pct_tasks_affected", top_n=top_n)
        if ct.empty:
            continue
        conf_tables[agg] = ct

        # Save the confidence table CSV
        save_csv(ct, results_dir / f"confidence_{agg}.csv", float_format="%.2f")

        # Count confidence levels
        for conf_level in ["High", "Moderate", "Low"]:
            n = int((ct["confidence"] == conf_level).sum())
            if n > 0:
                print(f"  {AGG_LABELS[agg]} top-{top_n}: {conf_level}={n}", end="  ")
        print()

        # Rank heatmap
        fig = _chart_rank_heatmap(ct, agg, top_n, PRIMARY_SUBTITLE)
        save_figure(fig, results_dir / "figures" / f"rank_heatmap_{agg}.png")

        # Score dot plot
        fig = _chart_score_comparison_dots(ct, agg, top_n, PRIMARY_SUBTITLE)
        save_figure(fig, results_dir / "figures" / f"score_dots_{agg}.png")

    # Confidence summary chart across levels
    if conf_tables:
        fig = _chart_confidence_summary(conf_tables, CONFIDENCE_TOP_N, PRIMARY_SUBTITLE)
        save_figure(fig, results_dir / "figures" / "confidence_summary.png")

    # ── 7. Exposure tier analysis (occupation level) ─────────────────────────
    print("\n[7/10] Exposure tier analysis...")
    tier_dfs: dict[str, pd.DataFrame] = {}
    tier_counts_data: dict[str, dict[str, int]] = {}

    for sname, r in source_results_occ.items():
        if r is None:
            continue
        df = r["df"].copy()
        df["tier"] = df["pct_tasks_affected"].apply(_assign_tier)
        tier_dfs[sname] = df
        counts = df["tier"].value_counts().to_dict()
        tier_counts_data[sname] = counts
        print(f"  {sname}: " + ", ".join(f"{TIER_LABELS[t]}={counts.get(t, 0)}" for t in TIER_ORDER))

    tier_counts_df = pd.DataFrame(tier_counts_data).reindex(TIER_ORDER).fillna(0).astype(int)
    save_csv(tier_counts_df.reset_index().rename(columns={"index": "Tier"}),
             results_dir / "tier_counts.csv")

    fig_tiers = _chart_tier_comparison(tier_counts_df, PRIMARY_SUBTITLE)
    save_figure(fig_tiers, results_dir / "figures" / "tier_comparison.png")

    # Tier shift heatmaps for each pair
    for sa, sb in pairs:
        if sa not in tier_dfs or sb not in tier_dfs:
            continue
        merged_tiers = tier_dfs[sa][["category", "tier"]].merge(
            tier_dfs[sb][["category", "tier"]], on="category", suffixes=(f"_{sa}", f"_{sb}")
        )
        shift = pd.crosstab(merged_tiers[f"tier_{sa}"], merged_tiers[f"tier_{sb}"])
        for t in TIER_ORDER:
            if t not in shift.index:
                shift.loc[t] = 0
            if t not in shift.columns:
                shift[t] = 0
        shift = shift.reindex(index=TIER_ORDER, columns=TIER_ORDER, fill_value=0)

        save_csv(shift.reset_index().rename(columns={"index": f"{sa}_tier"}),
                 results_dir / f"tier_shift_{sa.lower()}_vs_{sb.lower()}.csv")

        fig = _chart_tier_shift_heatmap(shift, sa, sb, PRIMARY_SUBTITLE)
        save_figure(fig, results_dir / "figures" / f"tier_shift_{sa.lower()}_vs_{sb.lower()}.png")

    for sname, df in tier_dfs.items():
        save_csv(df[["category", "pct_tasks_affected", "workers_affected", "wages_affected", "tier"]],
                 results_dir / f"occupations_tiered_{sname.lower()}.csv")

    # ── 8. Raw score exploration ─────────────────────────────────────────────
    print("\n[8/10] Raw score exploration...")
    from backend.compute import get_explorer_occupations

    explorer = get_explorer_occupations()
    if explorer is not None:
        exp_df = explorer["df"] if isinstance(explorer, dict) else explorer
        cols = exp_df.columns.tolist() if hasattr(exp_df, 'columns') else []
        auto_cols = [c for c in cols if "auto_aug" in c.lower()]
        pct_cols = [c for c in cols if "pct_norm" in c.lower()]
        print(f"  Explorer auto-aug columns: {auto_cols[:8]}...")
        print(f"  Explorer pct_norm columns: {pct_cols[:8]}...")

    # ── 9. Sensitivity analysis ──────────────────────────────────────────────
    print("\n[9/10] Sensitivity analysis...")

    # 9a. Time vs Value method
    sens_data: dict[str, dict[str, float]] = {}
    toggle_variants = [
        ("Time + Aug ON", {"method": "freq", "use_auto_aug": True}),
        ("Time + Aug OFF", {"method": "freq", "use_auto_aug": False}),
        ("Value + Aug ON", {"method": "imp", "use_auto_aug": True}),
        ("Value + Aug OFF", {"method": "imp", "use_auto_aug": False}),
    ]

    for sname, sdef in SOURCES.items():
        sens_data[sname] = {}
        for vlabel, voverrides in toggle_variants:
            r = _run_source(sdef["datasets"], sdef["combine"], "major", **voverrides)
            if r:
                pct = r["total_workers"] / eco_base["total_emp"] * 100
                sens_data[sname][vlabel] = pct
            else:
                sens_data[sname][vlabel] = 0

    sens_rows = []
    for vlabel, _ in toggle_variants:
        row = {"Variant": vlabel}
        for sname in SOURCE_NAMES:
            row[f"{sname} (% workers)"] = sens_data[sname][vlabel]
        sens_rows.append(row)
    save_csv(pd.DataFrame(sens_rows), results_dir / "sensitivity_toggles.csv")

    fig_sens = _chart_sensitivity_dots(sens_data, "National | All tasks")
    save_figure(fig_sens, results_dir / "figures" / "sensitivity_toggles.png")

    # 9b. Physical toggle
    print("  Physical toggle...")
    phys_modes = ["all", "exclude", "only"]
    phys_data: dict[str, dict[str, dict | None]] = {s: {} for s in SOURCES}
    phys_eco_bases: dict[str, dict[str, float]] = {}

    for mode in phys_modes:
        phys_eco_bases[mode] = eco_base
        for sname, sdef in SOURCES.items():
            r = _run_source(sdef["datasets"], sdef["combine"], "major", physical_mode=mode)
            phys_data[sname][mode] = r

    fig_phys = _chart_physical_split(phys_data, phys_eco_bases, PRIMARY_SUBTITLE)
    save_figure(fig_phys, results_dir / "figures" / "physical_split.png")

    phys_rows = []
    mode_labels = {"all": "All Tasks", "exclude": "Non-Physical Only", "only": "Physical Only"}
    for mode in phys_modes:
        row = {"Physical Filter": mode_labels[mode]}
        for sname in SOURCE_NAMES:
            r = phys_data[sname].get(mode)
            if r:
                row[f"{sname} Workers"] = r["total_workers"]
                row[f"{sname} % Workers"] = r["total_workers"] / eco_base["total_emp"] * 100
            else:
                row[f"{sname} Workers"] = 0
                row[f"{sname} % Workers"] = 0
        phys_rows.append(row)
    save_csv(pd.DataFrame(phys_rows), results_dir / "physical_comparison.csv")

    # 9c. Rank stability across method toggles
    print("  Rank stability across method toggles...")
    for sname, sdef in SOURCES.items():
        r_time = _run_source(sdef["datasets"], sdef["combine"], "major", method="freq")
        r_value = _run_source(sdef["datasets"], sdef["combine"], "major", method="imp")
        if r_time and r_value:
            top_time = set(r_time["df"].nlargest(10, "workers_affected")["category"].tolist())
            top_value = set(r_value["df"].nlargest(10, "workers_affected")["category"].tolist())
            overlap = top_time & top_value
            print(f"    {sname}: {len(overlap)}/10 top major categories stable across Time/Value")

    # ── 10. Copy key figures and generate PDF ────────────────────────────────
    print("\n[10/10] Copying key figures and generating PDF...")
    key_figures = [
        # Footprint
        "footprint_comparison.png",
        # Multi-level pct_tasks_affected
        "major_pct_tasks_affected.png",
        "minor_pct_tasks_affected.png",
        "broad_pct_tasks_affected.png",
        # Scatter (major + occupation)
        "scatter_aei_vs_mcp_major.png",
        "scatter_aei_vs_mcp_occupation.png",
        "scatter_mcp_vs_microsoft_major.png",
        "scatter_mcp_vs_microsoft_occupation.png",
        # Divergence
        "divergence_aei_vs_mcp_major.png",
        "divergence_mcp_vs_microsoft_major.png",
        # Confidence
        "confidence_summary.png",
        "rank_heatmap_major.png",
        "rank_heatmap_minor.png",
        "rank_heatmap_broad.png",
        "score_dots_major.png",
        "score_dots_minor.png",
        # Tiers
        "tier_comparison.png",
        "tier_shift_aei_vs_mcp.png",
        # Sensitivity
        "sensitivity_toggles.png",
        "physical_split.png",
    ]
    for fname in key_figures:
        src = results_dir / "figures" / fname
        if src.exists():
            shutil.copy2(src, figures_dir / fname)
            print(f"  Copied {fname}")
        else:
            print(f"  SKIP (not found): {fname}")

    # Generate PDF
    md_path = HERE / "dataset_source_comparison.md"
    if md_path.exists():
        pdf_path = results_dir / "dataset_source_comparison.pdf"
        try:
            generate_pdf(md_path, pdf_path)
            print(f"  PDF: {pdf_path}")
        except Exception as e:
            print(f"  PDF generation failed: {e}")

    print("\n" + "=" * 60)
    print("Done! Results in:", results_dir)
    print("Key figures in:", figures_dir)
    print("=" * 60)


if __name__ == "__main__":
    main()
