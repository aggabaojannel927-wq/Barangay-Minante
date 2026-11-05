"""Consent-aware LGBTQIA+ profile updates and aggregate-only reports."""

from datetime import date, datetime, timedelta

from flask import current_app
from sqlalchemy import extract, func, or_

from models import (
    ResidentDemographicHistory,
    ResidentProfile,
    User,
    db,
    utcnow,
)
from services.revision import LOCAL_TIMEZONE, local_datetime


RESPONSE_LABELS = {
    "yes": "Yes — identifies as LGBTQIA+",
    "no": "No — does not identify as LGBTQIA+",
    "prefer_not_to_say": "Prefer not to say",
}
REPORT_RESPONSE_LABELS = {
    **RESPONSE_LABELS,
    "not_provided": "No recorded answer",
}
REPORT_RESPONSE_FILTERS = {"", *REPORT_RESPONSE_LABELS}


def submitted_response(form):
    """Return a validated answer and its separate consent checkbox state."""
    raw = (form.get("lgbtqia_identification") or "").strip()
    if raw and raw not in RESPONSE_LABELS:
        raise ValueError("Choose a valid LGBTQIA+ self-identification response.")
    return raw or None, form.get("lgbtqia_consent") == "1"


def apply_profile_response(profile, form, actor_id, source, *, clear_when_blank=False):
    """Apply only an explicit, validated, consented answer to a profile.

    Blank walk-in fields mean "no update". A blank answer on the resident's
    own profile can clear an existing answer. A new value requires explicit
    consent. Unchanged values do not produce duplicate history rows.
    """
    if "lgbtqia_identification" not in form:
        return False
    answer, consent = submitted_response(form)
    previous = profile.lgbtqia_identification
    if answer == previous:
        return False
    if answer is None and not clear_when_blank:
        return False
    if answer is not None and not consent:
        raise ValueError(
            "The resident's explicit consent is required to record this optional answer. "
            "Leave it blank if the resident does not wish to provide it."
        )

    timestamp = utcnow()
    event_type = "recorded" if previous is None and answer is not None else (
        "withdrawn" if answer is None else "updated"
    )
    profile.lgbtqia_identification = answer
    profile.lgbtqia_consent_at = timestamp if answer is not None else None
    profile.lgbtqia_updated_at = timestamp
    profile.lgbtqia_updated_by = actor_id
    db.session.add(
        ResidentDemographicHistory(
            resident_profile_id=profile.id,
            response=answer,
            event_type=event_type,
            source=source,
            consent_confirmed=answer is not None,
            changed_by=actor_id,
            recorded_at=timestamp,
        )
    )
    return True


def validate_report_filters(values):
    filters = {
        key: (values.get(key, "") or "").strip()
        for key in ("start", "end", "month", "year", "purok", "response")
    }
    if any(len(value) > 120 for value in filters.values()):
        raise ValueError("A report filter is too long.")
    for key in ("start", "end"):
        if filters[key]:
            try:
                parsed = date.fromisoformat(filters[key])
                if parsed.year < 1900 or parsed.year > 9998:
                    raise ValueError
            except ValueError:
                raise ValueError("Enter a valid report date.") from None
    if filters["start"] and filters["end"] and filters["start"] > filters["end"]:
        raise ValueError("The report end date must be on or after the start date.")
    if filters["year"] and (
        not filters["year"].isdigit()
        or not 1900 <= int(filters["year"]) <= 9998
    ):
        raise ValueError("Choose a valid report year.")
    if filters["month"] and (
        not filters["month"].isdigit()
        or not 1 <= int(filters["month"]) <= 12
    ):
        raise ValueError("Choose a valid report month.")
    if filters["response"] not in REPORT_RESPONSE_FILTERS:
        raise ValueError("Choose a valid demographic response filter.")
    if filters["start"] and filters["end"]:
        if (date.fromisoformat(filters["end"]) - date.fromisoformat(filters["start"])).days > 3660:
            raise ValueError("Choose a reporting date range of 10 years or less.")
    return filters


def _filtered_residents(filters):
    query = (
        db.session.query(ResidentProfile)
        .join(User, User.id == ResidentProfile.user_id)
        .filter(
            User.role == "resident",
            User.is_active.is_(True),
            ResidentProfile.approval_status == "Approved",
        )
    )
    if filters["start"]:
        query = query.filter(
            User.created_at >= local_datetime(filters["start"] + "T00:00:00")
        )
    if filters["end"]:
        day_after = date.fromisoformat(filters["end"]) + timedelta(days=1)
        query = query.filter(
            User.created_at < local_datetime(day_after.isoformat() + "T00:00:00")
        )
    local_created = func.datetime(User.created_at, "+8 hours")
    if filters["year"]:
        query = query.filter(extract("year", local_created) == int(filters["year"]))
    elif filters["month"]:
        # A month without a year means that month in the current Manila year.
        query = query.filter(
            extract("year", local_created) == datetime.now(LOCAL_TIMEZONE).year
        )
    if filters["month"]:
        query = query.filter(extract("month", local_created) == int(filters["month"]))
    if filters["purok"]:
        query = query.filter(ResidentProfile.purok_zone == filters["purok"])
    if filters["response"] == "not_provided":
        query = query.filter(
            or_(
                ResidentProfile.lgbtqia_identification.is_(None),
                ResidentProfile.lgbtqia_identification.notin_(RESPONSE_LABELS),
            )
        )
    elif filters["response"]:
        query = query.filter(
            ResidentProfile.lgbtqia_identification == filters["response"]
        )
    return query


def _activity_months(filters, now=None):
    local_now = (now or datetime.now(LOCAL_TIMEZONE)).astimezone(LOCAL_TIMEZONE)
    current_index = local_now.year * 12 + local_now.month - 1
    if filters["start"] or filters["end"]:
        start_date = date.fromisoformat(filters["start"]) if filters["start"] else None
        end_date = date.fromisoformat(filters["end"]) if filters["end"] else local_now.date()
        if start_date is None:
            start_index = end_date.year * 12 + end_date.month - 12
        else:
            start_index = start_date.year * 12 + start_date.month - 1
        end_index = end_date.year * 12 + end_date.month - 1
    elif filters["year"] and filters["month"]:
        start_index = int(filters["year"]) * 12 + int(filters["month"]) - 1
        end_index = start_index
    elif filters["year"]:
        start_index = int(filters["year"]) * 12
        end_index = start_index + 11
    elif filters["month"]:
        year = int(filters["year"]) if filters["year"] else local_now.year
        start_index = year * 12 + int(filters["month"]) - 1
        end_index = start_index
    else:
        start_index = current_index - 11
        end_index = current_index
    if end_index < start_index:
        return []
    if end_index - start_index > 119:
        start_index = end_index - 119
    return [divmod(index, 12) for index in range(start_index, end_index + 1)]


def _activity_period(months):
    if not months:
        return "No reporting months selected"
    first_year, first_month = months[0]
    last_year, last_month = months[-1]
    first = date(first_year, first_month + 1, 1).strftime("%b %Y")
    last = date(last_year, last_month + 1, 1).strftime("%b %Y")
    return first if first == last else f"{first} to {last}"


def _suppressed_rows(label, message):
    return [{
        "title": label,
        "kind": "table",
        "rows": [("Breakdown", message)],
        "note": "Breakdowns are suppressed when a category has fewer residents than the configured privacy threshold.",
    }]


def build_lgbtqia_report(raw_filters=None, now=None):
    """Return database-derived aggregates, with small cells suppressed."""
    filters = validate_report_filters(raw_filters or {})
    query = _filtered_residents(filters)
    total = int(query.with_entities(func.count(ResidentProfile.id)).scalar() or 0)
    grouped = query.with_entities(
        ResidentProfile.lgbtqia_identification,
        func.count(ResidentProfile.id),
    ).group_by(ResidentProfile.lgbtqia_identification).all()
    counts = {key: 0 for key in RESPONSE_LABELS}
    counts["not_provided"] = 0
    for response, count in grouped:
        bucket = response if response in RESPONSE_LABELS else "not_provided"
        counts[bucket] += int(count)

    threshold = max(2, int(current_app.config.get("LGBTQIA_REPORT_MIN_GROUP_SIZE", 5)))
    # A small filtered cohort is itself sensitive: suppress the population
    # total as well as all category values to prevent the filter from revealing
    # the size of a narrowly selected group.
    small_cell = (0 < total < threshold) or any(
        0 < count < threshold for count in counts.values()
    )
    recorded = sum(counts[key] for key in RESPONSE_LABELS)
    disclosed = counts["yes"] + counts["no"]
    nondisclosed = counts["prefer_not_to_say"] + counts["not_provided"]

    period_months = _activity_months(filters, now)
    activity = {(year, month): 0 for year, month in period_months}
    if period_months:
        first_year, first_month = period_months[0]
        last_year, last_month = period_months[-1]
        first_start = local_datetime(f"{first_year:04d}-{first_month + 1:02d}-01T00:00:00")
        next_index = last_year * 12 + last_month + 1
        next_year, next_month = divmod(next_index, 12)
        last_end = local_datetime(f"{next_year:04d}-{next_month + 1:02d}-01T00:00:00")
        response_events = (
            db.session.query(ResidentDemographicHistory)
            .join(ResidentProfile, ResidentProfile.id == ResidentDemographicHistory.resident_profile_id)
            .join(User, User.id == ResidentProfile.user_id)
            .filter(
                User.role == "resident",
                User.is_active.is_(True),
                ResidentProfile.approval_status == "Approved",
                ResidentDemographicHistory.response.isnot(None),
                ResidentDemographicHistory.event_type.in_(("recorded", "updated")),
                ResidentDemographicHistory.recorded_at >= first_start,
                ResidentDemographicHistory.recorded_at < last_end,
            )
        )
        if filters["purok"]:
            response_events = response_events.filter(
                ResidentProfile.purok_zone == filters["purok"]
            )
        if filters["response"] in RESPONSE_LABELS:
            response_events = response_events.filter(
                ResidentDemographicHistory.response == filters["response"]
            )
        if filters["response"] == "not_provided":
            response_events = response_events.filter(False)
        local_recorded = func.datetime(ResidentDemographicHistory.recorded_at, "+8 hours")
        year_expr = extract("year", local_recorded)
        month_expr = extract("month", local_recorded)
        for year, month, count in response_events.with_entities(
            year_expr, month_expr, func.count(ResidentDemographicHistory.id)
        ).group_by(year_expr, month_expr).all():
            key = (int(year), int(month) - 1)
            if key in activity:
                activity[key] = int(count)

    trend_small_cell = any(0 < count < threshold for count in activity.values())
    percentages = {
        "yes": round(counts["yes"] * 100 / total, 2) if total else 0,
        "no": round(counts["no"] * 100 / total, 2) if total else 0,
        "prefer_not_to_say": round(counts["prefer_not_to_say"] * 100 / total, 2) if total else 0,
        "not_provided": round(counts["not_provided"] * 100 / total, 2) if total else 0,
    }
    card_values = {
        "Total Registered Residents": "Suppressed" if small_cell else total,
        "Residents Identifying as LGBTQIA+": "Suppressed" if small_cell else counts["yes"],
        "Residents Not Identifying as LGBTQIA+": "Suppressed" if small_cell else counts["no"],
        "Residents Who Prefer Not to Disclose": "Suppressed" if small_cell else counts["prefer_not_to_say"],
        "Residents With No Recorded Answer": "Suppressed" if small_cell else counts["not_provided"],
    }
    sections = []
    if small_cell:
        note = (
            f"Category totals, rates, and charts are suppressed because at least one category has "
            f"fewer than {threshold} residents."
        )
        sections.extend(_suppressed_rows("Response Distribution", note))
        sections.extend(_suppressed_rows("Response Comparison", note))
        additional_rows = [
            ("Residents with a recorded demographic response", "Suppressed"),
            ("Residents who voluntarily disclosed", "Suppressed"),
            ("Residents who did not disclose", "Suppressed"),
        ]
        additional_note = note
    else:
        labels = list(REPORT_RESPONSE_LABELS.items())
        sections.extend([
            {
                "id": "lgbtqia-response-doughnut",
                "title": "Voluntary Response Distribution",
                "kind": "donut",
                "rows": [(REPORT_RESPONSE_LABELS[key], counts[key]) for key, _label in labels],
                "percentages": {REPORT_RESPONSE_LABELS[key]: percentages[key] for key, _label in labels},
                "note": "Counts are unique active, approved Resident profiles. No response is not treated as No.",
            },
            {
                "id": "lgbtqia-response-bar",
                "title": "Comparison of Recorded Categories",
                "kind": "bar",
                "rows": [(REPORT_RESPONSE_LABELS[key], counts[key]) for key, _label in labels],
                "note": "Aggregate totals only; individual profiles are never listed.",
            },
        ])
        additional_rows = [
            ("Residents with a recorded demographic response", recorded),
            ("Residents who voluntarily disclosed", f"{disclosed} ({percentages['yes'] + percentages['no']:.2f}%)"),
            ("Residents who did not disclose", f"{nondisclosed} ({percentages['prefer_not_to_say'] + percentages['not_provided']:.2f}%)"),
        ]
        additional_note = "Disclosure percentages use the filtered registered-resident count as the denominator. Prefer not to say and no recorded answer are grouped as not disclosed."

    if trend_small_cell:
        sections.extend(_suppressed_rows(
            "Monthly Response Recording Activity",
            f"Monthly activity is suppressed because at least one month has fewer than {threshold} response changes.",
        ))
    else:
        sections.append({
            "id": "lgbtqia-monthly-trend",
            "title": "Monthly Voluntary Response Recording Activity",
            "kind": "line",
            "rows": [
                [date(year, month + 1, 1).strftime("%b %Y"), count]
                for (year, month), count in activity.items()
            ],
            "note": "Counts first-time responses and changed answers recorded during the selected period. More recorded changes do not mean the LGBTQIA+ population increased.",
        })
    sections.append({
        "title": "Disclosure Statistics",
        "kind": "table",
        "rows": additional_rows,
        "note": additional_note,
    })

    return {
        "title": "LGBTQIA+ Community Demographic Report",
        "filters": filters,
        "cards": card_values,
        "sections": sections,
        "period": _activity_period(period_months),
        "population_period": "All-time" if not any(filters.values()) else "Selected resident registration filters",
        "threshold": threshold,
        "suppressed": small_cell,
        "trend_suppressed": trend_small_cell,
        "privacy_statement": (
            "Confidential aggregate report. It contains no resident names, contact details, addresses, "
            "or direct identifiers. Small demographic cells are suppressed. Use only for authorized "
            "barangay program planning and follow the approved privacy and retention policy."
        ),
    }


def lgbtqia_docx_report(report, generated_by):
    """Create an editable aggregate-only Word export with the same report data."""
    from io import BytesIO
    from docx import Document
    from docx.shared import Inches, Pt
    from services.analytics import chart_png
    from services.revision import local_display

    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)
    document.add_heading("Barangay Minante 1", level=0)
    document.add_heading(report["title"], level=1)
    document.add_paragraph(f"Generated: {local_display(utcnow())} (Asia/Manila)")
    document.add_paragraph(f"Generated by: {generated_by}")
    document.add_paragraph(f"Response activity period: {report['period']}")
    document.add_paragraph(f"Registered resident scope: {report['population_period']}")

    document.add_heading("Summary Statistics", level=2)
    summary = document.add_table(rows=1, cols=2)
    summary.style = "Light Shading Accent 1"
    summary.rows[0].cells[0].text = "Category / Metric"
    summary.rows[0].cells[1].text = "Value"
    for label, value in report["cards"].items():
        cells = summary.add_row().cells
        cells[0].text = str(label)
        cells[1].text = str(value)

    for item in report["sections"]:
        document.add_heading(item["title"], level=2)
        if item.get("note"):
            document.add_paragraph(item["note"])
        chart = chart_png(item)
        if chart:
            document.add_picture(chart, width=Inches(6.3))
        table = document.add_table(rows=1, cols=2)
        table.style = "Light Shading Accent 1"
        table.rows[0].cells[0].text = "Category / Metric"
        table.rows[0].cells[1].text = "Value"
        for label, value in item.get("rows", []):
            cells = table.add_row().cells
            cells[0].text = str(label)
            percentage = item.get("percentages", {}).get(label)
            cells[1].text = f"{value} ({percentage:.2f}%)" if percentage is not None else str(value)

    document.add_heading("Privacy Statement", level=2)
    document.add_paragraph(report["privacy_statement"])
    footer = section.footer.paragraphs[0]
    footer.text = "Barangay Minante 1 | Aggregate demographic report | Handle according to approved privacy policy"
    for paragraph in document.paragraphs:
        for run in paragraph.runs:
            run.font.name = "Arial"
            if paragraph.style.name == "Normal":
                run.font.size = Pt(9)
    output = BytesIO()
    document.save(output)
    output.seek(0)
    return output
