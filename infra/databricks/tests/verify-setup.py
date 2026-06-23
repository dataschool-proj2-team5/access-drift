# Databricks notebook source
# 인프라 셋업 검증 노트북
# Databricks 워크스페이스에서 실행

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1. 현재 사용자 및 카탈로그 확인

# COMMAND ----------
# MAGIC %sql
# MAGIC SELECT current_user();
# MAGIC
# MAGIC SHOW CATALOGS LIKE 'access_drift';
# MAGIC SHOW SCHEMAS IN access_drift;

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2. 권한 확인

# COMMAND ----------
# MAGIC %sql
# MAGIC SHOW GRANTS ON CATALOG access_drift;
# MAGIC SHOW GRANTS ON SCHEMA access_drift.landing;
# MAGIC SHOW GRANTS ON SCHEMA access_drift.bronze;
# MAGIC SHOW GRANTS ON SCHEMA access_drift.silver;
# MAGIC SHOW GRANTS ON SCHEMA access_drift.intermediate;
# MAGIC SHOW GRANTS ON SCHEMA access_drift.gold;

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3. External Location 확인

# COMMAND ----------
# MAGIC %sql
# MAGIC DESCRIBE EXTERNAL LOCATION access_drift_landing_ext;
# MAGIC DESCRIBE EXTERNAL LOCATION access_drift_bronze_ext;
# MAGIC DESCRIBE EXTERNAL LOCATION access_drift_silver_ext;
# MAGIC DESCRIBE EXTERNAL LOCATION access_drift_intermediate_ext;
# MAGIC DESCRIBE EXTERNAL LOCATION access_drift_gold_ext;
