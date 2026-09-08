import os
import sys

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("cti_postgres_load").getOrCreate()

LAKE_SCHEMA = spark.conf.get("spark.cti.target_schema", "gold")
PG_SCHEMA = spark.conf.get("spark.cti.pg.schema", "public")

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
    target = f"{PG_SCHEMA}.{table}"
    stage = f"{PG_SCHEMA}.{table}_stage"
    column_list = ", ".join(f'"{c}"' for c in columns)

    statements = [f"CREATE TABLE IF NOT EXISTS {target} (LIKE {stage} INCLUDING DEFAULTS)"]

    if table.startswith("dim_"):
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
