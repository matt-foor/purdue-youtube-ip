from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence

import pandas as pd

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except Exception:  # pragma: no cover
    build = None
    HttpError = Exception


CHANNEL_METRICS_FULL = [
    "views",
    "estimatedMinutesWatched",
    "averageViewDuration",
    "averageViewPercentage",
    "subscribersGained",
    "subscribersLost",
    "videoThumbnailImpressions",
    "videoThumbnailImpressionsClickRate",
]
CHANNEL_METRICS_FALLBACK = [
    "views",
    "estimatedMinutesWatched",
    "averageViewDuration",
    "averageViewPercentage",
    "subscribersGained",
    "subscribersLost",
]
VIDEO_METRICS_FULL = [
    "views",
    "likes",
    "comments",
    "estimatedMinutesWatched",
    "averageViewDuration",
    "averageViewPercentage",
    "videoThumbnailImpressions",
    "videoThumbnailImpressionsClickRate",
]
VIDEO_METRICS_FALLBACK = [
    "views",
    "likes",
    "comments",
    "estimatedMinutesWatched",
    "averageViewDuration",
    "averageViewPercentage",
]


@dataclass(frozen=True)
class OwnerAnalyticsBundle:
    available: bool
    owned_channels: List[Dict[str, Any]]
    summary: Dict[str, Any]
    daily_metrics_df: pd.DataFrame
    video_metrics_df: pd.DataFrame
    available_metrics: List[str]
    missing_metrics: List[str]
    note: str = ""


def _analytics_client(credentials):
    if build is None:
        raise RuntimeError(
            "Missing dependency: google-api-python-client. Install with: python3 -m pip install google-api-python-client"
        )
    return build("youtubeAnalytics", "v2", credentials=credentials, cache_discovery=False)


def _youtube_client(credentials):
    if build is None:
        raise RuntimeError(
            "Missing dependency: google-api-python-client. Install with: python3 -m pip install google-api-python-client"
        )
    return build("youtube", "v3", credentials=credentials, cache_discovery=False)


def _call_with_backoff(fn, max_retries: int = 5):
    delay = 1.0
    last_exc: Optional[Exception] = None
    for _ in range(max_retries):
        try:
            return fn()
        except HttpError as exc:
            last_exc = exc
            status = getattr(exc.resp, "status", None)
            if status in (401, 403, 429, 500, 503):
                time.sleep(delay)
                delay = min(delay * 2, 16)
                continue
            raise
        except Exception as exc:
            last_exc = exc
            time.sleep(delay)
            delay = min(delay * 2, 16)
    raise RuntimeError(f"Google API request failed after retries: {last_exc}") from last_exc


def list_owned_channels(credentials) -> List[Dict[str, Any]]:
    youtube = _youtube_client(credentials)
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics,brandingSettings",
        mine=True,
        maxResults=50,
    )
    response = _call_with_backoff(request.execute)
    rows: List[Dict[str, Any]] = []
    for item in response.get("items", []):
        snippet = item.get("snippet", {}) or {}
        branding = (item.get("brandingSettings") or {}).get("channel", {}) or {}
        statistics = item.get("statistics", {}) or {}
        rows.append(
            {
                "channel_id": item.get("id", ""),
                "channel_title": snippet.get("title", ""),
                "canonical_url": f"https://www.youtube.com/channel/{item.get('id', '')}",
                "custom_url": snippet.get("customUrl", ""),
                "handle": branding.get("customUrl", "") or snippet.get("customUrl", ""),
                "subscriber_count": float(statistics.get("subscriberCount", 0) or 0),
                "video_count": float(statistics.get("videoCount", 0) or 0),
            }
        )
    return rows


def _query_report(
    analytics,
    *,
    metrics: Sequence[str],
    start_date: date,
    end_date: date,
    dimensions: Optional[str] = None,
    filters: Optional[str] = None,
    sort: Optional[str] = None,
    max_results: Optional[int] = None,
) -> pd.DataFrame:
    params: Dict[str, Any] = dict(
        ids="channel==MINE",
        startDate=start_date.isoformat(),
        endDate=end_date.isoformat(),
        metrics=",".join(metrics),
    )
    if dimensions:
        params["dimensions"] = dimensions
    if filters:
        params["filters"] = filters
    if sort:
        params["sort"] = sort
    if max_results:
        params["maxResults"] = max_results
    request = analytics.reports().query(**params)
    response = _call_with_backoff(request.execute)
    headers = [column.get("name", "") for column in response.get("columnHeaders", [])]
    rows = response.get("rows", []) or []
    if not headers:
        headers = list(dimensions.split(",")) if dimensions else []
        headers.extend(metrics)
    frame = pd.DataFrame(rows, columns=headers)
    for column in frame.columns:
        if column == "day" or column == "video":
            continue
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def _query_with_fallback(
    analytics,
    *,
    primary_metrics: Sequence[str],
    fallback_metrics: Sequence[str],
    start_date: date,
    end_date: date,
    dimensions: Optional[str] = None,
    filters: Optional[str] = None,
    sort: Optional[str] = None,
    max_results: Optional[int] = None,
) -> tuple[pd.DataFrame, List[str], List[str]]:
    try:
        frame = _query_report(
            analytics,
            metrics=primary_metrics,
            start_date=start_date,
            end_date=end_date,
            dimensions=dimensions,
            filters=filters,
            sort=sort,
            max_results=max_results,
        )
        return frame, list(primary_metrics), []
    except Exception:
        frame = _query_report(
            analytics,
            metrics=fallback_metrics,
            start_date=start_date,
            end_date=end_date,
            dimensions=dimensions,
            filters=filters,
            sort=sort,
            max_results=max_results,
        )
        missing = [metric for metric in primary_metrics if metric not in fallback_metrics]
        return frame, list(fallback_metrics), missing


def _safe_float(row: Dict[str, Any], key: str) -> float:
    value = row.get(key, 0)
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def _chunked(values: Sequence[str], size: int) -> Iterable[List[str]]:
    for index in range(0, len(values), size):
        chunk = [value for value in values[index : index + size] if value]
        if chunk:
            yield chunk


def _fetch_video_metrics(
    analytics,
    *,
    video_ids: Sequence[str],
    start_date: date,
    end_date: date,
) -> tuple[pd.DataFrame, List[str], List[str]]:
    frames: List[pd.DataFrame] = []
    available_metrics: List[str] = []
    missing_metrics: List[str] = []

    for chunk in _chunked(list(dict.fromkeys(video_ids)), 25):
        frame, available, missing = _query_with_fallback(
            analytics,
            primary_metrics=VIDEO_METRICS_FULL,
            fallback_metrics=VIDEO_METRICS_FALLBACK,
            start_date=start_date,
            end_date=end_date,
            dimensions="video",
            filters=f"video=={','.join(chunk)}",
            sort="-views",
            max_results=len(chunk),
        )
        frames.append(frame)
        if not available_metrics:
            available_metrics = available
            missing_metrics = missing

    if not frames:
        return pd.DataFrame(), available_metrics, missing_metrics

    video_df = pd.concat(frames, ignore_index=True)
    if "video" in video_df.columns:
        video_df = video_df.rename(columns={"video": "video_id"})
    return video_df, available_metrics, missing_metrics


def fetch_owner_channel_analytics(
    credentials,
    *,
    target_channel_id: str,
    video_ids: Sequence[str],
    window_days: int = 28,
) -> OwnerAnalyticsBundle:
    owned_channels = list_owned_channels(credentials)
    owned_ids = {row["channel_id"] for row in owned_channels}
    if target_channel_id not in owned_ids:
        return OwnerAnalyticsBundle(
            available=False,
            owned_channels=owned_channels,
            summary={},
            daily_metrics_df=pd.DataFrame(),
            video_metrics_df=pd.DataFrame(),
            available_metrics=[],
            missing_metrics=[],
            note="The connected Google account does not own the tracked channel, so owner-only metrics are unavailable.",
        )

    analytics = _analytics_client(credentials)
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=max(window_days - 1, 1))

    summary_df, summary_metrics, summary_missing = _query_with_fallback(
        analytics,
        primary_metrics=CHANNEL_METRICS_FULL,
        fallback_metrics=CHANNEL_METRICS_FALLBACK,
        start_date=start_date,
        end_date=end_date,
    )
    daily_df, daily_metrics, daily_missing = _query_with_fallback(
        analytics,
        primary_metrics=CHANNEL_METRICS_FULL,
        fallback_metrics=CHANNEL_METRICS_FALLBACK,
        start_date=start_date,
        end_date=end_date,
        dimensions="day",
        sort="day",
    )
    video_df, video_metrics, video_missing = _fetch_video_metrics(
        analytics,
        video_ids=video_ids,
        start_date=start_date,
        end_date=end_date,
    )

    summary_row = summary_df.iloc[0].to_dict() if not summary_df.empty else {}
    summary = {
        "window_days": window_days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "views": _safe_float(summary_row, "views"),
        "estimated_minutes_watched": _safe_float(summary_row, "estimatedMinutesWatched"),
        "estimated_watch_hours": _safe_float(summary_row, "estimatedMinutesWatched") / 60.0,
        "average_view_duration_seconds": _safe_float(summary_row, "averageViewDuration"),
        "average_view_percentage": _safe_float(summary_row, "averageViewPercentage"),
        "subscribers_gained": _safe_float(summary_row, "subscribersGained"),
        "subscribers_lost": _safe_float(summary_row, "subscribersLost"),
        "video_thumbnail_impressions": _safe_float(summary_row, "videoThumbnailImpressions"),
        "video_thumbnail_impressions_click_rate": _safe_float(summary_row, "videoThumbnailImpressionsClickRate"),
    }

    available_metrics = list(dict.fromkeys(summary_metrics + daily_metrics + video_metrics))
    missing_metrics = list(dict.fromkeys(summary_missing + daily_missing + video_missing))
    note = ""
    if missing_metrics:
        note = (
            "Some owner metrics were not returned by the YouTube Analytics query and the app fell back to a smaller supported metric set: "
            + ", ".join(missing_metrics)
        )

    return OwnerAnalyticsBundle(
        available=True,
        owned_channels=owned_channels,
        summary=summary,
        daily_metrics_df=daily_df,
        video_metrics_df=video_df,
        available_metrics=available_metrics,
        missing_metrics=missing_metrics,
        note=note,
    )
