"""Copy an existing SQLite database into an empty PostgreSQL database.

This utility never edits the SQLite source. It refuses a PostgreSQL target
that already contains data and requires --apply before inserting records.
Set DATABASE_URL to the destination PostgreSQL URL before running it.
"""

import argparse
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

from sqlalchemy import MetaData, create_engine, inspect, select, text
from sqlalchemy.exc import SQLAlchemyError


def sqlite_snapshot(source_path):
    """Make a transactionally consistent temporary copy using SQLite backup."""
    source_path = Path(source_path).expanduser().resolve()
    if not source_path.is_file():
        raise ValueError("The SQLite source file does not exist.")
    fd, snapshot_path = tempfile.mkstemp(prefix="barangay-migration-", suffix=".db")
    os.close(fd)
    try:
        source = sqlite3.connect(source_path)
        target = sqlite3.connect(snapshot_path)
        try:
            source.backup(target)
            result = target.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            target.close()
            source.close()
        if result.lower() != "ok":
            raise ValueError("SQLite integrity_check failed; the source was not copied.")
        return snapshot_path
    except Exception:
        Path(snapshot_path).unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Path to the SQLite database file")
    parser.add_argument(
        "--apply", action="store_true",
        help="Copy records after verifying that the PostgreSQL target is empty",
    )
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")):
        parser.error("Set DATABASE_URL to the PostgreSQL destination URL first.")

    # Import after checking the target URL: app.py builds its database engine
    # from DATABASE_URL, and no migration or write runs just by importing it.
    from app import app
    from models import db

    if db.engine.dialect.name != "postgresql":
        parser.error("The configured destination is not PostgreSQL.")

    snapshot_path = sqlite_snapshot(args.source)
    source_engine = create_engine("sqlite:///" + snapshot_path.replace("\\", "/"))
    try:
        with app.app_context():
            target_engine = db.engine
            target_inspector = inspect(target_engine)
            existing_tables = set(target_inspector.get_table_names())
            # Never overwrite an existing PostgreSQL deployment or its data.
            for table_name in existing_tables:
                quoted = target_engine.dialect.identifier_preparer.quote(table_name)
                with target_engine.connect() as connection:
                    if connection.execute(text(f"SELECT 1 FROM {quoted} LIMIT 1")).first():
                        raise ValueError(
                            "The PostgreSQL target already contains data. Use a new empty database."
                        )

            source_metadata = MetaData()
            source_metadata.reflect(bind=source_engine)
            source_tables = set(source_metadata.tables)
            model_tables = set(db.metadata.tables)
            unknown_tables = source_tables - model_tables
            if unknown_tables:
                raise ValueError(
                    "The SQLite database has tables not represented by the current models; "
                    "migration stopped to protect their data: " + ", ".join(sorted(unknown_tables))
                )

            mismatched_columns = []
            row_counts = {}
            for name in sorted(source_tables):
                source_table = source_metadata.tables[name]
                target_table = db.metadata.tables[name]
                extras = set(source_table.columns.keys()) - set(target_table.columns.keys())
                if extras:
                    mismatched_columns.append(name + ": " + ", ".join(sorted(extras)))
                with source_engine.connect() as connection:
                    row_counts[name] = connection.execute(
                        select(text("COUNT(*)")).select_from(source_table)
                    ).scalar_one()
            if mismatched_columns:
                raise ValueError(
                    "SQLite has columns that the current app does not model; "
                    "migration stopped rather than omit them: " + "; ".join(mismatched_columns)
                )

            total_rows = sum(row_counts.values())
            print(f"SQLite source tables: {len(source_tables)}; records: {total_rows}.")
            if not args.apply:
                print("Dry run only. PostgreSQL was not changed. Review the source, then rerun with --apply.")
                return 0

            # The schema is created with the current SQLAlchemy models. All
            # record inserts and sequence resets occur in one PG transaction.
            db.create_all()
            with target_engine.begin() as destination:
                for table in db.metadata.sorted_tables:
                    if table.name not in source_tables:
                        continue
                    source_table = source_metadata.tables[table.name]
                    names = [column.name for column in table.columns
                             if column.name in source_table.columns]
                    if not names:
                        continue
                    with source_engine.connect() as origin:
                        result = origin.execute(select(*(source_table.c[name] for name in names)))
                        while True:
                            batch = result.fetchmany(500)
                            if not batch:
                                break
                            destination.execute(
                                table.insert(),
                                [{name: row._mapping[name] for name in names} for row in batch],
                            )

                for table in db.metadata.sorted_tables:
                    if table.name not in source_tables or "id" not in table.columns:
                        continue
                    if not table.c.id.primary_key:
                        continue
                    quoted = target_engine.dialect.identifier_preparer.quote(table.name)
                    sequence = destination.execute(text(
                        "SELECT pg_get_serial_sequence(:table_name, 'id')"
                    ), {"table_name": table.name}).scalar_one_or_none()
                    if not sequence:
                        continue
                    last_id = destination.execute(
                        text(f"SELECT MAX(id) FROM {quoted}")
                    ).scalar_one()
                    if last_id is None:
                        destination.execute(text(
                            "SELECT setval(CAST(:sequence_name AS regclass), 1, false)"
                        ), {"sequence_name": sequence})
                    else:
                        destination.execute(text(
                            "SELECT setval(CAST(:sequence_name AS regclass), :last_id, true)"
                        ), {"sequence_name": sequence, "last_id": last_id})

                for name, expected in row_counts.items():
                    quoted = target_engine.dialect.identifier_preparer.quote(name)
                    actual = destination.execute(text(f"SELECT COUNT(*) FROM {quoted}")).scalar_one()
                    if actual != expected:
                        raise RuntimeError(f"Record count verification failed for table {name}.")

            print(f"Migration complete. Verified {total_rows} records across {len(source_tables)} tables.")
            print("The SQLite source file was left unchanged. Keep the verified backup until the app is checked.")
            return 0
    finally:
        source_engine.dispose()
        Path(snapshot_path).unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, SQLAlchemyError) as error:
        print(f"Migration stopped safely: {error}", file=sys.stderr)
        raise SystemExit(1)
