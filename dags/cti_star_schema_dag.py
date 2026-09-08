"""Build the CTI/RASD star schema in the lakehouse.

One task per .sql model, discovered from sql/ when the DAG is parsed -- drop a
file into sql/<layer>/ and a task appears, with no change here. Layers run in
order and the models inside a layer run in parallel:

    staging  ->  keys  ->  dim  ->  bridge  ->  fact

Each task is one spark-submit of run.py for a single model, which buys per-model
retries and a failure that names the model. The cost is a Spark session per
model. If start-up time dominates, replace the whole thing with a single task
running run.py with no arguments -- it builds everything in the right order by
itself.

Schemas and the model directory reach run.py as spark.cti.* configs, from
cti_config. The script has no environment lookups of its own.

max_active_runs is 1 on purpose. gold.dim_key is appended to, and two runs
overlapping could mint the same id twice.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.task_group import TaskGroup

from cti_config import PROJECT_HOME, SPARK_CONF, SPARK_CONN_ID, models_in

# Build order. Every layer waits for the whole of the one before it.
LAYERS = ["staging", "keys", "dim", "bridge", "fact"]

with DAG(
    dag_id="cti_star_schema",
    description="Build the CTI/RASD star schema from the models in sql/",
    start_date=datetime(2026, 1, 1),
    schedule="0 3 * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "cti",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["cti", "lakehouse", "spark"],
) as dag:

    previous = None

    for layer in LAYERS:
        models = models_in(layer)
        if not models:
            continue

        with TaskGroup(group_id=layer) as group:
            for model in models:
                SparkSubmitOperator(
                    task_id=model,
                    conn_id=SPARK_CONN_ID,
                    application=f"{PROJECT_HOME}/run.py",
                    application_args=[f"{layer}/{model}"],
                    conf=dict(SPARK_CONF),
                    name=f"cti_{model}",
                    verbose=False,
                )

        if previous is not None:
            previous >> group
        previous = group
