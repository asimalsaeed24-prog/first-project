"""Build the CTI/RASD star schema.

Reads each file in sql/ and runs it:

    spark-submit run.py                     # everything, in order
    spark-submit run.py dim/dim_country     # one model, for Airflow or a retry

Settings arrive as --conf, so the Airflow DAG owns them:

    spark.cti.source_schema   where cti.rasd and cti.entities live   (cti)
    spark.cti.target_schema   the schema to build into               (gold)
    spark.cti.sql_dir         the folder holding these .sql files    (sql)

The defaults in brackets are what you get running this by hand. Set
spark.cti.sql_dir to an absolute path unless you are running from the project
root -- spark-submit makes no promise about the working directory.

Two kinds of table, and the difference matters:

  * gold.dim_key holds every dimension's surrogate key and is the only table
    with state. Its file carries its own CREATE TABLE IF NOT EXISTS and appends
    the keys it has not seen before. BACK IT UP -- dropping it re-mints every id
    the business reports against.

  * Everything else -- staging, dimensions, bridges, fact -- is derived. Its
    .sql file is a plain SELECT, it is created on the first run and
    INSERT OVERWRITE-n after that, and it can be dropped and rebuilt freely.

Statements are separated by ';', so a ';' must not appear inside a string
literal or a comment in any .sql file.

INSERT OVERWRITE requires the query's columns to match the existing table. If
you add or rename a column in a derived model, DROP its table once and let this
script recreate it.
"""
import sys

from pyspark.sql import SparkSession

# Build order: staging, then the keys minted from it, then the dimensions that
# read those keys, then the bridges and the fact.
MODELS = [
    "staging/stg_report",
    "staging/stg_entity",
    "keys/dim_key",
    "dim/dim_classification",
    "dim/dim_country",
    "dim/dim_entity",
    "dim/dim_evidence_type",
    "dim/dim_group",
    "dim/dim_importance_level",
    "dim/dim_source",
    "dim/dim_threat_type",
    "bridge/bridge_country",
    "bridge/bridge_entity",
    "bridge/bridge_group",
    "fact/fact_report",
]

spark = SparkSession.builder.appName("cti_rasd_star_schema").getOrCreate()

SOURCE_SCHEMA = spark.conf.get("spark.cti.source_schema", "cti")
TARGET_SCHEMA = spark.conf.get("spark.cti.target_schema", "gold")
SQL_DIR = spark.conf.get("spark.cti.sql_dir", "sql")

# A model named on the command line, otherwise the whole list in order.
for model in sys.argv[1:] or MODELS:
    with open(f"{SQL_DIR}/{model}.sql", encoding="utf-8") as sql_file:
        query = sql_file.read()

    query = query.replace("{{ source_schema }}", SOURCE_SCHEMA)
    query = query.replace("{{ target_schema }}", TARGET_SCHEMA)

    table = f"{TARGET_SCHEMA}.{model.split('/')[-1]}"

    if model.startswith("keys/"):
        # Append-only. The file says what to create and what to add.
        print(f"appending to {table}")
        for statement in query.split(";"):
            if statement.strip():
                spark.sql(statement)

    elif spark.catalog.tableExists(table):
        print(f"overwriting {table}")
        spark.sql(f"INSERT OVERWRITE TABLE {table} {query}")

    else:
        print(f"creating {table}")
        spark.sql(f"CREATE TABLE {table} USING delta AS {query}")

print("done")
