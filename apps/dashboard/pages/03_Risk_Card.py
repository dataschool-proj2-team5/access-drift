from __future__ import annotations

import importlib
import base64
import mimetypes
from functools import lru_cache
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

import components.cards as card_components
from components.risk_text_panels import (
    render_ai_agent_placeholder,
    render_recommendation_panel,
    render_review_info_card,
)
from components.styles import apply_dashboard_style
import src.action_state as action_state
import src.data_loader as data_loader
import src.session_state as session_state


card_components = importlib.reload(card_components)
data_loader = importlib.reload(data_loader)
action_state = importlib.reload(action_state)
session_state = importlib.reload(session_state)


ICON_DIR = Path(__file__).resolve().parents[1] / "assets" / "icons"
BADGE_DIR = Path(__file__).resolve().parents[1] / "assets" / "badges"
PENDING_STATUS_CHANGE_KEY = "access_drift_pending_status_change"
STATUS_WIDGET_VERSION_KEY = "access_drift_status_widget_versions"


def render_access_path_v2_inline(case: pd.Series) -> None:
    owner_caption = f"{escape(str(case['owner_team']))}<br>{escape(str(case['related_person_status']))}"
    identity_caption = escape(str(case["identity_name"]))
    credential_caption = _credential_expiry_caption(case)
    asset_caption = _asset_caption(case)
    sensitivity_label = str(case.get("asset_sensitivity", "") or "")
    steps = [
        ("accesspath-icon-human.svg", case["owner_name"], owner_caption, "badge-owner.svg", "Owner", "", 187, 165),
        ("accesspath-icon-sp.svg", case["object_type"], identity_caption, "", "", "", 177, 165),
        ("accesspath-icon-credential.svg", case["credential_type"], credential_caption, "badge-activity.svg", "Activity", "", 177, 165),
        ("accesspath-icon-permission.svg", case["permission_level"], "can read and list<br>storage objects", "", "", "", 177, 165),
        ("accesspath-icon-asset.svg", case["asset_name"], asset_caption, "", "", "", 176, 165),
        ("accesspath-icon-datascope.svg", case["data_scope"], escape(str(case["data_categories"])), "", "", sensitivity_label, 181, 165),
    ]
    html = [
        '<div class="ad-card ad-access-card ad-access-card-v2">'
        '<h3 class="ad-card-title">Access Path</h3>'
        '<div class="ad-access-canvas" style="position:relative; height:352px; padding:88px 16px 0; box-sizing:border-box; gap:0; grid-template-columns:187px 177px 177px 177px 176px 181px; justify-content:space-between; align-items:start; overflow-x:auto;">'
        '<div class="ad-path-connector-line" style="position:absolute; left:175px; right:auto; width:920px; top:163px; height:2px; background:#6B7280; z-index:0; pointer-events:none;">'
        '<span style="position:absolute; right:-1px; top:50%; width:9px; height:9px; border-top:2px solid #6B7280; border-right:2px solid #6B7280; transform:translateY(-50%) rotate(45deg);"></span>'
        '</div>'
    ]
    for icon_file, value, caption, badge_file, badge_alt, text_badge, width, height in steps:
        pill = _path_badge_img(badge_file, badge_alt) if badge_file else _path_text_badge(text_badge)
        icon = _path_icon_img(icon_file, str(value))
        html.append(
            f"""
            <div class="ad-path-step" style="width:{width}px; height:{height}px; min-height:{height}px; padding:18px 15px 50px; display:flex; flex-direction:column; box-sizing:border-box; overflow:hidden; background:#fff; position:relative; z-index:1;">
              <div class="ad-path-main-row" style="display:flex; align-items:center; gap:12px; min-height:35px; margin-bottom:10px;">
                <div class="ad-path-icon-wrap" style="width:35px; height:35px; min-width:35px; margin-bottom:0; flex:0 0 35px; display:flex; align-items:center; justify-content:center;">{icon}</div>
                <div class="ad-path-value" style="font-size:16px; line-height:1.18; margin-bottom:0; min-height:0; display:block; white-space:normal; overflow-wrap:normal; word-break:normal; max-width:calc(100% - 47px);">{escape(str(value))}</div>
              </div>
              <div class="ad-path-caption" style="font-size:12px; line-height:1.25; min-height:30px; color:#6B7280; overflow-wrap:normal; word-break:keep-all;">{caption}</div>
              <div class="ad-path-pill-slot" style="position:absolute; right:15px; bottom:18px; min-height:23px; display:flex; justify-content:flex-end; align-items:flex-end; overflow:hidden;">{pill}</div>
            </div>
            """
        )
    html.append("</div></div>")
    st.html("".join(html))



def _credential_expiry_caption(case: pd.Series) -> str:
    expires_at = str(case.get("credential_expires_at", "") or "").strip()
    return f"\ub9cc\ub8cc\uc77c: {escape(expires_at) if expires_at else '-'}"


def _asset_caption(case: pd.Series) -> str:
    asset_name = str(case.get("asset_name", "") or "").strip()
    asset_full_name = str(case.get("asset_full_name", "") or "").strip()
    if not asset_full_name or asset_full_name == asset_name:
        return ""
    return escape(asset_full_name)


def _path_text_badge(label: str) -> str:
    if not label:
        return ""
    return (
        '<span class="ad-access-badge-text" '
        'style="display:inline-flex; align-items:center; min-height:23px; max-width:96px; '
        'padding:0 10px; border-radius:999px; background:#FFE1E1; color:#FF3B3B; '
        'font-size:12px; line-height:23px; font-weight:700; white-space:nowrap; '
        'overflow:hidden; text-overflow:ellipsis;">'
        f"{escape(label)}"
        "</span>"
    )


def _path_badge_img(filename: str, alt: str) -> str:
    if not filename:
        return ""
    return f'<img src="{_path_badge_data_uri(filename)}" alt="{escape(alt)}" class="ad-access-badge-img" style="height:23px; width:auto; max-width:76px; display:block;" />'


@lru_cache(maxsize=None)
def _path_badge_data_uri(filename: str) -> str:
    path = BADGE_DIR / filename
    mime_type = mimetypes.guess_type(path.name)[0] or "image/svg+xml"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


@lru_cache(maxsize=None)
def _path_icon_data_uri(filename: str) -> str:
    path = ICON_DIR / filename
    mime_type = mimetypes.guess_type(path.name)[0] or "image/svg+xml"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _path_icon_img(filename: str, alt: str) -> str:
    return f'<img src="{_path_icon_data_uri(filename)}" alt="{escape(alt)}" class="ad-path-icon" style="width:35px; height:35px; display:block; object-fit:contain;" />'


def _get_status_widget_versions() -> dict[str, int]:
    if STATUS_WIDGET_VERSION_KEY not in st.session_state:
        st.session_state[STATUS_WIDGET_VERSION_KEY] = {}
    return st.session_state[STATUS_WIDGET_VERSION_KEY]


def _bump_status_widget_version(case_id: str) -> None:
    versions = _get_status_widget_versions()
    key = str(case_id)
    versions[key] = int(versions.get(key, 0)) + 1


def _rerun_app() -> None:
    try:
        st.rerun(scope="app")
    except TypeError:
        st.rerun()


def _persist_or_fallback_status_change(pending: dict[str, str], reason: str, using_mock: bool) -> None:
    case_id = str(pending["case_id"])
    previous_status = str(pending["previous_status"])
    new_status = str(pending["new_status"])
    clean_reason = str(reason).strip()

    config = action_state.get_databricks_action_config()
    if action_state.can_write_action_state(config, using_mock) and config is not None:
        try:
            action_state.persist_review_status_change(
                config,
                risk_case_key=str(pending.get("risk_case_key") or case_id),
                previous_status=previous_status,
                new_status=new_status,
                reason=clean_reason,
            )
        except Exception:
            pass

    session_state.set_review_status(case_id, new_status)
    session_state.add_review_status_change_reason(case_id, previous_status, new_status, clean_reason)


def _open_status_change_dialog(using_mock: bool) -> None:
    pending = st.session_state.get(PENDING_STATUS_CHANGE_KEY)
    if not pending:
        return

    dialog = getattr(st, "dialog", None) or getattr(st, "experimental_dialog")

    @dialog("\uc870\uce58 \uc0c1\ud0dc \ubcc0\uacbd")
    def _render_dialog() -> None:
        previous_status = str(pending["previous_status"])
        new_status = str(pending["new_status"])
        case_label = str(pending["display_case_id"])

        st.markdown(f"**{case_label}** \uc0c1\ud0dc\ub97c `{previous_status}`\uc5d0\uc11c `{new_status}`\ub85c \ubcc0\uacbd\ud569\ub2c8\ub2e4.")
        reason = st.text_area(
            "\ubcc0\uacbd \uc0ac\uc720",
            key=f"status_change_reason_{pending['case_id']}_{new_status}",
            placeholder="\uc0c1\ud0dc \ubcc0\uacbd \uc0ac\uc720\ub97c \uc785\ub825\ud558\uc138\uc694.",
            height=120,
        )
        cancel_col, confirm_col = st.columns(2)
        with cancel_col:
            if st.button("\ucde8\uc18c", use_container_width=True):
                st.session_state.pop(PENDING_STATUS_CHANGE_KEY, None)
                _bump_status_widget_version(str(pending["case_id"]))
                _rerun_app()
        with confirm_col:
            if st.button("\uc800\uc7a5", type="primary", use_container_width=True, key="status_change_save"):
                if not str(reason).strip():
                    st.warning("\ubcc0\uacbd \uc0ac\uc720\ub97c \uc785\ub825\ud574\uc57c \uc0c1\ud0dc\ub97c \ubcc0\uacbd\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.")
                    return
                _persist_or_fallback_status_change(pending, str(reason), using_mock)
                st.session_state.pop(PENDING_STATUS_CHANGE_KEY, None)
                _bump_status_widget_version(str(pending["case_id"]))
                _rerun_app()

    _render_dialog()


st.set_page_config(page_title="Access Drift Risk Card", page_icon="AD", layout="wide")


def main() -> None:
    apply_dashboard_style(page="risk")
    st.markdown(
        """
        <style>
        .st-key-risk_v2_status_overlay {
          position: relative;
          z-index: 5;
          margin-top: -205px;
          margin-bottom: 155px;
          pointer-events: none;
        }

        .st-key-risk_v2_status_overlay div[data-testid="stHorizontalBlock"],
        .st-key-risk_v2_status_overlay div[data-testid="column"] {
          pointer-events: none;
        }

        .st-key-risk_v2_status_overlay div[data-testid="stSelectbox"] {
          max-width: 168px;
          margin-left: auto;
          margin-right: 24px;
          pointer-events: auto;
          position: relative;
        }

        .st-key-risk_v2_status_overlay div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
          border-radius: 8px !important;
          border-color: #2f5f87 !important;
          background: #ffffff !important;
          box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
          min-height: 38px !important;
        }

        .st-key-risk_v2_status_overlay div[data-testid="stSelectbox"] [data-baseweb="select"] > div:hover {
          border-color: var(--ad-blue) !important;
        }

        .st-key-risk_v2_status_overlay div[data-testid="stSelectbox"] [data-baseweb="select"] span,
        .st-key-risk_v2_status_overlay div[data-testid="stSelectbox"] [data-baseweb="select"] div,
        .st-key-risk_v2_status_overlay div[data-testid="stSelectbox"] [data-baseweb="select"] input {
          color: #0f4f7a !important;
          -webkit-text-fill-color: #0f4f7a !important;
          font-weight: 700 !important;
        }

        .st-key-status_change_save button {
          background: var(--ad-blue) !important;
          border-color: var(--ad-blue) !important;
          color: #ffffff !important;
        }

        .st-key-status_change_save button:hover {
          background: #002f5f !important;
          border-color: #002f5f !important;
          color: #ffffff !important;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )
    title_col, reviewer_col = st.columns([1, 0.18], gap="small", vertical_alignment="center")
    with title_col:
        st.html('<div class="ad-risk-title">Risk Card</div>')
    with reviewer_col:
        st.html(
            """
            <div style="display:flex; justify-content:flex-end; margin:0 0 10px;">
              <div class="ad-reviewer-chip" style="display:flex; align-items:center; gap:10px; min-width:150px; padding:9px 12px; background:#fff; border:1px solid #E2E6EB; border-radius:999px; box-shadow:0 1px 2px rgba(15,23,42,0.04); box-sizing:border-box;">
                <div class="ad-reviewer-avatar" style="width:30px; height:30px; border-radius:999px; background:linear-gradient(135deg,#0A66C2,#74B9FF); border:1px solid #D8E4F0; flex:0 0 30px; display:flex; align-items:center; justify-content:center; color:#fff; font-size:13px; font-weight:800;">박</div>
                <div style="line-height:1.15; text-align:left; min-width:0;">
                  <div style="font-size:13px; font-weight:700; color:#111827; white-space:nowrap;">&#48149;&#51648;&#50672;</div>
                  <div style="font-size:11px; font-weight:600; color:#6B7280; margin-top:3px; white-space:nowrap;">SecOps&#54016;</div>
                </div>
              </div>
            </div>
            """
        )

    result = data_loader.load_access_drift_data()
    if result.using_mock:
        st.sidebar.info("Using mock data")

    data = session_state.apply_review_status_overrides(result.data).sort_values("risk_score", ascending=False)
    case_ids = data["case_id"].tolist()
    case_label_by_id = dict(zip(data["case_id"].astype(str), data["display_case_id"].astype(str)))
    case_id_by_label = dict(zip(data["display_case_id"].astype(str), data["case_id"].astype(str)))
    requested_display_case_id = st.query_params.get("case")
    requested_case_id = st.query_params.get("case_id")
    if isinstance(requested_display_case_id, list):
        requested_display_case_id = requested_display_case_id[0] if requested_display_case_id else None
    if isinstance(requested_case_id, list):
        requested_case_id = requested_case_id[0] if requested_case_id else None
    requested_case_id = case_id_by_label.get(str(requested_display_case_id), requested_case_id)
    selected_index = case_ids.index(requested_case_id) if requested_case_id in case_ids else 0
    selected_case_id = st.sidebar.selectbox(
        "Case",
        case_ids,
        index=selected_index,
        format_func=lambda case_id: case_label_by_id.get(str(case_id), str(case_id)),
    )
    case = data.loc[data["case_id"] == selected_case_id].iloc[0].copy()
    selected_display_case_id = str(case["display_case_id"])
    if st.query_params.get("case") != selected_display_case_id or "case_id" in st.query_params:
        st.query_params.clear()
        st.query_params["case"] = selected_display_case_id

    st.html(f'<div class="ad-page-caption">{selected_display_case_id} &#183; {case["risk_title"]}</div>')

    current_status = str(case["review_status"])
    status_options = session_state.REVIEW_STATUS_OPTIONS
    status_index = status_options.index(current_status) if current_status in status_options else 0
    card_components.render_risk_header_card_v2(case)

    with st.container(key="risk_v2_status_overlay"):
        _, status_col = st.columns([5.05, 1.25], gap="small", vertical_alignment="top")
        with status_col:
            status_widget_version = _get_status_widget_versions().get(str(selected_case_id), 0)
            status_widget_key = f"review_status_{selected_case_id}_{status_widget_version}"
            selected_status = st.selectbox(
                "Review status",
                status_options,
                index=status_index,
                key=status_widget_key,
                label_visibility="collapsed",
            )
    if selected_status != current_status:
        st.session_state[PENDING_STATUS_CHANGE_KEY] = {
            "case_id": str(selected_case_id),
            "risk_case_key": str(case.get("risk_case_key", selected_case_id)),
            "display_case_id": selected_display_case_id,
            "previous_status": current_status,
            "new_status": selected_status,
        }
    _open_status_change_dialog(result.using_mock)
    case["review_status"] = current_status

    risk_tab, action_tab, ticket_tab = st.tabs(["\uc704\ud5d8 \ubd84\uc11d", "\uad8c\uc7a5 \uc870\uce58", "\ud2f0\ucf13 \ubc1c\uae09"])

    with risk_tab:
        render_access_path_v2_inline(case)
        summary_col, factors_col = st.columns([1.35, 1], gap="large")
        with summary_col:
            card_components.render_risk_summary_card_v2(case)
        with factors_col:
            card_components.render_risk_factors_card_v2(case)

    with action_tab:
        left, right = st.columns([2, 1], gap="large")
        with left:
            render_recommendation_panel(case)
        with right:
            render_ai_agent_placeholder(case)

    with ticket_tab:
        card_components.render_ticket_form_placeholder(case)


main()
