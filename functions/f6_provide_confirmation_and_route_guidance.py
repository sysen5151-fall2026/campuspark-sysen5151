"""F.6 Provide Confirmation and Route Guidance.

ICOM on the first-level IDEF0:
    inputs    IO.8  Confirmed Reservation Record           from F.5
              IO.16 Route Guidance Data                    from F.3
    control   IO.17 Approved Parking Rules and Capacity    from F.1
    output    IO.9  Reservation Confirmation and Navigation Guidance  to X.F.1

Shapes:
    IO.9   {"reservation_id": str, "lot": str, "address": str, "start": int, "end": int,
            "guidance": str | None, "warning": str | None}
           guidance None plus a warning when route data are unavailable; the booking stands (SR.16)
           address is the booked pool's entry in IO.16 "addresses"; "unavailable" only when IO.16 has none
"""


def provide_confirmation_and_route_guidance(confirmed_record: dict, route_guidance_data: dict, *,
                                            approved_rules: dict) -> dict:
    """in: IO.8, IO.16. control: IO.17. out: IO.9."""
    raise NotImplementedError
