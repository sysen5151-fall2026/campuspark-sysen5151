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
"""


def request_location_and_route(trip_details: dict, *, eligibility: dict):
    """in: IO.14. control: IO.3. out: IO.4, or None when the trip is not eligible."""
    raise NotImplementedError


def gather_lot_location_and_route_data(trip_details: dict, locations_and_routes: dict, *,
                                       eligibility: dict) -> tuple:
    """in: IO.14, IO.5. control: IO.3. out: (IO.15, IO.16)."""
    raise NotImplementedError
