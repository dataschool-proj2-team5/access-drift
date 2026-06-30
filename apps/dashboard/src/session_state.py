from __future__ import annotations

import pandas as pd
import streamlit as st

STATUS_OVERRIDE_KEY = "access_drift_review_status_overrides"
REVIEW_STATUS_OPTIONS = ["Open", "In Review", "Resolved"]


def get_review_status_overrides() -> dict[str, str]:
    if STATUS_OVERRIDE_KEY not in st.session_state:
        st.session_state[STATUS_OVERRIDE_KEY] = {}
    return st.session_state[STATUS_OVERRIDE_KEY]


def apply_review_status_overrides(data: pd.DataFrame) -> pd.DataFrame:
    overrides = get_review_status_overrides()
    if not overrides:
        return data

    updated = data.copy()
    updated["review_status"] = updated.apply(
        lambda row: overrides.get(str(row["case_id"]), row["review_status"]), axis=1
    )
    return updated


def set_review_status(case_id: str, status: str) -> None:
    if status not in REVIEW_STATUS_OPTIONS:
        return
    get_review_status_overrides()[str(case_id)] = status
