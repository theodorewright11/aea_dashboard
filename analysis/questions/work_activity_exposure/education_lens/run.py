"""
run.py — Work Activity Exposure: Education Lens

What does work activity exposure mean for what we teach and train?

Three core questions:
1. What fraction of the workforce is primarily doing high-exposure activities?
   (Not just which activities are exposed, but who is doing them)
2. Which activity types are durable training targets?
   (Low exposure across configs AND educationally relevant — associated with
   occupations that require meaningful training, not just physical labor)
3. Is AI's footprint growing into new activity categories over time, or
   deepening in the ones it already covers?
   (The "is AI a fad?" question made quantitative)

Three-category training framework:
  Category 1 — Durable (Train Directly):
    Robust (<33%) in all 5 configs AND associated with higher job zones (≥2.5).
    These are activities that education actually trains people for AND that
    will hold value as AI reshapes adjacent work.

  Category 2 — AI × Human Pair (Train for AI Collaboration):
    Moderate tier (33–66%). Human judgment combined with AI is still better
    than AI alone here. Training: develop the judgment layer above AI output,
    learn to direct and evaluate AI, build the skills AI doesn't cover well.
    Subcategory: stable moderate (slow trend) vs. rising moderate (fast trend
    heading toward fragile) — the latter may shift to oversight training soon.

  Category 3 — Delegate to AI / Oversight (Train for Direction and Review):
    Fragile (≥66%) or "next wave" (confirmed <33% but ceiling ≥33%). The human
    role here is increasingly setup, quality review, and exception handling.
    Training: set AI context effectively, review AI outputs critically, manage
    the exceptions AI can't handle.

Uncertainty note: Categories 2 and 3 are not fixed. Rising moderate activities
may become fragile; next-wave activities will when agentic AI deploys at scale.
We flag this throughout.

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
FRAGILE_THRESHOLD = 66.0
JOB_ZONE_THRESHOLD = 2.5   # mean job zone ≥ this → educationally relevant
FAST_GROWTH_THRESHOLD = 15.0  # pp over 15 months → "rising moderate"

# ── GWA classification ────────────────────────────────────────────────────────
GWA_DOMAIN_MAP: dict[str, str] = {
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
    "Getting Information":                                            "Information/Documentation",
    "Documenting/Recording Information":                              "Information/Documentation",
    "Organizing, Planning, and Prioritizing Work":                    "Information/Documentation",
    "Monitor Processes, Materials, or Surroundings":                  "Information/Documentation",
    "Communicating with Supervisors, Peers, or Subordinates":         "Interpersonal",
    "Communicating with People Outside the Organization":             "Interpersonal",
    "Establishing and Maintaining Interpersonal Relationships":       "Interpersonal",
    "Assisting and Caring for Others":                                "Interpersonal",
    "Coaching and Developing Others":                                 "Interpersonal",
    "Training and Teaching Others":                                   "Interpersonal",
    "Selling or Influencing Others":                                  "Interpersonal",
    "Resolving Conflicts and Negotiating with Others":                "Interpersonal",
    "Performing for or Working Directly with the Public":             "Interpersonal",
    "Coordinating the Work and Activities of Others":                 "Management/Coordination",
    "Scheduling Work and Activities":                                 "Management/Coordination",
    "Monitoring and Controlling Resources":                           "Management/Coordination",
    "Developing and Building Teams":                                  "Management/Coordination",
    "Guiding, Directing, and Motivating Subordinates":                "Management/Coordination",
    "Staffing Organizational Units":                                  "Management/Coordination",
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
    for keyword, domain in GWA_DOMAIN_MAP.items():
        if keyword.lower() in gwa_name.lower():
            return domain
    return "Other"


def _get_iwa_job_zones() -> pd.DataFrame:
    """Compute mean job_zone per IWA from eco_2025.

    eco_2025 has job_zone per task row (occupation-level attribute). We average
    over all occupations that have tasks in each IWA to get a mean job zone
    representing how much education/training is typically required for the
    occupations that do that type of work.
    """
    from backend.compute import load_eco_raw
    eco = load_eco_raw()
    if eco.empty or "job_zone" not in eco.columns or "iwa_title" not in eco.columns:
        return pd.DataFrame(columns=["category", "mean_job_zone"])
    return (
        eco.dropna(subset=["job_zone", "iwa_title"])
        .groupby("iwa_title")["job_zone"]
        .mean()
        .reset_index()
        .rename(columns={"iwa_title": "category", "job_zone": "mean_job_zone"})
    )


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("education_lens: loading data...")

    # ── 1. Primary config IWA and GWA data ───────────────────────────────────
    prim_iwa = get_wa_data(ANALYSIS_CONFIGS[PRIMARY_KEY], "iwa")
    ceil_iwa = get_wa_data(ANALYSIS_CONFIGS[CEILING_KEY], "iwa")
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
    def assign_tier(pct: float) -> str:
        if pct >= FRAGILE_THRESHOLD:
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

    # ── 4. IWA job zones (for education-relevance filter) ────────────────────
    iwa_jz = _get_iwa_job_zones()
    print(f"  Loaded job zones for {len(iwa_jz)} IWAs")

    # ── 5. Trend data ─────────────────────────────────────────────────────────
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

    growth_df = pd.DataFrame()
    if not trend_df.empty:
        first_date = trend_df["date"].min()
        last_date = trend_df["date"].max()
        first_vals = trend_df[trend_df["date"] == first_date].set_index("iwa")["pct_tasks_affected"]
        last_vals = trend_df[trend_df["date"] == last_date].set_index("iwa")["pct_tasks_affected"]
        growth_df = pd.DataFrame({
            "iwa": last_vals.index,
            "first_pct": first_vals.reindex(last_vals.index).values,
            "last_pct": last_vals.values,
        })
        growth_df["delta_pp"] = growth_df["last_pct"] - growth_df["first_pct"]
        growth_df["grew"] = growth_df["delta_pp"] > 0
        growth_df = growth_df.sort_values("delta_pp", ascending=False)
        save_csv(growth_df, results / "iwa_growth.csv")

        newly_above_10 = growth_df[
            (growth_df["first_pct"] < 10) & (growth_df["last_pct"] >= 10)
        ]
        print(f"  IWAs newly above 10% exposure: {len(newly_above_10)}")
        print(f"  IWAs with growing exposure: {growth_df['grew'].sum()} / {len(growth_df)}")

    # ── 6. Durable training targets (job-zone-filtered) ───────────────────────
    # Step 1: Find IWAs robust in all 5 configs
    all_robust: dict[str, list[str]] = {}
    for key, ds in ANALYSIS_CONFIGS.items():
        iwa = get_wa_data(ds, "iwa")
        if iwa.empty:
            continue
        all_robust[key] = iwa[iwa["pct_tasks_affected"] < ROBUST_THRESHOLD]["category"].tolist()

    stable_robust_set: set[str] = set(all_robust.get(list(ANALYSIS_CONFIGS.keys())[0], []))
    for robust_list in all_robust.values():
        stable_robust_set &= set(robust_list)

    durable_all = prim_iwa[prim_iwa["category"].isin(stable_robust_set)].copy()

    # Step 2: Filter by job zone — activities associated with occupations
    # requiring meaningful education/training (mean job zone >= JOB_ZONE_THRESHOLD)
    if not iwa_jz.empty:
        durable_all = durable_all.merge(iwa_jz, on="category", how="left")
        durable_all["mean_job_zone"] = durable_all["mean_job_zone"].fillna(2.0)
        educationally_relevant = durable_all[durable_all["mean_job_zone"] >= JOB_ZONE_THRESHOLD].copy()
    else:
        durable_all["mean_job_zone"] = float("nan")
        educationally_relevant = durable_all.copy()

    educationally_relevant = educationally_relevant.sort_values("workers_affected", ascending=False)
    save_csv(
        educationally_relevant[["category", "pct_tasks_affected", "workers_affected", "wages_affected", "mean_job_zone"]],
        results / "durable_training_targets.csv",
    )
    save_csv(
        durable_all[["category", "pct_tasks_affected", "workers_affected", "wages_affected", "mean_job_zone"]].sort_values("workers_affected", ascending=False),
        results / "durable_training_targets_all.csv",
    )
    print(f"  Durable targets (all robust): {len(durable_all)}, educationally relevant (jz>={JOB_ZONE_THRESHOLD}): {len(educationally_relevant)}")

    # ── 7. Three-category training framework ──────────────────────────────────
    # Category 1: Durable — educationally-relevant robust IWAs
    cat1 = educationally_relevant[["category", "pct_tasks_affected", "workers_affected"]].copy()
    cat1["training_category"] = "1_durable"

    # Category 2: AI × Human pair — moderate tier
    moderate_iwas = prim_iwa[prim_iwa["tier"] == "moderate"].copy()
    if not growth_df.empty:
        moderate_iwas = moderate_iwas.merge(
            growth_df[["iwa", "delta_pp", "first_pct", "last_pct"]].rename(columns={"iwa": "category"}),
            on="category", how="left"
        )
        moderate_iwas["delta_pp"] = moderate_iwas["delta_pp"].fillna(0)
        # Subcategorize: stable vs rising
        moderate_iwas["trend_type"] = moderate_iwas["delta_pp"].apply(
            lambda d: "rising_moderate" if d >= FAST_GROWTH_THRESHOLD else "stable_moderate"
        )
    else:
        moderate_iwas["delta_pp"] = 0.0
        moderate_iwas["trend_type"] = "stable_moderate"
    moderate_iwas["training_category"] = "2_ai_human_pair"

    cat2 = moderate_iwas[["category", "pct_tasks_affected", "workers_affected", "training_category",
                           "delta_pp", "trend_type"]].copy()

    # Category 3: Delegate/Oversight — fragile IWAs + next-wave IWAs
    fragile_iwas = prim_iwa[prim_iwa["tier"] == "fragile"].copy()
    fragile_iwas["training_category"] = "3_delegate_oversight"
    fragile_iwas["subcategory"] = "fragile"

    # Next-wave: confirmed <33% but ceiling ≥33%
    if not ceil_iwa.empty:
        ceil_for_merge = ceil_iwa.rename(columns={"pct_tasks_affected": "ceiling_pct",
                                                    "workers_affected": "ceiling_workers"})
        next_wave_df = prim_iwa.merge(ceil_for_merge[["category", "ceiling_pct"]], on="category", how="left")
        next_wave_df = next_wave_df[
            (next_wave_df["tier"] == "robust") &
            (next_wave_df["ceiling_pct"] >= ROBUST_THRESHOLD)
        ].copy()
        next_wave_df["training_category"] = "3_delegate_oversight"
        next_wave_df["subcategory"] = "next_wave"
        cat3 = pd.concat([
            fragile_iwas[["category", "pct_tasks_affected", "workers_affected", "training_category", "subcategory"]],
            next_wave_df[["category", "pct_tasks_affected", "workers_affected", "training_category", "subcategory"]],
        ], ignore_index=True)
    else:
        cat3 = fragile_iwas[["category", "pct_tasks_affected", "workers_affected", "training_category"]].copy()
        cat3["subcategory"] = "fragile"

    # Combine all categories and save
    cat1_save = cat1.copy(); cat1_save["subcategory"] = "durable"; cat1_save["delta_pp"] = float("nan")
    cat2_save = cat2.copy(); cat2_save["subcategory"] = cat2["trend_type"]
    framework_df = pd.concat([
        cat1_save[["category", "pct_tasks_affected", "workers_affected", "training_category", "subcategory", "delta_pp"]],
        cat2_save[["category", "pct_tasks_affected", "workers_affected", "training_category", "subcategory", "delta_pp"]],
        cat3[["category", "pct_tasks_affected", "workers_affected", "training_category", "subcategory"]].assign(delta_pp=float("nan")),
    ], ignore_index=True)
    save_csv(framework_df, results / "training_framework_categories.csv")
    print(f"  Training framework: Cat1={len(cat1)}, Cat2={len(cat2)} (stable={len(cat2[cat2['trend_type']=='stable_moderate'])}, rising={len(cat2[cat2['trend_type']=='rising_moderate'])}), Cat3={len(cat3)}")

    # ── 8. Domain-level exposure summary ─────────────────────────────────────
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

    # ── 9. Figures ────────────────────────────────────────────────────────────

    # 9a. Workforce by tier
    fig_tier = _make_workforce_tier_bar(tier_summary)
    _save(fig_tier, results / "figures" / "workforce_by_tier.png", figs_dir / "workforce_by_tier.png")

    # 9b. Durable training targets — educationally relevant (job-zone filtered)
    if not educationally_relevant.empty:
        fig_durable = _make_durable_targets_bar(educationally_relevant.head(20))
        _save(fig_durable, results / "figures" / "durable_training_targets.png", figs_dir / "durable_training_targets.png")

    # 9c. Training framework overview — 3 categories
    fig_framework = _make_training_framework(cat1, cat2, cat3, growth_df)
    _save(fig_framework, results / "figures" / "training_framework.png", figs_dir / "training_framework.png")

    # 9d. Exposure growth trend (top climbers + stable IWAs)
    if not trend_df.empty and not growth_df.empty:
        fig_trends = _make_exposure_trend(trend_df, prim_iwa, growth_df)
        _save(fig_trends, results / "figures" / "exposure_growth_trend.png", figs_dir / "exposure_growth_trend.png")

    # 9e. Domain comparison bar
    if not domain_summary.empty:
        fig_domain = _make_domain_bar(domain_summary)
        _save(fig_domain, results / "figures" / "domain_exposure.png", figs_dir / "domain_exposure.png")

    print("  saved all figures")

    # ── 10. PDF ────────────────────────────────────────────────────────────────
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
    jz_labels = [f" (job zone: {row['mean_job_zone']:.1f})" if pd.notna(row.get("mean_job_zone")) else ""
                 for _, row in df.iterrows()]
    fig = go.Figure(go.Bar(
        x=df["workers_affected"],
        y=df["category"],
        orientation="h",
        marker=dict(color=COLORS["positive"], line=dict(width=0)),
        text=[f"{format_workers(w)} | {p:.1f}%{jz}"
              for w, p, jz in zip(df["workers_affected"], df["pct_tasks_affected"], jz_labels)],
        textposition="outside",
        textfont=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(
        fig,
        "Durable Training Targets — Educationally Relevant",
        subtitle=f"IWAs robust in all 5 configs AND mean job zone ≥{JOB_ZONE_THRESHOLD} | ranked by workers affected",
        x_title="Workers Affected",
        show_legend=False,
        height=max(500, len(df) * 22),
        width=1100,
    )
    fig.update_layout(
        margin=dict(l=20, r=160, t=80, b=60),
        xaxis=dict(showgrid=True, range=[0, df["workers_affected"].max() * 1.35]),
        yaxis=dict(showgrid=False, tickfont=dict(size=9)),
        bargap=0.25,
    )
    return fig


def _make_training_framework(
    cat1: pd.DataFrame,
    cat2: pd.DataFrame,
    cat3: pd.DataFrame,
    growth_df: pd.DataFrame,
) -> go.Figure:
    """Overview figure: top examples from each training category with trend context.

    Layout: three horizontal bar groups, one per category, top 8 IWAs each.
    Color encodes category; bar length = workers affected.
    Delta annotation shows trend direction for Cat2 and Cat3.
    """
    CAT_COLORS = {
        "1_durable":          COLORS["positive"],
        "2_stable_moderate":  COLORS["primary"],
        "2_rising_moderate":  COLORS["secondary"],
        "3_delegate":         COLORS["negative"],
    }

    # Merge growth into cat3 for trend annotation
    if not growth_df.empty:
        cat3_merged = cat3.merge(
            growth_df[["iwa", "delta_pp"]].rename(columns={"iwa": "category"}),
            on="category", how="left"
        )
    else:
        cat3_merged = cat3.copy()
        cat3_merged["delta_pp"] = float("nan")

    # Top 8 per category by workers
    top_c1 = cat1.nlargest(8, "workers_affected")
    top_c2_stable = cat2[cat2["trend_type"] == "stable_moderate"].nlargest(5, "workers_affected")
    top_c2_rising = cat2[cat2["trend_type"] == "rising_moderate"].nlargest(5, "workers_affected")
    top_c3 = cat3_merged.nlargest(8, "workers_affected")

    def _row_label(row: dict, show_delta: bool = False) -> str:
        lbl = f"{format_workers(row['workers_affected'])} | {row['pct_tasks_affected']:.0f}%"
        if show_delta and pd.notna(row.get("delta_pp")):
            sign = "+" if row["delta_pp"] >= 0 else ""
            lbl += f" | {sign}{row['delta_pp']:.0f}pp trend"
        return lbl

    fig = go.Figure()

    # Cat 1 — Durable
    df1 = top_c1.sort_values("workers_affected", ascending=True)
    fig.add_trace(go.Bar(
        x=df1["workers_affected"],
        y=df1["category"],
        orientation="h",
        name="Durable — Train Directly",
        marker=dict(color=CAT_COLORS["1_durable"], line=dict(width=0)),
        text=[_row_label(r) for r in df1.to_dict("records")],
        textposition="outside",
        textfont=dict(size=8, family=FONT_FAMILY),
        cliponaxis=False,
        legendgroup="cat1",
    ))

    # Cat 2a — stable moderate
    df2s = top_c2_stable.sort_values("workers_affected", ascending=True)
    fig.add_trace(go.Bar(
        x=df2s["workers_affected"],
        y=df2s["category"],
        orientation="h",
        name="AI × Human (Stable) — Train AI Collaboration",
        marker=dict(color=CAT_COLORS["2_stable_moderate"], line=dict(width=0)),
        text=[_row_label(r, show_delta=True) for r in df2s.to_dict("records")],
        textposition="outside",
        textfont=dict(size=8, family=FONT_FAMILY),
        cliponaxis=False,
        legendgroup="cat2s",
    ))

    # Cat 2b — rising moderate
    df2r = top_c2_rising.sort_values("workers_affected", ascending=True)
    fig.add_trace(go.Bar(
        x=df2r["workers_affected"],
        y=df2r["category"],
        orientation="h",
        name="AI × Human (Rising) — Train AI Collaboration + Watch",
        marker=dict(color=CAT_COLORS["2_rising_moderate"], line=dict(width=0)),
        text=[_row_label(r, show_delta=True) for r in df2r.to_dict("records")],
        textposition="outside",
        textfont=dict(size=8, family=FONT_FAMILY),
        cliponaxis=False,
        legendgroup="cat2r",
    ))

    # Cat 3 — delegate/oversight
    df3 = top_c3.sort_values("workers_affected", ascending=True)
    fig.add_trace(go.Bar(
        x=df3["workers_affected"],
        y=df3["category"],
        orientation="h",
        name="Delegate to AI — Train for Oversight",
        marker=dict(color=CAT_COLORS["3_delegate"], line=dict(width=0)),
        text=[_row_label(r, show_delta=True) for r in df3.to_dict("records")],
        textposition="outside",
        textfont=dict(size=8, family=FONT_FAMILY),
        cliponaxis=False,
        legendgroup="cat3",
    ))

    n_rows = len(df1) + len(df2s) + len(df2r) + len(df3)
    style_figure(
        fig,
        "Three-Category Training Framework",
        subtitle="Top IWAs per category | workers affected | trend = growth since Sept 2024 | uncertainty: rising moderate may become delegation territory",
        x_title="Workers Affected",
        height=max(700, n_rows * 22 + 200),
        width=1300,
    )
    fig.update_layout(
        barmode="overlay",
        margin=dict(l=20, r=200, t=80, b=130),
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=False, tickfont=dict(size=9)),
        bargap=0.25,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5,
            font=dict(size=9),
        ),
    )
    return fig


def _make_exposure_trend(trend_df: pd.DataFrame, prim_iwa: pd.DataFrame, growth_df: pd.DataFrame) -> go.Figure:
    """Show trend lines for top climbers + a few stable-robust IWAs."""
    top_climbers = growth_df.head(6)["iwa"].tolist()
    stable_low = growth_df.nsmallest(3, "last_pct")["iwa"].tolist()
    show_iwas = list(dict.fromkeys(top_climbers + stable_low))

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
    fig.update_layout(margin=dict(l=60, r=40, t=80, b=140))
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
