"""Hold a space and remember that we held it (UC.1.8, UC.1.9).

Everything lives in memory for now, so restarting the server clears the
reservations. A database is fine to add later; it isn't what the milestone is
checking.

Worth repeating because it drives the whole design: remaining capacity is
configured capacity minus reservations we recorded. It is not a measurement.
A confirmation means we set capacity aside, not that a space is empty.

Times are minutes since midnight on a single day. The skeleton has no date
field yet, so every booking is treated as the same day. Bookings are half-open
intervals [start, end): one ending at 10:00 and another starting at 10:00
don't overlap, which matches the overlap rule in the SPEC's planned contract.
"""

import uuid

# reservation records, newest last
_RESERVATIONS = []


def clock(minutes):
    """640 -> '10:40'. Anything past midnight is marked as the next day."""
    day, rest = divmod(minutes, 24 * 60)
    label = f"{rest // 60:02d}:{rest % 60:02d}"
    return label + (" next day" if day else "")


def _peak_held(lot_id, start, end):
    """Most places held at any one moment inside [start, end).

    Counting every booking that touches the window would refuse some requests
    that actually fit: 09-10 and 10-11 never hold two places at once, so a
    09-11 request in a two-place lot still has room. Earlier this compared
    window labels as plain strings, so 09:00+2h and 10:00+2h never saw each
    other and the lot could be overbooked (SR.4).
    """
    events = []
    for r in _RESERVATIONS:
        if r["lot_id"] != lot_id:
            continue
        s, e = max(r["start_min"], start), min(r["end_min"], end)
        if s < e:
            events.append((s, 1))
            events.append((e, -1))
    # at the same minute, a booking ending frees its place before the next one starts
    events.sort(key=lambda ev: (ev[0], ev[1]))
    held = peak = 0
    for _, step in events:
        held += step
        peak = max(peak, held)
    return peak


def remaining_capacity(lot, start, end):
    return lot["capacity"] - _peak_held(lot["id"], start, end)


def reserve(profile, lot, destination, start, end):
    """Record a reservation. Returns None if the lot filled up in the meantime."""
    if remaining_capacity(lot, start, end) <= 0:
        return None
    record = {
        "id": uuid.uuid4().hex[:8],
        "driver_id": profile["driver_id"],
        "lot_id": lot["id"],
        "lot_name": lot["name"],
        "destination": destination,
        "start_min": start,
        "end_min": end,
        "start": clock(start),
        "end": clock(end),
    }
    _RESERVATIONS.append(record)
    return record


def all_reservations():
    return list(_RESERVATIONS)
