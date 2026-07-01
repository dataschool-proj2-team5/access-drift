from __future__ import annotations

import importlib

import streamlit as st

import components.cards as card_components
from components.styles import apply_dashboard_style
import src.data_loader as data_loader
from src.session_state import apply_review_status_overrides


card_components = importlib.reload(card_components)
data_loader = importlib.reload(data_loader)


st.set_page_config(page_title="Access Drift Overview", page_icon="AD", layout="wide")


def main() -> None:
    apply_dashboard_style(page="overview")
    st.html('<div class="ad-page-title">Overview</div>')

    result = data_loader.load_access_drift_data()
    if result.using_mock:
        st.sidebar.info("Using mock data")

    data = apply_review_status_overrides(result.data)
    card_components.render_summary_cards(data)
    card_components.render_priority_review_list(data)


main()
