# Barangay Management System Revision Notes

This note summarizes the current application revisions prepared for the Render deployment. It was checked against the Flask routes, services, templates, SQLite/PostgreSQL migration code, tests, and the repository's Render configuration.

## Major system changes

- **Resident Services scope:** Removed the Scholarship/Ayuda interface and exclusive flows, General Concern Intake, and the Resident Update Request, Household Management, and Assistance Referral panels/endpoints. Existing historical records and shared data structures are retained. Blotter Management remains separate and available.
- **Walk-in Front Desk:** Added assisted resident intake for staff, service-specific Permit, Event, Blotter, and Appointment requests, duplicate-resident matching, queue numbers and states, encoder tracking, printable acknowledgments, and manual follow-up.
- **Resident information:** Added family-head and repeatable family-member fields, plus resident-only disability information. Authorized staff can review and update saved details; children do not receive accounts. Reports use aggregate data and do not expose individual disability details.
- **Permit workflow:** Preserved administrator authorization, document verification, remarks, notifications, acknowledgments, and approved-permit downloads. Payment status and electronic signatures no longer gate permit status transitions. Permit Details omits the Payment Status section and View Payments link; retained payment records and other payment interfaces are not changed by permit updates.
- **Event workflow:** Added the availability calendar to the existing event application flow, using date/time/venue conflicts and current permit status. Pending applications remain distinct from approved bookings. Event status updates retain authorization and notification handling; payment is not required to mark an approved event Completed.
- **Scheduling:** Fixed status form value handling and validation so supported status selections are saved and invalid values are rejected with a useful response.
- **Reports & Analytics:** Removed report filter controls and load Permit, Event, Blotter, and Overall Barangay summaries automatically from the configured database. The Overall report includes population, gender, disability yes/no/unknown, and disability-type aggregates. The report download is PDF; the editable Word report endpoint is removed.
- **Security and data handling:** Retained role and ownership checks, CSRF validation, audit logging, private identification uploads, and non-destructive schema migrations for SQLite and PostgreSQL. Sensitive resident and household records remain in the database and are not included in this repository update.
- **Render database support:** Added PostgreSQL support through Render's `DATABASE_URL`, kept SQLite as the local default, adapted analytics/date calculations and schema upgrades for PostgreSQL, and added an empty-target SQLite-to-PostgreSQL migration utility. The Render setup guide uses a manually created/selected Singapore PostgreSQL service and keeps its URL out of source control.

## Deployment and validation

- Render's Blueprint uses `barangay_system` as its application root. It now expects `DATABASE_URL` for PostgreSQL and keeps private uploads under `/var/data` on a 1 GB disk. The guide gives step-by-step dashboard configuration and current cost information.
- The complete backend unit suite passed locally: `python -B -m unittest discover -s tests -p "test_*.py"` — **102 tests passed**.
- Permit browser checks also passed for the status workflow and signature-free permit processing, including acknowledgment and approved-permit downloads.
- Pointing `DATABASE_URL` at PostgreSQL does not automatically migrate a live SQLite database or uploaded files. Back up and verify any needed live records first. The new migration utility copies relational data only into an empty database; persistent disk storage keeps uploaded files, and independent backups are still required.

## Files intentionally kept out of the deployment commit

Local databases, resident uploads, environment secrets, virtual environments, backups, audit output, screenshots, generated ZIP archives, and generated PDF/Word documentation are excluded. The commit contains application code, templates, static assets, setup requirements, and automated tests only.
