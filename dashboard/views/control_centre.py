from __future__ import annotations

from typing import Sequence, Tuple, Any

import streamlit as st


def _inject_control_centre_css() -> None:
    st.markdown(
        """
        <style>
        .control-centre-wrap {
            max-width: var(--app-page-width);
            margin: 0 auto 1rem;
        }
        .control-centre-hero {
            position: relative;
            border-radius: 26px;
            padding: 1.5rem 1.4rem 1.35rem;
            background: linear-gradient(165deg, rgba(255,255,255,0.97), rgba(238,243,251,0.93));
            border: 1px solid rgba(0, 0, 0, 0.1);
            box-shadow: 0 18px 48px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255,255,255,0.98);
            overflow: hidden;
        }
        .control-centre-hero::before {
            content: "";
            position: absolute;
            inset: -30% -10% auto auto;
            width: 380px;
            height: 380px;
            background: radial-gradient(circle, rgba(230,0,18,0.18), rgba(0,113,227,0.08) 48%, transparent 68%);
            pointer-events: none;
        }
        .control-centre-brand-row {
            display: flex;
            align-items: center;
            gap: 1rem;
            position: relative;
            z-index: 2;
        }
        .control-centre-logo {
            width: 84px;
            height: 84px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            background: linear-gradient(165deg, #ff5b5b, #ff0000 54%, #b20012);
            color: #fff;
            font-weight: 900;
            letter-spacing: 0.03em;
            box-shadow: 0 0 0 7px rgba(255,255,255,0.75), 0 0 34px rgba(230,0,18,0.35), inset 0 -8px 16px rgba(0,0,0,0.25);
        }
        .control-centre-kicker {
            font-size: 12px;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: #5b6170;
            font-weight: 700;
        }
        .control-centre-title {
            margin-top: 0.15rem;
            font-size: clamp(30px, 4vw, 46px);
            line-height: 1.06;
            font-weight: 900;
            color: #17181c;
        }
        .control-centre-copy {
            margin-top: 0.4rem;
            color: #373d4a;
            font-size: 17px;
            line-height: 1.55;
            max-width: 920px;
        }
        .control-centre-note {
            margin-top: 0.9rem;
            border-radius: 16px;
            border: 1px solid rgba(0, 113, 227, 0.22);
            background: linear-gradient(165deg, rgba(236,245,255,0.95), rgba(247,251,255,0.92));
            padding: 0.85rem 1rem;
            color: #1f3d64;
            font-size: 14px;
            line-height: 1.5;
            max-width: 920px;
        }
        .control-centre-pillars {
            margin-top: 1rem;
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
        }
        .control-centre-pillar {
            border-radius: 14px;
            border: 1px solid rgba(0, 0, 0, 0.08);
            background: rgba(255,255,255,0.9);
            padding: 0.72rem 0.85rem;
        }
        .control-centre-pillar-title {
            font-weight: 800;
            color: #17181c;
            margin-bottom: 0.2rem;
        }
        .control-centre-pillar-copy {
            font-size: 13px;
            color: #4e5563;
            line-height: 1.4;
        }
        .control-centre-nav-head {
            margin: 1rem 0 0.45rem;
            font-size: 22px;
            font-weight: 900;
            color: #17181c;
        }
        .control-centre-nav-copy {
            color: #4e5563;
            margin-bottom: 0.7rem;
        }
        @media (max-width: 920px) {
            .control-centre-pillars {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render(nav_targets: Sequence[Tuple[str, str, Any, str]]) -> None:
    _inject_control_centre_css()

    st.markdown(
        """
        <div class="control-centre-wrap">
            <div class="control-centre-hero">
                <div class="control-centre-brand-row">
                    <div class="control-centre-logo">YC</div>
                    <div>
                        <div class="control-centre-kicker">YCreator Control Centre</div>
                        <div class="control-centre-title">Everything starts here.</div>
                    </div>
                </div>
                <div class="control-centre-copy">
                    YCreator is your premium workspace for YouTube creator intelligence: benchmark categories,
                    track channel-level performance, find outlier winners, and turn public signals into practical
                    content decisions without jumping between disconnected tools.
                </div>
                <div class="control-centre-note">
                    <strong>How to use this hub:</strong> pick a destination below based on your current objective.
                    Each module has a focused workflow with guided visuals, explainable metrics, and glass-style controls.
                </div>
                <div class="control-centre-pillars">
                    <div class="control-centre-pillar">
                        <div class="control-centre-pillar-title">Benchmark First</div>
                        <div class="control-centre-pillar-copy">Start with category-level signals to understand where momentum already exists.</div>
                    </div>
                    <div class="control-centre-pillar">
                        <div class="control-centre-pillar-title">Go Channel-Deep</div>
                        <div class="control-centre-pillar-copy">Move to channel snapshots and creator workspaces to diagnose what is driving outcomes.</div>
                    </div>
                    <div class="control-centre-pillar">
                        <div class="control-centre-pillar-title">Turn Insight Into Action</div>
                        <div class="control-centre-pillar-copy">Use outlier and download tools to convert findings into testable content decisions.</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="control-centre-nav-head">Choose your workspace</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="control-centre-nav-copy">Use these selector buttons to jump directly to the page that fits your current creator task.</div>',
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
