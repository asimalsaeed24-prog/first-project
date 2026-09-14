"""Reload PostgreSQL tables from Delta tables: parallel pages, one swap transaction.

A PostgreSQL transaction belongs to a single connection, so pages written in
parallel cannot share one. The load therefore runs in two steps:

1. Stage   Each Delta table is read at a pinned snapshot version and written in
           parallel into an UNLOGGED staging table next to its target. Each
           Spark partition is one page, with its own connection and batched
           inserts.
2. Swap    One transaction on one connection checks every staging row count,
           TRUNCATEs all targets in a single statement and refills them with
           INSERT ... SELECT from staging. Readers see all old data or all new
           data, never a half-loaded table.

Staging tables are dropped whether the load succeeds or fails.

High availability
- List every host in the JDBC URL with targetServerType=primary. Each step opens
  a fresh connection, so after a failover it reaches the new primary. If staging
  data is lost in the failover, the row-count check rolls the swap back.
- swap_mode="truncate" blocks reads on the targets until the swap commits.
  swap_mode="delete" keeps them readable during the swap, but leaves dead rows
  for autovacuum to clean up.
- Tables linked by foreign keys must be loaded in the same call. PostgreSQL only
  truncates a referenced table together with the tables that reference it.

Usage
  spark-submit \\
    --conf spark.cti.target_schema=cti_gold \\
    --conf "spark.cti.pg_url=jdbc:postgresql://pg1:5432,pg2:5432/cti?targetServerType=primary" \\
    --conf spark.cti.pg_user=... --conf spark.cti.pg_password=... \\
    delta_to_postgres.py dim_country,dim_rasd_entity,fact_rasd_report,bridge_country \\
      <s3_access_key> <s3_access_secret> <s3_endpoint>
"""

from __future__ import annotations

import math
import os
import sys
import uuid
from contextlib import contextmanager
from dataclasses import dataclass

from pyspark.sql import DataFrame, SparkSession

PG_DRIVER = "org.postgresql.Driver"


@dataclass
class _Load:
    source: str
    target: str
    staging: str
    df: DataFrame
    version: int
    columns: list[str]
    rows: int


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _qualified(schema: str, table: str) -> str:
    return f"{_quote(schema)}.{_quote(table)}"


@contextmanager
def _pg_connection(spark: SparkSession, jdbc_url: str, user: str, password: str):
    """JDBC connection on the driver, using the PostgreSQL jar Spark already loaded."""
    jvm = spark.sparkContext._jvm
    loader = jvm.java.lang.Thread.currentThread().getContextClassLoader()
    driver = jvm.java.lang.Class.forName(PG_DRIVER, True, loader).newInstance()
    props = jvm.java.util.Properties()
    props.setProperty("user", user)
    props.setProperty("password", password)
    conn = driver.connect(jdbc_url, props)
    if conn is None:
        raise ValueError(f"PostgreSQL driver does not accept URL {jdbc_url}")
    try:
        yield conn
    finally:
        conn.close()


def _execute(conn, sql: str) -> None:
    stmt = conn.createStatement()
    try:
        stmt.execute(sql)
    finally:
        stmt.close()


def _count(conn, table_sql: str) -> int:
    stmt = conn.createStatement()
    try:
        rs = stmt.executeQuery(f"SELECT count(*) FROM {table_sql}")
        rs.next()
        return rs.getLong(1)
    finally:
        stmt.close()


def _target_columns(conn, schema: str, table: str) -> set[str]:
    ps = conn.prepareStatement(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = ? AND table_name = ?"
    )
    try:
        ps.setString(1, schema)
        ps.setString(2, table)
        rs = ps.executeQuery()
        columns = set()
        while rs.next():
            columns.add(rs.getString(1))
        return columns
    finally:
        ps.close()


def _read_delta_snapshot(spark: SparkSession, source: str) -> tuple[DataFrame, int]:
    """Pin one Delta version so the row count and the written rows always match."""
    ref = f"delta.`{source}`" if "/" in source else source
    version = spark.sql(f"DESCRIBE HISTORY {ref} LIMIT 1").first()["version"]
    return spark.sql(f"SELECT * FROM {ref} VERSION AS OF {version}"), version


def _normalize(tables) -> list[tuple[str, str]]:
    """Accept 'schema.table', a Delta path, or (delta_source, pg_table) pairs."""
    if isinstance(tables, (str, tuple)):
        tables = [tables]
    pairs = []
    for item in tables:
        if isinstance(item, str):
            pairs.append((item, item.rstrip("/").split("/")[-1].split(".")[-1]))
        else:
            source, target = item
            pairs.append((source, target))
    return pairs


def delta_to_postgres(
    spark: SparkSession,
    tables,
    jdbc_url: str,
    user: str,
    password: str,
    pg_schema: str = "public",
    rows_per_page: int = 100_000,
    max_parallel_pages: int = 8,
    batch_size: int = 10_000,
    swap_mode: str = "truncate",
    lock_timeout: str = "30s",
    analyze: bool = True,
) -> dict[str, int]:
    """Replace the contents of PostgreSQL tables with the contents of Delta tables.

    Args:
        spark: Active SparkSession with Delta and the PostgreSQL JDBC jar.
        tables: One or more Delta tables. Each item is a metastore name
            ('cti_gold.dim_country'), a Delta path, or a (delta_source, pg_table)
            tuple. Without a tuple, the PostgreSQL table takes the last name part.
        jdbc_url: PostgreSQL JDBC URL. Use a multi-host URL with
            targetServerType=primary for failover.
        user: PostgreSQL user.
        password: PostgreSQL password.
        pg_schema: PostgreSQL schema that holds the target tables.
        rows_per_page: Target rows per parallel page (Spark partition).
        max_parallel_pages: Upper bound on pages, and so on concurrent connections.
        batch_size: Rows per JDBC insert batch within a page.
        swap_mode: 'truncate' (TRUNCATE + INSERT) or 'delete' (DELETE + INSERT,
            which keeps readers unblocked during the swap).
        lock_timeout: Longest time the swap waits for table locks before it fails
            instead of queueing other sessions behind it.
        analyze: Run ANALYZE on the targets after a successful swap.

    Returns:
        Rows loaded per PostgreSQL table.
    """
    if swap_mode not in ("truncate", "delete"):
        raise ValueError("swap_mode must be 'truncate' or 'delete'")

    run_id = uuid.uuid4().hex[:8]
    loads: list[_Load] = []
    for source, target in _normalize(tables):
        df, version = _read_delta_snapshot(spark, source)
        loads.append(_Load(
            source=source,
            target=target,
            staging=f"{target[:40]}__stg_{run_id}",
            df=df,
            version=version,
            columns=df.columns,
            rows=df.count(),
        ))
        print(f"read {source} version {version}: {loads[-1].rows} rows")

    try:
        # 1. prepare staging tables with the exact column types of the targets
        with _pg_connection(spark, jdbc_url, user, password) as conn:
            conn.setAutoCommit(True)
            for load in loads:
                existing = _target_columns(conn, pg_schema, load.target)
                if not existing:
                    raise ValueError(f"PostgreSQL table {pg_schema}.{load.target} does not exist")
                missing = [c for c in load.columns if c not in existing]
                if missing:
                    raise ValueError(f"{pg_schema}.{load.target} is missing columns {missing}")
                cols = ", ".join(_quote(c) for c in load.columns)
                _execute(conn, (
                    f"CREATE UNLOGGED TABLE {_qualified(pg_schema, load.staging)} AS "
                    f"SELECT {cols} FROM {_qualified(pg_schema, load.target)} WITH NO DATA"
                ))

        # 2. write pages in parallel, one connection per Spark partition
        for load in loads:
            pages = max(1, min(max_parallel_pages, math.ceil(load.rows / rows_per_page)))
            print(f"staging {load.target}: {load.rows} rows in {pages} parallel pages")
            (
                load.df.repartition(pages)
                .write.format("jdbc")
                .option("url", jdbc_url)
                .option("driver", PG_DRIVER)
                .option("dbtable", _qualified(pg_schema, load.staging))
                .option("user", user)
                .option("password", password)
                .option("numPartitions", pages)
                .option("batchsize", batch_size)
                .option("reWriteBatchedInserts", "true")
                .option("stringtype", "unspecified")
                .mode("append")
                .save()
            )

        # 3. swap all targets in one transaction
        with _pg_connection(spark, jdbc_url, user, password) as conn:
            conn.setAutoCommit(False)
            try:
                _execute(conn, "SET LOCAL lock_timeout = '{}'".format(lock_timeout.replace("'", "''")))
                _execute(conn, "SET CONSTRAINTS ALL DEFERRED")

                for load in loads:
                    staged = _count(conn, _qualified(pg_schema, load.staging))
                    if staged != load.rows:
                        raise RuntimeError(
                            f"{load.target}: staged {staged} rows, expected {load.rows}; nothing was replaced"
                        )

                targets = [_qualified(pg_schema, load.target) for load in loads]
                if swap_mode == "truncate":
                    _execute(conn, f"TRUNCATE TABLE {', '.join(targets)}")
                else:
                    for target in targets:
                        _execute(conn, f"DELETE FROM {target}")

                for load in loads:
                    cols = ", ".join(_quote(c) for c in load.columns)
                    _execute(conn, (
                        f"INSERT INTO {_qualified(pg_schema, load.target)} ({cols}) "
                        f"SELECT {cols} FROM {_qualified(pg_schema, load.staging)}"
                    ))

                conn.commit()
                print(f"swapped {len(loads)} tables in one transaction ({swap_mode})")
            except Exception:
                conn.rollback()
                raise

    finally:
        try:
            with _pg_connection(spark, jdbc_url, user, password) as conn:
                conn.setAutoCommit(True)
                for load in loads:
                    _execute(conn, f"DROP TABLE IF EXISTS {_qualified(pg_schema, load.staging)}")
        except Exception as error:
            print(f"warning: could not drop staging tables for run {run_id}: {error}")

    if analyze:
        with _pg_connection(spark, jdbc_url, user, password) as conn:
            conn.setAutoCommit(True)
            for load in loads:
                _execute(conn, f"ANALYZE {_qualified(pg_schema, load.target)}")

    return {load.target: load.rows for load in loads}


#?>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit(
            "usage: delta_to_postgres.py <table>[,<table>...] <s3_access_key> <s3_access_secret> <s3_endpoint>"
        )

    names, s3_access_key, s3_access_secret, s3_endpoint = sys.argv[1:]

    builder = SparkSession.builder.appName("delta_to_postgres").enableHiveSupport()
    if "HIVE_METASTORE_URI" in os.environ:
        builder = builder.config("hive.metastore.uris", os.environ["HIVE_METASTORE_URI"])
    spark = builder.getOrCreate()

    hadoop_conf = spark.sparkContext._jsc.hadoopConfiguration()
    hadoop_conf.set("fs.s3a.access.key", s3_access_key)
    hadoop_conf.set("fs.s3a.secret.key", s3_access_secret)
    hadoop_conf.set("fs.s3a.endpoint", s3_endpoint)
    hadoop_conf.set("fs.s3a.path.style.access", "true")

    target_schema = spark.conf.get("spark.cti.target_schema", "gold")
    sources = [
        name if "." in name or "/" in name else f"{target_schema}.{name}"
        for name in names.split(",")
        if name.strip()
    ]

    loaded = delta_to_postgres(
        spark,
        sources,
        jdbc_url=spark.conf.get("spark.cti.pg_url"),
        user=spark.conf.get("spark.cti.pg_user"),
        password=spark.conf.get("spark.cti.pg_password"),
        pg_schema=spark.conf.get("spark.cti.pg_schema", "public"),
    )
    for table, rows in loaded.items():
        print(f"loaded {table}: {rows} rows")
