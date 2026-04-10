"""
run.py — Economic Footprint: Job Structure

How do job zones and job outlook distribute across AI exposure levels?

Job zone (1–5): O*NET measure of preparation/education required.
Job outlook: Utah DWS star rating (1–3; 1=bright/high-wage, 2=average, 3=declining).

Shows:
  - Distribution of occupations and workers across (job_zone × exposure tier)
  - Distribution across (outlook × exposure tier)
  - Sector-level breakdown: average pct_tasks_affected by job_zone within each major
  - Box/violin: pct distribution by job_zone and by outlook (employment-weighted)

Primary config: all_confirmed.

Outputs:
  results/occ_structural.csv         — Per-occ: pct, job_zone, outlook, emp, major
  results/zone_tier_distribution.csv — Count/workers by (job_zone × exposure tier)
  results/outlook_tier_dist.csv      — Count/workers by (outlook × exposure tier)
  results/major_zone_pct.csv         — Avg pct by (major, job_zone)

Figures:
  zone_exposure_violin.png  — Employment-weighted violin of pct by job_zone
  outlook_exposure_violin.png — Violin of pct by outlook rating
  zone_tier_heatmap.png     — Heatmap: job_zone × exposure tier (worker count)
  outlook_tier_heatmap.png  — Heatmap: outlook × exposure tier (worker count)
  major_zone_heatmap.png    — Heatmap: major × job_zone, avg pct_tasks_affected

Run from project root:
    venv/Scripts/python -m analysis.questions.economic_footprint.job_structure.run
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
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.utils import (
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

EXPOSURE_TIERS = [
    ("High (≥60%)", 60, 101),
    ("Moderate (40–59%)", 40, 60),
    ("Restructuring (20–39%)", 20, 40),
    ("Low (<20%)", 0, 20),
]

ZONE_LABELS = {
    1: "Zone 1\n(Little prep)",
    2: "Zone 2\n(Some prep)",
    3: "Zone 3\n(Medium prep)",
    4: "Zone 4\n(Considerable prep)",
    5: "Zone 5\n(Extensive prep)",
}

OUTLOOK_LABELS = {
    5: "5 — Strongest outlook\n+ high wages",
    4: "4 — Good outlook\n+ relatively high wages",
    3: "3 — Moderate outlook\n+ low-mod wages",
    2: "2 — High wages\n+ limited outlook",
    1: "1 — Low wages\n+ strong outlook",
    0: "0 — Limited outlook\n+ low wages",
}

MCP_DATASET = "MCP Cumul. v4"


# -- Data helpers ---------------------------------------------------------------

def _get_structural() -> pd.DataFrame:
    """Return occ structural data: title_current, emp, wage, major, job_zone, outlook."""
    from backend.compute import get_explorer_occupations

    rows = [
        {
            "title_current": o["title_current"],
            "emp": o.get("emp") or 0,
            "wage": o.get("wage") or 0,
            "major": o.get("major", ""),
            "job_zone": o.get("job_zone"),
            "outlook": o.get("dws_star_rating"),
        }
        for o in get_explorer_occupations()
    ]
    return pd.DataFrame(rows)


def assign_tier(pct: float) -> str:
    for label, lo, hi in EXPOSURE_TIERS:
        if lo <= pct < hi:
            return label
    return "Low (<20%)"


def _load_task_level(dataset_name: str) -> pd.DataFrame:
    """Load task-level rows from a dataset CSV with job_zone, freq_mean, pct_normalized."""
    from backend.config import DATASETS

    meta = DATASETS.get(dataset_name)
    assert meta is not None, f"Unknown dataset: {dataset_name}"
    df = pd.read_csv(meta["file"], usecols=[
        "title_current", "task_normalized", "job_zone",
        "freq_mean", "pct_normalized", "major_occ_category",
    ])
    df["job_zone"] = pd.to_numeric(df["job_zone"], errors="coerce")
    df["freq_mean"] = pd.to_numeric(df["freq_mean"], errors="coerce")
    df["pct_normalized"] = pd.to_numeric(df["pct_normalized"], errors="coerce")
    return df[df["job_zone"].notna()].copy()


# -- Figure builders ------------------------------------------------------------

def _build_violin(df: pd.DataFrame, group_col: str, group_labels: dict,
                  title: str, subtitle: str) -> go.Figure:
    """Employment-weighted pseudo-violin using box traces per group."""
    fig = go.Figure()
    colors = [COLORS["primary"], COLORS["secondary"], COLORS["accent"],
              COLORS["positive"], COLORS["negative"]]

    valid = df[df[group_col].notna()].copy()
    valid[group_col] = valid[group_col].astype(int)
    groups = sorted(valid[group_col].unique())

    for i, g in enumerate(groups):
        sub = valid[valid[group_col] == g]
        # Expand by employment for weighted distribution
        expanded = sub.loc[sub.index.repeat((sub["emp"] / 1000).clip(1).astype(int))]
        label = group_labels.get(g, str(g))
        fig.add_trace(go.Violin(
            x=[label] * len(expanded),
            y=expanded["pct"],
            name=label,
            box_visible=True,
            meanline_visible=True,
            fillcolor=colors[i % len(colors)],
            opacity=0.7,
            line_color=colors[i % len(colors)],
            points=False,
        ))

    style_figure(fig, title, subtitle=subtitle, y_title="% Tasks Affected",
                 show_legend=False, height=600, width=1100)
    fig.update_layout(
        xaxis=dict(showgrid=False, showline=False),
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        violinmode="group",
    )
    return fig


def _build_tier_heatmap(dist_df: pd.DataFrame, group_col: str,
                         group_labels: dict, title: str) -> go.Figure:
    """Heatmap: group × exposure tier, cell = workers affected (millions)."""
    tier_order = [t[0] for t in EXPOSURE_TIERS]
    dist_df = dist_df.copy()
    dist_df[group_col] = dist_df[group_col].map(group_labels).fillna(dist_df[group_col].astype(str))

    pivot = dist_df.pivot_table(
        index=group_col, columns="tier", values="workers_m", aggfunc="first"
    ).reindex(columns=tier_order).fillna(0)

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=list(pivot.columns),
        y=list(pivot.index),
        colorscale=[[0, "#f0f4f8"], [0.5, COLORS["primary"]], [1.0, "#0d2b45"]],
        text=[[f"{v:.1f}M" if v > 0 else "" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=11, color="white", family=FONT_FAMILY),
        hovertemplate="%{y} | %{x}: %{z:.1f}M workers<extra></extra>",
        showscale=True,
        colorbar=dict(title="Workers<br>Affected (M)", tickfont=dict(size=10)),
    ))
    style_figure(fig, title,
                 subtitle="Cell values = workers affected (millions)",
                 show_legend=False, height=500, width=1000)
    fig.update_layout(
        xaxis=dict(showgrid=False, showline=False, tickangle=-15),
        yaxis=dict(showgrid=False, showline=False),
        margin=dict(l=200, r=80, t=90, b=80),
    )
    return fig


def _build_zone_metric_violin(task_df: pd.DataFrame, metric_col: str,
                               title: str, subtitle: str,
                               y_title: str) -> go.Figure:
    """Violin of a task-level metric (freq_mean or pct_normalized) by job_zone."""
    fig = go.Figure()
    colors = [COLORS["primary"], COLORS["secondary"], COLORS["accent"],
              COLORS["positive"], COLORS["negative"]]

    valid = task_df[task_df[metric_col].notna()].copy()
    valid["job_zone"] = valid["job_zone"].astype(int)
    zones = sorted(valid["job_zone"].unique())

    for i, z in enumerate(zones):
        sub = valid[valid["job_zone"] == z]
        label = ZONE_LABELS.get(z, str(z)).replace("\n", " ")
        fig.add_trace(go.Violin(
            x=[label] * len(sub),
            y=sub[metric_col],
            name=label,
            box_visible=True,
            meanline_visible=True,
            fillcolor=colors[i % len(colors)],
            opacity=0.7,
            line_color=colors[i % len(colors)],
            points=False,
        ))

    style_figure(fig, title, subtitle=subtitle, y_title=y_title,
                 show_legend=False, height=600, width=1100)
    fig.update_layout(
        xaxis=dict(showgrid=False, showline=False),
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        violinmode="group",
    )
    return fig


def _build_zone_metric_bar(task_df: pd.DataFrame, metric_col: str,
                            title: str, subtitle: str,
                            y_title: str) -> go.Figure:
    """Bar chart of average task-level metric by job_zone."""
    valid = task_df[task_df[metric_col].notna()].copy()
    valid["job_zone"] = valid["job_zone"].astype(int)
    zone_avg = valid.groupby("job_zone")[metric_col].mean().reset_index()
    zone_avg["label"] = zone_avg["job_zone"].map(
        {k: v.replace("\n", " ") for k, v in ZONE_LABELS.items()}
    )
    zone_avg = zone_avg.sort_values("job_zone")

    colors = [COLORS["primary"], COLORS["secondary"], COLORS["accent"],
              COLORS["positive"], COLORS["negative"]]

    fig = go.Figure(go.Bar(
        x=zone_avg["label"],
        y=zone_avg[metric_col],
        marker_color=[colors[i % len(colors)] for i in range(len(zone_avg))],
        text=[f"{v:.2f}" for v in zone_avg[metric_col]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["neutral"], family=FONT_FAMILY),
    ))

    style_figure(fig, title, subtitle=subtitle, y_title=y_title,
                 show_legend=False, height=500, width=900)
    fig.update_layout(
        xaxis=dict(showgrid=False, showline=False),
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
    )
    return fig


def _build_major_zone_heatmap(major_zone: pd.DataFrame) -> go.Figure:
    """Heatmap: major (rows) × job_zone (cols), avg pct_tasks_affected."""
    pivot = major_zone.pivot_table(
        index="major", columns="job_zone_label", values="avg_pct", aggfunc="first"
    ).fillna(np.nan)
    zone_col_order = [ZONE_LABELS.get(z, str(z)).replace("\n", " ") for z in range(1, 6)]
    existing = [c for c in zone_col_order if c in pivot.columns]
    pivot = pivot[existing]
    pivot = pivot.sort_index()

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=list(pivot.columns),
        y=list(pivot.index),
        colorscale=[[0, "#f0f4f8"], [0.5, COLORS["secondary"]], [1.0, "#0a2e25"]],
        text=[[f"{v:.1f}%" if not np.isnan(v) else "—" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=11, family=FONT_FAMILY),
        hovertemplate="%{y} | %{x}: %{z:.1f}%<extra></extra>",
        showscale=True,
        colorbar=dict(title="Avg %<br>Tasks<br>Affected", tickfont=dict(size=10)),
    ))
    style_figure(fig, "Average % Tasks Affected by Sector and Job Zone",
                 subtitle="Employment-weighted average across occupations in each cell",
                 show_legend=False, height=700, width=1100)
    fig.update_layout(
        xaxis=dict(showgrid=False, showline=False, tickangle=-15),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        margin=dict(l=280, r=80, t=90, b=100),
    )
    return fig


# -- Main -----------------------------------------------------------------------

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("job_structure: loading data...")
    structural = _get_structural()
    pct = get_pct_tasks_affected(ANALYSIS_CONFIGS[PRIMARY_KEY])

    df = structural.copy()
    df["pct"] = df["title_current"].map(pct).fillna(0.0)
    df["tier"] = df["pct"].apply(assign_tier)

    # -- 1. Save base data -----------------------------------------------------
    save_csv(
        df[["title_current", "major", "job_zone", "outlook", "emp", "wage", "pct", "tier"]],
        results / "occ_structural.csv",
    )

    # -- 2. Zone × tier distribution ------------------------------------------
    zone_tier = (
        df[df["job_zone"].notna()]
        .groupby(["job_zone", "tier"])
        .agg(n_occs=("title_current", "count"), workers=("emp", "sum"))
        .reset_index()
    )
    zone_tier["workers_m"] = zone_tier["workers"] / 1e6
    zone_tier["job_zone_label"] = zone_tier["job_zone"].map(
        {k: v.replace("\n", " ") for k, v in ZONE_LABELS.items()}
    )
    save_csv(zone_tier, results / "zone_tier_distribution.csv")

    # -- 3. Outlook × tier distribution ---------------------------------------
    outlook_tier = (
        df[df["outlook"].notna()]
        .groupby(["outlook", "tier"])
        .agg(n_occs=("title_current", "count"), workers=("emp", "sum"))
        .reset_index()
    )
    outlook_tier["workers_m"] = outlook_tier["workers"] / 1e6
    outlook_tier["outlook_label"] = outlook_tier["outlook"].map(
        {k: v.replace("\n", " ") for k, v in OUTLOOK_LABELS.items()}
    )
    save_csv(outlook_tier, results / "outlook_tier_dist.csv")

    # -- 4. Major × zone average pct ------------------------------------------
    major_zone = (
        df[df["job_zone"].notna() & (df["emp"] > 0)]
        .groupby(["major", "job_zone"])
        .apply(lambda g: np.average(g["pct"], weights=g["emp"]))
        .reset_index(name="avg_pct")
    )
    major_zone["job_zone_label"] = major_zone["job_zone"].map(
        {k: v.replace("\n", " ") for k, v in ZONE_LABELS.items()}
    )
    save_csv(major_zone, results / "major_zone_pct.csv")

    # -- 5. Figures ------------------------------------------------------------

    # 5a. Job zone violin
    fig_zone_v = _build_violin(
        df, "job_zone", {k: v.replace("\n", " ") for k, v in ZONE_LABELS.items()},
        "AI Exposure Distribution by Job Zone",
        subtitle=f"{ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]} | Employment-weighted violin",
    )
    save_figure(fig_zone_v, results / "figures" / "zone_exposure_violin.png")
    shutil.copy(results / "figures" / "zone_exposure_violin.png", figs_dir / "zone_exposure_violin.png")
    print("  zone_exposure_violin.png")

    # 5b. Outlook violin
    fig_outlook_v = _build_violin(
        df, "outlook", {k: v.replace("\n", " ") for k, v in OUTLOOK_LABELS.items()},
        "AI Exposure Distribution by Job Outlook Rating",
        subtitle=f"{ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]} | Employment-weighted violin | ECO 2025 DWS ratings (0-5, non-linear)",
    )
    save_figure(fig_outlook_v, results / "figures" / "outlook_exposure_violin.png")
    shutil.copy(results / "figures" / "outlook_exposure_violin.png", figs_dir / "outlook_exposure_violin.png")
    print("  outlook_exposure_violin.png")

    # 5c. Zone × tier heatmap
    fig_zone_heat = _build_tier_heatmap(
        zone_tier, "job_zone", {k: v.replace("\n", " ") for k, v in ZONE_LABELS.items()},
        "Workers by Job Zone and Exposure Tier",
    )
    save_figure(fig_zone_heat, results / "figures" / "zone_tier_heatmap.png")
    shutil.copy(results / "figures" / "zone_tier_heatmap.png", figs_dir / "zone_tier_heatmap.png")
    print("  zone_tier_heatmap.png")

    # 5d. Outlook × tier heatmap
    fig_outlook_heat = _build_tier_heatmap(
        outlook_tier, "outlook", {k: v.replace("\n", " ") for k, v in OUTLOOK_LABELS.items()},
        "Workers by Outlook Rating and Exposure Tier",
    )
    save_figure(fig_outlook_heat, results / "figures" / "outlook_tier_heatmap.png")
    shutil.copy(results / "figures" / "outlook_tier_heatmap.png", figs_dir / "outlook_tier_heatmap.png")
    print("  outlook_tier_heatmap.png")

    # 5e. Major × zone heatmap
    fig_major_zone = _build_major_zone_heatmap(major_zone)
    save_figure(fig_major_zone, results / "figures" / "major_zone_heatmap.png")
    shutil.copy(results / "figures" / "major_zone_heatmap.png", figs_dir / "major_zone_heatmap.png")
    print("  major_zone_heatmap.png")

    # -- 6. MCP-only zone analysis --------------------------------------------
    print("\njob_structure: MCP-only zone analysis...")
    pct_mcp = get_pct_tasks_affected(MCP_DATASET)
    df_mcp = structural.copy()
    df_mcp["pct"] = df_mcp["title_current"].map(pct_mcp).fillna(0.0)
    df_mcp["tier"] = df_mcp["pct"].apply(assign_tier)

    # 6a. MCP zone violin
    fig_mcp_zone_v = _build_violin(
        df_mcp, "job_zone", {k: v.replace("\n", " ") for k, v in ZONE_LABELS.items()},
        "AI Exposure by Job Zone — MCP Only",
        subtitle="MCP Cumul. v4 | Employment-weighted violin | Removes user self-selection bias",
    )
    save_figure(fig_mcp_zone_v, results / "figures" / "zone_exposure_violin_mcp.png")
    shutil.copy(results / "figures" / "zone_exposure_violin_mcp.png", figs_dir / "zone_exposure_violin_mcp.png")
    print("  zone_exposure_violin_mcp.png")

    # 6b. MCP zone × tier heatmap
    mcp_zone_tier = (
        df_mcp[df_mcp["job_zone"].notna()]
        .groupby(["job_zone", "tier"])
        .agg(n_occs=("title_current", "count"), workers=("emp", "sum"))
        .reset_index()
    )
    mcp_zone_tier["workers_m"] = mcp_zone_tier["workers"] / 1e6
    fig_mcp_zone_heat = _build_tier_heatmap(
        mcp_zone_tier, "job_zone", {k: v.replace("\n", " ") for k, v in ZONE_LABELS.items()},
        "Workers by Job Zone and Exposure Tier — MCP Only",
    )
    save_figure(fig_mcp_zone_heat, results / "figures" / "zone_tier_heatmap_mcp.png")
    shutil.copy(results / "figures" / "zone_tier_heatmap_mcp.png", figs_dir / "zone_tier_heatmap_mcp.png")
    print("  zone_tier_heatmap_mcp.png")

    # -- 7. Task freq and pct_norm by zone ------------------------------------
    print("\njob_structure: task-level freq/pct_norm by zone...")
    task_df = _load_task_level(ANALYSIS_CONFIGS[PRIMARY_KEY])

    # 7a. Freq by zone — bar
    fig_freq_bar = _build_zone_metric_bar(
        task_df, "freq_mean",
        "Average Task Frequency by Job Zone",
        subtitle=f"{ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]} | Mean freq_mean per task row",
        y_title="Avg freq_mean",
    )
    save_figure(fig_freq_bar, results / "figures" / "zone_freq_bar.png")
    shutil.copy(results / "figures" / "zone_freq_bar.png", figs_dir / "zone_freq_bar.png")
    print("  zone_freq_bar.png")

    # 7b. Freq by zone — violin
    fig_freq_violin = _build_zone_metric_violin(
        task_df, "freq_mean",
        "Task Frequency Distribution by Job Zone",
        subtitle=f"{ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]} | Each point = one task row",
        y_title="freq_mean",
    )
    save_figure(fig_freq_violin, results / "figures" / "zone_freq_violin.png")
    shutil.copy(results / "figures" / "zone_freq_violin.png", figs_dir / "zone_freq_violin.png")
    print("  zone_freq_violin.png")

    # 7c. Pct norm by zone — bar
    fig_pct_bar = _build_zone_metric_bar(
        task_df, "pct_normalized",
        "Average pct_normalized by Job Zone",
        subtitle=f"{ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]} | Mean pct_normalized per task row",
        y_title="Avg pct_normalized",
    )
    save_figure(fig_pct_bar, results / "figures" / "zone_pct_norm_bar.png")
    shutil.copy(results / "figures" / "zone_pct_norm_bar.png", figs_dir / "zone_pct_norm_bar.png")
    print("  zone_pct_norm_bar.png")

    # 7d. Pct norm by zone — violin
    fig_pct_violin = _build_zone_metric_violin(
        task_df, "pct_normalized",
        "pct_normalized Distribution by Job Zone",
        subtitle=f"{ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]} | Each point = one task row",
        y_title="pct_normalized",
    )
    save_figure(fig_pct_violin, results / "figures" / "zone_pct_norm_violin.png")
    shutil.copy(results / "figures" / "zone_pct_norm_violin.png", figs_dir / "zone_pct_norm_violin.png")
    print("  zone_pct_norm_violin.png")

    # -- 8. Summary stats ------------------------------------------------------
    print("\n-- Zone breakdown (primary config) --")
    for zone in range(1, 6):
        sub = df[df["job_zone"] == zone]
        if sub.empty:
            continue
        avg_pct = np.average(sub["pct"], weights=sub["emp"].clip(1)) if sub["emp"].sum() > 0 else 0
        print(f"  Zone {zone}: {len(sub)} occs, {format_workers(sub['emp'].sum())} workers, "
              f"avg pct = {avg_pct:.1f}%")

    print("\n-- Outlook breakdown (0-5 scale) --")
    for olk in range(6):
        sub = df[df["outlook"] == olk]
        if sub.empty:
            continue
        avg_pct = np.average(sub["pct"], weights=sub["emp"].clip(1)) if sub["emp"].sum() > 0 else 0
        print(f"  Outlook {olk}: {len(sub)} occs, {format_workers(sub['emp'].sum())} workers, "
              f"avg pct = {avg_pct:.1f}%")

    print("\n-- Zone breakdown (MCP only) --")
    for zone in range(1, 6):
        sub = df_mcp[df_mcp["job_zone"] == zone]
        if sub.empty:
            continue
        avg_pct = np.average(sub["pct"], weights=sub["emp"].clip(1)) if sub["emp"].sum() > 0 else 0
        print(f"  Zone {zone}: {len(sub)} occs, {format_workers(sub['emp'].sum())} workers, "
              f"avg pct = {avg_pct:.1f}%")

    # -- 9. PDF ----------------------------------------------------------------
    report_path = HERE / "job_structure_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "job_structure_report.pdf")

    print("\njob_structure: done.")


if __name__ == "__main__":
    main()
