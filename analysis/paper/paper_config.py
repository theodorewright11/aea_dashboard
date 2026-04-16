"""
paper_config.py — Visual palette and formatting constants for paper charts.

Defines a consistent visual language for all paper figures. Based on the
workforce_meeting_v2 readable style (big text, fill space), adapted for
publication use. Colors are muted/washed-out to match the correlation
heatmap aesthetic.
"""
from __future__ import annotations

import plotly.graph_objects as go

from analysis.utils import COLORS, FONT_FAMILY

# ── Canvas dimensions ────────────────────────────────────────────────────
PAPER_W: int = 1400
PAPER_H: int = 787

# ── Typography (px) ──────────────────────────────────────────────────────
TITLE_FS: int = 22
SUBTITLE_FS: int = 15
INSIDE_FS: int = 19       # Primary values inside bars
OUTSIDE_FS: int = 16      # Secondary info outside bars / data labels
TICK_FS: int = 15          # Axis tick labels
LABEL_FS: int = 16         # Axis titles
LEGEND_FS: int = 15        # Legend items
ANNOT_FS: int = 12         # Footnotes
HEATMAP_TEXT_FS: int = 18  # Correlation values inside heatmap cells
TABLE_HEADER_FS: int = 14  # Table column headers
TABLE_CELL_FS: int = 13    # Table cell text

# ── Five-config colors ───────────────────────────────────────────────────
CONFIG_COLORS: dict[str, str] = {
    "all_confirmed":      "#3a5f83",
    "all_ceiling":        "#4a7c6f",
    "human_conversation": "#c05621",
    "agentic_confirmed":  "#7b5ea7",
    "agentic_ceiling":    "#2e8b8b",
}

# ── Three-metric colors (muted, cohesive) ────────────────────────────────
METRIC_COLORS: dict[str, str] = {
    "tasks":   "#4a7a94",   # Muted slate blue
    "workers": "#6a9e8f",   # Muted sage teal
    "wages":   "#b39b6d",   # Warm tan
}

# ── Heatmap scale ────────────────────────────────────────────────────────
HEATMAP_LOW: str = "#f0e6d3"
HEATMAP_HIGH: str = "#0d2b45"

# ── Trend line colors (muted to match palette) ──────────────────────────
TREND_COLORS: dict[str, str] = {
    "all_confirmed": "#4a7a94",
    "all_ceiling":   "#6a9e8f",
}

# ── Full palette (consolidated reference) ────────────────────────────────
PAPER_PALETTE: dict[str, str] = {
    **CONFIG_COLORS,
    **METRIC_COLORS,
    "text":       COLORS["text"],
    "text_dark":  "#0a0a0a",      # Darker text for heatmap cells
    "muted":      COLORS["muted"],
    "neutral":    COLORS["neutral"],
    "grid":       COLORS["grid"],
    "surface":    "#ffffff",
    "page":       COLORS["bg_page"],
    "positive":   COLORS["positive"],
    "negative":   COLORS["negative"],
    # Table accent colors
    "row_highlight": "#e8f0f7",   # Light blue for start/end rows
    "cell_pos":      "#e6f4ea",   # Light green for positive deltas
    "row_ref":       "#f5f5f0",   # Light cream for reference row
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


def fmt_date(iso: str) -> str:
    """Format '2025-03-06' → 'March 6, 2025'."""
    from datetime import datetime
    dt = datetime.strptime(iso, "%Y-%m-%d")
    return dt.strftime("%B %d, %Y").replace(" 0", " ")


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
        title_font=dict(size=LABEL_FS, family=FONT_FAMILY),
    )
    fig.update_yaxes(
        gridcolor=PAPER_PALETTE["grid"],
        tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
        title_font=dict(size=LABEL_FS, family=FONT_FAMILY),
    )

    return fig
