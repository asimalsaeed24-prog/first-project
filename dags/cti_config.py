"""Settings both CTI DAGs pass down to Spark.

Everything the Spark scripts need arrives as --conf under the spark.cti.*
namespace, so the DAG owns the configuration and the scripts hold no
environment lookups of their own. The scripts keep defaults for these, which is
what makes a bare `spark-submit run.py <model>` still work outside Airflow.

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

# Where manage.py lives, for the django_migrate task.
DJANGO_HOME = Variable.get(
    "cti_django_home", default_var=str(Path(PROJECT_HOME) / "django_warehouse")
)

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


def expand(*entries: str) -> list[str]:
    """Turn stage entries into "layer/model" paths.

        "dim"             -> every model in sql/dim/, in name order
        "dim/dim_entity"  -> just that one

    A layer expands to whatever is on disk, so adding a .sql file adds a task.
    Naming a single model lets a stage pin something that has to go first.
    """
    models: list[str] = []
    for entry in entries:
        if "/" in entry:
            models.append(entry)
        else:
            models += [
                f"{entry}/{path.stem}"
                for path in sorted((SQL_DIR / entry).glob("*.sql"))
            ]
    return models


def stages(build_order: list[tuple[str, list[str]]]) -> list[tuple[str, list[str]]]:
    """Resolve a stage array into (stage name, models) with nothing repeated.

    A model already scheduled by an earlier stage is dropped from later ones, so
    a stage can pin one model and a later stage can sweep up "everything else in
    that folder" without building it twice.
    """
    resolved: list[tuple[str, list[str]]] = []
    scheduled: set[str] = set()

    for stage_name, entries in build_order:
        models = [model for model in expand(*entries) if model not in scheduled]
        scheduled.update(models)
        if models:
            resolved.append((stage_name, models))

    return resolved
