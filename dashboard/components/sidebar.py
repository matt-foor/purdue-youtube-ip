import streamlit as st


PAGE_OPTIONS = [
    "Channel Analysis",
    "Channel Insights",
    "Download Hub",
    "Outlier Finder",
    "Ytuber",
    "Deployment",
]

_LEGACY_PAGE_MAP = {
    "Recommendations": "Download Hub",
    "Thumbnails": "Download Hub",
    "Tools": "Download Hub",
}


def _normalize_page_name(value: str) -> str:
    page_name = _LEGACY_PAGE_MAP.get(str(value or "").strip(), str(value or "").strip())
    if page_name not in PAGE_OPTIONS:
        return PAGE_OPTIONS[0]
    return page_name


def render_sidebar_header() -> None:
    """Premium YouTube Creator mark + nav label (matches intro styling)."""
    st.markdown(
        """
        <div class="sidebar-brand-mast">
            <div class="sidebar-brand-emblem" aria-hidden="true">
                <div class="sidebar-brand-emblem-head">
                    <div class="sidebar-brand-emblem-eye"></div>
                    <div class="sidebar-brand-emblem-eye"></div>
                </div>
                <div class="sidebar-brand-emblem-smile"></div>
            </div>
            <div class="sidebar-brand-row">
                <div class="sidebar-brand-bar-col">
                    <div class="sidebar-brand-bar"></div>
                </div>
                <div class="sidebar-brand-copy">
                    <div class="sidebar-brand-yt">
                        <span class="sidebar-brand-yt-gradient">Creator</span>
                    </div>
                    <div class="sidebar-brand-ci">YouTube Insights</div>
                    <div class="sidebar-brand-line" aria-hidden="true"></div>
                    <div class="sidebar-brand-sub">Purdue × Google</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-nav-label">Navigate</div>',
        unsafe_allow_html=True,
    )


def render_sidebar_footer() -> None:
    """Attribution below the navigation menu."""
    st.markdown(
        "<hr style='border-color:rgba(0,0,0,0.1);margin:0.55rem 0 0.65rem;' />",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="font-size:10px;color:#86868b;margin-top:0.6rem;line-height:1.45;">
            <strong style="color:#1d1d1f;">Purdue University × Google</strong><br/>
            Daniels School of Business — MS BAIM Capstone<br/>
            <span style="opacity:0.9;">YouTube Creator Insights</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
