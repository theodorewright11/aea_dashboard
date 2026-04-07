"""
run.py — Time Trends: Occupations of Interest Timeline

Tracks the 29 named occupations through the full all_confirmed time series
and the all_ceiling series for comparison. Produces:
  - Multi-line chart: all 29 occupations over time (confirmed config)
  - Faceted panels: by group (high-profile, AI-controversial, Utah-relevant)
  - Bar chart: total gain over the window, sorted
  - Table: summary stats for each occupation

Run from project root:
    venv/Scripts/python -m analysis.questions.time_trends.occs_timeline.run
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.config import (
    ANALYSIS_CONFIG_SERIES,
    OCCS_OF_INTEREST,
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.utils import (
    CATEGORY_PALETTE,
    COLORS,
    FONT_FAMILY,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent

# Occupation groups for faceting
OCC_GROUPS: dict[str, list[str]] = {
    "High-Profile / High-Employment": [
        "Registered Nurses",
        "Software Developers",
        "General and Operations Managers",
        "Cashiers",
        "Customer Service Representatives",
        "Retail Salespersons",
        "Heavy and Tractor-Trailer Truck Drivers",
        "Elementary School Teachers, Except Special Education",
        "Waiters and Waitresses",
        "Janitors and Cleaners, Except Maids and Housekeeping Cleaners",
        "Accountants and Auditors",
        "Secretaries and Administrative Assistants, Except Legal, Medical, and Executive",
    ],
    "AI-Controversial / Interesting": [
        "Lawyers",
        "Physicians, All Other",
        "Financial Analysts",
        "Graphic Designers",
        "Technical Writers",
        "Web Developers",
        "Paralegals and Legal Assistants",
        "Data Scientists",
        "Human Resources Specialists",
        "Market Research Analysts and Marketing Specialists",
        "Editors",
        "Interpreters and Translators",
    ],
    "Utah-Relevant": [
        "Computer Systems Analysts",
        "Medical and Health Services Managers",
        "Construction Laborers",
        "Sales Representatives, Wholesale and Manufacturing, Except Technical and Scientific Products",
        "Network and Computer Systems Administrators",
    ],
}

GROUP_COLORS: dict[str, str] = {
    "High-Profile / High-Employment": "#1f77b4",
    "AI-Controversial / Interesting": "#ff7f0e",
    "Utah-Relevant": "#2ca02c",
}


def occ_to_group(occ: str) -> str:
    for group, occs in OCC_GROUPS.items():
        if occ in occs:
            return group
    return "Other"


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    confirmed_series = ANALYSIS_CONFIG_SERIES["all_confirmed"]
    confirmed_dates = [ds.rsplit(" ", 1)[-1] for ds in confirmed_series]
    ceiling_series = ANALYSIS_CONFIG_SERIES["all_ceiling"]
    ceiling_dates = [ds.rsplit(" ", 1)[-1] for ds in ceiling_series]

    # ── 1. Load confirmed series for all occs of interest ─────────────────────
    print("occs_timeline: loading all_confirmed series...")
    conf_rows: list[dict] = []
    for ds_name, d in zip(confirmed_series, confirmed_dates):
        print(f"  {ds_name}...")
        pct = get_pct_tasks_affected(ds_name)
        for occ in OCCS_OF_INTEREST:
            val = float(pct.get(occ, float("nan")))
            conf_rows.append({
                "occ": occ,
                "date": d,
                "config": "all_confirmed",
                "pct_tasks_affected": val,
                "group": occ_to_group(occ),
            })
    conf_df = pd.DataFrame(conf_rows)

    # ── 2. Load ceiling series ────────────────────────────────────────────────
    print("\noccs_timeline: loading all_ceiling series...")
    ceil_rows: list[dict] = []
    for ds_name, d in zip(ceiling_series, ceiling_dates):
        print(f"  {ds_name}...")
        pct = get_pct_tasks_affected(ds_name)
        for occ in OCCS_OF_INTEREST:
            val = float(pct.get(occ, float("nan")))
            ceil_rows.append({
                "occ": occ,
                "date": d,
                "config": "all_ceiling",
                "pct_tasks_affected": val,
                "group": occ_to_group(occ),
            })
    ceil_df = pd.DataFrame(ceil_rows)

    all_df = pd.concat([conf_df, ceil_df], ignore_index=True)
    save_csv(all_df, results / "occs_timeline.csv")

    # ── 3. Summary stats per occupation (confirmed) ───────────────────────────
    conf_wide = conf_df.pivot_table(
        index="occ", columns="date", values="pct_tasks_affected"
    ).reset_index()
    date_cols = [c for c in conf_wide.columns if c != "occ"]
    conf_wide[date_cols] = conf_wide[date_cols].ffill(axis=1)

    summary_rows: list[dict] = []
    for _, row in conf_wide.iterrows():
        occ = row["occ"]
        vals = row[date_cols].values.astype(float)
        first_val = vals[0] if not pd.isna(vals[0]) else 0.0
        last_val = vals[-1] if not pd.isna(vals[-1]) else 0.0
        total_gain = last_val - first_val
        # Find largest single-step jump
        diffs = [abs(vals[i+1] - vals[i]) for i in range(len(vals)-1)
                 if not (pd.isna(vals[i]) or pd.isna(vals[i+1]))]
        max_jump = max(diffs) if diffs else 0.0
        jump_date_idx = (
            [abs(vals[i+1] - vals[i]) for i in range(len(vals)-1)].index(max(diffs))
            if diffs else -1
        )
        jump_date = date_cols[jump_date_idx + 1] if jump_date_idx >= 0 else "—"
        summary_rows.append({
            "occ": occ,
            "group": occ_to_group(occ),
            "pct_first": round(first_val, 1),
            "pct_last": round(last_val, 1),
            "total_gain_pp": round(total_gain, 1),
            "max_single_jump_pp": round(max_jump, 1),
            "jump_date": jump_date,
        })
    summary_df = pd.DataFrame(summary_rows).sort_values("total_gain_pp", ascending=False)
    save_csv(summary_df, results / "occs_summary.csv")

    print(f"\noccs_timeline: top 5 gainers (confirmed):")
    for _, r in summary_df.head(5).iterrows():
        print(f"  {r['occ'][:45]:45s}: "
              f"{r['pct_first']:.1f}% to {r['pct_last']:.1f}% "
              f"(+{r['total_gain_pp']:.1f}pp, max jump {r['max_single_jump_pp']:.1f}pp at {r['jump_date']})")

    # ── 4. Figures ────────────────────────────────────────────────────────────

    pal = list(CATEGORY_PALETTE) if hasattr(CATEGORY_PALETTE, "__iter__") else [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
        "#bcbd22", "#17becf", "#aec7e8", "#ffbb78"
    ]

    # 4a. All 29 occupations — confirmed only
    fig_all = go.Figure()
    for i, occ in enumerate(OCCS_OF_INTEREST):
        sub = conf_df[conf_df["occ"] == occ].sort_values("date")
        if sub.empty:
            continue
        group = occ_to_group(occ)
        color = GROUP_COLORS.get(group, "#888")
        short = (occ[:30] + "...") if len(occ) > 30 else occ
        fig_all.add_trace(go.Scatter(
            x=sub["date"],
            y=sub["pct_tasks_affected"],
            mode="lines+markers",
            name=short,
            line=dict(color=color, width=1.5),
            marker=dict(size=5),
            opacity=0.8,
        ))
    style_figure(fig_all,
                 "All Occupations of Interest — Confirmed AI Exposure Over Time",
                 subtitle=f"All Confirmed series | {confirmed_dates[0]} to {confirmed_dates[-1]} | "
                          "Blue=High-profile | Orange=AI-controversial | Green=Utah",
                 x_title="Dataset date",
                 y_title="% Tasks Affected",
                 show_legend=True,
                 height=580, width=1150)
    fig_all.update_layout(
        margin=dict(l=60, r=20),
        legend=dict(font=dict(size=8)),
    )
    save_figure(fig_all, results / "figures" / "all_occs_confirmed.png")
    shutil.copy(results / "figures" / "all_occs_confirmed.png",
                figs_dir / "all_occs_confirmed.png")
    print("  all_occs_confirmed.png")

    # 4b. Faceted by group (3 subplots)
    group_list = list(OCC_GROUPS.keys())
    fig_facet = make_subplots(
        rows=1, cols=3,
        subplot_titles=group_list,
        shared_yaxes=True,
    )
    for col_idx, (group_name, occs_in_group) in enumerate(OCC_GROUPS.items(), start=1):
        group_pal = pal[:]
        for occ_i, occ in enumerate(occs_in_group):
            sub = conf_df[conf_df["occ"] == occ].sort_values("date")
            if sub.empty:
                continue
            short = (occ[:25] + "...") if len(occ) > 25 else occ
            fig_facet.add_trace(
                go.Scatter(
                    x=sub["date"],
                    y=sub["pct_tasks_affected"],
                    mode="lines+markers",
                    name=short,
                    line=dict(color=group_pal[occ_i % len(group_pal)], width=1.5),
                    marker=dict(size=4),
                    showlegend=True,
                    legendgroup=group_name,
                ),
                row=1, col=col_idx,
            )
    fig_facet.update_layout(
        title=dict(
            text="Occupations of Interest — Confirmed Exposure by Group",
            font=dict(size=15, family=FONT_FAMILY),
        ),
        height=520, width=1350,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family=FONT_FAMILY),
        legend=dict(font=dict(size=7), tracegroupgap=2),
        margin=dict(l=60, r=10, t=80, b=50),
    )
    fig_facet.update_yaxes(title_text="% Tasks Affected", row=1, col=1)
    for c in range(1, 4):
        fig_facet.update_xaxes(
            title_text="Date", row=1, col=c,
            gridcolor=COLORS["grid"], showgrid=True,
        )
        fig_facet.update_yaxes(gridcolor=COLORS["grid"], showgrid=True, row=1, col=c)
    save_figure(fig_facet, results / "figures" / "occs_faceted_by_group.png")
    shutil.copy(results / "figures" / "occs_faceted_by_group.png",
                figs_dir / "occs_faceted_by_group.png")
    print("  occs_faceted_by_group.png")

    # 4c. Total gain bar chart
    gain_plot = summary_df.sort_values("total_gain_pp", ascending=True)
    group_color_list = [
        GROUP_COLORS.get(occ_to_group(row["occ"]), "#888")
        for _, row in gain_plot.iterrows()
    ]
    short_occ = [
        (s[:40] + "...") if len(s) > 40 else s for s in gain_plot["occ"]
    ]
    fig_gain = go.Figure(go.Bar(
        x=gain_plot["total_gain_pp"],
        y=short_occ,
        orientation="h",
        marker_color=group_color_list,
        text=[f"+{v:.1f}pp ({l:.0f}%)" for v, l in
              zip(gain_plot["total_gain_pp"], gain_plot["pct_last"])],
        textposition="outside",
        textfont=dict(size=9, color="#333", family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(fig_gain,
                 "Total Gain in AI Exposure — Occupations of Interest",
                 subtitle=f"All Confirmed series | {confirmed_dates[0]} to {confirmed_dates[-1]} | "
                          "Blue=High-profile | Orange=AI-controversial | Green=Utah",
                 x_title="Total gain (pp)",
                 show_legend=False,
                 height=850, width=1050)
    fig_gain.update_layout(
        margin=dict(l=20, r=160),
        xaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
        yaxis=dict(showgrid=False),
        bargap=0.2,
    )
    save_figure(fig_gain, results / "figures" / "occs_total_gain.png")
    shutil.copy(results / "figures" / "occs_total_gain.png",
                figs_dir / "occs_total_gain.png")
    print("  occs_total_gain.png")

    # 4d. Confirmed vs ceiling for top 6 gainers
    top6 = summary_df.head(6)["occ"].tolist()
    fig_cv = go.Figure()
    for i, occ in enumerate(top6):
        color = pal[i % len(pal)]
        short = (occ[:28] + "...") if len(occ) > 28 else occ
        sub_conf = conf_df[conf_df["occ"] == occ].sort_values("date")
        sub_ceil = ceil_df[ceil_df["occ"] == occ].sort_values("date")
        if not sub_conf.empty:
            fig_cv.add_trace(go.Scatter(
                x=sub_conf["date"], y=sub_conf["pct_tasks_affected"],
                mode="lines+markers",
                name=f"{short} (conf)",
                line=dict(color=color, width=2),
                marker=dict(size=6),
            ))
        if not sub_ceil.empty:
            fig_cv.add_trace(go.Scatter(
                x=sub_ceil["date"], y=sub_ceil["pct_tasks_affected"],
                mode="lines",
                name=f"{short} (ceil)",
                line=dict(color=color, width=1, dash="dot"),
                showlegend=False,
            ))
    style_figure(fig_cv,
                 "Confirmed vs. Ceiling — Top 6 Gainers",
                 subtitle="Solid = confirmed | Dotted = ceiling | Top 6 by total confirmed gain",
                 x_title="Dataset date",
                 y_title="% Tasks Affected",
                 show_legend=True,
                 height=520, width=1100)
    fig_cv.update_layout(margin=dict(l=60, r=20), legend=dict(font=dict(size=9)))
    save_figure(fig_cv, results / "figures" / "top6_confirmed_vs_ceiling.png")
    shutil.copy(results / "figures" / "top6_confirmed_vs_ceiling.png",
                figs_dir / "top6_confirmed_vs_ceiling.png")
    print("  top6_confirmed_vs_ceiling.png")

    # ── 5. PDF ─────────────────────────────────────────────────────────────────
    report_path = HERE / "occs_timeline_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "occs_timeline_report.pdf")

    print("\noccs_timeline: done.")


if __name__ == "__main__":
    main()
