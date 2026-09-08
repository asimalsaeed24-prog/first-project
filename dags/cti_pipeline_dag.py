"""The CTI/RASD pipeline, end to end, in one DAG.

Build the star schema in the lakehouse, migrate the Postgres schema with Django,
then move the data across. One task per model throughout, so every model shows
up in the graph by name, can be retried on its own, and names itself when it
fails.

PIPELINE below is the whole schedule. Each entry is one task group:

    (group name, what kind of task, which models)

Groups run one after another and everything inside a group runs in parallel.
A "models" entry is either

    "dim"                 a layer -- expands to every .sql file in sql/dim/, so
                          adding a model adds a task with no edit here
    "semantic/vw_report"  one model -- pins something that has to go first

A model already scheduled by an earlier group is skipped later, which is what
lets the semantic layer pin its spine and then sweep up the rest of the folder.

Reorder the array, split a group, or pin a model, and the graph follows.

max_active_runs is 1 on purpose. gold.dim_key is appended to, and two runs
overlapping could mint the same id twice.
"""
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

# What kind of task a group builds.
BUILD = "build"          # spark-submit run.py <model>          -> lakehouse
MIGRATE = "migrate"      # django manage.py migrate             -> postgres schema
LOAD = "load"            # spark-submit load_postgres.py <table> -> postgres data

PIPELINE = [
    # group name                kind      models or layers
    ("staging_tables",          BUILD,    ["staging"]),
    ("key_registry",            BUILD,    ["keys"]),
    ("dimension_tables",        BUILD,    ["dim"]),
    # Bridges and the fact both read staging and the dimensions, and neither
    # reads the other, so they go together.
    ("fact_and_bridge_tables",  BUILD,    ["bridge", "fact"]),
    # The semantic views build on each other, so they come in dependency order.
    ("semantic_spine",          BUILD,    ["semantic/vw_report"]),
    ("semantic_views",          BUILD,    ["semantic/vw_report_country",
                                           "semantic/vw_report_entity",
                                           "semantic/vw_report_group"]),
    # Anything left in sql/semantic/, including views added later.
    ("semantic_metrics",        BUILD,    ["semantic"]),
    # Bring the Postgres schema up to date before anything is written to it.
    ("django_migrate",          MIGRATE,  []),
    # Dimensions first, so every id the facts point at is already there.
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

    # Resolve each phase separately. "Already scheduled" has to mean "already
    # built" or "already loaded" -- not both, or the Postgres groups would find
    # their tables taken by the build groups and end up empty.
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
