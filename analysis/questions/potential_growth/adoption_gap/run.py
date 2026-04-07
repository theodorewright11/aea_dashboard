"""
run.py — Potential Growth: Adoption Gap

Where is confirmed AI usage furthest below the demonstrated capability ceiling,
across both occupations and work activities?

Gap = all_ceiling − all_confirmed for pct_tasks_affected, workers_affected,
wages_affected. Surfaces standouts at every aggregation level:
  Occupations: major, minor, broad, occupation
  Work activities: GWA, IWA, DWA

Also runs cross-config robustness (major level, all 5 configs) and a trend
analysis showing how the confirmed workers count has grown relative to ceiling.

Figures (key ones copied to figures/):
  confirmed_vs_ceiling_scatter.png  — Scatter: confirmed vs ceiling per occupation
  occ_gap_major.png                 — Major categories: confirmed vs ceiling dumbbell
  occ_gap_minor.png                 — Top 20 minor categories by workers_affected gap
  occ_gap_occupation.png            — Top 30 occupations by workers_affected gap
  wa_gap_gwa.png                    — GWA level: confirmed vs ceiling (dumbbell)
  wa_gap_iwa.png                    — Top 20 IWAs by workers_affected gap
  gap_trend.png                     — Confirmed workers growth vs ceiling baseline
  config_robustness.png             — Major-level pct across all 5 configs (heatmap)

Run from project root:
    venv/Scripts/python -m analysis.questions.potential_growth.adoption_gap.run
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
    ANALYSIS_CONFIG_SERIES,
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

OCC_LEVELS = ["major", "minor", "broad", "occupation"]
WA_LEVELS = ["gwa", "iwa", "dwa"]

# Column rename map: agg_level → raw column name from get_group_data
AGG_COL_MAP = {
    "major": "major_occ_category",
    "minor": "minor_occ_category",
    "broad": "broad_occ",
    "occupation": "title_current",
}

METRICS = ["pct_tasks_affected", "workers_affected", "wages_affected"]
METRIC_LABELS = {
    "pct_tasks_affected": "% Tasks Affected",
    "workers_affected": "Workers Affected",
    "wages_affected": "Wages Affected ($)",
}


# ── Data helpers ──────────────────────────────────────────────────────────────

def get_occ_data(dataset_name: str, agg_level: str) -> pd.DataFrame:
    """Get occupation-hierarchy data for one dataset at one aggregation level."""
    from backend.compute import get_group_data

    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": "nat",
        "agg_level": agg_level,
        "sort_by": "Workers Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    if data is None:
        return pd.DataFrame()

    df = data["df"]
    raw_col = AGG_COL_MAP[agg_level]
    gc = data.get("group_col", raw_col)
    rename_col = gc if gc in df.columns else raw_col
    if rename_col not in df.columns:
        return pd.DataFrame()
    df = df.rename(columns={rename_col: "category"})
    df["dataset"] = dataset_name
    df["agg_level"] = agg_level
    cols = ["category", "pct_tasks_affected", "workers_affected", "wages_affected",
            "dataset", "agg_level"]
    return df[[c for c in cols if c in df.columns]].copy()


def get_wa_data(dataset_name: str, level: str = "iwa") -> pd.DataFrame:
    """Get work activity data for one pre-combined dataset at one WA level."""
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
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["dataset"] = dataset_name
    df["level"] = level
    cols = ["category", "pct_tasks_affected", "workers_affected", "wages_affected",
            "dataset", "level"]
    return df[[c for c in cols if c in df.columns]].copy()


def compute_gap(confirmed_df: pd.DataFrame, ceiling_df: pd.DataFrame,
                key_col: str = "category") -> pd.DataFrame:
    """Merge confirmed and ceiling DataFrames and compute gap for all metrics."""
    merged = confirmed_df.merge(
        ceiling_df, on=key_col, how="outer", suffixes=("_confirmed", "_ceiling")
    )
    for m in METRICS:
        c_col = f"{m}_confirmed"
        k_col = f"{m}_ceiling"
        if c_col not in merged.columns:
            merged[c_col] = 0.0
        if k_col not in merged.columns:
            merged[k_col] = 0.0
        merged[c_col] = merged[c_col].fillna(0.0)
        merged[k_col] = merged[k_col].fillna(0.0)
        merged[f"{m}_gap"] = merged[k_col] - merged[c_col]
    return merged


# ── Figure builders ────────────────────────────────────────────────────────────

def _dumbbell(gap_df: pd.DataFrame, metric: str, level_label: str,
              top_n: int = 23, sort_by_gap: bool = True) -> go.Figure:
    """Dumbbell chart: confirmed vs ceiling per category."""
    gap_col = f"{metric}_gap"
    confirmed_col = f"{metric}_confirmed"
    ceiling_col = f"{metric}_ceiling"

    df = gap_df.copy()
    if sort_by_gap:
        df = df.sort_values(gap_col, ascending=False).head(top_n)
    df = df.sort_values(gap_col, ascending=True)  # ascending for horiz bars

    categories = df["category"].tolist()
    confirmed_vals = df[confirmed_col].tolist()
    ceiling_vals = df[ceiling_col].tolist()

    # Format labels
    def _fmt(v: float) -> str:
        if metric == "pct_tasks_affected":
            return f"{v:.1f}%"
        if metric == "workers_affected":
            return format_workers(v)
        return f"${v / 1e9:.2f}B" if v >= 1e9 else f"${v / 1e6:.1f}M"

    fig = go.Figure()

    # Connector lines (shapes)
    for i, cat in enumerate(categories):
        fig.add_shape(
            type="line",
            x0=confirmed_vals[i], x1=ceiling_vals[i],
            y0=i, y1=i,
            line=dict(color=COLORS["grid"], width=2),
            layer="below",
        )

    # Confirmed dots
    fig.add_trace(go.Scatter(
        x=confirmed_vals,
        y=categories,
        mode="markers+text",
        name="Confirmed Usage",
        marker=dict(color=COLORS["primary"], size=10, line=dict(width=1, color=COLORS["bg"])),
        text=[_fmt(v) for v in confirmed_vals],
        textposition="middle left",
        textfont=dict(size=9, color=COLORS["primary"], family=FONT_FAMILY),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Confirmed: %{x:,.0f}<extra></extra>",
    ))

    # Ceiling dots
    fig.add_trace(go.Scatter(
        x=ceiling_vals,
        y=categories,
        mode="markers+text",
        name="Capability Ceiling",
        marker=dict(color=COLORS["secondary"], size=10, line=dict(width=1, color=COLORS["bg"])),
        text=[_fmt(v) for v in ceiling_vals],
        textposition="middle right",
        textfont=dict(size=9, color=COLORS["secondary"], family=FONT_FAMILY),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Ceiling: %{x:,.0f}<extra></extra>",
    ))

    chart_h = max(500, len(categories) * 32 + 200)
    style_figure(
        fig,
        f"Confirmed vs Ceiling — {level_label}",
        subtitle=f"Primary: All Confirmed | Ceiling: All Sources | {METRIC_LABELS[metric]}",
        x_title=METRIC_LABELS[metric],
        height=chart_h,
        show_legend=True,
    )
    fig.update_layout(
        margin=dict(l=20, r=120, t=80, b=120),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   tickfont=dict(size=9, color=COLORS["muted"])),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        legend=dict(
            orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        ),
    )
    return fig


def _gap_bar(gap_df: pd.DataFrame, metric: str, level_label: str,
             top_n: int = 20) -> go.Figure:
    """Simple horizontal bar: gap magnitude per category."""
    gap_col = f"{metric}_gap"
    df = gap_df.sort_values(gap_col, ascending=False).head(top_n)
    df = df.sort_values(gap_col, ascending=True)

    def _fmt(v: float) -> str:
        if metric == "pct_tasks_affected":
            return f"+{v:.1f}pp"
        if metric == "workers_affected":
            return format_workers(v)
        return f"${v / 1e9:.2f}B" if v >= 1e9 else f"${v / 1e6:.1f}M"

    fig = go.Figure(go.Bar(
        y=df["category"],
        x=df[gap_col],
        orientation="h",
        marker=dict(color=COLORS["accent"], line=dict(width=0)),
        text=[_fmt(v) for v in df[gap_col]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Gap: %{x:,.0f}<extra></extra>",
    ))
    chart_h = max(450, len(df) * 32 + 200)
    style_figure(
        fig,
        f"Largest Adoption Gaps — {level_label}",
        subtitle=f"Gap = Ceiling − Confirmed | {METRIC_LABELS[metric]} | Top {top_n}",
        x_title=None,
        height=chart_h,
        show_legend=False,
    )
    fig.update_layout(
        margin=dict(l=20, r=100, t=80, b=80),
        xaxis=dict(showgrid=False, showticklabels=False, showline=False, zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        bargap=0.25,
    )
    return fig


def _confirmed_vs_ceiling_scatter(occ_gap_df: pd.DataFrame) -> go.Figure:
    """Scatter: confirmed pct (x) vs ceiling pct (y) per occupation."""
    df = occ_gap_df.dropna(subset=["pct_tasks_affected_confirmed", "pct_tasks_affected_ceiling"])
    df = df[df["pct_tasks_affected_ceiling"] > 0]

    # Color by gap magnitude
    gap_vals = df["pct_tasks_affected_gap"].clip(lower=0)
    max_gap = gap_vals.max() if gap_vals.max() > 0 else 1

    fig = go.Figure()

    # Points
    fig.add_trace(go.Scatter(
        x=df["pct_tasks_affected_confirmed"],
        y=df["pct_tasks_affected_ceiling"],
        mode="markers",
        name="Occupation",
        marker=dict(
            color=gap_vals,
            colorscale=[[0, COLORS["primary"]], [0.5, COLORS["secondary"]], [1.0, COLORS["accent"]]],
            cmin=0,
            cmax=max_gap,
            size=6,
            opacity=0.65,
            line=dict(width=0.5, color=COLORS["bg"]),
            colorbar=dict(
                title=dict(text="Gap (pp)", font=dict(size=10, family=FONT_FAMILY)),
                thickness=12,
                len=0.6,
                tickfont=dict(size=9, family=FONT_FAMILY),
            ),
        ),
        text=df["category"],
        hovertemplate="<b>%{text}</b><br>Confirmed: %{x:.1f}%<br>Ceiling: %{y:.1f}%<extra></extra>",
    ))

    # y = x reference line (confirmed = ceiling, zero gap)
    max_val = max(df["pct_tasks_affected_ceiling"].max(), df["pct_tasks_affected_confirmed"].max())
    fig.add_trace(go.Scatter(
        x=[0, max_val],
        y=[0, max_val],
        mode="lines",
        name="No gap (y = x)",
        line=dict(color=COLORS["muted"], dash="dot", width=1.5),
        hoverinfo="skip",
    ))

    style_figure(
        fig,
        "Confirmed vs Ceiling — Every Occupation",
        subtitle="Points above y=x line have unrealized adoption potential | Color = gap magnitude",
        x_title="% Tasks Affected (Confirmed)",
        y_title="% Tasks Affected (Ceiling)",
        height=700, width=1000,
        show_legend=True,
    )
    fig.update_layout(
        margin=dict(l=60, r=40, t=80, b=100),
        legend=dict(
            orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        ),
    )
    return fig


def _config_robustness_heatmap(robustness_df: pd.DataFrame) -> go.Figure:
    """Heatmap: major category × config, showing pct_tasks_affected."""
    pivot = robustness_df.pivot_table(
        index="category", columns="config_label",
        values="pct_tasks_affected", aggfunc="mean"
    )
    # Sort categories by all_confirmed value
    confirmed_label = ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]
    if confirmed_label in pivot.columns:
        pivot = pivot.sort_values(confirmed_label, ascending=False)

    col_order = [ANALYSIS_CONFIG_LABELS[k] for k in
                 ["all_confirmed", "human_conversation", "agentic_confirmed",
                  "all_ceiling", "agentic_ceiling"]
                 if ANALYSIS_CONFIG_LABELS[k] in pivot.columns]
    pivot = pivot[[c for c in col_order if c in pivot.columns]]

    z = pivot.values
    fig = go.Figure(go.Heatmap(
        z=z,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0, "#f7f7f4"], [0.5, COLORS["primary"]], [1.0, COLORS["negative"]]],
        text=np.round(z, 1),
        texttemplate="%{text:.1f}%",
        hovertemplate="<b>%{y}</b><br>%{x}<br>%{z:.1f}%<extra></extra>",
        showscale=True,
        colorbar=dict(
            title=dict(text="% Tasks Affected", font=dict(size=10, family=FONT_FAMILY)),
            thickness=12,
            tickfont=dict(size=9, family=FONT_FAMILY),
        ),
    ))
    chart_h = max(600, len(pivot) * 28 + 200)
    style_figure(
        fig,
        "Exposure Across All Five Configs — Major Category",
        subtitle="Shows how different measurement approaches affect the adoption gap picture",
        height=chart_h, width=1100,
        show_legend=False,
    )
    fig.update_layout(
        margin=dict(l=20, r=40, t=80, b=120),
        xaxis=dict(tickangle=-20, tickfont=dict(size=10, family=FONT_FAMILY)),
        yaxis=dict(autorange="reversed", tickfont=dict(size=10, family=FONT_FAMILY)),
    )
    return fig


def _gap_trend(trend_df: pd.DataFrame, ceiling_val: float) -> go.Figure:
    """Line chart: confirmed workers over time, with ceiling as reference."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=trend_df["date"],
        y=trend_df["workers_confirmed"],
        mode="lines+markers",
        name="All Confirmed",
        line=dict(color=COLORS["primary"], width=2.5),
        marker=dict(size=7, color=COLORS["primary"]),
        hovertemplate="<b>%{x}</b><br>Workers: %{y:,.0f}<extra></extra>",
    ))

    # Ceiling reference line
    fig.add_hline(
        y=ceiling_val,
        line_dash="dot",
        line_color=COLORS["secondary"],
        line_width=2,
        annotation_text=f"Ceiling: {format_workers(ceiling_val)}",
        annotation_position="right",
        annotation_font=dict(size=10, color=COLORS["secondary"], family=FONT_FAMILY),
    )

    # Shade the gap area
    dates = trend_df["date"].tolist()
    vals = trend_df["workers_confirmed"].tolist()
    fig.add_trace(go.Scatter(
        x=dates + dates[::-1],
        y=[ceiling_val] * len(dates) + vals[::-1],
        fill="toself",
        fillcolor=f"rgba(74,124,111,0.08)",
        line=dict(width=0),
        name="Adoption gap",
        hoverinfo="skip",
    ))

    style_figure(
        fig,
        "Confirmed AI Adoption Growth vs Capability Ceiling",
        subtitle="Workers affected by confirmed AI usage over time | Ceiling = all sources Feb 2026",
        x_title="Date",
        y_title="Workers Affected",
        height=550, width=1100,
        show_legend=True,
    )
    fig.update_layout(
        margin=dict(l=60, r=120, t=80, b=100),
        xaxis=dict(tickfont=dict(size=10, family=FONT_FAMILY), gridcolor=COLORS["grid"]),
        yaxis=dict(tickfont=dict(size=10, family=FONT_FAMILY), gridcolor=COLORS["grid"]),
        legend=dict(
            orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        ),
    )
    return fig


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    fig_dir = results / "figures"
    committed_figs = HERE / "figures"
    committed_figs.mkdir(exist_ok=True)

    primary_ds = ANALYSIS_CONFIGS[PRIMARY_KEY]
    ceiling_ds = ANALYSIS_CONFIGS[CEILING_KEY]

    print("Adoption Gap — generating outputs...\n")

    # ── 1. Occupation-level gaps ──────────────────────────────────────────────

    print("== Occupation-level gaps ==")

    occ_level_key_figs: list[str] = []

    for level in OCC_LEVELS:
        level_label = level.replace("_", " ").title()
        if level == "broad":
            level_label = "Broad Occupation"
        elif level == "occupation":
            level_label = "Occupation"

        print(f"  {level_label}...")
        confirmed_df = get_occ_data(primary_ds, level)
        ceiling_df = get_occ_data(ceiling_ds, level)

        if confirmed_df.empty or ceiling_df.empty:
            print(f"    SKIP — no data")
            continue

        gap_df = compute_gap(confirmed_df, ceiling_df)

        # Save CSV
        top_n_csv = 50 if level == "occupation" else 999
        out = gap_df.sort_values("workers_affected_gap", ascending=False).head(top_n_csv)
        save_csv(out, results / f"occ_gap_{level}.csv")

        # Figures
        top_n_chart = 30 if level in ("occupation", "minor", "broad") else 23

        if level == "major":
            # Dumbbell for major (all categories)
            fig = _dumbbell(gap_df, "workers_affected", "Major Category",
                            top_n=top_n_chart, sort_by_gap=False)
            save_figure(fig, fig_dir / "occ_gap_major.png")
            occ_level_key_figs.append("occ_gap_major.png")

            # Also scatter confirmed vs ceiling at occupation level (built later, uses occ data)

        elif level == "minor":
            fig = _gap_bar(gap_df, "workers_affected", "Minor Category", top_n=20)
            save_figure(fig, fig_dir / "occ_gap_minor.png")
            occ_level_key_figs.append("occ_gap_minor.png")

        elif level == "broad":
            fig = _gap_bar(gap_df, "workers_affected", "Broad Occupation", top_n=20)
            save_figure(fig, fig_dir / "occ_gap_broad.png")

        elif level == "occupation":
            # Gap bar for top occupations
            fig = _gap_bar(gap_df, "workers_affected", "Occupation", top_n=30)
            save_figure(fig, fig_dir / "occ_gap_occupation.png")
            occ_level_key_figs.append("occ_gap_occupation.png")

            # Scatter confirmed vs ceiling
            fig = _confirmed_vs_ceiling_scatter(gap_df)
            save_figure(fig, fig_dir / "confirmed_vs_ceiling_scatter.png")
            occ_level_key_figs.append("confirmed_vs_ceiling_scatter.png")

    # ── 2. Work activity gaps ─────────────────────────────────────────────────

    print("\n== Work activity gaps ==")

    wa_key_figs: list[str] = []

    for level in WA_LEVELS:
        print(f"  {level.upper()}...")
        confirmed_wa = get_wa_data(primary_ds, level)
        ceiling_wa = get_wa_data(ceiling_ds, level)

        if confirmed_wa.empty or ceiling_wa.empty:
            print(f"    SKIP — no data")
            continue

        gap_df = compute_gap(confirmed_wa, ceiling_wa)
        save_csv(
            gap_df.sort_values("workers_affected_gap", ascending=False).head(50),
            results / f"wa_gap_{level}.csv",
        )

        top_n_chart = 20 if level in ("iwa", "dwa") else 13

        if level == "gwa":
            fig = _dumbbell(gap_df, "workers_affected", "GWA",
                            top_n=top_n_chart, sort_by_gap=False)
            save_figure(fig, fig_dir / "wa_gap_gwa.png")
            wa_key_figs.append("wa_gap_gwa.png")

        elif level == "iwa":
            fig = _gap_bar(gap_df, "workers_affected", "IWA", top_n=20)
            save_figure(fig, fig_dir / "wa_gap_iwa.png")
            wa_key_figs.append("wa_gap_iwa.png")

        elif level == "dwa":
            fig = _gap_bar(gap_df, "workers_affected", "DWA", top_n=20)
            save_figure(fig, fig_dir / "wa_gap_dwa.png")

    # ── 3. Cross-config robustness ────────────────────────────────────────────

    print("\n== Cross-config robustness (major level) ==")

    robustness_rows: list[dict] = []
    for config_key, dataset_name in ANALYSIS_CONFIGS.items():
        df = get_occ_data(dataset_name, "major")
        if df.empty:
            continue
        for _, row in df.iterrows():
            robustness_rows.append({
                "config_key": config_key,
                "config_label": ANALYSIS_CONFIG_LABELS[config_key],
                "category": row["category"],
                "pct_tasks_affected": row.get("pct_tasks_affected", np.nan),
                "workers_affected": row.get("workers_affected", np.nan),
            })

    if robustness_rows:
        rob_df = pd.DataFrame(robustness_rows)
        save_csv(rob_df, results / "config_robustness.csv")
        fig = _config_robustness_heatmap(rob_df)
        save_figure(fig, fig_dir / "config_robustness.png")

    # ── 4. Gap trend (confirmed growth over time) ─────────────────────────────

    print("\n== Gap trend (confirmed over time) ==")

    series = ANALYSIS_CONFIG_SERIES.get(PRIMARY_KEY, [])
    trend_rows: list[dict] = []

    for ds_name in series:
        df = get_occ_data(ds_name, "occupation")
        if df.empty:
            continue
        workers_total = df["workers_affected"].sum()
        # Parse date from dataset name (last token)
        date_str = ds_name.split(" ")[-1]
        trend_rows.append({"date": date_str, "workers_confirmed": workers_total,
                           "dataset": ds_name})

    if trend_rows:
        trend_df = pd.DataFrame(trend_rows).sort_values("date")
        save_csv(trend_df, results / "gap_trend.csv")

        # Get ceiling total for reference line
        ceiling_occ = get_occ_data(ceiling_ds, "occupation")
        ceiling_val = ceiling_occ["workers_affected"].sum() if not ceiling_occ.empty else 0

        fig = _gap_trend(trend_df, ceiling_val)
        save_figure(fig, fig_dir / "gap_trend.png")

    # ── 5. Copy key figures to committed figures/ ─────────────────────────────

    print("\n== Copying key figures ==")
    key_figs = [
        "confirmed_vs_ceiling_scatter.png",
        "occ_gap_major.png",
        "occ_gap_minor.png",
        "occ_gap_occupation.png",
        "wa_gap_gwa.png",
        "wa_gap_iwa.png",
        "gap_trend.png",
        "config_robustness.png",
    ]
    for fname in key_figs:
        src = fig_dir / fname
        if src.exists():
            shutil.copy2(src, committed_figs / fname)
            print(f"  Copied {fname}")
        else:
            print(f"  SKIP (not found): {fname}")

    # ── 6. Generate PDF ───────────────────────────────────────────────────────

    print("\n== Generating PDF ==")
    md_path = HERE / "adoption_gap_report.md"
    pdf_path = results / "adoption_gap_report.pdf"
    if md_path.exists():
        generate_pdf(md_path, pdf_path)
        print(f"  Saved {pdf_path.name}")
    else:
        print(f"  SKIP — report not yet written")

    print("\nDone.")


if __name__ == "__main__":
    main()
