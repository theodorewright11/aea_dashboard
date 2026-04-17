"""
Part 2 — Characterization: Where AI Exposure Falls

Five chart groups characterizing the structural distribution of AI exposure:
1. Physical/Informational Divide: box plots of % tasks affected by occ group
2. Job Zone: violin plots of % tasks affected by job zone (1–5)
3. SKA Levels: AI max bar + workforce markers for every SKA element (3 subplots)
4. Work Activities: all GWAs ranked by % tasks affected, colored by workers
5. Major Categories: all 22 majors, three side-by-side panels (pct/workers/wages)

Run from project root:
    venv/Scripts/python -m analysis.paper.results.part_2.run
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

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
    TITLE_FS, SUBTITLE_FS, INSIDE_FS, OUTSIDE_FS, TICK_FS, LABEL_FS,
    LEGEND_FS, ANNOT_FS,
    METRIC_COLORS, PAPER_PALETTE,
    style_paper_figure, fmt_wages, fmt_workers,
)

HERE = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

PRIMARY_KEY = "all_confirmed"
PRIMARY_DATASET = ANALYSIS_CONFIGS[PRIMARY_KEY]
PRIMARY_LABEL = ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]
CONFIG_SUBTITLE = f"{PRIMARY_LABEL} | National | freq, auto-aug ON"

# Physical/informational thresholds (matches exploratory)
PHYS_LOWER = 33.0
PHYS_UPPER = 67.0
OCC_GROUPS = ["Non-physical", "Mixed", "Physical"]
GROUP_COLORS = {
    "Non-physical": METRIC_COLORS["tasks"],    # Slate blue
    "Mixed":        METRIC_COLORS["workers"],   # Sage teal
    "Physical":     METRIC_COLORS["wages"],     # Warm tan
}

# Job zone labels
ZONE_LABELS = {
    1: "Zone 1 — Little/No Prep",
    2: "Zone 2 — Some Prep",
    3: "Zone 3 — Medium Prep",
    4: "Zone 4 — Considerable Prep",
    5: "Zone 5 — Extensive Prep",
}

# SKA constants
IMPORTANCE_THRESHOLD = 3.0
TOP_N_FOR_AVERAGE = 10
SKA_LABEL_MAX = 45


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────

def _copy_fig(results: Path, figures: Path, name: str) -> None:
    shutil.copy(results / "figures" / name, figures / name)


def _run_config(dataset_name: str, agg_level: str = "occupation") -> pd.DataFrame:
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
    assert data is not None, f"No data for {dataset_name}"
    df: pd.DataFrame = data["df"]
    group_col: str = data["group_col"]
    df = df.rename(columns={group_col: "category"})
    return df


def _get_national_totals() -> tuple[float, float]:
    from backend.compute import load_eco_raw
    eco = load_eco_raw()
    occ = eco.drop_duplicates(subset=["title_current"])
    total_emp = float(occ["emp_tot_nat_2024"].sum())
    total_wages = float((occ["emp_tot_nat_2024"] * occ["a_med_nat_2024"]).sum())
    return total_emp, total_wages


def _load_occ_structural() -> pd.DataFrame:
    """Load eco_2025 and compute per-occupation structural data:
    pct_physical, occ_group, job_zone.
    """
    eco = pd.read_csv(DATA_DIR / "final_eco_2025.csv")
    assert "title_current" in eco.columns
    assert "physical" in eco.columns
    assert "job_zone" in eco.columns

    occ = (
        eco.groupby("title_current")
        .agg(
            n_tasks=("physical", "count"),
            n_physical=("physical", "sum"),
            job_zone=("job_zone", "first"),
            emp=("emp_tot_nat_2024", "first"),
            wage=("a_med_nat_2024", "first"),
        )
        .reset_index()
    )
    occ["pct_physical"] = occ["n_physical"] / occ["n_tasks"] * 100

    occ["occ_group"] = "Mixed"
    occ.loc[occ["pct_physical"] < PHYS_LOWER, "occ_group"] = "Non-physical"
    occ.loc[occ["pct_physical"] > PHYS_UPPER, "occ_group"] = "Physical"

    return occ


def _get_wa_data(dataset_name: str, level: str = "gwa") -> pd.DataFrame:
    """Get work activity exposure for one pre-combined dataset."""
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
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────
# Chart 1: Physical / Informational Divide
# ─────────────────────────────────────────────────────────────────────────

def build_phys_info_divide(results: Path, figures: Path) -> None:
    occ = _load_occ_structural()
    pct = get_pct_tasks_affected(PRIMARY_DATASET)

    occ["pct_tasks_affected"] = occ["title_current"].map(pct)
    occ = occ.dropna(subset=["pct_tasks_affected"])

    # Summary stats for CSV
    summary_rows = []
    for grp in OCC_GROUPS:
        sub = occ[occ["occ_group"] == grp]
        summary_rows.append({
            "occ_group": grp,
            "n_occs": len(sub),
            "median_pct": round(float(sub["pct_tasks_affected"].median()), 1),
            "mean_pct": round(float(sub["pct_tasks_affected"].mean()), 1),
            "q25": round(float(sub["pct_tasks_affected"].quantile(0.25)), 1),
            "q75": round(float(sub["pct_tasks_affected"].quantile(0.75)), 1),
        })
    save_csv(pd.DataFrame(summary_rows), results / "phys_info_summary.csv")

    # Box plot
    fig = go.Figure()

    for grp in OCC_GROUPS:
        subset = occ[occ["occ_group"] == grp]
        fig.add_trace(go.Box(
            x=subset["pct_tasks_affected"],
            name=f"{grp}  (n={len(subset)})",
            marker_color=GROUP_COLORS[grp],
            line_color=GROUP_COLORS[grp],
            fillcolor=GROUP_COLORS[grp],
            opacity=0.7,
            boxmean=True,
            orientation="h",
        ))

    fig.update_layout(
        yaxis=dict(
            categoryorder="array",
            categoryarray=[
                f"{g}  (n={int(occ[occ['occ_group'] == g].shape[0])})"
                for g in reversed(OCC_GROUPS)
            ],
        ),
    )

    style_paper_figure(
        fig,
        "AI Task Exposure Is Structurally Higher in Non-Physical Occupations",
        subtitle=(
            f"Distribution of % tasks affected across {len(occ)} occupations | "
            f"{CONFIG_SUBTITLE}"
        ),
        height=420,
        width=PAPER_W,
        margin=dict(l=20, r=60, t=90, b=70),
    )

    fig.update_layout(showlegend=False)

    fig.update_xaxes(
        title=dict(text="% Tasks Affected", font=dict(size=LABEL_FS)),
        range=[0, 100], dtick=10,
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        showline=True, linecolor=PAPER_PALETTE["grid"],
    )
    fig.update_yaxes(
        showgrid=False, showline=False,
        tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
    )

    save_figure(fig, results / "figures" / "phys_info_divide.png")
    _copy_fig(results, figures, "phys_info_divide.png")
    print("  -> phys_info_divide.png")


# ─────────────────────────────────────────────────────────────────────────
# Chart 2: Job Zone Violin
# ─────────────────────────────────────────────────────────────────────────

def build_job_zone_violin(results: Path, figures: Path) -> None:
    occ = _load_occ_structural()
    pct = get_pct_tasks_affected(PRIMARY_DATASET)

    occ["pct_tasks_affected"] = occ["title_current"].map(pct)
    occ = occ.dropna(subset=["pct_tasks_affected", "job_zone"])
    occ["job_zone"] = occ["job_zone"].astype(int)

    # Summary stats
    zone_stats = []
    for z in sorted(occ["job_zone"].unique()):
        sub = occ[occ["job_zone"] == z]
        zone_stats.append({
            "job_zone": z,
            "n_occs": len(sub),
            "median_pct": round(float(sub["pct_tasks_affected"].median()), 1),
            "mean_pct": round(float(sub["pct_tasks_affected"].mean()), 1),
            "q25": round(float(sub["pct_tasks_affected"].quantile(0.25)), 1),
            "q75": round(float(sub["pct_tasks_affected"].quantile(0.75)), 1),
        })
    stats_df = pd.DataFrame(zone_stats)
    save_csv(stats_df, results / "job_zone_summary.csv")

    # Color gradient: Zone 1 lightest, Zone 5 darkest
    zone_colors = {
        1: "#b8cfe0",  # Light slate
        2: "#8cafc5",
        3: "#6090aa",
        4: "#3a6f8f",
        5: "#1a4f73",  # Deep slate
    }

    fig = go.Figure()

    zones = sorted(occ["job_zone"].unique())
    for z in zones:
        sub = occ[occ["job_zone"] == z]
        n = len(sub)
        med = sub["pct_tasks_affected"].median()
        mean = sub["pct_tasks_affected"].mean()
        label = ZONE_LABELS.get(z, f"Zone {z}")

        fig.add_trace(go.Violin(
            x=sub["pct_tasks_affected"],
            name=f"{label}  (n={n})",
            marker_color=zone_colors[z],
            line_color=zone_colors[z],
            fillcolor=zone_colors[z],
            opacity=0.7,
            box_visible=True,
            meanline_visible=True,
            orientation="h",
            side="positive",
            width=0.8,
        ))

    fig.update_layout(
        yaxis=dict(
            categoryorder="array",
            categoryarray=[
                f"{ZONE_LABELS.get(z, f'Zone {z}')}  (n={int(occ[occ['job_zone'] == z].shape[0])})"
                for z in reversed(zones)
            ],
        ),
    )

    # Add annotation with stats
    annot_lines = []
    for row in zone_stats:
        z = row["job_zone"]
        annot_lines.append(
            f"Zone {z}: median {row['median_pct']:.1f}%, "
            f"mean {row['mean_pct']:.1f}%"
        )
    annot_text = "<br>".join(annot_lines)

    fig.add_annotation(
        text=annot_text,
        xref="paper", yref="paper",
        x=0.98, y=0.02,
        showarrow=False,
        font=dict(size=ANNOT_FS, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        align="right",
        xanchor="right", yanchor="bottom",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor=PAPER_PALETTE["grid"],
        borderwidth=1,
        borderpad=6,
    )

    style_paper_figure(
        fig,
        "AI Exposure Peaks at Job Zone 4 (Considerable Preparation)",
        subtitle=(
            f"Distribution of % tasks affected by O*NET job zone across "
            f"{len(occ)} occupations | {CONFIG_SUBTITLE}"
        ),
        height=580,
        width=PAPER_W,
        margin=dict(l=20, r=60, t=90, b=70),
    )

    fig.update_layout(showlegend=False)

    fig.update_xaxes(
        title=dict(text="% Tasks Affected", font=dict(size=LABEL_FS)),
        range=[0, 100], dtick=10,
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        showline=True, linecolor=PAPER_PALETTE["grid"],
    )
    fig.update_yaxes(
        showgrid=False, showline=False,
        tickfont=dict(size=TICK_FS - 1, family=FONT_FAMILY),
    )

    save_figure(fig, results / "figures" / "job_zone_violin.png")
    _copy_fig(results, figures, "job_zone_violin.png")
    print("  -> job_zone_violin.png")


# ─────────────────────────────────────────────────────────────────────────
# Chart 3: SKA Levels
# ─────────────────────────────────────────────────────────────────────────

def _compute_ska_variants(
    onet_df: pd.DataFrame,
    pct_series: pd.Series,
    type_name: str,
) -> pd.DataFrame:
    """Compute AI and workforce imp×lv variants per element for one SKA type."""
    df = onet_df.copy()
    df["pct"] = df["title"].map(pct_series)
    df = df.dropna(subset=["pct", "importance", "level"])
    df = df[df["importance"] >= IMPORTANCE_THRESHOLD].copy()
    assert len(df) > 0, f"No {type_name} rows after importance filter"

    df["occ_score"] = df["importance"] * df["level"]
    df["ai_product"] = (df["pct"] / 100.0) * df["occ_score"]

    records = []
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
            "ai_95th": float(ai_vals.quantile(0.95)) if n_ai >= 2 else (float(ai_vals.iloc[0]) if n_ai == 1 else float("nan")),
            "ai_max": float(ai_vals.max()) if n_ai >= 1 else float("nan"),
            "ai_top10": float(ai_vals.nlargest(top_n_ai).mean()) if n_ai >= 1 else float("nan"),
            "eco_max": float(occ_vals.max()) if n_occ >= 1 else float("nan"),
            "eco_p95": float(occ_vals.quantile(0.95)) if n_occ >= 2 else (float(occ_vals.iloc[0]) if n_occ == 1 else float("nan")),
            "eco_top10": float(occ_vals.nlargest(top_n_occ).mean()) if n_occ >= 1 else float("nan"),
            "eco_mean": float(occ_vals.mean()) if n_occ >= 1 else float("nan"),
        })

    return pd.DataFrame(records)


def build_ska_levels(results: Path, figures: Path) -> None:
    pct = get_pct_tasks_affected(PRIMARY_DATASET)
    ska_data = load_ska_data()

    elements_by_type: dict[str, pd.DataFrame] = {}
    for type_name, onet_df in [
        ("skills", ska_data.skills),
        ("abilities", ska_data.abilities),
        ("knowledge", ska_data.knowledge),
    ]:
        df = _compute_ska_variants(onet_df, pct, type_name)
        elements_by_type[type_name] = df
        print(f"    {type_name}: {len(df)} elements")

    # Save CSV
    all_df = pd.concat(elements_by_type.values(), ignore_index=True)
    save_csv(all_df, results / "ska_levels.csv", float_format="%.4f")

    # Build the figure
    TYPES = ["skills", "abilities", "knowledge"]
    TYPE_LABELS = {"skills": "Skills", "abilities": "Abilities", "knowledge": "Knowledge"}
    ai_col = "ai_max"
    ai_label = "AI Maximum"

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

    for row, type_name in enumerate(TYPES, start=1):
        df = elements_by_type[type_name].copy()
        df["sort_pct"] = df[ai_col] / df["eco_max"].replace(0, float("nan")) * 100
        df = df.sort_values("sort_pct", ascending=False)

        enames = df["element_name"].tolist()
        ai_vals = df[ai_col].fillna(0).tolist()
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

        # Workforce max background bar (light gray)
        fig.add_trace(go.Bar(
            y=enames, x=emax_vals, orientation="h",
            name="Workforce Max",
            marker=dict(color="#e8e8e2", line=dict(width=0)),
            showlegend=_show("emax"),
            hovertemplate="Max (workforce): %{x:.1f}<extra></extra>",
        ), row=row, col=1)

        # AI max bar (paper primary color)
        fig.add_trace(go.Bar(
            y=enames, x=ai_vals, orientation="h",
            name=ai_label,
            marker=dict(color=METRIC_COLORS["tasks"], opacity=0.88, line=dict(width=0)),
            showlegend=_show(ai_col),
            hovertemplate=f"{ai_label}: %{{x:.1f}}<extra></extra>",
        ), row=row, col=1)

        # Workforce P95 marker — dark tick
        fig.add_trace(go.Scatter(
            y=enames, x=ep95_vals, mode="markers",
            name="Workforce P95",
            marker=dict(color="#1a1a1a", symbol="line-ew", size=14, line=dict(width=3, color="#1a1a1a")),
            showlegend=_show("ep95"),
            hovertemplate="P95 (workforce): %{x:.1f}<extra></extra>",
        ), row=row, col=1)

        # Workforce Top-10 marker — diamond
        fig.add_trace(go.Scatter(
            y=enames, x=etop10_vals, mode="markers",
            name="Workforce Top-10 Avg",
            marker=dict(color="#1a1a1a", symbol="diamond", size=7, line=dict(width=1, color="#1a1a1a")),
            showlegend=_show("etop10"),
            hovertemplate="Top-10 avg (workforce): %{x:.1f}<extra></extra>",
        ), row=row, col=1)

        # Workforce Mean marker — circle
        fig.add_trace(go.Scatter(
            y=enames, x=emean_vals, mode="markers",
            name="Workforce Mean",
            marker=dict(color="#1a1a1a", symbol="circle", size=7, line=dict(width=1, color="#1a1a1a")),
            showlegend=_show("emean"),
            hovertemplate="Economy mean (workforce): %{x:.1f}<extra></extra>",
        ), row=row, col=1)

        # Percentage column
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
                f"AI Capability vs. Workforce Requirements Across SKA Elements"
                f"<br><span style='font-size:{SUBTITLE_FS}px;"
                f"color:{PAPER_PALETTE['muted']}'>"
                f"AI Maximum of (pct/100 × imp × lv) | {CONFIG_SUBTITLE} | "
                f"Importance ≥ 3 | Sorted by AI as % of workforce max"
                f"</span>"
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
        margin=dict(l=270, r=80, t=90, b=100),
    )

    # Style subplot titles
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and any(ann.text.startswith(TYPE_LABELS[t]) for t in TYPES):
            ann.font = dict(size=LABEL_FS, family=FONT_FAMILY, color=PAPER_PALETTE["text"])

    save_figure(fig, results / "figures" / "ska_levels.png", scale=2)
    _copy_fig(results, figures, "ska_levels.png")
    print("  -> ska_levels.png")


# ─────────────────────────────────────────────────────────────────────────
# Chart 4: All GWAs by % Tasks Affected
# ─────────────────────────────────────────────────────────────────────────

def build_gwa_chart(results: Path, figures: Path) -> None:
    gwa_df = _get_wa_data(PRIMARY_DATASET, "gwa")
    assert not gwa_df.empty, "No GWA data returned"

    gwa_df = gwa_df.sort_values("pct_tasks_affected", ascending=True)
    save_csv(gwa_df, results / "gwa_exposure.csv")

    n_gwas = len(gwa_df)
    categories = gwa_df["category"].tolist()
    pct_vals = gwa_df["pct_tasks_affected"].tolist()
    workers_vals = gwa_df["workers_affected"].tolist()
    wages_vals = gwa_df["wages_affected"].tolist()

    # Color gradient: map workers_affected to color intensity
    w_min = min(workers_vals)
    w_max = max(workers_vals)
    w_range = w_max - w_min if w_max > w_min else 1.0

    def _workers_color(w: float) -> str:
        """Interpolate from light to dark based on workers_affected."""
        t = (w - w_min) / w_range
        # Interpolate between light (#b8cfe0) and dark (#1a4f73) in the slate blue range
        r = int(184 + t * (26 - 184))
        g = int(207 + t * (79 - 207))
        b = int(224 + t * (115 - 224))
        return f"rgb({r},{g},{b})"

    bar_colors = [_workers_color(w) for w in workers_vals]

    # Annotations: workers + wages outside the bar
    annotations = [
        f"{fmt_workers(w)} workers, {fmt_wages(wg)} wages"
        for w, wg in zip(workers_vals, wages_vals)
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=categories,
        x=pct_vals,
        orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"{v:.1f}%" for v in pct_vals],
        textposition="inside",
        insidetextanchor="end",
        textfont=dict(size=INSIDE_FS - 5, color="white", family=FONT_FAMILY),
        cliponaxis=False,
        showlegend=False,
        hovertemplate="%{y}<br>%{x:.1f}% tasks<extra></extra>",
    ))

    # Add workers + wages annotations outside bars
    fig.add_trace(go.Scatter(
        y=categories,
        x=[v + 1.5 for v in pct_vals],
        mode="text",
        text=annotations,
        textposition="middle right",
        textfont=dict(size=ANNOT_FS, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showlegend=False,
        hoverinfo="skip",
    ))

    height = max(PAPER_H + 200, n_gwas * 26 + 200)

    style_paper_figure(
        fig,
        "AI Task Exposure Across All General Work Activities",
        subtitle=(
            f"% tasks affected per GWA | Darker = more workers affected | "
            f"{CONFIG_SUBTITLE}"
        ),
        height=height,
        width=PAPER_W,
        margin=dict(l=20, r=300, t=90, b=70),
    )

    fig.update_xaxes(
        title=dict(text="% Tasks Affected", font=dict(size=LABEL_FS)),
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        showline=True, linecolor=PAPER_PALETTE["grid"],
        ticksuffix="%",
    )
    fig.update_yaxes(
        showgrid=False, showline=False,
        tickfont=dict(size=TICK_FS - 2, family=FONT_FAMILY),
    )

    save_figure(fig, results / "figures" / "gwa_exposure.png", scale=2)
    _copy_fig(results, figures, "gwa_exposure.png")
    print("  -> gwa_exposure.png")


# ─────────────────────────────────────────────────────────────────────────
# Chart 5: All 22 Major Categories — 3 Side-by-Side Panels
# ─────────────────────────────────────────────────────────────────────────

def build_major_categories(results: Path, figures: Path) -> None:
    df = _run_config(PRIMARY_DATASET, "major")
    assert not df.empty, "No major category data"

    # Sort by pct_tasks_affected descending for consistent ordering
    df = df.sort_values("pct_tasks_affected", ascending=False).reset_index(drop=True)
    save_csv(df, results / "major_categories.csv")

    categories = df["category"].tolist()
    pct_vals = df["pct_tasks_affected"].tolist()
    workers_vals = df["workers_affected"].tolist()
    wages_vals = df["wages_affected"].tolist()

    # Reverse for Plotly (top = first) — we want highest at top
    categories_r = list(reversed(categories))
    pct_r = list(reversed(pct_vals))
    workers_r = list(reversed(workers_vals))
    wages_r = list(reversed(wages_vals))

    n_cats = len(categories)

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=["% Tasks Affected", "Workers Affected", "Wages Affected"],
        horizontal_spacing=0.12,
        shared_yaxes=True,
    )

    # Panel 1: % Tasks Affected
    fig.add_trace(go.Bar(
        y=categories_r, x=pct_r, orientation="h",
        name="% Tasks Affected",
        marker=dict(color=METRIC_COLORS["tasks"], line=dict(width=0)),
        text=[f"{v:.1f}%" for v in pct_r],
        textposition="outside",
        textfont=dict(size=ANNOT_FS, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showlegend=False,
        cliponaxis=False,
    ), row=1, col=1)

    # Panel 2: Workers Affected
    fig.add_trace(go.Bar(
        y=categories_r, x=workers_r, orientation="h",
        name="Workers Affected",
        marker=dict(color=METRIC_COLORS["workers"], line=dict(width=0)),
        text=[fmt_workers(v) for v in workers_r],
        textposition="outside",
        textfont=dict(size=ANNOT_FS, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showlegend=False,
        cliponaxis=False,
    ), row=1, col=2)

    # Panel 3: Wages Affected
    fig.add_trace(go.Bar(
        y=categories_r, x=wages_r, orientation="h",
        name="Wages Affected",
        marker=dict(color=METRIC_COLORS["wages"], line=dict(width=0)),
        text=[fmt_wages(v) for v in wages_r],
        textposition="outside",
        textfont=dict(size=ANNOT_FS, color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        showlegend=False,
        cliponaxis=False,
    ), row=1, col=3)

    height = max(PAPER_H + 200, n_cats * 32 + 200)

    style_paper_figure(
        fig,
        "AI Exposure by Major Occupational Category",
        subtitle=CONFIG_SUBTITLE,
        height=height,
        width=PAPER_W + 200,
        margin=dict(l=20, r=100, t=90, b=50),
    )

    # Style each panel's axes
    fig.update_xaxes(showgrid=False, showticklabels=False, showline=False, zeroline=False)
    fig.update_yaxes(showgrid=False, showline=False)

    # Y-axis labels only on first panel
    fig.update_yaxes(
        tickfont=dict(size=TICK_FS - 2, family=FONT_FAMILY),
        row=1, col=1,
    )

    # Style subplot titles
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in ["% Tasks Affected", "Workers Affected", "Wages Affected"]:
            ann.font = dict(size=LABEL_FS, family=FONT_FAMILY, color=PAPER_PALETTE["text"])

    fig.update_layout(bargap=0.3)

    save_figure(fig, results / "figures" / "major_categories.png", scale=2)
    _copy_fig(results, figures, "major_categories.png")
    print("  -> major_categories.png")


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figures = HERE / "figures"
    figures.mkdir(exist_ok=True)

    print("=" * 60)
    print("Part 2: Characterization — Where AI Exposure Falls")
    print("=" * 60)

    print("\n[1/5] Physical / Informational Divide")
    build_phys_info_divide(results, figures)

    print("\n[2/5] Job Zone Violin")
    build_job_zone_violin(results, figures)

    print("\n[3/5] SKA Levels (AI Max)")
    build_ska_levels(results, figures)

    print("\n[4/5] Work Activities (GWA)")
    build_gwa_chart(results, figures)

    print("\n[5/5] Major Occupational Categories")
    build_major_categories(results, figures)

    print("\n" + "=" * 60)
    print("Part 2 complete — figures in results/figures/ and figures/")
    print("=" * 60)


if __name__ == "__main__":
    main()
