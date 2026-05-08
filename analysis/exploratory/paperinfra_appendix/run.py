"""Appendix figures.

Two charts produced fresh by this run.py (no copying from elsewhere):

1. phys_zone_faceted — three panels (Physical | Mixed | Non-physical) of
   job zone violins, with per-row (job zone) and per-column (phys group)
   median + n labels in addition to per-cell annotations.

2. ska_full — element-level SKA chart for skills, abilities, knowledge,
   with the full ladder of workforce references (mean, P95, top-10). The
   Part 2 chart trims this down for readability in the main text; the
   appendix preserves the full version with abilities included at the
   element level.

Run from project root:
    venv/Scripts/python -m analysis.exploratory.paperinfra_appendix.run
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.config import (
    ANALYSIS_CONFIGS,
    ROOT,
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.data.compute_ska import load_ska_data
from analysis.utils import FONT_FAMILY, save_figure, save_csv
from analysis.paper.paper_config import (
    PAPER_W, PAPER_H,
    TITLE_FS, SUBTITLE_FS, LABEL_FS, TICK_FS, ANNOT_FS, LEGEND_FS,
    METRIC_COLORS, PAPER_PALETTE,
    style_paper_figure,
)

HERE = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

PRIMARY_KEY = "all_confirmed"
PRIMARY_DATASET = ANALYSIS_CONFIGS[PRIMARY_KEY]

PHYS_LOWER = 33.0
PHYS_UPPER = 67.0

# Order panels Physical → Mixed → Non-physical
OCC_GROUPS = ["Physical", "Mixed", "Non-physical"]
GROUP_COLORS = {
    "Non-physical": METRIC_COLORS["tasks"],
    "Mixed":        METRIC_COLORS["workers"],
    "Physical":     METRIC_COLORS["wages"],
}

ZONE_LABELS = {
    1: "Zone 1 — Little/No Prep",
    2: "Zone 2 — Some Prep",
    3: "Zone 3 — Medium Prep",
    4: "Zone 4 — Considerable Prep",
    5: "Zone 5 — Extensive Prep",
}
ZONE_COLORS = {
    1: "#b8cfe0", 2: "#8cafc5", 3: "#6090aa",
    4: "#3a6f8f", 5: "#1a4f73",
}

IMPORTANCE_THRESHOLD = 3.0
TOP_N_FOR_AVERAGE = 10


def _copy_fig(results: Path, figures: Path, name: str) -> None:
    shutil.copy(results / "figures" / name, figures / name)


def _load_occ_structural() -> pd.DataFrame:
    eco = pd.read_csv(DATA_DIR / "final_eco_2025.csv")
    occ = (
        eco.groupby("title_current")
        .agg(
            n_tasks=("physical", "count"),
            n_physical=("physical", "sum"),
            job_zone=("job_zone", "first"),
        )
        .reset_index()
    )
    occ["pct_physical"] = occ["n_physical"] / occ["n_tasks"] * 100
    occ["occ_group"] = "Mixed"
    occ.loc[occ["pct_physical"] < PHYS_LOWER, "occ_group"] = "Non-physical"
    occ.loc[occ["pct_physical"] > PHYS_UPPER, "occ_group"] = "Physical"
    return occ


def _occ_with_pct() -> pd.DataFrame:
    occ = _load_occ_structural()
    pct = get_pct_tasks_affected(PRIMARY_DATASET)
    occ["pct_tasks_affected"] = occ["title_current"].map(pct)
    occ = occ.dropna(subset=["pct_tasks_affected", "job_zone"])
    occ["job_zone"] = occ["job_zone"].astype(int)
    return occ


# ──────────────────────────────────────────────────────────────────────────
# Chart 1: phys_zone_faceted (modified)
# ──────────────────────────────────────────────────────────────────────────

def build_phys_zone_faceted(results: Path, figures: Path) -> None:
    occ = _occ_with_pct()
    zones = sorted(occ["job_zone"].unique())

    rows_csv = []
    for grp in OCC_GROUPS:
        for z in zones:
            sub = occ[(occ["occ_group"] == grp) & (occ["job_zone"] == z)]
            rows_csv.append({
                "occ_group": grp,
                "job_zone": z,
                "n_occs": len(sub),
                "median_pct": (round(float(sub["pct_tasks_affected"].median()), 1)
                               if len(sub) else None),
                "mean_pct": (round(float(sub["pct_tasks_affected"].mean()), 1)
                             if len(sub) else None),
            })
    save_csv(pd.DataFrame(rows_csv), results / "phys_zone_crosstab.csv")

    # Panel titles include column-level (group) n + median across all zones
    panel_titles: list[str] = []
    for grp in OCC_GROUPS:
        sub = occ[occ["occ_group"] == grp]
        med = sub["pct_tasks_affected"].median()
        panel_titles.append(
            f"{grp}<br><sub>n={len(sub)} · median {med:.0f}%</sub>"
        )

    fig = make_subplots(
        rows=1, cols=3,
        shared_yaxes=True,
        horizontal_spacing=0.05,
        subplot_titles=panel_titles,
    )

    y_labels = [f"Zone {z}" for z in zones]

    for col_idx, grp in enumerate(OCC_GROUPS, start=1):
        grp_df = occ[occ["occ_group"] == grp]
        for z in zones:
            sub = grp_df[grp_df["job_zone"] == z]
            label = f"Zone {z}"
            if len(sub) == 0:
                fig.add_trace(go.Scatter(
                    x=[None], y=[label],
                    mode="markers",
                    marker=dict(opacity=0),
                    showlegend=False, hoverinfo="skip",
                ), row=1, col=col_idx)
                continue
            fig.add_trace(go.Violin(
                x=sub["pct_tasks_affected"],
                y=[label] * len(sub),
                marker_color=ZONE_COLORS[z],
                line_color=ZONE_COLORS[z],
                fillcolor=ZONE_COLORS[z],
                opacity=0.7,
                box_visible=True,
                meanline_visible=True,
                orientation="h",
                side="positive",
                width=0.9,
                points=False,
                showlegend=False,
                name=f"{grp} — {label}",
                hovertemplate=f"{grp}, {label}<br>%{{x:.1f}}%<extra></extra>",
            ), row=1, col=col_idx)

        # Per-cell n + median annotation, parked at far left of each panel
        # (avoids overlapping the density tails which sit on the right).
        for z in zones:
            sub = grp_df[grp_df["job_zone"] == z]
            if len(sub) == 0:
                txt = "n=0"
            else:
                med = sub["pct_tasks_affected"].median()
                txt = f"n={len(sub)} · med {med:.0f}%"
            fig.add_annotation(
                x=2, y=f"Zone {z}",
                xref=f"x{'' if col_idx == 1 else col_idx}",
                yref=f"y{'' if col_idx == 1 else col_idx}",
                text=txt,
                showarrow=False,
                xanchor="left", yanchor="middle",
                font=dict(size=ANNOT_FS - 2,
                          color=PAPER_PALETTE["neutral"],
                          family=FONT_FAMILY),
                bgcolor="rgba(255,255,255,0.85)",
            )

    y_order = [f"Zone {z}" for z in reversed(zones)]
    for col_idx in range(1, 4):
        fig.update_yaxes(
            categoryorder="array",
            categoryarray=y_order,
            showgrid=False, showline=False,
            tickfont=dict(size=TICK_FS - 1, family=FONT_FAMILY),
            row=1, col=col_idx,
        )
        fig.update_xaxes(
            range=[0, 100], dtick=20,
            showgrid=True, gridcolor=PAPER_PALETTE["grid"],
            showline=True, linecolor=PAPER_PALETTE["grid"],
            row=1, col=col_idx,
        )
        if col_idx == 2:
            fig.update_xaxes(
                title=dict(text="% Tasks Affected", font=dict(size=LABEL_FS)),
                row=1, col=col_idx,
            )

    # Per-row (zone) summary label, anchored beside the y-axis on the left.
    # Pooled across all three panels.
    for z in zones:
        sub = occ[occ["job_zone"] == z]
        med = sub["pct_tasks_affected"].median()
        fig.add_annotation(
            x=-0.025, y=f"Zone {z}",
            xref="paper",
            yref="y",
            text=f"<b>n={len(sub)}</b><br>med {med:.0f}%",
            showarrow=False,
            xanchor="right", yanchor="middle", align="right",
            font=dict(size=ANNOT_FS - 1,
                      color=PAPER_PALETTE["neutral"],
                      family=FONT_FAMILY),
        )

    style_paper_figure(
        fig,
        "AI Exposure by Physical Mix × Preparation Level",
        subtitle=f"Job zone violins within each occupation group ({len(occ)} occupations)",
        height=720,
        width=PAPER_W + 80,
        margin=dict(l=160, r=60, t=140, b=80),
    )

    # Style the panel titles (kept smaller because they wrap)
    panel_title_set = set(panel_titles)
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in panel_title_set:
            ann.font = dict(size=LABEL_FS - 1, family=FONT_FAMILY,
                            color=PAPER_PALETTE["text"])

    save_figure(fig, results / "figures" / "phys_zone_faceted.png", scale=2)
    _copy_fig(results, figures, "phys_zone_faceted.png")
    print("  -> phys_zone_faceted.png")


# ──────────────────────────────────────────────────────────────────────────
# Chart 2: ska_full — original element-level SKA with full workforce ladder
# ──────────────────────────────────────────────────────────────────────────

def _compute_ska_variants(
    onet_df: pd.DataFrame,
    pct_series: pd.Series,
    type_name: str,
) -> pd.DataFrame:
    df = onet_df.copy()
    df["pct"] = df["title"].map(pct_series)
    df = df.dropna(subset=["pct", "importance", "level"])
    df = df[df["importance"] >= IMPORTANCE_THRESHOLD].copy()
    assert len(df) > 0, f"No {type_name} rows after importance filter"

    df["occ_score"] = df["importance"] * df["level"]
    df["ai_product"] = (df["pct"] / 100.0) * df["occ_score"]

    records: list[dict] = []
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
            "ai_95th":  float(ai_vals.quantile(0.95)) if n_ai >= 2 else (
                        float(ai_vals.iloc[0]) if n_ai == 1 else float("nan")),
            "ai_max":   float(ai_vals.max()) if n_ai >= 1 else float("nan"),
            "ai_top10": float(ai_vals.nlargest(top_n_ai).mean()) if n_ai >= 1 else float("nan"),
            "eco_max":  float(occ_vals.max()) if n_occ >= 1 else float("nan"),
            "eco_p95":  float(occ_vals.quantile(0.95)) if n_occ >= 2 else (
                        float(occ_vals.iloc[0]) if n_occ == 1 else float("nan")),
            "eco_top10": float(occ_vals.nlargest(top_n_occ).mean()) if n_occ >= 1 else float("nan"),
            "eco_mean": float(occ_vals.mean()) if n_occ >= 1 else float("nan"),
        })
    return pd.DataFrame(records)


def build_ska_full(results: Path, figures: Path) -> None:
    pct = get_pct_tasks_affected(PRIMARY_DATASET)
    ska_data = load_ska_data()

    elements_by_type: dict[str, pd.DataFrame] = {}
    for type_name, onet_df in [
        ("skills", ska_data.skills),
        ("knowledge", ska_data.knowledge),
        ("abilities", ska_data.abilities),
    ]:
        df = _compute_ska_variants(onet_df, pct, type_name)
        elements_by_type[type_name] = df
        print(f"    {type_name}: {len(df)} elements")

    save_csv(
        pd.concat(elements_by_type.values(), ignore_index=True),
        results / "ska_full.csv", float_format="%.4f",
    )

    TYPES = ["skills", "knowledge", "abilities"]
    TYPE_LABELS = {"skills": "Skills", "knowledge": "Knowledge", "abilities": "Abilities"}
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

    ai_marker_color = METRIC_COLORS["workers"]

    for row, type_name in enumerate(TYPES, start=1):
        df = elements_by_type[type_name].copy()
        df["sort_pct"] = df["ai_max"] / df["eco_max"].replace(0, float("nan")) * 100
        df = df.sort_values("sort_pct", ascending=False)

        enames = df["element_name"].tolist()
        ai_vals = df["ai_max"].fillna(0).tolist()
        ai_p95_vals = df["ai_95th"].fillna(0).tolist()
        ai_top10_vals = df["ai_top10"].fillna(0).tolist()
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

        fig.add_trace(go.Bar(
            y=enames, x=emax_vals, orientation="h",
            name="Workforce Max",
            marker=dict(color="#e8e8e2", line=dict(width=0)),
            showlegend=_show("emax"),
            hovertemplate="Max (workforce): %{x:.1f}<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Bar(
            y=enames, x=ai_vals, orientation="h",
            name="AI Maximum",
            marker=dict(color=METRIC_COLORS["tasks"], opacity=0.88, line=dict(width=0)),
            showlegend=_show("ai_max"),
            hovertemplate="AI Maximum: %{x:.1f}<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scatter(
            y=enames, x=ai_p95_vals, mode="markers",
            name="AI P95",
            marker=dict(color=ai_marker_color, symbol="circle", size=8,
                        line=dict(width=1.5, color=ai_marker_color)),
            showlegend=_show("ai_p95"),
            hovertemplate="AI P95: %{x:.1f}<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scatter(
            y=enames, x=ai_top10_vals, mode="markers",
            name="AI Top-10 Avg",
            marker=dict(color=ai_marker_color, symbol="diamond", size=8,
                        line=dict(width=1.5, color=ai_marker_color)),
            showlegend=_show("ai_top10"),
            hovertemplate="AI Top-10 avg: %{x:.1f}<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scatter(
            y=enames, x=ep95_vals, mode="markers",
            name="Workforce P95",
            marker=dict(color="#1a1a1a", symbol="line-ew", size=14,
                        line=dict(width=3, color="#1a1a1a")),
            showlegend=_show("ep95"),
            hovertemplate="Workforce P95: %{x:.1f}<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scatter(
            y=enames, x=etop10_vals, mode="markers",
            name="Workforce Top-10 Avg",
            marker=dict(color="#1a1a1a", symbol="diamond", size=7,
                        line=dict(width=1, color="#1a1a1a")),
            showlegend=_show("etop10"),
            hovertemplate="Workforce Top-10 avg: %{x:.1f}<extra></extra>",
        ), row=row, col=1)

        fig.add_trace(go.Scatter(
            y=enames, x=emean_vals, mode="markers",
            name="Workforce Mean",
            marker=dict(color="#1a1a1a", symbol="circle", size=7,
                        line=dict(width=1, color="#1a1a1a")),
            showlegend=_show("emean"),
            hovertemplate="Workforce mean: %{x:.1f}<extra></extra>",
        ), row=row, col=1)

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
                "AI Capability vs. Workforce Requirements — Full SKA element view"
                f"<br><span style='font-size:{SUBTITLE_FS}px;"
                f"color:{PAPER_PALETTE['muted']}'>"
                "Bar = AI Maximum, faint background = workforce max | "
                "Teal markers = AI P95 + Top-10 | Black markers = workforce P95 + Top-10 + Mean"
                "</span>"
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
        margin=dict(l=270, r=80, t=120, b=100),
    )

    type_label_set = {f"{TYPE_LABELS[t]}  ({counts[t]} elements)" for t in TYPES}
    for ann in fig.layout.annotations:
        if hasattr(ann, "text") and ann.text in type_label_set:
            ann.font = dict(size=LABEL_FS, family=FONT_FAMILY, color=PAPER_PALETTE["text"])

    save_figure(fig, results / "figures" / "ska_full.png", scale=2)
    _copy_fig(results, figures, "ska_full.png")
    print("  -> ska_full.png")


def write_markdown() -> None:
    md_path = HERE / "appendix_charts.md"
    md_path.write_text(
        "# Appendix figures\n"
        "\n"
        "Auxiliary charts not in the main results. Generated by `run.py`.\n"
        "\n"
        "---\n"
        "\n"
        "## phys_zone_faceted\n"
        "\n"
        "![phys_zone_faceted](figures/phys_zone_faceted.png)\n"
        "\n"
        "---\n"
        "\n"
        "## ska_full\n"
        "\n"
        "![ska_full](figures/ska_full.png)\n",
        encoding="utf-8",
    )
    print(f"  -> {md_path.relative_to(ROOT)}")


def main() -> None:
    results = ensure_results_dir(HERE)
    figures = HERE / "figures"
    figures.mkdir(exist_ok=True)

    print("=" * 60)
    print("Appendix figures")
    print("=" * 60)

    print("\n[1/2] phys_zone_faceted (modified)")
    build_phys_zone_faceted(results, figures)

    print("\n[2/2] ska_full (full element-level SKA)")
    build_ska_full(results, figures)

    print("\nWriting appendix_charts.md")
    write_markdown()

    print("\nDone — figures in results/figures/ and figures/")


if __name__ == "__main__":
    main()
