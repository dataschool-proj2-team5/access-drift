from __future__ import annotations

import streamlit as st

from components.cards import render_priority_review_list, render_summary_cards
from components.styles import apply_dashboard_style
from src.data_loader import load_access_drift_data
from src.session_state import apply_review_status_overrides


st.set_page_config(page_title="Access Drift Overview", page_icon="AD", layout="wide")


def main() -> None:
    apply_dashboard_style(page="overview")
    st.html('<div class="ad-page-title">Overview</div>')

    result = load_access_drift_data()
    if result.using_mock:
        st.sidebar.info("Using mock data")

    data = apply_review_status_overrides(result.data)
    render_summary_cards(data)
    render_priority_review_list(data)


main()
