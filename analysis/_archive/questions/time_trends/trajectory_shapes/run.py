"""
run.py — Time Trends: Trajectory Shapes

Classifies all 923 occupations by HOW they grew over the all_confirmed time series,
not just how much. Five trajectory types are derived from growth timing, monotonicity,
and the relationship between early-period and late-period gains.

Trajectory types:
  early_mover  — High exposure from the start, < 15pp of additional gain (already arrived)
  late_mover   — Low-ish start, major jump concentrated in 2025–2026
  steady       — Consistent upward slope throughout, gain spread evenly
  plateaued    — Strong early growth then stalled in the back half
  laggard      — Minimal growth across the full window (< 5pp total)
  mixed        — Doesn't cleanly fit any category (non-monotonic, etc.)

Figures:
  trajectory_type_by_sector.png  — Stacked bar: trajectory mix per major sector
  trajectory_scatter.png         — Scatter: total gain vs first level, colored by type
  trajectory_example_lines.png   — Line chart: example occupations per type

Run from project root:
    venv/Scripts/python -m analysis.questions.time_trends.trajectory_shapes.run
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
    CATEGORY_PALETTE,
    COLORS,
    FONT_FAMILY,
    generate_pdf,
    save_csv,
    save_figure,
    style_figure,
)

HERE = Path(__file__).resolve().parent
PRIMARY_KEY = "all_confirmed"

# Trajectory color map
TRAJ_COLORS: dict[str, str] = {
    "early_mover":  "#1f77b4",
    "late_mover":   "#ff7f0e",
    "steady":       "#2ca02c",
    "plateaued":    "#9467bd",
    "laggard":      "#d62728",
    "mixed":        "#8c8c8c",
}

TRAJ_ORDER = ["early_mover", "late_mover", "steady", "plateaued", "laggard", "mixed"]


def load_series(series_datasets: list[str]) -> pd.DataFrame:
    """Load pct_tasks_affected for each dataset date; return wide DataFrame (occ × date)."""
    frames: dict[str, pd.Series] = {}
    for ds_name in series_datasets:
        date_str = ds_name.rsplit(" ", 1)[-1]
        print(f"  loading {ds_name}...")
        pct = get_pct_tasks_affected(ds_name)
        frames[date_str] = pct
    df = pd.DataFrame(frames)
    df.index.name = "title_current"
    df = df.reset_index()
    return df


def get_major_category(title: str, occ_df: pd.DataFrame) -> str:
    row = occ_df[occ_df["title_current"] == title]
    if row.empty:
        return "Unknown"
    return row.iloc[0].get("major_occ_category", "Unknown")


def classify_trajectory(vals: np.ndarray) -> str:
    """
    Classify a single occupation's growth trajectory given an array of pct values
    ordered chronologically. NaN values are forward-filled from the previous date;
    leading NaN are set to 0.
    """
    # Fill NaN: leading zeros, then forward-fill
    series = pd.Series(vals, dtype=float)
    series = series.ffill()
    series = series.fillna(0.0)
    v = series.values

    n = len(v)
    if n < 2:
        return "mixed"

    first = v[0]
    last = v[-1]
    total_gain = last - first
    mid_idx = n // 2
    early_gain = v[mid_idx] - v[0]
    late_gain = v[-1] - v[mid_idx]

    # Monotonicity: fraction of consecutive steps that are non-negative
    diffs = np.diff(v)
    mono_frac = np.sum(diffs >= -0.5) / len(diffs)  # small tolerance for float noise

    # Early mover: already high at start (>= 40%), minimal additional gain
    # Check before laggard so high-exposure stable occupations land here
    if first >= 40.0 and abs(total_gain) < 15.0:
        return "early_mover"

    # Laggard: very little total movement
    if abs(total_gain) < 5.0:
        return "laggard"

    # Plateaued: strong early growth but stalled in back half
    if early_gain >= 8.0 and late_gain < 3.0 and total_gain >= 8.0:
        return "plateaued"

    # Late mover: < 28pp at midpoint but gained ≥ 10pp in back half
    if v[mid_idx] < 28.0 and late_gain >= 10.0:
        return "late_mover"

    # Steady: reasonably monotonic with gain spread across both halves
    if mono_frac >= 0.6 and early_gain >= 3.0 and late_gain >= 3.0 and total_gain >= 8.0:
        return "steady"

    # Everything else
    return "mixed"


def pick_examples(traj_df: pd.DataFrame, traj_type: str, n: int = 3) -> list[str]:
    """Pick representative occupations for a trajectory type by mid-employment if possible."""
    sub = traj_df[traj_df["trajectory"] == traj_type].copy()
    if sub.empty:
        return []
    # Prefer occupations with clear trajectories (pick from middle of total_gain distribution)
    sub = sub.sort_values("total_gain")
    picks = sub.iloc[len(sub) // 4: 3 * len(sub) // 4]
    if len(picks) > n:
        picks = picks.sample(n, random_state=42)
    return picks["title_current"].tolist()


def main() -> None:
    results = ensure_results_dir(HERE)
    figs_dir = HERE / "figures"
    figs_dir.mkdir(exist_ok=True)

    # ── 1. Load time series ───────────────────────────────────────────────────
    print("trajectory_shapes: loading all_confirmed series...")
    series = ANALYSIS_CONFIG_SERIES[PRIMARY_KEY]
    dates = [ds.rsplit(" ", 1)[-1] for ds in series]
    wide = load_series(series)

    # ── 2. Classify trajectories ──────────────────────────────────────────────
    print("\ntrajectory_shapes: classifying trajectories...")
    date_cols = [c for c in wide.columns if c != "title_current"]
    records: list[dict] = []
    for _, row in wide.iterrows():
        vals = row[date_cols].values.astype(float)
        traj = classify_trajectory(vals)
        series_filled = pd.Series(vals, dtype=float).ffill().fillna(0.0).values
        first_val = series_filled[0]
        last_val = series_filled[-1]
        mid_idx = len(series_filled) // 2
        early_gain = series_filled[mid_idx] - series_filled[0]
        late_gain = series_filled[-1] - series_filled[mid_idx]
        records.append({
            "title_current": row["title_current"],
            "trajectory": traj,
            "first_pct": round(first_val, 2),
            "last_pct": round(last_val, 2),
            "total_gain": round(last_val - first_val, 2),
            "early_gain": round(early_gain, 2),
            "late_gain": round(late_gain, 2),
        })

    traj_df = pd.DataFrame(records)

    # ── 3. Attach major category ──────────────────────────────────────────────
    print("trajectory_shapes: attaching major categories...")
    from backend.compute import load_eco_raw
    eco = load_eco_raw()
    occ_major = eco[["title_current", "major_occ_category"]].drop_duplicates("title_current")
    traj_df = traj_df.merge(occ_major, on="title_current", how="left")
    traj_df["major_occ_category"] = traj_df["major_occ_category"].fillna("Unknown")

    save_csv(traj_df, results / "trajectory_classifications.csv")
    print(f"  {len(traj_df)} occupations classified")

    # ── 4. Summary counts ─────────────────────────────────────────────────────
    summary = (
        traj_df.groupby("trajectory")
        .agg(n_occs=("title_current", "count"),
             avg_first_pct=("first_pct", "mean"),
             avg_last_pct=("last_pct", "mean"),
             avg_total_gain=("total_gain", "mean"))
        .reset_index()
        .sort_values("n_occs", ascending=False)
    )
    save_csv(summary, results / "trajectory_summary.csv")
    print("\n  Trajectory counts:")
    for _, r in summary.iterrows():
        print(f"    {r['trajectory']:15s}: {r['n_occs']:3d} occs | "
              f"avg {r['avg_first_pct']:.1f}% to {r['avg_last_pct']:.1f}% "
              f"(+{r['avg_total_gain']:.1f}pp gain)")

    # ── 5. Sector × trajectory matrix ────────────────────────────────────────
    sector_traj = (
        traj_df.groupby(["major_occ_category", "trajectory"])
        .size()
        .reset_index(name="n_occs")
    )
    save_csv(sector_traj, results / "sector_trajectory_matrix.csv")

    # ── 6. Figures ────────────────────────────────────────────────────────────

    # 6a. Stacked bar: trajectory mix by sector
    print("\ntrajectory_shapes: building figures...")
    pivot = sector_traj.pivot_table(
        index="major_occ_category", columns="trajectory", values="n_occs", fill_value=0
    )
    # Sort sectors by total occupations
    pivot["_total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("_total", ascending=True).drop(columns="_total")
    # Normalize to percentages
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    fig_sector = go.Figure()
    for ttype in TRAJ_ORDER:
        if ttype not in pivot_pct.columns:
            continue
        fig_sector.add_trace(go.Bar(
            name=ttype.replace("_", " ").title(),
            x=pivot_pct[ttype],
            y=pivot_pct.index,
            orientation="h",
            marker_color=TRAJ_COLORS[ttype],
        ))
    style_figure(fig_sector,
                 "Trajectory Type Mix by Major Occupation Sector",
                 subtitle="All Confirmed series (Sep 2024 → Feb 2026) | Each bar = % of occupations in that sector",
                 x_title="Share of sector occupations (%)",
                 show_legend=True,
                 height=820, width=1100)
    fig_sector.update_layout(barmode="stack", margin=dict(l=20, r=20))
    save_figure(fig_sector, results / "figures" / "trajectory_type_by_sector.png")
    shutil.copy(results / "figures" / "trajectory_type_by_sector.png",
                figs_dir / "trajectory_type_by_sector.png")
    print("  trajectory_type_by_sector.png")

    # 6b. Scatter: total gain vs first level
    fig_scatter = go.Figure()
    for ttype in TRAJ_ORDER:
        sub = traj_df[traj_df["trajectory"] == ttype]
        if sub.empty:
            continue
        fig_scatter.add_trace(go.Scatter(
            x=sub["first_pct"],
            y=sub["total_gain"],
            mode="markers",
            name=ttype.replace("_", " ").title(),
            marker=dict(color=TRAJ_COLORS[ttype], size=5, opacity=0.7),
        ))
    style_figure(fig_scatter,
                 "Trajectory Shape: Starting Level vs. Total Growth",
                 subtitle="All Confirmed series | Each dot = one occupation",
                 x_title="% Tasks Affected at Start (Sep 2024)",
                 y_title="Total Gain (pp, Sep 2024 → Feb 2026)",
                 show_legend=True,
                 height=600, width=900)
    fig_scatter.update_layout(margin=dict(l=60, r=20))
    save_figure(fig_scatter, results / "figures" / "trajectory_scatter.png")
    shutil.copy(results / "figures" / "trajectory_scatter.png",
                figs_dir / "trajectory_scatter.png")
    print("  trajectory_scatter.png")

    # 6c. Example lines per trajectory type
    # Build the long-form time series for examples
    example_occs: list[str] = []
    for ttype in TRAJ_ORDER:
        example_occs.extend(pick_examples(traj_df, ttype, n=2))

    if example_occs:
        long_rows: list[dict] = []
        for _, row in wide[wide["title_current"].isin(example_occs)].iterrows():
            vals_raw = pd.Series(row[date_cols].values.astype(float))
            vals_filled = vals_raw.ffill().fillna(0.0).values
            ttype = traj_df.loc[traj_df["title_current"] == row["title_current"], "trajectory"]
            ttype_str = ttype.values[0] if len(ttype) > 0 else "mixed"
            for i, d in enumerate(dates):
                long_rows.append({
                    "title_current": row["title_current"],
                    "trajectory": ttype_str,
                    "date": d,
                    "pct_tasks_affected": vals_filled[i],
                })
        long_df = pd.DataFrame(long_rows)

        fig_lines = go.Figure()
        for occ in example_occs:
            sub = long_df[long_df["title_current"] == occ]
            if sub.empty:
                continue
            ttype = sub.iloc[0]["trajectory"]
            short_name = occ[:35] + "…" if len(occ) > 35 else occ
            fig_lines.add_trace(go.Scatter(
                x=sub["date"],
                y=sub["pct_tasks_affected"],
                mode="lines+markers",
                name=f"[{ttype.replace('_',' ')}] {short_name}",
                line=dict(color=TRAJ_COLORS.get(ttype, "#888"), width=2),
            ))
        style_figure(fig_lines,
                     "Example Occupation Trajectories — One Per Type",
                     subtitle="All Confirmed series | Selected examples from each trajectory category",
                     x_title="Dataset date",
                     y_title="% Tasks Affected",
                     show_legend=True,
                     height=550, width=1050)
        fig_lines.update_layout(margin=dict(l=60, r=20))
        save_figure(fig_lines, results / "figures" / "trajectory_example_lines.png")
        shutil.copy(results / "figures" / "trajectory_example_lines.png",
                    figs_dir / "trajectory_example_lines.png")
        print("  trajectory_example_lines.png")

    # ── 7. PDF ─────────────────────────────────────────────────────────────────
    report_path = HERE / "trajectory_shapes_report.md"
    if report_path.exists():
        from analysis.utils import generate_pdf
        generate_pdf(report_path, results / "trajectory_shapes_report.pdf")

    print("\ntrajectory_shapes: done.")


if __name__ == "__main__":
    main()
