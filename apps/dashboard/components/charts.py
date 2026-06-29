from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st


def render_risk_level_donut(data: pd.DataFrame) -> None:
    chart_data = data.groupby("risk_level", dropna=False).size().reset_index(name="count")
    chart = (
        alt.Chart(chart_data)
        .mark_arc(innerRadius=50)
        .encode(
            theta=alt.Theta("count:Q"),
            color=alt.Color("risk_level:N", title="Risk Level"),
            tooltip=["risk_level:N", "count:Q"],
        )
    )
    st.altair_chart(chart, use_container_width=True)


def render_issue_bar_chart(data: pd.DataFrame) -> None:
    chart_data = data.groupby("drift_type", dropna=False).size().reset_index(name="count")
    chart = (
        alt.Chart(chart_data)
        .mark_bar()
        .encode(
            x=alt.X("count:Q", title="Cases"),
            y=alt.Y("drift_type:N", title="Drift Type", sort="-x"),
            tooltip=["drift_type:N", "count:Q"],
        )
    )
    st.altair_chart(chart, use_container_width=True)


def render_access_path(case: pd.Series) -> None:
    steps = [
        ("Owner", case["owner_name"], case["owner_status"]),
        ("Identity", case["identity_name"], case["identity_type"]),
        ("Credential", case["object_name"], case["credential_status"]),
        ("Asset", case["asset_name"], case["permission_level"]),
    ]

    columns = st.columns(len(steps))
    for index, (label, value, caption) in enumerate(steps):
        with columns[index]:
            st.markdown(f"**{label}**")
            st.write(value)
            st.caption(caption)
            if index < len(steps) - 1:
                st.caption("->")
