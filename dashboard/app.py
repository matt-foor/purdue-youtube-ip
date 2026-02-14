import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.components.sidebar import render_sidebar
from dashboard.pages import channel_analysis, recommendations


st.set_page_config(page_title="YouTube IP Dashboard", page_icon="📺", layout="wide")


page = render_sidebar()

if page == "Thumbnail Generator":
    recommendations.render()
elif page == "Dataset Overview":
    channel_analysis.render()
else:
    st.title("Deploy Notes")
    st.markdown(
        """
        ### Environment Variables
        - `GEMINI_API_KEY` for Gemini image generation
        - `OPENAI_API_KEY` for OpenAI image generation fallback

        ### Local Run
        ```bash
        source .venv/bin/activate
        streamlit run dashboard/app.py
        ```

        ### Streamlit Cloud
        1. Push this repo to GitHub.
        2. Create a new Streamlit app with entrypoint `dashboard/app.py`.
        3. Add secrets `GEMINI_API_KEY` and/or `OPENAI_API_KEY`.
        """
    )
