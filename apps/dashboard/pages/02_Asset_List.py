from __future__ import annotations

import importlib

import streamlit as st

import components.asset_table_fit as asset_table_components
from components.styles import apply_dashboard_style
import src.data_loader as data_loader
from src.session_state import apply_review_status_overrides


asset_table_components = importlib.reload(asset_table_components)
data_loader = importlib.reload(data_loader)


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

          .st-key-asset_status_filter div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
            background: transparent !important;
            border: 1px solid #d1d5db !important;
            box-shadow: none !important;
          }

          .st-key-asset_status_filter div[data-testid="stSelectbox"] [data-baseweb="select"] > div:hover,
          .st-key-asset_status_filter div[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within {
            background: transparent !important;
            border-color: #9ca3af !important;
            box-shadow: none !important;
          }

          .st-key-asset_status_filter div[data-testid="stSelectbox"] [data-baseweb="select"] div,
          .st-key-asset_status_filter div[data-testid="stSelectbox"] [data-baseweb="select"] input {
            background: transparent !important;
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

    result = data_loader.load_access_drift_data()
    if result.using_mock:
        st.sidebar.info("Using mock data")

    data = apply_review_status_overrides(result.data)
    if status_filter != "All":
        data = data[data["review_status"].eq(status_filter)]
    asset_table_components.render_asset_table_fit(data)


main()
