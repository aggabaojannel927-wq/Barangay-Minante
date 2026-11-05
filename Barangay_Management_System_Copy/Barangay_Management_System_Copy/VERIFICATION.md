# Agency handoff verification

Validated on 20 October 2026 with Python 3.14 and the installed project dependencies.

- **82 automated acceptance/regression tests passed against the copied application.**
  The existing test suite was run externally with temporary SQLite databases; test
  fixtures and their synthetic login credentials are not part of the distribution.
- **69 original runtime/source files are byte-for-byte unchanged**, including the
  application, models, services, templates, styles, JavaScript, and portable scripts.
  `SOURCE_MANIFEST.json` records their hashes without original computer paths.
- All **288 snapshotted original project files** remained unchanged. The original
  database, uploads, and documents were never copied into the distribution or edited.
- The independent SQLite database has **36 tables**. SQLite integrity and foreign
  key checks passed. Only resident types, accepted-ID names, permit types, and event
  category names contain neutral setup data. All other tables are empty, including
  users, profiles, family members, households, requests, notifications, and logs.
- The schema-only SQL recreates all 36 tables successfully in a separate database.
- A separate temporary relocation, including a path containing spaces, initialized
  successfully and could be initialized again without replacing its administrator.
  Temporary generated credentials and its secret key are not in this package.
- Relocated health, login, registration, static assets, dashboard, user management,
  front desk, reports, schedules, announcements, configuration, permits, events,
  blotters, and notifications returned HTTP 200. PDF report generation passed with
  the existing authenticated POST/CSRF workflow.
- `pip check` reported **no broken dependencies** in the environment used for testing.
  A new dependency download/install on an agency computer was not performed here;
  install the pinned requirements on that computer as described in the README.
- A scan found no original-computer directory dependencies, actual `.env` file,
  private keys, resident uploads, backups, virtual environments, or cache files in
  the distribution. ZIP entries are checked against their source file hashes and
  archive CRC integrity.

## Agency configuration still required

Run `initialize_system.py` to generate a private local secret and choose your own
administrator credentials. Configure accepted IDs, venues, service rules, fees,
and staff accounts before evaluation with actual records. No default login ships
with the system. Registration is intentionally gated until accepted IDs are set.

The original SMS/email implementation simulates delivery; real delivery needs an
implemented provider integration and agency-owned credentials. Optional web fonts
need internet access; ordinary system font fallbacks remain available offline.

The Flask development server supports local evaluation. For production, arrange
HTTPS, a suitable WSGI server, private persistent storage and backups. Preserve
the SQLite database and local `.env` created after installation. The supplied
Render free-plan template uses temporary storage and needs persistent storage
configuration before real operational use.
