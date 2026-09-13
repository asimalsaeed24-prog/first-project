import sys
import os
from pyspark.sql import SparkSession



def get_SparkSession(name, s3_access_key, s3_access_secret, s3_endpoint):
    REQUIRED_JARS = [
        "delta-spark_2.12-3.3.0.jar",
        "delta-storage-3.3.0.jar",
        "hadoop-aws-3.3.4.jar",
        "aws-java-sdk-bundle-1.12.262.jar",
        "postgresql-42.7.3.jar",
        "jaxb-api-2.3.1.jar"
    ]  
    jar_paths = ",".join([f"/opt/spark/jars/{jar}" for jar in REQUIRED_JARS])
    spark = (
        SparkSession.builder.appName(name)
        .config('spark.master',os.environ['SPARK_MASTER_URL'])
        .config("spark.driver.bindAddress", "0.0.0.0")
        .config("spark.sql.autoBroadcastJoinThreshold", "-1")
        .config("spark.sql.repl.eagerEval.enabled", "true")
        .config("spark.sql.parquet.datetimeRebaseModeInWrite", "LEGACY")
        .config("spark.sql.caseSensitive", True)
        .config("spark.sql.catalog.spark_catalog","org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.jars",jar_paths)
        .config("hive.metastore.uris",  os.environ['HIVE_METASTORE_URI'])
        .config("spark.sql.warehouse.dir",  os.environ['S3_WAREHOUSE_PATH'])
        .enableHiveSupport()
        .getOrCreate()
    )

    spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.access.key", s3_access_key)
    spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.secret.key", s3_access_secret)
    spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.endpoint", s3_endpoint)
    spark.sparkContext._jsc.hadoopConfiguration().set("fs.s3a.path.style.access", "true")
    
    return spark



#?>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

if len(sys.argv) != 5:
    raise SystemExit("usage: run.py <layer>/<model> <s3_access_key> <s3_access_secret> <s3_endpoint>")

model = sys.argv[1]
name = model.split("/")[-1]
s3_access_key = sys.argv[2]
s3_access_secret = sys.argv[3]
s3_endpoint = sys.argv[4]

spark = get_SparkSession(name, s3_access_key, s3_access_secret, s3_endpoint)

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
