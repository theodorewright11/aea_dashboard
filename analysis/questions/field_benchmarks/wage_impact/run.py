"""
run.py — Field Benchmarks: Wage Impact

Compares the dollar magnitude of AI's economic footprint in our data to
Seampoint's Utah figures (the only external source with public wage-dollar estimates
at the state level we can directly compare to).

Seampoint Utah (2026, preliminary):
  Total workforce: 1.6M workers, $104B total annual wages
  AI can take over: ~$21B wages (20% of hours → ~20% of wage base as proxy)
  AI can make better: ~$15B near-term opportunity
  Total AI opportunity: $36B

Our metrics (Utah, geo="ut"):
  wages_affected = sum of wages affected across all occupations
  This is comparable to Seampoint's dollar figures, adjusted for what
  "affected" means in each framework.

National comparison also shown for context.

Figures (key ones copied to figures/):
  utah_wage_comparison.png  — Our confirmed/ceiling wages_affected vs Seampoint $21B/$36B
  utah_pct_comparison.png   — As % of total Utah wage base ($104B)
  national_wage_totals.png  — Our national wages_affected across all 5 configs

Run from project root:
    venv/Scripts/python -m analysis.questions.field_benchmarks.wage_impact.run
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
    format_wages,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
PRIMARY_KEY = "all_confirmed"
CEILING_KEY = "all_ceiling"

# ── Seampoint Utah constants ─────────────────────────────────────────────────
# Source: Seampoint LLC (2026), "Utah's AI Workforce Reality," preliminary draft.
SEAMPOINT_UT_TOTAL_WAGES    = 104e9   # $104B total Utah annual wages
SEAMPOINT_UT_WORKERS        = 1_600_000
SEAMPOINT_UT_TAKEOVER_WAGES = 21e9   # ~$21B — "AI can take over" share
SEAMPOINT_UT_AUGMENT_WAGES  = 15e9   # ~$15B — "AI can make better" near-term value
SEAMPOINT_UT_TOTAL_OPP      = 36e9   # $36B total AI opportunity ($21B + $15B)


def _get_group_wages(dataset_name: str, geo: str = "nat") -> dict:
    """Get aggregate wages_affected and workers_affected for a dataset + geo."""
    from backend.compute import get_group_data

    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": geo,
        "agg_level": "occupation",
        "sort_by": "Workers Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    if data is None:
        return {"workers_affected": 0.0, "wages_affected": 0.0}
    df = data["df"]
    return {
        "workers_affected": df["workers_affected"].sum(),
        "wages_affected":   df["wages_affected"].sum(),
    }


def _get_total_wages(geo: str = "nat") -> float:
    """Get total wage bill from explorer occupations."""
    from backend.compute import get_explorer_occupations, load_eco_raw

    all_occs = get_explorer_occupations()
    if geo == "nat":
        total = sum((o.get("emp") or 0) * (o.get("wage") or 0) for o in all_occs)
        return total
    # For state, we need to pull state-level employment data
    # Use Seampoint's $104B figure for Utah as the authoritative denominator
    # (our data may slightly differ due to dataset vintage)
    return SEAMPOINT_UT_TOTAL_WAGES


def _build_utah_wage_comparison(utah_df: pd.DataFrame) -> go.Figure:
    """Bar chart: our Utah wages_affected (confirmed/ceiling) vs Seampoint $21B/$36B."""
    fig = go.Figure()

    # Our configs — confirmed and ceiling only for clarity
    for key, color in [("all_confirmed", COLORS["primary"]), ("all_ceiling", COLORS["secondary"])]:
        row = utah_df[utah_df["config_key"] == key]
        if row.empty:
            continue
        wages_b = row.iloc[0]["wages_affected"] / 1e9
        fig.add_trace(go.Bar(
            name=ANALYSIS_CONFIG_LABELS[key],
            x=[ANALYSIS_CONFIG_LABELS[key]],
            y=[wages_b],
            marker=dict(color=color, line=dict(width=0)),
            text=[f"${wages_b:.1f}B"],
            textposition="outside",
            textfont=dict(size=12, color=COLORS["neutral"], family=FONT_FAMILY),
        ))

    # Seampoint benchmarks
    for lbl, val, col in [
        ("Seampoint<br>AI Can Take Over", SEAMPOINT_UT_TAKEOVER_WAGES / 1e9, COLORS["accent"]),
        ("Seampoint<br>Total Opportunity", SEAMPOINT_UT_TOTAL_OPP / 1e9, COLORS["accent"]),
    ]:
        fig.add_trace(go.Bar(
            name=lbl.replace("<br>", " "),
            x=[lbl],
            y=[val],
            marker=dict(
                color=col,
                pattern=dict(shape="/", size=6, fgcolor="white"),
                line=dict(width=0.5, color=COLORS["border"]),
            ),
            text=[f"${val:.0f}B"],
            textposition="outside",
            textfont=dict(size=12, color=COLORS["neutral"], family=FONT_FAMILY),
        ))

    style_figure(
        fig,
        "Utah Wages Affected by AI — AEA Dashboard vs. Seampoint",
        subtitle=(
            "AEA Dashboard: sum of wages_affected across Utah occupations | "
            "Seampoint (2026 preliminary): governance-constrained deployment estimate"
        ),
        y_title="Annual Wages Affected ($B)",
        height=520, width=950,
        show_legend=False,
    )
    fig.update_layout(
        barmode="group",
        bargap=0.25,
        xaxis=dict(showgrid=False, tickfont=dict(size=11, family=FONT_FAMILY)),
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   tickprefix="$", ticksuffix="B"),
        margin=dict(l=60, r=40, t=80, b=80),
    )
    return fig


def _build_utah_pct_comparison(utah_df: pd.DataFrame) -> go.Figure:
    """Bar chart: wages_affected as % of Utah total wage base."""
    labels = []
    vals   = []
    colors = []

    for key, color in [("all_confirmed", COLORS["primary"]), ("all_ceiling", COLORS["secondary"])]:
        row = utah_df[utah_df["config_key"] == key]
        if row.empty:
            continue
        pct = row.iloc[0]["wages_affected"] / SEAMPOINT_UT_TOTAL_WAGES * 100
        labels.append(ANALYSIS_CONFIG_LABELS[key])
        vals.append(round(pct, 1))
        colors.append(color)

    # Seampoint
    labels += ["Seampoint: AI Can Take Over", "Seampoint: Total Opportunity"]
    vals   += [
        SEAMPOINT_UT_TAKEOVER_WAGES / SEAMPOINT_UT_TOTAL_WAGES * 100,
        SEAMPOINT_UT_TOTAL_OPP / SEAMPOINT_UT_TOTAL_WAGES * 100,
    ]
    colors += [COLORS["accent"], COLORS["accent"]]

    fig = go.Figure(go.Bar(
        x=labels, y=vals,
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:.1f}%" for v in vals],
        textposition="outside",
        textfont=dict(size=12, color=COLORS["neutral"], family=FONT_FAMILY),
    ))
    style_figure(
        fig,
        "Utah Wages Affected as % of Total Wage Base ($104B)",
        subtitle=(
            "Common denominator: Seampoint's $104B total Utah annual wages | "
            "AEA solid bars = confirmed/ceiling; hatched = Seampoint estimates"
        ),
        y_title="% of Total Utah Wages",
        height=480, width=900,
        show_legend=False,
    )
    fig.update_layout(
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   ticksuffix="%", range=[0, max(vals) * 1.25]),
        xaxis=dict(showgrid=False, tickfont=dict(size=11, family=FONT_FAMILY)),
        margin=dict(l=60, r=40, t=80, b=100),
    )
    return fig


def _build_national_totals(nat_df: pd.DataFrame) -> go.Figure:
    """Bar chart: national wages_affected across all 5 configs."""
    config_order = ["all_confirmed", "all_ceiling", "human_conversation",
                    "agentic_confirmed", "agentic_ceiling"]
    color_map = {
        "all_confirmed":      COLORS["primary"],
        "all_ceiling":        COLORS["secondary"],
        "human_conversation": COLORS["accent"],
        "agentic_confirmed":  COLORS["muted"],
        "agentic_ceiling":    COLORS["neutral"],
    }

    rows = nat_df.set_index("config_key")
    labels = [ANALYSIS_CONFIG_LABELS[k] for k in config_order if k in rows.index]
    vals   = [rows.loc[k, "wages_affected"] / 1e12 for k in config_order if k in rows.index]
    cols   = [color_map[k] for k in config_order if k in rows.index]

    fig = go.Figure(go.Bar(
        x=labels, y=vals,
        marker=dict(color=cols, line=dict(width=0)),
        text=[f"${v:.2f}T" for v in vals],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["neutral"], family=FONT_FAMILY),
    ))
    style_figure(
        fig,
        "National Wages Affected by AI — All Five Configs",
        subtitle="sum(wages_affected) across all occupations | National | Freq | Auto-aug ON",
        y_title="Annual Wages Affected ($T)",
        height=480, width=1000,
        show_legend=False,
    )
    fig.update_layout(
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"],
                   tickprefix="$", ticksuffix="T"),
        xaxis=dict(showgrid=False, tickfont=dict(size=11, family=FONT_FAMILY)),
        margin=dict(l=60, r=40, t=80, b=100),
    )
    return fig


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("wage_impact: loading data...")

    nat_rows: list[dict] = []
    ut_rows:  list[dict] = []

    for key, ds_name in ANALYSIS_CONFIGS.items():
        label = ANALYSIS_CONFIG_LABELS[key]
        print(f"  {label}...")

        nat = _get_group_wages(ds_name, geo="nat")
        nat_rows.append({"config_key": key, "config_label": label,
                         "geo": "nat", **nat})

        ut = _get_group_wages(ds_name, geo="ut")
        ut_rows.append({"config_key": key, "config_label": label,
                        "geo": "ut", **ut})

    nat_df = pd.DataFrame(nat_rows)
    ut_df  = pd.DataFrame(ut_rows)

    # Seampoint comparison rows
    ext_rows = [
        {"source": "Seampoint Utah: AI can take over", "wages_b": SEAMPOINT_UT_TAKEOVER_WAGES / 1e9,
         "pct_of_ut_total": SEAMPOINT_UT_TAKEOVER_WAGES / SEAMPOINT_UT_TOTAL_WAGES * 100},
        {"source": "Seampoint Utah: AI can make better (near-term)", "wages_b": SEAMPOINT_UT_AUGMENT_WAGES / 1e9,
         "pct_of_ut_total": SEAMPOINT_UT_AUGMENT_WAGES / SEAMPOINT_UT_TOTAL_WAGES * 100},
        {"source": "Seampoint Utah: Total AI opportunity", "wages_b": SEAMPOINT_UT_TOTAL_OPP / 1e9,
         "pct_of_ut_total": SEAMPOINT_UT_TOTAL_OPP / SEAMPOINT_UT_TOTAL_WAGES * 100},
    ]

    # Print summary
    primary_nat = nat_df[nat_df["config_key"] == PRIMARY_KEY].iloc[0]
    ceiling_nat = nat_df[nat_df["config_key"] == CEILING_KEY].iloc[0]
    primary_ut  = ut_df[ut_df["config_key"]  == PRIMARY_KEY].iloc[0]
    ceiling_ut  = ut_df[ut_df["config_key"]  == CEILING_KEY].iloc[0]

    print("\n-- National wages affected --")
    print(f"  all_confirmed: ${primary_nat['wages_affected']/1e12:.2f}T")
    print(f"  all_ceiling:   ${ceiling_nat['wages_affected']/1e12:.2f}T")

    print("\n-- Utah wages affected --")
    print(f"  all_confirmed: ${primary_ut['wages_affected']/1e9:.1f}B "
          f"({primary_ut['wages_affected']/SEAMPOINT_UT_TOTAL_WAGES*100:.1f}% of $104B)")
    print(f"  all_ceiling:   ${ceiling_ut['wages_affected']/1e9:.1f}B "
          f"({ceiling_ut['wages_affected']/SEAMPOINT_UT_TOTAL_WAGES*100:.1f}% of $104B)")
    print(f"\n  Seampoint Utah takeover: $21.0B ({SEAMPOINT_UT_TAKEOVER_WAGES/SEAMPOINT_UT_TOTAL_WAGES*100:.1f}%)")
    print(f"  Seampoint Utah total:    $36.0B ({SEAMPOINT_UT_TOTAL_OPP/SEAMPOINT_UT_TOTAL_WAGES*100:.1f}%)")

    # Save CSVs
    ut_df["pct_of_seampoint_total"] = ut_df["wages_affected"] / SEAMPOINT_UT_TOTAL_WAGES * 100
    save_csv(nat_df, results / "national_wages.csv")
    save_csv(ut_df,  results / "utah_wages.csv")
    save_csv(pd.DataFrame(ext_rows), results / "seampoint_benchmarks.csv")
    print("\n  CSVs saved.")

    # Figures
    print("  Building figures...")
    fig = _build_utah_wage_comparison(ut_df)
    save_figure(fig, results / "figures" / "utah_wage_comparison.png")
    shutil.copy(results / "figures" / "utah_wage_comparison.png",
                figs_dir / "utah_wage_comparison.png")
    print("    utah_wage_comparison.png")

    fig = _build_utah_pct_comparison(ut_df)
    save_figure(fig, results / "figures" / "utah_pct_comparison.png")
    shutil.copy(results / "figures" / "utah_pct_comparison.png",
                figs_dir / "utah_pct_comparison.png")
    print("    utah_pct_comparison.png")

    fig = _build_national_totals(nat_df)
    save_figure(fig, results / "figures" / "national_wage_totals.png")
    shutil.copy(results / "figures" / "national_wage_totals.png",
                figs_dir / "national_wage_totals.png")
    print("    national_wage_totals.png")

    # PDF
    md_path = HERE / "wage_impact_report.md"
    if md_path.exists():
        generate_pdf(md_path, results / "wage_impact_report.pdf")

    print("\nwage_impact: done.")


if __name__ == "__main__":
    main()
