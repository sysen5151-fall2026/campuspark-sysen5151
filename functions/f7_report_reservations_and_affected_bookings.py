"""F.7 Report Reservations and Affected Bookings.

ICOM on the first-level IDEF0:
    inputs    IO.18 Reservation Records                    from F.5
              IO.19 Control Change Result                  from F.1
    control   IO.17 Approved Parking Rules and Capacity    from F.1
    outputs   IO.11 Control Update Acknowledgement         to X.F.2
              IO.12 Reservation Reports                    to X.F.2

Shapes:
    IO.11  {"accepted": bool, "version": int, "pool_id": str, "reason": str | None}
    IO.12  {"pool_id": str, "affected": list[IO.8], "confirmed_count": int}
           affected = confirmed reservations whose period overlaps a window in IO.19 (SR.9);
           confirmed_count = confirmed reservations in that pool (SR.10)
"""


def report_reservations_and_affected_bookings(reservation_records: list, control_change_result: dict, *,
                                              approved_rules: dict) -> tuple:
    """in: IO.18, IO.19. control: IO.17. out: (IO.11, IO.12)."""
    raise NotImplementedError
