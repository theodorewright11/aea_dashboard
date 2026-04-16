"""
paper_config.py — Visual palette and formatting constants for paper charts.

Defines a consistent visual language for all paper figures. Based on the
workforce_meeting_v2 readable style (big text, fill space), adapted for
publication use.
"""
from __future__ import annotations

import plotly.graph_objects as go

from analysis.utils import COLORS, FONT_FAMILY

# ── Canvas dimensions ────────────────────────────────────────────────────
PAPER_W: int = 1400
PAPER_H: int = 787

# ── Typography (px) ──────────────────────────────────────────────────────
TITLE_FS: int = 22
SUBTITLE_FS: int = 14
INSIDE_FS: int = 18       # Primary values inside bars
OUTSIDE_FS: int = 15      # Secondary info outside bars
TICK_FS: int = 13         # Axis tick labels
LABEL_FS: int = 14        # Axis titles, legend items
LEGEND_FS: int = 13
ANNOT_FS: int = 11        # Source attribution, footnotes
HEATMAP_TEXT_FS: int = 16  # Correlation values inside heatmap cells

# ── Five-config colors ───────────────────────────────────────────────────
CONFIG_COLORS: dict[str, str] = {
    "all_confirmed":      "#3a5f83",   # Slate blue (primary)
    "all_ceiling":        "#4a7c6f",   # Teal green
    "human_conversation": "#c05621",   # Warm orange
    "agentic_confirmed":  "#7b5ea7",   # Purple
    "agentic_ceiling":    "#2e8b8b",   # Dark teal
}

# ── Three-metric colors (for overview chart) ─────────────────────────────
# Blue → teal → gold spectrum: cohesive, professional
METRIC_COLORS: dict[str, str] = {
    "tasks":   "#2c5f7c",   # Deep blue
    "workers": "#4a8c7c",   # Teal
    "wages":   "#c4962c",   # Golden amber
}

# ── Heatmap scale ────────────────────────────────────────────────────────
HEATMAP_LOW: str = "#f0e6d3"
HEATMAP_HIGH: str = "#0d2b45"

# ── Trend line colors ────────────────────────────────────────────────────
TREND_COLORS: dict[str, str] = {
    "all_confirmed": "#3a5f83",
    "all_ceiling":   "#4a7c6f",
}

# ── Full palette (consolidated reference) ────────────────────────────────
PAPER_PALETTE: dict[str, str] = {
    **CONFIG_COLORS,
    **METRIC_COLORS,
    "text":     COLORS["text"],
    "muted":    COLORS["muted"],
    "neutral":  COLORS["neutral"],
    "grid":     COLORS["grid"],
    "surface":  "#ffffff",
    "page":     COLORS["bg_page"],
    "positive": COLORS["positive"],
    "negative": COLORS["negative"],
    # Table accent colors
    "row_start":  "#e8f0f7",   # Light blue for start/end rows
    "row_end":    "#e8f0f7",
    "cell_pos":   "#e6f4ea",   # Light green for positive deltas
}


# ── Paper-specific formatters ────────────────────────────────────────────

def fmt_wages(val: float) -> str:
    """Format wages with T/B/M/K units."""
    sign = "-" if val < 0 else ""
    av = abs(val)
    if av >= 1e12:
        return f"{sign}${av / 1e12:.1f}T"
    if av >= 1e9:
        return f"{sign}${av / 1e9:.1f}B"
    if av >= 1e6:
        return f"{sign}${av / 1e6:.1f}M"
    if av >= 1e3:
        return f"{sign}${av / 1e3:.0f}K"
    return f"{sign}${av:.0f}"


def fmt_workers(val: float) -> str:
    """Format workers with M/K units."""
    sign = "-" if val < 0 else ""
    av = abs(val)
    if av >= 1e6:
        return f"{sign}{av / 1e6:.1f}M"
    if av >= 1e3:
        return f"{sign}{av / 1e3:.0f}K"
    return f"{sign}{int(av)}"


# ── Figure styling ───────────────────────────────────────────────────────

def style_paper_figure(
    fig: go.Figure,
    title: str,
    subtitle: str = "",
    width: int = PAPER_W,
    height: int = PAPER_H,
    margin: dict | None = None,
) -> go.Figure:
    """Apply consistent paper styling to a Plotly figure.

    No source attribution or config subtitle by default — the paper's
    methods section handles that context.
    """
    title_html = title
    if subtitle:
        muted = PAPER_PALETTE["muted"]
        title_html += (
            f"<br><span style='font-size:{SUBTITLE_FS}px;"
            f"color:{muted}'>{subtitle}</span>"
        )

    m = margin or dict(l=20, r=60, t=90, b=70)

    fig.update_layout(
        title=dict(
            text=title_html,
            font=dict(size=TITLE_FS, color=PAPER_PALETTE["text"], family=FONT_FAMILY),
            x=0.01, xanchor="left",
        ),
        font=dict(family=FONT_FAMILY, color=PAPER_PALETTE["text"]),
        plot_bgcolor=PAPER_PALETTE["surface"],
        paper_bgcolor=PAPER_PALETTE["surface"],
        width=width,
        height=height,
        margin=m,
        legend=dict(
            font=dict(size=LEGEND_FS, family=FONT_FAMILY),
            orientation="h",
            yanchor="top", y=-0.08, xanchor="left", x=0,
        ),
    )

    fig.update_xaxes(
        gridcolor=PAPER_PALETTE["grid"],
        tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
    )
    fig.update_yaxes(
        gridcolor=PAPER_PALETTE["grid"],
        tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
    )

    return fig
