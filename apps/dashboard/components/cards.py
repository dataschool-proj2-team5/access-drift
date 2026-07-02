from __future__ import annotations

from html import escape
from textwrap import dedent
from urllib.parse import quote

import pandas as pd
import streamlit as st

RISK_LEVELS = ["Critical", "High", "Medium", "Low"]


def render_summary_cards(data: pd.DataFrame) -> None:
    total_col, issues_col, drift_col = st.columns([1.02, 1.15, 0.9], gap="medium")
    status_counts = data["review_status"].value_counts()
    open_count = int(status_counts.get("Open", 0))
    review_count = int(status_counts.get("In Review", 0))
    resolved_count = int(status_counts.get("Resolved", 0))
    total_count = len(data)
    open_stop = _percentage(open_count, total_count)
    review_stop = _percentage(open_count + review_count, total_count)

    with total_col:
        _render_overview_html(
            f"""
            <div class="ad-overview-summary-card">
              <div class="ad-overview-title">Total</div>
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
    demo_case_order = ["CASE-001", "CASE-002", "CASE-003"]
    priority = data[data["case_id"].isin(demo_case_order)].copy()
    priority["case_sort"] = pd.Categorical(priority["case_id"], categories=demo_case_order, ordered=True)
    priority = priority.sort_values("case_sort")
    priority["risk_title"] = priority["overview_title"].where(priority["overview_title"].ne(""), priority["risk_title"])
    priority["owner"] = priority["owner_name"] + " / " + priority["owner_team"]
    priority["detected_at"] = priority["detected_at"].apply(_format_datetime)

    rows = []
    for index, case in priority.reset_index(drop=True).iterrows():
        primary_button = " ad-button-primary" if index == 0 else ""
        risk_card_href = f"/Risk_Card?case_id={quote(str(case['case_id']))}"
        rows.append(
            f"""
            <div class="ad-priority-row">
              <div class="ad-checkbox"></div>
              <div>
                <div style="display:flex; gap:14px; align-items:center; flex-wrap:wrap">
                  <span class="ad-row-kicker">{escape(str(case["case_id"]))}</span>
                  <span class="ad-row-title">{escape(str(case["risk_title"]))}</span>
                </div>
                <div class="ad-row-subline">
                  {_risk_badge(str(case["risk_level"]), compact=True)}
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
              <a class="ad-button{primary_button}" href="{risk_card_href}" target="_self">View Risk Card</a>
            </div>
            """
        )

    st.html(
        f"""
        <div class="ad-card ad-priority-card ad-overview-priority">
          <div class="ad-section-header">
            <div class="ad-section-title">Priority Review</div>
            <div class="ad-count-pill">{len(priority)} review items</div>
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
            {escape(str(case["drift_type"]))} · {escape(str(case["object_type"]))} · {escape(str(case["credential_status"]))}
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
        icon = "✓" if index == 0 else "!"
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
          <div class="ad-agent-header">💠 AI Agent</div>
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
    with st.form("ticket-placeholder-form"):
        st.text_input("Title", value=f"[Access Drift] {case['risk_title']}")
        st.text_area("Description", value=case["recommended_action"], height=160)
        st.selectbox("Priority", ["High", "Medium", "Low"])
        st.text_input("Assignee", value=case["action_owner"])
        st.form_submit_button("Create ticket", disabled=True)


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
    css = "ad-pill-critical" if level == "Critical" else "ad-pill-high"
    label = escape(level) if compact else f"▮▮▮ {escape(level)}"
    return f'<span class="ad-pill {css}">{label}</span>'


def _status_badge(status: str) -> str:
    css = "ad-pill-open" if status == "Open" else "ad-pill-in-review"
    return f'<span class="ad-pill {css}">{escape(status)}</span>'


def _identity_badge(identity_type: str) -> str:
    css = "ad-pill-nhi" if identity_type == "NHI" else "ad-pill-hi"
    return f'<span class="ad-pill {css} ad-identity-type-pill" style="margin-left:8px">{escape(identity_type)}</span>'


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
    icons = ["PDF", "✓", "A", "◆"]
    return f"""
    <div class="ad-doc-card">
      <div class="ad-doc-icon">{escape(icons[index % len(icons)])}</div>
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
