"""One-time per session intro: light shell + YouTube red, crossfades into the dashboard. Pure CSS."""

from __future__ import annotations

import streamlit as st

from dashboard.components.theme import NN_BG_LAYER_URL

_INTRO_SESSION_KEY = "_v6_intro_animation_shown"

# Matches theme.py stAppViewContainer (neural tile + mesh) for a seamless handoff.
_INTRO_BG = f"""
  background-color: #f5f5f7;
  background-image:
    {NN_BG_LAYER_URL},
    radial-gradient(ellipse 100% 80% at 50% -30%, rgba(0, 113, 227, 0.11), transparent 55%),
    radial-gradient(ellipse 70% 50% at 100% 20%, rgba(230, 0, 18, 0.07), transparent 50%),
    radial-gradient(ellipse 60% 40% at 0% 90%, rgba(0, 119, 237, 0.08), transparent 45%),
    radial-gradient(circle at 18% 32%, rgba(0, 113, 227, 0.04) 0%, transparent 42%),
    radial-gradient(circle at 82% 68%, rgba(230, 0, 18, 0.035) 0%, transparent 40%),
    repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(0, 0, 0, 0.06) 39px, rgba(0, 0, 0, 0.06) 40px),
    repeating-linear-gradient(90deg, transparent, transparent 39px, rgba(0, 0, 0, 0.06) 39px, rgba(0, 0, 0, 0.06) 40px),
    linear-gradient(180deg, #fafafa 0%, #f5f5f7 45%, #eef0f4 100%);
  background-size: 220px 220px, auto, auto, auto, auto, auto, auto, auto, auto, auto;
  background-repeat: repeat, no-repeat, no-repeat, no-repeat, no-repeat, no-repeat, no-repeat, repeat, repeat, no-repeat;
  background-attachment: fixed;
"""


def inject_intro_animation() -> None:
    """Show a full-screen intro on the first run of the session only."""
    if st.session_state.get(_INTRO_SESSION_KEY):
        return
    st.session_state[_INTRO_SESSION_KEY] = True

    st.markdown(
        f"""
<style>
@keyframes v6IntroBar {{
  0% {{ transform: scaleY(0); opacity: 0; }}
  18% {{ opacity: 1; }}
  45% {{ transform: scaleY(1); }}
  100% {{ transform: scaleY(1); }}
}}
@keyframes v6IntroTextIn {{
  0% {{ opacity: 0; transform: translateY(14px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes v6IntroSubIn {{
  0% {{ opacity: 0; }}
  100% {{ opacity: 1; }}
}}
@keyframes v6IntroRedLine {{
  0% {{ transform: scaleX(0); opacity: 0; }}
  100% {{ transform: scaleX(1); opacity: 1; }}
}}
@keyframes v6IntroMeshPulse {{
  0%, 100% {{ opacity: 0.85; }}
  50% {{ opacity: 1; }}
}}
/* Inner content dissolves first — then the veil lifts to the real dashboard */
@keyframes v6IntroInnerExit {{
  0% {{ opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }}
  100% {{ opacity: 0; transform: translateY(-6px) scale(0.992); filter: blur(1px); }}
}}
@keyframes v6IntroVeilExit {{
  0% {{ opacity: 1; visibility: visible; }}
  100% {{ opacity: 0; visibility: hidden; }}
}}

#v6-intro-overlay {{
  position: fixed;
  inset: 0;
  z-index: 2147483646;
  display: flex;
  align-items: center;
  justify-content: center;
  {_INTRO_BG}
  animation: v6IntroVeilExit 1.15s cubic-bezier(0.33, 1, 0.68, 1) 2.75s forwards;
  pointer-events: auto;
}}

#v6-intro-overlay .v6-intro-mesh-soft {{
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0.5;
  animation: v6IntroMeshPulse 2.4s ease-in-out infinite;
  background-image:
    radial-gradient(circle at 50% 40%, rgba(255, 0, 0, 0.04) 0%, transparent 45%),
    radial-gradient(circle at 30% 70%, rgba(0, 113, 227, 0.05) 0%, transparent 40%);
}}

#v6-intro-overlay .v6-intro-inner {{
  position: relative;
  text-align: center;
  padding: 2rem 1.5rem;
  max-width: min(92vw, 640px);
  animation: v6IntroInnerExit 0.55s cubic-bezier(0.4, 0, 0.2, 1) 2.35s forwards;
}}

#v6-intro-overlay .v6-intro-bar-wrap {{
  display: flex;
  justify-content: center;
  margin-bottom: 1.25rem;
}}

#v6-intro-overlay .v6-intro-bar {{
  width: 5px;
  height: 88px;
  border-radius: 3px;
  background: linear-gradient(180deg, #ff3333 0%, #ff0000 40%, #cc0000 100%);
  box-shadow:
    0 0 20px rgba(255, 0, 0, 0.45),
    0 8px 32px rgba(230, 0, 18, 0.22);
  transform-origin: center bottom;
  animation: v6IntroBar 1s cubic-bezier(0.22, 1, 0.36, 1) 0.12s both;
}}

#v6-intro-overlay .v6-intro-brand {{
  font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", system-ui, sans-serif;
  font-size: clamp(1.75rem, 5.2vw, 2.75rem);
  font-weight: 800;
  letter-spacing: -0.035em;
  line-height: 1.15;
  color: #1d1d1f;
  animation: v6IntroTextIn 0.85s cubic-bezier(0.22, 1, 0.36, 1) 0.4s both;
}}

#v6-intro-overlay .v6-intro-brand .yt-red {{
  background: linear-gradient(135deg, #ff0000 0%, #e60012 55%, #cc0000 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  text-shadow: none;
}}

#v6-intro-overlay .v6-intro-accent-line {{
  height: 3px;
  width: 120px;
  margin: 1rem auto 0;
  border-radius: 999px;
  background: linear-gradient(90deg, transparent, #ff0000 20%, #ff0000 80%, transparent);
  transform-origin: center;
  animation: v6IntroRedLine 0.7s cubic-bezier(0.22, 1, 0.36, 1) 0.85s both;
}}

#v6-intro-overlay .v6-intro-title {{
  margin-top: 1rem;
  font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", system-ui, sans-serif;
  font-size: clamp(0.68rem, 1.8vw, 0.8rem);
  font-weight: 700;
  letter-spacing: 0.26em;
  text-transform: uppercase;
  color: #424245;
  animation: v6IntroSubIn 0.65s ease 0.95s both;
}}

#v6-intro-overlay .v6-intro-sub {{
  margin-top: 0.65rem;
  font-size: clamp(0.78rem, 1.9vw, 0.92rem);
  color: #0071e3;
  font-weight: 600;
  letter-spacing: 0.04em;
  animation: v6IntroSubIn 0.65s ease 1.12s both;
}}

@media (prefers-reduced-motion: reduce) {{
  #v6-intro-overlay {{
    animation: v6IntroVeilExit 0.45s ease 0.35s forwards !important;
  }}
  #v6-intro-overlay .v6-intro-inner {{
    animation: none !important;
    opacity: 1;
  }}
  #v6-intro-overlay .v6-intro-bar,
  #v6-intro-overlay .v6-intro-brand,
  #v6-intro-overlay .v6-intro-accent-line,
  #v6-intro-overlay .v6-intro-title,
  #v6-intro-overlay .v6-intro-sub {{
    animation: none !important;
    opacity: 1;
    transform: none;
  }}
  #v6-intro-overlay .v6-intro-mesh-soft {{ animation: none !important; }}
}}
</style>
<div id="v6-intro-overlay" role="presentation" aria-hidden="true">
  <div class="v6-intro-mesh-soft" aria-hidden="true"></div>
  <div class="v6-intro-inner">
    <div class="v6-intro-bar-wrap">
      <div class="v6-intro-bar"></div>
    </div>
    <div class="v6-intro-brand">
      <span class="yt-red">YouTube</span> Creator Insights
    </div>
    <div class="v6-intro-accent-line" aria-hidden="true"></div>
    <div class="v6-intro-title">Purdue × Google</div>
    <div class="v6-intro-sub">Opening your workspace</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
