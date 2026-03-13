from __future__ import annotations

import os
import time
from typing import Optional

import requests

from src.services.types_ml import ChannelPayload, InferenceResult

_URL = os.environ.get("ML_BACKEND_URL", "http://localhost:8000")
_KEY = os.environ.get("ML_BACKEND_API_KEY", "")
_DRY_RUN = os.environ.get("ML_DRY_RUN", "").lower() == "true"
_TIMEOUT = int(os.environ.get("ML_BACKEND_TIMEOUT", "30"))

_HEADERS = {
    "X-API-Key": _KEY,
    "Content-Type": "application/json",
}

_DRY_RUN_JOB_ID = "dry_run_job"


def start_inference(payload: ChannelPayload) -> str:
    if _DRY_RUN:
        return _DRY_RUN_JOB_ID

    resp = requests.post(
        f"{_URL}/jobs/channel-inference",
        json=payload,
        headers=_HEADERS,
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["job_id"]


def get_job_status(job_id: str) -> dict:
    if _DRY_RUN:
        return {"status": "done", "result": _dry_run_fixture(), "error": None}

    resp = requests.get(
        f"{_URL}/jobs/{job_id}",
        headers=_HEADERS,
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def get_status() -> dict:
    if _DRY_RUN:
        return {"service_status": "ok", "queue_depth": 0}

    resp = requests.get(f"{_URL}/status", timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def poll_until_done(
    job_id: str,
    *,
    poll_interval: float = 2.0,
    on_waiting: Optional[callable] = None,
) -> Optional[InferenceResult]:
    """
    blocking poll — intended for use outside of streamlit (e.g. tests).
    for streamlit, use st.fragment-based polling instead.

    returns result dict on success, None on failure.
    sets last error in the returned dict on failure.
    """
    while True:
        resp = get_job_status(job_id)
        status = resp.get("status")
        if status == "done":
            return resp.get("result")
        if status == "failed":
            return None
        if on_waiting:
            on_waiting(resp)
        time.sleep(poll_interval)


def retry_if_retryable(job_id: str, error: dict) -> Optional[str]:
    """
    if error.retryable is true, starts a fresh job using the stored payload.
    caller is responsible for re-supplying payload — this only handles the
    http retry of an already-submitted payload.

    not used directly in the polling loop; consumers call this explicitly.
    """
    return None  # placeholder — actual retry is handled in the streamlit layer


# --- dry-run fixture ---

def _dry_run_fixture() -> dict:
    return {
        "computed_at": "2026-03-12T00:00:00+00:00",
        "channel_tier": "full",
        "topics": {
            "coverage_summary": {
                "total_topics": 5,
                "top_topics": [
                    {"topic_id": 18, "topic_label": "engineering real engineering", "share": 0.42},
                    {"topic_id": 6, "topic_label": "planets planet exoplanets nasa", "share": 0.31},
                ],
                "category": "research_science",
            },
            "by_video": [],
        },
        "gaps": {
            "tier": "full",
            "topics": [
                {
                    "topic_id": 49,
                    "topic_label": "nuclear fusion science news",
                    "gap_score": 0.71,
                    "reach_score": 0.68,
                    "trend_score": 0.74,
                    "trajectory_score": 0.55,
                    "engagement_score": 0.62,
                    "median_views": 928033,
                    "trend_raw": 52.19,
                    "trend_recent": 65.59,
                    "trajectory": 1.26,
                    "trajectory_label": "rising",
                    "median_like_rate": 0.038,
                    "video_count": 191,
                    "category": "research_science",
                    "predicted_views_per_day": 4800.0,
                    "is_short_recommended": False,
                },
            ],
        },
        "time_windows": {
            "best_hour_utc": 15,
            "best_dow": "sunday",
            "top_hours_utc": [15, 14, 16],
            "top_days": ["sunday", "saturday", "wednesday"],
            "cadence_videos_per_week_recommended": 0.75,
            "cadence_interpretation": "higher cadence associated with better performance (controlling for channel size)",
        },
        "title_patterns": {"by_topic": {}},
        "thumbnail_blueprint": {
            "source": "niche",
            "axes": [
                {
                    "axis": "high_production_value",
                    "channel_score": 0.48,
                    "blueprint_score": 0.52,
                    "correlation": 0.12,
                    "direction": "positive",
                    "recommendation": "increase production value cues in thumbnail",
                },
            ],
        },
        "ai_sections": {
            "overview": "Dry-run mode: ml analysis disabled.",
            "topic_recommendations": "Dry-run mode: topic recommendations disabled.",
            "thumbnail_advice": "Dry-run mode: thumbnail advice disabled.",
            "publish_time_advice": "Dry-run mode: publish time advice disabled.",
        },
    }