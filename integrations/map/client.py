"""Campus Map & Navigation Service.

Also outside the boundary, also read only, also stubbed. Distances are made up
but the shape of the data is what we expect the real service to give us.
"""

# walk_minutes is keyed by destination so the ordering changes depending on
# where the driver is actually going.
LOTS = [
    {
        "id": "A-lot",
        "name": "A Lot",
        "permits": ["student", "staff"],
        "capacity": 40,
        "walk_minutes": {"Duffield Hall": 14, "Statler Hotel": 18, "Vet School": 9},
    },
    {
        "id": "hoy-garage",
        "name": "Hoy Road Garage",
        "permits": ["staff", "visitor"],
        "capacity": 25,
        "walk_minutes": {"Duffield Hall": 8, "Statler Hotel": 6, "Vet School": 16},
    },
    {
        "id": "forest-home",
        "name": "Forest Home Drive",
        "permits": ["student"],
        "capacity": 15,
        "walk_minutes": {"Duffield Hall": 11, "Statler Hotel": 13, "Vet School": 7},
    },
    {
        "id": "visitor-garage",
        "name": "Visitor Parking Garage",
        "permits": ["visitor"],
        "capacity": 30,
        "walk_minutes": {"Duffield Hall": 5, "Statler Hotel": 4, "Vet School": 20},
    },
]

DESTINATIONS = ["Duffield Hall", "Statler Hotel", "Vet School"]


def lots_near(destination):
    """Candidate lots with a walk time to the destination (UC.1.5).

    walk_minutes is None when we have no estimate for that destination. We
    used to fill in 15 minutes here, but SR.3 wants a missing fact shown as
    unavailable rather than a number we made up.
    """
    out = []
    for lot in LOTS:
        lot = dict(lot)
        lot["walk_minutes"] = lot["walk_minutes"].get(destination)
        out.append(lot)
    return out


def route_to(lot, destination):
    """One line of guidance. The real service returns an actual route."""
    if lot["walk_minutes"] is None:
        return f"Park at {lot['name']}. We don't have a walk time from there to {destination}."
    return (
        f"Park at {lot['name']}, then an estimated {lot['walk_minutes']} minute "
        f"walk to {destination}."
    )
