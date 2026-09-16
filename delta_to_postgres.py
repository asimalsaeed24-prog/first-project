"""Load one existing Delta table into one existing PostgreSQL table."""

import math
import os
import sys
from pyspark.sql import SparkSession

PG_DRIVER = "org.postgresql.Driver"


def verify_schema(source_df, target_df) -> None:
    """Fail if source and target columns/types are different."""
    source = [(f.name, f.dataType.simpleString()) for f in source_df.schema.fields]
    target = [(f.name, f.dataType.simpleString()) for f in target_df.schema.fields]

    if source != target:
        raise ValueError(
            "Source and target schemas do not match.\n"
            f"Source: {source}\n"
            f"Target: {target}"
        )


def delta_to_postgres(
    spark: SparkSession,
    source: str,
    target: str,
    jdbc_url: str,
    user: str,
    password: str,
    pg_schema: str = "public",
    pagination: bool = True,
    rows_per_page: int = 100_000,
    max_parallel_pages: int = 8,
    batch_size: int = 10_000,
) -> None:
    """Insert one Delta table into an existing PostgreSQL table."""

    source_df = spark.table(source)
    target_table = f'"{pg_schema}"."{target}"'

    target_df = (
        spark.read.format("jdbc")
        .option("url", jdbc_url)
        .option("driver", PG_DRIVER)
        .option("dbtable", target_table)
        .option("user", user)
        .option("password", password)
        .load()
        .limit(0)
    )

    verify_schema(source_df, target_df)

    pages = 1
    if pagination:
        rows = source_df.count()
        pages = max(1, min(max_parallel_pages, math.ceil(rows / rows_per_page)))

    (
        source_df.repartition(pages)
        .write.format("jdbc")
        .option("url", jdbc_url)
        .option("driver", PG_DRIVER)
        .option("dbtable", target_table)
        .option("user", user)
        .option("password", password)
        .option("batchsize", batch_size)
        .option("reWriteBatchedInserts", "true")
        .option("stringtype", "unspecified")
        .mode("append")
        .save()
    )


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise SystemExit(
            "usage: delta_to_postgres_simple_insert.py "
            "<source> <target> <s3_access_key> <s3_access_secret> <s3_endpoint>"
        )

    source, target, s3_access_key, s3_access_secret, s3_endpoint = sys.argv[1:]

    builder = SparkSession.builder.appName("delta_to_postgres").enableHiveSupport()
    if "HIVE_METASTORE_URI" in os.environ:
        builder = builder.config("hive.metastore.uris", os.environ["HIVE_METASTORE_URI"])

    spark = builder.getOrCreate()

    hadoop = spark.sparkContext._jsc.hadoopConfiguration()
    hadoop.set("fs.s3a.access.key", s3_access_key)
    hadoop.set("fs.s3a.secret.key", s3_access_secret)
    hadoop.set("fs.s3a.endpoint", s3_endpoint)
    hadoop.set("fs.s3a.path.style.access", "true")

    delta_to_postgres(
        spark=spark,
        source=source,
        target=target,
        jdbc_url=spark.conf.get("spark.cti.pg_url"),
        user=spark.conf.get("spark.cti.pg_user"),
        password=spark.conf.get("spark.cti.pg_password"),
        pg_schema=spark.conf.get("spark.cti.pg_schema", "public"),
        pagination=spark.conf.get("spark.cti.pagination", "true").lower() == "true",
    )