from __future__ import annotations

import streamlit as st


def apply_dashboard_style(page: str | None = None) -> None:
    st.markdown(
        """
        <style>
        :root {
          --ad-bg: #f4f5f7;
          --ad-card: #ffffff;
          --ad-border: #e2e6eb;
          --ad-text: #111827;
          --ad-muted: #737b8c;
          --ad-soft: #f7f8fa;
          --ad-blue: #003b68;
          --ad-blue-soft: #e8f3ff;
          --ad-red: #f23d42;
          --ad-red-soft: #ffe2e4;
          --ad-yellow: #f5b844;
          --ad-yellow-soft: #fff3d8;
          --ad-green: #41b76a;
          --ad-gray: #aeb5bf;
        }

        .stApp {
          background: var(--ad-bg);
          color: var(--ad-text);
        }

        html, body, [class*="css"], *,
        button, input, select, textarea,
        .stMarkdown, .stMarkdown *,
        .js-plotly-plot, .js-plotly-plot * {
          font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
        }

        .block-container {
          max-width: 1380px;
          padding: 2.25rem 2rem 4rem;
          margin-left: auto;
          margin-right: auto;
        }

        header[data-testid="stHeader"] {
          background: transparent;
        }

        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"] {
          display: none;
        }

        h1, h2, h3, p {
          letter-spacing: 0;
        }

        .ad-page-title {
          font-size: 40px;
          line-height: 1.1;
          font-weight: 800;
          margin: 0 0 34px;
          color: var(--ad-text);
        }

        .ad-risk-title {
          font-size: 38px;
          line-height: 1.1;
          font-weight: 800;
          margin: 0 0 14px;
          color: var(--ad-text);
        }

        .ad-page-caption {
          color: var(--ad-muted);
          font-size: 16px;
          margin: -4px 0 24px;
        }

        .ad-card {
          background: var(--ad-card);
          border: 1px solid var(--ad-border);
          border-radius: 18px;
          box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
          padding: 28px;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
          background: var(--ad-card);
          border: 1px solid var(--ad-border);
          border-radius: 18px;
          box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
          padding: 22px 24px;
        }

        div[data-testid="stPlotlyChart"] {
          margin-top: -8px;
        }

        [data-testid="stSidebar"] {
          background: #444444;
          border-right: 1px solid #3a3a3a;
        }

        [data-testid="stSidebar"] * {
          color: #f5f5f5;
        }

        .ad-summary-grid {
          display: grid;
          grid-template-columns: 1.02fr 1.15fr 0.9fr;
          gap: 32px;
          margin-bottom: 44px;
        }

        .ad-card-title {
          font-size: 26px;
          font-weight: 800;
          margin: 0 0 18px;
          color: var(--ad-text);
        }

        .ad-total-layout {
          display: grid;
          grid-template-columns: 220px 1fr;
          gap: 16px;
          align-items: center;
        }

        .ad-donut {
          --open: 37.5%;
          --review: 66.66%;
          width: 168px;
          height: 168px;
          border-radius: 50%;
          background: conic-gradient(
            #128bf4 0 var(--open),
            #ff7b73 var(--open) var(--review),
            #d8dce2 var(--review) 100%
          );
          display: grid;
          place-items: center;
          margin: 0 auto;
        }

        .ad-donut-inner {
          width: 108px;
          height: 108px;
          border-radius: 50%;
          background: #fff;
          display: grid;
          place-items: center;
          text-align: center;
          color: var(--ad-gray);
          font-weight: 800;
          font-size: 22px;
        }

        .ad-donut-inner strong {
          display: block;
          color: var(--ad-text);
          font-size: 31px;
          margin-top: 6px;
        }

        .ad-legend-row,
        .ad-top-drift-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          font-weight: 800;
          color: var(--ad-text);
          font-size: 18px;
          padding: 8px 0;
        }

        .ad-dot {
          width: 12px;
          height: 12px;
          border-radius: 999px;
          display: inline-block;
          margin-right: 12px;
        }

        .ad-top-drift-row {
          border-bottom: 1px solid var(--ad-border);
          padding: 13px 0;
        }

        .ad-top-drift-row:last-child {
          border-bottom: 0;
        }

        .ad-top-drift-row:first-child {
          color: var(--ad-red);
        }

        .ad-priority-card {
          padding: 30px 32px 34px;
          margin-top: 6px;
        }

        .ad-section-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 24px;
        }

        .ad-section-title {
          font-size: 28px;
          font-weight: 800;
          color: var(--ad-text);
        }

        .ad-count-pill {
          background: var(--ad-blue-soft);
          color: var(--ad-blue);
          border-radius: 999px;
          padding: 8px 18px;
          font-size: 14px;
          font-weight: 800;
        }

        .ad-priority-row {
          display: grid;
          grid-template-columns: 34px 450px minmax(320px, 1fr) 290px 170px;
          align-items: center;
          gap: 18px;
          border: 1px solid var(--ad-border);
          border-radius: 16px;
          background: #fff;
          padding: 24px 28px;
          margin-top: 20px;
        }

        .ad-checkbox {
          width: 22px;
          height: 22px;
          border: 2px solid #d2d8e0;
          border-radius: 6px;
        }

        .ad-row-kicker {
          color: #9ba3b1;
          font-weight: 800;
          font-size: 15px;
        }

        .ad-row-title,
        .ad-identity-value,
        .ad-detected-value {
          font-size: 20px;
          font-weight: 800;
          color: var(--ad-text);
        }

        .ad-row-subline {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-top: 14px;
          flex-wrap: wrap;
        }

        .ad-col-label {
          color: #9ba3b1;
          font-weight: 800;
          font-size: 17px;
          margin-bottom: 16px;
        }

        .ad-button {
          border-radius: 12px;
          border: 1px solid #d4dae2;
          padding: 13px 22px;
          text-align: center;
          font-weight: 800;
          color: var(--ad-text);
          background: #fff;
          text-decoration: none;
        }

        .ad-button-primary {
          background: var(--ad-blue);
          border-color: var(--ad-blue);
          color: #fff;
        }

        .ad-button:hover {
          text-decoration: none;
        }

        .ad-pill {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 7px;
          border-radius: 999px;
          padding: 7px 13px;
          font-size: 13px;
          font-weight: 800;
          line-height: 1;
          white-space: nowrap;
        }

        .ad-pill-critical,
        .ad-pill-nhi {
          background: var(--ad-blue-soft);
          color: var(--ad-blue);
        }

        .ad-pill-high,
        .ad-pill-open,
        .ad-pill-sensitive,
        .ad-pill-activity,
        .ad-pill-owner {
          background: var(--ad-red-soft);
          color: var(--ad-red);
        }

        .ad-pill-in-review {
          background: var(--ad-yellow-soft);
          color: #8a5b00;
        }

        .ad-pill-hi {
          background: #e8f3ff;
          color: var(--ad-blue);
        }

        .ad-owner-pill {
          border: 1px solid #d7dde5;
          color: var(--ad-text);
          background: #fff;
        }

        .ad-owner-pill::before {
          content: "";
          width: 18px;
          height: 18px;
          border-radius: 999px;
          background: #cdd3dc;
          display: inline-block;
        }

        .ad-risk-header {
          margin: 18px 0 26px;
          padding: 30px 24px;
        }

        .ad-risk-heading {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 16px;
          margin-bottom: 10px;
        }

        .ad-risk-heading h2 {
          font-size: 30px;
          font-weight: 800;
          margin: 0;
          color: var(--ad-text);
        }

        .ad-risk-subtitle {
          color: var(--ad-muted);
          font-size: 18px;
          font-weight: 700;
          margin: 8px 0;
        }

        .ad-risk-meta {
          display: grid;
          grid-template-columns: repeat(4, minmax(160px, 1fr));
          gap: 24px;
          margin-top: 18px;
        }

        .ad-meta-label {
          color: var(--ad-muted);
          font-size: 13px;
          font-weight: 800;
          margin-bottom: 4px;
        }

        .ad-meta-value {
          color: var(--ad-text);
          font-size: 17px;
          font-weight: 800;
        }

        .stTabs [data-baseweb="tab-list"] {
          gap: 28px;
          border-bottom: 1px solid var(--ad-border);
        }

        .stTabs [data-baseweb="tab"] {
          padding: 16px 0 14px;
          font-size: 20px;
          font-weight: 800;
          color: var(--ad-muted);
        }

        .stTabs [aria-selected="true"] {
          color: var(--ad-text);
          border-bottom: 0 !important;
        }

        .stTabs [data-baseweb="tab-highlight"] {
          background: var(--ad-blue) !important;
          height: 3px !important;
        }

        .ad-access-card {
          padding: 24px;
          margin-top: 18px;
        }

        .ad-access-canvas {
          background: var(--ad-soft);
          border: 1px solid var(--ad-border);
          border-radius: 12px;
          padding: 74px 18px;
          margin-top: 16px;
          display: grid;
          grid-template-columns: repeat(6, 1fr);
          gap: 26px;
          align-items: center;
        }

        .ad-path-step {
          position: relative;
          min-height: 155px;
          background: #fff;
          border: 1px solid var(--ad-border);
          border-radius: 8px;
          padding: 18px 16px;
        }

        .ad-path-step:not(:last-child)::after {
          content: "";
          position: absolute;
          top: 50%;
          right: -27px;
          width: 27px;
          height: 2px;
          background: #7d8794;
        }

        .ad-icon-box {
          width: 42px;
          height: 42px;
          border-radius: 2px;
          background: var(--ad-blue-soft);
          display: grid;
          place-items: center;
          color: var(--ad-blue);
          font-weight: 800;
          margin-bottom: 14px;
        }

        .ad-icon-box img {
          display: block;
          width: 28px;
          height: 28px;
          object-fit: contain;
        }

        .ad-path-label {
          color: var(--ad-muted);
          font-weight: 800;
          font-size: 12px;
          margin-bottom: 8px;
        }

        .ad-path-value {
          color: var(--ad-text);
          font-size: 17px;
          font-weight: 800;
          margin-bottom: 8px;
        }

        .ad-path-caption {
          color: var(--ad-muted);
          font-size: 12px;
          line-height: 1.45;
        }

        .ad-analysis-grid,
        .ad-recommendation-grid {
          display: grid;
          gap: 20px;
          margin-top: 22px;
        }

        .ad-analysis-grid {
          grid-template-columns: minmax(0, 2fr) minmax(320px, 1fr);
        }

        .ad-recommendation-grid {
          grid-template-columns: minmax(0, 2fr) minmax(360px, 1fr);
        }

        .ad-stack {
          display: grid;
          gap: 18px;
        }

        .ad-panel h3 {
          font-size: 21px;
          font-weight: 800;
          margin: 0 0 16px;
          color: var(--ad-text);
        }

        .ad-panel p {
          font-size: 18px;
          line-height: 1.65;
          margin: 0;
        }

        .ad-factor {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 16px;
          margin: 14px 0;
        }

        .ad-factor-icon {
          width: 22px;
          height: 22px;
          display: grid;
          place-items: center;
        }

        .ad-factor-icon img {
          display: block;
          width: 22px;
          height: 22px;
          object-fit: contain;
        }

        .ad-review-actions {
          display: grid;
          gap: 10px;
          margin-top: 18px;
        }

        .ad-action-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
        }

        .ad-doc-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 18px;
          margin: 18px 0 30px;
        }

        .ad-doc-card {
          border: 1px solid var(--ad-border);
          border-radius: 8px;
          padding: 18px;
          display: grid;
          grid-template-columns: 48px 1fr;
          gap: 16px;
          align-items: center;
        }

        .ad-doc-icon {
          width: 38px;
          height: 38px;
          border-radius: 8px;
          display: grid;
          place-items: center;
        }

        .ad-doc-icon img {
          display: block;
          width: 38px;
          height: 38px;
          object-fit: contain;
        }

        .ad-doc-title {
          font-weight: 800;
          font-size: 17px;
        }

        .ad-doc-subtitle {
          color: var(--ad-muted);
          margin-top: 3px;
        }

        .ad-step {
          display: grid;
          grid-template-columns: 42px 1fr;
          gap: 16px;
          align-items: center;
          margin: 17px 0;
          font-size: 18px;
        }

        .ad-step-number {
          width: 30px;
          height: 30px;
          border-radius: 999px;
          background: var(--ad-blue);
          color: #fff;
          display: grid;
          place-items: center;
          font-size: 14px;
          font-weight: 900;
        }

        .ad-step:nth-child(3) .ad-step-number {
          background: var(--ad-red);
        }

        .ad-step:nth-child(n+4) .ad-step-number {
          background: #6f7785;
        }

        .ad-agent-header {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 24px;
          font-weight: 800;
          margin-bottom: 18px;
        }

        .ad-agent-icon {
          display: block;
          width: 30px;
          height: 30px;
          object-fit: contain;
        }

        .ad-pill-icon {
          display: block;
          width: 14px;
          height: 14px;
          object-fit: contain;
        }

        .ad-risk-badge-img,
        .ad-identity-badge-img,
        .ad-status-badge-img {
          display: inline-block;
          vertical-align: middle;
          object-fit: contain;
          flex: 0 0 auto;
        }

        .ad-risk-badge-img {
          width: auto;
          height: 34px;
        }

        .ad-identity-badge-img {
          width: auto;
          height: 24px;
          margin-left: 8px;
        }

        .ad-status-badge-img {
          width: auto;
          height: 23px;
        }

        .ad-agent-body {
          background: var(--ad-soft);
          border: 1px solid var(--ad-border);
          border-radius: 10px;
          min-height: 620px;
          padding: 18px;
        }

        .ad-chat-bubble {
          max-width: 82%;
          border: 1px solid var(--ad-border);
          border-radius: 8px;
          background: #fff;
          padding: 16px;
          margin-bottom: 16px;
          line-height: 1.55;
        }

        .ad-chat-user {
          margin-left: auto;
          background: var(--ad-blue-soft);
          border-color: var(--ad-blue-soft);
        }

        .ad-chat-name {
          color: var(--ad-blue);
          font-weight: 800;
          margin-bottom: 8px;
        }

        .ad-agent-input {
          border: 1px solid var(--ad-border);
          border-radius: 8px;
          padding: 10px 10px 10px 18px;
          display: grid;
          grid-template-columns: 1fr 70px;
          gap: 10px;
          margin-top: 24px;
          color: #a0a7b3;
        }

        html, body, [class*="css"], *,
        button, input, select, textarea,
        .stMarkdown, .stMarkdown *,
        .js-plotly-plot, .js-plotly-plot * {
          font-weight: 500 !important;
        }

        .ad-page-title,
        .ad-risk-title,
        .ad-card-title,
        .ad-section-title,
        .ad-risk-heading h2,
        .ad-panel h3,
        .ad-agent-header,
        .ad-overview-title,
        .ad-row-title,
        .ad-identity-value,
        .ad-detected-value,
        .ad-meta-value,
        .ad-path-value,
        .ad-doc-title {
          font-weight: 700 !important;
        }

        .ad-page-caption,
        .ad-risk-subtitle,
        .ad-meta-label,
        .ad-row-kicker,
        .ad-col-label,
        .ad-path-label,
        .ad-path-caption,
        .ad-doc-subtitle {
          font-weight: 500 !important;
        }

        .ad-pill,
        .ad-pill *,
        .ad-count-pill,
        .ad-count-pill * {
          font-weight: 600 !important;
        }

        @media (max-width: 1100px) {
          .ad-summary-grid,
          .ad-analysis-grid,
          .ad-recommendation-grid,
          .ad-access-canvas {
            grid-template-columns: 1fr;
          }

          .ad-priority-row {
            grid-template-columns: 28px 1fr;
          }

          .ad-path-step::after {
            display: none;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if page == "overview":
        st.markdown(
            """
            <style>
            .block-container {
              max-width: 1380px;
              padding: 2rem 1.95rem 3rem;
              margin-left: auto;
              margin-right: auto;
            }

            .ad-page-title {
              font-size: 34px;
              line-height: 1.08;
              margin: 0 0 28px;
            }

            div[data-testid="stHorizontalBlock"] {
              gap: 1.65rem;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] {
              border-radius: 16px;
              padding: 18px 20px;
              min-height: 242px;
            }

            .ad-overview-title {
              font-size: 25px;
              font-weight: 800;
              line-height: 1.1;
              margin: 0 0 10px;
              color: var(--ad-text);
            }

            .ad-overview-summary-card {
              height: 244px;
              overflow: visible;
              background: #FFFFFF;
              border: 1px solid #E2E8F0;
              border-radius: 16px;
              box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
              padding: 22px 24px;
              box-sizing: border-box;
            }

            .ad-overview-total-grid {
              display: grid;
              grid-template-columns: 176px 1fr;
              gap: 18px;
              align-items: center;
              margin-top: 2px;
            }

            .ad-overview-donut {
              width: 154px;
              height: 154px;
              border-radius: 50%;
              background: conic-gradient(
                #128bf4 0 var(--open-stop),
                #ff7b73 var(--open-stop) var(--review-stop),
                #d8dce2 var(--review-stop) 100%
              );
              display: grid;
              place-items: center;
              margin: 4px auto 0;
            }

            .ad-overview-donut-inner {
              width: 100px;
              height: 100px;
              border-radius: 50%;
              background: #fff;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              color: #aeb5bf;
              font-size: 20px;
              font-weight: 800;
              line-height: 1.05;
            }

            .ad-overview-donut-inner strong {
              color: var(--ad-text);
              font-size: 29px;
              margin-top: 8px;
            }

            .ad-overview-total-legend {
              padding-top: 8px;
            }

            .ad-overview-total-legend .ad-legend-row {
              font-size: 15px;
              padding: 6px 0;
              gap: 10px;
            }

            .ad-overview-total-legend .ad-dot {
              width: 10px;
              height: 10px;
              margin-right: 10px;
            }

            .ad-overview-issues-chart {
              height: 132px;
              display: grid;
              grid-template-columns: repeat(4, 1fr);
              gap: 28px;
              align-items: end;
              padding: 0 24px;
              margin-top: 6px;
              border-bottom: 1px solid var(--ad-border);
            }

            .ad-overview-issue-bar-wrap {
              height: 118px;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: flex-end;
              gap: 7px;
            }

            .ad-overview-issue-value {
              color: var(--ad-text);
              font-weight: 800;
              font-size: 16px;
              line-height: 1;
            }

            .ad-overview-issue-bar {
              width: 34px;
              border-radius: 8px 8px 6px 6px;
            }

            .ad-overview-issue-labels {
              display: grid;
              grid-template-columns: repeat(4, 1fr);
              gap: 28px;
              padding: 9px 24px 0;
              text-align: center;
              color: var(--ad-text);
              font-size: 15px;
              font-weight: 800;
            }

            .ad-overview-top-drifts {
              height: 244px;
              padding: 22px 24px 20px;
              border-radius: 16px;
              display: flex;
              flex-direction: column;
            }

            .ad-overview-top-drifts .ad-card-title {
              font-size: 25px;
              margin-bottom: 4px;
            }

            .ad-overview-top-drifts .ad-top-drift-row {
              font-size: 14px;
              padding: 10px 0;
              gap: 12px;
            }

            .ad-overview-top-drifts .ad-top-drift-row:first-of-type,
            .ad-overview-top-drifts .ad-top-drift-row:first-of-type span,
            .ad-overview-top-drifts .ad-top-drift-primary,
            .ad-overview-top-drifts .ad-top-drift-primary span {
              color: #EC4141;
            }

            .ad-overview-priority {
              border-radius: 16px;
              padding: 24px 28px 28px;
              margin-top: 40px;
            }

            .ad-overview-priority .ad-section-header {
              margin-bottom: 16px;
            }

            .ad-overview-priority .ad-section-title {
              font-size: 26px;
              line-height: 1.1;
            }

            .ad-overview-priority .ad-count-pill {
              padding: 7px 16px;
              font-size: 12px;
            }

            .ad-overview-priority .ad-priority-row {
              grid-template-columns: 28px minmax(310px, 1.05fr) minmax(280px, 1fr) minmax(230px, 0.82fr) 136px;
              gap: 14px;
              border-radius: 14px;
              padding: 20px 22px;
              margin-top: 18px;
              min-height: 92px;
            }

            .ad-overview-priority .ad-checkbox {
              width: 20px;
              height: 20px;
              border-radius: 6px;
            }

            .ad-overview-priority .ad-row-kicker {
              font-size: 13px;
            }

            .ad-overview-priority .ad-row-title,
            .ad-overview-priority .ad-identity-value,
            .ad-overview-priority .ad-detected-value {
              font-size: 17px;
              line-height: 1.2;
            }

            .ad-overview-priority .ad-row-subline {
              gap: 14px;
              margin-top: 12px;
              flex-wrap: nowrap;
            }

            .ad-overview-priority .ad-risk-badge-slot {
              width: 104px;
              flex: 0 0 104px;
              display: inline-flex;
              align-items: center;
            }

            .ad-overview-priority .ad-risk-badge-slot .ad-risk-badge-img {
              height: 34px;
              width: 96px;
              max-width: 96px;
            }

            .ad-overview-priority .ad-col-label {
              font-size: 14px;
              margin-bottom: 12px;
            }

            .ad-overview-priority .ad-pill {
              font-size: 11px;
              padding: 6px 11px;
              gap: 5px;
            }

            .ad-overview-priority .ad-owner-pill {
              padding: 6px 10px;
            }

            .ad-overview-priority .ad-owner-pill::before {
              width: 16px;
              height: 16px;
            }

            .ad-overview-priority .ad-button {
              height: 42px;
              min-width: 124px;
              padding: 0 16px;
              border-radius: 10px;
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 14px;
              justify-self: end;
            }

            .ad-overview-priority .ad-identity-type-pill {
              margin-left: 6px !important;
            }

            @media (max-width: 1100px) {
              .ad-overview-priority .ad-priority-row {
                grid-template-columns: 28px 1fr;
              }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    if page == "risk":
        st.markdown(
            """
            <style>
            .stApp {
              background: #ffffff;
            }

            .block-container {
              max-width: 1380px;
              padding: 0.5rem 1.95rem 3rem;
              margin-left: auto;
              margin-right: auto;
            }

            .ad-risk-title {
              font-size: 32px;
              line-height: 1.08;
              margin: 0 0 10px;
            }

            .ad-page-caption {
              font-size: 15px;
              margin: 0 0 14px;
            }

            .ad-risk-header {
              margin: 0 0 12px;
              padding: 20px 22px;
              border-radius: 10px;
            }

            .ad-risk-heading {
              gap: 14px;
              margin-bottom: 8px;
            }

            .ad-risk-heading h2 {
              font-size: 27px;
              line-height: 1.12;
            }

            .ad-risk-subtitle {
              font-size: 15px;
              margin: 5px 0;
            }

            .ad-risk-meta {
              margin-top: 12px;
              gap: 18px;
            }

            .ad-risk-meta .ad-meta-label {
              font-size: 12px;
            }

            .ad-risk-meta .ad-meta-value {
              font-size: 15px;
            }

            .stTabs [data-baseweb="tab-list"] {
              gap: 30px;
            }

            .stTabs [data-baseweb="tab"] {
              padding: 11px 0 10px;
              font-size: 18px;
            }

            .ad-access-card {
              margin-top: 8px;
              padding: 18px 22px;
              border-radius: 10px;
            }

            .ad-access-card .ad-card-title {
              font-size: 20px;
              margin-bottom: 10px;
            }

            .ad-access-canvas {
              padding: 16px 14px;
              margin-top: 10px;
              gap: 18px;
            }

            .ad-path-step {
              min-height: 0;
              padding: 10px 12px;
            }

            .ad-icon-box {
              width: 24px;
              height: 24px;
              margin-bottom: 5px;
              font-size: 12px;
            }

            .ad-icon-box img {
              width: 18px;
              height: 18px;
            }

            .ad-path-label {
              font-size: 10px;
              margin-bottom: 4px;
            }

            .ad-path-value {
              font-size: 13px;
              line-height: 1.15;
              margin-bottom: 4px;
            }

            .ad-path-caption {
              font-size: 10px;
              line-height: 1.22;
            }

            .ad-path-step > div[style] {
              margin-top: 6px !important;
            }

            .ad-path-step .ad-pill {
              font-size: 10px;
              padding: 5px 8px;
            }

            .ad-analysis-grid,
            .ad-recommendation-grid {
              margin-top: 14px;
            }

            div[data-testid="stHorizontalBlock"] {
              gap: 1.35rem;
            }

            .ad-panel {
              border-radius: 10px;
              padding: 22px;
            }

            .ad-panel h3 {
              font-size: 20px;
              margin-bottom: 14px;
            }

            .ad-panel p {
              font-size: 16px;
              line-height: 1.55;
            }

            .ad-factor {
              font-size: 15px;
              margin: 12px 0;
            }

            .ad-review-actions {
              margin-top: 16px;
            }

            .ad-risk-header-v2 {
              min-height: 184px;
            }

            .ad-risk-v2-status-label {
              color: var(--ad-muted);
              font-size: 12px;
              font-weight: 600 !important;
              margin: 4px 0 8px;
              text-align: left;
            }

            div[data-testid="stSelectbox"] label {
              display: none;
            }

            div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
              min-height: 36px;
              border-radius: 999px;
              border-color: #d7dde5;
              background: #ffffff;
              box-shadow: none;
            }

            div[data-testid="stSelectbox"] [data-baseweb="select"] span {
              font-size: 13px;
              font-weight: 700 !important;
              color: var(--ad-text);
            }

            .ad-access-card-v2 .ad-access-canvas {
              padding: 22px 14px;
              gap: 14px;
              align-items: stretch;
            }

            .ad-access-card-v2 .ad-path-step {
              min-height: 122px;
              height: 122px;
              padding: 13px 12px;
              display: flex;
              flex-direction: column;
              justify-content: flex-start;
              box-sizing: border-box;
            }

            .ad-access-card-v2 .ad-path-main-row {
              display: flex;
              align-items: center;
              gap: 10px;
              min-height: 34px;
              margin-bottom: 8px;
            }

            .ad-access-card-v2 .ad-icon-box {
              width: 30px;
              height: 30px;
              min-width: 30px;
              margin-bottom: 0;
            }

            .ad-access-card-v2 .ad-icon-box img {
              width: 21px;
              height: 21px;
            }

            .ad-access-card-v2 .ad-path-value {
              min-height: 0;
              display: block;
              font-size: 15px;
              line-height: 1.25;
              margin-bottom: 0;
            }

            .ad-access-card-v2 .ad-path-caption {
              min-height: 30px;
              font-size: 12px;
              line-height: 1.35;
            }

            .ad-access-card-v2 .ad-path-pill-slot {
              margin-top: auto;
              min-height: 22px;
              display: flex;
              align-items: flex-end;
            }

            .ad-access-card-v2 .ad-path-step .ad-pill {
              font-size: 11px;
              padding: 5px 9px;
            }

            .ad-panel-v2-equal {
              min-height: 196px;
              height: 100%;
              box-sizing: border-box;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
