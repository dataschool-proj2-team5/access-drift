from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from components.cards import (
    _action_step,
    _as_list,
    _doc_card,
    _format_datetime,
    _icon_img,
    _status_badge,
)


def render_review_info_card(case: pd.Series) -> None:
    st.html(
        f"""
        <div class="ad-card ad-panel">
          <h3>Review Info</h3>
          <div class="ad-meta-label">\uac80\ud1a0 \ub2f4\ub2f9\uc790</div>
          <div class="ad-meta-value" style="margin-bottom:20px">{escape(str(case["reviewer"]))}</div>
          <div class="ad-meta-label">\uc870\uce58 \ub2f4\ub2f9\uc790</div>
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
          <h3 style="margin-top:28px">\ucc38\uc870 \ubb38\uc11c</h3>
          <div class="ad-doc-grid">
            {''.join(_doc_card(doc, index) for index, doc in enumerate(docs))}
          </div>
          <h3>\uc2e4\ud589 \ub2e8\uacc4 <span style="color:#aeb5bf; font-size:16px">\u24d8</span></h3>
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
            <span>AI Agent\uc5d0\uac8c \uc9c8\ubb38\ud558\uae30</span>
            <span class="ad-button ad-button-primary" style="padding:10px 14px">Send</span>
          </div>
        </div>
        """
    )
