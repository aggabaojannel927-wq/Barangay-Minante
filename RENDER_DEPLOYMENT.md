# Render PostgreSQL Setup

The app now supports Render-managed PostgreSQL through `DATABASE_URL`. It still uses SQLite by default on a developer's computer. The Render Blueprint does not create a database automatically: create or select one in the Render Dashboard, then add its private connection URL to the web service. This avoids provisioning a billable database just by syncing the repository.

## Configure the PostgreSQL service shown in your example

1. In Render, open **New + → PostgreSQL**. If you already created the database shown in your screenshot, open and use that database instead of creating another one.
2. If creating it now, name it (for example, `barangay-minante-db`), choose **Singapore**, and PostgreSQL **18**. For ongoing use, choose the smallest paid plan rather than Free. Set the database and user names or keep Render's generated values, then create it.
3. Push and deploy this PostgreSQL-ready application code before setting `DATABASE_URL`. The currently deployed SQLite-only version rejects PostgreSQL URLs. The updated code still runs on the SQLite fallback until you add the database URL.
4. Open the database's **Connect** panel and copy its **Internal Database URL**. Keep it private. The web service and database should both be in Singapore so they can communicate over Render's private network.
5. Open the `barangay-minante-1` web service → **Environment**. Add `DATABASE_URL` and paste the Internal Database URL as its value. Do not put this URL in the repository, a screenshot, or a public issue.
6. Keep `DATA_DIR=/var/data` for private ID scans, attachments, signatures, and generated files. The Blueprint keeps the existing 1 GB disk for these files; PostgreSQL stores relational records. Do not set `SQLITE_DB_PATH` on Render. Set `INITIAL_ADMIN_USERNAME`, `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_NAME`, `INITIAL_ADMIN_PASSWORD`, and a strong `SECRET_KEY` before the first start on a new database.
7. Render redeploys the service after the environment change. `python seed.py` creates/upgrades the PostgreSQL schema and initializes the administrator/catalogs; it preserves an existing administrator and does not create demo residents. Confirm `/healthz` returns `{"status":"ok","database":"postgresql"}`, then sign in and create a harmless test record. Restart and verify it remains.

## Retain records from an existing SQLite database

Pointing `DATABASE_URL` at PostgreSQL creates a new database; it does not transfer SQLite records or uploaded files. If the records matter, take and verify a SQLite backup before switching. Then, **before deploying the web service against the new empty database**, run the migration utility from a computer that can reach the database's External Database URL:

```powershell
cd barangay_system
$env:DATABASE_URL = "<Render External Database URL>"
python migrate_sqlite_to_postgres.py --source "<path to verified minante.db>"
python migrate_sqlite_to_postgres.py --source "<path to verified minante.db>" --apply
```

The first command is a dry run. The second copies records only if PostgreSQL is empty, validates table row counts, resets integer ID sequences, and leaves SQLite untouched. Do not run the migration twice. Before the migration, allow only your computer's current public IP under the database's inbound IP rules; never open PostgreSQL to all IPs for this step. After checking the successful migration output, set the web service's `DATABASE_URL` to its **Internal Database URL** and deploy. Remove the temporary external-IP rule after migrating. The utility deliberately stops if it finds unknown tables or columns rather than silently dropping them.

The currently deployed Free Render service may keep its SQLite file on an ephemeral filesystem. If that database exists only on Render and you do not have a local/verified SQLite backup, do not switch `DATABASE_URL` yet: the change alone cannot retrieve or copy that file. Export and verify the source records first. The migration utility does not transfer uploaded files; copy any files needed by those records into the persistent `DATA_DIR` disk before the switch.

## Cost and data-retention notes

As of October 2026, Render lists the smallest paid web plan at **$7/month**, its smallest paid PostgreSQL plan (`0.1c-256mb`) at **$6/month**, and a 1 GB persistent disk at **$0.25/month**. With this Blueprint's web plan and disk, the estimated base is about **$13.25/month**, before taxes, bandwidth, or other usage. Confirm the prices shown in your workspace before creating or upgrading resources.

Render Free PostgreSQL is suitable for a temporary test only: it is limited to 1 GB, expires 30 days after creation, has no backups, and is deleted after the additional 14-day grace period if not upgraded. Free web-service files are ephemeral. Paid PostgreSQL persists relational data; the attached disk is for the app's file uploads. Review Render's current [pricing](https://render.com/pricing), [Free instance limitations](https://render.com/docs/free), and [Postgres documentation](https://render.com/docs/postgresql) before using real resident data.

Keep the Internal/External Database URLs, `SECRET_KEY`, and initial administrator password private. Keep independent backups of PostgreSQL and uploaded files. Private identification documents remain outside public static folders and are served through the application's authorization checks.
