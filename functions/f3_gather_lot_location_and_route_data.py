"""F.3 Gather Lot Location and Route Data.

ICOM on the first-level IDEF0:
    inputs    IO.14 Trip Details                           from F.2
              IO.5  Parking Locations and Route Information from X.F.4 Supply Location and Route Data
    control   IO.3  Identity and Permit Eligibility        from X.F.3
    outputs   IO.4  Location and Route Request             to X.F.4
              IO.15 Candidate Parking Data                 to F.4
              IO.16 Route Guidance Data                    to F.6
IO.4 goes out and IO.5 comes back, so the module has two functions: one that writes the request
and one that turns the answer into IO.15 and IO.16.

Shapes:
    IO.3   {"driver_id": str, "status": "eligible" | "invalid" | "unknown" | "missing" | "failed",
            "permit": str | None}
    IO.4   {"destination": str}   only what the lookup needs (SR.13)
    IO.5   {"status": "ok" | "failed", "lots": list[{"pool_id": str, "name": str, "address": str,
            "walk_minutes": int | None}]}
    IO.15  {"trip": IO.14, "lots": list[{"pool_id", "name", "address", "walk_minutes"}],
            "route_status": "ok" | "unavailable"}   walk_minutes None means unavailable
    IO.16  {"destination": str, "status": "ok" | "unavailable",
            "routes": {pool_id: str | None}, "addresses": {pool_id: str | None}}
           addresses come from IO.5 and are kept even when every route is unavailable, so the
           confirmation can still show the lot address (SR.16)

The bodies were added in Chapter 5; the signatures and shapes above are unchanged.
"""

import copy


def request_location_and_route(trip_details: dict, *, eligibility: dict):
    """in: IO.14. control: IO.3. out: IO.4, or None when the trip is not eligible."""
    if not _is_eligible_trip(trip_details, eligibility):
        return None
    return {"destination": trip_details["destination"]}


def gather_lot_location_and_route_data(trip_details: dict, locations_and_routes: dict, *,
                                       eligibility: dict) -> tuple:
    """in: IO.14, IO.5. control: IO.3. out: (IO.15, IO.16)."""
    trip = copy.deepcopy(trip_details)
    destination = trip.get("destination") if isinstance(trip, dict) else None
    if not isinstance(destination, str):
        destination = ""
    answer = locations_and_routes if isinstance(locations_and_routes, dict) else {}
    answered = answer.get("status") == "ok"

    lots, routes, addresses = [], {}, {}
    if _is_eligible_trip(trip_details, eligibility):
        for lot in answer.get("lots") or []:
            if not isinstance(lot, dict) or not _is_text(lot.get("pool_id")):
                continue                    # an entry without a pool id cannot be offered or booked
            pool_id = lot["pool_id"]
            name = lot["name"] if _is_text(lot.get("name")) else pool_id
            address = lot["address"] if _is_text(lot.get("address")) else None
            # A failed answer gives no estimate at all; a missing or bad value is unavailable too.
            walk = lot.get("walk_minutes") if answered else None
            if not (isinstance(walk, int) and not isinstance(walk, bool) and walk >= 0):
                walk = None
            lots.append({"pool_id": pool_id, "name": name, "address": address,
                         "walk_minutes": walk})
            routes[pool_id] = None if walk is None else _route_text(name, walk, destination)
            addresses[pool_id] = address

    status = "ok" if any(route is not None for route in routes.values()) else "unavailable"
    candidates = {"trip": trip, "lots": lots, "route_status": status}
    guidance = {"destination": destination, "status": status, "routes": routes,
                "addresses": addresses}
    return candidates, guidance


def _is_eligible_trip(trip, eligibility):
    """A complete trip whose driver X.F.3 reports eligible."""
    return (isinstance(trip, dict) and isinstance(eligibility, dict)
            and eligibility.get("status") == "eligible"
            and eligibility.get("driver_id") == trip.get("driver_id")
            and not trip.get("missing")
            and _is_text(trip.get("destination")))


def _route_text(lot_name, walk_minutes, destination):
    return "From %s, walk about %d min to %s." % (lot_name, walk_minutes,
                                                  destination or "your destination")


def _is_text(value):
    return isinstance(value, str) and bool(value.strip())
