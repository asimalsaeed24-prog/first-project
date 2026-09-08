"""Django settings for the CTI/RASD warehouse schema.

This project exists to own the Postgres DDL and nothing else -- no views, no
templates, no auth. `manage.py migrate` is the only command it is here to run,
which is what the django_migrate task in the DAG calls.

Connection details come from the same environment variables psql uses, so the
same settings work from a shell, a container and the Airflow worker.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "not-a-secret-migrations-only")
DEBUG = False
ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "warehouse",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("PGDATABASE", "cti"),
        "USER": os.environ.get("PGUSER", "postgres"),
        "PASSWORD": os.environ.get("PGPASSWORD", ""),
        "HOST": os.environ.get("PGHOST", "localhost"),
        "PORT": os.environ.get("PGPORT", "5432"),
        "OPTIONS": {
            # Everything lands in one schema. Keep this in step with
            # spark.cti.pg.schema, which is what load_postgres.py writes to.
            "options": f"-c search_path={os.environ.get('PGSCHEMA', 'public')}"
        },
    }
}

# Where the semantic layer's .sql files live. The 0002 migration reads them, so
# the views in Postgres are built from the same text Spark uses.
CTI_SQL_DIR = Path(os.environ.get("CTI_SQL_DIR", BASE_DIR.parent / "sql"))

# The schema those views are created in, substituted for {{ target_schema }}.
CTI_POSTGRES_SCHEMA = os.environ.get("PGSCHEMA", "public")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
