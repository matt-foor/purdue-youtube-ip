import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional
import numpy as np
import pandas as pd
import xgboost as xgb

from src.modeling.model_cache import (
    load_bertopic_model,
    load_xgboost_longform,
    load_xgboost_shorts,
    load_xgboost_engagement_shorts,
    load_topic_engagement_stats,
    load_publish_time_stats,
    load_title_effectiveness_stats,
    load_topic_trend_baseline,
    load_topic_stats,
)
from src.constants.video_types import SHORTS_MAX_DURATION_SEC
from src.modeling.inference_normalizers import (
    normalize_coverage_summary,
    normalize_thumbnail_blueprint,
    normalize_title_patterns,
)

AGE_DAYS_LONGFORM = 30
AGE_DAYS_SHORTS = 7
CADENCE_PERCENTILE = "p75_videos_per_week"
SENTIMENT_CORR_POSITIVE = 0.05
SENTIMENT_CORR_NEGATIVE = -0.05
CHANNEL_SIG_N_VIDEOS = 50
N_VIDEOS_BERTOPIC_MIN = 20
N_VIDEOS_RELIABLE = 50
CLIP_MAX_THUMBNAILS = 50


class InferenceError(Exception):
    def __init__(self, error_code: str, message: str, retryable: bool):
        self.error_code = error_code
        self.message = message
        self.retryable = retryable
        super().__init__(message)


def _get_channel_tier(n_videos: int) -> str:
    if n_videos < N_VIDEOS_BERTOPIC_MIN:
        return "insufficient"
    if n_videos < N_VIDEOS_RELIABLE:
        return "limited"
    return "full"


def _build_doc(video: dict) -> str:
    title = video.get("title", "")
    desc = video.get("description", "")
    tags = " ".join(video.get("tags", []))
    return f"{title} {title} {desc} {tags}".strip()


def _channel_median_vpd(videos: list[dict]) -> float:
    vpd_vals = []
    now = datetime.now(timezone.utc)
    for v in videos:
        try:
            published = datetime.fromisoformat(v["published_at"].replace("Z", "+00:00"))
            age = max((now - published).days, 1)
            vpd_vals.append(v["view_count"] / age)
        except Exception:
            continue
    return float(np.median(vpd_vals)) if vpd_vals else 1.0


def _assign_topics(channel_data: dict) -> dict:
    videos = channel_data["videos"]
    tier = _get_channel_tier(len(videos))

    if tier == "insufficient":
        if not channel_data.get("category_hint"):
            raise InferenceError(
                "INVALID_CHANNEL_DATA",
                "Channel needs at least 20 videos for ML analysis.",
                False,
            )
        return {
            "tier": tier,
            "topic_ids": [],
            "covered_topic_ids": [],
            "category": channel_data["category_hint"],
            "by_video": {},
        }

    topic_model = load_bertopic_model()
    topic_stats = load_topic_stats()

    docs = [_build_doc(v) for v in videos]
    topics, _ = topic_model.transform(docs)

    by_video = {v["video_id"]: int(t) for v, t in zip(videos, topics)}
    covered = list({t for t in topics if t != -1})

    if channel_data.get("category_hint"):
        category = channel_data["category_hint"]
    else:
        video_topics = [t for t in topics if t != -1]
        if not video_topics:
            raise InferenceError("BERTOPIC_FAILED", "Could not assign topics.", True)
        topic_categories = (
            topic_stats[topic_stats["topic_id"].isin(video_topics)]
            .groupby("top_category")
            .size()
        )
        category = topic_categories.idxmax()

    return {
        "tier": tier,
        "topic_ids": [int(t) for t in topics],
        "covered_topic_ids": covered,
        "category": category,
        "by_video": by_video,
    }


def _predict_reach(
    topic_id: int,
    category: str,
    channel: dict,
    channel_median_vpd: float,
    is_short: bool,
) -> float:
    booster = load_xgboost_shorts() if is_short else load_xgboost_longform()
    age_days = AGE_DAYS_SHORTS if is_short else AGE_DAYS_LONGFORM
    topic_stats = load_topic_stats()

    trend_row = topic_stats[topic_stats["topic_id"] == topic_id]
    trend_score = float(trend_row["trend_score"].iloc[0]) if len(trend_row) else 0.0

    features = pd.DataFrame([{
        "log_subscribers": np.log1p(channel.get("subscriber_count", 0)),
        "log_age_days": np.log1p(age_days),
        "topic_id": topic_id,
        "category_name": category,
        "trend_score": trend_score,
        "platform_era": "recent",
        "publish_hour": 15,
        "publish_dow": 5,
        "log_duration": np.log1p(60 if is_short else 600),
        "is_hd": 1,
        "has_description": 1,
        "has_tags": 1,
        "is_sparse_text": 0,
        "bertopic_token_count": 20,
        "title_wordcount": 8,
        "title_has_number": 0,
        "title_has_question": 0,
        "title_has_brackets": 0,
        "title_has_caps_word": 0,
        "title_sentiment": 0,
    }])

    for col in ["topic_id", "category_name", "platform_era"]:
        features[col] = features[col].astype("category")

    dmat = xgb.DMatrix(features, enable_categorical=True)
    raw_vpd = float(np.expm1(booster.predict(dmat)[0]))

    corpus_median = float(np.expm1(7.0))
    scale = channel_median_vpd / corpus_median if corpus_median > 0 else 1.0
    return raw_vpd * scale


def _compute_gap_topics(
    topics_result: dict,
    channel_data: dict,
    channel_median_vpd: float,
) -> dict:
    from src.modeling.content_gap_scorer import score_gaps

    tier = topics_result["tier"]
    if tier == "insufficient":
        return {"topics": [], "tier": tier}

    covered = topics_result["covered_topic_ids"]
    category = topics_result["category"]

    gap_topics = score_gaps(
        covered_topic_ids=covered,
        channel_category=category,
    )

    engagement_stats = load_topic_engagement_stats()
    enriched = []

    for gap in gap_topics:
        topic_id = gap["topic_id"]
        is_short_rec = gap.get("trajectory_label") == "rising"

        reach = _predict_reach(
            topic_id, category,
            channel_data["channel"],
            channel_median_vpd,
            is_short_rec,
        )

        if is_short_rec:
            eng_score = gap.get("engagement_score", 0.5)
        else:
            topic_key = str(topic_id)
            eng_entry = engagement_stats.get("topics", {}).get(topic_key)
            if not eng_entry:
                eng_entry = engagement_stats.get("category_fallbacks", {}).get(category, {})
            eng_score = eng_entry.get("engagement_percentile", 0.5) if eng_entry else 0.5

        enriched.append({
            **gap,
            "predicted_views_per_day": round(reach, 1),
            "engagement_percentile": eng_score,
            "is_short_recommended": is_short_rec,
        })

    return {"topics": enriched, "tier": tier}


def _compute_time_windows(category: str) -> dict:
    stats = load_publish_time_stats()
    cat_stats = stats.get(category, {})
    if not cat_stats:
        return {}

    cadence = cat_stats.get("cadence", {})
    return {
        "best_hour_utc": cat_stats.get("best_hour_utc"),
        "best_dow": cat_stats.get("best_dow"),
        "top_hours_utc": cat_stats.get("top_hours_utc", []),
        "top_days": cat_stats.get("top_days", []),
        "cadence_videos_per_week_recommended": cadence.get(CADENCE_PERCENTILE),
        "cadence_interpretation": cadence.get("interpretation", ""),
    }


def _compute_title_patterns(gap_topics: list, category: str) -> dict:
    stats = load_title_effectiveness_stats()
    by_topic = {}

    for gap in gap_topics[:5]:
        topic_id = str(gap["topic_id"])
        entry = stats.get("topics", {}).get(topic_id)
        if not entry:
            entry = stats.get("category_fallbacks", {}).get(category, {})
        if entry:
            features = entry.get("features", {})
            duration = entry.get("duration", {})
            by_topic[topic_id] = {
                "recommendations": {
                    k: v for k, v in features.items()
                    if isinstance(v, dict) and v.get("recommend")
                },
                "optimal_duration_min": duration.get("optimal_range_min"),
                "duration_partial_corr": duration.get("partial_correlation"),
            }

    return {"by_topic": by_topic}


def _analyze_thumbnails(channel_data: dict, category: str) -> dict:
    from src.modeling.clip_analyzer import analyze_channel_thumbnails, get_blueprint_summary

    now = datetime.now(timezone.utc)
    videos = sorted(
        channel_data["videos"],
        key=lambda v: v["published_at"],
        reverse=True,
    )[:CLIP_MAX_THUMBNAILS]

    video_ids, views_per_day, thumbnail_urls = [], [], []
    for v in videos:
        try:
            published = datetime.fromisoformat(v["published_at"].replace("Z", "+00:00"))
            age = max((now - published).days, 1)
            vpd = v["view_count"] / age
        except Exception:
            vpd = 0.0

        url = v.get("thumbnail_url") or f"https://i.ytimg.com/vi/{v['video_id']}/hqdefault.jpg"
        video_ids.append(v["video_id"])
        views_per_day.append(vpd)
        thumbnail_urls.append(url)

    try:
        blueprint = analyze_channel_thumbnails(
            video_ids=video_ids,
            views_per_day=views_per_day,
            thumbnail_urls=thumbnail_urls,
            category=category,
        )
        raw_summary = get_blueprint_summary(blueprint)
        return normalize_thumbnail_blueprint(raw_summary)
    except Exception as e:
        raise InferenceError("CLIP_TIMEOUT", f"Thumbnail analysis failed: {e}", True)


def _build_gemini_context(
    channel_data: dict,
    topics_result: dict,
    gaps_result: dict,
    time_windows: dict,
    title_patterns: dict,
    thumbnail_result: dict,
) -> dict:
    trend_baseline = load_topic_trend_baseline()
    channel = channel_data["channel"]

    gap_topics_context = []
    for gap in gaps_result["topics"][:5]:
        topic_id = str(gap["topic_id"])
        baseline = trend_baseline.get(topic_id, {})
        gap_topics_context.append({
            "label": gap["topic_label"],
            "gap_score": round(gap["gap_score"], 3),
            "predicted_views_per_day": gap["predicted_views_per_day"],
            "engagement_percentile": round(gap["engagement_percentile"], 3),
            "is_short_recommended": gap["is_short_recommended"],
            "trajectory": gap.get("trajectory_label", "stable"),
            "trend_zscore": baseline.get("trend_zscore"),
            "seasonality_index": baseline.get("seasonality_index", {}),
        })

    return {
        "channel": {
            "title": channel.get("title"),
            "subscriber_count": channel.get("subscriber_count"),
            "category": topics_result["category"],
            "tier": topics_result["tier"],
            "video_count": len(channel_data["videos"]),
        },
        "gap_topics": gap_topics_context,
        "time_windows": time_windows,
        "title_patterns": title_patterns,
        "thumbnail_blueprint": thumbnail_result,
    }


def _call_gemini(context: dict) -> dict:
    import google.generativeai as genai

    api_key = os.environ.get("GEMINI_API_KEY_1")
    if not api_key:
        raise InferenceError("INTERNAL_ERROR", "No Gemini API key configured.", False)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-pro-preview-03-25")

    prompt = f"""You are an expert YouTube growth strategist. Given the following channel analysis data, generate actionable recommendations in JSON format.

Channel data:
{json.dumps(context, indent=2)}

Respond with a JSON object containing exactly these keys:
- overview: 2-3 sentence channel audit summary
- topic_recommendations: specific video ideas for the top 3 gap topics, referencing the data
- thumbnail_advice: concrete thumbnail recommendations based on the blueprint axes
- publish_time_advice: timing and cadence recommendations based on the time windows data

Return only valid JSON, no markdown."""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)
    except json.JSONDecodeError:
        raise InferenceError("INTERNAL_ERROR", "Gemini returned invalid JSON.", False)
    except Exception as e:
        if "429" in str(e):
            raise InferenceError("INTERNAL_ERROR", "Gemini rate limit hit.", True)
        raise InferenceError("INTERNAL_ERROR", str(e), False)


def run_channel_inference(channel_data: dict) -> dict:
    try:
        channel_median_vpd = _channel_median_vpd(channel_data["videos"])
        topics_result = _assign_topics(channel_data)
        category = topics_result["category"]
        gaps_result = _compute_gap_topics(topics_result, channel_data, channel_median_vpd)
        time_windows = _compute_time_windows(category)
        title_patterns_raw = _compute_title_patterns(gaps_result["topics"], category)
        thumbnail_result = _analyze_thumbnails(channel_data, category)
        context = _build_gemini_context(
            channel_data, topics_result, gaps_result,
            time_windows, title_patterns_raw, thumbnail_result,
        )
        ai_sections = _call_gemini(context)

        topic_stats_df = load_topic_stats()
        label_map: dict[int, str] = dict(
            zip(topic_stats_df["topic_id"].astype(int), topic_stats_df.get("topic_label", topic_stats_df.get("top_label", "")))
        ) if not topic_stats_df.empty else {}

        raw_topics_result = {
            "by_video": [
                {"video_id": vid, "topic_id": tid, "topic_label": label_map.get(tid, "")}
                for vid, tid in topics_result["by_video"].items()
            ],
            "coverage_summary": {
                "total_covered": len(topics_result["covered_topic_ids"]),
                "category": category,
            },
        }

        return {
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "channel_tier": topics_result["tier"],
            "topics": {
                "coverage_summary": normalize_coverage_summary(raw_topics_result, category),
                "by_video": topics_result["by_video"],
            },
            "gaps": gaps_result,
            "time_windows": time_windows,
            "title_patterns": normalize_title_patterns(title_patterns_raw),
            "thumbnail_blueprint": thumbnail_result,
            "ai_sections": ai_sections,
        }

    except InferenceError:
        raise
    except Exception as e:
        raise InferenceError("INTERNAL_ERROR", str(e), False)