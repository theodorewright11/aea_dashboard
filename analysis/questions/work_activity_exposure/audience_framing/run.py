"""
run.py — Work Activity Exposure: Audience Framing

Computes the supporting statistics and charts for four distinct audiences:
  Policy / legislators  — Where should training dollars go? What's coming?
  Workforce / educators — Which activity clusters to emphasize, which to deprioritize
  Researchers           — What this data supports vs. doesn't; novel angles
  Laypeople             — Is AI a fad? Will my kids need to be programmers?

Pulls from the other three sub-questions' CSVs where possible; generates
dedicated figures for each audience framing.

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

    # Assign tiers
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

    # Compute GWA growth (first → last)
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

    # ── Compute statistics for each audience ─────────────────────────────────

    # -- Policy stats
    # Top 5 GWAs by workers affected (primary config)
    top5_gwa_workers = prim_gwa.nlargest(5, "workers_affected")[["category", "workers_affected", "pct_tasks_affected"]]
    # What % of total BLS workers are in activities with >33% exposure?
    total_w = prim_iwa["workers_affected"].sum()
    exposed_w = prim_iwa[prim_iwa["pct_tasks_affected"] >= ROBUST_THRESHOLD]["workers_affected"].sum()
    pct_workforce_exposed = exposed_w / total_w * 100 if total_w > 0 else 0.0
    # GWAs with largest ceiling gap (next investment targets)
    top_gap_gwa = cv.merge(prim_gwa[["category", "workers_affected"]], on="category", how="left") if not prim_gwa.empty else cv
    top_gap_gwa = cv.nlargest(5, "gap_pp")[["category", "pct_tasks_affected", "ceiling_pct", "gap_pp"]]

    print(f"  Policy: {pct_workforce_exposed:.1f}% of affected workers in activities with >=33% exposure")

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

    # -- Workforce stats
    # IWAs that are: robust AND growing (the sweet spot for training)
    robust_iwas = prim_iwa[prim_iwa["tier"] == "robust"].copy()
    if not gwa_growth.empty:
        # Can't grow at GWA level for IWA; use IWA growth from education_lens if available
        pass
    training_sweet_spot = robust_iwas.nlargest(10, "workers_affected")[
        ["category", "pct_tasks_affected", "workers_affected"]
    ]
    save_csv(training_sweet_spot, results / "workforce_training_sweet_spot.csv")

    # -- Researcher stats
    # Config comparison at GWA level — how much do configs agree?
    config_pcts: dict[str, pd.Series] = {}
    for key, ds in ANALYSIS_CONFIGS.items():
        gwa = get_wa_data(ds, "gwa")
        if not gwa.empty:
            config_pcts[key] = gwa.set_index("category")["pct_tasks_affected"]

    if config_pcts:
        config_df = pd.DataFrame(config_pcts)
        config_df.columns = [ANALYSIS_CONFIG_LABELS[k] for k in config_df.columns]
        config_df["range_pp"] = config_df.max(axis=1) - config_df.min(axis=1)
        config_df["cv"] = config_df.iloc[:, :-1].std(axis=1) / config_df.iloc[:, :-1].mean(axis=1)
        config_df = config_df.sort_values("range_pp", ascending=False)
        save_csv(config_df.reset_index().rename(columns={"category": "gwa"}), results / "researcher_config_spread.csv")

    # -- Layperson stats
    # Simple GWA picture: which activities people recognize in their daily work
    layperson_gwa = prim_gwa[["category", "pct_tasks_affected", "workers_affected", "tier"]].copy()
    layperson_gwa = layperson_gwa.sort_values("workers_affected", ascending=False)
    save_csv(layperson_gwa, results / "layperson_gwa_summary.csv")

    # ── Figures ───────────────────────────────────────────────────────────────

    # Figure A (Policy): GWA workers affected + ceiling gap — what's coming
    fig_policy = _make_policy_gwa_chart(prim_gwa, cv)
    _save(fig_policy, results / "figures" / "policy_gwa_workers.png", figs_dir / "policy_gwa_workers.png")

    # Figure B (Workforce): Sweet spot — durable high-worker activities
    fig_workforce = _make_workforce_sweet_spot(training_sweet_spot)
    _save(fig_workforce, results / "figures" / "workforce_training_targets.png", figs_dir / "workforce_training_targets.png")

    # Figure C (Researcher): Config spread at GWA level
    if config_pcts:
        fig_researcher = _make_researcher_config_chart(config_df.reset_index().rename(columns={"category": "gwa"}))
        _save(fig_researcher, results / "figures" / "researcher_config_comparison.png", figs_dir / "researcher_config_comparison.png")

    # Figure D (Layperson): Simple "is AI a fad?" trend for GWAs
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
    """GWA bar: workers affected + ceiling gap stacked — the policy picture."""
    # Merge ceiling gap into GWA
    cv_gwa = cv.merge(
        prim_gwa[["category", "workers_affected", "pct_tasks_affected"]],
        on=["category", "pct_tasks_affected"], how="right"
    ) if "gap_pp" in cv.columns else prim_gwa.copy()

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


def _make_workforce_sweet_spot(df: pd.DataFrame) -> go.Figure:
    df = df.sort_values("workers_affected", ascending=True)
    fig = go.Figure(go.Bar(
        x=df["workers_affected"],
        y=df["category"],
        orientation="h",
        marker=dict(color=COLORS["positive"], line=dict(width=0)),
        text=[f"{format_workers(w)} | {p:.1f}%" for w, p in zip(df["workers_affected"], df["pct_tasks_affected"])],
        textposition="outside",
        textfont=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    style_figure(
        fig,
        "Training Sweet Spot — Large Workforce, AI-Resistant",
        subtitle="Robust IWAs (<33% exposure) ranked by workers affected | these are the durable investments",
        x_title="Workers Affected",
        show_legend=False,
        height=max(450, len(df) * 24),
        width=1000,
    )
    fig.update_layout(
        margin=dict(l=20, r=120, t=80, b=60),
        xaxis=dict(showgrid=True, range=[0, df["workers_affected"].max() * 1.3]),
        yaxis=dict(showgrid=False, tickfont=dict(size=10)),
        bargap=0.25,
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
        margin=dict(l=20, r=40, t=80, b=120),
    )
    return fig


def _make_layperson_trend(trend_df: pd.DataFrame, prim_gwa: pd.DataFrame) -> go.Figure:
    """Simple trend lines for the top 5 GWAs by workers affected — is AI growing?"""
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
    fig.update_layout(margin=dict(l=60, r=40, t=80, b=120))
    return fig


if __name__ == "__main__":
    main()
