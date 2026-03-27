import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.components.sidebar import render_sidebar
from dashboard.components.theme import inject_shared_theme
from dashboard.views import channel_analysis, channel_insights, outlier_finder, recommendations, tools, ytuber


st.set_page_config(
    page_title="YouTube IP V5",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def _render_hero() -> None:
    st.markdown(
        """
            <div class="fade-in" style="margin-bottom: 1.0rem;">
            <div class="yt-page-title">YouTube IP V5</div>
            <div class="yt-page-subtitle">
                Cross-channel analytics, benchmarking, and AI-assisted planning for YouTube creators.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


inject_shared_theme()

def _cleanup_retired_session_state() -> None:
    retired_prefixes = ("assistant_", "google_oauth_")
    retired_exact_keys = {"channel_insights_owned_channel"}
    for key in list(st.session_state.keys()):
        if key in retired_exact_keys or key.startswith(retired_prefixes):
            st.session_state.pop(key, None)


_cleanup_retired_session_state()
page = render_sidebar()

if page in {"Channel Analysis", "Thumbnails"}:
    _render_hero()

if page == "Channel Analysis":
    channel_analysis.render()
elif page == "Thumbnails":
    recommendations.render()
elif page == "Channel Insights":
    channel_insights.render()
elif page == "Outlier Finder":
    outlier_finder.render()
elif page == "Ytuber":
    ytuber.render()
elif page == "Tools":
    tools.render()
else:
    st.title("Deployment")
    st.markdown(
        """
        Deploy this repo directly from GitHub to Streamlit Community Cloud.

        ### Local Run
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
        streamlit run streamlit_app.py
        ```

        ### Streamlit Cloud Settings
        - Repo: `royayushkr/Youtube-IP-V5`
        - Branch: `main`
        - Main file path: `streamlit_app.py`

        ### Secrets
        ```toml
        YOUTUBE_API_KEYS = ["youtube_key_1", "youtube_key_2"]
        GEMINI_API_KEYS = ["gemini_key_1", "gemini_key_2"]
        OPENAI_API_KEYS = ["openai_key_1", "openai_key_2"]
        ```

        Single-key fallbacks also work with `YOUTUBE_API_KEY`, `GEMINI_API_KEY`, and `OPENAI_API_KEY`.

        ### Notes
        - `dashboard/app.py` remains the main application module.
        - `streamlit_app.py` is the root-level deployment entrypoint for Streamlit Cloud.
        - `Channel Analysis` and `Thumbnails` use the committed assets and configured AI providers already in the repo.
        - `Channel Insights` is public-only in this build and stores dated SQLite snapshots on manual refresh.
        - `Ytuber` and `Tools` remain available as part of the AI suite.
        - `Outlier Finder` remains a standalone research workflow.
        - `packages.txt` installs `ffmpeg` for the Tools page media flows.

        ### Alternate Entrypoint
        ```bash
        streamlit run dashboard/app.py
        ```
        """
    )
