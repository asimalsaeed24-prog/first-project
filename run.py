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
