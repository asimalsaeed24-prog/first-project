"""Build the CTI/RASD star schema.

Reads each file in sql/ and runs the statements in it:

    spark-submit run.py

SQL_DIR is a plain path string. "sql" works when you run from the project root.
Anywhere else -- spark-submit from another folder, or a notebook -- set it to an
absolute path, e.g. "/Workspace/Repos/you/first-project/sql".

To change what gets built, edit MODELS. To change a query, edit its .sql file.

Statements are separated by ';', so a ';' must not appear inside a string
literal or a comment in any .sql file.

The dimensions are APPEND-ONLY. Their ids come from Delta identity columns and
the business reports against them, so a dimension must never be dropped or
rebuilt with CREATE OR REPLACE -- that re-mints every id. Back them up.
"""
from pyspark.sql import SparkSession

SOURCE_SCHEMA = "cti"
TARGET_SCHEMA = "gold"

SQL_DIR = "sql"

# Build order: staging first, then the dimensions, then the bridges and the
# fact that read them.
MODELS = [
    "staging/stg_report",
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

for model in MODELS:
    with open(f"{SQL_DIR}/{model}.sql", encoding="utf-8") as sql_file:
        query = sql_file.read()

    query = query.replace("{{ source_schema }}", SOURCE_SCHEMA)
    query = query.replace("{{ target_schema }}", TARGET_SCHEMA)

    print(f"running {model}")
    for statement in query.split(";"):
        if statement.strip():
            spark.sql(statement)

print("done")
