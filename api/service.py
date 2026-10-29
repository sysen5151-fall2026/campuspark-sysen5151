"""How the first-level subsystems are wired together for the web routes.

Each route runs the functions of one use case in the order of the first-level IDEF0:

    UC.1 search   F.2 -> X.F.3 (permit system) -> F.3 -> X.F.4 (map service) -> F.3 -> F.4
    UC.1 booking  F.2 -> X.F.3 -> F.5 -> F.6
    UC.2 change   F.1 -> F.7

The mechanisms live here: the approved rules (C.1's RulesStore) and the saved reservations
(C.5's SQLite store, docs/deployment.md). Nothing in this module decides a rule; every decision is
made inside functions/.
"""

import os
import threading
import uuid
from collections import OrderedDict

from data.reservation_db import SqliteReservationStore
from functions.f1_apply_parking_controls import RulesStore, apply_parking_controls
from functions.f2_validate_trip_eligibility import validate_trip_eligibility
from functions.f3_gather_lot_location_and_route_data import (
    gather_lot_location_and_route_data, request_location_and_route)
from functions.f4_present_eligible_parking_options import present_eligible_parking_options
from functions.f5_recheck_and_record_reservation import recheck_and_record_reservation
from functions.f6_provide_confirmation_and_route_guidance import provide_confirmation_and_route_guidance
from functions.f7_report_reservations_and_affected_bookings import report_reservations_and_affected_bookings
from integrations.map import client as map_client
from integrations.permit import client as permit_client

# Saved reservations survive a restart in this file (not committed; *.db is in .gitignore).
DEFAULT_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "campuspark.db")

# Fixture staff account for the Parking Administrator (UC.2). Real accounts come from Campus IT.
APPROVED_STAFF = {"admin01"}

# IO.16 from each search, kept until the booking so F.6 never looks the route up twice (1.4.1.10).
_KEEP_GUIDANCE = 500

_lock = threading.RLock()
_state = {}


def _seed_pools():
    return {lot["id"]: {"name": lot["name"], "capacity": lot["capacity"],
                        "permits": list(lot["permits"]), "closures": []}
            for lot in map_client.LOTS}


def reset(db_path=None, pools=None):
    """Start from the fixture rules and an empty (or the configured) reservation database."""
    with _lock:
        if _state.get("store"):
            _state["store"].close()
        path = db_path or os.environ.get("CAMPUSPARK_DB") or DEFAULT_DB
        _state.update(rules=RulesStore(pools or _seed_pools(), APPROVED_STAFF),
                      store=SqliteReservationStore(path), guidance=OrderedDict())


def _ready():
    if not _state:
        reset()
    return _state


def clock(minutes):
    """540 -> '09:00'."""
    return "%02d:%02d" % divmod(minutes, 60)


def records():
    """Every saved reservation (IO.18)."""
    return _ready()["store"].all()


def approved_rules():
    """The approved rule set now in force (IO.17)."""
    return _ready()["rules"].current()


def _keep(key, guidance):
    kept = _ready()["guidance"]
    kept[key] = guidance
    while len(kept) > _KEEP_GUIDANCE:
        kept.popitem(last=False)


def _trip_and_eligibility(parking_request, rules):
    """F.2, then the permit system. Returns (IO.14, IO.3 or None)."""
    validation, trip = validate_trip_eligibility(parking_request, approved_rules=rules)
    if validation is None:
        return trip, None
    return trip, permit_client.identity_and_permit_eligibility(validation)


def search(parking_request):
    """UC.1.1 to UC.1.6. Returns a dict with the trip, IO.3, IO.6 and a search_id, or an error."""
    rules = approved_rules()
    trip, eligibility = _trip_and_eligibility(parking_request, rules)
    if trip["missing"]:
        return {"error_kind": "trip", "missing": trip["missing"]}
    if eligibility["status"] != "eligible":
        return {"error_kind": "identity"}
    location_request = request_location_and_route(trip, eligibility=eligibility)
    answer = map_client.locations_and_routes(location_request)
    candidates, guidance = gather_lot_location_and_route_data(trip, answer, eligibility=eligibility)
    options = present_eligible_parking_options(candidates, records(), eligibility=eligibility,
                                               approved_rules=rules)
    search_id = uuid.uuid4().hex
    _keep(search_id, guidance)
    addresses = guidance.get("addresses") or {}
    return {"trip": trip, "eligibility": eligibility, "options": options, "search_id": search_id,
            "addresses": addresses}


def book(parking_request, pool_id, request_id=None, search_id=None):
    """UC.1.7 to UC.1.9. Returns {"confirmation": IO.9} or {"refusal": IO.13} or an error."""
    rules = approved_rules()
    trip, eligibility = _trip_and_eligibility(parking_request, rules)
    if trip["missing"]:
        return {"error_kind": "trip", "missing": trip["missing"]}
    if eligibility["status"] != "eligible":
        return {"error_kind": "identity"}
    reservation_request = {"request_id": request_id or uuid.uuid4().hex, "driver_id": trip["driver_id"],
                           "pool_id": pool_id, "start": trip["start"], "end": trip["end"]}
    # F.5 checks capacity and then saves. One booking at a time keeps those two steps together
    # until C.5.3 Capacity Ledger takes over the commitment (RS.1.4.3, RS.2.5).
    with _lock:
        record, refusal, _ = recheck_and_record_reservation(
            reservation_request, eligibility=eligibility, approved_rules=rules,
            reservation_store=_ready()["store"])
    if refusal is not None:
        return {"refusal": refusal}
    guidance = _ready()["guidance"].get(search_id) or {}
    _keep(record["reservation_id"], guidance)
    return {"confirmation": provide_confirmation_and_route_guidance(record, guidance, approved_rules=rules)}


def find_confirmation(reservation_id, driver_id):
    """UC.1.10: show a saved confirmation again, only to the driver who made it."""
    for record in records():
        if record["reservation_id"] == reservation_id and record["driver_id"] == driver_id:
            guidance = _ready()["guidance"].get(reservation_id) or {}
            return provide_confirmation_and_route_guidance(record, guidance, approved_rules=approved_rules())
    return None


def change_controls(change):
    """UC.2: F.1 applies the administrator's change (IO.10), F.7 acknowledges and reports it."""
    with _lock:
        rules, result = apply_parking_controls(parking_rules_and_capacity=change,
                                               rules_store=_ready()["rules"])
    acknowledgement, report = report_reservations_and_affected_bookings(records(), result,
                                                                        approved_rules=rules)
    return acknowledgement, report
