"""Database and storage configuration for the Barangay system.

SQLite remains the local default. Set DATABASE_URL to a PostgreSQL URL in
production (for example, Render's Internal Database URL).
"""

import os
from datetime import timedelta

from dotenv import load_dotenv


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _absolute_path(value, default):
    path = os.path.expanduser(value or default)
    if not os.path.isabs(path):
        path = os.path.join(BASE_DIR, path)
    return os.path.abspath(path)


def _as_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _normalize_database_url(value):
    """Use SQLAlchemy's Psycopg 3 driver for PostgreSQL URLs."""
    value = (value or "").strip()
    if not value:
        return ""
    lower_value = value.lower()
    if lower_value.startswith("postgres://"):
        return "postgresql+psycopg://" + value[len("postgres://"):]
    if lower_value.startswith("postgresql://"):
        return "postgresql+psycopg://" + value[len("postgresql://"):]
    if lower_value.startswith(("postgresql+psycopg://", "sqlite:")):
        return value
    raise RuntimeError(
        "DATABASE_URL must be a PostgreSQL URL or a sqlite: URL."
    )


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "development-only-change-me")
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)

    DATA_DIR = _absolute_path(
        os.environ.get("DATA_DIR"), os.path.join(BASE_DIR, "instance")
    )
    SQLITE_DB_PATH = _absolute_path(
        os.environ.get("SQLITE_DB_PATH"), os.path.join(DATA_DIR, "minante.db")
    )
    _database_url = _normalize_database_url(os.environ.get("DATABASE_URL"))
    SQLALCHEMY_DATABASE_URI = _database_url or (
        "sqlite:///" + SQLITE_DB_PATH.replace("\\", "/")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    try:
        LGBTQIA_REPORT_MIN_GROUP_SIZE = max(
            2, int(os.environ.get("LGBTQIA_REPORT_MIN_GROUP_SIZE", "5"))
        )
    except ValueError:
        LGBTQIA_REPORT_MIN_GROUP_SIZE = 5
    SQLALCHEMY_ENGINE_OPTIONS = {"hide_parameters": True, "pool_pre_ping": True}
    if SQLALCHEMY_DATABASE_URI.startswith("sqlite:"):
        SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {
            "timeout": 30,
            "check_same_thread": False,
        }
    else:
        # Keep the connection count modest for Render's smallest Postgres plan.
        SQLALCHEMY_ENGINE_OPTIONS.update({
            "pool_size": 5,
            "max_overflow": 5,
            "pool_recycle": 300,
            "connect_args": {"connect_timeout": 10},
        })

    UPLOAD_FOLDER = os.path.join(DATA_DIR, "uploads")
    IDENTIFICATION_FOLDER = os.path.join(DATA_DIR, "identifications")
    PERMIT_FOLDER = os.path.join(DATA_DIR, "permits")
    SIGNATURE_FOLDER = os.path.join(DATA_DIR, "signatures")

    SESSION_COOKIE_SECURE = _as_bool(
        os.environ.get("SESSION_COOKIE_SECURE"), False
    )
    PREFERRED_URL_SCHEME = "https" if SESSION_COOKIE_SECURE else "http"
    SMS_PROVIDER = os.environ.get("SMS_PROVIDER", "simulated")
    BARANGAY_NAME = os.environ.get("BARANGAY_NAME", "Barangay Minante 1")
    CITY_MUNICIPALITY = os.environ.get(
        "CITY_MUNICIPALITY", "Cauayan City, Isabela"
    )
