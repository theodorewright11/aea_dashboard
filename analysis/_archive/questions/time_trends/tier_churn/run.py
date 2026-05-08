"""
run.py — Time Trends: Tier Churn

Tracks exposure tier membership over time: how many occupations crossed
the key thresholds (20% restructuring entry, 33% risk gate, 40% moderate entry,
60% high-tier entry) during the Sep 2024 to Feb 2026 window.

Tier definitions (pct_tasks_affected):
  high          >= 60%
  moderate      40-59%
  restructuring 20-39%
  low           < 20%

Key outputs:
  - Tier roster at first and last date
  - Tier transition matrix (first -> last): how many moved, up/down
  - New high-tier entrants (weren't >=60% at start, are now)
  - 33%-gate crossings (occupations that crossed the risk exposure threshold)
  - Per-sector tier stability score

Run from project root:
    venv/Scripts/python -m analysis.questions.time_trends.tier_churn.run
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from analysis.config import (
    ANALYSIS_CONFIG_SERIES,
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
PRIMARY_KEY = "all_confirmed"

# Tier boundaries
TIER_THRESHOLDS = {"high": 60.0, "moderate": 40.0, "restructuring": 20.0}

# Tier color map
TIER_COLORS: dict[str, str] = {
    "high":           "#d62728",
    "moderate":       "#ff7f0e",
    "restructuring":  "#1f77b4",
    "low":            "#aec7e8",
}

TIER_ORDER = ["high", "moderate", "restructuring", "low"]


def assign_tier(pct: float) -> str:
    if pct >= 60.0:
        return "high"
    if pct >= 40.0:
        return "moderate"
    if pct >= 20.0:
        return "restructuring"
    return "low"


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    # ── 1. Load first and last pct ────────────────────────────────────────────
    series = ANALYSIS_CONFIG_SERIES[PRIMARY_KEY]
    first_ds = series[0]
    last_ds = series[-1]
    first_date = first_ds.rsplit(" ", 1)[-1]
    last_date = last_ds.rsplit(" ", 1)[-1]

    print(f"tier_churn: comparing {first_date} to {last_date}...")
    pct_first = get_pct_tasks_affected(first_ds).rename("pct_first")
    pct_last = get_pct_tasks_affected(last_ds).rename("pct_last")

    # ── 2. Full series for all-dates tier assignment ──────────────────────────
    print("tier_churn: loading full series for intermediate dates...")
    all_series_frames: dict[str, pd.Series] = {}
    for ds_name in series:
        d = ds_name.rsplit(" ", 1)[-1]
        print(f"  {ds_name}...")
        all_series_frames[d] = get_pct_tasks_affected(ds_name)

    wide = pd.DataFrame(all_series_frames)
    wide.index.name = "title_current"
    wide = wide.reset_index()

    # Forward-fill for any NaN (occupation entered data mid-series)
    date_cols = [c for c in wide.columns if c != "title_current"]
    wide[date_cols] = wide[date_cols].ffill(axis=1).fillna(0.0)

    # ── 3. Attach major category ──────────────────────────────────────────────
    from backend.compute import load_eco_raw
    eco = load_eco_raw()
    occ_major = eco[["title_current", "major_occ_category"]].drop_duplicates("title_current")

    # ── 4. Tier at first and last date ────────────────────────────────────────
    merged = pd.DataFrame({
        "title_current": wide["title_current"],
        "pct_first": wide[first_date],
        "pct_last": wide[last_date],
    })
    merged["tier_first"] = merged["pct_first"].apply(assign_tier)
    merged["tier_last"] = merged["pct_last"].apply(assign_tier)
    merged["tier_changed"] = merged["tier_first"] != merged["tier_last"]
    merged = merged.merge(occ_major, on="title_current", how="left")
    merged["major_occ_category"] = merged["major_occ_category"].fillna("Unknown")

    save_csv(merged, results / "tier_first_last.csv")

    # ── 5. Tier transition matrix ─────────────────────────────────────────────
    transition = (
        merged.groupby(["tier_first", "tier_last"])
        .size()
        .reset_index(name="n_occs")
    )
    save_csv(transition, results / "tier_transition_matrix.csv")

    # ── 6. Tier count at each date ────────────────────────────────────────────
    tier_by_date: list[dict] = []
    for d in date_cols:
        col = wide[d]
        for tier in TIER_ORDER:
            if tier == "high":
                n = (col >= 60.0).sum()
            elif tier == "moderate":
                n = ((col >= 40.0) & (col < 60.0)).sum()
            elif tier == "restructuring":
                n = ((col >= 20.0) & (col < 40.0)).sum()
            else:
                n = (col < 20.0).sum()
            tier_by_date.append({"date": d, "tier": tier, "n_occs": int(n)})
    tier_time_df = pd.DataFrame(tier_by_date)
    save_csv(tier_time_df, results / "tier_counts_over_time.csv")

    # ── 7. New high-tier entrants (not in high at first, in high at last) ──────
    new_high = merged[(merged["tier_first"] != "high") & (merged["tier_last"] == "high")].copy()
    new_high = new_high.sort_values("pct_last", ascending=False)
    save_csv(new_high, results / "new_high_tier_entrants.csv")

    # 33%-gate crossings
    gate_crossings = merged[
        (merged["pct_first"] < 33.0) & (merged["pct_last"] >= 33.0)
    ].copy()
    gate_crossings = gate_crossings.sort_values("pct_last", ascending=False)
    save_csv(gate_crossings, results / "gate_crossings_33pct.csv")

    # ── 8. Sector tier stability ──────────────────────────────────────────────
    sector_stability = (
        merged.groupby("major_occ_category")
        .agg(
            n_occs=("title_current", "count"),
            n_stable=("tier_changed", lambda x: (~x).sum()),
            n_changed=("tier_changed", "sum"),
            n_new_high=(
                "tier_last",
                lambda x: ((x == "high") & (merged.loc[x.index, "tier_first"] != "high")).sum(),
            ),
        )
        .reset_index()
    )
    sector_stability["stability_rate"] = (
        sector_stability["n_stable"] / sector_stability["n_occs"] * 100
    ).round(1)
    sector_stability = sector_stability.sort_values("stability_rate", ascending=False)
    save_csv(sector_stability, results / "sector_tier_stability.csv")

    # ── 9. Summary stats ──────────────────────────────────────────────────────
    n_changed = merged["tier_changed"].sum()
    n_total = len(merged)
    print(f"\ntier_churn: {n_changed}/{n_total} occupations changed tier "
          f"({n_changed/n_total*100:.0f}%)")
    print(f"  New high-tier entrants: {len(new_high)}")
    print(f"  33%% gate crossings: {len(gate_crossings)}")

    # Tier counts at first and last
    for tier in TIER_ORDER:
        f = (merged["tier_first"] == tier).sum()
        l = (merged["tier_last"] == tier).sum()
        print(f"  {tier:15s}: {f} -> {l} ({l-f:+d})")

    # ── 10. Figures ───────────────────────────────────────────────────────────

    # 10a. Tier counts over time (stacked area)
    pivot_time = tier_time_df.pivot_table(
        index="date", columns="tier", values="n_occs", fill_value=0
    ).reset_index()
    for t in TIER_ORDER:
        if t not in pivot_time.columns:
            pivot_time[t] = 0

    fig_time = go.Figure()
    for tier in reversed(TIER_ORDER):
        fig_time.add_trace(go.Scatter(
            x=pivot_time["date"],
            y=pivot_time[tier],
            stackgroup="one",
            name=tier.title(),
            fillcolor=TIER_COLORS[tier],
            line=dict(color=TIER_COLORS[tier], width=1),
            mode="lines",
        ))
    style_figure(fig_time,
                 "Exposure Tier Roster Over Time",
                 subtitle="All Confirmed series | Count of occupations in each tier at each dataset date",
                 x_title="Dataset date",
                 y_title="Number of occupations",
                 show_legend=True,
                 height=500, width=1000)
    fig_time.update_layout(margin=dict(l=60, r=20))
    save_figure(fig_time, results / "figures" / "tier_counts_over_time.png")
    shutil.copy(results / "figures" / "tier_counts_over_time.png",
                figs_dir / "tier_counts_over_time.png")
    print("  tier_counts_over_time.png")

    # 10b. Tier transition Sankey (first → last)
    tier_to_idx = {t: i for i, t in enumerate(TIER_ORDER)}
    n_tiers = len(TIER_ORDER)
    sankey_source, sankey_target, sankey_value, sankey_color = [], [], [], []

    for _, row in transition.iterrows():
        src = tier_to_idx.get(row["tier_first"])
        tgt_raw = tier_to_idx.get(row["tier_last"])
        if src is None or tgt_raw is None:
            continue
        tgt = tgt_raw + n_tiers  # offset for target nodes
        sankey_source.append(src)
        sankey_target.append(tgt)
        sankey_value.append(int(row["n_occs"]))
        sankey_color.append(TIER_COLORS.get(row["tier_last"], "#888"))

    node_labels = [f"{t.title()}\n({first_date})" for t in TIER_ORDER] + \
                  [f"{t.title()}\n({last_date})" for t in TIER_ORDER]
    node_colors = [TIER_COLORS[t] for t in TIER_ORDER] * 2

    fig_sankey = go.Figure(go.Sankey(
        node=dict(
            label=node_labels,
            color=node_colors,
            pad=15, thickness=20,
            line=dict(color="#888", width=0.5),
        ),
        link=dict(
            source=sankey_source,
            target=sankey_target,
            value=sankey_value,
            color=[c.replace(")", ", 0.4)").replace("rgb", "rgba") if c.startswith("rgb") else c
                   for c in sankey_color],
        ),
    ))
    fig_sankey.update_layout(
        title=dict(
            text=f"Tier Transitions: {first_date} to {last_date}",
            font=dict(size=16, family=FONT_FAMILY),
        ),
        font=dict(family=FONT_FAMILY, size=11),
        height=500, width=900,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    save_figure(fig_sankey, results / "figures" / "tier_transition_sankey.png")
    shutil.copy(results / "figures" / "tier_transition_sankey.png",
                figs_dir / "tier_transition_sankey.png")
    print("  tier_transition_sankey.png")

    # 10c. Sector stability bar
    stab_plot = sector_stability.sort_values("stability_rate", ascending=True)
    fig_stab = go.Figure(go.Bar(
        x=stab_plot["stability_rate"],
        y=stab_plot["major_occ_category"],
        orientation="h",
        marker_color=COLORS["accent"],
        text=[f"{v:.0f}%" for v in stab_plot["stability_rate"]],
        textposition="outside",
        textfont=dict(size=10, color="#333", family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(fig_stab,
                 "Tier Stability by Sector",
                 subtitle=f"% of occupations in the same tier at {first_date} and {last_date}",
                 x_title="Stability Rate (%)",
                 show_legend=False,
                 height=750, width=1000)
    fig_stab.update_layout(
        margin=dict(l=20, r=80),
        xaxis=dict(range=[0, 110], showgrid=True, gridcolor=COLORS["grid"]),
        yaxis=dict(showgrid=False),
        bargap=0.3,
    )
    save_figure(fig_stab, results / "figures" / "sector_tier_stability.png")
    shutil.copy(results / "figures" / "sector_tier_stability.png",
                figs_dir / "sector_tier_stability.png")
    print("  sector_tier_stability.png")

    # 10d. New high-tier entrants by sector
    new_high_sector = (
        new_high.groupby("major_occ_category")
        .size()
        .reset_index(name="n_new_high")
        .sort_values("n_new_high", ascending=True)
    )
    if not new_high_sector.empty:
        fig_nh = go.Figure(go.Bar(
            x=new_high_sector["n_new_high"],
            y=new_high_sector["major_occ_category"],
            orientation="h",
            marker_color=TIER_COLORS["high"],
            text=new_high_sector["n_new_high"].astype(str),
            textposition="outside",
            textfont=dict(size=10, color="#333", family=FONT_FAMILY),
            cliponaxis=False,
        ))
        style_figure(fig_nh,
                     "New High-Tier Entrants by Sector",
                     subtitle=f"Occupations that crossed 60% threshold — not there in {first_date}, there by {last_date}",
                     x_title="Count of occupations",
                     show_legend=False,
                     height=700, width=950)
        fig_nh.update_layout(
            margin=dict(l=20, r=60),
            xaxis=dict(showgrid=True, gridcolor=COLORS["grid"]),
            yaxis=dict(showgrid=False),
            bargap=0.3,
        )
        save_figure(fig_nh, results / "figures" / "new_high_tier_by_sector.png")
        shutil.copy(results / "figures" / "new_high_tier_by_sector.png",
                    figs_dir / "new_high_tier_by_sector.png")
        print("  new_high_tier_by_sector.png")

    # ── 11. PDF ────────────────────────────────────────────────────────────────
    report_path = HERE / "tier_churn_report.md"
    if report_path.exists():
        generate_pdf(report_path, results / "tier_churn_report.pdf")

    print("\ntier_churn: done.")


if __name__ == "__main__":
    main()
