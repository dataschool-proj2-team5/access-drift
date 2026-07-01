# Dashboard UI Scaffold Spec

This document records the current page and component skeleton only. It is not a final UI design.

## Overview

```text
Overview
├─ Page Title
├─ Top Summary Cards
│  ├─ Actions: donut chart summary card
│  ├─ Issues: vertical bar chart summary card
│  └─ Top Drifts: ranked list card
└─ Priority Review
   └─ case row list card
```

## Risk Card

```text
Risk Card
├─ Page Title
├─ Risk Header Card: identity/risk summary card
├─ Tab Navigation
│  ├─ 위험 분석
│  ├─ 권장 조치
│  └─ 티켓 발급
└─ Tab Content
   ├─ 위험 분석
   │  ├─ Access Path: horizontal flow/path diagram
   │  ├─ Risk Summary: text summary card
   │  ├─ Risk Factors: checklist card
   │  └─ Review Info: status/action card
   ├─ 권장 조치
   │  ├─ AI RAG Recommendation: recommendation panel
   │  └─ AI Agent: chat panel
   └─ 티켓 발급
      └─ ticket creation form placeholder
```

## Component Mapping

| Area | Current component |
| --- | --- |
| Summary cards | `components/cards.py::render_summary_cards` |
| Donut chart | `components/charts.py::render_risk_level_donut` |
| Issue bar chart | `components/charts.py::render_issue_bar_chart` |
| Priority review list | `components/cards.py::render_priority_review_list` |
| Risk header | `components/cards.py::render_risk_header_card` |
| Access path | `components/charts.py::render_access_path` |
| Recommendation panel | `components/cards.py::render_recommendation_panel` |
| AI action placeholder | `components/cards.py::render_ai_agent_placeholder` |
| Ticket placeholder | `components/cards.py::render_ticket_form_placeholder` |

## TODO

- Replace placeholder charts with product-approved chart choices.
- Replace placeholder risk factors with confirmed business rules.
- Replace disabled AI and ticket actions with real integrations.
- Map final Gold Layer fields in `src/data_loader.py`.
