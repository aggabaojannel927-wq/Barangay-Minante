# Render deployment

The `workspace-latest` branch contains a temporary, no-cost Render demo Blueprint. It defines a Free web service and a Free Render PostgreSQL database in Singapore, linked through the private `DATABASE_URL`. The free web service has no persistent disk; uploaded files are ephemeral. The free database shown in the Render dashboard expires on December 5, 2026.

## Create the temporary demo

1. In Render, create a Blueprint from `aggabaojannel927-wq/Barangay-Minante`, branch `workspace-latest`. The Blueprint's database name matches the Free database already created, so Render can link the web service to it.
2. Enter `INITIAL_ADMIN_USERNAME`, `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_NAME`, and a strong `INITIAL_ADMIN_PASSWORD` in Render's prompts. `SECRET_KEY` is generated automatically. Keep passwords and connection URLs private.
3. Review the cost summary. Both compute resources should show Free. Do not proceed if Render shows a paid plan or disk charge.
4. Deploy the Blueprint. The startup command initializes the PostgreSQL schema and admin/catalog data. It does not create demo residents. After signing in, use invented sample names and information for any demo records.
5. Do not put real resident records, identification documents, signatures, or uploads in this temporary demo. The free database expires and the web service filesystem is ephemeral.

## Existing local data

The local database `barangay_system/instance/minante.db` is excluded from GitHub. It has not been migrated to Render. Keep it unchanged and backed up. The migration utility does not copy uploaded files, and the Free demo database is not an appropriate destination for real resident records.

When persistent hosting is affordable, create a paid Render PostgreSQL database and a paid web service with a persistent disk. Migrate the verified SQLite backup into a new, empty PostgreSQL database before the web service runs its seed command. Follow the migration utility's dry-run output before applying. Keep the database private and copy any required uploads to the persistent disk separately. If the demo database contains sample rows, do not use it as the migration target; the migration utility stops when its target contains data.

## Free plan limits and future production costs

Render Free PostgreSQL expires 30 days after creation unless upgraded. Free service files are ephemeral and free web services can spin down when idle. This configuration is for a temporary demo only.

The paid configuration previously prepared uses a $7/month web plan, a $6/month smallest paid Postgres compute plan, PostgreSQL storage at $0.30/GB-month, and a $0.25/month 1 GB persistent disk. For 1 GB Postgres storage, that is about $13.55/month before taxes, bandwidth, or other usage. Confirm current [Render pricing](https://render.com/pricing), [Free plan limits](https://render.com/docs/free), and [Blueprint behavior](https://render.com/docs/blueprint-spec) in your account before switching to paid hosting.