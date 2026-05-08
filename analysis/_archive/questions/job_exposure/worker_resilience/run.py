"""
run.py — Job Exposure: Worker Resilience

What can an individual worker do to make their job more resilient to AI?

For each occupation, ranks Skills, Abilities, and Knowledge elements by where
AI's current capability sits relative to the occupation's own requirement.
Elements where AI is below 100% of the requirement are where training effort
matters most (human advantage). Elements where AI is above 100% are where
workers should leverage AI as a tool rather than compete with it.

Uses all three O*NET types (S + A + K), importance >= 3 filter.
AI-as-pct per (occ, element) = AI capability score / occ_score × 100.
Per-occ overall = ratio of sums: sum(ai_score) / sum(occ_score) × 100.
All charts show the percentage framing (100% = neutral line, above = AI leads).

Key additions:
  - Separate charts for each SKA domain (3 human-advantage + 3 AI-advantage)
  - Separate heatmaps per domain (skills, abilities, knowledge)
  - Tips-and-tricks section: 3 occupations with actionable SKA + task guidance
  - Ceiling comparison layer

Primary config: all_confirmed. Ceiling shown as comparison.

Run from project root:
    venv/Scripts/python -m analysis.questions.job_exposure.worker_resilience.run
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
    ANALYSIS_CONFIG_SERIES,
    OCCS_OF_INTEREST,
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.data.compute_ska import SKAResult, compute_ska, load_ska_data
from analysis.utils import (
    COLORS,
    FONT_FAMILY,
    format_workers,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent

PRIMARY_KEY = "all_confirmed"
CEILING_KEY = "all_ceiling"
TOP_N_ELEMENTS = 15

# Occupations for tips-and-tricks section
TIPS_OCCS = [
    "Secretaries and Administrative Assistants, Except Legal, Medical, and Executive",
    "Registered Nurses",
    "Construction Laborers",
]


def _find_occ(title: str, available: set[str]) -> str | None:
    """Fuzzy match an occupation title against available titles."""
    title_lower = title.lower()
    for occ in available:
        if occ.lower() == title_lower:
            return occ
    for occ in available:
        if title_lower in occ.lower() or occ.lower() in title_lower:
            return occ
    return None


# ── Figures ───────────────────────────────────────────────────────────────────

def _element_gap_bar(
    element_df: pd.DataFrame,
    title: str,
    subtitle: str,
    direction: str,
    n: int = TOP_N_ELEMENTS,
    domain_filter: str | None = None,
) -> go.Figure:
    """Horizontal bar chart of top N elements ranked by `ai_pct_eco_mean`.

    `ai_pct_eco_mean = ai_capability / eco_mean_occ_score × 100` — reads as
    "AI has reached X% of the typical job's requirement for this element."
    Below 100 = human advantage; above 100 = AI leads.
    """
    df = element_df.copy()
    if domain_filter:
        df = df[df["type"] == domain_filter]

    if direction == "human_advantage":
        top = df.nsmallest(n, "ai_pct_eco_mean").sort_values("ai_pct_eco_mean", ascending=False)
        color = COLORS["primary"]
    else:
        top = df.nlargest(n, "ai_pct_eco_mean").sort_values("ai_pct_eco_mean", ascending=True)
        color = COLORS["negative"]

    if top.empty:
        return go.Figure()

    labels = [f"{v:.0f}%  ({t})" for v, t in zip(top["ai_pct_eco_mean"], top["type"])]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top["element_name"],
        x=top["ai_pct_eco_mean"],
        orientation="h",
        marker=dict(color=color, line=dict(width=0)),
        text=labels,
        textposition="outside",
        textfont=dict(size=10, color=COLORS["neutral"], family=FONT_FAMILY),
        cliponaxis=False,
    ))
    # 100% reference line (neutral — AI matches human requirement)
    fig.add_vline(x=100, line_dash="dot", line_color=COLORS["neutral"], line_width=1,
                  annotation_text="AI = 100% of occ need",
                  annotation_position="top",
                  annotation_font=dict(size=9, color=COLORS["neutral"], family=FONT_FAMILY))
    chart_h = max(400, len(top) * 38 + 200)
    style_figure(fig, title, subtitle=subtitle, x_title="AI capability as % of occ requirement",
                 height=chart_h, show_legend=False)
    fig.update_layout(
        margin=dict(l=20, r=120, t=80, b=100),
        xaxis=dict(showgrid=True, gridcolor=COLORS["border"], zeroline=False),
        yaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10, family=FONT_FAMILY)),
        bargap=0.25,
    )
    return fig


def _occ_heatmap(
    occ_elem_df: pd.DataFrame,
    occs: list[str],
    elements: list[str],
    title: str,
    subtitle: str,
) -> go.Figure:
    """Heatmap: occ × element AI-pct-of-occ for a selected set of occs and elements.

    Cell value = ai_capability / occ_score × 100. 100% is the neutral line;
    below 100 = human advantage, above 100 = AI leads.
    """
    pivot = occ_elem_df[
        occ_elem_df["title_current"].isin(occs) &
        occ_elem_df["element_name"].isin(elements)
    ].pivot_table(
        index="title_current", columns="element_name", values="ai_pct_occ", aggfunc="mean"
    )
    pivot = pivot.reindex(index=occs, columns=elements)

    z = pivot.values
    fig = go.Figure(go.Heatmap(
        z=z,
        x=elements,
        y=occs,
        colorscale=[
            [0.0, COLORS["primary"]],
            [0.5, "#f5f5f0"],
            [1.0, COLORS["negative"]],
        ],
        zmid=100,
        text=np.round(z, 0),
        texttemplate="%{text:.0f}%",
        hovertemplate="<b>%{y}</b><br>%{x}<br>AI at %{z:.0f}% of occ need<extra></extra>",
        showscale=True,
        colorbar=dict(title="AI as %<br>of occ need",
                      tickfont=dict(size=10)),
    ))
    chart_h = max(500, len(occs) * 24 + 250)
    chart_w = max(800, len(elements) * 45 + 250)
    style_figure(fig, title, subtitle=subtitle, x_title=None, y_title=None,
                 height=chart_h, width=chart_w, show_legend=False)
    fig.update_layout(
        margin=dict(l=20, r=40, t=80, b=100),
        xaxis=dict(tickangle=-45, tickfont=dict(size=8, family=FONT_FAMILY)),
        yaxis=dict(autorange="reversed", tickfont=dict(size=9, family=FONT_FAMILY)),
    )
    return fig


def _build_tips_and_tricks(
    occ_title: str,
    occ_elem_all: pd.DataFrame,
    pct: pd.Series,
    config_label: str,
) -> dict:
    """Build actionable tips for one occupation."""
    occ_data = occ_elem_all[occ_elem_all["title_current"] == occ_title].copy()
    if occ_data.empty:
        return {}

    # SKA elements: rank by ai_pct_occ (below 100% = human advantage; above = AI leads)
    human_elements = occ_data[occ_data["ai_pct_occ"] < 100].nsmallest(10, "ai_pct_occ")
    ai_elements = occ_data[occ_data["ai_pct_occ"] >= 100].nlargest(10, "ai_pct_occ")

    # Task-level data
    from backend.compute import get_occupation_tasks
    result = get_occupation_tasks(occ_title)

    task_rows = []
    if result and "tasks" in result:
        for t in result["tasks"]:
            auto_avg = t.get("avg_auto_aug")
            if auto_avg and auto_avg > 0:
                task_rows.append({
                    "task": t.get("task", ""),
                    "auto_avg": auto_avg,
                    "pct_avg": t.get("avg_pct_norm", 0),
                })
    task_df = pd.DataFrame(task_rows)
    if not task_df.empty:
        task_df = task_df.sort_values("auto_avg", ascending=False)

    pct_val = pct.get(occ_title, 0)

    return {
        "title_current": occ_title,
        "pct_tasks_affected": pct_val,
        "config": config_label,
        "human_advantage_elements": human_elements,
        "ai_advantage_elements": ai_elements,
        "tasks": task_df,
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    fig_dir = results / "figures"
    print("Worker Resilience -- generating outputs...\n")

    # ── Load SKA data ─────────────────────────────────────────────────────────
    print("Loading SKA base data...")
    ska_data = load_ska_data()

    # ── Primary config ────────────────────────────────────────────────────────
    print(f"Computing pct for primary config ({PRIMARY_KEY})...")
    pct_primary = get_pct_tasks_affected(ANALYSIS_CONFIGS[PRIMARY_KEY])

    print("Computing SKA gaps (primary config)...")
    result_primary: SKAResult = compute_ska(pct_primary, ska_data)

    # ── Ceiling config (comparison) ──────────────────────────────────────────
    print(f"Computing pct for ceiling config ({CEILING_KEY})...")
    pct_ceiling = get_pct_tasks_affected(ANALYSIS_CONFIGS[CEILING_KEY])
    print("Computing SKA gaps (ceiling config)...")
    result_ceiling: SKAResult = compute_ska(pct_ceiling, ska_data)

    # ── Per-element summary ──────────────────────────────────────────────────
    # Primary metric: ai_pct_eco_mean = ai_capability / mean(occ_score) × 100
    #   — reads as "AI has reached X% of the typical occupation's requirement"
    # Also kept: mean_gap (raw imp×level units) for backward compat & raw inspection
    ai_cap_df = result_primary.ai_capability.rename(
        columns={"ai_score": "ai_capability"}
    )
    eco_mean_df = result_primary.eco_baseline.rename(
        columns={"eco_score": "eco_mean_occ_score"}
    )
    eco_p95_df = result_primary.eco_baseline_p95.rename(
        columns={"eco_score_p95": "eco_p95_occ_score"}
    )

    all_elem_rows = []
    for type_name, elem_df in result_primary.occ_element_scores.items():
        agg = (
            elem_df.groupby("element_name")["gap"]
            .agg(["mean", "median", "std", "count"])
            .reset_index()
            .rename(columns={"mean": "mean_gap", "median": "median_gap",
                              "std": "std_gap", "count": "n_occs"})
        )
        agg["type"] = type_name
        all_elem_rows.append(agg)
    element_summary = pd.concat(all_elem_rows, ignore_index=True)

    # Merge in ai_capability + eco baselines
    element_summary = element_summary.merge(
        ai_cap_df[["element_name", "ai_capability", "type"]],
        on=["element_name", "type"], how="left",
    )
    element_summary = element_summary.merge(
        eco_mean_df[["element_name", "eco_mean_occ_score", "type"]],
        on=["element_name", "type"], how="left",
    )
    element_summary = element_summary.merge(
        eco_p95_df[["element_name", "eco_p95_occ_score", "type"]],
        on=["element_name", "type"], how="left",
    )
    # Percentage framings
    element_summary["ai_pct_eco_mean"] = (
        element_summary["ai_capability"] / element_summary["eco_mean_occ_score"] * 100.0
    )
    element_summary["ai_pct_eco_p95"] = (
        element_summary["ai_capability"] / element_summary["eco_p95_occ_score"] * 100.0
    )
    element_summary = element_summary.sort_values("ai_pct_eco_mean")

    save_csv(element_summary, results / "element_gaps_summary.csv")
    print(f"Saved element_gaps_summary.csv ({len(element_summary)} elements)")

    # Ceiling comparison element summary (ai_pct_eco_mean under ceiling config)
    ceiling_ai_cap = result_ceiling.ai_capability.rename(
        columns={"ai_score": "ceiling_ai_capability"}
    )
    ceiling_eco_mean = result_ceiling.eco_baseline.rename(
        columns={"eco_score": "ceiling_eco_mean"}
    )
    ceiling_merged = ceiling_ai_cap.merge(ceiling_eco_mean, on=["element_name", "type"])
    ceiling_merged["ceiling_ai_pct_eco_mean"] = (
        ceiling_merged["ceiling_ai_capability"]
        / ceiling_merged["ceiling_eco_mean"] * 100.0
    )
    element_summary = element_summary.merge(
        ceiling_merged[["element_name", "type", "ceiling_ai_pct_eco_mean"]],
        on=["element_name", "type"], how="left",
    )
    element_summary["pct_delta_ceiling"] = (
        element_summary["ceiling_ai_pct_eco_mean"] - element_summary["ai_pct_eco_mean"]
    )

    # Human advantage (AI below 100% of occ need)
    human_advantage = element_summary[element_summary["ai_pct_eco_mean"] < 100].nsmallest(
        TOP_N_ELEMENTS, "ai_pct_eco_mean"
    )
    save_csv(human_advantage, results / "human_advantage_elements.csv")

    # AI advantage (AI at or above 100% of occ need)
    ai_advantage = element_summary[element_summary["ai_pct_eco_mean"] >= 100].nlargest(
        TOP_N_ELEMENTS, "ai_pct_eco_mean"
    )
    save_csv(ai_advantage, results / "ai_advantage_elements.csv")

    # ── Per-occ element detail ────────────────────────────────────────────────
    occ_elem_all = pd.concat([
        df.assign(type=t)
        for t, df in result_primary.occ_element_scores.items()
    ], ignore_index=True)
    # Per-(occ, element) AI-as-% framing. Guards against zero occ_score.
    occ_elem_all["ai_pct_occ"] = np.where(
        occ_elem_all["occ_score"] > 0,
        occ_elem_all["ai_score"] / occ_elem_all["occ_score"] * 100.0,
        np.nan,
    )
    save_csv(occ_elem_all, results / "occ_element_gaps.csv")
    print("Saved occ_element_gaps.csv")

    occ_gaps = result_primary.occ_gaps.copy()
    save_csv(occ_gaps, results / "occ_gaps_summary.csv")
    print("Saved occ_gaps_summary.csv")

    # ── Trend analysis ───────────────────────────────────────────────────────
    # Tracks delta in overall_pct (percentage framing) per occupation across
    # the first→last date of each config series.
    print("\nComputing SKA pct trends...")
    trend_rows = []
    for config_key, series in ANALYSIS_CONFIG_SERIES.items():
        if len(series) < 2:
            continue
        pct_first = get_pct_tasks_affected(series[0])
        pct_last = get_pct_tasks_affected(series[-1])
        result_first = compute_ska(pct_first, ska_data)
        result_last = compute_ska(pct_last, ska_data)
        pct_first_s = result_first.occ_gaps.set_index("title_current")["overall_pct"]
        pct_last_s = result_last.occ_gaps.set_index("title_current")["overall_pct"]
        delta = (pct_last_s - pct_first_s)
        for occ, d in delta.items():
            trend_rows.append({
                "title_current": occ,
                "config": config_key,
                "pct_first": pct_first_s.get(occ, np.nan),
                "pct_last": pct_last_s.get(occ, np.nan),
                "pct_delta": d,
            })
        print(f"  {config_key}: median pct delta = {delta.median():.2f}pp")
    if trend_rows:
        trend_df = pd.DataFrame(trend_rows)
        save_csv(trend_df, results / "ska_gap_trends.csv")
        print("Saved ska_gap_trends.csv")

    # ── Occs of interest ─────────────────────────────────────────────────────
    available_occs = set(occ_gaps["title_current"].tolist())
    matched_occs = []
    for name in OCCS_OF_INTEREST:
        match = _find_occ(name, available_occs)
        if match:
            matched_occs.append(match)
        else:
            print(f"  WARNING: '{name}' not matched in SKA results")

    occ_interest_gaps = occ_gaps[occ_gaps["title_current"].isin(matched_occs)].copy()
    occ_interest_elem = occ_elem_all[occ_elem_all["title_current"].isin(matched_occs)]

    # Top 5 human/AI elements per occ of interest (ranked by ai_pct_occ)
    interest_rows = []
    for occ in matched_occs:
        occ_data = occ_interest_elem[occ_interest_elem["title_current"] == occ]
        top_human = occ_data.nsmallest(5, "ai_pct_occ")[["element_name", "type", "occ_score",
                                                    "ai_score", "gap", "ai_pct_occ"]].assign(
            direction="human_advantage", rank=range(1, 6))
        top_ai = occ_data.nlargest(5, "ai_pct_occ")[["element_name", "type", "occ_score",
                                               "ai_score", "gap", "ai_pct_occ"]].assign(
            direction="ai_advantage", rank=range(1, 6))
        for df_part in [top_human, top_ai]:
            df_part["title_current"] = occ
            interest_rows.append(df_part)
    if interest_rows:
        interest_detail = pd.concat(interest_rows, ignore_index=True)
        save_csv(interest_detail, results / "occs_of_interest_gaps.csv")
        print(f"Saved occs_of_interest_gaps.csv ({len(matched_occs)} occupations)")

    # ── Cross-config comparison ───────────────────────────────────────────────
    print("\nComputing cross-config SKA pct/gaps...")
    config_gap_rows = []
    for config_key, dataset_name in ANALYSIS_CONFIGS.items():
        pct_cfg = get_pct_tasks_affected(dataset_name)
        result_cfg = compute_ska(pct_cfg, ska_data)
        gaps_cfg = result_cfg.occ_gaps.copy()
        gaps_cfg["config"] = config_key
        config_gap_rows.append(gaps_cfg[
            ["title_current", "config", "overall_pct", "overall_gap",
             "skills_gap", "abilities_gap", "knowledge_gap",
             "skills_pct", "abilities_pct", "knowledge_pct"]
        ])
        print(f"  Done: {config_key}")
    config_gaps = pd.concat(config_gap_rows, ignore_index=True)
    save_csv(config_gaps, results / "occ_gaps_all_configs.csv")
    print("Saved occ_gaps_all_configs.csv")

    # ── Tips and Tricks section ──────────────────────────────────────────────
    print("\n== Tips and Tricks ==")
    tips_results = []
    for occ_name in TIPS_OCCS:
        matched = _find_occ(occ_name, available_occs)
        if not matched:
            print(f"  WARNING: '{occ_name}' not matched")
            continue
        print(f"  Building tips for: {matched}")
        tips = _build_tips_and_tricks(
            matched, occ_elem_all, pct_primary,
            ANALYSIS_CONFIG_LABELS[PRIMARY_KEY],
        )
        if tips:
            tips_results.append(tips)

            # Save per-occ CSV
            safe_name = matched.split(",")[0].replace(" ", "_").lower()

            # SKA elements
            ska_rows = []
            for _, row in tips["human_advantage_elements"].iterrows():
                ska_rows.append({
                    "element_name": row["element_name"],
                    "type": row["type"],
                    "ai_pct_occ": row["ai_pct_occ"],
                    "gap": row["gap"],
                    "occ_score": row["occ_score"],
                    "ai_score": row["ai_score"],
                    "recommendation": "Invest in yourself — human advantage",
                })
            for _, row in tips["ai_advantage_elements"].iterrows():
                ska_rows.append({
                    "element_name": row["element_name"],
                    "type": row["type"],
                    "ai_pct_occ": row["ai_pct_occ"],
                    "gap": row["gap"],
                    "occ_score": row["occ_score"],
                    "ai_score": row["ai_score"],
                    "recommendation": "Learn to leverage AI — AI advantage",
                })
            if ska_rows:
                save_csv(pd.DataFrame(ska_rows),
                         results / f"tips_{safe_name}_ska.csv")

            # Tasks
            if not tips["tasks"].empty:
                task_df = tips["tasks"].copy()
                task_df["recommendation"] = task_df["auto_avg"].apply(
                    lambda a: "Let AI handle this" if a >= 3.5
                    else "AI can assist" if a >= 2.0
                    else "Focus on doing this yourself"
                )
                save_csv(task_df, results / f"tips_{safe_name}_tasks.csv")

    print(f"  Saved tips data for {len(tips_results)} occupations")

    # ── Select occupations for heatmaps ──────────────────────────────────────
    # Mix: some from occs of interest + some that show the physical/info split
    # Physical-heavy: pick occs with lowest abilities_pct (largest human advantage on abilities)
    phys_occs = (
        occ_gaps.nsmallest(5, "abilities_pct")["title_current"].tolist()
    )
    # Info-heavy: pick occs with highest knowledge_pct (AI exceeds knowledge needs)
    info_occs = (
        occ_gaps.nlargest(5, "knowledge_pct")["title_current"].tolist()
    )
    # Combine with subset of interest occs, deduplicate
    heatmap_occs = list(dict.fromkeys(
        matched_occs[:8] + phys_occs + info_occs
    ))[:18]

    # ── Figures ───────────────────────────────────────────────────────────────
    print("\nGenerating figures...")

    # Per-domain bars (3 × 2 = 6 charts: human + AI for each domain)
    for domain in ["skills", "abilities", "knowledge"]:
        domain_label = domain.title()

        fig = _element_gap_bar(
            element_summary, direction="human_advantage",
            domain_filter=domain,
            title=f"Where Humans Lead — {domain_label}",
            subtitle=f"AI capability as % of typical occ need (<100% = human advantage) | {ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]}",
        )
        if fig.data:
            save_figure(fig, fig_dir / f"human_advantage_{domain}.png")
            print(f"  human_advantage_{domain}.png")

        fig = _element_gap_bar(
            element_summary, direction="ai_advantage",
            domain_filter=domain,
            title=f"Where AI Leads — {domain_label}",
            subtitle=f"AI capability as % of typical occ need (>100% = AI leads) | {ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]}",
        )
        if fig.data:
            save_figure(fig, fig_dir / f"ai_advantage_{domain}.png")
            print(f"  ai_advantage_{domain}.png")

    # Combined bars (all domains) — still useful as overview
    fig = _element_gap_bar(
        element_summary, direction="human_advantage",
        title="Where Humans Still Have the Biggest Advantage Over AI",
        subtitle=f"AI capability as % of typical occ need (<100% = human advantage) | {ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]}",
    )
    save_figure(fig, fig_dir / "human_advantage_bar.png")
    print("  human_advantage_bar.png")

    fig = _element_gap_bar(
        element_summary, direction="ai_advantage",
        title="Where AI Already Exceeds the Typical Occupation's Need",
        subtitle=f"AI capability as % of typical occ need (>100% = AI leads) | {ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]}",
    )
    save_figure(fig, fig_dir / "ai_advantage_bar.png")
    print("  ai_advantage_bar.png")

    # Per-domain heatmaps — pick elements with the largest |100 − ai_pct_eco_mean|
    for domain in ["skills", "abilities", "knowledge"]:
        domain_label = domain.title()
        domain_elements = (
            element_summary[element_summary["type"] == domain]
            .assign(dist_from_neutral=lambda d: (d["ai_pct_eco_mean"] - 100).abs())
            .nlargest(15, "dist_from_neutral")["element_name"]
            .tolist()
        )
        domain_occ_elem = occ_elem_all[occ_elem_all["type"] == domain]

        if domain_elements and heatmap_occs:
            fig = _occ_heatmap(
                domain_occ_elem, occs=heatmap_occs, elements=domain_elements,
                title=f"{domain_label} — AI capability as % of occ need",
                subtitle=f"Blue <100% (human advantage) | Red >100% (AI leads) | {ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]}",
            )
            save_figure(fig, fig_dir / f"heatmap_{domain}.png")
            print(f"  heatmap_{domain}.png")

    # Combined heatmap for occs of interest (still useful)
    if matched_occs:
        top_elements = (
            element_summary.assign(
                dist_from_neutral=lambda d: (d["ai_pct_eco_mean"] - 100).abs()
            )
            .nlargest(25, "dist_from_neutral")["element_name"]
            .tolist()
        )
        fig = _occ_heatmap(
            occ_elem_all, occs=matched_occs[:20], elements=top_elements,
            title="SKA Heatmap — Occupations of Interest (AI as % of occ need)",
            subtitle=f"Blue <100% (human advantage) | Red >100% (AI leads) | {ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]}",
        )
        save_figure(fig, fig_dir / "occ_heatmap.png")
        print("  occ_heatmap.png")

    # ── Copy key figures ──────────────────────────────────────────────────────
    committed = HERE / "figures"
    committed.mkdir(exist_ok=True)
    key_figs = [
        "human_advantage_bar.png", "ai_advantage_bar.png", "occ_heatmap.png",
        "human_advantage_skills.png", "ai_advantage_skills.png",
        "human_advantage_abilities.png", "ai_advantage_abilities.png",
        "human_advantage_knowledge.png", "ai_advantage_knowledge.png",
        "heatmap_skills.png", "heatmap_abilities.png", "heatmap_knowledge.png",
    ]
    for fname in key_figs:
        src = fig_dir / fname
        if src.exists():
            shutil.copy2(src, committed / fname)

    # ── PDF ───────────────────────────────────────────────────────────────────
    from analysis.utils import generate_pdf
    md_path = HERE / "worker_resilience_report.md"
    if md_path.exists():
        generate_pdf(md_path, results / "worker_resilience_report.pdf")

    print("\nDone.")


if __name__ == "__main__":
    main()
