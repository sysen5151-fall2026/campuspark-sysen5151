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

The body was added in Chapter 5; the signature and shapes above are unchanged.
"""

import copy


def report_reservations_and_affected_bookings(reservation_records: list, control_change_result: dict, *,
                                              approved_rules: dict) -> tuple:
    """in: IO.18, IO.19. control: IO.17. out: (IO.11, IO.12)."""
    # The affected list and the count follow from IO.18 and IO.19 alone; approved_rules is not read.
    change = control_change_result if isinstance(control_change_result, dict) else {}
    accepted = change.get("accepted") is True
    pool_id = change.get("pool_id")
    reason = None
    if not accepted:
        reason = change.get("reason") if _is_text(change.get("reason")) else \
            "the control change was not accepted"
    acknowledgement = {"accepted": accepted, "version": change.get("version"),
                       "pool_id": pool_id, "reason": reason}

    confirmed = [record for record in reservation_records or []
                 if isinstance(record, dict) and record.get("pool_id") == pool_id
                 and record.get("status") == "confirmed"]
    # Only an accepted change can affect a booking, whatever windows a rejected result names.
    windows = (change.get("windows") or []) if accepted else []
    affected = [copy.deepcopy(record) for record in confirmed
                if any(_overlaps(record, window) for window in windows)]
    report = {"pool_id": pool_id, "affected": affected, "confirmed_count": len(confirmed)}
    return acknowledgement, report


def _overlaps(record, window):
    """The record's [start, end) overlaps the half-open window."""
    return (isinstance(window, dict) and _is_int(window.get("start")) and _is_int(window.get("end"))
            and _is_int(record.get("start")) and _is_int(record.get("end"))
            and record["start"] < window["end"] and window["start"] < record["end"])


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_text(value):
    return isinstance(value, str) and bool(value.strip())
