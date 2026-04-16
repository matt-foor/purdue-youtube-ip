from __future__ import annotations

from html import escape
from typing import Any, Sequence, Tuple

import streamlit as st


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
            margin: 0.35rem auto 0.4rem;
            font-size: 1.35rem;
            font-weight: 800;
            color: #17181c;
            font-family: var(--app-font-display);
            text-align: center;
            max-width: 36rem;
        }
        .control-centre-nav-copy {
            color: #4e5563;
            margin: 0 auto 0.65rem;
            max-width: 36rem;
            text-align: center;
            text-wrap: balance;
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
            gap: 0.85rem 1.1rem !important;
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
        /* Compact glass cards: symmetric padding, single vertical axis for copy + CTA. */
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) {
            margin-bottom: 0.65rem !important;
            width: fit-content !important;
            max-width: min(100%, 22rem) !important;
            margin-left: auto !important;
            margin-right: auto !important;
            box-sizing: border-box !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            padding: 0.85rem 1rem !important;
            border-radius: 14px !important;
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
            flex: 0 0 auto !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            width: 100% !important;
            min-height: 0 !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) [data-testid="stVerticalBlock"] {
            flex: 0 0 auto !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            gap: 0.95rem !important;
            width: 100% !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) .stMarkdown {
            width: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) [data-testid="stMarkdownContainer"] {
            width: 100% !important;
            max-width: 19.5rem !important;
            margin-left: auto !important;
            margin-right: auto !important;
            text-align: center !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) [data-testid="stMarkdownContainer"] p {
            text-align: center !important;
        }
        /*
         * Primary CTA: Streamlit 1.53+ often drops the .stButton class from the outer wrapper, so
         * :has(.stButton) never matched and the inner row stayed left-aligned. Target :has(button) and
         * center the widget's immediate wrapper div (the wide horizontal flex row).
         */
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:has(button) {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:has(button) > div {
            width: 100% !important;
            display: flex !important;
            flex-direction: row !important;
            justify-content: center !important;
            align-items: center !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:has(button) .stButton,
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:has(button) [data-baseweb="button"] {
            width: auto !important;
            max-width: 100% !important;
            flex: 0 0 auto !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:has(button) button {
            width: auto !important;
            min-width: unset !important;
        }
        /* Some builds nest the widget in a nested horizontal flex block. */
        [data-testid="stVerticalBlockBorderWrapper"]:has(.cc-feature-card-title) [data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:has(button) [data-testid="stHorizontalBlock"] {
            justify-content: center !important;
            width: 100% !important;
        }
        .cc-feature-card-stack {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            gap: 0.7rem;
            width: 100%;
            max-width: 19.5rem;
            margin: 0 auto;
        }
        .cc-feature-card-title {
            font-family: var(--app-font-display);
            font-size: 1.08rem;
            font-weight: 800;
            color: #14161b;
            margin: 0;
            line-height: 1.3;
            width: 100%;
            text-align: center;
            text-wrap: balance;
        }
        .cc-feature-card-desc {
            font-size: 0.9rem;
            color: #4e5563;
            line-height: 1.5;
            margin: 0;
            width: 100%;
            text-align: center;
            text-wrap: balance;
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
            with st.container(border=True):
                st.markdown(
                    f'<div class="cc-feature-card-stack">'
                    f'<div class="cc-feature-card-title">{escape(title)}</div>'
                    f'<p class="cc-feature-card-desc">{escape(description)}</p>'
                    f"</div>",
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
