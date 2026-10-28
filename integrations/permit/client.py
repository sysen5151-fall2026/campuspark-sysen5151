"""Campus Identity & Permit System.

Outside our boundary, we only read from it. Real access still has to go
through Campus IT (assumption A2 in the report), so for now this returns
fixture data.
"""

# Three permit types, enough to show that eligibility actually filters.
FIXTURE_PROFILES = {
    "student01": {"driver_id": "student01", "name": "Student driver", "permit": "student"},
    "staff01": {"driver_id": "staff01", "name": "Staff driver", "permit": "staff"},
    "visitor01": {"driver_id": "visitor01", "name": "Visitor", "permit": "visitor"},
}


def validate(driver_id):
    """Return the driver's permit profile, or None if we can't confirm one.

    UC.1.3. The real call will be a request to the permit system.

    A blank or unknown ID returns None. It used to fall back to the student
    profile, which handed permit rights to someone we hadn't identified.
    SR.2 and SR.15 both say unknown rights can't support a booking.
    """
    if not driver_id or not driver_id.strip():
        return None
    return FIXTURE_PROFILES.get(driver_id.strip().lower())


def identity_and_permit_eligibility(validation_request):
    """IO.2 in, IO.3 out (UC.1.2, UC.1.3).

    Only the driver ID is sent. An ID the fixture cannot confirm comes back "unknown", which F.3,
    F.4 and F.5 all treat as no permission (SR.15).
    """
    driver_id = (validation_request or {}).get("driver_id")
    profile = validate(driver_id)
    if profile is None:
        return {"driver_id": driver_id, "status": "unknown", "permit": None}
    return {"driver_id": driver_id, "status": "eligible", "permit": profile["permit"]}
