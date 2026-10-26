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
"""


class ReservationStore:
    """Saved reservations. Each request_id adds at most one commitment (SR.4)."""

    def __init__(self):
        raise NotImplementedError

    def all(self) -> list:
        """Every saved reservation (IO.18)."""
        raise NotImplementedError


def recheck_and_record_reservation(reservation_request: dict, *, eligibility: dict,
                                   approved_rules: dict, reservation_store: ReservationStore) -> tuple:
    """in: IO.7. controls: IO.3, IO.17. mechanism: reservation_store.
    out: (IO.8 or None, IO.13 or None, IO.18). Exactly one of IO.8 and IO.13 is not None.
    """
    raise NotImplementedError
