from __future__ import annotations

import streamlit as st

from components.cards import (
    render_ai_agent_placeholder,
    render_recommendation_panel,
    render_review_info_card,
    render_risk_factors_card,
    render_risk_header_card,
    render_risk_summary_card,
    render_ticket_form_placeholder,
)
from components.charts import render_access_path
from components.styles import apply_dashboard_style
from src.data_loader import load_access_drift_data


st.set_page_config(page_title="Access Drift Risk Card", page_icon="AD", layout="wide")


def main() -> None:
    apply_dashboard_style(page="risk")
    st.html('<div class="ad-risk-title">Risk Card</div>')

    result = load_access_drift_data()
    if result.using_mock:
        st.sidebar.info("Using mock data")

    data = result.data.sort_values("risk_score", ascending=False)
    case_ids = data["case_id"].tolist()
    requested_case_id = st.query_params.get("case_id")
    if isinstance(requested_case_id, list):
        requested_case_id = requested_case_id[0] if requested_case_id else None
    selected_index = case_ids.index(requested_case_id) if requested_case_id in case_ids else 0
    selected_case_id = st.sidebar.selectbox("Case", case_ids, index=selected_index)
    case = data.loc[data["case_id"] == selected_case_id].iloc[0]

    st.html(f'<div class="ad-page-caption">{case["case_id"]} · {case["risk_title"]}</div>')

    render_risk_header_card(case)

    risk_tab, action_tab, ticket_tab = st.tabs(["위험 분석", "권장 조치", "티켓 발급"])

    with risk_tab:
        render_access_path(case)
        left, right = st.columns([2, 1], gap="large")
        with left:
            render_risk_summary_card(case)
            render_risk_factors_card(case)
        with right:
            render_review_info_card(case)

    with action_tab:
        left, right = st.columns([2, 1], gap="large")
        with left:
            render_recommendation_panel(case)
        with right:
            render_ai_agent_placeholder(case)

    with ticket_tab:
        render_ticket_form_placeholder(case)


main()
