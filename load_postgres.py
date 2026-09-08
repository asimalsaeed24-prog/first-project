"""Move the CTI/RASD star schema from the lakehouse into Postgres.

    spark-submit --jars postgresql-42.7.3.jar load_postgres.py                 # everything
    spark-submit --jars postgresql-42.7.3.jar load_postgres.py dim_country     # one table

Dimensions are MERGED on id, so a row that has left the lakehouse keeps its
place in Postgres and anything already pointing at that id still resolves.
Bridges and the fact are REPLACED in full.

Every table goes through a staging table: Spark writes that, then Postgres moves
it into place in a single transaction. Two reasons for the extra hop --

  * writing straight onto the target with mode="overwrite" DROPS it, taking the
    indexes, constraints and grants with it
  * TRUNCATE and INSERT commit together, so readers see the old rows right up
    until the new ones are all there, never a half-loaded table

Settings arrive as --conf, so the Airflow DAG owns them:

    spark.cti.target_schema   the lakehouse schema to read from  (gold)
    spark.cti.sql_dir         used only to list the tables       (sql)
    spark.cti.pg.schema       the Postgres schema to write to    (public)
    spark.cti.pg.url          jdbc:postgresql://host:port/database
    spark.cti.pg.user
    spark.cti.pg.password     redacted by Spark in the UI and logs, because
                              the name matches spark.redaction.regex

The Postgres JDBC driver has to be on the classpath (--jars, or --packages
org.postgresql:postgresql:42.7.3).
"""
import os
import sys

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("cti_postgres_load").getOrCreate()

LAKE_SCHEMA = spark.conf.get("spark.cti.target_schema", "gold")
PG_SCHEMA = spark.conf.get("spark.cti.pg.schema", "public")

# Used only to work out the default table list.
SQL_DIR = spark.conf.get("spark.cti.sql_dir", "sql")

JDBC_URL = spark.conf.get("spark.cti.pg.url", "jdbc:postgresql://localhost:5432/cti")
JDBC_USER = spark.conf.get("spark.cti.pg.user", "postgres")
JDBC_PASSWORD = spark.conf.get("spark.cti.pg.password", "")
JDBC_PROPERTIES = {
    "user": JDBC_USER,
    "password": JDBC_PASSWORD,
    "driver": "org.postgresql.Driver",
    "batchsize": "10000",
}


def run_on_postgres(statements):
    """Run statements in ONE transaction, over the JDBC driver already loaded.

    Going through the JVM's DriverManager means no psycopg2 on the cluster --
    the driver Spark is already using is the only thing needed.
    """
    jvm = spark.sparkContext._jvm
    connection = jvm.java.sql.DriverManager.getConnection(JDBC_URL, JDBC_USER, JDBC_PASSWORD)
    try:
        connection.setAutoCommit(False)
        statement = connection.createStatement()
        for sql in statements:
            statement.execute(sql)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def plan(table, columns):
    """The Postgres statements that move a staged table into its target."""
    target = f"{PG_SCHEMA}.{table}"
    stage = f"{PG_SCHEMA}.{table}_stage"
    column_list = ", ".join(f'"{c}"' for c in columns)

    # Take the shape from the staged table the first time round, so the target
    # never has to be created by hand.
    statements = [f"CREATE TABLE IF NOT EXISTS {target} (LIKE {stage} INCLUDING DEFAULTS)"]

    if table.startswith("dim_"):
        # id is the surrogate key from gold.dim_key. ON CONFLICT needs it to be
        # a real primary key, so add one the first time.
        statements.append(
            f"DO $$ BEGIN"
            f"  IF NOT EXISTS (SELECT 1 FROM pg_constraint"
            f"                 WHERE conrelid = '{target}'::regclass AND contype = 'p') THEN"
            f"    ALTER TABLE {target} ADD PRIMARY KEY (id);"
            f"  END IF;"
            f"END $$"
        )
        assignments = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in columns if c != "id")
        statements.append(
            f"INSERT INTO {target} ({column_list}) SELECT {column_list} FROM {stage} "
            f"ON CONFLICT (id) DO UPDATE SET {assignments}"
        )
    else:
        statements.append(f"TRUNCATE TABLE {target}")
        statements.append(
            f"INSERT INTO {target} ({column_list}) SELECT {column_list} FROM {stage}"
        )

    statements.append(f"DROP TABLE {stage}")
    return statements


# A table named on the command line, otherwise every dimension, bridge and fact.
tables = sys.argv[1:]
if not tables:
    for layer in ("dim", "bridge", "fact"):
        folder = os.path.join(SQL_DIR, layer)
        if os.path.isdir(folder):
            tables += sorted(f[:-4] for f in os.listdir(folder) if f.endswith(".sql"))

for table in tables:
    how = "merge" if table.startswith("dim_") else "replace"
    stage = f"{PG_SCHEMA}.{table}_stage"

    frame = spark.table(f"{LAKE_SCHEMA}.{table}")

    print(f"staging {LAKE_SCHEMA}.{table} -> {stage}")
    frame.write.jdbc(JDBC_URL, stage, mode="overwrite", properties=JDBC_PROPERTIES)

    print(f"{how} {stage} -> {PG_SCHEMA}.{table}")
    run_on_postgres(plan(table, frame.columns))

print("done")
