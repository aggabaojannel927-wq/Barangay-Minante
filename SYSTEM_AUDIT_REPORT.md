# Barangay Minante 1 Integrated Management System — Final Audit Report

Audit completed: October 5, 2026 (Asia/Manila)

## A. Executive Summary

The tested system is stable within the exercised scope. This revision adds the requested payment controls, walk-in acknowledgments, configurable Scholarship and Ayuda programs, scheduled/expiring announcements, real SQLite analytics, and editable Word reporting. The audit repaired verified workflow, authorization, upload, accessibility, pagination, performance, and documentation defects. It does not claim that undiscovered defects cannot remain.

## B. Project Areas Inspected

Flask routes and error handling; login, reset, sessions, CSRF, RBAC, ownership and self-processing restrictions; SQLite schema, migrations, foreign keys, indexes and backups; permits, events, blotters, scheduling, queueing, front desk, households, notifications, profiles, configuration and activity logs; uploads; acknowledgments and approved documents; payments; Scholarship/Ayuda programs; announcements; dashboards, reports, charts and DOCX export; templates, JavaScript, CSS, mobile layout, dependencies, README, `.gitignore`, and deployment configuration.

The route inventory contains 73 application routes and is generated at `barangay_system/audit-artifacts/ROUTE_INVENTORY.md` during the audit run. It is ignored from version control because it is a generated audit artifact.

## C. Critical Problems Found

| Problem | Location / root cause | Impact | Fix applied | Test result |
|---|---|---|---|---|
| A paid permit could be signed and released using a legacy confirmation field without an actual payment record. | Permit signing/release flow had no linked payment entity or eligibility check. | Financial records could be missing or misleading. | Added immutable `payments`, exact fee snapshot checks, authorized payment personnel, server-side signing/download/release gates, and actual-payment-only receipt generation. | Payment, waiver, duplicate, unauthorized, and full release-flow tests pass. |
| Community program applications, duplicate claims, and assistance release had no model or authorization workflow. | Feature absent. | Sensitive assistance records could not be managed safely. | Added reusable programs/applications, snapshots, one-time resident/household claim keys, review transitions, private files, and explicit authorized release confirmation. | Scholarship/Ayuda lifecycle, duplicate and slot tests pass. |

## D. High / Medium / Low Issues

| Severity | Problem | Fix / retest |
|---|---|---|
| High | Walk-in output was called a claim stub and did not include the required acknowledgment content. | Implemented a print view and editable DOCX Walk-in Transaction Acknowledgment with resident, queue, fee, payment state, requirements, staff encoder, next steps, and disclaimer. Ownership tests pass. |
| High | Announcements had no publish-start field, required no expiry, and could be deleted instead of retained. | Added Asia/Manila scheduling, dynamic backend lifecycle checks, categories, history-preserving Archive, program linking, and audit actions. Boundary tests pass. |
| High | A template referenced nonexistent `confirm_permit_payment`. | Removed the broken button and directed payment through the protected Payments module. Route-inventory/template endpoint test passes. |
| Medium | A document requirement could be supplied as text; staged files remained after a later validation failure. | Enforced type-specific validation and session-managed cleanup of uncommitted private uploads. Rollback upload test passes. |
| Medium | Announcement/program/payment/report lists could grow without pagination. | Added 30-record pagination, preserving query parameters. Page-two test passes. |
| Medium | The Administrator profile page raised a JavaScript null-reference error. | Guarded the optional controls. The final browser audit found zero JavaScript errors. |
| Low | Existing form submission code could disable a button indefinitely after a navigation/error edge case. | Added duplicate-submission guard, recovery on page restoration, and a timeout fallback. Browser interaction audit passes. |

## E. Broken Features Found

| Feature | Status | Result |
|---|---|---|
| Payment confirmation button | Fixed | Replaced with permission-controlled manual payment recording. |
| Walk-in acknowledgment | Fixed | Correct terminology and content, printable and editable Word output. |
| Program applications | Fixed | Configurable Scholarship/Ayuda workflow with protected records. |
| Announcement scheduling/expiration | Fixed | Dynamic backend lifecycle, preservation and archival. |
| Admin charts/report exports | Fixed | SQLite aggregates, visual charts, filters, and editable DOCX exports. |
| Real SMS/email delivery | Requires external service | Notifications remain explicitly simulated. |
| PDF output | Not implemented | Only DOCX is provided, per current working implementation. |

## F. Incorrect Logic Found

The audit corrected configured-fee-versus-actual-collection confusion, historical payment snapshot changes, payment-free service handling, duplicate payment/claim decisions, expired feed visibility, document type validation, staff self-processing, duplicate release attempts, queue transition races, and a staff view that could imply financial authority.

## G. 404 / Routing Problems

`confirm_permit_payment` was referenced by the Permit detail template but had no handler. The template was repaired and all `url_for` endpoint references are checked by regression test. Valid audited routes returned HTTP 200 in the browser audit; unknown routes retain the designed 404 response.

## H. Security / RBAC Findings

Server-side checks now restrict system-wide reports and chart endpoints to Administrators, payment recording to Administrators or explicitly authorized Staff, fee waivers to Administrators with a reason, program review/release to authorized non-owner personnel, and private program files to the owner or authorized operators. Residents cannot access other Residents’ program applications or payment receipts. Staff self-processing is rejected for permits and program applications. CSRF is checked on mutating routes. Uploaded filenames are discarded in favor of random opaque filenames; extension and matching content signature are required.

Remaining security limit: uploaded PDFs/images are signature-checked, not malware-scanned. Run malware scanning at the storage/host boundary before production use.

## I. Database Findings

The production SQLite file checked read-only: `integrity_check=ok`, zero foreign-key violations, 35 tables, and the new payment/program tables exist. The additive migration creates missing schema without deleting records. It does not convert legacy `payment_confirmed_at` flags into payment records because that would invent financial history. Review such legacy records manually.

SQLite foreign keys, WAL, busy timeout, and restart persistence were verified in an isolated test database. Query-specific indexes were added for request list ownership/date patterns, and the 5,000-record synthetic Permit query used `ix_permit_owner_date`.

## J. Code Cleanup

Shared typed requirement validation is used by permits and programs. Payment, announcement lifecycle, analytics, uploads, DOCX output, and program workflows are separated into focused services. Dead report-metrics code and temporary revision-edit scripts were removed. Documentation now points historical research material to the current README/audit report. No tables, columns, production data, or historical migration documentation were removed.

The removed report-metrics implementation was superseded by the shared analytics service and its exports; endpoint and export regression tests exercise the replacement. The removed temporary scripts were one-time editing utilities, not application imports or startup dependencies. Historical MariaDB material is retained as documentation; SQLite remains the runtime database.

## K. Performance Findings

Measurements use an isolated SQLite database with 5,000 synthetic Permit rows; they are not production benchmarks.

| Area | Median / result |
|---|---|
| Dashboard | 16.82 ms, 25 queries |
| Resident search front desk | 9.37 ms, 14 queries |
| Permit list (paginated) | 12.83 ms, 8 queries |
| Event list | 3.32 ms, 6 queries |
| Activity logs (paginated) | 3.58 ms, 4 queries |
| Notifications (paginated) | 3.58 ms, 5 queries |
| Permit analytics | 24.48 ms, 18 queries |
| Permit Word export | 1,495.51 ms, 116,901 bytes |

Charts render from the same aggregate data supplied to accessible HTML tables. Reports are moderately query-heavy because they intentionally produce multiple independent aggregates; full exports should be monitored on real data volumes.

These are post-change measurements only. No comparable pre-change benchmark was captured, so they do not establish a measured speedup. Pagination bounds list results; the ownership/date index avoids a full scan for the measured resident Permit query.

## L. Dashboard Results

Administrator: real summary metrics, compact analytics, active-announcement count, program/payment totals, and report charts were tested. Staff: request workload, missing requirements, ready-for-release, appointments, concerns, and walk-in counters derive from SQLite. Resident: personal requests, events, blotters, schedules, notifications, programs, acknowledgments, approved documents, feedback, and ownership were tested in scope.

## M. Feature Health Matrix

| Module | Status | Problems Found | Fixed | Remaining Risk |
|---|---|---|---|---|
| Authentication / RBAC | Fixed and Retested | Profile script error; route boundaries | Yes | No real external identity provider test |
| SQLite / migrations | Fixed and Retested | Missing new schema/indexes | Yes | Legacy payment evidence needs manual review |
| Permit / requirements / release | Fixed and Retested | Payment gate, document type and release race | Yes | Policy-specific release procedures need live review |
| Events / reservations | Working in Tested Scope | Concurrent overlap risk audited | Yes | SQLite remains single-instance oriented |
| Walk-in / queue | Fixed and Retested | Incorrect acknowledgment terminology/content | Yes | Live printer not tested |
| Payments | Fixed and Retested | No immutable payment records/RBAC | Yes | Manual cash only; no refunds/partial/additional charges |
| Scholarship / Ayuda | Fixed and Retested | Feature absent | Yes | Program policy and real beneficiary data need operational review |
| Announcements | Fixed and Retested | Scheduling/expiry/history absent | Yes | Lifecycle refresh occurs on backend access |
| Reports / DOCX | Fixed and Retested | Minimal counts, no filters/charts | Yes | Real Microsoft Word UI not available in audit environment |
| Uploads / privacy | Fixed and Retested | Type mismatch and rollback orphan risk | Yes | No malware scanner |
| Responsive UI / JS | Fixed and Retested | Profile null reference | Yes | Manual assistive-technology review remains useful |

## N. Weak Features

SQLite is appropriate for the configured single-service deployment but is sensitive to multi-instance/write-heavy scaling. The dynamic announcement lifecycle intentionally does not run a background scheduler; status is refreshed on backend access and active-feed filtering always applies immediately. Reports render multiple aggregates and Word charts, so large real data sets need monitoring. Private files remain local filesystem data and should move to managed private storage if usage grows.

## O. Failed / Untested Areas

No real SMS/email provider, hardware printer, production browser/device lab, external malware scanner, live payment terminal, or installed Microsoft Word application was available. Browser audit verified the Word download is a valid `.docx`; `python-docx` verified native text/tables in generated export tests.

## P. Regression Test Results

- 35 automated tests passed in 35.639 seconds in the final verification run.
- Isolated SQLite restart/integrity validation passed.
- 160 real Edge page checks across Administrator, Staff, Resident and widths 1440, 1024, 768, and 390 passed; zero JavaScript errors and zero horizontal-overflow detections.
- All 17 report types exported valid editable Word documents in tests.
- Concurrent payment, program claim, event reservation, and walk-in queue tests passed.
- Python source compilation and all Jinja template loading passed.

## Q. Remaining Risks

External notifications are simulated. Manual payments require trusted authorized staff and operational reconciliation. Legacy payment flags are not financial evidence. SQLite requires a persistent disk, a single service instance, backups, and appropriate file permissions. Production content policy, retention, and recipient eligibility rules remain Barangay decisions.

## R. Recommended Future Improvements

Configure approved SMS/email delivery, malware scanning, off-host encrypted private storage, production backup rotation/restore drills, and real-device/accessibility testing. Consider a scheduled background task only if policy requires announcement audit actions exactly at timestamp boundaries rather than on next access. Evaluate a multi-user database only if operating scale exceeds single-instance SQLite constraints.

## Required Final Checklist

Checked items refer to the tested scope described above, not exhaustive proof for every possible input. Evidence is in `barangay_system/tests/test_system.py`, `test_revision.py`, `validate_sqlite.py`, `browser_audit.py`, and `audit_inventory.py`, with generated browser/performance results in `barangay_system/audit-artifacts/`.

- [x] Project-wide code inspection completed.
- [x] All Flask routes reviewed; route inventory generated.
- [x] Broken links checked through endpoint validation and browser navigation.
- [x] Accidental 404s checked.
- [x] Authentication tested.
- [x] RBAC tested with direct URLs.
- [x] SQLite schema checked.
- [x] Database transactions checked, including concurrent submissions and rollback.
- [x] Resident Dashboard tested.
- [x] Staff Dashboard tested.
- [x] Admin Dashboard tested.
- [x] Permit workflow tested.
- [x] Event workflow tested.
- [x] Blotter workflow tested.
- [x] Walk-in workflow tested.
- [x] Dynamic Requirements tested.
- [x] Payments tested.
- [x] Queue tested.
- [x] Scheduling tested.
- [x] Release Counter tested.
- [x] Notifications tested within the simulated delivery implementation.
- [x] Scholarship tested.
- [x] Ayuda tested.
- [x] Announcement scheduling/expiration tested.
- [x] Reports tested.
- [x] Analytics totals validated against test fixtures.
- [x] Word exports tested for download, structure, native text/tables and chart content.
- [ ] PDFs tested: PDF upload validation is covered, but there is no application PDF export workflow to verify. Existing research PDFs are documentation artifacts.
- [x] File uploads tested.
- [x] Activity Logs tested.
- [x] Resident ownership tested.
- [x] Staff self-processing restrictions tested.
- [x] Loading states tested in browser interactions.
- [x] Error pages tested.
- [x] Responsive layout checked at four viewport widths.
- [x] Duplicate code reviewed.
- [x] Dead code reviewed.
- [x] Old MariaDB code reviewed; historical documentation retained.
- [x] Performance-sensitive areas tested with synthetic data.
- [x] Regression pass completed.
- [x] GitHub-sensitive file paths and ignore rules checked. No commit or push was performed; Git is unavailable in this environment, so tracked-file status was not verified.
- [x] Final audit report prepared.

Microsoft Word itself, a physical printer, and live SMS/email delivery remain untested. The regression run also emits existing datetime/SQLAlchemy deprecation warnings and file-handle cleanup warnings in upload/document tests; those warnings are not test failures and should be reviewed during test and dependency maintenance.
