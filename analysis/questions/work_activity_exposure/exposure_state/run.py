"""
run.py — Work Activity Exposure: Current State

What work activities are most exposed to AI, and how does that look across
all five canonical configs?

Uses the IWA level as primary (specific enough to be actionable, broad enough
to interpret). GWA summaries for overview charts. DWA for deep-dive CSV.

All five ANALYSIS_CONFIGS are pre-combined datasets (is_aei=False), so they
all use the eco_2025 O*NET baseline and can be directly compared.

Produces:
  results/iwa_all_configs.csv          — All IWAs × 5 configs (pct, workers, wages)
  results/gwa_all_configs.csv          — All GWAs × 5 configs
  results/dwa_confirmed.csv            — All DWAs for primary config
  results/iwa_trends_confirmed.csv     — IWA trends over time (all_confirmed series)
  results/iwa_confirmed_vs_ceiling.csv — IWA confirmed % vs ceiling %

Figures (key ones copied to figures/):
  top_iwas_pct.png         — Top 20 IWAs by % tasks affected (primary config)
  top_iwas_workers.png     — Top 20 IWAs by workers affected (primary config)
  gwa_config_comparison.png — GWA exposure across all 5 configs
  iwa_trends.png           — Top IWA exposure trends over time
  iwa_confirmed_vs_ceiling.png — Scatter: confirmed vs ceiling per IWA

Run from project root:
    venv/Scripts/python -m analysis.questions.work_activity_exposure.exposure_state.run
"""
from __future__ import annotations

import shutil
from pathlib import Path

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
    _format_bar_label,
    format_workers,
    generate_pdf,
    make_horizontal_bar,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
PRIMARY_KEY = "all_confirmed"
CEILING_KEY = "all_ceiling"

# ── Data helpers ──────────────────────────────────────────────────────────────

def get_wa_data(dataset_name: str, level: str = "iwa") -> pd.DataFrame:
    """Get work activity exposure for a single pre-combined dataset."""
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
    # All ANALYSIS_CONFIGS are is_aei=False → mcp_group
    group = result.get("mcp_group") or result.get("aei_group")
    if group is None:
        return pd.DataFrame()
    rows = group.get(level, [])
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["dataset"] = dataset_name
    return df


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("exposure_state: loading data across all 5 configs...")

    # ── 1. Collect IWA and GWA data for all 5 configs ────────────────────────
    iwa_frames: list[pd.DataFrame] = []
    gwa_frames: list[pd.DataFrame] = []

    for key, dataset_name in ANALYSIS_CONFIGS.items():
        label = ANALYSIS_CONFIG_LABELS[key]
        print(f"  {label}...")

        iwa = get_wa_data(dataset_name, "iwa")
        if not iwa.empty:
            iwa["config_key"] = key
            iwa["config_label"] = label
            iwa_frames.append(iwa)

        gwa = get_wa_data(dataset_name, "gwa")
        if not gwa.empty:
            gwa["config_key"] = key
            gwa["config_label"] = label
            gwa_frames.append(gwa)

    assert iwa_frames, "No IWA data returned — check dataset names"
    assert gwa_frames, "No GWA data returned"

    iwa_all = pd.concat(iwa_frames, ignore_index=True)
    gwa_all = pd.concat(gwa_frames, ignore_index=True)

    # ── 2. DWA for primary config only ───────────────────────────────────────
    dwa_primary = get_wa_data(ANALYSIS_CONFIGS[PRIMARY_KEY], "dwa")

    # ── 3. Save CSVs ─────────────────────────────────────────────────────────
    # Wide-format: one row per IWA, columns per config
    iwa_wide = _make_wide(iwa_all, "iwa")
    gwa_wide = _make_wide(gwa_all, "gwa")

    save_csv(iwa_wide, results / "iwa_all_configs.csv")
    save_csv(gwa_wide, results / "gwa_all_configs.csv")
    if not dwa_primary.empty:
        save_csv(
            dwa_primary[["category", "pct_tasks_affected", "workers_affected", "wages_affected"]]
            .sort_values("pct_tasks_affected", ascending=False),
            results / "dwa_confirmed.csv",
        )
    print("  saved IWA/GWA/DWA CSVs")

    # ── 4. Trend data for all_confirmed series ────────────────────────────────
    trend_rows: list[dict] = []
    series = ANALYSIS_CONFIG_SERIES[PRIMARY_KEY]
    for ds_name in series:
        iwa_t = get_wa_data(ds_name, "iwa")
        if iwa_t.empty:
            continue
        # Extract date from dataset name (last token)
        date_str = ds_name.rsplit(" ", 1)[-1]
        for _, row in iwa_t.iterrows():
            trend_rows.append({
                "iwa": row["category"],
                "date": date_str,
                "pct_tasks_affected": row["pct_tasks_affected"],
                "workers_affected": row["workers_affected"],
                "wages_affected": row["wages_affected"],
            })
    trend_df = pd.DataFrame(trend_rows)
    if not trend_df.empty:
        save_csv(trend_df, results / "iwa_trends_confirmed.csv")
    print("  saved trend data")

    # ── 5. Confirmed vs ceiling scatter ──────────────────────────────────────
    conf_iwa = iwa_all[iwa_all["config_key"] == PRIMARY_KEY][["category", "pct_tasks_affected", "workers_affected"]].rename(
        columns={"pct_tasks_affected": "confirmed_pct", "workers_affected": "confirmed_workers"}
    )
    ceil_iwa = iwa_all[iwa_all["config_key"] == CEILING_KEY][["category", "pct_tasks_affected"]].rename(
        columns={"pct_tasks_affected": "ceiling_pct"}
    )
    cv_df = conf_iwa.merge(ceil_iwa, on="category", how="inner")
    cv_df["gap"] = cv_df["ceiling_pct"] - cv_df["confirmed_pct"]
    save_csv(cv_df.sort_values("ceiling_pct", ascending=False), results / "iwa_confirmed_vs_ceiling.csv")
    print("  saved confirmed vs ceiling")

    # ── 6. Figures ────────────────────────────────────────────────────────────

    # Primary config IWA data (sorted descending)
    prim_iwa = iwa_all[iwa_all["config_key"] == PRIMARY_KEY].sort_values("pct_tasks_affected", ascending=False)
    prim_iwa_w = prim_iwa.sort_values("workers_affected", ascending=False)

    # 6a. Top 20 IWAs by % tasks affected
    fig_pct = _make_iwa_bar_pct(prim_iwa.head(20))
    _save(fig_pct, results / "figures" / "top_iwas_pct.png", figs_dir / "top_iwas_pct.png")

    # 6b. Top 20 IWAs by workers affected
    fig_workers = _make_iwa_bar_workers(prim_iwa_w.head(20))
    _save(fig_workers, results / "figures" / "top_iwas_workers.png", figs_dir / "top_iwas_workers.png")

    # 6c. GWA config comparison (grouped bars)
    fig_gwa = _make_gwa_config_comparison(gwa_all)
    _save(fig_gwa, results / "figures" / "gwa_config_comparison.png", figs_dir / "gwa_config_comparison.png")

    # 6d. IWA trends (top 8 IWAs by primary config pct)
    if not trend_df.empty:
        top_iwas = prim_iwa.head(8)["category"].tolist()
        fig_trends = _make_iwa_trends(trend_df, top_iwas)
        _save(fig_trends, results / "figures" / "iwa_trends.png", figs_dir / "iwa_trends.png")

    # 6e. Confirmed vs ceiling scatter
    if not cv_df.empty:
        fig_scatter = _make_cv_scatter(cv_df)
        _save(fig_scatter, results / "figures" / "iwa_confirmed_vs_ceiling.png", figs_dir / "iwa_confirmed_vs_ceiling.png")

    print("  saved all figures")

    # ── 7. PDF ────────────────────────────────────────────────────────────────
    report_md = HERE / "exposure_state_report.md"
    if report_md.exists():
        generate_pdf(report_md, results / "exposure_state_report.pdf")

    print("exposure_state: done.")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_wide(df: pd.DataFrame, level: str) -> pd.DataFrame:
    """Pivot long-format WA data to wide: one row per activity, cols per config."""
    frames = []
    for key, label in ANALYSIS_CONFIG_LABELS.items():
        sub = df[df["config_key"] == key][["category", "pct_tasks_affected", "workers_affected", "wages_affected"]].copy()
        sub = sub.rename(columns={
            "pct_tasks_affected": f"pct_{key}",
            "workers_affected": f"workers_{key}",
            "wages_affected": f"wages_{key}",
        })
        frames.append(sub)
    if not frames:
        return pd.DataFrame()
    result = frames[0]
    for f in frames[1:]:
        result = result.merge(f, on="category", how="outer")
    result = result.sort_values(f"pct_{PRIMARY_KEY}", ascending=False, na_position="last")
    return result


def _save(fig: go.Figure, results_path: Path, figures_path: Path) -> None:
    save_figure(fig, results_path)
    shutil.copy(str(results_path), str(figures_path))


def _make_iwa_bar_pct(df: pd.DataFrame) -> go.Figure:
    df = df.copy().sort_values("pct_tasks_affected", ascending=True)
    fig = go.Figure(go.Bar(
        x=df["pct_tasks_affected"],
        y=df["category"],
        orientation="h",
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=[f"{v:.1f}%" for v in df["pct_tasks_affected"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    fig.update_yaxes(tickfont=dict(size=10))
    style_figure(
        fig,
        "Top Work Activities by AI Exposure",
        subtitle="% tasks affected — All Confirmed Usage (AEI Both + Micro 2026-02-12) | freq | auto-aug on | national",
        x_title="% Tasks Affected",
        show_legend=False,
        height=700,
        width=1100,
    )
    fig.update_layout(
        margin=dict(l=20, r=80, t=80, b=60),
        xaxis=dict(showgrid=True, range=[0, max(df["pct_tasks_affected"]) * 1.18]),
        yaxis=dict(showgrid=False),
        bargap=0.3,
    )
    return fig


def _make_iwa_bar_workers(df: pd.DataFrame) -> go.Figure:
    df = df.copy().sort_values("workers_affected", ascending=True)
    fig = go.Figure(go.Bar(
        x=df["workers_affected"],
        y=df["category"],
        orientation="h",
        marker=dict(color=COLORS["secondary"], line=dict(width=0)),
        text=[format_workers(v) for v in df["workers_affected"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    fig.update_yaxes(tickfont=dict(size=10))
    style_figure(
        fig,
        "Top Work Activities by Workers Affected",
        subtitle="Workers affected — All Confirmed Usage | freq | auto-aug on | national",
        x_title="Workers Affected",
        show_legend=False,
        height=700,
        width=1100,
    )
    fig.update_layout(
        margin=dict(l=20, r=80, t=80, b=60),
        xaxis=dict(showgrid=True, range=[0, max(df["workers_affected"]) * 1.18]),
        yaxis=dict(showgrid=False),
        bargap=0.3,
    )
    return fig


def _make_gwa_config_comparison(gwa_all: pd.DataFrame) -> go.Figure:
    """Grouped bar chart: GWA × 5 configs, sorted by primary config pct."""
    prim = gwa_all[gwa_all["config_key"] == PRIMARY_KEY].sort_values("pct_tasks_affected", ascending=False)
    gwa_order = prim["category"].tolist()

    fig = go.Figure()
    config_keys = list(ANALYSIS_CONFIGS.keys())
    for i, key in enumerate(config_keys):
        sub = gwa_all[gwa_all["config_key"] == key].set_index("category")
        vals = [sub.loc[g, "pct_tasks_affected"] if g in sub.index else 0.0 for g in gwa_order]
        fig.add_trace(go.Bar(
            name=ANALYSIS_CONFIG_LABELS[key],
            x=gwa_order,
            y=vals,
            marker=dict(color=CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)], line=dict(width=0)),
        ))

    style_figure(
        fig,
        "Work Activity Exposure by GWA — All Five Configs",
        subtitle="% tasks affected at GWA level | freq | auto-aug on | national",
        y_title="% Tasks Affected",
        height=700,
        width=1300,
    )
    fig.update_layout(
        barmode="group",
        xaxis=dict(tickangle=-35, tickfont=dict(size=9)),
        margin=dict(l=60, r=40, t=80, b=160),
    )
    return fig


def _make_iwa_trends(trend_df: pd.DataFrame, top_iwas: list[str]) -> go.Figure:
    sub = trend_df[trend_df["iwa"].isin(top_iwas)].copy()
    sub = sub.sort_values("date")

    fig = go.Figure()
    for i, iwa in enumerate(top_iwas):
        d = sub[sub["iwa"] == iwa]
        if d.empty:
            continue
        fig.add_trace(go.Scatter(
            x=d["date"],
            y=d["pct_tasks_affected"],
            mode="lines+markers",
            name=iwa,
            line=dict(color=CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)], width=2),
            marker=dict(size=6),
        ))

    style_figure(
        fig,
        "Work Activity Exposure Over Time — Top IWAs",
        subtitle="All Confirmed Usage series (AEI Both + Micro) | % tasks affected | IWA level",
        x_title="Date",
        y_title="% Tasks Affected",
        height=600,
        width=1200,
    )
    fig.update_layout(margin=dict(l=60, r=40, t=80, b=120))
    return fig


def _make_cv_scatter(cv_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    # Color by gap size
    fig.add_trace(go.Scatter(
        x=cv_df["confirmed_pct"],
        y=cv_df["ceiling_pct"],
        mode="markers+text",
        text=cv_df["category"],
        textposition="top center",
        textfont=dict(size=8, color=COLORS["neutral"]),
        marker=dict(
            color=cv_df["gap"],
            colorscale=[[0, COLORS["primary"]], [1, COLORS["accent"]]],
            size=cv_df["confirmed_workers"].apply(lambda w: max(6, min(25, w / 4e5))),
            showscale=True,
            colorbar=dict(title="Gap (pp)", thickness=12, len=0.6),
            line=dict(width=0.5, color="white"),
        ),
    ))

    # Diagonal reference line
    max_val = max(cv_df["ceiling_pct"].max(), cv_df["confirmed_pct"].max()) + 5
    fig.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val],
        mode="lines",
        line=dict(color=COLORS["muted"], dash="dot", width=1),
        showlegend=False,
    ))

    style_figure(
        fig,
        "Confirmed vs Ceiling Exposure — All IWAs",
        subtitle="X = All Confirmed usage | Y = All Ceiling | Marker size ∝ workers affected | Color = gap (pp)",
        x_title="Confirmed % Tasks Affected",
        y_title="Ceiling % Tasks Affected",
        show_legend=False,
        height=700,
        width=900,
    )
    return fig


if __name__ == "__main__":
    main()
