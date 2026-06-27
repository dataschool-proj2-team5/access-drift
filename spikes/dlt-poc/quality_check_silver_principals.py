import dlt
from pyspark.sql.functions import lit, col

@dlt.table(
    name="dlt_silver_principals_quality_check_with_invalid",
    comment="Spike #16 - DLT expectation test with distributed invalid rows"
)
@dlt.expect("valid_principal_id", "principal_id IS NOT NULL")
@dlt.expect("valid_source_principal_id", "source_principal_id IS NOT NULL")
@dlt.expect("valid_principal_kind", "principal_kind IN ('HI', 'NHI')")
@dlt.expect("valid_principal_type", "principal_type IN ('app_registration', 'user')")
@dlt.expect("valid_status", "status IN ('active', 'inactive', 'terminated')")
def dlt_silver_principals_quality_check_with_invalid():
    base_df = spark.read.table("access_drift.silver.silver_principals")

    sample_df = base_df.limit(1)

    invalid_principal_id_df = sample_df.select(
        lit(None).cast("string").alias("principal_id"),
        col("source_system"),
        col("source_principal_id"),
        col("principal_kind"),
        col("principal_type"),
        col("display_name"),
        col("email"),
        col("status"),
        col("termination_date"),
        col("observed_at")
    )

    invalid_source_principal_id_df = sample_df.select(
        col("principal_id"),
        col("source_system"),
        lit(None).cast("string").alias("source_principal_id"),
        col("principal_kind"),
        col("principal_type"),
        col("display_name"),
        col("email"),
        col("status"),
        col("termination_date"),
        col("observed_at")
    )

    invalid_principal_kind_df = sample_df.select(
        col("principal_id"),
        col("source_system"),
        col("source_principal_id"),
        lit("INVALID_KIND").alias("principal_kind"),
        col("principal_type"),
        col("display_name"),
        col("email"),
        col("status"),
        col("termination_date"),
        col("observed_at")
    )

    invalid_principal_type_df = sample_df.select(
        col("principal_id"),
        col("source_system"),
        col("source_principal_id"),
        col("principal_kind"),
        lit("invalid_type").alias("principal_type"),
        col("display_name"),
        col("email"),
        col("status"),
        col("termination_date"),
        col("observed_at")
    )

    invalid_status_df = sample_df.select(
        col("principal_id"),
        col("source_system"),
        col("source_principal_id"),
        col("principal_kind"),
        col("principal_type"),
        col("display_name"),
        col("email"),
        lit("invalid_status").alias("status"),
        col("termination_date"),
        col("observed_at")
    )

    invalid_df = (
        invalid_principal_id_df
        .unionByName(invalid_source_principal_id_df)
        .unionByName(invalid_principal_kind_df)
        .unionByName(invalid_principal_type_df)
        .unionByName(invalid_status_df)
    )

    return base_df.unionByName(invalid_df)

@dlt.table(
    name="dlt_silver_principals_gate_drop_test",
    comment="Spike #16 - DLT expect_or_drop gate test with distributed invalid rows"
)
@dlt.expect_or_drop("valid_principal_id", "principal_id IS NOT NULL")
@dlt.expect_or_drop("valid_source_principal_id", "source_principal_id IS NOT NULL")
@dlt.expect_or_drop("valid_principal_kind", "principal_kind IN ('HI', 'NHI')")
@dlt.expect_or_drop("valid_principal_type", "principal_type IN ('app_registration', 'user')")
@dlt.expect_or_drop("valid_status", "status IN ('active', 'inactive', 'terminated')")
def dlt_silver_principals_gate_drop_test():
    base_df = spark.read.table("access_drift.silver.silver_principals")

    sample_df = base_df.limit(1)

    invalid_principal_id_df = sample_df.select(
        lit(None).cast("string").alias("principal_id"),
        col("source_system"),
        col("source_principal_id"),
        col("principal_kind"),
        col("principal_type"),
        col("display_name"),
        col("email"),
        col("status"),
        col("termination_date"),
        col("observed_at")
    )

    invalid_source_principal_id_df = sample_df.select(
        col("principal_id"),
        col("source_system"),
        lit(None).cast("string").alias("source_principal_id"),
        col("principal_kind"),
        col("principal_type"),
        col("display_name"),
        col("email"),
        col("status"),
        col("termination_date"),
        col("observed_at")
    )

    invalid_principal_kind_df = sample_df.select(
        col("principal_id"),
        col("source_system"),
        col("source_principal_id"),
        lit("INVALID_KIND").alias("principal_kind"),
        col("principal_type"),
        col("display_name"),
        col("email"),
        col("status"),
        col("termination_date"),
        col("observed_at")
    )

    invalid_principal_type_df = sample_df.select(
        col("principal_id"),
        col("source_system"),
        col("source_principal_id"),
        col("principal_kind"),
        lit("invalid_type").alias("principal_type"),
        col("display_name"),
        col("email"),
        col("status"),
        col("termination_date"),
        col("observed_at")
    )

    invalid_status_df = sample_df.select(
        col("principal_id"),
        col("source_system"),
        col("source_principal_id"),
        col("principal_kind"),
        col("principal_type"),
        col("display_name"),
        col("email"),
        lit("invalid_status").alias("status"),
        col("termination_date"),
        col("observed_at")
    )

    invalid_df = (
        invalid_principal_id_df
        .unionByName(invalid_source_principal_id_df)
        .unionByName(invalid_principal_kind_df)
        .unionByName(invalid_principal_type_df)
        .unionByName(invalid_status_df)
    )

    return base_df.unionByName(invalid_df)
