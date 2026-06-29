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
# MAGIC
# MAGIC SHOW CATALOGS LIKE 'access_drift_dev';
# MAGIC SHOW SCHEMAS IN access_drift_dev;

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2. 권한 확인

# COMMAND ----------
# MAGIC %sql
# MAGIC SHOW GRANTS ON CATALOG access_drift;
# MAGIC SHOW GRANTS ON CATALOG access_drift_dev;

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2-1. dev 스키마 권한 확인

# COMMAND ----------
# MAGIC %sql
# MAGIC SHOW GRANTS ON SCHEMA access_drift_dev.bronze;
# MAGIC SHOW GRANTS ON SCHEMA access_drift_dev.silver;
# MAGIC SHOW GRANTS ON SCHEMA access_drift_dev.intermediate;
# MAGIC SHOW GRANTS ON SCHEMA access_drift_dev.gold;
# MAGIC SHOW GRANTS ON SCHEMA access_drift_dev.eval;

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3. External Location 확인

# COMMAND ----------
# MAGIC %sql
# MAGIC DESCRIBE EXTERNAL LOCATION access_drift_lakehouse_ext;
