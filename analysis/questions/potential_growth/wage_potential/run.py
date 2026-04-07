"""
run.py — Potential Growth: Wage Potential

Which occupations and sectors have the highest economic value locked in
their adoption gap?

Wage gap = wages_affected(all_ceiling) − wages_affected(all_confirmed).
This is the dollar volume of wages associated with AI capabilities that
exist but aren't being deployed.

Key outputs:
  - Macro summary: aggregate confirmed vs ceiling wage totals
  - Ranked tables at major/minor/broad/occupation levels
  - Wage hotspots: top quartile on BOTH median wage AND pct_tasks_affected gap
  - IWA-level wage gap for work activities
  - Scatter: median_wage vs pct gap per occupation (the "where to look" chart)

Figures (key ones copied to figures/):
  macro_wage_summary.png       — Aggregate confirmed vs ceiling wages (5 configs)
  wage_gap_major.png           — Major categories by wages_affected gap (dumbbell)
  wage_gap_minor.png           — Top 20 minor categories by wages_affected gap
  wage_gap_occupation.png      — Top 30 occupations by wages_affected gap
  wage_hotspot_scatter.png     — Median wage vs pct gap, sized by employment
  wa_wage_gap_iwa.png          — Top 20 IWAs by wages_affected gap

Run from project root:
    venv/Scripts/python -m analysis.questions.potential_growth.wage_potential.run
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
    CATEGORY_PALETTE,
    COLORS,
    FONT_FAMILY,
    format_wages,
    format_workers,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent

PRIMARY_KEY = "all_confirmed"
CEILING_KEY = "all_ceiling"

AGG_COL_MAP = {
    "major": "major_occ_category",
    "minor": "minor_occ_category",
    "broad": "broad_occ",
    "occupation": "title_current",
}


# ── Data helpers ──────────────────────────────────────────────────────────────

def _get_occ_data(dataset_name: str, agg_level: str) -> pd.DataFrame:
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
    return df[["category", "pct_tasks_affected", "workers_affected", "wages_affected"]].copy()


def _get_wa_data(dataset_name: str, level: str = "iwa") -> pd.DataFrame:
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
    cols = ["category", "pct_tasks_affected", "workers_affected", "wages_affected"]
    return df[[c for c in cols if c in df.columns]].copy()


def _get_emp_wage_lookup() -> pd.DataFrame:
    """Return per-occupation employment and median wage (national)."""
    from backend.compute import get_explorer_occupations

    rows = []
    for occ in get_explorer_occupations():
        rows.append({
            "title_current": occ["title_current"],
            "emp_nat": occ.get("emp") or 0,
            "median_wage": occ.get("wage") or 0,
            "major": occ.get("major", ""),
        })
    return pd.DataFrame(rows)


def _compute_gap(confirmed_df: pd.DataFrame, ceiling_df: pd.DataFrame) -> pd.DataFrame:
    """Compute wage-focused gap table."""
    merged = confirmed_df.merge(
        ceiling_df, on="category", how="outer", suffixes=("_confirmed", "_ceiling")
    )
    for m in ["pct_tasks_affected", "workers_affected", "wages_affected"]:
        cc = f"{m}_confirmed"
        kc = f"{m}_ceiling"
        if cc not in merged.columns:
            merged[cc] = 0.0
        if kc not in merged.columns:
            merged[kc] = 0.0
        merged[cc] = merged[cc].fillna(0.0)
        merged[kc] = merged[kc].fillna(0.0)
        merged[f"{m}_gap"] = merged[kc] - merged[cc]
    return merged


# ── Figure builders ────────────────────────────────────────────────────────────

def _macro_summary_bar(macro_rows: list[dict]) -> go.Figure:
    """Grouped bar: confirmed vs ceiling wages across all 5 configs."""
    df = pd.DataFrame(macro_rows)
    configs = df["config_label"].tolist()
    confirmed_b = [w / 1e12 for w in df["wages_confirmed"]]
    ceiling_b = [w / 1e12 for w in df["wages_ceiling"]]
    gap_b = [w / 1e12 for w in df["wages_gap"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Confirmed Wages (Baseline)",
        x=configs,
        y=confirmed_b,
        marker_color=COLORS["primary"],
        text=[f"${v:.2f}T" for v in confirmed_b],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["primary"], family=FONT_FAMILY),
    ))
    fig.add_trace(go.Bar(
        name="Gap (Unrealized)",
        x=configs,
        y=gap_b,
        marker_color=COLORS["accent"],
        text=[f"+${v:.2f}T" for v in gap_b],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["accent"], family=FONT_FAMILY),
    ))
    style_figure(
        fig,
        "Wage Potential: Confirmed vs Ceiling — All Five Configs",
        subtitle="Stacked: confirmed baseline + unrealized gap | National | Freq | Auto-aug ON",
        x_title=None,
        y_title="Wages ($T)",
        height=580, width=1100,
        show_legend=True,
    )
    fig.update_layout(
        barmode="stack",
        bargap=0.3,
        xaxis=dict(tickfont=dict(size=10, family=FONT_FAMILY), tickangle=-15),
        yaxis=dict(gridcolor=COLORS["grid"], tickfont=dict(size=9)),
        margin=dict(l=60, r=40, t=80, b=120),
        legend=dict(
            orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        ),
    )
    return fig


def _wage_gap_dumbbell(gap_df: pd.DataFrame, level_label: str, top_n: int = 23,
                       sort_by_gap: bool = True) -> go.Figure:
    """Dumbbell: confirmed vs ceiling wages per category."""
    df = gap_df.copy()
    if sort_by_gap:
        df = df.sort_values("wages_affected_gap", ascending=False).head(top_n)
    df = df.sort_values("wages_affected_gap", ascending=True)

    categories = df["category"].tolist()
    confirmed_vals = df["wages_affected_confirmed"].tolist()
    ceiling_vals = df["wages_affected_ceiling"].tolist()

    def _fmt(v: float) -> str:
        if v >= 1e12:
            return f"${v / 1e12:.2f}T"
        if v >= 1e9:
            return f"${v / 1e9:.1f}B"
        if v >= 1e6:
            return f"${v / 1e6:.0f}M"
        return f"${v:,.0f}"

    fig = go.Figure()
    for i, cat in enumerate(categories):
        fig.add_shape(
            type="line",
            x0=confirmed_vals[i], x1=ceiling_vals[i],
            y0=i, y1=i,
            line=dict(color=COLORS["grid"], width=2),
            layer="below",
        )

    fig.add_trace(go.Scatter(
        x=confirmed_vals, y=categories,
        mode="markers+text",
        name="Confirmed",
        marker=dict(color=COLORS["primary"], size=10, line=dict(width=1, color=COLORS["bg"])),
        text=[_fmt(v) for v in confirmed_vals],
        textposition="middle left",
        textfont=dict(size=9, color=COLORS["primary"], family=FONT_FAMILY),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Confirmed: $%{x:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=ceiling_vals, y=categories,
        mode="markers+text",
        name="Ceiling",
        marker=dict(color=COLORS["secondary"], size=10, line=dict(width=1, color=COLORS["bg"])),
        text=[_fmt(v) for v in ceiling_vals],
        textposition="middle right",
        textfont=dict(size=9, color=COLORS["secondary"], family=FONT_FAMILY),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Ceiling: $%{x:,.0f}<extra></extra>",
    ))

    chart_h = max(500, len(categories) * 32 + 200)
    style_figure(
        fig,
        f"Wages: Confirmed vs Ceiling — {level_label}",
        subtitle="Gap = wage dollars associated with under-adopted AI capability",
        x_title="Wages Affected ($)",
        height=chart_h,
        show_legend=True,
    )
    fig.update_layout(
        margin=dict(l=20, r=130, t=80, b=120),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   tickfont=dict(size=9, color=COLORS["muted"])),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        legend=dict(
            orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5,
            font=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        ),
    )
    return fig


def _wage_gap_bar(gap_df: pd.DataFrame, level_label: str, top_n: int = 20) -> go.Figure:
    """Horizontal bar: wages_gap per category, top N."""
    df = gap_df.sort_values("wages_affected_gap", ascending=False).head(top_n)
    df = df.sort_values("wages_affected_gap", ascending=True)

    def _fmt(v: float) -> str:
        if v >= 1e9:
            return f"+${v / 1e9:.1f}B"
        return f"+${v / 1e6:.0f}M"

    fig = go.Figure(go.Bar(
        y=df["category"],
        x=df["wages_affected_gap"],
        orientation="h",
        marker=dict(color=COLORS["accent"], line=dict(width=0)),
        text=[_fmt(v) for v in df["wages_affected_gap"]],
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Wage gap: $%{x:,.0f}<extra></extra>",
    ))
    chart_h = max(450, len(df) * 32 + 200)
    style_figure(
        fig,
        f"Largest Wage Gaps — {level_label}",
        subtitle=f"Gap = Ceiling − Confirmed wages | Top {top_n} by wages gap",
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


def _hotspot_scatter(occ_gap_df: pd.DataFrame, emp_lookup: pd.DataFrame) -> go.Figure:
    """Scatter: pct_tasks_affected gap (x) vs median wage (y), sized by employment."""
    df = occ_gap_df.merge(
        emp_lookup.rename(columns={"title_current": "category"}),
        on="category", how="left",
    )
    df = df.dropna(subset=["median_wage", "pct_tasks_affected_gap"])
    df = df[df["pct_tasks_affected_gap"] > 0]
    df = df[df["median_wage"] > 0]

    # Normalize size
    max_emp = df["emp_nat"].max() if df["emp_nat"].max() > 0 else 1
    df["marker_size"] = (df["emp_nat"] / max_emp * 30 + 5).clip(upper=35)

    # Color by major category
    majors = df["major"].dropna().unique().tolist()
    color_map = {m: CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)] for i, m in enumerate(majors)}

    fig = go.Figure()
    for major in majors:
        sub = df[df["major"] == major]
        fig.add_trace(go.Scatter(
            x=sub["pct_tasks_affected_gap"],
            y=sub["median_wage"],
            mode="markers",
            name=major,
            marker=dict(
                color=color_map[major],
                size=sub["marker_size"].tolist(),
                opacity=0.65,
                line=dict(width=0.5, color=COLORS["bg"]),
            ),
            text=sub["category"],
            hovertemplate=(
                "<b>%{text}</b><br>Pct gap: %{x:.1f}pp<br>"
                "Median wage: $%{y:,.0f}<extra></extra>"
            ),
        ))

    # Reference lines at medians
    med_gap = df["pct_tasks_affected_gap"].median()
    med_wage = df["median_wage"].median()
    fig.add_vline(x=med_gap, line_dash="dot", line_color=COLORS["muted"], line_width=1,
                  annotation_text="Median gap", annotation_position="top",
                  annotation_font=dict(size=8, color=COLORS["muted"], family=FONT_FAMILY))
    fig.add_hline(y=med_wage, line_dash="dot", line_color=COLORS["muted"], line_width=1,
                  annotation_text="Median wage", annotation_position="right",
                  annotation_font=dict(size=8, color=COLORS["muted"], family=FONT_FAMILY))

    # Quadrant labels
    x_max = df["pct_tasks_affected_gap"].quantile(0.95)
    y_max = df["median_wage"].quantile(0.95)
    fig.add_annotation(
        x=x_max * 0.85, y=y_max * 0.85,
        text="<b>Wage hotspots</b><br>(high wage + big gap)",
        showarrow=False,
        font=dict(size=9, color=COLORS["accent"], family=FONT_FAMILY),
        align="center",
    )

    style_figure(
        fig,
        "Wage Hotspot Map — Every Occupation",
        subtitle="x = adoption gap (pp) | y = median annual wage | size = employment | color = sector",
        x_title="% Tasks Affected Gap (pp)",
        y_title="Median Annual Wage ($)",
        height=720, width=1100,
        show_legend=True,
    )
    fig.update_layout(
        margin=dict(l=70, r=40, t=80, b=120),
        legend=dict(
            orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5,
            font=dict(size=8, color=COLORS["neutral"], family=FONT_FAMILY),
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

    print("Wage Potential — generating outputs...\n")

    # ── 1. Macro summary across all 5 configs ─────────────────────────────────

    print("== Macro summary (all 5 configs) ==")
    macro_rows: list[dict] = []
    for config_key, dataset_name in ANALYSIS_CONFIGS.items():
        occ_df = _get_occ_data(dataset_name, "occupation")
        if occ_df.empty:
            continue
        # Get ceiling wages for this config
        ceil_occ = _get_occ_data(ceiling_ds, "occupation")
        wages_confirmed = occ_df["wages_affected"].sum()
        wages_ceiling = ceil_occ["wages_affected"].sum() if not ceil_occ.empty else 0
        macro_rows.append({
            "config_key": config_key,
            "config_label": ANALYSIS_CONFIG_LABELS[config_key],
            "wages_confirmed": wages_confirmed,
            "wages_ceiling": wages_ceiling,
            "wages_gap": wages_ceiling - wages_confirmed,
        })

    if macro_rows:
        macro_df = pd.DataFrame(macro_rows)
        save_csv(macro_df, results / "macro_summary.csv", float_format="%.0f")
        fig = _macro_summary_bar(macro_rows)
        save_figure(fig, fig_dir / "macro_wage_summary.png")
        # Print headline number
        row = macro_df[macro_df["config_key"] == PRIMARY_KEY]
        if not row.empty:
            gap = row.iloc[0]["wages_gap"]
            confirmed = row.iloc[0]["wages_confirmed"]
            print(f"  Primary gap: ${gap / 1e12:.2f}T unrealized | Confirmed: ${confirmed / 1e12:.2f}T")

    # ── 2. Occupation-hierarchy wage gaps ─────────────────────────────────────

    print("\n== Occupation-hierarchy wage gaps ==")
    emp_lookup = _get_emp_wage_lookup()

    for level in ["major", "minor", "broad", "occupation"]:
        level_label = level.replace("_", " ").title()
        if level == "broad":
            level_label = "Broad Occupation"

        print(f"  {level_label}...")
        confirmed_df = _get_occ_data(primary_ds, level)
        ceiling_df = _get_occ_data(ceiling_ds, level)
        if confirmed_df.empty or ceiling_df.empty:
            print(f"    SKIP")
            continue

        gap_df = _compute_gap(confirmed_df, ceiling_df)
        top_n_csv = 50 if level == "occupation" else 999
        save_csv(
            gap_df.sort_values("wages_affected_gap", ascending=False).head(top_n_csv),
            results / f"wage_gap_{level}.csv",
        )

        if level == "major":
            fig = _wage_gap_dumbbell(gap_df, "Major Category", top_n=23, sort_by_gap=False)
            save_figure(fig, fig_dir / "wage_gap_major.png")

        elif level == "minor":
            fig = _wage_gap_bar(gap_df, "Minor Category", top_n=20)
            save_figure(fig, fig_dir / "wage_gap_minor.png")

        elif level == "broad":
            fig = _wage_gap_bar(gap_df, "Broad Occupation", top_n=20)
            save_figure(fig, fig_dir / "wage_gap_broad.png")

        elif level == "occupation":
            fig = _wage_gap_bar(gap_df, "Occupation", top_n=30)
            save_figure(fig, fig_dir / "wage_gap_occupation.png")

            # Wage hotspot identification
            q75_wage = emp_lookup["median_wage"].quantile(0.75)
            q75_gap = gap_df["pct_tasks_affected_gap"].quantile(0.75)
            hotspot_df = gap_df.merge(
                emp_lookup.rename(columns={"title_current": "category"}),
                on="category", how="left",
            )
            hotspots = hotspot_df[
                (hotspot_df["median_wage"] >= q75_wage) &
                (hotspot_df["pct_tasks_affected_gap"] >= q75_gap)
            ].sort_values("wages_affected_gap", ascending=False)
            save_csv(hotspots, results / "wage_hotspots.csv")
            print(f"  Wage hotspots: {len(hotspots)} occupations "
                  f"(>= ${q75_wage:,.0f} wage AND >= {q75_gap:.1f}pp gap)")

            # Hotspot scatter
            fig = _hotspot_scatter(gap_df, emp_lookup)
            save_figure(fig, fig_dir / "wage_hotspot_scatter.png")

    # ── 3. Work activity wage gaps (IWA level) ────────────────────────────────

    print("\n== Work activity wage gaps (IWA) ==")
    for level in ["gwa", "iwa"]:
        confirmed_wa = _get_wa_data(primary_ds, level)
        ceiling_wa = _get_wa_data(ceiling_ds, level)
        if confirmed_wa.empty or ceiling_wa.empty:
            print(f"  SKIP {level}")
            continue
        gap_df = _compute_gap(confirmed_wa, ceiling_wa)
        save_csv(
            gap_df.sort_values("wages_affected_gap", ascending=False).head(30),
            results / f"wa_wage_gap_{level}.csv",
        )
        if level == "iwa":
            fig = _wage_gap_bar(gap_df, "IWA", top_n=20)
            save_figure(fig, fig_dir / "wa_wage_gap_iwa.png")
            print(f"  IWA: {len(gap_df)} activities")

    # ── 4. Copy key figures ───────────────────────────────────────────────────

    print("\n== Copying key figures ==")
    key_figs = [
        "macro_wage_summary.png",
        "wage_gap_major.png",
        "wage_gap_minor.png",
        "wage_gap_occupation.png",
        "wage_hotspot_scatter.png",
        "wa_wage_gap_iwa.png",
    ]
    for fname in key_figs:
        src = fig_dir / fname
        if src.exists():
            shutil.copy2(src, committed_figs / fname)
            print(f"  Copied {fname}")
        else:
            print(f"  SKIP: {fname}")

    # ── 5. Generate PDF ───────────────────────────────────────────────────────

    print("\n== Generating PDF ==")
    md_path = HERE / "wage_potential_report.md"
    pdf_path = results / "wage_potential_report.pdf"
    if md_path.exists():
        generate_pdf(md_path, pdf_path)
        print(f"  Saved {pdf_path.name}")
    else:
        print(f"  SKIP — report not yet written")

    print("\nDone.")


if __name__ == "__main__":
    main()
