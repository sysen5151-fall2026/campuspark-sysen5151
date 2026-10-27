"""F.5.3 Commit Capacity Hold, performed by C.5.3 Capacity Ledger.

ICOM on the second-level IDEF0 of F.5 Recheck and Record Reservation (Chapter 9):
    input     IO.21 Eligible Booking Request              from F.5.2 Recheck Booking Eligibility
    control   IO.17 Approved Parking Rules and Capacity   from F.1 (C.1 Parking Control Subsystem)
    outputs   IO.8  Confirmed Reservation Record          to F.6 (C.6 Confirmation Subsystem)
              IO.18 Reservation Records                   to F.4 (C.4) and F.7 (C.7)
              IO.22 Booking Refusal Reason                to F.5.4 Issue Booking Refusal
Mechanism: C.5.3 Capacity Ledger, injected as `ledger`.

Shapes (contracts/api-v1.yaml, version 1.1):
    IO.21  {"request_id": str, "driver_id": str, "pool_id": str, "start": int, "end": int}
           Already screened by F.5.1 and rechecked for eligibility and closures by F.5.2.
           Minutes since midnight; the period is [start, end).
    IO.17  {"version": int, "pools": {pool_id: {"name": str, "capacity": int, "permits": list[str],
            "closures": list[{"start": int, "end": int}]}}}
    IO.8   {"reservation_id": str, "request_id": str, "driver_id": str, "pool_id": str,
            "start": int, "end": int, "status": "confirmed"}
    IO.18  list[IO.8]
    IO.22  {"request_id": str | None, "reason": "missing_data" | "not_eligible" | "closed" | "pool_full"}
"""

import threading
import uuid


def _approved_capacity(approved_rules, pool_id):
    """Capacity of `pool_id` in IO.17, or None when it is absent or not an integer (RS.2.3)."""
    if not isinstance(approved_rules, dict):
        return None
    pools = approved_rules.get("pools")
    if not isinstance(pools, dict):
        return None
    rule = pools.get(pool_id)
    if not isinstance(rule, dict):
        return None
    capacity = rule.get("capacity")
    # bool is a subclass of int in Python; True/False are not a capacity.
    if isinstance(capacity, bool) or not isinstance(capacity, int):
        return None
    # The contract sets capacity minimum 0; a negative value is invalid data, not a full pool
    # (deviation D5 in docs/deviation-log.md).
    if capacity < 0:
        return None
    return capacity


class CapacityLedger:
    """C.5.3 Capacity Ledger: the saved reservations and their capacity holds."""

    def __init__(self):
        # One lock guards the whole ledger, so the request-ID lookup, the capacity check and the
        # save happen as one step (RS.1.4.3) and holds are serialized for every pool (RS.2.5).
        self._lock = threading.Lock()
        # Saved IO.8 records in save order. A record is never changed after it is saved, so a
        # shallow list snapshot taken under the lock can be copied safely outside it.
        self._records = []
        # request_id -> saved IO.8, at most one reservation per request ID (RS.2.5).
        self._by_request_id = {}
        # pool_id -> {minute: places held}; the capacity holds of the saved reservations.
        self._holds = {}

    def records(self) -> list:
        """Every saved reservation (IO.18)."""
        with self._lock:
            snapshot = list(self._records)
        return [dict(record) for record in snapshot]

    def _commit(self, request, capacity):
        """Check capacity and save in one step.

        Returns (saved IO.8 or None, refusal reason or None, snapshot of saved records).
        """
        request_id = request.get("request_id")
        with self._lock:
            saved = self._by_request_id.get(request_id)
            if saved is not None:
                # Repeated request ID: the saved reservation, no second hold (RS.1.4.3).
                return saved, None, list(self._records)
            if capacity is None:
                return None, "missing_data", list(self._records)

            pool_id = request["pool_id"]
            start = request["start"]
            end = request["end"]
            minutes = range(start, end)  # half-open [start, end)

            held = self._holds.get(pool_id, {})
            for minute in minutes:
                if held.get(minute, 0) >= capacity:
                    return None, "pool_full", list(self._records)

            # RS.2.1: only reservation ID, request ID, identity reference, pool, period, status.
            record = {
                "reservation_id": "res-" + uuid.uuid4().hex,
                "request_id": request_id,
                "driver_id": request["driver_id"],
                "pool_id": pool_id,
                "start": start,
                "end": end,
                "status": "confirmed",
            }
            held = self._holds.setdefault(pool_id, {})
            for minute in minutes:
                held[minute] = held.get(minute, 0) + 1
            self._records.append(record)
            self._by_request_id[request_id] = record
            return record, None, list(self._records)


def commit_capacity_hold(eligible_booking_request: dict, *, approved_rules: dict,
                         ledger: CapacityLedger) -> tuple:
    """in: IO.21. control: IO.17. mechanism: ledger (C.5.3).
    out: (IO.8 or None, IO.18, IO.22 or None). Exactly one of IO.8 and IO.22 is not None.
    """
    # The rule set passed on this call is the one in force (RS.2.2); nothing is cached.
    capacity = _approved_capacity(approved_rules, eligible_booking_request.get("pool_id"))
    saved, reason, snapshot = ledger._commit(eligible_booking_request, capacity)
    reservation_records = [dict(record) for record in snapshot]
    if saved is not None:
        return dict(saved), reservation_records, None
    refusal = {"request_id": eligible_booking_request.get("request_id"), "reason": reason}
    return None, reservation_records, refusal
