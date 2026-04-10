import math
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


# Creator Insights palette aligned to YouTube red + clean blue accents.
YT_COLORWAY: List[str] = [
    "#FF0033",
    "#00A6FF",
    "#F04438",
    "#38BDF8",
    "#FB7185",
    "#1D4ED8",
    "#F97316",
]

PLOTLY_INTERACTIVE_CONFIG: Dict[str, Any] = {
    "scrollZoom": True,
    "displayModeBar": True,
    "displaylogo": False,
    "doubleClick": "reset",
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}

# Light-shell analytics template (high contrast on #f5f5f7 mesh background)
PLOTLY_DASHBOARD_TEMPLATE: Dict[str, Any] = {
    "layout": {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(255,255,255,0.96)",
        "font": {
            "color": "#1d1d1f",
            "family": "Inter, system-ui, sans-serif",
        },
        "xaxis": {
            "gridcolor": "rgba(0,0,0,0.08)",
            "zerolinecolor": "rgba(0,0,0,0.12)",
            "linecolor": "rgba(0,0,0,0.2)",
            "title": {"font": {"color": "#1d1d1f", "size": 13}},
            "tickfont": {"color": "#424245", "size": 11},
        },
        "yaxis": {
            "gridcolor": "rgba(0,0,0,0.08)",
            "zerolinecolor": "rgba(0,0,0,0.12)",
            "linecolor": "rgba(0,0,0,0.2)",
            "title": {"font": {"color": "#1d1d1f", "size": 13}},
            "tickfont": {"color": "#424245", "size": 11},
        },
        "colorway": YT_COLORWAY,
        "hoverlabel": {
            "bgcolor": "#ffffff",
            "font": {"color": "#1d1d1f"},
            "bordercolor": "rgba(0,0,0,0.12)",
        },
    }
}

# Back-compat alias
PLOTLY_LIGHT_TEMPLATE = PLOTLY_DASHBOARD_TEMPLATE


def _friendly_label(raw: str) -> str:
    """Convert snake_case / terse names into plain-English labels."""
    text = str(raw or "").strip()
    if not text:
        return ""
    aliases = {
        "publish_month": "Publish Month",
        "publish_day": "Publish Day",
        "publish_hour": "Publish Hour (UTC)",
        "video_publishedAt": "Publish Date",
        "views_per_day": "Views Per Day",
        "engagement_rate": "Engagement Rate (%)",
        "engagement_pct": "Engagement Rate (%)",
        "outlier_score": "Outlier Score",
        "channel_title": "Channel",
        "video_title": "Video Title",
        "avg_views": "Average Views",
        "total_views": "Total Views",
        "videos": "Videos",
        "keyword": "Keyword",
        "momentum_delta": "Momentum Change",
        "competitor_count": "Competitor Count",
        "log10_subscribers": "Channel Size (log10 subscribers + 1)",
    }
    if text in aliases:
        return aliases[text]
    if text.endswith("_pct"):
        text = text[:-4] + " percent"
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text.title()


def _compact_number(value: float) -> str:
    """Format large values into compact user-friendly units (K/M/B/T)."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    sign = "-" if num < 0 else ""
    n = abs(num)
    if n >= 1_000_000_000_000:
        return f"{sign}{n / 1_000_000_000_000:.1f}T"
    if n >= 1_000_000_000:
        return f"{sign}{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{sign}{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{sign}{n / 1_000:.1f}K"
    if n.is_integer():
        return f"{int(num)}"
    return f"{num:.2f}"


def _needs_compact_units(series: pd.Series) -> bool:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.dropna().empty:
        return False
    return bool(numeric.abs().max() >= 10_000)


def apply_dashboard_chart_theme(fig: go.Figure) -> go.Figure:
    """Apply shared light analytics template for dashboard Plotly figures."""
    fig.update_layout(**PLOTLY_DASHBOARD_TEMPLATE["layout"])
    fig.update_layout(
        title_font=dict(
            size=17,
            family="Inter, system-ui, sans-serif",
            color="#1d1d1f",
        ),
        legend=dict(
            bgcolor="rgba(255,255,255,0.97)",
            bordercolor="rgba(0,0,0,0.12)",
            borderwidth=1,
            font=dict(color="#1d1d1f", size=12),
            title=dict(font=dict(color="#1d1d1f", size=12)),
        ),
        margin=dict(l=16, r=16, t=72, b=68),
    )
    fig.update_xaxes(
        automargin=True,
        title_standoff=14,
        tickfont=dict(color="#111216", size=12),
        title_font=dict(color="#111216", size=14),
    )
    fig.update_yaxes(
        automargin=True,
        title_standoff=14,
        tickfont=dict(color="#111216", size=12),
        title_font=dict(color="#111216", size=14),
    )
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode="hide")
    # Secondary axes (e.g. dual-axis) — same dark ink as primary
    for axis in ("xaxis2", "yaxis2", "xaxis3", "yaxis3"):
        if getattr(fig.layout, axis, None) is not None:
            fig.update_layout(
                **{
                    axis: dict(
                        title=dict(font=dict(color="#111216", size=12)),
                        tickfont=dict(color="#111216", size=11),
                        gridcolor="rgba(0,0,0,0.08)",
                    )
                }
            )
    if getattr(fig.layout, "polar", None) is not None:
        fig.update_layout(
            polar=dict(
                bgcolor="rgba(255,255,255,0.96)",
                radialaxis=dict(
                    gridcolor="rgba(0,0,0,0.08)",
                    linecolor="rgba(0,0,0,0.2)",
                    tickfont=dict(color="#424245", size=11),
                ),
                angularaxis=dict(
                    linecolor="rgba(0,0,0,0.2)",
                    tickfont=dict(color="#424245", size=11),
                ),
            )
        )
    # Plotly table traces: force steel-glass fills (avoid default dark themes)
    for trace in fig.data:
        if getattr(trace, "type", "") == "table":
            trace.header.update(
                fill=dict(color="rgba(238, 241, 247, 0.96)"),
                line=dict(color="rgba(0,0,0,0.12)"),
                font=dict(color="#1d1d1f", size=12),
                align="left",
            )
            trace.cells.update(
                fill=dict(color="rgba(255,255,255,0.92)"),
                line=dict(color="rgba(0,0,0,0.08)"),
                font=dict(color="#1d1d1f", size=12),
                align="left",
            )
    return fig


def show_plotly_chart(fig: go.Figure, *, config: Optional[Dict[str, Any]] = None) -> None:
    """Render Plotly with pan/zoom toolbar and scroll-wheel zoom enabled."""
    merged = dict(PLOTLY_INTERACTIVE_CONFIG)
    if config:
        merged.update(config)
    st.plotly_chart(fig, use_container_width=True, config=merged)


def graph_insight_expander(chart_title: str, body_md: str, *, for_instructions: bool = False) -> None:
    """Collapsed help text: chart interpretation (`for_instructions=False`) or step-by-step (`True`)."""
    if for_instructions:
        label = f"Instructions — {chart_title}"
    else:
        label = f"How to read this chart — {chart_title}"
    with st.expander(label, expanded=False):
        st.markdown(body_md)


def styled_metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    icon: Optional[str] = None,
    color: Optional[str] = None,
) -> str:
    """Return HTML for a single glassmorphism metric card.

    Leading whitespace is avoided so Markdown does not treat the block
    as an indented code block.
    """
    color_style = f"color:{color};" if color else ""
    delta_class = ""
    if delta:
        if delta.strip().startswith(("+", "▲")):
            delta_class = "positive"
        elif delta.strip().startswith(("-", "▼")):
            delta_class = "negative"
    delta_html = (
        f'<div class="metric-delta {delta_class}">{delta}</div>' if delta else ""
    )
    html = (
        f'<div class="metric-card">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value" style="{color_style}">'
        f'{value}'
        f'</div>'
        f'{delta_html}'
        f'</div>'
    )
    return html


def kpi_row(metrics: List[Dict[str, Any]]) -> None:
    """Render a row of KPI metric cards.

    Each metric dict: {label, value, delta?, icon?, color?}
    """
    cards_html = "".join(
        styled_metric_card(
            m.get("label", ""),
            str(m.get("value", "")),
            delta=m.get("delta"),
            icon=m.get("icon"),
            color=m.get("color"),
        )
        for m in metrics
    )
    st.markdown(f'<div class="metric-row">{cards_html}</div>', unsafe_allow_html=True)


def section_header(title: str, subtitle: Optional[str] = None, icon: Optional[str] = None) -> None:
    """Render a styled text-only section header with optional subtitle."""
    st.markdown(
        f'<div class="yt-section-header"><span>{title}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="yt-section-underline"></div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(
            "<p style='color:#6e6e73;font-size:13px;line-height:1.55;font-weight:500;'>" + subtitle + "</p>",
            unsafe_allow_html=True,
        )


def animated_counter(value: float, label: str) -> None:
    """Render a simple animated counter using CSS animation."""
    st.markdown(
        f"""
        <div class="fade-in" style="margin-bottom:0.6rem;">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="font-size:32px;">{value:,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def plotly_line_chart(
    df: pd.DataFrame,
    x: str,
    y_cols: Sequence[str],
    title: str,
    secondary_y: Optional[Iterable[str]] = None,
) -> go.Figure:
    """Create a multi-line Plotly chart with optional secondary y-axis."""
    x_label = _friendly_label(x)
    line_palette = ["#FF0033", "#00A6FF", "#F04438", "#38BDF8", "#FB7185", "#1D4ED8"]
    secondary_y = set(secondary_y or [])
    if secondary_y:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        for i, col in enumerate(y_cols):
            use_secondary = col in secondary_y
            color = line_palette[i % len(line_palette)]
            fig.add_trace(
                go.Scatter(
                    x=df[x],
                    y=df[col],
                    name=_friendly_label(col),
                    mode="lines+markers",
                    line={"shape": "linear", "color": color, "width": 2.2},
                    marker={"size": 6, "color": color},
                ),
                secondary_y=use_secondary,
            )
        fig.update_xaxes(title_text=x_label)
        fig.update_yaxes(title_text=_friendly_label(y_cols[0]), secondary_y=False)
        if len(y_cols) > 1:
            fig.update_yaxes(title_text=_friendly_label(y_cols[-1]), secondary_y=True)
        primary_cols = [c for c in y_cols if c not in secondary_y]
        secondary_cols = [c for c in y_cols if c in secondary_y]
        if any(_needs_compact_units(df[c]) for c in primary_cols if c in df.columns):
            fig.update_yaxes(tickformat="~s", secondary_y=False)
        if any(_needs_compact_units(df[c]) for c in secondary_cols if c in df.columns):
            fig.update_yaxes(tickformat="~s", secondary_y=True)
    else:
        fig = go.Figure()
        for i, col in enumerate(y_cols):
            color = line_palette[i % len(line_palette)]
            fig.add_trace(
                go.Scatter(
                    x=df[x],
                    y=df[col],
                    name=_friendly_label(col),
                    mode="lines+markers",
                    line={"shape": "linear", "color": color, "width": 2.2},
                    marker={"size": 6, "color": color},
                )
            )
        fig.update_xaxes(title_text=x_label)
        fig.update_yaxes(title_text=", ".join(_friendly_label(c) for c in y_cols))
        if any(_needs_compact_units(df[c]) for c in y_cols if c in df.columns):
            fig.update_yaxes(tickformat="~s")

    fig.update_layout(title=title, height=500)
    apply_dashboard_chart_theme(fig)
    return fig


def plotly_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    horizontal: bool = False,
) -> go.Figure:
    """Create a bar chart with red → cyan emphasis (Creator Insights charts)."""
    bar_line = dict(color="rgba(255,255,255,0.12)", width=0.8)
    _bar_cs = [[0, "rgba(255,0,0,0.35)"], [0.5, "#FF0000"], [1, "#00D4FF"]]
    x_label = _friendly_label(x)
    y_label = _friendly_label(y)
    numeric_values = pd.to_numeric(df[y], errors="coerce").fillna(0)
    compact_values = [_compact_number(v) for v in numeric_values.tolist()]
    if horizontal:
        fig = go.Figure(
            go.Bar(
                x=df[y],
                y=df[x],
                orientation="h",
                marker=dict(color=df[y], colorscale=_bar_cs, line=bar_line),
                text=compact_values,
                customdata=compact_values,
                texttemplate="%{text}",
                textposition="outside",
                textfont=dict(size=12, color="#1d1d1f"),
                cliponaxis=False,
                hovertemplate=f"{x_label}: %{{y}}<br>{y_label}: %{{customdata}}<extra></extra>",
            )
        )
        fig.update_xaxes(title_text=y_label)
        fig.update_yaxes(title_text=x_label)
        if _needs_compact_units(numeric_values):
            fig.update_xaxes(tickformat="~s")
    else:
        fig = go.Figure(
            go.Bar(
                x=df[x],
                y=df[y],
                marker=dict(color=df[y], colorscale=_bar_cs, line=bar_line),
                text=compact_values,
                customdata=compact_values,
                texttemplate="%{text}",
                textposition="outside",
                textfont=dict(size=12, color="#1d1d1f"),
                cliponaxis=False,
                hovertemplate=f"{x_label}: %{{x}}<br>{y_label}: %{{customdata}}<extra></extra>",
            )
        )
        fig.update_xaxes(title_text=x_label)
        fig.update_yaxes(title_text=y_label)
        if _needs_compact_units(numeric_values):
            fig.update_yaxes(tickformat="~s")
    fig.update_layout(title=title)
    apply_dashboard_chart_theme(fig)
    return fig


def plotly_donut_chart(
    df: pd.DataFrame,
    names: str,
    values: str,
    title: str,
) -> go.Figure:
    """Create a donut chart with center label."""
    fig = px.pie(
        df,
        names=names,
        values=values,
        hole=0.55,
        color_discrete_sequence=YT_COLORWAY,
        labels={names: _friendly_label(names), values: _friendly_label(values)},
    )
    fig.update_traces(
        textposition="outside",
        texttemplate="%{label}<br>%{percent}",
        textfont=dict(size=13, color="#1d1d1f"),
        marker=dict(line=dict(color="rgba(255,255,255,0.95)", width=1.2)),
        hovertemplate=f"{_friendly_label(names)}: %{{label}}<br>{_friendly_label(values)}: %{{value:~s}}<extra></extra>",
    )
    fig.update_layout(title=title, showlegend=True)
    apply_dashboard_chart_theme(fig)
    return fig


def plotly_heatmap(
    df: pd.DataFrame,
    x: str,
    y: str,
    z: str,
    title: str,
) -> go.Figure:
    """Create a heatmap from tall-form data with x, y, z columns."""
    pivot = df.pivot(index=y, columns=x, values=z)
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale="Viridis",
            colorbar=dict(
                title=_friendly_label(z),
                tickfont=dict(color="#424245"),
                title_font=dict(color="#1d1d1f", size=12),
            ),
        )
    )
    fig.update_layout(title=title)
    fig.update_xaxes(title_text=_friendly_label(x))
    fig.update_yaxes(title_text=_friendly_label(y))
    apply_dashboard_chart_theme(fig)
    return fig


def plotly_radar_chart(
    categories: Sequence[str],
    series: Dict[str, Sequence[float]],
    title: str,
) -> go.Figure:
    """Create a radar / spider chart for competitor comparison."""
    fig = go.Figure()
    for name, values in series.items():
        vals = list(values)
        if vals and vals[0] != vals[-1]:
            vals.append(vals[0])
        cats = list(categories)
        if cats and cats[0] != cats[-1]:
            cats.append(cats[0])
        fig.add_trace(go.Scatterpolar(r=vals, theta=cats, fill="toself", name=name))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True)), title=title)
    apply_dashboard_chart_theme(fig)
    return fig


def plotly_gauge_chart(
    value: float,
    title: str,
    max_val: float = 100,
) -> go.Figure:
    """Create a circular gauge for scoring."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            gauge={
                "axis": {"range": [0, max_val]},
                "bar": {"color": "#FF0000"},
                "steps": [
                    {"range": [0, max_val * 0.5], "color": "rgba(0,0,0,0.06)"},
                    {"range": [max_val * 0.5, max_val * 0.8], "color": "rgba(0,119,237,0.12)"},
                    {"range": [max_val * 0.8, max_val], "color": "rgba(255,0,0,0.18)"},
                ],
            },
            title={"text": title},
        )
    )
    apply_dashboard_chart_theme(fig)
    return fig


def plotly_scatter(
    df: pd.DataFrame,
    x: str,
    y: str,
    size: Optional[str],
    color: Optional[str],
    title: str,
    *,
    log_x: bool = False,
    enhanced_markers: bool = False,
) -> go.Figure:
    """Create a scatter plot with optional log-scaled X and clearer markers."""
    hover_cols = [c for c in ("channel_title", "video_title") if c in df.columns]
    color_kw: Dict[str, Any] = {}
    if color and color in df.columns:
        color_kw["color"] = color
        color_kw["color_discrete_sequence"] = YT_COLORWAY
    fig = px.scatter(
        df,
        x=x,
        y=y,
        size=size if size in df.columns else None,
        hover_data=hover_cols if hover_cols else None,
        labels={
            x: _friendly_label(x),
            y: _friendly_label(y),
            size: _friendly_label(size) if size else "",
            color: _friendly_label(color) if color else "",
        },
        **color_kw,
    )
    fig.update_layout(title=title)
    apply_dashboard_chart_theme(fig)
    if log_x:
        fig.update_xaxes(type="log", title=f"{_friendly_label(x)} (log scale)")
    else:
        fig.update_xaxes(title=_friendly_label(x))
    fig.update_yaxes(title=_friendly_label(y))
    if x in df.columns and _needs_compact_units(df[x]):
        fig.update_xaxes(tickformat="~s")
    if y in df.columns and _needs_compact_units(df[y]):
        fig.update_yaxes(tickformat="~s")
    if enhanced_markers:
        fig.update_traces(
            marker=dict(size=14, opacity=0.9, line=dict(width=1.2, color="rgba(255,255,255,0.25)")),
        )
    return fig


def plotly_treemap(
    df: pd.DataFrame,
    path: Sequence[str],
    values: str,
    title: str,
) -> go.Figure:
    """Create a treemap for keyword intelligence."""
    fig = px.treemap(
        df,
        path=path,
        values=values,
        color=values,
        color_continuous_scale=["rgba(255,0,0,0.2)", "#FF0000", "#00D4FF"],
        labels={values: _friendly_label(values)},
    )
    fig.update_layout(title=title)
    fig.update_traces(
        textfont=dict(size=13, color="#1d1d1f"),
        texttemplate="%{label}<br>%{value:~s}",
    )
    apply_dashboard_chart_theme(fig)
    return fig


def plotly_funnel_chart(
    stages: Sequence[str],
    values: Sequence[float],
    title: str,
) -> go.Figure:
    """Create a funnel chart for content pipeline stages."""
    fig = go.Figure(
        go.Funnel(
            y=list(stages),
            x=list(values),
            textinfo="text+percent initial",
            text=[_compact_number(v) for v in values],
            textfont=dict(size=13, color="#1d1d1f"),
            hovertemplate="Stage: %{y}<br>Value: %{x:~s}<extra></extra>",
        )
    )
    fig.update_layout(title=title)
    fig.update_xaxes(title_text="Value")
    fig.update_yaxes(title_text="Stage")
    apply_dashboard_chart_theme(fig)
    return fig


def styled_dataframe(
    df: pd.DataFrame,
    title: Optional[str] = None,
    precision: int = 1,
    image_columns: Optional[Sequence[str]] = None,
) -> None:
    """Render a styled dataframe with gradients on numeric columns.

    Args:
        df: DataFrame to render.
        title: Optional title shown above the table.
        precision: Decimal precision for numeric columns.
        image_columns: Optional list of columns that should display images if URLs.
    """
    if df.empty:
        st.info("No rows to display.")
        return

    if title:
        st.markdown(f"**{title}**", unsafe_allow_html=True)

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    styler = (
        df.style.format(precision=precision)
        .set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [
                        ("background", "linear-gradient(180deg, rgba(238,241,247,0.98), rgba(226,230,238,0.95))"),
                        ("color", "#1d1d1f"),
                        ("font-weight", "700"),
                        ("border", "1px solid rgba(0,0,0,0.12)"),
                    ],
                },
                {
                    "selector": "td",
                    "props": [
                        ("background", "rgba(255,255,255,0.9)"),
                        ("color", "#1d1d1f"),
                        ("border", "1px solid rgba(0,0,0,0.08)"),
                    ],
                },
            ]
        )
        .set_properties(
            **{
                "background-color": "rgba(255,255,255,0.9)",
                "color": "#1d1d1f",
                "border-color": "rgba(0,0,0,0.08)",
            }
        )
    )
    if len(numeric_cols) > 0:
        # Subtle in-cell magnitude cue that keeps the steel-glass background light.
        styler = styler.bar(subset=numeric_cols, color="#dbe6ff", align="left")

    # Use Streamlit's native image column config when requested
    column_config: Dict[str, Any] = {}
    if image_columns:
        for col in image_columns:
            if col in df.columns:
                column_config[col] = st.column_config.ImageColumn(col)

    try:
        st.dataframe(
            styler,
            use_container_width=True,
            hide_index=True,
            column_config=column_config or None,
        )
    except Exception:
        # Styled DataFrames use Arrow; a broken/missing pyarrow install (common on Windows) still shows data.
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config or None,
        )


def styled_keyword_chips(keywords: Sequence[str]) -> None:
    """Render a set of keywords as styled chips."""
    chips = "".join(f'<span class="keyword-chip">{kw}</span>' for kw in keywords)
    st.markdown(chips, unsafe_allow_html=True)
