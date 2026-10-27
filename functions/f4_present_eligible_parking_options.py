"""F.4 Present Eligible Parking Options.

ICOM on the first-level IDEF0:
    input     IO.15 Candidate Parking Data                 from F.3
    controls  IO.3  Identity and Permit Eligibility        from X.F.3
              IO.17 Approved Parking Rules and Capacity    from F.1
    output    IO.6  Eligible Parking Options               to X.F.1
Finding while writing this signature: "remaining capacity" needs the places already held, and no
flow on the first-level IDEF0 brings them to F.4. The signature takes IO.18 Reservation Records as
a second input, and the model is being corrected to match (F.4 receives IO.18). See
docs/prompt-log.md, Chapter 4 entry.

Shapes:
    IO.18  list[IO.8]   saved reservations, see F.5
    IO.6   {"status": "OPTIONS_AVAILABLE" | "NO_OPTIONS", "reason": str | None,
            "options": list[{"pool_id": str, "name": str, "walk_minutes": int | None,
            "remaining": int, "capacity": int, "facts": list[str]}]}
           "facts" are the rule and trip facts used to select the option (SR.3)

The body was added in Chapter 5; the signature and shapes above are unchanged.
"""

_DAY_END = 24 * 60


def present_eligible_parking_options(candidate_parking_data: dict, reservation_records: list, *,
                                     eligibility: dict, approved_rules: dict) -> dict:
    """in: IO.15, IO.18. controls: IO.3, IO.17. out: IO.6."""
    candidates = candidate_parking_data if isinstance(candidate_parking_data, dict) else {}
    trip = candidates.get("trip") if isinstance(candidates.get("trip"), dict) else {}

    problem = _eligibility_problem(trip, eligibility)
    if problem is not None:
        return _no_options(problem)
    start, end = trip.get("start"), trip.get("end")
    if trip.get("missing") or not _is_window(start, end):
        return _no_options("the trip details are incomplete, so no option can be checked")
    pools = approved_rules.get("pools") if isinstance(approved_rules, dict) else None
    if not isinstance(pools, dict):
        return _no_options("the approved parking rules are unavailable")

    permit = eligibility["permit"]
    window = "%s-%s" % (_hhmm(start), _hhmm(end))
    options, excluded, seen = [], {}, set()
    for lot in candidates.get("lots") or []:
        pool_id = lot.get("pool_id") if isinstance(lot, dict) else None
        if pool_id in seen:
            continue
        seen.add(pool_id)
        rule = pools.get(pool_id) if isinstance(pool_id, str) else None
        if not isinstance(rule, dict):
            _count(excluded, "not in the approved rules")
            continue
        permits = rule.get("permits") or []
        if permit not in permits:
            _count(excluded, "permit %s not accepted" % permit)
            continue
        if any(_overlaps(start, end, c) for c in rule.get("closures") or []):
            _count(excluded, "closed during %s" % window)
            continue
        capacity = rule.get("capacity")
        if not _is_int(capacity):
            _count(excluded, "no approved capacity")
            continue
        remaining = capacity - _peak_held(reservation_records, pool_id, start, end)
        if remaining < 1:
            _count(excluded, "full during %s" % window)
            continue
        walk = lot.get("walk_minutes")
        options.append({
            "pool_id": pool_id,
            "name": rule.get("name") or lot.get("name") or pool_id,
            "walk_minutes": walk,
            "remaining": remaining,
            "capacity": capacity,
            "facts": [
                "Permit rule: %s accepts %s; your permit is %s" % (pool_id, ", ".join(permits),
                                                                   permit),
                "Capacity: %d of %d places free for the whole of %s" % (remaining, capacity,
                                                                        window),
                "No closure during %s" % window,
                "Trip: %s, %s" % (trip.get("destination"), window),
                ("Walking estimate: about %d min" % walk) if walk is not None
                else "Walking estimate unavailable",
                "Approved rules version %s" % approved_rules.get("version"),
            ],
        })

    if options:
        return {"status": "OPTIONS_AVAILABLE", "reason": None, "options": options}
    if not seen:
        return _no_options("no parking lots were found for this trip")
    return _no_options("no lot fits this trip: " + "; ".join(
        "%s (%d)" % (why, n) for why, n in excluded.items()))


def _eligibility_problem(trip, eligibility):
    """Why the driver's eligibility does not allow options, or None when it does."""
    if not isinstance(eligibility, dict):
        return "the driver's identity and permit eligibility is missing"
    if eligibility.get("status") != "eligible":
        return "the driver's eligibility is not confirmed (status: %s)" % eligibility.get("status")
    if eligibility.get("driver_id") != trip.get("driver_id"):
        return "the eligibility answer is for a different driver than the trip"
    if not (isinstance(eligibility.get("permit"), str) and eligibility["permit"].strip()):
        return "the driver's permit is missing from the eligibility answer"
    return None


def _no_options(reason):
    return {"status": "NO_OPTIONS", "reason": reason, "options": []}


def _count(tally, why):
    tally[why] = tally.get(why, 0) + 1


def _peak_held(records, pool_id, start, end):
    """Most places held at once in the pool during [start, end), from confirmed reservations."""
    events = []
    for record in records or []:
        if not (isinstance(record, dict) and record.get("pool_id") == pool_id
                and record.get("status") == "confirmed"
                and _is_int(record.get("start")) and _is_int(record.get("end"))):
            continue
        held_from, held_to = max(record["start"], start), min(record["end"], end)
        if held_from < held_to:
            events.append((held_from, 1))
            events.append((held_to, -1))
    # At equal times -1 sorts first: a place freed at t is free for a period starting at t.
    events.sort()
    held = peak = 0
    for _, step in events:
        held += step
        peak = max(peak, held)
    return peak


def _overlaps(start, end, window):
    """[start, end) overlaps the half-open window."""
    return (isinstance(window, dict) and _is_int(window.get("start")) and _is_int(window.get("end"))
            and start < window["end"] and window["start"] < end)


def _is_window(start, end):
    return _is_int(start) and _is_int(end) and 0 <= start < end <= _DAY_END


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _hhmm(minutes):
    return "%02d:%02d" % divmod(minutes, 60)
