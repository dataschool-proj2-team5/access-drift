# Dashboard Data Contract

This dashboard currently looks for:

```text
apps/dashboard/data/sample_access_drift.csv
```

If the CSV file is missing, the app generates mock rows from `src/mock_data.py` and shows a `Using mock data` notice at the top of each page.

## Expected Internal Columns

The final CSV, database, or Gold Layer source contract is not fixed yet. Until then, dashboard pages depend on these internal scaffold columns:

| Column | Notes |
| --- | --- |
| `case_id` | Internal risk case identifier. |
| `risk_title` | Risk card title. |
| `risk_level` | Display severity such as Critical, High, Medium, or Low. |
| `drift_type` | Access drift category. |
| `identity_name` | Identity, principal, or account associated with the risk. |
| `identity_type` | Identity category. |
| `object_name` | Credential or access object name. |
| `object_type` | Access object category. |
| `credential_type` | Credential type. |
| `credential_status` | Credential lifecycle status. |
| `owner_status` | Owner lifecycle status. |
| `owner_name` | Owner display name. |
| `owner_team` | Owner team display name. |
| `related_person_status` | Related human identity status. |
| `linked_owner_label` | Display label for linked owner evidence. |
| `asset_name` | Asset display name. |
| `asset_type` | Asset category. |
| `asset_sensitivity` | Asset sensitivity label. |
| `data_scope` | Data scope label shown in Risk Card. |
| `data_categories` | Sensitive data category text shown in Risk Card. |
| `permission_level` | Permission or role level. |
| `last_accessed_at` | Last known access timestamp. |
| `detected_at` | Finding detection timestamp. |
| `created_at` | Access object or case creation timestamp. |
| `rotation_status` | Credential rotation status. |
| `risk_score` | Placeholder numeric risk score. |
| `review_status` | Review workflow status. |
| `reviewer` | Assigned reviewer. |
| `action_owner` | Person or team expected to take action. |
| `recommended_action` | Placeholder recommendation text. |
| `risk_summary` | Risk summary text shown in the analysis tab. |
| `risk_factors` | Risk factor checklist items. |
| `action_plan` | Recommended action plan steps. |
| `ai_agent_messages` | Mock AI Agent chat messages. |
| `overview_title` | Short title used in the Overview priority list. |
| `ai_summary` | Placeholder AI/RAG summary text. |
| `reference_docs` | Reference policy, runbook, or evidence links. |

## Future Source Mapping

When actual CSV, DB, or Gold Layer column names are finalized, update `src/data_loader.py` so source-specific names map into this internal schema. Keep Streamlit pages and components reading the internal names to avoid UI churn.
