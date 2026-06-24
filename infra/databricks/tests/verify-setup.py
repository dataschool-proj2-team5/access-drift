# Databricks notebook source
# 인프라 셋업 검증 노트북
# Databricks 워크스페이스에서 실행

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1. 현재 사용자 및 카탈로그 확인

# COMMAND ----------
# MAGIC %sql
# MAGIC SELECT
# MAGIC   current_user() AS current_user,
# MAGIC   current_catalog() AS current_catalog;
# MAGIC
# MAGIC SHOW CATALOGS LIKE 'access_drift';
# MAGIC SHOW SCHEMAS IN access_drift;

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2. 권한 확인

# COMMAND ----------
# MAGIC %sql
# MAGIC SHOW GRANTS ON CATALOG access_drift;

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3. External Location 확인

# COMMAND ----------
# MAGIC %sql
# MAGIC DESCRIBE EXTERNAL LOCATION access_drift_lakehouse_ext;
