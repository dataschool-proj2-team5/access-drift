from __future__ import annotations

from html import escape
from urllib.parse import quote

import pandas as pd
import streamlit as st

from components.cards import _badge_img, _format_datetime


VISIBLE_RISK_LEVELS = ["Critical", "High", "Medium"]
RISK_BADGE_FILES = {
    "Critical": "badge-critical.svg",
    "High": "badge-high.svg",
    "Medium": "badge-medium.svg",
}


def render_asset_table_fit(data: pd.DataFrame) -> None:
    assets = data[data["risk_level"].isin(VISIBLE_RISK_LEVELS)].copy()
    assets["drift_label"] = assets["drift_type"]
    assets["environment"] = assets.apply(_environment_for_case, axis=1)
    assets["owner"] = assets["owner_name"]
    assets["detected_at_display"] = assets["detected_at"].apply(_format_datetime)
    assets = assets.sort_values("risk_score", ascending=False)

    rows = []
    for _, case in assets.reset_index(drop=True).iterrows():
        display_case_id = case.get("display_case_id", case["case_id"])
        risk_card_href = f"/Risk_Card?case={quote(str(display_case_id))}"
        rows.append(
            f"""
            <div class="ad-asset-row">
              <div class="ad-asset-value ad-asset-case-id">{escape(str(display_case_id))}</div>
              <div class="ad-asset-value">{escape(str(case["drift_label"]))}</div>
              <div class="ad-asset-value">{escape(str(case["environment"]))}</div>
              <div class="ad-asset-value">{escape(str(case["identity_name"]))}</div>
              <div class="ad-asset-value">{escape(str(case["identity_type"]))}</div>
              <div class="ad-asset-value">{escape(str(case["owner"]))}</div>
              <div class="ad-asset-value">{escape(str(case["detected_at_display"]))}</div>
              <div>{_asset_risk_badge(str(case["risk_level"]))}</div>
              <a class="ad-button" href="{risk_card_href}" target="_self">View</a>
            </div>
            """
        )

    st.html(
        f"""
        <style>
          .ad-asset-list-card {{
            margin-top: 18px;
            padding: 0;
            border-radius: 16px;
            overflow-x: hidden;
            overflow-y: hidden;
          }}

          .ad-asset-table-header,
          .ad-asset-row {{
            display: grid;
            grid-template-columns: 80px 180px 84px minmax(220px, 0.8fr) 56px 120px 140px 104px 72px;
            column-gap: 12px;
            align-items: center;
            min-width: 0;
          }}

          .ad-asset-table-header {{
            padding: 12px 14px;
            color: #4b5563;
            font-size: 13px;
            font-weight: 800;
            border-bottom: 1px solid #e2e8f0;
            background: #f8fafc;
          }}

          .ad-asset-row {{
            min-height: 58px;
            padding: 11px 14px;
            border-bottom: 1px solid #e2e8f0;
            background: #fff;
          }}

          .ad-asset-row:last-child {{
            border-bottom: 0;
          }}

          .ad-asset-case-id {{
            color: #9ba3b1;
            font-size: 13px;
          }}

          .ad-asset-value {{
            color: #111827;
            font-size: 13px;
            font-weight: 700;
            line-height: 1.25;
          }}

          .ad-asset-table-header > div:nth-child(2),
          .ad-asset-table-header > div:nth-child(4),
          .ad-asset-table-header > div:nth-child(6),
          .ad-asset-row > div:nth-child(2),
          .ad-asset-row > div:nth-child(4),
          .ad-asset-row > div:nth-child(6) {{
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }}

          .ad-asset-table-header > div:nth-child(7),
          .ad-asset-row > div:nth-child(7) {{
            white-space: nowrap;
          }}

          .ad-asset-table-header > div:nth-child(8),
          .ad-asset-table-header > div:nth-child(9),
          .ad-asset-row > div:nth-child(8),
          .ad-asset-row > a:nth-child(9) {{
            justify-self: center;
          }}

          .ad-asset-row .ad-risk-badge-img {{
            height: 26px;
            width: auto;
            max-width: 86px;
          }}

          .ad-asset-row .ad-button {{
            height: 30px;
            min-width: 52px;
            padding: 0 8px;
            border-radius: 9px;
            border: 1px solid #b9d2e7;
            background: #ffffff;
            color: var(--ad-blue);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            justify-self: center;
            transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
          }}

          .ad-asset-row .ad-button:hover {{
            background: var(--ad-blue);
            border-color: var(--ad-blue);
            color: #ffffff;
          }}

          @media (max-width: 1400px) {{
            .ad-asset-table-header,
            .ad-asset-row {{
              grid-template-columns: 64px 130px 70px minmax(140px, 0.7fr) 42px 106px 104px 76px 56px;
              column-gap: 8px;
            }}
          }}

          @media (max-width: 1200px) {{
            .ad-asset-list-card {{ overflow-x: hidden; }}
          }}
        </style>
        <div class="ad-card ad-asset-list-card">
          <div class="ad-asset-table-header">
            <div>Case ID</div>
            <div>Drift Type</div>
            <div>Environment</div>
            <div>Identity</div>
            <div>Type</div>
            <div>Owner</div>
            <div>Detected At</div>
            <div>Risk</div>
            <div>Action</div>
          </div>
          {''.join(rows)}
        </div>
        """
    )


def _environment_for_case(case: pd.Series) -> str:
    identity_name = str(case.get("identity_name", "")).lower()
    object_name = str(case.get("object_name", "")).lower()
    drift_type = str(case.get("drift_type", "")).lower()
    asset_type = str(case.get("asset_type", "")).lower()
    combined = " ".join([identity_name, object_name, drift_type, asset_type])

    if any(token in combined for token in ["repo", "release-bot", "github", "contractor.repo"]):
        return "GitHub"
    if "postman" in combined or "api_key" in combined:
        return "Postman"
    if "slack" in combined:
        return "Slack"
    if "jira" in combined:
        return "Jira"
    if "confluence" in combined:
        return "Confluence"
    return "Azure"


def _asset_risk_badge(level: str) -> str:
    badge_file = RISK_BADGE_FILES.get(level)
    if badge_file:
        return _badge_img(badge_file, level, "ad-risk-badge-img")
    return f'<span class="ad-pill">{escape(level)}</span>'
