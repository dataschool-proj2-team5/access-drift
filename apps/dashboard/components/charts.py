from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

STATUS_ORDER = ["Open", "In Review", "Resolved"]
RISK_LEVEL_ORDER = ["Critical", "High", "Medium", "Low"]


def render_risk_level_donut(data: pd.DataFrame) -> None:
    chart_data = (
        data[data["review_status"].isin(STATUS_ORDER)]
        .groupby("review_status", dropna=False)
        .size()
        .reindex(STATUS_ORDER, fill_value=0)
        .reset_index(name="count")
    )
    chart = (
        alt.Chart(chart_data)
        .mark_arc(innerRadius=50)
        .encode(
            theta=alt.Theta("count:Q"),
            color=alt.Color("review_status:N", title="Status", sort=STATUS_ORDER),
            tooltip=["review_status:N", "count:Q"],
        )
    )
    st.altair_chart(chart, use_container_width=True)


def render_issue_bar_chart(data: pd.DataFrame) -> None:
    chart_data = (
        data[data["risk_level"].isin(RISK_LEVEL_ORDER)]
        .groupby("risk_level", dropna=False)
        .size()
        .reindex(RISK_LEVEL_ORDER, fill_value=0)
        .reset_index(name="count")
    )
    chart = (
        alt.Chart(chart_data)
        .mark_bar()
        .encode(
            x=alt.X("risk_level:N", title="Risk Level", sort=RISK_LEVEL_ORDER),
            y=alt.Y("count:Q", title="Cases"),
            tooltip=["risk_level:N", "count:Q"],
        )
    )
    st.altair_chart(chart, use_container_width=True)


def render_access_path(case: pd.Series) -> None:
    steps = [
        ("Owner", case["owner_name"], f"{case['owner_team']} · {case['related_person_status']}"),
        ("NHI", case["object_type"], case["identity_name"]),
        ("Credential", case["credential_type"], case["credential_status"]),
        ("Permission", case["permission_level"], "can read and list storage objects"),
        ("Sensitive Asset", case["asset_name"], case["asset_type"]),
        ("Data Scope", case["data_scope"], case["data_categories"]),
    ]

    columns = st.columns(len(steps))
    for index, (label, value, caption) in enumerate(steps):
        with columns[index]:
            st.markdown(f"**{label}**")
            st.write(value)
            st.caption(caption)
            if index < len(steps) - 1:
                st.caption("->")
