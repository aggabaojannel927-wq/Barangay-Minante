# Resident account registration: family and disability information

The existing `/register` form retains personal, residency, emergency-contact,
account, identification, consent, and approval requirements. It now asks whether
the applicant is the head of the family. Yes reveals repeatable family entries
with full name, date of birth, and relationship. Unsaved entries can be removed.
Family members are linked to the applicant's resident profile, not given accounts.

Disability answers are Yes, No, or Prefer not to say. Yes optionally records a
type and an optional description for Other. No and Prefer not to say discard any
submitted type/description. Non-disclosure remains unknown in population reports;
it is never counted as No. Family members without resident accounts are excluded
from population totals.

## Storage and migration

No new permanent tables are introduced:

| Existing table | Changes |
| --- | --- |
| `resident_profiles` | Add `disability_declined`, default false; reuse `is_household_head`, nullable `has_disability`, `disability_type`, and `disability_other`. |
| `resident_family_members` | Add nullable `date_of_birth` and `relationship`; relax age/gender NOT NULL so uncollected gender is not invented. DOB-based entries derive age at save time. Existing age/gender entries remain supported. |

`head_profile_id` links each member to the correct family head. Existing household
links are reused only when unambiguous; registration never joins an arbitrary
household based on a user-supplied household number.

The idempotent SQLite migration copies all family-member columns and records
inside a savepoint, checks row counts, and replaces that leaf table to relax its
old constraints. It restores ORM indexes and retains unique keys and foreign
keys. Unexpected additional columns cause migration to stop instead of discarding
them. Existing users, residents, family members, and service records are retained.

Restart using `./run.ps1` from the project root to apply the migration before the
app starts. If hosting imports the Flask application instead of running `app.py`,
run the existing migration command from `barangay_system` before starting workers:

```powershell
..\.venv\Scripts\python.exe -m flask --app app init-db
```

## Validation and confidentiality

- Validate head/disability answers and allowed disability types server-side.
- Require each submitted DOB-based member's name, valid birthdate (not future;
  age 0–120), and relationship; limit names to 150 and relationships to 80 characters.
- Limit family entries to 50 and optional disability descriptions to 300 characters.
- Reject duplicate normalized name/birthdate pairs and adding the applicant as
  their own family member. Validate ownership of saved IDs during staff edits.
- Save the account, profile, members, and audit entries in one transaction.
- Preserve existing members when omitted or when Head of Family changes to No.
- Use existing admin/staff permissions for family details and editing; residents
  cannot open another resident's confidential details. Registration and admin
  review responses use `private, no-store` caching.
- Keep sensitive names, disability details, and SQL parameter dumps out of the
  registration audit/error messages. Reports show aggregate counts only.
- Keep CSRF, private ID uploads, password hashing, verification, approval, and
  login gating in place. Pending residents cannot log in before approval.

## Files changed

All paths below are relative to `barangay_system`, except this document:

| File | Purpose |
| --- | --- |
| `app.py` | Validate and save registration family/disability data; protect caching and error logging. |
| `models.py` | Extend the existing resident/family models. |
| `migration.py` | Add fields and safely upgrade legacy family constraints. |
| `services/resident_family.py` | Reuse validation/persistence for DOB-based registration and existing staff entries. |
| `templates/register.html` | Integrate the family/disability section into the current registration form. |
| `templates/_resident_family_fields.html` | Shared conditional questions and fields. |
| `templates/_family_member_row.html` | Shared repeatable member row; registration uses DOB/relationship. |
| `static/js/resident-family.js` | Keep conditional controls synchronized; disability type is optional. |
| `templates/resident_information.html` | Display saved DOB/relationship and non-disclosure; preserve editing. |
| `templates/user_review.html` | Show family and disability information to authorized administrators. |
| `templates/privacy_notice.html` | Explain family collection and optional disability disclosure. |
| `tests/test_resident_family.py` | Remove the obsolete unchanged-registration hash assertion; retain the permit-form protection check. |
| `tests/test_registration_family.py` | Registration, validation, access control, staff editing, reports, approval/login, and legacy migration tests. |
| `tests/browser_registration_family.py` | Browser registration, repeatable fields, responsive layout, and login test. |
| `documentation/REGISTRATION_FAMILY_DISABILITY.md` (project root) | Implementation and testing notes. |

## Verification

From `barangay_system`:

```powershell
..\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
..\.venv\Scripts\python.exe tests/browser_registration_family.py
..\.venv\Scripts\python.exe tests/browser_resident_family.py
```

The browser scripts use the installed Microsoft Edge executable. Automated tests
use isolated temporary SQLite databases and test uploads, not live resident data.
Validation completed: **82 automated tests passed**, and both browser scripts
passed, including responsive widths of 1440, 768, and 390 pixels with no JavaScript
errors. Existing datetime/SQLAlchemy deprecation warnings and a pre-existing
test-file ResourceWarning remain; there were no test failures.
Legacy migration tests preserve every existing column value, check foreign keys,
run the upgrade twice, and then register DOB-based members successfully.

For manual testing:

1. Open **Create resident account**. Complete existing fields, choose Head of
   Family **Yes**, add two members, add/remove an unsaved third member, and submit.
2. Try disability **Yes** with a type, **Yes** without a type, **Other** with/without
   description, **No**, and **Prefer not to say** using different test accounts.
3. Review each account as Administrator. Confirm saved family DOBs/relationships
   and disability information. Pending accounts must remain unable to log in.
4. Verify ID and address, approve through the existing workflow, then log in using
   the new resident credentials. No family-member accounts should exist.
5. As staff, open the resident's **Family and Disability Information**. Save an
   edit twice: existing member IDs and DOBs/relationships must persist without
   duplicates. Head of Family **No** hides entries without deleting saved members.
6. Submit duplicate members, a future birthdate, or a missing relationship. The
   page must display a validation error and create no partial account/member data.
7. At desktop/tablet/mobile widths, check layout and conditional sections. Confirm
   residents cannot open another resident's admin/staff family details.
