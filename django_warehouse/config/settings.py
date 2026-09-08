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
            "options": f"-c search_path={os.environ.get('PGSCHEMA', 'public')}"
        },
    }
}

CTI_SQL_DIR = Path(os.environ.get("CTI_SQL_DIR", BASE_DIR.parent / "sql"))

CTI_POSTGRES_SCHEMA = os.environ.get("PGSCHEMA", "public")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
