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
"""


def validate_trip_eligibility(parking_request: dict, *, approved_rules: dict) -> tuple:
    """in: IO.1. control: IO.17. out: (IO.2 or None, IO.14).

    IO.2 is None whenever IO.14["missing"] is not empty: no validation request is sent for an
    incomplete request.
    """
    raise NotImplementedError
