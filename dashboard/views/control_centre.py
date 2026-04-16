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
        .control-centre-card-stack {
            margin-bottom: 1.15rem;
        }
        .control-centre-card-panel {
            border-radius: 18px;
            padding: 1rem 1.05rem 0.95rem;
            margin-bottom: 0.65rem;
            background: linear-gradient(
                165deg,
                rgba(246, 251, 255, 0.96),
                rgba(228, 240, 252, 0.9)
            );
            border: 1px solid rgba(0, 113, 227, 0.38);
            box-shadow:
                0 10px 32px rgba(0, 113, 227, 0.14),
                inset 0 1px 0 rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .control-centre-card-panel:hover {
            border-color: rgba(0, 113, 227, 0.55);
            box-shadow:
                0 14px 40px rgba(0, 113, 227, 0.18),
                inset 0 1px 0 rgba(255, 255, 255, 1);
        }
        .control-centre-card-panel-title {
            font-weight: 800;
            font-size: 1.06rem;
            color: #14161b;
            margin: 0 0 0.4rem;
            font-family: var(--app-font-display);
        }
        .control-centre-card-panel-desc {
            font-size: 0.93rem;
            color: #4e5563;
            line-height: 1.48;
            margin: 0;
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
            st.markdown(
                f"""
                <div class="control-centre-card-stack">
                    <div class="control-centre-card-panel">
                        <div class="control-centre-card-panel-title">{escape(title)}</div>
                        <p class="control-centre-card-panel-desc">{escape(description)}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                f"Open {title}",
                type="primary",
                icon=icon,
                use_container_width=True,
                key=f"cc_workspace_open_{idx}",
            ):
                st.switch_page(page_obj)
