from __future__ import annotations

from pathlib import Path

from airflow.models import Variable

PROJECT_HOME = Variable.get(
    "cti_project_home", default_var=str(Path(__file__).resolve().parents[1])
)
SQL_DIR = Path(PROJECT_HOME) / "sql"

DJANGO_HOME = Variable.get(
    "cti_django_home", default_var=str(Path(PROJECT_HOME) / "django_warehouse")
)

SPARK_CONN_ID = Variable.get("cti_spark_conn_id", default_var="spark_default")

POSTGRES_CONN_ID = Variable.get("cti_postgres_conn_id", default_var="cti_postgres")

POSTGRES_DRIVER = Variable.get(
    "cti_postgres_package", default_var="org.postgresql:postgresql:42.7.3"
)

SOURCE_SCHEMA = Variable.get("cti_source_schema", default_var="cti")
TARGET_SCHEMA = Variable.get("cti_target_schema", default_var="gold")
POSTGRES_SCHEMA = Variable.get("cti_postgres_schema", default_var="public")

SPARK_CONF = {
    "spark.cti.source_schema": SOURCE_SCHEMA,
    "spark.cti.target_schema": TARGET_SCHEMA,
    "spark.cti.sql_dir": str(SQL_DIR),
}

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
    resolved: list[tuple[str, list[str]]] = []
    scheduled: set[str] = set()

    for stage_name, entries in build_order:
        models = [model for model in expand(*entries) if model not in scheduled]
        scheduled.update(models)
        if models:
            resolved.append((stage_name, models))

    return resolved
