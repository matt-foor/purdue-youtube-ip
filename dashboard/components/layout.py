"""Shared shell: per-page feature heroes (badge → headline → description → tags)."""

from __future__ import annotations

from html import escape
from typing import Dict, List, Tuple

import streamlit as st


# Badge (ALL CAPS), headline, description, optional feature tags (glass pills)
PAGE_HERO: Dict[str, Tuple[str, str, str, Tuple[str, ...]]] = {
    "Channel Analysis": (
        "CHANNEL ANALYSIS",
        "Benchmark datasets and see which channels and videos actually move the needle.",
        "Filter committed CSVs, compare engagement across categories, and surface rankings, trends, and scatter insights—without leaving this workspace.",
        ("CSV benchmarks", "Engagement signals", "Portfolio view"),
    ),
    "Channel Insights": (
        "CHANNEL INSIGHTS",
        "Track public channel snapshots and turn real performance signals into better topic decisions.",
        "Add a public channel by URL, handle, or channel ID. Channel Insights stores manual snapshots over time, highlights the themes and formats that are working, and turns those signals into grounded next-topic ideas.",
        ("SQLite snapshots", "Heuristic & optional BERTopic", "Public API only"),
    ),
    "Download Hub": (
        "DOWNLOAD HUB",
        "One place for thumbnail ideas, exports, and public YouTube media downloads.",
        "Use the Thumbnails tab to generate concepts with your AI providers or pull the public thumbnail from any video. Switch to Video downloads for single links, batches, or playlists—metadata, transcripts, audio, and video where available.",
        ("Thumbnails & media", "Single & batch", "Consistent glass UI"),
    ),
    "Outlier Finder": (
        "OUTLIER FINDER",
        "Discover breakout videos before the niche catches up.",
        "Scan any topic, filter the noise, and surface overperforming videos with clear research signals. Review the winners first, understand the pattern next, and layer AI interpretation only after the evidence is visible.",
        (
            "Public YouTube API data",
            "Explainable outlier scoring",
            "Quota-aware query caching",
            "Structured AI research",
        ),
    ),
    "Ytuber": (
        "YTUBER",
        "Your live creator workspace for search, audits, AI studio, and planning.",
        "Search by handle, name, or channel ID—then move through audits, keyword intel, outliers, title lab, benchmarks, planner, and AI Studio in one continuous flow. Provider pools reflect your configured API keys.",
        ("YouTube Data API", "Multi-module workspace", "AI Studio"),
    ),
    "Deployment": (
        "DEPLOYMENT",
        "Run locally or ship to Streamlit Cloud with the same entrypoint everywhere.",
        "Use `streamlit_app.py` as the main file, install from `requirements.txt`, add `YOUTUBE` / `GEMINI` / `OPENAI` keys in Secrets, and use `packages.txt` for ffmpeg on Cloud when tools need it.",
        ("streamlit_app.py", "requirements.txt", "Secrets & packages"),
    ),
}


def render_page_hero(page: str) -> None:
    """Top-of-page glass hero: eyebrow → badge → headline → description → optional tags."""
    row = PAGE_HERO.get(page)
    if not row:
        return
    badge, headline, desc, tags = row
    tags_html = ""
    if tags:
        parts: List[str] = []
        for idx, t in enumerate(tags):
            cls = "feature-hero-tag"
            if idx % 3 == 0:
                cls += " feature-hero-tag--accent-r"
            elif idx % 3 == 1:
                cls += " feature-hero-tag--accent-b"
            parts.append(f'<span class="{cls}">{escape(t)}</span>')
        tags_html = f'<div class="feature-hero-tags">{"".join(parts)}</div>'

    st.markdown(
        f"""
<div class="glass-page-hero fade-in">
  <p class="product-eyebrow">YouTube Creator Insights <span class="product-eyebrow-sep">·</span> Purdue × Google</p>
  <div class="feature-badge">
    <span class="feature-badge-dot" aria-hidden="true"></span>
    {escape(badge)}
  </div>
  <h1 class="feature-headline">{escape(headline)}</h1>
  <p class="feature-description">{escape(desc)}</p>
  {tags_html}
</div>
""",
        unsafe_allow_html=True,
    )
