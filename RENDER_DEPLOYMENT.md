# Deploy Barangay Minante on Render

The application uses SQLite for local development and PostgreSQL when Render provides `DATABASE_URL`. The root `render.yaml` defines the web service and references the existing Render Postgres service named `barangay-minante-db`.

## Deploy through the Blueprint

1. Push the latest project revision to the GitHub repository's `main` branch.
2. In Render, choose **New +** and **Blueprint** (or **Generate Blueprint**), then connect `aggabaojannel927-wq/Barangay-Minante` on branch `main`.
3. Review the Blueprint changes. It should add the `barangay-minante-1` web service and use the existing `barangay-minante-db` database; do not create a second database.
4. Enter the prompted `INITIAL_ADMIN_USERNAME`, `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_NAME`, and a strong `INITIAL_ADMIN_PASSWORD`. Keep these private. Render generates `SECRET_KEY` automatically.
5. Choose the Free web service plan if you are only demonstrating the system, then create/apply the Blueprint.
6. Open the web service's **Events** or **Logs** page and wait for the deploy to show **Live**. Visit `/healthz`, then sign in with the Administrator credentials from step 4.

The Blueprint sets the web service region to Singapore and obtains `DATABASE_URL` from the existing Postgres service's internal connection string. Keep both services in the same Render workspace and region. The build and start commands are `pip install -r requirements.txt` and `python seed.py && gunicorn --workers 1 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT app:app`.

## Free-plan limits

The Free web service has an ephemeral filesystem. Uploaded IDs and other private files can disappear on restart, redeploy, or spin-down; the Postgres database stores relational records separately. Render Free Postgres expires 30 days after creation and is deleted after its grace period unless upgraded. Back up any records you need before the expiration date. Free services are for demonstrations, not production records.

## Data on first deploy

`seed.py` creates the schema, Administrator account, and service catalogs when the database is empty. It does not create sample residents or staff accounts and does not copy records from a local SQLite database. If local records need to be migrated, back up the local database first and plan a separate migration before using Render with real records.

Private ID uploads remain outside public static folders and are served only through authorization checks.
