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
METRIC_COLORS: dict[str, str] = {
    "tasks":   "#3a5f83",   # Slate blue
    "workers": "#4a7c6f",   # Teal green
    "wages":   "#c05621",   # Warm orange
}

# ── Heatmap scale ────────────────────────────────────────────────────────
HEATMAP_LOW: str = "#f0e6d3"
HEATMAP_HIGH: str = "#0d2b45"

# ── Trend line colors ────────────────────────────────────────────────────
TREND_COLORS: dict[str, str] = {
    "all_confirmed": "#3a5f83",
    "all_ceiling":   "#4a7c6f",
}

# ── Source attribution ───────────────────────────────────────────────────
SOURCE_LINE: str = "Source: AEA Dashboard — Utah OAIP"

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
}


def style_paper_figure(
    fig: go.Figure,
    title: str,
    subtitle: str = "",
    source_text: str = SOURCE_LINE,
    width: int = PAPER_W,
    height: int = PAPER_H,
    margin: dict | None = None,
) -> go.Figure:
    """Apply consistent paper styling to a Plotly figure."""
    muted = PAPER_PALETTE["muted"]
    title_html = title
    if subtitle:
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
            yanchor="top", y=-0.10, xanchor="left", x=0,
        ),
    )

    # Source attribution
    if source_text:
        fig.add_annotation(
            text=source_text,
            xref="paper", yref="paper",
            x=1.0, y=-0.10,
            showarrow=False,
            font=dict(size=ANNOT_FS, color=PAPER_PALETTE["muted"], family=FONT_FAMILY),
            xanchor="right",
        )

    # Gridlines
    fig.update_xaxes(
        gridcolor=PAPER_PALETTE["grid"],
        tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
    )
    fig.update_yaxes(
        gridcolor=PAPER_PALETTE["grid"],
        tickfont=dict(size=TICK_FS, family=FONT_FAMILY),
    )

    return fig
