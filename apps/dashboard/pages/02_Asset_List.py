from __future__ import annotations

import streamlit as st

from components.asset_table_fit import render_asset_table_fit
from components.styles import apply_dashboard_style
from src.data_loader import load_access_drift_data
from src.session_state import apply_review_status_overrides


st.set_page_config(page_title="Access Drift Asset List", page_icon="AD", layout="wide")


STATUS_FILTER_OPTIONS = ["All", "Open", "In Review", "Resolved"]


def main() -> None:
    apply_dashboard_style(page="overview")
    st.markdown(
        """
        <style>
          .stApp {
            background: #ffffff;
          }

          .ad-asset-table-header,
          .ad-asset-table-header > div {
            color: #4b5563 !important;
            font-weight: 700 !important;
          }

          .st-key-asset_status_filter div[data-testid="stSelectbox"] {
            max-width: 180px;
            margin-left: auto;
          }

          .st-key-asset_status_filter div[data-testid="stSelectbox"] label {
            color: #6b7280;
            font-size: 12px;
            font-weight: 700;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    title_col, status_col = st.columns([1, 0.22], gap="small", vertical_alignment="bottom")
    with title_col:
        st.html('<div class="ad-page-title">Asset List</div>')
    with status_col:
        with st.container(key="asset_status_filter"):
            status_filter = st.selectbox("Status", STATUS_FILTER_OPTIONS, index=0)

    result = load_access_drift_data()
    if result.using_mock:
        st.sidebar.info("Using mock data")

    data = apply_review_status_overrides(result.data)
    if status_filter != "All":
        data = data[data["review_status"].eq(status_filter)]
    render_asset_table_fit(data)


main()
