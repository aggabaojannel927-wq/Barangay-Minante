"""PostgreSQL URL, schema, and SQL compilation checks without a live database."""
import unittest
import sqlite3
import tempfile
import os
from pathlib import Path
from contextlib import closing
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from config import _normalize_database_url
from migration import _addition_ddl
from models import db
from app import app
import services.analytics as analytics
from migrate_sqlite_to_postgres import sqlite_snapshot


class PostgreSQLCompatibilityTests(unittest.TestCase):
    def test_database_url_selects_psycopg_driver(self):
        self.assertEqual(
            _normalize_database_url("postgres://user:secret@host/db"),
            "postgresql+psycopg://user:secret@host/db",
        )
        self.assertEqual(
            _normalize_database_url("postgresql://user:secret@host/db"),
            "postgresql+psycopg://user:secret@host/db",
        )
        self.assertEqual(
            _normalize_database_url("postgresql+psycopg://user@host/db"),
            "postgresql+psycopg://user@host/db",
        )
        self.assertEqual(_normalize_database_url("sqlite:///local.db"), "sqlite:///local.db")
        with self.assertRaises(RuntimeError):
            _normalize_database_url("mysql://host/db")

    def test_legacy_column_additions_use_postgresql_types_and_boolean_literals(self):
        self.assertEqual(
            _addition_ddl("DATETIME", "postgresql"), "TIMESTAMP"
        )
        self.assertEqual(
            _addition_ddl("BOOLEAN NOT NULL DEFAULT 1", "postgresql"),
            "BOOLEAN NOT NULL DEFAULT TRUE",
        )
        self.assertEqual(
            _addition_ddl("BOOLEAN NOT NULL DEFAULT 0", "postgresql"),
            "BOOLEAN NOT NULL DEFAULT FALSE",
        )
        self.assertEqual(
            _addition_ddl("BOOLEAN NOT NULL DEFAULT 1", "sqlite"),
            "BOOLEAN NOT NULL DEFAULT 1",
        )

    def test_current_model_schema_compiles_for_postgresql(self):
        with app.app_context():
            for table in db.metadata.sorted_tables:
                ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))
                self.assertIn(f'CREATE TABLE {table.name}', ddl)

    def test_analytics_date_and_duration_sql_compiles_for_postgresql(self):
        with app.app_context(), patch.object(
            analytics.db.session, "get_bind",
            return_value=SimpleNamespace(dialect=SimpleNamespace(name="postgresql")),
        ):
            year, month = analytics._year_month(db.metadata.tables['users'].c.created_at)
            elapsed = analytics._duration(
                db.metadata.tables['users'].c.updated_at,
                db.metadata.tables['users'].c.created_at,
                60,
            )
            statement = select(year, month, elapsed).compile(dialect=postgresql.dialect())
            sql = str(statement)
            self.assertIn("INTERVAL '8 hours'", sql)
            self.assertIn("EXTRACT(year FROM", sql)
            self.assertIn("EXTRACT(month FROM", sql)
            self.assertIn("EXTRACT(epoch FROM", sql)
            self.assertNotIn("strftime", sql)
            self.assertNotIn("julianday", sql)

    def test_sqlite_snapshot_is_consistent_and_leaves_source_unchanged(self):
        folder = Path(__file__).resolve().parents[1] / "instance"
        folder.mkdir(exist_ok=True)
        fd, source_name = tempfile.mkstemp(prefix="migration-fixture-", suffix=".db", dir=folder)
        os.close(fd)
        source = Path(source_name)
        snapshot = None
        try:
            with closing(sqlite3.connect(source)) as connection:
                connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, label TEXT)")
                connection.execute("INSERT INTO sample (label) VALUES ('synthetic fixture')")
                connection.commit()
            snapshot = sqlite_snapshot(source)
            with closing(sqlite3.connect(snapshot)) as connection:
                self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM sample").fetchone()[0], 1)
            with closing(sqlite3.connect(source)) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM sample").fetchone()[0], 1)
        finally:
            if snapshot:
                Path(snapshot).unlink(missing_ok=True)
            source.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
