import json
import tempfile
from functools import lru_cache
from pathlib import Path

import pandas as pd
import xgboost as xgb
from bertopic import BERTopic
from google.cloud import storage

MODEL_ROOT = Path(__file__).parent.parent.parent / "outputs" / "models"


def _is_gcs(path: str) -> bool:
    return str(path).startswith("gs://")


def _download_gcs(gcs_path: str, suffix: str) -> Path:
    client = storage.Client()
    bucket_name, blob_path = gcs_path[5:].split("/", 1)
    blob = client.bucket(bucket_name).blob(blob_path)
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    blob.download_to_filename(tmp.name)
    return Path(tmp.name)


def _resolve(relative: str, suffix: str) -> Path:
    env_root = __import__("os").environ.get("MODEL_ROOT")
    root = Path(env_root) if env_root else MODEL_ROOT
    full = str(root / relative)
    if _is_gcs(full):
        return _download_gcs(full, suffix)
    return Path(full)


@lru_cache(maxsize=1)
def load_bertopic_model() -> BERTopic:
    return BERTopic.load(str(_resolve("bertopic_model", "")))


@lru_cache(maxsize=1)
def load_xgboost_longform() -> xgb.Booster:
    b = xgb.Booster()
    b.load_model(str(_resolve("xgboost_longform.json", ".json")))
    return b


@lru_cache(maxsize=1)
def load_xgboost_shorts() -> xgb.Booster:
    b = xgb.Booster()
    b.load_model(str(_resolve("xgboost_shorts.json", ".json")))
    return b


@lru_cache(maxsize=1)
def load_xgboost_engagement_shorts() -> xgb.Booster:
    b = xgb.Booster()
    b.load_model(str(_resolve("xgboost_engagement_shorts.json", ".json")))
    return b


@lru_cache(maxsize=1)
def load_clip_model():
    import clip
    model, preprocess = clip.load("ViT-B/32", device="cpu")
    return model, preprocess


@lru_cache(maxsize=1)
def load_niche_blueprints() -> dict:
    with open(_resolve("niche_blueprints.json", ".json")) as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_topic_engagement_stats() -> dict:
    with open(_resolve("topic_engagement_stats.json", ".json")) as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_publish_time_stats() -> dict:
    with open(_resolve("publish_time_stats.json", ".json")) as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_title_effectiveness_stats() -> dict:
    with open(_resolve("title_effectiveness_stats.json", ".json")) as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_topic_trend_baseline() -> dict:
    with open(_resolve("topic_trend_baseline.json", ".json")) as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_topic_stats() -> pd.DataFrame:
    return pd.read_csv(_resolve("topic_stats.csv", ".csv"))


def clear_all_caches():
    load_bertopic_model.cache_clear()
    load_xgboost_longform.cache_clear()
    load_xgboost_shorts.cache_clear()
    load_xgboost_engagement_shorts.cache_clear()
    load_clip_model.cache_clear()
    load_niche_blueprints.cache_clear()
    load_topic_engagement_stats.cache_clear()
    load_publish_time_stats.cache_clear()
    load_title_effectiveness_stats.cache_clear()
    load_topic_trend_baseline.cache_clear()
    load_topic_stats.cache_clear()