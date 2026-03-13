import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from google.cloud import firestore

from src.api.schemas import ErrorEnvelope, JobStatus

INFERENCE_CACHE_TTL_HOURS = int(os.environ.get("INFERENCE_CACHE_TTL_HOURS", 24))
CHANNEL_SIG_N_VIDEOS = 50

_db: Optional[firestore.Client] = None


def _get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client()
    return _db


def _channel_signature(channel_data: dict) -> str:
    videos = sorted(
        channel_data["videos"],
        key=lambda v: v["published_at"],
        reverse=True,
    )[:CHANNEL_SIG_N_VIDEOS]
    sig = [(v["video_id"], v["published_at"]) for v in videos]
    return hashlib.sha256(json.dumps(sig).encode()).hexdigest()[:16]


def get_cache_key(channel_data: dict) -> str:
    cid = channel_data["channel"]["channel_id"]
    sig = _channel_signature(channel_data)
    return f"{cid}_{sig}"


def _latest_retrain_ts(db: firestore.Client) -> Optional[datetime]:
    try:
        doc = db.collection("retrain_records").order_by(
            "finished_at", direction=firestore.Query.DESCENDING
        ).limit(1).get()
        if doc:
            return doc[0].to_dict().get("finished_at")
    except Exception:
        pass
    return None


def check_cache(channel_data: dict) -> Optional[dict]:
    db = _get_db()
    key = get_cache_key(channel_data)
    doc = db.collection("inference_cache").document(key).get()
    if not doc.exists:
        return None

    cached = doc.to_dict()
    computed_at = cached.get("computed_at")
    if not computed_at:
        return None

    now = datetime.now(timezone.utc)
    if isinstance(computed_at, str):
        computed_at = datetime.fromisoformat(computed_at)
    if computed_at.tzinfo is None:
        computed_at = computed_at.replace(tzinfo=timezone.utc)

    ttl_ok = computed_at > now - timedelta(hours=INFERENCE_CACHE_TTL_HOURS)
    if not ttl_ok:
        return None

    retrain_ts = _latest_retrain_ts(db)
    if retrain_ts:
        if retrain_ts.tzinfo is None:
            retrain_ts = retrain_ts.replace(tzinfo=timezone.utc)
        if computed_at < retrain_ts:
            return None

    return cached.get("result")


def write_cache(channel_data: dict, result: dict) -> None:
    db = _get_db()
    key = get_cache_key(channel_data)
    now = datetime.now(timezone.utc)
    db.collection("inference_cache").document(key).set({
        "channel_id": channel_data["channel"]["channel_id"],
        "computed_at": now.isoformat(),
        "ttl_expires_at": (now + timedelta(hours=INFERENCE_CACHE_TTL_HOURS)).isoformat(),
        "result": result,
    })


def create_job(job_id: str, channel_id: str) -> None:
    db = _get_db()
    now = datetime.now(timezone.utc).isoformat()
    db.collection("inference_jobs").document(job_id).set({
        "status": JobStatus.PENDING,
        "channel_id": channel_id,
        "created_at": now,
        "updated_at": now,
        "result": None,
        "error": None,
    })


def create_job_done(job_id: str, channel_id: str, result: dict) -> None:
    db = _get_db()
    now = datetime.now(timezone.utc).isoformat()
    db.collection("inference_jobs").document(job_id).set({
        "status": JobStatus.DONE,
        "channel_id": channel_id,
        "created_at": now,
        "updated_at": now,
        "result": result,
        "error": None,
    })


def set_job_running(job_id: str) -> None:
    db = _get_db()
    db.collection("inference_jobs").document(job_id).update({
        "status": JobStatus.RUNNING,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })


def set_job_done(job_id: str, result: dict) -> None:
    db = _get_db()
    db.collection("inference_jobs").document(job_id).update({
        "status": JobStatus.DONE,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "result": result,
    })


def set_job_failed(job_id: str, error: ErrorEnvelope) -> None:
    db = _get_db()
    db.collection("inference_jobs").document(job_id).update({
        "status": JobStatus.FAILED,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "error": error.model_dump(),
    })


def get_job(job_id: str) -> Optional[dict]:
    db = _get_db()
    doc = db.collection("inference_jobs").document(job_id).get()
    return doc.to_dict() if doc.exists else None