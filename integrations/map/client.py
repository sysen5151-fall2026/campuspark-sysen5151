"""Campus Map & Navigation Service.

Also outside the boundary, also read only, also stubbed. Distances are made up
but the shape of the data is what we expect the real service to give us.
"""

# walk_minutes is keyed by destination so the ordering changes depending on
# where the driver is actually going.
LOTS = [
    {
        "id": "A-lot",
        "position": (42.45635, -76.47756),
        "address": "A Lot, Jessup Road, Ithaca, NY",
        "name": "A Lot",
        "permits": ["student", "staff"],
        "capacity": 40,
        "walk_minutes": {"Duffield Hall": 14, "Statler Hotel": 18, "Vet School": 9},
    },
    {
        "id": "hoy-garage",
        "position": (42.44395, -76.47953),
        "address": "Hoy Road Garage, Hoy Road, Ithaca, NY",
        "name": "Hoy Road Garage",
        "permits": ["staff", "visitor"],
        "capacity": 25,
        "walk_minutes": {"Duffield Hall": 8, "Statler Hotel": 6, "Vet School": 16},
    },
    {
        "id": "forest-home",
        "position": (42.44876, -76.47264),
        "address": "Forest Home Drive lot, Forest Home Drive, Ithaca, NY",
        "name": "Forest Home Drive",
        "permits": ["student"],
        "capacity": 15,
        "walk_minutes": {"Duffield Hall": 11, "Statler Hotel": 13, "Vet School": 7},
    },
    {
        "id": "visitor-garage",
        "position": (42.44545, -76.48068),
        "address": "Visitor Parking Garage, Campus Road, Ithaca, NY",
        "name": "Visitor Parking Garage",
        "permits": ["visitor"],
        "capacity": 30,
        "walk_minutes": {"Duffield Hall": 5, "Statler Hotel": 4, "Vet School": 20},
    },
]

DESTINATIONS = ["Duffield Hall", "Statler Hotel", "Vet School"]

# Map positions (latitude, longitude) for drawing the lots and destinations. No decision uses them.
# Destinations and Hoy Road Garage are the real places in OpenStreetMap (Nominatim, 2026-10-28; the
# Vet School point is Schurman Hall). The other fixture lots have no namesake in OpenStreetMap, so
# each sits on the real parking area nearest to where it was first drawn (OSM ways 1106713124,
# 625491206 and 1192681044).
DESTINATION_POSITIONS = {
    "Duffield Hall": (42.44453, -76.48260),
    "Statler Hotel": (42.44638, -76.48223),
    "Vet School": (42.44795, -76.46615),
}

# Addresses above are fixture text in the shape we expect from the map owner, not surveyed data.


def map_view():
    """Where to draw each lot and destination on the driver's map (UC.1.6). Display only."""
    return {"lots": [{"pool_id": lot["id"], "name": lot["name"], "lat": lot["position"][0],
                      "lon": lot["position"][1]} for lot in LOTS],
            "destinations": [{"name": name, "lat": lat, "lon": lon}
                             for name, (lat, lon) in DESTINATION_POSITIONS.items()]}


def locations_and_routes(location_request):
    """IO.4 in, IO.5 out: every lot with its address and walking estimate (UC.1.4, UC.1.5).

    Only the destination is sent (SR.13). A missing estimate stays None so F.3 can mark it
    unavailable instead of inventing one.
    """
    destination = (location_request or {}).get("destination")
    return {"status": "ok",
            "lots": [{"pool_id": lot["id"], "name": lot["name"], "address": lot["address"],
                      "walk_minutes": lot["walk_minutes"].get(destination)} for lot in LOTS]}


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
