from __future__ import annotations

import json
import os
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
try:
    from google_auth_oauthlib.flow import Flow
except Exception:  # pragma: no cover - import guard for environments missing the extra dependency
    Flow = None


GOOGLE_OAUTH_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

_SESSION_CREDENTIALS_KEY = "google_oauth_credentials"
_SESSION_PROFILE_KEY = "google_oauth_profile"
_SESSION_STATE_KEY = "google_oauth_state"


def _secret_values() -> Dict[str, Any]:
    try:
        return dict(st.secrets)
    except Exception:
        return {}


def _read_setting(name: str) -> str:
    secrets_map = _secret_values()
    value = secrets_map.get(name)
    if value is None:
        value = os.getenv(name, "")
    return str(value or "").strip()


def oauth_configured() -> bool:
    return bool(get_google_oauth_client_config()) and bool(get_google_oauth_redirect_uri())


def get_google_oauth_redirect_uri() -> str:
    redirect_uri = _read_setting("GOOGLE_OAUTH_REDIRECT_URI")
    if redirect_uri:
        return redirect_uri
    return ""


def get_google_oauth_client_config() -> Dict[str, Any]:
    raw_json = _read_setting("GOOGLE_OAUTH_CLIENT_CONFIG_JSON")
    if raw_json:
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise RuntimeError("GOOGLE_OAUTH_CLIENT_CONFIG_JSON is not valid JSON.") from exc
        if "web" in parsed:
            return parsed
        return {"web": parsed}

    client_id = _read_setting("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = _read_setting("GOOGLE_OAUTH_CLIENT_SECRET")
    redirect_uri = get_google_oauth_redirect_uri()
    if not client_id or not client_secret or not redirect_uri:
        return {}

    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }


def _flow(state: Optional[str] = None) -> Flow:
    if Flow is None:
        raise RuntimeError(
            "Missing dependency: google-auth-oauthlib. Install with: python3 -m pip install google-auth-oauthlib"
        )
    client_config = get_google_oauth_client_config()
    redirect_uri = get_google_oauth_redirect_uri()
    if not client_config or not redirect_uri:
        raise RuntimeError(
            "Google OAuth is not configured. Add GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, "
            "and GOOGLE_OAUTH_REDIRECT_URI to Streamlit secrets or environment variables."
        )
    flow = Flow.from_client_config(client_config, scopes=GOOGLE_OAUTH_SCOPES, state=state)
    flow.redirect_uri = redirect_uri
    return flow


def _credentials_to_dict(credentials: Credentials) -> Dict[str, Any]:
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes or GOOGLE_OAUTH_SCOPES),
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
    }


def _credentials_from_session(payload: Dict[str, Any]) -> Credentials:
    expiry_raw = payload.get("expiry")
    expiry = None
    if expiry_raw:
        try:
            expiry = datetime.fromisoformat(str(expiry_raw))
        except Exception:
            expiry = None
    return Credentials(
        token=payload.get("token"),
        refresh_token=payload.get("refresh_token"),
        token_uri=payload.get("token_uri"),
        client_id=payload.get("client_id"),
        client_secret=payload.get("client_secret"),
        scopes=payload.get("scopes") or GOOGLE_OAUTH_SCOPES,
        expiry=expiry,
    )


def build_google_authorization_url() -> str:
    flow = _flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    st.session_state[_SESSION_STATE_KEY] = state or secrets.token_urlsafe(24)
    return authorization_url


def _query_value(name: str) -> str:
    try:
        value = st.query_params.get(name, "")
    except Exception:
        return ""
    if isinstance(value, list):
        return str(value[0] if value else "").strip()
    return str(value or "").strip()


def fetch_google_profile(credentials: Credentials) -> Dict[str, Any]:
    if not credentials or not credentials.token:
        return {}
    try:
        response = requests.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
            timeout=20,
        )
        if response.status_code >= 400:
            return {}
        return response.json()
    except Exception:
        return {}


def complete_google_oauth_callback() -> Optional[Dict[str, Any]]:
    code = _query_value("code")
    error = _query_value("error")
    if error:
        try:
            st.query_params.clear()
        except Exception:
            pass
        raise RuntimeError(f"Google OAuth was not completed: {error}")
    if not code:
        return None

    returned_state = _query_value("state")
    expected_state = str(st.session_state.get(_SESSION_STATE_KEY, "") or "")
    if expected_state and returned_state and returned_state != expected_state:
        try:
            st.query_params.clear()
        except Exception:
            pass
        raise RuntimeError("Google OAuth state validation failed. Start the sign-in flow again.")

    flow = _flow(state=returned_state or None)
    flow.fetch_token(code=code)
    credentials = flow.credentials
    st.session_state[_SESSION_CREDENTIALS_KEY] = _credentials_to_dict(credentials)
    profile = fetch_google_profile(credentials)
    st.session_state[_SESSION_PROFILE_KEY] = profile
    st.session_state.pop(_SESSION_STATE_KEY, None)
    try:
        st.query_params.clear()
    except Exception:
        pass
    return profile


def clear_google_oauth_session() -> None:
    st.session_state.pop(_SESSION_CREDENTIALS_KEY, None)
    st.session_state.pop(_SESSION_PROFILE_KEY, None)
    st.session_state.pop(_SESSION_STATE_KEY, None)


def get_google_credentials() -> Optional[Credentials]:
    payload = st.session_state.get(_SESSION_CREDENTIALS_KEY)
    if not isinstance(payload, dict) or not payload.get("token"):
        return None

    credentials = _credentials_from_session(payload)
    if credentials.expired:
        if not credentials.refresh_token:
            clear_google_oauth_session()
            return None
        try:
            credentials.refresh(Request())
        except Exception:
            clear_google_oauth_session()
            return None
        st.session_state[_SESSION_CREDENTIALS_KEY] = _credentials_to_dict(credentials)
    return credentials


def get_google_profile() -> Dict[str, Any]:
    profile = st.session_state.get(_SESSION_PROFILE_KEY)
    if isinstance(profile, dict):
        return profile
    return {}


def oauth_ready_error() -> str:
    return (
        "Google OAuth is not configured yet. Add GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, "
        "and GOOGLE_OAUTH_REDIRECT_URI to secrets before enabling owner analytics."
    )


def oauth_scope_labels() -> List[str]:
    return [
        "Google Sign-In",
        "YouTube Read-Only Channel Access",
        "YouTube Analytics Read-Only Access",
    ]
