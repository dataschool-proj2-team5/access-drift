from __future__ import annotations

import streamlit as st

from components.cards import render_priority_review_list, render_summary_cards
from src.data_loader import load_access_drift_data


st.set_page_config(page_title="Access Drift Overview", page_icon="AD", layout="wide")


def main() -> None:
    st.title("Overview")
    st.caption("Access drift monitoring overview scaffold.")

    result = load_access_drift_data()
    if result.using_mock:
        st.info("Using mock data")

    st.subheader("Top Summary Cards")
    render_summary_cards(result.data)

    st.subheader("Priority Review")
    render_priority_review_list(result.data)


main()
