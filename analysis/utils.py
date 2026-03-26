"""
utils.py — Shared chart styling, formatting, and output helpers for analysis scripts.

All question scripts should use these helpers for consistent output.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

# ── Color palette ─────────────────────────────────────────────────────────────
# Consistent colors across all analysis outputs.

COLORS = {
    "primary": "#2563EB",       # Blue — main data series
    "secondary": "#7C3AED",     # Purple — comparison series
    "accent": "#F59E0B",        # Amber — highlights / callouts
    "positive": "#10B981",      # Green — increases / gains
    "negative": "#EF4444",      # Red — decreases / losses
    "neutral": "#6B7280",       # Gray — baselines / context
    "utah": "#DC2626",          # Red — Utah-specific
    "national": "#2563EB",      # Blue — National
    "aei": "#2563EB",           # Blue — AEI family
    "mcp": "#7C3AED",           # Purple — MCP family
    "microsoft": "#F59E0B",     # Amber — Microsoft
    "bg": "#FFFFFF",            # White background
    "text": "#1F2937",          # Dark gray text
    "grid": "#E5E7EB",          # Light gray gridlines
}

# Categorical palette for multi-series charts (up to 10 items)
CATEGORY_PALETTE = [
    "#2563EB", "#7C3AED", "#F59E0B", "#10B981", "#EF4444",
    "#8B5CF6", "#06B6D4", "#F97316", "#EC4899", "#6366F1",
]


# ── Figure styling ────────────────────────────────────────────────────────────

def style_figure(
    fig: go.Figure,
    title: str,
    *,
    subtitle: Optional[str] = None,
    x_title: Optional[str] = None,
    y_title: Optional[str] = None,
    width: int = 1200,
    height: int = 700,
    source_text: str = "Source: AEA Dashboard — Utah OAIP",
    show_legend: bool = True,
) -> go.Figure:
    """Apply consistent professional styling to a Plotly figure.

    Call this on every figure before saving. It handles layout, fonts,
    colors, margins, and source attribution.
    """
    title_text = title
    if subtitle:
        title_text += f"<br><span style='font-size:14px;color:{COLORS['neutral']}'>{subtitle}</span>"

    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(size=20, color=COLORS["text"], family="Arial, sans-serif"),
            x=0.01,
            xanchor="left",
        ),
        font=dict(
            family="Arial, sans-serif",
            size=13,
            color=COLORS["text"],
        ),
        plot_bgcolor=COLORS["bg"],
        paper_bgcolor=COLORS["bg"],
        width=width,
        height=height,
        margin=dict(l=60, r=40, t=80, b=80),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.12,
            xanchor="center",
            x=0.5,
            font=dict(size=12),
        ) if show_legend else dict(visible=False),
        xaxis=dict(
            title=x_title,
            gridcolor=COLORS["grid"],
            showline=True,
            linewidth=1,
            linecolor=COLORS["grid"],
        ),
        yaxis=dict(
            title=y_title,
            gridcolor=COLORS["grid"],
            showline=True,
            linewidth=1,
            linecolor=COLORS["grid"],
        ),
    )

    # Source attribution in bottom-right
    fig.add_annotation(
        text=source_text,
        xref="paper", yref="paper",
        x=1.0, y=-0.18,
        showarrow=False,
        font=dict(size=10, color=COLORS["neutral"]),
        xanchor="right",
    )

    return fig


def make_horizontal_bar(
    df: pd.DataFrame,
    category_col: str,
    value_col: str,
    title: str,
    *,
    subtitle: Optional[str] = None,
    x_title: Optional[str] = None,
    color: str = COLORS["primary"],
    highlight_categories: Optional[list[str]] = None,
    highlight_color: str = COLORS["accent"],
    top_n: Optional[int] = None,
    **style_kwargs,
) -> go.Figure:
    """Create a styled horizontal bar chart (the dashboard's signature chart type).

    Args:
        df: DataFrame with category and value columns.
        category_col: Column name for category labels.
        value_col: Column name for bar values.
        title: Chart title.
        subtitle: Optional subtitle line.
        x_title: X-axis label.
        color: Default bar color.
        highlight_categories: Categories to highlight in a different color.
        highlight_color: Color for highlighted categories.
        top_n: If set, take only the top N rows (assumes df is pre-sorted).
    """
    plot_df = df.head(top_n) if top_n else df

    # Build colors per bar
    colors = []
    for cat in plot_df[category_col]:
        if highlight_categories and cat in highlight_categories:
            colors.append(highlight_color)
        else:
            colors.append(color)

    fig = go.Figure(go.Bar(
        x=plot_df[value_col],
        y=plot_df[category_col],
        orientation="h",
        marker_color=colors,
        text=plot_df[value_col],
        textposition="auto",
        texttemplate="%{text:,.0f}",
    ))

    # Reverse y-axis so rank 1 is on top
    fig.update_yaxes(autorange="reversed")

    style_figure(
        fig, title,
        subtitle=subtitle,
        x_title=x_title,
        y_title=None,
        show_legend=False,
        **style_kwargs,
    )

    return fig


def make_line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: str,
    title: str,
    *,
    subtitle: Optional[str] = None,
    x_title: Optional[str] = None,
    y_title: Optional[str] = None,
    palette: Optional[list[str]] = None,
    **style_kwargs,
) -> go.Figure:
    """Create a styled multi-line chart for trends.

    Args:
        df: Long-format DataFrame.
        x_col: Column for x-axis (usually date).
        y_col: Column for y-axis (metric value).
        color_col: Column that defines each line (category name).
        title: Chart title.
    """
    palette = palette or CATEGORY_PALETTE
    categories = df[color_col].unique()

    fig = go.Figure()
    for i, cat in enumerate(categories):
        cat_df = df[df[color_col] == cat].sort_values(x_col)
        fig.add_trace(go.Scatter(
            x=cat_df[x_col],
            y=cat_df[y_col],
            mode="lines+markers",
            name=str(cat),
            line=dict(color=palette[i % len(palette)], width=2),
            marker=dict(size=6),
        ))

    style_figure(
        fig, title,
        subtitle=subtitle,
        x_title=x_title,
        y_title=y_title,
        **style_kwargs,
    )

    return fig


# ── Output helpers ────────────────────────────────────────────────────────────

def save_figure(
    fig: go.Figure,
    path: Path,
    *,
    width: Optional[int] = None,
    height: Optional[int] = None,
    scale: int = 3,
) -> None:
    """Save a Plotly figure as a high-res PNG.

    Args:
        fig: The styled Plotly figure.
        path: Output file path (.png).
        width: Override width (uses figure's layout width if None).
        height: Override height (uses figure's layout height if None).
        scale: Resolution multiplier (3 = 300 DPI equivalent at default size).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pio.write_image(
        fig, str(path),
        width=width or fig.layout.width or 1200,
        height=height or fig.layout.height or 700,
        scale=scale,
    )


def save_csv(df: pd.DataFrame, path: Path, *, float_format: str = "%.2f") -> None:
    """Save a DataFrame as CSV with consistent formatting."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(str(path), index=False, float_format=float_format)


# ── Formatting helpers ────────────────────────────────────────────────────────

def format_workers(n: float) -> str:
    """Format worker counts with adaptive units (e.g., '1.2M', '450K')."""
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif abs(n) >= 1_000:
        return f"{n / 1_000:.0f}K"
    return f"{n:.0f}"


def format_wages(n: float) -> str:
    """Format wage dollars with adaptive units (e.g., '$1.2B', '$450M')."""
    if abs(n) >= 1_000_000_000:
        return f"${n / 1_000_000_000:.1f}B"
    elif abs(n) >= 1_000_000:
        return f"${n / 1_000_000:.0f}M"
    elif abs(n) >= 1_000:
        return f"${n / 1_000:.0f}K"
    return f"${n:.0f}"


def format_pct(n: float) -> str:
    """Format a percentage value (e.g., 45.3 -> '45.3%')."""
    return f"{n:.1f}%"


def describe_config(config: dict) -> str:
    """Return a human-readable one-liner describing a compute config.

    Useful for figure subtitles and report annotations.
    Example: 'AEI v4 + MCP v4 + Microsoft | Average | Freq | National | All tasks | Auto-aug On'
    """
    datasets = ", ".join(config.get("selected_datasets", []))
    combine = config.get("combine_method", "Average")
    method = "Time" if config.get("method") == "freq" else "Value"
    geo = "National" if config.get("geo") == "nat" else "Utah"
    phys = {
        "all": "All tasks",
        "exclude": "Excl. physical",
        "only": "Physical only",
    }.get(config.get("physical_mode", "all"), "All tasks")
    aug = "Auto-aug On" if config.get("use_auto_aug") else "Auto-aug Off"

    parts = [datasets, combine, method, geo, phys, aug]
    return " | ".join(parts)
