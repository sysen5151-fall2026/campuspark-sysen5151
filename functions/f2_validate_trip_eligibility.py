"""F.2 Validate Trip Eligibility.

ICOM on the first-level IDEF0:
    input     IO.1  Parking Request                        from X.F.1 Request Campus Parking
    control   IO.17 Approved Parking Rules and Capacity    from F.1
    outputs   IO.2  Identity and Permit Validation Request to X.F.3 Verify Identity and Permits
              IO.14 Trip Details                           to F.3
The permit system answers with IO.3, which governs F.3, F.4 and F.5. F.2 only asks.

Shapes:
    IO.1   {"driver_id": str, "destination": str, "arrival": "HH:MM", "hours": int}
    IO.2   {"driver_id": str}   only approved identity fields leave CampusPark (SR.13)
    IO.14  {"driver_id": str, "destination": str, "start": int, "end": int, "missing": list[str]}
           "missing" names every required trip fact that was absent or invalid

The body was added in Chapter 5; the signature and shapes above are unchanged.
"""

import re

_ARRIVAL = re.compile(r"([01][0-9]|2[0-3]):[0-5][0-9]")
_DAY_END = 24 * 60


def validate_trip_eligibility(parking_request: dict, *, approved_rules: dict) -> tuple:
    """in: IO.1. control: IO.17. out: (IO.2 or None, IO.14).

    IO.2 is None whenever IO.14["missing"] is not empty: no validation request is sent for an
    incomplete request.
    """
    # IO.17 holds no rule about trip facts, so the check below does not read approved_rules.
    request = parking_request if isinstance(parking_request, dict) else {}
    missing = []

    driver_id = request.get("driver_id")
    if not _is_text(driver_id):
        missing.append("driver_id")

    destination = request.get("destination")
    if not _is_text(destination):
        missing.append("destination")

    arrival = request.get("arrival")
    start = None
    if isinstance(arrival, str) and _ARRIVAL.fullmatch(arrival):
        start = int(arrival[:2]) * 60 + int(arrival[3:])
    else:
        missing.append("arrival")

    hours = request.get("hours")
    end = None
    if not (isinstance(hours, int) and not isinstance(hours, bool) and hours >= 1):
        missing.append("hours")
    elif start is not None:
        if start + hours * 60 > _DAY_END:
            missing.append("hours")        # the trip must end by midnight of the same day
        else:
            end = start + hours * 60

    trip = {"driver_id": driver_id if isinstance(driver_id, str) else "",
            "destination": destination.strip() if isinstance(destination, str) else "",
            "start": start, "end": end, "missing": missing}
    # Only the approved identity field leaves CampusPark, and only for a complete request (SR.13).
    validation = None if missing else {"driver_id": driver_id}
    return validation, trip


def _is_text(value):
    return isinstance(value, str) and bool(value.strip())
