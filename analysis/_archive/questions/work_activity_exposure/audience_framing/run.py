"""
run.py — Work Activity Exposure: Audience Framing

Computes the supporting statistics and charts for four distinct audiences:
  Policy / legislators  — Where should training dollars go? What's coming?
  Workforce / educators — Which activity clusters to emphasize, using the
                          three-category training framework
  Researchers           — What this data supports vs. doesn't; novel angles;
                          AEI eco_2015 vs eco_2025 baseline comparison
  Laypeople             — Is AI a fad? How to think about my own job?

Three-category training framework (for workforce/educators and laypeople):
  1. Durable — Train Directly: robust activities, educationally relevant
  2. AI × Human Pair — Train for AI Collaboration: moderate tier, human
     judgment + AI is still better than AI alone
  3. Delegate to AI / Oversight — Train for Direction and Review: fragile or
     next-wave activities where human role shifts to setup and review

Pulls from the other three sub-questions' CSVs where possible.

Run from project root:
    venv/Scripts/python -m analysis.questions.work_activity_exposure.audience_framing.run
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

# Raw AEI dataset (is_aei=True → eco_2015 baseline)
AEI_BOTH_ECO2015 = "AEI Both 2026-02-12"


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


def get_wa_data_aei(dataset_name: str, level: str = "gwa") -> pd.DataFrame:
    """Get work activity data for a raw AEI dataset (is_aei=True → eco_2015, aei_group)."""
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
    # AEI raw datasets (is_aei=True) always come back via aei_group
    group = result.get("aei_group")
    if group is None:
        return pd.DataFrame()
    rows = group.get(level, [])
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    print("audience_framing: loading data...")

    # ── Load base data ────────────────────────────────────────────────────────
    prim_iwa = get_wa_data(ANALYSIS_CONFIGS[PRIMARY_KEY], "iwa")
    ceil_iwa = get_wa_data(ANALYSIS_CONFIGS[CEILING_KEY], "iwa")
    prim_gwa = get_wa_data(ANALYSIS_CONFIGS[PRIMARY_KEY], "gwa")

    assert not prim_iwa.empty, "No IWA data"

    # Merge confirmed + ceiling
    cv = prim_iwa.merge(
        ceil_iwa[["category", "pct_tasks_affected"]].rename(
            columns={"pct_tasks_affected": "ceiling_pct"}
        ),
        on="category", how="left"
    )
    cv["gap_pp"] = cv["ceiling_pct"] - cv["pct_tasks_affected"]

    def tier(pct: float) -> str:
        if pct >= 66:  return "fragile"
        if pct >= ROBUST_THRESHOLD: return "moderate"
        return "robust"

    prim_iwa["tier"] = prim_iwa["pct_tasks_affected"].apply(tier)
    prim_gwa["tier"] = prim_gwa["pct_tasks_affected"].apply(tier)

    # ── Trend data ────────────────────────────────────────────────────────────
    series = ANALYSIS_CONFIG_SERIES[PRIMARY_KEY]
    trend_rows: list[dict] = []
    for ds_name in series:
        gwa_t = get_wa_data(ds_name, "gwa")
        if gwa_t.empty:
            continue
        date_str = ds_name.rsplit(" ", 1)[-1]
        for _, row in gwa_t.iterrows():
            trend_rows.append({
                "gwa": row["category"],
                "date": date_str,
                "pct_tasks_affected": row["pct_tasks_affected"],
                "workers_affected": row["workers_affected"],
            })
    trend_df = pd.DataFrame(trend_rows)

    gwa_growth: pd.DataFrame = pd.DataFrame()
    if not trend_df.empty:
        first_date = trend_df["date"].min()
        last_date  = trend_df["date"].max()
        first_v = trend_df[trend_df["date"] == first_date].set_index("gwa")["pct_tasks_affected"]
        last_v  = trend_df[trend_df["date"] == last_date].set_index("gwa")["pct_tasks_affected"]
        gwa_growth = pd.DataFrame({
            "gwa": last_v.index,
            "first_pct": first_v.reindex(last_v.index).values,
            "last_pct": last_v.values,
        })
        gwa_growth["delta_pp"] = gwa_growth["last_pct"] - gwa_growth["first_pct"]
        gwa_growth = gwa_growth.sort_values("delta_pp", ascending=False).reset_index(drop=True)

    # ── Policy stats ──────────────────────────────────────────────────────────
    total_w = prim_iwa["workers_affected"].sum()
    exposed_w = prim_iwa[prim_iwa["pct_tasks_affected"] >= ROBUST_THRESHOLD]["workers_affected"].sum()
    pct_workforce_exposed = exposed_w / total_w * 100 if total_w > 0 else 0.0
    print(f"  Policy: {pct_workforce_exposed:.1f}% of affected workers in >=33% exposure activities")

    policy_stats = pd.DataFrame({
        "metric": [
            "pct_workforce_in_exposed_activities",
            "workers_in_exposed_activities",
            "workers_total",
            "n_fragile_iwas",
            "n_moderate_iwas",
            "n_robust_iwas",
        ],
        "value": [
            round(pct_workforce_exposed, 2),
            round(exposed_w / 1e6, 2),
            round(total_w / 1e6, 2),
            int((prim_iwa["tier"] == "fragile").sum()),
            int((prim_iwa["tier"] == "moderate").sum()),
            int((prim_iwa["tier"] == "robust").sum()),
        ],
        "unit": ["pct", "M workers", "M workers", "count", "count", "count"],
    })
    save_csv(policy_stats, results / "policy_key_stats.csv")

    # ── Workforce stats — training framework ──────────────────────────────────
    # Load education_lens training framework if available
    framework_path = HERE.parent / "education_lens" / "results" / "training_framework_categories.csv"
    if framework_path.exists():
        framework_df = pd.read_csv(framework_path)
    else:
        # Build minimal framework from primary IWA data
        framework_df = prim_iwa[["category", "pct_tasks_affected", "workers_affected", "tier"]].copy()
        framework_df["training_category"] = framework_df["tier"].map({
            "robust": "1_durable", "moderate": "2_ai_human_pair", "fragile": "3_delegate_oversight"
        })
        framework_df["subcategory"] = framework_df["tier"]
        framework_df["delta_pp"] = float("nan")

    # Top sweet-spot IWAs: durable category, large workforce
    durable_sweet_spot = framework_df[
        framework_df["training_category"] == "1_durable"
    ].nlargest(10, "workers_affected")[["category", "pct_tasks_affected", "workers_affected"]]
    save_csv(durable_sweet_spot, results / "workforce_training_sweet_spot.csv")

    # ── Researcher stats — config spread + eco_2015 comparison ───────────────
    config_pcts: dict[str, pd.Series] = {}
    for key, ds in ANALYSIS_CONFIGS.items():
        gwa = get_wa_data(ds, "gwa")
        if not gwa.empty:
            config_pcts[key] = gwa.set_index("category")["pct_tasks_affected"]

    config_df = pd.DataFrame()
    if config_pcts:
        config_df = pd.DataFrame(config_pcts)
        config_df.columns = [ANALYSIS_CONFIG_LABELS[k] for k in config_df.columns]
        config_df["range_pp"] = config_df.max(axis=1) - config_df.min(axis=1)
        config_df["cv"] = config_df.iloc[:, :-1].std(axis=1) / config_df.iloc[:, :-1].mean(axis=1)
        config_df = config_df.sort_values("range_pp", ascending=False)
        save_csv(config_df.reset_index().rename(columns={"category": "gwa"}), results / "researcher_config_spread.csv")

    # AEI eco_2015 baseline comparison
    # "AEI Both 2026-02-12" uses eco_2015 (is_aei=True → aei_group)
    # "AEI Both + Micro 2026-02-12" uses eco_2025 (is_aei=False → mcp_group)
    # Both capture similar AEI usage data (AEI conv + API); eco_2025 also includes Microsoft
    print(f"  Loading AEI eco_2015 baseline ({AEI_BOTH_ECO2015})...")
    aei_gwa_eco2015 = get_wa_data_aei(AEI_BOTH_ECO2015, "gwa")
    aei_iwa_eco2015 = get_wa_data_aei(AEI_BOTH_ECO2015, "iwa")
    if not aei_gwa_eco2015.empty:
        print(f"  eco_2015 GWA data: {len(aei_gwa_eco2015)} rows")
        aei_gwa_eco2015 = aei_gwa_eco2015.rename(columns={
            "pct_tasks_affected": "pct_eco2015",
            "workers_affected": "workers_eco2015",
        })
    if not aei_iwa_eco2015.empty:
        print(f"  eco_2015 IWA data: {len(aei_iwa_eco2015)} rows")

    # eco_2025 GWA (primary config = AEI Both + Micro, which is the closest comparable)
    eco2025_gwa = prim_gwa.rename(columns={
        "pct_tasks_affected": "pct_eco2025",
        "workers_affected": "workers_eco2025",
    })

    baseline_comp_gwa = pd.DataFrame()
    if not aei_gwa_eco2015.empty and not eco2025_gwa.empty:
        baseline_comp_gwa = aei_gwa_eco2015[["category", "pct_eco2015", "workers_eco2015"]].merge(
            eco2025_gwa[["category", "pct_eco2025", "workers_eco2025"]],
            on="category", how="outer"
        )
        baseline_comp_gwa["diff_pp"] = baseline_comp_gwa["pct_eco2025"] - baseline_comp_gwa["pct_eco2015"]
        save_csv(baseline_comp_gwa.sort_values("pct_eco2025", ascending=False, na_position="last"),
                 results / "researcher_eco_baseline_comparison_gwa.csv")

    if not aei_iwa_eco2015.empty:
        eco2025_iwa = prim_iwa.rename(columns={
            "pct_tasks_affected": "pct_eco2025",
            "workers_affected": "workers_eco2025",
        })
        baseline_comp_iwa = aei_iwa_eco2015[["category", "pct_tasks_affected"]].rename(
            columns={"pct_tasks_affected": "pct_eco2015"}
        ).merge(
            eco2025_iwa[["category", "pct_eco2025", "workers_eco2025"]],
            on="category", how="outer"
        )
        baseline_comp_iwa["diff_pp"] = baseline_comp_iwa["pct_eco2025"] - baseline_comp_iwa["pct_eco2015"]
        save_csv(baseline_comp_iwa.sort_values("pct_eco2025", ascending=False, na_position="last"),
                 results / "researcher_eco_baseline_comparison_iwa.csv")
        print(f"  Baseline comparison: {len(baseline_comp_iwa)} IWAs matched, {baseline_comp_iwa['pct_eco2025'].notna().sum()} in eco_2025, {baseline_comp_iwa['pct_eco2015'].notna().sum()} in eco_2015")

    # ── Layperson stats ───────────────────────────────────────────────────────
    layperson_gwa = prim_gwa[["category", "pct_tasks_affected", "workers_affected", "tier"]].copy()
    layperson_gwa = layperson_gwa.sort_values("workers_affected", ascending=False)
    save_csv(layperson_gwa, results / "layperson_gwa_summary.csv")

    # ── Figures ───────────────────────────────────────────────────────────────

    # Figure A (Policy): GWA workers affected — what's coming
    fig_policy = _make_policy_gwa_chart(prim_gwa, cv)
    _save(fig_policy, results / "figures" / "policy_gwa_workers.png", figs_dir / "policy_gwa_workers.png")

    # Figure B (Workforce): Sweet spot — 3-category training framework summary
    fig_workforce = _make_workforce_framework_chart(framework_df, prim_iwa)
    _save(fig_workforce, results / "figures" / "workforce_training_targets.png", figs_dir / "workforce_training_targets.png")

    # Figure C (Researcher): Config spread at GWA level
    if not config_df.empty:
        fig_researcher = _make_researcher_config_chart(config_df.reset_index().rename(columns={"category": "gwa"}))
        _save(fig_researcher, results / "figures" / "researcher_config_comparison.png", figs_dir / "researcher_config_comparison.png")

    # Figure D (Researcher): eco_2015 vs eco_2025 baseline comparison at GWA level
    if not baseline_comp_gwa.empty:
        fig_baseline = _make_eco_baseline_comparison(baseline_comp_gwa)
        _save(fig_baseline, results / "figures" / "researcher_eco_baseline_comparison.png",
              figs_dir / "researcher_eco_baseline_comparison.png")
        print("  Saved eco_2015 vs eco_2025 comparison figure")

    # Figure E (Layperson): Simple "is AI a fad?" trend for GWAs
    if not trend_df.empty:
        fig_layperson = _make_layperson_trend(trend_df, prim_gwa)
        _save(fig_layperson, results / "figures" / "layperson_ai_trend.png", figs_dir / "layperson_ai_trend.png")

    print("  saved all figures")

    # ── PDF ────────────────────────────────────────────────────────────────────
    report_md = HERE / "audience_framing_report.md"
    if report_md.exists():
        generate_pdf(report_md, results / "audience_framing_report.pdf")

    print("audience_framing: done.")


# ── Chart helpers ─────────────────────────────────────────────────────────────

def _save(fig: go.Figure, results_path: Path, figures_path: Path) -> None:
    save_figure(fig, results_path)
    shutil.copy(str(results_path), str(figures_path))


def _make_policy_gwa_chart(prim_gwa: pd.DataFrame, cv: pd.DataFrame) -> go.Figure:
    df = prim_gwa.sort_values("workers_affected", ascending=True).tail(15)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["workers_affected"],
        y=df["category"],
        orientation="h",
        name="Workers Affected (Confirmed)",
        marker=dict(color=COLORS["primary"], line=dict(width=0)),
        text=[f"{format_workers(w)} ({p:.1f}%)" for w, p in zip(df["workers_affected"], df["pct_tasks_affected"])],
        textposition="outside",
        textfont=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(
        fig,
        "Where Workforce Investment Matters Most",
        subtitle="Workers in AI-exposed activities (confirmed usage) — top 15 GWAs by scale | national",
        x_title="Workers Affected",
        show_legend=False,
        height=600,
        width=1000,
    )
    fig.update_layout(
        margin=dict(l=20, r=120, t=80, b=60),
        xaxis=dict(showgrid=True, range=[0, df["workers_affected"].max() * 1.3]),
        yaxis=dict(showgrid=False, tickfont=dict(size=10)),
        bargap=0.25,
    )
    return fig


def _make_workforce_framework_chart(framework_df: pd.DataFrame, prim_iwa: pd.DataFrame) -> go.Figure:
    """Summary chart: workers in each training category with category labels."""
    CAT_LABELS = {
        "1_durable":           "Durable\n(Train Directly)",
        "2_ai_human_pair":     "AI × Human Pair\n(Train AI Collaboration)",
        "3_delegate_oversight": "Delegate to AI\n(Train for Oversight)",
    }
    CAT_COLORS = {
        "1_durable":           COLORS["positive"],
        "2_ai_human_pair":     COLORS["primary"],
        "3_delegate_oversight": COLORS["negative"],
    }

    # Aggregate workers per category
    cat_summary = (
        framework_df.groupby("training_category")
        .agg(
            workers=("workers_affected", "sum"),
            n_iwas=("category", "count"),
        )
        .reset_index()
    )
    cat_summary = cat_summary[cat_summary["training_category"].isin(CAT_LABELS)].copy()
    cat_summary["label"] = cat_summary["training_category"].map(CAT_LABELS)
    cat_summary["color"] = cat_summary["training_category"].map(CAT_COLORS)
    total_w = cat_summary["workers"].sum()
    cat_summary["pct"] = cat_summary["workers"] / total_w * 100

    fig = go.Figure(go.Bar(
        x=cat_summary["label"],
        y=cat_summary["workers"],
        marker=dict(color=cat_summary["color"].tolist(), line=dict(width=0)),
        text=[f"{format_workers(w)}<br>({p:.0f}%)<br>{n} IWAs"
              for w, p, n in zip(cat_summary["workers"], cat_summary["pct"], cat_summary["n_iwas"])],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(
        fig,
        "Workforce by Training Category",
        subtitle="Three training strategies based on AI exposure tier and trend | All Confirmed Usage | national",
        y_title="Workers Affected",
        show_legend=False,
        height=550,
        width=850,
    )
    fig.update_layout(
        margin=dict(l=60, r=40, t=80, b=100),
        xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(showgrid=True),
        bargap=0.35,
    )
    return fig


def _make_researcher_config_chart(config_df: pd.DataFrame) -> go.Figure:
    """Dotplot: GWA × 5 configs showing spread."""
    config_keys = list(ANALYSIS_CONFIG_LABELS.values())
    gwa_order = config_df.sort_values("range_pp", ascending=False)["gwa"].tolist()

    fig = go.Figure()
    for i, label in enumerate(config_keys):
        if label not in config_df.columns:
            continue
        fig.add_trace(go.Scatter(
            x=config_df[label],
            y=config_df["gwa"],
            mode="markers",
            name=label,
            marker=dict(
                color=CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)],
                size=8,
                opacity=0.8,
            ),
        ))

    style_figure(
        fig,
        "Config Agreement at GWA Level",
        subtitle="Each dot = one config's pct_tasks_affected for that GWA | horizontal spread = disagreement between configs",
        x_title="% Tasks Affected",
        height=600,
        width=1100,
    )
    fig.update_layout(
        yaxis=dict(
            categoryorder="array",
            categoryarray=list(reversed(gwa_order)),
            tickfont=dict(size=9),
        ),
        margin=dict(l=20, r=40, t=80, b=130),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
        ),
    )
    return fig


def _make_eco_baseline_comparison(baseline_comp: pd.DataFrame) -> go.Figure:
    """Grouped bar: GWA pct under eco_2015 (AEI Both) vs eco_2025 (AEI Both + Micro).

    Caveat: eco_2015 and eco_2025 use different O*NET task inventories so absolute
    values are not directly comparable. The comparison is directionally informative —
    it shows which GWAs shift when you use the newer baseline and Microsoft data.
    eco_2025 also adds Microsoft scores, which inflates some categories.
    """
    # Drop GWAs missing from both
    df = baseline_comp.dropna(subset=["pct_eco2015", "pct_eco2025"], how="all").copy()
    # Sort by eco_2025 pct descending
    df = df.sort_values("pct_eco2025", ascending=True, na_position="last")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["pct_eco2015"],
        y=df["category"],
        orientation="h",
        name="AEI Both 2026-02-12 (eco_2015 baseline)",
        marker=dict(color=COLORS["primary"], opacity=0.85, line=dict(width=0)),
    ))
    fig.add_trace(go.Bar(
        x=df["pct_eco2025"],
        y=df["category"],
        orientation="h",
        name="AEI Both + Micro 2026-02-12 (eco_2025 baseline)",
        marker=dict(color=COLORS["accent"], opacity=0.85, line=dict(width=0)),
    ))

    style_figure(
        fig,
        "GWA Exposure: eco_2015 vs eco_2025 Baseline",
        subtitle="AEI Both (eco_2015 O*NET tasks) vs AEI Both + Micro (eco_2025 O*NET tasks) | caveat: task inventories and Microsoft inclusion differ — directional comparison only",
        x_title="% Tasks Affected",
        height=max(500, len(df) * 18),
        width=1200,
    )
    fig.update_layout(
        barmode="group",
        margin=dict(l=20, r=40, t=100, b=140),
        yaxis=dict(showgrid=False, tickfont=dict(size=9)),
        xaxis=dict(showgrid=True),
        bargap=0.2,
        bargroupgap=0.05,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.13,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
        ),
    )
    return fig


def _make_layperson_trend(trend_df: pd.DataFrame, prim_gwa: pd.DataFrame) -> go.Figure:
    """Simple trend lines for the top 5 GWAs by workers affected."""
    top5 = prim_gwa.nlargest(5, "workers_affected")["category"].tolist()
    sub = trend_df[trend_df["gwa"].isin(top5)].sort_values("date")

    fig = go.Figure()
    for i, gwa in enumerate(top5):
        d = sub[sub["gwa"] == gwa]
        if d.empty:
            continue
        fig.add_trace(go.Scatter(
            x=d["date"],
            y=d["pct_tasks_affected"],
            mode="lines+markers",
            name=gwa,
            line=dict(color=CATEGORY_PALETTE[i % len(CATEGORY_PALETTE)], width=3),
            marker=dict(size=7),
        ))

    style_figure(
        fig,
        "AI Exposure Over Time — Is It Growing?",
        subtitle="Top 5 GWAs by workers affected | All Confirmed Usage series | % tasks affected",
        x_title="Date",
        y_title="% Tasks Affected",
        height=550,
        width=1100,
    )
    fig.update_layout(margin=dict(l=60, r=40, t=80, b=140))
    return fig


if __name__ == "__main__":
    main()
