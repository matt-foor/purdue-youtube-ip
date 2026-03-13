from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel


class ErrorCode(str, Enum):
    CLIP_TIMEOUT = "CLIP_TIMEOUT"
    BERTOPIC_FAILED = "BERTOPIC_FAILED"
    INVALID_CHANNEL_DATA = "INVALID_CHANNEL_DATA"
    CACHE_MISS_FETCH_FAILED = "CACHE_MISS_FETCH_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorEnvelope(BaseModel):
    error_code: ErrorCode
    message: str
    retryable: bool


class VideoData(BaseModel):
    video_id: str
    title: str
    description: str
    tags: list[str]
    published_at: str
    duration_sec: int
    view_count: int
    like_count: int
    comment_count: int
    is_short: bool
    thumbnail_url: Optional[str] = None


class ChannelData(BaseModel):
    channel_id: str
    title: str
    description: str
    subscriber_count: int
    view_count: int
    video_count: int
    country: str
    published_at: str


class ChannelPayload(BaseModel):
    channel: ChannelData
    videos: list[VideoData]
    category_hint: Optional[str] = None


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: Optional[dict[str, Any]] = None
    error: Optional[ErrorEnvelope] = None


class CreateJobResponse(BaseModel):
    job_id: str