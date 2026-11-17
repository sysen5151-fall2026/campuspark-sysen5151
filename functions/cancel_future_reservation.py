"""Cancel Future Reservation, for SR.6 Future Booking Cancellation.

SR.6: CampusPark shall release the capacity held by a future reservation when the driver cancels
that reservation. No function on the first-level IDEF0 of F.0 owns this yet, so it is listed apart
from F.1 to F.7 in docs/traceability.md. It runs on the same mechanism as F.5, the C.5 Reservation
Subsystem store, and it is the next function to add to the model.

ICOM, written the same way as the first-level modules:
    input     Cancellation Request          from the Campus Driver
    control   now                           minutes since midnight, the booking must not have started
    outputs   Cancelled Reservation Record  the saved record, now with status "cancelled"
              Cancellation Refusal Notice   why nothing was cancelled
              Reservation Records           every saved reservation (IO.18), to F.4 and F.7
Mechanism: C.5 Reservation Subsystem. The injected store needs all() and cancel(); the product
injects the SQLite store in data/reservation_db.py.

The places come back on their own. F.4, F.5 and F.7 count only records whose status is "confirmed",
so a cancelled record stops counting for its whole period the moment it is saved. A second cancel
of the same booking returns the same record and releases nothing more. A booking that has already
started is refused here; SR.6 covers future bookings only, and the operating rule for a started
booking is still the owner's decision.

Shapes:
    Cancellation Request          {"reservation_id": str, "driver_id": str}
    Cancelled Reservation Record  IO.8 with "status": "cancelled"
    Cancellation Refusal Notice   {"reason": "missing_data" | "not_found" | "already_started",
                                   "message": str}
"""


def cancel_future_reservation(cancellation_request: dict, *, now: int, reservation_store) -> tuple:
    """in: Cancellation Request. control: now. mechanism: reservation_store.
    out: (cancelled record or None, refusal or None, IO.18). Exactly one of the first two is not None.
    """
    request = cancellation_request if isinstance(cancellation_request, dict) else {}
    reservation_id, driver_id = request.get("reservation_id"), request.get("driver_id")
    if not (_is_text(reservation_id) and _is_text(driver_id)):
        return None, _refusal("missing_data", "A cancellation needs the confirmation number and the "
                                              "driver ID the booking was made with."), reservation_store.all()

    # Only the driver who made the booking can cancel it, and a wrong pair says nothing about
    # whether the number exists.
    record = next((r for r in reservation_store.all() if r["reservation_id"] == reservation_id), None)
    if record is None or record["driver_id"] != driver_id:
        return None, _refusal("not_found", "No booking with that confirmation number for that "
                                           "driver ID."), reservation_store.all()

    if record["status"] == "cancelled":
        return record, None, reservation_store.all()

    if not _is_minute(now) or now >= record["start"]:
        return None, _refusal("already_started", "This booking has already started, so it can't be "
                                                 "cancelled here."), reservation_store.all()

    return reservation_store.cancel(reservation_id), None, reservation_store.all()


def _refusal(reason, message):
    return {"reason": reason, "message": message}


def _is_text(value):
    return isinstance(value, str) and value.strip() != ""


def _is_minute(value):
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 24 * 60
