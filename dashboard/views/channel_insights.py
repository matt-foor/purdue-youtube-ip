from __future__ import annotations

import json
import re
from html import escape
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd
import requests
import streamlit as st

from dashboard.components.visualizations import (
    format_compact_int,
    plotly_bar_chart,
    plotly_line_chart,
    show_plotly_chart,
    styled_dataframe,
    styled_keyword_chips,
)
from src.services.channel_insights_service import (
    TOPIC_MODE_BERTOPIC_OPTIONAL,
    TOPIC_MODE_HEURISTIC,
    list_connected_channels,
    load_channel_insights,
    refresh_channel_insights,
)
from src.services.model_artifact_service import get_bertopic_artifact_status
from src.utils.api_keys import get_provider_key_count, run_with_provider_keys


STATE_KEYS = (
    "channel_insights_selected_channel",
    "channel_insights_input",
    "channel_insights_force_refresh",
    "channel_insights_topic_mode",
    "channel_insights_error",
)

_TOPIC_LABEL_NOISE = {
    "video",
    "videos",
    "youtube",
    "yt",
    "tts",
    "short",
    "shorts",
    "official",
    "channel",
    "episode",
    "episodes",
    "clip",
    "clips",
    "summary",
    "explained",
}
_TOPIC_THEME_RULES = (
    ("Packaging Strategy", {"packaging", "thumbnail", "thumbnails", "ctr", "hook", "hooks", "title", "titles"}),
    ("COVID Coverage", {"covid", "vaccine", "vaccines", "coronavirus", "virus", "pandemic"}),
    ("Minecraft Gameplay", {"minecraft", "mod", "modded", "survival", "hardcore", "smp"}),
    ("Streaming Culture", {"streamer", "streamers", "twitch", "livestream", "livestreams", "vod"}),
    ("Fitness Training", {"workout", "workouts", "lifting", "muscle", "gym", "training"}),
    ("Food Content", {"recipe", "recipes", "cooking", "cook", "food", "meal", "meals"}),
    ("Tech Reviews", {"review", "reviews", "unboxing", "smartphone", "laptop", "gpu", "iphone", "android"}),
    ("Science Explainers", {"science", "physics", "chemistry", "space", "nasa", "engineering"}),
    ("AI Tools", {"ai", "chatgpt", "openai", "prompt", "prompts", "automation"}),
)
_DISPLAY_ACRONYMS = {
    "ai": "AI",
    "ctr": "CTR",
    "fps": "FPS",
    "ui": "UI",
    "ux": "UX",
}


def _inject_channel_insights_css() -> None:
    st.markdown(
        """
        <style>
        .channel-insights-page {
            max-width: var(--app-page-width);
            margin: 0 auto;
        }
        .ci-hero {
            max-width: 930px;
            margin: 0 auto 1.4rem;
            text-align: center;
        }
        .ci-kicker {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.45rem 0.78rem;
            border-radius: 999px;
            background: rgba(255, 0, 0, 0.12);
            border: 1px solid rgba(255, 0, 0, 0.35);
            color: #FF8888;
            font-size: 12px;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-bottom: 0.95rem;
        }
        .ci-kicker-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: #FF0000;
            box-shadow: 0 0 14px rgba(255, 0, 0, 0.5);
        }
        .ci-title {
            font-family: "Inter", system-ui, sans-serif;
            font-size: clamp(34px, 3.8vw, 50px);
            line-height: 1.02;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: -0.04em;
            margin-bottom: 0.8rem;
        }
        .ci-subtitle {
            color: #B0B0B0;
            font-size: 16px;
            line-height: 1.62;
            max-width: 760px;
            margin: 0 auto;
            font-weight: 500;
        }
        .ci-card {
            border-radius: 24px;
            border: 1px solid rgba(255,255,255,0.08);
            background:
                radial-gradient(circle at top left, rgba(255, 0, 0, 0.10) 0%, transparent 30%),
                radial-gradient(circle at top right, rgba(0, 212, 255, 0.08) 0%, transparent 26%),
                linear-gradient(180deg, rgba(22, 33, 62, 0.95) 0%, rgba(15, 15, 35, 0.98) 100%);
            box-shadow: 0 20px 46px rgba(3, 6, 20, 0.40);
            padding: 1.2rem 1.25rem;
            margin-bottom: 1rem;
        }
        .ci-card-title {
            font-family: "Inter", system-ui, sans-serif;
            color: #F7F8FC;
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 0.3rem;
        }
        .ci-card-copy {
            color: #B8C1DA;
            font-size: 13px;
            line-height: 1.55;
        }
        .ci-summary-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.7rem;
            margin-top: 0.95rem;
        }
        .ci-summary-item {
            padding: 0.75rem 0.85rem;
            border-radius: 18px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
        }
        .ci-summary-label {
            color: #8993B2;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.22rem;
        }
        .ci-summary-value {
            color: #F7F8FC;
            font-size: 14px;
            font-weight: 700;
            line-height: 1.5;
        }
        .ci-list {
            margin: 0;
            padding-left: 1rem;
            color: #D7DDF0;
            font-size: 13px;
            line-height: 1.6;
        }
        .ci-list li {
            margin-bottom: 0.35rem;
        }
        .ci-theme-card {
            padding: 0.85rem 0.95rem;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.08);
            background: rgba(255,255,255,0.03);
            margin-bottom: 0.8rem;
        }
        .ci-theme-title {
            color: #F7F8FC;
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }
        .ci-theme-copy {
            color: #B8C1DA;
            font-size: 13px;
            line-height: 1.6;
        }
        .ci-source-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
            background: rgba(139, 92, 246, 0.14);
            border: 1px solid rgba(196, 181, 253, 0.16);
            color: #F7F8FC;
            font-size: 11px;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        .ci-note {
            color: #97A2C3;
            font-size: 12px;
            line-height: 1.55;
        }
        .ci-empty {
            padding: 1rem 1.1rem;
            border-radius: 20px;
            border: 1px dashed rgba(255,255,255,0.12);
            background: rgba(255,255,255,0.02);
            color: #B8C1DA;
            font-size: 13px;
            line-height: 1.6;
        }
        .ci-kpi-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.95rem;
            margin: 0.2rem 0 0.8rem;
        }
        .ci-kpi-card {
            border-radius: 22px;
            border: 1px solid rgba(255,255,255,0.08);
            background:
                radial-gradient(circle at top left, rgba(255, 0, 0, 0.08) 0%, transparent 30%),
                linear-gradient(180deg, rgba(22, 33, 62, 0.95) 0%, rgba(15, 15, 35, 0.98) 100%);
            box-shadow: 0 16px 36px rgba(3, 6, 20, 0.32);
            padding: 1rem 1.05rem;
            min-height: 136px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .ci-kpi-label {
            color: #97A2C3;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }
        .ci-kpi-value {
            color: #F7F8FC;
            font-size: clamp(26px, 2.3vw, 34px);
            font-weight: 800;
            line-height: 1.05;
            margin-top: 0.55rem;
        }
        .ci-kpi-delta {
            color: #97A2C3;
            font-size: 12px;
            font-weight: 600;
            margin-top: 0.7rem;
        }
        .ci-kpi-delta-positive { color: #5EE6A8; }
        .ci-kpi-delta-negative { color: #FF8A8A; }
        .ci-markdown-card ul {
            margin: 0.1rem 0 0;
            padding-left: 1.2rem;
        }
        .ci-markdown-card li {
            margin-bottom: 0.45rem;
            color: #424245;
            line-height: 1.65;
        }
        @media (max-width: 1100px) {
            .ci-kpi-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        @media (max-width: 700px) {
            .ci-kpi-grid {
                grid-template-columns: minmax(0, 1fr);
            }
        }
        /* Light glass (classes are unique to Channel Insights) */
        .ci-title { color: #1d1d1f !important; }
        .ci-subtitle { color: #424245 !important; }
        .ci-card {
            background: rgba(255, 255, 255, 0.96) !important;
            border: 1px solid rgba(0, 0, 0, 0.11) !important;
            box-shadow: 0 16px 44px rgba(0, 0, 0, 0.1) !important;
        }
        .ci-card-title { color: #1d1d1f !important; }
        .ci-card-copy,
        .ci-list,
        .ci-note { color: #424245 !important; }
        .ci-summary-value,
        .ci-theme-title { color: #1d1d1f !important; }
        .ci-kpi-card {
            background: rgba(255, 255, 255, 0.96) !important;
            border: 1px solid rgba(0, 0, 0, 0.11) !important;
            box-shadow: 0 16px 44px rgba(0, 0, 0, 0.1) !important;
        }
        .ci-kpi-label,
        .ci-kpi-delta { color: #6e6e73 !important; }
        .ci-kpi-value { color: #1d1d1f !important; }
        .ci-kpi-delta-positive { color: #138a4b !important; }
        .ci-kpi-delta-negative { color: #b42318 !important; }
        .ci-source-pill {
            background: rgba(0, 113, 227, 0.12) !important;
            border: 1px solid rgba(0, 113, 227, 0.32) !important;
            color: #1d1d1f !important;
            font-weight: 700 !important;
        }
        .ci-empty {
            border: 1px dashed rgba(0, 0, 0, 0.15) !important;
            background: rgba(255, 255, 255, 0.8) !important;
            color: #6e6e73 !important;
        }
        /* Channel Insights help/info icon: replace dark dot with clear bulb */
        [data-testid*="stTooltipHoverTarget"] button,
        button[aria-label*="help" i],
        button[aria-label*="info" i] {
            width: 24px !important;
            height: 24px !important;
            min-width: 24px !important;
            min-height: 24px !important;
            border-radius: 999px !important;
            background: linear-gradient(165deg, #fffaf0, #fff3d9) !important;
            border: 1px solid rgba(230, 0, 18, 0.38) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
            color: transparent !important;
            position: relative !important;
        }
        [data-testid*="stTooltipHoverTarget"] button svg,
        button[aria-label*="help" i] svg,
        button[aria-label*="info" i] svg {
            opacity: 0 !important;
        }
        [data-testid*="stTooltipHoverTarget"] button::before,
        button[aria-label*="help" i]::before,
        button[aria-label*="info" i]::before {
            content: "💡";
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -54%);
            font-size: 13px;
            line-height: 1;
        }
        [data-testid*="stTooltipHoverTarget"] button:hover,
        button[aria-label*="help" i]:hover,
        button[aria-label*="info" i]:hover {
            background: linear-gradient(165deg, #fffbe7, #ffefc6) !important;
            border-color: rgba(230, 0, 18, 0.55) !important;
        }
        /* Glass primary / secondary actions (Channel Insights only — this CSS is injected on this page) */
        button[data-testid="baseButton-primary"] {
            font-weight: 700 !important;
            background: linear-gradient(180deg, rgba(232, 248, 255, 0.98), rgba(200, 230, 255, 0.88)) !important;
            color: #0a2540 !important;
            border: 1px solid rgba(0, 113, 227, 0.38) !important;
            box-shadow: 0 4px 18px rgba(0, 113, 227, 0.14) !important;
        }
        button[data-testid="baseButton-primary"]:hover {
            background: linear-gradient(180deg, rgba(210, 240, 255, 1), rgba(175, 220, 255, 0.92)) !important;
            border-color: rgba(0, 113, 227, 0.55) !important;
            color: #061a2e !important;
        }
        button[data-testid="baseButton-secondary"] {
            font-weight: 700 !important;
            background: rgba(255, 255, 255, 0.72) !important;
            color: #0a2540 !important;
            border: 1px solid rgba(0, 113, 227, 0.3) !important;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06) !important;
        }
        button[data-testid="baseButton-secondary"]:hover {
            background: rgba(240, 248, 255, 0.95) !important;
            border-color: rgba(0, 113, 227, 0.45) !important;
        }
        .ci-kpi-delta-hint {
            display: block;
            font-size: 11px;
            font-weight: 600;
            color: #86868b !important;
            margin-bottom: 0.2rem;
            line-height: 1.35;
        }
        .ci-kpi-value[title] { cursor: help; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _format_int(value: Any) -> str:
    if value is None or value == "":
        return "0"
    return f"{int(round(float(value))):,}"


def _format_pct(value: Any) -> str:
    return f"{float(value or 0) * 100:.1f}%"


def _history_delta_text(value: float, suffix: str = "") -> str:
    if value > 0:
        return f"+{value:.1f}{suffix}"
    if value < 0:
        return f"{value:.1f}{suffix}"
    return f"0.0{suffix}"


def _normalize_topic_tokens(label: str) -> List[str]:
    text = str(label or "").replace("/", " ")
    raw_tokens = re.findall(r"[A-Za-z0-9_]+", text)
    cleaned: List[str] = []
    for token in raw_tokens:
        normalized = token.strip().lower().replace("_", " ")
        normalized = re.sub(r"\s+", " ", normalized).strip()
        if not normalized or normalized in _TOPIC_LABEL_NOISE:
            continue
        if normalized.endswith("ies") and len(normalized) > 4:
            normalized = normalized[:-3] + "y"
        elif normalized.endswith("s") and len(normalized) > 4 and not normalized.endswith("ss"):
            normalized = normalized[:-1]
        if normalized in _TOPIC_LABEL_NOISE:
            continue
        if any(
            normalized == existing
            or normalized in existing
            or existing in normalized
            for existing in cleaned
        ):
            continue
        cleaned.append(normalized)
    return cleaned


def _format_topic_token(token: str) -> str:
    parts = [part for part in str(token or "").split() if part]
    return " ".join(_DISPLAY_ACRONYMS.get(part, part.title()) for part in parts)


def _compact_topic_label(label: str) -> str:
    text = str(label or "").strip()
    if not text or text in {"N/A", "No Theme Yet", "No Pattern Yet", "Unassigned"}:
        return text

    tokens = _normalize_topic_tokens(text)
    if not tokens:
        return text

    token_set = set(tokens)
    for theme_name, family in _TOPIC_THEME_RULES:
        if len(token_set & family) >= 2:
            return theme_name

    return _format_topic_token(tokens[0])


def _display_topic_metrics_df(payload: Dict[str, Any]) -> pd.DataFrame:
    topic_metrics_df = payload.get("topic_metrics_df", pd.DataFrame())
    if topic_metrics_df.empty:
        return topic_metrics_df
    display_df = topic_metrics_df.copy()
    display_df["topic_label"] = display_df["topic_label"].fillna("").astype(str).map(_compact_topic_label)
    return display_df


def _display_videos_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    display_df = df.copy()
    if "primary_topic" in display_df.columns:
        display_df["primary_topic"] = display_df["primary_topic"].fillna("").astype(str).map(_compact_topic_label)
    return display_df


def _preferred_text_provider() -> tuple[str, str] | tuple[None, None]:
    if get_provider_key_count("gemini") > 0:
        return "gemini", "gemini-2.5-flash"
    if get_provider_key_count("openai") > 0:
        return "openai", "gpt-4o-mini"
    return None, None


def _is_ai_retryable_error(exc: Exception) -> bool:
    message = str(exc).lower()
    retry_tokens = (
        "rate limit",
        "resource exhausted",
        "too many requests",
        "insufficient_quota",
        "api key",
        "401",
        "403",
        "429",
        "500",
        "503",
        "overloaded",
    )
    return any(token in message for token in retry_tokens)


def _gemini_generate_text(gemini_key: str, model: str, prompt: str) -> str:
    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        f"?key={gemini_key}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(endpoint, json=payload, timeout=90)
    if response.status_code >= 400:
        raise RuntimeError(f"Gemini text API error ({response.status_code}): {response.text[:500]}")

    body = response.json()
    texts: List[str] = []
    for candidate in body.get("candidates", []):
        for part in ((candidate.get("content", {}) or {}).get("parts", []) or []):
            text = part.get("text")
            if text:
                texts.append(text)

    if not texts:
        raise RuntimeError("Gemini did not return text output.")
    return "\n\n".join(texts)


def _openai_generate_text(openai_key: str, model: str, prompt: str) -> str:
    endpoint = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openai_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an advanced YouTube strategist supporting the "
                    "YouTube IP creator analytics platform. "
                    "Keep outputs concise, structured, and actionable."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.6,
    }
    response = requests.post(endpoint, headers=headers, json=payload, timeout=90)
    if response.status_code >= 400:
        raise RuntimeError(f"OpenAI text API error ({response.status_code}): {response.text[:500]}")
    body = response.json()
    choices = body.get("choices", [])
    if not choices:
        raise RuntimeError("OpenAI did not return any choices.")
    message = choices[0].get("message", {}) or {}
    content = message.get("content") or ""
    if not content:
        raise RuntimeError("OpenAI returned an empty message content.")
    return content


def _generate_text_with_provider_pool(provider: str, model: str, prompt: str) -> str:
    provider_name = provider.lower().strip()
    if provider_name == "gemini":
        return run_with_provider_keys(
            "gemini",
            lambda key: _gemini_generate_text(key, model, prompt),
            retryable_error=_is_ai_retryable_error,
        )
    if provider_name == "openai":
        return run_with_provider_keys(
            "openai",
            lambda key: _openai_generate_text(key, model, prompt),
            retryable_error=_is_ai_retryable_error,
        )
    raise RuntimeError(f"Unsupported text provider: {provider}")


def _llm_cache_key(payload: Dict[str, Any], section: str) -> str:
    summary = payload.get("summary", {})
    return "::".join(
        [
            "channel_insights_llm",
            section,
            str(payload.get("channel", {}).get("channel_id", "")),
            str(summary.get("snapshot_at", "")),
            str(summary.get("topic_mode_used", "")),
        ]
    )


def _serialize_records(records: Sequence[Dict[str, Any]], *, limit: int = 6, fields: Sequence[str] | None = None) -> str:
    trimmed: List[Dict[str, Any]] = []
    for row in list(records)[:limit]:
        if fields is None:
            trimmed.append(dict(row))
        else:
            trimmed.append({field: row.get(field) for field in fields})
    return json.dumps(trimmed, ensure_ascii=True, default=str)


def _generate_channel_insights_text(payload: Dict[str, Any], section: str, prompt: str) -> str:
    cache_key = _llm_cache_key(payload, section)
    cached_value = st.session_state.get(cache_key, "")
    if cached_value:
        return str(cached_value)

    provider, model = _preferred_text_provider()
    if not provider or not model:
        return ""

    try:
        output = _generate_text_with_provider_pool(provider, model, prompt)
    except Exception as exc:
        st.session_state[cache_key] = f"__ERROR__::{exc}"
        return ""

    st.session_state[cache_key] = output
    return output


def _render_ai_card(title: str, body: str, *, empty_message: str = "") -> None:
    if not body and not empty_message:
        return
    html_body = ""
    if body:
        bullet_items = []
        paragraph_items = []
        for raw_line in str(body).splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(("- ", "* ")):
                bullet_items.append(f"<li>{escape(line[2:].strip())}</li>")
            else:
                paragraph_items.append(f"<p class='ci-card-copy' style='margin:0.45rem 0 0;'>{escape(line)}</p>")
        if bullet_items:
            html_body += "<div class='ci-markdown-card'><ul>" + "".join(bullet_items) + "</ul></div>"
        if paragraph_items:
            html_body += "".join(paragraph_items)
    else:
        html_body = f"<div class='ci-card-copy'>{escape(empty_message)}</div>"

    st.markdown(
        f'<div class="ci-card"><div class="ci-card-title">{escape(title)}</div>{html_body}</div>',
        unsafe_allow_html=True,
    )


def _overview_actions_prompt(payload: Dict[str, Any], display_topic_metrics_df: pd.DataFrame) -> str:
    summary = dict(payload.get("summary", {}))
    summary["strongest_theme"] = _compact_topic_label(str(summary.get("strongest_theme", "")))
    summary["weakest_theme"] = _compact_topic_label(str(summary.get("weakest_theme", "")))
    topic_records = display_topic_metrics_df.to_dict(orient="records")
    duration_records = payload.get("duration_metrics_df", pd.DataFrame()).to_dict(orient="records")
    title_records = payload.get("title_pattern_metrics_df", pd.DataFrame()).to_dict(orient="records")
    return (
        "You are generating next-action recommendations for a YouTube creator analytics dashboard.\n"
        "Return exactly 4 markdown bullet points. Each bullet must be one actionable sentence.\n"
        "Use only the provided channel data. Mention concrete themes, formats, cadence, or packaging where relevant.\n\n"
        f"Channel: {payload.get('channel', {}).get('channel_title', '')}\n"
        f"Summary: {json.dumps(summary, ensure_ascii=True, default=str)}\n"
        f"Topic Metrics: {_serialize_records(topic_records, fields=['topic_label', 'video_count', 'median_views_per_day', 'trend_score', 'outlier_count'])}\n"
        f"Duration Metrics: {_serialize_records(duration_records, fields=['duration_bucket', 'median_views_per_day', 'videos'])}\n"
        f"Title Pattern Metrics: {_serialize_records(title_records, fields=['title_pattern', 'median_views_per_day', 'videos'])}"
    )


def _topic_trends_prompt(payload: Dict[str, Any], display_topic_metrics_df: pd.DataFrame) -> str:
    summary = dict(payload.get("summary", {}))
    topic_records = display_topic_metrics_df.to_dict(orient="records")
    return (
        "You are writing a concise analyst note for the Topic Trends tab of a YouTube creator dashboard.\n"
        "Return 3 short markdown bullet points. Focus on momentum, strongest themes, weak themes, and breakout potential.\n"
        "Do not invent metrics; use only the data provided.\n\n"
        f"Channel: {payload.get('channel', {}).get('channel_title', '')}\n"
        f"Summary: {json.dumps(summary, ensure_ascii=True, default=str)}\n"
        f"Topic Metrics: {_serialize_records(topic_records, limit=10, fields=['topic_label', 'video_count', 'median_views_per_day', 'trend_score', 'outlier_count', 'avg_engagement'])}"
    )


def _formats_prompt(payload: Dict[str, Any]) -> str:
    summary = dict(payload.get("summary", {}))
    duration_records = payload.get("duration_metrics_df", pd.DataFrame()).to_dict(orient="records")
    title_records = payload.get("title_pattern_metrics_df", pd.DataFrame()).to_dict(orient="records")
    day_records = payload.get("publish_day_metrics_df", pd.DataFrame()).to_dict(orient="records")
    hour_records = payload.get("publish_hour_metrics_df", pd.DataFrame()).to_dict(orient="records")
    return (
        "You are writing a concise analyst note for the Formats & Patterns tab of a YouTube creator dashboard.\n"
        "Return 3 short markdown bullet points. Focus on winning duration buckets, title patterns, and timing signals.\n"
        "Do not invent metrics; use only the data provided.\n\n"
        f"Channel: {payload.get('channel', {}).get('channel_title', '')}\n"
        f"Summary: {json.dumps(summary, ensure_ascii=True, default=str)}\n"
        f"Duration Metrics: {_serialize_records(duration_records, fields=['duration_bucket', 'median_views_per_day', 'videos', 'avg_engagement'])}\n"
        f"Title Pattern Metrics: {_serialize_records(title_records, fields=['title_pattern', 'median_views_per_day', 'videos', 'avg_engagement'])}\n"
        f"Publish Day Metrics: {_serialize_records(day_records, fields=['publish_day', 'median_views_per_day', 'videos'])}\n"
        f"Publish Hour Metrics: {_serialize_records(hour_records, fields=['publish_hour', 'median_views_per_day', 'videos'])}"
    )


def _render_summary_kpi_cards(summary: Dict[str, Any], deltas: Dict[str, Any]) -> None:
    mvpd = int(round(float(summary.get("median_views_per_day", 0) or 0)))
    mvp_c, mvp_full = format_compact_int(mvpd)
    roc = int(round(float(summary.get("recent_outlier_count", 0) or 0)))
    roc_c, roc_full = format_compact_int(roc)
    gap_days = float(summary.get("avg_upload_gap_days", 0) or 0)

    cards = [
        {
            "label": "Upload cadence",
            "value_html": f'<div class="ci-kpi-value">{escape(f"{gap_days:.1f} days")}</div>',
            "delta": _history_delta_text(deltas.get("upload_gap_delta", 0), "d") if deltas else None,
            "delta_hint": "Change in avg. days between uploads vs your last snapshot:",
        },
        {
            "label": "Recent outliers",
            "value_html": (
                f'<div class="ci-kpi-value" title="{escape(roc_full + " videos flagged as strong outliers")}">'
                f"{escape(roc_c)}</div>"
            ),
            "delta": _history_delta_text(deltas.get("outlier_count_delta", 0)) if deltas else None,
            "delta_hint": "Change in outlier count vs your last snapshot:",
        },
        {
            "label": "Strongest theme",
            "value_html": f'<div class="ci-kpi-value">{escape(_compact_topic_label(str(summary.get("strongest_theme", "N/A"))))}</div>',
            "delta": None,
            "delta_hint": "",
        },
        {
            "label": "Weakest theme",
            "value_html": f'<div class="ci-kpi-value">{escape(_compact_topic_label(str(summary.get("weakest_theme", "N/A"))))}</div>',
            "delta": None,
            "delta_hint": "",
        },
        {
            "label": "Median views / day",
            "value_html": (
                f'<div class="ci-kpi-value" title="{escape(mvp_full + " views per day (median across recent window)")}">'
                f"{escape(mvp_c)}</div>"
            ),
            "delta": _history_delta_text(deltas.get("median_views_per_day_delta", 0)) if deltas else None,
            "delta_hint": "Change in median views/day vs your last snapshot:",
        },
    ]

    html_cards: List[str] = []
    for card in cards:
        delta_text = card.get("delta")
        delta_class = "ci-kpi-delta"
        if delta_text:
            if str(delta_text).startswith("+"):
                delta_class += " ci-kpi-delta-positive"
            elif str(delta_text).startswith("-"):
                delta_class += " ci-kpi-delta-negative"
        hint = str(card.get("delta_hint") or "")
        if hint and delta_text:
            delta_block = (
                f'<div class="{delta_class}">'
                f'<span class="ci-kpi-delta-hint">{escape(hint)}</span>'
                f"{escape(str(delta_text))}</div>"
            )
        elif hint and not delta_text:
            delta_block = f'<div class="{delta_class}"><span class="ci-kpi-delta-hint">{escape(hint)}</span>—</div>'
        elif delta_text:
            delta_block = f'<div class="{delta_class}">{escape(str(delta_text))}</div>'
        else:
            delta_block = '<div class="ci-kpi-delta"></div>'
        html_cards.append(
            f'<div class="ci-kpi-card">'
            f'<div class="ci-kpi-label">{escape(str(card["label"]))}</div>'
            f'{card["value_html"]}'
            f"{delta_block}</div>"
        )

    st.caption(
        "Large numbers use **K / M / B**; hover a value for the exact figure. "
        "Deltas appear when a **previous snapshot** exists to compare against."
    )
    st.markdown(
        f'<div class="ci-kpi-grid">{"".join(html_cards)}</div>',
        unsafe_allow_html=True,
    )


def _queue_outlier_finder_theme(theme: str, channel_title: str) -> None:
    st.session_state["outlier_page_query"] = theme
    st.session_state["outlier_page_prefill_note"] = (
        f"Suggested from {channel_title}'s latest channel insights. Use this theme as a niche seed and refine it before scanning."
    )
    from dashboard.navigation_support import switch_to_outlier_finder

    switch_to_outlier_finder()


def _topic_mode_label(topic_mode: str) -> str:
    if topic_mode == TOPIC_MODE_BERTOPIC_OPTIONAL:
        return "Model-Backed Topics (Beta)"
    return "Heuristic Topics"


def _artifact_status_label(state: str) -> str:
    mapping = {
        "disabled": "Unavailable",
        "unconfigured": "Unavailable",
        "download_required": "Download Required",
        "ready": "Ready",
        "invalid": "Failed / Fallback Active",
        "load_failed": "Failed / Fallback Active",
        "transform_failed": "Failed / Fallback Active",
    }
    return mapping.get(str(state or "").strip().lower(), "Unavailable")


def _render_connect_card(connected_channels: list[dict[str, Any]]) -> None:
    artifact_status = get_bertopic_artifact_status()
    st.markdown(
        '<div class="ci-card">'
        '<div class="ci-card-title">Connect a public channel</div>'
        '<div class="ci-card-copy">'
        "Add a URL, @handle, or channel ID. Optionally force a live API refresh, then choose how topics are labeled "
        "before you tap <strong>Start analysis</strong>. Public-only; each run saves a snapshot."
        "</div>",
        unsafe_allow_html=True,
    )
    with st.form("channel_insights_connect_form"):
        channel_input = st.text_input(
            "Channel URL, handle, or channel ID",
            key="channel_insights_input",
            placeholder="https://www.youtube.com/@veritasium or @veritasium",
        )
        force_refresh = st.toggle(
            "Force live refresh",
            key="channel_insights_force_refresh",
            help="Re-fetch from the YouTube API instead of using the latest cached dataset row.",
        )
        st.selectbox(
            "Topic analysis mode",
            options=[TOPIC_MODE_HEURISTIC, TOPIC_MODE_BERTOPIC_OPTIONAL],
            key="channel_insights_topic_mode",
            format_func=_topic_mode_label,
            help="Pick before starting: heuristic is fastest; model-backed (beta) uses BERTopic when the bundle is ready.",
        )
        connect_clicked = st.form_submit_button("Start analysis", type="primary", use_container_width=True)

    st.caption(f"Artifact status: {_artifact_status_label(artifact_status.state)}")
    if artifact_status.state == "ready":
        st.success(artifact_status.message or "BERTopic bundle is ready.")
    elif artifact_status.state == "download_required":
        st.info(artifact_status.message or "The BERTopic bundle will download when you run the beta mode.")
    elif artifact_status.state == "invalid":
        st.warning(
            artifact_status.failure_reason
            or artifact_status.message
            or "BERTopic beta mode is currently unavailable."
        )
    else:
        st.caption(artifact_status.message or "Heuristic mode is the default until artifact configuration is complete.")

    st.markdown("</div>", unsafe_allow_html=True)

    if connect_clicked:
        if not channel_input.strip():
            st.session_state["channel_insights_error"] = "Enter a public channel URL, handle, or channel ID first."
        else:
            with st.spinner("Analyzing the channel and storing a fresh snapshot..."):
                try:
                    payload = refresh_channel_insights(
                        channel_input.strip(),
                        force_refresh=force_refresh,
                        topic_mode=st.session_state.get("channel_insights_topic_mode", TOPIC_MODE_HEURISTIC),
                    )
                except Exception as exc:
                    st.session_state["channel_insights_error"] = str(exc)
                else:
                    st.session_state["channel_insights_selected_channel"] = payload["channel"]["channel_id"]
                    st.session_state.pop("channel_insights_error", None)
                    st.rerun()

    tracked_options = connected_channels
    selected_channel_id = st.session_state.get("channel_insights_selected_channel", "")
    if tracked_options and selected_channel_id not in {row["channel_id"] for row in tracked_options}:
        selected_channel_id = tracked_options[0]["channel_id"]
        st.session_state["channel_insights_selected_channel"] = selected_channel_id

    st.markdown('<div class="ci-card" style="margin-top:1rem;"><div class="ci-card-title">Workspace</div>', unsafe_allow_html=True)
    if tracked_options:
        choice = st.selectbox(
            "Tracked channel",
            tracked_options,
            index=next((i for i, row in enumerate(tracked_options) if row["channel_id"] == selected_channel_id), 0),
            format_func=lambda row: row["channel_title"],
            help="Switch which stored channel loads in the tabs below.",
        )
        st.session_state["channel_insights_selected_channel"] = choice["channel_id"]
    else:
        st.markdown(
            "<div class='ci-empty'>No tracked channels yet. Run <strong>Start analysis</strong> above to add one.</div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<div class="ci-summary-grid" style="margin-top:0.75rem;">'
        f'<div class="ci-summary-item"><div class="ci-summary-label">Tracked count</div>'
        f'<div class="ci-summary-value">{len(connected_channels)}</div></div>'
        '<div class="ci-summary-item"><div class="ci-summary-label">Snapshots</div>'
        '<div class="ci-summary-value">Manual refresh</div></div>'
        '<div class="ci-summary-item"><div class="ci-summary-label">Scope</div>'
        '<div class="ci-summary-value">Public only</div></div>'
        "</div>"
        '<div class="ci-note" style="margin-top:0.75rem;">'
        "Topic trends, outliers, and recommendations update when you refresh a channel snapshot.</div></div>",
        unsafe_allow_html=True,
    )


def _render_summary_action_row(payload: Dict[str, Any]) -> None:
    channel = payload["channel"]
    summary = payload["summary"]
    topic_mode_used = summary.get("topic_mode_used", TOPIC_MODE_HEURISTIC)
    topic_mode_requested = summary.get("topic_mode_requested", TOPIC_MODE_HEURISTIC)
    topic_model_message = summary.get("topic_model_message", "")
    topic_model_failure_reason = summary.get("topic_model_failure_reason", "")
    artifact_status = payload.get("topic_artifact_status") or get_bertopic_artifact_status()
    art_state = _artifact_status_label(getattr(artifact_status, "state", "disabled"))
    bundle_ver = str(summary.get("topic_model_bundle_version", "") or "Not loaded")

    st.markdown(
        f'<div class="ci-card">'
        f'<div class="ci-source-pill">{escape(payload["source"].replace("_", " ").title())}</div>'
        f'<div class="ci-card-title" style="margin-top:0.65rem;">{escape(channel["channel_title"])}</div>'
        f'<div class="ci-card-copy">Latest snapshot: {escape(payload["snapshot_at"])}<br/>'
        f"Topic mode applied: {escape(_topic_mode_label(topic_mode_used))}</div></div>",
        unsafe_allow_html=True,
    )

    action_row = st.columns(2, gap="small")
    with action_row[0]:
        if st.button("Refresh snapshot", type="secondary", use_container_width=True):
            with st.spinner("Refreshing channel insights and writing a new snapshot..."):
                try:
                    fresh_payload = refresh_channel_insights(
                        channel["channel_id"],
                        force_refresh=False,
                        topic_mode=st.session_state.get("channel_insights_topic_mode", TOPIC_MODE_HEURISTIC),
                    )
                except Exception as exc:
                    st.session_state["channel_insights_error"] = str(exc)
                else:
                    st.session_state["channel_insights_selected_channel"] = fresh_payload["channel"]["channel_id"]
                    st.session_state.pop("channel_insights_error", None)
                    st.rerun()
    with action_row[1]:
        st.link_button("Open channel", channel["canonical_url"], use_container_width=True)

    with st.expander("Topic model details (requested vs applied)", expanded=False):
        st.markdown(
            f"- **Requested:** {_topic_mode_label(topic_mode_requested)}  \n"
            f"- **Applied:** {_topic_mode_label(topic_mode_used)}  \n"
            f"- **Artifact:** {art_state}  \n"
            f"- **Bundle:** {bundle_ver}"
        )
        if topic_model_message:
            st.caption(topic_model_message)
    if topic_mode_requested == TOPIC_MODE_BERTOPIC_OPTIONAL and topic_mode_used != TOPIC_MODE_BERTOPIC_OPTIONAL:
        st.warning(topic_model_failure_reason or "BERTopic beta mode could not run for this snapshot, so the page fell back to heuristic topics.")

    deltas = payload.get("history_delta", {})
    _render_summary_kpi_cards(summary, deltas)


def _render_overview_tab(payload: Dict[str, Any]) -> None:
    summary = payload["summary"]
    recommendations = payload.get("recommendations", {})
    topic_metrics_df = _display_topic_metrics_df(payload)
    duration_metrics_df = payload.get("duration_metrics_df", pd.DataFrame())
    ai_actions = _generate_channel_insights_text(payload, "overview_actions", _overview_actions_prompt(payload, topic_metrics_df))

    overview_cols = st.columns([1.15, 1], gap="large")
    with overview_cols[0]:
        st.markdown(
            f'<div class="ci-card">'
            '<div class="ci-card-title">What The Channel Is Signaling Right Now</div>'
            f"<div class=\"ci-card-copy\">{escape(recommendations.get('summary', 'Refresh the channel to generate grounded summary signals.'))}</div>"
            '<div class="ci-summary-grid">'
            f'<div class="ci-summary-item"><div class="ci-summary-label">Best Duration Bucket</div>'
            f'<div class="ci-summary-value">{escape(summary.get("best_duration_bucket", "N/A"))}</div></div>'
            f'<div class="ci-summary-item"><div class="ci-summary-label">Best Title Pattern</div>'
            f'<div class="ci-summary-value">{escape(summary.get("best_title_pattern", "N/A"))}</div></div>'
            f'<div class="ci-summary-item"><div class="ci-summary-label">Shorts Share</div>'
            f'<div class="ci-summary-value">{_format_pct(summary.get("shorts_ratio", 0))}</div></div>'
            f'<div class="ci-summary-item"><div class="ci-summary-label">Median Engagement</div>'
            f'<div class="ci-summary-value">{_format_pct(summary.get("median_engagement", 0))}</div></div>'
            '<div class="ci-summary-item"><div class="ci-summary-label">Analytics Scope</div>'
            '<div class="ci-summary-value">Public Only</div></div>'
            f'<div class="ci-summary-item"><div class="ci-summary-label">Topic Source</div>'
            f'<div class="ci-summary-value">{escape(_topic_mode_label(summary.get("topic_mode_used", TOPIC_MODE_HEURISTIC)))}</div></div>'
            "</div></div>",
            unsafe_allow_html=True,
        )

        fallback_actions = recommendations.get("actions", [])
        if ai_actions:
            _render_ai_card("Recommended Next Actions", ai_actions)
        elif fallback_actions:
            action_markup = "<ul class='ci-list'>" + "".join(f"<li>{escape(action)}</li>" for action in fallback_actions) + "</ul>"
            st.markdown(
                f'<div class="ci-card"><div class="ci-card-title">Recommended Next Actions</div>{action_markup}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<div class='ci-empty'>Refresh the channel to generate action recommendations.</div>", unsafe_allow_html=True)

    with overview_cols[1]:
        if not topic_metrics_df.empty:
            topic_fig = plotly_bar_chart(
                topic_metrics_df.head(8).sort_values("trend_score", ascending=True),
                x="topic_label",
                y="trend_score",
                title="Rising Themes In The Current Window",
                horizontal=True,
            )
            show_plotly_chart(topic_fig)

        if not duration_metrics_df.empty:
            duration_fig = plotly_bar_chart(
                duration_metrics_df.sort_values("median_views_per_day", ascending=True),
                x="duration_bucket",
                y="median_views_per_day",
                title="Winning Duration Buckets",
                horizontal=True,
            )
            show_plotly_chart(duration_fig)

        if summary.get("topic_mode_requested") == TOPIC_MODE_BERTOPIC_OPTIONAL and summary.get("topic_mode_used") != TOPIC_MODE_BERTOPIC_OPTIONAL:
            st.caption(summary.get("topic_model_failure_reason") or "BERTopic beta mode fell back to the heuristic topic flow.")


def _render_topic_trends_tab(payload: Dict[str, Any]) -> None:
    topic_metrics_df = _display_topic_metrics_df(payload)
    if topic_metrics_df.empty:
        st.markdown("<div class='ci-empty'>This channel needs more public uploads before theme clustering becomes stable.</div>", unsafe_allow_html=True)
        return

    topic_insight_text = _generate_channel_insights_text(payload, "topic_trends", _topic_trends_prompt(payload, topic_metrics_df))
    if topic_insight_text:
        _render_ai_card("AI Topic Trend Insights", topic_insight_text)

    styled_dataframe(
        topic_metrics_df[
            ["topic_label", "video_count", "median_views_per_day", "outlier_count", "trend_score", "avg_engagement"]
        ],
        title="Topic Cluster Performance",
        precision=2,
    )

    chart_cols = st.columns(2, gap="large")
    with chart_cols[0]:
        trend_fig = plotly_bar_chart(
            topic_metrics_df.head(10).sort_values("trend_score", ascending=True),
            x="topic_label",
            y="trend_score",
            title="Theme Momentum",
            horizontal=True,
        )
        show_plotly_chart(trend_fig)
    with chart_cols[1]:
        views_fig = plotly_bar_chart(
            topic_metrics_df.head(10).sort_values("median_views_per_day", ascending=True),
            x="topic_label",
            y="median_views_per_day",
            title="Median Views / Day By Theme",
            horizontal=True,
        )
        show_plotly_chart(views_fig)

    top_topics = topic_metrics_df["topic_label"].head(10).tolist()
    if top_topics:
        st.markdown("**Theme Vocabulary**")
        styled_keyword_chips(top_topics)


def _render_formats_tab(payload: Dict[str, Any]) -> None:
    duration_metrics_df = payload.get("duration_metrics_df", pd.DataFrame())
    title_pattern_metrics_df = payload.get("title_pattern_metrics_df", pd.DataFrame())
    publish_day_metrics_df = payload.get("publish_day_metrics_df", pd.DataFrame())
    publish_hour_metrics_df = payload.get("publish_hour_metrics_df", pd.DataFrame())
    format_insight_text = _generate_channel_insights_text(payload, "formats_patterns", _formats_prompt(payload))

    if format_insight_text:
        _render_ai_card("AI Format & Pattern Insights", format_insight_text)

    top_cols = st.columns(2, gap="large")
    with top_cols[0]:
        if not duration_metrics_df.empty:
            styled_dataframe(duration_metrics_df, title="Duration Performance", precision=2)
    with top_cols[1]:
        if not title_pattern_metrics_df.empty:
            styled_dataframe(title_pattern_metrics_df, title="Title Pattern Performance", precision=2)

    bottom_cols = st.columns(2, gap="large")
    with bottom_cols[0]:
        if not publish_day_metrics_df.empty:
            day_fig = plotly_bar_chart(
                publish_day_metrics_df.sort_values("median_views_per_day", ascending=True),
                x="publish_day",
                y="median_views_per_day",
                title="Best Publish Days",
                horizontal=True,
            )
            show_plotly_chart(day_fig)
    with bottom_cols[1]:
        if not publish_hour_metrics_df.empty:
            hour_fig = plotly_line_chart(
                publish_hour_metrics_df,
                x="publish_hour",
                y_cols=["median_views_per_day", "videos"],
                title="Publish Hour Signal",
                secondary_y=["videos"],
            )
            show_plotly_chart(hour_fig)


def _render_outliers_tab(payload: Dict[str, Any]) -> None:
    outliers_df = _display_videos_df(payload.get("outliers_df", pd.DataFrame()))
    underperformers_df = _display_videos_df(payload.get("underperformers_df", pd.DataFrame()))
    outlier_cols = st.columns(2, gap="large")
    with outlier_cols[0]:
        st.markdown("**Recent Outliers**")
        if outliers_df.empty:
            st.markdown("<div class='ci-empty'>No strong outliers have been detected in the current window yet.</div>", unsafe_allow_html=True)
        else:
            styled_dataframe(
                outliers_df[["video_title", "primary_topic", "views", "views_per_day", "performance_score", "why_it_worked"]],
                title=None,
                precision=2,
            )
    with outlier_cols[1]:
        st.markdown("**Underperformers**")
        if underperformers_df.empty:
            st.markdown("<div class='ci-empty'>No low-signal videos are available for comparison yet.</div>", unsafe_allow_html=True)
        else:
            styled_dataframe(
                underperformers_df[["video_title", "primary_topic", "views", "views_per_day", "performance_score", "why_it_lagged"]],
                title=None,
                precision=2,
            )


def _render_theme_cards(title: str, rows: Iterable[Dict[str, Any]], channel_title: str) -> None:
    st.markdown(f"**{title}**")
    items = list(rows)
    if not items:
        st.markdown("<div class='ci-empty'>No theme recommendations are available yet.</div>", unsafe_allow_html=True)
        return

    for item in items:
        st.markdown(
            f'<div class="ci-theme-card">'
            f'<div class="ci-theme-title">{escape(str(item.get("theme", "Theme")))}</div>'
            f'<div class="ci-theme-copy">{escape(str(item.get("rationale", "")))}</div>'
            f'<div class="ci-theme-copy" style="margin-top:0.35rem;color:#6e6e73;">{escape(str(item.get("action", "")))}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )
        theme = str(item.get("theme", "")).strip()
        if theme:
            if st.button(f"Send '{theme}' To Outlier Finder", key=f"channel_insights_theme_{title}_{theme}", use_container_width=True):
                _queue_outlier_finder_theme(theme, channel_title)


def _render_next_topics_tab(payload: Dict[str, Any]) -> None:
    recommendations = payload.get("recommendations", {})
    channel_title = payload["channel"]["channel_title"]
    columns = st.columns(3, gap="large")
    with columns[0]:
        _render_theme_cards("Double Down", recommendations.get("double_down", []), channel_title)
    with columns[1]:
        _render_theme_cards("Avoid Or Repackage", recommendations.get("avoid", []), channel_title)
    with columns[2]:
        _render_theme_cards("Test Next", recommendations.get("test_next", []), channel_title)

    st.markdown("**Suggested Video Directions**")
    ideas = recommendations.get("video_ideas", [])
    if ideas:
        for item in ideas:
            st.markdown(
                f'<div class="ci-theme-card">'
                f'<div class="ci-theme-title">{escape(str(item.get("title", "Idea")))}</div>'
                f'<div class="ci-theme-copy">{escape(str(item.get("why_now", "")))}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown("<div class='ci-empty'>No grounded ideas are available yet.</div>", unsafe_allow_html=True)

    ai_overlay = recommendations.get("ai_overlay", "")
    if ai_overlay:
        st.markdown("**AI Explanation Layer**")
        st.markdown(ai_overlay)


def _render_history_tab(payload: Dict[str, Any]) -> None:
    history_df = payload.get("history_df", pd.DataFrame())
    if history_df.empty:
        st.markdown("<div class='ci-empty'>Refresh the connected channel again later to unlock historical comparison.</div>", unsafe_allow_html=True)
        return

    styled_dataframe(history_df, title="Snapshot History", precision=2)
    if len(history_df) > 1:
        history_line = history_df.sort_values("snapshot_at").copy()
        history_line["snapshot_at"] = pd.to_datetime(history_line["snapshot_at"], errors="coerce")
        fig = plotly_line_chart(
            history_line,
            x="snapshot_at",
            y_cols=["median_views_per_day", "recent_outlier_count"],
            title="Snapshot Trendline",
            secondary_y=["recent_outlier_count"],
        )
        show_plotly_chart(fig)


def render() -> None:
    _inject_channel_insights_css()

    connected_channels = list_connected_channels()
    _render_connect_card(connected_channels)

    error_message = st.session_state.get("channel_insights_error")
    if error_message:
        st.error(error_message)

    selected_channel_id = st.session_state.get("channel_insights_selected_channel")
    if not selected_channel_id:
        st.markdown(
            "<div class='ci-empty'>Add a public channel above to build your first persisted insight snapshot. This workflow is designed for recurring manual refreshes now, with true scheduled daily monitoring reserved for a later phase.</div>",
            unsafe_allow_html=True,
        )
        return

    payload = load_channel_insights(selected_channel_id)
    if not payload:
        st.markdown(
            "<div class='ci-empty'>This tracked channel does not have a usable stored snapshot yet. Refresh the analysis to generate one.</div>",
            unsafe_allow_html=True,
        )
        return

    _render_summary_action_row(payload)

    tabs = st.tabs(["Overview", "Topic Trends", "Formats & Patterns", "Outliers", "Next Topics", "History"])
    with tabs[0]:
        _render_overview_tab(payload)
    with tabs[1]:
        _render_topic_trends_tab(payload)
    with tabs[2]:
        _render_formats_tab(payload)
    with tabs[3]:
        _render_outliers_tab(payload)
    with tabs[4]:
        _render_next_topics_tab(payload)
    with tabs[5]:
        _render_history_tab(payload)
