from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.task_group import TaskGroup

from cti_config import (
    DJANGO_HOME,
    POSTGRES_CONF,
    POSTGRES_DRIVER,
    PROJECT_HOME,
    SPARK_CONF,
    SPARK_CONN_ID,
    stages,
)

BUILD = "build"
MIGRATE = "migrate"
LOAD = "load"

PIPELINE = [
    ("staging_tables",          BUILD,    ["staging"]),
    ("key_registry",            BUILD,    ["keys"]),
    ("dimension_tables",        BUILD,    ["dim"]),
    ("fact_and_bridge_tables",  BUILD,    ["bridge", "fact"]),
    ("semantic_spine",          BUILD,    ["semantic/vw_report"]),
    ("semantic_views",          BUILD,    ["semantic/vw_report_country",
                                           "semantic/vw_report_entity",
                                           "semantic/vw_report_group"]),
    ("semantic_metrics",        BUILD,    ["semantic"]),
    ("django_migrate",          MIGRATE,  []),
    ("postgres_dimensions",     LOAD,     ["dim"]),
    ("postgres_facts",          LOAD,     ["bridge", "fact"]),
]

with DAG(
    dag_id="cti_pipeline",
    description="Build the CTI/RASD star schema, then publish it to Postgres",
    start_date=datetime(2026, 1, 1),
    schedule="0 3 * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "cti",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["cti", "lakehouse", "postgres", "spark"],
) as dag:

    models_for = {}
    for phase in (BUILD, MIGRATE, LOAD):
        in_phase = [(name, models) for name, kind, models in PIPELINE if kind == phase]
        models_for.update(dict(stages(in_phase)))

    previous = None

    for group_name, kind, _entries in PIPELINE:
        models = models_for.get(group_name, [])

        with TaskGroup(group_id=group_name) as group:
            if kind == MIGRATE:
                BashOperator(
                    task_id="manage_py_migrate",
                    bash_command=(
                        f"cd {DJANGO_HOME} && python manage.py migrate --no-input"
                    ),
                )

            for model in models:
                name = model.split("/")[-1]

                if kind == BUILD:
                    SparkSubmitOperator(
                        task_id=name,
                        conn_id=SPARK_CONN_ID,
                        application=f"{PROJECT_HOME}/run.py",
                        application_args=[model],
                        conf=dict(SPARK_CONF),
                        name=f"cti_{name}",
                        verbose=False,
                    )

                elif kind == LOAD:
                    SparkSubmitOperator(
                        task_id=name,
                        conn_id=SPARK_CONN_ID,
                        application=f"{PROJECT_HOME}/load_postgres.py",
                        application_args=[name],
                        conf=dict(POSTGRES_CONF),
                        packages=POSTGRES_DRIVER,
                        name=f"cti_pg_{name}",
                        verbose=False,
                    )

        if previous is not None:
            previous >> group
        previous = group
