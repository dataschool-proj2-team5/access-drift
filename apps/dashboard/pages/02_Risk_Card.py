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
from src.data_loader import load_access_drift_data


st.set_page_config(page_title="Access Drift Risk Card", page_icon="AD", layout="wide")


def main() -> None:
    st.title("Risk Card")

    result = load_access_drift_data()
    if result.using_mock:
        st.info("Using mock data")

    data = result.data.sort_values("risk_score", ascending=False)
    selected_case_id = st.selectbox("Case", data["case_id"].tolist())
    case = data.loc[data["case_id"] == selected_case_id].iloc[0]
    st.caption(f"{case['case_id']} · {case['risk_title']}")

    render_risk_header_card(case)

    risk_tab, action_tab, ticket_tab = st.tabs(["위험 분석", "권장 조치", "티켓 발급"])

    with risk_tab:
        st.subheader("Access Path")
        render_access_path(case)

        left, right = st.columns(2)
        with left:
            render_risk_summary_card(case)
            render_risk_factors_card(case)
        with right:
            render_review_info_card(case)

    with action_tab:
        render_recommendation_panel(case)
        render_ai_agent_placeholder(case)

    with ticket_tab:
        render_ticket_form_placeholder(case)


main()
