import streamlit as st

from src.services.google_oauth_service import (
    clear_google_oauth_session,
    get_google_oauth_client_config,
    get_google_oauth_redirect_uri,
    oauth_configured,
)


def test_google_oauth_config_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("GOOGLE_OAUTH_REDIRECT_URI", "https://example.streamlit.app/")

    config = get_google_oauth_client_config()

    assert config["web"]["client_id"] == "client-id"
    assert get_google_oauth_redirect_uri() == "https://example.streamlit.app/"
    assert oauth_configured() is True


def test_clear_google_oauth_session() -> None:
    st.session_state["google_oauth_credentials"] = {"token": "abc"}
    st.session_state["google_oauth_profile"] = {"email": "creator@example.com"}
    st.session_state["google_oauth_state"] = "state123"

    clear_google_oauth_session()

    assert "google_oauth_credentials" not in st.session_state
    assert "google_oauth_profile" not in st.session_state
    assert "google_oauth_state" not in st.session_state
