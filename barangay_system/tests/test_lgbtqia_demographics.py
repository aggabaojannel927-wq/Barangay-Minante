"""Voluntary demographic revision tests using the shared synthetic SQLite fixture."""

import unittest
from datetime import datetime, timedelta

import test_system as baseline
from app import app
from models import (
    ActivityLog,
    ResidentDemographicHistory,
    ResidentProfile,
    User,
    db,
    utcnow,
)
from sqlalchemy.exc import IntegrityError
from services.lgbtqia_demographics import build_lgbtqia_report
from services.revision import LOCAL_TIMEZONE, local_datetime


class LGBTQIADemographicTests(unittest.TestCase):
    setUp = baseline.SystemAcceptanceTests.setUp
    auth = baseline.SystemAcceptanceTests.auth
    clear_auth = baseline.SystemAcceptanceTests.clear_auth
    post = baseline.SystemAcceptanceTests.post
    registration_data = baseline.SystemAcceptanceTests.registration_data

    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    def _register(self, username, answer=None, consent=True):
        self.clear_auth()
        form = self.registration_data(username, f"{username}@test.local")
        if answer is not None:
            form["lgbtqia_identification"] = answer
        if consent:
            form["lgbtqia_consent"] = "1"
        response = self.post("/register", form)
        return response

    def _add_resident(self, index, response, purok="Purok Test", created_at=None):
        user = User(
            username=f"demo-{index}",
            role="resident",
            full_name=f"Private LGBTQIA Resident {index}",
            email=f"private-demo-{index}@test.local",
            contact_number=f"0917000{index:04d}",
            address=f"Private address {index}",
            is_active=True,
        )
        user.set_password("StrongPass123")
        if created_at:
            user.created_at = created_at
        db.session.add(user)
        db.session.flush()
        profile = ResidentProfile(
            user_id=user.id,
            approval_status="Approved",
            purok_zone=purok,
            lgbtqia_identification=response,
        )
        db.session.add(profile)
        db.session.flush()
        if response:
            db.session.add(
                ResidentDemographicHistory(
                    resident_profile_id=profile.id,
                    response=response,
                    event_type="recorded",
                    source="registration",
                    consent_confirmed=True,
                    changed_by=self.ids["admin"],
                    recorded_at=utcnow(),
                )
            )
        return user.id

    def test_registration_accepts_each_optional_answer_and_skips_without_classifying(self):
        for username, answer in (
            ("demo_yes", "yes"),
            ("demo_no", "no"),
            ("demo_prefer", "prefer_not_to_say"),
            ("demo_skip", None),
        ):
            response = self._register(username, answer)
            self.assertEqual(response.status_code, 302, username)
            with app.app_context():
                profile = User.query.filter_by(username=username).one().resident_profile
                self.assertEqual(profile.lgbtqia_identification, answer)
                self.assertEqual(
                    ResidentDemographicHistory.query.filter_by(
                        resident_profile_id=profile.id
                    ).count(),
                    1 if answer else 0,
                )

        denied = self._register("demo_no_consent", "yes", consent=False)
        self.assertEqual(denied.status_code, 200)
        self.assertIn(b"voluntary consent", denied.data.lower())
        with app.app_context():
            self.assertIsNone(User.query.filter_by(username="demo_no_consent").first())
            log_text = " ".join(
                row.details or "" for row in ActivityLog.query.all()
            ).lower()
            self.assertNotIn("yes", log_text)

    def test_walkin_records_voluntary_answers_on_the_correct_profile_without_duplicates(self):
        self.auth("staff")
        front_desk = self.client.get(f"/front-desk?resident_id={self.ids['resident']}")
        self.assertEqual(front_desk.status_code, 200)
        form_start = front_desk.data.index(b'id="assistedRequestForm"')
        field_position = front_desk.data.index(b'id="walkinRequestLgbtqia"')
        form_end = front_desk.data.index(b"</form>", form_start)
        self.assertLess(form_start, field_position)
        self.assertLess(field_position, form_end)
        resident_form = {
            "full_name": "Offline Demographic Resident",
            "address": "22 Sample Street",
            "purok_zone": "Purok 4",
            "privacy_consent": "1",
            "lgbtqia_identification": "yes",
            "lgbtqia_consent": "1",
        }
        created = self.post("/front-desk/residents/new", resident_form)
        self.assertEqual(created.status_code, 302)
        with app.app_context():
            resident = User.query.filter_by(
                full_name="Offline Demographic Resident"
            ).one()
            resident_id = resident.id
            profile_id = resident.resident_profile.id
            self.assertEqual(resident.resident_profile.lgbtqia_identification, "yes")
            self.assertEqual(
                ResidentDemographicHistory.query.filter_by(
                    resident_profile_id=profile_id
                ).count(),
                1,
            )

        # An existing profile can be updated through assisted intake. Repeating
        # the same answer must not create a duplicate demographic history row.
        request_data = {
            "resident_id": resident_id,
            "service_kind": "permit",
            "permit_type_id": self.ids["permit_type"],
            "purpose": "Paper request",
            "lgbtqia_identification": "yes",
            "lgbtqia_consent": "1",
        }
        self.post("/front-desk/requests", request_data)
        with app.app_context():
            self.assertEqual(
                User.query.filter_by(full_name="Offline Demographic Resident").count(),
                1,
            )
            self.assertEqual(
                ResidentDemographicHistory.query.filter_by(
                    resident_profile_id=profile_id
                ).count(),
                1,
            )

    def test_resident_can_update_or_clear_their_own_answer_and_database_rejects_invalid_values(self):
        self.auth("resident")
        updated = self.post(
            "/profile",
            {
                "full_name": "Resident One",
                "email": "resident@test.local",
                "contact_number": "09171234567",
                "lgbtqia_identification": "no",
                "lgbtqia_consent": "1",
            },
        )
        self.assertEqual(updated.status_code, 200)
        with app.app_context():
            profile = db.session.get(User, self.ids["resident"]).resident_profile
            self.assertEqual(profile.lgbtqia_identification, "no")
            self.assertEqual(
                ResidentDemographicHistory.query.filter_by(
                    resident_profile_id=profile.id
                ).count(),
                1,
            )
            profile.lgbtqia_identification = "unclassified"
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()

        self.auth("resident")
        cleared = self.post(
            "/profile",
            {
                "full_name": "Resident One",
                "email": "resident@test.local",
                "contact_number": "09171234567",
                "lgbtqia_identification": "",
            },
        )
        self.assertEqual(cleared.status_code, 200)
        with app.app_context():
            profile = db.session.get(User, self.ids["resident"]).resident_profile
            self.assertIsNone(profile.lgbtqia_identification)
            self.assertEqual(
                ResidentDemographicHistory.query.filter_by(
                    resident_profile_id=profile.id
                ).count(),
                2,
            )

    def test_staff_and_residents_cannot_access_aggregate_or_other_profile_data(self):
        with app.app_context():
            profile = db.session.get(User, self.ids["resident"]).resident_profile
            profile.lgbtqia_identification = "prefer_not_to_say"
            db.session.commit()

        self.auth("staff")
        self.assertEqual(self.client.get("/reports").status_code, 403)
        self.assertEqual(self.post("/reports/export/docx").status_code, 403)
        self.assertEqual(self.client.get(f"/users/{self.ids['resident']}").status_code, 403)
        front_desk = self.client.get("/front-desk")
        self.assertEqual(front_desk.status_code, 200)
        self.assertNotIn(b'data-current="prefer_not_to_say"', front_desk.data)
        self.assertEqual(
            self.client.get(
                f"/front-desk/residents/{self.ids['resident']}/information"
            ).status_code,
            200,
        )

        self.auth("other")
        self.assertEqual(self.client.get("/reports").status_code, 403)
        self.assertEqual(self.post("/reports/export/pdf").status_code, 403)
        self.assertEqual(self.client.get(f"/users/{self.ids['resident']}").status_code, 403)
        own_profile = self.client.get("/profile")
        self.assertEqual(own_profile.status_code, 200)
        self.assertNotIn(b'data-current="prefer_not_to_say"', own_profile.data)

        self.auth("admin")
        review = self.client.get(f"/users/{self.ids['resident']}")
        self.assertEqual(review.status_code, 200)
        self.assertIn(b"prefer_not_to_say", review.data)
        changed = self.post(
            f"/users/{self.ids['resident']}/lgbtqia",
            {"lgbtqia_identification": "yes", "lgbtqia_consent": "1"},
        )
        self.assertEqual(changed.status_code, 302)
        with app.app_context():
            self.assertEqual(
                db.session.get(User, self.ids["resident"])
                .resident_profile.lgbtqia_identification,
                "yes",
            )
            sensitive_logs = ActivityLog.query.filter_by(
                action="SENSITIVE_DEMOGRAPHIC_PROFILE_VIEWED"
            ).all()
            self.assertTrue(sensitive_logs)
            self.assertTrue(
                all("prefer_not_to_say" not in (row.details or "") for row in sensitive_logs)
            )
            changed_logs = ActivityLog.query.filter_by(
                action="LGBTQIA_RESPONSE_ADMIN_UPDATED"
            ).all()
            self.assertEqual(len(changed_logs), 1)
            self.assertNotIn("yes", changed_logs[0].details.lower())

    def test_aggregate_filters_charts_privacy_suppression_and_exports(self):
        created_at = local_datetime(
            datetime.now(LOCAL_TIMEZONE).date().isoformat() + "T12:00:00"
        )
        with app.app_context():
            index = 0
            for answer in ("yes", "no", "prefer_not_to_say", None):
                for _ in range(5):
                    self._add_resident(index, answer, created_at=created_at)
                    index += 1
            # A single person in a narrowly selected Purok is hidden completely.
            self._add_resident(index, "yes", purok="Small Purok", created_at=created_at)
            db.session.commit()

            report = build_lgbtqia_report({})
            self.assertEqual(report["cards"]["Residents Identifying as LGBTQIA+"], 6)
            self.assertEqual(report["cards"]["Residents Not Identifying as LGBTQIA+"], 5)
            self.assertEqual(report["cards"]["Residents Who Prefer Not to Disclose"], 5)
            self.assertEqual(report["cards"]["Residents With No Recorded Answer"], 7)
            self.assertTrue(any(section.get("kind") == "donut" for section in report["sections"]))
            self.assertTrue(any(section.get("kind") == "bar" for section in report["sections"]))
            self.assertTrue(any(section.get("kind") == "line" for section in report["sections"]))

            filtered = build_lgbtqia_report({"purok": "Purok Test", "response": "yes"})
            self.assertEqual(filtered["cards"]["Total Registered Residents"], 5)
            self.assertEqual(filtered["cards"]["Residents Identifying as LGBTQIA+"], 5)
            narrow = build_lgbtqia_report({"purok": "Small Purok", "response": "yes"})
            self.assertTrue(narrow["suppressed"])
            self.assertEqual(narrow["cards"]["Total Registered Residents"], "Suppressed")
            self.assertTrue(
                all(
                    value == "Suppressed"
                    for label, value in narrow["cards"].items()
                    if label != "Total Registered Residents" or narrow["suppressed"]
                )
            )

        self.auth("admin")
        page = self.post(
            "/reports",
            {"purok": "Purok Test", "response": "yes", "month": str(datetime.now(LOCAL_TIMEZONE).month),
             "year": str(datetime.now(LOCAL_TIMEZONE).year)},
        )
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"LGBTQIA+ Community Demographic Report", page.data)
        self.assertNotIn(b"Private LGBTQIA Resident", page.data)

        docx = self.post(
            "/reports/export/docx", {"purok": "Purok Test", "response": "yes"}
        )
        self.assertEqual(docx.status_code, 200)
        self.assertEqual(
            docx.mimetype,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        xml = baseline.SystemAcceptanceTests.docx_xml(docx)
        self.assertIn("LGBTQIA+ Community Demographic Report", xml)
        self.assertNotIn("Private LGBTQIA Resident", xml)
        self.assertNotIn("0917000", xml)
        self.assertNotIn("Private address", xml)

        pdf = self.post("/reports/export/pdf", {"purok": "Purok Test", "response": "yes"})
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.data.startswith(b"%PDF-"))
        pdf_text = baseline.SystemAcceptanceTests.pdf_text(pdf)
        self.assertIn("LGBTQIA+ Community Demographic Report", pdf_text)
        self.assertNotIn("Private LGBTQIA Resident", pdf_text)
        invalid = self.post("/reports/export/docx", {"response": "unrecognized"})
        self.assertEqual(invalid.status_code, 302)
        self.assertTrue(invalid.headers["Location"].endswith("/reports"))


if __name__ == "__main__":
    unittest.main()
