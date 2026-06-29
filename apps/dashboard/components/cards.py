from __future__ import annotations

import pandas as pd
import streamlit as st

from components.charts import render_issue_bar_chart, render_risk_level_donut


def render_summary_cards(data: pd.DataFrame) -> None:
    total_col, issues_col, drift_col = st.columns(3)

    with total_col:
        with st.container(border=True):
            st.metric("Total", len(data))
            render_risk_level_donut(data)

    with issues_col:
        with st.container(border=True):
            st.metric("Issues", int((data["risk_score"] > 0).sum()))
            render_issue_bar_chart(data)

    with drift_col:
        with st.container(border=True):
            st.markdown("**Top Drifts**")
            top_drifts = data["drift_type"].value_counts().head(5)
            for rank, (drift_type, count) in enumerate(top_drifts.items(), start=1):
                st.write(f"{rank}. {drift_type} ({count})")


def render_priority_review_list(data: pd.DataFrame) -> None:
    columns = [
        "case_id",
        "risk_title",
        "risk_level",
        "identity_name",
        "asset_name",
        "risk_score",
        "review_status",
    ]
    st.dataframe(
        data.sort_values("risk_score", ascending=False)[columns],
        use_container_width=True,
        hide_index=True,
    )


def render_risk_header_card(case: pd.Series) -> None:
    with st.container(border=True):
        left, middle, right = st.columns([2, 1, 1])
        with left:
            st.subheader(case["risk_title"])
            st.caption(f"{case['identity_name']} -> {case['asset_name']}")
        with middle:
            st.metric("Risk Level", case["risk_level"])
        with right:
            st.metric("Risk Score", int(case["risk_score"]))


def render_risk_summary_card(case: pd.Series) -> None:
    with st.container(border=True):
        st.markdown("**Risk Summary**")
        st.write(case["ai_summary"])


def render_risk_factors_card(case: pd.Series) -> None:
    with st.container(border=True):
        st.markdown("**Risk Factors**")
        factors = [
            f"Owner status: {case['owner_status']}",
            f"Credential status: {case['credential_status']}",
            f"Asset sensitivity: {case['asset_sensitivity']}",
            f"Permission level: {case['permission_level']}",
            f"Rotation status: {case['rotation_status']}",
        ]
        for factor in factors:
            st.checkbox(factor, value=True, disabled=True)


def render_review_info_card(case: pd.Series) -> None:
    with st.container(border=True):
        st.markdown("**Review Info**")
        st.write(f"Status: {case['review_status']}")
        st.write(f"Reviewer: {case['reviewer']}")
        st.write(f"Action owner: {case['action_owner']}")
        st.write(f"Detected at: {case['detected_at']}")
        st.write(f"Reference docs: {case['reference_docs']}")


def render_recommendation_panel(case: pd.Series) -> None:
    with st.container(border=True):
        st.markdown("**AI RAG Recommendation**")
        st.write(case["recommended_action"])
        st.caption("Placeholder only. RAG retrieval and business rules are not implemented yet.")


def render_ai_agent_placeholder(case: pd.Series) -> None:
    with st.container(border=True):
        st.markdown("**AI Agent**")
        st.text_area(
            "Draft action prompt",
            value=(
                f"Prepare an access review note for {case['case_id']} "
                f"covering {case['identity_name']} and {case['asset_name']}."
            ),
            height=120,
        )
        st.button("Generate draft", disabled=True)


def render_ticket_form_placeholder(case: pd.Series) -> None:
    with st.form("ticket-placeholder-form"):
        st.text_input("Title", value=f"[Access Drift] {case['risk_title']}")
        st.text_area("Description", value=case["recommended_action"], height=160)
        st.selectbox("Priority", ["High", "Medium", "Low"])
        st.text_input("Assignee", value=case["action_owner"])
        st.form_submit_button("Create ticket", disabled=True)
