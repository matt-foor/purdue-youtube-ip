from __future__ import annotations

from datetime import timezone
from typing import Optional

import pandas as pd

from src.constants.video_types import SHORTS_MAX_DURATION_SEC
from src.services.types_ml import ChannelData, ChannelPayload, VideoData


def build_channel_payload(
    channel_df: pd.DataFrame,
    channel_meta: dict,
    category_hint: Optional[str] = None,
) -> ChannelPayload:
    """
    converts ytuber session state into the ChannelPayload contract expected
    by the ml backend orchestrator.

    args:
        channel_df: dataframe returned by _fetch_or_get_cached_channel, after
                    _ensure_numeric_and_dates has been applied.
        channel_meta: dict with keys matching _channel_fields output:
                      channel_id, channel_title, channel_description,
                      channel_publishedAt, channel_subscriberCount,
                      channel_viewCount, channel_videoCount, channel_country
        category_hint: optional niche string (e.g. "tech"). when absent the
                       backend infers category via bertopic.

    returns:
        ChannelPayload ready for ml_backend_client.start_inference()

    raises:
        ValueError: if required columns are missing or have unexpected types
    """
    _validate_df(channel_df)

    channel: ChannelData = {
        "channel_id": str(channel_meta.get("channel_id", "") or ""),
        "title": str(channel_meta.get("channel_title", "") or ""),
        "description": str(channel_meta.get("channel_description", "") or ""),
        "subscriber_count": _safe_int(channel_meta.get("channel_subscriberCount", 0)),
        "view_count": _safe_int(channel_meta.get("channel_viewCount", 0)),
        "video_count": _safe_int(channel_meta.get("channel_videoCount", 0)),
        "country": str(channel_meta.get("channel_country", "") or ""),
        "published_at": _to_iso(channel_meta.get("channel_publishedAt", "")),
    }

    videos: list[VideoData] = []
    for _, row in channel_df.iterrows():
        vid = str(row.get("video_id") or "").strip()
        if not vid:
            continue

        duration_sec = _safe_int(row.get("duration_seconds", 0))
        is_short = bool(duration_sec < SHORTS_MAX_DURATION_SEC)

        thumbnail_url = _resolve_thumbnail(row, vid)
        published_at = _to_iso(row.get("video_publishedAt", ""))
        tags = _parse_tags(row.get("video_tags", ""))

        videos.append(
            VideoData(
                video_id=vid,
                title=str(row.get("video_title", "") or ""),
                description=str(row.get("video_description", "") or ""),
                tags=tags,
                published_at=published_at,
                duration_sec=duration_sec,
                view_count=_safe_int(row.get("views", 0)),
                like_count=_safe_int(row.get("likes", 0)),
                comment_count=_safe_int(row.get("comments", 0)),
                is_short=is_short,
                thumbnail_url=thumbnail_url,
            )
        )

    if not videos:
        raise ValueError("channel_df produced zero valid video rows")

    payload: ChannelPayload = {"channel": channel, "videos": videos}
    if category_hint and category_hint.strip():
        payload["category_hint"] = category_hint.strip().lower()

    return payload


# --- helpers ---

_REQUIRED_COLS = {"video_id", "video_title", "video_publishedAt", "duration_seconds"}


def _validate_df(df: pd.DataFrame) -> None:
    missing = _REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"channel_df missing required columns: {missing}")


def _safe_int(val) -> int:
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return 0


def _to_iso(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    if hasattr(val, "isoformat"):
        if getattr(val, "tzinfo", None) is None:
            val = val.replace(tzinfo=timezone.utc)
        return val.isoformat()
    return str(val)


def _resolve_thumbnail(row, video_id: str) -> str:
    for col in ("thumb_maxres_url", "thumb_standard_url", "thumb_high_url",
                "thumb_medium_url", "thumb_default_url"):
        url = str(row.get(col, "") or "").strip()
        if url:
            return url
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"


def _parse_tags(raw) -> list[str]:
    if isinstance(raw, list):
        return [str(t) for t in raw if t]
    if not raw or (isinstance(raw, float) and pd.isna(raw)):
        return []
    return [t.strip() for t in str(raw).split("|") if t.strip()]