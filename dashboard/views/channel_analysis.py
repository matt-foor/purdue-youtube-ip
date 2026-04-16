import os
from datetime import date, datetime

import pandas as pd
import streamlit as st

from dashboard.components.visualizations import (
    format_compact_int,
    graph_insight_expander,
    kpi_row,
    plotly_bar_chart,
    plotly_donut_chart,
    plotly_line_chart,
    plotly_scatter,
    section_header,
    show_plotly_chart,
    styled_dataframe,
)


BASE_DATA_DIR = os.path.join("data", "youtube api data")
CATEGORY_FILES = {
    "Research / Science": "research_science_channels_videos.csv",
    "Tech": "tech_channels_videos.csv",
    "Gaming": "gaming_channels_videos.csv",
    "Entertainment": "entertainment_channels_videos.csv",
}
ALL_LABEL = "All Categories"


def _coerce_publish_date_range(
    selection: object,
    *,
    data_min: date,
    data_max: date,
) -> tuple[date, date]:
    """Normalize ``st.date_input`` range output to an inclusive (start, end) pair.

    Range mode can return ``()``, ``(start,)``, ``(start, end)``, a bare ``date``, or a ``list``.
    Empty selection falls back to the dataset span so charts match the widget default.
    """
    if selection is None:
        return data_min, data_max
    if isinstance(selection, datetime):
        d = selection.date()
        return d, d
    if isinstance(selection, date):
        return selection, selection
    if isinstance(selection, (tuple, list)):
        dates: list[date] = []
        for item in selection:
            if item is None:
                continue
            if isinstance(item, datetime):
                dates.append(item.date())
            elif isinstance(item, date):
                dates.append(item)
        if len(dates) >= 2:
            a, b = dates[0], dates[1]
            if a > b:
                a, b = b, a
            return a, b
        if len(dates) == 1:
            d0 = dates[0]
            return d0, d0
        return data_min, data_max
    return data_min, data_max


def _filter_rows_by_publish_calendar_range(
    frame: pd.DataFrame, start: date, end: date
) -> pd.DataFrame:
    """Keep rows whose publish instant falls on a UTC calendar day in [*start*, *end*]."""
    ts = frame["video_publishedAt"]
    valid = ts.notna()
    ts_ok = ts[valid]
    if ts_ok.empty:
        return frame.iloc[0:0]
    if ts_ok.dt.tz is None:
        ts_ok = ts_ok.dt.tz_localize("UTC")
    else:
        ts_ok = ts_ok.dt.tz_convert("UTC")
    pub_day = ts_ok.dt.date
    m = valid.copy()
    m.loc[valid] = (pub_day >= start) & (pub_day <= end)
    return frame.loc[m]


def _dataset_path_for_label(label: str) -> str:
    filename = CATEGORY_FILES.get(label) or CATEGORY_FILES.get("Research / Science")
    return os.path.join(BASE_DATA_DIR, filename)


def _available_categories() -> list[str]:
    labels: list[str] = []
    for label, filename in CATEGORY_FILES.items():
        path = os.path.join(BASE_DATA_DIR, filename)
        if os.path.exists(path):
            labels.append(label)
    if labels:
        return [ALL_LABEL] + labels
    return list(CATEGORY_FILES.keys())


def _load_data_for_label(label: str) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    if label == ALL_LABEL:
        for filename in CATEGORY_FILES.values():
            path = os.path.join(BASE_DATA_DIR, filename)
            if os.path.exists(path):
                frames.append(pd.read_csv(path))
        if not frames:
            return pd.DataFrame()
        df = pd.concat(frames, ignore_index=True)
    else:
        dataset_path = _dataset_path_for_label(label)
        if not os.path.exists(dataset_path):
            return pd.DataFrame()
        df = pd.read_csv(dataset_path)

    for col in ["views", "likes", "comments"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["video_publishedAt"] = pd.to_datetime(
        df["video_publishedAt"], errors="coerce", utc=True
    )
    df["engagement_rate"] = (
        (df["likes"].fillna(0) + df["comments"].fillna(0))
        / df["views"].clip(lower=1)
    )
    df["publish_month"] = df["video_publishedAt"].dt.to_period("M").astype(str)
    df["publish_day"] = df["video_publishedAt"].dt.day_name()
    return df


def _render_engagement_formula_block() -> None:
    st.markdown("#### How Engagement Rate is Calculated")
    st.caption(
        "Engagement Rate (%) = ((Likes + Comments) / Views) * 100. "
        "If views are 0, we safely treat views as 1 to avoid divide-by-zero errors."
    )

    formula_matrix = pd.DataFrame(
        [
            {"Metric": "Likes", "Meaning": "Total likes on the video"},
            {"Metric": "Comments", "Meaning": "Total comments on the video"},
            {"Metric": "Views", "Meaning": "Total views on the video"},
            {
                "Metric": "Engagement Rate (%)",
                "Meaning": "((Likes + Comments) / Views) * 100",
            },
        ]
    )
    with st.expander("Open formula matrix", expanded=False):
        st.table(formula_matrix)


def render() -> None:
    section_header("Channel Analysis", icon="📊")

    categories = _available_categories()
    selected_category = st.selectbox("Dataset category", categories, index=0)

    st.caption(f"Analytics for `{selected_category}` YouTube channels and videos.")

    df = _load_data_for_label(selected_category)
    if df.empty:
        st.warning(
            "No data available for the selected category. Check that the CSV files exist."
        )
        return

    channels = sorted(df["channel_title"].dropna().unique().tolist())
    selected_channels = st.multiselect(
        "Filter channels", channels, default=channels[:8]
    )

    ts_min = df["video_publishedAt"].min()
    ts_max = df["video_publishedAt"].max()
    min_date = ts_min.date() if pd.notna(ts_min) else date.today()
    max_date = ts_max.date() if pd.notna(ts_max) else date.today()
    # Do not set max_value to the latest video date: choosing any window past that (e.g. next month)
    # would fail Streamlit validation and snap the widget back to the full range, so charts ignore the
    # user's range. min_value stays the dataset floor; upper bound defaults to last default +10y in Streamlit.
    date_range = st.date_input(
        "Published date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=None,
        key=f"channel_analysis_pub_range:{selected_category}",
        help="UTC publish date of each video. Narrow ranges with no uploads in this dataset will empty the charts until you widen the window.",
    )
    st.caption(
        "Filter uses each video's **UTC** calendar day. Switching dataset category resets this range to that file's span."
    )

    filtered = df.copy()
    if selected_channels:
        filtered = filtered[filtered["channel_title"].isin(selected_channels)]

    start_date, end_date = _coerce_publish_date_range(
        date_range, data_min=min_date, data_max=max_date
    )
    filtered = _filter_rows_by_publish_calendar_range(filtered, start_date, end_date)

    if filtered.empty:
        st.warning("No data after filters. Broaden your channel/date filters.")
        return

    n_videos = len(filtered)
    n_channels = int(filtered["channel_id"].nunique())
    total_views = int(filtered["views"].fillna(0).sum())
    avg_views = int(round(float(filtered["views"].fillna(0).mean())))
    med_eng_pct = float(filtered["engagement_rate"].median()) * 100

    v_c, v_full = format_compact_int(n_videos)
    ch_c, ch_full = format_compact_int(n_channels)
    tv_c, tv_full = format_compact_int(total_views)
    av_c, av_full = format_compact_int(avg_views)

    # KPI row (compact K/M/B/T; hover shows exact counts — avoid near-white value color on light cards)
    metrics = [
        {
            "label": "Videos",
            "value": v_c,
            "value_tooltip": f"{v_full} videos in this filtered set",
            "icon": "🎬",
            "color": "#FF0000",
        },
        {
            "label": "Channels",
            "value": ch_c,
            "value_tooltip": f"{ch_full} unique channels (after category, channel, and date filters)",
            "icon": "📺",
            "color": "#065FD4",
        },
        {
            "label": "Total Views",
            "value": tv_c,
            "value_tooltip": f"{tv_full} total views summed across all videos above",
            "icon": "👁️",
            "color": "#FF0000",
        },
        {
            "label": "Avg Views / Video",
            "value": av_c,
            "value_tooltip": f"{av_full} mean views per video in this slice",
            "icon": "📈",
            "color": "#1d1d1f",
        },
        {
            "label": "Typical Engagement Rate",
            "value": f"{med_eng_pct:.2f}%",
            "value_tooltip": (
                f"Median engagement {med_eng_pct:.4f}% — (likes + comments) ÷ views × 100 per video; "
                "half of videos fall below this rate and half above."
            ),
            "icon": "💡",
            "color": "#1d1d1f",
        },
    ]
    kpi_row(metrics)
    st.caption("Hover any large metric to see the **exact** number in a tooltip.")

    left, right = st.columns(2)

    with left:
        section_header("Top Channels by Views", icon="🏆")
        channel_summary = (
            filtered.groupby("channel_title", dropna=False)
            .agg(
                videos=("video_id", "count"),
                total_views=("views", "sum"),
                avg_views=("views", "mean"),
                typical_engagement_rate=("engagement_rate", "median"),
            )
            .sort_values("total_views", ascending=False)
            .head(15)
            .reset_index()
        )
        fig = plotly_bar_chart(
            channel_summary, x="channel_title", y="total_views", title="Top 15 Channels"
        )
        show_plotly_chart(fig)
        graph_insight_expander(
            "Top channels chart",
            """
**What you are looking at:** each bar is **total views** for one channel in your current filters (category, channels, date range).

**How to use it:** longer bars mean more **cumulative reach** in this window—not necessarily “better,” since a channel with fewer uploads can still have a tall bar if those videos went viral.

**Next step:** pair this with the **Channel Summary** table for upload counts and typical engagement so you do not confuse “few mega-hits” with “steady catalog strength.”
            """,
            for_insights=True,
        )
        styled_dataframe(channel_summary, title="Channel Summary")

    with right:
        section_header("Monthly Upload Trend", icon="📆")
        trend = (
            filtered.groupby("publish_month", dropna=False)
            .agg(videos=("video_id", "count"), views=("views", "sum"))
            .reset_index()
            .sort_values("publish_month")
        )
        fig = plotly_line_chart(
            trend,
            x="publish_month",
            y_cols=["videos", "views"],
            title="Videos & Views Over Time",
            secondary_y=["views"],
        )
        show_plotly_chart(fig)
        graph_insight_expander(
            "Uploads & views over time",
            """
**Red line (left scale):** how many videos were **published** each month.  
**Blue line (right scale):** **total views** attributed to uploads in that month (stack of catalog performance, not a single video’s lifetime).

**Patterns:** uploads up but views flat can mean packaging or topic fatigue; uploads down but views steady can mean older videos still pull watch time.

**Tip:** use the chart toolbar (top-right) to zoom a busy stretch of months.
            """,
            for_insights=True,
        )

    section_header("Best Performing Videos", icon="⭐")
    top_videos = filtered[
        [
            "channel_title",
            "video_title",
            "views",
            "likes",
            "comments",
            "engagement_rate",
            "video_publishedAt",
        ]
    ].sort_values("views", ascending=False)
    styled_dataframe(
        top_videos.head(50),
        title="Top Videos by Views",
        precision=2,
    )
    _render_engagement_formula_block()

    section_header("Publishing Day Performance", icon="🗓️")
    day_perf = (
        filtered.groupby("publish_day", dropna=False)
        .agg(
            videos=("video_id", "count"),
            avg_views=("views", "mean"),
            typical_engagement_rate=("engagement_rate", "median"),
        )
        .reindex(
            [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
        )
        .dropna(how="all")
        .reset_index()
    )

    col_day1, col_day2 = st.columns(2)
    with col_day1:
        fig_views = plotly_bar_chart(
            day_perf,
            x="publish_day",
            y="avg_views",
            title="Average Views by Day",
        )
        show_plotly_chart(fig_views)
        graph_insight_expander(
            "Average views by weekday",
            """
Each bar is the **mean (average) views** for videos whose **publish day** was that weekday.

**Caveat:** some weekdays have fewer uploads, so averages can jump around—treat this as a **hypothesis** for scheduling tests, not a guarantee Monday beats Friday.

**Pair with:** the engagement-by-day chart so you do not optimize for “high average views” on a day that actually has thin data.
            """,
            for_insights=True,
        )
    with col_day2:
        fig_eng = plotly_bar_chart(
            day_perf,
            x="publish_day",
            y="typical_engagement_rate",
            title="Typical Engagement Rate by Day",
        )
        show_plotly_chart(fig_eng)
        graph_insight_expander(
            "Engagement by weekday",
            """
Each bar is the **median** engagement rate (likes + comments per view) for videos published on that weekday—**not** the same as watch time or CTR.

**How to read it:** a taller bar means “typical” videos that day earned **more interaction per view** in this filtered dataset.

**Use with:** the average-views chart—a day can look great on engagement but have very few uploads, so read both together.
            """,
            for_insights=True,
        )

    section_header("Views vs Engagement", icon="📉")
    scatter_df = filtered.copy()
    fig_scatter = plotly_scatter(
        scatter_df,
        x="views",
        y="engagement_rate",
        size=None,
        color="channel_title",
        title="Views vs Engagement Rate (Log Scale)",
    )
    fig_scatter.update_traces(marker={"size": 9, "opacity": 0.65})
    fig_scatter.update_xaxes(type="log", title="Views (log scale)")
    fig_scatter.update_yaxes(title="Engagement Rate")
    show_plotly_chart(fig_scatter)
    graph_insight_expander(
        "Views vs engagement scatter",
        """
**Each dot** is one video. **Horizontal position** is view count on a **log** scale so both small creators and mega-hits fit on the same chart. **Height** is engagement rate (interaction per view).

**Color** is channel—compare how clusters separate.

**Quadrants (informal):** upper-left often means **strong engagement on modest reach** (niche or breakout candidates); lower-right can mean **huge reach with lighter interaction per view** (broad entertainment patterns).

**Reminder:** engagement here is likes + comments only; it is **not** YouTube Studio watch time or impressions.
        """,
        for_insights=True,
    )

    section_header("Engagement Distribution", icon="🥧")
    bins = []
    for val in filtered["engagement_rate"]:
        if pd.isna(val):
            continue
        pct = val * 100
        if pct < 2:
            bins.append("Low (<2%)")
        elif pct < 8:
            bins.append("Medium (2–8%)")
        else:
            bins.append("High (8%+)")
    if bins:
        counts = pd.Series(bins, name="bucket").value_counts().reset_index()
        counts.columns = ["bucket", "count"]
        dist_df = counts
        fig_donut = plotly_donut_chart(
            dist_df,
            names="bucket",
            values="count",
            title="Engagement Rate Buckets",
        )
        show_plotly_chart(fig_donut)
        graph_insight_expander(
            "Engagement distribution (donut)",
            """
Slices show the **share of videos** that fall into each engagement band: **Low** (under 2%), **Medium** (2–8%), **High** (over 8%)—using the same likes+comments÷views definition as elsewhere on this page.

**This is not “share of views.”** A thin High slice can still include some of your biggest view-getters; it only counts how many **videos** sit in each band.

**Use it:** if Low dominates, titles/thumbnails/topics may be attracting clicks without community payoff; if High grows, double down on what those videos have in common.
            """,
            for_insights=True,
        )
