from __future__ import annotations

import base64
import mimetypes
import re
from datetime import datetime
from functools import lru_cache
from html import escape
from pathlib import Path
from textwrap import dedent
from urllib.parse import quote

import pandas as pd
import streamlit as st

import src.jira_client as jira_client

RISK_LEVELS = ["Critical", "High", "Medium", "Low"]
DEMO_PRIORITY_RISK_CASE_KEYS = {
    "d9419944a82fd5211982ad866cb0ebca889271dcbd854c0c5bd8871769b6fb4f",
    "nhi:d8f4a5b6-7c8d-4e91-9f02-1a2b3c4d5e6f:asset-customer-export-storage-prod:nhi_residual_access",
}
ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"
ICON_DIR = ASSET_DIR / "icons"
BADGE_DIR = ASSET_DIR / "badges"


def render_summary_cards(data: pd.DataFrame) -> None:
    total_col, issues_col, drift_col = st.columns([1.02, 1.15, 0.9], gap="medium")
    actions_data = data[data["risk_level"].ne("Low")]
    status_counts = actions_data["review_status"].value_counts()
    open_count = int(status_counts.get("Open", 0))
    review_count = int(status_counts.get("In Review", 0))
    resolved_count = int(status_counts.get("Resolved", 0))
    total_count = len(actions_data)
    open_stop = _percentage(open_count, total_count)
    review_stop = _percentage(open_count + review_count, total_count)

    with total_col:
        _render_overview_html(
            f"""
            <div class="ad-overview-summary-card">
              <div class="ad-overview-title-row">
                <div class="ad-overview-title">Actions</div>
                <span class="ad-low-excluded-pill">Low excluded</span>
              </div>
              <div class="ad-overview-total-grid">
                <div class="ad-overview-donut" style="--open-stop:{open_stop}%; --review-stop:{review_stop}%;">
                  <div class="ad-overview-donut-inner">
                    <span>Total</span>
                    <strong>{total_count}</strong>
                  </div>
                </div>
                <div class="ad-overview-total-legend">
                  {_legend_row("Open", open_count, "#128bf4")}
                  {_legend_row("In review", review_count, "#ff7b73")}
                  {_legend_row("Resolved", resolved_count, "#bfc4ca")}
                </div>
              </div>
            </div>
            """
        )

    with issues_col:
        risk_counts = (
            data[data["risk_level"].isin(RISK_LEVELS)]
            .groupby("risk_level", dropna=False)
            .size()
            .reindex(RISK_LEVELS, fill_value=0)
        )
        max_count = max(int(risk_counts.max()), 1)
        _render_overview_html(
            f"""
            <div class="ad-overview-summary-card">
              <div class="ad-overview-title">Issues</div>
              <div class="ad-overview-issues-chart">
                {_issue_bar("Critical", int(risk_counts["Critical"]), max_count, "#003b68")}
                {_issue_bar("High", int(risk_counts["High"]), max_count, "#f23d42")}
                {_issue_bar("Medium", int(risk_counts["Medium"]), max_count, "#f5b844")}
                {_issue_bar("Low", int(risk_counts["Low"]), max_count, "#41b76a")}
              </div>
              <div class="ad-overview-issue-labels">
                <span>Critical</span>
                <span>High</span>
                <span>Medium</span>
                <span>Low</span>
              </div>
            </div>
            """
        )

    with drift_col:
        top_drifts = data.loc[data["drift_type"] != "No Active Drift", "drift_type"].value_counts().head(4)
        rows = []
        for index, (drift_type, count) in enumerate(top_drifts.items()):
            emphasis = " ad-top-drift-primary" if index == 0 else ""
            emphasis_style = ' style="color:#EC4141"' if index == 0 else ""
            rows.append(
                f'<div class="ad-top-drift-row{emphasis}"{emphasis_style}>'
                f"<span>{escape(str(drift_type))}</span>"
                f"<span>{int(count)}</span>"
                "</div>"
            )
        _render_overview_html(
            f"""
            <div class="ad-card ad-overview-top-drifts">
              <div class="ad-card-title">Top Drifts</div>
              {''.join(rows)}
            </div>
            """
        )


def render_priority_review_list(data: pd.DataFrame) -> None:
    demo_priority_mask = data["risk_case_key"].astype(str).isin(DEMO_PRIORITY_RISK_CASE_KEYS)
    priority = data[
        data["risk_level"].isin(RISK_LEVELS)
        | demo_priority_mask
    ].copy()
    priority["is_demo_priority_case"] = priority["risk_case_key"].astype(str).isin(DEMO_PRIORITY_RISK_CASE_KEYS)
    priority["priority_sort_score"] = pd.to_numeric(priority["risk_score"], errors="coerce").fillna(0)
    priority["priority_sort_detected_at"] = pd.to_datetime(priority["detected_at"], errors="coerce")
    priority = priority.sort_values(
        ["is_demo_priority_case", "priority_sort_score", "priority_sort_detected_at", "case_id"],
        ascending=[False, False, False, True],
        na_position="last",
    ).head(3)
    priority["risk_title"] = priority["overview_title"].where(priority["overview_title"].ne(""), priority["risk_title"])
    priority["owner"] = priority["owner_name"] + " / " + priority["owner_team"]
    priority["detected_at"] = priority["detected_at"].apply(_format_datetime)

    rows = []
    for _, case in priority.reset_index(drop=True).iterrows():
        display_case_id = case.get("display_case_id", case["case_id"])
        risk_card_href = f"/Risk_Card?case={quote(str(display_case_id))}"
        rows.append(
            f"""
            <div class="ad-priority-row">
              <div class="ad-checkbox"></div>
              <div>
                <div style="display:flex; gap:14px; align-items:center; flex-wrap:wrap">
                  <span class="ad-row-kicker">{escape(str(display_case_id))}</span>
                  <span class="ad-row-title">{escape(str(case["risk_title"]))}</span>
                </div>
                <div class="ad-row-subline">
                  <span class="ad-risk-badge-slot">{_risk_badge(str(case["risk_level"]), compact=True)}</span>
                  <span class="ad-pill ad-owner-pill">{escape(str(case["owner"]))}</span>
                </div>
              </div>
              <div>
                <div class="ad-col-label">Identity</div>
                <span class="ad-identity-value">{escape(str(case["identity_name"]))}</span>
                {_identity_badge(str(case["identity_type"]))}
              </div>
              <div>
                <div class="ad-col-label">Detected At</div>
                <span class="ad-detected-value">{escape(str(case["detected_at"]))}</span>
                {_status_badge(str(case["review_status"]))}
              </div>
              <a class="ad-button" href="{risk_card_href}" target="_self">View Risk Card</a>
            </div>
            """
        )

    st.html(
        f"""
        <div class="ad-card ad-priority-card ad-overview-priority">
          <div class="ad-section-header">
            <div class="ad-section-title">Priority Review</div>
          </div>
          {''.join(rows)}
        </div>
        """
    )


def render_risk_header_card(case: pd.Series) -> None:
    st.html(
        f"""
        <div class="ad-card ad-risk-header">
          <div class="ad-risk-heading">
            <h2>{escape(str(case["identity_name"]))}</h2>
            {_risk_badge(str(case["risk_level"]))}
            {_status_badge(str(case["review_status"]))}
          </div>
          <div class="ad-risk-subtitle">
            {escape(str(case["drift_type"]))} &#183; {escape(str(case["object_type"]))} &#183; {escape(str(case["credential_status"]))}
          </div>
          <div class="ad-risk-subtitle">{escape(str(case["linked_owner_label"]))}</div>
          <div class="ad-risk-meta">
            {_meta_item("Object type", case["object_type"])}
            {_meta_item("Identity type", case["identity_type"])}
            {_meta_item("Credential status", case["credential_status"])}
            {_meta_item("Last Accessed", _format_datetime(case["last_accessed_at"]))}
          </div>
        </div>
        """
    )


def render_risk_header_card_v2(case: pd.Series) -> None:
    st.html(
        f"""
        <div class="ad-card ad-risk-header ad-risk-header-v2">
          <div class="ad-risk-heading">
            <h2>{escape(str(case["identity_name"]))}</h2>
            {_risk_badge(str(case["risk_level"]))}
          </div>
          <div class="ad-risk-subtitle">
            {escape(str(case["drift_type"]))} &#183; {escape(str(case["object_type"]))} &#183; {escape(str(case["credential_status"]))}
          </div>
          <div class="ad-risk-subtitle">{escape(str(case["linked_owner_label"]))}</div>
          <div class="ad-risk-meta">
            {_meta_item("Object type", case["object_type"])}
            {_meta_item("Identity type", case["identity_type"])}
            {_meta_item("Credential status", case["credential_status"])}
            {_meta_item("Last Accessed", _format_datetime(case["last_accessed_at"]))}
          </div>
        </div>
        """
    )


def render_risk_summary_card_v2(case: pd.Series) -> None:
    st.html(
        f"""
        <div class="ad-card ad-panel ad-panel-v2-equal">
          <h3>Risk Summary</h3>
          <p>{escape(str(case["risk_summary"]))}</p>
        </div>
        """
    )


def render_risk_factors_card_v2(case: pd.Series) -> None:
    factors = _as_list(case["risk_factors"]) or [
        f"Owner status: {case['owner_status']}",
        f"Credential status: {case['credential_status']}",
        f"Asset sensitivity: {case['asset_sensitivity']}",
        f"Permission level: {case['permission_level']}",
        f"Rotation status: {case['rotation_status']}",
    ]
    factors = [
        "소유자 계정 비활성화" if factor == "HR/IdP 계정 비활성화" else factor
        for factor in factors
    ]
    factor_html = []
    for index, factor in enumerate(factors):
        icon_file = "riskfactors-icon-check.svg" if index == 0 else "riskfactors-icon-noncheck.svg"
        icon = _icon_img(icon_file, "Risk factor status", "ad-factor-status-icon")
        factor_html.append(
            f"""
            <div class="ad-factor">
              <span class="ad-factor-icon">{icon}</span>
              <span>{escape(factor)}</span>
            </div>
            """
        )
    st.html(
        f"""
        <div class="ad-card ad-panel ad-panel-v2-equal">
          <h3>Risk Factors</h3>
          {''.join(factor_html)}
        </div>
        """
    )


def render_risk_summary_card(case: pd.Series) -> None:
    st.html(
        f"""
        <div class="ad-card ad-panel">
          <h3>Risk Summary</h3>
          <p>{escape(str(case["risk_summary"]))}</p>
        </div>
        """
    )


def render_risk_factors_card(case: pd.Series) -> None:
    factors = _as_list(case["risk_factors"]) or [
        f"Owner status: {case['owner_status']}",
        f"Credential status: {case['credential_status']}",
        f"Asset sensitivity: {case['asset_sensitivity']}",
        f"Permission level: {case['permission_level']}",
        f"Rotation status: {case['rotation_status']}",
    ]
    factor_html = []
    for index, factor in enumerate(factors):
        icon_file = "riskfactors-icon-check.svg" if index == 0 else "riskfactors-icon-noncheck.svg"
        icon = _icon_img(icon_file, "Risk factor status", "ad-factor-status-icon")
        factor_html.append(
            f"""
            <div class="ad-factor">
              <span class="ad-factor-icon">{icon}</span>
              <span>{escape(factor)}</span>
            </div>
            """
        )
    st.html(
        f"""
        <div class="ad-card ad-panel">
          <h3>Risk Factors</h3>
          {''.join(factor_html)}
        </div>
        """
    )


def render_review_info_card(case: pd.Series) -> None:
    st.html(
        f"""
        <div class="ad-card ad-panel">
          <h3>Review Info</h3>
          <div class="ad-meta-label">검토 담당자</div>
          <div class="ad-meta-value" style="margin-bottom:20px">{escape(str(case["reviewer"]))}</div>
          <div class="ad-meta-label">조치 담당자</div>
          <div class="ad-meta-value" style="margin-bottom:22px">{escape(str(case["action_owner"]))}</div>
          <div style="display:flex; gap:12px; align-items:center; flex-wrap:wrap">
            {_status_badge(str(case["review_status"]))}
            <span class="ad-row-kicker">Detected At: {escape(_format_datetime(case["detected_at"]))}</span>
          </div>
          <div class="ad-review-actions">
            <div class="ad-button ad-button-primary">Create Review Request</div>
            <div class="ad-button">Mark as In Progress</div>
            <div class="ad-action-row">
              <div class="ad-button">Mark as Resolved</div>
              <div class="ad-button">Mark as False Positive</div>
            </div>
          </div>
        </div>
        """
    )


def render_recommendation_panel(case: pd.Series) -> None:
    docs = _as_list(case["reference_docs"])
    plan = _as_list(case["action_plan"])
    st.html(
        f"""
        <div class="ad-card ad-panel">
          <div class="ad-card ad-panel" style="background:#f8f9fb; box-shadow:none">
            <h3>AI Summary</h3>
            <p>{escape(str(case["ai_summary"]))}</p>
          </div>
          <h3 style="margin-top:28px">참조 문서</h3>
          <div class="ad-doc-grid">
            {''.join(_doc_card(doc, index) for index, doc in enumerate(docs))}
          </div>
          <h3>실행 단계 <span style="color:#aeb5bf; font-size:16px">ⓘ</span></h3>
          <div>
            {''.join(_action_step(step, index + 1) for index, step in enumerate(plan))}
          </div>
        </div>
        """
    )


def render_ai_agent_placeholder(case: pd.Series) -> None:
    messages = _as_list(case["ai_agent_messages"])
    first = messages[0] if len(messages) > 0 else ""
    question = messages[1] if len(messages) > 1 else ""
    answer = messages[2] if len(messages) > 2 else ""
    st.html(
        f"""
        <div class="ad-card ad-panel">
          <div class="ad-agent-header">{_icon_img("icon-azure-openai.svg", "AI Agent", "ad-agent-icon")} AI Agent</div>
          <div class="ad-agent-body">
            <div class="ad-chat-bubble">
              <div class="ad-chat-name">AI Agent</div>
              {escape(first)}
            </div>
            <div class="ad-chat-bubble ad-chat-user">{escape(question)}</div>
            <div class="ad-chat-bubble">
              <div class="ad-chat-name">AI Agent</div>
              {escape(answer)}
            </div>
          </div>
          <div class="ad-agent-input">
            <span>AI Agent에게 질문하기</span>
            <span class="ad-button ad-button-primary" style="padding:10px 14px">Send</span>
          </div>
        </div>
        """
    )


def render_ticket_form_placeholder(case: pd.Series) -> None:
    ticket = _ticket_payload(case)
    st.markdown(
        """
        <style>
        .st-key-jira_ticket_panel {
          margin-top: 8px;
        }

        .st-key-jira_ticket_panel .ad-jira-preview-header {
          display: flex;
          align-items: center;
          gap: 10px;
          margin: 0 0 8px;
          color: #172B4D;
          font-size: 20px;
          font-weight: 700;
        }

        .st-key-jira_ticket_panel .ad-jira-preview-icon {
          width: 22px;
          height: 22px;
          object-fit: contain;
          display: block;
        }

        .st-key-jira_ticket_panel div[data-testid="stForm"] {
          border: 1px solid #DFE1E6;
          border-radius: 8px;
          background: #FFFFFF;
          padding: 18px 20px;
          box-shadow: 0 1px 2px rgba(9, 30, 66, 0.08);
        }

        .st-key-jira_ticket_panel div[data-testid="stHorizontalBlock"] {
          gap: 2rem;
        }

        .st-key-jira_ticket_panel label p {
          color: #44546F !important;
          font-size: 12px !important;
          font-weight: 700 !important;
        }

        .st-key-jira_ticket_panel div[data-testid="stSelectbox"] label {
          display: block !important;
        }

        .st-key-jira_ticket_panel input,
        .st-key-jira_ticket_panel textarea,
        .st-key-jira_ticket_panel [data-baseweb="select"] > div {
          border-color: #DFE1E6 !important;
          border-radius: 4px !important;
          background: #FFFFFF !important;
          color: #172B4D !important;
          font-size: 14px !important;
          font-weight: 600 !important;
        }

        .st-key-jira_ticket_panel textarea {
          line-height: 1.55 !important;
          font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
        }

        .st-key-jira_ticket_panel .st-key-jira_title input {
          min-height: 48px !important;
          font-size: 18px !important;
          font-weight: 700 !important;
        }

        .st-key-jira_ticket_panel .st-key-jira_explanation textarea {
          min-height: 390px !important;
        }

        .st-key-jira_ticket_panel .st-key-jira_detail_panel {
          min-height: 448px;
          padding: 12px 16px 14px;
          border: 1px solid #DFE1E6;
          border-radius: 8px;
          background: #FAFBFC;
        }

        .st-key-jira_ticket_panel .ad-jira-side-title {
          color: #172B4D;
          font-size: 16px;
          font-weight: 700;
          margin-bottom: 6px;
        }

        .st-key-jira_ticket_panel .ad-jira-button-spacer {
          height: 4px;
        }

        .st-key-jira_ticket_panel div[data-testid="stFormSubmitButton"] button {
          background: #0C66E4 !important;
          border-color: #0C66E4 !important;
          color: #FFFFFF !important;
          border-radius: 4px !important;
          min-height: 38px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="jira_ticket_panel"):
        st.html(
            f"""
            <div class="ad-jira-preview-header">
              {_icon_img("icon-jira.svg", "Jira", "ad-jira-preview-icon")}
              <span>Jira Issue Preview</span>
            </div>
            """
        )
        with st.form("ticket-placeholder-form"):
            left_col, right_col = st.columns([0.66, 0.34], gap="large", vertical_alignment="top")
            with left_col:
                title = st.text_input("Title", value=ticket["title"], key="jira_title")
                explanation = st.text_area("Explanation", value=ticket["explanation"], height=430, key="jira_explanation")
            with right_col:
                with st.container(key="jira_detail_panel"):
                    st.html('<div class="ad-jira-side-title">세부 사항</div>')
                    priority_options = ["Highest", "High", "Medium", "Low", "Lowest"]
                    assignee = st.text_input("담당자", value=_display_person_name(ticket["assignee"]))
                    priority = st.selectbox(
                        "우선 순위",
                        priority_options,
                        index=priority_options.index(ticket["priority"]),
                    )
                    label = st.text_input("레이블", value=ticket["label"])
                    due_date = st.text_input("기한", value="", placeholder="YYYY.MM.DD")
                    team = st.text_input("Team", value=ticket["team"])
                    reporter = st.text_input("보고자", value=_display_person_name(ticket["reporter"]))
                    st.html('<div class="ad-jira-button-spacer"></div>')
                    submitted = st.form_submit_button("Create Jira issue", use_container_width=True)

    if not submitted:
        return

    normalized_due_date = _normalize_jira_due_date(due_date)
    if normalized_due_date is None:
        st.error("기한은 YYYY.MM.DD 형식으로 입력해야 합니다.")
        return

    config = jira_client.load_jira_config()
    if config is None:
        st.error("Jira secrets 설정이 없습니다. apps/dashboard/.streamlit/secrets.toml의 [jira] 섹션을 확인하세요.")
        return

    full_explanation = _append_jira_sidebar_fields(explanation, assignee, team, reporter)
    try:
        result = jira_client.create_jira_issue(
            config,
            title=title,
            explanation=full_explanation,
            priority=priority,
            label=label,
            due_date=normalized_due_date or "",
        )
    except Exception as exc:
        st.error(str(exc))
        return

    st.success(f"Jira issue created: {result.key}")
    st.markdown(f"[Open Jira issue]({result.url})")


def _ticket_payload(case: pd.Series) -> dict[str, str]:
    display_case_id = str(case.get("display_case_id", case.get("case_id", "")))
    risk_level = str(case.get("risk_level", "")).upper()
    risk_case_key = str(case.get("risk_case_key", ""))
    identity_name = str(case.get("identity_name", ""))
    is_demo_case = (
        risk_case_key in DEMO_PRIORITY_RISK_CASE_KEYS
        or display_case_id == "CASE-7B4DC4"
        or identity_name == "sp-crm-customer-export-prod"
    )

    if is_demo_case:
        return {
            "title": "[CASE-7B4DC4][CRITICAL] NHI residual access review",
            "explanation": (
                "퇴사자와 연결된 NHI가 Production 환경의 Critical 민감 자산에 접근 가능한 상태로 확인되어 검토를 요청드립니다.\n\n"
                "- Case ID: CASE-7B4DC4\n"
                "- 드리프트 유형: NHI Access Drift \n"
                "- 대상 NHI: sp-crm-customer-export-prod\n"
                "- 연관 사용자: CRM 데이터 운영팀 김민수 (퇴사일자: 2026/06/10)\n"
                "- 민감 자산: customer-export-storage-prod\n"
                "- 환경/민감도: Production / Critical\n"
                "- 최종 위험도: CRITICAL\n\n"
                "■ 위험 근거\n"
                "퇴사자 김민수가 소유한 활성 App Registration sp-crm-customer-export-prod에 유효한 credential이 남아 있고 "
                "customer-export-storage-prod 자산 접근 경로가 활성 상태입니다.\n\n"
                "■ 권장 조치\n"
                "담당자와 실제 사용 목적을 확인한 후, 퇴사자와 연결된 활성 Client Secret을 즉시 교체해야 합니다. "
                "이후 Storage Account의 RBAC 권한 및 공개 접근 설정에 대한 점검이 필요합니다."
            ),
            "priority": "Highest",
            "assignee": "이다영",
            "label": "CASE-7B4DC4",
            "team": "CRM 데이터 운영팀",
            "reporter": "박지연",
        }

    title = f"[{display_case_id}][{risk_level}] {case.get('overview_title', case.get('risk_title', 'Access drift'))} review"
    explanation = (
        "접근 드리프트 위험이 확인되어 검토를 요청드립니다.\n\n"
        f"- Case ID: {display_case_id}\n"
        f"- 드리프트 유형: {case.get('drift_type', '')}\n"
        f"- 대상 Identity: {case.get('identity_name', '')}\n"
        f"- 연관 사용자: {case.get('owner_team', '')} {case.get('owner_name', '')}\n"
        f"- 민감 자산: {case.get('asset_full_name', case.get('asset_name', ''))}\n"
        f"- 환경/민감도: {case.get('asset_type', '')} / {case.get('asset_sensitivity', '')}\n"
        f"- 최종 위험도: {risk_level}\n\n"
        "■ 위험 근거\n"
        f"{case.get('risk_summary', '')}\n\n"
        "■ 권장 조치\n"
        f"{case.get('ai_summary', case.get('recommended_action', ''))}"
    )
    return {
        "title": title,
        "explanation": explanation,
        "priority": _jira_priority_from_risk_level(str(case.get("risk_level", ""))),
        "assignee": str(case.get("action_owner", "")),
        "label": display_case_id,
        "team": str(case.get("owner_team", "")),
        "reporter": str(case.get("reviewer", "")),
    }


def _jira_priority_from_risk_level(risk_level: str) -> str:
    mapping = {
        "critical": "Highest",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
    }
    return mapping.get(str(risk_level).strip().lower(), "Medium")


def _normalize_jira_due_date(value: str) -> str | None:
    text = str(value).strip()
    if not text:
        return ""
    match = re.fullmatch(r"(\d{4})\.(\d{2})\.(\d{2})", text)
    if not match:
        return None
    normalized = "-".join(match.groups())
    try:
        datetime.strptime(normalized, "%Y-%m-%d")
    except ValueError:
        return None
    return normalized


def _display_person_name(value: str) -> str:
    text = str(value).strip()
    if not text:
        return ""
    for separator in ["·", "/", "|", ","]:
        if separator in text:
            return text.split(separator, 1)[0].strip()
    return text


def _append_jira_sidebar_fields(explanation: str, assignee: str, team: str, reporter: str) -> str:
    return (
        f"{explanation}\n\n"
        "■ Jira 입력 정보\n"
        f"- 담당자: {assignee}\n"
        f"- Team: {team}\n"
        f"- 보고자: {reporter}"
    )


def _legend_row(label: str, value: int, color: str) -> str:
    return f"""
    <div class="ad-legend-row">
      <span><span class="ad-dot" style="background:{color}"></span>{escape(label)}</span>
      <span>{int(value)}</span>
    </div>
    """


def _render_overview_html(html: str) -> None:
    compact_html = "".join(line.strip() for line in dedent(html).strip().splitlines())
    st.markdown(compact_html, unsafe_allow_html=True)


def _issue_bar(label: str, value: int, max_value: int, color: str) -> str:
    height = max(14, round((value / max_value) * 88))
    return f"""
    <div class="ad-overview-issue-bar-wrap" aria-label="{escape(label)} {value}">
      <div class="ad-overview-issue-value">{value}</div>
      <div class="ad-overview-issue-bar" style="height:{height}px; background:{color};"></div>
    </div>
    """


def _percentage(value: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((value / total) * 100, 2)


def _risk_badge(level: str, compact: bool = False) -> str:
    badge_files = {
        "Critical": "badge-critical.svg",
        "High": "badge-high.svg",
        "Medium": "badge-medium.svg",
    }
    badge_file = badge_files.get(level)
    if badge_file:
        return _badge_img(badge_file, level, "ad-risk-badge-img")
    return f'<span class="ad-pill">{escape(level)}</span>'


def _status_badge(status: str) -> str:
    status_badges = {
        "Open": "badge-priorityreview-open.svg",
        "In Review": "badge-priorityreview-inreview.svg",
    }
    if status in status_badges:
        return _badge_img(status_badges[status], status, "ad-status-badge-img")
    css = "ad-pill-open" if status == "Open" else "ad-pill-in-review"
    return f'<span class="ad-pill {css}">{escape(status)}</span>'


def _identity_badge(identity_type: str) -> str:
    badge_file = "badge-nhi.svg" if identity_type == "NHI" else "badge-hi.svg"
    return _badge_img(badge_file, identity_type, "ad-identity-badge-img")


def _meta_item(label: str, value: object) -> str:
    return f"""
    <div>
      <div class="ad-meta-label">{escape(label)}</div>
      <div class="ad-meta-value">{escape(str(value))}</div>
    </div>
    """


def _doc_card(doc: str, index: int) -> str:
    parts = [part.strip() for part in doc.split(" / ", 1)]
    title = parts[0]
    subtitle = parts[1] if len(parts) > 1 else ""
    icons = ["icon-pdf.png", "icon-policy-yellow.png", "icon-azure.svg", "icon-policy-green.png"]
    icon = _icon_img(icons[index % len(icons)], title, "ad-doc-card-icon")
    return f"""
    <div class="ad-doc-card">
      <div class="ad-doc-icon">{icon}</div>
      <div>
        <div class="ad-doc-title">{escape(title)}</div>
        <div class="ad-doc-subtitle">{escape(subtitle)}</div>
      </div>
    </div>
    """


def _action_step(step: str, index: int) -> str:
    return f"""
    <div class="ad-step">
      <div class="ad-step-number">{index}</div>
      <div>{escape(step)}</div>
    </div>
    """


def _asset_data_uri(directory: str, filename: str) -> str:
    path = ASSET_DIR / directory / filename
    mime_type = mimetypes.guess_type(path.name)[0] or "image/svg+xml"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _asset_img(directory: str, filename: str, alt: str, class_name: str = "") -> str:
    class_attr = f' class="{escape(class_name)}"' if class_name else ""
    return f'<img src="{_asset_data_uri(directory, filename)}" alt="{escape(alt)}"{class_attr} />'


def _icon_img(filename: str, alt: str, class_name: str = "") -> str:
    return _asset_img("icons", filename, alt, class_name)


def _badge_img(filename: str, alt: str, class_name: str = "") -> str:
    return _asset_img("badges", filename, alt, class_name)


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



