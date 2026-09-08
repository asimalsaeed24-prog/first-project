"""Move the CTI/RASD star schema from the lakehouse into Postgres.

One task per table, discovered from sql/ the same way the build DAG does it.
Dimensions are merged on id, bridges and the fact are replaced in full -- see
load_postgres.py.

The dimensions load first so that by the time the fact and the bridges land,
every id they point at is already in Postgres. Within each group the tables are
independent and run in parallel.

Connection details reach load_postgres.py as spark.cti.pg.* configs built from
the Airflow connection named by cti_config.POSTGRES_CONN_ID. They are Jinja
templates, so nothing is resolved until the task runs and no credential is read
while the DAG is being parsed.

That does require a provider new enough to template SparkSubmitOperator's conf
(apache-airflow-providers-apache-spark 4.x and later). On an older one, drop the
templates and build the dict from BaseHook.get_connection(...) instead --
accepting that the password is then read at parse time.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.task_group import TaskGroup

from cti_config import (
    POSTGRES_CONF,
    POSTGRES_DRIVER,
    PROJECT_HOME,
    SPARK_CONN_ID,
    models_in,
)

# Dimensions first, then everything that points at them.
LOAD_ORDER = [("dimensions", ["dim"]), ("facts", ["bridge", "fact"])]

with DAG(
    dag_id="cti_postgres_load",
    description="Merge dimensions and replace facts in Postgres",
    start_date=datetime(2026, 1, 1),
    schedule=None,  # triggered after cti_star_schema, or scheduled to taste
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "cti",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["cti", "postgres", "spark"],
) as dag:

    previous = None

    for group_id, layers in LOAD_ORDER:
        tables = models_in(*layers)
        if not tables:
            continue

        with TaskGroup(group_id=group_id) as group:
            for table in tables:
                SparkSubmitOperator(
                    task_id=table,
                    conn_id=SPARK_CONN_ID,
                    application=f"{PROJECT_HOME}/load_postgres.py",
                    application_args=[table],
                    conf=dict(POSTGRES_CONF),
                    packages=POSTGRES_DRIVER,
                    name=f"cti_pg_{table}",
                    verbose=False,
                )

        if previous is not None:
            previous >> group
        previous = group
