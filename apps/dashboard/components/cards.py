from __future__ import annotations

import pandas as pd
import streamlit as st

from components.charts import render_issue_bar_chart, render_risk_level_donut

RISK_LEVELS = ["Critical", "High", "Medium", "Low"]


def render_summary_cards(data: pd.DataFrame) -> None:
    total_col, issues_col, drift_col = st.columns(3)

    with total_col:
        with st.container(border=True):
            st.metric("Total", len(data))
            render_risk_level_donut(data)
            status_counts = data["review_status"].value_counts()
            st.write(f"Open: {status_counts.get('Open', 0)}")
            st.write(f"In review: {status_counts.get('In Review', 0)}")
            st.write(f"Resolved: {status_counts.get('Resolved', 0)}")

    with issues_col:
        with st.container(border=True):
            issue_count = int(data["risk_level"].isin(RISK_LEVELS).sum())
            st.metric("Issues", issue_count)
            render_issue_bar_chart(data)

    with drift_col:
        with st.container(border=True):
            st.markdown("**Top Drifts**")
            top_drifts = data.loc[data["drift_type"] != "No Active Drift", "drift_type"].value_counts().head(4)
            for rank, (drift_type, count) in enumerate(top_drifts.items(), start=1):
                st.write(f"{rank}. {drift_type} ({count})")


def render_priority_review_list(data: pd.DataFrame) -> None:
    demo_case_order = ["CASE-001", "CASE-002", "CASE-003"]
    priority = data[data["case_id"].isin(demo_case_order)].copy()
    priority["case_sort"] = pd.Categorical(priority["case_id"], categories=demo_case_order, ordered=True)
    priority = priority.sort_values("case_sort")
    priority["risk_title"] = priority["overview_title"].where(priority["overview_title"].ne(""), priority["risk_title"])
    priority["owner"] = priority["owner_name"] + " / " + priority["owner_team"]
    priority["detected_at"] = priority["detected_at"].apply(_format_datetime)
    columns = ["case_id", "risk_title", "identity_name", "owner", "risk_level", "identity_type", "detected_at", "review_status"]
    st.dataframe(
        priority[columns],
        use_container_width=True,
        hide_index=True,
    )


def render_risk_header_card(case: pd.Series) -> None:
    with st.container(border=True):
        left, middle, right = st.columns([3, 1, 1])
        with left:
            st.subheader(case["identity_name"])
            st.caption(f"{case['drift_type']} · {case['object_type']} · {case['credential_status']}")
            st.write(case["linked_owner_label"])
            meta_cols = st.columns(4)
            meta_cols[0].write(f"Object type: {case['object_type']}")
            meta_cols[1].write(f"Identity type: {case['identity_type']}")
            meta_cols[2].write(f"Credential status: {case['credential_status']}")
            meta_cols[3].write(f"Last Accessed: {_format_datetime(case['last_accessed_at'])}")
        with middle:
            st.metric("Risk Level", case["risk_level"])
        with right:
            st.metric("Status", case["review_status"])


def render_risk_summary_card(case: pd.Series) -> None:
    with st.container(border=True):
        st.markdown("**Risk Summary**")
        st.write(case["risk_summary"])


def render_risk_factors_card(case: pd.Series) -> None:
    with st.container(border=True):
        st.markdown("**Risk Factors**")
        factors = _as_list(case["risk_factors"]) or [
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
        st.write(f"Reviewer: {case['reviewer']}")
        st.write(f"Action owner: {case['action_owner']}")
        st.write(f"Status: {case['review_status']}")
        st.write(f"Detected at: {_format_datetime(case['detected_at'])}")


def render_recommendation_panel(case: pd.Series) -> None:
    with st.container(border=True):
        st.markdown("**AI Summary**")
        st.write(case["ai_summary"])

        st.markdown("**Reference Documents**")
        for doc in _as_list(case["reference_docs"]):
            st.write(f"- {doc}")

        st.markdown("**Action Plan**")
        for index, step in enumerate(_as_list(case["action_plan"]), start=1):
            st.write(f"{index}. {step}")


def render_ai_agent_placeholder(case: pd.Series) -> None:
    with st.container(border=True):
        st.markdown("**AI Agent**")
        for message in _as_list(case["ai_agent_messages"]):
            st.write(message)
        st.text_input("AI Agent에게 질문하기", placeholder="AI Agent에게 질문하기")
        st.button("Generate draft", disabled=True)


def render_ticket_form_placeholder(case: pd.Series) -> None:
    with st.form("ticket-placeholder-form"):
        st.text_input("Title", value=f"[Access Drift] {case['risk_title']}")
        st.text_area("Description", value=case["recommended_action"], height=160)
        st.selectbox("Priority", ["High", "Medium", "Low"])
        st.text_input("Assignee", value=case["action_owner"])
        st.form_submit_button("Create ticket", disabled=True)


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value:
        return [item.strip() for item in value.split(";") if item.strip()]
    return []


def _format_datetime(value: object) -> str:
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return ""
    return timestamp.strftime("%Y/%m/%d %H:%M")
