from __future__ import annotations

import streamlit as st

from src.data_loader import load_access_drift_data


st.set_page_config(
    page_title="Access Drift Dashboard",
    page_icon="AD",
    layout="wide",
)


def main() -> None:
    st.title("Access Drift Dashboard")
    st.caption("Scaffold entry point for the Access Drift Streamlit dashboard.")

    result = load_access_drift_data()

    if result.using_mock:
        st.info("Using mock data. Add data/sample_access_drift.csv to preview CSV-backed data.")
    else:
        st.success(f"Loaded CSV data from {result.source_path}")

    st.subheader("Dashboard Pages")
    st.write(
        "Use the sidebar to open Overview or Risk Card. "
        "This entry page intentionally stays minimal while the app structure is being shaped."
    )

    st.metric("Cases loaded", len(result.data))

    with st.expander("Expected data columns"):
        st.write(", ".join(result.data.columns))


if __name__ == "__main__":
    main()
