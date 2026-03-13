from typing import List, Optional, TypedDict


class VideoData(TypedDict):
    video_id: str
    title: str
    description: str
    tags: List[str]
    published_at: str
    duration_sec: int
    view_count: int
    like_count: int
    comment_count: int
    is_short: bool
    thumbnail_url: str


class ChannelData(TypedDict):
    channel_id: str
    title: str
    description: str
    subscriber_count: int
    view_count: int
    video_count: int
    country: str
    published_at: str


class ChannelPayload(TypedDict, total=False):
    channel: ChannelData
    videos: List[VideoData]
    category_hint: str


# --- inference result sub-types ---

class TopicCoverage(TypedDict):
    total_topics: int
    top_topics: List[dict]


class TopicsResult(TypedDict):
    coverage_summary: TopicCoverage
    by_video: List[dict]


class GapTopic(TypedDict):
    topic_id: int
    topic_label: str
    gap_score: float
    reach_score: float
    trend_score: float
    trajectory_score: float
    engagement_score: float
    median_views: int
    trend_raw: float
    trend_recent: float
    trajectory: float
    trajectory_label: str
    median_like_rate: float
    video_count: int
    category: str
    predicted_views_per_day: float
    is_short_recommended: bool


class GapsResult(TypedDict):
    topics: List[GapTopic]
    tier: str


class TimeWindows(TypedDict):
    best_hour_utc: int
    best_dow: str
    top_hours_utc: List[int]
    top_days: List[str]
    cadence_videos_per_week_recommended: float
    cadence_interpretation: str


class TitlePatterns(TypedDict):
    by_topic: dict


class ThumbnailAxis(TypedDict):
    axis: str
    channel_score: float
    blueprint_score: float
    correlation: float
    direction: str
    recommendation: str


class ThumbnailBlueprint(TypedDict):
    axes: List[ThumbnailAxis]
    source: str


class AiSections(TypedDict):
    overview: str
    topic_recommendations: str
    thumbnail_advice: str
    publish_time_advice: str


class InferenceResult(TypedDict):
    computed_at: str
    channel_tier: str
    topics: TopicsResult
    gaps: GapsResult
    time_windows: TimeWindows
    title_patterns: TitlePatterns
    thumbnail_blueprint: ThumbnailBlueprint
    ai_sections: AiSections