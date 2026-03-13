from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter

from src.api.worker import queue_depth
from src.jobs.job_store import _get_db

router = APIRouter()

_GCS_BUCKET = os.environ.get("GCS_BUCKET", "")


def _artifact_timestamps() -> dict:
    if not _GCS_BUCKET:
        return {}
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(_GCS_BUCKET)
        blobs = {
            "bertopic": "models/bertopic_model/",
            "xgboost_longform": "models/xgboost_longform.json",
            "xgboost_shorts": "models/xgboost_shorts.json",
            "clip": "models/niche_blueprints.json",
        }
        timestamps = {}
        for name, prefix in blobs.items():
            try:
                blob = next(iter(client.list_blobs(bucket, prefix=prefix, max_results=1)), None)
                if blob:
                    timestamps[name] = blob.updated.isoformat() if blob.updated else None
            except Exception:
                timestamps[name] = None
        return timestamps
    except Exception:
        return {}


def _last_retrain() -> dict | None:
    try:
        db = _get_db()
        docs = (
            db.collection("retrain_records")
            .order_by("started_at", direction="DESCENDING")
            .limit(1)
            .stream()
        )
        for doc in docs:
            return doc.to_dict()
        return None
    except Exception:
        return None


def _service_status(artifacts: dict, last_retrain: dict | None) -> str:
    if not artifacts:
        return "degraded"
    now = datetime.now(timezone.utc)
    for ts in artifacts.values():
        if ts:
            try:
                age_h = (now - datetime.fromisoformat(ts)).total_seconds() / 3600
                if age_h > 48:
                    return "degraded"
            except Exception:
                pass
    return "ok"


@router.get("/status")
def get_status() -> dict:
    artifacts = _artifact_timestamps()
    last_retrain = _last_retrain()
    return {
        "service_status": _service_status(artifacts, last_retrain),
        "queue_depth": queue_depth(),
        "artifacts": artifacts,          # key is "artifacts" — matches frontend
        "last_retrain": last_retrain,
    }