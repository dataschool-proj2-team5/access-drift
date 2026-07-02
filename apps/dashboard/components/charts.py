from __future__ import annotations

import base64
import mimetypes
from functools import lru_cache
from html import escape
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

STATUS_ORDER = ["Open", "In Review", "Resolved"]
STATUS_COLORS = ["#128bf4", "#ff7b73", "#d8dce2"]
RISK_LEVEL_ORDER = ["Critical", "High", "Medium", "Low"]
RISK_COLORS = ["#003b68", "#f23d42", "#f5b844", "#41b76a"]
ICON_DIR = Path(__file__).resolve().parents[1] / "assets" / "icons"


def render_risk_level_donut(data: pd.DataFrame) -> None:
    counts = (
        data[data["review_status"].isin(STATUS_ORDER)]
        .groupby("review_status", dropna=False)
        .size()
        .reindex(STATUS_ORDER, fill_value=0)
    )
    fig = go.Figure(
        data=[
            go.Pie(
                labels=STATUS_ORDER,
                values=counts.tolist(),
                hole=0.58,
                marker={"colors": STATUS_COLORS, "line": {"color": "#ffffff", "width": 0}},
                textinfo="none",
                sort=False,
                direction="clockwise",
            )
        ]
    )
    fig.update_layout(
        height=172,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        annotations=[
            {
                "text": f"<b style='color:#aeb5bf'>Total</b><br><b style='font-size:27px;color:#111827'>{len(data)}</b>",
                "showarrow": False,
                "x": 0.5,
                "y": 0.5,
                "font": {"size": 18},
            }
        ],
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_issue_bar_chart(data: pd.DataFrame) -> None:
    counts = (
        data[data["risk_level"].isin(RISK_LEVEL_ORDER)]
        .groupby("risk_level", dropna=False)
        .size()
        .reindex(RISK_LEVEL_ORDER, fill_value=0)
    )
    fig = go.Figure(
        data=[
            go.Bar(
                x=RISK_LEVEL_ORDER,
                y=counts.tolist(),
                marker={"color": RISK_COLORS},
                width=0.32,
                text=counts.tolist(),
                textposition="outside",
                textfont={"size": 16, "color": "#111827", "family": "Inter"},
                hoverinfo="skip",
            )
        ]
    )
    fig.update_layout(
        height=172,
        margin={"l": 8, "r": 8, "t": 16, "b": 24},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        bargap=0.55,
        xaxis={
            "showgrid": False,
            "showline": True,
            "linecolor": "#e2e6eb",
            "tickfont": {"size": 14, "color": "#111827", "family": "Inter"},
        },
        yaxis={"visible": False, "range": [0, max(counts.max() + 2, 12)]},
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_access_path(case: pd.Series) -> None:
    steps = [
        {
            "icon_file": "icon-human.svg",
            "label": "",
            "value": case["owner_name"],
            "caption": f"{case['owner_team']}<br>{case['related_person_status']}",
            "pill": "Owner",
            "pill_class": "ad-pill-owner",
        },
        {
            "icon_file": "accesspath-icon-sp.svg",
            "label": "NHI",
            "value": case["object_type"],
            "caption": case["identity_name"].replace("sp-crm-customer-", "sp-crm-customer-<br>"),
            "pill": "",
            "pill_class": "",
        },
        {
            "icon_file": "accesspath-icon-credential.svg",
            "label": "Credential",
            "value": case["credential_type"],
            "caption": "credential still valid",
            "pill": "Activity",
            "pill_class": "ad-pill-activity",
        },
        {
            "icon_file": "accesspath-icon-permission.svg",
            "label": "Permission",
            "value": case["permission_level"],
            "caption": "can read and list<br>storage objects",
            "pill": "",
            "pill_class": "",
        },
        {
            "icon_file": "accesspath-icon-asset.svg",
            "label": "Sensitive Asset",
            "value": case["asset_name"],
            "caption": "crm-customer-<br>export-prod",
            "pill": "",
            "pill_class": "",
        },
        {
            "icon_file": "accesspath-icon-datascope.svg",
            "label": "Data Scope",
            "value": case["data_scope"],
            "caption": case["data_categories"],
            "pill": case["asset_sensitivity"],
            "pill_class": "ad-pill-sensitive",
        },
    ]
    html = ['<div class="ad-card ad-access-card"><h3 class="ad-card-title">Access Path</h3><div class="ad-access-canvas">']
    for step in steps:
        pill = ""
        if step["pill"]:
            pill = f'<span class="ad-pill {step["pill_class"]}">{escape(str(step["pill"]))}</span>'
        icon = _icon_img(step["icon_file"], str(step["label"] or step["value"]), "ad-path-icon")
        html.append(
            f"""
            <div class="ad-path-step">
              <div class="ad-icon-box">{icon}</div>
              <div class="ad-path-label">{escape(str(step["label"]))}</div>
              <div class="ad-path-value">{escape(str(step["value"]))}</div>
              <div class="ad-path-caption">{step["caption"]}</div>
              <div style="margin-top:10px">{pill}</div>
            </div>
            """
        )
    html.append("</div></div>")
    st.html("".join(html))


def render_access_path_v2(case: pd.Series) -> None:
    owner_caption = f"{escape(str(case['owner_team']))}<br>{escape(str(case['related_person_status']))}"
    identity_caption = escape(str(case["identity_name"])).replace("sp-crm-customer-", "sp-crm-customer-<br>")
    steps = [
        {
            "icon_file": "icon-human.svg",
            "value": case["owner_name"],
            "caption": owner_caption,
            "pill": "Owner",
            "pill_class": "ad-pill-owner",
        },
        {
            "icon_file": "accesspath-icon-sp.svg",
            "value": case["object_type"],
            "caption": identity_caption,
            "pill": "",
            "pill_class": "",
        },
        {
            "icon_file": "accesspath-icon-credential.svg",
            "value": case["credential_type"],
            "caption": "credential still valid",
            "pill": "Activity",
            "pill_class": "ad-pill-activity",
        },
        {
            "icon_file": "accesspath-icon-permission.svg",
            "value": case["permission_level"],
            "caption": "can read and list<br>storage objects",
            "pill": "",
            "pill_class": "",
        },
        {
            "icon_file": "accesspath-icon-asset.svg",
            "value": case["asset_name"],
            "caption": "crm-customer-<br>export-prod",
            "pill": "",
            "pill_class": "",
        },
        {
            "icon_file": "accesspath-icon-datascope.svg",
            "value": case["data_scope"],
            "caption": escape(str(case["data_categories"])),
            "pill": case["asset_sensitivity"],
            "pill_class": "ad-pill-sensitive",
        },
    ]
    html = [
        '<div class="ad-card ad-access-card ad-access-card-v2">'
        '<h3 class="ad-card-title">Access Path</h3>'
        '<div class="ad-access-canvas" style="padding:22px 14px; gap:14px; align-items:stretch;">'
    ]
    for step in steps:
        pill = ""
        if step["pill"]:
            pill = f'<span class="ad-pill {step["pill_class"]}">{escape(str(step["pill"]))}</span>'
        icon = _icon_img(step["icon_file"], str(step["value"]), "ad-path-icon")
        html.append(
            f"""
            <div class="ad-path-step" style="height:122px; min-height:122px; padding:13px 12px; display:flex; flex-direction:column; box-sizing:border-box;">
              <div class="ad-path-main-row" style="display:flex; align-items:center; gap:10px; min-height:34px; margin-bottom:8px;">
                <div class="ad-icon-box" style="width:30px; height:30px; min-width:30px; margin-bottom:0; flex:0 0 30px;">{icon}</div>
                <div class="ad-path-value" style="font-size:15px; line-height:1.25; margin-bottom:0; min-height:0; display:block;">{escape(str(step["value"]))}</div>
              </div>
              <div class="ad-path-caption" style="font-size:12px; line-height:1.35; min-height:30px;">{step["caption"]}</div>
              <div class="ad-path-pill-slot" style="margin-top:auto; min-height:22px; display:flex; align-items:flex-end;">{pill}</div>
            </div>
            """
        )
    html.append("</div></div>")
    st.html("".join(html))


@lru_cache(maxsize=None)
def _icon_data_uri(filename: str) -> str:
    path = ICON_DIR / filename
    mime_type = mimetypes.guess_type(path.name)[0] or "image/svg+xml"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _icon_img(filename: str, alt: str, class_name: str = "") -> str:
    class_attr = f' class="{escape(class_name)}"' if class_name else ""
    return f'<img src="{_icon_data_uri(filename)}" alt="{escape(alt)}"{class_attr} />'
