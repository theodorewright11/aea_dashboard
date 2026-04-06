"""
run.py — Work Activity Exposure: Education Lens

What does work activity exposure mean for what we teach and train?

Three core questions:
1. What fraction of the workforce is primarily doing high-exposure activities?
   (Not just which activities are exposed, but who is doing them)
2. Which activity types are durable training targets?
   (Low exposure across configs, but also employed — worth investing in)
3. Is AI's footprint growing into new activity categories over time, or
   deepening in the ones it already covers?
   (The "is AI a fad?" question made quantitative)

Also classifies GWAs as cognitive/technical vs interpersonal vs physical —
the three-way split that matters most for education planning.

Run from project root:
    venv/Scripts/python -m analysis.questions.work_activity_exposure.education_lens.run
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
    format_workers,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
PRIMARY_KEY = "all_confirmed"
CEILING_KEY = "all_ceiling"

ROBUST_THRESHOLD = 33.0

# ── GWA classification ────────────────────────────────────────────────────────
# Maps GWA title keywords to broad domain. Applied via substring matching.
# These are the ~35 GWA categories from O*NET 2025.
GWA_DOMAIN_MAP: dict[str, str] = {
    # Cognitive / information-processing
    "Working with Computers":                                         "Cognitive/Technical",
    "Analyzing Data or Information":                                  "Cognitive/Technical",
    "Processing Information":                                         "Cognitive/Technical",
    "Making Decisions and Solving Problems":                          "Cognitive/Technical",
    "Thinking Creatively":                                            "Cognitive/Technical",
    "Estimating the Quantitative":                                    "Cognitive/Technical",
    "Updating and Using Relevant Knowledge":                          "Cognitive/Technical",
    "Interpreting the Meaning of Information":                        "Cognitive/Technical",
    "Identifying Objects, Actions, and Events":                       "Cognitive/Technical",
    "Judging the Qualities of Objects":                               "Cognitive/Technical",
    # Information gathering / documentation
    "Getting Information":                                            "Information/Documentation",
    "Documenting/Recording Information":                              "Information/Documentation",
    "Organizing, Planning, and Prioritizing Work":                    "Information/Documentation",
    "Monitor Processes, Materials, or Surroundings":                  "Information/Documentation",
    # Interpersonal / communication
    "Communicating with Supervisors, Peers, or Subordinates":         "Interpersonal",
    "Communicating with People Outside the Organization":             "Interpersonal",
    "Establishing and Maintaining Interpersonal Relationships":       "Interpersonal",
    "Assisting and Caring for Others":                                "Interpersonal",
    "Coaching and Developing Others":                                 "Interpersonal",
    "Training and Teaching Others":                                   "Interpersonal",
    "Selling or Influencing Others":                                  "Interpersonal",
    "Resolving Conflicts and Negotiating with Others":                "Interpersonal",
    "Performing for or Working Directly with the Public":             "Interpersonal",
    # Management / coordination
    "Coordinating the Work and Activities of Others":                 "Management/Coordination",
    "Scheduling Work and Activities":                                 "Management/Coordination",
    "Monitoring and Controlling Resources":                           "Management/Coordination",
    "Developing and Building Teams":                                  "Management/Coordination",
    "Guiding, Directing, and Motivating Subordinates":                "Management/Coordination",
    "Staffing Organizational Units":                                  "Management/Coordination",
    # Physical / operational
    "Handling and Moving Objects":                                    "Physical/Operational",
    "Performing General Physical Activities":                         "Physical/Operational",
    "Controlling Machines and Processes":                             "Physical/Operational",
    "Operating Vehicles, Mechanized Devices, or Equipment":           "Physical/Operational",
    "Repairing and Maintaining Mechanical Equipment":                 "Physical/Operational",
    "Repairing and Maintaining Electronic Equipment":                 "Physical/Operational",
    "Inspecting Equipment, Structures, or Materials":                 "Physical/Operational",
    "Drafting, Laying Out, and Specifying Technical Devices":         "Physical/Operational",
}


def get_wa_data(dataset_name: str, level: str = "iwa") -> pd.DataFrame:
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


def classify_gwa(gwa_name: str) -> str:
    """Classify a GWA into a broad domain using keyword matching."""
    for keyword, domain in GWA_DOMAIN_MAP.items():
        if keyword.lower() in gwa_name.lower():
            return domain
    return "Other"


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("education_lens: loading data...")

    # ── 1. Primary config IWA and GWA data ───────────────────────────────────
    prim_iwa = get_wa_data(ANALYSIS_CONFIGS[PRIMARY_KEY], "iwa")
    prim_gwa = get_wa_data(ANALYSIS_CONFIGS[PRIMARY_KEY], "gwa")

    assert not prim_iwa.empty, "No IWA data for primary config"

    # ── 2. Classify GWAs into domains ────────────────────────────────────────
    prim_gwa["domain"] = prim_gwa["category"].apply(classify_gwa)
    save_csv(
        prim_gwa[["category", "domain", "pct_tasks_affected", "workers_affected", "wages_affected"]]
        .sort_values("pct_tasks_affected", ascending=False),
        results / "gwa_domain_classified.csv",
    )

    # ── 3. Workforce share by IWA tier ───────────────────────────────────────
    # What fraction of workers are in high vs low exposure activity clusters?
    total_workers = prim_iwa["workers_affected"].sum() + (prim_iwa[prim_iwa["pct_tasks_affected"] < 1]["workers_affected"].sum())

    def assign_tier(pct: float) -> str:
        if pct >= 66:
            return "fragile"
        if pct >= ROBUST_THRESHOLD:
            return "moderate"
        return "robust"

    prim_iwa["tier"] = prim_iwa["pct_tasks_affected"].apply(assign_tier)
    tier_summary = (
        prim_iwa.groupby("tier")
        .agg(
            n_activities=("category", "count"),
            workers_affected=("workers_affected", "sum"),
            avg_pct=("pct_tasks_affected", "mean"),
        )
        .reset_index()
    )
    tier_summary["workers_affected_pct"] = tier_summary["workers_affected"] / tier_summary["workers_affected"].sum() * 100
    save_csv(tier_summary, results / "workforce_by_tier.csv")
    print("  Workforce by tier:")
    for _, row in tier_summary.iterrows():
        print(f"    {row['tier']}: {format_workers(row['workers_affected'])} ({row['workers_affected_pct']:.1f}%)")

    # ── 4. Durable training targets ───────────────────────────────────────────
    # IWAs that are: (a) robust across all 5 configs, (b) high worker count
    # Load all 5 configs and find consistent-robust IWAs
    all_robust: dict[str, list[str]] = {}
    for key, ds in ANALYSIS_CONFIGS.items():
        iwa = get_wa_data(ds, "iwa")
        if iwa.empty:
            continue
        robust = iwa[iwa["pct_tasks_affected"] < ROBUST_THRESHOLD]["category"].tolist()
        all_robust[key] = robust

    # Activities robust in all 5 configs
    stable_robust_set: set[str] = set(all_robust.get(list(ANALYSIS_CONFIGS.keys())[0], []))
    for robust_list in all_robust.values():
        stable_robust_set &= set(robust_list)

    durable_targets = prim_iwa[prim_iwa["category"].isin(stable_robust_set)].copy()
    durable_targets = durable_targets.sort_values("workers_affected", ascending=False)
    save_csv(
        durable_targets[["category", "pct_tasks_affected", "workers_affected", "wages_affected"]],
        results / "durable_training_targets.csv",
    )
    print(f"  Durable training targets (robust in all 5 configs): {len(durable_targets)}")

    # ── 5. Trend: expanding vs deepening ─────────────────────────────────────
    # Track which IWAs are newly above 10% across the time series
    series = ANALYSIS_CONFIG_SERIES[PRIMARY_KEY]
    trend_rows: list[dict] = []
    for ds_name in series:
        iwa_t = get_wa_data(ds_name, "iwa")
        if iwa_t.empty:
            continue
        date_str = ds_name.rsplit(" ", 1)[-1]
        for _, row in iwa_t.iterrows():
            trend_rows.append({
                "iwa": row["category"],
                "date": date_str,
                "pct_tasks_affected": row["pct_tasks_affected"],
            })
    trend_df = pd.DataFrame(trend_rows)

    if not trend_df.empty:
        # Compute first and last pct per IWA
        first_date = trend_df["date"].min()
        last_date = trend_df["date"].max()
        first_vals = trend_df[trend_df["date"] == first_date].set_index("iwa")["pct_tasks_affected"]
        last_vals = trend_df[trend_df["date"] == last_date].set_index("iwa")["pct_tasks_affected"]
        growth_df = pd.DataFrame({
            "iwa": last_vals.index,
            "first_pct": first_vals.reindex(last_vals.index),
            "last_pct": last_vals.values,
        })
        growth_df["delta_pp"] = growth_df["last_pct"] - growth_df["first_pct"]
        growth_df["grew"] = growth_df["delta_pp"] > 0
        growth_df = growth_df.sort_values("delta_pp", ascending=False)
        save_csv(growth_df, results / "iwa_growth.csv")

        # How many new IWAs crossed 10% (i.e., started below and ended above)?
        newly_above_10 = growth_df[
            (growth_df["first_pct"] < 10) & (growth_df["last_pct"] >= 10)
        ]
        print(f"  IWAs newly above 10% exposure since first date: {len(newly_above_10)}")
        print(f"  IWAs with growing exposure: {growth_df['grew'].sum()} / {len(growth_df)}")
    else:
        growth_df = pd.DataFrame()

    # ── 6. Domain-level exposure summary ─────────────────────────────────────
    # GWA domains: avg pct, total workers
    domain_summary = (
        prim_gwa.groupby("domain")
        .agg(
            n_gwas=("category", "count"),
            avg_pct=("pct_tasks_affected", "mean"),
            workers_affected=("workers_affected", "sum"),
        )
        .reset_index()
        .sort_values("avg_pct", ascending=False)
    )
    save_csv(domain_summary, results / "domain_exposure_summary.csv")

    # ── 7. Figures ────────────────────────────────────────────────────────────

    # 7a. Workforce by tier (pie-style bar)
    fig_tier = _make_workforce_tier_bar(tier_summary)
    _save(fig_tier, results / "figures" / "workforce_by_tier.png", figs_dir / "workforce_by_tier.png")

    # 7b. Durable training targets
    if not durable_targets.empty:
        fig_durable = _make_durable_targets_bar(durable_targets.head(20))
        _save(fig_durable, results / "figures" / "durable_training_targets.png", figs_dir / "durable_training_targets.png")

    # 7c. Exposure growth trend (top climbers + stable IWAs)
    if not trend_df.empty:
        fig_trends = _make_exposure_trend(trend_df, prim_iwa, growth_df)
        _save(fig_trends, results / "figures" / "exposure_growth_trend.png", figs_dir / "exposure_growth_trend.png")

    # 7d. Domain comparison bar
    if not domain_summary.empty:
        fig_domain = _make_domain_bar(domain_summary)
        _save(fig_domain, results / "figures" / "domain_exposure.png", figs_dir / "domain_exposure.png")

    print("  saved all figures")

    # ── 8. PDF ────────────────────────────────────────────────────────────────
    report_md = HERE / "education_lens_report.md"
    if report_md.exists():
        generate_pdf(report_md, results / "education_lens_report.pdf")

    print("education_lens: done.")


# ── Chart helpers ─────────────────────────────────────────────────────────────

def _save(fig: go.Figure, results_path: Path, figures_path: Path) -> None:
    save_figure(fig, results_path)
    shutil.copy(str(results_path), str(figures_path))


def _make_workforce_tier_bar(tier_summary: pd.DataFrame) -> go.Figure:
    tier_order = ["robust", "moderate", "fragile"]
    tier_labels = {"robust": "Robust (<33%)", "moderate": "Moderate (33–66%)", "fragile": "Fragile (≥66%)"}
    tier_colors = {"robust": COLORS["positive"], "moderate": COLORS["primary"], "fragile": COLORS["negative"]}

    df = tier_summary.set_index("tier").reindex(tier_order).reset_index()
    df = df.dropna(subset=["workers_affected"])

    fig = go.Figure(go.Bar(
        x=df["tier"].map(tier_labels),
        y=df["workers_affected"],
        marker=dict(color=[tier_colors.get(t, COLORS["muted"]) for t in df["tier"]], line=dict(width=0)),
        text=[f"{format_workers(w)}<br>({p:.1f}%)" for w, p in zip(df["workers_affected"], df["workers_affected_pct"])],
        textposition="outside",
        textfont=dict(size=12, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(
        fig,
        "Workforce by Activity Exposure Tier",
        subtitle="Workers affected by IWA tier — All Confirmed Usage | national",
        y_title="Workers Affected",
        show_legend=False,
        height=500,
        width=700,
    )
    fig.update_layout(
        margin=dict(l=60, r=40, t=80, b=80),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True),
        bargap=0.3,
    )
    return fig


def _make_durable_targets_bar(df: pd.DataFrame) -> go.Figure:
    df = df.sort_values("workers_affected", ascending=True)
    fig = go.Figure(go.Bar(
        x=df["workers_affected"],
        y=df["category"],
        orientation="h",
        marker=dict(color=COLORS["positive"], line=dict(width=0)),
        text=[f"{format_workers(w)} ({p:.1f}%)" for w, p in zip(df["workers_affected"], df["pct_tasks_affected"])],
        textposition="outside",
        textfont=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(
        fig,
        "Durable Training Targets — Robust Across All Configs",
        subtitle="IWAs with <33% exposure in every config | ranked by workers affected | text shows (confirmed %)",
        x_title="Workers Affected",
        show_legend=False,
        height=max(500, len(df) * 22),
        width=1100,
    )
    fig.update_layout(
        margin=dict(l=20, r=120, t=80, b=60),
        xaxis=dict(showgrid=True, range=[0, df["workers_affected"].max() * 1.25]),
        yaxis=dict(showgrid=False, tickfont=dict(size=9)),
        bargap=0.25,
    )
    return fig


def _make_exposure_trend(trend_df: pd.DataFrame, prim_iwa: pd.DataFrame, growth_df: pd.DataFrame) -> go.Figure:
    """Show trend lines for top climbers + a few stable-robust IWAs."""
    top_climbers = growth_df.head(6)["iwa"].tolist()
    # Add a couple of the most stable low-exposure IWAs for contrast
    stable_low = growth_df.nsmallest(3, "last_pct")["iwa"].tolist()
    show_iwas = list(dict.fromkeys(top_climbers + stable_low))  # dedupe, preserve order

    sub = trend_df[trend_df["iwa"].isin(show_iwas)].sort_values("date")

    fig = go.Figure()
    for i, iwa in enumerate(show_iwas):
        d = sub[sub["iwa"] == iwa]
        if d.empty:
            continue
        is_climber = iwa in top_climbers
        fig.add_trace(go.Scatter(
            x=d["date"],
            y=d["pct_tasks_affected"],
            mode="lines+markers",
            name=iwa,
            line=dict(
                color=CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)],
                width=3 if is_climber else 1.5,
                dash="solid" if is_climber else "dot",
            ),
            marker=dict(size=6 if is_climber else 4),
        ))

    style_figure(
        fig,
        "Is AI's Footprint Expanding? Top-Climbing Activity Types",
        subtitle="Top 6 fastest-growing IWAs (solid) vs 3 stable-low IWAs (dotted) | All Confirmed Usage series",
        x_title="Date",
        y_title="% Tasks Affected",
        height=600,
        width=1200,
    )
    fig.update_layout(margin=dict(l=60, r=40, t=80, b=120))
    return fig


def _make_domain_bar(domain_summary: pd.DataFrame) -> go.Figure:
    domain_colors = {
        "Cognitive/Technical":      COLORS["negative"],
        "Information/Documentation": COLORS["accent"],
        "Interpersonal":             COLORS["primary"],
        "Management/Coordination":   COLORS["secondary"],
        "Physical/Operational":      COLORS["positive"],
        "Other":                     COLORS["muted"],
    }
    df = domain_summary.sort_values("avg_pct", ascending=True)
    bar_colors = [domain_colors.get(d, COLORS["muted"]) for d in df["domain"]]

    fig = go.Figure(go.Bar(
        x=df["avg_pct"],
        y=df["domain"],
        orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"{v:.1f}%" for v in df["avg_pct"]],
        textposition="outside",
        textfont=dict(size=12, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(
        fig,
        "AI Exposure by Work Domain",
        subtitle="Average % tasks affected across GWAs in each domain | All Confirmed Usage",
        x_title="Average % Tasks Affected",
        show_legend=False,
        height=450,
        width=900,
    )
    fig.update_layout(
        margin=dict(l=20, r=80, t=80, b=60),
        xaxis=dict(showgrid=True, range=[0, df["avg_pct"].max() * 1.2]),
        yaxis=dict(showgrid=False),
        bargap=0.3,
    )
    return fig


if __name__ == "__main__":
    main()
