"""Settings both CTI DAGs pass down to Spark.

Everything the Spark scripts need arrives as --conf under the spark.cti.*
namespace, so the DAG owns the configuration and the scripts hold no
environment lookups of their own. The scripts keep defaults for these, which is
what makes a bare `spark-submit run.py` still work outside Airflow.

The two paths below are needed while the DAG file is being parsed -- to find the
.sql files and build one task per model -- so they cannot come from Spark. They
are Airflow Variables, overridable in the UI or with AIRFLOW_VAR_CTI_*, and they
fall back to the repo this file sits in.
"""
from __future__ import annotations

from pathlib import Path

from airflow.models import Variable

PROJECT_HOME = Variable.get(
    "cti_project_home", default_var=str(Path(__file__).resolve().parents[1])
)
SQL_DIR = Path(PROJECT_HOME) / "sql"

SPARK_CONN_ID = Variable.get("cti_spark_conn_id", default_var="spark_default")

# The Airflow connection holding the Postgres host, port, database, login and
# password. Read at task runtime through Jinja, never at parse time, so the
# password is not resolved until the task starts.
POSTGRES_CONN_ID = Variable.get("cti_postgres_conn_id", default_var="cti_postgres")

POSTGRES_DRIVER = Variable.get(
    "cti_postgres_package", default_var="org.postgresql:postgresql:42.7.3"
)

SOURCE_SCHEMA = Variable.get("cti_source_schema", default_var="cti")
TARGET_SCHEMA = Variable.get("cti_target_schema", default_var="gold")
POSTGRES_SCHEMA = Variable.get("cti_postgres_schema", default_var="public")

# What every task passes to Spark. sql_dir is absolute on purpose: spark-submit
# does not promise a working directory, so a relative "sql" would be a coin flip.
SPARK_CONF = {
    "spark.cti.source_schema": SOURCE_SCHEMA,
    "spark.cti.target_schema": TARGET_SCHEMA,
    "spark.cti.sql_dir": str(SQL_DIR),
}

# Postgres settings, resolved from the connection when the task runs.
# Spark redacts any config whose name matches secret|password|token before it
# reaches the UI or the event log, so naming this one ...password matters.
POSTGRES_CONF = {
    **SPARK_CONF,
    "spark.cti.pg.schema": POSTGRES_SCHEMA,
    "spark.cti.pg.url": (
        "jdbc:postgresql://"
        f"{{{{ conn.{POSTGRES_CONN_ID}.host }}}}"
        f":{{{{ conn.{POSTGRES_CONN_ID}.port }}}}"
        f"/{{{{ conn.{POSTGRES_CONN_ID}.schema }}}}"
    ),
    "spark.cti.pg.user": f"{{{{ conn.{POSTGRES_CONN_ID}.login }}}}",
    "spark.cti.pg.password": f"{{{{ conn.{POSTGRES_CONN_ID}.password }}}}",
}


def models_in(*layers: str) -> list[str]:
    """The model names under sql/<layer>, in a stable order."""
    return sorted(path.stem for layer in layers for path in (SQL_DIR / layer).glob("*.sql"))
