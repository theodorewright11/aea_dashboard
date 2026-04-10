"""
run.py — Economic Footprint: AI Modes

What's the automation/augmentation makeup of the AI footprint?

Three lenses:
  1. Agentic vs conversational split at major sector level
     (agentic_confirmed vs human_conversation configs)
  2. Auto-aug score distribution across all occupations (employment-weighted)
     — how automatable is the average American worker's task set?
  3. Automation vs augmentation direction: high auto-aug score = more replaceable;
     lower = augmentation territory. Show by sector.

Primary config: all_confirmed. Mode split uses:
  - Conversational: human_conversation (AEI Conv + Micro — human chat only)
  - Agentic: agentic_confirmed (MCP + API — tool-use only)

Outputs:
  results/mode_comparison_major.csv  — Major × mode: workers/wages/pct
  results/autoaug_distribution.csv   — Employment-weighted auto-aug score histogram
  results/autoaug_by_major.csv       — Average auto-aug score per major category
  results/autoaug_by_config.csv      — Economy-wide auto-aug stats per config

Figures:
  agentic_vs_conversational.png  — Butterfly chart: agentic vs conversational by major
  autoaug_distribution.png       — Employment-weighted auto-aug score distribution
  autoaug_by_major.png           — Average auto-aug score per major (bar)
  mode_workers_scatter.png       — Scatter: agentic workers vs conversational workers by major

Run from project root:
    venv/Scripts/python -m analysis.questions.economic_footprint.ai_modes.run
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
)
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    format_workers,
    format_wages,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
PRIMARY_KEY = "all_confirmed"
CONV_KEY = "human_conversation"
AGENTIC_KEY = "agentic_confirmed"


# -- Data helpers ---------------------------------------------------------------

def get_major_data(dataset_name: str) -> pd.DataFrame:
    """Return major-category data for a single dataset."""
    from backend.compute import get_group_data

    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": "nat",
        "agg_level": "major",
        "sort_by": "Workers Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    assert data is not None, f"No data for {dataset_name}"
    return data["df"].rename(columns={"major_occ_category": "category"})


def get_autoaug_by_major_config(config_key: str) -> pd.DataFrame:
    """
    Load task-level auto_aug for a config's dataset, grouped by major occ category.

    Returns DataFrame with columns:
        major, avg_auto_aug_with_vals, avg_auto_aug_all, config_key
    """
    from backend.config import DATASETS

    dataset_name = ANALYSIS_CONFIGS[config_key]
    meta = DATASETS.get(dataset_name)
    assert meta is not None, f"Unknown dataset: {dataset_name}"

    # Read just the columns we need — AEI files use 'title', others use 'title_current'
    all_cols = pd.read_csv(meta["file"], nrows=0).columns.tolist()
    need_cols = ["task_normalized", "major_occ_category", "auto_aug_mean"]
    title_col = "title_current" if "title_current" in all_cols else "title"
    need_cols.append(title_col)
    df = pd.read_csv(meta["file"], usecols=need_cols)
    df["auto_aug_mean"] = pd.to_numeric(df["auto_aug_mean"], errors="coerce")

    # Dedup to unique (major, task_normalized) pairs
    deduped = df.groupby(["major_occ_category", "task_normalized"]).agg(
        auto_aug_mean=("auto_aug_mean", "mean"),
    ).reset_index()

    # Per major: avg of tasks with values, avg of all tasks (NaN -> 0)
    rows: list[dict] = []
    for major, grp in deduped.groupby("major_occ_category"):
        with_vals = grp[grp["auto_aug_mean"].notna()]
        avg_with = with_vals["auto_aug_mean"].mean() if len(with_vals) > 0 else 0.0
        avg_all = grp["auto_aug_mean"].fillna(0.0).mean()
        rows.append({
            "major": major,
            "avg_auto_aug_with_vals": avg_with,
            "avg_auto_aug_all": avg_all,
            "config_key": config_key,
            "config_label": ANALYSIS_CONFIG_LABELS[config_key],
        })
    return pd.DataFrame(rows)


def get_autoaug_by_occ() -> pd.DataFrame:
    """
    Return per-occ auto-aug stats from the explorer.
    Fields: title_current, emp, major, auto_avg (avg auto-aug score across tasks).
    """
    from backend.compute import get_explorer_occupations

    rows = [
        {
            "title_current": o["title_current"],
            "emp": o.get("emp") or 0,
            "major": o.get("major", ""),
            "auto_avg": o.get("auto_avg_with_vals"),
        }
        for o in get_explorer_occupations()
    ]
    df = pd.DataFrame(rows)
    df["auto_avg"] = pd.to_numeric(df["auto_avg"], errors="coerce")
    return df


# -- Figure builders ------------------------------------------------------------

def _build_butterfly(conv_df: pd.DataFrame, agentic_df: pd.DataFrame) -> go.Figure:
    """Butterfly chart: agentic (left) vs conversational (right) workers by major.

    Y-axis labels include pct_tasks_affected for each mode in parentheses.
    """
    merged = conv_df[["category", "workers_affected", "pct_tasks_affected"]].merge(
        agentic_df[["category", "workers_affected", "pct_tasks_affected"]].rename(
            columns={"workers_affected": "workers_agentic",
                     "pct_tasks_affected": "pct_agentic"}
        ),
        on="category",
    )
    merged["workers_conv"] = merged["workers_affected"]
    merged["pct_conv"] = merged["pct_tasks_affected"]
    merged = merged.sort_values("workers_conv", ascending=True)

    # Y-axis labels with pct_tasks_affected
    y_labels = [
        f"{cat} (Conv: {pc:.1f}% | Agt: {pa:.1f}%)"
        for cat, pc, pa in zip(merged["category"], merged["pct_conv"], merged["pct_agentic"])
    ]

    fig = go.Figure()

    # Left bars: conversational (negative x for butterfly)
    fig.add_trace(go.Bar(
        x=[-v for v in merged["workers_conv"] / 1e6],
        y=y_labels,
        orientation="h",
        name="Conversational (human chat)",
        marker_color=COLORS["primary"],
        text=[f"{v/1e6:.1f}M" for v in merged["workers_conv"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))

    # Right bars: agentic
    fig.add_trace(go.Bar(
        x=[v / 1e6 for v in merged["workers_agentic"]],
        y=y_labels,
        orientation="h",
        name="Agentic (tool-use)",
        marker_color=COLORS["secondary"],
        text=[f"{v/1e6:.1f}M" for v in merged["workers_agentic"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))

    style_figure(fig, "Agentic vs Conversational AI Reach by Sector",
                 subtitle="Left = conversational | Right = agentic | Parentheses = % tasks affected per mode",
                 x_title="Workers Affected (millions)", height=800, width=1300)
    fig.update_layout(
        barmode="relative",
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   tickvals=[-60, -40, -20, 0, 20, 40, 60],
                   ticktext=["60M", "40M", "20M", "0", "20M", "40M", "60M"]),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=9)),
        margin=dict(l=20, r=100),
        bargap=0.15,
    )
    return fig


def _build_drop_chart(conv_df: pd.DataFrame, agentic_df: pd.DataFrame,
                      metric: str, title: str, x_label: str) -> go.Figure:
    """Ranked bar chart showing drop from conversational to agentic per major."""
    merged = conv_df[["category", metric]].merge(
        agentic_df[["category", metric]].rename(columns={metric: f"{metric}_agentic"}),
        on="category",
    )
    merged["drop"] = merged[metric] - merged[f"{metric}_agentic"]
    if metric == "workers_affected":
        merged["drop_display"] = merged["drop"] / 1e6
        fmt = lambda v: f"{v:.1f}M"
    else:
        merged["drop_display"] = merged["drop"]
        fmt = lambda v: f"{v:.1f}pp"
    merged = merged.sort_values("drop_display", ascending=True)

    fig = go.Figure(go.Bar(
        x=merged["drop_display"],
        y=merged["category"],
        orientation="h",
        marker_color=[COLORS["negative"] if v > 0 else COLORS["positive"]
                      for v in merged["drop_display"]],
        text=[fmt(v) for v in merged["drop_display"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))

    style_figure(fig, title,
                 subtitle="Conversational minus Agentic | Larger bar = bigger deployment gap",
                 x_title=x_label, show_legend=False, height=700, width=1100)
    fig.update_layout(
        margin=dict(l=20, r=100),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        bargap=0.25,
    )
    return fig


def _build_autoaug_distribution(occ_df: pd.DataFrame) -> go.Figure:
    """Employment-weighted histogram of average auto-aug scores."""
    valid = occ_df[occ_df["auto_avg"].notna() & (occ_df["emp"] > 0)].copy()

    bins = np.arange(0, 5.25, 0.25)
    bin_centers = (bins[:-1] + bins[1:]) / 2

    hist_vals, _ = np.histogram(
        valid["auto_avg"],
        bins=bins,
        weights=valid["emp"],
    )
    hist_m = hist_vals / 1e6

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=bin_centers,
        y=hist_m,
        width=0.22,
        marker_color=COLORS["primary"],
        marker_line_color=COLORS["bg"],
        marker_line_width=1,
        name="Workers (M)",
        hovertemplate="Score %.2f–%.2f: %%{y:.1f}M workers<extra></extra>",
    ))

    # Add mean line (employment-weighted)
    valid_emp = valid[valid["emp"] > 0]
    weighted_median = float(np.average(valid_emp["auto_avg"], weights=valid_emp["emp"])) if len(valid_emp) > 0 else valid["auto_avg"].mean()
    fig.add_vline(
        x=weighted_median, line_dash="dash", line_color=COLORS["accent"],
        annotation_text=f"Wtd mean: {weighted_median:.2f}",
        annotation_position="top right",
        annotation_font=dict(size=12, color=COLORS["accent"]),
    )

    style_figure(fig, "Employment-Weighted Auto-Aug Score Distribution",
                 subtitle="Each bar = workers in occupations with that average auto-aug score | Score: 0=not automatable, 5=fully automatable",
                 x_title="Average Auto-Aug Score (0–5)", y_title="Workers (millions)",
                 show_legend=False, height=550, width=1100)
    fig.update_layout(
        xaxis=dict(showgrid=False, dtick=0.5),
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
    )
    return fig


def _build_autoaug_by_major(occ_df: pd.DataFrame) -> go.Figure:
    """Employment-weighted average auto-aug score per major category."""
    valid = occ_df[occ_df["auto_avg"].notna() & (occ_df["emp"] > 0)].copy()
    _vw = valid[["major", "auto_avg", "emp"]].copy()
    _vw["_weighted"] = _vw["auto_avg"] * _vw["emp"]
    major_avg = (
        _vw.groupby("major")[["_weighted", "emp"]].sum()
        .assign(auto_avg_wtd=lambda d: d["_weighted"] / d["emp"])
        .drop(columns=["_weighted", "emp"])
        .reset_index()
        .sort_values("auto_avg_wtd", ascending=True)
    )

    fig = go.Figure(go.Bar(
        x=major_avg["auto_avg_wtd"],
        y=major_avg["major"],
        orientation="h",
        marker_color=COLORS["primary"],
        text=[f"{v:.2f}" for v in major_avg["auto_avg_wtd"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    fig.add_vline(x=major_avg["auto_avg_wtd"].mean(), line_dash="dash",
                  line_color=COLORS["muted"], annotation_text="Economy avg")

    style_figure(fig, "Employment-Weighted Auto-Aug Score by Sector",
                 subtitle="Score 0–5 | Higher = tasks more automatable by AI | Employment-weighted average",
                 x_title="Auto-Aug Score (0–5)", show_legend=False, height=700, width=1100)
    fig.update_layout(
        margin=dict(l=20, r=100),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        bargap=0.25,
    )
    return fig


def _build_autoaug_by_config(all_config_df: pd.DataFrame, metric: str,
                              title: str, subtitle: str) -> go.Figure:
    """Grouped bar chart: auto-aug metric per major across all configs."""
    config_palette = [COLORS["primary"], COLORS["secondary"], COLORS["accent"],
                      COLORS["positive"], COLORS["negative"]]

    # Sort majors by avg across configs
    major_order = (
        all_config_df.groupby("major")[metric].mean()
        .sort_values(ascending=True).index.tolist()
    )
    configs = all_config_df["config_label"].unique()

    fig = go.Figure()
    for i, cfg_label in enumerate(configs):
        cfg_data = all_config_df[all_config_df["config_label"] == cfg_label]
        cfg_data = cfg_data.set_index("major").reindex(major_order).reset_index()
        fig.add_trace(go.Bar(
            x=cfg_data[metric],
            y=cfg_data["major"],
            orientation="h",
            name=cfg_label,
            marker_color=config_palette[i % len(config_palette)],
            text=[f"{v:.2f}" if pd.notna(v) else "" for v in cfg_data[metric]],
            textposition="outside",
            textfont=dict(size=8, color=COLORS["neutral"], family=FONT_FAMILY),
            cliponaxis=False,
        ))

    style_figure(fig, title, subtitle=subtitle,
                 x_title="Auto-Aug Score (0–5)", height=800, width=1300)
    fig.update_layout(
        barmode="group",
        margin=dict(l=20, r=120),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        bargap=0.2,
        bargroupgap=0.05,
    )
    return fig


def _build_mode_scatter(conv_df: pd.DataFrame, agentic_df: pd.DataFrame) -> go.Figure:
    """Scatter: agentic workers vs conversational workers per major category."""
    merged = conv_df[["category", "workers_affected", "pct_tasks_affected"]].merge(
        agentic_df[["category", "workers_affected"]].rename(
            columns={"workers_affected": "workers_agentic", }
        ),
        on="category",
    )
    merged["conv_m"] = merged["workers_affected"] / 1e6
    merged["agentic_m"] = merged["workers_agentic"] / 1e6

    colors_per_point = [COLORS["primary"]] * len(merged)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=merged["conv_m"],
        y=merged["agentic_m"],
        mode="markers+text",
        text=merged["category"],
        textposition="top right",
        textfont=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
        marker=dict(
            color=COLORS["primary"],
            size=merged["pct_tasks_affected"].clip(5, 60),
            opacity=0.75,
            line=dict(color=COLORS["bg"], width=1),
        ),
        hovertemplate="<b>%{text}</b><br>Conversational: %{x:.1f}M<br>Agentic: %{y:.1f}M<extra></extra>",
    ))

    # Diagonal reference line (equal)
    max_val = max(merged["conv_m"].max(), merged["agentic_m"].max()) * 1.05
    fig.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val],
        mode="lines", line=dict(dash="dash", color=COLORS["muted"], width=1),
        name="Equal reach",
        showlegend=True,
    ))

    style_figure(fig, "Agentic vs Conversational Reach per Sector",
                 subtitle="Dot size = % tasks affected (primary config) | Points above diagonal = agentic leads",
                 x_title="Conversational Workers Affected (M)",
                 y_title="Agentic Workers Affected (M)",
                 height=650, width=900)
    return fig


# -- Main -----------------------------------------------------------------------

def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("ai_modes: loading data...")

    # -- 1. Mode comparison (major level) -------------------------------------
    conv_ds = ANALYSIS_CONFIGS[CONV_KEY]
    agentic_ds = ANALYSIS_CONFIGS[AGENTIC_KEY]
    primary_ds = ANALYSIS_CONFIGS[PRIMARY_KEY]

    print(f"  Conversational ({ANALYSIS_CONFIG_LABELS[CONV_KEY]})...")
    conv_major = get_major_data(conv_ds)
    conv_major["mode"] = "conversational"
    conv_major["config_label"] = ANALYSIS_CONFIG_LABELS[CONV_KEY]

    print(f"  Agentic ({ANALYSIS_CONFIG_LABELS[AGENTIC_KEY]})...")
    agentic_major = get_major_data(agentic_ds)
    agentic_major["mode"] = "agentic"
    agentic_major["config_label"] = ANALYSIS_CONFIG_LABELS[AGENTIC_KEY]

    print(f"  Primary ({ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]})...")
    primary_major = get_major_data(primary_ds)
    primary_major["mode"] = "all_confirmed"
    primary_major["config_label"] = ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]

    mode_df = pd.concat([conv_major, agentic_major, primary_major], ignore_index=True)
    save_csv(
        mode_df[["mode", "config_label", "category", "workers_affected", "wages_affected", "pct_tasks_affected"]],
        results / "mode_comparison_major.csv",
    )

    # Aggregate totals per mode
    mode_totals = []
    for ds_key, ds_name, mode_label in [
        (PRIMARY_KEY, primary_ds, "All Confirmed"),
        (CONV_KEY, conv_ds, "Conversational"),
        (AGENTIC_KEY, agentic_ds, "Agentic"),
    ]:
        from backend.compute import get_group_data
        occ_config = {
            "selected_datasets": [ds_name],
            "combine_method": "Average",
            "method": "freq",
            "use_auto_aug": True,
            "physical_mode": "all",
            "geo": "nat",
            "agg_level": "occupation",
            "sort_by": "Workers Affected",
            "top_n": 9999,
            "search_query": "",
            "context_size": 3,
        }
        occ_data = get_group_data(occ_config)
        if occ_data:
            occ_df = occ_data["df"]
            mode_totals.append({
                "mode": mode_label,
                "config_label": ANALYSIS_CONFIG_LABELS[ds_key],
                "workers_affected": occ_df["workers_affected"].sum(),
                "wages_affected": occ_df["wages_affected"].sum(),
            })
    totals_df = pd.DataFrame(mode_totals)
    save_csv(totals_df, results / "mode_totals.csv")

    # -- 2. Auto-aug distribution ----------------------------------------------
    print("  Auto-aug distribution...")
    occ_autoaug = get_autoaug_by_occ()
    valid = occ_autoaug[occ_autoaug["auto_avg"].notna()].copy()

    _vmp = valid[valid["emp"] > 0].copy()
    _vmp["_weighted"] = _vmp["auto_avg"] * _vmp["emp"]
    autoaug_major = (
        _vmp.groupby("major")[["_weighted", "emp"]].sum()
        .assign(auto_avg_wtd=lambda d: d["_weighted"] / d["emp"])
        .drop(columns=["_weighted", "emp"])
        .reset_index()
    )
    save_csv(autoaug_major, results / "autoaug_by_major.csv")

    valid_with_emp = valid[valid["emp"] > 0]
    wtd_mean = float(np.average(valid_with_emp["auto_avg"], weights=valid_with_emp["emp"])) if len(valid_with_emp) > 0 else valid["auto_avg"].mean()
    total_emp_autoaug = valid_with_emp["emp"].sum()
    n_above_2 = (valid_with_emp[valid_with_emp["auto_avg"] >= 2.0]["emp"].sum() / total_emp_autoaug * 100) if total_emp_autoaug > 0 else 0.0
    save_csv(pd.DataFrame([{
        "metric": "wtd_mean_score",
        "value": wtd_mean,
    }, {
        "metric": "pct_workers_score_ge_2",
        "value": n_above_2,
    }]), results / "autoaug_by_config.csv")

    # -- 3. Figures ------------------------------------------------------------

    # 3a. Butterfly chart
    fig_butterfly = _build_butterfly(conv_major, agentic_major)
    save_figure(fig_butterfly, results / "figures" / "agentic_vs_conversational.png")
    shutil.copy(results / "figures" / "agentic_vs_conversational.png",
                figs_dir / "agentic_vs_conversational.png")
    print("  agentic_vs_conversational.png")

    # 3b. Auto-aug distribution
    fig_dist = _build_autoaug_distribution(occ_autoaug)
    save_figure(fig_dist, results / "figures" / "autoaug_distribution.png")
    shutil.copy(results / "figures" / "autoaug_distribution.png",
                figs_dir / "autoaug_distribution.png")
    print("  autoaug_distribution.png")

    # 3c. Auto-aug by major
    fig_major = _build_autoaug_by_major(occ_autoaug)
    save_figure(fig_major, results / "figures" / "autoaug_by_major.png")
    shutil.copy(results / "figures" / "autoaug_by_major.png", figs_dir / "autoaug_by_major.png")
    print("  autoaug_by_major.png")

    # 3d. Mode scatter
    fig_scatter = _build_mode_scatter(conv_major, agentic_major)
    save_figure(fig_scatter, results / "figures" / "mode_workers_scatter.png")
    shutil.copy(results / "figures" / "mode_workers_scatter.png", figs_dir / "mode_workers_scatter.png")
    print("  mode_workers_scatter.png")

    # 3e. Workers drop: conversational -> agentic
    fig_workers_drop = _build_drop_chart(
        conv_major, agentic_major, "workers_affected",
        "Worker Reach Drop: Conversational → Agentic",
        x_label="Drop in Workers Affected (millions)",
    )
    save_figure(fig_workers_drop, results / "figures" / "agentic_workers_drop.png")
    shutil.copy(results / "figures" / "agentic_workers_drop.png", figs_dir / "agentic_workers_drop.png")
    print("  agentic_workers_drop.png")

    # 3f. Pct tasks drop: conversational -> agentic
    fig_pct_drop = _build_drop_chart(
        conv_major, agentic_major, "pct_tasks_affected",
        "Task Penetration Drop: Conversational → Agentic",
        x_label="Drop in % Tasks Affected (pp)",
    )
    save_figure(fig_pct_drop, results / "figures" / "agentic_pct_drop.png")
    shutil.copy(results / "figures" / "agentic_pct_drop.png", figs_dir / "agentic_pct_drop.png")
    print("  agentic_pct_drop.png")

    # 3g. Auto-aug by major across all configs (task-level)
    print("\n  Auto-aug by config (task-level)...")
    config_autoaug_dfs = []
    for ck in ANALYSIS_CONFIGS:
        print(f"    {ANALYSIS_CONFIG_LABELS[ck]}...")
        config_autoaug_dfs.append(get_autoaug_by_major_config(ck))
    all_config_autoaug = pd.concat(config_autoaug_dfs, ignore_index=True)
    save_csv(all_config_autoaug, results / "autoaug_by_major_config.csv")

    fig_aa_with = _build_autoaug_by_config(
        all_config_autoaug, "avg_auto_aug_with_vals",
        "Avg Auto-Aug by Sector × Config (Tasks With Values)",
        subtitle="Average auto_aug_mean across unique tasks that have a value | By dataset config",
    )
    save_figure(fig_aa_with, results / "figures" / "autoaug_by_config_with_vals.png")
    shutil.copy(results / "figures" / "autoaug_by_config_with_vals.png",
                figs_dir / "autoaug_by_config_with_vals.png")
    print("  autoaug_by_config_with_vals.png")

    fig_aa_all = _build_autoaug_by_config(
        all_config_autoaug, "avg_auto_aug_all",
        "Avg Auto-Aug by Sector × Config (All Tasks, Missing=0)",
        subtitle="Average auto_aug_mean across all unique tasks, NaN treated as 0 | By dataset config",
    )
    save_figure(fig_aa_all, results / "figures" / "autoaug_by_config_all.png")
    shutil.copy(results / "figures" / "autoaug_by_config_all.png",
                figs_dir / "autoaug_by_config_all.png")
    print("  autoaug_by_config_all.png")

    # -- 4. Summary ------------------------------------------------------------
    print("\n-- Mode totals --")
    for _, row in totals_df.iterrows():
        print(f"  {row['mode']}: {format_workers(row['workers_affected'])} workers, "
              f"{format_wages(row['wages_affected'])} wages")
    print(f"\n  Economy-wide wtd mean auto-aug score: {wtd_mean:.2f}/5.0")
    print(f"  Workers in occs with score >= 2.0: {n_above_2:.1f}%")

    # -- 5. PDF ----------------------------------------------------------------
    report_path = HERE / "ai_modes_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "ai_modes_report.pdf")

    print("\nai_modes: done.")


if __name__ == "__main__":
    main()
