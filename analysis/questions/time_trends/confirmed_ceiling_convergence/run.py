"""
run.py — Time Trends: Confirmed vs. Ceiling Convergence

Asks: is the gap between what AI is confirmed doing and what it demonstrably
can do narrowing over time, or are confirmed and ceiling growing in parallel?

Strategy:
  - At each shared date, compare all_confirmed and all_ceiling pct_tasks_affected
    at occupation level, then aggregate to major sector
  - The confirmed/ceiling ratio tells us what fraction of the capability
    ceiling is actually being activated (deployment efficiency)
  - If ratio is rising over time: deployment is catching up
  - If ratio is stable/falling: capability keeps outrunning adoption

Shared dates: all_ceiling series covers all all_confirmed dates (Sep 2024
onward). We use only dates present in BOTH series.

Run from project root:
    venv/Scripts/python -m analysis.questions.time_trends.confirmed_ceiling_convergence.run
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from analysis.config import (
    ANALYSIS_CONFIG_SERIES,
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.utils import (
    CATEGORY_PALETTE,
    COLORS,
    FONT_FAMILY,
    generate_pdf,
    make_line_chart,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent


def _date(ds: str) -> str:
    return ds.rsplit(" ", 1)[-1]


def get_major_pct(dataset_name: str) -> pd.Series:
    """Return pct_tasks_affected by major category (weighted by employment)."""
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
    if data is None:
        return pd.Series(dtype=float)
    df = data["df"].rename(columns={"major_occ_category": "category"})
    return df.set_index("category")["pct_tasks_affected"]


def get_national_pct(dataset_name: str, eco_emp: "pd.Series") -> float:
    """Return employment-weighted average pct_tasks_affected across all occupations.

    eco_emp is a pd.Series keyed by title_current → nat employment (from eco_2025).
    """
    pct = get_pct_tasks_affected(dataset_name)
    # Align on shared occupations
    joined = pct.to_frame("pct").join(eco_emp.rename("emp"), how="inner")
    if joined.empty or joined["emp"].sum() == 0:
        return 0.0
    return float((joined["pct"] * joined["emp"]).sum() / joined["emp"].sum())


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    # ── 0. Load eco employment weights once ──────────────────────────────────
    from backend.compute import load_eco_raw
    eco = load_eco_raw()
    emp_col = "emp_tot_nat_2024"
    eco_emp = (
        eco.drop_duplicates("title_current")
        .set_index("title_current")[emp_col]
        .fillna(0)
    )

    # ── 1. Find shared dates ──────────────────────────────────────────────────
    confirmed_series = ANALYSIS_CONFIG_SERIES["all_confirmed"]
    ceiling_series = ANALYSIS_CONFIG_SERIES["all_ceiling"]
    confirmed_dates = {_date(ds): ds for ds in confirmed_series}
    ceiling_dates = {_date(ds): ds for ds in ceiling_series}
    shared_dates = sorted(set(confirmed_dates) & set(ceiling_dates))

    print(f"confirmed_ceiling_convergence: {len(shared_dates)} shared dates")
    print(f"  Dates: {shared_dates}")

    # ── 2. National-level gap over time ───────────────────────────────────────
    print("\nconfirmed_ceiling_convergence: loading national pct...")
    nat_rows: list[dict] = []
    for d in shared_dates:
        print(f"  {d}...")
        conf_pct = get_national_pct(confirmed_dates[d], eco_emp)
        ceil_pct = get_national_pct(ceiling_dates[d], eco_emp)
        nat_rows.append({
            "date": d,
            "confirmed_pct": round(conf_pct, 3),
            "ceiling_pct": round(ceil_pct, 3),
            "gap_pp": round(ceil_pct - conf_pct, 3),
            "ratio": round(conf_pct / ceil_pct * 100, 2) if ceil_pct > 0 else 0.0,
        })
    nat_df = pd.DataFrame(nat_rows)
    save_csv(nat_df, results / "national_convergence.csv")
    print("\n  National confirmed/ceiling ratio over time:")
    for _, r in nat_df.iterrows():
        print(f"    {r['date']}: confirmed {r['confirmed_pct']:.1f}% | "
              f"ceiling {r['ceiling_pct']:.1f}% | gap {r['gap_pp']:.1f}pp | "
              f"ratio {r['ratio']:.1f}%")

    # ── 3. Major category gap over time ──────────────────────────────────────
    print("\nconfirmed_ceiling_convergence: loading major category pct...")
    major_rows: list[dict] = []
    for d in shared_dates:
        conf_major = get_major_pct(confirmed_dates[d])
        ceil_major = get_major_pct(ceiling_dates[d])
        cats = sorted(set(conf_major.index) | set(ceil_major.index))
        for cat in cats:
            cp = float(conf_major.get(cat, 0.0))
            cl = float(ceil_major.get(cat, 0.0))
            gap = cl - cp
            ratio = (cp / cl * 100) if cl > 0 else 0.0
            major_rows.append({
                "date": d,
                "category": cat,
                "confirmed_pct": round(cp, 3),
                "ceiling_pct": round(cl, 3),
                "gap_pp": round(gap, 3),
                "ratio": round(ratio, 2),
            })
    major_df = pd.DataFrame(major_rows)
    save_csv(major_df, results / "major_category_convergence.csv")

    # ── 4. Per-sector ratio trend (first to last) ─────────────────────────────
    first_d, last_d = shared_dates[0], shared_dates[-1]
    sector_trend: list[dict] = []
    cats_all = major_df["category"].unique()
    for cat in cats_all:
        sub = major_df[major_df["category"] == cat].sort_values("date")
        row_first = sub[sub["date"] == first_d]
        row_last = sub[sub["date"] == last_d]
        if row_first.empty or row_last.empty:
            continue
        sector_trend.append({
            "category": cat,
            "ratio_first": row_first.iloc[0]["ratio"],
            "ratio_last": row_last.iloc[0]["ratio"],
            "gap_first": row_first.iloc[0]["gap_pp"],
            "gap_last": row_last.iloc[0]["gap_pp"],
            "confirmed_gain": row_last.iloc[0]["confirmed_pct"] - row_first.iloc[0]["confirmed_pct"],
            "ceiling_gain": row_last.iloc[0]["ceiling_pct"] - row_first.iloc[0]["ceiling_pct"],
        })
    sector_trend_df = pd.DataFrame(sector_trend)
    sector_trend_df["ratio_delta"] = (
        sector_trend_df["ratio_last"] - sector_trend_df["ratio_first"]
    ).round(2)
    sector_trend_df["gap_delta"] = (
        sector_trend_df["gap_last"] - sector_trend_df["gap_first"]
    ).round(2)
    sector_trend_df = sector_trend_df.sort_values("ratio_delta", ascending=False)
    save_csv(sector_trend_df, results / "sector_convergence_summary.csv")

    print("\n  Sector ratio change (confirmed/ceiling ratio, first to last date):")
    for _, r in sector_trend_df.head(5).iterrows():
        print(f"    {r['category'][:40]:40s}: "
              f"{r['ratio_first']:.1f}% -> {r['ratio_last']:.1f}% "
              f"(delta {r['ratio_delta']:+.1f}pp)")
    print("  ...")
    for _, r in sector_trend_df.tail(3).iterrows():
        print(f"    {r['category'][:40]:40s}: "
              f"{r['ratio_first']:.1f}% -> {r['ratio_last']:.1f}% "
              f"(delta {r['ratio_delta']:+.1f}pp)")

    # ── 5. Figures ────────────────────────────────────────────────────────────

    # 5a. National confirmed vs ceiling over time + gap
    fig_nat = go.Figure()
    fig_nat.add_trace(go.Scatter(
        x=nat_df["date"], y=nat_df["ceiling_pct"],
        name="Ceiling", mode="lines+markers",
        line=dict(color=COLORS.get("ceiling", "#ff7f0e"), width=2, dash="dash"),
    ))
    fig_nat.add_trace(go.Scatter(
        x=nat_df["date"], y=nat_df["confirmed_pct"],
        name="Confirmed", mode="lines+markers",
        line=dict(color=COLORS.get("primary", "#1f77b4"), width=2),
    ))
    # Shaded gap region
    fig_nat.add_trace(go.Scatter(
        x=nat_df["date"].tolist() + nat_df["date"].tolist()[::-1],
        y=nat_df["ceiling_pct"].tolist() + nat_df["confirmed_pct"].tolist()[::-1],
        fill="toself",
        fillcolor="rgba(200, 200, 200, 0.3)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Adoption gap",
        showlegend=True,
    ))
    style_figure(fig_nat,
                 "Confirmed vs. Ceiling % Tasks Affected — National Average",
                 subtitle=f"Employment-weighted average across all occupations | {first_d} to {last_d}",
                 x_title="Dataset date",
                 y_title="Avg % Tasks Affected (emp-weighted)",
                 show_legend=True,
                 height=500, width=1000)
    fig_nat.update_layout(margin=dict(l=60, r=20))
    save_figure(fig_nat, results / "figures" / "national_confirmed_vs_ceiling.png")
    shutil.copy(results / "figures" / "national_confirmed_vs_ceiling.png",
                figs_dir / "national_confirmed_vs_ceiling.png")
    print("  national_confirmed_vs_ceiling.png")

    # 5b. Ratio over time (national)
    fig_ratio = go.Figure(go.Scatter(
        x=nat_df["date"], y=nat_df["ratio"],
        mode="lines+markers",
        line=dict(color=COLORS.get("primary", "#1f77b4"), width=2),
        marker=dict(size=8),
    ))
    style_figure(fig_ratio,
                 "Confirmed/Ceiling Ratio Over Time — National",
                 subtitle="100% = confirmed = ceiling (full adoption); lower = more unrealized potential",
                 x_title="Dataset date",
                 y_title="Confirmed as % of Ceiling",
                 show_legend=False,
                 height=420, width=900)
    fig_ratio.update_layout(yaxis=dict(range=[0, 105]), margin=dict(l=60, r=20))
    save_figure(fig_ratio, results / "figures" / "national_ratio_over_time.png")
    shutil.copy(results / "figures" / "national_ratio_over_time.png",
                figs_dir / "national_ratio_over_time.png")
    print("  national_ratio_over_time.png")

    # 5c. Sector ratio delta (bar chart)
    stdf = sector_trend_df.sort_values("ratio_delta", ascending=True)
    fig_sector = go.Figure(go.Bar(
        x=stdf["ratio_delta"],
        y=stdf["category"],
        orientation="h",
        marker_color=[
            COLORS.get("positive", "#2ca02c") if v >= 0 else COLORS.get("negative", "#d62728")
            for v in stdf["ratio_delta"]
        ],
        text=[f"{v:+.1f}pp" for v in stdf["ratio_delta"]],
        textposition="outside",
        textfont=dict(size=10, color="#333", family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(fig_sector,
                 "Change in Confirmed/Ceiling Ratio by Sector",
                 subtitle=f"Positive = deployment catching up | Negative = capability outrunning adoption | {first_d} to {last_d}",
                 x_title="Change in Confirmed/Ceiling Ratio (pp)",
                 show_legend=False,
                 height=750, width=1050)
    fig_sector.update_layout(
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        yaxis=dict(showgrid=False),
        margin=dict(l=20, r=100),
        bargap=0.3,
    )
    save_figure(fig_sector, results / "figures" / "sector_ratio_delta.png")
    shutil.copy(results / "figures" / "sector_ratio_delta.png",
                figs_dir / "sector_ratio_delta.png")
    print("  sector_ratio_delta.png")

    # 5d. Lines: confirmed vs ceiling for top 8 sectors by gap change
    top_gap_cats = sector_trend_df.reindex(
        sector_trend_df["gap_delta"].abs().sort_values(ascending=False).index
    )["category"].head(8).tolist()

    # Palette
    pal = CATEGORY_PALETTE if hasattr(CATEGORY_PALETTE, "__iter__") else [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"
    ]

    fig_lines = go.Figure()
    for i, cat in enumerate(top_gap_cats):
        color = pal[i % len(pal)]
        sub = major_df[major_df["category"] == cat].sort_values("date")
        short = cat[:30] + "…" if len(cat) > 30 else cat
        fig_lines.add_trace(go.Scatter(
            x=sub["date"], y=sub["confirmed_pct"],
            name=f"{short} (conf)", mode="lines",
            line=dict(color=color, width=2),
        ))
        fig_lines.add_trace(go.Scatter(
            x=sub["date"], y=sub["ceiling_pct"],
            name=f"{short} (ceil)", mode="lines",
            line=dict(color=color, width=1, dash="dot"),
            showlegend=False,
        ))
    style_figure(fig_lines,
                 "Confirmed vs. Ceiling — Sectors With Largest Gap Changes",
                 subtitle="Solid = confirmed | Dotted = ceiling | Top 8 by absolute gap change",
                 x_title="Dataset date",
                 y_title="% Tasks Affected",
                 show_legend=True,
                 height=550, width=1100)
    fig_lines.update_layout(margin=dict(l=60, r=20))
    save_figure(fig_lines, results / "figures" / "sector_lines_confirmed_vs_ceiling.png")
    shutil.copy(results / "figures" / "sector_lines_confirmed_vs_ceiling.png",
                figs_dir / "sector_lines_confirmed_vs_ceiling.png")
    print("  sector_lines_confirmed_vs_ceiling.png")

    # ── 6. PDF ─────────────────────────────────────────────────────────────────
    report_path = HERE / "confirmed_ceiling_convergence_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "confirmed_ceiling_convergence_report.pdf")

    print("\nconfirmed_ceiling_convergence: done.")


if __name__ == "__main__":
    main()
