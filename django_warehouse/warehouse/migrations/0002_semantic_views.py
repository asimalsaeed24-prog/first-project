"""Create the semantic layer as Postgres views.

The view bodies are read from sql/semantic/*.sql -- the same files Spark builds
its views from -- so the two engines expose the same columns and the same
definitions, and there is one place to change a definition.

The models in models.py for these views are managed = False, so 0001 recorded
them without emitting any DDL. This migration is what actually creates them.

Order matters: vw_report is the spine the fan-out views select from, and
vw_entity_coverage reads vw_report_entity. Views are dropped in reverse before
being created, because CREATE OR REPLACE VIEW in Postgres cannot change a view's
column list -- so a definition that gains or renames a column would fail.
"""
from pathlib import Path

from django.conf import settings
from django.db import migrations

# Dependency order. Matches the semantic stages in dags/cti_pipeline_dag.py.
VIEW_ORDER = [
    "vw_report",
    "vw_report_country",
    "vw_report_entity",
    "vw_report_group",
    "vw_entity_coverage",
]


def _definition(view: str) -> str:
    """The view body, with {{ target_schema }} pointed at the Postgres schema."""
    path = Path(settings.CTI_SQL_DIR) / "semantic" / f"{view}.sql"
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} not found. Point settings.CTI_SQL_DIR (or the CTI_SQL_DIR "
            f"environment variable) at the repo's sql/ folder."
        )
    return path.read_text(encoding="utf-8").replace(
        "{{ target_schema }}", settings.CTI_POSTGRES_SCHEMA
    )


def create_views(apps, schema_editor):
    schema = settings.CTI_POSTGRES_SCHEMA
    with schema_editor.connection.cursor() as cursor:
        for view in reversed(VIEW_ORDER):
            cursor.execute(f"DROP VIEW IF EXISTS {schema}.{view} CASCADE")
        for view in VIEW_ORDER:
            cursor.execute(f"CREATE VIEW {schema}.{view} AS {_definition(view)}")


def drop_views(apps, schema_editor):
    schema = settings.CTI_POSTGRES_SCHEMA
    with schema_editor.connection.cursor() as cursor:
        for view in reversed(VIEW_ORDER):
            cursor.execute(f"DROP VIEW IF EXISTS {schema}.{view} CASCADE")


class Migration(migrations.Migration):

    dependencies = [
        ("warehouse", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_views, drop_views),
    ]
