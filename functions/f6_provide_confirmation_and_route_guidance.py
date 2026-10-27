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

The body was added in Chapter 5; the signature and shapes above are unchanged.
"""


def provide_confirmation_and_route_guidance(confirmed_record: dict, route_guidance_data: dict, *,
                                            approved_rules: dict) -> dict:
    """in: IO.8, IO.16. control: IO.17. out: IO.9."""
    pool_id = confirmed_record.get("pool_id")
    pools = approved_rules.get("pools") if isinstance(approved_rules, dict) else None
    rule = pools.get(pool_id) if isinstance(pools, dict) else None
    lot = rule["name"] if isinstance(rule, dict) and _is_text(rule.get("name")) else pool_id

    # Guidance comes only from the IO.16 kept since the search; there is no second lookup (1.4.1.10).
    route_data = route_guidance_data if isinstance(route_guidance_data, dict) else {}
    addresses = route_data.get("addresses") if isinstance(route_data.get("addresses"), dict) else {}
    routes = route_data.get("routes") if isinstance(route_data.get("routes"), dict) else {}
    address = addresses.get(pool_id) if _is_text(addresses.get(pool_id)) else "unavailable"
    route = routes.get(pool_id) if route_data.get("status") == "ok" else None

    if _is_text(route):
        guidance, warning = route, None
    else:
        # The booking stands whatever happened to the route data (SR.16).
        guidance = None
        warning = ("Route guidance is unavailable for %s. Your reservation %s is confirmed and "
                   "kept; use the lot address to find it." % (lot, confirmed_record.get(
                       "reservation_id")))
    return {"reservation_id": confirmed_record.get("reservation_id"), "lot": lot,
            "address": address, "start": confirmed_record.get("start"),
            "end": confirmed_record.get("end"), "guidance": guidance, "warning": warning}


def _is_text(value):
    return isinstance(value, str) and bool(value.strip())
