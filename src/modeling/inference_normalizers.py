"""
output normalizers for inference.py.

these functions sit between raw helper outputs and the final dict returned by
run_channel_inference(). they enforce the canonical schema that types_ml.py
and the UI depend on, so inference.py helpers can return whatever is most
natural for computation and the API boundary is always clean.
"""

from __future__ import annotations

from typing import Any


def normalize_coverage_summary(
    topics_result: dict,
    category: str,
) -> dict:
    """
    converts the raw bertopic assign_topics output to the canonical shape:

        coverage_summary: {
            total_topics: int,
            top_topics: List[{topic_id, topic_label, share}],
            category: str,
        }

    raw backend today returns total_covered and category but no top_topics list.
    """
    raw = topics_result.get("coverage_summary", {})

    total = raw.get("total_topics") or raw.get("total_covered", 0)

    top_topics = raw.get("top_topics")
    if not top_topics:
        by_video = topics_result.get("by_video", [])
        counts: dict[int, dict] = {}
        for v in by_video:
            tid = v.get("topic_id")
            if tid is None or tid == -1:
                continue
            if tid not in counts:
                counts[tid] = {
                    "topic_id": tid,
                    "topic_label": v.get("topic_label", ""),
                    "count": 0,
                }
            counts[tid]["count"] += 1
        n_videos = max(len(by_video), 1)
        top_topics = sorted(counts.values(), key=lambda x: x["count"], reverse=True)
        for entry in top_topics:
            entry["share"] = round(entry.pop("count") / n_videos, 4)
        top_topics = top_topics[:10]

    return {
        "total_topics": int(total),
        "top_topics": top_topics,
        "category": raw.get("category", category),
    }


def normalize_thumbnail_blueprint(raw_blueprint: dict) -> dict:
    """
    converts get_blueprint_summary() output to the canonical shape:

        thumbnail_blueprint: {
            source: str,
            axes: List[{
                axis, channel_score, blueprint_score,
                correlation, direction, recommendation
            }]
        }

    get_blueprint_summary() returns:
        { source, n_videos, recommend: List[str], avoid: List[str], top_axes: dict }
    where top_axes maps axis_name -> { correlation, blended_correlation, ... }
    """
    source = raw_blueprint.get("source", "niche")
    top_axes: dict[str, Any] = raw_blueprint.get("top_axes", {})
    recommend: list[str] = raw_blueprint.get("recommend", [])
    avoid: list[str] = raw_blueprint.get("avoid", [])

    axes = []
    for axis_name, axis_data in top_axes.items():
        if not isinstance(axis_data, dict):
            continue
        corr = float(axis_data.get("blended_correlation", axis_data.get("correlation", 0.0)))
        direction = "positive" if axis_name in recommend else "negative" if axis_name in avoid else "neutral"
        if direction == "positive":
            recommendation = f"increase {axis_name.replace('_', ' ')} in thumbnail"
        elif direction == "negative":
            recommendation = f"reduce {axis_name.replace('_', ' ')} in thumbnail"
        else:
            recommendation = f"{axis_name.replace('_', ' ')} has no clear signal"

        axes.append({
            "axis": axis_name,
            "channel_score": round(float(axis_data.get("channel_mean", axis_data.get("mean", 0.5))), 4),
            "blueprint_score": round(float(axis_data.get("niche_mean", axis_data.get("mean", 0.5))), 4),
            "correlation": round(corr, 4),
            "direction": direction,
            "recommendation": recommendation,
        })

    axes.sort(key=lambda x: abs(x["correlation"]), reverse=True)

    return {"source": source, "axes": axes}


def normalize_title_patterns(raw_patterns: dict) -> dict:
    """
    ensures title_patterns.by_topic keys are always str(topic_id).
    """
    by_topic_raw = raw_patterns.get("by_topic", {})
    by_topic = {str(k): v for k, v in by_topic_raw.items()}
    return {"by_topic": by_topic}