-- Databricks SQL ops dashboard query 01
-- Purpose: minimal pipeline row counts across Bronze/Silver/Intermediate/Gold/Eval/Context/App.
-- Target catalog: access_drift_dev

SELECT 'bronze' AS layer, 'bronze_access_edges_seed' AS table_name, COUNT(*) AS row_count
FROM access_drift_dev.bronze.bronze_access_edges_seed
UNION ALL
SELECT 'bronze', 'bronze_assets_seed', COUNT(*)
FROM access_drift_dev.bronze.bronze_assets_seed
UNION ALL
SELECT 'bronze', 'bronze_azure_application_owners', COUNT(*)
FROM access_drift_dev.bronze.bronze_azure_application_owners
UNION ALL
SELECT 'bronze', 'bronze_azure_applications', COUNT(*)
FROM access_drift_dev.bronze.bronze_azure_applications
UNION ALL
SELECT 'bronze', 'bronze_azure_password_credentials', COUNT(*)
FROM access_drift_dev.bronze.bronze_azure_password_credentials
UNION ALL
SELECT 'bronze', 'bronze_github_access_edges', COUNT(*)
FROM access_drift_dev.bronze.bronze_github_access_edges
UNION ALL
SELECT 'bronze', 'bronze_github_apps', COUNT(*)
FROM access_drift_dev.bronze.bronze_github_apps
UNION ALL
SELECT 'bronze', 'bronze_github_credentials', COUNT(*)
FROM access_drift_dev.bronze.bronze_github_credentials
UNION ALL
SELECT 'bronze', 'bronze_github_repos', COUNT(*)
FROM access_drift_dev.bronze.bronze_github_repos
UNION ALL
SELECT 'bronze', 'bronze_google_workspace_access_edges', COUNT(*)
FROM access_drift_dev.bronze.bronze_google_workspace_access_edges
UNION ALL
SELECT 'bronze', 'bronze_google_workspace_assets', COUNT(*)
FROM access_drift_dev.bronze.bronze_google_workspace_assets
UNION ALL
SELECT 'bronze', 'bronze_google_workspace_users', COUNT(*)
FROM access_drift_dev.bronze.bronze_google_workspace_users
UNION ALL
SELECT 'bronze', 'bronze_identity_lifecycle_seed', COUNT(*)
FROM access_drift_dev.bronze.bronze_identity_lifecycle_seed
UNION ALL
SELECT 'bronze', 'bronze_slack_access_edges', COUNT(*)
FROM access_drift_dev.bronze.bronze_slack_access_edges
UNION ALL
SELECT 'bronze', 'bronze_slack_channels', COUNT(*)
FROM access_drift_dev.bronze.bronze_slack_channels
UNION ALL
SELECT 'bronze', 'bronze_slack_users', COUNT(*)
FROM access_drift_dev.bronze.bronze_slack_users
UNION ALL
SELECT 'silver', 'silver_assets', COUNT(*)
FROM access_drift_dev.silver.silver_assets
UNION ALL
SELECT 'silver', 'silver_credentials', COUNT(*)
FROM access_drift_dev.silver.silver_credentials
UNION ALL
SELECT 'silver', 'silver_edges', COUNT(*)
FROM access_drift_dev.silver.silver_edges
UNION ALL
SELECT 'silver', 'silver_principals', COUNT(*)
FROM access_drift_dev.silver.silver_principals
UNION ALL
SELECT 'intermediate', 'nhi_residual_access_findings', COUNT(*)
FROM access_drift_dev.intermediate.nhi_residual_access_findings
UNION ALL
SELECT 'gold', 'gold_core', COUNT(*)
FROM access_drift_dev.gold.gold_core
UNION ALL
SELECT 'eval', 'ground_truth_case', COUNT(*)
FROM access_drift_dev.eval.ground_truth_case
UNION ALL
SELECT 'context', 'asset_context', COUNT(*)
FROM access_drift_dev.context.asset_context
UNION ALL
SELECT 'context', 'assignment_routing', COUNT(*)
FROM access_drift_dev.context.assignment_routing
UNION ALL
SELECT 'app', 'risk_action_event', COUNT(*)
FROM access_drift_dev.app.risk_action_event
UNION ALL
SELECT 'app', 'risk_action_state', COUNT(*)
FROM access_drift_dev.app.risk_action_state
ORDER BY layer, table_name;
