# Render PostgreSQL Setup

The app uses SQLite by default on a developer's computer and Render-managed PostgreSQL through `DATABASE_URL` in production. The root `render.yaml` Blueprint creates both the web service and a private Render PostgreSQL database in Singapore. It connects them using the database's internal connection string. The database accepts connections only from Render's private network by default.

## Configure the PostgreSQL service

1. In Render, create a Blueprint from the repository's `workspace-latest` branch. The root `render.yaml` defines both the `barangay-minante-1` web service and the `barangay-minante-db` PostgreSQL database.
2. Review the resources before creating them. The database is in Singapore, uses PostgreSQL 18, the smallest paid compute plan (`0.1c-256mb`), and 1 GB of storage. `DATABASE_URL` is linked to its internal connection string. Its IP allow list is empty so only Render private-network clients can connect by default.
3. Keep `DATA_DIR=/var/data` for private ID scans, attachments, signatures, and generated documents. The Blueprint creates a separate 1 GB persistent disk for these files. Do not set `SQLITE_DB_PATH` on Render.
4. Set `INITIAL_ADMIN_USERNAME`, `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_NAME`, and a strong `INITIAL_ADMIN_PASSWORD` in the Blueprint prompts. Render generates `SECRET_KEY`.
5. If preserving local records, migrate them before allowing the web service to initialize the empty PostgreSQL database. Temporarily allow only your current public IP in the database's inbound IP rules for migration, then remove that rule.
6. `python seed.py` creates/upgrades the PostgreSQL schema and initializes the administrator and catalogs. It preserves an existing administrator and does not create demo residents. Confirm `/healthz` returns `{"status":"ok","database":"postgresql"}`, then sign in, create a harmless test record, restart, and verify the record remains.
## Preserve the existing local SQLite records

The project folder contains `barangay_system/instance/minante.db`. The root `.gitignore` excludes that database from GitHub, so a Render PostgreSQL database will start empty unless you migrate records. The migration utility requires an empty PostgreSQL target; `python seed.py` initializes the web service database, so migrate before creating the web service.

1. In Render, create only a PostgreSQL database first. Match the Blueprint: name `barangay-minante-db`, database `barangay_minante`, user `barangay_minante_user`, Singapore, PostgreSQL 18, paid plan `0.1c-256mb`, and 1 GB storage.
2. In the database's inbound IP rules, temporarily allow only your computer's current public IP. Do not allow all IPs. Copy the External Database URL and keep it private.
3. In PowerShell, run the migration utility from the `barangay_system` folder. Set `DATABASE_URL` to the External Database URL, run a dry run, review its row counts, then run with `--apply` only if they are correct:

   ```powershell
   cd barangay_system
   $env:DATABASE_URL = "<Render External Database URL>"
   ..\.venv\Scripts\python.exe migrate_sqlite_to_postgres.py --source "instance\minante.db"
   ..\.venv\Scripts\python.exe migrate_sqlite_to_postgres.py --source "instance\minante.db" --apply
   ```

   If using system Python instead of the project virtual environment, install `requirements.txt` first. Never paste the database URL into GitHub or a screenshot.
4. After the migration succeeds, remove the temporary public IP rule. Then create the Blueprint from `workspace-latest`. It will attach the existing database and create the web service. Render injects the private `DATABASE_URL` into the web service.
5. Enter the initial administrator settings when prompted. The startup seed creates or upgrades the schema and preserves the migrated administrator. The utility never modifies the SQLite source and stops if it detects unknown tables/columns or data already present in PostgreSQL.
6. The utility does not copy uploaded files. If existing records refer to files in `barangay_system/instance/uploads`, `identifications`, or `signatures`, copy those files to the Render disk at the appropriate `DATA_DIR` paths before exposing the service. Verify access and file persistence after deployment.

To start with an empty database instead, create the Blueprint directly. The startup seed initializes the empty PostgreSQL database with the admin account and catalogs.
## Cost and data-retention notes

As of November 2026, Render lists the smallest paid web plan at **$7/month**, the smallest paid PostgreSQL compute plan (`0.1c-256mb`) at **$6/month**, PostgreSQL storage at **$0.30/GB-month**, and a 1 GB persistent disk at **$0.25/month**. With 1 GB of database storage, the estimated base is about **$13.55/month**, before taxes, bandwidth, or other usage. Confirm the prices shown in your workspace before creating or upgrading resources.

Render Free PostgreSQL is suitable for a temporary test only: it is limited to 1 GB, expires 30 days after creation, has no backups, and is deleted after the additional 14-day grace period if not upgraded. Free web-service files are ephemeral. Paid PostgreSQL persists relational data; the attached disk is for the app's file uploads. Review Render's current [pricing](https://render.com/pricing), [Free instance limitations](https://render.com/docs/free), and [Postgres documentation](https://render.com/docs/postgresql) before using real resident data.

Keep the Internal/External Database URLs, `SECRET_KEY`, and initial administrator password private. Keep independent backups of PostgreSQL and uploaded files. Private identification documents remain outside public static folders and are served through the application's authorization checks.
