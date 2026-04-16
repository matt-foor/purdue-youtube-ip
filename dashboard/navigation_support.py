"""Helpers for programmatic navigation with ``st.navigation`` / ``st.switch_page``."""

from __future__ import annotations

import streamlit as st


def switch_to_outlier_finder() -> None:
    """Jump to Outlier Finder using the same ``st.Page`` instance as the sidebar router."""
    from dashboard import app as app_module

    st.switch_page(app_module.PAGE_OUTLIER_FINDER)
