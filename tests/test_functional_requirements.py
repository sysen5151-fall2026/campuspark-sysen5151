"""Requirement-driven tests for the CampusPark functional requirements 1.4.1.1 to 1.4.1.11.

Written before any implementation exists, from two sources only: the requirement text in the
Innoslate model (system requirements document, under 1.4.1 Provide Campus Parking Reservations)
and the ICOM docstrings of the signature-only modules in functions/. Each test names its
requirement, repeats the statement and the "passes when" criterion, and calls the documented
signatures: inputs positional, controls keyword-only, mechanisms (stores) injected.

Times are minutes since midnight and every booked period is the half-open interval [start, end),
as functions/__init__.py states. Where a criterion sets a 60 s limit, the calls are synchronous and
in process, so the test checks that the effect is visible on the very next call. The 60 s timing of
a deployed system is outside what these tests cover.
"""

import copy

from functions.f1_apply_parking_controls import RulesStore, apply_parking_controls
from functions.f2_validate_trip_eligibility import validate_trip_eligibility
from functions.f3_gather_lot_location_and_route_data import (
    gather_lot_location_and_route_data,
    request_location_and_route,
)
from functions.f4_present_eligible_parking_options import present_eligible_parking_options
from functions.f5_recheck_and_record_reservation import (
    ReservationStore,
    recheck_and_record_reservation,
)
from functions.f6_provide_confirmation_and_route_guidance import (
    provide_confirmation_and_route_guidance,
)
from functions.f7_report_reservations_and_affected_bookings import (
    report_reservations_and_affected_bookings,
)
import functions.f3_gather_lot_location_and_route_data as f3_module
import functions.f6_provide_confirmation_and_route_guidance as f6_module


# ---------------------------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------------------------

ADMIN = "pa-admin-01"            # on the approved staff list of every RulesStore built here
NOT_APPROVED = "drv-guest-77"    # never on the approved staff list
DRIVER = "d-100"
DESTINATION = "Duffield Hall"
REFUSAL_REASONS = {"missing_data", "not_eligible", "closed", "pool_full"}   # IO.13 value set

STANDARD_POOLS = ("P-NORTH", "P-EAST", "P-WEST")
POOL_NAMES = {
    "P-NORTH": "North Campus Garage",
    "P-EAST": "East Faculty Lot",
    "P-WEST": "West Commuter Lot",
    "P-SOUTH": "South Visitor Lot",
}
LOT_ADDRESSES = {
    "P-NORTH": "1 North Garage Road",
    "P-EAST": "2 East Lot Road",
    "P-WEST": "3 West Lot Road",
    "P-SOUTH": "4 South Lot Road",
}
WALK_MINUTES = {"P-NORTH": 6, "P-EAST": 9, "P-WEST": 14, "P-SOUTH": 11}
STANDARD_ADDRESSES = {p: LOT_ADDRESSES[p] for p in STANDARD_POOLS}   # IO.16 "addresses" from IO.5


def make_pools():
    """Approved pools in the IO.17 "pools" shape. Driver permits are "student" or "faculty"."""
    return {
        "P-NORTH": {"name": POOL_NAMES["P-NORTH"], "capacity": 2,
                    "permits": ["student", "faculty"], "closures": []},
        "P-EAST": {"name": POOL_NAMES["P-EAST"], "capacity": 3,
                   "permits": ["faculty"], "closures": []},
        "P-WEST": {"name": POOL_NAMES["P-WEST"], "capacity": 1,
                   "permits": ["student"], "closures": []},
    }


def make_rules_store(pools=None):
    """A fresh F.1 rules store whose only approved account is ADMIN."""
    return RulesStore(make_pools() if pools is None else pools, {ADMIN})


def control_change(pool_id, account=ADMIN, capacity=None, permits=None, closures=None):
    """IO.10 Parking Rules and Capacity. None leaves a field unchanged."""
    return {"account": account, "pool_id": pool_id, "capacity": capacity,
            "permits": permits, "closures": closures}


def eligibility(status="eligible", permit="student", driver_id=DRIVER):
    """IO.3 Identity and Permit Eligibility, as X.F.3 would answer."""
    return {"driver_id": driver_id, "status": status, "permit": permit}


def parking_request(**changes):
    """IO.1 Parking Request: Duffield Hall, arriving 09:00 for 2 hours, so [540, 660)."""
    request = {"driver_id": DRIVER, "destination": DESTINATION, "arrival": "09:00", "hours": 2}
    request.update(changes)
    return request


def trip_details(start=540, end=660):
    """IO.14 Trip Details for a complete request."""
    return {"driver_id": DRIVER, "destination": DESTINATION, "start": start, "end": end,
            "missing": []}


def lot_answer(status="ok", walk_minutes=WALK_MINUTES, pool_ids=STANDARD_POOLS):
    """IO.5 Parking Locations and Route Information, as the map stub (X.F.4) would answer."""
    return {"status": status,
            "lots": [{"pool_id": p, "name": POOL_NAMES[p], "address": LOT_ADDRESSES[p],
                      "walk_minutes": walk_minutes.get(p)} for p in pool_ids]}


def candidate_data(trip, pool_ids=STANDARD_POOLS, walk_minutes=WALK_MINUTES, route_status="ok"):
    """IO.15 Candidate Parking Data, as F.3 hands it to F.4."""
    return {"trip": trip,
            "lots": [{"pool_id": p, "name": POOL_NAMES[p], "address": LOT_ADDRESSES[p],
                      "walk_minutes": walk_minutes.get(p)} for p in pool_ids],
            "route_status": route_status}


def saved(reservation_id, pool_id, start, end, driver_id="d-200"):
    """One IO.8 Confirmed Reservation Record, used as IO.18 input data for F.4."""
    return {"reservation_id": reservation_id, "request_id": "req-" + reservation_id,
            "driver_id": driver_id, "pool_id": pool_id, "start": start, "end": end,
            "status": "confirmed"}


def reservation_request(request_id, pool_id="P-NORTH", start=540, end=660, driver_id=DRIVER):
    """IO.7 Reservation Request."""
    return {"request_id": request_id, "driver_id": driver_id, "pool_id": pool_id,
            "start": start, "end": end}


def book(request, approved_rules, store, permit="student"):
    """Run F.5 for a driver whom X.F.3 reports eligible with the given permit."""
    return recheck_and_record_reservation(
        request,
        eligibility=eligibility(permit=permit, driver_id=request.get("driver_id", DRIVER)),
        approved_rules=approved_rules,
        reservation_store=store,
    )


def assert_refused(outputs, store, reasons=REFUSAL_REASONS):
    """F.5 refused: no IO.8, an IO.13 with a listed reason, and IO.18 is what the store holds."""
    record, refusal, records = outputs
    assert record is None
    assert refusal is not None
    assert refusal["reason"] in reasons
    assert isinstance(refusal["message"], str) and refusal["message"].strip()
    assert records == store.all()
    return refusal


def option_ids(options_result):
    return sorted(option["pool_id"] for option in options_result["options"])


def reservation_ids(records):
    return sorted(record["reservation_id"] for record in records)


# ---------------------------------------------------------------------------------------------
# 1.4.1.1  F.1 Apply Parking Controls
# ---------------------------------------------------------------------------------------------

def test_FR_1_4_1_1_approved_change_takes_effect_and_unapproved_change_is_rejected():
    """FR 1.4.1.1 [F.1 Apply Parking Controls]

    Statement: CampusPark shall apply an approved parking control change and make the approved
    rules and capacity available to every function that decides on a trip or a booking.

    Verification: Test. Passes when: A change saved by an approved account is in effect for F.4
    and F.5 within 60 s. A change from a non-approved account is rejected and logged.

    The 60 s limit is checked for the in-process part only: the change must be visible to F.4 and
    F.5 on the very next call. "Logged" is checked through what the documented interface exposes,
    which is the reason carried by the rejected IO.19 Control Change Result; no log reader is
    documented on RulesStore.
    """
    store = make_rules_store()
    before = copy.deepcopy(store.current())
    candidates = candidate_data(trip_details())        # student trip, [540, 660)
    student = eligibility(permit="student")

    # Before any change the student trip can use both student pools.
    shown = present_eligible_parking_options(candidates, [], eligibility=student,
                                             approved_rules=store.current())
    assert option_ids(shown) == ["P-NORTH", "P-WEST"]

    # The approved account closes P-NORTH from 08:00 to 12:00.
    closure = {"start": 480, "end": 720}
    rules, result = apply_parking_controls(
        parking_rules_and_capacity=control_change("P-NORTH", closures=[closure]),
        rules_store=store)
    assert result["accepted"] is True
    assert result["reason"] is None
    assert result["pool_id"] == "P-NORTH"
    assert closure in result["windows"]
    assert rules["version"] > before["version"]
    assert result["version"] == rules["version"]
    assert closure in rules["pools"]["P-NORTH"]["closures"]
    assert store.current() == rules

    # In effect for F.4 on the next call: P-NORTH is no longer offered inside the closure.
    shown = present_eligible_parking_options(candidates, [], eligibility=student,
                                             approved_rules=store.current())
    assert option_ids(shown) == ["P-WEST"]

    # In effect for F.5 on the next call: booking P-NORTH inside the closure is refused.
    reservations = ReservationStore()
    refusal = assert_refused(
        book(reservation_request("req-1101", "P-NORTH"), store.current(), reservations),
        reservations)
    assert refusal["reason"] == "closed"
    assert reservations.all() == []

    # A non-approved account tries to close P-WEST: rejected with a reason, rules unchanged.
    after_approved = copy.deepcopy(store.current())
    rules, result = apply_parking_controls(
        parking_rules_and_capacity=control_change("P-WEST", account=NOT_APPROVED,
                                                  closures=[closure]),
        rules_store=store)
    assert result["accepted"] is False
    assert isinstance(result["reason"], str) and result["reason"].strip()
    assert result["pool_id"] == "P-WEST"
    assert rules == after_approved
    assert store.current() == after_approved

    # The rejected change is not in effect for F.4 or F.5.
    shown = present_eligible_parking_options(candidates, [], eligibility=student,
                                             approved_rules=store.current())
    assert option_ids(shown) == ["P-WEST"]
    record, refusal, records = book(reservation_request("req-1102", "P-WEST"),
                                    store.current(), reservations)
    assert refusal is None
    assert record["pool_id"] == "P-WEST"
    assert reservations.all() == [record]


# ---------------------------------------------------------------------------------------------
# 1.4.1.2  F.2 Validate Trip Eligibility
# ---------------------------------------------------------------------------------------------

def test_FR_1_4_1_2_flags_missing_trip_facts_and_sends_only_approved_identity_fields():
    """FR 1.4.1.2 [F.2 Validate Trip Eligibility]

    Statement: CampusPark shall check each parking request for the required trip facts and request
    identity and permit validation using only approved identity fields.

    Verification: Inspection, Test. Passes when: A request missing any trip field is flagged before
    a validation request is sent. The validation request holds only approved fields.

    This covers the Test part. The Inspection part (reviewing the code path that builds IO.2) is
    not replaced by this test.
    """
    rules = make_rules_store().current()

    # A complete request: nothing missing, the trip window is computed, IO.2 holds only driver_id.
    validation, trip = validate_trip_eligibility(parking_request(), approved_rules=rules)
    assert trip["missing"] == []
    assert trip["driver_id"] == DRIVER
    assert trip["destination"] == DESTINATION
    assert (trip["start"], trip["end"]) == (540, 660)
    assert validation == {"driver_id": DRIVER}

    # Personal fields beyond IO.1 that a form might carry never leave CampusPark (SR.13).
    with_extras = parking_request(full_name="Pat Doe", phone="607-555-0100", plate="ABC1234")
    validation, trip = validate_trip_eligibility(with_extras, approved_rules=rules)
    assert trip["missing"] == []
    assert validation == {"driver_id": DRIVER}

    # Each absent trip fact is flagged by name, and no validation request is produced.
    for fact in ("destination", "arrival", "hours"):
        request = parking_request()
        del request[fact]
        validation, trip = validate_trip_eligibility(request, approved_rules=rules)
        assert fact in trip["missing"], fact
        assert validation is None, fact

    # Each invalid trip fact is flagged the same way.
    for fact, bad_value in (("destination", "   "), ("arrival", "25:70"), ("hours", 0)):
        validation, trip = validate_trip_eligibility(parking_request(**{fact: bad_value}),
                                                     approved_rules=rules)
        assert fact in trip["missing"], fact
        assert validation is None, fact

    # Every missing fact is named, not only the first one found.
    validation, trip = validate_trip_eligibility({"driver_id": DRIVER}, approved_rules=rules)
    assert {"destination", "arrival", "hours"} <= set(trip["missing"])
    assert validation is None

    # Without a driver_id there is no identity to validate, so no validation request either.
    request = parking_request()
    del request["driver_id"]
    validation, trip = validate_trip_eligibility(request, approved_rules=rules)
    assert trip["missing"]
    assert validation is None


# ---------------------------------------------------------------------------------------------
# 1.4.1.3  F.3 Gather Lot Location and Route Data
# ---------------------------------------------------------------------------------------------

def test_FR_1_4_1_3_keeps_lots_and_marks_estimates_unavailable_when_map_is_down():
    """FR 1.4.1.3 [F.3 Gather Lot Location and Route Data]

    Statement: CampusPark shall request lot locations and route information for an eligible trip
    and keep every result, marking missing walking or route data as unavailable.

    Verification: Test. Passes when: With the map stub down, a search still returns options with an
    "estimate unavailable" label.

    "Map stub down" is modelled as IO.5 with status "failed" and no walking minutes for any lot,
    while the lot list itself is still present. The "estimate unavailable" label is checked as the
    documented values behind it: walk_minutes None in IO.15 and IO.6, route_status / status
    "unavailable" in IO.15 and IO.16. The display wording belongs to the web layer.
    """
    trip = trip_details()
    eligible = eligibility()

    # The request goes out for an eligible trip and holds only what the lookup needs (SR.13).
    assert request_location_and_route(trip, eligibility=eligible) == {"destination": DESTINATION}
    # No request goes out for a trip that is not eligible.
    for status in ("invalid", "unknown", "missing", "failed"):
        assert request_location_and_route(
            trip, eligibility=eligibility(status=status, permit=None)) is None, status

    # Map stub down: every lot is kept and every estimate is marked unavailable.
    candidates, guidance = gather_lot_location_and_route_data(
        trip, lot_answer(status="failed", walk_minutes={}), eligibility=eligible)
    assert sorted(lot["pool_id"] for lot in candidates["lots"]) == sorted(STANDARD_POOLS)
    assert all(lot["walk_minutes"] is None for lot in candidates["lots"])
    assert candidates["route_status"] == "unavailable"
    assert guidance["status"] == "unavailable"
    assert all(route is None for route in guidance["routes"].values())
    assert guidance["addresses"] == STANDARD_ADDRESSES     # addresses kept from IO.5 anyway

    # The search still returns options, each carrying the "estimate unavailable" value.
    shown = present_eligible_parking_options(candidates, [], eligibility=eligible,
                                             approved_rules=make_rules_store().current())
    assert shown["status"] == "OPTIONS_AVAILABLE"
    assert shown["options"]
    assert all(option["walk_minutes"] is None for option in shown["options"])

    # Map stub up but one lot has no walking data: that lot is kept and marked unavailable.
    candidates, guidance = gather_lot_location_and_route_data(
        trip, lot_answer(walk_minutes={"P-NORTH": 6, "P-EAST": 9}), eligibility=eligible)
    lots = {lot["pool_id"]: lot for lot in candidates["lots"]}
    assert sorted(lots) == sorted(STANDARD_POOLS)
    assert lots["P-WEST"]["walk_minutes"] is None
    assert lots["P-WEST"]["address"] == LOT_ADDRESSES["P-WEST"]
    assert lots["P-NORTH"]["walk_minutes"] == 6
    assert guidance["routes"].get("P-WEST") is None
    assert isinstance(guidance["routes"]["P-NORTH"], str) and guidance["routes"]["P-NORTH"].strip()
    assert guidance["addresses"] == STANDARD_ADDRESSES


# ---------------------------------------------------------------------------------------------
# 1.4.1.4  F.4 Present Eligible Parking Options
# ---------------------------------------------------------------------------------------------

def test_FR_1_4_1_4_presents_only_permitted_open_options_with_selection_facts():
    """FR 1.4.1.4 [F.4 Present Eligible Parking Options]

    Statement: CampusPark shall present only the parking options that match the approved rules,
    the driver's eligibility and the remaining capacity, with the facts used to select each option.

    Verification: Test, Inspection. Passes when: Each option shows the rule and trip facts used.
    No option appears that the permit-rule table excludes.

    This covers the Test part; the Inspection part is not replaced. The facts are checked for
    content, not wording: at least one rule fact and one trip fact, and the permit rule names the
    driver's permit.
    """
    pools = make_pools()
    pools["P-SOUTH"] = {"name": POOL_NAMES["P-SOUTH"], "capacity": 4, "permits": ["student"],
                        "closures": [{"start": 600, "end": 630}]}
    rules = make_rules_store(pools).current()
    candidates = candidate_data(trip_details(),                       # [540, 660)
                                pool_ids=("P-NORTH", "P-EAST", "P-WEST", "P-SOUTH"))
    records = [
        saved("r-1", "P-NORTH", 630, 700),    # overlaps the trip
        saved("r-2", "P-NORTH", 660, 780),    # starts when the trip ends: no overlap
        saved("r-3", "P-WEST", 600, 720),     # takes the only P-WEST place during the trip
    ]

    # Student: P-EAST is excluded by the permit table, P-WEST by capacity, P-SOUTH by a closure.
    student = eligibility(permit="student")
    shown = present_eligible_parking_options(candidates, records, eligibility=student,
                                             approved_rules=rules)
    assert shown["status"] == "OPTIONS_AVAILABLE"
    assert option_ids(shown) == ["P-NORTH"]
    option = shown["options"][0]
    assert option["name"] == POOL_NAMES["P-NORTH"]
    assert option["capacity"] == 2
    assert option["remaining"] == 1
    assert option["walk_minutes"] == WALK_MINUTES["P-NORTH"]
    facts = option["facts"]
    assert isinstance(facts, list) and len(facts) >= 2
    assert all(isinstance(fact, str) and fact.strip() for fact in facts)
    assert any("student" in fact for fact in facts)

    # For each permit, no option outside the permit-rule table, and every option shows its facts.
    faculty = present_eligible_parking_options(candidates, [], eligibility=eligibility(
        permit="faculty"), approved_rules=rules)
    assert option_ids(faculty) == ["P-EAST", "P-NORTH"]
    for permit in ("student", "faculty"):
        shown = present_eligible_parking_options(candidates, [], eligibility=eligibility(
            permit=permit), approved_rules=rules)
        for option in shown["options"]:
            assert permit in rules["pools"][option["pool_id"]]["permits"]
            assert option["facts"]

    # A permit that no pool accepts gets no options.
    shown = present_eligible_parking_options(candidates, [], eligibility=eligibility(
        permit="visitor"), approved_rules=rules)
    assert shown["status"] == "NO_OPTIONS"
    assert shown["options"] == []

    # A driver whose eligibility is not confirmed gets no options.
    for status in ("invalid", "unknown", "missing", "failed"):
        shown = present_eligible_parking_options(candidates, [], eligibility=eligibility(
            status=status, permit=None), approved_rules=rules)
        assert shown["status"] == "NO_OPTIONS", status
        assert shown["options"] == [], status


# ---------------------------------------------------------------------------------------------
# 1.4.1.5  F.5 Recheck and Record Reservation
# ---------------------------------------------------------------------------------------------

def test_FR_1_4_1_5_refuses_unknown_eligibility_and_keeps_one_record_per_request():
    """FR 1.4.1.5 [F.5 Recheck and Record Reservation]

    Statement: CampusPark shall recheck eligibility and capacity for the whole booked period and
    save one reservation with its capacity change, or refuse the booking with a specific reason.

    Verification: Test. Passes when: A repeated submit returns the saved booking. A missing, failed
    or unknown eligibility or capacity result produces a refusal and no record.
    """
    rules = make_rules_store().current()

    # A first submit saves one reservation.
    store = ReservationStore()
    request = reservation_request("req-5001", "P-NORTH", 540, 660)
    record, refusal, records = book(request, rules, store)
    assert refusal is None
    assert record["status"] == "confirmed"
    assert isinstance(record["reservation_id"], str) and record["reservation_id"]
    for key in ("request_id", "driver_id", "pool_id", "start", "end"):
        assert record[key] == request[key], key
    assert store.all() == [record]
    assert records == store.all()

    # A repeated submit returns the saved booking and adds no second commitment.
    again, refusal, records = book(dict(request), rules, store)
    assert refusal is None
    assert again == record
    assert store.all() == [record]
    assert records == [record]

    # Missing, failed, unknown or invalid eligibility: refusal and no record.
    for n, status in enumerate(("missing", "failed", "unknown", "invalid")):
        store = ReservationStore()
        outputs = recheck_and_record_reservation(
            reservation_request("req-51%02d" % n), eligibility=eligibility(status=status,
                                                                            permit=None),
            approved_rules=rules, reservation_store=store)
        refusal = assert_refused(outputs, store, {"missing_data", "not_eligible"})
        if status == "invalid":
            assert refusal["reason"] == "not_eligible"
        assert store.all() == []

    # Eligible driver, but the permit is not accepted in the pool: refusal and no record.
    store = ReservationStore()
    refusal = assert_refused(book(reservation_request("req-5150", "P-EAST"), rules, store), store)
    assert refusal["reason"] == "not_eligible"
    assert store.all() == []

    # Unknown capacity: the pool is not in the approved rules at all.
    store = ReservationStore()
    assert_refused(book(reservation_request("req-5160", "P-GHOST"), rules, store), store)
    assert store.all() == []

    # Failed capacity over the whole period: the only P-WEST place is held for part of it.
    store = ReservationStore()
    held, refusal, _ = book(reservation_request("req-5201", "P-WEST", 600, 630, "d-201"),
                            rules, store)
    assert refusal is None
    refusal = assert_refused(book(reservation_request("req-5202", "P-WEST", 540, 720),
                                  rules, store), store)
    assert refusal["reason"] == "pool_full"
    assert store.all() == [held]
    # A period that starts when the held one ends fits, since periods are [start, end).
    fits, refusal, _ = book(reservation_request("req-5203", "P-WEST", 630, 720), rules, store)
    assert refusal is None
    assert reservation_ids(store.all()) == reservation_ids([held, fits])

    # A closure inside the period refuses the booking even though the start time is open.
    pools = make_pools()
    pools["P-NORTH"]["closures"] = [{"start": 620, "end": 640}]
    closed_rules = make_rules_store(pools).current()
    store = ReservationStore()
    refusal = assert_refused(book(reservation_request("req-5301", "P-NORTH", 540, 660),
                                  closed_rules, store), store)
    assert refusal["reason"] == "closed"
    assert store.all() == []

    # A request missing booking data is refused as missing data.
    store = ReservationStore()
    incomplete = reservation_request("req-5401")
    del incomplete["end"]
    refusal = assert_refused(book(incomplete, rules, store), store)
    assert refusal["reason"] == "missing_data"
    assert store.all() == []


# ---------------------------------------------------------------------------------------------
# 1.4.1.6  F.6 Provide Confirmation and Route Guidance
# ---------------------------------------------------------------------------------------------

def test_FR_1_4_1_6_confirmation_shows_booking_facts_and_route_failure_keeps_booking():
    """FR 1.4.1.6 [F.6 Provide Confirmation and Route Guidance]

    Statement: CampusPark shall provide a confirmation with reference, lot, address and time
    window, add route guidance when route data exist, and keep the booking when route data fail.

    Verification: Test. Passes when: A confirmation shows reference, lot, address and time window.
    A route failure shows a warning and keeps the booking.

    The reference is the reservation_id. "lot" may be the pool id or the pool name. The address
    must be the booked pool's entry in IO.16 "addresses", with route data and on route failure
    alike.
    """
    rules = make_rules_store().current()
    store = ReservationStore()
    record, refusal, _ = book(reservation_request("req-6001", "P-NORTH", 540, 660), rules, store)
    assert refusal is None
    kept_record = copy.deepcopy(record)
    route_text = "From North Campus Garage walk east on Campus Road, about 6 min to Duffield Hall"

    # Route data exist: reference, lot, address, time window and guidance, no warning.
    found = {"destination": DESTINATION, "status": "ok",
             "routes": {"P-NORTH": route_text, "P-EAST": "East lot route", "P-WEST": None},
             "addresses": dict(LOT_ADDRESSES)}
    confirmation = provide_confirmation_and_route_guidance(record, found, approved_rules=rules)
    assert confirmation["reservation_id"] == record["reservation_id"]
    assert confirmation["lot"] in {"P-NORTH", POOL_NAMES["P-NORTH"]}
    assert confirmation["address"] == LOT_ADDRESSES["P-NORTH"]
    assert (confirmation["start"], confirmation["end"]) == (540, 660)
    assert isinstance(confirmation["guidance"], str) and confirmation["guidance"].strip()
    assert confirmation["warning"] is None

    # Route lookup failed: a warning, no guidance, the same confirmation facts, booking kept.
    failed = {"destination": DESTINATION, "status": "unavailable",
              "routes": {"P-NORTH": None, "P-EAST": None, "P-WEST": None},
              "addresses": dict(LOT_ADDRESSES)}
    warned = provide_confirmation_and_route_guidance(record, failed, approved_rules=rules)
    assert warned["guidance"] is None
    assert isinstance(warned["warning"], str) and warned["warning"].strip()
    assert warned["reservation_id"] == record["reservation_id"]
    assert warned["lot"] == confirmation["lot"]
    assert warned["address"] == LOT_ADDRESSES["P-NORTH"]
    assert (warned["start"], warned["end"]) == (540, 660)

    # Route data exist for other lots but not for the booked one: same handling as a failure.
    gap = {"destination": DESTINATION, "status": "ok",
           "routes": {"P-NORTH": None, "P-EAST": "East lot route"},
           "addresses": dict(LOT_ADDRESSES)}
    warned = provide_confirmation_and_route_guidance(record, gap, approved_rules=rules)
    assert warned["guidance"] is None
    assert isinstance(warned["warning"], str) and warned["warning"].strip()
    assert warned["reservation_id"] == record["reservation_id"]
    assert warned["address"] == LOT_ADDRESSES["P-NORTH"]

    # The booking stands: still saved and unchanged after every confirmation call.
    assert store.all() == [kept_record]
    assert record == kept_record


# ---------------------------------------------------------------------------------------------
# 1.4.1.7  F.7 Report Reservations and Affected Bookings
# ---------------------------------------------------------------------------------------------

def test_FR_1_4_1_7_reports_every_affected_booking_with_matching_counts():
    """FR 1.4.1.7 [F.7 Report Reservations and Affected Bookings]

    Statement: CampusPark shall find the reservations that an approved control change affects,
    report them to the Parking Administrator and acknowledge the change.

    Verification: Test. Passes when: The affected-booking list is complete within 60 s and the
    summary counts match the stored records.

    The 60 s limit is checked for the in-process part only: the list is complete on the first call
    after the change.
    """
    pools = make_pools()
    pools["P-NORTH"]["capacity"] = 5
    rules_store = make_rules_store(pools)
    store = ReservationStore()
    plan = [
        ("req-7001", "P-NORTH", 480, 600, "student"),   # ends when the window starts
        ("req-7002", "P-NORTH", 540, 630, "student"),   # straddles the window start
        ("req-7003", "P-NORTH", 600, 720, "student"),   # same as the window
        ("req-7004", "P-NORTH", 660, 700, "student"),   # inside the window
        ("req-7005", "P-NORTH", 720, 780, "student"),   # starts when the window ends
        ("req-7006", "P-NORTH", 900, 960, "student"),   # later in the day
        ("req-7007", "P-EAST", 600, 720, "faculty"),    # same time, other pool
    ]
    for n, (request_id, pool_id, start, end, permit) in enumerate(plan):
        _, refusal, _ = book(reservation_request(request_id, pool_id, start, end, "d-70%d" % n),
                             rules_store.current(), store, permit=permit)
        assert refusal is None, request_id
    by_request = {record["request_id"]: record for record in store.all()}

    # The approved change closes P-NORTH from 10:00 to 12:00.
    rules, change = apply_parking_controls(
        parking_rules_and_capacity=control_change("P-NORTH",
                                                  closures=[{"start": 600, "end": 720}]),
        rules_store=rules_store)
    assert change["accepted"] is True

    ack, report = report_reservations_and_affected_bookings(
        store.all(), change, approved_rules=rules_store.current())
    assert ack["accepted"] is True
    assert ack["reason"] is None
    assert ack["pool_id"] == "P-NORTH"
    assert ack["version"] == change["version"] == rules_store.current()["version"]
    assert report["pool_id"] == "P-NORTH"
    expected = [by_request[r] for r in ("req-7002", "req-7003", "req-7004")]
    assert reservation_ids(report["affected"]) == reservation_ids(expected)
    assert sorted(report["affected"], key=lambda r: r["reservation_id"]) == \
        sorted(expected, key=lambda r: r["reservation_id"])
    stored_count = sum(1 for r in store.all()
                       if r["pool_id"] == "P-NORTH" and r["status"] == "confirmed")
    assert stored_count == 6
    assert report["confirmed_count"] == stored_count

    # A rejected change affects nothing; the summary count still matches the stored records.
    rules, change = apply_parking_controls(
        parking_rules_and_capacity=control_change("P-NORTH", account=NOT_APPROVED,
                                                  closures=[{"start": 900, "end": 960}]),
        rules_store=rules_store)
    assert change["accepted"] is False
    ack, report = report_reservations_and_affected_bookings(
        store.all(), change, approved_rules=rules_store.current())
    assert ack["accepted"] is False
    assert isinstance(ack["reason"], str) and ack["reason"].strip()
    assert report["affected"] == []
    assert report["confirmed_count"] == stored_count

    # Even a rejected result that names a window affects no booking: only approved changes count.
    rejected = {"accepted": False, "reason": "account not approved",
                "version": rules_store.current()["version"], "pool_id": "P-NORTH",
                "windows": [{"start": 900, "end": 960}]}
    ack, report = report_reservations_and_affected_bookings(
        store.all(), rejected, approved_rules=rules_store.current())
    assert ack["accepted"] is False
    assert report["affected"] == []
    assert report["confirmed_count"] == stored_count


# ---------------------------------------------------------------------------------------------
# 1.4.1.8  F.1 Share One Set of Approved Rules and Capacity
# ---------------------------------------------------------------------------------------------

def test_FR_1_4_1_8_all_functions_use_the_same_current_rules_after_a_change():
    """FR 1.4.1.8 [F.1] Share One Set of Approved Rules and Capacity

    Statement: CampusPark shall give every function that applies parking rules the same current set
    of approved rules and capacity.

    Verification: Test. Passes when: After a change, F.2, F.4, F.5, F.6 and F.7 return the same
    decision for the same request.

    After an approved change, the rule set F.1 returns must equal the one the store hands out, and
    each of F.2, F.4, F.5, F.6 and F.7 must decide the same way whichever of the two it is given.
    Across functions, F.4 offers a pool exactly when F.5 would book it for the same trip, and F.7
    reports the booking that F.5 would now refuse.
    """
    store = make_rules_store()
    trip = trip_details()                               # student trip, [540, 660)
    student = eligibility(permit="student")
    route_data = {"destination": DESTINATION, "status": "ok",
                  "routes": {"P-NORTH": "Walk 6 min east to Duffield Hall"},
                  "addresses": dict(LOT_ADDRESSES)}

    # A booking made before the change, in the period the change will close.
    early_store = ReservationStore()
    early, refusal, _ = book(reservation_request("req-8001", "P-NORTH", 540, 660, "d-801"),
                             store.current(), early_store)
    assert refusal is None
    before = present_eligible_parking_options(candidate_data(trip), [], eligibility=student,
                                              approved_rules=store.current())
    assert "P-NORTH" in option_ids(before)

    returned, change = apply_parking_controls(
        parking_rules_and_capacity=control_change("P-NORTH",
                                                  closures=[{"start": 480, "end": 720}]),
        rules_store=store)
    assert change["accepted"] is True
    assert returned == store.current()
    assert change["version"] == store.current()["version"]
    sources = (copy.deepcopy(returned), store.current())

    # F.2: same trip decision from either copy; the trip itself is still complete.
    f2 = [validate_trip_eligibility(parking_request(), approved_rules=r) for r in sources]
    assert f2[0] == f2[1]
    assert f2[0][0] == {"driver_id": DRIVER}
    assert f2[0][1]["missing"] == []

    # F.4: same option list from either copy, and the closed pool is gone.
    f4 = [present_eligible_parking_options(candidate_data(trip), [], eligibility=student,
                                           approved_rules=r) for r in sources]
    assert f4[0] == f4[1]
    assert option_ids(f4[0]) == ["P-WEST"]

    # F.5: same decision per pool from either copy, and it agrees with the F.4 option list.
    decisions = []
    for n, rules in enumerate(sources):
        bookings = ReservationStore()
        per_pool = {}
        for pool_id in STANDARD_POOLS:
            record, refusal, _ = book(reservation_request("req-82%d-%s" % (n, pool_id), pool_id),
                                      rules, bookings)
            per_pool[pool_id] = "booked" if refusal is None else refusal["reason"]
        decisions.append(per_pool)
    assert decisions[0] == decisions[1]
    assert decisions[0] == {"P-NORTH": "closed", "P-EAST": "not_eligible", "P-WEST": "booked"}
    assert sorted(p for p, d in decisions[0].items() if d == "booked") == option_ids(f4[0])

    # F.6: same confirmation for the earlier booking from either copy.
    f6 = [provide_confirmation_and_route_guidance(early, route_data, approved_rules=r)
          for r in sources]
    assert f6[0] == f6[1]
    assert f6[0]["reservation_id"] == early["reservation_id"]
    assert f6[0]["lot"] in {"P-NORTH", POOL_NAMES["P-NORTH"]}

    # F.7: same report from either copy; the booking in the closed period is reported.
    f7 = [report_reservations_and_affected_bookings(early_store.all(), change, approved_rules=r)
          for r in sources]
    assert f7[0] == f7[1]
    ack, report = f7[0]
    assert ack["version"] == store.current()["version"]
    assert reservation_ids(report["affected"]) == [early["reservation_id"]]


# ---------------------------------------------------------------------------------------------
# 1.4.1.9  F.2 Carry Trip Details Through the Main Flow
# ---------------------------------------------------------------------------------------------

def test_FR_1_4_1_9_trip_details_entered_once_are_carried_to_options_and_booking():
    """FR 1.4.1.9 [F.2] Carry Trip Details Through the Main Flow

    Statement: CampusPark shall carry the accepted trip details through the eligibility check, the
    location lookup and the option list without asking the driver to enter them again.

    Verification: Demonstration. Passes when: A test user completes search and booking while
    entering the trip details once.

    This is the closest automated check at function level: the trip facts are typed once (IO.1),
    F.2 turns them into IO.14, and F.3, F.4, F.5 and F.6 work only from that IO.14 and what follows
    from it, with no second entry of destination, arrival or hours. The demonstration with a test
    user is still required and is not replaced by this test.
    """
    rules = make_rules_store().current()

    # The only entry of trip facts.
    entered_request = parking_request()                 # Duffield Hall, 09:00, 2 hours
    validation, trip = validate_trip_eligibility(entered_request, approved_rules=rules)
    assert trip["missing"] == []
    assert validation == {"driver_id": DRIVER}
    accepted = copy.deepcopy(trip)

    # X.F.3 answers the validation request F.2 produced.
    permit_answer = eligibility(driver_id=validation["driver_id"])

    # Location lookup: built from IO.14, and IO.15 carries the same trip forward.
    assert request_location_and_route(trip, eligibility=permit_answer) == {
        "destination": entered_request["destination"]}
    candidates, guidance = gather_lot_location_and_route_data(trip, lot_answer(),
                                                              eligibility=permit_answer)
    assert candidates["trip"] == accepted
    assert guidance["destination"] == entered_request["destination"]
    assert guidance["addresses"] == STANDARD_ADDRESSES

    # Option list: the window used for capacity is the carried one, since nothing else gives it.
    store = ReservationStore()
    _, refusal, _ = book(reservation_request("req-9000", "P-NORTH", 600, 720, "d-901"),
                         rules, store)
    assert refusal is None
    shown = present_eligible_parking_options(candidates, store.all(), eligibility=permit_answer,
                                             approved_rules=rules)
    options = {option["pool_id"]: option for option in shown["options"]}
    assert options["P-NORTH"]["remaining"] == 1

    # Booking and confirmation: built from the carried trip and the chosen option only.
    carried = candidates["trip"]
    booking = {"request_id": "req-9001", "driver_id": carried["driver_id"], "pool_id": "P-NORTH",
               "start": carried["start"], "end": carried["end"]}
    record, refusal, _ = recheck_and_record_reservation(booking, eligibility=permit_answer,
                                                        approved_rules=rules,
                                                        reservation_store=store)
    assert refusal is None
    confirmation = provide_confirmation_and_route_guidance(record, guidance, approved_rules=rules)
    assert (confirmation["start"], confirmation["end"]) == (540, 660)   # 09:00 for 2 hours
    assert record["driver_id"] == entered_request["driver_id"]

    # The accepted trip was not altered on the way through.
    assert trip == accepted
    assert candidates["trip"] == accepted


# ---------------------------------------------------------------------------------------------
# 1.4.1.10  F.3 Keep Route Guidance Until Confirmation
# ---------------------------------------------------------------------------------------------

def test_FR_1_4_1_10_confirmation_uses_route_guidance_kept_from_the_search(monkeypatch):
    """FR 1.4.1.10 [F.3] Keep Route Guidance Until Confirmation

    Statement: CampusPark shall keep the route guidance data from a search until the booking is
    confirmed or refused.

    Verification: Test. Passes when: A confirmation after a successful route lookup includes
    guidance without a second lookup.

    The test supplies the location and route answer (IO.5) exactly once, during the search. IO.16
    from that search must stay unchanged through the option list and the booking, and F.6 must
    build its guidance from it. While F.6 runs, the F.3 lookup functions are replaced with ones
    that fail the test if called, so a second lookup through F.3 is caught.
    """
    rules = make_rules_store().current()
    trip = trip_details()
    eligible = eligibility()

    # The search, with one successful route lookup.
    assert request_location_and_route(trip, eligibility=eligible) == {"destination": DESTINATION}
    candidates, guidance = gather_lot_location_and_route_data(trip, lot_answer(),
                                                              eligibility=eligible)
    assert guidance["status"] == "ok"
    assert guidance["addresses"] == STANDARD_ADDRESSES
    route_text = guidance["routes"]["P-NORTH"]
    assert isinstance(route_text, str) and route_text.strip()
    kept = copy.deepcopy(guidance)

    # Option list and booking happen between search and confirmation.
    shown = present_eligible_parking_options(candidates, [], eligibility=eligible,
                                             approved_rules=rules)
    assert "P-NORTH" in option_ids(shown)
    store = ReservationStore()
    record, refusal, _ = book(reservation_request("req-10001", "P-NORTH", trip["start"],
                                                  trip["end"]), rules, store)
    assert refusal is None
    assert guidance == kept

    def second_lookup(*args, **kwargs):
        raise AssertionError("F.6 asked for a second location and route lookup")

    for module in (f3_module, f6_module):
        monkeypatch.setattr(module, "request_location_and_route", second_lookup, raising=False)
        monkeypatch.setattr(module, "gather_lot_location_and_route_data", second_lookup,
                            raising=False)

    confirmation = provide_confirmation_and_route_guidance(record, guidance, approved_rules=rules)
    assert confirmation["reservation_id"] == record["reservation_id"]
    assert confirmation["warning"] is None
    assert isinstance(confirmation["guidance"], str)
    assert route_text in confirmation["guidance"]


# ---------------------------------------------------------------------------------------------
# 1.4.1.11  F.5 Make Saved Reservations Available for Reports
# ---------------------------------------------------------------------------------------------

def test_FR_1_4_1_11_every_saved_reservation_is_available_to_reports():
    """FR 1.4.1.11 [F.5] Make Saved Reservations Available for Reports

    Statement: CampusPark shall make every saved reservation available to the reporting function.

    Verification: Test. Passes when: Reservation reports list every reservation saved in a test run.

    IO.12 lists only reservations affected by a change, so each pool's report is driven by an
    approved whole-day closure [0, 1440); its affected list must then hold every reservation saved
    in that pool, and confirmed_count must match.
    """
    rules_store = make_rules_store()
    store = ReservationStore()
    plan = [
        ("req-11001", "P-NORTH", 480, 540, "d-1101", "student"),
        ("req-11002", "P-NORTH", 540, 660, "d-1102", "student"),
        ("req-11003", "P-EAST", 600, 720, "d-1103", "faculty"),
        ("req-11004", "P-EAST", 900, 960, "d-1104", "faculty"),
        ("req-11005", "P-WEST", 780, 840, "d-1105", "student"),
    ]
    saved_records = []
    for request_id, pool_id, start, end, driver_id, permit in plan:
        record, refusal, records = book(
            reservation_request(request_id, pool_id, start, end, driver_id),
            rules_store.current(), store, permit=permit)
        assert refusal is None, request_id
        saved_records.append(record)
    assert records == store.all()

    # A repeated submit and a refused submit do not change what is saved.
    again, refusal, _ = book(reservation_request("req-11002", "P-NORTH", 540, 660, "d-1102"),
                             rules_store.current(), store)
    assert refusal is None
    assert again == saved_records[1]
    assert_refused(book(reservation_request("req-11006", "P-WEST", 800, 860, "d-1106"),
                        rules_store.current(), store), store, {"pool_full"})
    assert reservation_ids(store.all()) == reservation_ids(saved_records)

    # Reports: each pool's report lists every reservation saved in it.
    reported, total = [], 0
    for pool_id in STANDARD_POOLS:
        rules, change = apply_parking_controls(
            parking_rules_and_capacity=control_change(pool_id,
                                                      closures=[{"start": 0, "end": 1440}]),
            rules_store=rules_store)
        assert change["accepted"] is True, pool_id
        ack, report = report_reservations_and_affected_bookings(
            store.all(), change, approved_rules=rules_store.current())
        in_pool = [r for r in saved_records if r["pool_id"] == pool_id]
        assert report["pool_id"] == pool_id
        assert reservation_ids(report["affected"]) == reservation_ids(in_pool), pool_id
        assert report["confirmed_count"] == len(in_pool), pool_id
        reported.extend(report["affected"])
        total += report["confirmed_count"]
    assert reservation_ids(reported) == reservation_ids(saved_records)
    assert total == len(saved_records)
