from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta
import glob

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.providers.apache.spark.hooks.spark_submit import SparkSubmitHook
from airflow.utils.task_group import TaskGroup



def expand(sql_dir: Path, *entries: str) -> list[str]:
    models: list[str] = []
    for entry in entries:
        if "/" in entry:
            models.append(entry)
        else:
            models += [
                f"{entry}/{path.stem}"
                for path in sorted((sql_dir / entry).glob("*.sql"))
            ]
    return models

def stages(sql_dir: Path, build_order: list[tuple[str, list[str]]]) -> list[tuple[str, list[str]]]:
    resolved: list[tuple[str, list[str]]] = []
    scheduled: set[str] = set()

    for stage_name, entries in build_order:
        models = [model for model in expand(sql_dir, *entries) if model not in scheduled]
        scheduled.update(models)
        if models:
            resolved.append((stage_name, models))

    return resolved


SPARK_CONN_ID = "spark_master_connection"
PROJECT_HOME ="/opt/spark/python"
SPARK_JARS_DIR = "/opt/spark/jars"
BUILD = "build"
MIGRATE = "migrate"
LOAD = "load"

s3_access_key = Variable.get("s3_access_key")
s3_access_secret = Variable.get("s3_access_password")
s3_endpoint = Variable.get("s3_endpoint")

SOURCE_SCHEMA = "cti"
TARGET_SCHEMA = "cti_gold"
SQL_DIR = Path(f"{PROJECT_HOME}/cti/sql")

SPARK_CONF = {
    "spark.cti.source_schema": SOURCE_SCHEMA,
    "spark.cti.target_schema": TARGET_SCHEMA,
    "spark.cti.sql_dir": str(SQL_DIR),
}

def run_spark_job_with_hook(model_name, s3_access_key, s3_access_secret, s3_endpoint):
    """Run Spark job using SparkSubmitHook instead of SparkSubmitOperator."""

    jar_paths = sorted(glob.glob(f"{SPARK_JARS_DIR}/*.jar"))
    jars = ",".join(jar_paths) if jar_paths else None
    

    application_args = [
        model_name,
        s3_access_key,
        s3_access_secret,
        s3_endpoint
    ]
    

    hook = SparkSubmitHook(
        conn_id=SPARK_CONN_ID,
        jars=jars,
        conf={
            "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
            "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
            "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem",
            "spark.driver.memory": "2g",
            "spark.executor.memory": "2g",
            "spark.cti.source_schema": SOURCE_SCHEMA,
            "spark.cti.target_schema": TARGET_SCHEMA,
            "spark.cti.sql_dir": str(SQL_DIR),
        },
        application_args=application_args,
        name=f"cti_{model_name.split('/')[-1]}",
        executor_cores=4,
        total_executor_cores=4,
        verbose=False,
    )
    

    hook.submit(application=f"{PROJECT_HOME}/cti/run.py")


PIPELINE = [
    ("staging_tables",          BUILD,    ["staging"]),
    ("key_registry",            BUILD,    ["keys"]),
    ("dimension_tables",        BUILD,    ["dim"]),
    ("fact_and_bridge_tables",  BUILD,    ["bridge", "fact"]),
    ("semantic_spine",          BUILD,    ["semantic/vw_report"]),
    ("semantic_views",          BUILD,    ["semantic/vw_report_country",
                                           "semantic/vw_report_entity",
                                           "semantic/vw_report_group",
                                           "semantic/vw_report_adversary",
                                           "semantic/vw_adversary_target_country"]),
    ("semantic_metrics",        BUILD,    ["semantic"]),
    # ("postgres_dimensions",     LOAD,     ["dim"]),
    # ("postgres_facts",          LOAD,     ["bridge", "fact"]),
]

with DAG(
    dag_id="spark_cti_rasd_data_model_dag",
    description="Build the CTI/RASD star schema",
    start_date=datetime(2026, 1, 1),
    schedule="0 3 * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["cti", "postgres", "spark"],
) as dag:

    models_for = {}
    for phase in (BUILD, MIGRATE, LOAD):
        in_phase = [(name, models) for name, kind, models in PIPELINE if kind == phase]
        models_for.update(dict(stages(SQL_DIR, in_phase)))

    previous = None

    for group_name, kind, _entries in PIPELINE:
        models = models_for.get(group_name, [])

        with TaskGroup(group_id=group_name) as group:
            for model in models:
                name = model.split("/")[-1]

                if kind == BUILD:
                    PythonOperator(
                        task_id=name,
                        python_callable=run_spark_job_with_hook,
                        op_kwargs={
                            "model_name": model,
                            "s3_access_key": s3_access_key,
                            "s3_access_secret": s3_access_secret,
                            "s3_endpoint": s3_endpoint,
                        },
                    )

                # elif kind == LOAD:
                #     SparkSubmitOperator(
                #         task_id=name,
                #         conn_id=SPARK_CONN_ID,
                #         application=f"{PROJECT_HOME}/load_postgres.py",
                #         application_args=[name],
                #         conf=dict(POSTGRES_CONF),
                #         packages=POSTGRES_DRIVER,
                #         name=f"cti_pg_{name}",
                #         verbose=False,
                #     )

        if previous is not None:
            previous >> group
        previous = group
