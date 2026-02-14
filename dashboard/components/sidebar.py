import streamlit as st


def render_sidebar() -> str:
    st.sidebar.title("YouTube IP Dashboard")
    st.sidebar.caption("Thumbnail generation + dataset analytics")
    page = st.sidebar.radio(
        "Navigate",
        ["Thumbnail Generator", "Dataset Overview", "Deploy Notes"],
        index=0,
    )
    st.sidebar.markdown("---")
    st.sidebar.info(
        "Set `GEMINI_API_KEY` or `OPENAI_API_KEY` in `.env` before generating thumbnails."
    )
    return page
