"""Download Hub: merged thumbnails + public media downloads in one page."""

from __future__ import annotations

import streamlit as st

from dashboard.components.visualizations import graph_insight_expander
from dashboard.views import recommendations, tools


def _inject_hub_shell_css() -> None:
    """Light wrapper so hub-level content matches dashboard glass rhythm."""
    st.markdown(
        """
        <style>
        .download-hub-page {
            max-width: var(--app-page-width);
            margin: 0 auto;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render() -> None:
    _inject_hub_shell_css()
    st.markdown('<div class="download-hub-page">', unsafe_allow_html=True)

    graph_insight_expander(
        "Download Hub overview",
        """
This page brings **thumbnail** workflows and **public YouTube media downloads** into one place.

- **Thumbnails** — Generate new concepts with Gemini or OpenAI, or **export the public thumbnail** from any video URL.  
- **Video downloads** — Fetch **one video**, **many URLs**, or a **playlist**, then download thumbnail assets, transcripts, audio, or video (where available).

All steps below use the same light glass styling as the rest of the app. Open **Instructions** in each section below for detailed steps.
        """,
        for_instructions=True,
    )

    tab_thumbs, tab_video = st.tabs(["Thumbnails", "Video downloads"])
    with tab_thumbs:
        recommendations.render_thumbnail_workspace()
    with tab_video:
        tools.render_media_workspace()

    st.markdown("</div>", unsafe_allow_html=True)
