from __future__ import annotations

from html import escape
from typing import Any, Sequence, Tuple

import streamlit as st

# Fixed card height so every Control Centre feature reads as the same symmetric glass tile.
_CC_CARD_HEIGHT_PX = 280


def _inject_control_centre_css() -> None:
    st.markdown(
        """
        <style>
        .control-centre-below {
            max-width: var(--app-page-width);
            margin: 0 auto 1rem;
        }
        .control-centre-note {
            margin: 0 auto 1.1rem;
            max-width: 920px;
            border-radius: var(--app-radius-md);
            border: 1px solid rgba(0, 113, 227, 0.22);
            background: linear-gradient(165deg, rgba(236,245,255,0.95), rgba(247,251,255,0.92));
            padding: 0.9rem 1.05rem;
            color: #1f3d64;
            font-size: 14px;
            line-height: 1.55;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
        }
        .control-centre-nav-head {
            margin: 0.35rem 0 0.4rem;
            font-size: 1.35rem;
            font-weight: 800;
            color: #17181c;
            font-family: var(--app-font-display);
        }
        .control-centre-nav-copy {
            color: #4e5563;
            margin-bottom: 0.75rem;
            max-width: 920px;
        }
        /*
         * Scope layout fixes by :has(.cc-feature-card-title) — not by section[data-testid="stMain"].
         * Streamlit 1.40+ often omits stMain as an ancestor for column/border blocks, so stMain-scoped
         * rules silently never match on Cloud (cards stay 50% width, buttons stay full-width).
         */
        [data-testid="stHorizontalBlock"]:has(.cc-feature-card-title) {
            justify-content: center !important;
            align-items: flex-start !important;
            flex-wrap: wrap !important;
            gap: 1.25rem !important;
            width: 100% !important;
        }
        [data-testid="stHorizontalBlock"]:has(.cc-feature-card-title) [data-testid="column"] {
            flex: 0 1 auto !important;
            width: auto !important;
            min-width: 0 !important;
            max-width: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
        }
        /* Uniform glass cards — only blocks that contain Control Centre card titles. */
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) {
            margin-bottom: 0.9rem !important;
            width: fit-content !important;
            max-width: min(100%, 380px) !important;
            margin-left: auto !important;
            margin-right: auto !important;
            box-sizing: border-box !important;
            min-height: """
        + f"{_CC_CARD_HEIGHT_PX}px !important;\n            height: {_CC_CARD_HEIGHT_PX}px !important;\n"
        + """
            display: flex !important;
            flex-direction: column !important;
            padding: 0.9rem 1rem 0.95rem !important;
            border-radius: 18px !important;
            background: linear-gradient(
                165deg,
                rgba(246, 251, 255, 0.96),
                rgba(228, 240, 252, 0.9)
            ) !important;
            border: 1px solid rgba(0, 113, 227, 0.38) !important;
            box-shadow:
                0 10px 32px rgba(0, 113, 227, 0.14),
                inset 0 1px 0 rgba(255, 255, 255, 0.98) !important;
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title):hover {
            border-color: rgba(0, 113, 227, 0.55) !important;
            box-shadow:
                0 14px 40px rgba(0, 113, 227, 0.18),
                inset 0 1px 0 rgba(255, 255, 255, 1) !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) > div {
            flex: 1 1 auto !important;
            display: flex !important;
            flex-direction: column !important;
            min-height: 0 !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) [data-testid="stVerticalBlock"] {
            flex: 1 1 auto !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 0.35rem !important;
        }
        /* Pin primary action to bottom of the card */
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:last-child {
            margin-top: auto !important;
        }
        /* Streamlit wraps buttons in a full-width flex row; force content-sized CTA. */
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) div[data-testid="stElementContainer"]:has(.stButton) {
            width: fit-content !important;
            max-width: 100% !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) .stButton {
            width: fit-content !important;
            max-width: 100% !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) .stButton > button {
            width: auto !important;
            min-width: unset !important;
        }
        .cc-feature-card-title {
            font-family: var(--app-font-display);
            font-size: 1.12rem;
            font-weight: 800;
            color: #14161b;
            margin: 0 0 0.35rem;
            line-height: 1.25;
            max-width: 20rem;
        }
        .cc-feature-card-desc {
            font-size: 0.93rem;
            color: #4e5563;
            line-height: 1.48;
            margin: 0;
            flex: 1 1 auto;
            min-height: 3.25em;
            max-width: 20rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render(nav_targets: Sequence[Tuple[str, str, Any, str]]) -> None:
    _inject_control_centre_css()

    st.markdown(
        """
        <div class="control-centre-below">
            <div class="control-centre-note">
                <strong>How to use this hub:</strong> pick a destination below for your current task.
                Each module uses the same glass UI, explainable metrics, and guided layouts—start broad with
                categories, then go deeper on a single channel or breakout pattern.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="control-centre-nav-head">Choose your workspace</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="control-centre-nav-copy">Jump straight into the workflow you need—each card opens the matching page.</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(2, gap="medium")
    for idx, (title, description, page_obj, icon) in enumerate(nav_targets):
        with cols[idx % 2]:
            with st.container(height=_CC_CARD_HEIGHT_PX, border=True):
                st.markdown(
                    f'<div class="cc-feature-card-title">{escape(title)}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<p class="cc-feature-card-desc">{escape(description)}</p>',
                    unsafe_allow_html=True,
                )
                if st.button(
                    f"Open {title}",
                    type="primary",
                    icon=icon,
                    use_container_width=False,
                    key=f"cc_workspace_open_{idx}",
                ):
                    st.switch_page(page_obj)
