# Barangay Minante 1 Management System — transferable source copy

This is the existing working Flask application, not a rebuild or documentation-only
package. It includes all runtime Python modules, models, routes, services, HTML
templates, CSS, JavaScript, migrations, and existing static assets. The unchanged
runtime files are listed with SHA-256 hashes in `SOURCE_MANIFEST.json`.

The included SQLite database contains the current schema and neutral setup catalogs
only. It contains **no accounts, passwords/password hashes, resident/family records,
uploaded IDs, signatures, requests, notifications, or audit logs**. No credentials,
virtual environment, caches, database backups, research documents, browser audit
artifacts, or developer test fixtures are included. The source models and migration
files preserve the entire existing schema, including legacy tables.

## Install and run on Windows

Use Python **3.11 or newer** (verified using Python 3.14), with pip and internet
access to install dependencies. Extract the ZIP first. Open PowerShell in the
extracted `Barangay_Management_System_Copy` folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe initialize_system.py
.\.venv\Scripts\python.exe barangay_system\app.py
```

The initializer asks for a **new** administrator username, email, and password. It
generates a unique local secret key in `barangay_system/.env`. There is no default
login. No password is written to the `.env` file. Existing administrator accounts
are preserved when the initializer is run again.

Open **http://127.0.0.1:5000**, then log in with the account you created. The provided
`setup.ps1` and `run.ps1` are optional shortcuts for dependency installation and
starting the application; run `initialize_system.py` once between those steps.

## Install and run on Linux/macOS

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python initialize_system.py
.venv/bin/python barangay_system/app.py
```

## Initial administrator configuration

1. In System Configuration, select the active **accepted ID types** for registration.
   IDs are intentionally unaccepted initially; public registration remains disabled
   until the Administrator configures them.
2. Configure supported permit/event categories, fees, venues, and available service
   requirements according to agency policy. Basic permit and event category names
   are initialized without inventing approved fees or venue rules.
3. Create authorized staff accounts through User Management. Residents register
   through the existing form and remain subject to ID/address verification and
   approval before login. No existing resident or staff accounts were transferred.
4. Use the existing permit, event, blotter, schedules, notifications, front desk,
   announcements, resident management, and reports interfaces as configured.

## Files and database

- `barangay_system/`: complete runtime application, including its own pinned
  `requirements.txt` and migrations.
- `barangay_system/instance/minante.db`: independently created clean SQLite database.
- `database/schema.sql`: schema-only SQL for inspection or recreation; no row data.
- `initialize_system.py`: local secret generation and interactive account setup.
- `setup.ps1`, `run.ps1`: portable Windows shortcuts from the original project.
- `render.yaml`: existing optional hosting configuration; supply your own settings.
- `VERIFICATION.md`: completed validation and known configuration requirements.

Default storage is relative to the transferred application folder. No directory on
the original owner's computer is required. Run the initializer from this copy; it
always initializes this copy's database. When starting the server, do not inherit
unrelated `DATABASE_URL`, `DATA_DIR`, or `SQLITE_DB_PATH` environment overrides.
These may override `.env` values. Runtime uploads and generated documents are saved
under `barangay_system/instance`. Keep that folder and `.env` private and backed up.

Starting `app.py` automatically applies the existing non-destructive schema upgrades.
For a WSGI deployment, run the following from `barangay_system` before starting it:

```sh
python -m flask --app app init-db
```

## Operational notes

- **SMS/email delivery is simulated in the existing system.** Real delivery needs
  an implemented provider integration and agency-supplied credentials. No provider
  API keys are included.
- Reports and document generation retain their existing PDF/Word functionality
  and dependencies. Reports use database records; a fresh database naturally has
  no resident/service totals until records are entered and approved.
- The stylesheet optionally loads Google Fonts. System font fallbacks work when
  offline; no external fonts are needed for application logic.
- Flask's built-in server is for local evaluation. Production hosting requires a
  suitable WSGI server, HTTPS, a private persistent SQLite directory, backups, and
  secure cookie configuration. Gunicorn is included for Linux hosting, not as a
  Windows server. The optional Render free-host template uses temporary storage;
  configure persistent storage before storing actual records.
- Install dependencies on the destination computer; the original computer's
  virtual environment is deliberately excluded.

## Quick verification after transfer

Run `python -m pip check` using the new virtual environment. After starting the
server, `/healthz` should return HTTP 200. Verify login, administrator configuration,
registration/approval, and a test transaction in each enabled module before using
actual resident information. Empty reports are expected before data entry.
