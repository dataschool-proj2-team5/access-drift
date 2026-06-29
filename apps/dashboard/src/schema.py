from __future__ import annotations

EXPECTED_COLUMNS = [
    "case_id",
    "risk_title",
    "risk_level",
    "drift_type",
    "identity_name",
    "identity_type",
    "object_name",
    "object_type",
    "credential_type",
    "credential_status",
    "owner_status",
    "owner_name",
    "related_person_status",
    "asset_name",
    "asset_type",
    "asset_sensitivity",
    "permission_level",
    "last_accessed_at",
    "detected_at",
    "created_at",
    "rotation_status",
    "risk_score",
    "review_status",
    "reviewer",
    "action_owner",
    "recommended_action",
    "ai_summary",
    "reference_docs",
]

DATE_COLUMNS = ["last_accessed_at", "detected_at", "created_at"]

RISK_LEVEL_ORDER = ["Critical", "High", "Medium", "Low"]

SCHEMA_DESCRIPTIONS = {
    "case_id": "Internal risk case identifier used by the dashboard.",
    "risk_title": "Human-readable risk card title.",
    "risk_level": "Display severity such as Critical, High, Medium, or Low.",
    "drift_type": "Access drift category.",
    "identity_name": "Identity, principal, or account associated with the risk.",
    "identity_type": "Identity category such as User, App Registration, or Service Principal.",
    "object_name": "Credential or access object name.",
    "object_type": "Access object category.",
    "credential_type": "Credential type involved in the finding.",
    "credential_status": "Credential lifecycle status.",
    "owner_status": "Owner lifecycle status.",
    "owner_name": "Owner display name.",
    "related_person_status": "Related human identity status.",
    "asset_name": "Asset display name.",
    "asset_type": "Asset category.",
    "asset_sensitivity": "Asset sensitivity label used for display only in this scaffold.",
    "permission_level": "Permission or role level associated with the access path.",
    "last_accessed_at": "Last known access timestamp.",
    "detected_at": "Finding detection timestamp.",
    "created_at": "Access object or case creation timestamp.",
    "rotation_status": "Credential rotation status.",
    "risk_score": "Placeholder numeric score. Final scoring logic is not implemented.",
    "review_status": "Review workflow status.",
    "reviewer": "Assigned reviewer.",
    "action_owner": "Person or team expected to take action.",
    "recommended_action": "Placeholder recommendation text.",
    "ai_summary": "Placeholder AI/RAG summary text.",
    "reference_docs": "Reference policy, runbook, or evidence links.",
}


def get_expected_columns() -> list[str]:
    return EXPECTED_COLUMNS.copy()


def get_missing_columns(columns: list[str]) -> list[str]:
    return [column for column in EXPECTED_COLUMNS if column not in columns]
