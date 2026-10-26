"""F.5 Recheck and Record Reservation.

ICOM on the first-level IDEF0:
    input     IO.7  Reservation Request                    from X.F.1
    controls  IO.3  Identity and Permit Eligibility        from X.F.3
              IO.17 Approved Parking Rules and Capacity    from F.1
    outputs   IO.8  Confirmed Reservation Record           to F.6
              IO.13 Booking Refusal Notice                 to X.F.1
              IO.18 Reservation Records                    to F.7 (and F.4, see the F.4 note)
Mechanism: none on the first-level IDEF0 yet. Saved reservations live in an injected store.

Shapes:
    IO.7   {"request_id": str, "driver_id": str, "pool_id": str, "start": int, "end": int}
    IO.8   {"reservation_id": str, "request_id": str, "driver_id": str, "pool_id": str,
            "start": int, "end": int, "status": "confirmed"}
    IO.13  {"reason": "missing_data" | "not_eligible" | "closed" | "pool_full", "message": str}
    IO.18  list[IO.8]

The body was added in Chapter 5; the signatures and shapes above are unchanged.
"""

import copy

_DAY_END = 24 * 60


class ReservationStore:
    """Saved reservations. Each request_id adds at most one commitment (SR.4)."""

    def __init__(self):
        self._records = []
        self._by_request_id = {}
        self._next_number = 1

    def all(self) -> list:
        """Every saved reservation (IO.18)."""
        return copy.deepcopy(self._records)

    def saved_for(self, request_id):
        """The saved reservation for this request_id, or None."""
        record = self._by_request_id.get(request_id)
        return copy.deepcopy(record) if record is not None else None

    def save(self, request):
        """Save a confirmed reservation for the request and return it (IO.8)."""
        record = {"reservation_id": "RES-%05d" % self._next_number,
                  "request_id": request["request_id"], "driver_id": request["driver_id"],
                  "pool_id": request["pool_id"], "start": request["start"],
                  "end": request["end"], "status": "confirmed"}
        self._next_number += 1
        self._records.append(record)
        self._by_request_id[record["request_id"]] = record
        return copy.deepcopy(record)


def recheck_and_record_reservation(reservation_request: dict, *, eligibility: dict,
                                   approved_rules: dict, reservation_store: ReservationStore) -> tuple:
    """in: IO.7. controls: IO.3, IO.17. mechanism: reservation_store.
    out: (IO.8 or None, IO.13 or None, IO.18). Exactly one of IO.8 and IO.13 is not None.
    """
    request = reservation_request if isinstance(reservation_request, dict) else {}

    # A request_id already saved returns that booking and adds no second commitment (SR.4).
    if _is_text(request.get("request_id")):
        saved = reservation_store.saved_for(request["request_id"])
        if saved is not None:
            return saved, None, reservation_store.all()

    refusal = _recheck(request, eligibility, approved_rules, reservation_store)
    if refusal is not None:
        return None, refusal, reservation_store.all()
    record = reservation_store.save(request)
    return record, None, reservation_store.all()


def _recheck(request, eligibility, approved_rules, store):
    """The refusal (IO.13) for this request, or None when it can be booked for the whole period."""
    missing = [field for field in ("request_id", "driver_id", "pool_id")
               if not _is_text(request.get(field))]
    start, end = request.get("start"), request.get("end")
    if not (_is_int(start) and 0 <= start < _DAY_END):
        missing.append("start")
    if not (_is_int(end) and end <= _DAY_END and (not _is_int(start) or end > start)):
        missing.append("end")
    if missing:
        return _refuse("missing_data", "The booking request is missing or has an invalid %s."
                       % ", ".join(missing))

    status = eligibility.get("status") if isinstance(eligibility, dict) else None
    if status in ("invalid", "unknown"):
        return _refuse("not_eligible", "The permit system did not confirm this driver's "
                       "eligibility (status: %s), so the booking was not made." % status)
    if status != "eligible":
        return _refuse("missing_data", "The identity and permit check gave no usable answer "
                       "(status: %s), so the booking was not made." % status)
    if eligibility.get("driver_id") != request["driver_id"]:
        return _refuse("not_eligible", "The eligibility answer is for a different driver, so "
                       "the booking was not made.")
    permit = eligibility.get("permit")
    if not _is_text(permit):
        return _refuse("missing_data", "The eligibility answer has no permit, so the permit rule "
                       "could not be checked and the booking was not made.")

    pool_id = request["pool_id"]
    pools = approved_rules.get("pools") if isinstance(approved_rules, dict) else None
    rule = pools.get(pool_id) if isinstance(pools, dict) else None
    capacity = rule.get("capacity") if isinstance(rule, dict) else None
    if not _is_int(capacity):
        return _refuse("missing_data", "There are no approved rules or capacity for pool %s, so "
                       "the booking was not made." % pool_id)
    if permit not in (rule.get("permits") or []):
        return _refuse("not_eligible", "Permit %s is not accepted in pool %s." % (permit, pool_id))
    for closure in rule.get("closures") or []:
        if _overlaps(start, end, closure):
            return _refuse("closed", "Pool %s is closed %s-%s, which falls inside the booked "
                           "period %s-%s." % (pool_id, _hhmm(closure["start"]),
                                               _hhmm(closure["end"]), _hhmm(start), _hhmm(end)))
    if _peak_held(store.all(), pool_id, start, end) >= capacity:
        return _refuse("pool_full", "Pool %s has no free place for the whole period %s-%s."
                       % (pool_id, _hhmm(start), _hhmm(end)))
    return None


def _refuse(reason, message):
    return {"reason": reason, "message": message}


def _peak_held(records, pool_id, start, end):
    """Most places held at once in the pool during [start, end), from confirmed reservations."""
    events = []
    for record in records:
        if record.get("pool_id") != pool_id or record.get("status") != "confirmed":
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


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_text(value):
    return isinstance(value, str) and bool(value.strip())


def _hhmm(minutes):
    return "%02d:%02d" % divmod(minutes, 60)
