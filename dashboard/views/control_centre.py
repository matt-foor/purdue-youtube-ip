from __future__ import annotations

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
                st.markdown(f"**{title}**")
                st.caption(description)
                st.page_link(
                    page=page_obj,
                    label=f"Open {title}",
                    icon=icon,
                    use_container_width=True,
                )
