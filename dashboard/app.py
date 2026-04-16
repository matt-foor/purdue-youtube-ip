import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.components.layout import render_page_hero
from dashboard.components.sidebar import render_sidebar_footer, render_sidebar_header
from dashboard.components.intro_animation import inject_intro_animation
from dashboard.components.theme import inject_shared_theme
from dashboard.views import channel_analysis, channel_insights, download_hub, outlier_finder, ytuber


def _render_app_shell(page: str) -> None:
    """Glass feature hero: badge, headline, description, tags."""
    render_page_hero(page)


def _cleanup_retired_session_state() -> None:
    retired_prefixes = ("assistant_", "google_oauth_")
    retired_exact_keys = {"channel_insights_owned_channel", "app_page"}
    for key in list(st.session_state.keys()):
        if key in retired_exact_keys or key.startswith(retired_prefixes):
            st.session_state.pop(key, None)


def _page_channel_analysis() -> None:
    _render_app_shell("Channel Analysis")
    channel_analysis.render()


def _page_channel_insights() -> None:
    _render_app_shell("Channel Insights")
    channel_insights.render()


def _page_download_hub() -> None:
    _render_app_shell("Download Hub")
    download_hub.render()


def _page_outlier_finder() -> None:
    _render_app_shell("Outlier Finder")
    outlier_finder.render()


def _page_ytuber() -> None:
    _render_app_shell("Ytuber")
    ytuber.render()


def _page_deployment() -> None:
    render_page_hero("Deployment")
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
        - `Channel Analysis` uses the committed assets and configured AI providers already in the repo.
        - `Download Hub` combines thumbnail generation/export with public media downloads (see each tab for API and ffmpeg notes).
        - `Channel Insights` is public-only in this build and stores dated SQLite snapshots on manual refresh.
        - `Ytuber` remains available as part of the AI suite.
        - `Outlier Finder` remains a standalone research workflow.
        - `packages.txt` installs `ffmpeg` for Download Hub video and media flows.

        ### Alternate Entrypoint
        ```bash
        streamlit run dashboard/app.py
        ```
        """
    )


PAGE_CHANNEL_ANALYSIS = st.Page(
    _page_channel_analysis,
    title="Channel Analysis",
    icon="📊",
    default=True,
)
PAGE_CHANNEL_INSIGHTS = st.Page(_page_channel_insights, title="Channel Insights", icon="💡")
PAGE_DOWNLOAD_HUB = st.Page(_page_download_hub, title="Download Hub", icon="📥")
PAGE_OUTLIER_FINDER = st.Page(_page_outlier_finder, title="Outlier Finder", icon="🎯")
PAGE_YTUBER = st.Page(_page_ytuber, title="Ytuber", icon="🎬")
PAGE_DEPLOYMENT = st.Page(_page_deployment, title="Deployment", icon="🚀")


def run() -> None:
    """Execute the multipage router. Must run on every Streamlit script rerun (not only on first import)."""
    st.set_page_config(
        page_title="YouTube Creator Insights | Purdue × Google",
        page_icon="📺",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_shared_theme()
    inject_intro_animation()
    _cleanup_retired_session_state()

    with st.sidebar:
        render_sidebar_header()

    pg = st.navigation(
        [
            PAGE_CHANNEL_ANALYSIS,
            PAGE_CHANNEL_INSIGHTS,
            PAGE_DOWNLOAD_HUB,
            PAGE_OUTLIER_FINDER,
            PAGE_YTUBER,
            PAGE_DEPLOYMENT,
        ],
        expanded=True,
    )

    with st.sidebar:
        render_sidebar_footer()

    pg.run()


if __name__ == "__main__":
    run()
