"""Order the eligible lots into the list the driver sees (UC.1.6).

Walk time first, remaining capacity as the tie breaker. That ordering is a
placeholder: how to weigh distance against the chance of a space is a
stakeholder requirements question, and those are due Oct 4. Leaving it simple
and obvious until then beats inventing a score nobody asked for.

Lots with no walk-time estimate go after the ones that have one. We don't
know they're far, but we can't claim they're close either.
"""

from api import reservations


def rank(lots, destination, start, end):
    scored = []
    for lot in lots:
        free = reservations.remaining_capacity(lot, start, end)
        if free <= 0:
            continue  # nothing to offer, don't show it
        scored.append({**lot, "remaining": free})

    def order(lot):
        walk = lot["walk_minutes"]
        return (walk is None, walk if walk is not None else 0, -lot["remaining"])

    return sorted(scored, key=order)
