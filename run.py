"""Build one model of the CTI/RASD star schema.

    spark-submit run.py dim/dim_country

One model per run, so every Airflow task is one model: each shows up in the
graph, can be retried on its own, and a failure names the model that broke.

This script knows nothing about what order the models go in. That lives in
BUILD_ORDER in dags/cti_star_schema_dag.py.

Settings arrive as --conf, so the Airflow DAG owns them:

    spark.cti.source_schema   where cti.rasd and cti.entities live   (cti)
    spark.cti.target_schema   the schema to build into               (gold)
    spark.cti.sql_dir         the folder holding the .sql files      (sql)

The defaults in brackets are what you get running this by hand. Set
spark.cti.sql_dir to an absolute path unless you are running from the project
root -- spark-submit makes no promise about the working directory.

What a model becomes depends on its folder:

  * keys/     the surrogate keys every dimension draws from, and the only table
              with state. The file carries its own CREATE TABLE IF NOT EXISTS
              and appends the keys it has not seen before. BACK IT UP --
              dropping it re-mints every id the business reports against.

  * semantic/ a VIEW. No storage, always current, safe to rebuild any time.

  * anything  a TABLE, created on the first run and INSERT OVERWRITE-n after
    else      that. Derived, so it can be dropped and rebuilt freely.

Statements are separated by ';', so a ';' must not appear inside a string
literal or a comment in any .sql file.

INSERT OVERWRITE requires the query's columns to match the existing table. If
you add or rename a column in a model, DROP its table once and let this script
recreate it.
"""
import sys

from pyspark.sql import SparkSession

if len(sys.argv) != 2:
    raise SystemExit("usage: run.py <layer>/<model>    e.g. run.py dim/dim_country")

model = sys.argv[1]
name = model.split("/")[-1]

spark = SparkSession.builder.appName(f"cti_{name}").getOrCreate()

SOURCE_SCHEMA = spark.conf.get("spark.cti.source_schema", "cti")
TARGET_SCHEMA = spark.conf.get("spark.cti.target_schema", "gold")
SQL_DIR = spark.conf.get("spark.cti.sql_dir", "sql")

with open(f"{SQL_DIR}/{model}.sql", encoding="utf-8") as sql_file:
    query = sql_file.read()

query = query.replace("{{ source_schema }}", SOURCE_SCHEMA)
query = query.replace("{{ target_schema }}", TARGET_SCHEMA)

table = f"{TARGET_SCHEMA}.{name}"

if model.startswith("keys/"):
    # Append-only. The file says what to create and what to add.
    print(f"appending to {table}")
    for statement in query.split(";"):
        if statement.strip():
            spark.sql(statement)

elif model.startswith("semantic/"):
    print(f"defining view {table}")
    spark.sql(f"CREATE OR REPLACE VIEW {table} AS {query}")

elif spark.catalog.tableExists(table):
    print(f"overwriting {table}")
    spark.sql(f"INSERT OVERWRITE TABLE {table} {query}")

else:
    print(f"creating {table}")
    spark.sql(f"CREATE TABLE {table} USING delta AS {query}")

print(f"done {table}")
