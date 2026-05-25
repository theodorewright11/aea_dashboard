"""
Part 3 — Action: What To Do About It

Audience scaffolding will be reintroduced as more charts come in.

  1. Conv → Confirmed → Ceiling gap by major occ category
  2. Tech commodities composite (top-25)
  3. Risk score 5f — Occupations Most At Risk (SKA-gated focused set)
  4. U.S. states clustered on AI exposure (choropleth map)
  5. AI intensity vs. median-rank anchor (full eco_2025)

Run from project root:
    venv/Scripts/python -m analysis.paper.results.part_3.run
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
    ROOT,
    ensure_results_dir,
    get_pct_tasks_affected,
)
from analysis.utils import FONT_FAMILY, save_csv, save_figure
from analysis.paper.paper_config import (
    PAPER_W, PAPER_H,
    ANNOT_FS, LABEL_FS, TICK_FS, INSIDE_FS,
    METRIC_COLORS, METRIC_COLORS_LIGHT, PAPER_PALETTE,
    paper_fonts,
    style_paper_figure, fmt_wages, fmt_workers,
)
from plotly.subplots import make_subplots

HERE = Path(__file__).resolve().parent
ANALYSIS_DATA_DIR = ROOT / "analysis" / "data"
TECH_SKILLS_FILE = ANALYSIS_DATA_DIR / "technology_skills_v30.1.csv"

PRIMARY_KEY = "all_confirmed"
PRIMARY_DATASET = ANALYSIS_CONFIGS[PRIMARY_KEY]
PRIMARY_LABEL = ANALYSIS_CONFIG_LABELS[PRIMARY_KEY]

# Tasks blue + workers green blend, light → dark (used by tech_commodities)
BLEND_LIGHT = "#cdd9d4"
BLEND_DARK = "#2a4f56"
TASKS_LIGHT = "#cfe0ec"
TASKS_DARK = "#2c4f6b"


# ─────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────

def _copy_fig(results: Path, figures: Path, name: str) -> None:
    shutil.copy(results / "figures" / name, figures / name)


def _run_config(dataset_name: str, agg_level: str) -> pd.DataFrame:
    """Run get_group_data for one dataset and return a category dataframe."""
    from backend.compute import get_group_data
    config = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": "nat",
        "agg_level": agg_level,
        "sort_by": "% Tasks Affected",
        "top_n": 9999,
        "search_query": "",
        "context_size": 3,
    }
    data = get_group_data(config)
    assert data is not None, f"No data for {dataset_name} @ {agg_level}"
    df: pd.DataFrame = data["df"]
    return df.rename(columns={data["group_col"]: "category"})


# ─────────────────────────────────────────────────────────────────────────
# Figure 1: Tech commodities composite (reuse skills_landscape pipeline)
# ─────────────────────────────────────────────────────────────────────────

def _structural_for_tech() -> pd.DataFrame:
    """Per-occ structural data for tech-skills join."""
    from backend.compute import get_explorer_occupations
    rows = [
        {
            "title_current": o["title_current"],
            "emp": o.get("emp") or 0,
            "wage": o.get("wage") or 0,
            "major": o.get("major", ""),
        }
        for o in get_explorer_occupations()
    ]
    return pd.DataFrame(rows)


def build_tech_commodities(results: Path, figures: Path) -> None:
    """Top 25 software commodities selected by total employment usage
    (each (occ, tool) entry contributes the occ's emp once — same occ counts
    multiple times across its tools), then ranked by mean % tasks affected.

    No AI data enters the selection — only the ordering and bar length.
    Bar length = mean % tasks affected (all_confirmed). Color = workers using.
    """
    assert TECH_SKILLS_FILE.exists(), f"Tech skills file not found: {TECH_SKILLS_FILE}"
    pct = get_pct_tasks_affected(PRIMARY_DATASET)
    structural = _structural_for_tech()

    tech = pd.read_csv(TECH_SKILLS_FILE)
    tech.columns = [c.strip() for c in tech.columns]
    tech = tech.merge(
        structural.rename(columns={"title_current": "Title"}),
        on="Title", how="left",
    )
    pct_merge = pct.rename("pct").reset_index()
    pct_merge.columns = ["Title", "pct"]
    tech = tech.merge(pct_merge, on="Title", how="left")
    tech["pct"] = tech["pct"].fillna(0.0)
    tech["emp"] = tech["emp"].fillna(0.0)

    # Selection: top 25 commodities by Σ emp across entries (same occ
    # counts once per tool it lists under the commodity — by design).
    agg = (
        tech.groupby("Commodity Title")
        .agg(
            workers_using=("emp", "sum"),
            mean_pct_affected=("pct", "mean"),
            n_occs=("Title", "nunique"),
            n_entries=("Title", "size"),
        )
        .reset_index()
    )
    top = agg.sort_values("workers_using", ascending=False).head(25).copy()
    # Display order: by % tasks affected (the ranking dimension).
    top = top.sort_values("mean_pct_affected", ascending=False)
    save_csv(top, results / "tech_commodities_top25.csv", float_format="%.3f")

    plot = top.sort_values("mean_pct_affected", ascending=True)  # plotly bottom-up
    # Y-axis: strip the trailing "software" word from each commodity
    # name (all 25 end with it — the title and axis title carry context).
    plot["display_name"] = (
        plot["Commodity Title"].str.replace(r"\s+software$", "", regex=True)
    )

    # ── Layout / fonts: pull every size from paper_fonts(W) so print pt
    # stays on the standard ladder (no `-2` adjustments, no hardcoded px).
    W = PAPER_W
    px = paper_fonts(W)

    wk_vals = plot["workers_using"].to_numpy(dtype=float)
    wk_min, wk_max = float(wk_vals.min()), float(wk_vals.max())

    # Color scale anchored on the workers METRIC_COLORS gold. Light-to-dark
    # so the eye reads color as "more workers using this commodity".
    WORKERS_LIGHT = "#f1e6cc"
    WORKERS_DARK = METRIC_COLORS["workers"]

    pct_max = float(plot["mean_pct_affected"].max())

    MARGIN_L, MARGIN_R = 20, 140

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=plot["mean_pct_affected"],
        y=plot["display_name"],
        orientation="h",
        marker=dict(
            color=wk_vals,
            colorscale=[[0, WORKERS_LIGHT], [1, WORKERS_DARK]],
            cmin=wk_min, cmax=wk_max,
            showscale=False,                # legend drawn manually below
            line=dict(width=0),
        ),
        text=[f"{p:.0f}%" for p in plot["mean_pct_affected"]],
        textposition="inside",
        insidetextanchor="end",
        textfont=dict(size=px["in_chart_floor"],
                      color=PAPER_PALETTE["text"], family=FONT_FAMILY),
        constraintext="none",
        cliponaxis=False,
        showlegend=False,
        hovertemplate="<b>%{y}</b><br>% tasks affected: %{x:.1f}%<extra></extra>",
    ))

    # Bottom legend: single centered annotation. Inline color swatches
    # interpolating WORKERS_LIGHT → WORKERS_DARK give a gradient-like
    # cue without needing separate shapes. We use 7 swatches for a
    # smoother light-to-dark transition.
    def _hex_to_rgb(h: str) -> tuple[int, int, int]:
        return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))
    rgb_l = _hex_to_rgb(WORKERS_LIGHT)
    rgb_d = _hex_to_rgb(WORKERS_DARK)
    N_SWATCH = 7
    swatch_html = ""
    for i in range(N_SWATCH):
        t = i / (N_SWATCH - 1)
        c = tuple(int(rgb_l[k] + (rgb_d[k] - rgb_l[k]) * t) for k in range(3))
        swatch_html += f"<span style='color:rgb({c[0]},{c[1]},{c[2]})'>■</span>"
    legend_text = (
        f"Workers Using&nbsp;&nbsp;{fmt_workers(wk_min)}&nbsp;"
        f"{swatch_html}&nbsp;{fmt_workers(wk_max)}"
    )
    # Note: xref="paper" x=0.5 centers on the *rendered* plot area, but
    # Plotly auto-expands the left margin to fit long y-tick labels, so
    # the rendered plot area is shifted right of the PNG center. The
    # tuned x value below lands the legend centered on the PNG.
    fig.add_annotation(
        x=0.14, y=-0.17,
        xref="paper", yref="paper",
        text=legend_text, showarrow=False,
        xanchor="center", yanchor="middle",
        font=dict(size=px["in_chart_floor"],
                  color=PAPER_PALETTE["text"], family=FONT_FAMILY),
    )

    # Right-side annotation per bar: just "N occs" (workers is encoded
    # in bar color and read off the bottom legend).
    label_x = pct_max * 1.04
    for i, occ in enumerate(plot["n_occs"]):
        fig.add_annotation(
            x=label_x, y=i,
            xref="x", yref="y",
            text=f"{int(occ)} occs",
            showarrow=False,
            xanchor="left", yanchor="middle",
            font=dict(size=px["in_chart_floor"],
                      color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        )

    # Force every text element to honor the 8 pt floor — no auto-shrink.
    fig.update_layout(
        uniformtext=dict(minsize=px["in_chart_floor"], mode="show"),
        bargap=0.22,
    )

    style_paper_figure(
        fig,
        "AI Exposure of the 25 Most-Used Software Commodities",
        height=1280, width=W,
        margin=dict(l=MARGIN_L, r=MARGIN_R, t=110, b=190),
    )
    x_top = pct_max * 1.15
    fig.update_xaxes(
        title=dict(text="Software Use Exposed",
                   font=dict(size=px["axis_title"], family=FONT_FAMILY)),
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        showticklabels=True, ticksuffix="%",
        range=[0, x_top],
        tickfont=dict(size=px["tick"], family=FONT_FAMILY),
    )
    # Force every commodity name to render — Plotly auto-thins category
    # ticks when there are many rows; dtick=1 keeps all 25.
    fig.update_yaxes(
        title=dict(text="O*NET Software Commodity",
                   font=dict(size=px["axis_title"], family=FONT_FAMILY)),
        showgrid=False, showline=False,
        tickmode="linear", tick0=0, dtick=1,
        tickfont=dict(size=px["tick"], family=FONT_FAMILY),
    )

    save_figure(fig, results / "figures" / "tech_commodities.png", scale=2)
    _copy_fig(results, figures, "tech_commodities.png")
    print("  -> tech_commodities.png")


# ─────────────────────────────────────────────────────────────────────────
# Figure 2: Agentic Confirmed → Agentic Ceiling MCP extension
# (top 10 major occ + top 10 GWA, % tasks | workers | wages)
# ─────────────────────────────────────────────────────────────────────────

# Local copy of the part_2 GWA loader — keeps part_3 independent of cross-part
# import paths. agentic_confirmed (eco_2025 rebase) and agentic_ceiling are
# both is_aei=False, so both come back as "mcp_group" with matching baselines.
def _get_wa_data(dataset_name: str, level: str = "gwa") -> pd.DataFrame:
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


def _axis_max_and_ticks(max_val: float) -> tuple[float, list[float]]:
    """Tight axis range + clean tick values. Mirrors the part_2 helper."""
    import math
    if max_val <= 0:
        return 1.0, [0.0]
    range_max = max_val * 1.05
    raw_step = range_max / 3.0
    magnitude = 10 ** math.floor(math.log10(raw_step))
    norm = raw_step / magnitude
    if norm < 1.5:
        step = 1.0 * magnitude
    elif norm < 2.25:
        step = 2.0 * magnitude
    elif norm < 3.0:
        step = 2.5 * magnitude
    elif norm < 7.0:
        step = 5.0 * magnitude
    else:
        step = 10.0 * magnitude
    n_max = int(range_max / step)
    ticks = [float(step * i) for i in range(n_max + 1)]
    return float(range_max), ticks


def _strip_zero_decimal(s: str) -> str:
    for unit in ("M", "B", "K", "T"):
        s = s.replace(f".0{unit}", unit)
    return s


def _balanced_wrap(label: str, max_chars: int = 22) -> str:
    if len(label) <= max_chars:
        return label
    candidates: list[tuple[int, int, str, str]] = []
    for i in range(1, len(label)):
        if label[i - 1] in (",", " "):
            line1 = label[:i].rstrip(", ").rstrip()
            line2 = label[i:].lstrip()
            if not line1 or not line2:
                continue
            if label[i - 1] == ",":
                line1 = line1 + ","
            candidates.append((max(len(line1), len(line2)), i, line1, line2))
    if not candidates:
        return label
    candidates.sort(key=lambda t: (t[0], t[1]))
    _, _, line1, line2 = candidates[0]
    return f"{line1}<br>{line2}"


def _wrap_major_label(label: str, max_chars: int = 22) -> str:
    return _balanced_wrap(label.replace(" Occupations", ""), max_chars)


def _wrap_gwa_label(label: str, max_chars: int = 32) -> str:
    return _balanced_wrap(label, max_chars)


def _agentic_ceiling_top10(level: str) -> pd.DataFrame:
    """Load agentic_confirmed + agentic_ceiling at the requested level
    (major or gwa), merge on category, return the top 10 sorted by
    agentic_confirmed % tasks descending. Each row carries pct_conf,
    pct_ceil, and pct_gap = pct_ceil − pct_conf so callers can re-rank
    by gap for the second panel.

    Both configs are is_aei=False on the eco_2025 baseline, so subtraction
    is clean (no mixed task universe / WA mapping)."""
    if level == "major":
        conf = _run_config(ANALYSIS_CONFIGS["agentic_confirmed"], "major")
        ceil = _run_config(ANALYSIS_CONFIGS["agentic_ceiling"], "major")
    else:
        conf = _get_wa_data(ANALYSIS_CONFIGS["agentic_confirmed"], level)
        ceil = _get_wa_data(ANALYSIS_CONFIGS["agentic_ceiling"], level)

    keep = ["category", "pct_tasks_affected"]
    df = (
        conf[keep].rename(columns={"pct_tasks_affected": "pct_conf"})
        .merge(
            ceil[keep].rename(columns={"pct_tasks_affected": "pct_ceil"}),
            on="category", how="inner",
        )
    )
    df["pct_gap"] = (df["pct_ceil"] - df["pct_conf"]).clip(lower=0)
    top10 = df.sort_values("pct_conf", ascending=False).head(10).reset_index(drop=True)
    return top10


def _build_agentic_ceiling_panels(
    top10: pd.DataFrame,
    title: str,
    y_axis_title: str,
    wrap_fn,
    out_name: str,
    results: Path,
    figures: Path,
    *,
    row_height: int = 110,
    hspacing: float = 0.30,
) -> None:
    """Two-panel horizontal bar chart, both panels showing % tasks
    exposed for the same 10 categories but ranked differently:

      Panel 1: agentic_confirmed % tasks, sorted by this value desc
               ("where agentic AI is most prominently used today")
      Panel 2: ceiling gap (= agentic_ceiling − agentic_confirmed),
               same 10 categories, re-sorted by gap desc
               ("where the biggest untapped agentic tooling lives")

    Each panel uses its own y-axis ordering — `shared_yaxes=False` —
    because the rank differs between panels. The y-labels appear on
    both panels' left edges so readers can match categories by name.
    """
    # Panel 1: sorted by pct_conf desc; reverse for plotly bottom-up.
    df1 = top10.iloc[::-1].reset_index(drop=True)
    cats1_r = [wrap_fn(c) for c in df1["category"].tolist()]
    vals1   = df1["pct_conf"].tolist()

    # Panel 2: same 10 cats, re-sorted by gap desc; reverse for plotly.
    df2 = top10.sort_values("pct_gap", ascending=False).reset_index(drop=True)
    df2 = df2.iloc[::-1].reset_index(drop=True)
    cats2_r = [wrap_fn(c) for c in df2["category"].tolist()]
    vals2   = df2["pct_gap"].tolist()

    n_cats = len(cats1_r)

    CANVAS_W = 2000
    px = paper_fonts(CANVAS_W)
    TITLE_FS_  = px["title"]
    PANEL_FS_  = px["panel_title"]
    AXIS_FS_   = px["axis_title"]
    TICK_FS_   = px["tick"]
    BAR_FS_    = px["in_chart_floor"]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[
            "Agentic Usage",
            "Unused Agentic Tooling",
        ],
        horizontal_spacing=hspacing,   # GWA-level labels are longer phrases
                                        # than major-cat labels and need
                                        # more horizontal_spacing before
                                        # panel-2 y-labels stop overlapping
                                        # back into panel 1's plot area.
        shared_yaxes=False,         # each panel has its own ordering
    )

    inside_font  = dict(size=BAR_FS_, color="white",                    family=FONT_FAMILY)
    outside_font = dict(size=BAR_FS_, color=PAPER_PALETTE["text"],     family=FONT_FAMILY)

    panels = [
        {
            "col": 1,
            "cats": cats1_r,
            "vals": vals1,
            "color": METRIC_COLORS["tasks"],
            "axis_title": "Tasks Exposed",
            "hover_name": "Agentic Confirmed",
        },
        {
            "col": 2,
            "cats": cats2_r,
            "vals": vals2,
            "color": METRIC_COLORS_LIGHT["tasks"],
            "axis_title": "Tasks (Ceiling − Confirmed)",
            "hover_name": "Ceiling Gap",
        },
    ]

    for p in panels:
        vals = p["vals"]
        vmax = max(vals) if vals else 1.0
        # Inside (white) when bar wide enough to legibly hold "XX.X%";
        # otherwise outside in dark text past the bar end. 0.30 catches
        # the GWA panel-2 short bars (~12–15% on a 47% panel max) and
        # places their labels outside cleanly.
        threshold = 0.30 * vmax
        positions = ["inside" if v >= threshold else "outside" for v in vals]
        labels    = [f"{v:.1f}%" for v in vals]

        fig.add_trace(go.Bar(
            y=p["cats"], x=vals, orientation="h",
            marker=dict(color=p["color"], line=dict(width=0)),
            text=labels,
            textposition=positions,
            insidetextanchor="end",
            insidetextfont=inside_font,
            outsidetextfont=outside_font,
            textangle=0,
            showlegend=False,
            cliponaxis=False, constraintext="none",
            hovertemplate=(
                "<b>%{y}</b><br>" + p["hover_name"] + ": %{x:.1f}%<extra></extra>"
            ),
        ), row=1, col=p["col"])

    bottom_margin = 150
    height = max(PAPER_H + 200, n_cats * row_height + 360)
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=TITLE_FS_, color=PAPER_PALETTE["text"], family=FONT_FAMILY),
            x=0.01, xanchor="left",
            y=0.99, yanchor="top",
        ),
        font=dict(family=FONT_FAMILY, color=PAPER_PALETTE["text"]),
        plot_bgcolor=PAPER_PALETTE["surface"],
        paper_bgcolor=PAPER_PALETTE["surface"],
        width=CANVAS_W,
        height=height,
        margin=dict(l=110, r=110, t=140, b=bottom_margin),
        bargap=0.22,
        showlegend=False,
    )
    fig.update_xaxes(
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        showline=True, linecolor=PAPER_PALETTE["grid"],
        zeroline=True, zerolinecolor=PAPER_PALETTE["grid"],
        tickfont=dict(size=TICK_FS_, family=FONT_FAMILY),
        tickangle=0,
        ticklabelstandoff=8,
    )
    fig.update_yaxes(
        showgrid=False, showline=False,
        tickfont=dict(size=TICK_FS_, family=FONT_FAMILY),
        automargin=True,
        ticklabelstandoff=2,
        ticks="",
        ticklen=0,
    )

    # Per-panel axis range with ~20% padding past the max so the outside
    # value labels at the longest bar's end print without clipping.
    for p in panels:
        vmax = max(p["vals"]) if p["vals"] else 0.0
        _rng, ticks = _axis_max_and_ticks(vmax)
        padded_max = vmax * 1.20 if vmax > 0 else _rng
        fig.update_xaxes(
            range=[0, padded_max], tickvals=ticks,
            ticktext=[f"{int(v)}%" for v in ticks],
            title=dict(text=p["axis_title"],
                       font=dict(size=AXIS_FS_, family=FONT_FAMILY)),
            row=1, col=p["col"],
        )
    fig.update_yaxes(
        title=dict(text=y_axis_title,
                   font=dict(size=AXIS_FS_, family=FONT_FAMILY), standoff=20),
        row=1, col=1,
    )

    # Subplot titles render via fig.layout.annotations — restyle to the
    # panel-title pt from the paper font ladder.
    for ann in fig.layout.annotations:
        ann.font = dict(size=PANEL_FS_, color=PAPER_PALETTE["text"], family=FONT_FAMILY)

    save_figure(fig, results / "figures" / out_name, scale=2)
    _copy_fig(results, figures, out_name)
    print(f"  -> {out_name}")


def build_agentic_ceiling_major(results: Path, figures: Path) -> None:
    """Two-panel chart for the top 10 major occ categories ranked by
    agentic_confirmed % tasks. Left panel: current agentic use. Right
    panel: the ceiling gap (untapped MCP tooling), same 10 categories
    re-sorted by gap desc."""
    top10 = _agentic_ceiling_top10("major")
    save_csv(top10, results / "agentic_ceiling_major.csv", float_format="%.3f")
    _build_agentic_ceiling_panels(
        top10,
        title="Agentic Confirmed vs. Agentic Ceiling Gap — Top 10 Major Occupational Categories",
        y_axis_title="Major Occupational Category",
        wrap_fn=_wrap_major_label,
        out_name="agentic_ceiling_major.png",
        results=results,
        figures=figures,
        row_height=110,
        hspacing=0.30,
    )


def build_agentic_ceiling_gwa(results: Path, figures: Path) -> None:
    """Top 10 GWAs ranked by agentic_confirmed % tasks exposed. Same
    two-panel structure as the major chart."""
    top10 = _agentic_ceiling_top10("gwa")
    save_csv(top10, results / "agentic_ceiling_gwa.csv", float_format="%.3f")
    _build_agentic_ceiling_panels(
        top10,
        title="Agentic Confirmed vs. Agentic Ceiling Gap — Top 10 General Work Activities",
        y_axis_title="O*NET General Work Activity",
        wrap_fn=_wrap_gwa_label,
        out_name="agentic_ceiling_gwa.png",
        results=results,
        figures=figures,
        row_height=110,
        hspacing=0.42,
    )


# ─────────────────────────────────────────────────────────────────────────
# Figure 3: AI intensity vs. median-rank anchor (chart 15 from
# exploratory/pct_norm_vs_eco v3) — major occ categories ranked by
# Σ pct (rated, bias-corrected) / Σ (freq × emp) over FULL eco_2025.
# Bars colored by pct_tasks_affected (darker = higher).
# Imports at function level so part_3 can still run if exploratory/ is
# absent (folder is gitignored).
# ─────────────────────────────────────────────────────────────────────────

def build_intensity_anchor_fulleco(results: Path, figures: Path) -> None:
    try:
        from analysis.exploratory.audit_pct_norm_eco.run import (
            BIAS_VARIANTS, compute_bias_ratios,
        )
        from analysis.exploratory.audit_pct_norm_eco.run_v3 import (
            compute_v3_intensity,
            compute_major_full_eco_denominator,
        )
    except ImportError as exc:
        print(f"  -> SKIPPED: exploratory/audit_pct_norm_eco not available ({exc})")
        return

    base = compute_v3_intensity(
        "all_confirmed", compute_bias_ratios(BIAS_VARIANTS["equal"])
    ).copy()
    full_den = compute_major_full_eco_denominator()
    base["den_full"] = base["category"].map(full_den).fillna(0.0)
    base["ratio_full"] = np.where(
        base["den_full"] > 0, base["num"] / base["den_full"], 0.0
    )
    total_full = base["ratio_full"].sum()
    base["ratio_full_pct"] = (
        base["ratio_full"] / total_full * 100.0 if total_full > 0 else 0.0
    )
    # Pull pct_tasks_affected from the same dashboard pipeline that drives
    # the Part 2 major_categories chart so the colorbar values match
    # exactly. The exploratory `compute_major_pct_tasks_affected` only sums
    # over rated task-occ pairs and produces a different (higher) number.
    major_df = _run_config(PRIMARY_DATASET, "major")
    pct_aff = major_df.set_index("category")["pct_tasks_affected"]
    base["pct_tasks_affected"] = base["category"].map(pct_aff).fillna(0.0)

    # Anchor major: Office and Administrative Support — a near-median major
    # category used as the x=1 reference for the lift axis.
    anchor_major = "Office and Administrative Support Occupations"
    anchor_val = base.loc[base["category"] == anchor_major, "ratio_full_pct"].iloc[0]
    assert anchor_val > 0, f"Anchor value for {anchor_major} must be > 0"
    base["lift"] = base["ratio_full_pct"] / anchor_val
    median_lift = float(base["lift"].median())

    out = base[["category", "ratio_full_pct", "lift", "pct_tasks_affected"]].copy()
    out["anchor_value"] = anchor_val
    out["median_lift"] = median_lift
    save_csv(
        out.sort_values("lift", ascending=False),
        results / "intensity_anchor_fulleco.csv",
        float_format="%.4f",
    )

    plot_df = base.sort_values("lift", ascending=True).reset_index(drop=True)
    # Strip the redundant " Occupations" suffix from y-tick display labels.
    plot_df["display_category"] = (
        plot_df["category"].str.replace(r"\s*Occupations\s*$", "", regex=True)
    )
    cvals = plot_df["pct_tasks_affected"].to_numpy(dtype=float)
    cmin, cmax = float(cvals.min()), float(cvals.max())

    W = PAPER_W
    px = paper_fonts(W)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=plot_df["display_category"], x=plot_df["lift"], orientation="h",
        marker=dict(
            color=cvals,
            colorscale=[[0, TASKS_LIGHT], [1, TASKS_DARK]],
            cmin=cmin, cmax=cmax,
            showscale=False,
            line=dict(width=0),
        ),
        text=[f"{v:.2f}x" for v in plot_df["lift"]],
        textposition="outside",
        textfont=dict(size=px["tick"], color=PAPER_PALETTE["text"], family=FONT_FAMILY),
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>lift: %{x:.2f}x<extra></extra>",
        showlegend=False,
    ))

    # Median reference line — anchor is set so it sits at x = 1
    fig.add_vline(
        x=1.0, line_dash="dash",
        line_color=PAPER_PALETTE["negative"], line_width=1.5,
    )
    fig.add_annotation(
        x=1.0, y=1.005,
        xref="x", yref="paper",
        text="median",
        showarrow=False, xanchor="left", yanchor="bottom",
        font=dict(size=px["in_chart_floor"], color=PAPER_PALETTE["negative"], family=FONT_FAMILY),
    )

    # Bottom legend: HTML-swatch gradient matching tech_commodities style.
    def _hex_to_rgb(h: str) -> tuple[int, int, int]:
        return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))
    rgb_l = _hex_to_rgb(TASKS_LIGHT)
    rgb_d = _hex_to_rgb(TASKS_DARK)
    N_SWATCH = 7
    swatch_html = ""
    for i in range(N_SWATCH):
        t = i / (N_SWATCH - 1)
        c = tuple(int(rgb_l[k] + (rgb_d[k] - rgb_l[k]) * t) for k in range(3))
        swatch_html += f"<span style='color:rgb({c[0]},{c[1]},{c[2]})'>■</span>"
    legend_text = (
        f"Tasks Exposed&nbsp;&nbsp;{cmin:.0f}%&nbsp;"
        f"{swatch_html}&nbsp;{cmax:.0f}%"
    )
    # Bottom legend — same position pattern as tech_commodities (centered
    # on the PNG, with the same gap from x-axis title to legend).
    fig.add_annotation(
        x=0.14, y=-0.17,
        xref="paper", yref="paper",
        text=legend_text, showarrow=False,
        xanchor="center", yanchor="middle",
        font=dict(size=px["in_chart_floor"],
                  color=PAPER_PALETTE["text"], family=FONT_FAMILY),
    )

    style_paper_figure(
        fig,
        "Actual AI Usage as a Multiple of Median Usage",
        subtitle=(
            "Σ pct usage ÷ Σ (freq × employment) for equalization — debiased to a "
            "Claude / Copilot / ChatGPT GWA-distribution blend (work-related ChatGPT chats)."
        ),
        height=1280, width=W,
        margin=dict(l=20, r=80, t=110, b=190),
    )
    x_top = max(plot_df["lift"]) * 1.04
    fig.update_xaxes(
        title=dict(text="Usage Relative to Median (×)", font=dict(size=px["axis_title"], family=FONT_FAMILY)),
        showgrid=True, gridcolor=PAPER_PALETTE["grid"],
        range=[0, x_top],
        tickfont=dict(size=px["tick"], family=FONT_FAMILY),
    )
    fig.update_yaxes(
        title=dict(text="Major Occupational Category", font=dict(size=px["axis_title"], family=FONT_FAMILY)),
        showgrid=False, showline=False,
        tickfont=dict(size=px["tick"], family=FONT_FAMILY),
    )

    save_figure(fig, results / "figures" / "intensity_anchor_fulleco.png", scale=2)
    _copy_fig(results, figures, "intensity_anchor_fulleco.png")
    print("  -> intensity_anchor_fulleco.png")


# ─────────────────────────────────────────────────────────────────────────
# Figure 4: Risk Score Audit — Section 5f (SKA-gated focused 43)
# Pulls audit's flag-frame + focused-set builders, renders in paper style.
# Skips gracefully if exploratory/risk_score_audit isn't available.
# ─────────────────────────────────────────────────────────────────────────

def build_risk_score_5f(results: Path, figures: Path) -> None:
    try:
        from analysis.exploratory.audit_risk_score.run import (
            _load_flag_df, _build_focused_set,
        )
    except ImportError as exc:
        print(f"  -> SKIPPED: exploratory/audit_risk_score not available ({exc})")
        return

    flags_df = _load_flag_df()
    sub = _build_focused_set(flags_df)
    s5f = sub[sub["ska_gated"] == 1].copy()
    s5f["abs_emp"] = s5f["emp_proj_pct"].abs()
    s5f = s5f.sort_values("abs_emp", ascending=True).reset_index(drop=True)

    save_csv(
        s5f.sort_values("abs_emp", ascending=False)[
            ["title_current", "major_short", "job_zone", "emp_proj_pct",
             "pct", "ska_pct", "pct_delta", "workers_affected", "wages_affected"]
        ],
        results / "risk_score_5f.csv",
        float_format="%.3f",
    )

    pct_min_f = float(s5f["pct"].min())
    pct_max_f = float(s5f["pct"].max())

    # Composition counts for the caption / prose (printed to stdout, also
    # saved alongside the per-occ CSV so the numbers are reproducible).
    zone_counts = (
        s5f["job_zone"].astype(int).value_counts().sort_index()
    )
    major_counts = s5f["major_short"].value_counts()
    print(f"  -> risk_score_5f composition (n={len(s5f)}):")
    print("       by job zone:")
    for z, c in zone_counts.items():
        print(f"         zone {z}: {c}")
    print("       by major occ category:")
    for m, c in major_counts.items():
        print(f"         {m}: {c}")
    counts_rows = (
        [{"group": "job_zone", "label": f"zone {int(z)}", "count": int(c)}
         for z, c in zone_counts.items()]
        + [{"group": "major", "label": m, "count": int(c)}
           for m, c in major_counts.items()]
    )
    save_csv(pd.DataFrame(counts_rows), results / "risk_score_5f_counts.csv")

    W = PAPER_W + 280
    px = paper_fonts(W)
    floor_px = px["in_chart_floor"]
    tick_px = px["tick"]
    axis_px = px["axis_title"]

    def _truncate_title(s: str, max_len: int = 50) -> str:
        # Keep each y-label on a single line: if the title overruns max_len,
        # cut at the last comma or space inside the window and append "…".
        if len(s) <= max_len:
            return s
        breakers = [i for i in range(max_len) if s[i] in ", "]
        cut = max(breakers) if breakers else max_len - 1
        return s[:cut].rstrip(" ,") + "…"

    y_labels = [_truncate_title(t) for t in s5f["title_current"]]

    # Plotly's colorbar.x interpretation in v6 doesn't line up cleanly
    # with plot-area paper coords, so we hand-draw the legend the same way
    # build_tech_commodities() does — full positioning control for
    # label-left + gradient-right, centered on the whole PNG.
    MARGIN_L, MARGIN_R = 520, 120
    MARGIN_T, MARGIN_B = 130, 240
    plot_area_px = W - MARGIN_L - MARGIN_R
    canvas_center_paper = (W / 2 - MARGIN_L) / plot_area_px

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=y_labels, x=s5f["abs_emp"], orientation="h",
        marker=dict(
            color=s5f["pct"].values,
            colorscale=[[0, TASKS_LIGHT], [1, TASKS_DARK]],
            cmin=pct_min_f, cmax=pct_max_f,
            showscale=False,                # legend drawn manually below
            line=dict(width=0),
        ),
        showlegend=False,
        hovertemplate="<b>%{y}</b><br>emp proj: -%{x:.1f}%<extra></extra>",
    ))

    # Bottom legend: single centered annotation with inline HTML swatches,
    # mirroring the build_tech_commodities() pattern. All on one line:
    #   "Tasks Exposed   51% [■■■■■■■] 87%"
    def _hex_to_rgb(h: str) -> tuple[int, int, int]:
        return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))
    rgb_l = _hex_to_rgb(TASKS_LIGHT)
    rgb_d = _hex_to_rgb(TASKS_DARK)
    N_SWATCH = 7
    swatch_html = ""
    for i in range(N_SWATCH):
        t = i / (N_SWATCH - 1)
        c = tuple(int(rgb_l[k] + (rgb_d[k] - rgb_l[k]) * t) for k in range(3))
        swatch_html += f"<span style='color:rgb({c[0]},{c[1]},{c[2]})'>■</span>"
    legend_text = (
        f"Tasks Exposed&nbsp;&nbsp;{pct_min_f:.0f}%&nbsp;"
        f"{swatch_html}&nbsp;{pct_max_f:.0f}%"
    )
    # xref="paper" x=0.5 centers on the rendered plot area, not on the PNG.
    # With a large explicit left margin (and Plotly's tendency to expand
    # it further to fit long y-tick labels), the plot area sits right of
    # the PNG center. The x below was empirically tuned to land the legend
    # centered on the PNG for this margin pair; retune if margins change.
    fig.add_annotation(
        x=0.10, y=-0.08,
        xref="paper", yref="paper",
        text=legend_text, showarrow=False,
        xanchor="center", yanchor="middle",
        font=dict(size=floor_px,
                  color=PAPER_PALETTE["text"], family=FONT_FAMILY),
    )

    n = len(s5f)
    # All labels are now single-line (truncated), so per-row drops back to
    # ~56 px — plenty for a 9 pt print tick label without overlap.
    height = max(900, n * 56 + MARGIN_T + MARGIN_B)

    # Tight x range so bars fill more of the chart width. Tasks column
    # sits right after the longest bar; x_top is set so the tasks text
    # ends close to the right edge of the plot area.
    x_max = float(s5f["abs_emp"].max())
    # "87% tasks" text width in x units (rough: 9 chars × 0.55 × floor_px).
    tasks_text_w_px = int(0.55 * floor_px * len("87% tasks"))
    tasks_label_x = x_max * 1.04
    # x_top: tasks_label_x + text width (converted to x units) + small pad.
    # Iterative solve since x_per_px depends on x_top — one pass is enough
    # because the relationship is monotone and the pad absorbs the error.
    approx_x_per_px = (x_max * 1.20) / max(plot_area_px, 1)
    x_top = tasks_label_x + tasks_text_w_px * approx_x_per_px + 1.5

    # In-bar emp_proj label: only when the bar is wide enough to hold the
    # text inside without overflowing into the bar's left edge.
    # Approx text width: 7 chars (e.g. "-36.1%") × 0.55 × floor_px.
    inside_text_w_px = int(0.55 * floor_px * 7)
    inside_pad_px = 18
    needed_px = inside_text_w_px + inside_pad_px
    x_per_px = x_top / max(plot_area_px, 1)
    inside_threshold = needed_px * x_per_px

    # Per-bar dynamic text color for the inside label: white on darker
    # bars, dark on lighter ones.
    pct_mid = (pct_min_f + pct_max_f) / 2

    for i, row in s5f.iterrows():
        # Tasks number — always at fixed x, left-anchored, neutral color.
        fig.add_annotation(
            x=tasks_label_x, y=y_labels[i],
            xref="x", yref="y",
            text=f"{row['pct']:.0f}% tasks",
            showarrow=False,
            xanchor="left", yanchor="middle",
            font=dict(size=floor_px,
                      color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
        )

        # Proj number — inside the bar (right-aligned at bar end) if it
        # fits, else just outside the bar end (left-anchored).
        proj_text = f"{row['emp_proj_pct']:+.1f}%"
        if row["abs_emp"] >= inside_threshold:
            text_color = "white" if row["pct"] >= pct_mid else PAPER_PALETTE["text_dark"]
            fig.add_annotation(
                x=row["abs_emp"], y=y_labels[i],
                xref="x", yref="y",
                text=proj_text,
                showarrow=False,
                xanchor="right", yanchor="middle",
                xshift=-8,
                font=dict(size=floor_px, color=text_color, family=FONT_FAMILY),
            )
        else:
            fig.add_annotation(
                x=row["abs_emp"], y=y_labels[i],
                xref="x", yref="y",
                text=proj_text,
                showarrow=False,
                xanchor="left", yanchor="middle",
                xshift=4,
                font=dict(size=floor_px,
                          color=PAPER_PALETTE["neutral"], family=FONT_FAMILY),
            )

    style_paper_figure(
        fig,
        "Occupations with High AI Exposure and Negative Employment Projection",
        height=height, width=W,
        margin=dict(l=MARGIN_L, r=MARGIN_R, t=MARGIN_T, b=MARGIN_B),
    )
    # X-axis ticks (and gridlines) stop at 40%, even though x_top extends
    # further to leave room for the "% tasks" annotation column.
    fig.update_xaxes(
        title=dict(text="BLS Projected Employment 2024–2034 (%)",
                   font=dict(size=axis_px, family=FONT_FAMILY)),
        showgrid=True, gridcolor=PAPER_PALETTE["grid"], ticksuffix="%",
        range=[0, x_top],
        tickmode="array", tickvals=[0, 10, 20, 30, 40],
        tickfont=dict(size=tick_px, family=FONT_FAMILY),
    )
    fig.update_yaxes(
        title=dict(text="Occupation", font=dict(size=axis_px, family=FONT_FAMILY)),
        showgrid=False, showline=False,
        tickfont=dict(size=tick_px, family=FONT_FAMILY),
    )
    fig.update_layout(bargap=0.22)

    save_figure(fig, results / "figures" / "risk_score_5f.png", scale=2)
    _copy_fig(results, figures, "risk_score_5f.png")
    print("  -> risk_score_5f.png")


# ─────────────────────────────────────────────────────────────────────────
# Figure 5: State Exposure vs. Most-At-Risk Concentration
# Two-panel horizontal bar (% emp exposed | % emp in "Most At Risk" set).
# Computation runs through deepdive_state_signal (gitignored exploratory);
# skips gracefully if that folder isn't present.
# ─────────────────────────────────────────────────────────────────────────

def build_state_clusters_map(results: Path, figures: Path) -> None:
    """U.S. choropleth coloring each state by its Ward AI-exposure cluster.

    Replaces the prior `state_exposure_at_risk.png` two-panel bar chart in
    the paper main body. Clustering computed once via the exploratory
    `deepdive_state_clusters.compute_clusters()` helper so the paper and
    exploratory views stay in sync.
    """
    try:
        from analysis.exploratory.deepdive_state_clusters.run import (
            compute_clusters, OUTLIER_CLUSTER_ID,
        )
    except ImportError as exc:
        print(f"  -> SKIPPED: exploratory/deepdive_state_clusters not available ({exc})")
        return

    pkg = compute_clusters()
    state_df       = pkg["state_df"]
    cluster_names  = pkg["cluster_names"]
    cluster_color  = pkg["cluster_color"]
    order          = pkg["order"]

    save_csv(
        state_df[["geo", "cluster", "cluster_name",
                  "pct_emp_wtd", "focused_share_pct"]]
        .sort_values(["cluster", "pct_emp_wtd"]),
        results / "state_clusters_map.csv",
        float_format="%.3f",
    )

    # Reverse the canonical order so the darkest blue (worst exposure)
    # sits at the TOP of the colorbar rather than the bottom — Plotly
    # renders colorbars low-z at the bottom.
    display_order = list(reversed(order))
    display_idx = {int(cid): i for i, cid in enumerate(display_order)}
    n_clusters = len(display_order)

    colorscale: list[list] = []
    for i, cid in enumerate(display_order):
        lo = i / n_clusters
        hi = (i + 1) / n_clusters
        colorscale.append([lo, cluster_color[cid]])
        colorscale.append([hi, cluster_color[cid]])

    z_vals = state_df["cluster"].map(display_idx).astype(float)

    fig = go.Figure(data=go.Choropleth(
        locations=state_df["geo"].str.upper(),
        z=z_vals,
        locationmode="USA-states",
        colorscale=colorscale,
        zmin=-0.5, zmax=n_clusters - 0.5,
        marker_line_color="white",
        marker_line_width=0.8,
        showscale=False,  # custom legend below via scatter traces
        text=[
            f"{r['geo'].upper()}<br>"
            f"% workforce exposed: {r['pct_emp_wtd']:.1f}%<br>"
            f"% in High AI Exp & <0 Emp Proj: {r['focused_share_pct']:.1f}%"
            for _, r in state_df.iterrows()
        ],
        hovertemplate="%{text}<extra></extra>",
    ))

    # NOTE: style_paper_figure isn't used on this chart. It calls
    # update_xaxes / update_yaxes which interfere with geo-subplot sizing
    # (the map ends up tiny in a mostly-empty canvas regardless of domain
    # or projection scale settings). We build paper-equivalent chrome
    # manually using the same font ladder. Per paper convention the
    # subtitle drops off the image (it becomes the figure caption).
    W, H = PAPER_W, 940
    px = paper_fonts(W)

    fig.update_geos(
        scope="usa",
        projection=dict(type="albers usa", scale=1.05),
        showland=True, landcolor=PAPER_PALETTE["surface"],
        showlakes=False, showsubunits=True,
        subunitcolor="white",
        bgcolor="rgba(0,0,0,0)",
        # Geo subplot fills the full canvas width; legend sits below.
        domain=dict(x=[0.0, 1.0], y=[0.20, 1.0]),
    )

    # Custom legend: invisible scatter traces (one per cluster) rendered
    # in legend order. Plotly's horizontal colorbar can't fit the long
    # cluster names without overlap, so we use legend entries instead.
    # Iterate `order` (severe → mild) so the most-severe cluster (DC) sits
    # at the top of the legend, matching the prior colorbar layout.
    for cid in order:
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(size=14, color=cluster_color[cid],
                        line=dict(width=0)),
            name=cluster_names[cid],
            showlegend=True,
            hoverinfo="skip",
        ))

    fig.update_layout(
        width=W, height=H,
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=20, r=20, t=70, b=20),
        title=dict(
            text="U.S. States Clustered on Workforce Exposure",
            font=dict(size=px["title"], family=FONT_FAMILY,
                      color=PAPER_PALETTE["text"]),
            x=0.012, xanchor="left",
            y=0.97,  yanchor="top",
        ),
        legend=dict(
            orientation="v",
            x=0.5, xanchor="center",
            y=0.18, yanchor="top",
            font=dict(size=px["legend"], family=FONT_FAMILY,
                      color=PAPER_PALETTE["text"]),
            bgcolor="rgba(255,255,255,0)",
            itemclick=False, itemdoubleclick=False,
            tracegroupgap=2,
        ),
        # Hide the cartesian axes that the scatter traces create.
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )

    save_figure(fig, results / "figures" / "state_clusters_map.png", scale=2)
    _copy_fig(results, figures, "state_clusters_map.png")
    print("  -> state_clusters_map.png")


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    results = ensure_results_dir(HERE)
    figures = HERE / "figures"
    figures.mkdir(exist_ok=True)

    print("=" * 64)
    print("Part 3: Action — What To Do About It")
    print("=" * 64)

    print("\n[1/6] Agentic Confirmed vs. Agentic Ceiling — major occupational categories")
    build_agentic_ceiling_major(results, figures)

    print("\n[2/6] Agentic Confirmed vs. Agentic Ceiling — general work activities")
    build_agentic_ceiling_gwa(results, figures)

    print("\n[3/6] Tech commodities composite")
    build_tech_commodities(results, figures)

    print("\n[4/6] Risk score 5f — SKA-gated focused 43")
    build_risk_score_5f(results, figures)

    print("\n[5/6] U.S. states clustered on AI exposure (map)")
    build_state_clusters_map(results, figures)

    print("\n[6/6] AI intensity vs. median-rank anchor (full eco_2025)")
    build_intensity_anchor_fulleco(results, figures)

    print("\n" + "=" * 64)
    print("Part 3 complete — figures in results/figures/ and figures/")
    print("=" * 64)


if __name__ == "__main__":
    main()
