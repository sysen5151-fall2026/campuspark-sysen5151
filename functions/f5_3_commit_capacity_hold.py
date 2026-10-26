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


class CapacityLedger:
    """C.5.3 Capacity Ledger: the saved reservations and their capacity holds."""

    def __init__(self):
        raise NotImplementedError

    def records(self) -> list:
        """Every saved reservation (IO.18)."""
        raise NotImplementedError


def commit_capacity_hold(eligible_booking_request: dict, *, approved_rules: dict,
                         ledger: CapacityLedger) -> tuple:
    """in: IO.21. control: IO.17. mechanism: ledger (C.5.3).
    out: (IO.8 or None, IO.18, IO.22 or None). Exactly one of IO.8 and IO.22 is not None.
    """
    raise NotImplementedError
